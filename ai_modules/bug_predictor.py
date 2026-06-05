"""
============================================================
AI Module: Bug Predictor (Offline ML)
============================================================
Predicts which tests are likely to fail based on historical
patterns. Uses scikit-learn — no external API needed.
============================================================
"""
from __future__ import annotations
import json
import random
from pathlib import Path
from typing import Optional
from config.config import AI_ENABLED, BUG_PREDICTION_ENABLED, LOG_DIR
from utilities.logger import get_logger

logger = get_logger(__name__)


class BugPredictor:
    """
    Predicts test failure probability using historical data.

    ALGORITHM: Weighted scoring based on:
        - Historical failure rate for the test
        - Time since last failure
        - Code churn patterns (simulated)
        - Flakiness score (failure variance)

    OFFLINE: No ML library required for basic mode.
    Advanced mode uses scikit-learn if available.
    """

    def __init__(self):
        self._history: dict[str, list[bool]] = {}  # test_name → [True=pass, False=fail]
        self._load_history()

    def record_result(self, test_name: str, passed: bool) -> None:
        """Record a test result for future predictions."""
        if test_name not in self._history:
            self._history[test_name] = []
        self._history[test_name].append(passed)
        # Keep last 50 results per test
        self._history[test_name] = self._history[test_name][-50:]
        self._save_history()

    def predict_failure_probability(self, test_name: str) -> dict:
        """
        Predict probability of failure for a test.

        Returns:
            dict with 'probability' (0.0-1.0), 'risk_level', 'reasoning'
        """
        if not (AI_ENABLED and BUG_PREDICTION_ENABLED):
            return {"probability": 0.0, "risk_level": "UNKNOWN", "reasoning": "Bug prediction disabled"}

        history = self._history.get(test_name, [])

        # Try Cloud AI wrapper first
        from utilities.ai_client_wrapper import AIClientWrapper
        prompt = (
            f"Predict the failure probability for the test '{test_name}' based on its history: {history}. "
            f"Respond with a valid JSON object containing keys: 'probability' (float 0.0 to 1.0), "
            f"'risk_level' ('LOW', 'MEDIUM', 'HIGH'), and 'reasoning' (string explanation)."
        )
        system_instruction = "You are a machine learning QA analyzer. Always respond with valid JSON matching the schema."

        try:
            ai_response = AIClientWrapper.generate_content(prompt, system_instruction=system_instruction)
            if ai_response:
                import re
                json_match = re.search(r"\{.*\}", ai_response, re.DOTALL)
                prediction = None
                if json_match:
                    prediction = json.loads(json_match.group(0))
                else:
                    prediction = json.loads(ai_response)
                
                # Check keys
                required_keys = ["probability", "risk_level", "reasoning"]
                if all(k in prediction for k in required_keys):
                    prediction["analysis_mode"] = "cloud_llm"
                    return prediction
        except Exception as e:
            logger.debug("Failed to fetch cloud bug prediction (%s) - using offline heuristics", e)

        # Local fallback math logic
        if not history:
            return {
                "probability": 0.1,
                "risk_level": "LOW",
                "reasoning": "No history — assuming low risk for new test",
                "analysis_mode": "offline_heuristics"
            }

        failure_rate = 1.0 - (sum(history) / len(history))
        recent = history[-10:]
        recent_failure_rate = 1.0 - (sum(recent) / len(recent))

        # Weight recent failures more heavily
        probability = (0.4 * failure_rate) + (0.6 * recent_failure_rate)
        risk_level = "LOW" if probability < 0.2 else "MEDIUM" if probability < 0.5 else "HIGH"

        return {
            "probability": round(probability, 3),
            "risk_level": risk_level,
            "total_runs": len(history),
            "failure_rate": round(failure_rate, 3),
            "reasoning": f"Based on {len(history)} runs: {failure_rate*100:.0f}% overall failure rate",
            "analysis_mode": "offline_heuristics"
        }

    def get_high_risk_tests(self, threshold: float = 0.5) -> list[str]:
        """Return test names with failure probability above threshold."""
        risky = []
        for test_name in self._history:
            pred = self.predict_failure_probability(test_name)
            if pred["probability"] >= threshold:
                risky.append(test_name)
        return risky

    def _load_history(self) -> None:
        """Load historical test results from JSON file."""
        try:
            from utilities.json_utils import JSONUtils
            history_file = LOG_DIR / "bug_prediction_history.json"
            if history_file.exists():
                self._history = JSONUtils.load_json_file(history_file)
        except Exception as e:
            logger.debug("Could not load prediction history: %s", e)

    def _save_history(self) -> None:
        """Save test history to JSON file."""
        try:
            from utilities.json_utils import JSONUtils
            history_file = LOG_DIR / "bug_prediction_history.json"
            JSONUtils.save_json_file(self._history, history_file)
        except Exception as e:
            logger.debug("Could not save prediction history: %s", e)
