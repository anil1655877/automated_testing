"""
============================================================
AI-Enhanced Enterprise Test Automation Framework
JSON Utilities
============================================================
Helpers for JSON schema validation, file loading, path
querying, and test data management from JSON files.
============================================================
"""
import json
from pathlib import Path
from typing import Any, Optional, Union
import jsonschema
from jsonpath_ng import parse as jsonpath_parse

from config.config import TEST_DATA_DIR, SCHEMAS_DIR
from utilities.logger import get_logger

logger = get_logger(__name__)


class JSONUtils:
    """
    Utility class for JSON operations in test automation.

    FEATURES:
        - Load test data from JSON files
        - Validate API responses against JSON schemas
        - Query nested JSON with JSONPath expressions
        - Deep comparison of JSON objects
        - Pretty-print JSON for logging
    """

    @staticmethod
    def load_json_file(filepath: Union[str, Path]) -> Any:
        """
        Load and parse a JSON file.

        Args:
            filepath: Path to JSON file

        Returns:
            Any: Parsed JSON content (dict, list, etc.)

        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If file contains invalid JSON
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"JSON file not found: {filepath}")
        
        import time
        retries = 5
        delay = 0.2
        last_err = None
        while retries > 0:
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                logger.debug("Loaded JSON from: %s", filepath)
                return data
            except PermissionError as e:
                last_err = e
                retries -= 1
                time.sleep(delay)
                delay *= 1.5
            except Exception as e:
                raise e
        raise last_err

    @staticmethod
    def load_test_data(filename: str) -> Any:
        """
        Load test data from the standard test_data directory.

        Args:
            filename: JSON filename (e.g., 'login_data.json')

        Returns:
            Any: Parsed test data
        """
        return JSONUtils.load_json_file(TEST_DATA_DIR / filename)

    @staticmethod
    def load_schema(filename: str) -> dict:
        """
        Load a JSON schema from the schemas directory.

        Args:
            filename: Schema filename (e.g., 'user_schema.json')

        Returns:
            dict: JSON schema
        """
        return JSONUtils.load_json_file(SCHEMAS_DIR / filename)

    @staticmethod
    def validate_schema(data: Any, schema: dict) -> tuple[bool, Optional[str]]:
        """
        Validate data against a JSON schema.

        Args:
            data: Data to validate
            schema: JSON Schema (draft-07)

        Returns:
            tuple[bool, Optional[str]]: (is_valid, error_message)

        USAGE:
            is_valid, error = JSONUtils.validate_schema(api_response, user_schema)
            assert is_valid, f"Schema validation failed: {error}"
        """
        try:
            jsonschema.validate(instance=data, schema=schema)
            logger.debug("✓ Schema validation passed")
            return True, None
        except jsonschema.ValidationError as e:
            error_msg = f"{e.message} at path: {' -> '.join(str(p) for p in e.path)}"
            logger.warning("Schema validation failed: %s", error_msg)
            return False, error_msg
        except jsonschema.SchemaError as e:
            error_msg = f"Invalid schema: {e.message}"
            logger.error(error_msg)
            return False, error_msg

    @staticmethod
    def query_jsonpath(data: Any, expression: str) -> list[Any]:
        """
        Query JSON data using JSONPath expression.

        Args:
            data: JSON data to query
            expression: JSONPath expression (e.g., "$.users[*].email")

        Returns:
            list: Matching values

        USAGE:
            emails = JSONUtils.query_jsonpath(response_json, "$.data[*].email")
            first_id = JSONUtils.query_jsonpath(response_json, "$.data[0].id")[0]
        """
        try:
            jsonpath_expr = jsonpath_parse(expression)
            matches = [match.value for match in jsonpath_expr.find(data)]
            logger.debug("JSONPath '%s' matched %d results", expression, len(matches))
            return matches
        except Exception as e:
            logger.error("JSONPath query failed: %s | Expression: %s", e, expression)
            return []

    @staticmethod
    def get_nested_value(data: dict, key_path: str, default: Any = None) -> Any:
        """
        Get value from nested dict using dot-notation key path.

        Args:
            data: Dictionary to search
            key_path: Dot-separated path (e.g., "user.address.city")
            default: Value to return if key not found

        Returns:
            Any: Value at key path, or default

        USAGE:
            city = JSONUtils.get_nested_value(user_data, "address.city", "Unknown")
        """
        keys = key_path.split(".")
        current = data
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key, default)
            else:
                return default
        return current

    @staticmethod
    def deep_compare(expected: Any, actual: Any, ignore_keys: Optional[list] = None) -> tuple[bool, list[str]]:
        """
        Deep comparison of two JSON-like structures with detailed diff reporting.

        Args:
            expected: Expected value
            actual: Actual value from API/DB
            ignore_keys: List of keys to skip in comparison

        Returns:
            tuple[bool, list[str]]: (matches, list_of_differences)

        USAGE:
            matches, diffs = JSONUtils.deep_compare(expected_user, actual_user, ignore_keys=["id", "created_at"])
            assert matches, f"JSON mismatch: {diffs}"
        """
        ignore_keys = ignore_keys or []
        differences = []

        def _compare(exp, act, path: str = ""):
            if isinstance(exp, dict) and isinstance(act, dict):
                all_keys = set(exp.keys()) | set(act.keys())
                for key in all_keys:
                    if key in ignore_keys:
                        continue
                    full_path = f"{path}.{key}" if path else key
                    if key not in exp:
                        differences.append(f"Extra key in actual: {full_path} = {act[key]!r}")
                    elif key not in act:
                        differences.append(f"Missing key in actual: {full_path}")
                    else:
                        _compare(exp[key], act[key], full_path)
            elif isinstance(exp, list) and isinstance(act, list):
                if len(exp) != len(act):
                    differences.append(f"Array length mismatch at {path}: expected {len(exp)}, got {len(act)}")
                for i, (e_item, a_item) in enumerate(zip(exp, act)):
                    _compare(e_item, a_item, f"{path}[{i}]")
            else:
                if exp != act:
                    differences.append(f"Value mismatch at {path}: expected {exp!r}, got {act!r}")

        _compare(expected, actual)
        return len(differences) == 0, differences

    @staticmethod
    def pretty_print(data: Any) -> str:
        """
        Return pretty-formatted JSON string for logging.

        Args:
            data: JSON-serializable data

        Returns:
            str: Indented JSON string
        """
        return json.dumps(data, indent=2, default=str, ensure_ascii=False)

    @staticmethod
    def save_json_file(data: Any, filepath: Union[str, Path]) -> None:
        """
        Save data to a JSON file.

        Args:
            data: JSON-serializable data
            filepath: Destination file path
        """
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        import time
        retries = 5
        delay = 0.2
        last_err = None
        while retries > 0:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, default=str, ensure_ascii=False)
                logger.debug("JSON saved to: %s", filepath)
                return
            except PermissionError as e:
                last_err = e
                retries -= 1
                time.sleep(delay)
                delay *= 1.5
            except Exception as e:
                raise e
        raise last_err
