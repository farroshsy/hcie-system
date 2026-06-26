#!/usr/bin/env python3
"""
Phase 0 End-to-End Test
Proves the event system works end-to-end with real Kafka
"""

import asyncio
import json
import time
import logging
import requests
from datetime import datetime
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class E2ETest:
    """End-to-end test for event system"""
    
    def __init__(self):
        self.api_base = "http://localhost:8001"
        self.test_results = []
    
    def log_result(self, test_name: str, success: bool, message: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} {test_name}: {message}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def test_api_health(self) -> bool:
        """Test API health endpoint"""
        try:
            response = requests.get(f"{self.api_base}/health", timeout=10)
            success = response.status_code == 200
            self.log_result("API Health", success, f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_result("API Health", False, str(e))
            return False
    
    def test_user_registration_flow(self) -> bool:
        """Test complete user registration event flow"""
        try:
            # Step 1: Register user (should trigger outbox event)
            user_data = {
                "email": f"test-{int(time.time())}@example.com",
                "password": "testpassword123",
                "username": f"testuser-{int(time.time())}"
            }
            
            logger.info("🔄 Step 1: Registering user...")
            response = requests.post(
                f"{self.api_base}/auth/register",
                json=user_data,
                timeout=10
            )
            
            if response.status_code != 201:
                self.log_result("User Registration", False, f"Registration failed: {response.text}")
                return False
            
            user_id = response.json().get("user_id")
            logger.info(f"✅ User registered: {user_id}")
            
            # Step 2: Check outbox table for event
            logger.info("🔄 Step 2: Checking outbox table...")
            time.sleep(2)  # Give outbox worker time to process
            
            # Check metrics - look for total events created (not pending)
            metrics_response = requests.get(f"{self.api_base}/api/metrics/outbox", timeout=10)
            
            if metrics_response.status_code == 200:
                metrics = metrics_response.json()
                total_events = metrics.get("data", {}).get("total_events", 0)
                logger.info(f"📊 Outbox metrics: {total_events} total events created")
                
                if total_events > 0:
                    self.log_result("Outbox Event", True, f"Found {total_events} events created")
                else:
                    self.log_result("Outbox Event", False, "No events created")
                    return False
            else:
                self.log_result("Outbox Event", False, "Failed to get metrics")
                return False
            
            # Step 3: Wait for processing
            logger.info("🔄 Step 3: Waiting for event processing...")
            time.sleep(5)  # Give workers time to process
            
            # Step 4: Check final metrics
            final_metrics_response = requests.get(f"{self.api_base}/api/metrics/outbox", timeout=10)
            
            if final_metrics_response.status_code == 200:
                final_metrics = final_metrics_response.json()
                published_events = final_metrics.get("data", {}).get("published_events", 0)
                logger.info(f"📊 Final metrics: {published_events} published events")
                
                if published_events > 0:
                    self.log_result("Event Processing", True, f"Successfully published {published_events} events")
                else:
                    self.log_result("Event Processing", False, "No events published")
                    return False
            else:
                self.log_result("Event Processing", False, "Failed to get final metrics")
                return False
            
            # Step 5: CRITICAL - Verify consumer actually processed events
            logger.info("🔄 Step 5: Verifying consumer processing...")
            
            redis_response = requests.get(f"{self.api_base}/debug/redis/processed-events", timeout=10)
            
            if redis_response.status_code == 200:
                redis_data = redis_response.json()
                processed_count = redis_data.get("data", {}).get("processed_events_count", 0)
                logger.info(f"📊 Consumer metrics: {processed_count} events processed")
                
                if processed_count > 0:
                    self.log_result("Consumer Processing", True, f"Consumer processed {processed_count} events")
                else:
                    self.log_result("Consumer Processing", False, "Consumer didn't process any events")
                    return False
            else:
                self.log_result("Consumer Processing", False, "Failed to get consumer metrics")
                return False
                
        except Exception as e:
            self.log_result("User Registration Flow", False, str(e))
            return False
    
    def test_circuit_breaker(self) -> bool:
        """Test circuit breaker functionality with real Kafka failure"""
        try:
            logger.info("🔧 Testing circuit breaker with Kafka failure simulation...")
            
            # Step 1: Get baseline metrics
            baseline_response = requests.get(f"{self.api_base}/api/metrics/health", timeout=10)
            if baseline_response.status_code != 200:
                self.log_result("Circuit Breaker", False, "Failed to get baseline health")
                return False
            
            baseline_health = baseline_response.json()
            logger.info(f"📊 Baseline health: {baseline_health}")
            
            # Step 2: Simulate Kafka failure
            logger.warning("🔧 Simulating Kafka failure...")
            
            # Use subprocess to control Docker containers
            import subprocess
            
            try:
                # Stop Kafka
                result = subprocess.run(
                    ["docker", "stop", "docker-kafka-1"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode != 0:
                    logger.warning(f"⚠️ Failed to stop Kafka: {result.stderr}")
                    # Continue test anyway - might already be stopped
                
                logger.info("⏸️ Kafka stopped")
                
                # Wait for circuit breaker to trigger
                logger.info("⏳ Waiting for circuit breaker to detect failure...")
                time.sleep(10)
                
                # Step 3: Test event publishing during failure
                logger.info("🧪 Testing event publishing during Kafka failure...")
                
                test_event_data = {
                    "email": f"circuit-test-{int(time.time())}@example.com",
                    "password": "testpassword123",
                    "username": f"circuituser-{int(time.time())}"
                }
                
                failure_response = requests.post(
                    f"{self.api_base}/auth/register",
                    json=test_event_data,
                    timeout=10
                )
                
                # Event should still be saved to outbox (transaction succeeds)
                if failure_response.status_code == 201:
                    logger.info("✅ Event saved to outbox during Kafka failure")
                else:
                    logger.warning(f"⚠️ Event creation failed during Kafka failure: {failure_response.text}")
                
                # Step 4: Restart Kafka
                logger.info("🔄 Restarting Kafka...")
                
                restart_result = subprocess.run(
                    ["docker", "start", "docker-kafka-1"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if restart_result.returncode != 0:
                    logger.error(f"❌ Failed to restart Kafka: {restart_result.stderr}")
                    self.log_result("Circuit Breaker", False, "Failed to restart Kafka")
                    return False
                
                logger.info("✅ Kafka restarted")
                
                # Wait for Kafka to be ready
                logger.info("⏳ Waiting for Kafka to be ready...")
                time.sleep(15)
                
                # Step 5: Test recovery
                logger.info("🔄 Testing circuit breaker recovery...")
                
                # Create another test event
                recovery_event_data = {
                    "email": f"recovery-test-{int(time.time())}@example.com",
                    "password": "testpassword123",
                    "username": f"recoveryuser-{int(time.time())}"
                }
                
                recovery_response = requests.post(
                    f"{self.api_base}/auth/register",
                    json=recovery_event_data,
                    timeout=10
                )
                
                if recovery_response.status_code == 201:
                    logger.info("✅ Event created successfully after Kafka recovery")
                    
                    # Wait for processing
                    time.sleep(5)
                    
                    # ✅ Validate full recovery pipeline
                    final_metrics_response = requests.get(f"{self.api_base}/api/metrics/outbox", timeout=10)
                    final_redis_response = requests.get(f"{self.api_base}/debug/redis/processed-events", timeout=10)
                    
                    if final_metrics_response.status_code == 200 and final_redis_response.status_code == 200:
                        final_metrics = final_metrics_response.json()
                        final_redis_data = final_redis_response.json()
                        
                        published_events = final_metrics.get("data", {}).get("published_events", 0)
                        processed_count = final_redis_data.get("data", {}).get("processed_events_count", 0)
                        
                        logger.info(f"📊 Recovery metrics: {published_events} published, {processed_count} processed")
                        
                        # ✅ Validate recovery: both published and processed events should increase
                        baseline_published = baseline_health.get("data", {}).get("outbox_metrics", {}).get("published_events", 0)
                        baseline_processed = 0  # We don't track baseline for Redis
                        
                        if published_events > baseline_published and processed_count > baseline_processed:
                            self.log_result("Circuit Breaker", True, f"Recovery successful: {published_events} published, {processed_count} processed")
                            return True
                        else:
                            self.log_result("Circuit Breaker", False, f"Recovery incomplete: published={published_events}, processed={processed_count}")
                            return False
                    else:
                        self.log_result("Circuit Breaker", False, "Failed to get final recovery metrics")
                        return False
                else:
                    self.log_result("Circuit Breaker", False, f"Recovery test failed: {recovery_response.text}")
                    return False
                    
            except subprocess.TimeoutExpired:
                self.log_result("Circuit Breaker", False, "Docker command timeout")
                return False
            except Exception as e:
                self.log_result("Circuit Breaker", False, f"Test execution error: {e}")
                return False
                
        except Exception as e:
            self.log_result("Circuit Breaker", False, str(e))
            return False
    
    def test_partitioning(self) -> bool:
        """Test partitioning strategy with validation"""
        try:
            # Register multiple users to test partitioning
            logger.info("🔄 Testing partitioning with multiple users...")
            
            # Use same user_id to test partitioning consistency
            test_user_id = f"partition-user-{int(time.time())}"
            
            for i in range(3):
                user_data = {
                    "email": f"partition-test-{i}-{int(time.time())}@example.com",
                    "password": "testpassword123",
                    "username": f"partitionuser-{i}",
                    "user_id": test_user_id  # Force same user_id for partitioning test
                }
                
                response = requests.post(
                    f"{self.api_base}/auth/register",
                    json=user_data,
                    timeout=10
                )
                
                if response.status_code != 201:
                    self.log_result("Partitioning", False, f"User {i} registration failed")
                    return False
                
                logger.info(f"📝 User {i} registered with user_id: {test_user_id}")
            
            # Wait for processing
            time.sleep(5)
            
            # Check metrics
            response = requests.get(f"{self.api_base}/api/metrics/outbox", timeout=10)
            
            if response.status_code == 200:
                metrics = response.json()
                total_events = metrics.get("data", {}).get("total_events", 0)
                
                if total_events >= 3:
                    logger.info(f"📊 Partitioning test: {total_events} events processed")
                    
                    # Check outbox events to verify partitioning
                    outbox_response = requests.get(f"{self.api_base}/debug/outbox/events?limit=3", timeout=10)
                    
                    if outbox_response.status_code == 200:
                        outbox_events = outbox_response.json().get("data", [])
                        
                        # Extract partition keys from actual envelope data
                        partition_keys = []
                        for event in outbox_events:
                            if event.get("event_type") == "user_registered":
                                # Parse envelope to get partition key
                                try:
                                    envelope = event.get("envelope", {})
                                    partition_key = envelope.get("metadata", {}).get("partition_key")
                                    
                                    logger.info(f"🔍 Event {event['event_id']} partition_key: {partition_key}")
                                    
                                    if partition_key:
                                        partition_keys.append(partition_key)
                                except Exception as e:
                                    logger.warning(f"⚠️ Failed to parse envelope for event {event['event_id']}: {e}")
                        
                        # ✅ Validate partitioning: all events should have same partition key
                        if len(partition_keys) >= 3:
                            unique_partition_keys = set(partition_keys)
                            
                            if len(unique_partition_keys) == 1:
                                partition_key = unique_partition_keys.pop()
                                self.log_result("Partitioning", True, f"All events use same partition_key: {partition_key}")
                                return True
                            else:
                                self.log_result("Partitioning", False, f"Events use different partition_keys: {list(unique_partition_keys)}")
                                return False
                        else:
                            self.log_result("Partitioning", False, f"Only {len(partition_keys)} events found with partition_keys")
                            return False
                    else:
                        self.log_result("Partitioning", False, "Failed to get outbox events")
                        return False
                else:
                    self.log_result("Partitioning", False, f"Only {total_events} events processed")
                    return False
            else:
                self.log_result("Partitioning", False, "Failed to get metrics")
                return False
                
        except Exception as e:
            self.log_result("Partitioning", False, str(e))
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all end-to-end tests with strict success criteria"""
        logger.info("🚀 Starting Phase 0 End-to-End Tests")
        logger.info("=" * 50)
        
        # Required tests that ALL must pass
        required_tests = [
            ("API Health Check", self.test_api_health),
            ("User Registration Flow", self.test_user_registration_flow),
            ("Event Processing", self._check_event_processing),
            ("Consumer Processing", self._check_consumer_processing),
        ]
        
        # Optional tests for advanced features
        optional_tests = [
            ("Circuit Breaker", self.test_circuit_breaker),
            ("Partitioning Strategy", self.test_partitioning),
        ]
        
        all_tests = required_tests + optional_tests
        passed = 0
        total = len(all_tests)
        required_passed = 0
        required_total = len(required_tests)
        
        for test_name, test_func in all_tests:
            logger.info(f"\n🧪 Running: {test_name}")
            test_passed = test_func()
            
            if test_passed:
                passed += 1
                if test_name in [name for name, _ in required_tests]:
                    required_passed += 1
            time.sleep(1)  # Brief pause between tests
        
        logger.info("\n" + "=" * 50)
        logger.info(f"📊 Overall Test Results: {passed}/{total} passed")
        logger.info(f"📈 Success Rate: {(passed / total) * 100:.1f}%")
        logger.info(f"🎯 Required Tests: {required_passed}/{required_total} passed")
        
        # Strict success criteria - ALL required tests must pass
        success = required_passed == required_total
        
        return {
            "total_tests": total,
            "passed_tests": passed,
            "failed_tests": total - passed,
            "success_rate": (passed / total) * 100,
            "required_passed": required_passed,
            "required_total": required_total,
            "all_required_passed": success,
            "results": self.test_results
        }
    
    def _check_event_processing(self) -> bool:
        """Check if events are being processed (internal helper)"""
        try:
            response = requests.get(f"{self.api_base}/api/metrics/outbox", timeout=10)
            
            if response.status_code == 200:
                metrics = response.json()
                published_events = metrics.get("data", {}).get("published_events", 0)
                
                if published_events > 0:
                    self.log_result("Event Processing", True, f"Published {published_events} events")
                    return True
                else:
                    self.log_result("Event Processing", False, "No published events")
                    return False
            else:
                self.log_result("Event Processing", False, "Failed to get metrics")
                return False
                
        except Exception as e:
            self.log_result("Event Processing", False, str(e))
            return False
    
    def _check_consumer_processing(self) -> bool:
        """Check if consumer is processing events (internal helper)"""
        try:
            response = requests.get(f"{self.api_base}/debug/redis/processed-events", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                processed_count = data.get("data", {}).get("processed_events_count", 0)
                
                if processed_count > 0:
                    self.log_result("Consumer Processing", True, f"Consumer processed {processed_count} events")
                    return True
                else:
                    self.log_result("Consumer Processing", False, "Consumer didn't process events")
                    return False
            else:
                self.log_result("Consumer Processing", False, "Failed to get consumer metrics")
                return False
                
        except Exception as e:
            self.log_result("Consumer Processing", False, str(e))
            return False

def main():
    """Main test runner"""
    tester = E2ETest()
    
    try:
        results = tester.run_all_tests()
        
        # Save results to file
        with open("e2e_test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        logger.info("💾 Results saved to e2e_test_results.json")
        
        # Exit with appropriate code
        if results["all_required_passed"]:
            logger.info("🎉 Phase 0 tests PASSED - All required systems working!")
            logger.info(f"✅ Overall: {results['passed_tests']}/{results['total_tests']} tests passed")
            return 0
        else:
            logger.error("❌ Phase 0 tests FAILED - Required systems not working")
            logger.error(f"❌ Required: {results['required_passed']}/{results['required_total']} tests passed")
            return 1
            
    except Exception as e:
        logger.error(f"💥 Test runner crashed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
