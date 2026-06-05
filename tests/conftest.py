"""
============================================================
AI-Enhanced Enterprise Test Automation Framework
PyTest Configuration & Fixtures (conftest.py)
============================================================
Central fixture file. PyTest auto-discovers this file and
makes all fixtures available to every test in the project.

KEY FIXTURES:
  driver       - WebDriver instance (session-scoped per test)
  api_client   - REST API client
  db           - Database connector
  login_page   - Pre-navigated LoginPage
  dashboard    - Authenticated DashboardPage
  test_data    - JSON test data loader

HOOKS:
  pytest_runtest_makereport  - Screenshot on failure
  pytest_configure           - Allure environment metadata
  pytest_sessionstart        - Framework startup log
  pytest_sessionfinish       - Report generation trigger
============================================================
"""
import os
import sys
import pytest
import allure
from pathlib import Path
from datetime import datetime
from typing import Generator

# ── Add project root to path ──────────────────────────────────
# Required so all imports work correctly from any working directory
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

from config.config import (
    BROWSER, HEADLESS, ENVIRONMENT, BASE_URL,
    SCREENSHOT_ON_FAILURE, print_config_summary,
)
from utilities.driver_factory import DriverFactory
from utilities.logger import get_logger
from utilities.api_client import APIClient
from utilities.db_connector import get_db_connector
from utilities.screenshot_utils import ScreenshotUtils
from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage
from pages.registration_page import RegistrationPage
from pages.ecommerce_page import EcommercePage
from pages.admin_page import AdminPage

logger = get_logger(__name__)


# ─────────────────────────────────────────────────────────────
# SECTION 1: PyTest Hooks
# ─────────────────────────────────────────────────────────────

def pytest_configure(config):
    """
    Called once before test collection.
    Sets up Allure environment metadata and validates configuration.
    """
    # Write Allure environment properties file
    allure_dir = ROOT_DIR / "reports" / "allure-results"
    allure_dir.mkdir(parents=True, exist_ok=True)

    env_props = allure_dir / "environment.properties"
    env_props.write_text(
        f"Environment={ENVIRONMENT}\n"
        f"Browser={BROWSER}\n"
        f"Headless={HEADLESS}\n"
        f"Base_URL={BASE_URL}\n"
        f"Python_Version={sys.version.split()[0]}\n"
        f"Executed_At={datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    )


def pytest_sessionstart(session):
    """Called after test session setup, before collection."""
    print_config_summary()
    logger.info("=" * 60)
    logger.info("  TEST SESSION STARTED")
    logger.info("  Environment : %s", ENVIRONMENT)
    logger.info("  Browser     : %s (headless=%s)", BROWSER, HEADLESS)
    logger.info("=" * 60)


# ── Session Results Tracking for Analytics ────────────────────
_session_results = {"passed": 0, "failed": 0, "skipped": 0}


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_logreport(report):
    """Log test result status for execution analytics."""
    if report.when == "call":
        if report.passed:
            _session_results["passed"] += 1
        elif report.failed:
            _session_results["failed"] += 1
    elif report.when == "setup" and report.skipped:
        _session_results["skipped"] += 1


def pytest_sessionfinish(session, exitstatus):
    """Called after entire test session finishes."""
    logger.info("=" * 60)
    logger.info("  TEST SESSION FINISHED | Exit Status: %s", exitstatus)
    logger.info("=" * 60)

    # ── Generate Execution Analytics & Historical Trend Report ──
    try:
        analytics_dir = ROOT_DIR / "reports" / "analytics"
        analytics_dir.mkdir(parents=True, exist_ok=True)

        from utilities.json_utils import JSONUtils

        # Load existing trend data if present
        trend_file = analytics_dir / "historical_trend.json"
        trends = []
        if trend_file.exists():
            try:
                trends = JSONUtils.load_json_file(trend_file)
            except Exception:
                trends = []

        # Load Failure Analyzer logs
        failure_log_file = ROOT_DIR / "logs" / "failure_analysis.json"
        ai_summary = {}
        if failure_log_file.exists():
            try:
                raw_failures = JSONUtils.load_json_file(failure_log_file)
                from collections import Counter
                categories = Counter(f.get("category", "UNKNOWN") for f in raw_failures)
                ai_summary = {
                    "total_failures_analyzed": len(raw_failures),
                    "by_category": dict(categories.most_common())
                }
            except Exception:
                pass

        current_run = {
            "timestamp": datetime.now().isoformat(),
            "exit_status": int(exitstatus),
            "passed": _session_results["passed"],
            "failed": _session_results["failed"],
            "skipped": _session_results["skipped"],
            "total_tests": _session_results["passed"] + _session_results["failed"] + _session_results["skipped"],
            "ai_failure_analysis": ai_summary
        }

        # Save current run analytics
        JSONUtils.save_json_file(current_run, analytics_dir / "current_run.json")

        # Append and keep last 20 runs
        trends.append(current_run)
        JSONUtils.save_json_file(trends[-20:], trend_file)

        # Archive reports
        archive_dir = ROOT_DIR / "reports" / "archive"
        archive_dir.mkdir(parents=True, exist_ok=True)
        archive_file = archive_dir / f"analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        JSONUtils.save_json_file(current_run, archive_file)

        logger.info("✓ Run analytics and historical trends generated successfully")
        print("\n" + "=" * 60)
        print("  TEST SUMMARY & EXECUTION ANALYTICS")
        print("=" * 60)
        print(f"  Passed  : {current_run['passed']}")
        print(f"  Failed  : {current_run['failed']}")
        print(f"  Skipped : {current_run['skipped']}")
        print(f"  Total   : {current_run['total_tests']}")
        if ai_summary:
            print(f"  AI Failure Analysis Categories: {ai_summary['by_category']}")
        print("=" * 60 + "\n")

    except Exception as e:
        logger.warning("Could not generate execution analytics: %s", e)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Hook that runs after each test phase (setup, call, teardown).

    PURPOSE: Capture screenshot when a test FAILS.
    Attaches screenshot to Allure report for visual debugging.

    IMPLEMENTATION NOTE:
        tryfirst=True  - Run before other plugins' hooks
        hookwrapper=True - Allows us to inspect the outcome
    """
    outcome = yield
    rep = outcome.get_result()

    # Store test result on the item for use in fixtures
    setattr(item, f"rep_{rep.when}", rep)

    # Capture screenshot only on test CALL phase failure
    if rep.when == "call" and rep.failed:
        driver = item.funcargs.get("driver")
        if driver:
            try:
                ss_utils = ScreenshotUtils(driver)
                test_name = item.nodeid.replace("::", "_").replace("/", "_")
                ss_path = ss_utils.capture_on_failure(test_name)
                if ss_path:
                    # Attach to Allure report
                    with open(ss_path, "rb") as f:
                        allure.attach(
                            f.read(),
                            name=f"FAILURE_{test_name}",
                            attachment_type=allure.attachment_type.PNG,
                        )
                    logger.info("Screenshot attached to Allure: %s", ss_path)
            except Exception as e:
                logger.warning("Could not capture failure screenshot: %s", e)


# ─────────────────────────────────────────────────────────────
# SECTION 2: Driver Fixtures
# ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def driver(request):
    """
    Create a fresh WebDriver for each test function.

    SCOPE: function — each test gets its own isolated browser.
    This is the safest scope for UI tests: no state leaks
    between tests, and failures don't affect other tests.

    Supports pytest-xdist parallel execution via thread-local storage.

    USAGE in test:
        def test_login(driver):
            driver.get("https://example.com")
    """
    # Get browser override from command line or config
    browser = request.config.getoption("--browser", default=BROWSER)
    headless = request.config.getoption("--headless", default=str(HEADLESS)).lower() == "true"

    web_driver = DriverFactory.create_driver(browser=browser, headless=headless)
    logger.info("Driver created for test: %s [%s]", request.node.name, browser)

    yield web_driver

    # Teardown — always runs even if test fails
    DriverFactory.quit_driver(web_driver)
    logger.info("Driver quit after test: %s", request.node.name)


@pytest.fixture(scope="function")
def headless_driver():
    """
    Create a headless WebDriver regardless of config.
    Use for tests that should never open a visible browser.
    """
    web_driver = DriverFactory.create_driver(headless=True)
    yield web_driver
    DriverFactory.quit_driver(web_driver)


# ─────────────────────────────────────────────────────────────
# SECTION 3: Page Object Fixtures
# ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def login_page(driver) -> LoginPage:
    """
    Provide a LoginPage object, navigated to login URL.

    USAGE in test:
        def test_login(login_page):
            login_page.login("user@test.com", "pass")
            assert login_page.is_logged_in()
    """
    page = LoginPage(driver)
    page.navigate()
    return page


@pytest.fixture(scope="function")
def registration_page(driver) -> RegistrationPage:
    """Provide a RegistrationPage object, navigated to register URL."""
    page = RegistrationPage(driver)
    page.navigate()
    return page


@pytest.fixture(scope="function")
def dashboard_page(driver) -> DashboardPage:
    """Provide a DashboardPage — navigates directly (no login)."""
    page = DashboardPage(driver)
    page.navigate()
    return page


@pytest.fixture(scope="function")
def authenticated_dashboard(driver) -> Generator[DashboardPage, None, None]:
    """
    Provide a DashboardPage with a logged-in session.

    This fixture logs in as the test user before yielding
    the dashboard page object for tests that need auth context.

    USAGE:
        def test_user_profile(authenticated_dashboard):
            assert authenticated_dashboard.is_user_logged_in()
    """
    from config.config import TEST_USERNAME, TEST_PASSWORD
    if not TEST_USERNAME or TEST_USERNAME == "your_username_here":
        pytest.skip("Test credentials not configured. Please register a user and update .env")

    login = LoginPage(driver)
    login.navigate()
    login.login(TEST_USERNAME, TEST_PASSWORD)

    if not login.is_logged_in():
        pytest.skip("Failed to authenticate with configured TEST_USERNAME. Skipping authenticated dashboard test.")

    dashboard = DashboardPage(driver)
    yield dashboard


@pytest.fixture(scope="function")
def ecommerce_page(driver) -> EcommercePage:
    """Provide EcommercePage, navigated to store."""
    page = EcommercePage(driver)
    page.navigate()
    return page


@pytest.fixture(scope="function")
def admin_page(driver) -> AdminPage:
    """Provide AdminPage for RBAC testing."""
    return AdminPage(driver)


# ─────────────────────────────────────────────────────────────
# SECTION 4: API & Database Fixtures
# ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def api_client() -> Generator[APIClient, None, None]:
    """
    Session-scoped API client — shared across all API tests.
    Session scope: created once, reused, closed at end of session.
    """
    client = APIClient()
    logger.info("API client created (session scope)")
    yield client
    client.close()
    logger.info("API client closed")


@pytest.fixture(scope="session")
def db() -> Generator:
    """
    Session-scoped database connector.
    Automatically tries MySQL, falls back to SQLite.
    """
    connector = get_db_connector()
    
    # Coordinate database schema setup for pytest-xdist parallel workers
    worker_id = os.environ.get("PYTEST_XDIST_WORKER")
    if worker_id:
        lock_file = ROOT_DIR / "data" / "db_setup.lock"
        if worker_id == "gw0":
            connector.setup_test_schema()
            lock_file.parent.mkdir(parents=True, exist_ok=True)
            lock_file.write_text("initialized")
            logger.info("Worker gw0 completed database schema initialization")
        else:
            retries = 40
            while not lock_file.exists() and retries > 0:
                import time
                time.sleep(0.5)
                retries -= 1
            logger.info("Worker %s connected to initialized database schema", worker_id)
    else:
        connector.setup_test_schema()

    logger.info("Database connector ready (%s)", connector.db_type)
    yield connector
    connector.close()
    logger.info("Database connector closed")
    
    # Cleanup lock file on session finish (worker gw0 or serial)
    try:
        lock_file = ROOT_DIR / "data" / "db_setup.lock"
        if lock_file.exists() and (not worker_id or worker_id == "gw0"):
            lock_file.unlink()
    except Exception:
        pass


@pytest.fixture(scope="function")
def clean_db(db):
    """
    Function-scoped DB fixture that cleans test tables after each test.
    Use when tests write data that shouldn't persist to next test.
    """
    yield db
    try:
        db.teardown_test_data(["test_users", "test_orders", "test_audit_log"])
        logger.debug("Test data cleaned after test")
    except Exception as e:
        logger.warning("Could not clean test data: %s", e)


# ─────────────────────────────────────────────────────────────
# SECTION 5: Test Data Fixtures
# ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def login_test_data() -> list[dict]:
    """Load login test data from JSON file."""
    from utilities.json_utils import JSONUtils
    return JSONUtils.load_test_data("login_data.json")


@pytest.fixture(scope="session")
def registration_test_data() -> list[dict]:
    """Load registration test data from JSON file."""
    from utilities.json_utils import JSONUtils
    return JSONUtils.load_test_data("registration_data.json")


@pytest.fixture(scope="session")
def api_test_data() -> dict:
    """Load API test data from JSON file."""
    from utilities.json_utils import JSONUtils
    return JSONUtils.load_test_data("api_data.json")


@pytest.fixture(scope="session")
def ecommerce_test_data() -> dict:
    """Load e-commerce test data."""
    from utilities.json_utils import JSONUtils
    return JSONUtils.load_test_data("ecommerce_data.json")


# ─────────────────────────────────────────────────────────────
# SECTION 6: Command-Line Options
# ─────────────────────────────────────────────────────────────

def pytest_addoption(parser):
    """
    Add custom command-line options to pytest.

    USAGE:
        pytest --browser=firefox
        pytest --headless=true
        pytest --env=staging
    """
    parser.addoption(
        "--browser",
        action="store",
        default=BROWSER,
        help="Browser to run tests: chrome | firefox | edge",
    )
    parser.addoption(
        "--headless",
        action="store",
        default=str(HEADLESS),
        help="Run browser in headless mode: true | false",
    )
    parser.addoption(
        "--env",
        action="store",
        default=ENVIRONMENT,
        help="Target environment: dev | staging | production",
    )
