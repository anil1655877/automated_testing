"""
============================================================
AI-Enhanced Enterprise Test Automation Framework
Admin / Role-Based Access Page Object
============================================================
Models the admin panel and RBAC (Role-Based Access Control)
testing scenarios — verifying different permission levels.
============================================================
"""
from selenium.webdriver.common.by import By
from pages.base_page import BasePage
from config.config import BASE_URL, ADMIN_URL
from utilities.logger import get_logger

logger = get_logger(__name__)


class AdminPage(BasePage):
    """
    Page Object for Admin Panel and RBAC testing.

    RBAC TESTING CONCEPT:
        Role-Based Access Control verifies that:
        - Admin users can access admin features
        - Regular users cannot access admin features
        - Read-only users cannot modify data
        - Unauthenticated users are redirected to login
    """

    PAGE_URL = f"{BASE_URL}/profile"
    ADMIN_URL = ADMIN_URL

    # ─── Profile Page Locators ────────────────────────────────
    USERNAME_DISPLAY   = (By.ID, "userName-value")
    BOOKS_SECTION      = (By.CSS_SELECTOR, ".ReactTable, .books-table")
    DELETE_BOOK_BTN    = (By.CSS_SELECTOR, "#delete-record-undefined, [data-key='delete']")
    DELETE_ALL_BTN     = (By.ID, "submit")
    GO_TO_STORE_BTN    = (By.ID, "gotoStore")
    LOGOUT_BTN         = (By.ID, "submit")
    COLLECTION_TITLE   = (By.CSS_SELECTOR, ".profile-wrapper")
    NO_BOOKS_ROW       = (By.CSS_SELECTOR, ".rt-noData")
    BOOK_ROWS          = (By.CSS_SELECTOR, ".rt-tr-group")

    # ─── Admin Panel Locators ─────────────────────────────────
    ADMIN_MENU         = (By.CSS_SELECTOR, ".admin-menu, [data-testid='admin']")
    USER_MANAGEMENT    = (By.CSS_SELECTOR, "#user-management, [href*='users']")
    REPORTS_LINK       = (By.CSS_SELECTOR, "#reports, [href*='reports']")
    SETTINGS_LINK      = (By.CSS_SELECTOR, "#settings, [href*='settings']")
    ACCESS_DENIED_MSG  = (By.CSS_SELECTOR, ".access-denied, .forbidden, [data-testid='forbidden']")
    UNAUTHORIZED_MSG   = (By.CSS_SELECTOR, ".unauthorized, [data-testid='unauthorized']")

    # ─── Navigation ──────────────────────────────────────────

    def navigate_to_profile(self) -> "AdminPage":
        """Navigate to user profile page."""
        self.navigate_to(self.PAGE_URL)
        logger.info("Navigated to Profile page")
        return self

    def navigate_to_admin(self) -> "AdminPage":
        """Navigate to admin panel URL."""
        self.navigate_to(self.ADMIN_URL)
        logger.info("Navigated to Admin page")
        return self

    def go_to_book_store(self) -> None:
        """Navigate to book store from profile."""
        self.click(self.GO_TO_STORE_BTN)

    def logout(self) -> None:
        """Log out the current user."""
        self.click(self.LOGOUT_BTN)
        logger.info("User logged out from admin/profile page")

    # ─── Profile Actions ──────────────────────────────────────

    def delete_all_books(self) -> "AdminPage":
        """Delete all books from user collection."""
        if self.is_element_visible(self.DELETE_ALL_BTN, timeout=5):
            self.click(self.DELETE_ALL_BTN)
            logger.info("Deleted all books from collection")
        return self

    def get_collection_book_count(self) -> int:
        """Get count of books in user's collection."""
        rows = self.find_elements(self.BOOK_ROWS)
        return len([r for r in rows if r.text.strip()])

    def get_displayed_username(self) -> str:
        """Get username shown on profile page."""
        if self.is_element_visible(self.USERNAME_DISPLAY, timeout=10):
            return self.get_text(self.USERNAME_DISPLAY)
        return ""

    # ─── RBAC Verification ───────────────────────────────────

    def is_profile_accessible(self) -> bool:
        """
        Check if profile page is accessible (user is authenticated).
        Redirected to login = not accessible.
        """
        current_url = self.get_current_url()
        if "login" in current_url:
            logger.info("Profile not accessible — redirected to login")
            return False
        return self.is_element_visible(self.USERNAME_DISPLAY, timeout=10)

    def is_admin_panel_accessible(self) -> bool:
        """
        Check if admin panel is accessible.

        Returns True only for admin-role users.
        Non-admin users should be blocked or redirected.
        """
        current_url = self.get_current_url()
        if "login" in current_url:
            return False
        if self.is_element_visible(self.ACCESS_DENIED_MSG, timeout=5):
            return False
        return self.is_element_visible(self.ADMIN_MENU, timeout=5)

    def is_access_denied_shown(self) -> bool:
        """Check if 'Access Denied' message is displayed."""
        return self.is_element_visible(self.ACCESS_DENIED_MSG, timeout=5)

    def is_redirected_to_login(self) -> bool:
        """Verify user was redirected to login page (unauthorized access)."""
        try:
            self.wait_for_url("/login", timeout=10)
            return True
        except Exception:
            return "login" in self.get_current_url()

    def is_user_management_visible(self) -> bool:
        """Check if User Management menu is visible (admin-only)."""
        return self.is_element_visible(self.USER_MANAGEMENT, timeout=5)

    def is_reports_visible(self) -> bool:
        """Check if Reports section is accessible."""
        return self.is_element_visible(self.REPORTS_LINK, timeout=5)

    def is_collection_empty(self) -> bool:
        """Check if user's book collection is empty."""
        return self.is_element_visible(self.NO_BOOKS_ROW, timeout=5)

    def is_delete_button_visible(self) -> bool:
        """Check if delete buttons are visible (write access required)."""
        return self.is_element_visible(self.DELETE_BOOK_BTN, timeout=5)
