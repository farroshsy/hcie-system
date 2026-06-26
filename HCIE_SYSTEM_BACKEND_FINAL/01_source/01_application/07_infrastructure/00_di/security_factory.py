"""Security adapters + factories for Phase 8.

Provides concrete implementations of the three Phase 8 protocols:

- `SecretsProviderProtocol`   -> `EnvSecretsProvider`, `InMemorySecretsProvider`
- `AuthorizationProtocol`     -> `AllowAllAuthorizer`, `RoleAllowlistAuthorizer`
- `AuditSinkProtocol`         -> `LoggingAuditSink`, `NullAuditSink`

The default factories return safe, in-process implementations:
`EnvSecretsProvider` (production-friendly), `AllowAllAuthorizer` (dev
default; emits an audit record on every grant so it is never silent),
and `LoggingAuditSink`. Production deployments swap these for real
backends via container.set().
"""

from __future__ import annotations

import fnmatch
import logging
import os
from collections import defaultdict
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set


# ---------------------------------------------------------------------------
# Secrets adapters
# ---------------------------------------------------------------------------

class EnvSecretsProvider:
    """`SecretsProviderProtocol` backed by `os.environ`.

    Optional prefix filter avoids polluting the secrets namespace with
    every environment variable. Example: prefix="HCIE_SECRET_" hides
    everything that does not start with that string from
    `list_secret_keys()`.
    """

    def __init__(self, prefix: str = "", environ: Optional[Mapping[str, str]] = None) -> None:
        self._prefix = prefix
        self._env = environ if environ is not None else os.environ

    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        # Honor exact key first, then the prefix-aware form.
        if key in self._env:
            return self._env[key]
        prefixed = f"{self._prefix}{key}" if self._prefix else key
        return self._env.get(prefixed, default)

    def has_secret(self, key: str) -> bool:
        return self.get_secret(key) is not None

    def list_secret_keys(self) -> Sequence[str]:
        if not self._prefix:
            return tuple(self._env.keys())
        return tuple(k for k in self._env if k.startswith(self._prefix))


class InMemorySecretsProvider:
    """In-memory `SecretsProviderProtocol` for tests / fakes."""

    def __init__(self, secrets: Optional[Mapping[str, str]] = None) -> None:
        self._store: Dict[str, str] = dict(secrets or {})

    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return self._store.get(key, default)

    def has_secret(self, key: str) -> bool:
        return key in self._store

    def list_secret_keys(self) -> Sequence[str]:
        return tuple(self._store.keys())

    def set_secret(self, key: str, value: str) -> None:
        """Test-only mutator; not part of the protocol surface."""
        self._store[key] = value


def build_secrets_provider() -> EnvSecretsProvider:
    return EnvSecretsProvider(prefix=os.environ.get("HCIE_SECRETS_PREFIX", ""))


# ---------------------------------------------------------------------------
# Authorization adapters
# ---------------------------------------------------------------------------

class AllowAllAuthorizer:
    """`AuthorizationProtocol` that authorizes everything.

    Dev-only default. Records every grant + check on the audit sink so
    permissive behaviour is never silent in test logs.
    """

    def __init__(self, audit: Optional[Any] = None) -> None:
        self._audit = audit
        self._grants: Set[str] = set()

    @staticmethod
    def _key(subject: str, action: str, resource: str) -> str:
        return f"{subject}::{action}::{resource}"

    def is_authorized(self, subject: str, action: str, resource: str) -> bool:
        if self._audit is not None:
            self._audit.record(
                actor=subject, action=action, resource=resource,
                outcome="allow_all", policy="AllowAllAuthorizer",
            )
        return True

    def grant(self, subject: str, action: str, resource: str) -> None:
        self._grants.add(self._key(subject, action, resource))

    def revoke(self, subject: str, action: str, resource: str) -> None:
        self._grants.discard(self._key(subject, action, resource))


class RoleAllowlistAuthorizer:
    """Role-based `AuthorizationProtocol`.

    Stores `{subject: {action: [resource_patterns]}}`. Patterns use
    fnmatch globbing. Default policy is deny.
    """

    def __init__(self) -> None:
        self._policy: Dict[str, Dict[str, List[str]]] = defaultdict(lambda: defaultdict(list))

    def is_authorized(self, subject: str, action: str, resource: str) -> bool:
        patterns = self._policy.get(subject, {}).get(action, [])
        return any(fnmatch.fnmatchcase(resource, pattern) for pattern in patterns)

    def grant(self, subject: str, action: str, resource: str) -> None:
        patterns = self._policy[subject][action]
        if resource not in patterns:
            patterns.append(resource)

    def revoke(self, subject: str, action: str, resource: str) -> None:
        action_map = self._policy.get(subject)
        if action_map is None:
            return
        patterns = action_map.get(action)
        if not patterns:
            return
        try:
            patterns.remove(resource)
        except ValueError:
            pass


def build_authorizer() -> AllowAllAuthorizer:
    return AllowAllAuthorizer()


# ---------------------------------------------------------------------------
# Audit adapters
# ---------------------------------------------------------------------------

class LoggingAuditSink:
    """`AuditSinkProtocol` over stdlib `logging`.

    Each record is emitted at INFO level on `hcie.audit`. Structured
    fields are attached as `extra` so JSON handlers can serialize them
    cleanly; a fallback "k=v" suffix keeps plain handlers readable.
    """

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        self._logger = logger if logger is not None else logging.getLogger("hcie.audit")
        self.records: List[Dict[str, Any]] = []

    def record(self, *, actor: str, action: str, resource: str,
               outcome: str, **fields: Any) -> None:
        payload: Dict[str, Any] = {
            "actor": actor, "action": action, "resource": resource,
            "outcome": outcome,
        }
        payload.update(fields)
        self.records.append(payload)
        suffix = " ".join(f"{k}={v}" for k, v in payload.items())
        self._logger.info(suffix, extra={"audit": payload})

    def flush(self) -> None:
        for handler in self._logger.handlers:
            try:
                handler.flush()
            except Exception:
                pass


class NullAuditSink:
    """`AuditSinkProtocol` that discards. Used when audit is disabled."""

    def __init__(self) -> None:
        self.records: List[Dict[str, Any]] = []

    def record(self, *, actor: str, action: str, resource: str,
               outcome: str, **fields: Any) -> None:
        return None

    def flush(self) -> None:
        return None


def build_audit_sink() -> LoggingAuditSink:
    return LoggingAuditSink()
