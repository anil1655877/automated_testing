import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Tooltip, ResponsiveContainer, PieChart, Pie, Cell 
} from 'recharts';
import { 
  Play, Shield, Cpu, Terminal, Eye, Download, Mail, CheckCircle, AlertTriangle, Clock, Layers, ChevronLeft, ChevronRight, Activity, RefreshCw, UploadCloud, Image as ImageIcon, Sun, Moon, Trash2, ZoomIn, ZoomOut, RotateCcw, X
} from 'lucide-react';
import axios from 'axios';
import { io } from 'socket.io-client';
import JSZip from 'jszip';

const SEV_COLORS = {
  'CRITICAL': '#ef4444',
  'HIGH': '#f97316',
  'MEDIUM': '#eab308',
  'LOW': '#3b82f6'
};

const PIE_COLORS = ['#ef4444', '#f97316', '#eab308', '#3b82f6'];
const CAT_COLORS = ['#3b82f6', '#10b981', '#a78bfa', '#f59e0b', '#ef4444'];

const uuidv4 = () => {
  try {
    return crypto.randomUUID();
  } catch {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  }
};

export default function App() {
  const [theme, setTheme] = useState('dark');
  const [activeView, setActiveView] = useState('dashboard');
  const [reports, setReports] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [selectedSessionId, setSelectedSessionId] = useState(null);
  const [currentSessionDetails, setCurrentSessionDetails] = useState(null);
  
  // Launch scan inputs
  const [targetUrl, setTargetUrl] = useState('https://demoqa.com');
  const [projectName, setProjectName] = useState('');
  const [uploadTab, setUploadTab] = useState('url');
  
  // Folder upload files state
  const [folderFiles, setFolderFiles] = useState([]);
  const [folderName, setFolderName] = useState('');
  const [rawFolderFilesCount, setRawFolderFilesCount] = useState(0);
  const [ignoredFilesCount, setIgnoredFilesCount] = useState(0);
  const [estimatedFolderSize, setEstimatedFolderSize] = useState(0);
  const [ignoredFoldersList, setIgnoredFoldersList] = useState([]);
  const [compressionProgress, setCompressionProgress] = useState(0);
  const [compressionState, setCompressionState] = useState('idle'); // idle, compressing, uploading, error, success
  const [uploadMetrics, setUploadMetrics] = useState({ speed: '0.00', eta: 0, currentFile: '' });
  const [uploadErrorMessage, setUploadErrorMessage] = useState('');
  const [uploadErrorSeverity, setUploadErrorSeverity] = useState('warning'); // warning, error
  const cancelSourceRef = useRef(null);
  
  // ZIP upload state
  const [zipFile, setZipFile] = useState(null);
  const [zipFileName, setZipFileName] = useState('');
  
  // ZIP upload optimization/progress states
  const [originalZipSize, setOriginalZipSize] = useState(0);
  const [optimizedZipSize, setOptimizedZipSize] = useState(0);
  const [zipOptimizationProgress, setZipOptimizationProgress] = useState(0);
  const [zipOptimizationState, setZipOptimizationState] = useState('idle'); // idle, optimizing, ready, error
  const [zipExtractionPercentage, setZipExtractionPercentage] = useState(0);
  const [zipIgnoredFilesCount, setZipIgnoredFilesCount] = useState(0);
  const [zipAllowedFilesCount, setZipAllowedFilesCount] = useState(0);
  const [zipTotalFilesCount, setZipTotalFilesCount] = useState(0);
  const [zipErrorMessage, setZipErrorMessage] = useState('');
  const [zipErrorSeverity, setZipErrorSeverity] = useState('warning');
  const [zipIgnoredFoldersList, setZipIgnoredFoldersList] = useState([]);
  const [zipUploadMetrics, setZipUploadMetrics] = useState({ speed: '0.00', eta: 0, currentFile: '' });
  const zipCancelSourceRef = useRef(null);

  // Socket and Log states
  const [scanning, setScanning] = useState(false);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [liveLogs, setLiveLogs] = useState([]);
  const [liveProgress, setLiveProgress] = useState({ percentage: 0, pagesCrawled: 0, totalBugs: 0 });
  const [detectedBugs, setDetectedBugs] = useState([]);
  
  // Authentication interruption states
  const [authRequest, setAuthRequest] = useState(null); // { sessionId, url, type: 'credentials' | 'otp' }
  const [credentialsForm, setCredentialsForm] = useState({ username: '', password: '', role: 'Admin' });
  const [otpToken, setOtpToken] = useState('');
  const [uploadPercentage, setUploadPercentage] = useState(0);
  const [isUrlSubmitting, setIsUrlSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);

  // Advanced Screenshot Annotation compare/zoom states
  const [screenshotTabs, setScreenshotTabs] = useState({}); // { [bugId]: 'annotated' | 'original' }
  const [compareModalBug, setCompareModalBug] = useState(null); // bug object
  const [compareMode, setCompareMode] = useState('slider'); // 'slider' | 'side-by-side'
  const [zoomModalImage, setZoomModalImage] = useState(null); // { src, title }
  const [sliderVal, setSliderVal] = useState(50);
  const [scale, setScale] = useState(1);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  useEffect(() => {
    setSliderVal(50);
  }, [compareModalBug]);

  useEffect(() => {
    setScale(1);
    setPosition({ x: 0, y: 0 });
    setIsDragging(false);
  }, [zoomModalImage]);

  const handleMouseDown = (e) => {
    if (scale === 1) return;
    setIsDragging(true);
    setDragStart({ x: e.clientX - position.x, y: e.clientY - position.y });
  };

  const handleMouseMove = (e) => {
    if (!isDragging) return;
    setPosition({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y
    });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const zoomIn = () => setScale(prev => Math.min(prev + 0.5, 4));
  const zoomOut = () => {
    setScale(prev => {
      const next = Math.max(prev - 0.5, 1);
      if (next === 1) setPosition({ x: 0, y: 0 });
      return next;
    });
  };
  const resetZoom = () => {
    setScale(1);
    setPosition({ x: 0, y: 0 });
  };

  const socketRef = useRef(null);
  const logTerminalEndRef = useRef(null);

  // Fetch initial details
  const loadData = async () => {
    try {
      const repRes = await axios.get('/api/reports');
      setReports(repRes.data);

      const analRes = await axios.get('/api/analytics');
      setAnalytics(analRes.data);
    } catch (err) {
      console.error("Error communicating with backend:", err);
    }
  };

  // Helper to load details of a specific test session
  const viewSessionReport = async (sessionId) => {
    try {
      const res = await axios.get(`/api/reports/${sessionId}`);
      setCurrentSessionDetails(res.data);
      setSelectedSessionId(sessionId);
      setActiveView('reports');
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadData();
    // Auto-update dashboard metrics periodically
    const interval = setInterval(loadData, 8000);
    return () => clearInterval(interval);
  }, []);

  // Connect to Socket.IO and listen to live events
  useEffect(() => {
    socketRef.current = io('http://localhost:5000');

    socketRef.current.on('connect', () => {
      console.log('Socket.IO connection established with backend.');
    });

    socketRef.current.on('log', (logEntry) => {
      setLiveLogs((prev) => [...prev, logEntry]);
    });

    socketRef.current.on('progress', (prog) => {
      setLiveProgress(prog);
    });

    socketRef.current.on('bug_detected', (bug) => {
      setDetectedBugs((prev) => [...prev, bug]);
    });

    socketRef.current.on('auth_required', (req) => {
      setAuthRequest(req);
    });

    socketRef.current.on('extraction_progress', (data) => {
      setZipExtractionPercentage(data.percentage);
      if (data.currentFile) {
        setZipUploadMetrics(prev => ({
          ...prev,
          currentFile: data.currentFile
        }));
      }
    });

    socketRef.current.on('completed', ({ sessionId }) => {
      setScanning(false);
      loadData();
      // Auto open detailed reports view
      viewSessionReport(sessionId);
    });

    return () => {
      if (socketRef.current) socketRef.current.disconnect();
    };
  }, []);

  // Auto-scroll logs to bottom
  useEffect(() => {
    if (logTerminalEndRef.current) {
      logTerminalEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [liveLogs]);

  // Join Socket Session Room when starting a scan
  const startLiveMonitoring = (sessionId) => {
    setActiveSessionId(sessionId);
    setLiveLogs([]);
    setDetectedBugs([]);
    setLiveProgress({ percentage: 0, pagesCrawled: 0, totalBugs: 0 });
    setScanning(true);
    setActiveView('monitor');
    if (socketRef.current) {
      socketRef.current.emit('join', sessionId);
    }
  };

  // 1. Submit Deployed URL with Retry and Loading States
  const handleUrlScanSubmit = async (e) => {
    e.preventDefault();
    if (!targetUrl) return;
    
    setIsUrlSubmitting(true);
    setSubmitError(null);

    const maxRetries = 3;
    let attempt = 0;
    let success = false;
    let lastError = null;

    while (attempt < maxRetries && !success) {
      try {
        if (attempt > 0) {
          console.log(`[URL Scanner] Retrying API request... Attempt ${attempt + 1}/${maxRetries}`);
        }
        
        const res = await axios.post('/api/project/test', {
          url: targetUrl,
          name: projectName || undefined
        });
        
        const { session } = res.data;
        startLiveMonitoring(session.id);
        success = true;
      } catch (err) {
        lastError = err;
        attempt++;
        
        if (attempt < maxRetries) {
          // Exponential backoff: wait 1s, then 2s before retrying
          await new Promise(resolve => setTimeout(resolve, attempt * 1000));
        }
      }
    }

    setIsUrlSubmitting(false);

    if (!success) {
      const errorMsg = lastError?.response?.data?.error || lastError?.message || 'Connection failed or server error';
      setSubmitError(errorMsg);
      alert(`Failed to trigger URL scan (tried ${maxRetries} times): ${errorMsg}`);
    }
  };

  // 2. Submit Project Folder Upload
  const handleFolderUploadChange = (e) => {
    setUploadErrorMessage('');
    setUploadErrorSeverity('warning');
    setCompressionState('idle');
    
    const files = e.target.files;
    if (!files || files.length === 0) return;

    console.time('[Folder Scanner] Scanning time');
    const totalFilesCount = files.length;
    setRawFolderFilesCount(totalFilesCount);

    const ignoredKeywords = ['node_modules', '.git', 'dist', 'build', '.next', 'coverage', 'temp', 'cache'];
    const dangerousExtensions = ['.exe', '.dll', '.bat', '.sh', '.cmd', '.msi', '.apk'];
    const allowedExtensions = [
      '.js', '.jsx', '.ts', '.tsx', '.html', '.css', '.scss', '.json', '.md', 
      '.py', '.java', '.cpp', '.c', '.php',
      '.png', '.jpg', '.jpeg', '.gif', '.svg'
    ];

    const cleanFiles = [];
    const detectedIgnoredFolders = new Set();
    let dangerousCount = 0;
    let ignoredFolderCount = 0;
    let nonWhitelistedCount = 0;
    let totalUncompressedSize = 0;

    // High performance single-pass loop optimized for 30,000+ files
    for (let i = 0; i < totalFilesCount; i++) {
      const file = files[i];
      const relativePath = file.webkitRelativePath || file.name;
      
      // Ignore hidden files (except config/ignore templates)
      if (file.name.startsWith('.') && file.name !== '.env' && file.name !== '.gitignore') {
        nonWhitelistedCount++;
        continue;
      }

      // Check ignored folders recursively
      const segments = relativePath.split('/');
      let isIgnoredDir = false;
      for (let j = 0; j < segments.length - 1; j++) {
        const seg = segments[j].toLowerCase();
        const matchesIgnored = ignoredKeywords.some(keyword => seg === keyword || seg.includes('cache') || seg.includes('temp'));
        if (matchesIgnored) {
          detectedIgnoredFolders.add(segments[j]);
          isIgnoredDir = true;
          break;
        }
      }

      if (isIgnoredDir) {
        ignoredFolderCount++;
        continue;
      }

      // Check extensions
      const lastDot = file.name.lastIndexOf('.');
      const ext = lastDot !== -1 ? file.name.substring(lastDot).toLowerCase() : '';

      if (dangerousExtensions.includes(ext)) {
        dangerousCount++;
        continue;
      }

      if (!allowedExtensions.includes(ext)) {
        nonWhitelistedCount++;
        continue;
      }

      // Pass safe, whitelisted file
      cleanFiles.push(file);
      totalUncompressedSize += file.size;
    }

    console.timeEnd('[Folder Scanner] Scanning time');
    console.log(`[Folder Upload Logs] Total: ${totalFilesCount}, Whitelisted: ${cleanFiles.length}, Ignored Directory Files: ${ignoredFolderCount}, Blocks: ${dangerousCount}, Skips: ${nonWhitelistedCount}`);

    // If zero safe files found - Critical Failure (Red color)
    if (cleanFiles.length === 0) {
      setUploadErrorSeverity('error');
      setUploadErrorMessage('No safe files found to upload: The selected folder does not contain any valid project files matching the allowed file types.');
      setFolderFiles([]);
      setIgnoredFilesCount(totalFilesCount);
      setEstimatedFolderSize(0);
      setIgnoredFoldersList(Array.from(detectedIgnoredFolders));
      return;
    }

    // Friendly notifications (Orange color)
    let infoMessage = '';
    const totalIgnored = ignoredFolderCount + dangerousCount + nonWhitelistedCount;
    if (dangerousCount > 0) {
      infoMessage += `⚠️ ${dangerousCount} dangerous files ignored automatically. `;
    }
    if (ignoredFolderCount > 0) {
      infoMessage += `Ignored ${ignoredFolderCount} files inside blocked directories.`;
    }

    if (infoMessage) {
      setUploadErrorSeverity('warning');
      setUploadErrorMessage(infoMessage);
    }

    setFolderFiles(cleanFiles);
    setIgnoredFilesCount(totalIgnored);
    setEstimatedFolderSize(totalUncompressedSize);
    setIgnoredFoldersList(Array.from(detectedIgnoredFolders));

    const rootName = cleanFiles[0].webkitRelativePath.split('/')[0];
    setFolderName(rootName);
  };

  const handleFolderUploadSubmit = async (e) => {
    if (e) e.preventDefault();
    if (folderFiles.length === 0) return;

    setCompressionState('compressing');
    setCompressionProgress(0);
    setUploadErrorMessage('');

    try {
      const zip = new JSZip();
      folderFiles.forEach((file) => {
        const relativePath = file.webkitRelativePath || file.name;
        zip.file(relativePath, file);
      });

      const zippedBlob = await zip.generateAsync({
        type: 'blob',
        compression: 'DEFLATE',
        compressionOptions: { level: 6 }
      }, (metadata) => {
        setCompressionProgress(Math.round(metadata.percent));
        setUploadMetrics(prev => ({
          ...prev,
          currentFile: metadata.currentFile ? `Compressing: ${metadata.currentFile.substring(metadata.currentFile.lastIndexOf('/') + 1)}` : ''
        }));
      });

      setCompressionState('uploading');
      setUploadPercentage(0);

      const formData = new FormData();
      formData.append('folderZip', zippedBlob, `${folderName || 'project'}.zip`);
      formData.append('projectName', folderName || 'Uploaded Folder Project');

      cancelSourceRef.current = axios.CancelToken.source();
      const startTime = Date.now();

      const res = await axios.post('/api/project/upload-folder', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 300000,
        cancelToken: cancelSourceRef.current.token,
        onUploadProgress: (progEvent) => {
          const percent = Math.round((progEvent.loaded * 100) / progEvent.total);
          setUploadPercentage(percent);

          const elapsedSeconds = (Date.now() - startTime) / 1000;
          const bytesUploaded = progEvent.loaded;
          const speedBytesPerSecond = elapsedSeconds > 0 ? (bytesUploaded / elapsedSeconds) : 0;
          const speedMB = (speedBytesPerSecond / (1024 * 1024)).toFixed(2);
          
          const remainingBytes = progEvent.total - bytesUploaded;
          const etaSeconds = speedBytesPerSecond > 0 ? Math.round(remainingBytes / speedBytesPerSecond) : 0;

          setUploadMetrics({
            speed: speedMB,
            eta: etaSeconds,
            currentFile: `Uploading... (${(bytesUploaded / (1024 * 1024)).toFixed(1)}MB / ${(progEvent.total / (1024 * 1024)).toFixed(1)}MB)`
          });
        }
      });

      const { session } = res.data;
      setCompressionState('success');
      startLiveMonitoring(session.id);
    } catch (err) {
      setCompressionState('error');
      setUploadErrorSeverity('error');
      
      if (axios.isCancel(err)) {
        setUploadErrorMessage('Upload cancelled by user.');
      } else if (err.code === 'ECONNABORTED') {
        setUploadErrorMessage('Request Timeout: Upload took too long (limit exceeded 5 minutes).');
      } else if (!err.response) {
        setUploadErrorMessage('Server Unreachable: Connection lost or backend service is offline.');
      } else if (err.response.status === 413) {
        setUploadErrorMessage('Payload Limit Exceeded: Zipped project exceeds the 100MB server limit.');
      } else {
        setUploadErrorMessage(`Upload failed: ${err.response?.data?.error || err.message}`);
      }
    }
  };

  const handleCancelUpload = () => {
    if (cancelSourceRef.current) {
      cancelSourceRef.current.cancel('Upload aborted by user.');
    }
  };

  // 3. ZIP File Drag & Drop Setup
  const handleZipFileChange = async (e) => {
    const files = e.target.files;
    if (!files || !files[0]) return;

    const file = files[0];
    setZipFileName(file.name);
    setOriginalZipSize(file.size);
    setZipErrorMessage('');
    setZipErrorSeverity('warning');
    setZipOptimizationProgress(0);
    setZipOptimizationState('optimizing');
    setZipIgnoredFoldersList([]);

    try {
      console.time('[ZIP Scanner] In-browser ZIP read');
      const zip = await JSZip.loadAsync(file);
      
      const fileEntries = Object.entries(zip.files).filter(([, fileObj]) => !fileObj.dir);
      const totalEntriesCount = fileEntries.length;
      setZipTotalFilesCount(totalEntriesCount);

      const ignoredKeywords = ['node_modules', '.git', 'dist', 'build', '.next', 'coverage', 'temp', 'cache'];
      const dangerousExtensions = ['.exe', '.dll', '.bat', '.sh', '.cmd', '.msi', '.apk'];
      const allowedExtensions = [
        '.js', '.jsx', '.ts', '.tsx', '.html', '.css', '.scss', '.json', '.md', 
        '.py', '.java', '.cpp', '.c', '.php',
        '.png', '.jpg', '.jpeg', '.gif', '.svg'
      ];

      const cleanEntries = [];
      const detectedIgnoredFolders = new Set();
      let dangerousCount = 0;
      let ignoredFolderCount = 0;
      let nonWhitelistedCount = 0;

      for (const [filename, fileObj] of fileEntries) {
        const segments = filename.split('/');
        
        // Ignore hidden files
        const baseFilename = segments[segments.length - 1];
        if (baseFilename.startsWith('.') && baseFilename !== '.env' && baseFilename !== '.gitignore') {
          nonWhitelistedCount++;
          continue;
        }

        // Check ignored folders recursively
        let isIgnoredDir = false;
        for (let j = 0; j < segments.length - 1; j++) {
          const seg = segments[j].toLowerCase();
          const matchesIgnored = ignoredKeywords.some(keyword => seg === keyword || seg.includes('cache') || seg.includes('temp'));
          if (matchesIgnored) {
            detectedIgnoredFolders.add(segments[j]);
            isIgnoredDir = true;
            break;
          }
        }

        if (isIgnoredDir) {
          ignoredFolderCount++;
          continue;
        }

        // Check extensions
        const lastDot = baseFilename.lastIndexOf('.');
        const ext = lastDot !== -1 ? baseFilename.substring(lastDot).toLowerCase() : '';

        if (dangerousExtensions.includes(ext)) {
          dangerousCount++;
          continue;
        }

        if (!allowedExtensions.includes(ext)) {
          nonWhitelistedCount++;
          continue;
        }

        cleanEntries.push([filename, fileObj]);
      }

      console.timeEnd('[ZIP Scanner] In-browser ZIP read');
      console.log(`[ZIP Scan Logs] Total: ${totalEntriesCount}, Whitelisted: ${cleanEntries.length}, Ignored Directory Files: ${ignoredFolderCount}, Blocks: ${dangerousCount}, Skips: ${nonWhitelistedCount}`);

      const totalIgnored = ignoredFolderCount + dangerousCount + nonWhitelistedCount;
      setZipIgnoredFilesCount(totalIgnored);
      setZipAllowedFilesCount(cleanEntries.length);
      setZipIgnoredFoldersList(Array.from(detectedIgnoredFolders));

      if (cleanEntries.length === 0) {
        setZipErrorSeverity('error');
        setZipErrorMessage('No safe files found to upload: The selected ZIP does not contain any valid project files matching the allowed file types.');
        setZipFile(null);
        setZipOptimizationState('error');
        return;
      }

      // Repackage the clean entries into a new ZIP in-browser
      const newZip = new JSZip();
      
      let copiedCount = 0;
      for (const [filename, fileObj] of cleanEntries) {
        const content = await fileObj.async('uint8array');
        newZip.file(filename, content);
        copiedCount++;
        setZipOptimizationProgress(Math.round((copiedCount / cleanEntries.length) * 50));
      }

      const optimizedBlob = await newZip.generateAsync({
        type: 'blob',
        compression: 'DEFLATE',
        compressionOptions: { level: 6 }
      }, (metadata) => {
        setZipOptimizationProgress(50 + Math.round(metadata.percent / 2));
      });

      setOptimizedZipSize(optimizedBlob.size);
      setZipFile(optimizedBlob);
      setZipOptimizationState('ready');

      // Warnings or Error boundaries based on size
      if (optimizedBlob.size > 500 * 1024 * 1024) {
        setZipErrorSeverity('error');
        setZipErrorMessage('ZIP file is too large. Remove node_modules, build files, or cache folders and try again.');
        setZipOptimizationState('error');
      } else {
        let infoMessage = '';
        if (dangerousCount > 0) {
          infoMessage += `⚠️ ${dangerousCount} dangerous files ignored automatically. `;
        }
        if (ignoredFolderCount > 0) {
          infoMessage += `Ignored ${ignoredFolderCount} files inside blocked directories. `;
        }
        if (optimizedBlob.size > 300 * 1024 * 1024) {
          infoMessage += `Optimized ZIP size is very large (${(optimizedBlob.size / (1024 * 1024)).toFixed(1)}MB). `;
        }
        if (infoMessage) {
          setZipErrorSeverity('warning');
          setZipErrorMessage(infoMessage);
        }
      }

    } catch (err) {
      console.error('[ZIP Scanner] Error parsing ZIP:', err);
      setZipErrorSeverity('error');
      setZipErrorMessage(`Failed to optimize ZIP archive: ${err.message}`);
      setZipFile(null);
      setZipOptimizationState('error');
    }
  };

  const handleZipUploadSubmit = async (e) => {
    if (e) e.preventDefault();
    if (!zipFile) return;

    setZipOptimizationState('uploading');
    setZipExtractionPercentage(0);
    setUploadPercentage(0);
    setZipErrorMessage('');

    const localSessionId = uuidv4();
    const formData = new FormData();
    formData.append('zipFile', zipFile, zipFileName || 'project.zip');
    formData.append('projectName', projectName || zipFileName.replace('.zip', ''));
    formData.append('sessionId', localSessionId);

    // Join room for logs immediately
    if (socketRef.current) {
      socketRef.current.emit('join', localSessionId);
    }

    zipCancelSourceRef.current = axios.CancelToken.source();
    const startTime = Date.now();

    try {
      const res = await axios.post('/api/project/upload-zip', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 300000,
        cancelToken: zipCancelSourceRef.current.token,
        onUploadProgress: (progEvent) => {
          const percent = Math.round((progEvent.loaded * 100) / progEvent.total);
          setUploadPercentage(percent);

          const elapsedSeconds = (Date.now() - startTime) / 1000;
          const bytesUploaded = progEvent.loaded;
          const speedBytesPerSecond = elapsedSeconds > 0 ? (bytesUploaded / elapsedSeconds) : 0;
          const speedMB = (speedBytesPerSecond / (1024 * 1024)).toFixed(2);
          
          const remainingBytes = progEvent.total - bytesUploaded;
          const etaSeconds = speedBytesPerSecond > 0 ? Math.round(remainingBytes / speedBytesPerSecond) : 0;

          setZipUploadMetrics({
            speed: speedMB,
            eta: etaSeconds,
            currentFile: `Uploading... (${(bytesUploaded / (1024 * 1024)).toFixed(1)}MB / ${(progEvent.total / (1024 * 1024)).toFixed(1)}MB)`
          });
        }
      });

      const { session } = res.data;
      setZipOptimizationState('success');
      startLiveMonitoring(session.id);
    } catch (err) {
      setZipOptimizationState('error');
      setZipErrorSeverity('error');
      
      if (axios.isCancel(err)) {
        setZipErrorMessage('Upload cancelled by user.');
      } else if (err.code === 'ECONNABORTED') {
        setZipErrorMessage('Request Timeout: Upload took too long (limit exceeded 5 minutes).');
      } else if (!err.response) {
        setZipErrorMessage('Server Unreachable: Connection lost or backend service is offline.');
      } else if (err.response.status === 413) {
        setZipErrorMessage('ZIP file is too large. Remove node_modules, build files, or cache folders and try again.');
      } else {
        setZipErrorMessage(`Upload failed: ${err.response?.data?.error || err.message}`);
      }
    }
  };

  const handleCancelZipUpload = () => {
    if (zipCancelSourceRef.current) {
      zipCancelSourceRef.current.cancel('Upload aborted by user.');
    }
  };

  // 4. Resolve Credentials Pause Prompt
  const submitCredentialsResponse = async (e) => {
    e.preventDefault();
    if (!authRequest) return;
    try {
      await axios.post('/api/auth/session', {
        sessionId: authRequest.sessionId,
        username: credentialsForm.username,
        password: credentialsForm.password,
        role: credentialsForm.role
      });
      setAuthRequest(null);
    } catch (err) {
      alert(`Failed to submit authorization session: ${err.message}`);
    }
  };

  // 5. Resolve OTP Pause Prompt
  const submitOtpResponse = async (e) => {
    e.preventDefault();
    if (!authRequest) return;
    try {
      await axios.post('/api/auth/otp', {
        sessionId: authRequest.sessionId,
        otp: otpToken
      });
      setAuthRequest(null);
      setOtpToken('');
    } catch (err) {
      alert(`Failed to send OTP verification code: ${err.message}`);
    }
  };

  const handleApproveBug = async (sessionId, bugId) => {
    try {
      await axios.post(`/api/reports/${sessionId}/approve-bug/${bugId}`);
      // Refresh local UI
      viewSessionReport(sessionId);
      loadData();
    } catch (err) {
      console.error(err);
    }
  };

  const handleDeleteSession = async (sessionId) => {
    if (!confirm('Are you sure you want to delete this test session report?')) return;
    try {
      await axios.delete(`/api/reports/${sessionId}`);
      setSelectedSessionId(null);
      setCurrentSessionDetails(null);
      loadData();
      setActiveView('dashboard');
    } catch (err) {
      console.error(err);
    }
  };

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  const bgStyle = theme === 'dark' ? 'bg-[#0b0f19] text-slate-100' : 'bg-slate-50 text-slate-900';
  const cardStyle = theme === 'dark' ? 'bg-[#131926] border-slate-800' : 'bg-white border-slate-200';
  const inputStyle = theme === 'dark' ? 'bg-[#0b0f19] border-slate-800 focus:border-blue-500' : 'bg-slate-50 border-slate-300 focus:border-blue-600';
  const textMuted = theme === 'dark' ? 'text-slate-400' : 'text-slate-600';

  return (
    <div className={`flex h-screen overflow-hidden ${bgStyle} transition-colors duration-300`}>
      
      {/* ── SIDEBAR NAVIGATION ── */}
      <aside className={`hidden md:flex flex-col w-64 border-r shrink-0 ${theme === 'dark' ? 'bg-[#101622] border-slate-800' : 'bg-slate-100 border-slate-200'}`}>
        <div className="flex items-center gap-3 p-6 border-b border-inherit">
          <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-blue-500/10 text-blue-500">
            <Cpu className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <h1 className="font-extrabold text-sm tracking-wider uppercase">QA-Bot Engine</h1>
            <p className="text-[10px] text-blue-500 font-mono font-bold">Node.js Playwright</p>
          </div>
        </div>

        <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
          {[
            { id: 'dashboard', label: 'Dashboard Home', icon: Activity },
            { id: 'upload', label: 'Configure New Test', icon: UploadCloud },
            { id: 'monitor', label: 'Execution Monitor', icon: Terminal },
            { id: 'reports', label: 'Bug Reports Viewer', icon: Shield },
            { id: 'analytics', label: 'Bug Analytics', icon: Clock }
          ].map((item) => {
            const Icon = item.icon;
            const isActive = activeView === item.id;
            return (
              <button
                key={item.id}
                onClick={() => {
                  setActiveView(item.id);
                  if (item.id !== 'reports') {
                    setSelectedSessionId(null);
                  }
                }}
                className={`flex items-center gap-3 w-full px-4 py-2.5 rounded-lg text-xs font-semibold tracking-wide transition-all ${
                  isActive 
                    ? 'bg-blue-600/15 text-blue-500 border-l-4 border-blue-500' 
                    : `${textMuted} hover:bg-slate-800/40 hover:text-slate-200`
                }`}
              >
                <Icon className="w-4 h-4" />
                {item.label}
              </button>
            );
          })}
        </nav>

        <div className="p-4 border-t border-inherit flex items-center justify-between">
          <span className="text-[10px] text-slate-500 font-mono">v1.0.0 (Production)</span>
          <button 
            onClick={toggleTheme}
            className={`p-1.5 rounded-lg border border-inherit hover:bg-slate-800/40 transition`}
          >
            {theme === 'dark' ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-indigo-600" />}
          </button>
        </div>
      </aside>

      {/* ── MAIN CONTAINER ── */}
      <div className="flex flex-col flex-1 h-full overflow-hidden">
        
        {/* ── TOPBAR ── */}
        <header className={`flex items-center justify-between px-6 py-4 border-b ${theme === 'dark' ? 'bg-[#0f1522] border-slate-800' : 'bg-white border-slate-200'}`}>
          <h2 className="text-sm font-bold tracking-wider uppercase">
            {activeView.replace('_', ' ')}
          </h2>
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-bold bg-blue-500/10 text-blue-500">
              Host API: http://localhost:5000
            </span>
            {scanning && (
              <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-bold bg-amber-500/10 text-amber-500 animate-pulse">
                Active Scan Running
              </span>
            )}
          </div>
        </header>

        {/* ── CONTENT AREA ── */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeView}
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              transition={{ duration: 0.2 }}
              className="h-full space-y-6"
            >
              
              {/* ──────────────────────────────────────────────────
                  1. DASHBOARD HOME
              ────────────────────────────────────────────────── */}
              {activeView === 'dashboard' && (
                <div className="space-y-6">
                  {/* Summary Metric Cards */}
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                    {[
                      { title: 'Total Projects', val: analytics?.summary.totalProjects ?? 0, desc: 'Configured URLs/ZIP archives', icon: Layers, color: 'text-blue-500', bg: 'bg-blue-500/10' },
                      { title: 'Test Runs', val: analytics?.summary.totalSessions ?? 0, desc: 'Execution session history', icon: Clock, color: 'text-indigo-500', bg: 'bg-indigo-500/10' },
                      { title: 'Bugs Detected', val: analytics?.summary.totalBugs ?? 0, desc: 'Total caught by crawler', icon: AlertTriangle, color: 'text-amber-500', bg: 'bg-amber-500/10' },
                      { title: 'Approved Bugs', val: analytics?.summary.approvedBugs ?? 0, desc: 'Flagged for dev reviews', icon: CheckCircle, color: 'text-emerald-500', bg: 'bg-emerald-500/10' }
                    ].map((m, idx) => {
                      const Icon = m.icon;
                      return (
                        <div key={idx} className={`p-5 rounded-xl border ${cardStyle} space-y-3`}>
                          <div className="flex items-center justify-between">
                            <span className="text-[10px] font-bold text-slate-500 uppercase">{m.title}</span>
                            <div className={`p-2 rounded-lg ${m.bg} ${m.color}`}>
                              <Icon className="w-5 h-5" />
                            </div>
                          </div>
                          <div className="space-y-1">
                            <h3 className="text-2xl font-bold tracking-tight">{m.val}</h3>
                            <p className="text-[10px] text-slate-500">{m.desc}</p>
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {/* Scans List Table */}
                  <div className={`p-6 rounded-xl border ${cardStyle} space-y-4`}>
                    <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Recent Executions</h3>
                    <div className="overflow-x-auto">
                      <table className="w-full text-left border-collapse text-xs">
                        <thead>
                          <tr className="border-b border-inherit text-slate-500 uppercase font-mono">
                            <th className="py-3 px-4">Session ID</th>
                            <th className="py-3 px-4">Project Name</th>
                            <th className="py-3 px-4">Source Type</th>
                            <th className="py-3 px-4">Status</th>
                            <th className="py-3 px-4">Pages Tested</th>
                            <th className="py-3 px-4">Bugs</th>
                            <th className="py-3 px-4 text-right">Actions</th>
                          </tr>
                        </thead>
                        <tbody>
                          {reports.map((s) => (
                            <tr key={s.id} className="border-b border-slate-800/40 hover:bg-slate-800/20">
                              <td className="py-3 px-4 font-mono font-bold text-blue-500">{s.id.substring(0, 8)}...</td>
                              <td className="py-3 px-4 font-bold">{s.Project?.name}</td>
                              <td className="py-3 px-4">
                                <span className="px-2 py-0.5 rounded bg-slate-800 text-[10px] font-mono font-bold text-slate-400">
                                  {s.Project?.sourceType.toUpperCase()}
                                </span>
                              </td>
                              <td className="py-3 px-4">
                                <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold ${
                                  s.status === 'COMPLETED' ? 'bg-emerald-500/10 text-emerald-500' :
                                  s.status === 'RUNNING' ? 'bg-blue-500/10 text-blue-500 animate-pulse' :
                                  s.status === 'FAILED' ? 'bg-red-500/10 text-red-500' : 'bg-slate-700/30 text-slate-400'
                                }`}>
                                  {s.status}
                                </span>
                              </td>
                              <td className="py-3 px-4">{s.totalPages} pages</td>
                              <td className="py-3 px-4 font-bold text-amber-500">{s.totalBugs} bugs</td>
                              <td className="py-3 px-4 text-right space-x-2">
                                <button 
                                  onClick={() => viewSessionReport(s.id)}
                                  className="px-2.5 py-1 text-[10px] font-bold bg-blue-600 hover:bg-blue-500 text-white rounded transition"
                                >
                                  View Report
                                </button>
                                <button 
                                  onClick={() => handleDeleteSession(s.id)}
                                  className="p-1 text-[10px] text-red-500 hover:bg-red-500/10 rounded transition"
                                >
                                  <Trash2 className="w-4 h-4" />
                                </button>
                              </td>
                            </tr>
                          ))}
                          {reports.length === 0 && (
                            <tr>
                              <td colSpan="7" className="py-8 text-center text-slate-500 font-mono">No scans executed yet. Click "Configure New Test" to begin.</td>
                            </tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}

              {/* ──────────────────────────────────────────────────
                  2. CONFIGURE NEW TEST
              ────────────────────────────────────────────────── */}
              {activeView === 'upload' && (
                <div className="max-w-2xl mx-auto space-y-6">
                  <div className={`p-6 rounded-xl border ${cardStyle} space-y-6`}>
                    <div className="space-y-2">
                      <h3 className="text-base font-bold">Deploy and Test QA Session</h3>
                      <p className={`text-xs ${textMuted}`}>Select your source model input type, configure scope parameters, and start testing:</p>
                    </div>

                    {/* Mode Selector Tabs */}
                    <div className="flex border-b border-inherit">
                      {[
                        { id: 'url', label: 'By URL' },
                        { id: 'folder', label: 'Upload Folder' },
                        { id: 'zip', label: 'Upload ZIP' }
                      ].map((t) => (
                        <button
                          key={t.id}
                          onClick={() => setUploadTab(t.id)}
                          className={`px-5 py-2.5 text-xs font-bold transition-all border-b-2 ${
                            uploadTab === t.id 
                              ? 'border-blue-500 text-blue-500' 
                              : 'border-transparent text-slate-500 hover:text-slate-300'
                          }`}
                        >
                          {t.label}
                        </button>
                      ))}
                    </div>

                    {/* Form elements */}
                    {uploadTab === 'url' && (
                      <form onSubmit={handleUrlScanSubmit} className="space-y-4 text-xs">
                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <label className="font-bold uppercase tracking-wider block">Project Alias/Name</label>
                            <input 
                              type="text" 
                              value={projectName}
                              onChange={(e) => setProjectName(e.target.value)}
                              placeholder="My Landing Page"
                              className={`w-full px-4 py-2.5 rounded-lg border focus:outline-none ${inputStyle}`}
                            />
                          </div>
                          <div className="space-y-2">
                            <label className="font-bold uppercase tracking-wider block">Target Endpoint URL</label>
                            <input 
                              type="url" 
                              required
                              value={targetUrl}
                              onChange={(e) => setTargetUrl(e.target.value)}
                              placeholder="https://example.com"
                              className={`w-full px-4 py-2.5 rounded-lg border focus:outline-none font-mono ${inputStyle}`}
                            />
                          </div>
                        </div>

                        {submitError && (
                          <div className="p-3.5 rounded-lg border border-red-500/20 bg-red-500/10 text-red-500 font-medium">
                            ⚠️ {submitError}
                          </div>
                        )}

                        <button 
                          type="submit"
                          disabled={scanning || isUrlSubmitting}
                          className="flex items-center justify-center gap-2 w-full px-4 py-3 rounded-lg font-bold bg-blue-600 hover:bg-blue-500 text-white transition disabled:bg-slate-800 disabled:text-slate-600"
                        >
                          {isUrlSubmitting ? (
                            <>
                              <RefreshCw className="w-4 h-4 animate-spin" /> Submitting Request...
                            </>
                          ) : (
                            <>
                              <Play className="w-4 h-4" /> Start Automated Test Run
                            </>
                          )}
                        </button>
                      </form>
                    )}

                    {uploadTab === 'folder' && (
                      <form onSubmit={handleFolderUploadSubmit} className="space-y-4 text-xs">
                        <div className="space-y-2">
                          <label className="font-bold uppercase tracking-wider block">Project Alias/Name</label>
                          <input 
                            type="text" 
                            value={folderName}
                            onChange={(e) => setFolderName(e.target.value)}
                            placeholder="My Local Project Folder"
                            className={`w-full px-4 py-2.5 rounded-lg border focus:outline-none ${inputStyle}`}
                          />
                        </div>

                        <div className="space-y-2">
                          <label className="font-bold uppercase tracking-wider block">Select Directory Folder</label>
                          <div className={`p-8 border-2 border-dashed rounded-lg text-center cursor-pointer hover:border-blue-500 transition ${theme === 'dark' ? 'bg-[#0b0f19] border-slate-800' : 'bg-slate-50 border-slate-300'}`}>
                            <input
                              type="file"
                              webkitdirectory=""
                              directory=""
                              multiple
                              onChange={handleFolderUploadChange}
                              className="hidden"
                              id="folder-upload-input"
                            />
                            <label htmlFor="folder-upload-input" className="cursor-pointer space-y-2 block">
                              <UploadCloud className="w-8 h-8 text-slate-400 mx-auto" />
                              <span className="block text-slate-300 font-bold">Click to choose directory folder</span>
                              <span className="block text-[10px] text-slate-500">Filters node_modules, git, build outputs automatically</span>
                            </label>
                          </div>
                          
                          {/* Folder stats panel */}
                          {rawFolderFilesCount > 0 && (
                            <div className="p-4 rounded-lg bg-black/40 border border-slate-800 space-y-3 mt-2 leading-relaxed">
                              <h4 className="font-bold text-slate-300">Selected Folder Stats:</h4>
                              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 font-mono text-[10px] text-slate-400">
                                <div>Total Files: <strong className="text-white">{rawFolderFilesCount}</strong></div>
                                <div>Uploadable Files: <strong className="text-emerald-400">{folderFiles.length}</strong></div>
                                <div>Ignored Files: <strong className="text-amber-500">{ignoredFilesCount}</strong></div>
                                <div>Estimated Size: <strong className="text-blue-400">{(estimatedFolderSize / (1024 * 1024)).toFixed(2)} MB</strong></div>
                              </div>
                              {ignoredFoldersList.length > 0 && (
                                <div className="text-[9px] text-slate-500">
                                  Ignored folders: {ignoredFoldersList.map((f, i) => (
                                    <span key={i} className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 font-bold mr-1.5">{f}</span>
                                  ))}
                                </div>
                              )}
                              
                              {/* Smart recommendations */}
                              {(estimatedFolderSize > 25 * 1024 * 1024 || rawFolderFilesCount > 1500) && (
                                <div className="p-2.5 rounded bg-blue-500/5 border border-blue-500/10 text-[10px] text-blue-400 space-y-1">
                                  <span className="font-bold text-slate-300">💡 Smart Recommendation:</span>
                                  <p className="text-slate-400 leading-normal mt-1">
                                    This project is large ({rawFolderFilesCount} files, ${(estimatedFolderSize / (1024 * 1024)).toFixed(1)}MB). 
                                    To speed up local compression and ensure stable transfers, we recommend:
                                    <ul className="list-disc list-inside mt-1 space-y-0.5">
                                      <li>Uploading as a pre-packaged **ZIP file** instead.</li>
                                      <li>Double-checking if you have deleted local **node_modules** or **build** folders before selection.</li>
                                    </ul>
                                  </p>
                                </div>
                              )}
                            </div>
                          )}
                        </div>

                        {/* Error messages boundary */}
                        {uploadErrorMessage && (
                          <div className={`p-3 rounded-lg border flex items-center justify-between ${
                            uploadErrorSeverity === 'error' 
                              ? 'bg-red-500/10 border-red-500/20 text-red-400' 
                              : 'bg-amber-500/10 border-amber-500/20 text-amber-500'
                          }`}>
                            <span className="leading-normal">{uploadErrorMessage}</span>
                            {compressionState === 'error' && (
                              <button
                                type="button"
                                onClick={handleFolderUploadSubmit}
                                className="px-2.5 py-1 text-[10px] bg-red-500 hover:bg-red-600 text-white rounded font-bold transition ml-2 shrink-0"
                              >
                                Retry Upload
                              </button>
                            )}
                          </div>
                        )}

                        {/* Compress / Upload State Bar */}
                        {compressionState === 'compressing' && (
                          <div className="space-y-2 p-3 rounded-lg bg-blue-500/5 border border-blue-500/10">
                            <div className="flex justify-between text-[10px] font-mono text-blue-400">
                              <span>{uploadMetrics.currentFile || 'Compressing folder files in browser...'}</span>
                              <span>{compressionProgress}%</span>
                            </div>
                            <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                              <div className="bg-blue-500 h-full transition-all duration-200" style={{ width: `${compressionProgress}%` }}></div>
                            </div>
                          </div>
                        )}

                        {compressionState === 'uploading' && (
                          <div className="space-y-2.5 p-3 rounded-lg bg-blue-500/5 border border-blue-500/10">
                            <div className="flex justify-between text-[10px] font-mono text-blue-400">
                              <span className="truncate max-w-[250px]">{uploadMetrics.currentFile}</span>
                              <span>{uploadPercentage}%</span>
                            </div>
                            <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                              <div className="bg-blue-500 h-full transition-all duration-200" style={{ width: `${uploadPercentage}%` }}></div>
                            </div>
                            <div className="flex justify-between text-[9px] text-slate-500 font-mono">
                              <span>Speed: <strong className="text-slate-300">{uploadMetrics.speed} MB/s</strong></span>
                              <span>Remaining: <strong className="text-slate-300">{uploadMetrics.eta}s</strong></span>
                              <button 
                                type="button" 
                                onClick={handleCancelUpload}
                                className="text-red-400 hover:underline font-bold"
                              >
                                Cancel
                              </button>
                            </div>
                          </div>
                        )}

                        <button 
                          type="submit"
                          disabled={scanning || folderFiles.length === 0 || compressionState === 'compressing' || compressionState === 'uploading'}
                          className="flex items-center justify-center gap-2 w-full px-4 py-3 rounded-lg font-bold bg-blue-600 hover:bg-blue-500 text-white transition disabled:bg-slate-800 disabled:text-slate-600"
                        >
                          <Play className="w-4 h-4" /> 
                          {compressionState === 'compressing' ? 'Compressing Project...' : 
                           compressionState === 'uploading' ? 'Uploading Archive...' : 
                           'Upload Folder and Start Test'}
                        </button>
                      </form>
                    )}

                    {uploadTab === 'zip' && (
                      <form onSubmit={handleZipUploadSubmit} className="space-y-4 text-xs">
                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <label className="font-bold uppercase tracking-wider block">Project Alias/Name</label>
                            <input 
                              type="text" 
                              value={projectName}
                              onChange={(e) => setProjectName(e.target.value)}
                              placeholder="My ZIP Archive"
                              className={`w-full px-4 py-2.5 rounded-lg border focus:outline-none ${inputStyle}`}
                            />
                          </div>
                          
                          <div className="space-y-2">
                            <label className="font-bold uppercase tracking-wider block">Select Zip file</label>
                            <div className={`p-8 border-2 border-dashed rounded-lg text-center cursor-pointer hover:border-blue-500 transition ${theme === 'dark' ? 'bg-[#0b0f19] border-slate-800' : 'bg-slate-50 border-slate-300'}`}>
                              <input
                                type="file"
                                accept=".zip"
                                onChange={handleZipFileChange}
                                className="hidden"
                                id="zip-upload-input"
                              />
                              <label htmlFor="zip-upload-input" className="cursor-pointer space-y-2 block">
                                <UploadCloud className="w-8 h-8 text-slate-400 mx-auto" />
                                <span className="block text-slate-300 font-bold">
                                  {zipFileName ? zipFileName : 'Click to choose ZIP archive'}
                                </span>
                                <span className="block text-[10px] text-slate-500">
                                  Strips node_modules, build artifacts, and dangerous scripts in-browser
                                </span>
                              </label>
                            </div>
                          </div>
                        </div>

                        {/* ZIP stats panel */}
                        {originalZipSize > 0 && zipOptimizationState !== 'optimizing' && (
                          <div className="p-4 rounded-lg bg-black/40 border border-slate-800 space-y-3 mt-2 leading-relaxed">
                            <h4 className="font-bold text-slate-300">ZIP Optimization Stats:</h4>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 font-mono text-[10px] text-slate-400">
                              <div>Original Size: <strong className="text-white">{(originalZipSize / (1024 * 1024)).toFixed(2)} MB</strong></div>
                              <div>Optimized Size: <strong className="text-emerald-400">{(optimizedZipSize / (1024 * 1024)).toFixed(2)} MB</strong></div>
                              <div>
                                Space Saved: {' '}
                                <strong className="text-blue-400">
                                  {originalZipSize > 0 
                                    ? (((originalZipSize - optimizedZipSize) / originalZipSize) * 100).toFixed(1)
                                    : '0.0'
                                  }%
                                </strong>
                              </div>
                              <div>Uploadable Files: <strong className="text-emerald-400">{zipAllowedFilesCount}</strong></div>
                            </div>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 font-mono text-[10px] text-slate-400 pt-1">
                              <div>Total Original Files: <strong className="text-slate-300">{zipTotalFilesCount}</strong></div>
                              <div>Ignored Files: <strong className="text-amber-500">{zipIgnoredFilesCount}</strong></div>
                            </div>
                            {zipIgnoredFoldersList.length > 0 && (
                              <div className="text-[9px] text-slate-500">
                                Ignored folders: {zipIgnoredFoldersList.map((f, i) => (
                                  <span key={i} className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 font-bold mr-1.5">{f}</span>
                                ))}
                              </div>
                            )}
                            
                            {/* Smart recommendations */}
                            {(optimizedZipSize > 100 * 1024 * 1024) && (
                              <div className="p-2.5 rounded bg-blue-500/5 border border-blue-500/10 text-[10px] text-blue-400 space-y-1">
                                <span className="font-bold text-slate-300">💡 Smart Recommendation:</span>
                                <p className="text-slate-400 leading-normal mt-1">
                                  Even after optimization, this archive is quite large ({(optimizedZipSize / (1024 * 1024)).toFixed(1)}MB). 
                                  If upload issues occur, double check that any local database dumps, assets, or media have been removed.
                                </p>
                              </div>
                            )}
                          </div>
                        )}

                        {/* Error and Warning Messages Boundary */}
                        {zipErrorMessage && (
                          <div className={`p-3 rounded-lg border flex items-center justify-between ${
                            zipErrorSeverity === 'error' 
                              ? 'bg-red-500/10 border-red-500/20 text-red-400' 
                              : 'bg-amber-500/10 border-amber-500/20 text-amber-500'
                          }`}>
                            <span className="leading-normal">{zipErrorMessage}</span>
                            {zipOptimizationState === 'error' && zipFile && (
                              <button
                                type="button"
                                onClick={handleZipUploadSubmit}
                                className="px-2.5 py-1 text-[10px] bg-red-500 hover:bg-red-600 text-white rounded font-bold transition ml-2 shrink-0"
                              >
                                Retry Upload
                              </button>
                            )}
                          </div>
                        )}

                        {/* Three-Tier Progress Indicators */}
                        
                        {/* 1. In-browser ZIP Optimization */}
                        {zipOptimizationState === 'optimizing' && (
                          <div className="space-y-2 p-3 rounded-lg bg-blue-500/5 border border-blue-500/10">
                            <div className="flex justify-between text-[10px] font-mono text-blue-400">
                              <span>Analyzing and optimizing ZIP archive in browser...</span>
                              <span>{zipOptimizationProgress}%</span>
                            </div>
                            <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                              <div className="bg-blue-500 h-full transition-all duration-200" style={{ width: `${zipOptimizationProgress}%` }}></div>
                            </div>
                          </div>
                        )}

                        {/* 2. File Uploading */}
                        {zipOptimizationState === 'uploading' && uploadPercentage < 100 && (
                          <div className="space-y-2.5 p-3 rounded-lg bg-blue-500/5 border border-blue-500/10">
                            <div className="flex justify-between text-[10px] font-mono text-blue-400">
                              <span className="truncate max-w-[250px]">{zipUploadMetrics.currentFile}</span>
                              <span>{uploadPercentage}%</span>
                            </div>
                            <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                              <div className="bg-blue-500 h-full transition-all duration-200" style={{ width: `${uploadPercentage}%` }}></div>
                            </div>
                            <div className="flex justify-between text-[9px] text-slate-500 font-mono">
                              <span>Speed: <strong className="text-slate-300">{zipUploadMetrics.speed} MB/s</strong></span>
                              <span>Remaining: <strong className="text-slate-300">{zipUploadMetrics.eta}s</strong></span>
                              <button 
                                type="button" 
                                onClick={handleCancelZipUpload}
                                className="text-red-400 hover:underline font-bold"
                              >
                                Cancel
                              </button>
                            </div>
                          </div>
                        )}

                        {/* 3. Server-side Extraction & Scanning */}
                        {zipOptimizationState === 'uploading' && uploadPercentage === 100 && (
                          <div className="space-y-2.5 p-3 rounded-lg bg-emerald-500/5 border border-emerald-500/10">
                            <div className="flex justify-between text-[10px] font-mono text-emerald-400">
                              <span className="truncate max-w-[250px]">{zipUploadMetrics.currentFile || 'Server extracting ZIP archive...'}</span>
                              <span>{zipExtractionPercentage}%</span>
                            </div>
                            <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                              <div className="bg-emerald-500 h-full transition-all duration-200" style={{ width: `${zipExtractionPercentage}%` }}></div>
                            </div>
                            <div className="text-[9px] text-slate-500 font-mono">
                              <span>Upload complete. Decompressing files safely on node endpoint...</span>
                            </div>
                          </div>
                        )}

                        <button 
                          type="submit"
                          disabled={scanning || !zipFile || zipOptimizationState === 'optimizing' || zipOptimizationState === 'uploading'}
                          className="flex items-center justify-center gap-2 w-full px-4 py-3 rounded-lg font-bold bg-blue-600 hover:bg-blue-500 text-white transition disabled:bg-slate-800 disabled:text-slate-600"
                        >
                          <Play className="w-4 h-4" /> 
                          {zipOptimizationState === 'optimizing' ? 'Optimizing ZIP...' : 
                           zipOptimizationState === 'uploading' ? (uploadPercentage < 100 ? 'Uploading ZIP...' : 'Extracting ZIP on server...') : 
                           'Upload ZIP and Unpack'}
                        </button>
                      </form>
                    )}
                  </div>
                </div>
              )}

              {/* ──────────────────────────────────────────────────
                  3. LIVE EXECUTION MONITOR
              ────────────────────────────────────────────────── */}
              {activeView === 'monitor' && (
                <div className="grid lg:grid-cols-3 gap-6">
                  
                  {/* Logs terminal */}
                  <div className={`lg:col-span-2 p-6 rounded-xl border ${cardStyle} space-y-4`}>
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-sm font-bold uppercase">Real-Time Engine Logs</h3>
                        <p className="text-xs text-slate-500">Streaming Playwright browser automation trace outputs:</p>
                      </div>
                      <div className="flex items-center gap-2 text-xs">
                        <span className="font-mono text-slate-400">Session: #{activeSessionId?.substring(0, 8)}...</span>
                      </div>
                    </div>

                    {/* Progress details */}
                    <div className="grid grid-cols-3 gap-3 text-center text-xs py-3 border-y border-inherit">
                      <div>
                        <span className="text-[10px] text-slate-500 uppercase block">Percentage</span>
                        <span className="font-bold text-blue-500 text-lg">{liveProgress.percentage}%</span>
                      </div>
                      <div>
                        <span className="text-[10px] text-slate-500 uppercase block">Pages Crawled</span>
                        <span className="font-bold text-white text-lg">{liveProgress.pagesCrawled}</span>
                      </div>
                      <div>
                        <span className="text-[10px] text-slate-500 uppercase block">Bugs Caught</span>
                        <span className="font-bold text-red-500 text-lg">{liveProgress.totalBugs}</span>
                      </div>
                    </div>

                    <div className="p-5 rounded-lg bg-black border border-slate-900 font-mono text-xs text-slate-400 min-h-[300px] max-h-[350px] overflow-y-auto space-y-2">
                      {liveLogs.map((log, idx) => (
                        <div key={idx} className={
                          log.level === 'SUCCESS' ? 'text-emerald-400 font-bold' :
                          log.level === 'ERROR' ? 'text-red-400' :
                          log.level === 'WARN' ? 'text-amber-400' : 'text-slate-400'
                        }>
                          [{new Date(log.timestamp).toLocaleTimeString()}] [{log.level}] {log.message}
                        </div>
                      ))}
                      <div ref={logTerminalEndRef} />
                    </div>
                  </div>

                  {/* Bugs detected list */}
                  <div className={`p-6 rounded-xl border ${cardStyle} space-y-4`}>
                    <h3 className="text-sm font-bold uppercase">Live Caught Bugs</h3>
                    <div className="space-y-3 max-h-[420px] overflow-y-auto pr-1">
                      {detectedBugs.map((bug, idx) => (
                        <div key={idx} className="p-3 rounded-lg bg-red-500/5 border border-red-500/20 space-y-1">
                          <div className="flex justify-between items-start">
                            <span className="font-bold text-xs text-white">{bug.title}</span>
                            <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-red-500/10 text-red-500 uppercase">{bug.severity}</span>
                          </div>
                          <p className="text-[10px] text-slate-500 font-mono truncate">{bug.pageUrl}</p>
                        </div>
                      ))}
                      {detectedBugs.length === 0 && (
                        <p className="text-slate-500 text-xs text-center py-12">Waiting for bugs to be detected...</p>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* ──────────────────────────────────────────────────
                  4. DETAILED REPORT VIEWER
              ────────────────────────────────────────────────── */}
              {activeView === 'reports' && (
                <div className="space-y-6">
                  {selectedSessionId && currentSessionDetails ? (
                    <div className="space-y-6">
                      {/* Session Header */}
                      <div className={`p-6 rounded-xl border ${cardStyle} flex flex-wrap justify-between items-center gap-4`}>
                        <div className="space-y-1">
                          <span className="text-[10px] font-bold text-slate-500 uppercase">Interactive Session Report</span>
                          <h2 className="text-base font-bold font-mono text-blue-500">{currentSessionDetails.Project?.name}</h2>
                          <span className="text-[10px] text-slate-400 block font-mono">
                            Type: {currentSessionDetails.Project?.sourceType.toUpperCase()} | Path: {currentSessionDetails.Project?.sourcePath}
                          </span>
                        </div>
                        <div className="flex gap-2">
                          <a 
                            href={`/api/reports/${selectedSessionId}/pdf`}
                            download
                            className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-white rounded font-bold transition"
                          >
                            <Download className="w-4 h-4" /> Download PDF Report
                          </a>
                          <button 
                            onClick={() => setActiveView('dashboard')}
                            className="px-3 py-1.5 text-xs bg-blue-600 hover:bg-blue-500 text-white rounded font-bold transition"
                          >
                            Back to Dashboard
                          </button>
                        </div>
                      </div>

                      {/* Bugs Details Grid */}
                      <div className="grid lg:grid-cols-3 gap-6">
                        
                        {/* Bugs List */}
                        <div className={`lg:col-span-2 p-6 rounded-xl border ${cardStyle} space-y-4`}>
                          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Anomalies Detected</h3>
                          <div className="space-y-4">
                            {currentSessionDetails.Reports?.map((bug) => (
                              <div key={bug.id} className="p-4 rounded-xl border border-slate-800 bg-[#0e1420]/40 space-y-3">
                                <div className="flex justify-between items-start flex-wrap gap-2">
                                  <div>
                                    <h4 className="text-sm font-bold text-white flex items-center gap-2">
                                      <span className="w-2 h-2 rounded-full" style={{ backgroundColor: SEV_COLORS[bug.severity] }}></span>
                                      {bug.title}
                                    </h4>
                                    <span className="text-[10px] text-slate-500 font-mono block mt-1 break-all">{bug.pageUrl}</span>
                                  </div>
                                  <div className="flex items-center gap-2">
                                    <span className="px-2 py-0.5 rounded text-[9px] font-bold uppercase bg-slate-800 text-blue-500 font-mono">
                                      {bug.category}
                                    </span>
                                    <span className="px-2 py-0.5 rounded text-[9px] font-bold uppercase" style={{ backgroundColor: `${SEV_COLORS[bug.severity]}20`, color: SEV_COLORS[bug.severity] }}>
                                      {bug.severity}
                                    </span>
                                    {bug.screenshotPath && (
                                      <button
                                        onClick={() => {
                                          setCompareModalBug(bug);
                                          setCompareMode('slider');
                                        }}
                                        className="flex items-center gap-1 px-2 py-0.5 rounded text-[9px] font-bold uppercase bg-blue-600/10 hover:bg-blue-600/20 text-blue-400 transition"
                                      >
                                        <ImageIcon className="w-3 h-3" /> Compare Views
                                      </button>
                                    )}
                                  </div>
                                </div>

                                <div className="grid md:grid-cols-2 gap-4 text-xs leading-relaxed text-slate-400 pt-2 border-t border-slate-800/40">
                                  <div>
                                    <strong className="text-slate-300 block mb-1">Issue Description:</strong>
                                    {bug.description}
                                  </div>
                                  <div>
                                    <strong className="text-slate-300 block mb-1">Diagnosed Root Cause:</strong>
                                    {bug.rootCause}
                                  </div>
                                </div>

                                <div className="text-xs leading-relaxed text-slate-400">
                                  <strong className="text-slate-300 block mb-1">Suggested Developer Fix:</strong>
                                  <code className="p-2 rounded bg-black/60 border border-slate-800/60 block font-mono text-emerald-400 text-[10px]">
                                    {bug.suggestedFix}
                                  </code>
                                </div>

                                <div className="text-xs text-slate-400">
                                  <strong className="text-slate-300 block mb-1">Steps to Reproduce:</strong>
                                  <pre className="p-2 rounded bg-black/40 border border-slate-800/40 font-mono text-[9px] leading-normal text-slate-500 block">
                                    {bug.stepsToReproduce}
                                  </pre>
                                </div>

                                {/* Bug approval toggle */}
                                <div className="flex justify-between items-center pt-2 border-t border-slate-800/40">
                                  <span className="text-[10px] text-slate-600 font-mono">
                                    Browser: {bug.browserInfo} ({bug.deviceType})
                                  </span>
                                  {bug.approved ? (
                                    <span className="flex items-center gap-1 text-emerald-500 text-xs font-bold">
                                      <CheckCircle className="w-4 h-4" /> Dispatched to Jira/Slack
                                    </span>
                                  ) : (
                                    <button
                                      onClick={() => handleApproveBug(selectedSessionId, bug.id)}
                                      className="px-3 py-1 bg-blue-600 hover:bg-blue-500 text-white rounded font-bold text-[10px] transition"
                                    >
                                      Approve and Alert Devs
                                    </button>
                                  )}
                                </div>
                              </div>
                            ))}

                            {currentSessionDetails.Reports?.length === 0 && (
                              <p className="text-slate-500 font-mono text-center py-12 text-xs">No bugs detected in this test execution.</p>
                            )}
                          </div>
                        </div>

                        {/* Screenshots gallery & logs panel */}
                        <div className="space-y-6">
                          <div className={`p-6 rounded-xl border ${cardStyle} space-y-4`}>
                            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Failure Screenshot Gallery</h3>
                            <div className="grid grid-cols-1 gap-4">
                              {currentSessionDetails.Reports?.map((bug) => {
                                if (!bug.screenshotPath) return null;
                                const currentTab = screenshotTabs[bug.id] || 'annotated';
                                const displaySrc = currentTab === 'annotated' ? (bug.annotatedScreenshotPath || bug.screenshotPath) : bug.screenshotPath;
                                
                                return (
                                  <div key={bug.id} className="p-3 rounded-lg border border-slate-800 bg-[#0b0f19] space-y-3">
                                    {/* Header of screenshot card: Title and Tabs */}
                                    <div className="flex justify-between items-center gap-2">
                                      <span className="text-[10px] font-bold block text-slate-300 truncate max-w-[120px]" title={bug.title}>
                                        {bug.title}
                                      </span>
                                      <div className="flex rounded-md bg-slate-850 p-0.5 border border-slate-700/50">
                                        <button
                                          onClick={() => setScreenshotTabs(prev => ({ ...prev, [bug.id]: 'annotated' }))}
                                          className={`px-2 py-0.5 rounded text-[9px] font-bold transition-all ${
                                            currentTab === 'annotated'
                                              ? 'bg-blue-600 text-white shadow-sm'
                                              : 'text-slate-400 hover:text-slate-200'
                                          }`}
                                        >
                                          Annotated
                                        </button>
                                        <button
                                          onClick={() => setScreenshotTabs(prev => ({ ...prev, [bug.id]: 'original' }))}
                                          className={`px-2 py-0.5 rounded text-[9px] font-bold transition-all ${
                                            currentTab === 'original'
                                              ? 'bg-blue-600 text-white shadow-sm'
                                              : 'text-slate-400 hover:text-slate-200'
                                          }`}
                                        >
                                          Original
                                        </button>
                                      </div>
                                    </div>

                                    {/* Image container */}
                                    <div className="relative aspect-video rounded overflow-hidden bg-black flex items-center justify-center border border-slate-850 group">
                                      <img 
                                        src={displaySrc} 
                                        alt={bug.title} 
                                        className="max-h-full max-w-full object-contain"
                                      />
                                      
                                      {/* Quick action hover overlay */}
                                      <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-3">
                                        <button
                                          onClick={() => {
                                            setZoomModalImage({ src: displaySrc, title: bug.title });
                                          }}
                                          title="Zoom Fullscreen"
                                          className="p-2 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-white transition transform translate-y-2 group-hover:translate-y-0 duration-200"
                                        >
                                          <Eye className="w-4 h-4" />
                                        </button>
                                        <button
                                          onClick={() => {
                                            setCompareModalBug(bug);
                                            setCompareMode('slider');
                                          }}
                                          title="Compare Screenshots"
                                          className="p-2 rounded-lg bg-blue-600/80 hover:bg-blue-500 text-white transition transform translate-y-2 group-hover:translate-y-0 duration-200"
                                        >
                                          <Layers className="w-4 h-4" />
                                        </button>
                                      </div>
                                    </div>
                                    
                                    {/* Bottom controls summary */}
                                    <div className="flex justify-between items-center text-[9px] text-slate-500">
                                      <span>Category: {bug.category}</span>
                                      <button
                                        onClick={() => {
                                          setCompareModalBug(bug);
                                          setCompareMode('slider');
                                        }}
                                        className="text-blue-400 hover:underline flex items-center gap-1 font-semibold"
                                      >
                                        <Layers className="w-3 h-3" /> Compare Views
                                      </button>
                                    </div>
                                  </div>
                                );
                              })}
                              {!currentSessionDetails.Reports?.some(b => b.screenshotPath) && (
                                <p className="text-slate-600 text-xs text-center py-12 font-mono">No screenshot files recorded.</p>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-6">
                      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                        <div>
                          <h3 className="text-base font-bold">Bug Reports Explorer</h3>
                          <p className={`text-xs ${textMuted}`}>Select from previous or recently generated test session reports below:</p>
                        </div>
                      </div>

                      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {reports.map((s) => (
                          <div key={s.id} className={`p-5 rounded-xl border ${cardStyle} flex flex-col justify-between space-y-4 hover:border-blue-500/30 transition-all`}>
                            <div className="space-y-2">
                              <div className="flex items-start justify-between gap-2">
                                <h4 className="text-sm font-bold truncate max-w-[180px] text-white" title={s.Project?.name}>
                                  {s.Project?.name}
                                </h4>
                                <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold ${
                                  s.status === 'COMPLETED' ? 'bg-emerald-500/10 text-emerald-500' :
                                  s.status === 'RUNNING' ? 'bg-blue-500/10 text-blue-500 animate-pulse' :
                                  s.status === 'FAILED' ? 'bg-red-500/10 text-red-500' : 'bg-slate-700/30 text-slate-400'
                                }`}>
                                  {s.status}
                                </span>
                              </div>
                              <p className={`text-[10px] font-mono truncate ${textMuted}`} title={s.Project?.sourcePath}>
                                {s.Project?.sourcePath}
                              </p>
                              <div className="flex gap-2">
                                <span className="px-1.5 py-0.5 rounded bg-slate-800/60 text-[9px] font-mono text-slate-400 border border-slate-700/30">
                                  {s.Project?.sourceType.toUpperCase()}
                                </span>
                                <span className="px-1.5 py-0.5 rounded bg-slate-800/60 text-[9px] font-mono text-slate-400 border border-slate-700/30">
                                  ID: {s.id.substring(0, 8)}
                                </span>
                              </div>
                            </div>

                            <div className="grid grid-cols-2 gap-2 py-2.5 border-y border-slate-800/30 text-[10px] text-slate-400 font-mono">
                              <div>Pages: <strong className="text-white">{s.totalPages}</strong></div>
                              <div>Bugs: <strong className={s.totalBugs > 0 ? "text-amber-500 font-bold" : "text-emerald-400"}>{s.totalBugs}</strong></div>
                              <div className="col-span-2 text-[9px] text-slate-500 mt-1">
                                Ran: {new Date(s.createdAt).toLocaleString()}
                              </div>
                            </div>

                            <div className="flex items-center justify-between gap-2 pt-2">
                              <button 
                                onClick={() => viewSessionReport(s.id)}
                                className="flex-1 py-2 text-xs font-bold bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition text-center"
                              >
                                View Detailed Report
                              </button>
                              <button 
                                onClick={() => handleDeleteSession(s.id)}
                                className="p-2 text-red-500 hover:bg-red-500/10 rounded-lg border border-transparent hover:border-red-500/20 transition"
                                title="Delete Session Report"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          </div>
                        ))}
                        {reports.length === 0 && (
                          <div className="col-span-full py-12 text-center text-slate-500 font-mono border border-dashed rounded-xl">
                            No session reports recorded yet. Click "Configure New Test" to begin.
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* ──────────────────────────────────────────────────
                  5. BUG ANALYTICS
              ────────────────────────────────────────────────── */}
              {activeView === 'analytics' && (
                <div className="grid lg:grid-cols-2 gap-6">
                  
                  {/* Severity Breakdown */}
                  <div className={`p-6 rounded-xl border ${cardStyle} space-y-4 flex flex-col justify-between`}>
                    <h3 className="text-sm font-bold uppercase tracking-wider">Bug Severity Distribution</h3>
                    <div className="h-64 flex items-center justify-center">
                      {analytics?.severity && analytics.severity.some(s => s.value > 0) ? (
                        <ResponsiveContainer width="100%" height="100%">
                          <PieChart>
                            <Pie
                              data={analytics.severity}
                              cx="50%"
                              cy="50%"
                              innerRadius={60}
                              outerRadius={90}
                              paddingAngle={5}
                              dataKey="value"
                            >
                              {analytics.severity.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                              ))}
                            </Pie>
                            <Tooltip contentStyle={{ backgroundColor: '#131926', border: '1px solid #334155' }} />
                          </PieChart>
                        </ResponsiveContainer>
                      ) : (
                        <p className="text-slate-500 font-mono text-xs">No analytics data recorded.</p>
                      )}
                    </div>
                    <div className="flex justify-around text-[10px] flex-wrap gap-2">
                      {analytics?.severity.map((d, idx) => (
                        <div key={idx} className="flex items-center gap-1.5">
                          <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: PIE_COLORS[idx] }}></div>
                          <span className="text-slate-400 font-bold">{d.name}: {d.value}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Category Breakdown */}
                  <div className={`p-6 rounded-xl border ${cardStyle} space-y-4 flex flex-col justify-between`}>
                    <h3 className="text-sm font-bold uppercase tracking-wider">Category Breakdown</h3>
                    <div className="h-64 flex items-center justify-center">
                      {analytics?.category && analytics.category.some(c => c.value > 0) ? (
                        <ResponsiveContainer width="100%" height="100%">
                          <PieChart>
                            <Pie
                              data={analytics.category}
                              cx="50%"
                              cy="50%"
                              innerRadius={60}
                              outerRadius={90}
                              paddingAngle={5}
                              dataKey="value"
                            >
                              {analytics.category.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={CAT_COLORS[index % CAT_COLORS.length]} />
                              ))}
                            </Pie>
                            <Tooltip contentStyle={{ backgroundColor: '#131926', border: '1px solid #334155' }} />
                          </PieChart>
                        </ResponsiveContainer>
                      ) : (
                        <p className="text-slate-500 font-mono text-xs">No analytics data recorded.</p>
                      )}
                    </div>
                    <div className="flex justify-around text-[10px] flex-wrap gap-2">
                      {analytics?.category.map((d, idx) => (
                        <div key={idx} className="flex items-center gap-1.5">
                          <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: CAT_COLORS[idx] }}></div>
                          <span className="text-slate-400 font-bold">{d.name}: {d.value}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

            </motion.div>
          </AnimatePresence>
        </main>
      </div>

      {/* ==========================================
          INTERRUPTION MODALS (PORTALS)
      ========================================== */}
      <AnimatePresence>
        {authRequest && (
          <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            
            {authRequest.type === 'credentials' && (
              <motion.div 
                initial={{ scale: 0.95, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.95, opacity: 0 }}
                className={`w-full max-w-md p-6 rounded-xl border shadow-2xl space-y-4 ${cardStyle}`}
              >
                <div className="flex items-start gap-3">
                  <div className="p-2.5 rounded-lg bg-amber-500/10 text-amber-500">
                    <Shield className="w-6 h-6 animate-bounce" />
                  </div>
                  <div>
                    <h3 className="font-bold text-sm text-white uppercase">Authentication Form Detected</h3>
                    <p className={`text-[10px] ${textMuted} mt-0.5`}>Playwright paused on page: {authRequest.url}</p>
                  </div>
                </div>

                <form onSubmit={submitCredentialsResponse} className="space-y-4 text-xs">
                  <div className="space-y-1">
                    <label className="font-bold text-slate-400">Username/Email</label>
                    <input 
                      type="text" 
                      required
                      value={credentialsForm.username}
                      onChange={(e) => setCredentialsForm({ ...credentialsForm, username: e.target.value })}
                      placeholder="admin@company.com"
                      className={`w-full px-3 py-2 rounded border focus:outline-none ${inputStyle}`}
                    />
                  </div>

                  <div className="space-y-1">
                    <label className="font-bold text-slate-400">Password</label>
                    <input 
                      type="password" 
                      required
                      value={credentialsForm.password}
                      onChange={(e) => setCredentialsForm({ ...credentialsForm, password: e.target.value })}
                      placeholder="••••••••"
                      className={`w-full px-3 py-2 rounded border focus:outline-none ${inputStyle}`}
                    />
                  </div>

                  <div className="space-y-1">
                    <label className="font-bold text-slate-400 font-mono">Assigned Role Context</label>
                    <select 
                      value={credentialsForm.role}
                      onChange={(e) => setCredentialsForm({ ...credentialsForm, role: e.target.value })}
                      className={`w-full px-3 py-2 rounded border focus:outline-none ${inputStyle}`}
                    >
                      <option value="Admin">Admin</option>
                      <option value="Manager">Manager</option>
                      <option value="Employee">Employee</option>
                      <option value="Customer">Customer</option>
                    </select>
                  </div>

                  <button 
                    type="submit"
                    className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded font-bold transition"
                  >
                    Provide Session Credentials
                  </button>
                </form>
              </motion.div>
            )}

            {authRequest.type === 'otp' && (
              <motion.div 
                initial={{ scale: 0.95, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.95, opacity: 0 }}
                className={`w-full max-w-md p-6 rounded-xl border shadow-2xl space-y-4 ${cardStyle}`}
              >
                <div className="flex items-start gap-3">
                  <div className="p-2.5 rounded-lg bg-amber-500/10 text-amber-500">
                    <Mail className="w-6 h-6 animate-bounce" />
                  </div>
                  <div>
                    <h3 className="font-bold text-sm text-white uppercase">One-Time Password Required</h3>
                    <p className={`text-[10px] ${textMuted} mt-0.5`}>Playwright crawler is waiting for authorization security key:</p>
                  </div>
                </div>

                <form onSubmit={submitOtpResponse} className="space-y-4 text-xs">
                  <div className="space-y-1">
                    <label className="font-bold text-slate-400">Security Verification Code</label>
                    <input 
                      type="text" 
                      required
                      value={otpToken}
                      onChange={(e) => setOtpToken(e.target.value)}
                      placeholder="e.g. 583921"
                      className={`w-full px-3 py-2 rounded border text-center font-bold tracking-widest text-lg focus:outline-none ${inputStyle}`}
                    />
                  </div>

                  <button 
                    type="submit"
                    className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded font-bold transition"
                  >
                    Submit OTP & Resume Scan
                  </button>
                </form>
              </motion.div>
            )}

          </div>
        )}
      </AnimatePresence>

      {/* ==========================================
          COMPARISON & ZOOM MODALS
      ========================================== */}
      <AnimatePresence>
        {compareModalBug && (
          <div className="fixed inset-0 bg-black/90 backdrop-blur-md z-50 flex items-center justify-center p-4">
            <motion.div 
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className={`w-full max-w-5xl p-6 rounded-xl border shadow-2xl space-y-4 ${cardStyle}`}
            >
              {/* Header */}
              <div className="flex justify-between items-center border-b border-slate-800 pb-3">
                <div>
                  <h3 className="font-bold text-sm text-white uppercase flex items-center gap-2">
                    <Layers className="w-4 h-4 text-blue-500" />
                    Screenshot Visual Comparison
                  </h3>
                  <p className={`text-[10px] ${textMuted} mt-0.5`}>{compareModalBug.title} - {compareModalBug.pageUrl}</p>
                </div>
                <button 
                  onClick={() => setCompareModalBug(null)}
                  className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* View Mode Switcher */}
              <div className="flex justify-between items-center gap-4 bg-slate-900/60 p-2 rounded-lg border border-slate-800">
                <div className="flex gap-2">
                  <button
                    onClick={() => setCompareMode('slider')}
                    className={`px-3 py-1.5 rounded text-xs font-bold transition-all ${
                      compareMode === 'slider'
                        ? 'bg-blue-600 text-white shadow-sm'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    Interactive Slider
                  </button>
                  <button
                    onClick={() => setCompareMode('side-by-side')}
                    className={`px-3 py-1.5 rounded text-xs font-bold transition-all ${
                      compareMode === 'side-by-side'
                        ? 'bg-blue-600 text-white shadow-sm'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    Side-by-Side
                  </button>
                </div>
                <span className="text-[10px] text-slate-500 font-mono">
                  {compareMode === 'slider' ? 'Drag slider left/right to compare original vs annotated' : 'Compare original (left) vs annotated (right)'}
                </span>
              </div>

              {/* Body */}
              <div className="relative flex items-center justify-center bg-black/40 rounded-lg overflow-hidden border border-slate-800/80 p-1 min-h-[350px]">
                {compareMode === 'side-by-side' ? (
                  <div className="grid md:grid-cols-2 gap-4 w-full h-full">
                    {/* Left Column: Original */}
                    <div className="space-y-2 flex flex-col items-center">
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider bg-slate-800/40 px-2 py-0.5 rounded">Original (No Markings)</span>
                      <div className="relative aspect-video rounded overflow-hidden bg-black flex items-center justify-center border border-slate-800 w-full">
                        <img 
                          src={compareModalBug.screenshotPath} 
                          alt="Original" 
                          className="max-h-full max-w-full object-contain cursor-pointer"
                          onClick={() => setZoomModalImage({ src: compareModalBug.screenshotPath, title: `${compareModalBug.title} (Original)` })}
                        />
                      </div>
                    </div>

                    {/* Right Column: Annotated */}
                    <div className="space-y-2 flex flex-col items-center">
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider bg-red-500/10 text-red-400 px-2 py-0.5 rounded border border-red-500/15">Annotated (QA Overlay)</span>
                      <div className="relative aspect-video rounded overflow-hidden bg-black flex items-center justify-center border border-slate-800 w-full">
                        <img 
                          src={compareModalBug.annotatedScreenshotPath || compareModalBug.screenshotPath} 
                          alt="Annotated" 
                          className="max-h-full max-w-full object-contain cursor-pointer"
                          onClick={() => setZoomModalImage({ src: compareModalBug.annotatedScreenshotPath || compareModalBug.screenshotPath, title: `${compareModalBug.title} (Annotated)` })}
                        />
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="relative w-full max-w-3xl aspect-video select-none overflow-hidden rounded-lg border border-slate-800 bg-black">
                    {/* Background: Original */}
                    <img 
                      src={compareModalBug.screenshotPath} 
                      className="absolute inset-0 w-full h-full object-contain" 
                      alt="Original" 
                      draggable="false"
                    />
                    
                    {/* Foreground: Annotated (Clipped) */}
                    <div 
                      className="absolute inset-0 w-full h-full overflow-hidden" 
                      style={{ clipPath: `inset(0 ${100 - sliderVal}% 0 0)` }}
                    >
                      <img 
                        src={compareModalBug.annotatedScreenshotPath || compareModalBug.screenshotPath} 
                        className="absolute inset-0 w-full h-full object-contain" 
                        alt="Annotated" 
                        style={{ width: '100%', height: '100%' }}
                        draggable="false"
                      />
                    </div>
                    
                    {/* Divider Line & handle */}
                    <div className="absolute top-0 bottom-0 w-0.5 bg-blue-500 z-10 pointer-events-none" style={{ left: `${sliderVal}%` }}>
                      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-blue-650 text-white flex items-center justify-center shadow-lg border border-blue-400">
                        <ChevronLeft className="w-3 h-3 absolute left-1" />
                        <ChevronRight className="w-3 h-3 absolute right-1" />
                      </div>
                    </div>
                    
                    {/* Range Input Overlay */}
                    <input 
                      type="range" 
                      min="0" 
                      max="100" 
                      value={sliderVal} 
                      onChange={(e) => setSliderVal(Number(e.target.value))} 
                      className="absolute inset-0 w-full h-full opacity-0 cursor-ew-resize z-20"
                    />
                  </div>
                )}
              </div>

              {/* Details & Actions Footer */}
              <div className="flex flex-wrap justify-between items-center gap-3 pt-3 border-t border-slate-800/60">
                <span className="text-[10px] text-slate-500 font-mono font-bold">
                  Location details: {compareModalBug.xpathOrSelector || 'N/A'} | Severity: {compareModalBug.severity}
                </span>
                <button
                  onClick={() => setCompareModalBug(null)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded font-bold text-xs transition"
                >
                  Close Comparison
                </button>
              </div>
            </motion.div>
          </div>
        )}

        {zoomModalImage && (
          <div className="fixed inset-0 bg-black/95 backdrop-blur-md z-[60] flex flex-col items-center justify-between p-4 select-none">
            {/* Header */}
            <div className="w-full flex justify-between items-center border-b border-slate-800/60 pb-3 max-w-5xl">
              <div>
                <h3 className="font-bold text-sm text-white uppercase flex items-center gap-2">
                  <Eye className="w-4 h-4 text-blue-500" />
                  Visual Zoom & Pan Preview
                </h3>
                <p className={`text-[10px] ${textMuted} mt-0.5`}>{zoomModalImage.title}</p>
              </div>
              <button 
                onClick={() => setZoomModalImage(null)}
                className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Canvas / Image zoom area */}
            <div 
              className="flex-1 w-full max-w-5xl flex items-center justify-center overflow-hidden my-4 bg-black/30 rounded-xl border border-slate-800 relative cursor-grab active:cursor-grabbing"
              onMouseDown={handleMouseDown}
              onMouseMove={handleMouseMove}
              onMouseUp={handleMouseUp}
              onMouseLeave={handleMouseUp}
            >
              <img
                src={zoomModalImage.src}
                alt={zoomModalImage.title}
                draggable="false"
                style={{
                  transform: `translate(${position.x}px, ${position.y}px) scale(${scale})`,
                  cursor: scale > 1 ? (isDragging ? 'grabbing' : 'grab') : 'default',
                  transition: isDragging ? 'none' : 'transform 0.15s ease-out'
                }}
                className="max-h-full max-w-full object-contain pointer-events-none origin-center"
              />
              
              {scale === 1 && (
                <div className="absolute bottom-3 left-1/2 -translate-x-1/2 px-3 py-1 rounded bg-black/60 text-[9px] text-slate-400 font-mono pointer-events-none">
                  Tip: Zoom in to pan around the screenshot
                </div>
              )}
            </div>

            {/* Controls Footer */}
            <div className="w-full max-w-5xl flex justify-between items-center border-t border-slate-800/60 pt-3">
              <div className="flex gap-2">
                <button
                  onClick={zoomIn}
                  className="p-2 bg-slate-800 hover:bg-slate-700 text-white rounded transition flex items-center gap-1.5 text-xs font-bold"
                  title="Zoom In"
                >
                  <ZoomIn className="w-4 h-4" /> Zoom In
                </button>
                <button
                  onClick={zoomOut}
                  disabled={scale === 1}
                  className="p-2 bg-slate-800 hover:bg-slate-700 text-white rounded transition flex items-center gap-1.5 text-xs font-bold disabled:opacity-40 disabled:hover:bg-slate-800"
                  title="Zoom Out"
                >
                  <ZoomOut className="w-4 h-4" /> Zoom Out
                </button>
                <button
                  onClick={resetZoom}
                  disabled={scale === 1 && position.x === 0 && position.y === 0}
                  className="p-2 bg-slate-800 hover:bg-slate-700 text-white rounded transition flex items-center gap-1.5 text-xs font-bold disabled:opacity-40 disabled:hover:bg-slate-800"
                  title="Reset Zoom"
                >
                  <RotateCcw className="w-4 h-4" /> Reset
                </button>
              </div>
              
              <div className="text-xs text-slate-500 font-mono">
                Scale: {scale.toFixed(1)}x
              </div>

              <button
                onClick={() => setZoomModalImage(null)}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded font-bold text-xs transition"
              >
                Close Zoom
              </button>
            </div>
          </div>
        )}
      </AnimatePresence>

    </div>
  );
}
