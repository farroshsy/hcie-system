"""In-memory protocol fakes for Phase 4 unit tests.

These fakes satisfy the protocols defined in
`01_source/00_core/00_interfaces/{07_storage_ports,08_idempotency_ports}.py`.
They are deliberately small, dependency-free, and deterministic so that
core unit tests can run without booting Redis, Postgres, or Kafka.

Naming follows the protocol name + `Fake` prefix:

    FakeKVStore                    -> KVStoreProtocol
    FakeMasteryStore               -> MasteryStoreProtocol
    FakeBanditParamsStore          -> BanditParamsStoreProtocol
    FakeUserContextStore           -> UserContextStoreProtocol
    FakeInteractionWriteStore      -> InteractionWriteStoreProtocol
    FakeSQLExecStore               -> SQLExecStoreProtocol
    FakeAnalyticsQueryStore        -> AnalyticsQueryProtocol
    FakeIdempotencyKeyStore        -> IdempotencyKeyStoreProtocol

The fakes do *not* import from FINAL on purpose -- that keeps the unit
test substrate from depending on import resolution of numbered packages.
"""

from __future__ import annotations

import fnmatch
import threading
import time
from typing import Any, Dict, Iterator, List, Mapping, Optional, Sequence, Tuple, Union


class FakeKVStore:
    """KVStoreProtocol fake."""

    def __init__(self) -> None:
        self._data: Dict[str, Tuple[Any, Optional[float]]] = {}
        self._lock = threading.Lock()

    def _expired(self, key: str) -> bool:
        v = self._data.get(key)
        if v is None:
            return True
        _, exp = v
        return exp is not None and exp < time.monotonic()

    def get_value(self, key: str) -> Any:
        with self._lock:
            if self._expired(key):
                self._data.pop(key, None)
                return None
            return self._data[key][0]

    def set_value(self, key: str, value: Any, expire_seconds: Optional[int] = None) -> Any:
        exp = time.monotonic() + expire_seconds if expire_seconds else None
        with self._lock:
            self._data[key] = (value, exp)
            return True


class FakeMasteryStore:
    """MasteryStoreProtocol fake.

    Mastery is stored as a Beta(alpha, beta) pair; `set_mastery` and
    `update_mastery_absolute` write tuples; `get_mastery` returns them.
    """

    def __init__(self) -> None:
        self._mastery: Dict[Tuple[str, str], Tuple[float, float]] = {}

    def get_mastery(self, user_id: str, node: str) -> Tuple[float, float]:
        return self._mastery.get((user_id, node), (1.0, 1.0))

    def set_mastery(self, user_id: str, concept: str, mastery: float) -> Any:
        self._mastery[(user_id, concept)] = (mastery, 1.0 - mastery)
        return True

    def update_mastery_absolute(self, user_id: str, node: str, alpha: float, beta: float) -> Any:
        self._mastery[(user_id, node)] = (alpha, beta)
        return True

    def get_user_mastery(
        self, user_id: str, concept_id: Optional[str] = None
    ) -> Dict[str, float]:
        if concept_id is not None:
            a, b = self._mastery.get((user_id, concept_id), (1.0, 1.0))
            return {concept_id: a / (a + b)}
        return {
            c: a / (a + b)
            for (u, c), (a, b) in self._mastery.items()
            if u == user_id
        }


class FakeBanditParamsStore:
    """BanditParamsStoreProtocol fake."""

    def __init__(self) -> None:
        self._params: Dict[Tuple[str, str], Tuple[float, float]] = {}

    def get_bandit_params(self, user_id: str, arm: str) -> Tuple[float, float]:
        return self._params.get((user_id, arm), (1.0, 1.0))

    def get_representation(self, user_id: str, arm: str) -> Tuple[float, float]:
        return self._params.get((user_id, arm), (1.0, 1.0))

    def update_representation(self, user_id: str, arm: str, reward: float) -> Any:
        a, b = self._params.get((user_id, arm), (1.0, 1.0))
        self._params[(user_id, arm)] = (a + reward, b + (1.0 - reward))
        return True


class FakeUserContextStore:
    """UserContextStoreProtocol fake."""

    def __init__(self) -> None:
        self._ctx: Dict[str, Dict[str, Any]] = {}

    def get_user_context(self, user_id: str) -> Dict[str, Any]:
        return dict(self._ctx.get(user_id, {}))

    def update_user_context(self, user_id: str, context: Dict[str, Any]) -> Any:
        self._ctx.setdefault(user_id, {}).update(context)
        return True


class FakeInteractionWriteStore:
    """InteractionWriteStoreProtocol fake."""

    def __init__(self) -> None:
        self.interactions: List[Dict[str, Any]] = []

    def save_interaction(self, interaction_data: Mapping[str, Any]) -> bool:
        self.interactions.append(dict(interaction_data))
        return True

    def get_user_interactions(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        out = [i for i in self.interactions if i.get("user_id") == user_id]
        return out[-limit:]

    def get_interactions_for_analysis(self, limit: int = 1000) -> List[Dict[str, Any]]:
        return self.interactions[-limit:]


class FakeSQLExecStore:
    """SQLExecStoreProtocol fake.

    Records every (query, params) call for assertion. Returns None by
    default; tests can call `queue_read(rows)` / `queue_write(rows)` to
    pre-stage results in FIFO order.
    """

    def __init__(self) -> None:
        self.reads: List[Tuple[str, Optional[tuple], bool]] = []
        self.writes: List[Tuple[str, Optional[tuple], bool, int]] = []
        self._read_queue: List[Any] = []
        self._write_queue: List[Any] = []

    def queue_read(self, result: Any) -> None:
        self._read_queue.append(result)

    def queue_write(self, result: Any) -> None:
        self._write_queue.append(result)

    def execute_read(
        self,
        query: str,
        params: Optional[tuple] = None,
        fetch_one: bool = False,
    ) -> Optional[Union[Dict[str, Any], List[Dict[str, Any]]]]:
        self.reads.append((query, params, fetch_one))
        if self._read_queue:
            return self._read_queue.pop(0)
        return None

    def execute_write(
        self,
        query: str,
        params: Optional[tuple] = None,
        fetch_one: bool = False,
        timeout_ms: int = 30000,
    ) -> Optional[Union[Dict[str, Any], List[Dict[str, Any]]]]:
        self.writes.append((query, params, fetch_one, timeout_ms))
        if self._write_queue:
            return self._write_queue.pop(0)
        return None


class FakeAnalyticsQueryStore:
    """AnalyticsQueryProtocol fake."""

    def __init__(self) -> None:
        self.queries: List[Tuple[str, Optional[Sequence[Any]]]] = []
        self._queue: List[List[Dict[str, Any]]] = []

    def queue_rows(self, rows: List[Dict[str, Any]]) -> None:
        self._queue.append(rows)

    def fetch_all(
        self,
        query: str,
        params: Optional[Sequence[Any]] = None,
    ) -> List[Dict[str, Any]]:
        self.queries.append((query, params))
        if self._queue:
            return self._queue.pop(0)
        return []


class FakeIdempotencyKeyStore:
    """IdempotencyKeyStoreProtocol fake.

    Models a Redis-like KV with TTL semantics in-memory. TTLs are honoured
    via `time.monotonic()`. `set_if_absent_with_ttl` is the lock-acquire
    primitive; `set_with_ttl_batch` is atomic with respect to other calls
    on this fake.
    """

    def __init__(self) -> None:
        self._store: Dict[str, Tuple[str, float]] = {}
        self._lock = threading.Lock()

    def _is_alive(self, key: str) -> bool:
        v = self._store.get(key)
        if v is None:
            return False
        _, exp = v
        if exp < time.monotonic():
            self._store.pop(key, None)
            return False
        return True

    def get_value(self, key: str) -> Any:
        with self._lock:
            return self._store[key][0] if self._is_alive(key) else None

    def set_with_ttl(self, key: str, value: str, ttl_seconds: int) -> None:
        with self._lock:
            self._store[key] = (value, time.monotonic() + ttl_seconds)

    def set_with_ttl_batch(self, items: Sequence[Tuple[str, str, int]]) -> None:
        with self._lock:
            now = time.monotonic()
            for k, v, ttl in items:
                self._store[k] = (v, now + ttl)

    def set_if_absent_with_ttl(self, key: str, value: str, ttl_seconds: int) -> bool:
        with self._lock:
            if self._is_alive(key):
                return False
            self._store[key] = (value, time.monotonic() + ttl_seconds)
            return True

    def delete(self, key: str) -> bool:
        with self._lock:
            return self._store.pop(key, None) is not None

    def scan_keys(self, pattern: str) -> Iterator[str]:
        with self._lock:
            keys = [k for k in self._store.keys() if fnmatch.fnmatch(k, pattern)]
        for k in keys:
            yield k
