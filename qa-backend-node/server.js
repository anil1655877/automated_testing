import express from 'express';
import { createServer } from 'http';
import { Server } from 'socket.io';
import cors from 'cors';
import multer from 'multer';
import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs-extra';
import { v4 as uuidv4 } from 'uuid';
import JSZip from 'jszip';
import PDFDocument from 'pdfkit';

import { 
  initDb, Project, TestSession, Report, Log, User,
  isMongoConnected, MongoProject, MongoTestSession, MongoReport, MongoLog 
} from './db.js';
import { runPlaywrightScan, pendingAuthRequests } from './test-engine.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Ensure local static paths exist
const UPLOADS_DIR = path.join(__dirname, 'public', 'uploads');
const SCREENSHOTS_DIR = path.join(__dirname, 'public', 'screenshots');
const VIDEOS_DIR = path.join(__dirname, 'public', 'videos');

await fs.ensureDir(UPLOADS_DIR);
await fs.ensureDir(SCREENSHOTS_DIR);
await fs.ensureDir(VIDEOS_DIR);

const app = express();
const httpServer = createServer(app);

// Prevent Node process crashes from unhandled rejections/exceptions
process.on('uncaughtException', (err) => {
  console.error('CRITICAL: Uncaught Exception:', err);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('CRITICAL: Unhandled Rejection at:', promise, 'reason:', reason);
});

// Configure robust CORS for local development & deployment
app.use(cors({
  origin: '*',
  methods: ['GET', 'POST', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With'],
  credentials: true
}));

app.use(express.json({ limit: '500mb' }));
app.use(express.urlencoded({ limit: '500mb', extended: true }));

// Deployed URL Validation & SSRF prevention helper
function validateTargetUrl(urlString) {
  if (!urlString || typeof urlString !== 'string') {
    throw new Error('Target URL must be a non-empty string.');
  }

  let formattedUrl = urlString.trim();
  if (!/^https?:\/\//i.test(formattedUrl)) {
    // Default to https if no protocol provided
    formattedUrl = 'https://' + formattedUrl;
  }

  let parsedUrl;
  try {
    parsedUrl = new URL(formattedUrl);
  } catch (err) {
    throw new Error('Invalid URL format. Please provide a valid URL (e.g., https://example.com).');
  }

  let hostname = parsedUrl.hostname.toLowerCase();

  // If running inside a container, rewrite localhost/127.0.0.1 to host.docker.internal
  if (process.env.RUNNING_IN_DOCKER === 'true' && (hostname === 'localhost' || hostname === '127.0.0.1')) {
    parsedUrl.hostname = 'host.docker.internal';
    hostname = 'host.docker.internal';
  }

  // SSRF Protection / Private IP gating
  const isLocal = 
    hostname === 'localhost' ||
    hostname === '127.0.0.1' ||
    hostname === '0.0.0.0' ||
    hostname === '169.254.169.254' ||
    hostname === '::1' ||
    hostname.endsWith('.local') ||
    hostname.startsWith('10.') ||
    hostname.startsWith('192.168.') ||
    /^172\.(1[6-9]|2[0-9]|3[0-1])\./.test(hostname);

  if (isLocal && process.env.ALLOW_LOCAL_SCAN === 'false') {
    throw new Error('Scanning local or private IP addresses is restricted for security (SSRF prevention).');
  }

  return parsedUrl.href;
}

// Serve static assets (screenshots, videos, hosted uploads)
app.use('/screenshots', express.static(SCREENSHOTS_DIR));
app.use('/videos', express.static(VIDEOS_DIR));
app.use('/uploads', express.static(UPLOADS_DIR));
app.use(express.static(path.join(__dirname, 'public')));

// Configure Multer for local zip/file storage
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, UPLOADS_DIR);
  },
  filename: (req, file, cb) => {
    cb(null, `${uuidv4()}_${file.originalname}`);
  }
});
const upload = multer({ 
  storage,
  limits: {
    fileSize: 500 * 1024 * 1024 // 500MB limit
  }
});

// Setup Socket.IO
const io = new Server(httpServer, {
  cors: {
    origin: '*',
    methods: ['GET', 'POST']
  }
});

io.on('connection', (socket) => {
  console.log(`Socket client connected: ${socket.id}`);
  
  socket.on('join', (sessionId) => {
    socket.join(sessionId);
    console.log(`Client ${socket.id} joined test session room: ${sessionId}`);
  });

  socket.on('disconnect', () => {
    console.log(`Socket client disconnected: ${socket.id}`);
  });
});

// Simple Background Queue System
const scanQueue = [];
let activeWorker = false;

async function runQueueWorker() {
  if (activeWorker || scanQueue.length === 0) return;
  activeWorker = true;

  const job = scanQueue.shift();
  try {
    console.log(`Running queued job ${job.sessionId}...`);
    await runPlaywrightScan(job.sessionId, job.sourceType, job.sourcePath, io);
  } catch (err) {
    console.error(`Queue job ${job.sessionId} crashed:`, err);
  } finally {
    activeWorker = false;
    runQueueWorker();
  }
}

function addToQueue(sessionId, sourceType, sourcePath) {
  scanQueue.push({ sessionId, sourceType, sourcePath });
  runQueueWorker();
}

// ==========================================
// REST API ENDPOINTS
// ==========================================

// 1. Trigger URL Testing Run
app.post('/api/project/test', async (req, res) => {
  const { url, name } = req.body;
  if (!url) return res.status(400).json({ error: 'Target URL is required.' });

  try {
    const validatedUrl = validateTargetUrl(url);
    const hostname = new URL(validatedUrl).hostname;

    const project = await Project.create({
      name: name || `Scan URL: ${hostname}`,
      sourceType: 'url',
      sourcePath: validatedUrl
    });

    const session = await TestSession.create({
      projectId: project.id,
      status: 'PENDING'
    });

    if (isMongoConnected) {
      await MongoProject.create({
        _id: project.id,
        name: project.name,
        sourceType: 'url',
        sourcePath: validatedUrl
      }).catch(err => console.error('MongoDB project creation failed:', err.message));

      await MongoTestSession.create({
        _id: session.id,
        projectId: project.id,
        status: 'PENDING'
      }).catch(err => console.error('MongoDB session creation failed:', err.message));
    }

    addToQueue(session.id, 'url', validatedUrl);

    res.status(201).json({ message: 'URL scan job queued successfully.', project, session });
  } catch (err) {
    console.error('Failed to trigger scan:', err.message);
    const isClientErr = err.message.includes('restricted') || err.message.includes('Invalid URL') || err.message.includes('non-empty string');
    res.status(isClientErr ? 400 : 500).json({ error: err.message });
  }
});

// 2. Upload Project Folder Route (receives zipped folder file from frontend)
app.post('/api/project/upload-folder', upload.single('folderZip'), async (req, res) => {
  const { projectName } = req.body;
  if (!req.file) {
    return res.status(400).json({ error: 'No zipped folder file provided.' });
  }

  try {
    const projectDirName = `folder_${uuidv4()}`;
    const projectPath = path.join(UPLOADS_DIR, projectDirName);
    await fs.ensureDir(projectPath);

    // Safe ZIP Extraction via JSZip
    const zipData = await fs.readFile(req.file.path);
    const zip = await JSZip.loadAsync(zipData);
    
    for (const [filename, fileObj] of Object.entries(zip.files)) {
      if (fileObj.dir) continue;
      
      // Filter out ignored paths for extraction safety
      if (filename.includes('node_modules') || filename.includes('.git') || filename.includes('dist/') || filename.includes('build/')) {
        continue;
      }

      const destPath = path.join(projectPath, filename);
      // Validate path integrity (Zip-slip security protection)
      if (!destPath.startsWith(projectPath)) {
        continue;
      }

      await fs.ensureDir(path.dirname(destPath));
      const content = await fileObj.async('nodebuffer');
      await fs.writeFile(destPath, content);
    }

    // Clean up temporary archive file
    await fs.remove(req.file.path);

    const project = await Project.create({
      name: projectName || 'Uploaded Folder Project',
      sourceType: 'folder',
      sourcePath: projectPath
    });

    const session = await TestSession.create({
      projectId: project.id,
      status: 'PENDING'
    });

    if (isMongoConnected) {
      await MongoProject.create({
        _id: project.id,
        name: project.name,
        sourceType: 'folder',
        sourcePath: projectPath
      }).catch(err => console.error('MongoDB project creation failed:', err.message));

      await MongoTestSession.create({
        _id: session.id,
        projectId: project.id,
        status: 'PENDING'
      }).catch(err => console.error('MongoDB session creation failed:', err.message));
    }

    addToQueue(session.id, 'folder', projectPath);

    res.status(201).json({ message: 'Zipped folder project created and queued.', project, session });
  } catch (err) {
    if (req.file && req.file.path) {
      await fs.remove(req.file.path).catch(() => {});
    }
    res.status(500).json({ error: err.message });
  }
});

// 3. Upload Project ZIP Route
app.post('/api/project/upload-zip', upload.single('zipFile'), async (req, res) => {
  const { projectName, sessionId } = req.body;
  if (!req.file) return res.status(400).json({ error: 'No zip file provided.' });

  const activeSessionId = sessionId || uuidv4();

  try {
    const projectDirName = `zip_${uuidv4()}`;
    const projectPath = path.join(UPLOADS_DIR, projectDirName);
    await fs.ensureDir(projectPath);

    // Initialize logs room
    console.log(`[ZIP Unpacker] Starting extraction for session ${activeSessionId}...`);
    if (io) {
      io.to(activeSessionId).emit('log', {
        message: 'ZIP upload complete. Beginning server-side archive extraction...',
        level: 'INFO',
        timestamp: new Date()
      });
      io.to(activeSessionId).emit('extraction_progress', { percentage: 0 });
    }

    // Safe ZIP Extraction via JSZip
    const zipData = await fs.readFile(req.file.path);
    const zip = await JSZip.loadAsync(zipData);
    
    const fileEntries = Object.entries(zip.files).filter(([filename, fileObj]) => !fileObj.dir);
    const totalFiles = fileEntries.length;
    let extractedCount = 0;

    for (const [filename, fileObj] of fileEntries) {
      // Exclude hidden files or dangerous files
      const baseFilename = filename.substring(filename.lastIndexOf('/') + 1);
      if (baseFilename.startsWith('.') && baseFilename !== '.env' && baseFilename !== '.gitignore') {
        extractedCount++;
        continue;
      }

      // Filter out ignored paths
      if (filename.includes('node_modules') || filename.includes('.git') || filename.includes('dist/') || filename.includes('build/') || filename.includes('.next/') || filename.includes('coverage/') || filename.includes('cache/')) {
        extractedCount++;
        continue;
      }

      const destPath = path.join(projectPath, filename);
      // Validate path integrity (Zip-slip security protection)
      if (!destPath.startsWith(projectPath)) {
        extractedCount++;
        continue;
      }

      await fs.ensureDir(path.dirname(destPath));
      const content = await fileObj.async('nodebuffer');
      await fs.writeFile(destPath, content);
      
      extractedCount++;
      const percent = Math.round((extractedCount / totalFiles) * 100);
      if (percent % 10 === 0 && io) {
        io.to(activeSessionId).emit('extraction_progress', { 
          percentage: percent,
          currentFile: `Extracted: ${baseFilename}`
        });
      }
    }

    // Emit completed extraction state
    if (io) {
      io.to(activeSessionId).emit('extraction_progress', { percentage: 100 });
      io.to(activeSessionId).emit('log', {
        message: 'Server-side ZIP extraction complete. Project hosted successfully.',
        level: 'SUCCESS',
        timestamp: new Date()
      });
    }

    // Clean up temporary archive file
    await fs.remove(req.file.path);

    const project = await Project.create({
      name: projectName || req.file.originalname,
      sourceType: 'zip',
      sourcePath: projectPath
    });

    const session = await TestSession.create({
      id: activeSessionId, // Match pre-allocated uuid
      projectId: project.id,
      status: 'PENDING'
    });

    if (isMongoConnected) {
      await MongoProject.create({
        _id: project.id,
        name: project.name,
        sourceType: 'zip',
        sourcePath: projectPath
      }).catch(err => console.error('MongoDB project creation failed:', err.message));

      await MongoTestSession.create({
        _id: session.id,
        projectId: project.id,
        status: 'PENDING'
      }).catch(err => console.error('MongoDB session creation failed:', err.message));
    }

    addToQueue(session.id, 'zip', projectPath);

    res.status(201).json({ message: 'ZIP archive unpacked and queued.', project, session });
  } catch (err) {
    if (req.file && req.file.path) {
      await fs.remove(req.file.path).catch(() => {});
    }
    if (io) {
      io.to(activeSessionId).emit('log', {
        message: `ZIP extraction failed: ${err.message}`,
        level: 'ERROR',
        timestamp: new Date()
      });
    }
    res.status(500).json({ error: err.message });
  }
});

// 4. Handle Credentials Response
app.post('/api/auth/session', (req, res) => {
  const { sessionId, username, password, role } = req.body;
  const pending = pendingAuthRequests.get(sessionId);

  if (!pending || pending.type !== 'credentials') {
    return res.status(400).json({ error: 'No active credentials auth request found for this session.' });
  }

  // Resolve Playwright execution wait promise
  pending.resolve({ username, password, role });
  pendingAuthRequests.delete(sessionId);

  res.json({ message: 'Credentials sent to automation engine successfully.' });
});

// 5. Handle OTP Verification Code Response
app.post('/api/auth/otp', (req, res) => {
  const { sessionId, otp } = req.body;
  const pending = pendingAuthRequests.get(sessionId);

  if (!pending || pending.type !== 'otp') {
    return res.status(400).json({ error: 'No active OTP verification request found for this session.' });
  }

  // Resolve Playwright waiting promise
  pending.resolve({ otp });
  pendingAuthRequests.delete(sessionId);

  res.json({ message: 'OTP verification code sent to engine.' });
});

// 6. Get all scans and session history
app.get('/api/projects', async (req, res) => {
  try {
    const projects = await Project.findAll({
      order: [['createdAt', 'DESC']]
    });
    res.json(projects);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 7. Get details of a single project
app.get('/api/projects/:id', async (req, res) => {
  try {
    const project = await Project.findByPk(req.params.id, {
      include: [TestSession]
    });
    if (!project) return res.status(404).json({ error: 'Project record not found.' });
    res.json(project);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 8. Fetch all test session reports
app.get('/api/reports', async (req, res) => {
  try {
    const sessions = await TestSession.findAll({
      order: [['createdAt', 'DESC']],
      include: [Project]
    });
    res.json(sessions);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 9. Fetch details of a specific test session
app.get('/api/reports/:id', async (req, res) => {
  try {
    const session = await TestSession.findByPk(req.params.id, {
      include: [Project, Report, Log]
    });
    if (!session) return res.status(404).json({ error: 'Test session not found.' });
    res.json(session);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 10. Delete a report session
app.delete('/api/reports/:id', async (req, res) => {
  try {
    const session = await TestSession.findByPk(req.params.id);
    if (!session) return res.status(404).json({ error: 'Session report not found.' });
    
    // Auto-clean video files & screenshots
    const videoDir = path.join(VIDEOS_DIR, session.id);
    const screenshotDir = path.join(SCREENSHOTS_DIR, session.id);
    await fs.remove(videoDir).catch(() => {});
    await fs.remove(screenshotDir).catch(() => {});

    await session.destroy();

    // Sync deletion to MongoDB if connected
    if (isMongoConnected) {
      await MongoTestSession.deleteOne({ _id: req.params.id }).catch(err => console.error('MongoDB delete session failed:', err.message));
      await MongoReport.deleteMany({ sessionId: req.params.id }).catch(err => console.error('MongoDB delete reports failed:', err.message));
      await MongoLog.deleteMany({ sessionId: req.params.id }).catch(err => console.error('MongoDB delete logs failed:', err.message));
    }

    res.json({ message: 'Session report and related media cleaned.' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 11. Approve Bug
app.post('/api/reports/:id/approve-bug/:bugId', async (req, res) => {
  try {
    const bug = await Report.findOne({
      where: { id: req.params.bugId, sessionId: req.params.id }
    });
    if (!bug) return res.status(404).json({ error: 'Bug record not found.' });
    
    bug.approved = true;
    await bug.save();

    // Sync approval to MongoDB if connected
    if (isMongoConnected) {
      await MongoReport.updateOne(
        { _id: req.params.bugId },
        { approved: true }
      ).catch(err => console.error('MongoDB approve bug update failed:', err.message));
    }

    res.json({ message: 'Bug approved and flagged for developers.' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 12. Dashboard Analytics Summary
app.get('/api/analytics', async (req, res) => {
  try {
    const totalProjects = await Project.count();
    const totalSessions = await TestSession.count();
    const totalBugs = await Report.count();
    const approvedBugs = await Report.count({ where: { approved: true } });

    // Severity Breakdown
    const critical = await Report.count({ where: { severity: 'CRITICAL' } });
    const high = await Report.count({ where: { severity: 'HIGH' } });
    const medium = await Report.count({ where: { severity: 'MEDIUM' } });
    const low = await Report.count({ where: { severity: 'LOW' } });

    // Category Breakdown
    const ui = await Report.count({ where: { category: 'UI' } });
    const api = await Report.count({ where: { category: 'API' } });
    const consoleLogs = await Report.count({ where: { category: 'CONSOLE' } });
    const resource = await Report.count({ where: { category: 'RESOURCE' } });
    const performance = await Report.count({ where: { category: 'PERFORMANCE' } });

    // Session stability trends (last 7 completed scans)
    const recentSessions = await TestSession.findAll({
      where: { status: 'COMPLETED' },
      limit: 7,
      order: [['createdAt', 'DESC']],
      include: [Project]
    });

    const trend = recentSessions.reverse().map((s, idx) => ({
      name: s.Project?.name.substring(0, 12) || `Scan #${idx}`,
      bugs: s.totalBugs
    }));

    res.json({
      summary: {
        totalProjects,
        totalSessions,
        totalBugs,
        approvedBugs
      },
      severity: [
        { name: 'Critical', value: critical },
        { name: 'High', value: high },
        { name: 'Medium', value: medium },
        { name: 'Low', value: low }
      ],
      category: [
        { name: 'UI Issues', value: ui },
        { name: 'API Faults', value: api },
        { name: 'Console Errors', value: consoleLogs },
        { name: 'Asset Issues', value: resource },
        { name: 'Performance', value: performance }
      ],
      trend
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 13. Download PDF Report Endpoint
app.get('/api/reports/:id/pdf', async (req, res) => {
  try {
    const session = await TestSession.findByPk(req.params.id, {
      include: [Project, Report]
    });
    if (!session) return res.status(404).json({ error: 'Session not found' });

    const doc = new PDFDocument({ margin: 50 });
    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Disposition', `attachment; filename=QA_Report_${session.id}.pdf`);
    doc.pipe(res);

    // Title / Header
    doc.fillColor('#0b0f19').fontSize(24).text('QA Automated Test Session Summary', { align: 'center' });
    doc.moveDown(0.5);
    doc.fontSize(10).fillColor('#64748b').text(`Session ID: ${session.id}`, { align: 'center' });
    doc.text(`Generated at: ${new Date().toLocaleString()}`, { align: 'center' });
    doc.moveDown(1.5);

    // Project metadata
    doc.fillColor('#0b0f19').fontSize(14).text('Project Specifications');
    doc.strokeColor('#e2e8f0').lineWidth(1).moveTo(50, doc.y).lineTo(550, doc.y).stroke();
    doc.moveDown(0.5);

    doc.fontSize(11).fillColor('#334155');
    doc.text(`Project Name: ${session.Project?.name || 'Local Project'}`);
    doc.text(`Source Type: ${session.Project?.sourceType.toUpperCase()}`);
    doc.text(`Source Path: ${session.Project?.sourcePath}`);
    doc.text(`Execution State: ${session.status}`);
    doc.text(`Total Pages Scanned: ${session.totalPages}`);
    doc.text(`Total Bugs Found: ${session.totalBugs}`);
    doc.text(`Scan Duration: ${session.durationSeconds}s`);
    doc.moveDown(2);

    // Bugs listing
    doc.fontSize(14).fillColor('#0b0f19').text('Bug & Issues Log');
    doc.strokeColor('#e2e8f0').lineWidth(1).moveTo(50, doc.y).lineTo(550, doc.y).stroke();
    doc.moveDown(0.5);

    if (session.Reports && session.Reports.length > 0) {
      session.Reports.forEach((bug, idx) => {
        doc.fontSize(12).fillColor('#ef4444').text(`${idx + 1}. [${bug.severity}] ${bug.title}`);
        doc.fontSize(10).fillColor('#334155');
        doc.text(`Category: ${bug.category}`);
        doc.text(`Page: ${bug.pageUrl}`);
        doc.text(`Description: ${bug.description}`);
        doc.text(`Root Cause: ${bug.rootCause}`);
        doc.text(`Suggested Fix: ${bug.suggestedFix}`);
        doc.moveDown(1);
      });
    } else {
      doc.fontSize(11).fillColor('#0f766e').text('No bugs or failures were detected during this run.');
    }

    doc.end();
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Express Error Handling Middleware for Upload/Payload limits
app.use((err, req, res, next) => {
  if (err instanceof multer.MulterError) {
    if (err.code === 'LIMIT_FILE_SIZE') {
      return res.status(413).json({ error: 'ZIP file is too large. Remove node_modules, build files, or cache folders and try again.' });
    }
    return res.status(400).json({ error: `Upload error: ${err.message}` });
  }
  
  if (err.status === 413 || err.type === 'entity.too.large') {
    return res.status(413).json({ error: 'ZIP file is too large. Remove node_modules, build files, or cache folders and try again.' });
  }

  console.error('Unhandled Server Error:', err);
  res.status(500).json({ error: 'Internal Server Error: Something went wrong on the server.' });
});

// Start Server
const PORT = process.env.PORT || 5000;
initDb()
  .then(() => {
    httpServer.listen(PORT, () => {
      console.log(`Express and Socket.IO servers online on port ${PORT}`);
    });
  })
  .catch((err) => {
    console.error('Fatal initialization error during database sync:', err.message);
    // Bind anyway so the proxy doesn't get a 502 Bad Gateway and the developer can see the dashboard
    httpServer.listen(PORT, () => {
      console.log(`Express and Socket.IO servers online on port ${PORT} (SQLite/PostgreSQL fallback active due to init error)`);
    });
  });
