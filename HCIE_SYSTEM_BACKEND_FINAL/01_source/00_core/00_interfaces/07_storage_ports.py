"""Storage-facing dependency ports for Phase 3 layer cleanup.

Each protocol below was derived from observed usage in the FINAL core tree,
not from a generic CRUD template, so the existing `RedisFeatureStore` and
`PostgresInteractionStore` implementations can satisfy these contracts with
zero rename. The protocols follow Interface Segregation: a core component
depends only on the narrow port it needs, e.g. `MasteryStoreProtocol` for
learners, `AnalyticsQueryProtocol` for analytics views.

Observed usage sources (FINAL tree):

- `RedisFeatureStore.get_value / set_value / get_mastery / set_mastery /
  update_mastery_absolute / get_user_mastery / get_bandit_params /
  get_user_context / update_user_context` — see core/04_learners,
  core/05_engines, core/06_transfer, core/09_validation.
- `PostgresInteractionStore.execute_read / execute_write /
  save_interaction / get_user_interactions / get_interactions_for_analysis`
  — see core/07_bandit, core/03_ensemble.
- Analytics modules (`core/16_analytics/*`) depend on a different injected
  `_db_store` that exposes only `fetch_all(query, params)`. That is its
  own narrow port.

Out of scope for these protocols (deliberately):

- Raw `redis_client.*` access used in `09_validation/idempotency_manager.py`,
  `05_engines/learner.py`, and `05_engines/engine.py`. Those call sites need
  a dedicated `IdempotencyKeyStoreProtocol` (and a follow-up code-level
  refactor) before the raw Redis client can be hidden.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Protocol, Sequence, Tuple, Union, runtime_checkable


@runtime_checkable
class KVStoreProtocol(Protocol):
    """Minimal key-value port matching `RedisFeatureStore.{get_value,set_value}`.

    Method names are aligned with the existing implementation to avoid any
    rename in `storage/redis_store/redis_store.py`.
    """

    def get_value(self, key: str) -> Any:
        ...

    def set_value(self, key: str, value: Any, expire_seconds: Optional[int] = None) -> Any:
        ...


@runtime_checkable
class MasteryStoreProtocol(Protocol):
    """Per-user, per-concept Bayesian mastery storage.

    Aligned with `RedisFeatureStore.{get_mastery, set_mastery,
    update_mastery_absolute, get_user_mastery}`.
    """

    def get_mastery(self, user_id: str, node: str) -> Tuple[float, float]:
        ...

    def set_mastery(self, user_id: str, concept: str, mastery: float) -> Any:
        ...

    def update_mastery_absolute(self, user_id: str, node: str, alpha: float, beta: float) -> Any:
        ...

    def get_user_mastery(
        self, user_id: str, concept_id: Optional[str] = None
    ) -> Dict[str, float]:
        ...


@runtime_checkable
class BanditParamsStoreProtocol(Protocol):
    """Redis-side bandit parameter access.

    Aligned with `RedisFeatureStore.{get_bandit_params, get_representation,
    update_representation}`.
    """

    def get_bandit_params(self, user_id: str, arm: str) -> Tuple[float, float]:
        ...

    def get_representation(self, user_id: str, arm: str) -> Tuple[float, float]:
        ...

    def update_representation(self, user_id: str, arm: str, reward: float) -> Any:
        ...


@runtime_checkable
class UserContextStoreProtocol(Protocol):
    """Per-user context cache.

    Aligned with `RedisFeatureStore.{get_user_context, update_user_context}`.
    """

    def get_user_context(self, user_id: str) -> Dict[str, Any]:
        ...

    def update_user_context(self, user_id: str, context: Dict[str, Any]) -> Any:
        ...


@runtime_checkable
class InteractionWriteStoreProtocol(Protocol):
    """Interaction persistence.

    Aligned with `PostgresInteractionStore.{save_interaction,
    get_user_interactions, get_interactions_for_analysis}`.
    """

    def save_interaction(self, interaction_data: Mapping[str, Any]) -> bool:
        ...

    def get_user_interactions(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        ...

    def get_interactions_for_analysis(self, limit: int = 1000) -> List[Dict[str, Any]]:
        ...


@runtime_checkable
class SQLExecStoreProtocol(Protocol):
    """Generic SQL execution port for code that issues hand-written queries.

    Aligned with `PostgresInteractionStore.{execute_read, execute_write}`.
    Used by `core/07_bandit/bandit.py`, `core/07_bandit/transfer_aware_bandit.py`,
    and `core/18_session/brain_bridge_service.py` (the bridge is queued for
    reclassification into the application layer).
    """

    def execute_read(
        self,
        query: str,
        params: Optional[tuple] = None,
        fetch_one: bool = False,
    ) -> Optional[Union[Dict[str, Any], List[Dict[str, Any]]]]:
        ...

    def execute_write(
        self,
        query: str,
        params: Optional[tuple] = None,
        fetch_one: bool = False,
        timeout_ms: int = 30000,
    ) -> Optional[Union[Dict[str, Any], List[Dict[str, Any]]]]:
        ...


@runtime_checkable
class AnalyticsQueryProtocol(Protocol):
    """Read-only analytical query port.

    Used in `core/16_analytics/*` via the injected `self._db_store.fetch_all(...)`
    surface. Concrete implementations live in
    `01_source/02_infrastructure/01_storage/00_postgresql/`.
    """

    def fetch_all(
        self,
        query: str,
        params: Optional[Sequence[Any]] = None,
    ) -> List[Dict[str, Any]]:
        ...
