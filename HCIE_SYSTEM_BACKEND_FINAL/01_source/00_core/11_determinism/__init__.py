"""
Deterministic Runtime Components

Provides deterministic replay capabilities for scientific reproducibility.

Components:
- DeterministicUUIDGenerator: Namespace-based UUID generation for replay stability
- SimulatedTimeProvider: Deterministic time advancement
- RNGStreamManager: Isolated RNG streams for different concerns
- DeterministicModeConfig: Configuration for opt-in deterministic mode

Architecture Principle:
- Determinism is opt-in (deterministic=False by default)
- RNG streams are isolated by concern (time, noise, bandit, exploration, uuid)
- UUIDs use namespace-based generation (not RNG-derived)
- PYTHONHASHSEED set externally (not in runtime init)
- Replay is lineage-sensitive, not just seed-based
"""
