"""Normalize interaction outcome keys for UnifiedLearningBrain and trajectory recording.

Copied from `HCIE_SYSTEM_BACKENDV2/infrastructure/experiment/interaction_keys.py`.
This module is pure and belongs in core state semantics, not infrastructure.
The remaining Phase 3 step is to rewire the canonical `unified_brain.py`
imports to this helper through the import-rewrite pass.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


def interaction_is_correct(interaction: Optional[Dict[str, Any]], default: bool = False) -> bool:
    """Read correctness from ``correct`` or ``correctness``."""
    if not interaction:
        return default
    if interaction.get("correct") is not None:
        return bool(interaction.get("correct"))
    if interaction.get("correctness") is not None:
        return bool(interaction.get("correctness"))
    return default


def normalize_interaction_for_brain(interaction: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure both ``correct`` and ``correctness`` are set when either is present.

    UnifiedLearningBrain and learners read ``correct``; trajectory DB uses ``correctness``.
    """
    normalized = dict(interaction)
    if normalized.get("correct") is not None:
        normalized["correctness"] = bool(normalized["correct"])
    elif normalized.get("correctness") is not None:
        normalized["correct"] = bool(normalized["correctness"])
    return normalized
