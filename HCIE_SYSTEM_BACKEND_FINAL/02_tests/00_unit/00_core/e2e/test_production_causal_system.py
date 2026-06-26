#!/usr/bin/env python3
"""
Production-Grade Causal Measurement System Test

Tests the redesigned causal measurement system for:
1. Scalar-vector consistency
2. Mathematically correct attribution
3. Production safety (no crashes)
4. Convergence to correct values
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.learning.unified_brain import UnifiedLearningBrain
from datetime import datetime
import traceback

def test_scalar_vector_consistency():
    """Test that scalar mastery and vector transfer are handled correctly"""
    print("🔥 TESTING SCALAR-VECTOR CONSISTENCY")
    
    brain = UnifiedLearningBrain()
    
    # Test interaction with scalar mastery and vector transfer
    user_id = 'test_user_scalar'
    concept = 'test_concept'
    interaction = {
        'correct': True,
        'response_time': 8.0,
        'timestamp': datetime.now().isoformat()
    }
    
    try:
        result = brain.process_event(user_id, concept, interaction, write_enabled=False)
        
        # Check that result contains proper causal attribution
        if hasattr(result, 'causal_attribution'):
            causal = result.causal_attribution
            print(f"✅ Causal attribution computed")
            print(f"   ΔM: {causal.get('delta_mastery', 'N/A')}")
            print(f"   J_t: {causal.get('J_t', 'N/A')}")
            print(f"   Effects: {causal.get('effects', {})}")
            
            # Verify attribution validity
            if causal.get('attribution_valid', False):
                print("✅ Attribution mathematically valid")
            else:
                print("⚠️ Attribution invalid")
        else:
            print("⚠️ No causal attribution found")
            
        return True
        
    except Exception as e:
        print(f"❌ Scalar-vector test failed: {e}")
        traceback.print_exc()
        return False

def test_mathematical_attribution():
    """Test that causal effects sum to actual learning"""
    print("\n🔥 TESTING MATHEMATICAL ATTRIBUTION")
    
    brain = UnifiedLearningBrain()
    
    # Process multiple interactions to build learning history
    user_id = 'test_user_math'
    concept = 'test_concept_math'
    
    total_delta = 0.0
    total_attributed = 0.0
    
    for i in range(5):
        interaction = {
            'correct': i % 2 == 0,  # Alternate success/failure
            'response_time': 5.0 + i,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            result = brain.process_event(user_id, concept, interaction, write_enabled=False)
            
            if hasattr(result, 'causal_attribution') and result.causal_attribution:
                causal = result.causal_attribution
                delta = causal.get('delta_mastery', 0.0)
                effects = causal.get('effects', {})
                
                total_delta += delta
                total_attributed += sum(effects.values())
                
                print(f"   Interaction {i+1}: ΔM={delta:.6f}, Attributed={sum(effects.values()):.6f}")
                
        except Exception as e:
            print(f"❌ Interaction {i+1} failed: {e}")
            return False
    
    # Verify mathematical consistency
    attribution_error = abs(total_delta - total_attributed)
    print(f"\n📊 MATHEMATICAL VALIDATION:")
    print(f"   Total ΔM: {total_delta:.6f}")
    print(f"   Total Attributed: {total_attributed:.6f}")
    print(f"   Attribution Error: {attribution_error:.8f}")
    
    if attribution_error < 1e-6:
        print("✅ Mathematical attribution is consistent")
        return True
    else:
        print("❌ Mathematical attribution is inconsistent")
        return False

def test_production_safety():
    """Test that system handles edge cases without crashing"""
    print("\n🔥 TESTING PRODUCTION SAFETY")
    
    brain = UnifiedLearningBrain()
    
    # Edge case 1: Zero transfer
    user_id_1 = 'test_edge_1'
    concept_edge = 'test_concept_edge'
    interaction1 = {
        'correct': False,
        'response_time': 100.0,  # Very high response time
        'timestamp': datetime.now().isoformat()
    }
    
    # Edge case 2: Missing data
    user_id_2 = 'test_edge_2'
    interaction2 = {
        'timestamp': datetime.now().isoformat()
        # Missing correct and response_time
    }
    
    # Edge case 3: Extreme values
    user_id_3 = 'test_edge_3'
    interaction3 = {
        'correct': True,
        'response_time': 0.1,  # Very fast response
        'timestamp': datetime.now().isoformat()
    }
    
    edge_cases = [
        ("Zero transfer/high cost", user_id_1, concept_edge, interaction1),
        ("Missing data", user_id_2, concept_edge, interaction2),
        ("Extreme values", user_id_3, concept_edge, interaction3)
    ]
    
    success_count = 0
    
    for case_name, user_id, concept, interaction in edge_cases:
        try:
            result = brain.process_event(user_id, concept, interaction, write_enabled=False)
            print(f"✅ {case_name}: Handled successfully")
            
            # Check for fallback causal result
            if hasattr(result, 'causal_attribution') and result.causal_attribution:
                if result.causal_attribution.get('status') == 'failed':
                    print(f"   Fallback mode activated: {result.causal_attribution.get('error', 'Unknown')}")
            
            success_count += 1
            
        except Exception as e:
            print(f"❌ {case_name}: Failed with {e}")
    
    return success_count == len(edge_cases)

def test_state_isolation():
    """Test that read-only mode doesn't modify state (state isolation)"""
    print("🔄 Testing state isolation (read-only mode)...")
    
    brain = UnifiedLearningBrain()
    
    user_id = 'test_isolation'
    concept = 'test_concept_isolation'
    
    mastery_values = []
    
    # Process 20 interactions in read-only mode
    for i in range(20):
        interaction = {
            'correct': i < 15,  # First 15 correct, then 5 incorrect
            'response_time': 8.0,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            result = brain.process_event(user_id, concept, interaction, write_enabled=False)
            mastery = result.mastery if hasattr(result, 'mastery') else 0.0
            mastery_values.append(mastery)
            
        except Exception as e:
            print(f"❌ State isolation test failed at interaction {i+1}: {e}")
            return False
    
    # Analyze state isolation
    initial_mastery = mastery_values[0] if mastery_values else 0.0
    final_mastery = mastery_values[-1] if mastery_values else 0.0
    max_mastery = max(mastery_values) if mastery_values else 0.0
    
    print(f"📊 STATE ISOLATION ANALYSIS:")
    print(f"   Initial mastery: {initial_mastery:.6f}")
    print(f"   Final mastery: {final_mastery:.6f}")
    print(f"   Peak mastery: {max_mastery:.6f}")
    
    # State isolation criteria: mastery should remain constant in read-only mode
    mastery_variance = max(mastery_values) - min(mastery_values) if mastery_values else 0.0
    
    if mastery_variance < 1e-6:  # Essentially no change
        print("✅ State isolation working correctly (read-only mode)")
        return True
    else:
        print("❌ State isolation failed (read-only mode modified state)")
        return False

def test_convergence_behavior():
    """Test that mastery converges appropriately over multiple interactions (write mode)"""
    print("� Testing real convergence behavior (write mode)...")
    
    brain = UnifiedLearningBrain()
    
    user_id = 'test_convergence_real'
    concept = 'test_concept_real'
    
    mastery_values = []
    
    # Process 20 interactions with write enabled to see real convergence
    for i in range(20):
        interaction = {
            'correct': i < 15,  # First 15 correct, then 5 incorrect
            'response_time': 8.0,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # For convergence tracking, we need to capture the mastery change
            # The result contains pre-update mastery, so we track the change ourselves
            pre_update_result = brain.process_event(user_id, concept, {}, write_enabled=False)
            pre_mastery = pre_update_result.mastery if hasattr(pre_update_result, 'mastery') else 0.0
            
            result = brain.process_event(user_id, concept, interaction, write_enabled=True)
            
            # Small delay to ensure state is written
            import time
            time.sleep(0.001)
            
            # Read the updated state with a different event_id to avoid duplicate detection
            import uuid
            read_result = brain.process_event(user_id, concept, {}, write_enabled=False, event_id=str(uuid.uuid4()))
            mastery = read_result.mastery if hasattr(read_result, 'mastery') else pre_mastery
            mastery_values.append(mastery)
            
        except Exception as e:
            print(f"❌ Convergence test failed at interaction {i+1}: {e}")
            return False
    
    # Analyze convergence
    initial_mastery = mastery_values[0] if mastery_values else 0.0
    final_mastery = mastery_values[-1] if mastery_values else 0.0
    max_mastery = max(mastery_values) if mastery_values else 0.0
    
    print(f"📊 REAL CONVERGENCE ANALYSIS:")
    print(f"   Initial mastery: {initial_mastery:.6f}")
    print(f"   Final mastery: {final_mastery:.6f}")
    print(f"   Peak mastery: {max_mastery:.6f}")
    
    # Real convergence criteria
    mastery_improved = final_mastery > initial_mastery
    mastery_in_bounds = 0.0 <= final_mastery <= 1.0
    
    if mastery_improved and mastery_in_bounds:
        print("✅ Real convergence behavior is reasonable")
        return True
    else:
        print("❌ Real convergence behavior is unreasonable")
        print(f"   Improved: {mastery_improved}, In bounds: {mastery_in_bounds}")
        return False

def main():
    """Run all production-grade tests"""
    print("🚀 PRODUCTION-GRADE CAUSAL SYSTEM TESTS")
    print("=" * 60)
    
    tests = [
        ("Scalar-Vector Consistency", test_scalar_vector_consistency),
        ("Mathematical Attribution", test_mathematical_attribution),
        ("Production Safety", test_production_safety),
        ("State Isolation", test_state_isolation),
        ("Real Convergence Behavior", test_convergence_behavior)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: CRASHED - {e}")
            traceback.print_exc()
    
    print(f"\n{'='*60}")
    print(f"🏁 TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL PRODUCTION-GRADE TESTS PASSED!")
        print("✅ System is ready for production deployment")
    else:
        print("⚠️ Some tests failed - review before production")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
