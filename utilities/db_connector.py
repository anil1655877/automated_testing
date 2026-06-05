"""
============================================================
AI-Enhanced Enterprise Test Automation Framework
Database Connector Utility
============================================================
Provides a unified interface for MySQL and SQLite with
automatic fallback, connection pooling, CRUD helpers,
and schema validation capabilities.
============================================================
"""
from __future__ import annotations
import sqlite3
from contextlib import contextmanager
from typing import Any, Optional, Generator
from pathlib import Path

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from config.config import db_config, SQLITE_DB_PATH
from utilities.logger import get_logger

logger = get_logger(__name__)


class DBConnector:
    """
    Unified database connector supporting MySQL and SQLite.

    DESIGN PATTERN: Context Manager + Singleton per engine
        - Manages connection lifecycle automatically
        - Falls back to SQLite when MySQL is unavailable
        - Thread-safe connection pooling via SQLAlchemy

    USAGE:
        db = DBConnector()

        # Execute a query
        results = db.fetch_all("SELECT * FROM users WHERE active=1")

        # Context manager (auto-commit/rollback)
        with db.session() as session:
            session.execute(text("INSERT INTO logs VALUES (:msg)"), {"msg": "test"})

        # Check data exists
        assert db.record_exists("users", "email", "test@example.com")
    """

    def __init__(self, use_sqlite: bool = False):
        """
        Initialize database connector.

        Args:
            use_sqlite: Force SQLite usage (skips MySQL connection attempt)
        """
        self._engine = None
        self._Session = None
        self._db_type = "sqlite" if use_sqlite else "mysql"

        if not use_sqlite:
            self._try_mysql_connect()
        else:
            self._connect_sqlite()

    def _try_mysql_connect(self) -> None:
        """Attempt MySQL connection; fall back to SQLite on failure."""
        try:
            conn_str = db_config.connection_string
            self._engine = create_engine(
                conn_str,
                poolclass=QueuePool,
                pool_size=db_config.pool_size,
                max_overflow=db_config.max_overflow,
                pool_pre_ping=True,     # Validate connections before use
                pool_recycle=3600,      # Recycle connections every hour
                echo=False,             # Set True for SQL query logging
            )
            # Test connection
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            self._Session = sessionmaker(bind=self._engine)
            self._db_type = "mysql"
            logger.info("✓ Connected to MySQL: %s:%s/%s",
                        db_config.host, db_config.port, db_config.name)
        except Exception as e:
            logger.warning("MySQL connection failed (%s) — falling back to SQLite", e)
            self._connect_sqlite()

    def _connect_sqlite(self) -> None:
        """Connect to SQLite (fallback or explicit)."""
        SQLITE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn_str = db_config.sqlite_connection_string
        self._engine = create_engine(
            conn_str,
            connect_args={"check_same_thread": False},  # Allow multi-threading
            echo=False,
        )
        self._Session = sessionmaker(bind=self._engine)
        self._db_type = "sqlite"
        logger.info("✓ Connected to SQLite: %s", SQLITE_DB_PATH)

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """
        Context manager for database sessions with auto commit/rollback.

        USAGE:
            with db.session() as sess:
                sess.execute(text("INSERT INTO ..."))
            # Auto-committed on exit, rolled back on exception
        """
        sess = self._Session()
        try:
            yield sess
            sess.commit()
            logger.debug("DB transaction committed")
        except SQLAlchemyError as e:
            sess.rollback()
            logger.error("DB transaction rolled back: %s", e)
            raise
        finally:
            sess.close()

    def execute_query(self, query: str, params: Optional[dict] = None) -> Any:
        """
        Execute a DML query (INSERT, UPDATE, DELETE).

        Args:
            query: SQL query string (use :param for parameters)
            params: Dictionary of query parameters

        Returns:
            ResultProxy: SQLAlchemy result object

        Example:
            db.execute_query(
                "UPDATE users SET status=:status WHERE id=:id",
                {"status": "active", "id": 42}
            )
        """
        with self._engine.connect() as conn:
            result = conn.execute(text(query), params or {})
            conn.commit()
            logger.debug("Query executed: %s | Params: %s", query[:80], params)
            return result

    def fetch_all(self, query: str, params: Optional[dict] = None) -> list[dict]:
        """
        Fetch all rows matching a SELECT query.

        Args:
            query: SQL SELECT query
            params: Query parameters

        Returns:
            list[dict]: List of rows as dictionaries

        Example:
            users = db.fetch_all("SELECT * FROM users WHERE role=:role", {"role": "admin"})
            print(users[0]["email"])
        """
        with self._engine.connect() as conn:
            result = conn.execute(text(query), params or {})
            rows = [dict(row._mapping) for row in result]
            logger.debug("fetch_all: %d rows returned", len(rows))
            return rows

    def fetch_one(self, query: str, params: Optional[dict] = None) -> Optional[dict]:
        """
        Fetch a single row matching a SELECT query.

        Args:
            query: SQL SELECT query (LIMIT 1 recommended)
            params: Query parameters

        Returns:
            Optional[dict]: Single row as dict, or None if not found
        """
        with self._engine.connect() as conn:
            result = conn.execute(text(query), params or {})
            row = result.fetchone()
            return dict(row._mapping) if row else None

    def record_exists(self, table: str, column: str, value: Any) -> bool:
        """
        Check if a record exists in a table.

        Args:
            table: Table name
            column: Column to filter on
            value: Expected value

        Returns:
            bool: True if at least one matching record exists

        Example:
            assert db.record_exists("users", "email", "john@example.com")
        """
        query = f"SELECT 1 FROM {table} WHERE {column} = :value LIMIT 1"
        result = self.fetch_one(query, {"value": value})
        exists = result is not None
        logger.debug("record_exists('%s', '%s', '%s'): %s", table, column, value, exists)
        return exists

    def get_row_count(self, table: str, condition: str = "", params: Optional[dict] = None) -> int:
        """
        Get count of rows in a table, optionally filtered.

        Args:
            table: Table name
            condition: WHERE clause (without the WHERE keyword)
            params: Query parameters

        Returns:
            int: Row count

        Example:
            count = db.get_row_count("orders", "status=:s AND user_id=:u",
                                     {"s": "pending", "u": 5})
        """
        where = f"WHERE {condition}" if condition else ""
        query = f"SELECT COUNT(*) as cnt FROM {table} {where}"
        result = self.fetch_one(query, params)
        count = result["cnt"] if result else 0
        logger.debug("Row count in '%s' (cond=%s): %d", table, condition, count)
        return count

    def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists in the database.

        Args:
            table_name: Name of the table to check

        Returns:
            bool: True if table exists
        """
        inspector = inspect(self._engine)
        exists = table_name in inspector.get_table_names()
        logger.debug("Table '%s' exists: %s", table_name, exists)
        return exists

    def get_column_names(self, table_name: str) -> list[str]:
        """
        Get list of column names for a table.

        Args:
            table_name: Table name

        Returns:
            list[str]: Column name list
        """
        inspector = inspect(self._engine)
        columns = inspector.get_columns(table_name)
        return [col["name"] for col in columns]

    def setup_test_schema(self) -> None:
        """
        Create standard test tables for framework testing.
        Creates tables if they don't already exist.
        """
        is_mysql = self._db_type == "mysql"
        auto_inc = "AUTO_INCREMENT" if is_mysql else "AUTOINCREMENT"
        id_type = "INT" if is_mysql else "INTEGER"

        ddl_statements = [
            f"""
            CREATE TABLE IF NOT EXISTS test_users (
                id {id_type} PRIMARY KEY {auto_inc},
                username VARCHAR(100) NOT NULL UNIQUE,
                email VARCHAR(200) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(50) DEFAULT 'user',
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            f"""
            CREATE TABLE IF NOT EXISTS test_products (
                id {id_type} PRIMARY KEY {auto_inc},
                name VARCHAR(200) NOT NULL,
                description TEXT,
                price DECIMAL(10, 2) NOT NULL,
                stock_quantity INTEGER DEFAULT 0,
                category VARCHAR(100),
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            f"""
            CREATE TABLE IF NOT EXISTS test_orders (
                id {id_type} PRIMARY KEY {auto_inc},
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                total_amount DECIMAL(10, 2) NOT NULL,
                status VARCHAR(50) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            f"""
            CREATE TABLE IF NOT EXISTS test_audit_log (
                id {id_type} PRIMARY KEY {auto_inc},
                action VARCHAR(100) NOT NULL,
                entity_type VARCHAR(100),
                entity_id INTEGER,
                performed_by VARCHAR(100),
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
        ]
        with self._engine.connect() as conn:
            for ddl in ddl_statements:
                conn.execute(text(ddl))
            conn.commit()
        logger.info("✓ Test schema created/verified")

    def teardown_test_data(self, tables: list[str]) -> None:
        """
        Clean up test data from specified tables.
        Used in test teardown to restore clean state.

        Args:
            tables: List of table names to truncate
        """
        with self._engine.connect() as conn:
            for table in tables:
                if self._db_type == "mysql":
                    conn.execute(text(f"TRUNCATE TABLE {table}"))
                else:
                    conn.execute(text(f"DELETE FROM {table}"))
                logger.debug("Cleared table: %s", table)
            conn.commit()
        logger.info("✓ Test data cleaned from: %s", tables)

    @property
    def db_type(self) -> str:
        """Returns current database type ('mysql' or 'sqlite')."""
        return self._db_type

    def close(self) -> None:
        """Dispose engine and close all connections."""
        if self._engine:
            self._engine.dispose()
            logger.info("Database connections closed")


# ── Module-level singleton ────────────────────────────────────
_db_instance: Optional[DBConnector] = None


def get_db_connector(use_sqlite: bool = False) -> DBConnector:
    """
    Get (or create) the singleton DBConnector instance.

    Args:
        use_sqlite: Force SQLite (useful for local dev without MySQL)

    Returns:
        DBConnector: Shared connector instance
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = DBConnector(use_sqlite=use_sqlite)
    return _db_instance
