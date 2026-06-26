#!/usr/bin/env python3
"""
Quick Health Test - Tests actual working endpoints
"""

import requests
import json
import time
from datetime import datetime

class QuickHealthTest:
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
        status = "PASS" if success else "FAIL"
        print(f"[{status}] {test_name}: {details} ({response_time:.2f}s)")
    
    def test_health_endpoint(self):
        """Test basic health endpoint"""
        start_time = time.time()
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                services = data.get("services", {})
                all_healthy = all(services.values())
                
                if all_healthy:
                    self.log_result("Health Check", True, f"All services healthy: {list(services.keys())}", response_time)
                    return True
                else:
                    unhealthy = [k for k, v in services.items() if not v]
                    self.log_result("Health Check", False, f"Unhealthy services: {unhealthy}", response_time)
                    return False
            else:
                self.log_result("Health Check", False, f"Status {response.status_code}", response_time)
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_result("Health Check", False, f"Exception: {str(e)}", response_time)
            return False
    
    def test_task_generation(self):
        """Test task generation endpoint"""
        start_time = time.time()
        try:
            test_user = "health_test_user"
            response = requests.get(f"{self.base_url}/api/v1/tasks/{test_user}", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["user_id", "task_id", "node_id", "question", "difficulty"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    self.log_result("Task Generation", True, f"Task {data.get('task_id')} generated", response_time)
                    return True, data
                else:
                    self.log_result("Task Generation", False, f"Missing fields: {missing_fields}", response_time)
                    return False, None
            else:
                self.log_result("Task Generation", False, f"Status {response.status_code}", response_time)
                return False, None
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_result("Task Generation", False, f"Exception: {str(e)}", response_time)
            return False, None
    
    def test_task_submission(self, task_data):
        """Test task submission endpoint"""
        if not task_data:
            self.log_result("Task Submission", False, "No task data to submit", 0)
            return False
        
        start_time = time.time()
        try:
            payload = {
                "user_id": task_data["user_id"],
                "task_id": task_data["task_id"],
                "node_id": task_data["node_id"],
                "representation": task_data.get("representation", "text"),
                "answer": "85",  # Test answer
                "response_time": 15.5
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/tasks/submit",
                json=payload,
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                self.log_result("Task Submission", True, f"Task submitted successfully", response_time)
                return True
            else:
                text = response.text
                self.log_result("Task Submission", False, f"Status {response.status_code}: {text[:100]}", response_time)
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_result("Task Submission", False, f"Exception: {str(e)}", response_time)
            return False
    
    def test_task_history(self):
        """Test task history endpoint"""
        start_time = time.time()
        try:
            test_user = "health_test_user"
            response = requests.get(f"{self.base_url}/api/v1/tasks/history/{test_user}", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                history_count = len(data.get("history", []))
                self.log_result("Task History", True, f"Retrieved {history_count} history items", response_time)
                return True
            else:
                self.log_result("Task History", False, f"Status {response.status_code}", response_time)
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_result("Task History", False, f"Exception: {str(e)}", response_time)
            return False
    
    def test_admin_services(self):
        """Test admin services endpoint"""
        start_time = time.time()
        try:
            response = requests.get(f"{self.base_url}/admin/services/status", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                services = list(data.keys())
                self.log_result("Admin Services", True, f"Retrieved {len(services)} services", response_time)
                return True
            else:
                self.log_result("Admin Services", False, f"Status {response.status_code}", response_time)
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_result("Admin Services", False, f"Exception: {str(e)}", response_time)
            return False
    
    def test_admin_interaction_creation(self):
        """Test admin interaction creation"""
        start_time = time.time()
        try:
            payload = {
                "user_id": "admin_test_user",
                "concept_id": "test_concept",
                "representation": "text"
            }
            
            response = requests.post(
                f"{self.base_url}/admin/admin/interactions/create",
                json=payload,
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                self.log_result("Admin Interaction Creation", True, "Interaction created successfully", response_time)
                return True
            else:
                text = response.text
                self.log_result("Admin Interaction Creation", False, f"Status {response.status_code}: {text[:100]}", response_time)
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_result("Admin Interaction Creation", False, f"Exception: {str(e)}", response_time)
            return False
    
    def run_quick_tests(self):
        """Run all quick health tests"""
        print("="*60)
        print("QUICK HEALTH TEST - HCIE RealSystem Backend V2")
        print("="*60)
        
        # Test basic health
        health_ok = self.test_health_endpoint()
        if not health_ok:
            print("CRITICAL: Health check failed - stopping tests")
            return False
        
        # Test task generation
        task_success, task_data = self.test_task_generation()
        
        # Test task submission (only if task generation worked)
        if task_success:
            self.test_task_submission(task_data)
        
        # Test task history
        self.test_task_history()
        
        # Test admin endpoints
        self.test_admin_services()
        self.test_admin_interaction_creation()
        
        # Generate summary
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["success"])
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print("\n" + "="*60)
        print("QUICK TEST SUMMARY")
        print("="*60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Save results
        report = {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": total_tests - passed_tests,
                "success_rate": success_rate,
                "timestamp": datetime.now().isoformat()
            },
            "results": self.results
        }
        
        with open("quick_health_test_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\nDetailed report saved to: quick_health_test_report.json")
        
        return success_rate >= 70

if __name__ == "__main__":
    tester = QuickHealthTest()
    success = tester.run_quick_tests()
    exit(0 if success else 1)
