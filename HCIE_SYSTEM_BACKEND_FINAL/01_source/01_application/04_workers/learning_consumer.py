#!/usr/bin/env python3
"""
🚀 TRUE LEARNING CONSUMER - Phase 2 Integration
The ONLY place where UnifiedBrain processes learning events

Phase E1 - Ownership Enforcement:
UnifiedBrain establishes ownership context before writing canonical cognition state.
"""

import os
import sys
import logging
import signal
import time
import json
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.learning.unified_brain import UnifiedLearningBrain
from app.infrastructure.kafka.kafka_factory import KafkaFactory, DefaultKafkaProducerFactory
from app.infrastructure.outbox.outbox_pattern import get_outbox_pattern
from app.runtime.composition import RuntimeRole, build_worker_runtime
from config.env import settings

logger = logging.getLogger(__name__)

try:
    from core.telemetry.trace_context import (
        get_trace_context,
        set_trace_context,
        extract_trace_from_event,
        inject_trace_to_event,
        TraceContext
    )
    TRACE_CONTEXT_AVAILABLE = True
except ImportError:
    TRACE_CONTEXT_AVAILABLE = False
    logger.warning("⚠️ Trace context not available - distributed tracing disabled")

try:
    from core.ownership.ownership_enforcement import get_ownership_enforcement, CognitionWriter, with_ownership
    OWNERSHIP_ENFORCEMENT_AVAILABLE = True
except ImportError:
    OWNERSHIP_ENFORCEMENT_AVAILABLE = False
    logger.warning("⚠️ Ownership enforcement not available - enforcement disabled")


def _iso_timestamp() -> str:
    from datetime import datetime
    return datetime.utcnow().isoformat() + "Z"


def _build_learning_processed_payload(
    event_id: str,
    user_id: str,
    concept_id: str,
    result,
    trace_context,
) -> Dict[str, Any]:
    """Schema-compliant LearningProcessed payload (event_schema.CognitionUpdated fields)."""
    payload = {
        "event_id": f"{event_id}_processed",
        "event_type": "LearningProcessed",
        "original_event_id": event_id,
        "user_id": user_id,
        "concept": concept_id,
        "result": {
            "mastery": result.mastery,
            "mastery_before": getattr(result, "mastery_before", None),
            "uncertainty": result.uncertainty,
            "zpd_score": result.zpd_score,
            "processing_mode": result.processing_mode,
            "lyapunov_mastery": getattr(result, "lyapunov_mastery", None),
            "bayesian_alpha": getattr(result, "bayesian_alpha", None),
            "bayesian_beta": getattr(result, "bayesian_beta", None),
            "kalman_mastery": getattr(result, "kalman_mastery", None),
            "kalman_covariance": getattr(result, "kalman_covariance", None),
            "selected_concept": getattr(result, "selected_concept", None),
            "is_exploration": getattr(result, "is_exploration", False),
        },
        "timestamp": _iso_timestamp(),
        "source": "learning_consumer",
        "causation_id": event_id,
        "correlation_id": trace_context.trace_id if trace_context else None,
    }
    if TRACE_CONTEXT_AVAILABLE and trace_context:
        payload = inject_trace_to_event(payload, trace_context)
    return payload


def _build_cognition_updated_payload(
    event_id: str,
    user_id: str,
    concept_id: str,
    result,
    event_data: Dict[str, Any],
    trace_context,
) -> Dict[str, Any]:
    """Schema-compliant CognitionUpdated payload for projection-consumer."""
    ts = _iso_timestamp()
    alpha = getattr(result, "bayesian_alpha", None)
    beta = getattr(result, "bayesian_beta", None)
    bayesian_mastery = (alpha / (alpha + beta)) if alpha and beta else getattr(result, "mastery", 0.3)

    payload = {
        "schema_version": "1.0",
        "event_id": f"{event_id}_cognition",
        "event_type": "CognitionUpdated",
        "source": "learning_consumer",
        "source_service": "learning_consumer",
        "timestamp": ts,
        "event_timestamp": ts,
        "emitted_at": ts,
        "interaction_id": event_id,
        "user_id": user_id,
        "concept_id": concept_id,
        "interaction_number": event_data.get("interaction_number"),
        "state_before": {
            "mastery": getattr(result, "mastery_before", result.mastery),
            "uncertainty": getattr(result, "uncertainty_before", result.uncertainty),
            "ensemble_mastery": getattr(result, "ensemble_mastery_before", result.mastery),
        },
        "state_after": {
            "mastery": result.mastery,
            "uncertainty": result.uncertainty,
            "ensemble_mastery": result.mastery,
            "lyapunov_mastery": getattr(result, "lyapunov_mastery", None),
            "bayesian_mastery": bayesian_mastery,
            "kalman_mastery": getattr(result, "kalman_mastery", None),
        },
        "governance_snapshot": {
            "jt_value": getattr(result, "J_value", None),
            "jt_volatility": getattr(result, "jt_volatility", None),
            "exploration_pressure": getattr(result, "exploration_pressure", None),
            "stability_index": getattr(result, "stability_index", None),
            "ensemble_weights": getattr(result, "ensemble_weights", None),
        },
        "transfer_efficiency": getattr(result, "transfer_efficiency", None),
        "experiment_run_id": event_data.get("experiment_run_id"),
        "causation_id": f"{event_id}_processed",
        "correlation_id": trace_context.trace_id if trace_context else None,
        "result": {
            "mastery": result.mastery,
            "uncertainty": result.uncertainty,
            "zpd_score": result.zpd_score,
            "processing_mode": result.processing_mode,
            "lyapunov_mastery": getattr(result, "lyapunov_mastery", None),
            "bayesian_alpha": alpha,
            "bayesian_beta": beta,
            "kalman_mastery": getattr(result, "kalman_mastery", None),
            "kalman_covariance": getattr(result, "kalman_covariance", None),
            "J_value": getattr(result, "J_value", None),
        },
    }
    for key in ("experiment_id", "policy_version", "cohort_id", "assignment_hash"):
        if key in event_data:
            payload[key] = event_data[key]
    if TRACE_CONTEXT_AVAILABLE and trace_context:
        payload = inject_trace_to_event(payload, trace_context)
    return payload


def _save_outbox_payload(outbox, tx, payload: Dict[str, Any], topic: str) -> None:
    outbox_event = outbox.create_event(
        event_id=payload["event_id"],
        event_type=payload["event_type"],
        topic=topic,
        payload=payload,
    )
    outbox.save_event(outbox_event, transaction=tx)


def safe_deserialize(raw_value):
    """
    Clean deserializer with production schema validation
    From old consumer for compatibility
    """
    try:
        # Handle both string and bytes input
        if isinstance(raw_value, bytes):
            deserialized = json.loads(raw_value.decode('utf-8'))
        elif isinstance(raw_value, str):
            deserialized = json.loads(raw_value)
        else:
            deserialized = raw_value
        
        # Extract payload from envelope if present
        if "payload" in deserialized:
            envelope = deserialized
            deserialized = envelope["payload"]
            logger.info(f"📦 Extracted payload from envelope: {envelope.get('event_id', 'unknown')}")
        elif "data" in deserialized:
            # Legacy format - extract data
            deserialized = deserialized["data"]
            logger.info("📦 Extracted payload from legacy data format")
        
        # Validate required fields
        required_fields = ["event_id", "user_id", "concept", "interaction"]  # Schema uses 'concept' not 'concept_id'
        for field in required_fields:
            if field not in deserialized:
                logger.error(f"❌ Missing required field: {field}")
                return {
                    "_validation_error": "missing_required_field",
                    "error": f"Missing required field: {field}",
                    "raw_data": str(raw_value)[:200]
                }
        
        return deserialized
        
    except json.JSONDecodeError as e:
        return {
            "_validation_error": "json_parse_failed",
            "error": str(e),
            "raw_data": str(raw_value)[:200]
        }
    except Exception as e:
        return {
            "_validation_error": "deserialization_failed",
            "error": str(e),
            "raw_data": str(raw_value)[:200]
        }

class LearningConsumerService:
    """
    🔥 TRUE LEARNING CONSUMER - Single source of truth for learning state
    This is the ONLY place where UnifiedBrain.process_event() is called
    """
    
    def __init__(self):
        """Initialize the learning consumer"""
        self.consumer = None
        self.unified_brain = None
        self.runtime = None
        self.outbox = None
        self.postgres_store = None
        self.consumer_progress_repo = None  # D1 - Consumer progress metadata repository

        self.processed_count = 0
        self.error_count = 0
        self.running = False
        self.start_time = None
        self.last_health_check = 0
        self.health_check_interval = 60  # seconds

    def get_runtime_service(self):
        """Get the runtime service using composition root (Phase 1 foundation)"""
        if self.runtime is None:
            self.runtime = build_worker_runtime(RuntimeRole.LEARNING_CONSUMER, settings)
        return self.runtime
        
    def initialize(self):
        """Initialize learning consumer with all dependencies"""
        try:
            logger.info("🚀 Initializing TRUE Learning Consumer...")
            
            # 🔥 BYPASS WRAPPER: Use raw KafkaConsumer to isolate rebalance issue
            from kafka import KafkaConsumer
            import json
            
            self.consumer = KafkaConsumer(
                bootstrap_servers=settings.kafka_bootstrap_servers,
                group_id="learning-domain",
                auto_offset_reset=settings.kafka_auto_offset_reset,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda m: m.decode('utf-8') if m else None,
                # 🔥 DISABLE AUTO COMMIT: Manual commit after successful processing for transactional semantics
                enable_auto_commit=False,
                # 🔥 FIX REBALANCE LOOP: Increase timeouts to prevent heartbeat failures
                session_timeout_ms=30000,
                heartbeat_interval_ms=10000,
                max_poll_interval_ms=300000,
                max_poll_records=500
            )
            
            # Subscribe to topic
            learning_topics = ["user-interactions"]
            self.consumer.subscribe(learning_topics)
            logger.info(f"✅ Raw KafkaConsumer subscribed to: {learning_topics} (manual commit enabled)")
            
            # 🔥 DEFER UnifiedBrain initialization until AFTER poll loop starts to prevent blocking
            # This prevents heartbeat timeouts during heavy initialization
            self.unified_brain = None
            logger.info("⚠️ UnifiedBrain initialization DEFERRED - will initialize on first message")
            
            self.start_time = time.time()
            logger.info("🎯 TRUE Learning Consumer initialized successfully (deferred UnifiedBrain)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize learning consumer: {e}")
            return False
    
    def _ensure_unified_brain_initialized(self):
        """Lazy initialize UnifiedBrain on first message to prevent blocking during startup"""
        if self.unified_brain is None:
            logger.info("🔥 Lazy initializing UnifiedBrain on first message...")
            try:
                from storage.postgres_store.interaction_store import PostgresInteractionStore
                from storage.redis_store.redis_store import RedisFeatureStore
                from app.infrastructure.kafka.kafka_factory import KafkaFactory, DefaultKafkaProducerFactory
                from config.env import settings
                
                postgres_store = PostgresInteractionStore()
                redis_store = RedisFeatureStore()
                from app.repositories.learning_state_repository import LearningStateRepository

                learning_state_repo = LearningStateRepository(
                    postgres_store,
                    redis_store=redis_store,
                )

                kafka_factory = KafkaFactory(settings, producer_factory=DefaultKafkaProducerFactory())
                event_bus = kafka_factory.create_producer()
                outbox = get_outbox_pattern(postgres_store, event_bus=event_bus)
                self.outbox = outbox
                
                deterministic_config = None
                if settings.enable_deterministic_mode:
                    from core.determinism.deterministic_config import DeterministicModeConfig
                    deterministic_config = DeterministicModeConfig(
                        deterministic=True,
                        seed=settings.deterministic_seed,
                        deterministic_uuids=settings.deterministic_uuids,
                        deterministic_time=settings.deterministic_time,
                        trajectory_determinism=settings.trajectory_determinism
                    )
                    logger.info(f"🔥 Deterministic mode enabled (seed={settings.deterministic_seed})")

                trajectory_recorder = None
                if settings.enable_trajectory_recording:
                    try:
                        from infrastructure.experiment.trajectory_recorder import TrajectoryRecorder
                        postgres_store = PostgresInteractionStore()
                        trajectory_recorder = TrajectoryRecorder(postgres_store)
                        logger.info("🔥 Trajectory recorder initialized for automatic capture")
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to initialize trajectory recorder: {e}")

                # Slice 0a removed `system_mode` (was hardcoded JT in practice).
                self.unified_brain = UnifiedLearningBrain(
                    event_bus=None,
                    outbox=self.outbox,
                    deterministic_config=deterministic_config,
                    trajectory_recorder=trajectory_recorder,
                    redis_store=redis_store,
                    postgres_store=postgres_store,
                    learning_state_repo=learning_state_repo,
                    environment="production",
                )
                
                logger.info("✅ UnifiedBrain lazy initialization complete")
            except Exception as e:
                logger.error(f"❌ Failed to lazy initialize UnifiedBrain: {e}")
                raise

    def process_learning_event(self, event_data: Dict[str, Any], message=None) -> bool:
        """
        🔥 CRITICAL: The ONLY place where learning events are processed
        This maintains single source of truth invariant
        
        Args:
            event_data: The event payload
            message: Kafka message object for explicit offset commit (optional)
        """
        try:
            # 🔥 Lazy initialize UnifiedBrain on first message
            self._ensure_unified_brain_initialized()
            
            # B3.6: Extract trace context from event payload
            trace_context = None
            if TRACE_CONTEXT_AVAILABLE:
                trace_context = extract_trace_from_event(event_data)
                if trace_context:
                    # Set trace context for this processing span
                    trace_context = trace_context.create_child(component="learning_consumer")
                    set_trace_context(trace_context)
                    logger.info(f"🔍 Trace context extracted: {trace_context.trace_id} (span: {trace_context.span_id})")
            
            # Check for validation errors (from safe_deserialize)
            if "_validation_error" in event_data:
                error_type = event_data["_validation_error"]
                logger.error(f"🚨 EXACT VALIDATION FAILURE: {error_type}")
                logger.error(f"🚨 FULL FAILED EVENT: {event_data}")
                return False
            
            # Validate required fields
            required_fields = ["event_id", "user_id", "concept", "interaction"]  # Schema uses 'concept' not 'concept_id'
            for field in required_fields:
                if field not in event_data:
                    logger.error(f"❌ Missing required field: {field}")
                    return False
            
            # Extract event data
            event_id = event_data["event_id"]
            user_id = event_data["user_id"]
            concept_id = event_data["concept"]  # 🔥 Schema uses 'concept' not 'concept_id'
            interaction = event_data["interaction"]
            
            # 🔥 PHASE 5: ATOMIC TRANSACTION WRAPPER
            from app.infrastructure.unit_of_work import get_transaction
            
            # Get Postgres store for transaction
            from storage.postgres_store.interaction_store import PostgresInteractionStore
            postgres_store = PostgresInteractionStore()
            
            # 🔥 CRITICAL: Wrap entire processing in atomic transaction
            with get_transaction(postgres_store) as tx:
                try:
                    # Phase E1: Establish ownership context for UnifiedBrain
                    if OWNERSHIP_ENFORCEMENT_AVAILABLE:
                        ownership = get_ownership_enforcement()
                        ownership.set_writer(CognitionWriter.UNIFIED_BRAIN)
                    
                    # 🔥 CALL UNIFIEDBRAIN - THE ONLY PLACE THIS HAPPENS
                    logger.info(f"🧠 Processing learning event: {event_id} for user {user_id}, concept_id {concept_id}")
                    
                    # B3.6: Pass trace context to UnifiedBrain
                    if TRACE_CONTEXT_AVAILABLE and trace_context:
                        # Add trace_id to event_data for UnifiedBrain
                        event_data["trace_id"] = trace_context.trace_id
                    
                    # � CALL UNIFIEDBRAIN - THE ONLY PLACE THIS HAPPENS
                    result = self.unified_brain.process_event(
                        user_id=user_id,
                        concept=concept_id,
                        interaction=interaction,
                        mode="write",
                        event_id=event_id,
                        interaction_id=event_id,
                        write_enabled=True,
                        event_data=event_data,
                    )
                    if not getattr(result, "event_id", None):
                        result.event_id = event_id
                    
                    # CRITICAL: Save outbox event in SAME transaction
                    # This event contains all cognitive state data for analytics-consumer to derive metrics
                    if self.outbox:
                        learning_payload = _build_learning_processed_payload(
                            event_id, user_id, concept_id, result, trace_context
                        )
                        _save_outbox_payload(
                            self.outbox, tx, learning_payload, topic="learning_analytics"
                        )
                        logger.info(
                            "📊 Published LearningProcessed: %s", learning_payload["event_id"]
                        )
                        cognition_payload = _build_cognition_updated_payload(
                            event_id, user_id, concept_id, result, event_data, trace_context
                        )
                        _save_outbox_payload(
                            self.outbox, tx, cognition_payload, topic="learning_analytics"
                        )
                        logger.info(
                            "📊 Published CognitionUpdated: %s", cognition_payload["event_id"]
                        )

                    # Log successful processing
                    trace_info = f" trace={trace_context.trace_id}" if trace_context else ""
                    logger.info(f"✅ Learning event processed atomically: {event_id} → mastery={result.mastery:.6f}{trace_info}")
                    
                    # Transaction commits here automatically
                    self.processed_count += 1

                    # 🔥 MANUAL COMMIT: Commit offset AFTER successful transaction for transactional semantics
                    if message:
                        try:
                            self.consumer.commit()
                            logger.debug(f"✅ Offset committed for event {event_id}: partition={message.partition}, offset={message.offset}")
                        except Exception as commit_error:
                            logger.warning(f"⚠️ Offset commit failed for event {event_id}: {commit_error}")

                    return True
                    
                except Exception as e:
                    # Transaction rolls back automatically
                    logger.error(f"❌ Learning event processing failed, transaction rolled back: {e}")
                    raise
                    
                finally:
                    # Phase E1: Clear ownership context after processing
                    if OWNERSHIP_ENFORCEMENT_AVAILABLE:
                        ownership = get_ownership_enforcement()
                        ownership.clear_writer()
            
        except Exception as e:
            logger.error(f"❌ Failed to process learning event: {e}")
            self.error_count += 1
            return False
    
    # 🔥 PHASE 5: Derived event publishing now handled in atomic transaction
    # _publish_derived_event removed to ensure all operations are in single transaction
    
    def run(self):
        if not self.initialize():
            logger.error("❌ Failed to initialize, exiting")
            return
        
        self.running = True
        self.start_time = time.time()
        self._start_time = time.time()  # Initialize for processing_time calculation
        logger.info("🚀 Starting TRUE Learning Consumer loop...")
        
        try:
            while self.running:
                # Poll for messages
                try:
                    message_batch = self.consumer.poll(timeout_ms=1000)
                except Exception as e:
                    logger.error(f"❌ Poll error: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    # 🔥 FIX: Recreate consumer with manual commit (consistent with main config)
                    from kafka import KafkaConsumer
                    self.consumer = KafkaConsumer(
                bootstrap_servers=settings.kafka_bootstrap_servers,
                group_id="learning-domain",
                auto_offset_reset=settings.kafka_auto_offset_reset,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda m: m.decode('utf-8') if m else None,
                enable_auto_commit=False,  # 🔥 DISABLE AUTO COMMIT: Manual commit for transactional semantics
                # 🔥 FIX REBALANCE LOOP: Increase timeouts to prevent heartbeat failures
                session_timeout_ms=30000,
                heartbeat_interval_ms=10000,
                max_poll_interval_ms=300000,
                max_poll_records=500
            )
                    logger.warning("⚠️ Consumer recreated after poll error")
                    self.error_count += 1
                    continue

                for topic_partition, messages in message_batch.items():
                    for message in messages:
                        try:
                            # B3.6: Use safe_deserialize for validation (from old consumer)
                            deserialized = safe_deserialize(message.value)
                            
                            # Process the learning event (pass message for explicit offset commit)
                            success = self.process_learning_event(deserialized, message=message)
                            
                            if not success:
                                logger.warning(f"⚠️ Failed to process event, skipping: {deserialized.get('event_id')}")
                                self.error_count += 1
                                
                        except Exception as e:
                            logger.error(f"❌ Error processing message: {e}")
                            import traceback
                            logger.error(traceback.format_exc())
                            # HCIEKafkaConsumer handles commits automatically
                
                # Health check and metrics
                if time.time() - self.last_health_check > self.health_check_interval:
                    self._health_check()
                    self.last_health_check = time.time()
                    
        except KeyboardInterrupt:
            logger.info("🛑 Received shutdown signal")
        except Exception as e:
            logger.error(f"❌ Consumer error: {e}")
            import traceback
            logger.error(traceback.format_exc())
        finally:
            self.shutdown()
    
    def _health_check(self):
        """Periodic health check and metrics reporting"""
        if self.start_time is None:
            logger.warning("⚠️ Health check called before start_time initialized")
            return
        
        uptime = time.time() - self.start_time
        rate = self.processed_count / uptime if uptime > 0 else 0
        
        logger.info(f"📊 Health Check - Processed: {self.processed_count}, Errors: {self.error_count}, Rate: {rate:.2f}/sec, Uptime: {uptime:.1f}s")
        
        # D1 - Persist consumer progress metadata
        self._save_consumer_progress()
    
    def shutdown(self):
        """Graceful shutdown"""
        logger.info("🛑 Shutting down TRUE Learning Consumer...")
        self.running = False
        
        if self.consumer:
            try:
                self.consumer.close()
                logger.info("✅ Kafka consumer closed")
            except Exception as e:
                logger.warning(f"⚠️ Error closing consumer: {e}")
        
        # Final metrics
        uptime = time.time() - self.start_time if self.start_time else 0
        logger.info(f"📊 Final Metrics - Processed: {self.processed_count}, Errors: {self.error_count}, Uptime: {uptime:.1f}s")
        
        # D1 - Persist final consumer progress metadata
        self._save_consumer_progress()
    
    def _load_consumer_progress(self):
        """D1 - Load consumer progress metadata for restart recovery"""
        if not self.consumer_progress_repo:
            return
        
        try:
            consumer_id = "learning-consumer"
            topic = "user-interactions"
            
            # Load progress for all partitions (simplified - assuming single partition for now)
            progress = self.consumer_progress_repo.get_progress(consumer_id, topic, 0)
            
            if progress:
                self.processed_count = progress.get('processed_count', 0)
                self.error_count = progress.get('error_count', 0)
                logger.info(f"🔄 Loaded consumer progress: processed={self.processed_count}, errors={self.error_count}")
            else:
                logger.info("🆕 No existing consumer progress found - starting fresh")
        except Exception as e:
            logger.warning(f"⚠️ Failed to load consumer progress: {e}")
    
    def _save_consumer_progress(self):
        """D1 - Save consumer progress metadata for restart recovery"""
        if not self.consumer_progress_repo:
            return
        
        try:
            consumer_id = "learning-consumer"
            topic = "user-interactions"
            partition = 0
            
            # Get current offset (simplified - using processed_count as proxy)
            offset = self.processed_count
            
            self.consumer_progress_repo.save_progress(
                consumer_id=consumer_id,
                topic=topic,
                partition=partition,
                offset=offset,
                processed_count=self.processed_count,
                error_count=self.error_count
            )
        except Exception as e:
            logger.warning(f"⚠️ Failed to save consumer progress: {e}")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"🛑 Received signal {signum}, shutting down...")
    if 'consumer_service' in globals():
        consumer_service.shutdown()
    sys.exit(0)

if __name__ == "__main__":
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and run consumer
    consumer_service = LearningConsumerService()
    consumer_service.run()

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"🛑 Received signal {signum}, shutting down...")
    if 'consumer_service' in globals():
        consumer_service.shutdown()
    sys.exit(0)

if __name__ == "__main__":
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and run consumer
    consumer_service = LearningConsumerService()
    consumer_service.run()
