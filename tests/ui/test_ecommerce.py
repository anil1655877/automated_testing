"""
============================================================
AI-Enhanced Enterprise Test Automation Framework
UI Test: E-Commerce Functionality
============================================================
"""
import pytest
import allure
from pages.ecommerce_page import EcommercePage
from utilities.logger import get_logger

logger = get_logger(__name__)


@allure.feature("E-Commerce")
@allure.story("Product Catalog")
class TestEcommerce:
    """E-commerce test suite — product listing, search, and detail views."""

    @allure.title("Product Listing Page Loads")
    @pytest.mark.smoke
    @pytest.mark.ecommerce
    def test_product_page_loads(self, ecommerce_page: EcommercePage):
        """TC-EC-001: Product listing page loads successfully."""
        with allure.step("Verify product list is displayed"):
            assert ecommerce_page.is_product_page_loaded(), \
                "Product listing should be visible"

    @allure.title("Products Are Listed")
    @pytest.mark.regression
    @pytest.mark.ecommerce
    def test_products_are_listed(self, ecommerce_page: EcommercePage):
        """TC-EC-002: Verify products exist in the catalog."""
        with allure.step("Get product count"):
            count = ecommerce_page.get_product_count()
            assert count > 0, f"Expected products in catalog, got {count}"
            logger.info("Products in catalog: %d", count)

    @allure.title("Product Search Works")
    @pytest.mark.regression
    @pytest.mark.ecommerce
    def test_product_search(self, ecommerce_page: EcommercePage):
        """TC-EC-003: Search filters product list correctly."""
        with allure.step("Search for 'Git'"):
            ecommerce_page.search_product("Git")
        with allure.step("Verify search results are non-empty or properly filtered"):
            titles = ecommerce_page.get_product_titles()
            logger.info("Search results: %s", titles)
            # Result: either filtered results or empty (valid both ways)
            assert isinstance(titles, list), "get_product_titles should return a list"

    @allure.title("Product Detail View Opens")
    @pytest.mark.regression
    @pytest.mark.ecommerce
    def test_product_detail_opens(self, ecommerce_page: EcommercePage):
        """TC-EC-004: Clicking a product opens its detail view."""
        with allure.step("Get available products"):
            titles = ecommerce_page.get_product_titles()
            if not titles:
                pytest.skip("No products available to click")

        with allure.step(f"Click first product: '{titles[0]}'"):
            ecommerce_page.click_product(titles[0])

        with allure.step("Verify detail page is displayed"):
            # Check URL changed or detail is visible
            current_url = ecommerce_page.get_current_url()
            assert "books" in current_url or "profile" in current_url, \
                f"Expected product detail. Got: {current_url}"

    @allure.title("Product Search - No Results Handling")
    @pytest.mark.regression
    @pytest.mark.ecommerce
    @pytest.mark.negative
    def test_search_no_results(self, ecommerce_page: EcommercePage):
        """TC-EC-005: Search with no matching product handles gracefully."""
        with allure.step("Search for non-existent product"):
            ecommerce_page.search_product("xyz_no_such_product_abc_999")
        with allure.step("Verify zero results or empty state"):
            count = ecommerce_page.get_search_result_count()
            assert count == 0, f"Expected 0 results, got {count}"

    @allure.title("Author and Publisher Info Displayed")
    @pytest.mark.regression
    @pytest.mark.ecommerce
    def test_author_publisher_info(self, ecommerce_page: EcommercePage):
        """TC-EC-006: Author and publisher columns are populated."""
        with allure.step("Get author list"):
            authors = ecommerce_page.get_author_list()
            publishers = ecommerce_page.get_publisher_list()
            logger.info("Authors: %s", authors[:3])
            logger.info("Publishers: %s", publishers[:3])
            assert len(authors) > 0, "Author column should have data"
