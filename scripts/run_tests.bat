@echo off
REM ============================================================
REM AI-Enhanced Enterprise Test Automation Framework
REM Windows Execution Script
REM ============================================================
REM USAGE:
REM   run_tests.bat smoke
REM   run_tests.bat regression chrome
REM   run_tests.bat api
REM   run_tests.bat all firefox headless
REM ============================================================

SET SUITE=%1
SET BROWSER=%2
SET HEADLESS_MODE=%3

IF "%SUITE%"=="" SET SUITE=smoke
IF "%BROWSER%"=="" SET BROWSER=chrome
IF "%HEADLESS_MODE%"=="headless" (SET HEADLESS=true) ELSE (SET HEADLESS=false)

echo.
echo ============================================================
echo   AI-Enhanced Enterprise Test Automation Framework
echo   Suite     : %SUITE%
echo   Browser   : %BROWSER%
echo   Headless  : %HEADLESS%
echo ============================================================
echo.

REM Create required directories
mkdir reports\html-reports 2>nul
mkdir reports\allure-results 2>nul
mkdir reports\screenshots 2>nul
mkdir logs 2>nul

REM Set environment
SET PYTHONPATH=%CD%
SET ENVIRONMENT=dev

IF "%SUITE%"=="smoke" (
    echo Running SMOKE tests...
    pytest tests/ -m smoke --tb=short -v --reruns=2 ^
        --html=reports\html-reports\smoke_report.html ^
        --self-contained-html --alluredir=reports\allure-results
)

IF "%SUITE%"=="regression" (
    echo Running REGRESSION tests...
    pytest tests/ui/ -m regression --tb=short -v --reruns=2 ^
        -n 2 ^
        --html=reports\html-reports\regression_report.html ^
        --self-contained-html --alluredir=reports\allure-results
)

IF "%SUITE%"=="api" (
    echo Running API tests...
    pytest tests/api/ --tb=short -v ^
        --html=reports\html-reports\api_report.html ^
        --self-contained-html --alluredir=reports\allure-results
)

IF "%SUITE%"=="database" (
    echo Running DATABASE tests...
    pytest tests/database/ --tb=short -v ^
        --html=reports\html-reports\db_report.html ^
        --self-contained-html --alluredir=reports\allure-results
)

IF "%SUITE%"=="all" (
    echo Running ALL tests...
    pytest tests/ --tb=short -v --reruns=2 -n 2 ^
        --html=reports\html-reports\full_report.html ^
        --self-contained-html --alluredir=reports\allure-results
)

echo.
echo ============================================================
echo   Execution Complete!
echo   HTML Report : reports\html-reports\
echo   Allure Data : reports\allure-results\
echo ============================================================
echo.
echo To view Allure report:
echo   allure serve reports\allure-results
