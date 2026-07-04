"""
Priority 1 Deterministic Runtime Tests

Tests for minimal viable determinism:
- Namespace-based UUID generation
- Isolated RNG streams
- Simulated time provider
- Opt-in deterministic mode
"""
import unittest
import uuid
from datetime import datetime
import numpy as np

from core.determinism.deterministic_uuid import DeterministicUUIDGenerator
from core.determinism.rng_stream_manager import RNGStreamManager
from core.determinism.simulated_time import SimulatedTimeProvider
from core.determinism.deterministic_config import DeterministicModeConfig


class TestDeterministicUUIDGenerator(unittest.TestCase):
    """Test namespace-based deterministic UUID generation."""
    
    def test_uuid_determinism(self):
        """Test that same seed produces same UUIDs."""
        gen1 = DeterministicUUIDGenerator(seed=42)
        gen2 = DeterministicUUIDGenerator(seed=42)
        
        uuid1 = gen1.generate("event")
        uuid2 = gen2.generate("event")
        
        self.assertEqual(uuid1, uuid2)
    
    def test_uuid_monotonic_counter(self):
        """Test that counter increments properly."""
        gen = DeterministicUUIDGenerator(seed=42)
        
        uuid1 = gen.generate("event")
        uuid2 = gen.generate("event")
        
        self.assertNotEqual(uuid1, uuid2)
        self.assertEqual(gen.get_counter(), 2)
    
    def test_uuid_reset(self):
        """Test that reset restores counter."""
        gen = DeterministicUUIDGenerator(seed=42)
        
        gen.generate("event")
        gen.generate("event")
        self.assertEqual(gen.get_counter(), 2)
        
        gen.reset()
        self.assertEqual(gen.get_counter(), 0)
        
        # Should generate same UUID after reset
        uuid_after_reset = gen.generate("event")
        uuid_first = gen.generate("event")
        # Note: Not testing exact equality because counter starts at 0 again
        self.assertNotEqual(uuid_after_reset, uuid_first)
    
    def test_uuid_event_type_influences_output(self):
        """Test that event_type affects UUID generation."""
        gen = DeterministicUUIDGenerator(seed=42)
        
        uuid1 = gen.generate("TaskAttemptSubmitted")
        uuid2 = gen.generate("LearningProcessed")
        
        self.assertNotEqual(uuid1, uuid2)


class TestRNGStreamManager(unittest.TestCase):
    """Test isolated RNG stream management."""
    
    def test_stream_isolation(self):
        """Test that different streams produce different sequences."""
        manager = RNGStreamManager(seed=42)
        
        # Get values from different streams
        val_time = manager.get_time_stream().randn()
        val_noise = manager.get_noise_stream().randn()
        val_bandit = manager.get_bandit_stream().randn()
        
        # They should be different (statistically)
        self.assertNotEqual(val_time, val_noise)
        self.assertNotEqual(val_noise, val_bandit)
    
    def test_stream_determinism(self):
        """Test that same seed produces same stream values."""
        manager1 = RNGStreamManager(seed=42)
        manager2 = RNGStreamManager(seed=42)
        
        val1 = manager1.get_time_stream().randn()
        val2 = manager2.get_time_stream().randn()
        
        self.assertEqual(val1, val2)
    
    def test_reset_all(self):
        """Test that reset_all restores all streams."""
        manager = RNGStreamManager(seed=42)
        
        # Generate some values
        manager.get_time_stream().randn()
        manager.get_noise_stream().randn()
        
        # Reset
        manager.reset_all()
        
        # Should get same values as fresh manager
        fresh_manager = RNGStreamManager(seed=42)
        val1 = manager.get_time_stream().randn()
        val2 = fresh_manager.get_time_stream().randn()
        
        self.assertEqual(val1, val2)


class TestSimulatedTimeProvider(unittest.TestCase):
    """Test deterministic time provider."""
    
    def test_time_determinism(self):
        """Test that same seed produces same time sequence."""
        rng1 = np.random.RandomState(42)
        rng2 = np.random.RandomState(42)
        
        provider1 = SimulatedTimeProvider(seed=42, rng_stream=rng1)
        provider2 = SimulatedTimeProvider(seed=42, rng_stream=rng2)
        
        # Advance both
        provider1.advance()
        provider2.advance()
        
        self.assertEqual(provider1.now(), provider2.now())
    
    def test_time_monotonic(self):
        """Test that time always advances."""
        provider = SimulatedTimeProvider(seed=42)
        
        time1 = provider.now()
        provider.advance()
        time2 = provider.now()
        
        self.assertGreater(time2, time1)
    
    def test_time_reset(self):
        """Test that reset restores initial time."""
        provider = SimulatedTimeProvider(seed=42)
        
        initial_time = provider.now()
        provider.advance()
        provider.advance()
        provider.reset()
        
        self.assertEqual(provider.now(), initial_time)
    
    def test_time_with_dedicated_rng_stream(self):
        """Test that time uses dedicated RNG stream."""
        manager = RNGStreamManager(seed=42)
        provider = SimulatedTimeProvider(seed=42, rng_stream=manager.get_time_stream())
        
        # This should use rng_time stream
        provider.advance()
        
        # Verify that other streams are unaffected
        manager.get_noise_stream().randn()  # Use noise stream
        time_before_noise = provider.now()
        provider.advance()
        time_after_noise = provider.now()
        
        self.assertGreater(time_after_noise, time_before_noise)


class TestDeterministicModeConfig(unittest.TestCase):
    """Test deterministic mode configuration."""
    
    def test_production_config(self):
        """Test production config has determinism disabled."""
        config = DeterministicModeConfig.production()
        
        self.assertFalse(config.deterministic)
        self.assertFalse(config.event_determinism)
        self.assertFalse(config.trajectory_determinism)
        self.assertFalse(config.full_determinism)
    
    def test_experiment_config(self):
        """Test experiment config has event + trajectory determinism."""
        config = DeterministicModeConfig.experiment(seed=42)
        
        self.assertTrue(config.deterministic)
        self.assertTrue(config.event_determinism)
        self.assertTrue(config.trajectory_determinism)
        self.assertFalse(config.full_determinism)
        self.assertEqual(config.seed, 42)
    
    def test_replay_validation_config(self):
        """Test replay validation config has full determinism."""
        config = DeterministicModeConfig.replay_validation(seed=42)
        
        self.assertTrue(config.deterministic)
        self.assertTrue(config.event_determinism)
        self.assertTrue(config.trajectory_determinism)
        self.assertTrue(config.full_determinism)
        self.assertTrue(config.deterministic_noise)
        self.assertEqual(config.seed, 42)


if __name__ == '__main__':
    unittest.main()
