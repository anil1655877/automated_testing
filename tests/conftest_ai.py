"""
============================================================
AI-Enhanced Enterprise Test Automation Framework
AI Conftest — AI Module Fixtures for Tests
============================================================
Provides AI-specific fixtures (FailureAnalyzer, SelfHealingLocator,
SmartDataGenerator, BugPredictor) to all test modules.
Import this conftest by placing in tests/ alongside conftest.py.
============================================================
"""
import pytest
from ai_modules.failure_analyzer import FailureAnalyzer
from ai_modules.self_healing_locator import SelfHealingLocator
from ai_modules.smart_data_generator import SmartDataGenerator
from ai_modules.bug_predictor import BugPredictor
from ai_modules.test_case_generator import TestCaseGenerator
from utilities.logger import get_logger

logger = get_logger(__name__)


@pytest.fixture(scope="session")
def failure_analyzer() -> FailureAnalyzer:
    """
    Session-scoped FailureAnalyzer fixture.

    USAGE:
        def test_something(failure_analyzer):
            result = failure_analyzer.analyze("TimeoutException after 20s")
            assert result["category"] == "TIMEOUT"
    """
    analyzer = FailureAnalyzer()
    logger.info("FailureAnalyzer fixture initialized (offline mode)")
    yield analyzer
    # Print session summary at end
    summary = analyzer.get_failure_summary()
    if summary.get("total_failures", 0) > 0:
        logger.info("Failure Analysis Summary: %s", summary)


@pytest.fixture(scope="function")
def self_healing_locator(driver):
    """
    Function-scoped SelfHealingLocator fixture.
    Requires the 'driver' fixture from conftest.py.

    USAGE:
        def test_find_element(self_healing_locator):
            element = self_healing_locator.find(
                primary=(By.ID, "submit-btn"),
                fallbacks=[(By.CSS_SELECTOR, "button[type='submit']")],
                element_description="Submit button",
            )
    """
    healer = SelfHealingLocator(driver)
    yield healer
    # Log healing events after each test
    events = SelfHealingLocator.get_healing_report()
    if events:
        logger.info("%d self-healing events occurred this session", len(events))


@pytest.fixture(scope="session")
def data_generator() -> SmartDataGenerator:
    """
    Session-scoped SmartDataGenerator fixture.

    USAGE:
        def test_register_user(data_generator, registration_page):
            user = data_generator.valid_user()
            registration_page.fill_registration_form(
                user["first_name"], user["last_name"],
                user["username"], user["password"]
            )
    """
    return SmartDataGenerator()


@pytest.fixture(scope="session")
def bug_predictor() -> BugPredictor:
    """
    Session-scoped BugPredictor fixture.
    Records pass/fail outcomes for ML-based failure prediction.

    USAGE:
        def test_login(bug_predictor, login_page):
            risk = bug_predictor.predict_failure_probability("test_login")
            if risk["risk_level"] == "HIGH":
                pytest.xfail("High failure probability predicted")
    """
    return BugPredictor()


@pytest.fixture(scope="session")
def test_case_generator() -> TestCaseGenerator:
    """
    Session-scoped TestCaseGenerator fixture.

    USAGE:
        def test_generate_login_cases(test_case_generator):
            cases = test_case_generator.generate("login_form", "LOGIN")
            assert len(cases) > 0
    """
    return TestCaseGenerator()


@pytest.fixture(scope="session")
def valid_user_data(data_generator) -> dict:
    """Pre-generated valid user dict for tests needing fresh user data."""
    return data_generator.valid_user()


@pytest.fixture(scope="session")
def invalid_user_data(data_generator) -> dict:
    """Pre-generated SQL injection user for security tests."""
    return data_generator.invalid_user("sql_injection")


@pytest.fixture(scope="session")
def boundary_usernames(data_generator) -> list:
    """Boundary value usernames for parametrize-style tests."""
    return data_generator.boundary_values("username")


@pytest.fixture(scope="session")
def boundary_passwords(data_generator) -> list:
    """Boundary value passwords for password validation tests."""
    return data_generator.boundary_values("password")


# ── Auto-record test results for BugPredictor ─────────────────
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Record pass/fail for each test into BugPredictor history."""
    outcome = yield
    rep = outcome.get_result()

    if rep.when == "call":
        predictor = item.session._store.get("bug_predictor_instance", None)
        if predictor is None:
            # Initialize predictor for session if not already set
            try:
                predictor = BugPredictor()
                item.session._store["bug_predictor_instance"] = predictor
            except Exception:
                return
        try:
            predictor.record_result(item.nodeid, passed=not rep.failed)
        except Exception:
            pass
