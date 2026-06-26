"""Unit tests for the Phase 8 security ports + adapters.

Verifies that:

1. All three security protocols are `runtime_checkable`.
2. Adapters in `security_factory.py` satisfy the protocols at runtime.
3. `Container.secrets_provider() / .authorizer() / .audit_sink()`
   return memoized singletons.
4. RoleAllowlistAuthorizer matches glob patterns and denies by default.
5. LoggingAuditSink captures records with the required core fields.
"""

from __future__ import annotations

import logging

from finals_loader import from_finals


def test_protocols_are_runtime_checkable() -> None:
    ports = from_finals("01_source/00_core/00_interfaces/11_security_ports.py")
    factory = from_finals("01_source/01_application/07_infrastructure/00_di/security_factory.py")

    secrets = factory.build_secrets_provider()
    authorizer = factory.build_authorizer()
    audit = factory.build_audit_sink()

    assert isinstance(secrets, ports.SecretsProviderProtocol)
    assert isinstance(authorizer, ports.AuthorizationProtocol)
    assert isinstance(audit, ports.AuditSinkProtocol)


def test_in_memory_secrets_provider_returns_default_when_missing() -> None:
    factory = from_finals("01_source/01_application/07_infrastructure/00_di/security_factory.py")
    secrets = factory.InMemorySecretsProvider({"db_password": "s3cret"})

    assert secrets.get_secret("db_password") == "s3cret"
    assert secrets.get_secret("missing") is None
    assert secrets.get_secret("missing", "fallback") == "fallback"
    assert secrets.has_secret("db_password") is True
    assert secrets.has_secret("missing") is False
    assert set(secrets.list_secret_keys()) == {"db_password"}


def test_env_secrets_provider_prefix_isolates_namespace() -> None:
    factory = from_finals("01_source/01_application/07_infrastructure/00_di/security_factory.py")
    env = {
        "HCIE_SECRET_DB_PASSWORD": "p4ss",
        "OTHER_VAR": "ignored",
    }
    secrets = factory.EnvSecretsProvider(prefix="HCIE_SECRET_", environ=env)
    assert secrets.get_secret("DB_PASSWORD") == "p4ss"
    assert secrets.has_secret("DB_PASSWORD") is True
    keys = set(secrets.list_secret_keys())
    assert "HCIE_SECRET_DB_PASSWORD" in keys
    assert "OTHER_VAR" not in keys


def test_role_allowlist_authorizer_denies_by_default() -> None:
    factory = from_finals("01_source/01_application/07_infrastructure/00_di/security_factory.py")
    authz = factory.RoleAllowlistAuthorizer()

    assert authz.is_authorized("role:researcher", "read", "experiment/E-1") is False

    authz.grant("role:researcher", "read", "experiment/*")
    assert authz.is_authorized("role:researcher", "read", "experiment/E-1") is True
    assert authz.is_authorized("role:researcher", "write", "experiment/E-1") is False
    assert authz.is_authorized("role:researcher", "read", "session/abc") is False

    authz.revoke("role:researcher", "read", "experiment/*")
    assert authz.is_authorized("role:researcher", "read", "experiment/E-1") is False


def test_allow_all_authorizer_emits_audit_record() -> None:
    factory = from_finals("01_source/01_application/07_infrastructure/00_di/security_factory.py")
    audit = factory.LoggingAuditSink()
    authz = factory.AllowAllAuthorizer(audit=audit)

    assert authz.is_authorized("user:42", "read", "experiment/E-9") is True
    assert len(audit.records) == 1
    rec = audit.records[0]
    assert rec["actor"] == "user:42"
    assert rec["action"] == "read"
    assert rec["resource"] == "experiment/E-9"
    assert rec["outcome"] == "allow_all"
    assert rec["policy"] == "AllowAllAuthorizer"


def test_logging_audit_sink_captures_required_core_fields() -> None:
    factory = from_finals("01_source/01_application/07_infrastructure/00_di/security_factory.py")

    bag = []

    class _Capture(logging.Handler):
        def emit(self, record):
            bag.append((record.levelno, record.getMessage(),
                        getattr(record, "audit", None)))

    audit_logger = logging.getLogger("hcie.audit.test_phase8")
    handler = _Capture(level=logging.INFO)
    audit_logger.addHandler(handler)
    audit_logger.setLevel(logging.INFO)
    try:
        sink = factory.LoggingAuditSink(logger=audit_logger)
        sink.record(actor="user:x", action="login", resource="session/s1",
                    outcome="allow", trace_id="abc-123")
        sink.flush()
    finally:
        audit_logger.removeHandler(handler)

    assert len(sink.records) == 1
    record_payload = bag[-1][2]
    assert record_payload["actor"] == "user:x"
    assert record_payload["outcome"] == "allow"
    assert record_payload["trace_id"] == "abc-123"


def test_null_audit_sink_is_silent() -> None:
    factory = from_finals("01_source/01_application/07_infrastructure/00_di/security_factory.py")
    sink = factory.NullAuditSink()
    sink.record(actor="user:x", action="read", resource="r", outcome="allow")
    sink.flush()
    assert sink.records == []


def test_container_security_accessors_are_singletons() -> None:
    container_mod = from_finals("01_source/01_application/07_infrastructure/00_di/container.py")
    container = container_mod.Container()

    sec1 = container.secrets_provider()
    sec2 = container.secrets_provider()
    az1 = container.authorizer()
    az2 = container.authorizer()
    au1 = container.audit_sink()
    au2 = container.audit_sink()

    assert sec1 is sec2
    assert az1 is az2
    assert au1 is au2
