#!/usr/bin/env python3
"""
============================================================
AI-Enhanced Enterprise Test Automation Framework
Environment Setup Script
============================================================
Run this once to set up your local development environment:
  python scripts/setup_env.py
============================================================
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
VENV_DIR = ROOT_DIR / ".venv"
ENV_FILE = ROOT_DIR / ".env"
ENV_EXAMPLE = ROOT_DIR / ".env.example"

REQUIRED_DIRS = [
    "reports/html-reports",
    "reports/allure-results",
    "reports/screenshots",
    "reports/screenshots/failures",
    "reports/screenshots/elements",
    "logs",
    "logs/test_logs",
    "drivers",
    "data",
]

REQUIRED_PYTHON = (3, 9)


def print_banner():
    print("\n" + "=" * 60)
    print("  AI-Enhanced Enterprise Test Automation Framework")
    print("  Environment Setup")
    print("=" * 60)


def check_python_version():
    """Verify Python version meets minimum requirement."""
    version = sys.version_info[:2]
    if version < REQUIRED_PYTHON:
        print(f"❌ Python {REQUIRED_PYTHON[0]}.{REQUIRED_PYTHON[1]}+ required. Got: {version[0]}.{version[1]}")
        sys.exit(1)
    print(f"✓ Python {version[0]}.{version[1]} OK")


def create_directories():
    """Create all required framework directories."""
    print("\n📁 Creating required directories...")
    for d in REQUIRED_DIRS:
        dir_path = ROOT_DIR / d
        dir_path.mkdir(parents=True, exist_ok=True)
        # Create .gitkeep to track empty dirs in git
        gitkeep = dir_path / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
    print(f"✓ Created {len(REQUIRED_DIRS)} directories")


def setup_env_file():
    """Create .env from .env.example if it doesn't exist."""
    print("\n⚙️  Setting up environment configuration...")
    if ENV_FILE.exists():
        print("✓ .env file already exists (skipping)")
        return
    if ENV_EXAMPLE.exists():
        shutil.copy(ENV_EXAMPLE, ENV_FILE)
        print("✓ Created .env from .env.example")
        print("  ⚠️  IMPORTANT: Edit .env with your actual credentials!")
    else:
        print("⚠️  .env.example not found — creating minimal .env")
        ENV_FILE.write_text(
            "ENVIRONMENT=dev\n"
            "BROWSER=chrome\n"
            "HEADLESS=false\n"
            "BASE_URL=https://demoqa.com\n"
            "AI_ENABLED=true\n"
            "SELF_HEALING_ENABLED=true\n"
            "SCREENSHOT_ON_FAILURE=true\n"
            "LOG_LEVEL=INFO\n"
        )


def install_dependencies():
    """Install Python package dependencies."""
    print("\n📦 Installing dependencies...")
    requirements = ROOT_DIR / "requirements.txt"
    if not requirements.exists():
        print("❌ requirements.txt not found!")
        return False
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(requirements), "--quiet"],
        capture_output=False
    )
    if result.returncode == 0:
        print("✓ All dependencies installed")
        return True
    else:
        print("⚠️  Some dependencies failed — check pip output above")
        return False


def verify_framework():
    """Run a quick import test to verify framework is working."""
    print("\n🔍 Verifying framework imports...")
    test_imports = [
        "selenium",
        "pytest",
        "requests",
        "faker",
        "allure",
        "sqlalchemy",
    ]
    failed = []
    for module in test_imports:
        try:
            __import__(module)
            print(f"  ✓ {module}")
        except ImportError:
            print(f"  ❌ {module} — not installed")
            failed.append(module)
    return len(failed) == 0


def print_next_steps():
    """Print user instructions for next steps."""
    print("\n" + "=" * 60)
    print("  ✅ SETUP COMPLETE!")
    print("=" * 60)
    print("""
  NEXT STEPS:
  ──────────────────────────────────────────────────────────
  1. Edit .env with your credentials:
       notepad .env  (Windows)
       nano .env     (Linux/Mac)

  2. Run smoke tests to verify setup:
       pytest tests/ -m smoke -v

  3. Run full regression:
       pytest tests/ -m regression -v

  4. Run with parallel execution:
       pytest tests/ -n 4 -v

  5. Generate Allure report:
       allure serve reports/allure-results

  6. Use the Windows script:
       scripts\\run_tests.bat smoke

  QUICK REFERENCE:
  ──────────────────────────────────────────────────────────
  Smoke tests only    : pytest tests/ -m smoke
  Regression          : pytest tests/ -m regression
  API tests           : pytest tests/api/
  Database tests      : pytest tests/database/
  Specific browser    : pytest tests/ --browser=firefox
  Headless mode       : pytest tests/ --headless=true
  Parallel (4 workers): pytest tests/ -n 4
  ──────────────────────────────────────────────────────────
""")


def main():
    print_banner()
    check_python_version()
    create_directories()
    setup_env_file()
    install_dependencies()
    success = verify_framework()
    print_next_steps()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
