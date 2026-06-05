# 🎓 Interview Questions & Answers

**100+ Interview Q&A for the AI-Enhanced Enterprise Test Automation Framework**

*Covers: Selenium, PyTest, POM, API Testing, Database, CI/CD, Docker, AI in Testing*

---

## Section 1: Framework Architecture (10 Questions)

**Q1: What is the Page Object Model (POM) design pattern?**

> POM separates test logic from UI implementation. Each web page is represented as a class containing:
> - **Locators** (element selectors) as class variables
> - **Action methods** (click, type, navigate) as instance methods
> - No assertion logic in page objects
>
> *Tests call page methods, never raw Selenium commands.*
> ```python
> # BAD (no POM):
> driver.find_element(By.ID, "username").send_keys("admin")
>
> # GOOD (with POM):
> login_page.enter_username("admin")
> ```

**Q2: What design patterns are used in this framework?**

> - **Factory Pattern** — `DriverFactory.create_driver()` hides browser creation complexity
> - **Page Object Model** — each page is a class
> - **Singleton** — `get_db_connector()` returns one shared DB instance
> - **Decorator Pattern** — `@retry()` wraps functions with retry logic
> - **Context Manager** — `db.session()` auto-commits/rollbacks
> - **Fluent Interface** — `page.enter_username(u).enter_password(p).click_login()`

**Q3: Why use explicit waits over implicit waits or `time.sleep()`?**

> - `time.sleep(5)` always waits 5 seconds even if element appears in 1s → slow
> - Implicit wait applies globally and can conflict with explicit waits
> - Explicit waits (`WebDriverWait`) poll every 500ms and return immediately when condition is met
> - They target specific conditions: `visibility_of_element_located`, `element_to_be_clickable`
> - Our `WaitUtils` class centralizes all wait strategies with configurable timeouts

**Q4: How does the framework handle cross-browser testing?**

> The `DriverFactory` uses a factory pattern:
> ```python
> driver = DriverFactory.create_driver("firefox")  # or "chrome", "edge"
> ```
> - Each browser has its own options class (`ChromeOptions`, `FirefoxOptions`, `EdgeOptions`)
> - `webdriver-manager` auto-downloads the correct driver binary
> - Command-line override: `pytest tests/ --browser=firefox`
> - Docker uses Selenium Grid with Chrome and Firefox nodes

**Q5: How is the framework's configuration managed?**

> Three-layer config system:
> 1. **`.env` file** — machine-specific secrets (never committed to git)
> 2. **`env_config.ini`** — environment defaults (dev/staging/production)
> 3. **`config.py`** — reads both, resolves precedence, exposes typed constants
>
> Priority: `.env` overrides `env_config.ini` defaults.

**Q6: What is the conftest.py file and why is it important?**

> `conftest.py` is PyTest's fixture/hook configuration file. Our conftest:
> - Defines `driver` fixture (creates/quits WebDriver per test)
> - Defines `api_client`, `db` fixtures (session-scoped)
> - Defines page object fixtures (`login_page`, `dashboard_page`)
> - Hooks: `pytest_runtest_makereport` captures screenshots on failure
> - Hooks: `pytest_configure` writes Allure environment metadata
> - Adds custom CLI options (`--browser`, `--headless`, `--env`)

**Q7: What is the difference between `scope="function"` and `scope="session"` fixtures?**

> - `scope="function"` — fixture created/destroyed for EACH test (our `driver` fixture uses this)
> - `scope="class"` — shared within a test class
> - `scope="module"` — shared within a test file
> - `scope="session"` — created once for the entire test run (our `api_client`, `db` use this)
>
> *Use `function` scope for driver to ensure test isolation. Use `session` for expensive setup like DB connections.*

**Q8: How does the retry mechanism work?**

> The `@retry()` decorator wraps a function and catches specified exceptions:
> ```python
> @retry(max_attempts=3, delay=2.0, backoff=2.0,
>        exceptions=(TimeoutException, StaleElementReferenceException))
> def click_button(locator):
>     driver.find_element(*locator).click()
> ```
> - Attempt 1 fails → wait 2s
> - Attempt 2 fails → wait 4s (backoff=2.0)
> - Attempt 3 fails → raise exception
> - `pytest-rerunfailures` retries at the test level (`--reruns=2`)

**Q9: How does the logging framework work?**

> Centralized logging via `get_logger(__name__)`:
> - Console: colored output using `colorlog`
> - File: rotating file handler (10MB max, 5 backups)
> - Per-test logs: optional test-specific log files
> - Thread-safe: separate logger per module name
> - Level override: `LOG_LEVEL=DEBUG` in `.env`

**Q10: How is test data managed?**

> Three sources:
> 1. **JSON files** in `data/test_data/` — loaded via `JSONUtils.load_test_data()`
> 2. **`@pytest.mark.parametrize`** — inline data for simple scenarios
> 3. **`SmartDataGenerator`** — runtime generation using Faker for fresh unique data
>
> Schemas in `data/schemas/` validate API response structure via `jsonschema`.

---

## Section 2: Selenium & UI Testing (20 Questions)

**Q11: What is the difference between `find_element` and `find_elements`?**
> - `find_element` → returns first match; raises `NoSuchElementException` if not found
> - `find_elements` → returns list of all matches; returns empty list if none found

**Q12: How do you handle dynamic elements with changing IDs?**
> Use stable locator strategies: CSS attributes (`[data-testid='btn']`), partial text (`contains()`), XPath axes, or our `SelfHealingLocator` which tries 5 fallback strategies automatically.

**Q13: What is a stale element and how do you handle it?**
> A stale element is a reference to an element that no longer exists in the DOM (page re-rendered). Solutions:
> - Re-find the element after each page load
> - Use `safe_click()` / `safe_get_text()` with built-in retry
> - Add `StaleElementReferenceException` to ignored exceptions in `WebDriverWait`

**Q14: How do you handle file uploads in Selenium?**
> ```python
> file_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
> file_input.send_keys("C:\\path\\to\\file.pdf")  # Direct path — no click needed
> ```

**Q15: How do you handle JavaScript alerts?**
> ```python
> alert = WebDriverWait(driver, 10).until(EC.alert_is_present())
> text = alert.text
> alert.accept()   # OK button
> alert.dismiss()  # Cancel button
> ```

**Q16: What is the difference between `click()` and JavaScript click?**
> - `element.click()` — Selenium simulates user click; fails if element is hidden/intercepted
> - JS click: `driver.execute_script("arguments[0].click();", element)` — bypasses overlays and visibility; use as fallback

**Q17: How do you take a screenshot on test failure?**
> In our `conftest.py`, the `pytest_runtest_makereport` hook runs after every test call. If `rep.failed`, it calls `ScreenshotUtils.capture_on_failure(test_name)` and attaches the PNG to the Allure report.

**Q18: How do you perform drag and drop?**
> ```python
> source = driver.find_element(By.ID, "source")
> target = driver.find_element(By.ID, "target")
> ActionChains(driver).drag_and_drop(source, target).perform()
> ```

**Q19: How do you switch between windows/tabs?**
> ```python
> driver.switch_to.window(driver.window_handles[-1])  # Switch to newest tab
> driver.switch_to.window(driver.window_handles[0])   # Switch back to first tab
> ```

**Q20: What locator strategy is most reliable and why?**
> Priority: `ID` > `CSS Selector` > `XPath`
> - ID: fastest, guaranteed unique (if developer uses them properly)
> - CSS: concise, widely supported, good performance
> - XPath: most flexible but slowest; avoid absolute XPath (`/html/body/div[1]/...`)
> - Avoid: `CLASS_NAME` (non-unique), `TAG_NAME` (too broad)

**Q21: How do you handle dropdowns with `<select>` tags?**
> ```python
> from selenium.webdriver.support.select import Select
> dropdown = Select(driver.find_element(By.ID, "country"))
> dropdown.select_by_visible_text("India")
> dropdown.select_by_value("IN")
> dropdown.select_by_index(5)
> current = dropdown.first_selected_option.text
> ```

**Q22: How do you scroll to an element?**
> ```python
> element = driver.find_element(By.ID, "target")
> driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
> ```

**Q23: What is headless mode and when do you use it?**
> Headless mode runs the browser without a visible UI window. Use it:
> - In CI/CD pipelines (no display available)
> - In Docker containers
> - For faster execution (no rendering overhead)
> Enable: `HEADLESS=true` in `.env` or `--headless=true` CLI flag

**Q24: How do you verify that a page loaded completely?**
> ```python
> WebDriverWait(driver, 30).until(
>     lambda d: d.execute_script("return document.readyState") == "complete"
> )
> ```
> Our `wait_for_page_load()` in BasePage does this automatically after navigation.

**Q25: How do you handle iframes?**
> ```python
> iframe = driver.find_element(By.ID, "frame1")
> driver.switch_to.frame(iframe)    # Enter iframe
> # ... interact with elements inside iframe ...
> driver.switch_to.default_content()  # Exit back to main page
> ```

**Q26: What is the difference between `getText()` and `getAttribute("value")`?**
> - `element.text` — visible text content of an element (paragraphs, spans, buttons)
> - `element.get_attribute("value")` — value of input fields, hidden fields

**Q27: How do you verify an element is NOT visible?**
> ```python
> # Method 1: Check visibility
> assert not element.is_displayed()
>
> # Method 2: WebDriverWait for invisibility
> WebDriverWait(driver, 10).until(EC.invisibility_of_element_located((By.ID, "spinner")))
>
> # Method 3: Our utility
> page.wait_for_disappear((By.ID, "spinner"))
> ```

**Q28: How do you handle AJAX calls?**
> ```python
> # Wait for AJAX to complete (if jQuery)
> WebDriverWait(driver, 10).until(lambda d: d.execute_script("return jQuery.active") == 0)
>
> # OR wait for specific element to appear after AJAX
> WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "result")))
> ```

**Q29: How do you run cross-browser tests?**
> ```bash
> pytest tests/ --browser=chrome -v
> pytest tests/ --browser=firefox -v
> pytest tests/ --browser=edge -v
>
> # In GitHub Actions matrix:
> strategy:
>   matrix:
>     browser: [chrome, firefox]
> ```

**Q30: How do you manage WebDriver instances in parallel execution?**
> Each pytest-xdist worker gets its own process. Our `DriverFactory` uses `threading.local()` storage so each thread/worker gets its own isolated WebDriver instance. The `driver` fixture is `scope="function"` ensuring complete isolation.

---

## Section 3: API Testing (15 Questions)

**Q31: What HTTP methods do you test and what do they do?**
> - `GET` — Retrieve resource(s) → expect 200
> - `POST` — Create new resource → expect 201
> - `PUT` — Replace entire resource → expect 200
> - `PATCH` — Partial update → expect 200
> - `DELETE` — Remove resource → expect 200 or 204

**Q32: What is JSON schema validation?**
> Validates that an API response has the expected structure, field names, and types:
> ```python
> schema = {"type": "object", "required": ["id", "name"], "properties": {"id": {"type": "integer"}}}
> jsonschema.validate(instance=response.json(), schema=schema)
> ```
> Catches regressions where a field is renamed or removed from the API contract.

**Q33: How do you test authentication APIs?**
> ```python
> # 1. Get token
> response = client.post("/auth/token", body={"username": "u", "password": "p"})
> token = response.json()["token"]
>
> # 2. Use token in subsequent requests
> client.set_token(token)
> profile = client.get("/users/me")
> assert profile.status_code == 200
> ```

**Q34: What is API chaining?**
> Using the output of one API call as input for the next:
> ```python
> # Chain: Create user → Get user → Update user → Delete user
> create_resp = client.post("/users", body=user_data)
> user_id = create_resp.json()["id"]
> get_resp = client.get(f"/users/{user_id}")
> delete_resp = client.delete(f"/users/{user_id}")
> ```

**Q35: How do you handle API rate limiting?**
> Our `APIClient` uses `urllib3.Retry` with `status_forcelist=[429]`. On 429 (Too Many Requests), it automatically retries with exponential backoff (0.3s → 0.6s → 1.2s).

**Q36: What is the difference between 400 and 422 status codes?**
> - `400 Bad Request` — Malformed request syntax (invalid JSON, missing required header)
> - `422 Unprocessable Entity` — Valid syntax but business validation failed (e.g., email already taken)

**Q37: How do you test that an API returns correct Content-Type?**
> ```python
> response = client.get("/users")
> content_type = response.headers.get("Content-Type", "")
> assert "application/json" in content_type
> ```

**Q38: What is response time assertion?**
> API performance testing: verify responses come within SLA limits:
> ```python
> start = time.time()
> response = client.get("/users")
> elapsed_ms = (time.time() - start) * 1000
> assert elapsed_ms < 2000, f"Too slow: {elapsed_ms:.0f}ms"
> ```

**Q39: How do you mock API responses in tests?**
> Using the `responses` library:
> ```python
> import responses
> @responses.activate
> def test_with_mock():
>     responses.add(responses.GET, "https://api.example.com/users",
>                   json={"users": []}, status=200)
>     response = client.get("/users")
>     assert response.status_code == 200
> ```

**Q40: What is the difference between end-to-end API testing and contract testing?**
> - **E2E API testing**: Tests the live API, real network, real data
> - **Contract testing** (Pact): Tests that producer and consumer agree on API shape without requiring both live simultaneously

**Q41: How do you test pagination in APIs?**
> ```python
> # Test first page
> resp = client.get("/books", params={"page": 1, "limit": 10})
> assert len(resp.json()["data"]) <= 10
>
> # Test last page returns fewer items
> resp = client.get("/books", params={"page": 999, "limit": 10})
> assert len(resp.json()["data"]) >= 0  # May be empty or fewer
> ```

**Q42: What security tests do you run on APIs?**
> - SQL injection in query params
> - Auth bypass (no token, expired token, wrong token)
> - IDOR (access other user's data by changing ID)
> - Rate limit enforcement
> - Input validation (XSS payloads in POST body)

**Q43: How do you handle environment-specific API endpoints?**
> Our `config.py` resolves URL based on `ENVIRONMENT`:
> ```python
> _URL_MAP = {"dev": {"api_url": "..."}, "staging": {"api_url": "..."}}
> API_BASE_URL = os.getenv("API_BASE_URL") or _URL_MAP[ENVIRONMENT]["api_url"]
> ```

**Q44: What is idempotency in API testing?**
> An operation is idempotent if calling it multiple times has the same effect as calling it once.
> - `GET` is idempotent (same result every time)
> - `PUT` is idempotent (updates to same state)
> - `POST` is NOT idempotent (creates a new resource each time)
> Test: Call `DELETE /users/5` twice → first returns 200, second returns 404

**Q45: How do you validate nested JSON responses?**
> Using JSONPath:
> ```python
> from utilities.json_utils import JSONUtils
> emails = JSONUtils.query_jsonpath(response.json(), "$.data[*].email")
> assert all("@" in email for email in emails)
> ```

---

## Section 4: Database Testing (10 Questions)

**Q46: What is database validation in test automation?**
> Verifying that application actions (UI clicks, API calls) correctly persist data to the database. Example: After registering a user through UI, verify the user record exists in `users` table with correct `email` and `role`.

**Q47: How do you connect to MySQL in Python?**
> ```python
> from sqlalchemy import create_engine, text
> engine = create_engine("mysql+mysqlconnector://user:pass@localhost:3306/db")
> with engine.connect() as conn:
>     result = conn.execute(text("SELECT * FROM users WHERE email=:e"), {"e": "test@test.com"})
> ```

**Q48: Why use parameterized queries?**
> Prevents SQL injection. Never use f-strings or string concatenation in SQL:
> ```python
> # DANGEROUS:
> query = f"SELECT * FROM users WHERE name='{user_input}'"
>
> # SAFE (parameterized):
> query = "SELECT * FROM users WHERE name=:name"
> conn.execute(text(query), {"name": user_input})
> ```

**Q49: What is the SQLite fallback strategy?**
> When MySQL is unavailable, `DBConnector._try_mysql_connect()` catches `OperationalError` and automatically calls `_connect_sqlite()`. All tests use the same `fetch_all()`, `execute_query()` interface, so tests don't need changing. The `db_type` property tells you which DB is active.

**Q50: How do you ensure test data isolation?**
> Using the `clean_db` fixture that truncates test tables after each test:
> ```python
> @pytest.fixture(scope="function")
> def clean_db(db):
>     yield db
>     db.teardown_test_data(["test_users", "test_orders"])
> ```

**Q51: How do you test database constraints?**
> ```python
> def test_unique_email_constraint(clean_db):
>     clean_db.execute_query("INSERT INTO users ... VALUES (:e)", {"e": "same@email.com"})
>     with pytest.raises(Exception):  # Catches SQLAlchemy IntegrityError
>         clean_db.execute_query("INSERT INTO users ... VALUES (:e)", {"e": "same@email.com"})
> ```

**Q52: What is connection pooling and why does it matter?**
> A pool maintains multiple open connections to the DB, reusing them instead of creating/closing for every query. Reduces latency significantly. Our `DBConnector` uses SQLAlchemy's `QueuePool` with configurable `pool_size` and `max_overflow`.

**Q53: How do you verify data consistency across UI and DB?**
> ```python
> # 1. Perform UI action (login form submission)
> login_page.login("user@test.com", "pass")
>
> # 2. Verify in database
> user = db.fetch_one("SELECT last_login FROM users WHERE email=:e", {"e": "user@test.com"})
> assert user["last_login"] is not None, "Login timestamp not updated in DB"
> ```

**Q54: What is a transaction rollback test?**
> Testing that failed operations don't partially commit data. In our framework, the `session()` context manager automatically rolls back on exception:
> ```python
> with db.session() as sess:
>     sess.execute(text("INSERT INTO users ..."))
>     raise ValueError("Force rollback")
> # Database unchanged — rollback happened automatically
> ```

**Q55: How do you test for data integrity?**
> - Check NOT NULL: verify required fields are non-null after insert
> - Check UNIQUE: verify duplicate inserts fail
> - Check FOREIGN KEY: verify orphaned records don't exist
> - Check row counts: insert N records, count should equal N
> - Check data types: price field should be DECIMAL, not VARCHAR

---

## Section 5: CI/CD & DevOps (15 Questions)

**Q56: What is the difference between Continuous Integration and Continuous Deployment?**
> - **CI**: Automatically build + test on every code push
> - **CD**: Automatically deploy to production after CI passes
> - Our GitHub Actions does CI (runs tests). CD would add a deploy step.

**Q57: How does the GitHub Actions workflow trigger?**
> ```yaml
> on:
>   push:
>     branches: [main, develop]    # On code push
>   pull_request:
>     branches: [main]             # On PR creation/update
>   workflow_dispatch:             # Manual trigger from UI
> ```

**Q58: What is a matrix build in GitHub Actions?**
> Runs the same job with multiple configurations simultaneously:
> ```yaml
> strategy:
>   matrix:
>     test-group: [ui, api]     # Runs 2 parallel jobs
>     browser: [chrome, firefox] # 4 jobs total
> ```

**Q59: How do you handle secrets in GitHub Actions?**
> Store in GitHub → Settings → Secrets → Actions:
> ```yaml
> env:
>   TEST_PASSWORD: ${{ secrets.TEST_PASSWORD }}
> ```
> Never hardcode credentials in workflow files.

**Q60: What is the purpose of `concurrency` in GitHub Actions?**
> Prevents redundant runs:
> ```yaml
> concurrency:
>   group: ${{ github.workflow }}-${{ github.ref }}
>   cancel-in-progress: true
> ```
> If a new push happens while tests are running, the old run is cancelled.

**Q61: What is a Jenkins declarative pipeline?**
> A Groovy-based `Jenkinsfile` checked into source control defining the entire CI pipeline as code. Our Jenkinsfile has: Checkout → Setup → Lint → Smoke → Regression → API → DB → Reports → Archive stages.

**Q62: How do you manage credentials in Jenkins?**
> Via Jenkins Credentials Manager (Manage Jenkins → Credentials). Reference in Jenkinsfile:
> ```groovy
> environment {
>     TEST_PASSWORD = credentials('TEST_PASSWORD')
> }
> ```
> Never hardcode passwords in Jenkinsfile.

**Q63: How does Docker improve test reliability?**
> - Eliminates "works on my machine" issues
> - Same OS, same Chrome version, same Python version everywhere
> - Selenium Grid distributes tests across multiple browser containers
> - Tests run in isolated environment with no shared state

**Q64: What is Selenium Grid?**
> A server that allows running tests on multiple machines/browsers simultaneously. Hub distributes test requests to Nodes (Chrome, Firefox, Edge). Our `docker-compose.yml` sets up Hub + Chrome + Firefox nodes.

**Q65: How do you configure test retry in CI/CD?**
> ```yaml
> # GitHub Actions: test-level retry
> run: pytest tests/ --reruns=2 --reruns-delay=3
>
> # Jenkins: stage-level retry
> options { retry(1) }
>
> # Pipeline: run last-failed first
> pytest --lf -v
> ```

**Q66: What is `artifact` archiving in CI/CD?**
> Saving test outputs (HTML reports, screenshots, logs) after pipeline completion so developers can review failures. In GitHub Actions: `actions/upload-artifact`. In Jenkins: `archiveArtifacts`.

**Q67: How do you prevent CI failures from blocking deployments?**
> ```yaml
> # In GitHub Actions: allow test failures but still archive reports
> - run: pytest tests/ -m regression
>   continue-on-error: true

> # In Jenkins:
> catchError(buildResult: 'UNSTABLE', stageResult: 'FAILURE') {
>     sh 'pytest tests/ ...'
> }
> ```

**Q68: What is a flaky test and how do you handle it?**
> A test that sometimes passes and sometimes fails with no code changes. Causes: timing issues, external dependencies, test order dependence. Solutions:
> - Replace `time.sleep()` with explicit waits
> - Add `--reruns=2` for automatic retry
> - Fix test isolation (don't share state between tests)
> - Use `@pytest.mark.flaky` to track known flaky tests

**Q69: How do you cache dependencies in GitHub Actions?**
> ```yaml
> - uses: actions/setup-python@v5
>   with:
>     python-version: "3.11"
>     cache: pip          # Caches pip downloads
>
> - uses: actions/cache@v4
>   with:
>     path: ~/.cache/pip
>     key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
> ```

**Q70: What is the purpose of `pytest.ini` vs `conftest.py`?**
> - `pytest.ini` — static PyTest configuration (markers, addopts, log settings, test paths). Loaded before collection.
> - `conftest.py` — Python fixtures and hooks. Can be per-directory. Auto-discovered by PyTest.

---

## Section 6: AI in Testing (10 Questions)

**Q71: What is a self-healing locator?**
> A locator that automatically recovers when the primary selector fails by trying alternative strategies:
> 1. Primary locator (as written)
> 2. Explicit fallbacks (developer-provided)
> 3. Auto-generated alternatives (ID→CSS, CSS→XPath)
> 4. Fuzzy text matching (finds element with similar text)
> 5. Attribute scanning (aria-label, placeholder, data-testid)

**Q72: How does the AI failure analyzer work?**
> Uses regex pattern matching against a catalogue of known error signatures:
> - `TimeoutException` → TIMEOUT category → suggests increasing wait time
> - `NoSuchElementException` → LOCATOR_ERROR → suggests updating selector
> - `AssertionError` → ASSERTION_FAILURE → suggests reviewing test data
> No external API — runs 100% offline.

**Q73: What is boundary value analysis (BVA)?**
> Testing at the edges of valid input ranges. Our `SmartDataGenerator.boundary_values()` generates:
> - `username`: `""`, `"a"`, `"ab"`, `"a"*50`, `"a"*101` (just below/above limits)
> This catches off-by-one errors in input validation.

**Q74: How does the bug predictor work?**
> Records pass/fail history per test. Calculates weighted failure rate:
> ```
> probability = 0.4 × overall_failure_rate + 0.6 × recent_failure_rate
> ```
> Tests above 50% failure probability are flagged as high-risk. No ML library required for basic mode.

**Q75: What is the difference between AI-assisted and AI-driven testing?**
> - **AI-assisted**: AI helps the human (suggestions, analysis, data generation) — our framework
> - **AI-driven**: AI makes all decisions (test design, execution, assertion) — requires LLM integration

---

## Section 7: PyTest Specific (15 Questions)

**Q76: What is a PyTest fixture?**
> A function decorated with `@pytest.fixture` that provides reusable setup/teardown logic to tests. Tests declare fixtures as parameters and PyTest injects them automatically.

**Q77: How does `@pytest.mark.parametrize` work?**
> ```python
> @pytest.mark.parametrize("username,password,should_pass", [
>     ("admin", "Admin@123", True),
>     ("", "", False),
> ])
> def test_login(username, password, should_pass):
>     ...  # runs twice with different params
> ```

**Q78: What is the `yield` keyword in fixtures?**
> Splits fixture into setup (before yield) and teardown (after yield):
> ```python
> @pytest.fixture
> def driver():
>     web_driver = DriverFactory.create_driver()
>     yield web_driver     # Test runs here
>     web_driver.quit()    # Teardown runs after test
> ```

**Q79: What are PyTest markers?**
> Tags applied to tests for selective execution:
> ```python
> @pytest.mark.smoke      # Run: pytest -m smoke
> @pytest.mark.negative   # Run: pytest -m negative
> ```
> Custom markers must be registered in `pytest.ini` under `[pytest] markers =`

**Q80: How do you skip a test?**
> ```python
> @pytest.mark.skip(reason="Feature not yet implemented")
> def test_new_feature():
>     ...
>
> # Skip conditionally:
> @pytest.mark.skipif(sys.platform == "win32", reason="Unix only")
> def test_unix_path():
>     ...
>
> # Skip inside test:
> if not os.getenv("API_KEY"):
>     pytest.skip("API key not configured")
> ```

**Q81: What is `pytest-xdist` and how does it work?**
> Plugin for parallel test execution. Distributes tests across multiple worker processes:
> ```bash
> pytest tests/ -n 4    # 4 parallel workers
> pytest tests/ -n auto # Use all CPU cores
> ```
> Each worker has its own process and driver instance.

**Q82: What is `--reruns` in pytest-rerunfailures?**
> Automatically retries failed tests N times before marking as failed:
> ```bash
> pytest tests/ --reruns=2 --reruns-delay=3
> # Failed test → wait 3s → retry → wait 3s → retry → if still fails, mark FAILED
> ```

**Q83: How do you assert exceptions in PyTest?**
> ```python
> with pytest.raises(ValueError) as exc_info:
>     some_function_that_should_raise()
> assert "expected message" in str(exc_info.value)
> ```

**Q84: What is `conftest.py` scope hierarchy?**
> PyTest searches for `conftest.py` from test file's directory up to root. Fixtures are available to all tests at the same level or below. Multiple `conftest.py` files can exist at different directory levels.

**Q85: How do you generate an HTML test report?**
> ```bash
> pip install pytest-html
> pytest tests/ --html=report.html --self-contained-html
> ```
> `--self-contained-html` embeds CSS/JS in the HTML file (no external dependencies).

**Q86: What are hooks in PyTest?**
> Functions that PyTest calls at specific lifecycle points. Common hooks:
> - `pytest_configure` — after command-line parsing
> - `pytest_sessionstart` / `pytest_sessionfinish` — session start/end
> - `pytest_runtest_makereport` — after each test phase (our screenshot hook)
> - `pytest_addoption` — add custom CLI options

**Q87: How do you run only failed tests from the last run?**
> ```bash
> pytest tests/ --lf   # --last-failed
> pytest tests/ --ff   # --failed-first (run failed first, then rest)
> ```
> PyTest stores results in `.pytest_cache/`.

**Q88: What is `@pytest.fixture(autouse=True)`?**
> Fixture applied automatically to ALL tests in scope without explicit parameter declaration. Useful for setup that every test needs (e.g., logging test name, resetting state).

**Q89: How do you set test execution order?**
> ```bash
> pip install pytest-ordering
>
> @pytest.mark.run(order=1)
> def test_create_user():
>     ...
>
> @pytest.mark.run(order=2)
> def test_get_user():
>     ...
> ```

**Q90: What is the difference between `assert` and `pytest.raises`?**
> - `assert` — verifies a condition is True; fails test on False
> - `pytest.raises` — verifies code raises a specific exception; fails test if it doesn't raise

---

## Section 8: Behavioral / Situational (10 Questions)

**Q91: A test worked yesterday but fails today. What's your debugging approach?**
> 1. Check if the app changed (release deployed?)
> 2. Run the test in isolation (`pytest test_file.py::test_name -v -s`)
> 3. Enable debug logging (`--log-cli-level=DEBUG`)
> 4. Check screenshots in `reports/screenshots/failures/`
> 5. Check Allure report for step-by-step failure
> 6. Inspect the page source at point of failure
> 7. Check if locator changed (inspect element in browser)

**Q92: How do you handle a test that is consistently flaky?**
> 1. Add `--reruns=2` for automatic retry (short-term fix)
> 2. Replace `time.sleep()` with explicit waits
> 3. Investigate root cause: timing? data? test order dependence?
> 4. Fix isolation: use `clean_db` fixture, fresh driver per test
> 5. Mark with `@pytest.mark.flaky` and create a ticket to track

**Q93: How would you automate testing a feature that requires OTP/2FA?**
> - Ask developers to add a test mode that bypasses 2FA for test accounts
> - Or: use a shared test email + IMAP library to read OTP from inbox
> - Or: mock the OTP service in API tests
> - Never hardcode OTP in tests

**Q94: How do you decide what NOT to automate?**
> Don't automate:
> - Tests that run once or rarely
> - Tests requiring human judgment (e.g., color accuracy, UX feel)
> - Highly volatile UIs under active development
> - Tests with complex dynamic CAPTCHA
> - Exploratory testing

**Q95: What metrics do you use to measure automation quality?**
> - **Execution time**: How long does the suite take?
> - **Pass rate**: What % of tests pass consistently?
> - **Flakiness rate**: % of tests with intermittent failures
> - **Coverage**: % of test cases automated
> - **Defect detection rate**: Bugs caught by automation before production

**Q96: How do you keep tests maintainable as the app evolves?**
> - Centralize locators in page objects (one place to update)
> - Use data-driven testing (change data, not test code)
> - Self-healing locators reduce maintenance
> - Review failing tests after every sprint
> - Avoid hardcoding URLs, credentials, timeouts

**Q97: Describe your test pyramid strategy.**
> ```
>          /\
>         /E2E\    ← Few, slow, expensive (Selenium UI tests)
>        /──────\
>       /  API   \ ← More, medium cost (API tests)
>      /──────────\
>     / Unit Tests \ ← Many, fast, cheap (developer-owned)
>    /──────────────\
> ```
> Our framework: Unit (not covered) → API tests → UI E2E tests

**Q98: How do you set up a new test environment from scratch?**
> 1. Clone repo
> 2. `python scripts/setup_env.py` (creates dirs, installs deps)
> 3. Configure `.env` with target URLs and credentials
> 4. Run `pytest tests/ -m smoke -v` to verify
> 5. If needed: `docker-compose up -d` for full stack

**Q99: What's the most complex automation challenge you've solved?**
> *Sample answer:* "Self-healing locators. The app used dynamically generated IDs that changed on every deploy. I implemented a 5-strategy fallback system that tries the primary locator, then CSS alternatives, then fuzzy text matching. This reduced locator maintenance from hours per week to near-zero."

**Q100: How do you justify automation ROI to management?**
> - **Before**: 20 manual testers × 3 days regression = 60 person-days
> - **After**: Automated regression runs in 15 minutes on CI
> - **ROI**: 1 month to build → saves 720 person-hours/year
> - Additional: Catches regressions before production (saves hotfix cost)
> - Additional: Enables faster release cycles (continuous delivery)

---

*Good luck with your interviews! This framework demonstrates production-grade automation skills. 🚀*
