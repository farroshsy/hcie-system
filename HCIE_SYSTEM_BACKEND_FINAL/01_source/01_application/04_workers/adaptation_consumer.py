#!/usr/bin/env python3
"""
Adaptation Consumer - Phase C of B3.3
Consumes CognitionUpdated events and derives pedagogical adaptations

Phase C Constraints:
- MUST NOT contain pedagogy logic (only transport)
- MUST remain cognition-read-only (no learner_progress mutation)
- Semantic idempotency: same CognitionUpdated.event_id → same AdaptationGenerated semantic output
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

from core.adaptation.deterministic_adaptation_engine import get_deterministic_adaptation_engine
from core.adaptation.policy_isolation import get_policy_runtime_registry
from core.adaptation.policy_snapshot import get_policy_snapshot_service  # 🔥 C2.1.5: Immutable policy snapshots
from app.infrastructure.kafka.kafka_factory import KafkaFactory, DefaultKafkaProducerFactory
from app.infrastructure.outbox.outbox_pattern import get_outbox_pattern
from app.services.experiment.runtime_experiment_injection import get_runtime_experiment_injector
from config.env import settings

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

logger = logging.getLogger(__name__)


class AdaptationConsumerService:
    """
    Adaptation Consumer - Transport layer for adaptation derivation
    
    Responsibilities:
    - Consume CognitionUpdated events
    - Validate events
    - Enforce semantic idempotency
    - Invoke DeterministicAdaptationEngine (derive_semantics + materialize_adaptation_event)
    - Emit AdaptationGenerated events via outbox
    - Persist progress metadata
    
    Constraints:
    - NO pedagogy logic in consumer (only transport)
    - Cognition-read-only (no learner_progress mutation)
    - Semantic idempotency: same CognitionUpdated.event_id → same AdaptationGenerated semantic output
    """
    
    def __init__(self):
        """Initialize the adaptation consumer"""
        self.consumer = None
        self.adaptation_engine = None
        self.outbox = None
        self.postgres_store = None
        self.consumer_progress_repo = None
        self.experiment_injector = None  # C2.1.2: Runtime Experiment Injection
        self.policy_runtime_registry = None  # C2.1.3: Policy Runtime Registry
        self.policy_snapshot_service = None  # 🔥 C2.1.5: Immutable policy snapshots
        
        self.processed_count = 0
        self.error_count = 0
        self.running = False
        self.start_time = None
        self.last_health_check = 0
        self.health_check_interval = 60  # seconds
        
        # Semantic idempotency cache (in-memory for Phase C)
        # TODO: Move to Redis for production-scale idempotency
        self.processed_event_ids = set()
    
    def _reconstruct_policy_runtime_from_snapshot(self, snapshot):
        """
        🔥 C2.1.5: Reconstruct PolicyRuntime from immutable snapshot.
        
        This ensures replay uses frozen policy configuration, not mutable live policy.
        The snapshot contains strategy types and parameters, which we use to
        reconstruct the policy runtime instance.
        """
        from core.adaptation.policy_isolation import (
            PolicyRuntime,
            DefaultPacingStrategy,
            DefaultRemediationStrategy,
            DefaultDifficultyStrategy,
            DefaultUXTransformer,
            AggressivePacingStrategy,
            ConservativePacingStrategy
        )
        
        # Map strategy type names to strategy classes
        strategy_classes = {
            "DefaultPacingStrategy": DefaultPacingStrategy,
            "AggressivePacingStrategy": AggressivePacingStrategy,
            "ConservativePacingStrategy": ConservativePacingStrategy,
            "DefaultRemediationStrategy": DefaultRemediationStrategy,
            "DefaultDifficultyStrategy": DefaultDifficultyStrategy,
            "DefaultUXTransformer": DefaultUXTransformer
        }
        
        # Reconstruct strategies from snapshot
        pacing_strategy_class = strategy_classes.get(
            snapshot.pacing_strategy.strategy_type,
            DefaultPacingStrategy
        )
        pacing_strategy = pacing_strategy_class()
        
        remediation_strategy_class = strategy_classes.get(
            snapshot.remediation_strategy.strategy_type,
            DefaultRemediationStrategy
        )
        remediation_strategy = remediation_strategy_class()
        
        difficulty_strategy_class = strategy_classes.get(
            snapshot.difficulty_strategy.strategy_type,
            DefaultDifficultyStrategy
        )
        difficulty_strategy = difficulty_strategy_class()
        
        ux_transformer_class = strategy_classes.get(
            snapshot.ux_transformer.strategy_type,
            DefaultUXTransformer
        )
        ux_transformer = ux_transformer_class()
        
        # Reconstruct PolicyRuntime with frozen configuration
        policy_runtime = PolicyRuntime(
            policy_version=snapshot.policy_version,
            pacing_strategy=pacing_strategy,
            remediation_strategy=remediation_strategy,
            difficulty_strategy=difficulty_strategy,
            ux_transformer=ux_transformer,
            adaptation_parameters=dict(snapshot.adaptation_parameters),
            thresholds=dict(snapshot.thresholds)
        )
        
        logger.debug(
            f"🔒 Reconstructed PolicyRuntime from snapshot {snapshot.snapshot_id} "
            f"(policy={snapshot.policy_version})"
        )
        
        return policy_runtime
        
    def initialize(self):
        """Initialize adaptation consumer with all dependencies"""
        try:
            logger.info("🚀 Initializing Adaptation Consumer...")
            
            # 1. Create Kafka factory and consumer
            kafka_factory = KafkaFactory(settings, producer_factory=DefaultKafkaProducerFactory())
            
            # Subscribe to learning_analytics topic (where CognitionUpdated events are published)
            self.consumer = kafka_factory.create_consumer(
                group_id="adaptation-domain"  # Separate consumer group for adaptation
            )
            
            adaptation_topics = ["learning_analytics"]
            self.consumer.subscribe(adaptation_topics)
            
            logger.info(f"✅ Kafka consumer subscribed to: {adaptation_topics}")
            
            # 2. Create DeterministicAdaptationEngine
            self.adaptation_engine = get_deterministic_adaptation_engine()
            logger.info("✅ DeterministicAdaptationEngine initialized")
            
            # 3. C2.1.2: Initialize Runtime Experiment Injector
            self.experiment_injector = get_runtime_experiment_injector()
            logger.info("✅ RuntimeExperimentInjector initialized")
            
            # 4. C2.1.3: Initialize Policy Runtime Registry
            self.policy_runtime_registry = get_policy_runtime_registry()
            logger.info("✅ PolicyRuntimeRegistry initialized")
            
            # 🔥 C2.1.5: Initialize Policy Snapshot Service (immutable policy state for replay)
            self.policy_snapshot_service = get_policy_snapshot_service()
            logger.info("✅ PolicySnapshotService initialized")
            
            # 5. Create outbox for derived events
            from storage.postgres_store.interaction_store import PostgresInteractionStore
            postgres_store = PostgresInteractionStore()
            
            event_bus = kafka_factory.create_producer()
            self.outbox = get_outbox_pattern(postgres_store, event_bus=event_bus)
            
            logger.info("✅ Outbox pattern initialized")
            
            # 5. Initialize consumer progress repository
            from app.repositories.session_runtime_repository import ConsumerProgressRepository
            self.consumer_progress_repo = ConsumerProgressRepository(postgres_store)
            
            # Load existing progress for restart recovery
            self._load_consumer_progress()
            
            self.start_time = time.time()
            logger.info("🎯 Adaptation Consumer initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize adaptation consumer: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def process_cognition_event(self, event_data: Dict[str, Any]) -> bool:
        """
        Process CognitionUpdated event and derive adaptation
        
        Constraints:
        - Cognition-read-only (no learner_progress mutation)
        - Semantic idempotency: same CognitionUpdated.event_id → same AdaptationGenerated semantic output
        """
        try:
            # Extract trace context from event payload
            trace_context = None
            if TRACE_CONTEXT_AVAILABLE:
                trace_context = extract_trace_from_event(event_data)
                if trace_context:
                    # Set trace context for this processing span
                    trace_context = trace_context.create_child(component="adaptation_consumer")
                    set_trace_context(trace_context)
                    logger.info(f"🔍 Trace context extracted: {trace_context.trace_id} (span: {trace_context.span_id})")
            
            # Validate event type
            event_type = event_data.get("event_type")
            if event_type != "CognitionUpdated":
                logger.debug(f"⏭️ Skipping non-CognitionUpdated event: {event_type}")
                return True  # Not an error, just skip
            
            # Validate required fields
            required_fields = ["event_id", "user_id", "result"]
            for field in required_fields:
                if field not in event_data:
                    logger.error(f"❌ Missing required field: {field}")
                    return False
            
            # Extract event data
            event_id = event_data["event_id"]
            user_id = event_data["user_id"]
            cognition_result = event_data["result"]
            
            # 🔥 SEMANTIC IDEMPOTENCY CHECK
            # Same CognitionUpdated.event_id → same AdaptationGenerated semantic output
            if event_id in self.processed_event_ids:
                logger.debug(f"⏭️ Already processed event (semantic idempotency): {event_id}")
                return True  # Not an error, just skip
            
            # Extract cognition snapshot from CognitionUpdated event
            cognition_snapshot = {
                "mastery": cognition_result.get("mastery", 0.0),
                "uncertainty": cognition_result.get("uncertainty", 1.0),
                "zpd_score": cognition_result.get("zpd_score", 0.0),
                "bayesian_alpha": cognition_result.get("bayesian_alpha"),
                "bayesian_beta": cognition_result.get("bayesian_beta"),
                "kalman_mastery": cognition_result.get("kalman_mastery"),
                "kalman_covariance": cognition_result.get("kalman_covariance"),
                "lyapunov_mastery": cognition_result.get("lyapunov_mastery")
            }
            
            # 🔥 C2.1.2: Get experiment context for user
            experiment_context = self.experiment_injector.get_experiment_context(user_id)
            policy_version = self.experiment_injector.get_policy_version_for_user(user_id)
            
            # Use assigned policy version from experiment, fallback to default
            active_policy_version = policy_version if policy_version else "v1.0.0"
            
            # 🔥 C2.1.3: Get PolicyRuntime for the assigned policy version
            policy_runtime = self.policy_runtime_registry.get_runtime(active_policy_version)
            
            if experiment_context.is_active():
                logger.info(
                    f"🧪 Active experiment context for user {user_id}: "
                    f"experiment={experiment_context.experiment_id}, "
                    f"policy={active_policy_version}"
                )
                logger.debug(f"🎯 PolicyRuntime loaded: {policy_runtime.policy_version}")
            
            # 🔥 ATOMIC TRANSACTION WRAPPER
            from app.infrastructure.unit_of_work import get_transaction
            from storage.postgres_store.interaction_store import PostgresInteractionStore
            postgres_store = PostgresInteractionStore()
            
            # 🔥 CRITICAL: Wrap entire processing in atomic transaction
            with get_transaction(postgres_store) as tx:
                try:
                    logger.info(f"🧠 Processing CognitionUpdated event: {event_id} for user {user_id}")
                    
                    # 🔥 C2.1.3: Extract additional context needed for policy-specific decisions
                    tasks_completed = event_data.get("tasks_completed", 0)
                    learner_engagement = event_data.get("learner_engagement", 0.5)
                    recent_errors = event_data.get("recent_errors", 0)
                    error_pattern = event_data.get("error_pattern", "unknown")
                    difficulty_level = cognition_snapshot.get("difficulty_level", 0.5)
                    
                    # 🔥 C2.1.5: Use immutable policy snapshot for replay-safe adaptation derivation
                    # Get snapshot for this experiment/policy version to ensure replay validity
                    policy_snapshot = None
                    if experiment_context.is_active():
                        from app.services.experiment.experiment_registry import get_experiment_registry
                        experiment_registry = get_experiment_registry()
                        snapshot_ids = experiment_registry.get_policy_snapshots(experiment_context.experiment_id)
                        
                        if snapshot_ids:
                            # Find snapshot matching the assigned policy version
                            for snapshot_id in snapshot_ids:
                                snapshot = self.policy_snapshot_service.get_snapshot(snapshot_id)
                                if snapshot and snapshot.policy_version == active_policy_version:
                                    policy_snapshot = snapshot
                                    logger.debug(f"🔒 Using policy snapshot {snapshot_id} for replay-safe adaptation")
                                    break
                    
                    # Fallback to live policy runtime if no snapshot (for non-experiment or legacy cases)
                    if policy_snapshot is None:
                        logger.debug(f"⚠️ No snapshot found for policy {active_policy_version}, using live runtime")
                        policy_runtime = self.policy_runtime_registry.get_runtime(active_policy_version)
                        if not policy_runtime:
                            logger.error(f"❌ Policy version {active_policy_version} not found in registry")
                            return False
                    else:
                        # 🔥 C2.1.5: Reconstruct PolicyRuntime from immutable snapshot
                        # This ensures replay uses frozen policy configuration, not mutable live policy
                        policy_runtime = self._reconstruct_policy_runtime_from_snapshot(policy_snapshot)
                    
                    # 🔥 LAYER 1: Pure semantic derivation using PolicyRuntime strategies
                    # Use policy-specific pacing, remediation, difficulty, and UX strategies
                    pacing_decision = policy_runtime.calculate_pacing_decision(
                        cognition_snapshot=cognition_snapshot,
                        tasks_completed=tasks_completed,
                        learner_engagement=learner_engagement
                    )
                    
                    remediation_decision = policy_runtime.calculate_remediation_decision(
                        recent_errors=recent_errors,
                        error_pattern=error_pattern,
                        cognition_snapshot=cognition_snapshot
                    )
                    
                    difficulty_decision = policy_runtime.calculate_difficulty_decision(
                        current_difficulty=difficulty_level,
                        recent_correctness=cognition_snapshot.get("recent_correctness", 0.5),
                        cognition_snapshot=cognition_snapshot
                    )
                    
                    # Transform UX semantics using policy-specific transformer
                    ux_semantics = policy_runtime.transform_ux_semantics(
                        cognition_snapshot=cognition_snapshot
                    )
                    
                    # Build semantic adaptation from policy-specific decisions
                    # Create SemanticAdaptation object for materialization
                    from core.adaptation.deterministic_adaptation_engine import SemanticAdaptation
                    from core.adaptation.policy_isolation import PolicyRuntime
                    
                    # Determine adaptation type based on policy decisions
                    adaptation_type = "pacing_adjustment"  # Default, could be derived from decisions
                    if remediation_decision.get("should_remediate"):
                        adaptation_type = "remediation"
                    elif difficulty_decision.get("difficulty_adjustment", 0) != 0:
                        adaptation_type = "difficulty_adjustment"
                    
                    # Build recommendation from policy-specific decisions
                    recommendation = {
                        "pacing_decision": pacing_decision,
                        "remediation_decision": remediation_decision,
                        "difficulty_decision": difficulty_decision,
                        "ux_semantics": ux_semantics,
                        "adaptation_parameters": policy_runtime.adaptation_parameters,
                        "thresholds": policy_runtime.thresholds
                    }
                    
                    # Compute deterministic inputs hash
                    deterministic_inputs_hash = self.adaptation_engine.compute_deterministic_inputs_hash(
                        cognition_snapshot=cognition_snapshot,
                        policy_version=active_policy_version,
                        adaptation_type=adaptation_type
                    )
                    
                    # Create SemanticAdaptation object
                    policy_adaptation = SemanticAdaptation(
                        adaptation_type=adaptation_type,
                        recommendation=recommendation,
                        deterministic_inputs_hash=deterministic_inputs_hash,
                        policy_version=active_policy_version,
                        policy_inputs_schema_version=policy_runtime.get_policy_inputs_schema_version() if hasattr(policy_runtime, 'get_policy_inputs_schema_version') else "1.0.0",
                        schema_version=self.adaptation_engine.SCHEMA_VERSION
                    )
                    
                    # 🔥 LAYER 2: Event materialization (adds transport metadata)
                    adaptation_event = self.adaptation_engine.materialize_adaptation_event(
                        semantic_adaptation=policy_adaptation,  # Use policy-specific adaptation
                        cognition_snapshot=cognition_snapshot,
                        user_id=user_id,
                        session_id=event_data.get("session_id"),
                        causation_id=event_id,  # Semantic lineage: link to CognitionUpdated
                        trace_context={
                            'trace_id': trace_context.trace_id if trace_context else None,
                            'span_id': trace_context.span_id if trace_context else None,
                            'parent_span_id': trace_context.parent_span_id if trace_context else None
                        } if trace_context else None
                    )
                    
                    # 🔥 C2.1.4: Attach experiment lineage to AdaptationGenerated event
                    # Lineage is causal, not metadata - must be individual fields for replay
                    if experiment_context.is_active():
                        adaptation_event["experiment_id"] = experiment_context.experiment_id
                        adaptation_event["policy_version"] = experiment_context.policy_version
                        adaptation_event["cohort_id"] = experiment_context.cohort_id
                        adaptation_event["assignment_hash"] = experiment_context.assignment_hash
                        logger.debug(
                            f"🧪 Attached experiment lineage to AdaptationGenerated: "
                            f"experiment={experiment_context.experiment_id}, "
                            f"policy={active_policy_version}"
                        )
                    
                    # 🔥 EMIT AdaptationGenerated event via outbox
                    outbox_event = self.outbox.create_event(
                        event_id=adaptation_event["event_id"],
                        event_type=adaptation_event["event_type"],
                        topic="learning_analytics",  # Same topic, filtered by event_type
                        payload=adaptation_event
                    )
                    
                    self.outbox.save_event(outbox_event, transaction=tx)
                    logger.info(f"✅ AdaptationGenerated event emitted: {adaptation_event['event_id']}, type={policy_adaptation.adaptation_type}")
                    
                    # 🔥 SEMANTIC IDEMPOTENCY: Mark event as processed
                    self.processed_event_ids.add(event_id)
                    
                    # Log successful processing
                    trace_info = f" trace={trace_context.trace_id}" if trace_context else ""
                    logger.info(f"✅ Cognition event processed atomically: {event_id} → adaptation={policy_adaptation.adaptation_type}{trace_info}")
                    
                    # Transaction commits here automatically
                    self.processed_count += 1
                    return True
                    
                except Exception as e:
                    # Transaction rolls back automatically
                    logger.error(f"❌ Adaptation derivation failed, transaction rolled back: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    raise
            
        except Exception as e:
            logger.error(f"❌ Failed to process cognition event: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.error_count += 1
            return False
    
    def run(self):
        """Main consumer loop"""
        if not self.initialize():
            logger.error("❌ Failed to initialize, exiting")
            return
        
        self.running = True
        self.start_time = time.time()
        logger.info("🚀 Starting Adaptation Consumer loop...")
        
        try:
            while self.running:
                # Poll for messages
                try:
                    message_batch = self.consumer.poll(timeout_ms=1000)
                except Exception as e:
                    logger.error(f"❌ Poll error: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    continue
                
                for topic_partition, messages in message_batch.items():
                    for message in messages:
                        try:
                            # Deserialize event (handle both bytes and dict)
                            if isinstance(message.value, bytes):
                                deserialized = json.loads(message.value.decode('utf-8'))
                            elif isinstance(message.value, dict):
                                deserialized = message.value
                            else:
                                deserialized = json.loads(message.value)
                            
                            # Process the cognition event
                            success = self.process_cognition_event(deserialized)
                            
                            if success:
                                self.processed_count += 1
                            else:
                                logger.warning(f"⚠️ Failed to process event, skipping: {deserialized.get('event_id')}")
                                self.error_count += 1
                                
                        except Exception as e:
                            logger.error(f"❌ Error processing message: {e}")
                            import traceback
                            logger.error(traceback.format_exc())
                
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
        
        # Persist consumer progress metadata
        self._save_consumer_progress()
    
    def shutdown(self):
        """Graceful shutdown"""
        logger.info("🛑 Shutting down Adaptation Consumer...")
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
        
        # Persist final consumer progress metadata
        self._save_consumer_progress()
    
    def _load_consumer_progress(self):
        """Load consumer progress metadata for restart recovery"""
        if not self.consumer_progress_repo:
            return
        
        try:
            consumer_id = "adaptation-consumer"
            topic = "learning_analytics"
            
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
        """Save consumer progress metadata for restart recovery"""
        if not self.consumer_progress_repo:
            return
        
        try:
            consumer_id = "adaptation-consumer"
            topic = "learning_analytics"
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
    consumer_service = AdaptationConsumerService()
    consumer_service.run()
