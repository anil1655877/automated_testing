"""
============================================================
AI-Enhanced Enterprise Test Automation Framework
API Test: CRUD Operations
============================================================
Tests REST API CRUD operations using DemoQA BookStore API.
Includes token auth, schema validation, and API chaining.
============================================================
"""
import pytest
import allure
from utilities.api_client import APIClient
from utilities.json_utils import JSONUtils
from utilities.logger import get_logger

logger = get_logger(__name__)

# ── JSON Schemas for validation ──────────────────────────────
BOOK_SCHEMA = {
    "type": "object",
    "required": ["isbn", "title", "subTitle", "author", "publish_date", "publisher"],
    "properties": {
        "isbn":         {"type": "string"},
        "title":        {"type": "string"},
        "subTitle":     {"type": "string"},
        "author":       {"type": "string"},
        "publish_date": {"type": "string"},
        "publisher":    {"type": "string"},
        "pages":        {"type": "integer"},
        "description":  {"type": "string"},
        "website":      {"type": "string"},
    },
}

BOOKS_LIST_SCHEMA = {
    "type": "object",
    "required": ["books"],
    "properties": {
        "books": {
            "type": "array",
            "items": BOOK_SCHEMA,
        }
    },
}

USER_TOKEN_SCHEMA = {
    "type": "object",
    "required": ["token", "expires", "status", "result"],
    "properties": {
        "token":   {"type": "string"},
        "expires": {"type": "string"},
        "status":  {"type": "string"},
        "result":  {"type": "string"},
    },
}


@allure.feature("API Testing")
@allure.story("Book Store API - CRUD")
class TestCrudAPI:
    """API CRUD test suite using DemoQA BookStore API."""

    BASE_PATH = "/BookStore/v1"

    @allure.title("GET Books - Returns Book List")
    @pytest.mark.smoke
    @pytest.mark.api
    @pytest.mark.crud
    def test_get_all_books(self, api_client: APIClient):
        """TC-API-001: GET /Books returns list of books with 200 status."""
        with allure.step("Send GET /Books request"):
            response = api_client.get(f"{self.BASE_PATH}/Books")

        with allure.step("Verify status 200"):
            api_client.assert_status(response, 200)

        with allure.step("Verify response schema"):
            body = api_client.get_response_json(response)
            is_valid, error = JSONUtils.validate_schema(body, BOOKS_LIST_SCHEMA)
            assert is_valid, f"Schema validation failed: {error}"

        with allure.step("Verify books list is not empty"):
            books = body.get("books", [])
            assert len(books) > 0, "Books list should not be empty"
            logger.info("Total books returned: %d", len(books))

    @allure.title("GET Book by ISBN - Returns Single Book")
    @pytest.mark.regression
    @pytest.mark.api
    @pytest.mark.crud
    def test_get_book_by_isbn(self, api_client: APIClient):
        """TC-API-002: GET /Book?ISBN={isbn} returns specific book."""
        # First fetch all books to get a valid ISBN
        with allure.step("Fetch book list to get a valid ISBN"):
            list_response = api_client.get(f"{self.BASE_PATH}/Books")
            api_client.assert_status(list_response, 200)
            books = list_response.json().get("books", [])
            if not books:
                pytest.skip("No books in API to test with")
            isbn = books[0]["isbn"]
            logger.info("Testing with ISBN: %s", isbn)

        with allure.step(f"GET /Book?ISBN={isbn}"):
            response = api_client.get(f"{self.BASE_PATH}/Book", params={"ISBN": isbn})

        with allure.step("Verify status 200 and schema"):
            api_client.assert_status(response, 200)
            body = api_client.get_response_json(response)
            is_valid, error = JSONUtils.validate_schema(body, BOOK_SCHEMA)
            assert is_valid, f"Book schema invalid: {error}"
            assert body["isbn"] == isbn, f"Expected ISBN {isbn}, got {body['isbn']}"

    @allure.title("GET Book by Invalid ISBN - Returns 400")
    @pytest.mark.regression
    @pytest.mark.api
    @pytest.mark.negative
    def test_get_book_invalid_isbn(self, api_client: APIClient):
        """TC-API-003: GET /Book with invalid ISBN returns error."""
        with allure.step("Request book with invalid ISBN"):
            response = api_client.get(
                f"{self.BASE_PATH}/Book",
                params={"ISBN": "INVALID-ISBN-12345"}
            )
        with allure.step("Verify error status (400 or 404)"):
            assert response.status_code in (400, 404), \
                f"Expected 400/404 for invalid ISBN, got {response.status_code}"

    @allure.title("POST Generate Token - Valid Credentials")
    @pytest.mark.regression
    @pytest.mark.api
    @pytest.mark.auth
    def test_generate_auth_token(self, api_client: APIClient):
        """TC-API-004: POST /GenerateToken returns valid auth token."""
        from config.config import TEST_USERNAME, TEST_PASSWORD
        payload = {"userName": TEST_USERNAME, "password": TEST_PASSWORD}

        with allure.step("Request auth token"):
            response = api_client.post("/Account/v1/GenerateToken", body=payload)

        with allure.step("Verify response"):
            if response.status_code == 200:
                body = api_client.get_response_json(response)
                # Check for failed authorization due to unconfigured/placeholder credentials
                if body.get("status") == "Failed" or not body.get("token"):
                    if not TEST_USERNAME or TEST_USERNAME == "your_username_here" or "your_username" in TEST_USERNAME:
                        logger.warning("Default credentials used. Skipping token generation test.")
                        pytest.skip("Auth credentials not configured in .env")
                
                is_valid, error = JSONUtils.validate_schema(body, USER_TOKEN_SCHEMA)
                assert is_valid, f"Token response schema invalid: {error}"
                assert body.get("token"), "Token should not be empty"
                logger.info("Auth token generated successfully")
            else:
                # Credentials may not be set up in .env — skip gracefully
                logger.warning(
                    "Token generation returned %d — verify TEST_USERNAME/PASSWORD in .env",
                    response.status_code
                )
                pytest.skip("Auth credentials not configured")

    @allure.title("API Response Time is Acceptable")
    @pytest.mark.performance
    @pytest.mark.api
    def test_api_response_time(self, api_client: APIClient):
        """TC-API-005: API must respond within 3 seconds."""
        with allure.step("Call Books API and measure response time"):
            api_client.get(f"{self.BASE_PATH}/Books")
            api_client.assert_response_time(max_ms=3000)
            logger.info("Avg response time: %.0fms", api_client.avg_response_time_ms)

    @allure.title("Books API Returns Valid Content-Type")
    @pytest.mark.regression
    @pytest.mark.api
    def test_content_type_header(self, api_client: APIClient):
        """TC-API-006: Response Content-Type should be application/json."""
        with allure.step("Check Content-Type header"):
            response = api_client.get(f"{self.BASE_PATH}/Books")
            content_type = response.headers.get("Content-Type", "")
            assert "application/json" in content_type, \
                f"Expected JSON content-type, got: {content_type}"

    @allure.title("Unauthorized API Access Returns 401")
    @pytest.mark.regression
    @pytest.mark.api
    @pytest.mark.security
    def test_unauthorized_access(self, api_client: APIClient):
        """TC-API-007: Protected endpoints return 401 without auth token."""
        with allure.step("Access user-specific endpoint without token"):
            api_client.clear_token()
            response = api_client.get("/Account/v1/User/some-fake-user-id")
        with allure.step("Verify 401 or 403 status"):
            assert response.status_code in (401, 403), \
                f"Expected 401/403 for unauthorized access, got {response.status_code}"
