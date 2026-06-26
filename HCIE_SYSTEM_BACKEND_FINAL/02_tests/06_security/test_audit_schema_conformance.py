"""Conformance test: the live audit sink's payload must match 08_security/00_audit/audit_schema.json.

This makes the committed schema LOAD-BEARING — if `LoggingAuditSink.record()` ever drifts from the
documented contract (drops a required field, changes the outcome enum), this test fails. Validation is
dependency-free (manual checks derived from the schema file); a full draft-07 jsonschema validation runs
additionally when `jsonschema` is installed.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.infrastructure.di.security_factory import LoggingAuditSink

# 06_security -> 02_tests -> <backend root>
BACKEND_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = BACKEND_ROOT / "08_security" / "00_audit" / "audit_schema.json"


@pytest.fixture(scope="module")
def schema() -> dict:
    assert SCHEMA_PATH.exists(), f"audit schema missing at {SCHEMA_PATH}"
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _emit(**kw) -> dict:
    sink = LoggingAuditSink()
    sink.record(**kw)
    assert len(sink.records) == 1
    return sink.records[0]


def test_recorded_payload_satisfies_required_and_enum(schema):
    payload = _emit(
        actor="user:42", action="read", resource="experiment/E-1234",
        outcome="allow", policy="RbacAuthorizer", trace_id="trace-abc",
    )
    # required fields present
    for field in schema["required"]:
        assert field in payload, f"record() omitted required audit field {field!r}"
    # outcome respects the schema enum
    enum = schema["properties"]["outcome"]["enum"]
    assert payload["outcome"] in enum
    # optional structured fields pass through (schema allows additionalProperties)
    assert payload["policy"] == "RbacAuthorizer"
    assert payload["trace_id"] == "trace-abc"


def test_every_outcome_enum_value_is_accepted(schema):
    for outcome in schema["properties"]["outcome"]["enum"]:
        payload = _emit(actor="svc:x", action="check", resource="r", outcome=outcome)
        assert payload["outcome"] == outcome


def test_full_jsonschema_validation_when_available(schema):
    jsonschema = pytest.importorskip("jsonschema")
    payload = _emit(actor="user:1", action="write", resource="session/s/runtime", outcome="deny")
    jsonschema.validate(instance=payload, schema=schema)  # raises on drift


def test_schema_documents_the_actual_signature(schema):
    # Guard against the schema and the sink silently diverging on the required set.
    assert set(schema["required"]) == {"actor", "action", "resource", "outcome"}
