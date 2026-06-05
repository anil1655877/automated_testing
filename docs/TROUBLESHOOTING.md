# 🔧 Troubleshooting Guide

Solutions for every common issue in the AI-Enhanced Enterprise Test Automation Framework.

---

## Table of Contents
1. [Installation Issues](#installation-issues)
2. [Browser & WebDriver Issues](#browser--webdriver-issues)
3. [Test Execution Issues](#test-execution-issues)
4. [Parallel Execution Issues](#parallel-execution-issues)
5. [Database Issues](#database-issues)
6. [API Test Issues](#api-test-issues)
7. [Docker Issues](#docker-issues)
8. [CI/CD Issues](#cicd-issues)
9. [AI Module Issues](#ai-module-issues)
10. [Reporting Issues](#reporting-issues)

---

## Installation Issues

### ❌ `ModuleNotFoundError: No module named 'selenium'`
```bash
# FIX: Activate virtual environment first
.venv\Scripts\activate    # Windows
source .venv/bin/activate # Linux/Mac
pip install -r requirements.txt
```

### ❌ `pip: command not found`
```bash
# FIX: Use python -m pip
python -m pip install -r requirements.txt
python3 -m pip install -r requirements.txt  # Linux
```

### ❌ `Permission denied creating .venv`
```powershell
# FIX: Run as Administrator (Windows)
# Right-click PowerShell → Run as Administrator
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
python -m venv .venv
```

### ❌ `colorlog not found` / `fuzzywuzzy not found`
```bash
# FIX: Some packages need separate install
pip install colorlog fuzzywuzzy python-Levenshtein
```

---

## Browser & WebDriver Issues

### ❌ `SessionNotCreatedException: Message: session not created`
```
This error means Chrome and ChromeDriver versions don't match.
```
```bash
# FIX 1: webdriver-manager handles this automatically
# Make sure it's in requirements.txt: webdriver-manager==4.0.2

# FIX 2: Clear webdriver-manager cache
rmdir /s "%USERPROFILE%\.wdm"    # Windows
rm -rf ~/.wdm                    # Linux/Mac

# FIX 3: Update Chrome to latest version
# Then re-run tests — webdriver-manager downloads matching driver
```

### ❌ `WebDriverException: Chrome failed to start`
```bash
# FIX: Add headless + sandbox flags for server environments
# In config/browser_config.py, ensure these are set:
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--headless=new")

# OR set in .env:
HEADLESS=true
```

### ❌ `TimeoutException: Message: timed out after X seconds`
```bash
# FIX 1: Increase wait times in .env
EXPLICIT_WAIT=30         # Increase from 20
PAGE_LOAD_TIMEOUT=90     # Increase from 60

# FIX 2: The page may be loading slowly — check network
# FIX 3: Locator may have changed — inspect element and update
```

### ❌ `NoSuchElementException: Unable to locate element`
```python
# FIX 1: Enable self-healing locators
SELF_HEALING_ENABLED=true   # In .env

# FIX 2: Inspect the current page source
driver.page_source           # Print page source for debugging

# FIX 3: Wait longer for the element
self.wait.wait_for_element_visible((By.ID, "my-element"), timeout=30)

# FIX 4: Element may be in an iframe
self.switch_to_frame(iframe_locator)
# ... interact with element ...
self.switch_to_default_content()
```

### ❌ `StaleElementReferenceException`
```python
# FIX: Use safe_click() and safe_get_text() with built-in retry
page.safe_click((By.ID, "btn"))         # Retries up to 3 times
page.safe_get_text((By.ID, "msg"))      # Retries up to 3 times

# OR use the retry decorator
from utilities.retry_utils import retry_on_exception

@retry_on_exception((StaleElementReferenceException,), max_attempts=3)
def get_element_text():
    return driver.find_element(By.ID, "content").text
```

---

## Test Execution Issues

### ❌ `Failed to create report directory`
```bash
# FIX: Create directories manually
mkdir -p reports/html-reports reports/allure-results reports/screenshots logs
# OR run setup script:
python scripts/setup_env.py
```

### ❌ `ImportError: cannot import name 'config'`
```bash
# FIX: Add project root to PYTHONPATH
set PYTHONPATH=%CD%          # Windows
export PYTHONPATH=$(pwd)     # Linux/Mac

# OR run pytest from project root always:
cd C:\Automation_Testing
pytest tests/ -v
```

### ❌ Tests fail because of wrong BASE_URL
```bash
# FIX: Update .env file
BASE_URL=https://demoqa.com          # Demo site (free)
API_BASE_URL=https://demoqa.com

# The framework uses DemoQA by default (no registration needed for most tests)
```

### ❌ `FAILED tests/ui/test_login.py::TestLogin::test_valid_login`
```bash
# This means login credentials are wrong
# FIX: Register an account at https://demoqa.com/register
# Then update .env:
TEST_USERNAME=your_registered_username
TEST_PASSWORD=YourPassword@123
```

---

## Parallel Execution Issues

### ❌ `execnet.gateway.gateway_bootstrap.EOFError` / OneDrive Synchronization Conflicts
```
CAUSE: OneDrive locks temporary file descriptors or log files generated during worker initialization, causing pytest-xdist channels to crash.
```
```bash
# FIX 1: Move the project directory OUT of any OneDrive managed folder.
#   Bad:  C:\Users\userName\OneDrive\Automation_Testing
#   Good: C:\Automation_Testing  (Run from a local disk root)

# FIX 2: Antigravity framework wraps JSON logging read/write operations in retry loops (utilities/json_utils.py).
# If conflicts persist, pause or close OneDrive sync while running full regressions.
```

### ❌ `sqlite3.OperationalError: database is locked` / xdist Worker Collisions
```
CAUSE: Multiple parallel worker processes attempting to write to the SQLite database file concurrently (typically during schema creation).
```
```bash
# FIX: The framework includes process-level locking built into tests/conftest.py.
# Only the primary worker (gw0) sets up the schema, while other workers wait for 'db_setup.lock'.
#
# If a build is hard-interrupted, a stale lock file might remain. Run:
rm -f data/db_setup.lock  # Linux/Mac
Remove-Item -Force data/db_setup.lock -ErrorAction SilentlyContinue # PowerShell

# Alternatively, reduce worker count:
pytest tests/ -n 2 --dist=loadscope
```

### ❌ Worker fails to bootstrap
```bash
# FIX: Use forked execution mode (safer on Windows)
pytest tests/ -n 2 --dist=loadscope -v

# FIX: Reduce workers
pytest tests/ -n 1 -v   # Sequential but still uses xdist
```

### ❌ Tests pass alone but fail in parallel
```bash
# CAUSE: Tests sharing state (driver, DB data, files)
# FIX: Each test should be independent
# - Each test gets its own driver (scope="function" in conftest)
# - Use clean_db fixture to reset DB after each test
# - Don't use global variables in tests
```

---

## Database Issues

### ❌ `OperationalError: Can't connect to MySQL server`
```bash
# CAUSE: MySQL not running or wrong credentials
# FIX 1: Framework automatically falls back to SQLite
# Check logs for: "MySQL unavailable — falling back to SQLite"

# FIX 2: Start MySQL service
net start MySQL80              # Windows
sudo systemctl start mysql     # Linux

# FIX 3: Verify credentials in .env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password

# FIX 4: Test connection manually
mysql -u root -p -e "SELECT 1"
```

### ❌ `sqlite3.OperationalError: no such table`
```bash
# FIX: Run schema setup
from utilities.db_connector import get_db_connector
db = get_db_connector(use_sqlite=True)
db.setup_test_schema()   # Creates all tables

# OR: The conftest.py db fixture does this automatically
# Make sure your test uses the 'db' fixture:
def test_something(db):
    ...
```

---

## API Test Issues

### ❌ `ConnectionError: Max retries exceeded`
```bash
# CAUSE: API server is down or URL is wrong
# FIX: Check BASE_URL in .env
BASE_URL=https://demoqa.com
API_BASE_URL=https://demoqa.com

# Verify connectivity:
curl https://demoqa.com/BookStore/v1/Books
```

### ❌ API returns 401 Unauthorized
```bash
# CAUSE: Auth token not set or expired
# FIX 1: Check TEST_USERNAME and TEST_PASSWORD in .env
# FIX 2: Register at https://demoqa.com/register first
# FIX 3: The token test (test_generate_auth_token) skips gracefully if creds missing
```

---

## Docker Issues

### ❌ `docker build` fails
```bash
# FIX: Ensure Docker Desktop is running
docker info

# FIX: Build from project root (not docker/ folder)
docker build -t ai-test-framework -f docker/Dockerfile .
```

### ❌ Chrome crashes in Docker
```bash
# FIX: Add --shm-size flag
docker run --rm --shm-size=2gb ai-test-framework pytest tests/ -m smoke

# OR in docker-compose.yml:
shm_size: 2gb
```

---

## CI/CD Issues

### ❌ GitHub Actions: `Error: Process completed with exit code 1`
```bash
# FIX 1: Check if smoke tests pass locally first
pytest tests/ -m smoke -v

# FIX 2: Check for missing secrets in GitHub
# Settings → Secrets → Actions:
# TEST_USERNAME, TEST_PASSWORD, DB_PASSWORD

# FIX 3: Tests may be timing out — check logs for TimeoutException
```

### ❌ Jenkins: `fatal: unable to auto-detect email address`
```bash
# FIX: Configure git identity in Jenkins
git config --global user.email "jenkins@yourcompany.com"
git config --global user.name "Jenkins CI"

# OR in Jenkinsfile:
sh 'git config user.email "jenkins@ci.com"'
sh 'git config user.name "Jenkins"'
```

---

## AI Module Issues

### ❌ `Individual quota reached` / `Our servers are experiencing high traffic` / Quota Exceeded
These are external API errors indicating that your Cloud AI service (such as Google Gemini API) has reached its limits.

```bash
# FIX 1: Set USE_MOCK_AI=true in your .env file.
# The framework will automatically bypass the cloud API and fall back to local mock generation.
USE_MOCK_AI=true

# FIX 2: Set ENABLE_AI=false or AI_ENABLED=false in .env.
# This will disable the AI modules entirely, relying on standard Selenium/API execution.
ENABLE_AI=false

# FIX 3: Check GEMINI_API_KEY in .env.
# Ensure you are using a valid API key with overages enabled.
# The AIClientWrapper is designed to automatically detect quota limit failures (HTTP 429),
# log a warning, and gracefully switch to local mock mode for the remainder of the session.
```

### ❌ `fuzzywuzzy: UserWarning: Using slow python-Levenshtein`
```bash
# FIX: Install the C extension for speed
pip install python-Levenshtein
# Warning disappears, fuzzy matching becomes 10x faster
```

---

## Reporting Issues

### ❌ Allure report is empty
```bash
# FIX: Run tests with --alluredir flag
pytest tests/ --alluredir=reports/allure-results

# Then serve:
allure serve reports/allure-results
```

### ❌ `allure: command not found`
```bash
# FIX: Install Allure CLI
# Windows (Scoop):
scoop install allure

# macOS:
brew install allure

# Verify:
allure --version
```

### ❌ Screenshots not attached to Allure
```bash
# FIX 1: Enable screenshot on failure in .env
SCREENSHOT_ON_FAILURE=true

# FIX 2: Check that allure-pytest is installed
pip install allure-pytest allure-python-commons

# FIX 3: The conftest.py hook attaches screenshots automatically
# Ensure your test uses the 'driver' fixture (not a custom driver)
```

---

## Quick Diagnostic Checklist

Run this sequence if nothing works:

```bash
# 1. Check Python version
python --version

# 2. Check venv is active
which python   # Should show .venv path

# 3. Check all imports
python -c "import selenium, pytest, requests, faker; print('OK')"

# 4. Check .env exists
type .env     # Windows
cat .env      # Linux/Mac

# 5. Check directories exist
dir reports   # Windows
ls reports    # Linux/Mac

# 6. Run simplest possible test
pytest tests/ui/test_login.py::TestLogin::test_login_page_ui_elements -v -s

# 7. Enable maximum debug output
pytest tests/ -m smoke -v -s --log-cli-level=DEBUG
```
