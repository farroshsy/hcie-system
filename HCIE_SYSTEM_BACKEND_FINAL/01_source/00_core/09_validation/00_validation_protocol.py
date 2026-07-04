"""Protocol contract for `validation`.

Phase 2 scaffold. Concrete implementations live in sibling modules and are
constructed via `XX_factory.py`. Source of truth for the existing behaviour
is `HCIE_SYSTEM_BACKENDV2/core/learning/`.
"""

from __future__ import annotations

from typing import Any, Mapping, Protocol, runtime_checkable

@runtime_checkable
class ValidationProtocol(Protocol):
    """Validators (comparative, idempotency, schema)."""

    def validate(self, payload: Mapping[str, Any]) -> tuple[bool, list[str]]: ...
