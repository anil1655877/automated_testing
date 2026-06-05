"""
============================================================
AI-Enhanced Enterprise Test Automation Framework
Registration Page Object
============================================================
Encapsulates all interactions with the User Registration page.
============================================================
"""
from selenium.webdriver.common.by import By
from pages.base_page import BasePage
from config.config import BASE_URL
from utilities.logger import get_logger

logger = get_logger(__name__)


class RegistrationPage(BasePage):
    """Page Object for the User Registration / New User page."""

    PAGE_URL = f"{BASE_URL}/register"

    # ─── Locators ────────────────────────────────────────────
    FIRST_NAME_INPUT   = (By.ID, "firstname")
    LAST_NAME_INPUT    = (By.ID, "lastname")
    USERNAME_INPUT     = (By.ID, "userName")
    PASSWORD_INPUT     = (By.ID, "password")
    CAPTCHA_CHECKBOX   = (By.CSS_SELECTOR, "div.recaptcha-checkbox-border")
    REGISTER_BUTTON    = (By.ID, "register")
    BACK_TO_LOGIN_BTN  = (By.ID, "gotologin")
    PAGE_HEADER        = (By.CSS_SELECTOR, "h5.text-center")

    # Success/Error indicators
    SUCCESS_MESSAGE    = (By.ID, "output")
    ERROR_MESSAGE      = (By.CSS_SELECTOR, ".text-danger, #errorMessage, [class*='error']")
    FIELD_ERROR        = (By.CSS_SELECTOR, "input.is-invalid")

    # ─── Page Actions ────────────────────────────────────────

    def navigate(self) -> "RegistrationPage":
        """Navigate to the registration page."""
        self.navigate_to(self.PAGE_URL)
        logger.info("Navigated to Registration page")
        return self

    def enter_first_name(self, first_name: str) -> "RegistrationPage":
        self.type_text(self.FIRST_NAME_INPUT, first_name)
        return self

    def enter_last_name(self, last_name: str) -> "RegistrationPage":
        self.type_text(self.LAST_NAME_INPUT, last_name)
        return self

    def enter_username(self, username: str) -> "RegistrationPage":
        self.type_text(self.USERNAME_INPUT, username)
        return self

    def enter_password(self, password: str) -> "RegistrationPage":
        self.type_text(self.PASSWORD_INPUT, password)
        return self

    def click_register(self) -> "RegistrationPage":
        self.click(self.REGISTER_BUTTON)
        logger.info("Register button clicked")
        return self

    def fill_registration_form(
        self,
        first_name: str,
        last_name: str,
        username: str,
        password: str,
    ) -> "RegistrationPage":
        """
        Fill all registration form fields.

        Args:
            first_name: User's first name
            last_name: User's last name
            username: Desired username
            password: Password (must meet complexity requirements)
        """
        return (
            self.enter_first_name(first_name)
                .enter_last_name(last_name)
                .enter_username(username)
                .enter_password(password)
        )

    def click_back_to_login(self) -> None:
        """Click 'Back to Login' button."""
        self.click(self.BACK_TO_LOGIN_BTN)

    # ─── State Verification ──────────────────────────────────

    def is_registration_page_displayed(self) -> bool:
        """Check if registration page is displayed."""
        return self.is_element_visible(self.FIRST_NAME_INPUT, timeout=10)

    def is_registration_successful(self) -> bool:
        """Check if registration completed successfully."""
        return self.is_element_visible(self.SUCCESS_MESSAGE, timeout=10)

    def get_success_message(self) -> str:
        """Return success message text."""
        if self.is_element_visible(self.SUCCESS_MESSAGE, timeout=5):
            return self.get_text(self.SUCCESS_MESSAGE)
        return ""

    def get_error_message(self) -> str:
        """Return error message text."""
        if self.is_element_visible(self.ERROR_MESSAGE, timeout=5):
            return self.get_text(self.ERROR_MESSAGE)
        return ""

    def has_invalid_fields(self) -> bool:
        """Check if any fields show validation errors."""
        return len(self.find_elements(self.FIELD_ERROR)) > 0

    def is_register_button_enabled(self) -> bool:
        """Check if the Register button is enabled."""
        element = self.find_element(self.REGISTER_BUTTON)
        return element.is_enabled()

    def get_username_value(self) -> str:
        """Get current value of username field."""
        return self.get_input_value(self.USERNAME_INPUT)
