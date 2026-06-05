"""
============================================================
AI Module: Test Case Generator (Offline)
============================================================
Auto-generates test cases from page structure or API schema.
100% offline using templates + heuristics.
============================================================
"""
from __future__ import annotations
from typing import Optional
from config.config import AI_ENABLED
from utilities.logger import get_logger

logger = get_logger(__name__)


class TestCaseGenerator:
    """
    Generates test case outlines from page/API metadata.
    Offline — uses template-based generation.
    """

    TEMPLATES = {
        "login_form": [
            "TC-{id}-001: Valid login with correct credentials → expect dashboard",
            "TC-{id}-002: Invalid login with wrong password → expect error message",
            "TC-{id}-003: Empty username → expect validation error",
            "TC-{id}-004: Empty password → expect validation error",
            "TC-{id}-005: Both fields empty → expect form validation",
            "TC-{id}-006: SQL injection in username → expect rejection",
            "TC-{id}-007: XSS in username → expect sanitized output",
            "TC-{id}-008: Max length username (256 chars) → expect rejection",
            "TC-{id}-009: Whitespace-only credentials → expect rejection",
            "TC-{id}-010: Case sensitivity of username → verify behavior",
        ],
        "api_endpoint": [
            "TC-{id}-001: GET all resources → expect 200 + non-empty list",
            "TC-{id}-002: GET resource by valid ID → expect 200 + correct data",
            "TC-{id}-003: GET resource by invalid ID → expect 404",
            "TC-{id}-004: POST create valid resource → expect 201 + ID in response",
            "TC-{id}-005: POST with missing required field → expect 400",
            "TC-{id}-006: PUT update existing resource → expect 200 + updated data",
            "TC-{id}-007: DELETE resource → expect 200/204 + verify deleted",
            "TC-{id}-008: Unauthorized access (no token) → expect 401",
            "TC-{id}-009: Wrong method (GET on POST endpoint) → expect 405",
            "TC-{id}-010: Response schema validation → all fields present",
        ],
        "crud_db": [
            "TC-{id}-001: INSERT valid record → verify row exists",
            "TC-{id}-002: SELECT by primary key → verify correct data",
            "TC-{id}-003: UPDATE field value → verify change persisted",
            "TC-{id}-004: DELETE record → verify row removed",
            "TC-{id}-005: UNIQUE constraint violation → expect DB error",
            "TC-{id}-006: NOT NULL constraint → expect DB error on null insert",
            "TC-{id}-007: COUNT rows after bulk insert → verify count",
            "TC-{id}-008: Transaction rollback on error → verify data unchanged",
        ],
    }

    def generate(self, template: str, prefix: str = "AUTO") -> list[str]:
        """
        Generate test case list from a template.

        Args:
            template: Template name ('login_form', 'api_endpoint', 'crud_db')
            prefix: Test ID prefix

        Returns:
            list[str]: Generated test case descriptions
        """
        if not AI_ENABLED:
            logger.debug("AI disabled — returning empty test case list")
            return []

        from utilities.ai_client_wrapper import AIClientWrapper
        prompt = (
            f"Generate a list of 5-10 test case descriptions for the following template: '{template}' "
            f"using the ID prefix '{prefix}'. Respond with a valid JSON array of strings."
        )
        system_instruction = "You are a QA test engineer. Always respond with a valid JSON list of test case strings."

        try:
            ai_response = AIClientWrapper.generate_content(prompt, system_instruction=system_instruction)
            if ai_response:
                import re
                json_match = re.search(r"\[.*\]", ai_response, re.DOTALL)
                if json_match:
                    cases = json.loads(json_match.group(0))
                else:
                    cases = json.loads(ai_response)
                if isinstance(cases, list) and all(isinstance(c, str) for c in cases):
                    return cases
        except Exception as e:
            logger.debug("Failed to generate dynamic test cases (%s) - using template fallback", e)

        tmpl = self.TEMPLATES.get(template, [])
        return [tc.replace("{id}", prefix) for tc in tmpl]

    def generate_from_fields(self, fields: list[str], form_name: str = "FORM") -> list[str]:
        """
        Generate test cases from a list of form field names.

        Args:
            fields: List of field names (e.g., ['username', 'email', 'password'])
            form_name: Form name for test IDs
        """
        test_cases = []
        for i, field in enumerate(fields, 1):
            test_cases.extend([
                f"TC-{form_name}-{i:02d}a: {field} → empty value → expect validation error",
                f"TC-{form_name}-{i:02d}b: {field} → valid value → expect acceptance",
                f"TC-{form_name}-{i:02d}c: {field} → max length exceeded → expect rejection",
                f"TC-{form_name}-{i:02d}d: {field} → special characters → verify handling",
            ])
        return test_cases

    def print_test_cases(self, template: str, prefix: str = "AUTO") -> None:
        """Print generated test cases to console."""
        cases = self.generate(template, prefix)
        print(f"\n{'='*60}")
        print(f"  Generated Test Cases: {template} [{prefix}]")
        print(f"{'='*60}")
        for case in cases:
            print(f"  ✓ {case}")
        print(f"{'='*60}\n")
