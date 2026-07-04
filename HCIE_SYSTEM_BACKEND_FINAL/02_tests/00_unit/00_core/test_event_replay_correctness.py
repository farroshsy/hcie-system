#!/usr/bin/env python3
"""
🚀 EVENT REPLAY SAFETY TEST - Phase 10
Validates exactly-once semantics with event replay in the new architecture
"""

import os
import sys
import json
import time
import logging
from typing import Dict, Any, List

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.learning.unified_brain import UnifiedLearningBrain
from app.repositories.learning_state_repository import LearningStateRepository
from storage.redis_store.redis_store import RedisFeatureStore
from storage.postgres_store.interaction_store import PostgresInteractionStore
from app.infrastructure.outbox.outbox_pattern import OutboxPattern, OutboxEvent
from app.infrastructure.kafka.kafka_factory import KafkaFactory, DefaultKafkaProducerFactory
from app.infrastructure.messaging.event_bus import KafkaEventBus

logger = logging.getLogger(__name__)

class EventReplayCorrectnessTest:
    """
    🚀 Comprehensive test for event replay safety
    Validates the entire integrated architecture
    """
    
    def __init__(self):
        self.test_results = []
        self.redis_store = None
        self.postgres_store = None
        self.learning_state_repo = None
        self.unified_brain = None
        self.outbox = None
        
    def setup_test_environment(self) -> bool:
        """Setup test environment with all components"""
        try:
            logger.info("🔧 Setting up test environment...")
            
            # Initialize Redis
            self.redis_store = RedisFeatureStore()
            logger.info("✅ Redis store initialized")
            
            # Initialize Postgres and repository
            self.postgres_store = PostgresInteractionStore()
            self.learning_state_repo = LearningStateRepository(
                postgres_store=self.postgres_store,
                redis_store=self.redis_store
            )
            logger.info("✅ Postgres learning state repository initialized")
            
            # Initialize outbox (for derived events)
            try:
                kafka_factory = KafkaFactory(None, producer_factory=DefaultKafkaProducerFactory())
                kafka_producer = kafka_factory.create_producer()
                event_bus = KafkaEventBus(kafka_producer)
                self.outbox = OutboxPattern(self.postgres_store, event_bus)
                logger.info("✅ Outbox pattern initialized")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize outbox: {e}")
                self.outbox = None
            
            # Initialize UnifiedBrain with new architecture
            self.unified_brain = UnifiedLearningBrain(
                system_mode="jt",
                event_bus=None,  # Don't use direct event bus
                outbox=self.outbox  # Use outbox for atomic publishing
            )
            logger.info("✅ UnifiedBrain initialized with new architecture")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to setup test environment: {e}")
            return False
    
    def cleanup_test_environment(self) -> bool:
        """Cleanup test environment"""
        try:
            # Clean up test data
            test_user_id = "replay_test_user"
            test_concept = "replay_test_concept"
            
            # Delete from Postgres
            if self.learning_state_repo:
                self.learning_state_repo.delete_state(test_user_id, test_concept)
            
            # Clean up Redis
            if self.redis_store:
                # Clean up idempotency keys
                test_event_id = "replay_test_event_001"
                keys_to_delete = [
                    f"processed:{test_event_id}",
                    f"result:{test_event_id}",
                    f"hash:{test_event_id}",
                    f"lock:{test_event_id}"
                ]
                for key in keys_to_delete:
                    try:
                        self.redis_store.delete_value(key)
                    except:
                        pass
            
            logger.info("✅ Test environment cleaned up")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to cleanup test environment: {e}")
            return False
    
    def test_event_replay_safety(self) -> bool:
        """
        🚀 TEST: Event replay safety with new architecture
        Validates exactly-once semantics even with replay
        """
        try:
            logger.info("🧪 Testing event replay safety...")
            
            # Test data
            test_user_id = "replay_test_user"
            test_concept = "replay_test_concept"
            test_event_id = "replay_test_event_001"
            
            # Create test event
            test_event = {
                "event_id": test_event_id,
                "user_id": test_user_id,
                "concept": test_concept,
                "interaction": {
                    "correct": True,
                    "response_time": 5.0
                },
                "timestamp": time.time(),
                "source": "replay_test"
            }
            
            # 🚀 FIRST PROCESSING
            logger.info("📥 First processing of event...")
            result1 = self.unified_brain.process_kafka_event(test_event)
            
            # Validate first result
            assert result1.mastery > 0, f"Expected positive mastery, got {result1.mastery}"
            assert result1.event_id == test_event_id, f"Expected event_id {test_event_id}, got {result1.event_id}"
            logger.info(f"✅ First processing: mastery={result1.mastery:.6f}")
            
            # 🔄 REPLAY THE SAME EVENT
            logger.info("🔄 Replaying the same event...")
            result2 = self.unified_brain.process_kafka_event(test_event)
            
            # Validate replay result (should be identical)
            assert result2.mastery == result1.mastery, f"Replay mastery mismatch: {result2.mastery} != {result1.mastery}"
            assert result2.event_id == result1.event_id, f"Replay event_id mismatch: {result2.event_id} != {result1.event_id}"
            logger.info(f"✅ Replay processing: mastery={result2.mastery:.6f} (identical)")
            
            # 🔄 THIRD REPLAY (stress test)
            logger.info("🔄 Third replay (stress test)...")
            result3 = self.unified_brain.process_kafka_event(test_event)
            
            # Validate third replay (should still be identical)
            assert result3.mastery == result1.mastery, f"Third replay mastery mismatch: {result3.mastery} != {result1.mastery}"
            logger.info(f"✅ Third replay: mastery={result3.mastery:.6f} (still identical)")
            
            # 🔍 VERIFY POSTGRES STATE CONSISTENCY
            logger.info("🔍 Verifying Postgres state consistency...")
            saved_state = self.learning_state_repo.get_state(test_user_id, test_concept)
            
            assert saved_state is not None, "State not found in Postgres"
            assert saved_state["mastery"] == result1.mastery, f"Postgres mastery mismatch: {saved_state['mastery']} != {result1.mastery}"
            logger.info(f"✅ Postgres state consistent: mastery={saved_state['mastery']:.6f}")
            
            # 🔍 VERIFY REDIS CACHE CONSISTENCY
            logger.info("🔍 Verifying Redis cache consistency...")
            cache_key = f"learning_state:{test_user_id}:{test_concept}"
            cached_data = self.redis_store.get_value(cache_key)
            
            if cached_data:
                cached_state = json.loads(cached_data)
                assert cached_state["mastery"] == result1.mastery, f"Redis cache mastery mismatch: {cached_state['mastery']} != {result1.mastery}"
                logger.info(f"✅ Redis cache consistent: mastery={cached_state['mastery']:.6f}")
            else:
                logger.warning("⚠️ Redis cache not found (may be expected)")
            
            # 🎯 TEST DIFFERENT EVENT (should create new state)
            logger.info("🎯 Testing different event (should create new state)...")
            different_event = test_event.copy()
            different_event["event_id"] = "replay_test_event_002"
            different_event["interaction"]["correct"] = False
            
            result4 = self.unified_brain.process_kafka_event(different_event)
            
            # Should have different mastery (incorrect answer)
            assert result4.mastery != result1.mastery, "Different event should produce different mastery"
            logger.info(f"✅ Different event processed: mastery={result4.mastery:.6f} (different as expected)")
            
            self.log_result("Event Replay Safety", True, "All replay tests passed - exactly-once semantics maintained")
            return True
            
        except Exception as e:
            logger.error(f"❌ Event replay safety test failed: {e}")
            self.log_result("Event Replay Safety", False, f"Test failed: {e}")
            return False
    
    def test_atomic_transaction_boundary(self) -> bool:
        """
        🚀 TEST: Atomic transaction boundary validation
        Ensures all operations happen in single transaction
        """
        try:
            logger.info("🧪 Testing atomic transaction boundary...")
            
            # Test data
            test_user_id = "atomic_test_user"
            test_concept = "atomic_test_concept"
            test_event_id = "atomic_test_event_001"
            
            # Create test event
            test_event = {
                "event_id": test_event_id,
                "user_id": test_user_id,
                "concept": test_concept,
                "interaction": {
                    "correct": True,
                    "response_time": 3.0
                },
                "timestamp": time.time(),
                "source": "atomic_test"
            }
            
            # Process event (should be atomic)
            result = self.unified_brain.process_kafka_event(test_event)
            
            # Verify atomicity: both Postgres and Redis should be updated
            postgres_state = self.learning_state_repo.get_state(test_user_id, test_concept)
            redis_cache = self.redis_store.get_value(f"learning_state:{test_user_id}:{test_concept}")
            
            assert postgres_state is not None, "Postgres state should be updated"
            assert redis_cache is not None, "Redis cache should be updated"
            
            # Verify consistency
            postgres_mastery = postgres_state["mastery"]
            redis_mastery = json.loads(redis_cache)["mastery"]
            
            assert postgres_mastery == redis_mastery, f"Atomicity violation: Postgres={postgres_mastery}, Redis={redis_mastery}"
            assert postgres_mastery == result.mastery, f"Result mismatch: result={result.mastery}, Postgres={postgres_mastery}"
            
            logger.info(f"✅ Atomic transaction validated: mastery={postgres_mastery:.6f}")
            
            self.log_result("Atomic Transaction Boundary", True, "All operations in single transaction")
            return True
            
        except Exception as e:
            logger.error(f"❌ Atomic transaction boundary test failed: {e}")
            self.log_result("Atomic Transaction Boundary", False, f"Test failed: {e}")
            return False
    
    def test_source_of_truth_priority(self) -> bool:
        """
        🚀 TEST: Source of truth priority (Postgres over Redis)
        Ensures Postgres is always the source of truth
        """
        try:
            logger.info("🧪 Testing source of truth priority...")
            
            # Test data
            test_user_id = "source_test_user"
            test_concept = "source_test_concept"
            test_event_id = "source_test_event_001"
            
            # Create test event
            test_event = {
                "event_id": test_event_id,
                "user_id": test_user_id,
                "concept": test_concept,
                "interaction": {
                    "correct": True,
                    "response_time": 4.0
                },
                "timestamp": time.time(),
                "source": "source_test"
            }
            
            # Process event
            result = self.unified_brain.process_kafka_event(test_event)
            
            # Get state from both sources
            postgres_state = self.learning_state_repo.get_state(test_user_id, test_concept)
            redis_cache = self.redis_store.get_value(f"learning_state:{test_user_id}:{test_concept}")
            
            # Verify Postgres is source of truth
            assert postgres_state is not None, "Postgres should have state"
            assert postgres_state["mastery"] == result.mastery, "Postgres should match result"
            
            # Corrupt Redis cache (simulate inconsistency)
            if redis_cache:
                corrupted_data = json.loads(redis_cache)
                corrupted_data["mastery"] = 0.999  # Wrong value
                self.redis_store.set_value(f"learning_state:{test_user_id}:{test_concept}", json.dumps(corrupted_data))
                logger.info("🔥 Simulated Redis cache corruption")
            
            # Read state again (should return Postgres data, not corrupted Redis)
            fresh_state = self.learning_state_repo.get_state(test_user_id, test_concept)
            
            # Should return correct Postgres data, not corrupted Redis
            assert fresh_state["mastery"] == result.mastery, f"Should return Postgres data: {fresh_state['mastery']} != {result.mastery}"
            logger.info(f"✅ Source of truth validated: Postgres={fresh_state['mastery']:.6f} (correct)")
            
            self.log_result("Source of Truth Priority", True, "Postgres correctly prioritized over Redis")
            return True
            
        except Exception as e:
            logger.error(f"❌ Source of truth priority test failed: {e}")
            self.log_result("Source of Truth Priority", False, f"Test failed: {e}")
            return False
    
    def log_result(self, test_name: str, success: bool, message: str):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": time.time()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status}: {test_name} - {message}")
    
    def run_all_tests(self) -> bool:
        """Run all replay safety tests"""
        logger.info("🚀 Starting Event Replay Correctness Tests...")
        
        if not self.setup_test_environment():
            logger.error("❌ Failed to setup test environment")
            return False
        
        try:
            # Run all tests
            tests = [
                self.test_event_replay_safety,
                self.test_atomic_transaction_boundary,
                self.test_source_of_truth_priority
            ]
            
            passed = 0
            total = len(tests)
            
            for test in tests:
                if test():
                    passed += 1
                time.sleep(0.1)  # Small delay between tests
            
            # Summary
            logger.info(f"📊 Test Results: {passed}/{total} tests passed")
            
            for result in self.test_results:
                status = "✅" if result["success"] else "❌"
                logger.info(f"{status} {result['test']}: {result['message']}")
            
            success = passed == total
            if success:
                logger.info("🎉 All Event Replay Correctness Tests PASSED!")
            else:
                logger.error(f"❌ {total - passed} tests failed")
            
            return success
            
        finally:
            self.cleanup_test_environment()

def main():
    """Main test runner"""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run tests
    test = EventReplayCorrectnessTest()
    success = test.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
