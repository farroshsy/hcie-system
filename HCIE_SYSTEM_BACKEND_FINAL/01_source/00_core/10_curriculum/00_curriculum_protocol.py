"""Protocol contract for `curriculum`.

Phase 2 scaffold. Concrete implementations live in sibling modules and are
constructed via `XX_factory.py`. Source of truth for the existing behaviour
is `HCIE_SYSTEM_BACKENDV2/core/curriculum/`.
"""

from __future__ import annotations

from typing import Any, Mapping, Protocol, Sequence, runtime_checkable

@runtime_checkable
class CurriculumProtocol(Protocol):
    """Concept + task + difficulty ladder registry."""

    def concept(self, concept_id: str) -> Mapping[str, Any]: ...
    def tasks_for(self, concept_id: str) -> Sequence[Mapping[str, Any]]: ...
    def difficulty(self, task_id: str) -> float: ...
