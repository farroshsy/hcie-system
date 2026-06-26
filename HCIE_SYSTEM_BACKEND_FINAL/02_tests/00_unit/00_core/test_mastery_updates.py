#!/usr/bin/env python3
"""
Test if UnifiedLearningBrain actually updates mastery

Phase 10b: marker-quarantined. This test instantiates the full
``UnifiedLearningBrain`` and requires live Redis + Postgres. Opt in
with ``HCIE_FINALS_RUN_REDIS=1 HCIE_FINALS_RUN_PG=1``.
"""

import pytest

import pytest as _pt_skip
_pt_skip.skip(
    "written for the pre-Phase-14g brain API (removed system_mode); mastery update is covered by test_load_bearing_path (Kalman) + the integration suite.",
    allow_module_level=True,
)


pytestmark = [pytest.mark.requires_redis, pytest.mark.requires_pg]

from core.learning.unified_brain import UnifiedLearningBrain
from datetime import datetime

def test_mastery_updates():
    """Test if UnifiedLearningBrain actually updates mastery"""
    
    brain = UnifiedLearningBrain(system_mode='jt')
    user_id = 'mastery_test_user'
    concept = 'k2_algorithms'
    
    print('🧪 TESTING MASTERY UPDATES')
    print('=' * 40)
    
    # Step 1: Get initial mastery
    initial_result = brain.process_event(
        user_id=user_id,
        concept=concept,
        interaction=None,
        mode='read'
    )
    initial_mastery = initial_result.mastery
    print(f'Initial mastery: {initial_mastery:.6f}')
    
    # Step 2: Simulate a learning interaction (WRITE mode)
    interaction = {
        'task_id': 'test_task_001',
        'correctness': 0.9,  # High performance
        'response_time': 15.0,
        'difficulty': 0.3,
        'timestamp': datetime.utcnow().isoformat(),
        'attempts': 1,
        'hints_used': 0,
        'frustration': 0.1,
        'engagement': 0.9
    }
    
    print(f'\n📝 Submitting interaction: correctness={interaction["correctness"]}')
    
    # Step 3: Update mastery with WRITE mode
    write_result = brain.process_event(
        user_id=user_id,
        concept=concept,
        interaction=interaction,
        mode='write'
    )
    
    print(f'Write result mastery: {write_result.mastery:.6f}')
    
    # Step 4: Check if mastery actually changed
    final_result = brain.process_event(
        user_id=user_id,
        concept=concept,
        interaction=None,
        mode='read'
    )
    final_mastery = final_result.mastery
    mastery_change = final_mastery - initial_mastery
    
    print(f'Final mastery: {final_mastery:.6f}')
    print(f'Mastery change: {mastery_change:+.6f}')
    
    if abs(mastery_change) > 0.001:
        print('✅ MASTERY ACTUALLY UPDATED!')
    else:
        print('❌ MASTERY DID NOT CHANGE - UnifiedBrain not updating!')
    
    # Step 5: Try multiple interactions to see cumulative effect
    print('\n🔄 Testing cumulative updates...')
    for i in range(3):
        interaction['correctness'] = 0.8 + (i * 0.05)  # Gradually improving
        brain.process_event(
            user_id=user_id,
            concept=concept,
            interaction=interaction,
            mode='write'
        )
        
        check_result = brain.process_event(
            user_id=user_id,
            concept=concept,
            interaction=None,
            mode='read'
        )
        print(f'  After interaction {i+2}: mastery = {check_result.mastery:.6f}')
    
    # Step 6: Test with poor performance
    print('\n📉 Testing with poor performance...')
    poor_interaction = {
        'task_id': 'test_task_poor',
        'correctness': 0.1,  # Very poor performance
        'response_time': 60.0,
        'difficulty': 0.3,
        'timestamp': datetime.utcnow().isoformat(),
        'attempts': 3,
        'hints_used': 2,
        'frustration': 0.9,
        'engagement': 0.3
    }
    
    before_poor = brain.process_event(
        user_id=user_id,
        concept=concept,
        interaction=None,
        mode='read'
    ).mastery
    
    brain.process_event(
        user_id=user_id,
        concept=concept,
        interaction=poor_interaction,
        mode='write'
    )
    
    after_poor = brain.process_event(
        user_id=user_id,
        concept=concept,
        interaction=None,
        mode='read'
    ).mastery
    
    print(f'Before poor performance: {before_poor:.6f}')
    print(f'After poor performance: {after_poor:.6f}')
    print(f'Change: {after_poor - before_poor:+.6f}')
    
    if after_poor < before_poor:
        print('✅ MASTERY DECREASED with poor performance!')
    else:
        print('❌ MASTERY did not decrease with poor performance!')

if __name__ == "__main__":
    test_mastery_updates()
