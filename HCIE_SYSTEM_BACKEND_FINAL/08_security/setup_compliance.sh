#!/bin/bash

# HCIE Compliance & Security Setup Script
# This script sets up the compliance and security tools for the HCIE education system

set -e

echo "=========================================="
echo "HCIE Compliance & Security Setup"
echo "=========================================="
echo ""

# Check if Python 3.8+ is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo "Found Python version: $PYTHON_VERSION"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install compliance requirements
echo "Installing compliance requirements..."
pip install --upgrade pip
pip install -r requirements-compliance.txt

# Set up pre-commit hooks
echo "Setting up pre-commit hooks..."
pre-commit install

# Initialize detect-secrets baseline
echo "Initializing detect-secrets baseline..."
detect-secrets scan > .secrets.baseline 2>/dev/null || echo "No secrets found or detect-secrets not installed"

# Create .secrets.baseline if it doesn't exist
if [ ! -f ".secrets.baseline" ]; then
    echo '{"version":"1.0","results":[]}' > .secrets.baseline
fi

# Run initial compliance checks
echo "Running initial compliance checks..."
echo ""

echo "1. Running Black (code formatting)..."
black --check 01_source/ 2>/dev/null || echo "  Some files need formatting (run 'black 01_source/' to fix)"

echo ""
echo "2. Running isort (import sorting)..."
isort --check-only 01_source/ 2>/dev/null || echo "  Some imports need sorting (run 'isort 01_source/' to fix)"

echo ""
echo "3. Running flake8 (linting)..."
flake8 01_source/ --max-line-length=100 --extend-ignore=E203,W503 || echo "  Some linting issues found"

echo ""
echo "4. Running Bandit (security scanning)..."
bandit -r 01_source/ -f json -o bandit-report.json 2>/dev/null || echo "  Some security issues found (check bandit-report.json)"

echo ""
echo "5. Running custom compliance checks..."
python 08_security/00_compliance/ferpa_gdpr_linter.py 01_source/ 2>/dev/null || echo "  Some FERPA/GDPR issues found"
python 08_security/00_audit/pii_detector.py 01_source/ 2>/dev/null || echo "  Some PII concerns found"
python 08_security/00_compliance/01_ferpa/learner_data_check.py 01_source/ 2>/dev/null || echo "  Some learner data security issues found"

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Review and fix any issues found above"
echo "2. Run 'pre-commit run --all-files' to check all files"
echo "3. Commit the changes - pre-commit hooks will run automatically"
echo ""
echo "Manual commands:"
echo "- Format code: black 01_source/"
echo "- Sort imports: isort 01_source/"
echo "- Fix linting: flake8 01_source/ --max-line-length=100"
echo "- Security scan: bandit -r 01_source/"
echo "- Compliance check: python 08_security/00_compliance/ferpa_gdpr_linter.py 01_source/"
echo ""
echo "For more information, see the README in 08_security/"
