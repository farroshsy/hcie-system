"""Idempotency key-store port for Phase 3 layer cleanup.

`core/09_validation/idempotency_manager.py` historically reached into
`self.redis_store.redis_client` to call low-level Redis primitives
(`pipeline()`, `set(nx=True, ex=...)`, `delete(...)`, `setex(...)`,
`scan_iter(...)`). Those operations are *semantic* idempotency operations,
not generic Redis features, so this port re-publishes them at the domain
level. A Redis-backed adapter (`RedisIdempotencyKeyStore`, defined in the
application composition root) satisfies the contract.

The protocol is intentionally minimal and matches Interface Segregation:
core code that already depends on a richer storage port (e.g. `KVStoreProtocol`
for read-by-key) should still depend on a separate handle for these
idempotency-specific operations. That keeps `RedisFeatureStore` from leaking
its `redis_client` attribute into core call sites.
"""

from __future__ import annotations

from typing import Any, Iterator, Protocol, Sequence, Tuple, runtime_checkable


@runtime_checkable
class IdempotencyKeyStoreProtocol(Protocol):
    """Narrow port for distributed idempotency / dedup operations."""

    def get_value(self, key: str) -> Any:
        """Return the value at `key`, or None if absent."""
        ...

    def set_with_ttl(self, key: str, value: str, ttl_seconds: int) -> None:
        """Unconditionally set `key=value` with an expiration window."""
        ...

    def set_with_ttl_batch(
        self,
        items: Sequence[Tuple[str, str, int]],
    ) -> None:
        """Atomically set a batch of `(key, value, ttl_seconds)` triples.

        Implementations must guarantee that either all triples are visible
        after the call or none of them are.
        """
        ...

    def set_if_absent_with_ttl(
        self,
        key: str,
        value: str,
        ttl_seconds: int,
    ) -> bool:
        """Try to set `key=value` only if `key` is currently absent.

        Returns True on success (lock acquired); False if the key already
        existed (someone else holds the lock).
        """
        ...

    def delete(self, key: str) -> bool:
        """Delete `key`. Returns True if a key was removed."""
        ...

    def scan_keys(self, pattern: str) -> Iterator[str]:
        """Iterate over keys matching `pattern` without blocking the server."""
        ...
