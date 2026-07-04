"""Redis-backed adapter for `IdempotencyKeyStoreProtocol`.

The adapter wraps a `RedisFeatureStore` and exposes only the narrow surface
that `core/09_validation/idempotency_manager.py` needs. Once injected, core
no longer reaches through `self.redis_store.redis_client` to call low-level
Redis primitives directly.
"""

from __future__ import annotations

from typing import Any, Iterator, Sequence, Tuple


class RedisIdempotencyKeyStore:
    """Concrete `IdempotencyKeyStoreProtocol` impl backed by `RedisFeatureStore`."""

    def __init__(self, redis_store: Any) -> None:
        self._redis_store = redis_store

    @property
    def _client(self) -> Any:
        client = getattr(self._redis_store, "redis_client", None)
        if client is None:
            raise RuntimeError(
                "RedisFeatureStore did not expose redis_client; cannot run idempotency operations"
            )
        return client

    def get_value(self, key: str) -> Any:
        return self._redis_store.get_value(key)

    def set_with_ttl(self, key: str, value: str, ttl_seconds: int) -> None:
        self._client.setex(key, ttl_seconds, value)

    def set_with_ttl_batch(
        self,
        items: Sequence[Tuple[str, str, int]],
    ) -> None:
        pipe = self._client.pipeline()
        for key, value, ttl_seconds in items:
            pipe.setex(key, ttl_seconds, value)
        pipe.execute()

    def set_if_absent_with_ttl(
        self,
        key: str,
        value: str,
        ttl_seconds: int,
    ) -> bool:
        result = self._client.set(key, value, nx=True, ex=ttl_seconds)
        return bool(result)

    def delete(self, key: str) -> bool:
        return self._client.delete(key) > 0

    def scan_keys(self, pattern: str) -> Iterator[str]:
        for key in self._client.scan_iter(match=pattern):
            yield key


def build_idempotency_key_store(redis_store: Any) -> RedisIdempotencyKeyStore:
    return RedisIdempotencyKeyStore(redis_store)
