#!/usr/bin/env python3
"""
Test CT Learning - Test with actual CT tasks instead of EdNet
"""

import requests
import json
import time
from datetime import datetime

class CTLearningTester:
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
    
    def test_ct_task_generation(self):
        """Test task generation with CT mode"""
        start_time = time.time()
        try:
            # Test with CT mode explicitly
            test_user = "ct_test_user"
            response = requests.get(f"{self.base_url}/api/v1/tasks/{test_user}?mode=ct", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                task_id = data.get("task_id", "")
                concept_id = data.get("node_id", "")
                
                # Check if it's a CT task
                if "ct_" in concept_id or "ct_" in task_id:
                    self.log_result("CT Task Generation", True, f"CT task generated: {concept_id}", response_time)
                    return True, data
                elif "fallback" in task_id or "EdNet" in task_id:
                    self.log_result("CT Task Generation", False, f"Still getting fallback/EdNet: {task_id}", response_time)
                    return False, data
                else:
                    self.log_result("CT Task Generation", False, f"Unknown task type: {task_id}", response_time)
                    return False, data
            else:
                self.log_result("CT Task Generation", False, f"Status {response.status_code}", response_time)
                return False, None
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_result("CT Task Generation", False, f"Exception: {str(e)}", response_time)
            return False, None
    
    def test_ct_task_submission(self, task_data):
        """Test task submission with CT task"""
        if not task_data:
            self.log_result("CT Task Submission", False, "No task data", 0)
            return False
        
        start_time = time.time()
        try:
            payload = {
                "user_id": "ct_test_user",
                "task_id": task_data["task_id"],
                "node_id": task_data["node_id"],
                "representation": task_data.get("representation", "text"),
                "answer": "No validation",  # Correct answer for first CT problem
                "response_time": 15.0,
                "mode": "ct"
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/tasks/submit",
                json=payload,
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if fallback was used
                if data.get("fallback_used"):
                    self.log_result("CT Task Submission", False, f"Fallback used: {data.get('processing_error')}", response_time)
                    return False
                else:
                    self.log_result("CT Task Submission", True, f"Real CT submission processed", response_time)
                    return True
            else:
                self.log_result("CT Task Submission", False, f"Status {response.status_code}: {response.text[:100]}", response_time)
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_result("CT Task Submission", False, f"Exception: {str(e)}", response_time)
            return False
    
    def test_ct_mastery_updates(self):
        """Test mastery updates with CT concepts"""
        start_time = time.time()
        try:
            test_user = "ct_mastery_user"
            
            # Submit multiple CT answers
            ct_answers = [
                ("No validation", "ct_problem_identification"),  # Correct
                ("Input mismatch", "ct_problem_identification"),  # Correct
                ("Wrong condition", "ct_problem_identification"), # Correct
            ]
            
            mastery_changes = []
            
            for i, (answer, expected_concept) in enumerate(ct_answers):
                # Get task
                task_response = requests.get(f"{self.base_url}/api/v1/tasks/{test_user}?mode=ct", timeout=10)
                if task_response.status_code != 200:
                    continue
                
                task_data = task_response.json()
                
                # Submit answer
                payload = {
                    "user_id": test_user,
                    "task_id": task_data["task_id"],
                    "node_id": task_data["node_id"],
                    "representation": "text",
                    "answer": answer,
                    "response_time": 10.0 + i,
                    "mode": "ct"
                }
                
                submit_response = requests.post(
                    f"{self.base_url}/api/v1/tasks/submit",
                    json=payload,
                    timeout=10
                )
                
                if submit_response.status_code == 200:
                    submit_data = submit_response.json()
                    mastery_update = submit_data.get("mastery_update", {})
                    change = mastery_update.get("improvement", 0)
                    mastery_changes.append(change)
                    
                    print(f"  CT Answer {i+1}: {answer} -> mastery change: {change:+.3f}")
                    
                    # Check for fake pattern
                    if abs(change - 0.05) < 0.001:
                        print(f"    WARNING: Fake +/-0.05 pattern")
                else:
                    print(f"  CT Answer {i+1}: Submission failed")
                    mastery_changes.append(0)
            
            response_time = time.time() - start_time
            
            if not mastery_changes:
                self.log_result("CT Mastery Updates", False, "No mastery changes recorded", response_time)
                return False
            
            # Check if changes are realistic
            fake_pattern_count = sum(1 for change in mastery_changes 
                                   if abs(change - 0.05) < 0.001 or abs(change + 0.05) < 0.001)
            
            if fake_pattern_count == len(mastery_changes):
                self.log_result("CT Mastery Updates", False, f"All fake +/-0.05 pattern", response_time)
                return False
            else:
                self.log_result("CT Mastery Updates", True, f"Real CT mastery changes detected", response_time)
                return True
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_result("CT Mastery Updates", False, f"Exception: {str(e)}", response_time)
            return False
    
    def test_ct_history_persistence(self):
        """Test CT task history persistence"""
        start_time = time.time()
        try:
            test_user = "ct_history_user"
            
            # Submit CT tasks
            for i in range(3):
                task_response = requests.get(f"{self.base_url}/api/v1/tasks/{test_user}?mode=ct", timeout=10)
                if task_response.status_code != 200:
                    continue
                
                task_data = task_response.json()
                
                payload = {
                    "user_id": test_user,
                    "task_id": task_data["task_id"],
                    "node_id": task_data["node_id"],
                    "representation": "text",
                    "answer": "No validation",  # Use a correct answer
                    "response_time": 10.0 + i,
                    "mode": "ct"
                }
                
                requests.post(f"{self.base_url}/api/v1/tasks/submit", json=payload, timeout=10)
            
            # Check history
            time.sleep(1)  # Wait for processing
            response = requests.get(f"{self.base_url}/api/v1/tasks/history/{test_user}", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                history = data.get("history", [])
                total = data.get("total", len(history))
                
                if total >= 3:
                    self.log_result("CT History Persistence", True, f"CT history working: {total} items", response_time)
                    return True
                elif total > 0:
                    self.log_result("CT History Persistence", True, f"Partial CT history: {total} items", response_time)
                    return True
                else:
                    self.log_result("CT History Persistence", False, f"No CT history saved: {total} items", response_time)
                    return False
            else:
                self.log_result("CT History Persistence", False, f"History endpoint failed: {response.status_code}", response_time)
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_result("CT History Persistence", False, f"Exception: {str(e)}", response_time)
            return False
    
    def run_ct_tests(self):
        """Run CT-specific learning tests"""
        print("="*70)
        print("CT LEARNING TESTS - Real Computational Thinking Tasks")
        print("="*70)
        print("Testing with actual CT tasks instead of EdNet fallbacks...")
        print()
        
        # Test CT task generation
        success, task_data = self.test_ct_task_generation()
        
        if success:
            # Test CT task submission
            self.test_ct_task_submission(task_data)
        
        # Test CT mastery updates
        self.test_ct_mastery_updates()
        
        # Test CT history persistence
        self.test_ct_history_persistence()
        
        # Generate summary
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["success"])
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print("\n" + "="*70)
        print("CT LEARNING TEST SUMMARY")
        print("="*70)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Determine if CT learning is working
        if success_rate >= 75:
            print(f"\nSTATUS: CT Learning appears to be working!")
        else:
            print(f"\nSTATUS: CT Learning still has issues")
        
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
        
        with open("ct_learning_test_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\nDetailed report saved to: ct_learning_test_report.json")
        
        return success_rate >= 75

if __name__ == "__main__":
    tester = CTLearningTester()
    success = tester.run_ct_tests()
    exit(0 if success else 1)
