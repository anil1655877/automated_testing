"""
============================================================
AI-Enhanced Enterprise Test Automation Framework
Database Tests: CRUD Validation
============================================================
Tests MySQL/SQLite CRUD operations, data integrity,
and consistency using the framework's DBConnector.
============================================================
"""
import pytest
import allure
from datetime import datetime
from utilities.db_connector import DBConnector
from utilities.logger import get_logger

logger = get_logger(__name__)


@allure.feature("Database")
@allure.story("CRUD Validation")
class TestDatabaseCRUD:
    """Database CRUD test suite using MySQL (or SQLite fallback)."""

    @allure.title("Database Connection is Established")
    @pytest.mark.smoke
    @pytest.mark.database
    def test_database_connection(self, db: DBConnector):
        """TC-DB-001: Verify database connection is active."""
        with allure.step("Check database type"):
            db_type = db.db_type
            logger.info("Connected to: %s", db_type)
            assert db_type in ("mysql", "sqlite"), \
                f"Invalid DB type: {db_type}"

    @allure.title("INSERT User Record")
    @pytest.mark.regression
    @pytest.mark.database
    @pytest.mark.crud
    def test_insert_user(self, clean_db: DBConnector):
        """TC-DB-002: INSERT a user record into test_users table."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        username = f"testuser_{timestamp}"
        email = f"{username}@test.com"

        with allure.step(f"Insert user: {username}"):
            clean_db.execute_query(
                """INSERT INTO test_users (username, email, password_hash, role)
                   VALUES (:u, :e, :p, :r)""",
                {"u": username, "e": email, "p": "hashed_pw_xyz", "r": "user"},
            )

        with allure.step("Verify user was inserted"):
            assert clean_db.record_exists("test_users", "email", email), \
                f"Inserted user '{email}' not found in database"
            logger.info("✓ User inserted: %s", email)

    @allure.title("SELECT User by Username")
    @pytest.mark.regression
    @pytest.mark.database
    @pytest.mark.crud
    def test_select_user(self, clean_db: DBConnector):
        """TC-DB-003: SELECT a user record by username."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        username = f"selecttest_{timestamp}"
        email = f"{username}@test.com"

        with allure.step("Insert user for SELECT test"):
            clean_db.execute_query(
                """INSERT INTO test_users (username, email, password_hash)
                   VALUES (:u, :e, :p)""",
                {"u": username, "e": email, "p": "hash_abc"},
            )

        with allure.step("SELECT user by username"):
            user = clean_db.fetch_one(
                "SELECT * FROM test_users WHERE username = :u",
                {"u": username},
            )

        with allure.step("Verify fetched record"):
            assert user is not None, f"User '{username}' should exist"
            assert user["email"] == email, \
                f"Email mismatch: expected {email}, got {user['email']}"
            assert user["role"] == "user", \
                f"Default role should be 'user', got {user['role']}"
            logger.info("✓ User fetched: %s", user)

    @allure.title("UPDATE User Role")
    @pytest.mark.regression
    @pytest.mark.database
    @pytest.mark.crud
    def test_update_user_role(self, clean_db: DBConnector):
        """TC-DB-004: UPDATE a user's role from 'user' to 'admin'."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        username = f"roletest_{timestamp}"
        email = f"{username}@test.com"

        with allure.step("Create test user"):
            clean_db.execute_query(
                """INSERT INTO test_users (username, email, password_hash, role)
                   VALUES (:u, :e, :p, :r)""",
                {"u": username, "e": email, "p": "hash_xyz", "r": "user"},
            )

        with allure.step("Update role to 'admin'"):
            clean_db.execute_query(
                "UPDATE test_users SET role = :r WHERE username = :u",
                {"r": "admin", "u": username},
            )

        with allure.step("Verify role was updated"):
            user = clean_db.fetch_one(
                "SELECT role FROM test_users WHERE username = :u",
                {"u": username},
            )
            assert user["role"] == "admin", \
                f"Role should be 'admin', got '{user['role']}'"
            logger.info("✓ Role updated to admin for: %s", username)

    @allure.title("DELETE User Record")
    @pytest.mark.regression
    @pytest.mark.database
    @pytest.mark.crud
    def test_delete_user(self, clean_db: DBConnector):
        """TC-DB-005: DELETE a user record and verify removal."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        username = f"deltest_{timestamp}"
        email = f"{username}@test.com"

        with allure.step("Insert user to delete"):
            clean_db.execute_query(
                """INSERT INTO test_users (username, email, password_hash)
                   VALUES (:u, :e, :p)""",
                {"u": username, "e": email, "p": "hash_del"},
            )
            assert clean_db.record_exists("test_users", "username", username)

        with allure.step("Delete the user"):
            clean_db.execute_query(
                "DELETE FROM test_users WHERE username = :u",
                {"u": username},
            )

        with allure.step("Verify user was deleted"):
            assert not clean_db.record_exists("test_users", "username", username), \
                f"User '{username}' should have been deleted"
            logger.info("✓ User deleted: %s", username)

    @allure.title("Row Count Query")
    @pytest.mark.regression
    @pytest.mark.database
    def test_row_count(self, clean_db: DBConnector):
        """TC-DB-006: Verify row count after multiple INSERTs."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        for i in range(3):
            clean_db.execute_query(
                """INSERT INTO test_users (username, email, password_hash)
                   VALUES (:u, :e, :p)""",
                {"u": f"counttest_{timestamp}_{i}", "e": f"count{i}_{timestamp}@test.com",
                 "p": "hash"},
            )
        count = clean_db.get_row_count(
            "test_users", "username LIKE :pattern",
            {"pattern": f"counttest_{timestamp}%"}
        )
        assert count == 3, f"Expected 3 rows, got {count}"

    @allure.title("Table Schema Validation")
    @pytest.mark.regression
    @pytest.mark.database
    def test_table_schema_validation(self, db: DBConnector):
        """TC-DB-007: Verify test_users table has expected columns."""
        with allure.step("Get columns of test_users table"):
            columns = db.get_column_names("test_users")
            logger.info("Columns: %s", columns)

        with allure.step("Verify required columns exist"):
            required = ["id", "username", "email", "password_hash", "role", "is_active"]
            for col in required:
                assert col in columns, \
                    f"Required column '{col}' missing from test_users table"

    @allure.title("Duplicate Email Constraint")
    @pytest.mark.regression
    @pytest.mark.database
    @pytest.mark.negative
    def test_duplicate_email_rejected(self, clean_db: DBConnector):
        """TC-DB-008: Duplicate email should violate UNIQUE constraint."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        email = f"unique_{timestamp}@test.com"

        with allure.step("Insert first user"):
            clean_db.execute_query(
                """INSERT INTO test_users (username, email, password_hash)
                   VALUES (:u, :e, :p)""",
                {"u": f"unique1_{timestamp}", "e": email, "p": "hash1"},
            )

        with allure.step("Attempt duplicate email insert"):
            with pytest.raises(Exception) as exc_info:
                clean_db.execute_query(
                    """INSERT INTO test_users (username, email, password_hash)
                       VALUES (:u, :e, :p)""",
                    {"u": f"unique2_{timestamp}", "e": email, "p": "hash2"},
                )
            logger.info("✓ Duplicate email correctly rejected: %s", exc_info.type.__name__)
