# ============================================================
# AI-Enhanced Enterprise Test Automation Framework
# PowerShell Test Runner Script
# ============================================================
# USAGE:
#   .\scripts\run_tests.ps1 -Suite smoke
#   .\scripts\run_tests.ps1 -Suite regression -Browser firefox -Parallel 4
#   .\scripts\run_tests.ps1 -Suite api -Headless
#   .\scripts\run_tests.ps1 -Suite all -Parallel 2 -Headless
# ============================================================

param(
    [ValidateSet("smoke","regression","api","database","all","ui","security")]
    [string]$Suite = "smoke",

    [ValidateSet("chrome","firefox","edge")]
    [string]$Browser = "chrome",

    [switch]$Headless,

    [ValidateRange(1,8)]
    [int]$Parallel = 1,

    [switch]$GenerateReport,
    [switch]$OpenReport,
    [string]$Markers = ""
)

# ── Banner ────────────────────────────────────────────────────
function Write-Banner {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "  AI-Enhanced Enterprise Test Automation Framework" -ForegroundColor Cyan
    Write-Host "  Suite    : $Suite" -ForegroundColor White
    Write-Host "  Browser  : $Browser" -ForegroundColor White
    Write-Host "  Headless : $($Headless.IsPresent)" -ForegroundColor White
    Write-Host "  Parallel : $Parallel workers" -ForegroundColor White
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
}

# ── Prerequisite checks ───────────────────────────────────────
function Test-Prerequisites {
    # Python check
    try {
        $pyVersion = python --version 2>&1
        Write-Host "✓ $pyVersion" -ForegroundColor Green
    } catch {
        Write-Host "✗ Python not found. Install from python.org" -ForegroundColor Red
        exit 1
    }

    # pytest check
    try {
        $ptVersion = python -m pytest --version 2>&1
        Write-Host "✓ $ptVersion" -ForegroundColor Green
    } catch {
        Write-Host "✗ pytest not found. Run: pip install -r requirements.txt" -ForegroundColor Red
        exit 1
    }

    # .env check
    if (-not (Test-Path ".env")) {
        Write-Host "⚠ .env not found — using defaults" -ForegroundColor Yellow
        Copy-Item ".env.example" ".env" -ErrorAction SilentlyContinue
    } else {
        Write-Host "✓ .env configuration found" -ForegroundColor Green
    }
}

# ── Create required directories ───────────────────────────────
function Initialize-Directories {
    $dirs = @(
        "reports\html-reports",
        "reports\allure-results",
        "reports\screenshots\failures",
        "reports\screenshots\elements",
        "logs\test_logs"
    )
    foreach ($dir in $dirs) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
    }
    Write-Host "✓ Report directories ready" -ForegroundColor Green
}

# ── Build pytest command ──────────────────────────────────────
function Build-PytestCommand {
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $reportName = "reports\html-reports\${Suite}_${timestamp}.html"

    $cmd = "python -m pytest"

    # Test path by suite
    switch ($Suite) {
        "smoke"      { $cmd += " tests/ -m smoke" }
        "regression" { $cmd += " tests/ -m regression" }
        "ui"         { $cmd += " tests/ui/" }
        "api"        { $cmd += " tests/api/" }
        "database"   { $cmd += " tests/database/" }
        "security"   { $cmd += " tests/ -m security" }
        "all"        { $cmd += " tests/" }
    }

    # Custom markers override
    if ($Markers) {
        $cmd += " -m `"$Markers`""
    }

    # Parallel
    if ($Parallel -gt 1) {
        $cmd += " -n $Parallel"
    }

    # Options
    $cmd += " --tb=short"
    $cmd += " -v"
    $cmd += " --reruns=2"
    $cmd += " --reruns-delay=3"
    $cmd += " --html=`"$reportName`""
    $cmd += " --self-contained-html"
    $cmd += " --alluredir=reports\allure-results"

    # Browser env vars
    $env:BROWSER = $Browser
    $env:HEADLESS = $Headless.IsPresent.ToString().ToLower()
    $env:PYTHONPATH = (Get-Location).Path

    return $cmd
}

# ── Main execution ────────────────────────────────────────────
Write-Banner
Set-Location (Split-Path -Parent $PSScriptRoot)

Test-Prerequisites
Initialize-Directories

$pytestCmd = Build-PytestCommand
Write-Host ""
Write-Host "Running: $pytestCmd" -ForegroundColor Yellow
Write-Host ""

$startTime = Get-Date
Invoke-Expression $pytestCmd
$exitCode = $LASTEXITCODE
$duration = (Get-Date) - $startTime

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
if ($exitCode -eq 0) {
    Write-Host "  ✅ ALL TESTS PASSED" -ForegroundColor Green
} else {
    Write-Host "  ❌ SOME TESTS FAILED (exit code: $exitCode)" -ForegroundColor Red
}
Write-Host "  Duration : $($duration.ToString('mm\:ss'))" -ForegroundColor White
Write-Host "  Reports  : reports\html-reports\" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Cyan

if ($GenerateReport -or $OpenReport) {
    Write-Host ""
    Write-Host "Generating Allure report..." -ForegroundColor Yellow
    $allureCheck = Get-Command allure -ErrorAction SilentlyContinue
    if ($allureCheck) {
        allure generate reports\allure-results -o reports\allure-report --clean
        if ($OpenReport) {
            Start-Process "reports\allure-report\index.html"
        }
    } else {
        Write-Host "⚠ allure CLI not found — install with: scoop install allure" -ForegroundColor Yellow
    }
}

exit $exitCode
