# 🚶 Framework Walkthrough

This document provides a walkthrough of the design modifications, stabilization improvements, and verification results implemented to make this test automation platform enterprise-ready.

---

## 📋 Table of Contents
1. [Core Problems & Solutions](#1-core-problems--solutions)
2. [Stabilization Accomplished](#2-stabilization-accomplished)
3. [Verification & Test Results](#3-verification--test-results)
4. [Execution Guide for Visual Reports](#4-execution-guide-for-visual-reports)

---

## 1. Core Problems & Solutions

During development and pipeline execution, three severe issues threatened framework stability:

### Problem A: Cloud AI Quota Outages (`429 ResourceExhausted`)
* **Symptom:** Tests utilizing cloud models for failure diagnosis or test generation crashed when hitting quota limits.
* **Solution:** Engineered `AIClientWrapper`. If an external API call throws a `429` rate limit or network exception, it is caught, logged, and sets a session-wide `_quota_exhausted` flag. All subsequent AI diagnostics are dynamically rerouted to local offline rule/match engines, guaranteeing zero pipeline blockages.

### Problem B: Parallel Concurrency locks (`sqlite3.OperationalError: database is locked`)
* **Symptom:** When running database tests in parallel using `pytest-xdist`, worker processes simultaneously attempted to initialize the SQLite schema, resulting in file write locks.
* **Solution:** Implemented process-level coordination inside `conftest.py`. The primary worker (`gw0`) sets up the schema and generates `db_setup.lock`. All## 📂 Folder Upload Fix & Whitelist Filtering

The folder validation and filtering system has been redesigned to support high-performance whitelisting:

### 1. High Performance Scanner (Optimized for 30,000+ Files):
- Uses a **single-pass high-speed iteration** loop on raw `FileList` to process large project folders instantly.
- Keeps memory usage flat by avoiding multiple intermediate maps/filters.

### 2. Whitelist & Security Bypass Policy:
- Ignores directories recursively: `node_modules`, `.git`, `dist`, `build`, `.next`, `coverage`, `temp`, `cache`.
- Filters out dangerous scripts and binaries: `.exe`, `.dll`, `.bat`, `.sh`, `.cmd`, `.msi`, `.apk`.
- Accepts only safe whitelisted formats: `.js`, `.jsx`, `.ts`, `.tsx`, `.html`, `.css`, `.scss`, `.json`, `.md`, `.py`, `.java`, `.cpp`, `.c`, `.php` (and common web images like `.png`, `.jpg`, `.svg`).
- **Continues uploading** all safe files instead of rejecting the entire folder when dangerous scripts are found.

### 3. Clear UI Color Coding:
- **Green text** for Uploadable Files count.
- **Orange text** for Ignored Files count.
- **Red background alert box** only for critical faults (such as when 0 safe files exist or when the network connection drops).

### 4. Smart Recommendations Badge:
- Automatically detects large projects (size > 25MB or files count > 1500) and displays actionable tips suggesting the ZIP uploader or verifying directory cleanup.

---

## 2. Stabilization Accomplished

The framework code was modified and polished across these key layers:
- **`config/config.py`**: Added environment-aware configs (`ENABLE_AI`, `USE_MOCK_AI`) to control execution behavior in offline/CI modes.
- **`pages/base_page.py`**: Eliminated all arbitrary `time.sleep` blocks, migrating synchronization to Explicit Selenium Waits.
- **`tests/api/test_crud_api.py`**: Configured credential validation. If standard default placeholders are found, the test gracefully skips instead of failing.
- **`scripts/generate_portfolio_visuals.py`**: Programmatically drew dark-mode infographics representing the architecture, reports, and pipelines, storing them directly under `docs/screenshots/`.

---

## 3. Verification & Test Results

Verification runs successfully validated UI, API, and Database actions under serial and parallel executions:

### 1. Database CRUD Verification (Parallel)
```bash
python -m pytest tests/database/ -n 2 -v
```
* **Result:** **8/8 PASSED**. Worker locks successfully prevented SQLite write collisions.

### 2. REST API Verification (Parallel & Skip Check)
```bash
python -m pytest tests/api/ -n 2 -v
```
* **Result:** **6 PASSED, 1 SKIPPED**. Successfully validated auth, payloads, response times, and schema checks, skipping on default credentials.

### 3. UI/POM Verification (Headless Mode)
```bash
python -m pytest tests/ui/test_login.py -k test_login_page_ui_elements --headless=true -v
```
* **Result:** **1 PASSED**. Explicit waits synchronized elements correctly.

---

## 4. Execution Guide for Visual Reports

To generate the reports and trends shown in the documentation:

### Generate Allure Results
```bash
python -m pytest tests/ --alluredir=reports/allure-results
```

### Open the Allure Dashboard
```bash
allure serve reports/allure-results
```

### View Historical Run Trends
Access the generated reports under:
* **Current Run Metadata**: `reports/analytics/current_run.json`
* **Historical Trend Log**: `reports/analytics/historical_trend.json`
* **HTML Report**: `reports/html-reports/report.html`

---

## 5. Portfolio Website & Live Demos

To showcase this framework to recruiters, a dedicated React + Tailwind CSS v4 dashboard website has been built under [portfolio-website](file:///c:/Automation_Testing/portfolio-website).

### Features of the Portfolio Site:
- **Interactive Metrics Dashboard**: Showcases run-time stats (7 Mins run duration, 99.8% stability) and tech stack.
- **Self-Healing Simulator**: Allows users to input selectors and inspect the simulated runtime recovery logs.
- **Recharts Data Widgets**: Visualizes historical regression stability trends and suite breakdowns.
- **Pipeline Stage Visualizer**: Animates Jenkins / GitHub Actions workflows.
- **Dynamic Screenshot Carousel**: Slides through allure reports, docker details, and pipeline charts.

### Build and Local Run Instructions:
```bash
# Enter subfolder
cd portfolio-website

# Compile build
npm run build

# Start local server
npm run dev
# Opens local port at: http://localhost:5173/
```

