"""
============================================================
AI-Enhanced Enterprise Test Automation Framework
Configuration Management Module
============================================================
Centralizes all configuration settings with environment
variable overrides and multi-environment support.
============================================================
"""
import os
import configparser
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

# ── Load .env file ───────────────────────────────────────────
# Automatically loads environment variables from .env file
# Falls back gracefully if .env doesn't exist
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / ".env")


# ── Load INI Configuration ───────────────────────────────────
config_parser = configparser.ConfigParser()
config_parser.read(ROOT_DIR / "config" / "env_config.ini")


def get_env(key: str, default: str = "") -> str:
    """Retrieve environment variable with fallback default."""
    return os.getenv(key, default)


def get_env_bool(key: str, default: bool = False) -> bool:
    """Retrieve boolean environment variable."""
    value = os.getenv(key, str(default)).lower()
    return value in ("true", "1", "yes", "on")


def get_env_int(key: str, default: int = 0) -> int:
    """Retrieve integer environment variable."""
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default


# ────────────────────────────────────────────────────────────
# SECTION 1: Environment Detection
# ────────────────────────────────────────────────────────────
ENVIRONMENT = get_env("ENVIRONMENT", "dev")
VALID_ENVS = ("dev", "staging", "production")
if ENVIRONMENT not in VALID_ENVS:
    raise ValueError(f"Invalid ENVIRONMENT '{ENVIRONMENT}'. Must be one of: {VALID_ENVS}")


# ────────────────────────────────────────────────────────────
# SECTION 2: URL Configuration (per environment)
# ────────────────────────────────────────────────────────────
_URL_MAP = {
    "dev": {
        "base_url": "https://demoqa.com",
        "api_url": "https://demoqa.com/api",
        "admin_url": "https://demoqa.com/admin",
    },
    "staging": {
        "base_url": "https://staging.your-app.com",
        "api_url": "https://staging-api.your-app.com",
        "admin_url": "https://staging-admin.your-app.com",
    },
    "production": {
        "base_url": "https://your-app.com",
        "api_url": "https://api.your-app.com",
        "admin_url": "https://admin.your-app.com",
    },
}

# Override with .env values if provided
BASE_URL = get_env("BASE_URL") or _URL_MAP[ENVIRONMENT]["base_url"]
API_BASE_URL = get_env("API_BASE_URL") or _URL_MAP[ENVIRONMENT]["api_url"]
ADMIN_URL = get_env("ADMIN_URL") or _URL_MAP[ENVIRONMENT]["admin_url"]


# ────────────────────────────────────────────────────────────
# SECTION 3: Browser Configuration
# ────────────────────────────────────────────────────────────
BROWSER = get_env("BROWSER", "chrome").lower()
HEADLESS = get_env_bool("HEADLESS", False)
BROWSER_TIMEOUT = get_env_int("BROWSER_TIMEOUT", 30)
IMPLICIT_WAIT = get_env_int("IMPLICIT_WAIT", 10)
EXPLICIT_WAIT = get_env_int("EXPLICIT_WAIT", 20)
PAGE_LOAD_TIMEOUT = get_env_int("PAGE_LOAD_TIMEOUT", 60)
WINDOW_SIZE = get_env("WINDOW_SIZE", "1920,1080")

SUPPORTED_BROWSERS = ("chrome", "firefox", "edge", "safari")
if BROWSER not in SUPPORTED_BROWSERS:
    raise ValueError(f"Unsupported browser '{BROWSER}'. Choose from: {SUPPORTED_BROWSERS}")


# ────────────────────────────────────────────────────────────
# SECTION 4: Test User Credentials
# ────────────────────────────────────────────────────────────
ADMIN_USERNAME = get_env("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = get_env("ADMIN_PASSWORD", "Admin@123")
TEST_USERNAME = get_env("TEST_USERNAME", "testuser")
TEST_PASSWORD = get_env("TEST_PASSWORD", "TestUser@123")
READONLY_USERNAME = get_env("READONLY_USERNAME", "readonly")
READONLY_PASSWORD = get_env("READONLY_PASSWORD", "ReadOnly@123")


# ────────────────────────────────────────────────────────────
# SECTION 5: Database Configuration
# ────────────────────────────────────────────────────────────
DB_HOST = get_env("DB_HOST", "localhost")
DB_PORT = get_env_int("DB_PORT", 3306)
DB_NAME = get_env("DB_NAME", "test_automation_db")
DB_USER = get_env("DB_USER", "root")
DB_PASSWORD = get_env("DB_PASSWORD", "")
DB_POOL_SIZE = get_env_int("DB_POOL_SIZE", 5)
DB_MAX_OVERFLOW = get_env_int("DB_MAX_OVERFLOW", 10)

# SQLite fallback path (used when MySQL is unavailable)
SQLITE_DB_PATH = ROOT_DIR / get_env("SQLITE_DB_PATH", "data/test_db.sqlite")


# ────────────────────────────────────────────────────────────
# SECTION 6: API Configuration
# ────────────────────────────────────────────────────────────
API_TIMEOUT = get_env_int("API_TIMEOUT", 30)
API_KEY = get_env("API_KEY", "")
API_SECRET = get_env("API_SECRET", "")
JWT_SECRET = get_env("JWT_SECRET", "test-secret-key")


# ────────────────────────────────────────────────────────────
# SECTION 7: Reporting & Screenshots
# ────────────────────────────────────────────────────────────
SCREENSHOT_ON_FAILURE = get_env_bool("SCREENSHOT_ON_FAILURE", True)
SCREENSHOT_DIR = ROOT_DIR / get_env("SCREENSHOT_DIR", "reports/screenshots")
HTML_REPORT_DIR = ROOT_DIR / get_env("HTML_REPORT_DIR", "reports/html-reports")
ALLURE_RESULTS_DIR = ROOT_DIR / get_env("ALLURE_RESULTS_DIR", "reports/allure-results")

# Create report directories if they don't exist
for _dir in [SCREENSHOT_DIR, HTML_REPORT_DIR, ALLURE_RESULTS_DIR]:
    _dir.mkdir(parents=True, exist_ok=True)


# ────────────────────────────────────────────────────────────
# SECTION 8: Parallel Execution
# ────────────────────────────────────────────────────────────
PARALLEL_WORKERS = get_env_int("PARALLEL_WORKERS", 4)
MAX_RETRIES = get_env_int("MAX_RETRIES", 2)
RETRY_DELAY = get_env_int("RETRY_DELAY", 3)


# ────────────────────────────────────────────────────────────
# SECTION 9: Logging
# ────────────────────────────────────────────────────────────
LOG_LEVEL = get_env("LOG_LEVEL", "INFO").upper()
LOG_DIR = ROOT_DIR / get_env("LOG_DIR", "logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "automation.log"


# ────────────────────────────────────────────────────────────
# SECTION 10: AI Module Configuration
# ────────────────────────────────────────────────────────────
# Support both ENABLE_AI and AI_ENABLED environment variables
_enable_ai_env = os.getenv("ENABLE_AI")
if _enable_ai_env is not None:
    AI_ENABLED = _enable_ai_env.lower() in ("true", "1", "yes", "on")
else:
    AI_ENABLED = get_env_bool("AI_ENABLED", True)

USE_MOCK_AI = get_env_bool("USE_MOCK_AI", True)
GEMINI_API_KEY = get_env("GEMINI_API_KEY", "")
AI_CONFIDENCE_THRESHOLD = float(get_env("AI_CONFIDENCE_THRESHOLD", "0.85"))
SELF_HEALING_ENABLED = get_env_bool("SELF_HEALING_ENABLED", True)
BUG_PREDICTION_ENABLED = get_env_bool("BUG_PREDICTION_ENABLED", True)


# ────────────────────────────────────────────────────────────
# SECTION 11: Selenium Grid
# ────────────────────────────────────────────────────────────
USE_SELENIUM_GRID = get_env_bool("USE_SELENIUM_GRID", False)
SELENIUM_GRID_URL = get_env("SELENIUM_GRID_URL", "http://localhost:4444/wd/hub")


# ────────────────────────────────────────────────────────────
# SECTION 12: Path Constants
# ────────────────────────────────────────────────────────────
DRIVERS_DIR = ROOT_DIR / "drivers"
DATA_DIR = ROOT_DIR / "data"
TEST_DATA_DIR = DATA_DIR / "test_data"
SCHEMAS_DIR = DATA_DIR / "schemas"


# ────────────────────────────────────────────────────────────
# SECTION 13: Data Classes (type-safe configuration)
# ────────────────────────────────────────────────────────────
@dataclass
class DatabaseConfig:
    """Type-safe database configuration."""
    host: str = DB_HOST
    port: int = DB_PORT
    name: str = DB_NAME
    user: str = DB_USER
    password: str = DB_PASSWORD
    pool_size: int = DB_POOL_SIZE
    max_overflow: int = DB_MAX_OVERFLOW

    @property
    def connection_string(self) -> str:
        """Returns SQLAlchemy connection string for MySQL."""
        return (
            f"mysql+mysqlconnector://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.name}"
        )

    @property
    def sqlite_connection_string(self) -> str:
        """Returns SQLAlchemy connection string for SQLite."""
        return f"sqlite:///{SQLITE_DB_PATH}"


@dataclass
class BrowserConfig:
    """Type-safe browser configuration."""
    browser: str = BROWSER
    headless: bool = HEADLESS
    implicit_wait: int = IMPLICIT_WAIT
    explicit_wait: int = EXPLICIT_WAIT
    page_load_timeout: int = PAGE_LOAD_TIMEOUT
    window_size: str = WINDOW_SIZE
    use_grid: bool = USE_SELENIUM_GRID
    grid_url: str = SELENIUM_GRID_URL


# ── Singleton Config Instances ───────────────────────────────
db_config = DatabaseConfig()
browser_config = BrowserConfig()


def print_config_summary() -> None:
    """Print a summary of the current configuration (useful for debugging)."""
    print("\n" + "=" * 60)
    print("  FRAMEWORK CONFIGURATION SUMMARY")
    print("=" * 60)
    print(f"  Environment : {ENVIRONMENT}")
    print(f"  Base URL    : {BASE_URL}")
    print(f"  API URL     : {API_BASE_URL}")
    print(f"  Browser     : {BROWSER} ({'headless' if HEADLESS else 'headed'})")
    print(f"  DB Host     : {DB_HOST}:{DB_PORT}/{DB_NAME}")
    print(f"  Grid        : {'Enabled @ ' + SELENIUM_GRID_URL if USE_SELENIUM_GRID else 'Disabled'}")
    print(f"  AI Features : {'Enabled (Mock Mode)' if AI_ENABLED and USE_MOCK_AI else 'Enabled (Cloud Mode)' if AI_ENABLED else 'Disabled'}")
    print(f"  Workers     : {PARALLEL_WORKERS}")
    print(f"  Log Level   : {LOG_LEVEL}")
    print("=" * 60 + "\n")
