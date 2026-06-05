"""
============================================================
AI-Enhanced Enterprise Test Automation Framework
Dashboard Page Object
============================================================
"""
from selenium.webdriver.common.by import By
from pages.base_page import BasePage
from config.config import BASE_URL
from utilities.logger import get_logger

logger = get_logger(__name__)


class DashboardPage(BasePage):
    """Page Object for the main Dashboard / Books Store page."""

    PAGE_URL = f"{BASE_URL}/books"

    # ─── Locators ────────────────────────────────────────────
    HEADER_TITLE       = (By.CSS_SELECTOR, ".main-header")
    USER_GREETING      = (By.CSS_SELECTOR, "#userName-value, .user-name")
    LOGOUT_BUTTON      = (By.ID, "submit")
    PROFILE_LINK       = (By.CSS_SELECTOR, "a[href*='profile']")
    SEARCH_INPUT       = (By.ID, "searchBox")
    BOOK_TABLE         = (By.CSS_SELECTOR, ".ReactTable")
    BOOK_ROWS          = (By.CSS_SELECTOR, ".rt-tr-group")
    BOOK_TITLE_CELLS   = (By.CSS_SELECTOR, ".rt-td a")
    BOOK_AUTHOR_CELLS  = (By.CSS_SELECTOR, ".rt-td:nth-child(3)")
    ROWS_PER_PAGE      = (By.CSS_SELECTOR, "select[aria-label='rows per page']")
    PAGE_NUMBER        = (By.CSS_SELECTOR, ".-pageInfo")
    NEXT_PAGE_BTN      = (By.CSS_SELECTOR, ".-next button")
    PREV_PAGE_BTN      = (By.CSS_SELECTOR, ".-previous button")
    TOTAL_BOOKS_COUNT  = (By.CSS_SELECTOR, ".-totalCount")
    LOADING_SPINNER    = (By.CSS_SELECTOR, ".loading, .-loading")
    CATEGORY_LINKS     = (By.CSS_SELECTOR, "#item-0 .menu-list")

    # ─── Navigation ──────────────────────────────────────────

    def navigate(self) -> "DashboardPage":
        """Navigate to the dashboard/books page."""
        self.navigate_to(self.PAGE_URL)
        self.wait_for_page_load()
        logger.info("Navigated to Dashboard")
        return self

    def logout(self) -> None:
        """Perform logout action."""
        self.click(self.LOGOUT_BUTTON)
        logger.info("Logout clicked")

    def go_to_profile(self) -> None:
        """Navigate to user profile page."""
        self.click(self.PROFILE_LINK)

    # ─── Search ──────────────────────────────────────────────

    def search_book(self, keyword: str) -> "DashboardPage":
        """
        Search for a book by keyword.

        Args:
            keyword: Search term (title, author, publisher)
        """
        self.type_text(self.SEARCH_INPUT, keyword)
        logger.info("Searched for: '%s'", keyword)
        return self

    def clear_search(self) -> "DashboardPage":
        """Clear the search box."""
        self.type_text(self.SEARCH_INPUT, "", clear_first=True)
        return self

    # ─── Book List ───────────────────────────────────────────

    def get_book_titles(self) -> list[str]:
        """Get list of all visible book titles."""
        elements = self.find_elements(self.BOOK_TITLE_CELLS)
        return [el.text.strip() for el in elements if el.text.strip()]

    def get_book_count(self) -> int:
        """Get count of books currently displayed."""
        return len(self.find_elements(self.BOOK_ROWS))

    def click_book_by_title(self, title: str) -> None:
        """Click a book link by its exact title."""
        locator = (By.LINK_TEXT, title)
        self.click(locator)
        logger.info("Clicked book: '%s'", title)

    def is_book_visible(self, title: str) -> bool:
        """Check if a book with given title is in the list."""
        titles = self.get_book_titles()
        return any(title.lower() in t.lower() for t in titles)

    def get_search_results_count(self) -> int:
        """Get count of books after search."""
        return len([t for t in self.get_book_titles() if t])

    # ─── Pagination ──────────────────────────────────────────

    def go_to_next_page(self) -> None:
        """Click Next page button."""
        self.click(self.NEXT_PAGE_BTN)
        self.wait_for_page_load()

    def go_to_prev_page(self) -> None:
        """Click Previous page button."""
        self.click(self.PREV_PAGE_BTN)

    def set_rows_per_page(self, count: int) -> None:
        """Set number of rows displayed per page."""
        self.select_dropdown_by_value(self.ROWS_PER_PAGE, str(count))

    # ─── State Verification ──────────────────────────────────

    def is_dashboard_loaded(self) -> bool:
        """Check if dashboard is loaded successfully."""
        return self.is_element_visible(self.BOOK_TABLE, timeout=15)

    def is_user_logged_in(self) -> bool:
        """Check if user appears logged in on dashboard."""
        return self.is_element_visible(self.LOGOUT_BUTTON, timeout=10)

    def get_logged_in_user(self) -> str:
        """Get the logged-in username from header."""
        if self.is_element_visible(self.USER_GREETING, timeout=5):
            return self.get_text(self.USER_GREETING)
        return ""

    def wait_for_books_to_load(self) -> "DashboardPage":
        """Wait until book table is populated."""
        self.wait_for_disappear(self.LOADING_SPINNER, timeout=15)
        self.wait_for_element(self.BOOK_TABLE)
        return self
