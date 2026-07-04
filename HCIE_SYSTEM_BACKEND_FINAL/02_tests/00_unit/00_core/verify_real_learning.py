#!/usr/bin/env python3
"""
Verify Real Learning - Test if actual learning is working or just fallback
"""

import requests
import json
import time
from datetime import datetime

class RealLearningVerifier:
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
    
    def test_fallback_detection(self):
        """Test if fallback is being triggered in normal flow"""
        start_time = time.time()
        try:
            # Submit multiple answers and check for fallback usage
            test_user = "fallback_test_user"
            fallback_count = 0
            
            for i, answer in enumerate(["85", "45", "90", "30", "75"]):
                payload = {
                    "user_id": test_user,
                    "task_id": f"test_task_{i}",
                    "node_id": f"concept_{i}",
                    "representation": "text",
                    "answer": answer,
                    "response_time": 10.0 + i
                }
                
                response = requests.post(
                    f"{self.base_url}/api/v1/tasks/submit",
                    json=payload,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("fallback_used"):
                        fallback_count += 1
                        print(f"  Fallback triggered for task {i}: {data.get('processing_error', 'No error info')}")
                else:
                    print(f"  Task {i} failed: {response.status_code}")
            
            response_time = time.time() - start_time
            
            if fallback_count == 0:
                self.log_result("Fallback Detection", True, f"No fallbacks triggered in 5 submissions", response_time)
                return True
            elif fallback_count <= 2:  # Some fallbacks acceptable for missing tasks
                self.log_result("Fallback Detection", True, f"Only {fallback_count} fallbacks (acceptable)", response_time)
                return True
            else:
                self.log_result("Fallback Detection", False, f"Too many fallbacks: {fallback_count}/5", response_time)
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_result("Fallback Detection", False, f"Exception: {str(e)}", response_time)
            return False
    
    def test_mastery_progression(self):
        """Test if mastery is actually changing (not just fake +/-0.05)"""
        start_time = time.time()
        try:
            test_user = "mastery_test_user"
            
            # Get initial mastery
            response = requests.get(f"{self.base_url}/api/v1/analytics/user/{test_user}/mastery", timeout=10)
            initial_mastery = {}
            
            if response.status_code == 200:
                data = response.json()
                initial_mastery = data.get("mastery", {})
            else:
                # Try alternative endpoint
                response = requests.get(f"{self.base_url}/api/v1/tasks/{test_user}/mastery", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    initial_mastery = data.get("mastery", {})
            
            # Submit several answers to the same concept
            concept_id = "test_concept"
            mastery_changes = []
            
            for i, answer in enumerate(["85", "90", "95"]):  # All correct answers
                payload = {
                    "user_id": test_user,
                    "task_id": f"mastery_task_{i}",
                    "node_id": concept_id,
                    "representation": "text",
                    "answer": answer,
                    "response_time": 10.0
                }
                
                # Get mastery before
                response = requests.get(f"{self.base_url}/api/v1/analytics/user/{test_user}/mastery", timeout=10)
                before_mastery = 0.5
                if response.status_code == 200:
                    data = response.json()
                    before_mastery = data.get("mastery", {}).get(concept_id, 0.5)
                
                # Submit answer
                submit_response = requests.post(
                    f"{self.base_url}/api/v1/tasks/submit",
                    json=payload,
                    timeout=10
                )
                
                if submit_response.status_code == 200:
                    submit_data = submit_response.json()
                    mastery_update = submit_data.get("mastery_update", {})
                    new_mastery = mastery_update.get("new_mastery", before_mastery)
                    change = new_mastery - before_mastery
                    mastery_changes.append(change)
                    
                    print(f"  Answer {i+1}: {before_mastery:.3f} -> {new_mastery:.3f} (change: {change:+.3f})")
                    
                    # Check if it's the fake +/-0.05 pattern
                    if abs(change - 0.05) < 0.001 or abs(change + 0.05) < 0.001:
                        print(f"    WARNING: Fake +/-0.05 pattern detected")
                else:
                    print(f"  Answer {i+1}: Submission failed")
                    mastery_changes.append(0)
            
            response_time = time.time() - start_time
            
            # Analyze mastery changes
            if not mastery_changes:
                self.log_result("Mastery Progression", False, "No mastery changes recorded", response_time)
                return False
            
            # Check for fake pattern
            fake_pattern_count = sum(1 for change in mastery_changes 
                                   if abs(change - 0.05) < 0.001 or abs(change + 0.05) < 0.001)
            
            if fake_pattern_count == len(mastery_changes):
                self.log_result("Mastery Progression", False, f"All changes are fake +/-0.05 pattern", response_time)
                return False
            elif fake_pattern_count > len(mastery_changes) * 0.5:
                self.log_result("Mastery Progression", False, f"Too many fake patterns: {fake_pattern_count}/{len(mastery_changes)}", response_time)
                return False
            else:
                self.log_result("Mastery Progression", True, f"Real mastery changes detected", response_time)
                return True
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_result("Mastery Progression", False, f"Exception: {str(e)}", response_time)
            return False
    
    def test_history_persistence(self):
        """Test if history is actually being saved and retrieved"""
        start_time = time.time()
        try:
            test_user = "history_test_user"
            
            # Submit several tasks
            task_count = 5
            for i in range(task_count):
                payload = {
                    "user_id": test_user,
                    "task_id": f"history_task_{i}",
                    "node_id": f"concept_{i}",
                    "representation": "text",
                    "answer": str(70 + i * 5),
                    "response_time": 10.0 + i
                }
                
                response = requests.post(
                    f"{self.base_url}/api/v1/tasks/submit",
                    json=payload,
                    timeout=10
                )
                
                if response.status_code != 200:
                    print(f"  Task {i} submission failed: {response.status_code}")
            
            # Wait a moment for processing
            time.sleep(1)
            
            # Check history
            response = requests.get(f"{self.base_url}/api/v1/tasks/history/{test_user}", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                history = data.get("history", [])
                total = data.get("total", len(history))
                
                if total >= task_count:
                    self.log_result("History Persistence", True, f"History working: {total}/{task_count} items saved", response_time)
                    return True
                elif total > 0:
                    self.log_result("History Persistence", True, f"Partial history: {total}/{task_count} items saved", response_time)
                    return True
                else:
                    self.log_result("History Persistence", False, f"No history saved: {total}/{task_count} items", response_time)
                    return False
            else:
                self.log_result("History Persistence", False, f"History endpoint failed: {response.status_code}", response_time)
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_result("History Persistence", False, f"Exception: {str(e)}", response_time)
            return False
    
    def test_redis_connectivity(self):
        """Test if Redis is actually being used for storage"""
        start_time = time.time()
        try:
            # Check if we can access Redis through the API
            response = requests.get(f"{self.base_url}/admin/services/status", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                redis_status = data.get("redis", {})
                
                if redis_status.get("status") == "healthy":
                    self.log_result("Redis Connectivity", True, "Redis is healthy and accessible", response_time)
                    return True
                else:
                    self.log_result("Redis Connectivity", False, f"Redis status: {redis_status.get('status')}", response_time)
                    return False
            else:
                self.log_result("Redis Connectivity", False, f"Admin endpoint failed: {response.status_code}", response_time)
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_result("Redis Connectivity", False, f"Exception: {str(e)}", response_time)
            return False
    
    def test_real_vs_fake_responses(self):
        """Distinguish between real learning and fake fallback responses"""
        start_time = time.time()
        try:
            test_user = "real_vs_fake_test"
            
            # Submit to a non-existent task (should trigger fallback)
            payload = {
                "user_id": test_user,
                "task_id": "definitely_nonexistent_task_12345",
                "node_id": "test_concept",
                "representation": "text",
                "answer": "85",
                "response_time": 15.0
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/tasks/submit",
                json=payload,
                timeout=10
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for fallback indicators
                fallback_indicators = [
                    data.get("fallback_used"),
                    data.get("status") == "partial_success",
                    data.get("processing_error") is not None
                ]
                
                if any(fallback_indicators):
                    self.log_result("Real vs Fake", True, f"Fallback properly detected: {fallback_indicators}", response_time)
                    return True
                else:
                    self.log_result("Real vs Fake", False, "Fallback not detected for non-existent task", response_time)
                    return False
            else:
                self.log_result("Real vs Fake", False, f"Submission failed: {response.status_code}", response_time)
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_result("Real vs Fake", False, f"Exception: {str(e)}", response_time)
            return False
    
    def run_verification_tests(self):
        """Run all real learning verification tests"""
        print("="*70)
        print("REAL LEARNING VERIFICATION - HCIE System")
        print("="*70)
        print("Testing if actual learning is working or just fallback...")
        print()
        
        # Run verification tests
        self.test_fallback_detection()
        self.test_mastery_progression()
        self.test_history_persistence()
        self.test_redis_connectivity()
        self.test_real_vs_fake_responses()
        
        # Generate summary
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["success"])
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print("\n" + "="*70)
        print("REAL LEARNING VERIFICATION SUMMARY")
        print("="*70)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Determine system reality
        critical_failures = []
        for result in self.results:
            if not result["success"] and any(keyword in result["test_name"] for keyword in ["Mastery", "History", "Fallback"]):
                critical_failures.append(result["test_name"])
        
        if critical_failures:
            print(f"\nCRITICAL ISSUES - System may be using FAKE learning:")
            for issue in critical_failures:
                print(f"  - {issue}")
            print(f"\nSTATUS: System is NOT ready for research/production")
        else:
            print(f"\nSTATUS: Real learning appears to be working")
        
        # Save results
        report = {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": total_tests - passed_tests,
                "success_rate": success_rate,
                "critical_failures": critical_failures,
                "timestamp": datetime.now().isoformat()
            },
            "results": self.results
        }
        
        with open("real_learning_verification_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\nDetailed report saved to: real_learning_verification_report.json")
        
        return success_rate >= 70, critical_failures

if __name__ == "__main__":
    verifier = RealLearningVerifier()
    success, issues = verifier.run_verification_tests()
    exit(0 if success else 1)
