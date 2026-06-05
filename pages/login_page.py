"""
============================================================
AI-Enhanced Enterprise Test Automation Framework
Login Page Object
============================================================
Encapsulates all interactions with the Login page.
Uses DemoQA as a concrete real-world example target.
============================================================
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from pages.base_page import BasePage
from config.config import BASE_URL
from utilities.logger import get_logger

logger = get_logger(__name__)


class LoginPage(BasePage):
    """
    Page Object for the Login page.

    POM PRINCIPLE: All locators and actions related to login
    live here. Tests only call methods like login(), not
    raw Selenium find/click commands.

    TARGET: https://demoqa.com/login (default dev env)
    """

    # ─── Page URL ────────────────────────────────────────────
    PAGE_URL = f"{BASE_URL}/login"

    # ─── Locators ────────────────────────────────────────────
    # Format: ELEMENT_NAME = (By.*, "selector")
    # WHY TUPLES: Easy to swap locator strategy without changing tests

    USERNAME_INPUT = (By.ID, "userName")
    PASSWORD_INPUT = (By.ID, "password")
    LOGIN_BUTTON   = (By.ID, "login")
    LOGIN_HEADER   = (By.CSS_SELECTOR, "h5.text-center")

    # Success indicators
    PROFILE_USERNAME = (By.ID, "userName-value")
    LOGOUT_BUTTON    = (By.ID, "submit")

    # Error indicators
    ERROR_MESSAGE    = (By.CSS_SELECTOR, ".text-danger, #errorMessage, [class*='error']")
    INVALID_STYLE    = (By.CSS_SELECTOR, "input.is-invalid")

    # Form elements
    FORGOT_PASSWORD  = (By.CSS_SELECTOR, "a[href*='forgot']")
    REGISTER_LINK    = (By.ID, "newUser")

    # ─── Page Actions ────────────────────────────────────────

    def navigate(self) -> "LoginPage":
        """Navigate to the login page."""
        self.navigate_to(self.PAGE_URL)
        logger.info("Navigated to Login page: %s", self.PAGE_URL)
        return self

    def enter_username(self, username: str) -> "LoginPage":
        """Type username into the username field."""
        self.type_text(self.USERNAME_INPUT, username)
        logger.debug("Entered username: %s", username)
        return self  # Fluent interface — enables method chaining

    def enter_password(self, password: str) -> "LoginPage":
        """Type password into the password field."""
        self.type_text(self.PASSWORD_INPUT, password)
        logger.debug("Entered password: [MASKED]")
        return self

    def click_login(self) -> "LoginPage":
        """Click the Login submit button."""
        self.click(self.LOGIN_BUTTON)
        logger.info("Login button clicked")
        return self

    def login(self, username: str, password: str) -> "LoginPage":
        """
        Complete login flow: enter credentials and submit.

        FLUENT INTERFACE PATTERN:
            page.login("user@test.com", "Pass@123")
            # Equivalent to:
            page.enter_username("user@test.com")
                .enter_password("Pass@123")
                .click_login()

        Args:
            username: Login email/username
            password: Login password

        Returns:
            self (for method chaining)
        """
        return self.enter_username(username).enter_password(password).click_login()

    def click_new_user(self) -> None:
        """Click 'New User' / Register link."""
        self.click(self.REGISTER_LINK)

    # ─── State Verification ──────────────────────────────────

    def is_login_page_displayed(self) -> bool:
        """Return True if the login page header/form is visible."""
        return self.is_element_visible(self.USERNAME_INPUT, timeout=10)

    def is_logged_in(self) -> bool:
        """
        Check if login was successful by verifying post-login indicators.

        STRATEGY: Check URL change AND presence of profile element.
        Dual-check makes this more reliable than URL alone.
        """
        try:
            # Wait for URL to change away from /login
            self.wait_for_url("/books", timeout=10)
            return True
        except Exception:
            # Fallback: check for profile username display
            return self.is_element_visible(self.PROFILE_USERNAME, timeout=5)

    def get_error_message(self) -> str:
        """
        Get the login error message text.

        Returns:
            str: Error message text, or empty string if no error
        """
        if self.is_element_visible(self.ERROR_MESSAGE, timeout=5):
            return self.get_text(self.ERROR_MESSAGE)
        return ""

    def is_error_displayed(self) -> bool:
        """Return True if an error message is visible."""
        return bool(self.get_error_message())

    def get_username_field_value(self) -> str:
        """Get current value of username input."""
        return self.get_input_value(self.USERNAME_INPUT)

    def get_password_field_value(self) -> str:
        """Get current value of password input."""
        return self.get_input_value(self.PASSWORD_INPUT)

    def is_login_button_enabled(self) -> bool:
        """Check if Login button is enabled (not disabled)."""
        element = self.find_element(self.LOGIN_BUTTON)
        return element.is_enabled()

    def clear_form(self) -> "LoginPage":
        """Clear both username and password fields."""
        self.type_text(self.USERNAME_INPUT, "", clear_first=True)
        self.type_text(self.PASSWORD_INPUT, "", clear_first=True)
        return self

    def get_logged_in_username(self) -> str:
        """Get the displayed username after successful login."""
        if self.is_element_visible(self.PROFILE_USERNAME, timeout=10):
            return self.get_text(self.PROFILE_USERNAME)
        return ""
