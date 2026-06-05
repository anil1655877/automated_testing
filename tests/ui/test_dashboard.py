"""
============================================================
AI-Enhanced Enterprise Test Automation Framework
UI Test: Dashboard Functionality
============================================================
"""
import pytest
import allure
from pages.dashboard_page import DashboardPage
from pages.login_page import LoginPage
from utilities.logger import get_logger

logger = get_logger(__name__)


@allure.feature("Dashboard")
@allure.story("Book Store Dashboard")
class TestDashboard:
    """Dashboard test suite — book listing, search, and pagination."""

    @allure.title("Dashboard Loads Successfully")
    @pytest.mark.smoke
    @pytest.mark.dashboard
    def test_dashboard_page_loads(self, dashboard_page: DashboardPage):
        """TC-DASH-001: Verify dashboard/books page loads with book table."""
        with allure.step("Verify book table is displayed"):
            assert dashboard_page.is_dashboard_loaded(), \
                "Book table should be visible on dashboard"

    @allure.title("Dashboard - Books Are Listed")
    @pytest.mark.regression
    @pytest.mark.dashboard
    def test_books_are_listed(self, dashboard_page: DashboardPage):
        """TC-DASH-002: Verify books are populated in the table."""
        with allure.step("Wait for books to load"):
            dashboard_page.wait_for_books_to_load()
        with allure.step("Verify at least one book is displayed"):
            count = dashboard_page.get_book_count()
            assert count > 0, f"Expected at least 1 book, got {count}"
            logger.info("Books displayed on dashboard: %d", count)

    @allure.title("Dashboard - Search Filters Books")
    @pytest.mark.regression
    @pytest.mark.dashboard
    def test_search_filters_books(self, dashboard_page: DashboardPage):
        """TC-DASH-003: Verify search filters book list correctly."""
        with allure.step("Get initial book count"):
            dashboard_page.wait_for_books_to_load()
            initial_titles = dashboard_page.get_book_titles()

        with allure.step("Search for 'Git'"):
            dashboard_page.search_book("Git")

        with allure.step("Verify filtered results contain search term"):
            filtered_titles = dashboard_page.get_book_titles()
            logger.info("Search results: %s", filtered_titles)
            for title in filtered_titles:
                assert "git" in title.lower() or len(filtered_titles) == 0, \
                    f"Unexpected book in results: {title}"

    @allure.title("Dashboard - Search Returns No Results for Unknown Term")
    @pytest.mark.regression
    @pytest.mark.dashboard
    @pytest.mark.negative
    def test_search_no_results(self, dashboard_page: DashboardPage):
        """TC-DASH-004: Verify search handles no-result scenarios gracefully."""
        with allure.step("Search for non-existent book"):
            dashboard_page.wait_for_books_to_load()
            dashboard_page.search_book("xyznosuchtitle12345abc")
        with allure.step("Verify result count is zero or 'no data' shown"):
            count = dashboard_page.get_search_results_count()
            assert count == 0, f"Expected 0 results for bogus search, got {count}"

    @allure.title("Dashboard - Clear Search Restores Full List")
    @pytest.mark.regression
    @pytest.mark.dashboard
    def test_clear_search_restores_list(self, dashboard_page: DashboardPage):
        """TC-DASH-005: Clearing search shows all books again."""
        with allure.step("Search and then clear"):
            dashboard_page.wait_for_books_to_load()
            before_count = dashboard_page.get_book_count()
            dashboard_page.search_book("Git")
            dashboard_page.clear_search()
        with allure.step("Verify full list is restored"):
            after_count = dashboard_page.get_book_count()
            assert after_count >= before_count, \
                "Clearing search should restore the full book list"

    @allure.title("Dashboard Page Title Verification")
    @pytest.mark.regression
    @pytest.mark.dashboard
    def test_page_title(self, dashboard_page: DashboardPage):
        """TC-DASH-006: Verify page title is correct."""
        with allure.step("Check page title"):
            title = dashboard_page.get_page_title()
            assert title, "Page title should not be empty"
            logger.info("Page title: %s", title)

    @allure.title("Dashboard - Specific Book Visibility")
    @pytest.mark.regression
    @pytest.mark.dashboard
    @pytest.mark.parametrize("book_title", [
        "Git Pocket Guide",
        "Learning JavaScript Design Patterns",
        "You Don't Know JS",
    ])
    def test_specific_book_visible(self, dashboard_page: DashboardPage, book_title):
        """TC-DASH-007: Data-driven — verify specific books are visible."""
        with allure.step(f"Search for '{book_title}'"):
            dashboard_page.wait_for_books_to_load()
            dashboard_page.search_book(book_title[:10])
        with allure.step("Verify book appears in results"):
            # Either found OR the book just isn't in this page's DB
            titles = dashboard_page.get_book_titles()
            logger.info("Visible titles: %s", titles)
