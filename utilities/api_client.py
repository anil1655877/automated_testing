"""
============================================================
AI-Enhanced Enterprise Test Automation Framework
API Client Utility
============================================================
A reusable REST API client with token authentication,
request/response logging, schema validation, retry logic,
and session management for API test automation.
============================================================
"""
from __future__ import annotations
import json
import time
from typing import Any, Optional, Union
from urllib.parse import urljoin

import requests
from requests import Response, Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import jsonschema

from config.config import API_BASE_URL, API_TIMEOUT, API_KEY
from utilities.logger import get_logger

logger = get_logger(__name__)


class APIClient:
    """
    Enterprise-grade REST API test client.

    FEATURES:
        - Automatic token/API key auth management
        - Built-in retry with exponential backoff
        - Request/response logging
        - JSON schema validation
        - Response time tracking
        - Session reuse for performance
        - Chainable API calls

    USAGE:
        client = APIClient()

        # GET request
        response = client.get("/users")
        assert response.status_code == 200

        # POST with body
        response = client.post("/users", body={"name": "John"})
        assert response.json()["id"] is not None

        # With auth token
        client.set_token("Bearer eyJhbGci...")
        response = client.get("/profile")

        # Schema validation
        client.validate_schema(response, user_schema)
    """

    def __init__(
        self,
        base_url: str = API_BASE_URL,
        timeout: int = API_TIMEOUT,
        api_key: str = API_KEY,
    ):
        """
        Initialize API client with base URL and defaults.

        Args:
            base_url: Base API URL (all requests relative to this)
            timeout: Request timeout in seconds
            api_key: API key for authentication
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.api_key = api_key
        self._token: Optional[str] = None
        self._session = self._create_session()
        self._response_times: list[float] = []
        logger.info("APIClient initialized: %s", self.base_url)

    def _create_session(self) -> Session:
        """
        Create a requests Session with retry strategy.

        RETRY STRATEGY:
            - Retries on 429 (rate limit), 500, 502, 503, 504
            - Exponential backoff: 0.3s, 0.6s, 1.2s ...
            - Connection + read timeouts
        """
        session = Session()

        retry_strategy = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "DELETE"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Default headers
        session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "EnterpriseTestFramework/1.0",
        })

        if self.api_key:
            session.headers.update({"X-API-Key": self.api_key})

        return session

    def set_token(self, token: str) -> "APIClient":
        """
        Set Bearer token for subsequent authenticated requests.

        Args:
            token: JWT or Bearer token (include 'Bearer ' prefix if needed)

        Returns:
            self (for method chaining)
        """
        self._token = token
        if not token.startswith("Bearer "):
            token = f"Bearer {token}"
        self._session.headers.update({"Authorization": token})
        logger.debug("Authorization token set")
        return self

    def clear_token(self) -> "APIClient":
        """Remove Authorization header."""
        self._token = None
        self._session.headers.pop("Authorization", None)
        logger.debug("Authorization token cleared")
        return self

    def set_header(self, key: str, value: str) -> "APIClient":
        """
        Add/update a custom request header.

        Args:
            key: Header name
            value: Header value
        """
        self._session.headers.update({key: value})
        return self

    # ─────────────────────────────────────────────────────────
    # HTTP Methods
    # ─────────────────────────────────────────────────────────

    def get(
        self,
        endpoint: str,
        params: Optional[dict] = None,
        headers: Optional[dict] = None,
        **kwargs,
    ) -> Response:
        """Send GET request."""
        return self._request("GET", endpoint, params=params, headers=headers, **kwargs)

    def post(
        self,
        endpoint: str,
        body: Optional[dict] = None,
        params: Optional[dict] = None,
        headers: Optional[dict] = None,
        **kwargs,
    ) -> Response:
        """Send POST request with JSON body."""
        return self._request("POST", endpoint, body=body, params=params, headers=headers, **kwargs)

    def put(
        self,
        endpoint: str,
        body: Optional[dict] = None,
        params: Optional[dict] = None,
        headers: Optional[dict] = None,
        **kwargs,
    ) -> Response:
        """Send PUT request with JSON body."""
        return self._request("PUT", endpoint, body=body, params=params, headers=headers, **kwargs)

    def patch(
        self,
        endpoint: str,
        body: Optional[dict] = None,
        headers: Optional[dict] = None,
        **kwargs,
    ) -> Response:
        """Send PATCH request."""
        return self._request("PATCH", endpoint, body=body, headers=headers, **kwargs)

    def delete(
        self,
        endpoint: str,
        params: Optional[dict] = None,
        headers: Optional[dict] = None,
        **kwargs,
    ) -> Response:
        """Send DELETE request."""
        return self._request("DELETE", endpoint, params=params, headers=headers, **kwargs)

    def _request(
        self,
        method: str,
        endpoint: str,
        body: Optional[dict] = None,
        params: Optional[dict] = None,
        headers: Optional[dict] = None,
        **kwargs,
    ) -> Response:
        """
        Core request method with logging, timing, and error handling.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (relative to base_url)
            body: Request body (JSON)
            params: URL query parameters
            headers: Additional request headers

        Returns:
            Response: requests Response object
        """
        url = urljoin(self.base_url + "/", endpoint.lstrip("/"))
        start_time = time.time()

        logger.info("→ %s %s | Params: %s | Body: %s",
                    method, url, params, str(body)[:200] if body else None)

        try:
            response = self._session.request(
                method=method,
                url=url,
                json=body,
                params=params,
                headers=headers,
                timeout=self.timeout,
                **kwargs,
            )
            elapsed = time.time() - start_time
            self._response_times.append(elapsed)

            logger.info(
                "← %s %s [%dms] | Status: %d | Size: %d bytes",
                method, endpoint, int(elapsed * 1000),
                response.status_code, len(response.content),
            )

            if response.status_code >= 400:
                logger.warning(
                    "API Error Response: %s",
                    response.text[:500]
                )

            return response

        except requests.exceptions.ConnectionError as e:
            logger.error("Connection error to %s: %s", url, e)
            raise
        except requests.exceptions.Timeout as e:
            logger.error("Timeout after %ds for %s: %s", self.timeout, url, e)
            raise
        except requests.exceptions.RequestException as e:
            logger.error("Request failed for %s: %s", url, e)
            raise

    # ─────────────────────────────────────────────────────────
    # Assertion Helpers
    # ─────────────────────────────────────────────────────────

    def assert_status(self, response: Response, expected: int) -> None:
        """
        Assert response status code matches expected.

        Args:
            response: Response object
            expected: Expected HTTP status code
        """
        actual = response.status_code
        assert actual == expected, (
            f"Expected status {expected}, got {actual}.\n"
            f"URL: {response.url}\n"
            f"Body: {response.text[:500]}"
        )
        logger.debug("✓ Status code: %d", actual)

    def assert_response_time(self, max_ms: int = 2000) -> None:
        """
        Assert last API call responded within time limit.

        Args:
            max_ms: Maximum acceptable response time in milliseconds
        """
        if not self._response_times:
            return
        last_ms = int(self._response_times[-1] * 1000)
        assert last_ms <= max_ms, (
            f"Response too slow: {last_ms}ms (max: {max_ms}ms)"
        )
        logger.debug("✓ Response time: %dms (max: %dms)", last_ms, max_ms)

    def validate_schema(self, response: Response, schema: dict) -> None:
        """
        Validate response JSON against a JSON Schema.

        Args:
            response: API response
            schema: JSON Schema dict (draft-07 compatible)

        Raises:
            jsonschema.ValidationError: If response doesn't match schema
            AssertionError: If response body is not valid JSON
        """
        try:
            body = response.json()
        except ValueError as e:
            raise AssertionError(f"Response is not valid JSON: {e}\nBody: {response.text[:200]}")

        try:
            jsonschema.validate(instance=body, schema=schema)
            logger.debug("✓ JSON schema validation passed")
        except jsonschema.ValidationError as e:
            logger.error("Schema validation failed: %s", e.message)
            raise

    def get_response_json(self, response: Response) -> Any:
        """
        Safely parse response JSON.

        Returns:
            Any: Parsed JSON body

        Raises:
            AssertionError: If body is not valid JSON
        """
        try:
            return response.json()
        except ValueError as e:
            raise AssertionError(
                f"Failed to parse response as JSON: {e}\n"
                f"Status: {response.status_code}\n"
                f"Body: {response.text[:300]}"
            )

    @property
    def avg_response_time_ms(self) -> float:
        """Average response time of all requests in milliseconds."""
        if not self._response_times:
            return 0.0
        return sum(self._response_times) / len(self._response_times) * 1000

    def reset_session(self) -> None:
        """Create a fresh session (clears all cookies, tokens, headers)."""
        self._session.close()
        self._session = self._create_session()
        self._token = None
        logger.info("API session reset")

    def close(self) -> None:
        """Close the HTTP session."""
        self._session.close()
        logger.debug("API client session closed")
