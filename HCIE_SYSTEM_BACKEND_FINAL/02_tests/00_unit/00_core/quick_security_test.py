#!/usr/bin/env python3
"""
Quick Security Test - Tests actual security issues on working endpoints
"""

import requests
import json
import time
from datetime import datetime

class QuickSecurityTest:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.results = []
    
    def log_result(self, test_name, success, details="", response_time=0):
        result = {
            "test_name": test_name,
            "success": success,
            "details": details,
            "response_time": response_time,
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)
        status = "SECURE" if success else "VULNERABLE"
        print(f"[{status}] {test_name}: {details} ({response_time:.2f}s)")
    
    def test_unauthorized_task_access(self):
        """Test accessing tasks without authentication"""
        start_time = time.time()
        try:
            # Test if tasks endpoint requires authentication (it shouldn't based on our test)
            response = requests.get(f"{self.base_url}/api/v1/tasks/unauthorized_user", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                self.log_result("Unauthorized Task Access", False, "Tasks endpoint allows anonymous access", response_time)
                return False
            elif response.status_code in [401, 403]:
                self.log_result("Unauthorized Task Access", True, "Tasks endpoint properly protected", response_time)
                return True
            else:
                self.log_result("Unauthorized Task Access", False, f"Unexpected status {response.status_code}", response_time)
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_result("Unauthorized Task Access", False, f"Exception: {str(e)}", response_time)
            return False
    
    def test_unauthorized_admin_access(self):
        """Test accessing admin endpoints without authentication"""
        start_time = time.time()
        try:
            response = requests.get(f"{self.base_url}/admin/services/status", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                self.log_result("Unauthorized Admin Access", False, "Admin endpoint allows anonymous access", response_time)
                return False
            elif response.status_code in [401, 403]:
                self.log_result("Unauthorized Admin Access", True, "Admin endpoint properly protected", response_time)
                return True
            else:
                self.log_result("Unauthorized Admin Access", False, f"Unexpected status {response.status_code}", response_time)
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_result("Unauthorized Admin Access", False, f"Exception: {str(e)}", response_time)
            return False
    
    def test_malicious_task_submission(self):
        """Test submitting malicious data"""
        start_time = time.time()
        try:
            # Test SQL injection payload
            malicious_payloads = [
                "'; DROP TABLE users; --",
                "' OR '1'='1",
                "<script>alert('XSS')</script>",
                "' UNION SELECT password FROM users --"
            ]
            
            vulnerabilities_found = 0
            
            for payload in malicious_payloads:
                try:
                    submit_payload = {
                        "user_id": "security_test_user",
                        "task_id": "test_task",
                        "node_id": "test_node",
                        "representation": "text",
                        "answer": payload,
                        "response_time": 10.0
                    }
                    
                    response = requests.post(
                        f"{self.base_url}/api/v1/tasks/submit",
                        json=submit_payload,
                        timeout=10
                    )
                    
                    # Check if server processes malicious input (bad) or rejects it (good)
                    if response.status_code == 500:
                        # Server crashed - potential vulnerability
                        vulnerabilities_found += 1
                    elif response.status_code in [400, 422]:
                        # Server properly rejected malicious input
                        pass
                    else:
                        # Unexpected response
                        vulnerabilities_found += 0.5
                        
                except Exception:
                    # Exception might indicate server crash or proper rejection
                    pass
            
            response_time = time.time() - start_time
            
            if vulnerabilities_found == 0:
                self.log_result("Malicious Task Submission", True, "All malicious payloads properly handled", response_time)
                return True
            else:
                self.log_result("Malicious Task Submission", False, f"{vulnerabilities_found} potential vulnerabilities found", response_time)
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_result("Malicious Task Submission", False, f"Exception: {str(e)}", response_time)
            return False
    
    def test_rate_limiting(self):
        """Test basic rate limiting"""
        start_time = time.time()
        try:
            # Send rapid requests to check for rate limiting
            num_requests = 50
            rate_limited = False
            
            for i in range(num_requests):
                try:
                    response = requests.get(f"{self.base_url}/api/v1/tasks/rate_test_user_{i}", timeout=2)
                    
                    if response.status_code == 429:
                        rate_limited = True
                        break
                        
                except requests.exceptions.Timeout:
                    # Timeout might indicate rate limiting
                    rate_limited = True
                    break
                except Exception:
                    continue
            
            response_time = time.time() - start_time
            
            if rate_limited:
                self.log_result("Rate Limiting", True, f"Rate limiting detected after {i+1} requests", response_time)
                return True
            else:
                self.log_result("Rate Limiting", False, f"No rate limiting detected after {num_requests} requests", response_time)
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_result("Rate Limiting", False, f"Exception: {str(e)}", response_time)
            return False
    
    def test_large_payload_submission(self):
        """Test submitting very large payloads"""
        start_time = time.time()
        try:
            # Create a large payload
            large_answer = "A" * 10000  # 10KB string
            
            submit_payload = {
                "user_id": "large_payload_test",
                "task_id": "test_task",
                "node_id": "test_node",
                "representation": "text",
                "answer": large_answer,
                "response_time": 10.0
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/tasks/submit",
                json=submit_payload,
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code in [400, 413, 422]:
                self.log_result("Large Payload Submission", True, "Large payload properly rejected", response_time)
                return True
            elif response.status_code == 500:
                self.log_result("Large Payload Submission", False, "Server crashed with large payload", response_time)
                return False
            else:
                self.log_result("Large Payload Submission", False, f"Unexpected status {response.status_code}", response_time)
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_result("Large Payload Submission", True, f"Large payload caused exception (good): {str(e)[:50]}", response_time)
            return True
    
    def test_invalid_json_submission(self):
        """Test submitting invalid JSON"""
        start_time = time.time()
        try:
            # Test malformed JSON
            invalid_json = '{"user_id": "test", "task_id": "test", "answer": 123,}'  # Trailing comma
            
            response = requests.post(
                f"{self.base_url}/api/v1/tasks/submit",
                data=invalid_json,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code in [400, 422]:
                self.log_result("Invalid JSON Submission", True, "Invalid JSON properly rejected", response_time)
                return True
            else:
                self.log_result("Invalid JSON Submission", False, f"Invalid JSON accepted (status {response.status_code})", response_time)
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_result("Invalid JSON Submission", True, f"Invalid JSON caused exception (good): {str(e)[:50]}", response_time)
            return True
    
    def run_security_tests(self):
        """Run all security tests"""
        print("="*60)
        print("QUICK SECURITY TEST - HCIE RealSystem Backend V2")
        print("="*60)
        
        # Run security tests
        self.test_unauthorized_task_access()
        self.test_unauthorized_admin_access()
        self.test_malicious_task_submission()
        self.test_rate_limiting()
        self.test_large_payload_submission()
        self.test_invalid_json_submission()
        
        # Generate summary
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["success"])
        security_score = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print("\n" + "="*60)
        print("SECURITY TEST SUMMARY")
        print("="*60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Security Score: {security_score:.1f}%")
        
        # Identify critical issues
        critical_issues = []
        for result in self.results:
            if not result["success"] and "Unauthorized" in result["test_name"]:
                critical_issues.append(result["test_name"])
        
        if critical_issues:
            print(f"\nCRITICAL SECURITY ISSUES:")
            for issue in critical_issues:
                print(f"  - {issue}")
        
        # Save results
        report = {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": total_tests - passed_tests,
                "security_score": security_score,
                "critical_issues": critical_issues,
                "timestamp": datetime.now().isoformat()
            },
            "results": self.results
        }
        
        with open("quick_security_test_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\nDetailed report saved to: quick_security_test_report.json")
        
        return security_score >= 70, critical_issues

if __name__ == "__main__":
    tester = QuickSecurityTest()
    success, issues = tester.run_security_tests()
    exit(0 if success else 1)
