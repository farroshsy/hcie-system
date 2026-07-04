#!/usr/bin/env python3
"""
HCIE Learner Data Security Checker

Specific checks for learner data handling in education systems:
- Learner data encryption requirements
- Data access logging
- Age-appropriate data handling
- Third-party data sharing compliance
- Parental consent verification for minors
"""

import ast
import re
import sys
from pathlib import Path
from typing import List, Dict, Any


class LearnerDataSecurityChecker(ast.NodeVisitor):
    """AST visitor for learner data security checks"""
    
    def __init__(self, filename: str):
        self.filename = filename
        self.issues: List[Dict[str, Any]] = []
        
        # Learner data fields that require special handling
        sensitive_learner_fields = {
            'student_id', 'learner_id', 'user_id', 'email', 'name',
            'full_name', 'first_name', 'last_name', 'age', 'grade',
            'school', 'classroom', 'teacher', 'parent_email',
            'guardian_contact', 'special_education_status',
            'disability', 'iep_status', 'academic_performance',
            'behavior_records', 'attendance', 'discipline'
        }
        
    def check_learner_data_encryption(self, node: ast.Call) -> None:
        """Check if learner data is properly encrypted"""
        if isinstance(node.func, ast.Attribute):
            # Look for database operations with learner data
            if node.func.attr in ['insert', 'update', 'save', 'store', 'write']:
                for arg in node.args:
                    if self._contains_learner_data(arg):
                        # Check if encryption is mentioned in nearby context
                        self.issues.append({
                            'line': node.lineno,
                            'type': 'UNENCRYPTED_LEARNER_DATA',
                            'message': 'Learner data operation without visible encryption',
                            'severity': 'HIGH'
                        })
    
    def check_access_logging(self, node: ast.FunctionDef) -> None:
        """Check if learner data access is logged"""
        has_learner_access = False
        has_logging = False
        
        # Check if function accesses learner data
        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                if 'student' in child.id.lower() or 'learner' in child.id.lower():
                    has_learner_access = True
            elif isinstance(child, ast.Attribute):
                if 'student' in child.attr.lower() or 'learner' in child.attr.lower():
                    has_learner_access = True
            elif isinstance(child, ast.Call):
                if isinstance(child.func, ast.Attribute):
                    if child.func.attr in ['log', 'info', 'debug', 'audit']:
                        has_logging = True
        
        if has_learner_access and not has_logging:
            self.issues.append({
                'line': node.lineno,
                'type': 'MISSING_ACCESS_LOG',
                'message': f'Function {node.name} accesses learner data without visible logging',
                'severity': 'MEDIUM'
            })
    
    def check_third_party_sharing(self, node: ast.Call) -> None:
        """Check for third-party data sharing compliance"""
        if isinstance(node.func, ast.Attribute):
            # Look for HTTP requests to external services
            if node.func.attr in ['post', 'put', 'request']:
                for arg in node.args:
                    if isinstance(arg, ast.Constant):
                        if isinstance(arg.value, str):
                            # Check if URL is external and not whitelisted
                            if self._is_external_url(arg.value):
                                self.issues.append({
                                    'line': node.lineno,
                                    'type': 'EXTERNAL_DATA_SHARING',
                                    'message': f'External URL detected: {arg.value}. Verify learner data sharing compliance',
                                    'severity': 'HIGH'
                                })
    
    def check_age_verification(self, node: ast.FunctionDef) -> None:
        """Check for age verification for learner data access"""
        # Look for functions that might need age verification
        age_sensitive_keywords = ['profile', 'personal', 'contact', 'parent', 'guardian']
        
        function_needs_age_check = any(keyword in node.name.lower() for keyword in age_sensitive_keywords)
        has_age_check = False
        
        if function_needs_age_check:
            for child in ast.walk(node):
                if isinstance(child, ast.Compare):
                    for comparator in child.comparators:
                        if isinstance(comparator, ast.Constant):
                            if isinstance(comparator.value, int) and 12 <= comparator.value <= 18:
                                has_age_check = True
                                break
                elif isinstance(child, ast.Name):
                    if 'age' in child.id.lower():
                        has_age_check = True
                        break
            
            if not has_age_check:
                self.issues.append({
                    'line': node.lineno,
                    'type': 'MISSING_AGE_VERIFICATION',
                    'message': f'Function {node.name} should verify learner age for data access',
                    'severity': 'MEDIUM'
                })
    
    def check_parental_consent(self, node: ast.FunctionDef) -> None:
        """Check for parental consent for minor learners"""
        consent_keywords = ['consent', 'permission', 'authorization', 'parent', 'guardian']
        data_keywords = ['data', 'personal', 'profile', 'information']
        
        needs_consent_check = any(
            kw in node.name.lower() for kw in consent_keywords + data_keywords
        )
        
        if needs_consent_check:
            has_consent_logic = False
            for child in ast.walk(node):
                if isinstance(child, ast.Name):
                    if any(kw in child.id.lower() for kw in consent_keywords):
                        has_consent_logic = True
                        break
            
            if not has_consent_logic:
                self.issues.append({
                    'line': node.lineno,
                    'type': 'MISSING_PARENTAL_CONSENT',
                    'message': f'Function {node.name} should verify parental consent for minors',
                    'severity': 'HIGH'
                })
    
    def check_data_minimization(self, node: ast.Assign) -> None:
        """Check for data minimization compliance"""
        if isinstance(node.value, ast.Call):
            # Check if loading entire learner records when only specific fields needed
            if isinstance(node.value.func, ast.Attribute):
                if node.value.func.attr in ['find_all', 'all', 'select', 'query']:
                    # Warn if no field selection is specified
                    for child in ast.walk(node.value):
                        if isinstance(child, ast.keyword):
                            if child.arg in ['fields', 'only', 'select']:
                                return  # Field selection present
                    
                    self.issues.append({
                        'line': node.lineno,
                        'type': 'DATA_MINIMIZATION',
                        'message': 'Consider selecting specific fields instead of entire records',
                        'severity': 'LOW'
                    })
    
    def _contains_learner_data(self, node: ast.AST) -> bool:
        """Check if AST node contains learner data references"""
        if isinstance(node, ast.Name):
            return any(field in node.id.lower() for field in ['student', 'learner', 'user'])
        elif isinstance(node, ast.Attribute):
            return any(field in node.attr.lower() for field in ['student', 'learner', 'user'])
        return False
    
    def _is_external_url(self, url: str) -> bool:
        """Check if URL is external (not localhost or internal)"""
        external_indicators = ['http://', 'https://']
        internal_domains = ['localhost', '127.0.0.1', '0.0.0.0', 'internal']
        
        if not any(indicator in url for indicator in external_indicators):
            return False
        
        return not any(domain in url for domain in internal_domains)
    
    def visit_Call(self, node: ast.Call) -> None:
        self.check_learner_data_encryption(node)
        self.check_third_party_sharing(node)
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.check_access_logging(node)
        self.check_age_verification(node)
        self.check_parental_consent(node)
        self.generic_visit(node)
    
    def visit_Assign(self, node: ast.Assign) -> None:
        self.check_data_minimization(node)
        self.generic_visit(node)


def check_file(filepath: str) -> List[Dict[str, Any]]:
    """Run learner data security checks on a single file"""
    issues = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
            
        tree = ast.parse(source, filename=filepath)
        
        # Run learner data security checks
        checker = LearnerDataSecurityChecker(filepath)
        checker.visit(tree)
        issues.extend(checker.issues)
        
    except SyntaxError as e:
        issues.append({
            'line': e.lineno,
            'type': 'SYNTAX_ERROR',
            'message': f'Syntax error: {e.msg}',
            'severity': 'ERROR'
        })
    except Exception as e:
        issues.append({
            'line': 0,
            'type': 'PARSE_ERROR',
            'message': f'Error parsing file: {str(e)}',
            'severity': 'ERROR'
        })
    
    return issues


def main():
    """Main entry point for the learner data security checker"""
    if len(sys.argv) < 2:
        print("Usage: python learner_data_check.py <file_or_directory>")
        sys.exit(1)
    
    target = sys.argv[1]
    all_issues = []
    
    if Path(target).is_file():
        issues = check_file(target)
        all_issues.extend(issues)
    elif Path(target).is_dir():
        for py_file in Path(target).rglob('*.py'):
            issues = check_file(str(py_file))
            all_issues.extend(issues)
    else:
        print(f"Error: {target} is not a valid file or directory")
        sys.exit(1)
    
    # Report results
    if all_issues:
        print(f"Learner Data Security Issues: {len(all_issues)}")
        print("=" * 70)
        
        # Group by severity
        high_issues = [i for i in all_issues if i.get('severity') == 'HIGH']
        medium_issues = [i for i in all_issues if i.get('severity') == 'MEDIUM']
        low_issues = [i for i in all_issues if i.get('severity') == 'LOW']
        
        if high_issues:
            print(f"\nHIGH SEVERITY ({len(high_issues)}):")
            for issue in high_issues:
                print(f"  {issue.get('filename', target)}:{issue['line']} - {issue['type']}")
                print(f"    {issue['message']}")
        
        if medium_issues:
            print(f"\nMEDIUM SEVERITY ({len(medium_issues)}):")
            for issue in medium_issues:
                print(f"  {issue.get('filename', target)}:{issue['line']} - {issue['type']}")
                print(f"    {issue['message']}")
        
        if low_issues:
            print(f"\nLOW SEVERITY ({len(low_issues)}):")
            for issue in low_issues:
                print(f"  {issue.get('filename', target)}:{issue['line']} - {issue['type']}")
                print(f"    {issue['message']}")
        
        print(f"\nTotal: {len(all_issues)} issues found")
        sys.exit(1)
    else:
        print("✓ No learner data security issues found")
        sys.exit(0)


if __name__ == "__main__":
    main()
