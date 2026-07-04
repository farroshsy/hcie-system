#!/usr/bin/env python3
"""
Comprehensive User Lifecycle Testing
Tests real user scenarios: register -> login -> learn -> progress -> return -> auth validation
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
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import aiohttp
import pytest
from dataclasses import dataclass


@dataclass
class UserSession:
    """User session data for testing"""
    user_id: str
    email: str
    password: str
    token: Optional[str] = None
    refresh_token: Optional[str] = None
    session_id: Optional[str] = None
    current_task: Optional[Dict] = None
    learning_history: List[Dict] = None
    
    def __post_init__(self):
        if self.learning_history is None:
            self.learning_history = []


class UserLifecycleTester:
    """Comprehensive user lifecycle testing"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.session = None
        self.test_results = []
        
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
        status = "PASS" if success else "FAIL"
        print(f"[{status}] {test_name}: {details} ({response_time:.2f}s)")
    
    async def register_user(self, user: UserSession) -> bool:
        """Test user registration"""
        start_time = time.time()
        
        try:
            payload = {
                "email": user.email,
                "password": user.password,
                "user_id": user.user_id,
                "role": "student"
            }
            
            async with self.session.post(
                f"{self.base_url}/api/v1/auth/register",
                json=payload
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 201:
                    data = await response.json()
                    user.token = data.get("access_token")
                    user.refresh_token = data.get("refresh_token")
                    self.log_result("User Registration", True, f"User {user.user_id} registered", response_time)
                    return True
                else:
                    text = await response.text()
                    self.log_result("User Registration", False, f"Status {response.status}: {text}", response_time)
                    return False
                    
        except Exception as e:
            response_time = time.time() - start_time
            self.log_result("User Registration", False, f"Exception: {str(e)}", response_time)
            return False
    
    async def login_user(self, user: UserSession) -> bool:
        """Test user login"""
        start_time = time.time()
        
        try:
            payload = {
                "email": user.email,
                "password": user.password
            }
            
            async with self.session.post(
                f"{self.base_url}/api/v1/auth/login",
                json=payload
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    user.token = data.get("access_token")
                    user.refresh_token = data.get("refresh_token")
                    user.session_id = data.get("session_id")
                    self.log_result("User Login", True, f"User {user.user_id} logged in", response_time)
                    return True
                else:
                    text = await response.text()
                    self.log_result("User Login", False, f"Status {response.status}: {text}", response_time)
                    return False
                    
        except Exception as e:
            response_time = time.time() - start_time
            self.log_result("User Login", False, f"Exception: {str(e)}", response_time)
            return False
    
    async def get_next_task(self, user: UserSession) -> bool:
        """Test getting next adaptive task"""
        start_time = time.time()
        
        try:
            headers = {"Authorization": f"Bearer {user.token}"}
            
            async with self.session.get(
                f"{self.base_url}/api/v1/tasks/{user.user_id}",
                headers=headers
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    user.current_task = data
                    self.log_result("Get Next Task", True, f"Task {data.get('task_id')} retrieved", response_time)
                    return True
                else:
                    text = await response.text()
                    self.log_result("Get Next Task", False, f"Status {response.status}: {text}", response_time)
                    return False
                    
        except Exception as e:
            response_time = time.time() - start_time
            self.log_result("Get Next Task", False, f"Exception: {str(e)}", response_time)
            return False
    
    async def submit_answer(self, user: UserSession, answer: str = None) -> bool:
        """Test submitting task answer"""
        start_time = time.time()
        
        try:
            if not user.current_task:
                self.log_result("Submit Answer", False, "No current task", time.time() - start_time)
                return False
            
            if answer is None:
                # Simulate realistic answer based on task difficulty
                import random
                if user.current_task.get("difficulty") == "easy":
                    answer = str(random.randint(80, 100))
                elif user.current_task.get("difficulty") == "medium":
                    answer = str(random.randint(60, 80))
                else:
                    answer = str(random.randint(40, 60))
            
            payload = {
                "user_id": user.user_id,
                "task_id": user.current_task["task_id"],
                "node_id": user.current_task.get("node_id", "test_node"),
                "answer": answer,
                "response_time": random.uniform(5.0, 30.0)
            }
            
            headers = {"Authorization": f"Bearer {user.token}"}
            
            async with self.session.post(
                f"{self.base_url}/api/v1/tasks/submit",
                json=payload,
                headers=headers
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    user.learning_history.append({
                        "task_id": user.current_task["task_id"],
                        "answer": answer,
                        "result": data,
                        "timestamp": datetime.now().isoformat()
                    })
                    self.log_result("Submit Answer", True, f"Answer submitted, mastery: {data.get('mastery_update', {}).get('new_mastery', 'N/A')}", response_time)
                    return True
                else:
                    text = await response.text()
                    self.log_result("Submit Answer", False, f"Status {response.status}: {text}", response_time)
                    return False
                    
        except Exception as e:
            response_time = time.time() - start_time
            self.log_result("Submit Answer", False, f"Exception: {str(e)}", response_time)
            return False
    
    async def get_learning_history(self, user: UserSession) -> bool:
        """Test retrieving learning history"""
        start_time = time.time()
        
        try:
            headers = {"Authorization": f"Bearer {user.token}"}
            
            async with self.session.get(
                f"{self.base_url}/api/v1/tasks/history/{user.user_id}",
                headers=headers
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    self.log_result("Get Learning History", True, f"Retrieved {len(data)} history items", response_time)
                    return True
                else:
                    text = await response.text()
                    self.log_result("Get Learning History", False, f"Status {response.status}: {text}", response_time)
                    return False
                    
        except Exception as e:
            response_time = time.time() - start_time
            self.log_result("Get Learning History", False, f"Exception: {str(e)}", response_time)
            return False
    
    async def refresh_token(self, user: UserSession) -> bool:
        """Test token refresh"""
        start_time = time.time()
        
        try:
            if not user.refresh_token:
                self.log_result("Token Refresh", False, "No refresh token available", time.time() - start_time)
                return False
            
            payload = {"refresh_token": user.refresh_token}
            
            async with self.session.post(
                f"{self.base_url}/api/v1/auth/refresh",
                json=payload
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    user.token = data.get("access_token")
                    self.log_result("Token Refresh", True, "Token refreshed successfully", response_time)
                    return True
                else:
                    text = await response.text()
                    self.log_result("Token Refresh", False, f"Status {response.status}: {text}", response_time)
                    return False
                    
        except Exception as e:
            response_time = time.time() - start_time
            self.log_result("Token Refresh", False, f"Exception: {str(e)}", response_time)
            return False
    
    async def logout_user(self, user: UserSession) -> bool:
        """Test user logout"""
        start_time = time.time()
        
        try:
            headers = {"Authorization": f"Bearer {user.token}"}
            
            async with self.session.post(
                f"{self.base_url}/api/v1/auth/logout",
                headers=headers
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    user.token = None
                    user.refresh_token = None
                    self.log_result("User Logout", True, f"User {user.user_id} logged out", response_time)
                    return True
                else:
                    text = await response.text()
                    self.log_result("User Logout", False, f"Status {response.status}: {text}", response_time)
                    return False
                    
        except Exception as e:
            response_time = time.time() - start_time
            self.log_result("User Logout", False, f"Exception: {str(e)}", response_time)
            return False
    
    async def simulate_learning_session(self, user: UserSession, num_tasks: int = 5) -> bool:
        """Simulate a complete learning session"""
        print(f"\n=== Starting Learning Session for {user.user_id} ===")
        
        # Login
        if not await self.login_user(user):
            return False
        
        # Complete multiple tasks
        for i in range(num_tasks):
            print(f"\n--- Task {i+1}/{num_tasks} ---")
            
            # Get next task
            if not await self.get_next_task(user):
                continue
            
            # Submit answer
            await self.submit_answer(user)
            
            # Small delay to simulate real user behavior
            await asyncio.sleep(1)
        
        # Get learning history
        await self.get_learning_history(user)
        
        # Logout
        await self.logout_user(user)
        
        print(f"\n=== Learning Session Complete ===")
        return True
    
    async def test_returning_user(self, user: UserSession) -> bool:
        """Test returning user after some time"""
        print(f"\n=== Testing Returning User {user.user_id} ===")
        
        # Simulate time passing (token might expire)
        print("Simulating token expiration...")
        user.token = None  # Simulate expired token
        
        # Try to get task without valid token (should fail)
        success = await self.get_next_task(user)
        if success:
            self.log_result("Token Expiration Test", False, "Should have failed with expired token", 0)
            return False
        else:
            self.log_result("Token Expiration Test", True, "Correctly rejected expired token", 0)
        
        # Refresh token
        if not await self.refresh_token(user):
            # If refresh fails, try login again
            if not await self.login_user(user):
                return False
        
        # Continue learning
        return await self.simulate_learning_session(user, num_tasks=2)
    
    async def run_complete_lifecycle_test(self) -> Dict:
        """Run complete user lifecycle test"""
        print("=== Starting Complete User Lifecycle Test ===")
        
        # Create test user
        user = UserSession(
            user_id=f"test_user_{uuid.uuid4().hex[:8]}",
            email=f"test_{uuid.uuid4().hex[:8]}@example.com",
            password="TestPassword123!"
        )
        
        # 1. Registration
        await self.register_user(user)
        
        # 2. First learning session
        await self.simulate_learning_session(user, num_tasks=3)
        
        # 3. Returning user session
        await self.test_returning_user(user)
        
        # Generate report
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["success"])
        
        report = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": (passed_tests / total_tests) * 100 if total_tests > 0 else 0,
            "test_results": self.test_results,
            "user_id": user.user_id,
            "learning_history_count": len(user.learning_history)
        }
        
        print(f"\n=== Test Summary ===")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {report['success_rate']:.1f}%")
        
        return report


async def main():
    """Main test runner"""
    async with UserLifecycleTester() as tester:
        report = await tester.run_complete_lifecycle_test()
        
        # Save detailed report
        with open("user_lifecycle_test_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\nDetailed report saved to: user_lifecycle_test_report.json")
        
        return report["success_rate"] >= 80


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
