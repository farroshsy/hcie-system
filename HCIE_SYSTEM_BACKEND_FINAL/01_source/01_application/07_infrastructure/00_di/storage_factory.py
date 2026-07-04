"""Storage factories.

Each factory returns a concrete store that already satisfies the protocols
defined in `01_source/00_core/00_interfaces/07_storage_ports.py` (verified by
`tools/migrate/check_protocols.py`).
"""

from __future__ import annotations

from typing import Any


def build_redis_store() -> Any:
    """Return a `RedisFeatureStore` instance.

    Satisfies `KVStoreProtocol`, `MasteryStoreProtocol`,
    `BanditParamsStoreProtocol`, and `UserContextStoreProtocol`.
    """
    from storage.redis_store.redis_store import RedisFeatureStore
    return RedisFeatureStore()


def build_postgres_store() -> Any:
    """Return a `PostgresInteractionStore` instance.

    Satisfies `InteractionWriteStoreProtocol` and `SQLExecStoreProtocol`.
    """
    from storage.postgres_store.interaction_store import PostgresInteractionStore
    return PostgresInteractionStore()
