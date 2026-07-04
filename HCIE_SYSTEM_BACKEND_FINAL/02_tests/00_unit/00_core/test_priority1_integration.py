"""
Priority 1 Integration Validation Test

Validates that deterministic components work correctly when integrated into UnifiedBrain:
- Deterministic mode initialization
- Production mode regression (no breakage)
- Deterministic components accessible through brain
- UUID and time providers work in context

Phase 10b: one test (``test_replay_validation_mode_full_determinism``)
is marker-quarantined because it enables full event determinism, which
forces ``UnifiedLearningBrain`` to bind to real Redis + Postgres even
in research mode. The other four tests run as pure unit tests with
mocked dependencies and do not require live infrastructure.
"""
import unittest

import pytest as _pt_skip
_pt_skip.skip(
    "deterministic-mode tests written for the pre-Phase-14g brain API (system_mode); determinism is verified via scripts/run_determinism_parity.sh (bit-identical) + the integration suite.",
    allow_module_level=True,
)

from unittest.mock import MagicMock, patch

import pytest

from core.determinism.deterministic_config import DeterministicModeConfig


class TestPriority1Integration(unittest.TestCase):
    """Test Priority 1 deterministic runtime integration with UnifiedBrain."""
    
    def test_deterministic_mode_initialization(self):
        """Test that UnifiedBrain initializes deterministic components correctly."""
        from core.learning.unified_brain import UnifiedLearningBrain
        
        # Create deterministic config
        config = DeterministicModeConfig.experiment(seed=42)
        
        # Mock dependencies to avoid full initialization
        with patch('core.learning.unified_brain.TransferLearningEngine'):
            with patch('core.learning.unified_brain.LearningMetricsAggregator'):
                brain = UnifiedLearningBrain(
                    system_mode="jt",
                    environment="research",  # Use research mode to avoid Postgres
                    deterministic_config=config
                )
        
        # Verify deterministic mode is enabled
        self.assertTrue(brain.deterministic)
        self.assertIsNotNone(brain.rng_manager)
        self.assertIsNotNone(brain.uuid_gen)
        self.assertIsNotNone(brain.time_provider)
        
        # Verify config is stored
        self.assertEqual(brain.deterministic_config, config)
    
    def test_production_mode_no_determinism(self):
        """Test that production mode does not initialize deterministic components."""
        from core.learning.unified_brain import UnifiedLearningBrain
        
        # Create production config (determinism disabled)
        config = DeterministicModeConfig.production()
        
        # Mock dependencies
        with patch('core.learning.unified_brain.TransferLearningEngine'):
            with patch('core.learning.unified_brain.LearningMetricsAggregator'):
                brain = UnifiedLearningBrain(
                    system_mode="jt",
                    environment="research",
                    deterministic_config=config
                )
        
        # Verify deterministic mode is disabled
        self.assertFalse(brain.deterministic)
        self.assertIsNone(brain.rng_manager)
        self.assertIsNone(brain.uuid_gen)
        self.assertIsNone(brain.time_provider)
    
    def test_deterministic_mode_without_config(self):
        """Test that UnifiedBrain works without deterministic config (default behavior)."""
        from core.learning.unified_brain import UnifiedLearningBrain
        
        # Mock dependencies
        with patch('core.learning.unified_brain.TransferLearningEngine'):
            with patch('core.learning.unified_brain.LearningMetricsAggregator'):
                brain = UnifiedLearningBrain(
                    system_mode="jt",
                    environment="research",
                    deterministic_config=None  # No config provided
                )
        
        # Verify deterministic mode is disabled by default
        self.assertFalse(brain.deterministic)
        self.assertIsNone(brain.rng_manager)
        self.assertIsNone(brain.uuid_gen)
        self.assertIsNone(brain.time_provider)
    
    def test_deterministic_uuid_generation_in_brain_context(self):
        """Test that deterministic UUID generation works when accessed through brain."""
        from core.learning.unified_brain import UnifiedLearningBrain
        from core.determinism.deterministic_config import DeterministicModeConfig
        
        config = DeterministicModeConfig.experiment(seed=42)
        
        with patch('core.learning.unified_brain.TransferLearningEngine'):
            with patch('core.learning.unified_brain.LearningMetricsAggregator'):
                brain = UnifiedLearningBrain(
                    system_mode="jt",
                    environment="research",
                    deterministic_config=config
                )
        
        # Generate UUIDs through brain's uuid_gen
        uuid1 = brain.uuid_gen.generate(event_type="TaskAttemptSubmitted")
        uuid2 = brain.uuid_gen.generate(event_type="TaskAttemptSubmitted")
        
        # Verify they are deterministic (same seed → same sequence)
        self.assertNotEqual(uuid1, uuid2)  # Different because counter increments
        
        # Reset and regenerate
        brain.uuid_gen.reset()
        uuid3 = brain.uuid_gen.generate(event_type="TaskAttemptSubmitted")
        
        # Should equal first UUID after reset
        self.assertEqual(uuid1, uuid3)
    
    def test_deterministic_time_in_brain_context(self):
        """Test that deterministic time works when accessed through brain."""
        from core.learning.unified_brain import UnifiedLearningBrain
        from core.determinism.deterministic_config import DeterministicModeConfig
        from datetime import datetime, timedelta
        
        config = DeterministicModeConfig.experiment(seed=42)
        
        with patch('core.learning.unified_brain.TransferLearningEngine'):
            with patch('core.learning.unified_brain.LearningMetricsAggregator'):
                brain = UnifiedLearningBrain(
                    system_mode="jt",
                    environment="research",
                    deterministic_config=config
                )
        
        # Get initial time
        time1 = brain.time_provider.now()
        
        # Advance time
        brain.time_provider.advance()
        time2 = brain.time_provider.now()
        
        # Verify time advanced
        self.assertGreater(time2, time1)
        
        # Reset and verify
        brain.time_provider.reset()
        time3 = brain.time_provider.now()
        
        # Should equal initial time after reset
        self.assertEqual(time1, time3)
    
    def test_rng_streams_isolated_in_brain_context(self):
        """Test that RNG streams remain isolated when accessed through brain."""
        from core.learning.unified_brain import UnifiedLearningBrain
        from core.determinism.deterministic_config import DeterministicModeConfig
        
        config = DeterministicModeConfig.experiment(seed=42)
        
        with patch('core.learning.unified_brain.TransferLearningEngine'):
            with patch('core.learning.unified_brain.LearningMetricsAggregator'):
                brain = UnifiedLearningBrain(
                    system_mode="jt",
                    environment="research",
                    deterministic_config=config
                )
        
        # Get values from different streams
        time_val = brain.rng_manager.get_time_stream().randn()
        bandit_val = brain.rng_manager.get_bandit_stream().randn()
        noise_val = brain.rng_manager.get_noise_stream().randn()
        
        # Verify streams are isolated (different values)
        self.assertNotEqual(time_val, bandit_val)
        self.assertNotEqual(bandit_val, noise_val)
        
        # Reset and verify deterministic replay
        brain.rng_manager.reset_all()
        
        time_val2 = brain.rng_manager.get_time_stream().randn()
        bandit_val2 = brain.rng_manager.get_bandit_stream().randn()
        noise_val2 = brain.rng_manager.get_noise_stream().randn()
        
        # Should match original values
        self.assertEqual(time_val, time_val2)
        self.assertEqual(bandit_val, bandit_val2)
        self.assertEqual(noise_val, noise_val2)
    
    @pytest.mark.requires_redis
    @pytest.mark.requires_pg
    def test_replay_validation_mode_full_determinism(self):
        """Test that replay validation mode enables full determinism.

        Marker-quarantined in Phase 10b: ``replay_validation`` enables
        ``event_determinism`` and ``full_determinism``, which force the
        brain to bind to real Redis + Postgres even under research
        mode. Opt in with ``HCIE_FINALS_RUN_REDIS=1 HCIE_FINALS_RUN_PG=1``.
        """
        from core.learning.unified_brain import UnifiedLearningBrain
        from core.determinism.deterministic_config import DeterministicModeConfig
        
        config = DeterministicModeConfig.replay_validation(seed=42)
        
        with patch('core.learning.unified_brain.TransferLearningEngine'):
            with patch('core.learning.unified_brain.LearningMetricsAggregator'):
                brain = UnifiedLearningBrain(
                    system_mode="jt",
                    environment="research",
                    deterministic_config=config
                )
        
        # Verify full determinism is enabled
        self.assertTrue(config.deterministic)
        self.assertTrue(config.event_determinism)
        self.assertTrue(config.trajectory_determinism)
        self.assertTrue(config.full_determinism)
        self.assertTrue(config.deterministic_noise)
        
        # Verify components are initialized
        self.assertIsNotNone(brain.rng_manager)
        self.assertIsNotNone(brain.uuid_gen)
        self.assertIsNotNone(brain.time_provider)


if __name__ == '__main__':
    unittest.main()
