"""
============================================================
AI-Enhanced Enterprise Test Automation Framework
WebDriver Factory
============================================================
Creates and manages WebDriver instances for Chrome, Firefox,
Edge — local, headless, or Selenium Grid remote execution.
Implements the Factory design pattern for browser management.
============================================================
"""
from __future__ import annotations
import threading
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.remote.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager

from config.config import (
    BROWSER, HEADLESS, IMPLICIT_WAIT, PAGE_LOAD_TIMEOUT,
    USE_SELENIUM_GRID, SELENIUM_GRID_URL, browser_config,
)
from config.browser_config import (
    get_chrome_options, get_firefox_options,
    get_edge_options, get_remote_capabilities,
)
from utilities.logger import get_logger

logger = get_logger(__name__)


class DriverFactory:
    """
    Factory class for creating WebDriver instances.
    
    DESIGN PATTERN: Factory Pattern
        - Hides creation complexity from test classes
        - Centralizes driver configuration
        - Supports multiple browsers and execution modes
        - Thread-safe for parallel execution
    
    USAGE:
        # Create driver using config defaults
        driver = DriverFactory.create_driver()
        
        # Create specific browser
        driver = DriverFactory.create_driver("firefox")
        
        # Create headless Chrome
        driver = DriverFactory.create_driver("chrome", headless=True)
    """

    # Thread-local storage for parallel test execution
    # Each thread/worker gets its own driver instance
    _thread_local = threading.local()

    @classmethod
    def create_driver(
        cls,
        browser: Optional[str] = None,
        headless: Optional[bool] = None,
    ) -> WebDriver:
        """
        Create and configure a WebDriver instance.
        
        Args:
            browser: Browser name ('chrome', 'firefox', 'edge')
                     Defaults to BROWSER from config
            headless: Run in headless mode (no visible window)
                      Defaults to HEADLESS from config
        
        Returns:
            WebDriver: Configured and ready WebDriver instance
        
        Raises:
            ValueError: If an unsupported browser name is provided
        """
        target_browser = (browser or BROWSER).lower()
        is_headless = headless if headless is not None else HEADLESS

        logger.info("Creating %s driver (headless=%s, grid=%s)",
                    target_browser, is_headless, USE_SELENIUM_GRID)

        # ── Selenium Grid (Remote) Execution ──────────────────
        if USE_SELENIUM_GRID:
            driver = cls._create_remote_driver(target_browser)
        # ── Local Browser Execution ───────────────────────────
        elif target_browser == "chrome":
            driver = cls._create_chrome_driver()
        elif target_browser == "firefox":
            driver = cls._create_firefox_driver()
        elif target_browser == "edge":
            driver = cls._create_edge_driver()
        else:
            raise ValueError(
                f"Unsupported browser: '{target_browser}'. "
                f"Choose from: chrome, firefox, edge"
            )

        # ── Apply Common Settings ─────────────────────────────
        cls._configure_driver(driver)

        # Store in thread-local for parallel execution
        cls._thread_local.driver = driver
        logger.info("✓ Driver created successfully: %s", target_browser)
        return driver

    @classmethod
    def _create_chrome_driver(cls) -> WebDriver:
        """Create a local Chrome WebDriver with auto-managed ChromeDriver."""
        options = get_chrome_options()
        try:
            # webdriver-manager automatically downloads matching ChromeDriver
            service = ChromeService(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            logger.debug("Chrome driver created using webdriver-manager")
        except Exception as e:
            logger.warning("webdriver-manager failed (%s), trying system driver", e)
            # Fallback: use system-installed chromedriver
            driver = webdriver.Chrome(options=options)
        return driver

    @classmethod
    def _create_firefox_driver(cls) -> WebDriver:
        """Create a local Firefox WebDriver with auto-managed GeckoDriver."""
        options = get_firefox_options()
        try:
            service = FirefoxService(GeckoDriverManager().install())
            driver = webdriver.Firefox(service=service, options=options)
            logger.debug("Firefox driver created using webdriver-manager")
        except Exception as e:
            logger.warning("webdriver-manager failed (%s), trying system driver", e)
            driver = webdriver.Firefox(options=options)
        return driver

    @classmethod
    def _create_edge_driver(cls) -> WebDriver:
        """Create a local Edge WebDriver with auto-managed EdgeDriver."""
        options = get_edge_options()
        try:
            service = EdgeService(EdgeChromiumDriverManager().install())
            driver = webdriver.Edge(service=service, options=options)
            logger.debug("Edge driver created using webdriver-manager")
        except Exception as e:
            logger.warning("webdriver-manager failed (%s), trying system driver", e)
            driver = webdriver.Edge(options=options)
        return driver

    @classmethod
    def _create_remote_driver(cls, browser: str) -> WebDriver:
        """
        Create a remote WebDriver for Selenium Grid execution.
        
        Args:
            browser: Target browser name
        
        Returns:
            WebDriver: Remote WebDriver connected to Grid node
        """
        capabilities = get_remote_capabilities(browser)
        driver = webdriver.Remote(
            command_executor=SELENIUM_GRID_URL,
            options=cls._get_options_for_remote(browser),
        )
        logger.info("Remote driver connected to Grid: %s", SELENIUM_GRID_URL)
        return driver

    @staticmethod
    def _get_options_for_remote(browser: str):
        """Get browser options for remote/Grid execution."""
        options_map = {
            "chrome": get_chrome_options,
            "firefox": get_firefox_options,
            "edge": get_edge_options,
        }
        return options_map.get(browser, get_chrome_options)()

    @staticmethod
    def _configure_driver(driver: WebDriver) -> None:
        """
        Apply common WebDriver settings after creation.
        
        Settings applied:
            - Implicit wait: Automatically wait for elements
            - Page load timeout: Max time to wait for page load
            - Window maximize: Full screen for consistent results
        """
        driver.implicitly_wait(IMPLICIT_WAIT)
        driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
        driver.maximize_window()
        logger.debug(
            "Driver configured: implicit_wait=%ds, page_load_timeout=%ds",
            IMPLICIT_WAIT, PAGE_LOAD_TIMEOUT,
        )

    @classmethod
    def get_current_driver(cls) -> Optional[WebDriver]:
        """
        Get the WebDriver for the current thread.
        
        Returns:
            Optional[WebDriver]: Current thread's driver, or None
        """
        return getattr(cls._thread_local, "driver", None)

    @classmethod
    def quit_driver(cls, driver: Optional[WebDriver] = None) -> None:
        """
        Safely quit and clean up the WebDriver instance.
        
        Args:
            driver: Driver to quit. If None, quits current thread's driver.
        """
        target = driver or cls.get_current_driver()
        if target:
            try:
                target.quit()
                logger.info("✓ Driver quit successfully")
            except Exception as e:
                logger.warning("Error quitting driver: %s", e)
            finally:
                cls._thread_local.driver = None
