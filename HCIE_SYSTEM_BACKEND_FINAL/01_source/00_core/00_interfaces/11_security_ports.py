"""Security ports for Phase 8 -- the last cross-cutting concerns.

Three runtime-checkable protocols give core code a typed contract for
the security surface without coupling to any concrete backend (env vars,
Vault, AWS Secrets Manager, a roles database, an audit log sink, ...).

- `SecretsProviderProtocol`   : read-only key/value access to secrets.
- `AuthorizationProtocol`     : subject/action/resource ACL surface.
- `AuditSinkProtocol`         : append-only audit event writer.

These mirror the Phase 5/6 pattern (`ConfigProviderProtocol`,
`LoggerProtocol`, `MetricsRecorderProtocol`): minimal, structurally
verifiable, and composable in the application layer.
"""

from __future__ import annotations

from typing import Any, Optional, Protocol, Sequence, runtime_checkable


@runtime_checkable
class SecretsProviderProtocol(Protocol):
    """Read-only secrets access.

    Production adapters typically wrap Vault, AWS Secrets Manager, or
    Kubernetes Secret mounts. Dev/test code uses in-memory or env-only
    adapters. Listing keys is optional but useful for diagnostics --
    adapters may return an empty sequence if their backend does not
    enumerate.
    """

    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]: ...
    def has_secret(self, key: str) -> bool: ...
    def list_secret_keys(self) -> Sequence[str]: ...


@runtime_checkable
class AuthorizationProtocol(Protocol):
    """Subject / action / resource authorization surface.

    The shape is deliberately simple: the caller asks "is this subject
    allowed to perform `action` against `resource`?". Adapters decide
    how to interpret subjects (user id, role, service account) and
    resource strings (path, URN, glob).
    """

    def is_authorized(self, subject: str, action: str, resource: str) -> bool: ...
    def grant(self, subject: str, action: str, resource: str) -> None: ...
    def revoke(self, subject: str, action: str, resource: str) -> None: ...


@runtime_checkable
class AuditSinkProtocol(Protocol):
    """Append-only audit event writer.

    `record()` accepts a fixed core shape (actor / action / resource /
    outcome) plus arbitrary structured fields. `flush()` is a no-op for
    in-process adapters and a real flush for buffered remote sinks.
    """

    def record(self, *, actor: str, action: str, resource: str,
               outcome: str, **fields: Any) -> None: ...
    def flush(self) -> None: ...
