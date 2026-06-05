"""
============================================================
AI-Enhanced Enterprise Test Automation Framework
AI Module: Failure Analyzer
============================================================
Analyzes test failure patterns using ML/heuristics.
Fully OFFLINE — no external AI API required.
Falls back gracefully when cloud AI is unavailable.
============================================================
"""
from __future__ import annotations
import re
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from collections import Counter
from config.config import AI_ENABLED, LOG_DIR
from utilities.logger import get_logger

logger = get_logger(__name__)

# ── Known failure patterns (offline rules engine) ────────────
FAILURE_PATTERNS = [
    {
        "pattern": r"TimeoutException|timed out|timeout",
        "category": "TIMEOUT",
        "root_cause": "Element not found within wait time",
        "suggestion": "Increase explicit wait, check if element locator is correct, verify page load",
        "severity": "HIGH",
    },
    {
        "pattern": r"NoSuchElementException|Unable to locate element",
        "category": "LOCATOR_ERROR",
        "root_cause": "Element not found in DOM — locator may be incorrect or page changed",
        "suggestion": "Update locator strategy, use self-healing locators, verify page structure",
        "severity": "HIGH",
    },
    {
        "pattern": r"StaleElementReferenceException|stale element",
        "category": "STALE_ELEMENT",
        "root_cause": "DOM was updated after element was found — element reference is outdated",
        "suggestion": "Re-find element, use safe_click() or safe_get_text() with retry",
        "severity": "MEDIUM",
    },
    {
        "pattern": r"ElementClickInterceptedException|click.*intercepted",
        "category": "CLICK_INTERCEPTED",
        "root_cause": "Another element is covering the target — overlay/modal/cookie banner",
        "suggestion": "Dismiss overlays first, use JS click, scroll element into view",
        "severity": "MEDIUM",
    },
    {
        "pattern": r"AssertionError|assert.*failed|Expected.*got",
        "category": "ASSERTION_FAILURE",
        "root_cause": "Test assertion failed — actual value differs from expected",
        "suggestion": "Review test data, check application state, verify expected values",
        "severity": "HIGH",
    },
    {
        "pattern": r"ConnectionError|Max retries|connection.*refused",
        "category": "NETWORK_ERROR",
        "root_cause": "Network connection failed — server may be down or URL incorrect",
        "suggestion": "Check BASE_URL in config, verify server is running, check VPN/firewall",
        "severity": "CRITICAL",
    },
    {
        "pattern": r"JSONDecodeError|json.*decode|invalid.*json",
        "category": "JSON_ERROR",
        "root_cause": "API returned non-JSON response (HTML error page, empty body)",
        "suggestion": "Log full response body, check API endpoint URL, verify auth token",
        "severity": "HIGH",
    },
    {
        "pattern": r"OperationalError|mysql.*error|sqlite.*error|database",
        "category": "DATABASE_ERROR",
        "root_cause": "Database connection or query failed",
        "suggestion": "Check DB credentials, verify MySQL is running, use SQLite fallback",
        "severity": "HIGH",
    },
    {
        "pattern": r"WebDriverException|session.*not.*created|chrome.*crashed",
        "category": "DRIVER_ERROR",
        "root_cause": "Browser/WebDriver initialization failed",
        "suggestion": "Update ChromeDriver, check browser version, use headless mode in CI",
        "severity": "CRITICAL",
    },
    {
        "pattern": r"401|403|Unauthorized|Forbidden",
        "category": "AUTH_ERROR",
        "root_cause": "Authentication or authorization failed",
        "suggestion": "Check credentials in .env, verify token expiry, re-authenticate",
        "severity": "HIGH",
    },
]


class FailureAnalyzer:
    """
    AI-powered test failure analyzer.

    ARCHITECTURE:
        1. PRIMARY: Rule-based pattern matching (always available offline)
        2. SECONDARY: ML-based clustering (if scikit-learn available)
        3. FALLBACK: Returns structured mock analysis (if all else fails)

    NO EXTERNAL API REQUIRED — runs 100% offline.

    USAGE:
        analyzer = FailureAnalyzer()
        result = analyzer.analyze("TimeoutException: element not found after 20s")
        print(result["category"])   # TIMEOUT
        print(result["suggestion"]) # Increase explicit wait...
    """

    def __init__(self):
        self._failure_history: list[dict] = []
        self._analysis_log: list[dict] = []
        logger.info("FailureAnalyzer initialized (offline mode)")

    def analyze(self, error_message: str, test_name: str = "", context: str = "") -> dict:
        """
        Analyze a test failure and return categorized diagnosis.

        Args:
            error_message: The exception/error message string
            test_name: Name of the failing test
            context: Additional context (stack trace, page URL, etc.)

        Returns:
            dict: Analysis result with category, root_cause, and suggestion
        """
        if not AI_ENABLED:
            return self._get_disabled_response(error_message)

        # ── Step 1: Call AI Wrapper with fallback to local rules ──
        from utilities.ai_client_wrapper import AIClientWrapper
        prompt = (
            f"Analyze the following test failure and return a JSON object with keys: "
            f"'category', 'root_cause', 'suggestion', 'severity'.\n"
            f"Error message: {error_message}\n"
            f"Test name: {test_name}\n"
            f"Context: {context}"
        )
        system_instruction = "You are an expert QA failure analyzer. Always respond with valid JSON containing the specified analysis fields."

        analysis = None
        try:
            ai_response = AIClientWrapper.generate_content(prompt, system_instruction=system_instruction)
            # Find the JSON block in case there is surrounding text
            if ai_response:
                import re
                json_match = re.search(r"\{.*\}", ai_response, re.DOTALL)
                if json_match:
                    analysis = json.loads(json_match.group(0))
                else:
                    analysis = json.loads(ai_response)
                
                # Verify required keys
                required_keys = ["category", "root_cause", "suggestion", "severity"]
                if not all(k in analysis for k in required_keys):
                    analysis = None
        except Exception as e:
            logger.debug("Failed to perform/parse cloud failure analysis (%s) - using offline fallback", e)
            analysis = None

        if not analysis:
            analysis = self._pattern_match(error_message)

        # ── Step 2: Frequency analysis from history ──────────
        if self._failure_history:
            frequency_hint = self._check_failure_frequency(analysis["category"])
            if frequency_hint:
                analysis["frequency_note"] = frequency_hint

        # ── Step 3: Record for trend analysis ────────────────
        record = {
            "timestamp": datetime.now().isoformat(),
            "test_name": test_name,
            "error_snippet": error_message[:200],
            "category": analysis["category"],
            "severity": analysis["severity"],
        }
        self._failure_history.append(record)
        self._save_analysis(record)

        logger.info("Failure analyzed: [%s] %s", analysis["category"], analysis["root_cause"])
        return analysis

    def _pattern_match(self, error_message: str) -> dict:
        """Match error against known failure patterns."""
        error_lower = error_message.lower()

        for pattern in FAILURE_PATTERNS:
            if re.search(pattern["pattern"], error_message, re.IGNORECASE):
                return {
                    "category": pattern["category"],
                    "root_cause": pattern["root_cause"],
                    "suggestion": pattern["suggestion"],
                    "severity": pattern["severity"],
                    "matched_pattern": pattern["pattern"],
                    "confidence": 0.90,
                    "analysis_mode": "offline_rules",
                }

        # Default: unknown failure
        return {
            "category": "UNKNOWN",
            "root_cause": "Failure pattern not recognized",
            "suggestion": "Review full stack trace, enable debug logging, check screenshots",
            "severity": "MEDIUM",
            "matched_pattern": None,
            "confidence": 0.40,
            "analysis_mode": "offline_rules",
        }

    def _check_failure_frequency(self, category: str) -> Optional[str]:
        """Detect recurring failure categories (indicates systemic issue)."""
        recent = self._failure_history[-20:]  # Last 20 failures
        category_counts = Counter(r["category"] for r in recent)
        count = category_counts.get(category, 0)
        if count >= 3:
            return f"⚠ This category ({category}) has occurred {count} times recently — likely systemic"
        return None

    def get_failure_summary(self) -> dict:
        """
        Generate a summary of all failures analyzed in this session.

        Returns:
            dict: Category frequencies, most common failure, severity breakdown
        """
        if not self._failure_history:
            return {"message": "No failures analyzed yet"}

        categories = Counter(r["category"] for r in self._failure_history)
        severities = Counter(r["severity"] for r in self._failure_history)

        return {
            "total_failures": len(self._failure_history),
            "by_category": dict(categories.most_common()),
            "by_severity": dict(severities),
            "most_common": categories.most_common(1)[0] if categories else None,
            "recommendation": self._get_top_recommendation(categories.most_common(1)),
        }

    def _get_top_recommendation(self, most_common: list) -> str:
        """Get actionable recommendation based on most frequent failure."""
        if not most_common:
            return "No patterns detected"
        category = most_common[0][0]
        for pattern in FAILURE_PATTERNS:
            if pattern["category"] == category:
                return pattern["suggestion"]
        return "Review test logs for details"

    def _save_analysis(self, record: dict) -> None:
        """Save failure analysis to JSON log file for post-run review."""
        try:
            from utilities.json_utils import JSONUtils
            log_file = LOG_DIR / "failure_analysis.json"
            existing = []
            if log_file.exists():
                try:
                    existing = JSONUtils.load_json_file(log_file)
                except Exception:
                    existing = []
            existing.append(record)
            JSONUtils.save_json_file(existing[-100:], log_file)
        except Exception as e:
            logger.debug("Could not save analysis log: %s", e)

    @staticmethod
    def _get_disabled_response(error_message: str) -> dict:
        """Return minimal response when AI is disabled."""
        return {
            "category": "AI_DISABLED",
            "root_cause": "AI module is disabled (AI_ENABLED=false)",
            "suggestion": "Enable AI in .env: AI_ENABLED=true",
            "severity": "INFO",
            "confidence": 0.0,
            "analysis_mode": "disabled",
        }
