#!/usr/bin/env python3
"""
HCIE PII (Personally Identifiable Information) Detector

Detects potential PII in code for education data compliance:
- Email addresses
- Phone numbers
- Social Security Numbers
- Student IDs
- Names and addresses
- Other sensitive learner information
"""

import re
import sys
from pathlib import Path
from typing import List, Dict


class PIIDetector:
    """Detects PII patterns in code"""
    
    # PII patterns
    EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    SSN_PATTERN = r'\b\d{3}-\d{2}-\d{4}\b|\b\d{9}\b'
    PHONE_PATTERN = r'\b\d{3}-\d{3}-\d{4}\b|\b\(\d{3}\)\s*\d{3}-\d{4}\b'
    CREDIT_CARD_PATTERN = r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
    DATE_PATTERN = r'\b\d{1,2}/\d{1,2}/\d{4}\b|\b\d{4}-\d{1,2}-\d{1,2}\b'
    
    # Education-specific patterns
    STUDENT_ID_PATTERN = r'\bstudent[_-]?id\s*[:=]\s*[\'"]?[A-Za-z0-9]{5,20}[\'"]?\b'
    LEARNER_ID_PATTERN = r'\blearner[_-]?id\s*[:=]\s*[\'"]?[A-Za-z0-9]{5,20}[\'"]?\b'
    
    # Keywords that might indicate PII handling
    PII_KEYWORDS = [
        'email', 'password', 'ssn', 'social_security', 'phone', 'address',
        'credit_card', 'creditcard', 'full_name', 'firstname', 'lastname',
        'date_of_birth', 'dob', 'secret', 'token', 'api_key', 'private_key'
    ]
    
    def __init__(self):
        self.issues: List[Dict[str, str]] = []
        
    def detect_pii_in_line(self, line: str, line_number: int, filename: str) -> None:
        """Detect PII patterns in a single line of code"""
        
        # Check for email patterns
        if re.search(self.EMAIL_PATTERN, line):
            self.issues.append({
                'file': filename,
                'line': line_number,
                'type': 'EMAIL_ADDRESS',
                'pattern': self.EMAIL_PATTERN,
                'context': line.strip()
            })
        
        # Check for SSN patterns
        if re.search(self.SSN_PATTERN, line):
            self.issues.append({
                'file': filename,
                'line': line_number,
                'type': 'SOCIAL_SECURITY_NUMBER',
                'pattern': self.SSN_PATTERN,
                'context': line.strip()
            })
        
        # Check for phone patterns
        if re.search(self.PHONE_PATTERN, line):
            self.issues.append({
                'file': filename,
                'line': line_number,
                'type': 'PHONE_NUMBER',
                'pattern': self.PHONE_PATTERN,
                'context': line.strip()
            })
        
        # Check for credit card patterns
        if re.search(self.CREDIT_CARD_PATTERN, line):
            self.issues.append({
                'file': filename,
                'line': line_number,
                'type': 'CREDIT_CARD_NUMBER',
                'pattern': self.CREDIT_CARD_PATTERN,
                'context': line.strip()
            })
        
        # Check for student/learner ID patterns
        if re.search(self.STUDENT_ID_PATTERN, line, re.IGNORECASE):
            self.issues.append({
                'file': filename,
                'line': line_number,
                'type': 'STUDENT_ID',
                'pattern': self.STUDENT_ID_PATTERN,
                'context': line.strip()
            })
        
        if re.search(self.LEARNER_ID_PATTERN, line, re.IGNORECASE):
            self.issues.append({
                'file': filename,
                'line': line_number,
                'type': 'LEARNER_ID',
                'pattern': self.LEARNER_ID_PATTERN,
                'context': line.strip()
            })
        
        # Check for PII keywords with hardcoded values
        for keyword in self.PII_KEYWORDS:
            if keyword in line.lower():
                # Look for assignment patterns with the keyword
                assignment_pattern = rf'{keyword}\s*[:=]\s*[\'"](.*?)[\'"]'
                match = re.search(assignment_pattern, line, re.IGNORECASE)
                if match and len(match.group(1)) > 3:  # Exclude short values
                    self.issues.append({
                        'file': filename,
                        'line': line_number,
                        'type': 'POTENTIAL_PII_ASSIGNMENT',
                        'keyword': keyword,
                        'context': line.strip()
                    })
    
    def check_for_hardcoded_secrets(self, line: str, line_number: int, filename: str) -> None:
        """Check for hardcoded secrets and credentials"""
        secret_patterns = [
            (r'password\s*[:=]\s*[\'"][^\'"]{8,}[\'"]', 'HARDCODED_PASSWORD'),
            (r'api[_-]?key\s*[:=]\s*[\'"][A-Za-z0-9]{20,}[\'"]', 'HARDCODED_API_KEY'),
            (r'secret\s*[:=]\s*[\'"][A-Za-z0-9]{16,}[\'"]', 'HARDCODED_SECRET'),
            (r'token\s*[:=]\s*[\'"][A-Za-z0-9]{20,}[\'"]', 'HARDCODED_TOKEN'),
        ]
        
        for pattern, issue_type in secret_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                self.issues.append({
                    'file': filename,
                    'line': line_number,
                    'type': issue_type,
                    'severity': 'HIGH',
                    'context': line.strip()
                })
    
    def scan_file(self, filepath: str) -> List[Dict[str, str]]:
        """Scan a single file for PII"""
        self.issues = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line_number, line in enumerate(f, 1):
                    self.detect_pii_in_line(line, line_number, filepath)
                    self.check_for_hardcoded_secrets(line, line_number, filepath)
        except Exception as e:
            self.issues.append({
                'file': filepath,
                'line': 0,
                'type': 'SCAN_ERROR',
                'message': f'Error scanning file: {str(e)}',
                'severity': 'ERROR'
            })
        
        return self.issues


def check_directory(directory: str) -> List[Dict[str, str]]:
    """Check all Python files in a directory"""
    all_issues = []
    detector = PIIDetector()
    
    for py_file in Path(directory).rglob('*.py'):
        # Skip test files and common exclusions
        if any(exclude in str(py_file) for exclude in ['test', '__pycache__', '.venv', 'venv']):
            continue
        
        issues = detector.scan_file(str(py_file))
        all_issues.extend(issues)
    
    return all_issues


def check_file(filepath: str) -> List[Dict[str, str]]:
    """Check a single file for PII"""
    detector = PIIDetector()
    return detector.scan_file(filepath)


def main():
    """Main entry point"""
    # Force UTF-8 stdout on Windows
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    
    if len(sys.argv) < 2:
        print("Usage: python pii_detector.py <file_or_directory>")
        sys.exit(1)
    
    target = sys.argv[1]
    
    if Path(target).is_file():
        all_issues = check_file(target)
    elif Path(target).is_dir():
        all_issues = check_directory(target)
    else:
        print(f"Error: {target} is not a valid file or directory")
        sys.exit(1)
    
    # Report results
    if all_issues:
        print(f"PII Detection Results: {len(all_issues)} issues found")
        print("=" * 70)
        
        # Group by severity
        high_severity = [i for i in all_issues if i.get('severity') == 'HIGH']
        medium_severity = [i for i in all_issues if i.get('severity') != 'HIGH']
        
        if high_severity:
            print(f"\nHIGH SEVERITY ({len(high_severity)}):")
            for issue in high_severity:
                print(f"  {issue['file']}:{issue['line']} - {issue['type']}")
                print(f"    Context: {issue.get('context', issue.get('message', 'N/A'))}")
        
        if medium_severity:
            print(f"\nMEDIUM SEVERITY ({len(medium_severity)}):")
            for issue in medium_severity:
                print(f"  {issue['file']}:{issue['line']} - {issue['type']}")
                print(f"    Context: {issue.get('context', issue.get('message', 'N/A'))}")
        
        print(f"\nTotal: {len(all_issues)} PII/security concerns found")
        sys.exit(1)
    else:
        print("[OK] No PII or hardcoded secrets detected")
        sys.exit(0)


if __name__ == "__main__":
    main()
