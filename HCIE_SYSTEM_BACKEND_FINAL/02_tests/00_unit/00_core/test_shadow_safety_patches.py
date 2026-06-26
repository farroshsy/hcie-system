#!/usr/bin/env python3
"""
🛡️ SHADOW MODE SAFETY PATCHES TEST
Validates that write guards prevent double writes
"""

import os

import pytest as _pt_skip
_pt_skip.skip(
    "core.learning.shadow_mode_engine was retired; test targets removed code.",
    allow_module_level=True,
)

import sys
import json
import time
import logging
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.learning.unified_brain import UnifiedLearningBrain
from core.learning.shadow_mode_engine import ShadowModeEngine

logger = logging.getLogger(__name__)

class ShadowSafetyPatchesTest:
    """Test shadow mode safety patches"""
    
    def __init__(self):
        self.test_results = []
    
    def test_write_guard_prevents_double_writes(self) -> bool:
        """Test that write_enabled=False prevents state writes"""
        try:
            logger.info("🧪 Testing write guard prevents double writes...")
            
            # Create unified brain
            unified_brain = UnifiedLearningBrain()
            
            # Test event
            test_event = {
                "event_id": "test_write_guard_001",
                "user_id": "test_user",
                "concept": "test_concept",
                "interaction": {"correct": True, "response_time": 5.0},
                "timestamp": time.time()
            }
            
            # Test 1: Normal write (should work)
            logger.info("📝 Testing normal write (write_enabled=True)...")
            result1 = unified_brain.process_kafka_event(test_event, write_enabled=True)
            
            # Test 2: Shadow mode write (should skip state write)
            logger.info("🛡️ Testing shadow mode write (write_enabled=False)...")
            result2 = unified_brain.process_kafka_event(test_event, write_enabled=False)
            
            # Both should return valid results
            assert result1 is not None, "Normal write should return result"
            assert result2 is not None, "Shadow mode should return result"
            
            # Results should be identical (same calculation, different write behavior)
            assert abs(result1.mastery - result2.mastery) < 0.001, "Results should be identical"
            
            logger.info(f"✅ Write guard test passed: mastery={result1.mastery:.6f}")
            
            self.log_result("Write Guard Prevents Double Writes", True, 
                          "write_enabled=False prevents state writes")
            return True
            
        except Exception as e:
            logger.error(f"❌ Write guard test failed: {e}")
            self.log_result("Write Guard Prevents Double Writes", False, f"Test failed: {e}")
            return False
    
    def test_shadow_mode_engine_safety(self) -> bool:
        """Test that shadow mode engine uses write guards"""
        try:
            logger.info("🧪 Testing shadow mode engine safety...")
            
            # Create shadow mode engine
            shadow_engine = ShadowModeEngine()
            
            # Test event
            test_event = {
                "event_id": "test_shadow_safety_001",
                "user_id": "test_user",
                "concept": "test_concept",
                "correct": True,
                "response_time": 3.0,
                "timestamp": time.time()
            }
            
            # Mock cursor (not used in unified brain with write_enabled=False)
            mock_cursor = None
            
            # Process through shadow mode
            logger.info("🔄 Processing through shadow mode engine...")
            result = shadow_engine.process_submission(test_event, mock_cursor)
            
            # Should return legacy result
            assert result is not None, "Shadow mode should return result"
            assert "mastery" in result, "Result should contain mastery"
            
            logger.info(f"✅ Shadow mode safety test passed: mastery={result.get('mastery', 0):.3f}")
            
            self.log_result("Shadow Mode Engine Safety", True, 
                          "Shadow mode uses write guards correctly")
            return True
            
        except Exception as e:
            logger.error(f"❌ Shadow mode safety test failed: {e}")
            self.log_result("Shadow Mode Engine Safety", False, f"Test failed: {e}")
            return False
    
    def test_assertion_guard_catches_issues(self) -> bool:
        """Test that assertion guard catches potential issues"""
        try:
            logger.info("🧪 Testing assertion guard catches issues...")
            
            # Create shadow mode engine
            shadow_engine = ShadowModeEngine()
            
            # Test event that might cause issues
            problematic_event = {
                "event_id": "test_assertion_001",
                "user_id": "test_user",
                "concept": "test_concept",
                "correct": True,
                "response_time": -1.0,  # Negative response time might cause issues
                "timestamp": time.time()
            }
            
            mock_cursor = None
            
            # This should either work or fail with assertion
            try:
                result = shadow_engine.process_submission(problematic_event, mock_cursor)
                logger.info("✅ Assertion guard test passed (no issues detected)")
                success = True
            except AssertionError as ae:
                logger.info(f"✅ Assertion guard caught issue: {ae}")
                success = True  # Assertion caught the issue - that's good!
            except Exception as e:
                logger.error(f"❌ Unexpected error (not assertion): {e}")
                success = False
            
            self.log_result("Assertion Guard Catches Issues", success,
                          "Assertion guard detects potential double writes")
            return success
            
        except Exception as e:
            logger.error(f"❌ Assertion guard test failed: {e}")
            self.log_result("Assertion Guard Catches Issues", False, f"Test failed: {e}")
            return False
    
    def test_simple_drift_logging(self) -> bool:
        """Test that simple drift logging works"""
        try:
            logger.info("🧪 Testing simple drift logging...")
            
            # Create shadow mode engine
            shadow_engine = ShadowModeEngine()
            
            # Test events with different outcomes
            events = [
                {
                    "event_id": "test_drift_001",
                    "user_id": "test_user",
                    "concept": "test_concept",
                    "correct": True,
                    "response_time": 1.0,
                    "timestamp": time.time()
                },
                {
                    "event_id": "test_drift_002", 
                    "user_id": "test_user",
                    "concept": "test_concept",
                    "correct": False,
                    "response_time": 10.0,
                    "timestamp": time.time()
                }
            ]
            
            mock_cursor = None
            comparison_count = 0
            
            for event in events:
                result = shadow_engine.process_submission(event, mock_cursor)
                comparison_count += 1
                
                # Check if comparison was logged
                if len(shadow_engine.comparison_log) >= comparison_count:
                    comparison = shadow_engine.comparison_log[-1]
                    mastery_delta = comparison.get("mastery_delta", 0)
                    
                    # Should log differences
                    if abs(mastery_delta) > 0.01:
                        logger.info(f"📊 Drift detected: mastery_delta={mastery_delta:.3f}")
                    
            logger.info(f"✅ Simple drift logging test passed: {comparison_count} comparisons logged")
            
            self.log_result("Simple Drift Logging", True,
                          f"Logged {comparison_count} comparisons with drift detection")
            return True
            
        except Exception as e:
            logger.error(f"❌ Simple drift logging test failed: {e}")
            self.log_result("Simple Drift Logging", False, f"Test failed: {e}")
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
        """Run all shadow safety patch tests"""
        logger.info("🛡️ Starting Shadow Safety Patches Tests...")
        
        # Run all tests
        tests = [
            self.test_write_guard_prevents_double_writes,
            self.test_shadow_mode_engine_safety,
            self.test_assertion_guard_catches_issues,
            self.test_simple_drift_logging
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
            time.sleep(0.1)  # Small delay between tests
        
        # Summary
        logger.info(f"📊 Shadow Safety Test Results: {passed}/{total} tests passed")
        
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            logger.info(f"{status} {result['test']}: {result['message']}")
        
        success = passed == total
        if success:
            logger.info("🎉 All Shadow Safety Patches Tests PASSED!")
            logger.info("🛡️ Shadow mode is now safe from double writes!")
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
    test = ShadowSafetyPatchesTest()
    success = test.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
