import { chromium, firefox, webkit } from 'playwright';
import express from 'express';
import path from 'path';
import fs from 'fs-extra';
import { fileURLToPath } from 'url';
import { Report, TestSession, Log, isMongoConnected, MongoReport, MongoTestSession, MongoLog } from './db.js';
import { v4 as uuidv4 } from 'uuid';
import axios from 'axios';
import { annotateScreenshot } from './annotation-service.js'; // We will use axios to check for broken links

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Map to hold pending user authentication responses
// Keys: sessionId, Values: { resolve, reject, type }
export const pendingAuthRequests = new Map();

// Helper to log message to console, DB, and socket
async function logMessage(sessionId, message, level = 'INFO', io = null) {
  console.log(`[Session ${sessionId}] [${level}] ${message}`);
  
  // Save log in DB
  try {
    await Log.create({
      sessionId,
      message,
      level
    });

    if (isMongoConnected) {
      await MongoLog.create({
        sessionId,
        message,
        level
      }).catch(err => console.error('Failed to write log to MongoDB:', err.message));
    }
  } catch (err) {
    console.error('Failed to write log to DB:', err);
  }

  // Emit real-time log via Socket.IO
  if (io) {
    io.to(sessionId).emit('log', {
      message,
      level,
      timestamp: new Date()
    });
  }
}

// Generate intelligent bug reports based on raw failure signatures (AI or robust Offline Rule Heuristics)
function classifyBug(errorType, details, url, browserName, deviceType) {
  let title = 'General Bug Detected';
  let description = '';
  let category = 'UI';
  let severity = 'MEDIUM';
  let rootCause = '';
  let suggestedFix = '';
  let stepsToReproduce = `1. Open browser (${browserName}) configured as ${deviceType}\n2. Navigate to ${url}\n3. Trigger event: ${errorType}`;

  switch (errorType) {
    case 'PAGE_CRASH':
      title = 'Critical Webpage Hydraulic Crash';
      description = `The page layout crashed or became empty. Hydration might have failed during React/Vue mounting. details: ${details}`;
      category = 'UI';
      severity = 'CRITICAL';
      rootCause = `Dynamic frontend framework hydration error, routing crash, or broken chunk imports.`;
      suggestedFix = `Ensure React mount points exist in the DOM, check bundle output, and inspect web server routes.`;
      break;

    case 'CONSOLE_ERROR':
      title = 'Uncaught Runtime JavaScript Exception';
      description = `An uncaught error was captured in the browser console: ${details}`;
      category = 'CONSOLE';
      severity = details.toLowerCase().includes('typeerror') || details.toLowerCase().includes('referenceerror') ? 'HIGH' : 'MEDIUM';
      rootCause = `Variable is undefined, failed script bundle load, or missing component reference in production bundle.`;
      suggestedFix = `Ensure all component methods are bound, add conditional chaining (?.) on optional properties, and resolve bundler warnings.`;
      break;

    case 'NETWORK_FAILED':
      if (details && details.includes('Image failed')) {
        title = 'Missing Image Asset (404 / Failed Load)';
        description = details;
        category = 'RESOURCE';
        severity = 'MEDIUM';
        rootCause = `The image file does not exist at the resolved path, or the CDN/storage bucket is unreachable.`;
        suggestedFix = `Verify the image path, upload the asset, or handle fallback using onerror="this.src='fallback.png'".`;
      } else {
        title = 'Failed Network Resource Request';
        description = `Network request to resource failed: ${details}`;
        category = 'API';
        severity = 'HIGH';
        rootCause = `CORS authorization issues, API server downtime, or invalid relative network path resolutions.`;
        suggestedFix = `Verify API backend headers allow cross-origin requests, check endpoints availability, and configure base URLs.`;
      }
      break;

    case 'SLOW_PAGE':
      title = 'Slow Loading Response Time';
      description = `Page response load duration exceeded the standard 3.0s SLA limit: ${details} seconds`;
      category = 'PERFORMANCE';
      severity = 'MEDIUM';
      rootCause = `Unoptimized images, bloated bundle sizes, missing resource compression, or slow backend API endpoints.`;
      suggestedFix = `Compress image assets, leverage bundler tree-shaking, enable Gzip compression, and optimize DB queries.`;
      break;

    case 'LAYOUT_OVERFLOW':
      title = 'Layout Viewport Horizontal Overflow';
      description = `Page layout contains elements exceeding the viewport boundary width (${details}px). Causes undesirable horizontal scrolling.`;
      category = 'UI';
      severity = 'LOW';
      rootCause = `Static element widths (e.g. width: 600px) or unconfigured viewport boundaries in responsive media queries.`;
      suggestedFix = `Utilize CSS flexbox/grid, replace static widths with percentage/viewport units, and check elements on mobile viewports.`;
      break;

    case 'ACCESSIBILITY_WARN':
      title = 'Accessibility Compliance Issue';
      description = `An HTML design pattern violated web accessibility guidelines: ${details}`;
      category = 'UI';
      severity = 'LOW';
      rootCause = `Missing alternative attributes (alt) on images, invalid heading hierarchies, or missing descriptive button labels.`;
      suggestedFix = `Ensure all interactive visual objects and image elements contain clear aria-labels or alt-text tags.`;
      break;

    case 'BROKEN_BUTTON':
      title = 'Broken or Unimplemented Interactive Button';
      description = `An interactive button was detected with usability issues: ${details}`;
      category = 'UI';
      severity = 'MEDIUM';
      rootCause = `Placeholder href attribute, empty click handlers, or lack of accessible labels/indicators.`;
      suggestedFix = `Ensure all interactive elements have functional JS event handlers, replace dummy links with actual action handlers, and add aria-label attributes for screen readers.`;
      break;

    case 'BROKEN_LINK':
      title = 'Broken Page Link (404/Unreachable)';
      description = `A hyperlink points to an unreachable page: ${details}`;
      category = 'RESOURCE';
      severity = 'HIGH';
      rootCause = `The linked resource or page does not exist on the target server or there is a routing misconfiguration.`;
      suggestedFix = `Update the href attribute of the anchor tag to point to a valid active URL, or remove the link if it is obsolete.`;
      break;

    case 'UI_OVERLAP':
      title = 'Visual Layout Component Overlap';
      description = `Visual layout components intersect/overlap each other: ${details}`;
      category = 'UI';
      severity = 'HIGH';
      rootCause = `Absolute positioning errors, z-index misconfigurations, or unconstrained CSS layout margins.`;
      suggestedFix = `Ensure proper relative or flex layout styles, verify z-index ordering, and test responsive layouts.`;
      break;

    case 'BLANK_SECTION':
      title = 'Empty / Blank Page Section';
      description = `A large layout container is visible but completely blank: ${details}`;
      category = 'UI';
      severity = 'MEDIUM';
      rootCause = `Failed rendering flow, dynamic list array is empty, or API fetched empty arrays with no fallback state.`;
      suggestedFix = `Implement empty state templates, add conditional loading indicators, and check API payload rendering.`;
      break;

    case 'INVISIBLE_BUTTON':
      title = 'Invisible Interactive Component';
      description = `An interactive button/link is hidden but active in the DOM layout: ${details}`;
      category = 'UI';
      severity = 'LOW';
      rootCause = `CSS opacity: 0, visibility: hidden, display: none or size 0x0 styles applied to active control components.`;
      suggestedFix = `Verify visibility state before rendering, avoid using opacity/hidden attributes for active buttons, or remove interactive events.`;
      break;

    case 'VALIDATION_ISSUE':
      title = 'Form Validation Field Failure';
      description = `Form element constraints or active validation attributes indicate validation failure: ${details}`;
      category = 'UI';
      severity = 'MEDIUM';
      rootCause = `Default html invalid states, active custom error-indicator classes, or error block displays next to field inputs.`;
      suggestedFix = `Validate input inputs against patterns, verify default values, and display user-friendly input instruction hints.`;
      break;

    default:
      title = `Unexpected issue in ${errorType}`;
      description = details;
  }

  return {
    title,
    description,
    category,
    severity,
    rootCause,
    suggestedFix,
    stepsToReproduce
  };
}

// Automatically find, fill out, and submit forms in the DOM to test user flows
async function interactAndFillForms(sessionId, page, io) {
  try {
    const inputs = await page.$$('input:not([type="hidden"]), textarea, select');
    if (inputs.length === 0) return;

    await logMessage(sessionId, `DOM Interaction: Found ${inputs.length} input elements on this page. Performing automatic form-filling...`, 'INFO', io);

    for (const input of inputs) {
      try {
        const isVisible = await input.isVisible().catch(() => false);
        const isDisabled = await input.isDisabled().catch(() => false);
        if (!isVisible || isDisabled) continue;

        const tagName = await input.evaluate(el => el.tagName.toLowerCase()).catch(() => '');
        const type = (await input.getAttribute('type').catch(() => '')) || 'text';
        const name = ((await input.getAttribute('name').catch(() => '')) || '').toLowerCase();
        const id = ((await input.getAttribute('id').catch(() => '')) || '').toLowerCase();
        const placeholder = ((await input.getAttribute('placeholder').catch(() => '')) || '').toLowerCase();

        // Skip auth/login fields to avoid interfering with checkAndHandleAuthentication
        if (type === 'password' && (name.includes('login') || id.includes('login'))) {
          continue;
        }

        if (tagName === 'select') {
          // Select second option if available
          await input.selectOption({ index: 1 }).catch(() => {});
          await logMessage(sessionId, `DOM Interaction: Selected option for dropdown [name="${name || id}"]`, 'INFO', io);
        } else if (tagName === 'textarea') {
          await input.fill('This is an automated test message submitted by the Playwright QA engine. Testing textarea behavior.').catch(() => {});
          await logMessage(sessionId, `DOM Interaction: Filled textarea [name="${name || id}"]`, 'INFO', io);
        } else if (type === 'checkbox' || type === 'radio') {
          await input.check().catch(() => {});
          await logMessage(sessionId, `DOM Interaction: Checked checkbox/radio [name="${name || id}"]`, 'INFO', io);
        } else if (type === 'file') {
          // Skip file uploads
        } else {
          // Input text, email, number, etc.
          let val = 'QA Automated Test';
          if (type === 'email' || name.includes('email') || placeholder.includes('email')) {
            val = `qa-auto-${Date.now()}@example.com`;
          } else if (type === 'number' || name.includes('phone') || name.includes('tel') || placeholder.includes('phone') || placeholder.includes('mobile')) {
            val = '5550199234';
          } else if (name.includes('name') || placeholder.includes('name')) {
            val = 'Alex Automation';
          } else if (name.includes('subject') || placeholder.includes('subject')) {
            val = 'Automated QA Testing Subject';
          } else if (type === 'password') {
            val = 'SecurePass123!';
          } else if (type === 'date') {
            val = '2026-01-01';
          }
          await input.fill(val).catch(() => {});
          await logMessage(sessionId, `DOM Interaction: Filled input [name="${name || id}"] with value: ${val}`, 'INFO', io);
        }
      } catch (inputErr) {
        // Continue to next input
      }
    }

    // Attempt to locate a submit or action button
    const submitBtn = await page.$('button[type="submit"], input[type="submit"], button:has-text("Submit"), button:has-text("Send"), button:has-text("Save"), button:has-text("Register"), button:has-text("Login")');
    if (submitBtn) {
      const isVisible = await submitBtn.isVisible().catch(() => false);
      if (isVisible) {
        await logMessage(sessionId, `DOM Interaction: Found action button. Clicking submit button to trigger form actions...`, 'INFO', io);
        
        // Click and wait for navigation or timeout
        await Promise.all([
          page.waitForNavigation({ waitUntil: 'networkidle', timeout: 5000 }).catch(() => {}),
          submitBtn.click().catch(() => {})
        ]);
        await page.waitForTimeout(2000);
      }
    }
  } catch (err) {
    await logMessage(sessionId, `DOM Interaction Warning: ${err.message}`, 'WARN', io);
  }
}

export async function runPlaywrightScan(sessionId, sourceType, sourcePath, io = null) {
  let tempServer = null;
  let targetUrl = '';
  let localServerPort = null;
  let browser = null;
  let context = null;

  try {
    await logMessage(sessionId, `Starting automated scan. Source: ${sourceType} -> ${sourcePath}`, 'INFO', io);

    // 1. Host local projects if folder or zip upload
    if (sourceType === 'folder' || sourceType === 'zip') {
      const app = express();
      app.use(express.static(sourcePath));
      
      // Serve index.html or fallback to any HTML file
      app.get('*', (req, res, next) => {
        const indexFile = path.join(sourcePath, 'index.html');
        if (fs.existsSync(indexFile)) {
          res.sendFile(indexFile);
        } else {
          res.status(404).send('No index.html found in uploaded folder project.');
        }
      });

      // Find free port or bind randomly
      const serverInstance = app.listen(0);
      await new Promise((resolve) => {
        serverInstance.on('listening', () => {
          localServerPort = serverInstance.address().port;
          tempServer = serverInstance;
          targetUrl = `http://localhost:${localServerPort}`;
          resolve();
        });
      });

      await logMessage(sessionId, `Uploaded project hosted locally at: ${targetUrl}`, 'INFO', io);
    } else {
      targetUrl = sourcePath; // url
    }

    // Update status in databases
    try {
      await TestSession.update({ status: 'RUNNING' }, { where: { id: sessionId } });
      if (isMongoConnected) {
        await MongoTestSession.updateOne({ _id: sessionId }, { status: 'RUNNING' });
      }
    } catch (dbErr) {
      console.error('Failed to update status to RUNNING in DB:', dbErr.message);
    }

    // Set up Playwright Browsers and viewports
    const browsers = [
      { name: 'Chromium', launch: chromium },
    ];

    const devices = [
      { type: 'Desktop', width: 1440, height: 900 },
      { type: 'Mobile', width: 375, height: 812 }
    ];

    let totalBugs = 0;
    const visitedUrls = new Set();
    const urlsToVisit = [targetUrl];
    let pagesCrawled = 0;

    for (const browserConfig of browsers) {
      await logMessage(sessionId, `Launching Playwright browser: ${browserConfig.name}`, 'INFO', io);
      
      browser = await browserConfig.launch.launch({
        headless: true,
        args: [
          '--no-sandbox',
          '--disable-setuid-sandbox',
          '--disable-dev-shm-usage',
          '--disable-gpu',
          '--disable-web-security',
          '--ignore-certificate-errors'
        ]
      });

      try {
        for (const device of devices) {
          await logMessage(sessionId, `Configuring viewport profile: ${device.type} (${device.width}x${device.height})`, 'INFO', io);
          
          context = await browser.newContext({
            viewport: { width: device.width, height: device.height },
            userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            ignoreHTTPSErrors: true,
            extraHTTPHeaders: {
              'Accept-Language': 'en-US,en;q=0.9',
              'Referer': 'https://www.google.com/'
            },
            recordVideo: {
              dir: path.join(__dirname, 'public', 'videos', sessionId),
              size: { width: 1280, height: 720 }
            }
          });

          try {
            const page = await context.newPage();

            // Register Console & Error Listeners
            page.on('pageerror', async (error) => {
              await logMessage(sessionId, `Console Javascript hydration exception caught: ${error.message}`, 'ERROR', io);
              const resolved = await findRelatedDOMElement(page, 'CONSOLE_ERROR', error.message);
              await handleBugDetection(sessionId, page, 'CONSOLE_ERROR', error.message, browserConfig.name, device.type, io, resolved?.box, 'JS Exception', resolved?.selector);
              totalBugs++;
            });

            page.on('requestfailed', async (request) => {
              const failure = request.failure();
              await logMessage(sessionId, `Network resource fetch failed: ${request.url()} -> ${failure?.errorText || 'Failed'}`, 'WARN', io);
              const details = `${request.url()} (${failure?.errorText || 'Unknown Error'})`;
              const resolved = await findRelatedDOMElement(page, 'NETWORK_FAILED', details);
              await handleBugDetection(sessionId, page, 'NETWORK_FAILED', details, browserConfig.name, device.type, io, resolved?.box, 'API Failure', resolved?.selector);
              totalBugs++;
            });

            // Start scanning URLs queue
            visitedUrls.clear();
            urlsToVisit.length = 0;
            urlsToVisit.push(targetUrl);
            pagesCrawled = 0;

            while (urlsToVisit.length > 0 && pagesCrawled < 10) {
              const currentUrl = urlsToVisit.shift();
              if (visitedUrls.has(currentUrl)) continue;
              visitedUrls.add(currentUrl);
              pagesCrawled++;

              await logMessage(sessionId, `Navigating to target route: ${currentUrl}`, 'INFO', io);
              
              const startLoad = Date.now();
              let navSuccess = true;
              await page.goto(currentUrl, { waitUntil: 'load', timeout: 15000 }).catch(async (e) => {
                navSuccess = false;
                await logMessage(sessionId, `Navigation timed out or failed: ${e.message}`, 'ERROR', io);
              });
              
              if (!navSuccess) continue;
              
              const loadDuration = (Date.now() - startLoad) / 1000;

              // 1. Performance Bug Check
              if (loadDuration > 3.0) {
                const bodyBox = { x: 0, y: 0, width: device.width, height: 100 };
                await handleBugDetection(sessionId, page, 'SLOW_PAGE', `${loadDuration.toFixed(2)}`, browserConfig.name, device.type, io, bodyBox, 'Slow Response Time');
                totalBugs++;
              }

              // 2. Authentication Detection & Interruption Prompts
              await checkAndHandleAuthentication(sessionId, page, io);

              // 3. Unified DOM and visual issues scanning
              const pageIssues = await scanPageIssues(page);
              for (const issue of pageIssues) {
                await handleBugDetection(
                  sessionId,
                  page,
                  issue.type,
                  issue.reason,
                  browserConfig.name,
                  device.type,
                  io,
                  issue.box,
                  issue.label,
                  issue.selector,
                  pageIssues
                );
                totalBugs++;
              }

              // 4. Fill DOM inputs automatically and submit form interactions
              await interactAndFillForms(sessionId, page, io);

              // 7. Crawl internal link tags and validate links
              const links = await page.evaluate(() => {
                return Array.from(document.querySelectorAll('a[href]'))
                  .map(a => a.href)
                  .filter(href => href.startsWith('http') || href.startsWith('/'));
              });

              for (const link of links) {
                let resolvedLink;
                try {
                  resolvedLink = new URL(link, currentUrl).href;
                } catch (err) {
                  continue;
                }
                const parsedTarget = new URL(resolvedLink);
                const parsedBase = new URL(targetUrl);
                
                // Stay within same domain and avoid fragment loops
                if (parsedTarget.hostname === parsedBase.hostname && !visitedUrls.has(resolvedLink) && !urlsToVisit.includes(resolvedLink)) {
                  // Perform a quick HEAD check to see if the link is broken
                  try {
                    const checkRes = await axios.head(resolvedLink, { timeout: 3000 }).catch(async () => {
                      // Fallback to GET if HEAD fails
                      return await axios.get(resolvedLink, { timeout: 3000 });
                    });
                    
                    if (checkRes.status >= 400) {
                      // Find link box
                      const el = await page.locator(`a[href="${link}"]`).first();
                      const box = await el.boundingBox().catch(() => null);
                      await handleBugDetection(sessionId, page, 'BROKEN_LINK', `Link points to a broken page: ${resolvedLink} (HTTP status ${checkRes.status})`, browserConfig.name, device.type, io, box, 'Broken Link');
                      totalBugs++;
                    } else {
                      urlsToVisit.push(resolvedLink);
                    }
                  } catch (linkErr) {
                    // Ignore connection resets or timeout bugs unless it's a clear 404
                    if (linkErr.response && linkErr.response.status >= 400) {
                      const el = await page.locator(`a[href="${link}"]`).first();
                      const box = await el.boundingBox().catch(() => null);
                      await handleBugDetection(sessionId, page, 'BROKEN_LINK', `Link points to a broken page: ${resolvedLink} (HTTP status ${linkErr.response.status})`, browserConfig.name, device.type, io, box, 'Broken Link');
                      totalBugs++;
                    } else if (!linkErr.response) {
                      // DNS or host down
                      const el = await page.locator(`a[href="${link}"]`).first();
                      const box = await el.boundingBox().catch(() => null);
                      await handleBugDetection(sessionId, page, 'BROKEN_LINK', `Link points to an unreachable endpoint: ${resolvedLink} (Error: ${linkErr.message})`, browserConfig.name, device.type, io, box, 'Broken Link');
                      totalBugs++;
                    }
                  }
                }
              }

              // Update progress in database
              try {
                await TestSession.update({ totalPages: pagesCrawled, totalBugs }, { where: { id: sessionId } });
                if (isMongoConnected) {
                  await MongoTestSession.updateOne({ _id: sessionId }, { totalPages: pagesCrawled, totalBugs });
                }
              } catch (dbErr) {
                console.error('Failed to update progress in DB:', dbErr.message);
              }

              if (io) {
                io.to(sessionId).emit('progress', {
                  pagesCrawled,
                  totalBugs,
                  percentage: Math.min(Math.round((pagesCrawled / 10) * 100), 99)
                });
              }
            }
          } finally {
            await context.close();
            context = null;
          }
        }
      } finally {
        await browser.close();
        browser = null;
      }
    }

    // Complete session
    try {
      await TestSession.update({ 
        status: 'COMPLETED',
        totalPages: pagesCrawled,
        totalBugs
      }, { where: { id: sessionId } });

      if (isMongoConnected) {
        await MongoTestSession.updateOne({ _id: sessionId }, { 
          status: 'COMPLETED',
          totalPages: pagesCrawled,
          totalBugs
        });
      }
    } catch (dbErr) {
      console.error('Failed to save COMPLETED state in DB:', dbErr.message);
    }

    await logMessage(sessionId, `Scan validation pipeline completed. Found ${totalBugs} bugs.`, 'SUCCESS', io);
    if (io) {
      io.to(sessionId).emit('progress', {
        pagesCrawled,
        totalBugs,
        percentage: 100
      });
      io.to(sessionId).emit('completed', { sessionId, totalBugs });
    }

  } catch (err) {
    await logMessage(sessionId, `Pipeline failed: ${err.message}`, 'ERROR', io);
    try {
      await TestSession.update({ status: 'FAILED' }, { where: { id: sessionId } });
      if (isMongoConnected) {
        await MongoTestSession.updateOne({ _id: sessionId }, { status: 'FAILED' });
      }
    } catch (dbErr) {
      console.error('Failed to save FAILED state in DB:', dbErr.message);
    }
    if (io) {
      io.to(sessionId).emit('progress', { percentage: 0 });
    }
  } finally {
    if (context) {
      await context.close().catch(() => {});
    }
    if (browser) {
      await browser.close().catch(() => {});
    }
    if (tempServer) {
      tempServer.close();
      await logMessage(sessionId, `Temporary local project webserver stopped.`, 'INFO', io);
    }
  }
}

// Check if page contains login or OTP/SSO buttons and pause the execution flow for user feedback
async function checkAndHandleAuthentication(sessionId, page, io) {
  // Look for password inputs or login forms
  const authState = await page.evaluate(() => {
    const passwordInput = document.querySelector('input[type="password"]');
    const otpInput = document.querySelector('input[name*="otp"], input[id*="otp"], input[placeholder*="OTP"], input[placeholder*="verification"]');
    const googleLoginBtn = document.querySelector('button[id*="google"], button[class*="google"], a[href*="google-login"]');
    const ssoBtn = document.querySelector('button[id*="sso"], button[class*="sso"], a[href*="sso"]');
    
    return {
      requiresCredentials: !!passwordInput,
      requiresOtp: !!otpInput,
      requiresSso: !!(googleLoginBtn || ssoBtn)
    };
  });

  if (authState.requiresCredentials) {
    await logMessage(sessionId, 'Auth requested: Login page credentials form detected. Pausing browser crawling...', 'WARN', io);
    
    // Notify client via Socket.IO
    if (io) {
      io.to(sessionId).emit('auth_required', {
        sessionId,
        url: page.url(),
        type: 'credentials'
      });
    }

    // Wait for resolve/reject promise from server routes
    const authData = await new Promise((resolve, reject) => {
      pendingAuthRequests.set(sessionId, { resolve, reject, type: 'credentials' });
    });

    await logMessage(sessionId, `Auth credentials received (User role: ${authData.role}). Continuing login submission...`, 'INFO', io);

    // Type credentials dynamically
    await page.evaluate((data) => {
      const emailField = document.querySelector('input[type="email"], input[type="text"][name*="user"], input[type="text"][name*="email"], input[type="text"][id*="user"], input[type="text"][id*="email"]');
      const passwordField = document.querySelector('input[type="password"]');
      
      if (emailField) emailField.value = data.username;
      if (passwordField) passwordField.value = data.password;

      // Submit
      const submitBtn = document.querySelector('button[type="submit"], input[type="submit"], button[id*="submit"], button[class*="submit"], button[class*="login"]');
      if (submitBtn) {
        submitBtn.click();
      } else {
        const form = passwordField.closest('form');
        if (form) form.submit();
      }
    }, authData);

    // Wait for navigation after submit
    await page.waitForTimeout(4000);
  }

  if (authState.requiresOtp) {
    await logMessage(sessionId, 'OTP requested: One-Time Password verification input detected. Pausing browser...', 'WARN', io);
    if (io) {
      io.to(sessionId).emit('auth_required', {
        sessionId,
        url: page.url(),
        type: 'otp'
      });
    }

    const otpData = await new Promise((resolve, reject) => {
      pendingAuthRequests.set(sessionId, { resolve, reject, type: 'otp' });
    });

    await logMessage(sessionId, `OTP token token input received (${otpData.otp}). Filling token...`, 'INFO', io);

    await page.evaluate((data) => {
      const otpField = document.querySelector('input[name*="otp"], input[id*="otp"], input[placeholder*="OTP"], input[placeholder*="verification"]');
      if (otpField) {
        otpField.value = data.otp;
        const form = otpField.closest('form');
        if (form) {
          const submitBtn = form.querySelector('button, input[type="submit"]');
          if (submitBtn) submitBtn.click();
          else form.submit();
        }
      }
    }, otpData);

    await page.waitForTimeout(4000);
  }
}

// Helper to find associated DOM element for page-level exceptions/failed requests
async function findRelatedDOMElement(page, errorType, details) {
  try {
    return await page.evaluate(({ type, msg }) => {
      // 1. Look for visible error components/overlays first
      const errorContainers = Array.from(document.querySelectorAll('.error, .alert, .message-error, [class*="error"], [class*="alert"], vite-error-overlay, nextjs-portal'));
      for (const container of errorContainers) {
        const rect = container.getBoundingClientRect();
        if (rect.width > 0 && rect.height > 0 && window.getComputedStyle(container).display !== 'none') {
          let selector = container.tagName.toLowerCase();
          if (container.id) selector += `#${container.id}`;
          else if (container.className) selector += '.' + container.className.trim().split(/\s+/)[0];
          return {
            selector,
            box: { x: rect.left, y: rect.top, width: rect.width, height: rect.height }
          };
        }
      }

      // 2. Look for elements containing words from the error details
      if (msg) {
        const lowerMsg = msg.toLowerCase();
        // If it's an image resource
        if (lowerMsg.includes('.png') || lowerMsg.includes('.jpg') || lowerMsg.includes('.jpeg') || lowerMsg.includes('.svg') || lowerMsg.includes('.gif')) {
          const imgs = Array.from(document.querySelectorAll('img'));
          for (const img of imgs) {
            const src = img.getAttribute('src') || '';
            if (src && lowerMsg.includes(src.toLowerCase())) {
              const rect = img.getBoundingClientRect();
              return {
                selector: `img[src="${src}"]`,
                box: { x: rect.left, y: rect.top, width: rect.width, height: rect.height }
              };
            }
          }
        }

        // If it mentions a button or link
        if (lowerMsg.includes('button') || lowerMsg.includes('click')) {
          const buttons = Array.from(document.querySelectorAll('button, a.btn, a.button'));
          for (const btn of buttons) {
            const text = (btn.innerText || '').toLowerCase();
            if (text && lowerMsg.includes(text)) {
              const rect = btn.getBoundingClientRect();
              let selector = btn.tagName.toLowerCase();
              if (btn.id) selector += `#${btn.id}`;
              return {
                selector,
                box: { x: rect.left, y: rect.top, width: rect.width, height: rect.height }
              };
            }
          }
        }
      }

      // 3. Fallback to body or top section
      return {
        selector: 'body',
        box: { x: 0, y: 0, width: window.innerWidth, height: 120 }
      };
    }, { type: errorType, msg: details });
  } catch (err) {
    return {
      selector: 'body',
      box: { x: 0, y: 0, width: 1280, height: 120 }
    };
  }
}

// Scan page for UI overlaps, blank sections, invisible elements, etc.
async function scanPageIssues(page) {
  try {
    return await page.evaluate(() => {
      const issues = [];
      
      // Helper to get element identifier/selector
      function getSelector(el) {
        if (el.id) return `#${el.id}`;
        let sel = el.tagName.toLowerCase();
        if (el.className && typeof el.className === 'string') {
          const firstClass = el.className.trim().split(/\s+/)[0];
          if (firstClass && !firstClass.includes(':') && !firstClass.includes('{') && !firstClass.includes('}')) {
            sel += `.${firstClass}`;
          }
        }
        if (el.getAttribute('name')) {
          sel += `[name="${el.getAttribute('name')}"]`;
        }
        return sel;
      }

      // 1. Scan for Broken Buttons (void href or empty description)
      const buttons = Array.from(document.querySelectorAll('button, input[type="submit"], input[type="button"], [role="button"], a.btn, a.button'));
      buttons.forEach((btn, index) => {
        const rect = btn.getBoundingClientRect();
        const style = window.getComputedStyle(btn);
        if (style.display === 'none' || style.visibility === 'hidden') return;
        
        const text = (btn.innerText || btn.value || btn.getAttribute('aria-label') || '').trim();
        const href = btn.getAttribute('href');
        
        let isBroken = false;
        let reason = '';
        
        if (href && (href.trim() === '#' || href.trim().toLowerCase().startsWith('javascript:void'))) {
          const hasOnClick = btn.hasAttribute('onclick') || btn.getAttribute('onclick') !== null;
          if (!hasOnClick && !btn.className.includes('js-') && btn.tagName.toLowerCase() === 'a') {
            isBroken = true;
            reason = 'Button uses a void link (href="#" or javascript:void(0)) with no click handler.';
          }
        }
        
        if (!text && !btn.querySelector('img, svg')) {
          isBroken = true;
          reason = 'Button is empty and has no readable text or icon.';
        }
        
        if (isBroken && rect.width > 0 && rect.height > 0) {
          issues.push({
            type: 'BROKEN_BUTTON',
            selector: getSelector(btn),
            reason,
            label: 'Broken Button',
            drawType: 'border',
            box: { x: rect.left, y: rect.top, width: rect.width, height: rect.height }
          });
        }
      });

      // 2. Scan for Missing/Broken Images
      const imgs = Array.from(document.querySelectorAll('img'));
      imgs.forEach(img => {
        const rect = img.getBoundingClientRect();
        const isBroken = !img.complete || img.naturalWidth === 0 || rect.width === 0 || rect.height === 0;
        if (isBroken && window.getComputedStyle(img).display !== 'none') {
          issues.push({
            type: 'MISSING_IMAGE',
            selector: getSelector(img),
            reason: `Image failed to load: ${img.src || 'No source specified'}`,
            label: 'Missing Image',
            drawType: 'circle',
            box: { x: rect.left, y: rect.top, width: rect.width || 40, height: rect.height || 40 }
          });
        }
      });

      // 3. Scan for UI Overlaps
      const interactive = Array.from(document.querySelectorAll('button, a, input, select, textarea, h1, h2, h3, img'));
      const visibleInteractive = interactive.filter(el => {
        const rect = el.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0 && window.getComputedStyle(el).display !== 'none' && window.getComputedStyle(el).visibility !== 'hidden';
      });

      for (let i = 0; i < visibleInteractive.length; i++) {
        const rectA = visibleInteractive[i].getBoundingClientRect();
        for (let j = i + 1; j < visibleInteractive.length; j++) {
          if (visibleInteractive[i].contains(visibleInteractive[j]) || visibleInteractive[j].contains(visibleInteractive[i])) {
            continue;
          }
          const rectB = visibleInteractive[j].getBoundingClientRect();
          
          // Calculate intersection
          const overlapX = Math.max(0, Math.min(rectA.right, rectB.right) - Math.max(rectA.left, rectB.left));
          const overlapY = Math.max(0, Math.min(rectA.bottom, rectB.bottom) - Math.max(rectA.top, rectB.top));
          
          if (overlapX > 10 && overlapY > 10) {
            const areaA = rectA.width * rectA.height;
            const areaB = rectB.width * rectB.height;
            const overlapArea = overlapX * overlapY;
            
            if (overlapArea / Math.min(areaA, areaB) > 0.4) {
              issues.push({
                type: 'UI_OVERLAP',
                selector: `${getSelector(visibleInteractive[i])} overlaps ${getSelector(visibleInteractive[j])}`,
                reason: 'UI component overlap detected, resulting in potential readability or click obstruction.',
                label: 'UI Overlap',
                drawType: 'glow',
                box: { 
                  x: Math.min(rectA.left, rectB.left), 
                  y: Math.min(rectA.top, rectB.top), 
                  width: Math.max(rectA.right, rectB.right) - Math.min(rectA.left, rectB.left), 
                  height: Math.max(rectA.bottom, rectB.bottom) - Math.min(rectA.top, rectB.top) 
                }
              });
              break;
            }
          }
        }
      }

      // 4. Scan for Blank Sections
      const containers = Array.from(document.querySelectorAll('div, section, main, article'));
      containers.forEach(el => {
        const rect = el.getBoundingClientRect();
        if (rect.width > 250 && rect.height > 180) {
          const text = el.innerText.trim();
          const hasVisibleChildren = Array.from(el.querySelectorAll('*')).some(child => {
            const childRect = child.getBoundingClientRect();
            return childRect.width > 0 && childRect.height > 0 && window.getComputedStyle(child).display !== 'none';
          });
          const style = window.getComputedStyle(el);
          if (text === '' && !hasVisibleChildren && style.display !== 'none' && style.visibility !== 'hidden') {
            issues.push({
              type: 'BLANK_SECTION',
              selector: getSelector(el),
              reason: 'Container section is visible but completely blank (no text or children).',
              label: 'Blank Section',
              drawType: 'glow',
              box: { x: rect.left, y: rect.top, width: rect.width, height: rect.height }
            });
          }
        }
      });

      // 5. Scan for Invisible Buttons/Controls
      const allButtons = Array.from(document.querySelectorAll('button, a.btn, a.button, input[type="submit"]'));
      allButtons.forEach(btn => {
        const rect = btn.getBoundingClientRect();
        const style = window.getComputedStyle(btn);
        const isOpacityZero = parseFloat(style.opacity) === 0;
        const isVisibilityHidden = style.visibility === 'hidden';
        const isDisplayNone = style.display === 'none';
        const isZeroSize = rect.width === 0 || rect.height === 0;

        if (isOpacityZero || isVisibilityHidden || isDisplayNone || isZeroSize) {
          let parentRect = btn.parentElement ? btn.parentElement.getBoundingClientRect() : null;
          let drawX = rect.left || (parentRect ? parentRect.left : 10);
          let drawY = rect.top || (parentRect ? parentRect.top : 10);
          
          issues.push({
            type: 'INVISIBLE_BUTTON',
            selector: getSelector(btn),
            reason: `Interactive component is hidden from layout via style (${isOpacityZero ? 'opacity:0' : isVisibilityHidden ? 'visibility:hidden' : 'display:none'}).`,
            label: 'Invisible Component',
            drawType: 'border',
            box: { x: drawX, y: drawY, width: rect.width || 80, height: rect.height || 30 }
          });
        }
      });

      // 6. Scan for Validation Issues
      const valInputs = Array.from(document.querySelectorAll('input:invalid, select:invalid, textarea:invalid, [aria-invalid="true"], .is-invalid, .error-field'));
      valInputs.forEach(input => {
        const rect = input.getBoundingClientRect();
        if (rect.width > 0 && rect.height > 0) {
          let errorMsg = 'Input validation constraints failed.';
          const parent = input.parentElement;
          if (parent) {
            const errorEl = parent.querySelector('.error-message, .invalid-feedback, [class*="error"], [class*="invalid"]');
            if (errorEl) {
              errorMsg = errorEl.innerText.trim();
            }
          }
          issues.push({
            type: 'VALIDATION_ISSUE',
            selector: getSelector(input),
            reason: `Form control has validation failure: ${errorMsg}`,
            label: 'Validation Issue',
            drawType: 'border',
            box: { x: rect.left, y: rect.top, width: rect.width, height: rect.height }
          });
        }
      });

      // 7. Crashed Components
      const errorContainers = Array.from(document.querySelectorAll('vite-error-overlay, nextjs-portal, .nextjs-static-error-boundary, #webpack-dev-server-client-overlay, .react-error-boundary, [class*="ErrorFallback"]'));
      errorContainers.forEach(container => {
        const rect = container.getBoundingClientRect();
        if (rect.width > 0 && rect.height > 0) {
          issues.push({
            type: 'PAGE_CRASH',
            selector: getSelector(container),
            reason: 'Development crash overlay or frontend runtime error boundary fallback detected.',
            label: 'Crashed Component',
            drawType: 'glow',
            box: { x: rect.left, y: rect.top, width: rect.width, height: rect.height }
          });
        }
      });

      const bodyText = document.body.innerText.toLowerCase();
      if (bodyText.includes('uncaught error') || bodyText.includes('component crashed') || bodyText.includes('react error #')) {
        const allDivs = Array.from(document.querySelectorAll('div, p, h1'));
        for (const div of allDivs) {
          const text = div.innerText || '';
          if ((text.includes('Uncaught Error') || text.includes('Component Crashed') || text.includes('React error #')) && div.children.length === 0) {
            const rect = div.getBoundingClientRect();
            if (rect.width > 0 && rect.height > 0) {
              issues.push({
                type: 'PAGE_CRASH',
                selector: getSelector(div),
                reason: `Text content indicates crash: "${text.substring(0, 80)}"`,
                label: 'Crashed Component',
                drawType: 'glow',
                box: { x: rect.left, y: rect.top, width: rect.width, height: rect.height }
              });
              break;
            }
          }
        }
      }

      // 8. Responsive Layout Overflow
      const windowWidth = window.innerWidth;
      const allEls = Array.from(document.querySelectorAll('*'));
      for (const el of allEls) {
        const rect = el.getBoundingClientRect();
        if (rect.right > windowWidth && rect.width > 0 && rect.height > 0 && window.getComputedStyle(el).display !== 'none') {
          issues.push({
            type: 'LAYOUT_OVERFLOW',
            selector: getSelector(el),
            reason: `Element overflows screen horizontal viewport boundary (element right at ${rect.right}px, screen width is ${windowWidth}px).`,
            label: 'Responsive Overflow',
            drawType: 'glow',
            box: { x: rect.left, y: rect.top, width: rect.width, height: rect.height }
          });
          break;
        }
      }

      // 9. Accessibility Alt-text checks
      const altImgs = Array.from(document.querySelectorAll('img:not([alt])'));
      altImgs.forEach(img => {
        const rect = img.getBoundingClientRect();
        if (rect.width > 0 && rect.height > 0 && window.getComputedStyle(img).display !== 'none') {
          issues.push({
            type: 'ACCESSIBILITY_WARN',
            selector: getSelector(img),
            reason: 'Image is missing an alternative description tag (alt attribute).',
            label: 'Accessibility Warning',
            drawType: 'circle',
            box: { x: rect.left, y: rect.top, width: rect.width, height: rect.height }
          });
        }
      });

      return issues;
    });
  } catch (err) {
    return [];
  }
}

// Handles screenshots and reports logging when bugs are caught
let bugDetectionPromiseChain = Promise.resolve();

// Handles screenshots and reports logging when bugs are caught (serialized to prevent memory OOM)
async function handleBugDetection(sessionId, page, errorType, details, browserName, deviceType, io = null, elementBox = null, annotationLabel = null, selector = null, otherAnnotations = []) {
  return new Promise((resolve, reject) => {
    bugDetectionPromiseChain = bugDetectionPromiseChain.then(async () => {
      try {
        await _handleBugDetectionInternal(sessionId, page, errorType, details, browserName, deviceType, io, elementBox, annotationLabel, selector, otherAnnotations);
        resolve();
      } catch (err) {
        console.error('Error during serialized handleBugDetection:', err);
        resolve(); // Resolve anyway to allow subsequent checks in queue to run
      }
    });
  });
}

async function _handleBugDetectionInternal(sessionId, page, errorType, details, browserName, deviceType, io = null, elementBox = null, annotationLabel = null, selector = null, otherAnnotations = []) {
  const bugMeta = classifyBug(errorType, details, page.url(), browserName, deviceType);
  const originalFilename = `bug_${uuidv4()}_original.png`;
  const annotatedFilename = `bug_${uuidv4()}_annotated.png`;
  const screenshotDir = path.join(__dirname, 'public', 'screenshots', sessionId);
  await fs.ensureDir(screenshotDir);
  
  const originalPath = path.join(screenshotDir, originalFilename);
  const annotatedPath = path.join(screenshotDir, annotatedFilename);

  let screenshotPath = '';
  let annotatedScreenshotPath = '';
  let screenshotBuffer = null;

  // Take original screenshot
  try {
    screenshotBuffer = await page.screenshot({ fullPage: false });
    await fs.writeFile(originalPath, screenshotBuffer);
    screenshotPath = `/screenshots/${sessionId}/${originalFilename}`;
  } catch (err) {
    console.error('Failed to capture page screenshot:', err);
  }

  // Draw annotations on screenshot using browser-based Canvas API
  const annotations = [];
  
  // Severity-coded colors
  const severityColors = {
    CRITICAL: '#ef4444', // Red
    HIGH: '#f97316',     // Orange
    MEDIUM: '#f59e0b',   // Amber
    LOW: '#3b82f6'       // Blue
  };
  
  const mainColor = severityColors[bugMeta.severity] || '#ef4444';

  if (elementBox && elementBox.x !== undefined && elementBox.y !== undefined && elementBox.width > 0 && elementBox.height > 0) {
    annotations.push({
      x: elementBox.x,
      y: elementBox.y,
      width: elementBox.width,
      height: elementBox.height,
      label: annotationLabel || bugMeta.title,
      color: mainColor,
      drawType: errorType === 'LAYOUT_OVERFLOW' ? 'glow' : (errorType === 'ACCESSIBILITY_WARN' || errorType === 'NETWORK_FAILED') ? 'circle' : 'border'
    });
  }

  // Add other annotations if any
  if (otherAnnotations && otherAnnotations.length > 0) {
    otherAnnotations.forEach(other => {
      if (!other.box) return;
      // Don't duplicate the primary annotation
      if (elementBox && Math.abs(other.box.x - elementBox.x) < 5 && Math.abs(other.box.y - elementBox.y) < 5) {
        return;
      }
      
      // Map other issues type to category/severity
      let otherSeverity = 'MEDIUM';
      if (other.type === 'PAGE_CRASH') otherSeverity = 'CRITICAL';
      else if (other.type === 'MISSING_IMAGE' || other.type === 'UI_OVERLAP') otherSeverity = 'HIGH';
      else if (other.type === 'ACCESSIBILITY_WARN') otherSeverity = 'LOW';
      
      annotations.push({
        x: other.box.x,
        y: other.box.y,
        width: other.box.width,
        height: other.box.height,
        label: other.label || other.type,
        color: severityColors[otherSeverity] || '#eab308',
        drawType: other.drawType || 'border'
      });
    });
  }

  if (screenshotBuffer && annotations.length > 0) {
    try {
      const browser = page.context().browser();
      // Draw using default type border if not specified per item
      const annotatedBuffer = await annotateScreenshot(browser, screenshotBuffer, annotations, 'border');
      await fs.writeFile(annotatedPath, annotatedBuffer);
      annotatedScreenshotPath = `/screenshots/${sessionId}/${annotatedFilename}`;
    } catch (err) {
      console.error('Failed to annotate page screenshot:', err.message);
      annotatedScreenshotPath = screenshotPath; // Fallback
    }
  } else {
    annotatedScreenshotPath = screenshotPath; // Fallback
  }

  // Fetch console & network logs
  const logsList = await page.evaluate(() => {
    return window.performance ? JSON.stringify(window.performance.getEntries().slice(0, 10)) : '[]';
  });

  // Save report into database
  try {
    const reportData = {
      sessionId,
      title: bugMeta.title,
      description: bugMeta.description,
      category: bugMeta.category,
      severity: bugMeta.severity,
      pageUrl: page.url(),
      xpathOrSelector: selector || null,
      screenshotPath,
      annotatedScreenshotPath,
      rootCause: bugMeta.rootCause,
      suggestedFix: bugMeta.suggestedFix,
      stepsToReproduce: bugMeta.stepsToReproduce,
      browserInfo: browserName,
      deviceType,
      consoleLogs: details,
      networkLogs: logsList,
      approved: false
    };

    await Report.create(reportData);

    if (isMongoConnected) {
      await MongoReport.create(reportData).catch(err => console.error('Failed to create report in MongoDB:', err.message));
    }

    await logMessage(sessionId, `[BUG CREATED] ${bugMeta.title} (${bugMeta.severity}) on ${page.url()}`, 'WARN', io);

    if (io) {
      io.to(sessionId).emit('bug_detected', {
        title: bugMeta.title,
        severity: bugMeta.severity,
        category: bugMeta.category,
        pageUrl: page.url()
      });
    }
  } catch (err) {
    console.error('Failed to create bug report in DB:', err);
  }
}
