"""
============================================================
AI-Enhanced Enterprise Test Automation Framework
E-Commerce Page Object
============================================================
Models a full e-commerce product catalog and cart workflow.
Uses DemoQA elements as demonstration targets.
============================================================
"""
from selenium.webdriver.common.by import By
from pages.base_page import BasePage
from config.config import BASE_URL
from utilities.logger import get_logger

logger = get_logger(__name__)


class EcommercePage(BasePage):
    """Page Object for E-Commerce product browsing and cart flows."""

    PAGE_URL = f"{BASE_URL}/books"

    # ─── Locators ────────────────────────────────────────────
    PRODUCT_LIST       = (By.CSS_SELECTOR, ".ReactTable, .product-grid, .books-wrapper")
    PRODUCT_ITEMS      = (By.CSS_SELECTOR, ".rt-tr-group, .product-item")
    PRODUCT_TITLES     = (By.CSS_SELECTOR, ".rt-td a, .product-title")
    PRODUCT_PRICES     = (By.CSS_SELECTOR, ".rt-td:nth-child(4), .product-price")
    SEARCH_INPUT       = (By.ID, "searchBox")
    CART_ICON          = (By.CSS_SELECTOR, ".cart-icon, #addToCart, [data-testid='cart']")
    CART_COUNT_BADGE   = (By.CSS_SELECTOR, ".cart-count, .badge")
    CHECKOUT_BTN       = (By.CSS_SELECTOR, "#checkout, .checkout-btn")
    SORT_DROPDOWN      = (By.CSS_SELECTOR, "select.sort, [data-testid='sort']")
    CATEGORY_FILTER    = (By.CSS_SELECTOR, ".category-filter, [data-testid='category']")
    PRICE_RANGE_MIN    = (By.CSS_SELECTOR, "[data-testid='price-min']")
    PRICE_RANGE_MAX    = (By.CSS_SELECTOR, "[data-testid='price-max']")
    EMPTY_CART_MSG     = (By.CSS_SELECTOR, ".empty-cart, [data-testid='empty-cart']")
    PRODUCT_DETAIL     = (By.CSS_SELECTOR, ".profile-wrapper, .product-detail")
    ADD_TO_COLLECTION  = (By.CSS_SELECTOR, "#addNewRecordButton, .add-to-collection")
    BACK_BTN           = (By.CSS_SELECTOR, "#backButton, .back-to-book-store")
    PUBLISHER_COL      = (By.CSS_SELECTOR, ".rt-td:nth-child(5)")
    AUTHOR_COL         = (By.CSS_SELECTOR, ".rt-td:nth-child(3)")

    # ─── Navigation ──────────────────────────────────────────

    def navigate(self) -> "EcommercePage":
        """Navigate to the e-commerce/product listing page."""
        self.navigate_to(self.PAGE_URL)
        self.wait_for_element(self.PRODUCT_LIST)
        logger.info("Navigated to E-Commerce page")
        return self

    # ─── Search & Filter ─────────────────────────────────────

    def search_product(self, keyword: str) -> "EcommercePage":
        """Search for a product."""
        self.type_text(self.SEARCH_INPUT, keyword)
        logger.info("Searching product: '%s'", keyword)
        return self

    def select_category(self, category: str) -> "EcommercePage":
        """Filter by category."""
        if self.is_element_visible(self.CATEGORY_FILTER, timeout=3):
            self.select_dropdown_by_text(self.CATEGORY_FILTER, category)
        return self

    def sort_by(self, option: str) -> "EcommercePage":
        """Sort products by the given option."""
        if self.is_element_visible(self.SORT_DROPDOWN, timeout=3):
            self.select_dropdown_by_text(self.SORT_DROPDOWN, option)
        return self

    def set_price_range(self, min_price: str, max_price: str) -> "EcommercePage":
        """Set price filter range."""
        if self.is_element_visible(self.PRICE_RANGE_MIN, timeout=3):
            self.type_text(self.PRICE_RANGE_MIN, min_price)
            self.type_text(self.PRICE_RANGE_MAX, max_price)
        return self

    # ─── Product Interactions ─────────────────────────────────

    def get_product_titles(self) -> list[str]:
        """Get all visible product/book titles."""
        elements = self.find_elements(self.PRODUCT_TITLES)
        return [el.text.strip() for el in elements if el.text.strip()]

    def get_product_count(self) -> int:
        """Get number of products visible."""
        return len([t for t in self.get_product_titles() if t])

    def click_product(self, title: str) -> "EcommercePage":
        """Click on a specific product by title."""
        locator = (By.LINK_TEXT, title)
        if not self.is_element_visible(locator, timeout=3):
            # Try partial text match
            locator = (By.PARTIAL_LINK_TEXT, title[:20])
        self.click(locator)
        logger.info("Clicked product: '%s'", title)
        return self

    def add_to_collection(self) -> "EcommercePage":
        """Click 'Add to Collection' button on product detail page."""
        self.click(self.ADD_TO_COLLECTION)
        logger.info("Added to collection")
        return self

    def go_back_to_store(self) -> "EcommercePage":
        """Navigate back to the main store page."""
        self.click(self.BACK_BTN)
        return self

    def get_publisher_list(self) -> list[str]:
        """Get all publisher names visible in the list."""
        elements = self.find_elements(self.PUBLISHER_COL)
        return [el.text.strip() for el in elements if el.text.strip()]

    def get_author_list(self) -> list[str]:
        """Get all author names visible in the list."""
        elements = self.find_elements(self.AUTHOR_COL)
        return [el.text.strip() for el in elements if el.text.strip()]

    # ─── State Verification ──────────────────────────────────

    def is_product_in_list(self, title: str) -> bool:
        """Check if a product with given title appears in list."""
        titles = self.get_product_titles()
        return any(title.lower() in t.lower() for t in titles)

    def is_product_page_loaded(self) -> bool:
        """Check if product listing is fully loaded."""
        return self.is_element_visible(self.PRODUCT_LIST, timeout=15)

    def get_search_result_count(self) -> int:
        """Count of items returned by search."""
        return self.get_product_count()

    def is_product_detail_displayed(self) -> bool:
        """Check if product detail view is shown."""
        return self.is_element_visible(self.PRODUCT_DETAIL, timeout=10)
