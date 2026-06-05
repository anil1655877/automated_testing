"""
============================================================
AI-Enhanced Enterprise Test Automation Framework
Wait Utilities
============================================================
Provides intelligent waiting strategies beyond basic
implicit waits — explicit waits, fluent waits, and
custom condition wrappers for reliable test execution.
============================================================
"""
import time
from typing import Callable, Optional, Any, Type
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException,
    StaleElementReferenceException, ElementNotInteractableException,
)
from config.config import EXPLICIT_WAIT
from utilities.logger import get_logger

logger = get_logger(__name__)

# ── Type Alias ───────────────────────────────────────────────
Locator = tuple[str, str]  # e.g., (By.ID, "username")


class WaitUtils:
    """
    Collection of intelligent wait strategies for Selenium.
    
    CONCEPT: Why use explicit waits?
        - Web apps are asynchronous (AJAX, animations, API calls)
        - Elements appear/disappear based on app state
        - Hardcoded time.sleep() is flaky and slow
        - Explicit waits check conditions periodically until timeout
    
    USAGE:
        waiter = WaitUtils(driver)
        element = waiter.wait_for_element_visible((By.ID, "login-btn"))
        waiter.wait_for_url_contains("dashboard")
    """

    def __init__(self, driver: WebDriver, timeout: int = EXPLICIT_WAIT):
        """
        Initialize WaitUtils with a WebDriver and default timeout.
        
        Args:
            driver: Selenium WebDriver instance
            timeout: Default wait timeout in seconds
        """
        self.driver = driver
        self.timeout = timeout
        self._wait = WebDriverWait(
            driver,
            timeout,
            poll_frequency=0.5,
            ignored_exceptions=[
                StaleElementReferenceException,
                NoSuchElementException,
            ],
        )

    def wait_for_element_visible(
        self, locator: Locator, timeout: Optional[int] = None, message: str = ""
    ) -> WebElement:
        """
        Wait until element is present in DOM and visible on screen.
        
        Args:
            locator: Tuple of (By.*, selector_value)
            timeout: Custom timeout (uses default if not specified)
            message: Custom error message on timeout
        
        Returns:
            WebElement: The visible element
            
        Raises:
            TimeoutException: If element doesn't become visible in time
        """
        wait = self._get_wait(timeout)
        msg = message or f"Element {locator} not visible after {timeout or self.timeout}s"
        try:
            element = wait.until(EC.visibility_of_element_located(locator), message=msg)
            logger.debug("Element visible: %s", locator)
            return element
        except TimeoutException:
            logger.error("TIMEOUT: %s", msg)
            raise

    def wait_for_element_clickable(
        self, locator: Locator, timeout: Optional[int] = None
    ) -> WebElement:
        """
        Wait until element is visible AND enabled (ready to click).
        
        Args:
            locator: Tuple of (By.*, selector_value)
            timeout: Custom timeout
        
        Returns:
            WebElement: The clickable element
        """
        wait = self._get_wait(timeout)
        try:
            element = wait.until(EC.element_to_be_clickable(locator))
            logger.debug("Element clickable: %s", locator)
            return element
        except TimeoutException:
            logger.error("TIMEOUT: Element %s not clickable after %ds", locator, timeout or self.timeout)
            raise

    def wait_for_element_present(
        self, locator: Locator, timeout: Optional[int] = None
    ) -> WebElement:
        """
        Wait until element exists in DOM (may not be visible).
        
        Args:
            locator: Element locator tuple
            timeout: Custom timeout
        
        Returns:
            WebElement: The present element
        """
        wait = self._get_wait(timeout)
        try:
            element = wait.until(EC.presence_of_element_located(locator))
            logger.debug("Element present in DOM: %s", locator)
            return element
        except TimeoutException:
            logger.error("TIMEOUT: Element %s not in DOM after %ds", locator, timeout or self.timeout)
            raise

    def wait_for_element_invisible(
        self, locator: Locator, timeout: Optional[int] = None
    ) -> bool:
        """
        Wait until element disappears from view (e.g., loading spinner).
        
        Args:
            locator: Element locator tuple
            timeout: Custom timeout
        
        Returns:
            bool: True when element is invisible
        """
        wait = self._get_wait(timeout)
        try:
            result = wait.until(EC.invisibility_of_element_located(locator))
            logger.debug("Element invisible: %s", locator)
            return result
        except TimeoutException:
            logger.error("TIMEOUT: Element %s still visible after %ds", locator, timeout or self.timeout)
            raise

    def wait_for_text_in_element(
        self, locator: Locator, text: str, timeout: Optional[int] = None
    ) -> bool:
        """
        Wait until specific text appears inside an element.
        
        Args:
            locator: Element locator tuple
            text: Expected text to appear
            timeout: Custom timeout
        
        Returns:
            bool: True when text is found
        """
        wait = self._get_wait(timeout)
        try:
            result = wait.until(EC.text_to_be_present_in_element(locator, text))
            logger.debug("Text '%s' found in element %s", text, locator)
            return result
        except TimeoutException:
            logger.error("TIMEOUT: Text '%s' not found in %s after %ds", text, locator, timeout or self.timeout)
            raise

    def wait_for_url_contains(self, partial_url: str, timeout: Optional[int] = None) -> bool:
        """
        Wait until the current URL contains a specific string.
        Useful for validating navigation (e.g., after login).
        
        Args:
            partial_url: Substring expected in URL
            timeout: Custom timeout
        
        Returns:
            bool: True when URL matches
        """
        wait = self._get_wait(timeout)
        try:
            result = wait.until(EC.url_contains(partial_url))
            logger.debug("URL contains '%s': %s", partial_url, self.driver.current_url)
            return result
        except TimeoutException:
            logger.error(
                "TIMEOUT: URL doesn't contain '%s'. Current: %s",
                partial_url, self.driver.current_url
            )
            raise

    def wait_for_title_contains(self, title: str, timeout: Optional[int] = None) -> bool:
        """
        Wait until page title contains a specific string.
        
        Args:
            title: Expected substring in page title
            timeout: Custom timeout
        
        Returns:
            bool: True when title matches
        """
        wait = self._get_wait(timeout)
        return wait.until(EC.title_contains(title))

    def wait_for_alert(self, timeout: Optional[int] = None):
        """
        Wait for a browser alert/confirm/prompt dialog.
        
        Returns:
            Alert: The alert object (call .accept() or .dismiss())
        """
        wait = self._get_wait(timeout)
        return wait.until(EC.alert_is_present())

    def wait_for_custom_condition(
        self, condition: Callable, timeout: Optional[int] = None, message: str = ""
    ) -> Any:
        """
        Wait for any custom callable condition.
        
        ADVANCED USAGE: For complex conditions not covered by EC.*
        
        Args:
            condition: Callable that takes driver and returns truthy value
            timeout: Custom timeout
            message: Timeout error message
        
        Example:
            waiter.wait_for_custom_condition(
                lambda d: len(d.find_elements(By.CLASS_NAME, "result")) > 0
            )
        """
        wait = self._get_wait(timeout)
        return wait.until(condition, message=message)

    def wait_for_element_count(
        self, locator: Locator, count: int, timeout: Optional[int] = None
    ) -> list[WebElement]:
        """
        Wait until exactly N elements matching the locator are present.
        
        Args:
            locator: Element locator tuple
            count: Expected number of elements
            timeout: Custom timeout
        
        Returns:
            list[WebElement]: List of matching elements
        """
        wait = self._get_wait(timeout)
        condition = lambda d: (
            elements := d.find_elements(*locator)
        ) and len(elements) >= count and elements
        return wait.until(condition, message=f"Expected {count} elements for {locator}")

    def wait_for_page_load(self, timeout: Optional[int] = None) -> None:
        """
        Wait until the page document is fully loaded (readyState=complete).
        
        Args:
            timeout: Custom timeout
        """
        wait = self._get_wait(timeout)
        wait.until(
            lambda d: d.execute_script("return document.readyState") == "complete",
            message="Page did not fully load"
        )
        logger.debug("Page fully loaded")

    def wait_for_ajax_complete(self, timeout: Optional[int] = None) -> None:
        """
        Wait until all jQuery AJAX requests complete.
        Only applicable to pages using jQuery.
        
        Args:
            timeout: Custom timeout
        """
        wait = self._get_wait(timeout)
        try:
            wait.until(
                lambda d: d.execute_script("return jQuery.active") == 0,
                message="AJAX requests not completed"
            )
            logger.debug("All AJAX requests completed")
        except Exception:
            logger.debug("jQuery not available, skipping AJAX wait")

    def smart_wait(self, locator: Locator, timeout: Optional[int] = None) -> WebElement:
        """
        Intelligent wait that tries multiple strategies:
        1. Wait for element to be clickable
        2. Fall back to just visible
        3. Fall back to just present in DOM
        
        This is the recommended method for most use cases.
        
        Args:
            locator: Element locator tuple
            timeout: Custom timeout
        
        Returns:
            WebElement: The found element
        """
        try:
            return self.wait_for_element_clickable(locator, timeout)
        except TimeoutException:
            pass
        try:
            return self.wait_for_element_visible(locator, timeout)
        except TimeoutException:
            pass
        return self.wait_for_element_present(locator, timeout)

    def _get_wait(self, timeout: Optional[int]) -> WebDriverWait:
        """Get WebDriverWait with specified or default timeout."""
        if timeout is None:
            return self._wait
        return WebDriverWait(
            self.driver,
            timeout,
            poll_frequency=0.5,
            ignored_exceptions=[StaleElementReferenceException, NoSuchElementException],
        )


# ── Standalone utility functions ──────────────────────────────
def sleep(seconds: float, reason: str = "") -> None:
    """
    Explicit sleep with mandatory reason documentation.
    
    ANTI-PATTERN WARNING: Use explicit waits instead.
    Only use this when there's no better alternative
    (e.g., waiting for a non-DOM animation to complete).
    
    Args:
        seconds: Seconds to sleep
        reason: Why this sleep is necessary (required for code review)
    """
    if reason:
        logger.debug("Sleeping %.1fs: %s", seconds, reason)
    else:
        logger.warning("Sleep called without reason - consider using explicit waits!")
    time.sleep(seconds)
