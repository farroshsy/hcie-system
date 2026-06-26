#!/usr/bin/env python3
"""
Security Vulnerability Testing
Tests critical security issues: unauthorized access, token misuse, injection, rate limiting
"""

import asyncio

import pytest as _pt_skip
_pt_skip.skip(
    "integration-style test requiring aiohttp + a live API; exercised in the integration suite.",
    allow_module_level=True,
)

import json
import time
import uuid
from datetime import datetime
from typing import Dict, List
import aiohttp
import pytest
from concurrent.futures import ThreadPoolExecutor
import threading


class SecurityTester:
    """Comprehensive security testing"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.session = None
        self.test_results = []
        self.user_tokens = {}
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_result(self, test_name: str, success: bool, details: str = "", response_time: float = 0):
        """Log test result"""
        result = {
            "test_name": test_name,
            "success": success,
            "details": details,
            "response_time": response_time,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "SECURE" if success else "VULNERABLE"
        print(f"[{status}] {test_name}: {details} ({response_time:.2f}s)")
    
    async def create_test_user(self, user_id: str) -> str:
        """Create test user and return token"""
        try:
            payload = {
                "email": f"security_test_{user_id}@example.com",
                "password": "TestPassword123!",
                "user_id": user_id,
                "role": "student"
            }
            
            async with self.session.post(
                f"{self.base_url}/api/v1/auth/register",
                json=payload
            ) as response:
                if response.status == 201:
                    data = await response.json()
                    token = data.get("access_token")
                    self.user_tokens[user_id] = token
                    return token
                return None
        except Exception:
            return None
    
    async def test_unauthorized_access(self) -> bool:
        """Test unauthorized access to protected endpoints"""
        print("\n=== Testing Unauthorized Access ===")
        
        protected_endpoints = [
            f"/api/v1/tasks/user123",
            "/api/v1/tasks/history/user123",
            "/api/v1/analytics/user123",
            "/api/v1/admin/users",
            "/api/v1/admin/system/stats"
        ]
        
        all_secure = True
        
        for endpoint in protected_endpoints:
            start_time = time.time()
            
            try:
                async with self.session.get(f"{self.base_url}{endpoint}") as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 401:
                        self.log_result("Unauthorized Access", True, f"GET {endpoint} correctly returned 401", response_time)
                    elif response.status == 403:
                        self.log_result("Unauthorized Access", True, f"GET {endpoint} correctly returned 403", response_time)
                    else:
                        self.log_result("Unauthorized Access", False, f"GET {endpoint} returned {response.status} (expected 401/403)", response_time)
                        all_secure = False
                        
            except Exception as e:
                response_time = time.time() - start_time
                self.log_result("Unauthorized Access", False, f"GET {endpoint} exception: {str(e)}", response_time)
                all_secure = False
        
        return all_secure
    
    async def test_token_misuse(self) -> bool:
        """Test using user A's token to access user B's data"""
        print("\n=== Testing Token Misuse ===")
        
        # Create two users
        user_a_token = await self.create_test_user("user_a")
        user_b_token = await self.create_test_user("user_b")
        
        if not user_a_token or not user_b_token:
            self.log_result("Token Misuse", False, "Failed to create test users", 0)
            return False
        
        # Test: User A tries to access User B's data
        test_cases = [
            ("User A token on User B tasks", user_a_token, "/api/v1/tasks/user_b"),
            ("User B token on User A tasks", user_b_token, "/api/v1/tasks/user_a"),
            ("User A token on User B history", user_a_token, "/api/v1/tasks/history/user_b"),
            ("User B token on User A history", user_b_token, "/api/v1/tasks/history/user_a")
        ]
        
        all_secure = True
        
        for test_name, token, endpoint in test_cases:
            start_time = time.time()
            
            try:
                headers = {"Authorization": f"Bearer {token}"}
                
                async with self.session.get(f"{self.base_url}{endpoint}", headers=headers) as response:
                    response_time = time.time() - start_time
                    
                    if response.status in [401, 403, 404]:
                        self.log_result("Token Misuse", True, f"{test_name} correctly rejected ({response.status})", response_time)
                    else:
                        self.log_result("Token Misuse", False, f"{test_name} allowed access ({response.status})", response_time)
                        all_secure = False
                        
            except Exception as e:
                response_time = time.time() - start_time
                self.log_result("Token Misuse", False, f"{test_name} exception: {str(e)}", response_time)
                all_secure = False
        
        return all_secure
    
    async def test_sql_injection(self) -> bool:
        """Test SQL injection attempts"""
        print("\n=== Testing SQL Injection ===")
        
        # Create test user
        token = await self.create_test_user("sql_test_user")
        if not token:
            self.log_result("SQL Injection", False, "Failed to create test user", 0)
            return False
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # SQL injection payloads
        injection_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "'; SELECT * FROM users; --",
            "' UNION SELECT password FROM users --",
            "'; DELETE FROM learning_sessions; --",
            "'; UPDATE users SET role='admin' WHERE user_id='sql_test_user'; --",
            "'; INSERT INTO users (email, password) VALUES ('hacker@evil.com', 'password'); --"
        ]
        
        all_secure = True
        
        for payload in injection_payloads:
            start_time = time.time()
            
            try:
                # Test in task submission
                submit_payload = {
                    "user_id": "sql_test_user",
                    "task_id": "test_task",
                    "node_id": "test_node",
                    "answer": payload,
                    "response_time": 10.0
                }
                
                async with self.session.post(
                    f"{self.base_url}/api/v1/tasks/submit",
                    json=submit_payload,
                    headers=headers
                ) as response:
                    response_time = time.time() - start_time
                    
                    if response.status in [400, 422, 500]:
                        self.log_result("SQL Injection", True, f"Payload rejected: {payload[:50]}...", response_time)
                    else:
                        self.log_result("SQL Injection", False, f"Payload may have been processed: {payload[:50]}... (status: {response.status})", response_time)
                        all_secure = False
                        
            except Exception as e:
                response_time = time.time() - start_time
                self.log_result("SQL Injection", True, f"Payload caused exception (good): {payload[:50]}... - {str(e)}", response_time)
        
        return all_secure
    
    async def test_xss_attempts(self) -> bool:
        """Test XSS attempts"""
        print("\n=== Testing XSS Attempts ===")
        
        token = await self.create_test_user("xss_test_user")
        if not token:
            self.log_result("XSS Testing", False, "Failed to create test user", 0)
            return False
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # XSS payloads
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "';alert('XSS');//",
            "<svg onload=alert('XSS')>",
            "'\"><script>alert('XSS')</script>"
        ]
        
        all_secure = True
        
        for payload in xss_payloads:
            start_time = time.time()
            
            try:
                submit_payload = {
                    "user_id": "xss_test_user",
                    "task_id": "test_task",
                    "node_id": "test_node",
                    "answer": payload,
                    "response_time": 10.0
                }
                
                async with self.session.post(
                    f"{self.base_url}/api/v1/tasks/submit",
                    json=submit_payload,
                    headers=headers
                ) as response:
                    response_time = time.time() - start_time
                    
                    if response.status in [400, 422]:
                        self.log_result("XSS Testing", True, f"XSS payload rejected: {payload[:30]}...", response_time)
                    else:
                        self.log_result("XSS Testing", False, f"XSS payload may have been processed: {payload[:30]}... (status: {response.status})", response_time)
                        all_secure = False
                        
            except Exception as e:
                response_time = time.time() - start_time
                self.log_result("XSS Testing", True, f"XSS payload caused exception (good): {payload[:30]}... - {str(e)}", response_time)
        
        return all_secure
    
    async def test_rate_limiting(self) -> bool:
        """Test rate limiting under load"""
        print("\n=== Testing Rate Limiting ===")
        
        token = await self.create_test_user("rate_limit_user")
        if not token:
            self.log_result("Rate Limiting", False, "Failed to create test user", 0)
            return False
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test rapid requests
        num_requests = 100
        start_time = time.time()
        rate_limited = False
        
        for i in range(num_requests):
            try:
                async with self.session.get(
                    f"{self.base_url}/api/v1/tasks/rate_limit_user",
                    headers=headers
                ) as response:
                    if response.status == 429:
                        rate_limited = True
                        self.log_result("Rate Limiting", True, f"Rate limiting triggered after {i+1} requests", time.time() - start_time)
                        break
                    elif response.status == 401:
                        # Token expired, refresh
                        token = await self.create_test_user("rate_limit_user")
                        if not token:
                            break
                        headers = {"Authorization": f"Bearer {token}"}
                        
            except Exception as e:
                if i > 10:  # Allow some exceptions due to server load
                    break
        
        if not rate_limited:
            self.log_result("Rate Limiting", False, f"No rate limiting detected after {num_requests} requests", time.time() - start_time)
            return False
        
        return True
    
    async def test_concurrent_sessions(self) -> bool:
        """Test concurrent session handling"""
        print("\n=== Testing Concurrent Sessions ===")
        
        # Create multiple users with concurrent sessions
        num_users = 10
        tasks_per_user = 5
        
        async def user_session(user_id: int):
            """Simulate user session"""
            token = await self.create_test_user(f"concurrent_user_{user_id}")
            if not token:
                return False
            
            headers = {"Authorization": f"Bearer {token}"}
            success_count = 0
            
            for task_num in range(tasks_per_user):
                try:
                    # Get task
                    async with self.session.get(
                        f"{self.base_url}/api/v1/tasks/concurrent_user_{user_id}",
                        headers=headers
                    ) as response:
                        if response.status == 200:
                            # Submit answer
                            submit_payload = {
                                "user_id": f"concurrent_user_{user_id}",
                                "task_id": f"task_{task_num}",
                                "node_id": "test_node",
                                "answer": str(task_num * 10),
                                "response_time": 5.0
                            }
                            
                            async with self.session.post(
                                f"{self.base_url}/api/v1/tasks/submit",
                                json=submit_payload,
                                headers=headers
                            ) as submit_response:
                                if submit_response.status == 200:
                                    success_count += 1
                except Exception:
                    pass
            
            return success_count == tasks_per_user
        
        # Run concurrent sessions
        start_time = time.time()
        
        tasks = [user_session(i) for i in range(num_users)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        response_time = time.time() - start_time
        successful_sessions = sum(1 for r in results if r is True)
        
        if successful_sessions >= num_users * 0.8:  # 80% success rate
            self.log_result("Concurrent Sessions", True, f"{successful_sessions}/{num_users} sessions successful", response_time)
            return True
        else:
            self.log_result("Concurrent Sessions", False, f"Only {successful_sessions}/{num_users} sessions successful", response_time)
            return False
    
    async def run_security_tests(self) -> Dict:
        """Run all security tests"""
        print("=== Starting Security Vulnerability Tests ===")
        
        test_functions = [
            ("Unauthorized Access", self.test_unauthorized_access),
            ("Token Misuse", self.test_token_misuse),
            ("SQL Injection", self.test_sql_injection),
            ("XSS Attempts", self.test_xss_attempts),
            ("Rate Limiting", self.test_rate_limiting),
            ("Concurrent Sessions", self.test_concurrent_sessions)
        ]
        
        results = {}
        
        for test_name, test_func in test_functions:
            try:
                results[test_name] = await test_func()
            except Exception as e:
                self.log_result(test_name, False, f"Test failed with exception: {str(e)}", 0)
                results[test_name] = False
        
        # Generate report
        total_tests = len(results)
        passed_tests = sum(results.values())
        
        report = {
            "total_security_tests": total_tests,
            "passed_security_tests": passed_tests,
            "failed_security_tests": total_tests - passed_tests,
            "security_score": (passed_tests / total_tests) * 100 if total_tests > 0 else 0,
            "test_results": results,
            "detailed_results": self.test_results
        }
        
        print(f"\n=== Security Test Summary ===")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Security Score: {report['security_score']:.1f}%")
        
        return report


async def main():
    """Main security test runner"""
    async with SecurityTester() as tester:
        report = await tester.run_security_tests()
        
        # Save detailed report
        with open("security_test_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\nDetailed security report saved to: security_test_report.json")
        
        # Return True if security score is acceptable
        return report["security_score"] >= 80


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
