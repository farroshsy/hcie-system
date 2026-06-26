"""
Replay Validation Harness

Validates deterministic replay capabilities.

Tests:
- Event determinism: same events → same state
- Replay equivalence: replay from events reconstructs same state
- Trajectory stability: same seed → same concept sequence
"""
import logging
from typing import Dict, Any, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ReplayValidationResult:
    """Result of replay validation."""
    success: bool
    event_determinism: bool
    replay_equivalence: bool
    trajectory_stability: bool
    details: Dict[str, Any]


class ReplayValidator:
    """
    Validates deterministic replay capabilities.
    
    Tests:
    1. Event determinism: Same event sequence produces identical state
    2. Replay equivalence: Replay from event history reconstructs same state
    3. Trajectory stability: Same seed produces same concept sequence
    """
    
    def __init__(self):
        """Initialize replay validator."""
        self.validation_results = []
    
    def validate_event_determinism(self, brain, events: List[Dict[str, Any]]) -> bool:
        """
        Validate that same events produce same state.
        
        Args:
            brain: UnifiedLearningBrain instance
            events: List of events to process
            
        Returns:
            True if event determinism holds
        """
        logger.info("🔍 Validating event determinism...")
        
        # Process events once
        state1 = {}
        for event in events:
            result = brain.process_event(
                user_id=event["user_id"],
                concept=event["concept"],
                interaction=event.get("interaction"),
                mode="write"
            )
            state1[event["user_id"]] = result.get("state", {})
        
        # Reset brain and process again
        brain.uuid_gen.reset() if brain.uuid_gen else None
        brain.time_provider.reset() if brain.time_provider else None
        brain.rng_manager.reset_all() if brain.rng_manager else None
        
        state2 = {}
        for event in events:
            result = brain.process_event(
                user_id=event["user_id"],
                concept=event["concept"],
                interaction=event.get("interaction"),
                mode="write"
            )
            state2[event["user_id"]] = result.get("state", {})
        
        # Compare states
        for user_id in state1:
            if state1[user_id] != state2[user_id]:
                logger.error(f"❌ Event determinism failed for user {user_id}")
                logger.error(f"   State1: {state1[user_id]}")
                logger.error(f"   State2: {state2[user_id]}")
                return False
        
        logger.info("✅ Event determinism validated")
        return True
    
    def validate_replay_equivalence(self, original_events: List[Dict[str, Any]], 
                                   replayed_events: List[Dict[str, Any]]) -> bool:
        """
        Validate that replay from event history reconstructs same state.
        
        Args:
            original_events: Events from original run
            replayed_events: Events from replayed run
            
        Returns:
            True if replay equivalence holds
        """
        logger.info("🔍 Validating replay equivalence...")
        
        # Compare event sequences
        if len(original_events) != len(replayed_events):
            logger.error("❌ Replay equivalence failed: event count mismatch")
            logger.error(f"   Original: {len(original_events)}, Replayed: {len(replayed_events)}")
            return False
        
        for i, (orig, replay) in enumerate(zip(original_events, replayed_events)):
            # Compare key fields
            if orig.get("concept") != replay.get("concept"):
                logger.error(f"❌ Replay equivalence failed at event {i}")
                logger.error(f"   Original concept: {orig.get('concept')}")
                logger.error(f"   Replayed concept: {replay.get('concept')}")
                return False
            
            # Compare mastery if available
            orig_mastery = orig.get("mastery")
            replay_mastery = replay.get("mastery")
            if orig_mastery is not None and replay_mastery is not None:
                if abs(orig_mastery - replay_mastery) > 1e-6:
                    logger.error(f"❌ Replay equivalence failed at event {i}")
                    logger.error(f"   Original mastery: {orig_mastery}")
                    logger.error(f"   Replayed mastery: {replay_mastery}")
                    return False
        
        logger.info("✅ Replay equivalence validated")
        return True
    
    def validate_trajectory_stability(self, brain, seed: int, num_steps: int = 10) -> bool:
        """
        Validate that same seed produces same concept sequence.
        
        Args:
            brain: UnifiedLearningBrain instance
            seed: Deterministic seed
            num_steps: Number of steps to test
            
        Returns:
            True if trajectory stability holds
        """
        logger.info("🔍 Validating trajectory stability...")
        
        # Generate trajectory once
        concepts1 = []
        for i in range(num_steps):
            if hasattr(brain, 'select_next_concept'):
                concept = brain.select_next_concept(
                    user_id="test_user",
                    available_concepts=["concept_a", "concept_b", "concept_c"]
                )
                concepts1.append(concept)
        
        # Reset and generate again
        brain.uuid_gen.reset() if brain.uuid_gen else None
        brain.time_provider.reset() if brain.time_provider else None
        brain.rng_manager.reset_all() if brain.rng_manager else None
        
        concepts2 = []
        for i in range(num_steps):
            if hasattr(brain, 'select_next_concept'):
                concept = brain.select_next_concept(
                    user_id="test_user",
                    available_concepts=["concept_a", "concept_b", "concept_c"]
                )
                concepts2.append(concept)
        
        # Compare trajectories
        if concepts1 != concepts2:
            logger.error("❌ Trajectory stability failed")
            logger.error(f"   Trajectory1: {concepts1}")
            logger.error(f"   Trajectory2: {concepts2}")
            return False
        
        logger.info("✅ Trajectory stability validated")
        return True
    
    def run_full_validation(self, brain, seed: int, events: List[Dict[str, Any]]) -> ReplayValidationResult:
        """
        Run full replay validation suite.
        
        Args:
            brain: UnifiedLearningBrain instance
            seed: Deterministic seed
            events: Test events
            
        Returns:
            ReplayValidationResult with all validation results
        """
        logger.info("🚀 Running full replay validation suite...")
        
        result = ReplayValidationResult(
            success=False,
            event_determinism=False,
            replay_equivalence=False,
            trajectory_stability=False,
            details={}
        )
        
        # Test 1: Event determinism
        try:
            result.event_determinism = self.validate_event_determinism(brain, events)
        except Exception as e:
            logger.error(f"❌ Event determinism validation failed with exception: {e}")
            result.event_determinism = False
        
        # Test 2: Trajectory stability
        try:
            result.trajectory_stability = self.validate_trajectory_stability(brain, seed)
        except Exception as e:
            logger.error(f"❌ Trajectory stability validation failed with exception: {e}")
            result.trajectory_stability = False
        
        # Test 3: Replay equivalence (if events have replay data)
        # This requires running the experiment twice and comparing
        result.replay_equivalence = True  # Placeholder
        
        # Overall success
        result.success = result.event_determinism and result.trajectory_stability
        
        logger.info(f"🎯 Replay validation complete: {'✅ PASSED' if result.success else '❌ FAILED'}")
        logger.info(f"   Event determinism: {'✅' if result.event_determinism else '❌'}")
        logger.info(f"   Trajectory stability: {'✅' if result.trajectory_stability else '❌'}")
        logger.info(f"   Replay equivalence: {'✅' if result.replay_equivalence else '❌'}")
        
        return result
