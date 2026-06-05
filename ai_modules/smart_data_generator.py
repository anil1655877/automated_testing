"""
============================================================
AI-Enhanced Enterprise Test Automation Framework
AI Module: Smart Test Data Generator
============================================================
Generates realistic, boundary-aware test data.
Uses Faker + custom rules — 100% OFFLINE, no API needed.
============================================================
"""
from __future__ import annotations
import random
import string
import uuid
from datetime import datetime, timedelta
from typing import Any
from faker import Faker
from config.config import AI_ENABLED
from utilities.logger import get_logger

logger = get_logger(__name__)
fake = Faker()
Faker.seed(42)  # Reproducible data for consistent test runs


class SmartDataGenerator:
    """
    AI-enhanced test data generator.

    GENERATES:
        - Valid user data (realistic names, emails, passwords)
        - Boundary value data (min/max length strings)
        - Invalid data (empty, special chars, SQL injection)
        - API payloads matching schemas
        - Database seed data

    NO EXTERNAL API REQUIRED — uses Faker + rules engine.

    USAGE:
        gen = SmartDataGenerator()
        user = gen.valid_user()
        print(user["email"])  # john.doe.12345@example.com

        bad = gen.invalid_user("empty_email")
        assert bad["email"] == ""
    """

    # ─── Valid Data Generators ────────────────────────────────

    def valid_user(self, role: str = "user") -> dict:
        """Generate a complete, valid user record."""
        first = fake.first_name()
        last = fake.last_name()
        uid = random.randint(10000, 99999)
        return {
            "first_name": first,
            "last_name": last,
            "username": f"{first.lower()}.{last.lower()}.{uid}",
            "email": f"{first.lower()}.{last.lower()}.{uid}@testmail.com",
            "password": self.strong_password(),
            "role": role,
            "phone": fake.phone_number(),
            "address": fake.address().replace("\n", ", "),
            "city": fake.city(),
            "country": fake.country_code(),
            "is_active": True,
            "created_at": datetime.now().isoformat(),
        }

    def valid_product(self) -> dict:
        """Generate a valid product/book record."""
        return {
            "name": fake.catch_phrase(),
            "description": fake.paragraph(nb_sentences=3),
            "price": round(random.uniform(9.99, 99.99), 2),
            "stock_quantity": random.randint(10, 500),
            "category": random.choice(["Technology", "Fiction", "Science", "Business"]),
            "isbn": self.valid_isbn(),
            "author": fake.name(),
            "publisher": fake.company(),
            "publish_date": fake.date_between(start_date="-5y", end_date="today").isoformat(),
        }

    def valid_order(self, user_id: int = 1, product_id: int = 1) -> dict:
        """Generate a valid order record."""
        quantity = random.randint(1, 10)
        unit_price = round(random.uniform(9.99, 49.99), 2)
        return {
            "user_id": user_id,
            "product_id": product_id,
            "quantity": quantity,
            "total_amount": round(quantity * unit_price, 2),
            "status": random.choice(["pending", "confirmed", "shipped", "delivered"]),
            "created_at": datetime.now().isoformat(),
        }

    def valid_api_payload(self, endpoint_type: str = "user") -> dict:
        """
        Generate API request payload for common endpoint types.

        Args:
            endpoint_type: 'user', 'login', 'product', 'order'
        """
        generators = {
            "user": self.valid_user,
            "login": self._login_payload,
            "product": self.valid_product,
            "order": self.valid_order,
        }
        gen_fn = generators.get(endpoint_type, self.valid_user)
        return gen_fn()

    # ─── Invalid Data Generators ─────────────────────────────

    def invalid_user(self, scenario: str) -> dict:
        """
        Generate invalid user data for negative testing.

        Args:
            scenario: Failure scenario name

        SCENARIOS:
            'empty_email'       → email = ""
            'invalid_email'     → email = "notanemail"
            'short_password'    → password = "abc"
            'sql_injection'     → username = "admin' OR '1'='1"
            'xss_attack'        → username = "<script>alert(1)</script>"
            'max_length'        → all fields at max character limit
            'whitespace_only'   → all fields = "   "
        """
        base = self.valid_user()
        scenarios = {
            "empty_email": {**base, "email": ""},
            "invalid_email": {**base, "email": "notanemail@"},
            "no_at_email": {**base, "email": "noemail.com"},
            "short_password": {**base, "password": "abc"},
            "no_uppercase_password": {**base, "password": "alllowercase1!"},
            "no_special_char_password": {**base, "password": "NoSpecial123"},
            "empty_username": {**base, "username": ""},
            "sql_injection": {**base, "username": "admin' OR '1'='1", "email": "hack@test.com"},
            "xss_attack": {**base, "username": "<script>alert('XSS')</script>"},
            "max_length": {**base,
                          "username": "u" * 256,
                          "email": "e" * 250 + "@test.com",
                          "first_name": "F" * 256},
            "whitespace_only": {**base,
                               "username": "   ",
                               "email": "   ",
                               "first_name": "   "},
            "special_chars": {**base, "username": "user!@#$%^&*()"},
            "unicode": {**base, "first_name": "Ünïcödé Nämé", "email": "unicode@tëst.com"},
            "null_values": {"username": None, "email": None, "password": None,
                           "first_name": None, "last_name": None},
        }
        return scenarios.get(scenario, base)

    def boundary_values(self, field_type: str) -> list[Any]:
        """
        Generate boundary value analysis (BVA) test data.

        BOUNDARY VALUE ANALYSIS:
            Tests at the minimum, maximum, just below min, just above max.
            Example for a field with min=1, max=100:
                Values: 0, 1, 2, 99, 100, 101

        Args:
            field_type: 'username', 'password', 'price', 'quantity', 'age'
        """
        boundaries = {
            "username": ["", "a", "ab", "a" * 50, "a" * 100, "a" * 101, "a" * 255],
            "password": ["", "a", "Ab1!", "Ab1!" * 5, "Ab1!" * 16],
            "email": ["", "a@b.c", "a" * 64 + "@" + "b" * 63 + ".com"],
            "price": [0.0, 0.01, 0.99, 1.0, 999.99, 1000.0, 9999.99, -0.01, -1.0],
            "quantity": [0, 1, 2, 99, 100, 101, 999, 1000, -1],
            "age": [0, 1, 17, 18, 65, 120, 121, -1],
            "phone": ["", "1", "12345", "123456789012345", "1" * 20],
        }
        return boundaries.get(field_type, [])

    # ─── Password Generator ───────────────────────────────────

    def strong_password(self) -> str:
        """
        Generate a strong password meeting common complexity rules:
        - Min 8 characters
        - At least 1 uppercase
        - At least 1 lowercase
        - At least 1 digit
        - At least 1 special character
        """
        upper = random.choice(string.ascii_uppercase)
        lower = "".join(random.choices(string.ascii_lowercase, k=4))
        digit = "".join(random.choices(string.digits, k=2))
        special = random.choice("!@#$%^&*")
        password = upper + lower + digit + special
        return "".join(random.sample(password, len(password)))

    def weak_password(self) -> str:
        """Generate a password that fails complexity checks."""
        return random.choice(["password", "123456", "abc", "test", "qwerty"])

    # ─── Special Data Types ───────────────────────────────────

    def valid_isbn(self) -> str:
        """Generate a valid-format ISBN-13."""
        digits = [random.randint(0, 9) for _ in range(12)]
        check = (10 - sum((3 if i % 2 else 1) * d for i, d in enumerate(digits))) % 10
        return "978" + "".join(str(d) for d in digits[:9]) + str(check)

    def unique_email(self) -> str:
        """Generate a guaranteed unique email using UUID."""
        uid = str(uuid.uuid4())[:8]
        return f"autotest_{uid}@testmail.com"

    def unique_username(self, prefix: str = "user") -> str:
        """Generate a unique username."""
        uid = str(uuid.uuid4())[:8]
        return f"{prefix}_{uid}"

    def sql_injection_payloads(self) -> list[str]:
        """Common SQL injection test strings."""
        return [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "' UNION SELECT 1,2,3 --",
            "admin'--",
            "1; SELECT * FROM users",
        ]

    def xss_payloads(self) -> list[str]:
        """Common XSS test strings."""
        return [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert(1)>",
            "javascript:alert(1)",
            "<svg onload=alert(1)>",
        ]

    def _login_payload(self) -> dict:
        """Generate login API payload."""
        return {"userName": self.unique_username(), "password": self.strong_password()}

    # ─── Bulk Data Generation ──────────────────────────────────

    def generate_users(self, count: int = 10, role: str = "user") -> list[dict]:
        """Generate multiple user records."""
        return [self.valid_user(role) for _ in range(count)]

    def generate_products(self, count: int = 10) -> list[dict]:
        """Generate multiple product records."""
        return [self.valid_product() for _ in range(count)]
