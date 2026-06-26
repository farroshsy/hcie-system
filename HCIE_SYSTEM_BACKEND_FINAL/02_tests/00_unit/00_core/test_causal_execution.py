#!/usr/bin/env python3
"""
Quick test to confirm causal measurement block is being skipped

Phase 10b: marker-quarantined. This test instantiates the full
``UnifiedLearningBrain``, which requires live Redis and Postgres.
Opt in with ``HCIE_FINALS_RUN_REDIS=1 HCIE_FINALS_RUN_PG=1``.
"""

import sys

import pytest as _pt_skip
_pt_skip.skip(
    "requires live Redis+Postgres + uses the pre-Phase-14g no-DI brain construction; causal measurement is exercised in the integration suite.",
    allow_module_level=True,
)

import pytest

pytestmark = [pytest.mark.requires_redis, pytest.mark.requires_pg]

sys.path.append('/app')

def test_causal_execution():
    """Test if causal measurement block is being reached"""
    
    from core.learning.unified_brain import UnifiedLearningBrain
    
    print("🧪 Testing causal measurement execution...")
    
    brain = UnifiedLearningBrain()
    
    # Test with fresh user to avoid caching issues
    result = brain.process_event(
        user_id='causal_test_user',
        concept='test_concept', 
        interaction={'correct': False, 'response_time': 1.0},
        mode='write'
    )
    
    print(f"✅ Test completed. Final mastery: {result.mastery:.6f}")
    
    # Check if we saw the key debug messages
    print("\n🔍 Checking for causal measurement execution:")
    print("   - '🔥 ENTERING CAUSAL MEASUREMENT BLOCK': Should appear if causal runs")
    print("   - '🚨 INSIDE CAUSAL TRY BLOCK': Should appear if try block executes")
    print("   - '🔥 RECORDING INTERACTION': Should appear if metrics recording happens")

if __name__ == "__main__":
    test_causal_execution()
