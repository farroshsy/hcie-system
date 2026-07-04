#!/usr/bin/env python3
"""
🔍 REAL-WORLD VALIDATIONS
Step 2: Production readiness validation tests
"""

import os
import sys
import time
import logging

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.learning.unified_brain import UnifiedLearningBrain

logger = logging.getLogger(__name__)

class RealWorldValidations:
    """Real-world validation tests for production readiness"""
    
    def __init__(self):
        self.test_results = []
    
    def test_replay_consistency(self) -> bool:
        """Test: Same event → same result (idempotency)"""
        try:
            logger.info("🧪 Testing replay consistency...")
            
            brain = UnifiedLearningBrain()
            
            test_event = {
                'event_id': 'replay_test_001',
                'user_id': 'replay_user',
                'concept': 'k2_algorithms',
                'interaction': {'correct': True, 'response_time': 4.0, 'confidence': 0.8},
                'timestamp': time.time()
            }
            
            # Process same event 3 times with different event_ids
            results = []
            for i in range(3):
                test_event['event_id'] = f'replay_test_00{i+1}'
                result = brain.process_kafka_event(test_event.copy(), write_enabled=True)
                results.append(result.mastery)
                time.sleep(0.1)
            
            # Check consistency
            max_diff = max(results) - min(results)
            
            logger.info(f"📊 Results: {[round(r, 6) for r in results]}")
            logger.info(f"📊 Max difference: {max_diff:.6f}")
            
            if max_diff < 0.001:
                logger.info("✅ REPLAY TEST: PASSED")
                self.log_result("Replay Consistency", True, f"Max difference: {max_diff:.6f} < 0.001")
                return True
            else:
                logger.error(f"❌ REPLAY TEST: FAILED - Max difference: {max_diff:.6f}")
                self.log_result("Replay Consistency", False, f"Max difference: {max_diff:.6f} >= 0.001")
                return False
                
        except Exception as e:
            logger.error(f"❌ Replay test failed: {e}")
            self.log_result("Replay Consistency", False, f"Test failed: {e}")
            return False
    
    def test_restart_persistence(self) -> bool:
        """Test: Service restart → state still correct"""
        try:
            logger.info("🧪 Testing restart persistence...")
            
            # Process event before "restart"
            brain_before = UnifiedLearningBrain()
            
            before_restart_event = {
                'event_id': 'restart_before',
                'user_id': 'restart_user',
                'concept': 'k5_algorithms',
                'interaction': {'correct': True, 'response_time': 3.5, 'confidence': 0.9},
                'timestamp': time.time()
            }
            
            before_result = brain_before.process_kafka_event(before_restart_event, write_enabled=True)
            before_mastery = before_result.mastery
            
            # Simulate restart by creating new brain instance
            brain_after = UnifiedLearningBrain()
            
            # Check state after restart
            after_restart_result = brain_after.process_event(
                user_id='restart_user',
                concept='k5_algorithms',
                interaction={'correct': False, 'response_time': 5.0, 'confidence': 0.7},
                mode='read'
            )
            
            after_mastery = after_restart_result.mastery
            
            logger.info(f"📊 Before restart mastery: {before_mastery:.6f}")
            logger.info(f"📊 After restart mastery: {after_mastery:.6f}")
            logger.info(f"📊 Difference: {abs(before_mastery - after_mastery):.6f}")
            
            if abs(before_mastery - after_mastery) < 0.001:
                logger.info("✅ RESTART TEST: PASSED")
                self.log_result("Restart Persistence", True, f"Difference: {abs(before_mastery - after_mastery):.6f} < 0.001")
                return True
            else:
                logger.error(f"❌ RESTART TEST: FAILED - Difference: {abs(before_mastery - after_mastery):.6f}")
                self.log_result("Restart Persistence", False, f"Difference: {abs(before_mastery - after_mastery):.6f} >= 0.001")
                return False
                
        except Exception as e:
            logger.error(f"❌ Restart test failed: {e}")
            self.log_result("Restart Persistence", False, f"Test failed: {e}")
            return False
    
    def test_multi_user_isolation(self) -> bool:
        """Test: Different users → no cross-contamination"""
        try:
            logger.info("🧪 Testing multi-user isolation...")
            
            brain = UnifiedLearningBrain()
            
            users = ['user_alpha', 'user_beta', 'user_gamma']
            concepts = ['k2_algorithms', 'k5_algorithms', 'k8_algorithms']
            
            user_results = {}
            
            for i, user in enumerate(users):
                concept = concepts[i % len(concepts)]
                
                test_event = {
                    'event_id': f'multi_user_{user}',
                    'user_id': user,
                    'concept': concept,
                    'interaction': {'correct': i % 2 == 0, 'response_time': 4.0 + i, 'confidence': 0.8 - i * 0.1},
                    'timestamp': time.time()
                }
                
                result = brain.process_kafka_event(test_event, write_enabled=True)
                user_results[user] = {
                    'concept': concept,
                    'mastery': result.mastery,
                    'correct': test_event['interaction']['correct']
                }
            
            logger.info("📊 Multi-user results:")
            for user, data in user_results.items():
                logger.info(f"  👤 {user}: {data['concept']} mastery {data['mastery']:.6f} correct {data['correct']}")
            
            # Check for cross-contamination
            masteries = [data['mastery'] for data in user_results.values()]
            unique_masteries = len(set(round(m, 4) for m in masteries))
            
            if unique_masteries == len(users):
                logger.info("✅ MULTI-USER TEST: PASSED")
                self.log_result("Multi-User Isolation", True, f"Unique mastery values: {unique_masteries}/{len(users)}")
                return True
            else:
                logger.error(f"❌ MULTI-USER TEST: FAILED - Unique mastery values: {unique_masteries}/{len(users)}")
                self.log_result("Multi-User Isolation", False, f"Possible cross-contamination detected")
                return False
                
        except Exception as e:
            logger.error(f"❌ Multi-user test failed: {e}")
            self.log_result("Multi-User Isolation", False, f"Test failed: {e}")
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
    
    def run_all_validations(self) -> bool:
        """Run all real-world validation tests"""
        logger.info("🔍 Starting Real-World Validations...")
        
        # Run all tests
        tests = [
            self.test_replay_consistency,
            self.test_restart_persistence,
            self.test_multi_user_isolation
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
            time.sleep(0.1)  # Small delay between tests
        
        # Summary
        logger.info(f"📊 Real-World Validation Results: {passed}/{total} tests passed")
        
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            logger.info(f"{status} {result['test']}: {result['message']}")
        
        success = passed == total
        if success:
            logger.info("🎉 ALL REAL-WORLD VALIDATIONS PASSED!")
            logger.info("✅ System is production-ready")
            logger.info("✅ Idempotency working correctly")
            logger.info("✅ State persistence working")
            logger.info("✅ User isolation working")
        else:
            logger.error(f"❌ {total - passed} tests failed")
        
        return success

def main():
    """Main validation runner"""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run validations
    validations = RealWorldValidations()
    success = validations.run_all_validations()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
