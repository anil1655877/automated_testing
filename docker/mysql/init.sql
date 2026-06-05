/*
============================================================
AI-Enhanced Enterprise Test Automation Framework
MySQL Initialization Script
Runs automatically when MySQL container starts for the first time
============================================================
*/

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS test_automation_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE test_automation_db;

-- ── Users table ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS test_users (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(100) NOT NULL UNIQUE,
    email         VARCHAR(200) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role          VARCHAR(50)  NOT NULL DEFAULT 'user',
    is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_role  (role)
);

-- ── Products table ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS test_products (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(200)   NOT NULL,
    description   TEXT,
    price         DECIMAL(10, 2) NOT NULL,
    stock_quantity INT           NOT NULL DEFAULT 0,
    category      VARCHAR(100),
    is_active     BOOLEAN        NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ── Orders table ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS test_orders (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    user_id      INT            NOT NULL,
    product_id   INT            NOT NULL,
    quantity     INT            NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    status       VARCHAR(50)    NOT NULL DEFAULT 'pending',
    created_at   TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id    (user_id),
    INDEX idx_status     (status)
);

-- ── Audit log table ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS test_audit_log (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    action       VARCHAR(100) NOT NULL,
    entity_type  VARCHAR(100),
    entity_id    INT,
    performed_by VARCHAR(100),
    details      TEXT,
    created_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_action      (action),
    INDEX idx_entity_type (entity_type)
);

-- ── Seed data ─────────────────────────────────────────────────
INSERT IGNORE INTO test_users (username, email, password_hash, role)
VALUES
    ('admin_user', 'admin@testframework.com',  SHA2('Admin@123', 256),    'admin'),
    ('test_user',  'testuser@testframework.com', SHA2('TestUser@123', 256), 'user'),
    ('readonly',   'readonly@testframework.com', SHA2('ReadOnly@123', 256), 'viewer');

INSERT IGNORE INTO test_products (name, description, price, stock_quantity, category)
VALUES
    ('Selenium WebDriver Handbook', 'Complete guide to Selenium automation', 29.99, 100, 'Technology'),
    ('Python Testing Cookbook',     'Recipes for effective Python testing',  24.99, 150, 'Technology'),
    ('Clean Code',                  'Writing maintainable, readable code',   34.99,  75, 'Engineering');

SELECT 'Database initialization complete!' AS status;
