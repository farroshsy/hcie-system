"""Outbox factory.

Wraps `app/infrastructure/outbox/outbox_pattern.get_outbox_pattern` so callers
get a fully-constructed `OutboxPattern` bound to a Postgres store and an
optional event bus. Satisfies `OutboxPortProtocol` (see
`tools/migrate/check_protocols.py`).
"""

from __future__ import annotations

from typing import Any, Optional


def build_outbox(db_store: Any, event_bus: Optional[Any] = None) -> Any:
    from app.infrastructure.outbox.outbox_pattern import get_outbox_pattern
    return get_outbox_pattern(db_store, event_bus)
