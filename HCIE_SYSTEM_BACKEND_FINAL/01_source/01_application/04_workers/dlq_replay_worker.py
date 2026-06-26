"""FINAL-native DLQ replay worker.

This worker is the operational counterpart to the research-grade
``ReplayEngine`` (``01_source/02_infrastructure/02_experiment/replay_engine.py``)
and the ``/v3/experiments/.../replay`` surface that the chapter relies on for
Contribution A (deterministic replay integrity). It handles **two** concerns
on purpose:

1. **Operational replay** — the historical DLQ-replay role from the V2 stack:
   consume failed Kafka events, classify the root cause, apply only safety-
   gated repairs, republish to the canonical input topic with idempotency,
   and emit a replay-audit record. This is what keeps the pipeline alive in
   the face of transient schema drift without inventing pedagogical state.

2. **Research replay coordination** — a thin command channel that lets an
   operator (or an automated audit) ask the worker to drive ``ReplayEngine``
   batch replay for a specific ``experiment_run_id``. The worker does **not**
   reimplement deterministic replay; it just calls the canonical engine and
   emits an audit record with the resulting divergence summary. This keeps
   the chapter's claim — that one and only one component owns deterministic
   replay — provable.

Both paths share the same Redis-backed transactional outbox so we can recover
from a crash mid-replay without double-publishing.
"""

from __future__ import annotations

import json
import logging
import os
import signal
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

import redis
from kafka import KafkaAdminClient, KafkaConsumer, KafkaProducer
from kafka.admin import NewTopic
from prometheus_client import Counter, Gauge, Histogram, start_http_server

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Prometheus instrumentation
# ---------------------------------------------------------------------------

DLQ_PROCESSED = Counter(
    "hcie_dlq_processed_total",
    "DLQ records inspected by the replay worker",
)
DLQ_REPLAYED = Counter(
    "hcie_dlq_replayed_total",
    "DLQ records successfully replayed",
    labelnames=("root_cause", "safety"),
)
DLQ_FAILED = Counter(
    "hcie_dlq_failed_total",
    "DLQ records that could not be replayed",
    labelnames=("root_cause", "stage"),
)
DLQ_SKIPPED = Counter(
    "hcie_dlq_skipped_total",
    "DLQ records skipped (duplicate, locked, or poison)",
    labelnames=("reason",),
)
DLQ_RECOVERED = Counter(
    "hcie_dlq_recovered_total",
    "Intent-store records recovered after a crash",
)
DLQ_BATCH_SIZE = Gauge(
    "hcie_dlq_last_batch_size",
    "Last DLQ batch size processed",
)
DLQ_HANDLE_SECONDS = Histogram(
    "hcie_dlq_handle_seconds",
    "Per-record processing latency",
    labelnames=("outcome",),
)
RESEARCH_REPLAY_REQUESTS = Counter(
    "hcie_research_replay_requests_total",
    "Research replay commands received by the worker",
    labelnames=("status",),
)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DLQConfig:
    bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    dlq_topic: str = os.getenv("DLQ_TOPIC", "hcie-events-dlq")
    main_topic: str = os.getenv("DLQ_MAIN_TOPIC", "user-interactions")
    replay_topic: str = os.getenv("DLQ_REPLAY_TOPIC", "hcie-events-replay")
    command_topic: str = os.getenv("DLQ_COMMAND_TOPIC", "hcie-replay-commands")
    group_id: str = os.getenv("DLQ_GROUP_ID", "hcie-final-dlq-replay-worker")
    command_group_id: str = os.getenv(
        "DLQ_COMMAND_GROUP_ID",
        "hcie-final-dlq-replay-worker-commands",
    )
    redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    metrics_port: int = int(os.getenv("DLQ_METRICS_PORT", "8003"))
    batch_size: int = int(os.getenv("DLQ_BATCH_SIZE", "25"))
    poll_timeout_ms: int = int(os.getenv("DLQ_POLL_TIMEOUT_MS", "5000"))
    idle_sleep_s: float = float(os.getenv("DLQ_IDLE_SLEEP_S", "2.0"))
    poison_after_attempts: int = int(os.getenv("DLQ_POISON_AFTER_ATTEMPTS", "5"))
    intent_ttl_s: int = int(os.getenv("DLQ_INTENT_TTL_S", str(7 * 24 * 3600)))
    done_ttl_s: int = int(os.getenv("DLQ_DONE_TTL_S", str(30 * 24 * 3600)))
    lock_ttl_s: int = int(os.getenv("DLQ_LOCK_TTL_S", "300"))
    enable_research_replay: bool = os.getenv(
        "DLQ_ENABLE_RESEARCH_REPLAY", "true"
    ).lower() in {"1", "true", "yes"}


# ---------------------------------------------------------------------------
# Failure classification + repair strategies
# ---------------------------------------------------------------------------


class SafetyLevel(str, Enum):
    SAFE = "safe"
    RISKY = "risky"
    DANGEROUS = "dangerous"
    MANUAL = "manual"


@dataclass
class FailureAnalysis:
    error_reason: str
    root_cause: str
    safety: SafetyLevel
    confidence: float
    repairs: List[str] = field(default_factory=list)
    remaining_issues: List[str] = field(default_factory=list)
    manual_review_required: bool = False
    decode_error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_reason": self.error_reason,
            "root_cause": self.root_cause,
            "safety": self.safety.value,
            "confidence": round(self.confidence, 3),
            "repairs": list(self.repairs),
            "remaining_issues": list(self.remaining_issues),
            "manual_review_required": self.manual_review_required,
            "decode_error": self.decode_error,
        }


_VALID_EVENT_TYPES = {
    "task_submitted",
    "task_completed",
    "reward_received",
    "interaction",
    "learning_attempt",
    "external_attempt",
}

_EVENT_TYPE_NORMALIZATION = {
    "submit": "task_submitted",
    "complete": "task_completed",
    "master": "concept_mastered",
    "TASK_SUBMITTED": "task_submitted",
    "TaskSubmitted": "task_submitted",
    "TASK_COMPLETED": "task_completed",
    "TaskCompleted": "task_completed",
    "REWARD_RECEIVED": "reward_received",
}


class FailureClassifier:
    """Determine the *true* root cause from the DLQ envelope.

    The V2 worker conflated ``error_reason`` (what the writer printed) with
    ``root_cause`` (what is actually wrong with the payload). We keep that
    distinction here so the safety classifier never auto-applies a fix
    motivated by a misleading error label.
    """

    _MISSING_FIELD_PATTERN = "missing_"

    def classify(self, dlq_envelope: Dict[str, Any], event: Optional[Dict[str, Any]]) -> FailureAnalysis:
        error_reason = str(dlq_envelope.get("error_reason", "unknown"))
        remaining_issues: List[str] = list(dlq_envelope.get("remaining_issues") or [])
        validation_errors: List[str] = [
            str(err) for err in dlq_envelope.get("validation_errors") or []
        ]
        applied_fixes: List[str] = list(dlq_envelope.get("applied_fixes") or [])

        if event is None:
            return FailureAnalysis(
                error_reason=error_reason,
                root_cause="invalid_json_payload",
                safety=SafetyLevel.MANUAL,
                confidence=0.0,
                remaining_issues=remaining_issues,
                manual_review_required=True,
                decode_error=str(dlq_envelope.get("decode_error") or ""),
            )

        if not remaining_issues:
            remaining_issues = self._derive_remaining_issues(event)

        root_cause = self._determine_root_cause(
            error_reason=error_reason,
            event=event,
            remaining_issues=remaining_issues,
            validation_errors=validation_errors,
            applied_fixes=applied_fixes,
        )
        safety, confidence = self._safety_for(root_cause, event)
        return FailureAnalysis(
            error_reason=error_reason,
            root_cause=root_cause,
            safety=safety,
            confidence=confidence,
            remaining_issues=remaining_issues,
        )

    def _derive_remaining_issues(self, event: Dict[str, Any]) -> List[str]:
        issues: List[str] = []
        for field_name in ("event_id", "timestamp", "version", "event_type"):
            if not event.get(field_name) and field_name != "version":
                issues.append(f"missing_{field_name}")
            elif field_name == "version" and "version" not in event:
                issues.append("missing_version")
        if not (event.get("user_id") or event.get("synthetic_user_id")):
            issues.append("missing_user_id")
        if "event_id" in event and not isinstance(event["event_id"], str):
            issues.append("invalid_uuid")
        if event.get("event_type") and event["event_type"] not in (
            _VALID_EVENT_TYPES | set(_EVENT_TYPE_NORMALIZATION.keys())
        ):
            issues.append("invalid_event_type")
        if "reward" in event:
            try:
                value = float(event["reward"])
                if value < -1.0 or value > 100.0:
                    issues.append("invalid_reward")
            except (TypeError, ValueError):
                issues.append("invalid_reward")
        return issues

    def _determine_root_cause(
        self,
        *,
        error_reason: str,
        event: Dict[str, Any],
        remaining_issues: List[str],
        validation_errors: List[str],
        applied_fixes: List[str],
    ) -> str:
        if any(issue == "invalid_uuid" for issue in remaining_issues):
            return "invalid_uuid_format"
        if any(issue == "invalid_reward" for issue in remaining_issues):
            return "invalid_reward_range"
        if any(issue == "invalid_event_type" for issue in remaining_issues):
            return "invalid_event_type"
        cheaply_fixable_missing = {
            "missing_event_id",
            "missing_timestamp",
            "missing_version",
        }
        if any(issue in cheaply_fixable_missing for issue in remaining_issues):
            return "missing_required_fields"
        if any(issue.startswith(self._MISSING_FIELD_PATTERN) for issue in remaining_issues):
            return "missing_business_fields"
        if validation_errors:
            text = " ".join(validation_errors).lower()
            if "event_type" in text:
                return "invalid_event_type"
            if "concept" in text:
                return "invalid_concept_format"
            return "schema_structure_violation"
        if applied_fixes and remaining_issues:
            return "partial_fix_failed"
        if error_reason == "fixable_validation_failed":
            return "missing_required_fields"
        if error_reason == "cross_layer_inconsistency":
            return "cross_layer_constraint_violation"
        if error_reason == "migration_failed":
            return "schema_migration_error"
        return error_reason or "unknown_error"

    @staticmethod
    def _safety_for(root_cause: str, event: Dict[str, Any]) -> Tuple[SafetyLevel, float]:
        if root_cause == "missing_required_fields":
            return SafetyLevel.SAFE, 0.95
        if root_cause == "invalid_event_type":
            return (SafetyLevel.RISKY, 0.80) if event.get("event_type") in _EVENT_TYPE_NORMALIZATION else (SafetyLevel.MANUAL, 0.2)
        if root_cause == "schema_migration_error":
            return SafetyLevel.RISKY, 0.70
        if root_cause == "invalid_uuid_format":
            return SafetyLevel.RISKY, 0.65
        if root_cause == "invalid_reward_range":
            return SafetyLevel.MANUAL, 0.10
        if root_cause == "missing_business_fields":
            return SafetyLevel.MANUAL, 0.20
        if root_cause == "cross_layer_constraint_violation":
            return SafetyLevel.MANUAL, 0.05
        return SafetyLevel.MANUAL, 0.10


RepairStrategy = Callable[[Dict[str, Any], FailureAnalysis], bool]


def _repair_missing_required(event: Dict[str, Any], analysis: FailureAnalysis) -> bool:
    changed = False
    if not event.get("event_id"):
        event["event_id"] = str(uuid.uuid4())
        analysis.repairs.append("generated_event_id")
        changed = True
    if not event.get("timestamp"):
        event["timestamp"] = datetime.now(timezone.utc).isoformat()
        analysis.repairs.append("generated_timestamp")
        changed = True
    if "version" not in event:
        event["version"] = 1
        analysis.repairs.append("defaulted_version")
        changed = True
    return changed


def _repair_event_type(event: Dict[str, Any], analysis: FailureAnalysis) -> bool:
    event_type = event.get("event_type")
    mapped = _EVENT_TYPE_NORMALIZATION.get(event_type or "")
    if mapped:
        event["event_type"] = mapped
        analysis.repairs.append(f"normalized_event_type:{event_type}->{mapped}")
        return True
    return False


def _repair_uuid(event: Dict[str, Any], analysis: FailureAnalysis) -> bool:
    event_id = event.get("event_id")
    if isinstance(event_id, str):
        try:
            uuid.UUID(event_id)
            return False
        except ValueError:
            pass
    event["event_id"] = str(uuid.uuid4())
    analysis.repairs.append("regenerated_event_id")
    return True


def _repair_schema_migration(event: Dict[str, Any], analysis: FailureAnalysis) -> bool:
    if event.get("version", 1) < 2:
        event["version"] = 2
        analysis.repairs.append("upgraded_version_to_2")
        return True
    return False


REPAIR_STRATEGIES: Dict[str, RepairStrategy] = {
    "missing_required_fields": _repair_missing_required,
    "invalid_event_type": _repair_event_type,
    "invalid_uuid_format": _repair_uuid,
    "schema_migration_error": _repair_schema_migration,
}


# ---------------------------------------------------------------------------
# Worker
# ---------------------------------------------------------------------------


class DLQReplayWorker:
    """Operational + research replay worker for the FINAL stack."""

    def __init__(
        self,
        config: Optional[DLQConfig] = None,
        *,
        classifier: Optional[FailureClassifier] = None,
        research_replay: Optional[Callable[[str, int], Dict[str, Any]]] = None,
    ) -> None:
        self.config = config or DLQConfig()
        self.running = True
        self.redis_client = self._connect_redis()
        self.consumer = self._build_consumer(self.config.dlq_topic, self.config.group_id)
        self.command_consumer = (
            self._build_consumer(self.config.command_topic, self.config.command_group_id, latest=True)
            if self.config.enable_research_replay
            else None
        )
        self.main_producer = self._build_producer()
        self.audit_producer = self._build_producer()
        self.classifier = classifier or FailureClassifier()
        self.research_replay = research_replay
        self._ensure_topic(self.config.replay_topic)
        if self.command_consumer is not None:
            self._ensure_topic(self.config.command_topic)

    # ----- wiring -------------------------------------------------------

    def _connect_redis(self) -> Optional[redis.Redis]:
        try:
            client = redis.Redis.from_url(self.config.redis_url, decode_responses=True)
            client.ping()
            logger.info("DLQ idempotency store connected: %s", self.config.redis_url)
            return client
        except Exception as exc:  # noqa: BLE001
            logger.warning("Redis unavailable for DLQ replay idempotency: %r", exc)
            return None

    def _build_consumer(self, topic: str, group_id: str, *, latest: bool = False) -> KafkaConsumer:
        return KafkaConsumer(
            topic,
            bootstrap_servers=self.config.bootstrap_servers,
            auto_offset_reset="latest" if latest else "earliest",
            enable_auto_commit=False,
            group_id=group_id,
            value_deserializer=self._decode_json_bytes,
            key_deserializer=lambda b: b.decode("utf-8") if b else None,
        )

    def _build_producer(self) -> KafkaProducer:
        return KafkaProducer(
            bootstrap_servers=self.config.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v, sort_keys=True, default=str).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
            acks="all",
            retries=5,
        )

    @staticmethod
    def _decode_json_bytes(payload: bytes) -> Dict[str, Any]:
        try:
            return json.loads(payload.decode("utf-8"))
        except Exception as exc:  # noqa: BLE001
            return {
                "error_reason": "invalid_json",
                "raw_bytes": payload.decode("utf-8", errors="replace"),
                "decode_error": repr(exc),
            }

    def _ensure_topic(self, topic: str) -> None:
        try:
            admin = KafkaAdminClient(bootstrap_servers=self.config.bootstrap_servers)
            admin.create_topics(
                [NewTopic(topic, num_partitions=1, replication_factor=1)], validate_only=False
            )
            admin.close()
            logger.info("DLQ topic ensured: %s", topic)
        except Exception as exc:  # noqa: BLE001
            logger.info("Topic %s already exists or could not be created: %r", topic, exc)

    # ----- main loop ----------------------------------------------------

    def stop(self, *_: object) -> None:
        self.running = False

    def run_forever(self) -> None:
        logger.info(
            "Starting FINAL DLQ replay worker: dlq=%s main=%s audit=%s commands=%s",
            self.config.dlq_topic,
            self.config.main_topic,
            self.config.replay_topic,
            self.config.command_topic if self.command_consumer else "(disabled)",
        )
        start_http_server(self.config.metrics_port)
        signal.signal(signal.SIGTERM, self.stop)
        signal.signal(signal.SIGINT, self.stop)
        self._recover_intents()

        while self.running:
            processed = self.process_batch(self.config.batch_size)
            self._drain_command_topic()
            if processed == 0:
                time.sleep(self.config.idle_sleep_s)

        self._close()

    def _close(self) -> None:
        try:
            self.consumer.close()
            if self.command_consumer is not None:
                self.command_consumer.close()
        finally:
            self.main_producer.flush()
            self.main_producer.close()
            self.audit_producer.flush()
            self.audit_producer.close()

    # ----- DLQ batch ----------------------------------------------------

    def process_batch(self, limit: int) -> int:
        records = self.consumer.poll(timeout_ms=self.config.poll_timeout_ms)
        processed = 0
        for _partition, messages in records.items():
            for message in messages:
                if processed >= limit:
                    break
                processed += 1
                DLQ_PROCESSED.inc()
                with DLQ_HANDLE_SECONDS.labels(outcome="any").time():
                    self._handle_record(message.key, message.value, message.offset)
            if processed >= limit:
                break
        if processed:
            self.consumer.commit()
        DLQ_BATCH_SIZE.set(processed)
        return processed

    def _handle_record(self, key: Optional[str], dlq_envelope: Dict[str, Any], offset: int) -> None:
        event, analysis = self._extract_event(dlq_envelope)
        event_id = (event or {}).get("event_id") or f"offset-{offset}"

        if analysis.manual_review_required or event is None:
            DLQ_FAILED.labels(root_cause=analysis.root_cause, stage="decode").inc()
            self._audit(key, str(event_id), False, analysis, offset)
            return

        if self._is_poison(str(event_id)):
            DLQ_SKIPPED.labels(reason="poison").inc()
            self._audit(key, str(event_id), False, analysis, offset, extra={"poison": True})
            return

        repaired = self._apply_repairs(event, analysis)
        if not repaired and analysis.safety == SafetyLevel.MANUAL:
            DLQ_FAILED.labels(root_cause=analysis.root_cause, stage="safety_gate").inc()
            self._audit(key, str(event_id), False, analysis, offset)
            return

        if not self._validate_event(event, analysis):
            DLQ_FAILED.labels(root_cause=analysis.root_cause, stage="validation").inc()
            self._audit(key, str(event_id), False, analysis, offset)
            return

        if self._already_done(str(event_id)):
            DLQ_SKIPPED.labels(reason="already_done").inc()
            return
        if not self._acquire_lock(str(event_id)):
            DLQ_SKIPPED.labels(reason="lock_held").inc()
            return

        self._store_intent(str(event_id), event, analysis, offset)
        try:
            self.main_producer.send(
                self.config.main_topic,
                key=key or event.get("user_id") or event.get("synthetic_user_id"),
                value=event,
            ).get(timeout=15)
            self._mark_done(str(event_id))
            DLQ_REPLAYED.labels(root_cause=analysis.root_cause, safety=analysis.safety.value).inc()
            self._audit(key, str(event_id), True, analysis, offset)
            logger.info("Replayed DLQ event %s (root_cause=%s, repairs=%s)", event_id, analysis.root_cause, analysis.repairs)
        except Exception as exc:  # noqa: BLE001
            self._release_lock(str(event_id))
            self._bump_attempt(str(event_id))
            DLQ_FAILED.labels(root_cause=analysis.root_cause, stage="produce").inc()
            self._audit(key, str(event_id), False, analysis, offset, extra={"replay_error": repr(exc)})
            logger.exception("DLQ replay failed for event %s", event_id)

    def _extract_event(
        self, dlq_envelope: Dict[str, Any]
    ) -> Tuple[Optional[Dict[str, Any]], FailureAnalysis]:
        raw_event = (
            dlq_envelope.get("event")
            or dlq_envelope.get("data")
            or dlq_envelope.get("deserialized_data", {}).get("data")
            or dlq_envelope.get("deserialized_data", {}).get("partial_data")
        )
        if raw_event is None and dlq_envelope.get("raw_bytes"):
            try:
                raw_event = json.loads(dlq_envelope["raw_bytes"])
            except Exception as exc:  # noqa: BLE001
                return None, FailureAnalysis(
                    error_reason=str(dlq_envelope.get("error_reason", "invalid_json")),
                    root_cause="invalid_json_payload",
                    safety=SafetyLevel.MANUAL,
                    confidence=0.0,
                    manual_review_required=True,
                    decode_error=repr(exc),
                )
        if not isinstance(raw_event, dict):
            return None, FailureAnalysis(
                error_reason=str(dlq_envelope.get("error_reason", "non_object_payload")),
                root_cause="non_object_payload",
                safety=SafetyLevel.MANUAL,
                confidence=0.0,
                manual_review_required=True,
            )
        event = dict(raw_event)
        analysis = self.classifier.classify(dlq_envelope, event)
        return event, analysis

    def _apply_repairs(self, event: Dict[str, Any], analysis: FailureAnalysis) -> bool:
        if analysis.safety == SafetyLevel.MANUAL:
            return False
        strategy = REPAIR_STRATEGIES.get(analysis.root_cause)
        if strategy is None:
            return False
        # Safe repairs always apply; risky require confidence > 0.6;
        # dangerous require confidence > 0.9. We do not gate by safety alone
        # because some root causes (e.g. invalid_event_type) are flagged risky
        # only because typo'd input is risky to normalize blindly.
        if analysis.safety == SafetyLevel.SAFE:
            applied = strategy(event, analysis)
        elif analysis.safety == SafetyLevel.RISKY and analysis.confidence > 0.6:
            applied = strategy(event, analysis)
        elif analysis.safety == SafetyLevel.DANGEROUS and analysis.confidence > 0.9:
            applied = strategy(event, analysis)
        else:
            applied = False
        # Always re-run the cheap fillers so a partially-repaired event still
        # gets an event_id / timestamp / version regardless of root cause.
        applied = _repair_missing_required(event, analysis) or applied
        return applied

    # ----- validation ---------------------------------------------------

    def _validate_event(self, event: Dict[str, Any], analysis: FailureAnalysis) -> bool:
        for field_name in ("event_id", "event_type"):
            if not event.get(field_name):
                analysis.remaining_issues.append(f"missing_{field_name}")
                return False
        if not (event.get("user_id") or event.get("synthetic_user_id")):
            analysis.remaining_issues.append("missing_user_id")
            return False
        if event["event_type"] not in _VALID_EVENT_TYPES:
            analysis.remaining_issues.append("invalid_event_type")
            return False
        if "reward" in event:
            try:
                value = float(event["reward"])
            except (TypeError, ValueError):
                analysis.remaining_issues.append("invalid_reward")
                return False
            if value < -1.0 or value > 100.0:
                analysis.remaining_issues.append("invalid_reward")
                return False
        return True

    # ----- idempotency + transactional outbox --------------------------

    def _redis_key(self, scope: str, event_id: str) -> str:
        return f"hcie:dlq:{scope}:{event_id}"

    def _already_done(self, event_id: str) -> bool:
        return bool(self.redis_client and self.redis_client.exists(self._redis_key("done", event_id)))

    def _acquire_lock(self, event_id: str) -> bool:
        if not self.redis_client:
            return True
        return bool(
            self.redis_client.set(
                self._redis_key("processing", event_id),
                str(time.time()),
                nx=True,
                ex=self.config.lock_ttl_s,
            )
        )

    def _release_lock(self, event_id: str) -> None:
        if self.redis_client:
            self.redis_client.delete(self._redis_key("processing", event_id))

    def _store_intent(
        self,
        event_id: str,
        event: Dict[str, Any],
        analysis: FailureAnalysis,
        offset: int,
    ) -> None:
        if not self.redis_client:
            return
        payload = {
            "event": event,
            "analysis": analysis.to_dict(),
            "original_offset": offset,
            "stored_at": datetime.now(timezone.utc).isoformat(),
        }
        self.redis_client.setex(
            self._redis_key("intent", event_id),
            self.config.intent_ttl_s,
            json.dumps(payload, sort_keys=True, default=str),
        )

    def _mark_done(self, event_id: str) -> None:
        if not self.redis_client:
            return
        pipe = self.redis_client.pipeline()
        pipe.setex(self._redis_key("done", event_id), self.config.done_ttl_s, "1")
        pipe.delete(self._redis_key("processing", event_id))
        pipe.delete(self._redis_key("intent", event_id))
        pipe.delete(self._redis_key("attempts", event_id))
        pipe.execute()

    def _bump_attempt(self, event_id: str) -> None:
        if not self.redis_client:
            return
        attempts = self.redis_client.incr(self._redis_key("attempts", event_id))
        self.redis_client.expire(self._redis_key("attempts", event_id), self.config.intent_ttl_s)
        if attempts >= self.config.poison_after_attempts:
            self.redis_client.setex(self._redis_key("poison", event_id), self.config.done_ttl_s, "1")

    def _is_poison(self, event_id: str) -> bool:
        return bool(self.redis_client and self.redis_client.exists(self._redis_key("poison", event_id)))

    def _recover_intents(self) -> None:
        if not self.redis_client:
            return
        pattern = self._redis_key("intent", "*")
        recovered = 0
        for key in self.redis_client.scan_iter(match=pattern):
            try:
                raw = self.redis_client.get(key)
                if not raw:
                    continue
                payload = json.loads(raw)
                event = payload.get("event") or {}
                event_id = event.get("event_id") or key.rsplit(":", 1)[-1]
                if self._already_done(event_id) or self._is_poison(event_id):
                    self.redis_client.delete(key)
                    continue
                self.main_producer.send(
                    self.config.main_topic,
                    key=event.get("user_id") or event.get("synthetic_user_id"),
                    value=event,
                ).get(timeout=15)
                self._mark_done(event_id)
                DLQ_RECOVERED.inc()
                recovered += 1
                self._audit(
                    key=None,
                    event_id=event_id,
                    success=True,
                    analysis=FailureAnalysis(
                        error_reason="intent_recovered",
                        root_cause="crash_recovery",
                        safety=SafetyLevel.SAFE,
                        confidence=1.0,
                        repairs=["replayed_from_intent_store"],
                    ),
                    offset=int(payload.get("original_offset", -1)),
                )
            except Exception as exc:  # noqa: BLE001
                logger.exception("Failed to recover intent %s: %r", key, exc)
        if recovered:
            logger.info("Recovered %s pending intents from Redis", recovered)

    # ----- research replay coordination --------------------------------

    def _drain_command_topic(self) -> None:
        if self.command_consumer is None:
            return
        records = self.command_consumer.poll(timeout_ms=200)
        for _partition, messages in records.items():
            for message in messages:
                self._handle_command(message.value)
        if records:
            self.command_consumer.commit()

    def _handle_command(self, command: Dict[str, Any]) -> None:
        action = str(command.get("action") or "").lower()
        if action != "replay_experiment_run":
            RESEARCH_REPLAY_REQUESTS.labels(status="unsupported").inc()
            logger.warning("Unsupported replay command action=%s", action)
            return
        experiment_run_id = str(command.get("experiment_run_id") or "")
        num_users = int(command.get("num_users") or 100)
        if not experiment_run_id:
            RESEARCH_REPLAY_REQUESTS.labels(status="malformed").inc()
            logger.warning("replay_experiment_run command missing experiment_run_id")
            return
        if self.research_replay is None:
            RESEARCH_REPLAY_REQUESTS.labels(status="disabled").inc()
            logger.warning(
                "Received replay_experiment_run but research_replay hook not configured; "
                "use the /v3/experiments endpoint instead."
            )
            return
        try:
            summary = self.research_replay(experiment_run_id, num_users)
            RESEARCH_REPLAY_REQUESTS.labels(status="ok").inc()
            self.audit_producer.send(
                self.config.replay_topic,
                key=experiment_run_id,
                value={
                    "kind": "research_replay_summary",
                    "experiment_run_id": experiment_run_id,
                    "num_users": num_users,
                    "summary": summary,
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                },
            )
            self.audit_producer.flush(timeout=5)
            logger.info(
                "Research replay completed for run=%s users=%s summary=%s",
                experiment_run_id,
                num_users,
                {k: summary.get(k) for k in ("mean_divergence", "stochasticity_bounded")},
            )
        except Exception as exc:  # noqa: BLE001
            RESEARCH_REPLAY_REQUESTS.labels(status="error").inc()
            logger.exception("Research replay failed for %s: %r", experiment_run_id, exc)

    # ----- audit emit ---------------------------------------------------

    def _audit(
        self,
        key: Optional[str],
        event_id: str,
        success: bool,
        analysis: FailureAnalysis,
        offset: int,
        *,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        payload: Dict[str, Any] = {
            "kind": "dlq_replay_attempt",
            "event_id": event_id,
            "success": success,
            "analysis": analysis.to_dict(),
            "original_offset": offset,
            "attempted_at": datetime.now(timezone.utc).isoformat(),
        }
        if extra:
            payload.update(extra)
        try:
            self.audit_producer.send(self.config.replay_topic, key=key or event_id, value=payload)
            self.audit_producer.flush(timeout=5)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to emit DLQ replay audit event: %r", exc)


# ---------------------------------------------------------------------------
# Research replay hook
# ---------------------------------------------------------------------------


def _default_research_replay_hook() -> Optional[Callable[[str, int], Dict[str, Any]]]:
    """Return a callable bound to the canonical ``ReplayEngine``.

    Imports are lazy because the worker container only needs them when the
    research replay command channel is enabled.
    """
    try:
        from app.api.v3.service.router import _batch_replay  # type: ignore  # noqa: WPS433
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Research replay hook unavailable, command channel will reject "
            "replay_experiment_run requests: %r",
            exc,
        )
        return None

    def _hook(experiment_run_id: str, num_users: int) -> Dict[str, Any]:
        return _batch_replay(experiment_run_id, num_users=num_users)

    return _hook


def main() -> int:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    config = DLQConfig()
    hook = _default_research_replay_hook() if config.enable_research_replay else None
    DLQReplayWorker(config=config, research_replay=hook).run_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
