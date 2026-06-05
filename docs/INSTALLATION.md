# 📦 Installation Guide

Complete step-by-step installation for the AI-Enhanced Enterprise Test Automation Framework.

---

## System Requirements

| Requirement | Minimum | Recommended |
|---|---|---|
| OS | Windows 10 / Ubuntu 20.04 / macOS 12 | Windows 11 / Ubuntu 22.04 |
| Python | 3.9 | 3.11 |
| RAM | 4 GB | 8 GB |
| Storage | 2 GB free | 5 GB free |
| Browser | Chrome 115+ | Chrome latest |
| Docker | Optional | 20.10+ |
| MySQL | Optional | 8.0 |

---

## Step 1: Install Python 3.11

### Windows
```powershell
# Download from python.org or use winget:
winget install Python.Python.3.11

# Verify
python --version       # Python 3.11.x
pip --version          # pip 24.x
```

### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip -y
python3.11 --version
```

### macOS
```bash
brew install python@3.11
python3.11 --version
```

---

## Step 2: Clone the Repository

```bash
# Via HTTPS
git clone https://github.com/yourusername/ai-enterprise-test-framework.git

# OR via SSH
git clone git@github.com:yourusername/ai-enterprise-test-framework.git

# Enter project directory
cd ai-enterprise-test-framework
```

> **Note:** If you don't have Git, download from [git-scm.com](https://git-scm.com)

---

## Step 3: Create Virtual Environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux / macOS
python3.11 -m venv .venv
source .venv/bin/activate

# Verify activation (should show .venv path)
which python    # Linux/Mac
where python    # Windows
```

---

## Step 4: Install Dependencies

```bash
# Upgrade pip first
pip install --upgrade pip

# Install all framework dependencies
pip install -r requirements.txt

# Verify key packages
pip show selenium pytest allure-pytest
```

> **Takes 2–5 minutes** depending on internet speed.

---

## Step 5: Configure Environment Variables

```bash
# Windows
copy .env.example .env
notepad .env

# Linux / macOS
cp .env.example .env
nano .env     # or: code .env
```

### Key Variables to Edit

```ini
# ── Application Target ─────────────────────────────────────
BASE_URL=https://demoqa.com        # Change to YOUR app URL
API_BASE_URL=https://demoqa.com

# ── Test Credentials ────────────────────────────────────────
TEST_USERNAME=your_test_username
TEST_PASSWORD=YourPassword@123

# ── Browser ─────────────────────────────────────────────────
BROWSER=chrome                     # chrome | firefox | edge
HEADLESS=false                     # true for CI/CD

# ── Database (optional — SQLite used if MySQL unavailable) ──
DB_HOST=localhost
DB_PORT=3306
DB_NAME=test_automation_db
DB_USER=root
DB_PASSWORD=your_mysql_password

# ── AI Modules ──────────────────────────────────────────────
AI_ENABLED=true                    # Toggle all AI features (true/false)
USE_MOCK_AI=true                   # true to bypass external cloud AI (recommended for offline/CI/CD stability)
SELF_HEALING_ENABLED=true          # Toggle UI locator healing on failure
BUG_PREDICTION_ENABLED=true        # Toggle bug probability risk checks
```

---

## Step 6: Verify Chrome Installation

```bash
# Check Chrome version
google-chrome --version     # Linux
chrome --version            # macOS
# Windows: Open Chrome → Help → About Google Chrome

# ChromeDriver is auto-downloaded by webdriver-manager
# No manual ChromeDriver installation needed!
```

---

## Step 7: Run Setup Script (Optional)

```bash
# Automated setup: creates directories, copies .env, verifies imports
python scripts/setup_env.py
```

---

## Step 8: Run Smoke Tests

```bash
# This verifies everything is working
pytest tests/ -m smoke -v

# Expected output:
# ✓ tests/ui/test_login.py::TestLogin::test_login_page_ui_elements PASSED
# ✓ tests/ui/test_dashboard.py::TestDashboard::test_dashboard_page_loads PASSED
# ...
```

---

## Optional: Install MySQL

### Windows
```powershell
# Download MySQL 8.0 Community Server from:
# https://dev.mysql.com/downloads/mysql/

# OR use Docker (recommended):
docker run -d --name test-mysql \
  -e MYSQL_ROOT_PASSWORD=RootPass@123 \
  -e MYSQL_DATABASE=test_automation_db \
  -p 3306:3306 \
  mysql:8.0
```

### Linux
```bash
sudo apt install mysql-server -y
sudo mysql_secure_installation
sudo mysql -u root -p
# In MySQL shell:
CREATE DATABASE test_automation_db;
CREATE USER 'automation_user'@'localhost' IDENTIFIED BY 'AutomationDB@123';
GRANT ALL ON test_automation_db.* TO 'automation_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

> **Without MySQL:** The framework automatically falls back to SQLite — database tests still work!

---

## Optional: Install Allure CLI

### Windows
```powershell
# Via Scoop
scoop install allure

# OR via Chocolatey
choco install allure

# OR manual: download from GitHub releases
# https://github.com/allure-framework/allure2/releases
```

### Linux / macOS
```bash
# macOS via Homebrew
brew install allure

# Linux via npm
npm install -g allure-commandline

# Verify
allure --version
```

---

## Optional: Install Docker

```bash
# Download Docker Desktop from:
# https://www.docker.com/products/docker-desktop/

# Verify
docker --version
docker-compose --version

# Run full test stack with Docker:
cd docker
docker-compose up -d
```

---

## Git Configuration (for GitHub integration)

```bash
# Configure git identity (required for commits)
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Verify
git config --list

# Initialize repo (if starting fresh)
git init
git add .
git commit -m "Initial commit: AI-Enhanced Test Framework"
git remote add origin https://github.com/yourusername/repo.git
git push -u origin main
```

---

## Troubleshooting Installation

| Error | Solution |
|---|---|
| `ModuleNotFoundError: selenium` | Run `pip install -r requirements.txt` in activated venv |
| `ChromeDriver not found` | webdriver-manager handles this automatically |
| `Permission denied: .venv` | Run terminal as Administrator (Windows) |
| `pip: command not found` | Use `python -m pip` instead of `pip` |
| `MySQL connection refused` | Framework falls back to SQLite automatically |
| `allure: command not found` | Install Allure CLI (optional, for reports) |

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed solutions.
