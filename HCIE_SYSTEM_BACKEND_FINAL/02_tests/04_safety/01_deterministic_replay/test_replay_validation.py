"""
Priority 1 Validation Test

Validates deterministic components work correctly for replay:
- UUID determinism: same seed → same UUIDs
- Time determinism: same seed → same timestamps
- RNG stream isolation: separate streams don't interfere
- Full deterministic replay: reset → same sequence
"""
import unittest
from core.determinism.deterministic_uuid import DeterministicUUIDGenerator
from core.determinism.rng_stream_manager import RNGStreamManager
from core.determinism.simulated_time import SimulatedTimeProvider
from core.determinism.deterministic_config import DeterministicModeConfig


class TestPriority1Validation(unittest.TestCase):
    """Test Priority 1 deterministic replay capabilities."""
    
    def test_full_deterministic_replay_scenario(self):
        """Test complete deterministic replay scenario with all components."""
        # Simulate a deterministic replay scenario
        seed = 42
        
        # First run
        uuid_gen1 = DeterministicUUIDGenerator(seed=seed)
        rng_manager1 = RNGStreamManager(seed=seed)
        time_provider1 = SimulatedTimeProvider(
            seed=seed,
            rng_stream=rng_manager1.get_time_stream()
        )
        
        # Generate deterministic sequence
        sequence1 = []
        for i in range(10):
            event_id = str(uuid_gen1.generate(event_type="TaskAttemptSubmitted"))
            timestamp = time_provider1.now()
            time_provider1.advance()
            bandit_val = rng_manager1.get_bandit_stream().randn()
            noise_val = rng_manager1.get_noise_stream().randn()
            sequence1.append({
                "event_id": event_id,
                "timestamp": timestamp,
                "bandit_val": bandit_val,
                "noise_val": noise_val
            })
        
        # Reset and run again (simulating replay)
        uuid_gen2 = DeterministicUUIDGenerator(seed=seed)
        rng_manager2 = RNGStreamManager(seed=seed)
        time_provider2 = SimulatedTimeProvider(
            seed=seed,
            rng_stream=rng_manager2.get_time_stream()
        )
        
        sequence2 = []
        for i in range(10):
            event_id = str(uuid_gen2.generate(event_type="TaskAttemptSubmitted"))
            timestamp = time_provider2.now()
            time_provider2.advance()
            bandit_val = rng_manager2.get_bandit_stream().randn()
            noise_val = rng_manager2.get_noise_stream().randn()
            sequence2.append({
                "event_id": event_id,
                "timestamp": timestamp,
                "bandit_val": bandit_val,
                "noise_val": noise_val
            })
        
        # Verify deterministic replay
        self.assertEqual(len(sequence1), len(sequence2))
        for i, (item1, item2) in enumerate(zip(sequence1, sequence2)):
            self.assertEqual(item1["event_id"], item2["event_id"],
                           f"Event ID mismatch at step {i}")
            self.assertEqual(item1["timestamp"], item2["timestamp"],
                           f"Timestamp mismatch at step {i}")
            self.assertEqual(item1["bandit_val"], item2["bandit_val"],
                           f"Bandit value mismatch at step {i}")
            self.assertEqual(item1["noise_val"], item2["noise_val"],
                           f"Noise value mismatch at step {i}")
    
    def test_rng_stream_isolation_during_replay(self):
        """Test that RNG streams remain isolated during replay."""
        seed = 42
        
        # First run
        rng_manager1 = RNGStreamManager(seed=seed)
        time_stream1 = rng_manager1.get_time_stream()
        bandit_stream1 = rng_manager1.get_bandit_stream()
        noise_stream1 = rng_manager1.get_noise_stream()
        
        # Generate values from each stream
        time_vals1 = [time_stream1.randn() for _ in range(5)]
        bandit_vals1 = [bandit_stream1.randn() for _ in range(5)]
        noise_vals1 = [noise_stream1.randn() for _ in range(5)]
        
        # Reset and replay
        rng_manager2 = RNGStreamManager(seed=seed)
        time_stream2 = rng_manager2.get_time_stream()
        bandit_stream2 = rng_manager2.get_bandit_stream()
        noise_stream2 = rng_manager2.get_noise_stream()
        
        time_vals2 = [time_stream2.randn() for _ in range(5)]
        bandit_vals2 = [bandit_stream2.randn() for _ in range(5)]
        noise_vals2 = [noise_stream2.randn() for _ in range(5)]
        
        # Verify each stream reproduces same sequence
        self.assertEqual(time_vals1, time_vals2, "Time stream should be deterministic")
        self.assertEqual(bandit_vals1, bandit_vals2, "Bandit stream should be deterministic")
        self.assertEqual(noise_vals1, noise_vals2, "Noise stream should be deterministic")
        
        # Verify streams are isolated (different sequences)
        self.assertNotEqual(time_vals1, bandit_vals1, "Time and bandit streams should differ")
        self.assertNotEqual(bandit_vals1, noise_vals1, "Bandit and noise streams should differ")
    
    def test_config_modes(self):
        """Test that different config modes work correctly."""
        # Production mode - determinism disabled
        prod_config = DeterministicModeConfig.production()
        self.assertFalse(prod_config.deterministic)
        self.assertFalse(prod_config.event_determinism)
        
        # Experiment mode - event + trajectory determinism
        exp_config = DeterministicModeConfig.experiment(seed=42)
        self.assertTrue(exp_config.deterministic)
        self.assertTrue(exp_config.event_determinism)
        self.assertTrue(exp_config.trajectory_determinism)
        self.assertFalse(exp_config.full_determinism)
        
        # Replay validation mode - full determinism
        replay_config = DeterministicModeConfig.replay_validation(seed=42)
        self.assertTrue(replay_config.deterministic)
        self.assertTrue(replay_config.event_determinism)
        self.assertTrue(replay_config.trajectory_determinism)
        self.assertTrue(replay_config.full_determinism)
        self.assertTrue(replay_config.deterministic_noise)


if __name__ == '__main__':
    unittest.main()
