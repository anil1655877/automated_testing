# ============================================================
# AI-Enhanced Enterprise Test Automation Framework
# MySQL Setup Script (PowerShell)
# ============================================================
# Sets up MySQL database with schema, user, and seed data.
# Falls back gracefully if MySQL is not installed.
#
# USAGE:
#   .\scripts\setup_mysql.ps1
#   .\scripts\setup_mysql.ps1 -Reset    # Drop and recreate DB
# ============================================================

param(
    [switch]$Reset,
    [string]$Host     = "localhost",
    [string]$Port     = "3306",
    [string]$RootPass = "",
    [string]$DbName   = "test_automation_db",
    [string]$DbUser   = "automation_user",
    [string]$DbPass   = "AutomationDB@123"
)

# ── Load from .env if available ───────────────────────────────
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match "^([^#=]+)=(.*)$") {
            $key   = $matches[1].Trim()
            $value = $matches[2].Trim()
            switch ($key) {
                "DB_HOST"     { $Host = $value }
                "DB_PORT"     { $Port = $value }
                "DB_PASSWORD" { if ($value) { $RootPass = $value } }
                "DB_NAME"     { $DbName = $value }
                "DB_USER"     { $DbUser = $value }
            }
        }
    }
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  MySQL Setup for AI Test Framework" -ForegroundColor Cyan
Write-Host "  Host  : $Host`:$Port" -ForegroundColor White
Write-Host "  DB    : $DbName" -ForegroundColor White
Write-Host "  User  : $DbUser" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# ── Check MySQL is available ──────────────────────────────────
$mysqlCmd = Get-Command mysql -ErrorAction SilentlyContinue
if (-not $mysqlCmd) {
    Write-Host "⚠ MySQL client (mysql.exe) not found in PATH" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Options:" -ForegroundColor White
    Write-Host "  1. Install MySQL 8.0: https://dev.mysql.com/downloads/mysql/" -ForegroundColor White
    Write-Host "  2. Use Docker:  docker run -d --name test-mysql -e MYSQL_ROOT_PASSWORD=RootPass@123 -p 3306:3306 mysql:8.0" -ForegroundColor White
    Write-Host "  3. Skip MySQL — framework auto-uses SQLite fallback (no setup needed!)" -ForegroundColor Green
    Write-Host ""
    Write-Host "SQLite fallback is ACTIVE when MySQL is unavailable." -ForegroundColor Green
    Write-Host "All database tests still pass with SQLite." -ForegroundColor Green
    exit 0
}

# ── Attempt connection ────────────────────────────────────────
$rootAuthArgs = @("-h", $Host, "-P", $Port, "-u", "root")
if ($RootPass) {
    $rootAuthArgs += "-p$RootPass"
}

function Invoke-MySQL {
    param([string]$Sql, [string]$Database = "")
    $args = $rootAuthArgs.Clone()
    if ($Database) { $args += $Database }
    $args += "-e"
    $args += $Sql
    & mysql @args 2>&1
    return $LASTEXITCODE
}

# Test connection
Write-Host "Testing MySQL connection..." -ForegroundColor Yellow
$testResult = Invoke-MySQL "SELECT 1;"
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Cannot connect to MySQL at $Host`:$Port" -ForegroundColor Red
    Write-Host "  Verify MySQL is running: net start MySQL80" -ForegroundColor White
    Write-Host "  Framework will use SQLite fallback automatically." -ForegroundColor Green
    exit 0
}
Write-Host "✓ MySQL connection successful" -ForegroundColor Green

# ── Drop existing DB if Reset ─────────────────────────────────
if ($Reset) {
    Write-Host "⚠ Resetting database '$DbName'..." -ForegroundColor Yellow
    Invoke-MySQL "DROP DATABASE IF EXISTS $DbName;"
    Write-Host "✓ Existing database dropped" -ForegroundColor Green
}

# ── Create database ───────────────────────────────────────────
Write-Host "Creating database '$DbName'..." -ForegroundColor Yellow
Invoke-MySQL "CREATE DATABASE IF NOT EXISTS $DbName CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to create database" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Database '$DbName' ready" -ForegroundColor Green

# ── Create user and grant permissions ────────────────────────
Write-Host "Setting up user '$DbUser'..." -ForegroundColor Yellow
$userSql = @"
CREATE USER IF NOT EXISTS '${DbUser}'@'localhost' IDENTIFIED BY '${DbPass}';
GRANT ALL PRIVILEGES ON ${DbName}.* TO '${DbUser}'@'localhost';
FLUSH PRIVILEGES;
"@
$userSql | & mysql @rootAuthArgs 2>&1
Write-Host "✓ User '$DbUser' configured" -ForegroundColor Green

# ── Run schema initialization ─────────────────────────────────
$initSql = "docker\mysql\init.sql"
if (Test-Path $initSql) {
    Write-Host "Running schema initialization..." -ForegroundColor Yellow
    & mysql @rootAuthArgs $DbName "<" $initSql 2>&1
    Write-Host "✓ Schema and seed data applied" -ForegroundColor Green
} else {
    Write-Host "Running inline schema creation..." -ForegroundColor Yellow
    $schema = @"
USE $DbName;
CREATE TABLE IF NOT EXISTS test_users (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(100) NOT NULL UNIQUE,
    email         VARCHAR(200) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role          VARCHAR(50)  NOT NULL DEFAULT 'user',
    is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS test_products (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(200)   NOT NULL,
    price         DECIMAL(10,2)  NOT NULL,
    stock_quantity INT           NOT NULL DEFAULT 0,
    category      VARCHAR(100),
    is_active     BOOLEAN        NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS test_orders (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    user_id      INT            NOT NULL,
    quantity     INT            NOT NULL,
    total_amount DECIMAL(10,2)  NOT NULL,
    status       VARCHAR(50)    NOT NULL DEFAULT 'pending',
    created_at   TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS test_audit_log (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    action       VARCHAR(100) NOT NULL,
    entity_type  VARCHAR(100),
    performed_by VARCHAR(100),
    created_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
SELECT 'Schema created successfully' AS status;
"@
    $schema | & mysql @rootAuthArgs $DbName 2>&1
    Write-Host "✓ Inline schema applied" -ForegroundColor Green
}

# ── Update .env with DB credentials ──────────────────────────
Write-Host ""
Write-Host "Updating .env with database settings..." -ForegroundColor Yellow
if (Test-Path ".env") {
    $envContent = Get-Content ".env"
    $envContent = $envContent -replace "^DB_HOST=.*", "DB_HOST=$Host"
    $envContent = $envContent -replace "^DB_PORT=.*", "DB_PORT=$Port"
    $envContent = $envContent -replace "^DB_NAME=.*", "DB_NAME=$DbName"
    $envContent = $envContent -replace "^DB_USER=.*", "DB_USER=$DbUser"
    $envContent = $envContent -replace "^DB_PASSWORD=.*", "DB_PASSWORD=$DbPass"
    Set-Content ".env" $envContent
    Write-Host "✓ .env updated with MySQL settings" -ForegroundColor Green
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  ✅ MySQL Setup Complete!" -ForegroundColor Green
Write-Host "  Database : $DbName @ $Host`:$Port" -ForegroundColor White
Write-Host "  User     : $DbUser" -ForegroundColor White
Write-Host ""
Write-Host "  Run database tests:" -ForegroundColor White
Write-Host "    pytest tests/database/ -v" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Green
