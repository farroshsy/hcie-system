"""Reward Components

Reward calculation surface for FINAL. CT reward variant was retired in
Phase 14c (CT vocabulary superseded by K-12 DAG seeded by alembic
009_seed_k12_concepts / 010_seed_k12_tasks). See
99_legacy_quarantine/phase14c_ct_legacy/.
"""

from .reward import RewardCalculator

__all__ = ["RewardCalculator"]
