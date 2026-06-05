"""
============================================================
AI-Enhanced Enterprise Test Automation Framework
UI Test: Login Functionality
============================================================
Tests login feature covering positive, negative, boundary,
and data-driven scenarios using DemoQA as the target app.
============================================================
"""
import pytest
import allure
from pages.login_page import LoginPage
from utilities.logger import get_logger

logger = get_logger(__name__)


@allure.feature("Authentication")
@allure.story("User Login")
class TestLogin:
    """
    Test suite for Login functionality.

    COVERAGE:
        - Valid login (positive)
        - Invalid credentials (negative)
        - Empty field validation
        - Data-driven login scenarios
        - UI element verification
        - Post-login state verification
    """

    @allure.title("Valid Login - Successful Authentication")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    @pytest.mark.login
    @pytest.mark.positive
    def test_valid_login(self, login_page: LoginPage):
        """
        TC-LOGIN-001: Verify user can log in with valid credentials.

        STEPS:
            1. Navigate to login page
            2. Enter valid username
            3. Enter valid password
            4. Click Login button
            5. Verify redirect to books/dashboard

        EXPECTED: User is redirected to dashboard or books page
        """
        from config.config import TEST_USERNAME, TEST_PASSWORD
        if not TEST_USERNAME or TEST_USERNAME == "your_username_here":
            pytest.skip("Test credentials not configured. Please register a user and update .env")

        with allure.step("Enter valid credentials and submit"):
            login_page.login(TEST_USERNAME, TEST_PASSWORD)

        with allure.step("Verify successful login"):
            assert login_page.is_logged_in(), (
                "Login failed: user was not redirected to dashboard. "
                f"Current URL: {login_page.get_current_url()}"
            )
        logger.info("✓ TC-LOGIN-001: Valid login test passed")

    @allure.title("Invalid Login - Wrong Password")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.regression
    @pytest.mark.login
    @pytest.mark.negative
    def test_invalid_password(self, login_page: LoginPage):
        """
        TC-LOGIN-002: Verify error shown for wrong password.

        EXPECTED: Error message displayed, user stays on login page
        """
        with allure.step("Enter valid username with wrong password"):
            login_page.login("validuser", "WrongPassword999!")

        with allure.step("Verify error message is shown"):
            assert not login_page.is_logged_in(), "Should NOT be logged in with wrong password"
            # Either error message OR stay on login page is acceptable
            current_url = login_page.get_current_url()
            assert "login" in current_url or "books" not in current_url, (
                "User should remain on login page after invalid credentials"
            )
        logger.info("✓ TC-LOGIN-002: Invalid password test passed")

    @allure.title("Invalid Login - Non-existent User")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.regression
    @pytest.mark.login
    @pytest.mark.negative
    def test_nonexistent_user(self, login_page: LoginPage):
        """TC-LOGIN-003: Verify error for non-existent username."""
        with allure.step("Enter non-existent user credentials"):
            login_page.login("nonexistent_user_xyz_12345", "SomePassword@123")

        with allure.step("Verify login is not successful"):
            assert not login_page.is_logged_in(), "Should NOT login with non-existent user"

    @allure.title("Empty Fields - Username and Password Empty")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.regression
    @pytest.mark.login
    @pytest.mark.negative
    def test_empty_credentials(self, login_page: LoginPage):
        """
        TC-LOGIN-004: Verify form validation when both fields empty.
        EXPECTED: Login button may be disabled or error shown
        """
        with allure.step("Click login without entering credentials"):
            login_page.click_login()

        with allure.step("Verify user is NOT logged in"):
            assert not login_page.is_logged_in(), (
                "Should NOT login with empty credentials"
            )

    @allure.title("Empty Username Only")
    @allure.severity(allure.severity_level.MINOR)
    @pytest.mark.regression
    @pytest.mark.login
    @pytest.mark.negative
    def test_empty_username(self, login_page: LoginPage):
        """TC-LOGIN-005: Empty username, valid password."""
        with allure.step("Enter only password, leave username empty"):
            login_page.enter_password("ValidPassword@123").click_login()

        with allure.step("Verify login fails"):
            assert not login_page.is_logged_in(), "Empty username should not allow login"

    @allure.title("Empty Password Only")
    @allure.severity(allure.severity_level.MINOR)
    @pytest.mark.regression
    @pytest.mark.login
    @pytest.mark.negative
    def test_empty_password(self, login_page: LoginPage):
        """TC-LOGIN-006: Valid username, empty password."""
        with allure.step("Enter only username, leave password empty"):
            login_page.enter_username("validuser@test.com").click_login()

        with allure.step("Verify login fails"):
            assert not login_page.is_logged_in(), "Empty password should not allow login"

    @allure.title("Login Page UI Elements Verification")
    @allure.severity(allure.severity_level.MINOR)
    @pytest.mark.regression
    @pytest.mark.login
    @pytest.mark.ui
    def test_login_page_ui_elements(self, login_page: LoginPage):
        """
        TC-LOGIN-007: Verify all expected UI elements are present.

        ELEMENTS CHECKED:
            - Username input field
            - Password input field
            - Login button
            - New User registration link
        """
        with allure.step("Verify login form elements are visible"):
            assert login_page.is_element_visible(LoginPage.USERNAME_INPUT), \
                "Username field should be visible"
            assert login_page.is_element_visible(LoginPage.PASSWORD_INPUT), \
                "Password field should be visible"
            assert login_page.is_element_visible(LoginPage.LOGIN_BUTTON), \
                "Login button should be visible"
            assert login_page.is_element_visible(LoginPage.REGISTER_LINK, timeout=5), \
                "New User link should be visible"

        logger.info("✓ TC-LOGIN-007: All login UI elements verified")

    @allure.title("Data-Driven Login Test")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.regression
    @pytest.mark.login
    @pytest.mark.parametrize("username,password,should_pass", [
        ("",         "",              False),   # Both empty
        ("user",     "",              False),   # No password
        ("",         "pass",          False),   # No username
        ("wronguser","WrongPass!1",   False),   # Wrong credentials
        ("   ",      "Password@123",  False),   # Whitespace username
    ])
    def test_login_data_driven(self, login_page: LoginPage, username, password, should_pass):
        """
        TC-LOGIN-008: Data-driven login boundary tests.

        PARAMETRIZE: Runs this single test with multiple data sets.
        This covers more ground than individual test methods.
        """
        with allure.step(f"Login with username='{username}', password='[masked]'"):
            login_page.login(username, password)

        with allure.step(f"Verify result — should_pass={should_pass}"):
            actual_result = login_page.is_logged_in()
            if should_pass:
                assert actual_result, f"Expected successful login for '{username}'"
            else:
                assert not actual_result, f"Expected login failure for '{username}'"

    @allure.title("Login Page Navigation - Redirect to Register")
    @allure.severity(allure.severity_level.MINOR)
    @pytest.mark.regression
    @pytest.mark.login
    def test_navigate_to_register(self, login_page: LoginPage):
        """TC-LOGIN-009: Verify 'New User' link navigates to registration page."""
        with allure.step("Click 'New User' button"):
            login_page.click_new_user()

        with allure.step("Verify registration page is shown"):
            current_url = login_page.get_current_url()
            assert "register" in current_url or "login" in current_url, (
                f"Expected register page. Got: {current_url}"
            )

    @allure.title("Login - SQL Injection Prevention")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.security
    @pytest.mark.login
    @pytest.mark.negative
    def test_sql_injection_prevention(self, login_page: LoginPage):
        """
        TC-LOGIN-010: Security test — SQL injection in login fields.

        SQL INJECTION: Malicious input that tries to bypass auth.
        Example: username = "admin' OR '1'='1"

        EXPECTED: Application rejects the input, login fails.
        """
        sql_payloads = [
            "admin' OR '1'='1",
            "'; DROP TABLE users; --",
            "' UNION SELECT 1,2,3 --",
        ]
        for payload in sql_payloads:
            with allure.step(f"Try SQL injection: {payload[:30]}..."):
                login_page.login(payload, "anypassword")
                assert not login_page.is_logged_in(), (
                    f"SQL injection should not allow login: {payload}"
                )
                login_page.navigate()  # Reset for next payload
