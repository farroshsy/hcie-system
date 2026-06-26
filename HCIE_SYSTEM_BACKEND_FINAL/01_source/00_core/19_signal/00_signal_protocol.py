"""Protocol contract for `signal`.

Phase 2 scaffold. Concrete implementations live in sibling modules and are
constructed via `XX_factory.py`. Source of truth for the existing behaviour
is `HCIE_SYSTEM_BACKENDV2/core/signal/`.
"""

from __future__ import annotations

from typing import Any, Mapping, Protocol, runtime_checkable

@runtime_checkable
class SignalProtocol(Protocol):
    """Extract semantic + governance signals from raw interaction events."""

    def extract(self, interaction: Mapping[str, Any]) -> Mapping[str, Any]: ...
