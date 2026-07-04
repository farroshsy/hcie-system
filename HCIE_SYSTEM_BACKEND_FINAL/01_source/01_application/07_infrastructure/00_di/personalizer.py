"""Personalizer adapter.

`ColdStartOptimizer.get_personalized_mastery` is declared `@staticmethod` in
`01_source/00_core/12_mastery/cold_start_optimizer.py` (imported as
`core.mastery.cold_start_optimizer`). The core protocol
`PersonalizedMasteryProtocol` expects an instance-shaped contract so the
adapter below wraps the static call.

This is the canonical bridge between core's protocol contract and the live
implementation. If a future implementation becomes stateful the adapter
itself can grow without touching core.

Phase 14e audit slice relocated this from
`app.services.user_profiling.cold_start_optimizer` to its canonical home in
the `00_core/12_mastery/` slot (prior estimation is core math, not a service).
"""

from __future__ import annotations

from typing import Any, Optional


class StaticColdStartPersonalizer:
    """Instance-shaped adapter around `ColdStartOptimizer.get_personalized_mastery`."""

    def get_personalized_mastery(
        self,
        user_id: str,
        concept: str,
        user_profile: Optional[Any] = None,
    ) -> float:
        from core.mastery.cold_start_optimizer import ColdStartOptimizer
        return ColdStartOptimizer.get_personalized_mastery(user_id, concept, user_profile)


def build_personalizer() -> StaticColdStartPersonalizer:
    return StaticColdStartPersonalizer()
