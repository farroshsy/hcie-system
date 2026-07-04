@echo off
REM HCIE Compliance & Security Setup Script (Windows)
REM This script sets up the compliance and security tools for the HCIE education system

echo ==========================================
echo HCIE Compliance & Security Setup
echo ==========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo Found Python version: %PYTHON_VERSION%

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install compliance requirements
echo Installing compliance requirements...
python -m pip install --upgrade pip
pip install -r requirements-compliance.txt

REM Set up pre-commit hooks
echo Setting up pre-commit hooks...
pre-commit install

REM Initialize detect-secrets baseline
echo Initializing detect-secrets baseline...
detect-secrets scan > .secrets.baseline 2>nul || echo No secrets found or detect-secrets not installed

REM Create .secrets.baseline if it doesn't exist
if not exist ".secrets.baseline" (
    echo {"version":"1.0","results":[]} > .secrets.baseline
)

REM Run initial compliance checks
echo Running initial compliance checks...
echo.

echo 1. Running Black (code formatting)...
black --check 01_source/ 2>nul || echo   Some files need formatting (run 'black 01_source/' to fix)

echo.
echo 2. Running isort (import sorting)...
isort --check-only 01_source/ 2>nul || echo   Some imports need sorting (run 'isort 01_source/' to fix)

echo.
echo 3. Running flake8 (linting)...
flake8 01_source/ --max-line-length=100 --extend-ignore=E203,W503 || echo   Some linting issues found

echo.
echo 4. Running Bandit (security scanning)...
bandit -r 01_source/ -f json -o bandit-report.json 2>nul || echo   Some security issues found (check bandit-report.json)

echo.
echo 5. Running custom compliance checks...
python 08_security/00_compliance/ferpa_gdpr_linter.py 01_source/ 2>nul || echo   Some FERPA/GDPR issues found
python 08_security/00_audit/pii_detector.py 01_source/ 2>nul || echo   Some PII concerns found
python 08_security/00_compliance/01_ferpa/learner_data_check.py 01_source/ 2>nul || echo   Some learner data security issues found

echo.
echo ==========================================
echo Setup Complete!
echo ==========================================
echo.
echo Next steps:
echo 1. Review and fix any issues found above
echo 2. Run 'pre-commit run --all-files' to check all files
echo 3. Commit the changes - pre-commit hooks will run automatically
echo.
echo Manual commands:
echo - Format code: black 01_source/
echo - Sort imports: isort 01_source/
echo - Fix linting: flake8 01_source/ --max-line-length=100
echo - Security scan: bandit -r 01_source/
echo - Compliance check: python 08_security/00_compliance/ferpa_gdpr_linter.py 01_source/
echo.
echo For more information, see the README in 08_security/
