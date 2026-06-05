@echo off
REM ============================================================
REM AI-Enhanced Enterprise Test Automation Framework
REM Allure Report Generator Script (Windows)
REM ============================================================
REM USAGE:
REM   generate_report.bat          -> Open live Allure server
REM   generate_report.bat static   -> Generate static HTML report
REM   generate_report.bat clean    -> Clean + regenerate
REM ============================================================

SET MODE=%1
SET RESULTS_DIR=reports\allure-results
SET REPORT_DIR=reports\allure-report

IF "%MODE%"=="" SET MODE=serve

echo.
echo ============================================================
echo   AI Test Framework - Report Generator
echo   Mode: %MODE%
echo ============================================================
echo.

REM Check allure is installed
WHERE allure >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: allure CLI not found!
    echo.
    echo Install options:
    echo   1. Scoop (recommended): scoop install allure
    echo   2. Chocolatey:          choco install allure
    echo   3. Download from:       https://github.com/allure-framework/allure2/releases
    echo.
    echo Alternative: Open reports\html-reports\*.html directly in browser
    pause
    exit /b 1
)

REM Check results directory exists
IF NOT EXIST "%RESULTS_DIR%" (
    echo ERROR: No Allure results found at: %RESULTS_DIR%
    echo.
    echo Run tests first:
    echo   pytest tests/ --alluredir=reports/allure-results
    echo   OR
    echo   scripts\run_tests.bat smoke
    pause
    exit /b 1
)

IF "%MODE%"=="clean" (
    echo Cleaning old reports...
    IF EXIST "%REPORT_DIR%" rmdir /s /q "%REPORT_DIR%"
    SET MODE=static
)

IF "%MODE%"=="static" (
    echo Generating static HTML report...
    allure generate "%RESULTS_DIR%" -o "%REPORT_DIR%" --clean
    echo.
    echo Static report generated at: %REPORT_DIR%\index.html
    echo.
    echo Opening report in browser...
    start "" "%REPORT_DIR%\index.html"
    goto :EOF
)

IF "%MODE%"=="serve" (
    echo Starting Allure live report server...
    echo Press Ctrl+C to stop
    echo.
    allure serve "%RESULTS_DIR%"
)

echo.
echo Done!
