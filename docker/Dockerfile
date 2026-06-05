# ============================================================
# AI-Enhanced Enterprise Test Automation Framework
# Dockerfile
# ============================================================
# Multi-stage build for lean production image
# Base: Python 3.11 + Chromium headless + all framework deps
# ============================================================

FROM python:3.11-slim AS base

# ── Build metadata ──────────────────────────────────────────
LABEL maintainer="QA Automation Team"
LABEL description="AI-Enhanced Enterprise Test Automation Framework"
LABEL version="1.0.0"

# ── Prevent interactive prompts during apt-get ───────────────
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# ── Install system dependencies ──────────────────────────────
# chromium-driver: ChromeDriver for Selenium
# xvfb: Virtual framebuffer (headless display)
# fonts-liberation: Required fonts for Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    firefox-esr \
    xvfb \
    fonts-liberation \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    curl \
    wget \
    unzip \
    jq \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ── Set Chrome binary path ───────────────────────────────────
# Points Selenium to system Chromium instead of downloaded binary
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# ── Set working directory ────────────────────────────────────
WORKDIR /app

# ── Install Python dependencies ──────────────────────────────
# Copy requirements first to leverage Docker layer caching
# If requirements.txt hasn't changed, this layer is cached
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ── Copy framework source code ───────────────────────────────
COPY . .

# ── Create required directories ──────────────────────────────
RUN mkdir -p \
    reports/html-reports \
    reports/allure-results \
    reports/screenshots \
    logs \
    drivers \
    data

# ── Set environment variables for Docker execution ───────────
ENV BROWSER=chrome
ENV HEADLESS=true
ENV ENVIRONMENT=dev
ENV AI_ENABLED=true
ENV SELF_HEALING_ENABLED=true
ENV SCREENSHOT_ON_FAILURE=true
ENV LOG_LEVEL=INFO

# ── Default command: run smoke tests ─────────────────────────
# Override with: docker run ... pytest tests/ -m regression
CMD ["pytest", "tests/", "-m", "smoke", "--tb=short", "-v"]

# ── Health check ─────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import selenium; print('Framework OK')" || exit 1

# ============================================================
# BUILD:
#   docker build -t ai-test-framework:latest .
#
# RUN SMOKE TESTS:
#   docker run --rm ai-test-framework:latest
#
# RUN REGRESSION:
#   docker run --rm ai-test-framework:latest pytest tests/ -m regression
#
# RUN WITH REPORTS:
#   docker run --rm -v $(pwd)/reports:/app/reports ai-test-framework:latest
# ============================================================
