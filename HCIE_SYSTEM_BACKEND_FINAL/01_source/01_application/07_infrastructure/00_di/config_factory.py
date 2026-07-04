"""Configuration provider factory for Phase 5.

Implements two `ConfigProviderProtocol` adapters:

- `PydanticSettingsConfigProvider`: wraps a `pydantic-settings` `Settings`
  instance and exposes its fields through the protocol surface.
- `EnvOverlayConfigProvider`: layers `os.environ` on top of any other
  provider, preserving the BACKENDV2 contract that env vars beat file
  defaults.

`build_config_provider()` composes them into the canonical runtime
provider. If the live `config.env.load_settings()` entrypoint is not
importable (e.g. unit tests, fresh checkout without BACKENDV2 on
`sys.path`), the factory degrades to a pure-env provider rather than
failing at boot.

The factory deliberately avoids touching core. Core depends only on
`ConfigProviderProtocol`; the wiring lives here.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Mapping, Optional

logger = logging.getLogger(__name__)


_TRUTHY = {"1", "true", "yes", "on", "y", "t"}
_FALSY = {"0", "false", "no", "off", "n", "f"}


def _coerce_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return bool(value)
    s = str(value).strip().lower()
    if s in _TRUTHY:
        return True
    if s in _FALSY:
        return False
    return default


def _coerce_int(value: Any, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _coerce_float(value: Any, default: float) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


class PydanticSettingsConfigProvider:
    """Adapter wrapping a pydantic-settings `Settings` instance.

    Field lookup falls back through the lower-case attribute name then
    the upper-case one (matching BACKENDV2's case-insensitive policy).
    """

    def __init__(self, settings: Any) -> None:
        self._settings = settings

    def _resolve(self, key: str) -> Any:
        for candidate in (key, key.lower(), key.upper()):
            if hasattr(self._settings, candidate):
                return getattr(self._settings, candidate)
        return None

    def get(self, key: str, default: Any = None) -> Any:
        v = self._resolve(key)
        return v if v is not None else default

    def get_int(self, key: str, default: int = 0) -> int:
        return _coerce_int(self._resolve(key), default)

    def get_float(self, key: str, default: float = 0.0) -> float:
        return _coerce_float(self._resolve(key), default)

    def get_bool(self, key: str, default: bool = False) -> bool:
        return _coerce_bool(self._resolve(key), default)

    def get_str(self, key: str, default: str = "") -> str:
        v = self._resolve(key)
        return default if v is None else str(v)

    def snapshot(self) -> Mapping[str, Any]:
        # pydantic v1 and v2 both expose `.dict()` / `.model_dump()`.
        for accessor in ("model_dump", "dict"):
            fn = getattr(self._settings, accessor, None)
            if callable(fn):
                try:
                    return dict(fn())
                except Exception:
                    continue
        return {k: getattr(self._settings, k) for k in dir(self._settings)
                if not k.startswith("_") and not callable(getattr(self._settings, k))}


class EnvOverlayConfigProvider:
    """Overlay provider: env vars (uppercased key) beat the base provider.

    The base provider is consulted only when the env var is unset, so
    operator overrides via `KEY=value` always win without rebuilding the
    base Settings object.
    """

    def __init__(self, base: Any, env: Optional[Dict[str, str]] = None) -> None:
        self._base = base
        self._env = env if env is not None else os.environ

    def _env_lookup(self, key: str) -> Optional[str]:
        for candidate in (key.upper(), key, key.lower()):
            if candidate in self._env:
                return self._env[candidate]
        return None

    def get(self, key: str, default: Any = None) -> Any:
        env_v = self._env_lookup(key)
        if env_v is not None:
            return env_v
        return self._base.get(key, default)

    def get_int(self, key: str, default: int = 0) -> int:
        env_v = self._env_lookup(key)
        if env_v is not None:
            return _coerce_int(env_v, default)
        return self._base.get_int(key, default)

    def get_float(self, key: str, default: float = 0.0) -> float:
        env_v = self._env_lookup(key)
        if env_v is not None:
            return _coerce_float(env_v, default)
        return self._base.get_float(key, default)

    def get_bool(self, key: str, default: bool = False) -> bool:
        env_v = self._env_lookup(key)
        if env_v is not None:
            return _coerce_bool(env_v, default)
        return self._base.get_bool(key, default)

    def get_str(self, key: str, default: str = "") -> str:
        env_v = self._env_lookup(key)
        if env_v is not None:
            return env_v
        return self._base.get_str(key, default)

    def snapshot(self) -> Mapping[str, Any]:
        merged: Dict[str, Any] = dict(self._base.snapshot())
        for k, v in self._env.items():
            merged[k] = v
        return merged


class _EnvOnlyProvider:
    """Fallback provider used when no live Settings object is available.

    Consulted via `EnvOverlayConfigProvider` so behaviour mirrors the
    operator-override semantics of the real wiring.
    """

    def get(self, key: str, default: Any = None) -> Any:
        return os.environ.get(key.upper(), default)

    def get_int(self, key: str, default: int = 0) -> int:
        return _coerce_int(os.environ.get(key.upper()), default)

    def get_float(self, key: str, default: float = 0.0) -> float:
        return _coerce_float(os.environ.get(key.upper()), default)

    def get_bool(self, key: str, default: bool = False) -> bool:
        return _coerce_bool(os.environ.get(key.upper()), default)

    def get_str(self, key: str, default: str = "") -> str:
        return os.environ.get(key.upper(), default)

    def snapshot(self) -> Mapping[str, Any]:
        return dict(os.environ)


def build_config_provider(*, settings: Any = None) -> EnvOverlayConfigProvider:
    """Build the canonical config provider for the live runtime.

    If `settings` is provided, it is wrapped directly. Otherwise the
    factory imports `config.env.load_settings()` (the BACKENDV2 env
    loader). If that import fails -- typical in unit tests -- a pure-env
    provider is used so the rest of the system keeps booting.
    """
    if settings is None:
        try:
            from config.env import load_settings
            settings = load_settings()
        except Exception as exc:
            logger.warning(
                "build_config_provider: live Settings unavailable (%s); "
                "falling back to env-only provider", exc,
            )
            return EnvOverlayConfigProvider(_EnvOnlyProvider())

    base = PydanticSettingsConfigProvider(settings)
    return EnvOverlayConfigProvider(base)
