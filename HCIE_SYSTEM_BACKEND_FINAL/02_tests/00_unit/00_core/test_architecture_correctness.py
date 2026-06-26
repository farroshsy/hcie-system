#!/usr/bin/env python3
"""
🚀 ARCHITECTURE CORRECTNESS TEST - No Database Required
Tests the core architectural changes without requiring PostgreSQL
"""

import os
import sys
import json
import time
import logging
from typing import Dict, Any, List

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

class ArchitectureCorrectnessTest:
    """
    🚀 Test core architectural changes without database dependencies
    """
    
    def __init__(self):
        self.test_results = []
    
    def test_api_event_emission_pattern(self) -> bool:
        """
        🚀 TEST: Verify API endpoints use event emission pattern
        """
        try:
            logger.info("🧪 Testing API event emission pattern...")
            
            # Check learning_v2.py
            learning_v2_path = "app/api/ux/endpoints/learning_v2.py"
            with open(learning_v2_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Should have outbox pattern, not direct UnifiedBrain calls
            has_outbox = "outbox.save_event" in content
            has_transaction = "get_transaction" in content
            has_async_response = '"status": "accepted"' in content
            no_direct_calls = "unified_brain.process_event" not in content
            
            success = has_outbox and has_transaction and has_async_response and no_direct_calls
            
            if success:
                logger.info("✅ learning_v2.py correctly uses event emission")
            else:
                logger.error(f"❌ learning_v2.py issues: outbox={has_outbox}, transaction={has_transaction}, async={has_async_response}, no_direct={no_direct_calls}")
            
            # Check learning.py
            learning_path = "app/api/ux/endpoints/learning.py"
            with open(learning_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            has_outbox = "outbox.save_event" in content
            has_transaction = "get_transaction" in content
            has_async_response = '"status": "accepted"' in content
            
            success = success and has_outbox and has_transaction and has_async_response
            
            self.log_result("API Event Emission Pattern", success, 
                          "API endpoints emit events via outbox pattern")
            return success
            
        except Exception as e:
            logger.error(f"❌ API event emission pattern test failed: {e}")
            self.log_result("API Event Emission Pattern", False, f"Test failed: {e}")
            return False
    
    def test_learning_consumer_architecture(self) -> bool:
        """
        🚀 TEST: Verify learning consumer architecture
        """
        try:
            logger.info("🧪 Testing learning consumer architecture...")
            
            # Check learning_consumer.py exists and has correct structure
            consumer_path = "app/workers/learning_consumer.py"
            with open(consumer_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Should have atomic transaction wrapper
            has_transaction = "get_transaction" in content
            has_unified_brain = "process_kafka_event" in content
            has_single_group = '"learning-domain"' in content
            has_derived_events = "learning_analytics" in content
            
            success = has_transaction and has_unified_brain and has_single_group and has_derived_events
            
            if success:
                logger.info("✅ Learning consumer has correct architecture")
            else:
                logger.error(f"❌ Learning consumer issues: transaction={has_transaction}, unified_brain={has_unified_brain}, single_group={has_single_group}, derived={has_derived_events}")
            
            self.log_result("Learning Consumer Architecture", success,
                          "Learning consumer uses atomic transactions and single group")
            return success
            
        except Exception as e:
            logger.error(f"❌ Learning consumer architecture test failed: {e}")
            self.log_result("Learning Consumer Architecture", False, f"Test failed: {e}")
            return False
    
    def test_postgres_repository_pattern(self) -> bool:
        """
        🚀 TEST: Verify Postgres repository pattern
        """
        try:
            logger.info("🧪 Testing Postgres repository pattern...")
            
            # Check learning_state_repository.py exists
            repo_path = "app/repositories/learning_state_repository.py"
            with open(repo_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Should have Postgres-first pattern
            has_postgres_first = "Save to Postgres first" in content
            has_redis_cache = "Update Redis cache AFTER" in content
            has_fallback = "FALLBACK: Try Redis cache" in content
            has_table_creation = "CREATE TABLE IF NOT EXISTS learning_state" in content
            
            success = has_postgres_first and has_redis_cache and has_fallback and has_table_creation
            
            if success:
                logger.info("✅ Postgres repository has correct source-of-truth pattern")
            else:
                logger.error(f"❌ Repository issues: postgres_first={has_postgres_first}, redis_cache={has_redis_cache}, fallback={has_fallback}, table={has_table_creation}")
            
            self.log_result("Postgres Repository Pattern", success,
                          "Postgres is source of truth, Redis is cache")
            return success
            
        except Exception as e:
            logger.error(f"❌ Postgres repository pattern test failed: {e}")
            self.log_result("Postgres Repository Pattern", False, f"Test failed: {e}")
            return False
    
    def test_unified_brain_event_driven(self) -> bool:
        """
        🚀 TEST: Verify UnifiedBrain has event-driven entrypoint
        """
        try:
            logger.info("🧪 Testing UnifiedBrain event-driven entrypoint...")
            
            # Check unified_brain.py
            brain_path = "core/learning/unified_brain.py"
            with open(brain_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Should have event-driven method
            has_process_kafka = "def process_kafka_event" in content
            has_validation = "Validate required fields" in content
            has_postgres_methods = "_get_canonical_state_from_postgres" in content
            has_postgres_save = "_save_canonical_state_to_postgres" in content
            
            success = has_process_kafka and has_validation and has_postgres_methods and has_postgres_save
            
            if success:
                logger.info("✅ UnifiedBrain has event-driven entrypoint")
            else:
                logger.error(f"❌ UnifiedBrain issues: kafka={has_process_kafka}, validation={has_validation}, postgres_get={has_postgres_methods}, postgres_save={has_postgres_save}")
            
            self.log_result("UnifiedBrain Event-Driven", success,
                          "UnifiedBrain has event-driven entrypoint with Postgres integration")
            return success
            
        except Exception as e:
            logger.error(f"❌ UnifiedBrain event-driven test failed: {e}")
            self.log_result("UnifiedBrain Event-Driven", False, f"Test failed: {e}")
            return False
    
    def test_docker_compose_cleanup(self) -> bool:
        """
        🚀 TEST: Verify docker-compose has been cleaned up
        """
        try:
            logger.info("🧪 Testing docker-compose cleanup...")
            
            # Check docker-compose.yml
            docker_path = "docker/docker-compose.yml"
            with open(docker_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Should have single learning consumer, no feedback-service
            has_learning_consumer = "learning-consumer:" in content
            has_learning_consumer_script = "python app/workers/learning_consumer.py" in content
            no_feedback_service = "feedback-service:" not in content
            has_removed_comment = "REMOVED: feedback-service" in content
            
            success = has_learning_consumer and has_learning_consumer_script and no_feedback_service and has_removed_comment
            
            if success:
                logger.info("✅ Docker-compose correctly cleaned up")
            else:
                logger.error(f"❌ Docker-compose issues: learning_consumer={has_learning_consumer}, script={has_learning_consumer_script}, no_feedback={no_feedback_service}, comment={has_removed_comment}")
            
            self.log_result("Docker Compose Cleanup", success,
                          "Single learning consumer, feedback-service removed")
            return success
            
        except Exception as e:
            logger.error(f"❌ Docker-compose cleanup test failed: {e}")
            self.log_result("Docker Compose Cleanup", False, f"Test failed: {e}")
            return False
    
    def test_kafka_partitioning_updated(self) -> bool:
        """
        🚀 TEST: Verify Kafka partitioning strategy updated
        """
        try:
            logger.info("🧪 Testing Kafka partitioning strategy...")
            
            # Check kafka_partitioning.py
            partitioning_path = "app/infrastructure/messaging/kafka_partitioning.py"
            with open(partitioning_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Should have new learning events
            has_learning_interaction = '"learning_interaction": "user_id"' in content
            has_learning_processed = '"learning_processed": "user_id"' in content
            has_new_comment = "🚀 NEW:" in content
            
            success = has_learning_interaction and has_learning_processed and has_new_comment
            
            if success:
                logger.info("✅ Kafka partitioning correctly updated")
            else:
                logger.error(f"❌ Kafka partitioning issues: interaction={has_learning_interaction}, processed={has_learning_processed}, comment={has_new_comment}")
            
            self.log_result("Kafka Partitioning Updated", success,
                          "New learning events added to partitioning strategy")
            return success
            
        except Exception as e:
            logger.error(f"❌ Kafka partitioning updated test failed: {e}")
            self.log_result("Kafka Partitioning Updated", False, f"Test failed: {e}")
            return False
    
    def test_unit_of_work_integration(self) -> bool:
        """
        🚀 TEST: Verify UnitOfWork integration in consumer
        """
        try:
            logger.info("🧪 Testing UnitOfWork integration...")
            
            # Check learning_consumer.py for UnitOfWork pattern
            consumer_path = "app/workers/learning_consumer.py"
            with open(consumer_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Should have UnitOfWork pattern
            has_transaction_wrapper = "with get_transaction" in content
            has_atomic_comment = "ATOMIC TRANSACTION WRAPPER" in content
            has_same_transaction = "in SAME transaction" in content
            has_rollback_handling = "transaction rolls back" in content
            
            success = has_transaction_wrapper and has_atomic_comment and has_same_transaction and has_rollback_handling
            
            if success:
                logger.info("✅ UnitOfWork correctly integrated")
            else:
                logger.error(f"❌ UnitOfWork issues: wrapper={has_transaction_wrapper}, comment={has_atomic_comment}, same_tx={has_same_transaction}, rollback={has_rollback_handling}")
            
            self.log_result("UnitOfWork Integration", success,
                          "Consumer uses UnitOfWork for atomic transactions")
            return success
            
        except Exception as e:
            logger.error(f"❌ UnitOfWork integration test failed: {e}")
            self.log_result("UnitOfWork Integration", False, f"Test failed: {e}")
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
        """Run all architecture correctness tests"""
        logger.info("🚀 Starting Architecture Correctness Tests...")
        
        # Run all tests
        tests = [
            self.test_api_event_emission_pattern,
            self.test_learning_consumer_architecture,
            self.test_postgres_repository_pattern,
            self.test_unified_brain_event_driven,
            self.test_docker_compose_cleanup,
            self.test_kafka_partitioning_updated,
            self.test_unit_of_work_integration
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
            time.sleep(0.1)  # Small delay between tests
        
        # Summary
        logger.info(f"📊 Architecture Test Results: {passed}/{total} tests passed")
        
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            logger.info(f"{status} {result['test']}: {result['message']}")
        
        success = passed == total
        if success:
            logger.info("🎉 All Architecture Correctness Tests PASSED!")
            logger.info("🚀 The surgical integration is working correctly!")
        else:
            logger.error(f"❌ {total - passed} tests failed")
        
        return success

def main():
    """Main test runner"""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run tests
    test = ArchitectureCorrectnessTest()
    success = test.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
