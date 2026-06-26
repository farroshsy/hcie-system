"""Config provider port for Phase 5 config consolidation.

Historically, core / application modules read configuration two ways:

1. `from config.settings import settings` (a global `pydantic-settings`
   `Settings` object), or
2. direct `os.getenv("KEY", default)` calls scattered through individual
   files.

Both styles couple business logic to a specific configuration mechanism
and make tests harder to write deterministically. The protocol below
gives core code a single, narrow read-only contract; concrete adapters
in the application composition root (`01_application/07_infrastructure/00_di/config_factory.py`)
back it with the live `Settings` object plus an `os.environ` overlay.

Design choices:

- Read-only: configuration is set at process boot via the factory; core
  code never writes.
- Typed accessors (`get_int`, `get_float`, `get_bool`, `get_str`) so
  call sites don't repeat `int(provider.get(...))` boilerplate.
- `snapshot()` returns a flat mapping so debug / audit code can dump the
  full effective config without leaking the underlying object.
- Phase 5 deliberately omits a `SecretResolverProtocol`. Secret-shaped
  values (e.g. database URLs containing credentials) continue to flow
  through `get_str()` until Phase 8 introduces a dedicated secrets API.
"""

from __future__ import annotations

from typing import Any, Mapping, Protocol, runtime_checkable


@runtime_checkable
class ConfigProviderProtocol(Protocol):
    """Read-only, typed configuration access for core code."""

    def get(self, key: str, default: Any = None) -> Any:
        """Return the raw value at `key` or `default` if absent."""
        ...

    def get_int(self, key: str, default: int = 0) -> int:
        """Return `key` coerced to int; falls back to `default` on absence
        or coercion failure."""
        ...

    def get_float(self, key: str, default: float = 0.0) -> float:
        """Return `key` coerced to float; falls back to `default` on
        absence or coercion failure."""
        ...

    def get_bool(self, key: str, default: bool = False) -> bool:
        """Return `key` coerced to bool. Truthy strings ("1", "true",
        "yes", "on" -- case-insensitive) map to True; absent keys return
        `default`."""
        ...

    def get_str(self, key: str, default: str = "") -> str:
        """Return `key` as string; falls back to `default` on absence."""
        ...

    def snapshot(self) -> Mapping[str, Any]:
        """Return a flat mapping of every effective key -> value.

        Implementations should return a defensive copy; mutations on the
        result must not affect the provider's internal state.
        """
        ...
