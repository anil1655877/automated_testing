import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from database import Scan, Bug
from pathlib import Path

# Paths
ROOT_DIR = Path(__file__).resolve().parent
SCREENSHOT_DIR = ROOT_DIR / "reports" / "screenshots" / "scans"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

class QAPlatformScanner:
    def __init__(self, db_session):
        self.db = db_session
        self.visited_urls = set()
        self.bugs_list = []
        
    def scan_website(self, scan_id: int, start_url: str):
        # 1. Update status to RUNNING
        scan = self.db.query(Scan).filter(Scan.id == scan_id).first()
        if not scan:
            return
        scan.status = "RUNNING"
        self.db.commit()
        
        start_time = time.time()
        
        # Setup Selenium Options
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        driver = None
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Crawl internal links using BeautifulSoup (up to 10 pages)
            self._crawl_links(start_url, max_pages=5)
            
            scan.total_pages = len(self.visited_urls)
            self.db.commit()
            
            # Test each crawled page with headless Selenium
            for idx, page_url in enumerate(self.visited_urls):
                self._scan_page_selenium(driver, scan_id, page_url, idx)
                
            # Perform additional API mock test validations
            self._run_api_validation(scan_id, start_url)
            
            # Compile scan statistics
            scan.status = "COMPLETED"
            scan.total_bugs = len(self.bugs_list)
            scan.duration_seconds = int(time.time() - start_time)
            self.db.commit()
            
        except Exception as e:
            scan.status = "FAILED"
            self.db.commit()
            raise e
        finally:
            if driver:
                driver.quit()
                
    def _crawl_links(self, current_url: str, max_pages: int = 5):
        if len(self.visited_urls) >= max_pages:
            return
            
        self.visited_urls.add(current_url)
        base_domain = urlparse(current_url).netloc
        
        try:
            resp = requests.get(current_url, timeout=10)
            if resp.status_code != 200:
                return
                
            soup = BeautifulSoup(resp.text, 'html.parser')
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                full_url = urljoin(current_url, href)
                
                # Ensure it belongs to the same domain and not visited
                if urlparse(full_url).netloc == base_domain and full_url not in self.visited_urls:
                    if len(self.visited_urls) < max_pages:
                        self._crawl_links(full_url, max_pages)
        except Exception:
            pass

    def _scan_page_selenium(self, driver, scan_id: int, url: str, index: int):
        try:
            start_load = time.time()
            driver.get(url)
            load_time = time.time() - start_load
            
            # 1. Performance Bug Check (Slow page load)
            if load_time > 3.0:
                self._record_bug(
                    scan_id=scan_id,
                    title=f"Slow Response Time on {urlparse(url).path or '/'}",
                    description=f"Page loaded in {load_time:.2f} seconds, which exceeds the SLA recommendation of 3.0 seconds.",
                    category="PERFORMANCE",
                    severity="MEDIUM",
                    page_url=url,
                    xpath_or_selector="document",
                    root_cause="Large static assets, missing CDN caching, or slow backend queries.",
                    suggested_fix="Optimize asset sizes, enable Gzip compression, and cache static paths."
                )
                
            # 2. Browser Console Error Check
            logs = driver.get_log('browser')
            for log in logs:
                if log.get('level') == 'SEVERE':
                    msg = log.get('message', '')
                    self._record_bug(
                        scan_id=scan_id,
                        title="Uncaught JavaScript Error",
                        description=f"Severe console log trace captured: {msg}",
                        category="CONSOLE",
                        severity="HIGH",
                        page_url=url,
                        xpath_or_selector="window.console",
                        root_cause="Reference error, missing script tag import, or undefined variable call in Javascript runtime.",
                        suggested_fix="Review file dependencies, ensure script tags compile, and write checks surrounding window properties."
                    )
                    
            # 3. Screenshot Capture & Visual UI assertions (mocking dynamic failure check)
            # Take standard screenshot for the gallery
            ss_filename = f"scan_{scan_id}_page_{index}.png"
            ss_path = SCREENSHOT_DIR / ss_filename
            driver.save_screenshot(str(ss_path))
            
            # Simple check for empty/missing page elements
            page_text = driver.find_element("tag name", "body").text
            if not page_text or len(page_text.strip()) < 50:
                self._record_bug(
                    scan_id=scan_id,
                    title="Empty Body content / Render failure",
                    description=f"Page layout appears blank. Visible text length is less than 50 characters.",
                    category="UI",
                    severity="CRITICAL",
                    page_url=url,
                    xpath_or_selector="body",
                    screenshot_path=f"/screenshots/scans/{ss_filename}",
                    root_cause="Failed backend routing response or dynamic react hydration crash.",
                    suggested_fix="Inspect backend router logs and ensure React index entrypoints resolve DOM targets."
                )
                
            # Check for broken links/assets on page
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            for img in soup.find_all('img', src=True):
                img_src = urljoin(url, img.get('src'))
                try:
                    # Don't check external images to prevent timeouts
                    if urlparse(img_src).netloc == urlparse(url).netloc:
                        img_resp = requests.head(img_src, timeout=3)
                        if img_resp.status_code == 404:
                            self._record_bug(
                                scan_id=scan_id,
                                title="Missing Image Asset (404)",
                                description=f"Image source not found: {img_src}",
                                category="RESOURCE",
                                severity="LOW",
                                page_url=url,
                                xpath_or_selector=f"img[src='{img.get('src')}']",
                                screenshot_path=f"/screenshots/scans/{ss_filename}",
                                root_cause="Image source file is missing from assets directory or is misconfigured.",
                                suggested_fix="Ensure image file exists in correct relative path or points to valid CDN resource."
                            )
                except Exception:
                    pass
                    
        except Exception as e:
            # Fatal execution failure
            self._record_bug(
                scan_id=scan_id,
                title="Browser Navigation Failure",
                description=f"Selenium could not load page: {str(e)}",
                category="UI",
                severity="CRITICAL",
                page_url=url,
                root_cause="Target server is down, DNS resolution failed, or network connection timeout.",
                suggested_fix="Verify that destination host is online and check local proxy configurations."
            )

    def _run_api_validation(self, scan_id: int, base_url: str):
        # Scan for API failures. E.g. Check auth paths or catalog paths on base site
        api_path = urljoin(base_url, "/api/v1/users")
        try:
            resp = requests.get(api_path, timeout=5)
            # If endpoint exists but returns error, or if it doesn't exist
            if resp.status_code == 404:
                # Common on demo sites, skip major warning but mock check
                pass
            elif resp.status_code >= 500:
                self._record_bug(
                    scan_id=scan_id,
                    title="API Server Error (HTTP 500)",
                    description=f"Backend endpoint {api_path} failed with response code {resp.status_code}.",
                    category="API",
                    severity="CRITICAL",
                    page_url=base_url,
                    xpath_or_selector="/api",
                    root_cause="Internal server exception, uncaught backend handler error, or database timeout.",
                    suggested_fix="Verify backend service logs, test database queries, and add exception middleware handlers."
                )
        except Exception:
            pass

    def _record_bug(self, scan_id: int, title: str, description: str, category: str, severity: str, **kwargs):
        bug = Bug(
            scan_id=scan_id,
            title=title,
            description=description,
            category=category,
            severity=severity,
            page_url=kwargs.get("page_url"),
            xpath_or_selector=kwargs.get("xpath_or_selector"),
            screenshot_path=kwargs.get("screenshot_path"),
            root_cause=kwargs.get("root_cause"),
            suggested_fix=kwargs.get("suggested_fix"),
            approved=False
        )
        self.db.add(bug)
        self.db.commit()
        self.bugs_list.append(bug)
