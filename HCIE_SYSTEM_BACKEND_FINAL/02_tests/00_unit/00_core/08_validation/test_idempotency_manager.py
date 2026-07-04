"""Behavioural unit test for the refactored `IdempotencyManager`.

Phase 3 introduced `IdempotencyKeyStoreProtocol` and rewired
`idempotency_manager.py` so all Redis access goes through the port. This
test exercises that port end-to-end using `FakeIdempotencyKeyStore` --
no Redis required.

Covers:

- Constructor accepts `idempotency_store=` and rejects neither-arg.
- Constructor still accepts legacy `redis_store=` via the in-core
  adapter (`_LegacyRedisStoreAdapter`).
- `acquire_lock` / `release_lock` happy path + contention.
- `mark_processed` writes both keys atomically and is one-shot.
- `is_processed` reflects the write.
- `get_cached_result` returns the cached payload with default fields
  filled in.
- `mark_content_hash` writes a hash key.
"""

from __future__ import annotations

import pytest

from fakes import FakeIdempotencyKeyStore
from finals_loader import from_finals


@pytest.fixture(scope="module")
def idem_module():
    return from_finals("01_source/00_core/09_validation/idempotency_manager.py")


@pytest.fixture
def store() -> FakeIdempotencyKeyStore:
    return FakeIdempotencyKeyStore()


@pytest.fixture
def manager(idem_module, store):
    return idem_module.IdempotencyManager(idempotency_store=store, ttl_hours=1)


class TestConstructor:
    def test_requires_at_least_one_dependency(self, idem_module):
        with pytest.raises(RuntimeError):
            idem_module.IdempotencyManager()

    def test_accepts_idempotency_store(self, idem_module, store):
        mgr = idem_module.IdempotencyManager(idempotency_store=store)
        assert mgr.idempotency_store is store

    def test_legacy_redis_store_is_adapted(self, idem_module):
        class _DummyRedisClient:
            def setex(self, *a, **k):
                return True

            def set(self, *a, **k):
                return True

            def delete(self, *a, **k):
                return 1

            def scan_iter(self, **k):
                return iter([])

            def pipeline(self):
                class _P:
                    def setex(self, *a, **k):
                        return self

                    def execute(self):
                        return []

                return _P()

        class _DummyRedisStore:
            redis_client = _DummyRedisClient()

            def get_value(self, key):
                return None

        mgr = idem_module.IdempotencyManager(redis_store=_DummyRedisStore())
        # Legacy adapter satisfies the protocol surface.
        assert mgr.idempotency_store is not None
        assert hasattr(mgr.idempotency_store, "set_if_absent_with_ttl")


class TestLocks:
    def test_acquire_then_release(self, manager, store):
        assert manager.acquire_lock("evt-1") is True
        # Lock key is present.
        assert store.get_value("lock:evt-1") == "locked"
        assert manager.release_lock("evt-1") is True
        assert store.get_value("lock:evt-1") is None

    def test_contention(self, manager):
        assert manager.acquire_lock("evt-2") is True
        assert manager.acquire_lock("evt-2") is False

    def test_release_unknown_returns_false(self, manager):
        assert manager.release_lock("never-locked") is False


class TestMarkAndQueryProcessed:
    def test_round_trip(self, manager):
        assert manager.is_processed("evt-3") is False
        ok = manager.mark_processed("evt-3", {"mastery": 0.42})
        assert ok is True
        assert manager.is_processed("evt-3") is True

    def test_mark_is_one_shot(self, manager):
        manager.mark_processed("evt-4", {"mastery": 0.1})
        # Second call short-circuits because already processed.
        assert manager.mark_processed("evt-4", {"mastery": 0.2}) is False

    def test_cached_result_has_defaults(self, manager):
        manager.mark_processed("evt-5", {"mastery": 0.5})
        cached = manager.get_cached_result("evt-5")
        assert cached is not None
        # Defaults filled in by the manager:
        assert "ensemble_weights" in cached
        assert "policy" in cached
        assert "processing_time" in cached


class TestContentHash:
    def test_writes_hash_key(self, manager, store):
        ok = manager.mark_content_hash({"a": 1, "b": 2}, "evt-6")
        assert ok is True
        keys = list(store.scan_keys("hash:*"))
        assert len(keys) == 1
        assert store.get_value(keys[0]) == "evt-6"
