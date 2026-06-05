"""
============================================================
AI-Enhanced Enterprise Test Automation Framework
AI Client Wrapper Utility
============================================================
Coordinates all cloud AI API integrations (e.g. Gemini) with
automatic quota checking, retry mechanics, and a graceful
local mock fallback system. Prevents CI pipeline failures.
============================================================
"""
import os
import json
from typing import Optional, Any
from config.config import AI_ENABLED, USE_MOCK_AI, GEMINI_API_KEY
from utilities.logger import get_logger

logger = get_logger(__name__)

# Dynamic import of google-generativeai to prevent startup crashes if not installed
try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False


class AIClientWrapper:
    """
    Wrapper for AI integrations with robust fallback mechanisms.
    If the quota is exceeded or the API key is not configured, it fails over to a local mock AI.
    """
    _quota_exhausted = False
    _initialized = False

    @classmethod
    def _init_gemini(cls) -> None:
        """Initialize the Gemini API client safely."""
        if cls._initialized:
            return
        if not AI_ENABLED:
            logger.info("AI features are disabled globally via configuration.")
            cls._initialized = True
            return
        if USE_MOCK_AI:
            logger.info("AI Client initialized in MOCK mode (USE_MOCK_AI=True)")
            cls._initialized = True
            return
        if not GEMINI_API_KEY or GEMINI_API_KEY == "your_api_key_here":
            logger.warning("GEMINI_API_KEY is missing or set to placeholder. Defaulting to local mock mode.")
            cls._quota_exhausted = True
            cls._initialized = True
            return

        if not HAS_GENAI:
            logger.warning("google-generativeai library is not installed. Defaulting to local mock mode.")
            cls._quota_exhausted = True
            cls._initialized = True
            return

        try:
            genai.configure(api_key=GEMINI_API_KEY)
            cls._initialized = True
            logger.info("✓ Gemini API Client configured successfully")
        except Exception as e:
            logger.error("Failed to configure Gemini API client: %s. Falling back to local mock mode.", e)
            cls._quota_exhausted = True
            cls._initialized = True

    @classmethod
    def generate_content(cls, prompt: str, system_instruction: Optional[str] = None) -> str:
        """
        Generate content using Gemini API, with automatic fallback to mock responses on quota limits.

        Args:
            prompt: Text prompt to send to the model
            system_instruction: Optional context/instructions for the system persona

        Returns:
            str: Generated content or mock fallback
        """
        cls._init_gemini()

        if not AI_ENABLED:
            return cls._get_mock_response(prompt, "AI_DISABLED")

        if USE_MOCK_AI or cls._quota_exhausted:
            return cls._get_mock_response(prompt, "MOCK_MODE_ACTIVE" if USE_MOCK_AI else "QUOTA_EXHAUSTED_FALLBACK")

        try:
            # Invoke the Generative Model
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                system_instruction=system_instruction
            )
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            err_msg = str(e)
            # Check for quota limits, high traffic, rate limits or resource exhaustion
            if any(term in err_msg or term in err_msg.lower() for term in ["429", "resourceexhausted", "quota", "traffic", "limit"]):
                logger.error("⚠ AI Quota reached or server busy (%s). Activating framework-wide offline fallback.", err_msg)
                cls._quota_exhausted = True
            else:
                logger.error("AI API Call failed (%s). Falling back to mock response.", err_msg)
            return cls._get_mock_response(prompt, "API_FAILURE_FALLBACK")

    @classmethod
    def _get_mock_response(cls, prompt: str, reason: str) -> str:
        """Generate structured local mock responses based on the query pattern."""
        logger.info("Generating local mock AI response (reason: %s)", reason)
        prompt_lower = prompt.lower()

        # 1. Failure Analysis Query
        if "analyze" in prompt_lower or "failure" in prompt_lower or "exception" in prompt_lower:
            analysis = {
                "category": "TIMEOUT",
                "root_cause": "Element did not load in the page DOM within the explicit wait timeout.",
                "suggestion": "Increase the explicit wait time, check if the selector needs self-healing, and verify server latency.",
                "severity": "HIGH",
                "confidence": 0.85,
                "analysis_mode": "mock_llm"
            }
            if "nosuchelement" in prompt_lower:
                analysis["category"] = "LOCATOR_ERROR"
                analysis["root_cause"] = "The element was not found in the DOM (NoSuchElementException)."
                analysis["suggestion"] = "Update locator strategy or verify page structure has not changed."
            elif "staleelement" in prompt_lower:
                analysis["category"] = "STALE_ELEMENT"
                analysis["root_cause"] = "The element reference is stale due to a dynamic page refresh."
                analysis["suggestion"] = "Re-locate the element in the DOM before performing actions."
            elif "assertionerror" in prompt_lower:
                analysis["category"] = "ASSERTION_FAILURE"
                analysis["root_cause"] = "Assertion failed: expected value does not match actual value."
                analysis["suggestion"] = "Review the test data and verify if the application state matches expectations."
            elif "connection" in prompt_lower or "refused" in prompt_lower:
                analysis["category"] = "NETWORK_ERROR"
                analysis["root_cause"] = "The connection to the target host failed."
                analysis["suggestion"] = "Check the host URL status and network connectivity."
            return json.dumps(analysis)

        # 2. Test Case Generation Query
        if "test case" in prompt_lower or "generate cases" in prompt_lower or "outline" in prompt_lower:
            cases = [
                "TC-MOCK-001: Verify successful login with valid credentials",
                "TC-MOCK-002: Verify invalid password rejects login with error",
                "TC-MOCK-003: Verify empty username validation is enforced",
                "TC-MOCK-004: Verify SQL injection prevention on authentication fields"
            ]
            return json.dumps(cases)

        # 3. Bug Prediction Query
        if "predict" in prompt_lower or "risk" in prompt_lower:
            prediction = {
                "probability": 0.25,
                "risk_level": "MEDIUM",
                "reasoning": "Recent code updates in authentication modules suggest moderate risk.",
                "analysis_mode": "mock_llm"
            }
            return json.dumps(prediction)

        return "Local mock AI response: Operation completed successfully without external API dependencies."
