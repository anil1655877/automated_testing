# 🏆 Framework Best Practices

This guide outlines the coding standards, design patterns, and engineering principles that govern the **AI-Enhanced Enterprise Test Automation Framework**. Adhering to these standards ensures the test suite remains fast, maintainable, thread-safe, and highly readable.

---

## 📋 Table of Contents
1. [Page Object Model Design](#1-page-object-model-design)
2. [Locator Standards & Self-Healing](#2-locator-standards--self-healing)
3. [Synchronization & Wait Strategy](#3-synchronization--wait-strategy)
4. [Test Class & Method Structure](#4-test-class--method-structure)
5. [Database Verification & Fallbacks](#5-database-verification--fallbacks)
6. [Offline-Safe AI & Wrapper Rules](#6-offline-safe-ai--wrapper-rules)
7. [Thread Safety & Parallel Execution](#7-thread-safety--parallel-execution)
8. [Reporting, Logging, and Screenshots](#8-reporting-logging-and-screenshots)

---

## 1. Page Object Model Design

The Page Object Model (POM) separates page layout and interactions from the actual test cases.

### Rule 1.1: Inherit from `BasePage`
All page objects must inherit from `pages.base_page.BasePage`. The constructor should pass the `driver` instance to the parent.
```python
from pages.base_page import BasePage

class MyFeaturePage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
```

### Rule 1.2: No Assertions in Page Objects
Page objects should model the application UI and expose behaviors (actions), not verify correctness. Assertions must live only in the **Test classes**.
- **Bad:**
  ```python
  def verify_header(self):
      assert self.get_text(self.HEADER) == "Welcome"
  ```
- **Good:**
  ```python
  def get_header_text(self):
      return self.safe_get_text(self.HEADER)
  ```

### Rule 1.3: Private/Encapsulated Locators
Locators should be private or encapsulated within the page object class using uppercase tuples (e.g. `(By.ID, "value")`). Do not expose raw Selenium elements directly.
```python
from selenium.webdriver.common.by import By

class LoginPage(BasePage):
    # Locators
    _USERNAME_INPUT = (By.ID, "userName")
    _PASSWORD_INPUT = (By.ID, "password")
    _SUBMIT_BUTTON = (By.ID, "login")
```

---

## 2. Locator Standards & Self-Healing

Locators are the most frequent cause of flakiness.

### Rule 2.1: Priority Order for Locators
Use the most stable locators first:
1. `By.ID` (Unique, fastest)
2. `By.CSS_SELECTOR` (using unique data attributes: `[data-testid="submit"]`)
3. `By.NAME`
4. `By.CSS_SELECTOR` (standard)
5. `By.XPATH` (Use absolute paths as a last resort only)

### Rule 2.2: Implement Self-Healing for Critical Elements
When locating dynamic elements that are prone to changing attributes, leverage the `SelfHealingLocator` wrapper. Provide fallback selectors.
```python
def click_checkout(self):
    element = self.self_healing_locator.find(
        primary=(By.CSS_SELECTOR, "button.checkout-btn"),
        fallbacks=[
            (By.XPATH, "//button[contains(text(), 'Checkout')]"),
            (By.CSS_SELECTOR, ".cart-footer button"),
        ],
        element_description="Checkout Button"
    )
    element.click()
```

---

## 3. Synchronization & Wait Strategy

Never write hardcoded delays (`time.sleep()`). They slow down tests and cause random pipeline crashes.

### Rule 3.1: Use Explicit Waits
Leverage the explicit wait methods defined in `utilities/wait_utils.py` via `BasePage` actions, or call `WaitUtils` directly.
- **Bad:**
  ```python
  import time
  time.sleep(5)  # Hard blocking
  driver.find_element(By.ID, "submit").click()
  ```
- **Good:**
  ```python
  self.wait.wait_for_element_visible(self._SUBMIT_BUTTON)
  self.safe_click(self._SUBMIT_BUTTON)
  ```

### Rule 3.2: Wait for Page/Dynamic Loads
When interacting with actions that trigger async JavaScript calls or page loads, explicitly wait for the state:
- `wait_for_page_load()`
- `wait_for_element_clickable(locator)`
- `wait_for_element_invisible(locator)`

---

## 4. Test Class & Method Structure

Keep tests clean, expressive, and parameterized.

### Rule 4.1: Clean Test Class Boilerplate
Decorate test classes with appropriate PyTest markers. Use descriptive names.
```python
import pytest

@pytest.mark.ui
@pytest.mark.regression
class TestUserRegistration:
    def test_successful_registration(self, registration_page, valid_user_data):
        registration_page.register_new_user(
            valid_user_data["first_name"],
            valid_user_data["last_name"],
            valid_user_data["username"],
            valid_user_data["password"]
        )
        assert registration_page.is_registration_successful()
```

### Rule 4.2: Parameterization for Data-Driven Testing
Avoid duplicating test methods for different datasets. Use `pytest.mark.parametrize`.
```python
@pytest.mark.parametrize("username,password,error_msg", [
    ("", "Pass@123", "User name is required"),
    ("user", "", "Password is required"),
    ("invalid", "wrong", "Invalid username or password!"),
])
def test_invalid_login_validation(self, login_page, username, password, error_msg):
    login_page.login(username, password)
    assert login_page.get_error_message() == error_msg
```

---

## 5. Database Verification & Fallbacks

Verify back-end database integrity alongside front-end and API behaviors.

### Rule 5.1: Reset/Teardown Database Data
Use the `clean_db` fixture for tests that insert, update, or delete records. This prevents test isolation leaks.
```python
def test_user_audit_log(self, clean_db):
    # Perform database actions
    clean_db.insert_audit_record("testuser", "LOGIN", "SUCCESS")
    # Teardown database changes automatically happens post-yield
```

### Rule 5.2: Ensure SQLite Fallback Readiness
Always write database tests using the database connector wrapper rather than raw driver connections (e.g. MySQLdb). The wrapper automatically detects connection failures and spins up an isolated, locally initialized SQLite schema.
```python
def test_db_read_write(self, db):
    # db is abstract, handles MySQL or SQLite under the hood
    db.execute_query("INSERT INTO test_users ...")
```

---

## 6. Offline-Safe AI & Wrapper Rules

AI features must never break the pipeline due to third-party outages or rate limit limits.

### Rule 6.1: Run via the `AIClientWrapper`
Never invoke the Gemini or external cloud API SDK directly. Always dispatch queries to the `AIClientWrapper`.
```python
from utilities.ai_client_wrapper import AIClientWrapper

ai_client = AIClientWrapper()
response = ai_client.generate_content(prompt="Analyze log...")
```

### Rule 6.2: Mock Mode for CI/CD Pipelines
Always enforce `USE_MOCK_AI=true` in GitHub Actions, Jenkinsfiles, and Docker configurations. This guarantees deterministic execution times and eliminates external API dependencies.

---

## 7. Thread Safety & Parallel Execution

Running tests in parallel via `pytest-xdist` requires careful setup.

### Rule 7.1: Coordinate Session Schema Setup
Do not run database DDL/schema setups concurrently inside worker fixtures. Ensure schema creation is coordinated via a process-level lock, so only the primary coordinator worker `gw0` sets up the schema.
```python
# conftest.py db fixture logic
if worker_id and worker_id != "gw0":
    # Wait for gw0 to release lock
    while not lock_file.exists():
        time.sleep(0.5)
```

### Rule 7.2: Use Function-Scoped Drivers
Keep the `driver` fixture function-scoped. Sharing driver instances across parallel tests will result in thread collisions and random crashes.

---

## 8. Reporting, Logging, and Screenshots

A test suite is only as good as its reports.

### Rule 8.1: Write Logging Contexts
Log key events using the centralized logger:
```python
logger.info("Starting authentication flow for user: %s", username)
logger.warning("Element %s not visible immediately, retrying", locator)
```

### Rule 8.2: Embed Media in Failures
Ensure the `pytest_runtest_makereport` hook captures screenshot logs upon failure. Screenshots must automatically be saved, formatted, and embedded inside both the pytest-html report and Allure attachments.

---
