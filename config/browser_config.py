"""
============================================================
AI-Enhanced Enterprise Test Automation Framework
Browser Configuration Module
============================================================
Provides browser-specific options and capabilities for
Chrome, Firefox, Edge with support for headless mode,
remote Grid execution, and performance settings.
============================================================
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from config.config import HEADLESS, WINDOW_SIZE


def get_chrome_options() -> ChromeOptions:
    """
    Configure Chrome browser options for automation.
    
    Returns:
        ChromeOptions: Configured Chrome options object
        
    WHY THESE OPTIONS:
        --no-sandbox: Required in Docker/CI environments
        --disable-dev-shm-usage: Prevents crashes in Docker (shared memory)
        --disable-gpu: Prevents GPU issues in headless mode
        --disable-extensions: Removes browser extensions that can interfere
        --disable-popup-blocking: Prevents unexpected popup blocks
        --ignore-certificate-errors: Handles self-signed SSL certs in test envs
    """
    options = ChromeOptions()

    # ── Performance Arguments ────────────────────────────────
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-web-security")

    # ── Window Size ──────────────────────────────────────────
    options.add_argument(f"--window-size={WINDOW_SIZE}")

    # ── SSL & Security ───────────────────────────────────────
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--allow-running-insecure-content")

    # ── Headless Mode ────────────────────────────────────────
    if HEADLESS:
        options.add_argument("--headless=new")  # Chrome 112+ headless mode
        options.add_argument("--disable-setuid-sandbox")

    # ── Download Configuration ───────────────────────────────
    prefs = {
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "profile.default_content_setting_values.notifications": 2,
    }
    options.add_experimental_option("prefs", prefs)

    # ── Exclude Automation Flags (bypass bot detection) ──────
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    return options


def get_firefox_options() -> FirefoxOptions:
    """
    Configure Firefox browser options for automation.
    
    Returns:
        FirefoxOptions: Configured Firefox options object
    """
    options = FirefoxOptions()

    # ── Headless Mode ────────────────────────────────────────
    if HEADLESS:
        options.add_argument("--headless")

    # ── Window Size ──────────────────────────────────────────
    width, height = WINDOW_SIZE.split(",")
    options.add_argument(f"--width={width}")
    options.add_argument(f"--height={height}")

    # ── Preferences ──────────────────────────────────────────
    options.set_preference("dom.webnotifications.enabled", False)
    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/pdf")
    options.set_preference("pdfjs.disabled", True)
    options.set_preference("geo.enabled", False)
    options.set_preference("browser.tabs.remote.autostart", False)

    return options


def get_edge_options() -> EdgeOptions:
    """
    Configure Microsoft Edge browser options for automation.
    
    Returns:
        EdgeOptions: Configured Edge options object
    """
    options = EdgeOptions()

    # ── Core Arguments (same as Chrome - Edge uses Chromium) ─
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-notifications")
    options.add_argument(f"--window-size={WINDOW_SIZE}")
    options.add_argument("--ignore-certificate-errors")

    # ── Headless Mode ────────────────────────────────────────
    if HEADLESS:
        options.add_argument("--headless=new")

    return options


def get_remote_capabilities(browser: str) -> dict:
    """
    Get Selenium Grid capabilities for remote execution.
    
    Args:
        browser: Browser name ('chrome', 'firefox', 'edge')
        
    Returns:
        dict: Desired capabilities for Selenium Grid
    """
    capabilities_map = {
        "chrome": {
            "browserName": "chrome",
            "platformName": "LINUX",
            "goog:chromeOptions": {
                "args": ["--headless=new", "--no-sandbox", "--disable-dev-shm-usage"]
            },
        },
        "firefox": {
            "browserName": "firefox",
            "platformName": "LINUX",
            "moz:firefoxOptions": {
                "args": ["-headless"]
            },
        },
        "edge": {
            "browserName": "MicrosoftEdge",
            "platformName": "LINUX",
            "ms:edgeOptions": {
                "args": ["--headless=new", "--no-sandbox"]
            },
        },
    }
    return capabilities_map.get(browser.lower(), capabilities_map["chrome"])
