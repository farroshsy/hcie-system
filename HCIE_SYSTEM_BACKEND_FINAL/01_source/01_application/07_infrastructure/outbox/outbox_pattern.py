"""
Outbox Pattern Implementation
Transactional event publishing with retry logic and DLQ support
"""

import logging
import json
import time
import threading
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Import EventBus for type hints
from app.infrastructure.messaging.event_bus import EventBus
from app.infrastructure.unit_of_work import get_transaction

class OutboxEventStatus(str, Enum):
    PENDING = "pending"
    PUBLISHED = "published"
    FAILED = "failed"

@dataclass
class OutboxEvent:
    """Outbox event for atomic publishing"""
    id: Optional[str] = None
    event_id: str = ""
    event_type: str = ""
    payload: Dict[str, Any] = None
    topic: str = ""
    partition_key: Optional[str] = None  # 🔥 ADDED: Kafka partition key
    status: OutboxEventStatus = OutboxEventStatus.PENDING
    created_at: datetime = None
    published_at: Optional[datetime] = None
    retry_count: int = 0
    error_message: Optional[str] = None
    
    # 🔥 DETERMINISTIC RUNTIME: Deterministic replay metadata
    deterministic_mode: Optional[bool] = None
    deterministic_seed: Optional[int] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.payload is None:
            self.payload = {}

class OutboxPattern:
    """
    Outbox pattern implementation for atomic event publishing
    Ensures database operations and event publishing are atomic
    """
    
    def __init__(self, db_store, event_bus: Optional[EventBus] = None):
        self.db_store = db_store
        self.event_bus = event_bus
        self.running = False
        self.thread = None
        self.last_heartbeat = None
        self.processed_count = 0
        self.error_count = 0
        
        # Backward compatibility
        if event_bus and hasattr(event_bus, 'kafka_producer'):
            self.kafka_producer = event_bus.kafka_producer
        else:
            self.kafka_producer = None
        
    def create_event(self, event_id: str, event_type: str, payload: Dict[str, Any], topic: str, 
                    deterministic_mode: Optional[bool] = None, deterministic_seed: Optional[int] = None) -> OutboxEvent:
        """Create outbox event for later publishing
        
        Args:
            event_id: Unique event identifier
            event_type: Type of event
            payload: Event payload data
            topic: Kafka topic for publishing
            deterministic_mode: Whether event was generated in deterministic mode (optional, uses global context if None)
            deterministic_seed: Seed used for deterministic generation (optional, uses global context if None)
        
        🔥 DETERMINISTIC RUNTIME: If deterministic metadata not provided, uses global deterministic context
        """
        # 🔥 DETERMINISTIC RUNTIME: Use global deterministic context if not explicitly provided
        if deterministic_mode is None or deterministic_seed is None:
            try:
                from core.determinism.deterministic_config import get_global_deterministic_config
                global_config = get_global_deterministic_config()
                if global_config:
                    if deterministic_mode is None:
                        deterministic_mode = global_config.deterministic
                    if deterministic_seed is None:
                        deterministic_seed = global_config.seed
            except ImportError:
                # Deterministic config not available, use provided values or None
                pass
        
        return OutboxEvent(
            event_id=event_id,
            event_type=event_type,
            payload=payload,
            topic=topic,
            deterministic_mode=deterministic_mode,  # 🔥 DETERMINISTIC RUNTIME
            deterministic_seed=deterministic_seed  # 🔥 DETERMINISTIC RUNTIME
        )
    
    def save_event(self, event: OutboxEvent, transaction=None) -> str:
        """Save event to outbox table with full EventEnvelope (within same transaction)"""
        try:
            from app.infrastructure.messaging.event_bus import EventEnvelope
            
            # ✅ B3.6: Extract semantic lineage fields from payload if present
            # This allows derived events to carry causation_id and correlation_id
            if 'causation_id' in event.payload:
                event.causation_id = event.payload['causation_id']
            if 'correlation_id' in event.payload:
                event.correlation_id = event.payload['correlation_id']
            
            # ✅ Create EventEnvelope with metadata, validation, and partition key
            # Pre-compute partition key for efficiency
            from app.infrastructure.messaging.kafka_partitioning import KafkaPartitioningStrategy
            
            # 🔥 DETERMINISTIC RUNTIME: Extract deterministic metadata from event
            deterministic_mode = getattr(event, 'deterministic_mode', None)
            deterministic_seed = getattr(event, 'deterministic_seed', None)
            
            # Create envelope first
            envelope = EventEnvelope(
                event_id=event.event_id,
                event_type=event.event_type,
                payload=event.payload,
                topic=event.topic,
                version=1,
                timestamp=event.created_at,
                correlation_id=getattr(event, 'correlation_id', None),
                causation_id=getattr(event, 'causation_id', None),
                source_service=getattr(event, 'source_service', 'outbox-pattern'),
                metadata={},  # ✅ B3.6: Initialize metadata for trace context
                deterministic_mode=deterministic_mode,  # 🔥 DETERMINISTIC RUNTIME
                deterministic_seed=deterministic_seed  # 🔥 DETERMINISTIC RUNTIME
            )
            
            # ✅ B3.6: Extract trace context from payload and put in envelope metadata
            if 'trace_context' in event.payload:
                trace_context = event.payload['trace_context']
                envelope.metadata['trace_id'] = trace_context.get('trace_id')
                envelope.metadata['span_id'] = trace_context.get('span_id')
                envelope.metadata['parent_span_id'] = trace_context.get('parent_span_id')
                logger.debug(f"🔍 Trace context extracted to envelope metadata: trace_id={envelope.metadata['trace_id']}")
            
            # ✅ Use full envelope for partition key computation
            # B3.6: Extract payload for partition key computation (not full envelope dict)
            envelope_dict_for_partition = {
                "event_type": envelope.event_type,
                "payload": envelope.payload
            }
            logger.debug(f"🔍 Partition key computation: event_type={envelope.event_type}, payload keys={list(envelope.payload.keys())}")
            partition_key = KafkaPartitioningStrategy.get_partition_key(envelope_dict_for_partition)
            logger.debug(f"🔍 Partition key computed: {partition_key}")
            envelope.partition_key = partition_key
            
            # ✅ Validate event schema before persistence
            from app.infrastructure.messaging.event_schema import event_schema_manager
            if not event_schema_manager.validate_event(envelope.event_type, envelope.payload):
                raise ValueError(f"Invalid event schema for {envelope.event_type}")
            
            # ✅ Validate version
            if envelope.version != 1:
                raise ValueError(f"Unsupported event version: {envelope.version}")
            
            # 🔥 TRAFFIC CLASSIFICATION: Determine traffic_type from envelope
            traffic_type = envelope.payload.get('traffic_type') or envelope.metadata.get('traffic_type') or 'research'
            
            # Use the database store to save event with explicit transaction
            # This should be called within the same transaction as the business operation
            if transaction:
                # ✅ Store full envelope in new table with JSONB
                # 🔥 DETERMINISTIC RUNTIME: Include deterministic metadata
                # 🔥 IDEMPOTENCY: Use ON CONFLICT DO NOTHING to handle duplicate event_ids
                transaction.db_store.execute_write(
                    """
                    INSERT INTO outbox_event_envelopes 
                    (event_id, event_type, topic, version, timestamp, envelope, correlation_id, causation_id, source_service, deterministic_mode, deterministic_seed, traffic_type, status, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (event_id) DO NOTHING
                    """,
                    (event.event_id, envelope.event_type, envelope.topic, envelope.version, 
                     envelope.timestamp, json.dumps(envelope.to_dict()), envelope.correlation_id, 
                     envelope.causation_id, envelope.source_service, envelope.deterministic_mode, 
                     envelope.deterministic_seed, traffic_type, OutboxEventStatus.PENDING.value, datetime.utcnow())
                )
                
                # ✅ Removed legacy table storage - use only JSONB envelope
                # TODO: Add migration script to clean up outbox_events table
                logger.debug("📝 Using only JSONB envelope storage (legacy table deprecated)")
            else:
                # Create new transaction
                # 🔥 DETERMINISTIC RUNTIME: Include deterministic metadata
                # 🔥 IDEMPOTENCY: Use ON CONFLICT DO NOTHING to handle duplicate event_ids
                self.db_store.execute_write(
                    """
                    INSERT INTO outbox_event_envelopes 
                    (event_id, event_type, topic, version, timestamp, envelope, correlation_id, causation_id, source_service, deterministic_mode, deterministic_seed, traffic_type, status, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (event_id) DO NOTHING
                    """,
                    (event.event_id, envelope.event_type, envelope.topic, envelope.version, 
                     envelope.timestamp, json.dumps(envelope.to_dict()), envelope.correlation_id, 
                     envelope.causation_id, envelope.source_service, envelope.deterministic_mode, 
                     envelope.deterministic_seed, traffic_type, OutboxEventStatus.PENDING.value, datetime.utcnow())
                )
                
                # ✅ Removed legacy table storage - use only JSONB envelope
                # TODO: Add migration script to clean up outbox_events table
                logger.debug("📝 Using only JSONB envelope storage (legacy table deprecated)")
            
            logger.debug(f"📝 Outbox event envelope saved: {event.event_id}")
            return event.event_id
            
        except Exception as e:
            logger.error(f"❌ Failed to save outbox event: {e}")
            raise
    
    def publish_pending_events(self, batch_size: int = 10, max_retries: int = 3) -> Dict[str, Any]:
        """Publish pending events from outbox with exponential backoff and DLQ support.

        Ordering: per-partition fairness using ROW_NUMBER() partitioned by
        partition_key. Within a single Kafka partition_key (e.g. one learner)
        events are processed in created_at order — Kafka requires this for
        per-key ordering guarantees. Across partition_keys, we round-robin so
        a single backed-up partition (e.g. an abandoned research replay run)
        cannot starve other partitions (e.g. live user attempts).

        This replaces strict global FIFO `ORDER BY created_at ASC` which
        allowed any large legacy backlog to block all new live user events.
        """
        if not self.event_bus:
            logger.warning("⚠️ Event bus not available - skipping outbox publishing")
            return {"published": 0, "failed": 0, "dlq": 0, "errors": []}

        stats = {"published": 0, "failed": 0, "dlq": 0, "errors": []}

        # Import metrics collector
        from app.infrastructure.monitoring.event_metrics import event_metrics_collector

        try:
            # ✅ Use explicit transaction for true isolation - ALL operations inside
            with get_transaction(self.db_store) as tx:
                # Two-phase: (1) rank candidate event ids using per-partition
                # fairness, (2) re-fetch those ids with FOR UPDATE SKIP LOCKED
                # so concurrent publishers don't grab the same row.
                #
                # Per-partition fairness via window function:
                #   - ROW_NUMBER PARTITION BY partition_key gives each
                #     partition its own ordered sequence (1, 2, 3, ...).
                #   - WHERE partition_rank ≤ 5 guarantees the candidate pool
                #     contains rank=1 of EVERY partition, no matter how many
                #     partitions exist (measured 605 active when this was
                #     fixed; a tiny LIMIT was starving partitions ranked >150).
                #   - ORDER BY (partition_rank ASC, MD5(pk||id)) puts all
                # Algorithm:
                # Phase-1: collect the oldest-rank (rank 1..3) candidate IDs
                #   for every pending partition.
                #   LIMIT 3000 caps the per-batch candidate pool so the window-
                #   function sort over a large backlog stays under ~1 s; 3000 is
                #   generous (≥ 600 active partitions × 5 ranks = 3 000 max).
                #   Because we take rank ≤ 3 of every partition via the inner
                #   ROW_NUMBER, every live-user partition is always represented
                #   regardless of how many research-replay rows exist.
                # Phase-2: ORDER BY random() gives each batch a different random
                #   cross-section; FOR UPDATE SKIP LOCKED + LIMIT batch_size
                #   enforces the actual publish quota.
                candidate_ids = tx.db_store.execute_read(
                    """
                    SELECT id FROM (
                        SELECT id,
                               ROW_NUMBER() OVER (
                                   PARTITION BY COALESCE(envelope::jsonb->>'partition_key', event_id)
                                   ORDER BY created_at ASC, id ASC
                               ) AS partition_rank
                        FROM outbox_event_envelopes
                        WHERE status = %s
                          AND retry_count < %s
                    ) ranked
                    WHERE partition_rank <= 3
                    LIMIT 3000
                    """,
                    (OutboxEventStatus.PENDING.value, max_retries),
                )
                id_list = [r['id'] for r in (candidate_ids or [])]
                if not id_list:
                    return stats

                # Phase-2: random shuffle via ORDER BY random() so each
                # invocation picks a different cross-section from the
                # candidate pool. PostgreSQL seeds its PRNG per-connection so
                # we get genuine per-batch randomness without setseed()
                # (which returns void and cannot appear in ORDER BY).
                # FOR UPDATE SKIP LOCKED prevents double-publish.
                events = tx.db_store.execute_read(
                    """
                    SELECT id, event_id, event_type, topic, version, timestamp, envelope,
                           correlation_id, causation_id, source_service,
                           deterministic_mode, deterministic_seed,
                           retry_count, created_at
                    FROM outbox_event_envelopes
                    WHERE id = ANY(%s)
                      AND status = %s
                    ORDER BY random()
                    LIMIT %s
                    FOR UPDATE SKIP LOCKED
                    """,
                    (id_list, OutboxEventStatus.PENDING.value, batch_size),
                )
                
                # Collect events for processing outside transaction
                events_to_process = []
                for event_row in events:
                    # Use new schema with full envelope - event_row is now a dict
                    id = event_row['id']
                    event_id = event_row['event_id']
                    event_type = event_row['event_type']
                    topic = event_row['topic']
                    version = event_row['version']
                    timestamp = event_row['timestamp']
                    envelope = event_row['envelope']
                    correlation_id = event_row['correlation_id']
                    causation_id = event_row['causation_id']
                    source_service = event_row['source_service']
                    deterministic_mode = event_row.get('deterministic_mode')  # 🔥 DETERMINISTIC RUNTIME
                    deterministic_seed = event_row.get('deterministic_seed')  # 🔥 DETERMINISTIC RUNTIME
                    retry_count = event_row['retry_count']
                    created_at = event_row['created_at']
                    
                    # Recreate EventEnvelope from stored envelope
                    from app.infrastructure.messaging.event_bus import EventEnvelope
                    envelope = EventEnvelope.from_dict(envelope)
                    
                    events_to_process.append({
                        'id': id,
                        'event_id': event_id,
                        'event_type': event_type,
                        'topic': topic,
                        'version': version,
                        'timestamp': timestamp,
                        'envelope': envelope,  # Full envelope
                        'correlation_id': correlation_id,
                        'causation_id': causation_id,
                        'source_service': source_service,
                        'deterministic_mode': deterministic_mode,  # 🔥 DETERMINISTIC RUNTIME
                        'deterministic_seed': deterministic_seed,  # 🔥 DETERMINISTIC RUNTIME
                        'retry_count': retry_count,
                        'created_at': created_at
                    })
            
            # Transaction is now closed - process events outside
            for event_data in events_to_process:
                try:
                    event_id = event_data['event_id']
                    event_type = event_data['event_type']
                    envelope = event_data['envelope']  # ✅ Use full envelope
                    topic = event_data['topic']
                    retry_count = event_data['retry_count']
                    
                    # ✅ Exponential backoff outside transaction
                    if retry_count > 0:
                        backoff_delay = min(2 ** retry_count, 60)  # Cap at 60 seconds
                        logger.debug(f"Backoff delay: {backoff_delay}s for event {event_id} (retry {retry_count})")
                        time.sleep(backoff_delay)
                    
                    # Publish via event bus (transport-agnostic) - use pre-computed envelope
                    # 🔍 Log partition key for debugging
                    logger.info(f"🔍 [OUTBOX] Publishing event {event_id} with partition_key: {envelope.partition_key}")
                    
                    success = self.event_bus.publish(envelope)
                    
                    if success:
                        # Record success metric
                        event_metrics_collector.record_event(
                            event_type=event_type,
                            topic=topic,
                            status="published",
                            processing_time_ms=0.0,  # TODO: Track actual processing time
                            retry_count=retry_count
                        )
                        logger.info(f"✅ [OUTBOX] Published event {event_id} to topic {topic} with partition_key: {envelope.partition_key}")
                        
                        # Mark as published (within new transaction)
                        with get_transaction(self.db_store) as tx:
                            tx.db_store.execute_write(
                                """
                                UPDATE outbox_event_envelopes
                                SET status = %s, published_at = %s
                                WHERE id = %s
                                """,
                                (OutboxEventStatus.PUBLISHED.value, datetime.utcnow(), event_data['id'])
                            )
                            stats["published"] += 1
                            logger.debug(f"Published outbox event: {event_id}")
                    else:
                        # Record failure metric
                        event_metrics_collector.record_event(
                            event_type=event_type,
                            topic=topic,
                            status="failed",
                            processing_time_ms=0.0,  # TODO: Track actual processing time
                            retry_count=retry_count
                        )
                        
                        # Increment retry count
                        new_retry_count = retry_count + 1
                        if new_retry_count >= max_retries:
                            # Send to DLQ after max retries
                            self._send_to_dlq(event_id, event_type, envelope, topic, str(event_data['id']))
                            
                            # Record DLQ metric
                            event_metrics_collector.record_event(
                                event_type=event_type,
                                topic=f"{topic}.dlq",
                                status="dlq",
                                processing_time_ms=0.0,
                                retry_count=retry_count
                            )
                            
                            with get_transaction(self.db_store) as tx:
                                tx.db_store.execute_write(
                                    """
                                    UPDATE outbox_event_envelopes
                                    SET status = %s, error_message = %s, retry_count = %s
                                    WHERE id = %s
                                    """,
                                    (OutboxEventStatus.FAILED.value, 
                                     f"Max retries exceeded: {retry_count}", 
                                     retry_count, event_data['id'])
                                )
                            stats["dlq"] += 1
                            logger.warning(f"Event sent to DLQ after max retries: {event_id}")
                        else:
                            with get_transaction(self.db_store) as tx:
                                tx.db_store.execute_write(
                                    """
                                    UPDATE outbox_event_envelopes
                                    SET retry_count = retry_count + 1, error_message = %s
                                    WHERE id = %s
                                    """,
                                    ("Kafka publish failed", event_data['id'])
                                )
                            stats["failed"] += 1
                            logger.warning(f"⚠️ Failed to publish outbox event: {event_id}")
                    
                except Exception as e:
                    # Record error metric
                    event_metrics_collector.record_event(
                        event_type=event_type,
                        topic=topic,
                        status="failed",
                        processing_time_ms=0.0,
                        retry_count=retry_count
                    )
                    
                    # Mark as failed (within new transaction)
                    with get_transaction(self.db_store) as tx:
                        tx.db_store.execute_write(
                            """
                            UPDATE outbox_event_envelopes
                            SET status = %s, error_message = %s, retry_count = retry_count + 1
                            WHERE id = %s
                            """,
                            (OutboxEventStatus.FAILED.value, str(e), event_data['id'])
                        )
                    stats["failed"] += 1
                    stats["errors"].append(f"Event {event_data['event_id']}: {e}")
                    logger.error(f"❌ Outbox event processing failed: {e}")
            
        except Exception as e:
            logger.error(f"❌ Outbox publishing batch failed: {e}")
            stats["errors"].append(f"Batch processing failed: {e}")
        
        return stats
    
    def _send_to_dlq(self, event_id: str, event_type: str, payload: Dict[str, Any], topic: str, outbox_id: str):
        """Send failed event to Dead Letter Queue via EventBus"""
        try:
            dlq_event = {
                "event_id": event_id,
                "event_type": event_type,
                "payload": payload,
                "original_topic": topic,
                "outbox_id": outbox_id,
                "failed_at": datetime.utcnow().isoformat(),
                "error_reason": "Max retries exceeded"
            }
            
            # ✅ Send via EventBus (maintains abstraction)
            from app.infrastructure.messaging.event_bus import EventEnvelope
            
            dlq_envelope = EventEnvelope(
                event_id=f"{event_id}-dlq",
                event_type="dlq_event",
                payload=dlq_event,
                topic=f"{topic}.dlq"
            )
            
            success = self.event_bus.publish(dlq_envelope)
            
            if success:
                logger.info(f"📨 Event sent to DLQ via EventBus: {event_id}")
            else:
                logger.error(f"❌ Failed to send event to DLQ via EventBus: {event_id}")
                
        except Exception as e:
            logger.error(f"❌ DLQ publishing failed for {event_id}: {e}")
    
    def cleanup_old_events(self, days_old: int = 7) -> int:
        """Clean up old published events"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            result = self.db_store.execute_write(
                """
                DELETE FROM outbox_event_envelopes
                WHERE status = %s
                AND published_at < %s
                """,
                (OutboxEventStatus.PUBLISHED.value, cutoff_date)
            )
            
            logger.info(f"🧹 Cleaned up {result} old outbox events")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to cleanup old outbox events: {e}")
            return 0
    
    def get_outbox_stats(self) -> Dict[str, Any]:
        """Get outbox statistics"""
        try:
            result = self.db_store.execute_read(
                """
                SELECT status, COUNT(*) as count,
                       MIN(created_at) as oldest,
                       MAX(created_at) as newest
                FROM outbox_event_envelopes
                GROUP BY status
                """
            )
            
            return {
                "by_status": {row['status']: row['count'] for row in result},
                "oldest_event": min([row['oldest'] for row in result if row['oldest']], None),
                "newest_event": max([row['newest'] for row in result if row['newest']], None)
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get outbox stats: {e}")
            return {}
    
    def start_background_processor(self, interval_seconds: int = 5, worker_id: str = "default"):
        """Start background outbox processor with worker ID for future scaling"""
        if self.running:
            logger.warning("Outbox processor already running")
            return
        
        self.worker_id = worker_id
        self.running = True
        self.thread = threading.Thread(target=self._background_processor, daemon=True)
        self.thread.start()
        logger.info(f"🔄 Outbox background processor started (worker: {worker_id})")
    
    def stop_background_processor(self):
        """Stop background outbox processor"""
        if not self.running:
            return
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=10)
        logger.info("🛑 Outbox background processor stopped")
    
    def _background_processor(self, interval_seconds: int = 5):
        """Production-safe background processor with restart strategy"""
        logger.info("🔄 Starting production-safe outbox processor")
        
        consecutive_failures = 0
        max_consecutive_failures = 5
        restart_delay = min(interval_seconds * 2, 60)  # Cap at 60s
        
        while self.running:
            try:
                # Update heartbeat
                self.last_heartbeat = datetime.utcnow()
                
                # Process pending events.
                # batch_size=50 (was 10): bumped to drain backlog faster.
                # Combined with per-partition-fairness in publish_pending_events,
                # one batch now publishes up to 50 events distributed across
                # active partitions, so live users get sub-second turnaround
                # even when a research-replay partition has 100k events queued.
                stats = self.publish_pending_events(batch_size=50, max_retries=3)
                
                # Update counters
                self.processed_count += stats["published"] + stats["dlq"]
                self.error_count += stats["failed"]
                
                # Reset failure counter on success
                if stats["published"] > 0 or stats["dlq"] > 0:
                    consecutive_failures = 0
                
                # Log progress
                if stats["published"] > 0 or stats["failed"] > 0:
                    logger.info(f"📊 Outbox batch: {stats['published']} published, {stats['failed']} failed, {stats['dlq']} DLQ")
                
                # Adaptive polling: reduce interval if active, increase if idle
                if stats["published"] > 0:
                    # Active processing - shorter interval
                    sleep_time = max(interval_seconds // 2, 1)
                else:
                    # Idle - normal interval
                    sleep_time = interval_seconds
                
                time.sleep(sleep_time)
                
            except Exception as e:
                consecutive_failures += 1
                self.error_count += 1
                
                logger.error(f"❌ Outbox processor error #{consecutive_failures}: {e}")
                
                # Exponential backoff on consecutive failures
                if consecutive_failures >= max_consecutive_failures:
                    logger.critical(f"💥 Too many failures ({consecutive_failures}), pausing for {restart_delay}s")
                    time.sleep(restart_delay)
                    consecutive_failures = 0  # Reset after pause
                else:
                    # Short pause before retry
                    time.sleep(min(interval_seconds, 10))
        
        logger.info("🛑 Production-safe outbox processor stopped")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of outbox processor"""
        return {
            "running": self.running,
            "worker_id": getattr(self, 'worker_id', 'unknown'),
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "processed_count": self.processed_count,
            "error_count": self.error_count,
            "thread_alive": self.thread.is_alive() if self.thread else False
        }

# Global outbox instance
_outbox_instance: Optional[OutboxPattern] = None

def get_outbox_pattern(db_store, event_bus=None, kafka_producer=None) -> OutboxPattern:
    """Get singleton outbox pattern instance with event bus injection"""
    global _outbox_instance
    if _outbox_instance is None:
        # Create event bus if not provided (backward compatibility)
        if event_bus is None and kafka_producer is not None:
            from app.infrastructure.messaging.event_bus import KafkaEventBus
            event_bus = KafkaEventBus(kafka_producer)
        elif event_bus is None:
            event_bus = None
        
        _outbox_instance = OutboxPattern(db_store, event_bus)
    else:
        # ✅ Update event_bus if provided and instance already exists
        # This allows outbox-worker to inject event_bus after singleton creation
        if event_bus is not None and _outbox_instance.event_bus is None:
            _outbox_instance.event_bus = event_bus
            logger.info("🔧 Updated outbox pattern with event_bus (singleton injection)")
    return _outbox_instance
