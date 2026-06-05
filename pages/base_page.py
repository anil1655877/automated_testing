"""
============================================================
AI-Enhanced Enterprise Test Automation Framework
Base Page Object
============================================================
All page objects inherit from BasePage. Centralizes all
WebDriver interactions, providing consistent, reliable,
self-healing element access across the entire framework.
============================================================
"""
from __future__ import annotations
import time
from typing import Optional, List
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException,
    StaleElementReferenceException, ElementNotInteractableException,
    ElementClickInterceptedException,
)

from config.config import EXPLICIT_WAIT, IMPLICIT_WAIT, SCREENSHOT_ON_FAILURE
from utilities.logger import get_logger
from utilities.wait_utils import WaitUtils, sleep
from utilities.screenshot_utils import ScreenshotUtils

logger = get_logger(__name__)

# Locator type alias
Locator = tuple[str, str]


class BasePage:
    """
    Base Page Object — parent of all page objects.

    DESIGN PATTERN: Page Object Model (POM)
        Each web page is represented by a class. Locators and
        page interactions live in the page class, keeping tests
        clean and free of Selenium implementation details.

    PRINCIPLES:
        1. Tests call page methods — not raw Selenium commands
        2. Locators are class-level tuples, easy to update
        3. All waits are centralized here, not in tests
        4. Screenshots on every failure automatically

    USAGE (in test file):
        page = LoginPage(driver)
        page.navigate()
        page.login("admin@test.com", "Password@123")
        assert page.is_logged_in()
    """

    def __init__(self, driver: WebDriver):
        """
        Initialize BasePage with WebDriver instance.

        Args:
            driver: Active Selenium WebDriver
        """
        self.driver = driver
        self.wait = WaitUtils(driver, EXPLICIT_WAIT)
        self.screenshot = ScreenshotUtils(driver)
        self.actions = ActionChains(driver)
        logger.debug("BasePage initialized: %s", self.__class__.__name__)

    # ─────────────────────────────────────────────────────────
    # Navigation Methods
    # ─────────────────────────────────────────────────────────

    def navigate_to(self, url: str) -> None:
        """Navigate browser to a URL."""
        logger.info("Navigating to: %s", url)
        self.driver.get(url)
        self.wait_for_page_load()

    def go_back(self) -> None:
        """Navigate to previous page in browser history."""
        self.driver.back()
        self.wait_for_page_load()

    def refresh(self) -> None:
        """Refresh the current page."""
        self.driver.refresh()
        self.wait_for_page_load()

    def get_current_url(self) -> str:
        """Return the current page URL."""
        return self.driver.current_url

    def get_page_title(self) -> str:
        """Return the current page title."""
        return self.driver.title

    # ─────────────────────────────────────────────────────────
    # Element Finding (with Smart Waits)
    # ─────────────────────────────────────────────────────────

    def find_element(self, locator: Locator, timeout: Optional[int] = None) -> WebElement:
        """
        Find element with explicit wait — preferred over driver.find_element.

        Args:
            locator: Tuple (By.*, selector)
            timeout: Optional custom timeout

        Returns:
            WebElement: Found element
        """
        return self.wait.wait_for_element_visible(locator, timeout)

    def find_elements(self, locator: Locator, timeout: Optional[int] = None) -> List[WebElement]:
        """
        Find all elements matching locator.

        Args:
            locator: Tuple (By.*, selector)
            timeout: Optional wait timeout

        Returns:
            List[WebElement]: All matching elements
        """
        try:
            self.wait.wait_for_element_present(locator, timeout or 5)
        except TimeoutException:
            return []
        return self.driver.find_elements(*locator)

    def is_element_visible(self, locator: Locator, timeout: int = 5) -> bool:
        """
        Check if element is visible without raising exception.

        Args:
            locator: Element locator tuple
            timeout: Max time to wait

        Returns:
            bool: True if element visible within timeout
        """
        try:
            self.wait.wait_for_element_visible(locator, timeout)
            return True
        except (TimeoutException, NoSuchElementException):
            return False

    def is_element_present(self, locator: Locator, timeout: int = 3) -> bool:
        """Check if element exists in DOM (may be hidden)."""
        try:
            self.wait.wait_for_element_present(locator, timeout)
            return True
        except (TimeoutException, NoSuchElementException):
            return False

    # ─────────────────────────────────────────────────────────
    # Interaction Methods
    # ─────────────────────────────────────────────────────────

    def click(self, locator: Locator, timeout: Optional[int] = None) -> None:
        """
        Click element with smart retry on intercepted click.

        Args:
            locator: Element locator
            timeout: Optional wait timeout
        """
        element = self.wait.wait_for_element_clickable(locator, timeout)
        try:
            element.click()
            logger.debug("Clicked: %s", locator)
        except ElementClickInterceptedException:
            logger.warning("Click intercepted, using JS click for: %s", locator)
            self.js_click(locator)

    def type_text(self, locator: Locator, text: str, clear_first: bool = True) -> None:
        """
        Type text into an input field.

        Args:
            locator: Input element locator
            text: Text to type
            clear_first: Clear existing text before typing
        """
        element = self.wait.wait_for_element_visible(locator)
        if clear_first:
            element.clear()
        element.send_keys(text)
        logger.debug("Typed '%s' into: %s", text[:20] + "..." if len(text) > 20 else text, locator)

    def clear_and_type(self, locator: Locator, text: str) -> None:
        """Clear field using keyboard shortcut, then type text."""
        element = self.wait.wait_for_element_visible(locator)
        element.send_keys(Keys.CONTROL + "a")
        element.send_keys(Keys.DELETE)
        element.send_keys(text)

    def get_text(self, locator: Locator, timeout: Optional[int] = None) -> str:
        """Get visible text of an element."""
        element = self.find_element(locator, timeout)
        text = element.text.strip()
        logger.debug("get_text from %s: '%s'", locator, text[:50])
        return text

    def get_attribute(self, locator: Locator, attribute: str) -> str:
        """Get attribute value from an element."""
        element = self.find_element(locator)
        return element.get_attribute(attribute) or ""

    def get_input_value(self, locator: Locator) -> str:
        """Get value attribute of an input field."""
        return self.get_attribute(locator, "value")

    def select_dropdown_by_text(self, locator: Locator, text: str) -> None:
        """Select dropdown option by visible text."""
        element = self.find_element(locator)
        Select(element).select_by_visible_text(text)
        logger.debug("Selected '%s' from dropdown: %s", text, locator)

    def select_dropdown_by_value(self, locator: Locator, value: str) -> None:
        """Select dropdown option by value attribute."""
        element = self.find_element(locator)
        Select(element).select_by_value(value)

    def get_selected_option(self, locator: Locator) -> str:
        """Get currently selected dropdown option text."""
        element = self.find_element(locator)
        return Select(element).first_selected_option.text

    def check_checkbox(self, locator: Locator) -> None:
        """Check a checkbox if not already checked."""
        element = self.find_element(locator)
        if not element.is_selected():
            element.click()

    def uncheck_checkbox(self, locator: Locator) -> None:
        """Uncheck a checkbox if currently checked."""
        element = self.find_element(locator)
        if element.is_selected():
            element.click()

    def hover_over(self, locator: Locator) -> None:
        """Hover mouse over an element (for dropdown menus etc.)."""
        element = self.find_element(locator)
        self.actions.move_to_element(element).perform()

    def double_click(self, locator: Locator) -> None:
        """Double-click an element."""
        element = self.wait.wait_for_element_clickable(locator)
        self.actions.double_click(element).perform()

    def right_click(self, locator: Locator) -> None:
        """Right-click (context menu) on an element."""
        element = self.find_element(locator)
        self.actions.context_click(element).perform()

    def drag_and_drop(self, source_locator: Locator, target_locator: Locator) -> None:
        """Drag element from source to target."""
        source = self.find_element(source_locator)
        target = self.find_element(target_locator)
        self.actions.drag_and_drop(source, target).perform()

    def press_enter(self, locator: Locator) -> None:
        """Press Enter key on an element."""
        self.find_element(locator).send_keys(Keys.ENTER)

    def press_tab(self, locator: Locator) -> None:
        """Press Tab key on an element."""
        self.find_element(locator).send_keys(Keys.TAB)

    def scroll_to_element(self, locator: Locator) -> None:
        """Scroll element into viewport."""
        element = self.find_element(locator)
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)

    def scroll_to_top(self) -> None:
        """Scroll to top of page."""
        self.driver.execute_script("window.scrollTo(0, 0);")

    def scroll_to_bottom(self) -> None:
        """Scroll to bottom of page."""
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    # ─────────────────────────────────────────────────────────
    # JavaScript Helpers
    # ─────────────────────────────────────────────────────────

    def js_click(self, locator: Locator) -> None:
        """Click element via JavaScript (bypasses overlay issues)."""
        element = self.find_element(locator)
        self.driver.execute_script("arguments[0].click();", element)
        logger.debug("JS-clicked: %s", locator)

    def js_set_value(self, locator: Locator, value: str) -> None:
        """Set input value via JavaScript."""
        element = self.find_element(locator)
        self.driver.execute_script(f"arguments[0].value='{value}';", element)

    def js_scroll_to(self, x: int, y: int) -> None:
        """Scroll to specific coordinates."""
        self.driver.execute_script(f"window.scrollTo({x}, {y});")

    def execute_script(self, script: str, *args) -> any:
        """Execute arbitrary JavaScript."""
        return self.driver.execute_script(script, *args)

    # ─────────────────────────────────────────────────────────
    # Wait Methods
    # ─────────────────────────────────────────────────────────

    def wait_for_page_load(self, timeout: Optional[int] = None) -> None:
        """Wait until document.readyState is 'complete'."""
        self.wait.wait_for_page_load(timeout)

    def wait_for_element(self, locator: Locator, timeout: Optional[int] = None) -> WebElement:
        """Wait for element to be clickable (preferred for actions)."""
        return self.wait.wait_for_element_clickable(locator, timeout)

    def wait_for_text(self, locator: Locator, text: str, timeout: Optional[int] = None) -> bool:
        """Wait until element contains expected text."""
        return self.wait.wait_for_text_in_element(locator, text, timeout)

    def wait_for_url(self, url_fragment: str, timeout: Optional[int] = None) -> bool:
        """Wait until URL contains given fragment."""
        return self.wait.wait_for_url_contains(url_fragment, timeout)

    def wait_for_disappear(self, locator: Locator, timeout: Optional[int] = None) -> bool:
        """Wait until element disappears (e.g., loading spinners)."""
        return self.wait.wait_for_element_invisible(locator, timeout)

    # ─────────────────────────────────────────────────────────
    # Alert / Popup Handling
    # ─────────────────────────────────────────────────────────

    def accept_alert(self, timeout: int = 5) -> str:
        """Accept browser alert and return its text."""
        alert = self.wait.wait_for_alert(timeout)
        text = alert.text
        alert.accept()
        logger.debug("Alert accepted: '%s'", text)
        return text

    def dismiss_alert(self, timeout: int = 5) -> str:
        """Dismiss browser alert/confirm dialog."""
        alert = self.wait.wait_for_alert(timeout)
        text = alert.text
        alert.dismiss()
        logger.debug("Alert dismissed: '%s'", text)
        return text

    def switch_to_frame(self, locator: Locator) -> None:
        """Switch WebDriver context into an iframe."""
        frame = self.find_element(locator)
        self.driver.switch_to.frame(frame)

    def switch_to_default_content(self) -> None:
        """Switch back to main document from iframe."""
        self.driver.switch_to.default_content()

    def switch_to_new_window(self) -> None:
        """Switch to the most recently opened window/tab."""
        self.driver.switch_to.window(self.driver.window_handles[-1])

    def close_current_window_and_switch_back(self) -> None:
        """Close current window and switch to previous."""
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])

    # ─────────────────────────────────────────────────────────
    # Screenshot & Reporting
    # ─────────────────────────────────────────────────────────

    def take_screenshot(self, name: str) -> str:
        """
        Capture screenshot and return file path.

        Args:
            name: Descriptive screenshot name

        Returns:
            str: Absolute path to screenshot file
        """
        path = self.screenshot.capture(name, subfolder=self.__class__.__name__)
        return str(path)

    # ─────────────────────────────────────────────────────────
    # Stale Element Recovery
    # ─────────────────────────────────────────────────────────

    def safe_click(self, locator: Locator, max_attempts: int = 3) -> None:
        """
        Click with stale element retry — handles DOM re-renders.

        Args:
            locator: Element locator
            max_attempts: Max retry count for stale element

        WHEN TO USE:
            Pages that re-render (SPA frameworks like React/Vue)
            where elements briefly disappear and reappear in DOM.
        """
        for attempt in range(1, max_attempts + 1):
            try:
                self.click(locator)
                return
            except StaleElementReferenceException:
                if attempt == max_attempts:
                    raise
                logger.warning("Stale element, retrying click (attempt %d)", attempt)
                sleep(0.5, reason=f"Wait for DOM re-render before retrying click on {locator}")

    def safe_get_text(self, locator: Locator, max_attempts: int = 3) -> str:
        """Get element text with stale element retry."""
        for attempt in range(1, max_attempts + 1):
            try:
                return self.get_text(locator)
            except StaleElementReferenceException:
                if attempt == max_attempts:
                    raise
                sleep(0.3, reason=f"Wait for DOM re-render before retrying get_text on {locator}")
        return ""

    # ─────────────────────────────────────────────────────────
    # Assertions (Page-level)
    # ─────────────────────────────────────────────────────────

    def assert_page_title(self, expected_title: str) -> None:
        """Assert page title matches expected value."""
        actual = self.get_page_title()
        assert expected_title in actual, (
            f"Page title mismatch. Expected '{expected_title}' in '{actual}'"
        )

    def assert_url_contains(self, expected_fragment: str) -> None:
        """Assert current URL contains expected fragment."""
        actual = self.get_current_url()
        assert expected_fragment in actual, (
            f"URL mismatch. Expected '{expected_fragment}' in '{actual}'"
        )

    def assert_element_text(self, locator: Locator, expected_text: str) -> None:
        """Assert element contains expected text."""
        actual = self.get_text(locator)
        assert expected_text in actual, (
            f"Text mismatch. Expected '{expected_text}' in '{actual}'"
        )
