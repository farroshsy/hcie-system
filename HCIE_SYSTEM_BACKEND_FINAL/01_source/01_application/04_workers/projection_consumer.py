#!/usr/bin/env python3
"""
Projection Consumer - B3.4 Projection Enrichment Pipeline

Transforms ProjectionService from synchronous to async materialized view:
- Consumes CognitionUpdated events from learning_analytics topic
- Consumes AdaptationGenerated events from learning_analytics topic
- Generates learner projections from cognitive state
- Enriches projections with adaptation semantics
- Emits ProjectionUpdated events (cognition + adaptation enrichment)
- Streams updates via WebSocket

Architecture:
CognitionUpdated → AdaptationGenerated → Projection enrichment/materialization → Frontend

ProjectionUpdated = pure cognition projection + adaptation enrichment

This creates:
- ONE stable semantic layer for frontend (LearnerProjection)
- Replayable frontend state
- Reconstructable learner journeys
- Async-safe pedagogy
- Topology-consistent UX
- Frontend becomes declarative, thin, cacheable, replay-safe, topology-independent, replaceable
"""

import os
import sys
import logging
import time
import json
from typing import Dict, Any, Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.session.projection_service import ProjectionService
from core.projection.ux_semantics import UXSemanticsTransformer
from app.infrastructure.kafka.kafka_factory import KafkaFactory, DefaultKafkaProducerFactory
from app.infrastructure.outbox.outbox_pattern import get_outbox_pattern
from config.env import settings
from storage.postgres_store.interaction_store import PostgresInteractionStore

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
    logging.warning("⚠️ Trace context not available")

logger = logging.getLogger(__name__)


class ProjectionConsumerService:
    """
    Projection Consumer - B3.4 Projection Enrichment Pipeline
    
    Consumes CognitionUpdated and AdaptationGenerated events.
    Generates ProjectionUpdated events with adaptation enrichment.
    
    Architecture:
    - CognitionUpdated triggers pure cognition projection
    - AdaptationGenerated triggers projection enrichment
    - Frontend consumes ONE enriched ProjectionUpdated event
    """
    
    def __init__(self):
        self.running = False
        self.consumer = None
        self.producer = None
        self.projection_service = None
        self.postgres_store = None
        self.redis_store = None
        self.outbox = None
        self.health_check_interval = 30
        self.last_health_check = time.time()  # Initialize to avoid NoneType error
        
        # Metrics
        self.processed_count = 0
        self.error_count = 0
        self.start_time = None
        
        # B3.4: In-memory projection cache for enrichment
        # 🔥 C2.1.4: Cache key now includes experiment lineage to prevent cross-policy contamination
        # Key: (user_id, concept_id, policy_version, experiment_id) -> projection_data
        # Without this: cross-policy projection contamination = replay corruption
        # TODO: Move to Redis for production-scale caching
        self.projection_cache = {}
        
    def initialize(self):
        """Initialize projection consumer with all dependencies"""
        try:
            logger.info("🚀 Initializing Projection Consumer...")
            
            # 1. Create Kafka factory and consumer
            kafka_factory = KafkaFactory(settings, producer_factory=DefaultKafkaProducerFactory())
            
            # Subscribe to learning_analytics topic (CognitionUpdated events)
            # Note: Currently LearningProcessed events are emitted, need CognitionUpdated
            self.consumer = kafka_factory.create_consumer(
                group_id="projection-domain"
            )
            
            learning_analytics_topics = ["learning_analytics"]
            self.consumer.subscribe(learning_analytics_topics)
            
            logger.info(f"✅ Kafka consumer subscribed to: {learning_analytics_topics}")
            
            # 2. Create Kafka producer for projection updates
            self.producer = kafka_factory.create_producer()
            
            # 3. Create database store
            postgres_store = PostgresInteractionStore()
            self.postgres_store = postgres_store
            self._ensure_projection_table()
            
            # 4. Create outbox for projection events
            self.outbox = get_outbox_pattern(postgres_store, event_bus=self.producer)
            
            # 5. Create ProjectionService
            # Initialize with required dependencies
            from storage.redis_store.redis_store import RedisFeatureStore
            redis_store = RedisFeatureStore()
            self.redis_store = redis_store
            
            self.projection_service = ProjectionService(
                cognitive_store=postgres_store,
                cache_store=redis_store
            )
            
            logger.info("✅ Projection Consumer initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize projection consumer: {e}")
            return False

    def _ensure_projection_table(self) -> None:
        """Create the derived projection read-model table if missing."""
        self.postgres_store.execute_write(
            """
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_name = 'learner_projections'
                )
                AND NOT EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_name = 'learner_projections'
                      AND column_name = 'concept_id'
                )
                THEN
                    ALTER TABLE learner_projections
                    RENAME TO learner_projections_legacy_slice2;
                END IF;
            END $$;

            CREATE TABLE IF NOT EXISTS learner_projections (
                user_id TEXT NOT NULL,
                concept_id TEXT NOT NULL,
                recommended_concept TEXT NOT NULL,
                projection JSONB NOT NULL DEFAULT '{}'::jsonb,
                ux_semantics JSONB NOT NULL DEFAULT '{}'::jsonb,
                governance JSONB NOT NULL DEFAULT '{}'::jsonb,
                cold_start JSONB NOT NULL DEFAULT '{}'::jsonb,
                selection_metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
                capability_manifest_fingerprint TEXT,
                source_event_id TEXT,
                synthetic BOOLEAN NOT NULL DEFAULT FALSE,
                traffic_type TEXT NOT NULL DEFAULT 'research',
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (user_id, concept_id)
            );
            ALTER TABLE learner_projections
            ADD COLUMN IF NOT EXISTS synthetic BOOLEAN NOT NULL DEFAULT FALSE;
            ALTER TABLE learner_projections
            ADD COLUMN IF NOT EXISTS traffic_type TEXT NOT NULL DEFAULT 'research';
            CREATE INDEX IF NOT EXISTS idx_learner_projections_user_updated
            ON learner_projections(user_id, updated_at DESC);
            """,
            (),
        )

    def _cache_projection(self, user_id: str, row: Dict[str, Any]) -> None:
        if not self.redis_store:
            return
        try:
            client = getattr(self.redis_store, "redis_client", None) or getattr(self.redis_store, "client", None)
            if client is None and hasattr(self.redis_store, "_ensure_connected"):
                client = self.redis_store._ensure_connected()
            if client is not None:
                client.setex(
                    f"learner_projection:{user_id}:latest",
                    30,
                    json.dumps(row, default=str),
                )
        except Exception as exc:
            logger.debug("Projection cache write skipped for %s: %s", user_id, exc)

    def _upsert_learner_projection(
        self,
        *,
        user_id: str,
        concept: str,
        event_id: str,
        projection: Dict[str, Any],
        ux_semantics: Dict[str, Any],
        cognitive_state: Dict[str, Any],
        event_data: Dict[str, Any],
        adaptation: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Persist derived projection row from `learning_analytics` only."""
        if not self.postgres_store:
            raise RuntimeError("postgres_store is not initialized")

        recommended = concept
        if projection.get("recommended_concepts"):
            recommended = projection["recommended_concepts"][0]
        if ux_semantics.get("next_concept_guidance"):
            recommended = ux_semantics.get("next_concept_guidance") or recommended

        result = event_data.get("result", {}) or {}
        governance = {
            "J_value": cognitive_state.get("J_value"),
            "zpd_score": cognitive_state.get("zpd_score"),
            "zpd_target": cognitive_state.get("zpd_target"),
            "uncertainty": cognitive_state.get("uncertainty"),
            "adaptive_rate": cognitive_state.get("adaptive_rate"),
            "transfer_amounts": cognitive_state.get("transfer_amounts"),
        }
        selection_metrics = {
            "policy_type": "projection_store",
            "source_topic": "learning_analytics",
            "source_event_type": event_data.get("event_type"),
            "deterministic": bool(event_data.get("deterministic_inputs_hash")),
            "adaptation_enriched": adaptation is not None,
        }
        if event_data.get("deterministic_inputs_hash"):
            selection_metrics["deterministic_inputs_hash"] = event_data["deterministic_inputs_hash"]

        capability_manifest_fingerprint = (
            event_data.get("capability_manifest_fingerprint")
            or result.get("capability_manifest_fingerprint")
        )

        # Determine traffic type from user_id
        traffic_type = "human"  # default
        if str(user_id).startswith("run-") or str(user_id).startswith("synthetic:") or str(user_id).startswith("ex_"):
            traffic_type = "research"
        if event_data.get("traffic_type"):
            traffic_type = event_data.get("traffic_type")

        row_payload = {
            "projection": projection,
            "ux_semantics": ux_semantics,
            "governance": governance,
            "cold_start": result.get("cold_start", {}),
            "selection_metrics": selection_metrics,
            "adaptation": adaptation,
        }

        self.postgres_store.execute_write(
            """
            INSERT INTO learner_projections (
                user_id, concept_id, recommended_concept, projection,
                ux_semantics, governance, cold_start, selection_metrics,
                capability_manifest_fingerprint, source_event_id, synthetic, traffic_type, updated_at
            )
            VALUES (%s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s::jsonb, %s::jsonb, %s, %s, %s, %s, NOW())
            ON CONFLICT (user_id, concept_id)
            DO UPDATE SET
                recommended_concept = EXCLUDED.recommended_concept,
                projection = EXCLUDED.projection,
                ux_semantics = EXCLUDED.ux_semantics,
                governance = EXCLUDED.governance,
                cold_start = EXCLUDED.cold_start,
                selection_metrics = EXCLUDED.selection_metrics,
                capability_manifest_fingerprint = EXCLUDED.capability_manifest_fingerprint,
                source_event_id = EXCLUDED.source_event_id,
                synthetic = EXCLUDED.synthetic,
                traffic_type = EXCLUDED.traffic_type,
                updated_at = NOW()
            """,
            (
                user_id,
                concept,
                recommended,
                json.dumps(projection, default=str),
                json.dumps(ux_semantics, default=str),
                json.dumps(governance, default=str),
                json.dumps(result.get("cold_start", {}), default=str),
                json.dumps(selection_metrics, default=str),
                capability_manifest_fingerprint,
                event_id,
                str(user_id).startswith("synthetic:"),
                traffic_type,
            ),
        )

        self._cache_projection(
            user_id,
            {
                "user_id": user_id,
                "concept_id": concept,
                "recommended_concept": recommended,
                **row_payload,
                "capability_manifest_fingerprint": capability_manifest_fingerprint,
                "source_event_id": event_id,
            },
        )
    
    def process_cognition_event(self, event_data: Dict[str, Any]) -> bool:
        """
        Process CognitionUpdated event and generate ProjectionUpdated event
        
        B3.4: This now caches the projection for later adaptation enrichment.
        """
        try:
            # B3.6: Extract trace context from event payload
            trace_context = None
            if TRACE_CONTEXT_AVAILABLE:
                trace_context = extract_trace_from_event(event_data)
                if trace_context:
                    # Set trace context for this processing span
                    trace_context = trace_context.create_child(component="projection_consumer")
                    set_trace_context(trace_context)
                    logger.info(f"🔍 Trace context extracted: {trace_context.trace_id} (span: {trace_context.span_id})")
            
            # Extract event data
            event_id = event_data.get("event_id")
            user_id = event_data.get("user_id")
            concept = event_data.get("concept_id") or event_data.get("concept")  # 🔥 C2.1.4: Prefer concept_id (canonical), fallback to concept for backward compatibility
            
            if not user_id:
                logger.error("❌ Missing user_id in event")
                return False
            
            logger.info(f"🔄 Processing cognition event: {event_id} for user {user_id}")
            
            # Extract cognitive state from event result
            result = event_data.get("result", {})
            cognitive_state = {
                "mastery": result.get("mastery", 0.0),
                "uncertainty": result.get("uncertainty", 0.0),
                "confidence": result.get("confidence", 0.5),
                "bayesian_alpha": result.get("bayesian_alpha", 1.0),
                "bayesian_beta": result.get("bayesian_beta", 1.0),
                "kalman_mastery": result.get("kalman_mastery", 0.5),
                "kalman_covariance": result.get("kalman_covariance", 0.5),
                "lyapunov_mastery": result.get("lyapunov_mastery", 0.5),
                "zpd_score": result.get("zpd_score", 0.0),
                "zpd_target": result.get("zpd_target", 0.7),
                "J_value": result.get("J_value", 0.0),
                "adaptive_rate": result.get("adaptive_rate", 0.5),
                "transfer_amounts": result.get("transfer_amounts", {}),
                "streak_length": result.get("streak_length", 0),
                "recent_correctness": result.get("recent_correctness", 0.5),
                "streak_trend": result.get("streak_trend", "stable"),
                "recent_mastery_variance": result.get("recent_mastery_variance", 0.5)
            }
            
            # C1.1.4: Transform cognition internals into UX semantics
            ux_semantics = UXSemanticsTransformer.transform(cognitive_state)
            ux_semantics_dict = {
                "readiness": ux_semantics.readiness.value,
                "confidence_stability": ux_semantics.confidence_stability.value,
                "challenge_suitability": ux_semantics.challenge_suitability.value,
                "pacing_responsiveness": ux_semantics.pacing_responsiveness.value,
                "cognitive_stability": ux_semantics.cognitive_stability.value,
                "transfer_readiness": ux_semantics.transfer_readiness.value,
                "learning_momentum": ux_semantics.learning_momentum,
                "uncertainty_band": ux_semantics.uncertainty_band,
                "next_concept_guidance": ux_semantics.next_concept_guidance,
                "pedagogical_state": ux_semantics.pedagogical_state,
                "recommended_action": ux_semantics.recommended_action
            }
            
            # Generate learner projection using ProjectionService
            # Use generate_projection_async for B3.4 async pattern
            try:
                projection = self.projection_service.generate_projection_async(
                    user_id=user_id,
                    concept_id=concept,
                    cognitive_state=cognitive_state
                )

                # ProjectionService historically stores projected_mastery on a
                # 0-100 scale (core/18_session/projection_service.py line 142:
                #   projected_mastery = mastery * 100).
                # Normalise to 0-1 before persisting so downstream reads are
                # consistent with every other mastery field in the system.
                if isinstance(projection, dict) and projection.get("projected_mastery") is not None:
                    pm = projection["projected_mastery"]
                    if isinstance(pm, (int, float)) and pm > 1.5:
                        projection["projected_mastery"] = pm / 100.0

                logger.info(f"✅ Generated projection for user {user_id}, concept {concept}")
                
            except Exception as e:
                logger.error(f"❌ Failed to generate projection: {e}")
                return False

            self._upsert_learner_projection(
                user_id=user_id,
                concept=concept,
                event_id=event_id,
                projection=projection,
                ux_semantics=ux_semantics_dict,
                cognitive_state=cognitive_state,
                event_data=event_data,
            )
            
            # B3.4: Cache projection for adaptation enrichment
            # 🔥 C2.1.4: Cache key includes experiment lineage to prevent cross-policy contamination
            policy_version = event_data.get("policy_version", "default")
            experiment_id = event_data.get("experiment_id", "default")
            cache_key = (user_id, concept, policy_version, experiment_id)
            self.projection_cache[cache_key] = {
                "projection": projection,
                "cognitive_state": cognitive_state,
                "event_id": event_id,
                "trace_context": trace_context,
                "adaptation": None,  # Will be filled by AdaptationGenerated event
                "policy_version": policy_version,  # 🔥 C2.1.4: Track for cache validation
                "experiment_id": experiment_id  # 🔥 C2.1.4: Track for cache validation
            }
            
            # Emit ProjectionUpdated event (canonical event type)
            # B3.4: Initially without adaptation enrichment (will be enriched later)
            # C1.1.4: Include UX semantics instead of raw cognition internals
            from datetime import datetime
            _ts = datetime.utcnow().isoformat() + "Z"
            projection_event = {
                "event_id": f"{event_id}_projection",
                "event_type": "ProjectionUpdated",  # ✅ Canonical event type
                "user_id": user_id,
                "concept": concept,  # 🔥 Fixed: use concept (schema expects "concept", not "concept_id")
                "timestamp": _ts,
                "source": "projection_consumer",
                # B4.1.2: UX semantics only (pedagogical, NOT cognition internals)
                # Frontend consumes ONLY UX semantics for learner-facing display
                "ux_semantics": ux_semantics_dict,
                # B3.4: Projection data (pure cognition projection)
                "projection": projection,
                # B3.4: Adaptation enrichment (None initially, will be enriched later)
                "adaptation": None,
                # 🔥 Semantic lineage: causation_id links to CognitionUpdated event
                "causation_id": event_id,
                # 🔥 Trace lineage: correlation_id links to trace context
                "correlation_id": trace_context.trace_id if trace_context else None
            }
            if event_data.get("capability_manifest_fingerprint"):
                projection_event["capability_manifest_fingerprint"] = event_data["capability_manifest_fingerprint"]
            elif result.get("capability_manifest_fingerprint"):
                projection_event["capability_manifest_fingerprint"] = result["capability_manifest_fingerprint"]
            
            # B3.6: Inject trace context into projection event
            if TRACE_CONTEXT_AVAILABLE and trace_context:
                projection_event = inject_trace_to_event(projection_event, trace_context)
            
            # C2.1.4: Propagate experiment lineage from CognitionUpdated
            # Experiment lineage is causal - must be preserved through event chain
            if "experiment_id" in event_data:
                projection_event["experiment_id"] = event_data["experiment_id"]
            if "policy_version" in event_data:
                projection_event["policy_version"] = event_data["policy_version"]
            if "cohort_id" in event_data:
                projection_event["cohort_id"] = event_data["cohort_id"]
            if "assignment_hash" in event_data:
                projection_event["assignment_hash"] = event_data["assignment_hash"]
            
            # Save to outbox
            outbox_event = self.outbox.create_event(
                event_id=projection_event["event_id"],
                event_type=projection_event["event_type"],
                topic="projections",  # ✅ Canonical topic for ProjectionUpdated
                payload=projection_event
            )
            
            self.outbox.save_event(outbox_event)
            
            logger.info(f"📊 Emitted ProjectionUpdated event (cognition-only): {projection_event['event_id']}")
            
            # B4.1.1: WebSocket broadcast now handled by Projection Stream Gateway
            # Canonical topology: ProjectionConsumer → Outbox → Kafka → Projection Stream Gateway → WebSocket
            # Direct asyncio.create_task broadcast removed to eliminate semantic bifurcation risk
            
            self.processed_count += 1
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to process cognition event: {e}")
            self.error_count += 1
            return False
    
    def process_adaptation_event(self, event_data: Dict[str, Any]) -> bool:
        """
        Process AdaptationGenerated event and enrich projection
        
        B3.4: This enriches the cached projection with adaptation semantics.
        """
        try:
            # B3.6: Extract trace context from event payload
            trace_context = None
            if TRACE_CONTEXT_AVAILABLE:
                trace_context = extract_trace_from_event(event_data)
                if trace_context:
                    # Set trace context for this processing span
                    trace_context = trace_context.create_child(component="projection_consumer")
                    set_trace_context(trace_context)
                    logger.info(f"🔍 Trace context extracted: {trace_context.trace_id} (span: {trace_context.span_id})")
            
            # Extract event data
            event_id = event_data.get("event_id")
            user_id = event_data.get("user_id")
            adaptation_type = event_data.get("adaptation_type")
            recommendation = event_data.get("recommendation", {})
            
            if not user_id:
                logger.error("❌ Missing user_id in adaptation event")
                return False
            
            logger.info(f"🔄 Processing adaptation event: {event_id} for user {user_id}, type={adaptation_type}")
            
            # B3.4: Enrich projection with adaptation (deterministic, no external lookups)
            # Extract adaptation enrichment data (pure from event payload)
            adaptation_enrichment = {
                "adaptation_type": adaptation_type,
                "recommendation": recommendation,
                "policy_version": event_data.get("policy_version"),
                "deterministic_inputs_hash": event_data.get("deterministic_inputs_hash")
            }
            
            # C1.1.4: Extract cognitive state from adaptation event and transform to UX semantics
            cognition_snapshot = event_data.get("cognition_snapshot", {})
            cognitive_state = {
                "mastery": cognition_snapshot.get("mastery", 0.0),
                "uncertainty": cognition_snapshot.get("uncertainty", 0.0),
                "confidence": cognition_snapshot.get("confidence", 0.5),
                "bayesian_alpha": cognition_snapshot.get("bayesian_alpha", 1.0),
                "bayesian_beta": cognition_snapshot.get("bayesian_beta", 1.0),
                "kalman_mastery": cognition_snapshot.get("kalman_mastery", 0.5),
                "kalman_covariance": cognition_snapshot.get("kalman_covariance", 0.5),
                "lyapunov_mastery": cognition_snapshot.get("lyapunov_mastery", 0.5),
                "zpd_score": cognition_snapshot.get("zpd_score", 0.0),
                "zpd_target": cognition_snapshot.get("zpd_target", 0.7),
                "J_value": cognition_snapshot.get("J_value", 0.0),
                "adaptive_rate": cognition_snapshot.get("adaptive_rate", 0.5),
                "transfer_amounts": cognition_snapshot.get("transfer_amounts", {}),
                "streak_length": cognition_snapshot.get("streak_length", 0),
                "recent_correctness": cognition_snapshot.get("recent_correctness", 0.5),
                "streak_trend": cognition_snapshot.get("streak_trend", "stable"),
                "recent_mastery_variance": cognition_snapshot.get("recent_mastery_variance", 0.5)
            }
            
            # C1.1.4: Transform cognition internals into UX semantics
            ux_semantics = UXSemanticsTransformer.transform(cognitive_state)
            ux_semantics_dict = {
                "readiness": ux_semantics.readiness.value,
                "confidence_stability": ux_semantics.confidence_stability.value,
                "challenge_suitability": ux_semantics.challenge_suitability.value,
                "pacing_responsiveness": ux_semantics.pacing_responsiveness.value,
                "cognitive_stability": ux_semantics.cognitive_stability.value,
                "transfer_readiness": ux_semantics.transfer_readiness.value,
                "learning_momentum": ux_semantics.learning_momentum,
                "uncertainty_band": ux_semantics.uncertainty_band,
                "next_concept_guidance": ux_semantics.next_concept_guidance,
                "pedagogical_state": ux_semantics.pedagogical_state,
                "recommended_action": ux_semantics.recommended_action
            }
            
            # B3.4: Find cached projection to enrich
            # Since AdaptationGenerated is triggered by CognitionUpdated, we need to find the most recent projection
            # For simplicity, we'll emit an enriched ProjectionUpdated event directly
            # In production, this would use a proper projection store
            
            # Emit enriched ProjectionUpdated event
            projection_payload = event_data.get("cognition_snapshot", {})
            enriched_projection_event = {
                "event_id": f"{event_id}_projection_enriched",
                "event_type": "ProjectionUpdated",  # ✅ Canonical event type
                "user_id": user_id,
                "concept": event_data.get("cognition_snapshot", {}).get("concept_id") or event_data.get("cognition_snapshot", {}).get("concept"),  # 🔥 Fixed: use concept (schema expects "concept", not "concept_id")
                "timestamp": time.time(),
                "source": "projection_consumer",
                # B4.1.2: UX semantics only (pedagogical, NOT cognition internals)
                "ux_semantics": ux_semantics_dict,
                # B3.4: Projection data (required by schema)
                "projection": projection_payload,  # 🔥 Fixed: include projection field from cognition snapshot
                # B3.4: Adaptation enrichment (deterministic from event payload)
                "adaptation": adaptation_enrichment,
                # 🔥 Semantic lineage: causation_id links to AdaptationGenerated event
                "causation_id": event_id,
                # 🔥 Trace lineage: correlation_id links to trace context
                "correlation_id": trace_context.trace_id if trace_context else None
            }
            concept = enriched_projection_event["concept"] or "unknown"
            self._upsert_learner_projection(
                user_id=user_id,
                concept=concept,
                event_id=event_id,
                projection=projection_payload,
                ux_semantics=ux_semantics_dict,
                cognitive_state=cognitive_state,
                event_data=event_data,
                adaptation=adaptation_enrichment,
            )
            if event_data.get("capability_manifest_fingerprint"):
                enriched_projection_event["capability_manifest_fingerprint"] = event_data["capability_manifest_fingerprint"]
            
            # B3.6: Inject trace context into enriched projection event
            if TRACE_CONTEXT_AVAILABLE and trace_context:
                enriched_projection_event = inject_trace_to_event(enriched_projection_event, trace_context)
            
            # C2.1.4: Propagate experiment lineage from AdaptationGenerated
            # Experiment lineage is causal - must be preserved through event chain
            if "experiment_id" in event_data:
                enriched_projection_event["experiment_id"] = event_data["experiment_id"]
            if "policy_version" in event_data:
                enriched_projection_event["policy_version"] = event_data["policy_version"]
            if "cohort_id" in event_data:
                enriched_projection_event["cohort_id"] = event_data["cohort_id"]
            if "assignment_hash" in event_data:
                enriched_projection_event["assignment_hash"] = event_data["assignment_hash"]
            
            # Save to outbox
            outbox_event = self.outbox.create_event(
                event_id=enriched_projection_event["event_id"],
                event_type=enriched_projection_event["event_type"],
                topic="projections",  # ✅ Canonical topic for ProjectionUpdated
                payload=enriched_projection_event
            )
            
            self.outbox.save_event(outbox_event)
            
            logger.info(f"📊 Emitted ProjectionUpdated event (adaptation-enriched): {enriched_projection_event['event_id']}")
            
            # B4.1.1: WebSocket broadcast now handled by Projection Stream Gateway
            # Canonical topology: ProjectionConsumer → Outbox → Kafka → Projection Stream Gateway → WebSocket
            # Direct asyncio.create_task broadcast removed to eliminate semantic bifurcation risk
            
            self.processed_count += 1
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to process adaptation event: {e}")
            self.error_count += 1
            return False
    
    def process_recommendation_event(self, event_data: Dict[str, Any]) -> bool:
        """
        🔥 P0: Process RecommendationGenerated event (single authority persistence)
        
        This event establishes the recommendation decision as the single source of truth.
        ProjectionConsumer persists it to learner_projections, ensuring all downstream
        components observe the same decision.
        
        CRITICAL: This replaces the broken contract where ProjectionService was expected
        to generate recommendations. Projection now observes; it does not generate.
        """
        try:
            user_id = event_data.get("user_id")
            recommended_concept = event_data.get("recommended_concept")
            policy = event_data.get("policy")
            selection_metrics = event_data.get("selection_metrics", {})
            governance = event_data.get("governance", {})
            confidence = event_data.get("confidence", 0.7)
            deterministic_hash = event_data.get("deterministic_inputs_hash")
            
            if not user_id or not recommended_concept:
                logger.error(f"❌ Missing required fields in RecommendationGenerated: user_id={user_id}, recommended_concept={recommended_concept}")
                return False
            
            logger.info(f"🔄 Processing recommendation event: {recommended_concept} for user {user_id} (policy: {policy})")
            
            # 🔥 P0: Update recommendation decision across all user's projection rows
            # Design: concept_id = current/active concept, recommended_concept = next concept
            # Update all rows for this user to reflect the new recommendation
            self.postgres_store.execute_write(
                """
                UPDATE learner_projections
                SET 
                    recommended_concept = %s,
                    selection_metrics = selection_metrics || %s::jsonb,
                    governance = governance || %s::jsonb,
                    capability_manifest_fingerprint = COALESCE(%s, capability_manifest_fingerprint),
                    source_event_id = %s,
                    updated_at = NOW()
                WHERE user_id = %s
                  AND (%s OR synthetic = FALSE)
                """,
                (
                    recommended_concept,
                    json.dumps({"recommendation_authority": "unified_brain_bandit"}, default=str),
                    json.dumps(governance, default=str),
                    deterministic_hash,
                    event_data.get("event_id"),
                    user_id,
                    str(user_id).startswith("synthetic:"),
                ),
            )
            
            # Invalidate cache for this user since recommendations changed
            try:
                client = self._cache_client()
                if client:
                    client.delete(f"learner_projection:live_only:{user_id}:latest")
                    client.delete(f"learner_projection:with_synthetic:{user_id}:latest")
            except Exception:
                pass  # Cache invalidation is best-effort
            
            logger.info(f"✅ Updated recommendation {recommended_concept} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to process recommendation event: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def run(self):
        """Main consumer loop"""
        if not self.initialize():
            logger.error("❌ Failed to initialize, exiting")
            return
        
        self.running = True
        logger.info("🚀 Starting Projection Consumer loop...")
        
        try:
            while self.running:
                # Poll for messages
                message_batch = self.consumer.poll(timeout_ms=1000)
                
                for topic_partition, messages in message_batch.items():
                    for message in messages:
                        try:
                            # Parse event data - handle both dict and bytes formats
                            if isinstance(message.value, dict):
                                event_data = message.value
                            else:
                                event_data = json.loads(message.value.decode('utf-8'))
                            
                            # B3.4: Filter for CognitionUpdated, AdaptationGenerated, and RecommendationGenerated events
                            event_type = event_data.get("event_type")
                            
                            if event_type == "CognitionUpdated":
                                # Process cognition event (pure cognition projection)
                                success = self.process_cognition_event(event_data)
                            elif event_type == "AdaptationGenerated":
                                # Process adaptation event (adaptation enrichment)
                                success = self.process_adaptation_event(event_data)
                            elif event_type == "RecommendationGenerated":
                                # 🔥 P0: Process recommendation event (single authority persistence)
                                success = self.process_recommendation_event(event_data)
                            else:
                                logger.debug(f"⏭️  Skipping non-projection event: {event_type}")
                                continue
                            
                            # Note: HCIEKafkaConsumer handles auto-commit internally
                            # No explicit commit needed
                                
                        except Exception as e:
                            logger.error(f"❌ Error processing message: {e}")
                            import traceback
                            logger.error(traceback.format_exc())
                            # HCIEKafkaConsumer handles auto-commit internally
                
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
        uptime = time.time() - self.start_time if self.start_time else 0
        rate = self.processed_count / uptime if uptime > 0 else 0
        
        logger.info(f"📊 Health Check - Processed: {self.processed_count}, Errors: {self.error_count}, Rate: {rate:.2f}/sec, Uptime: {uptime:.1f}s")
    
    def shutdown(self):
        """Graceful shutdown"""
        logger.info("🛑 Shutting down Projection Consumer...")
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


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"🛑 Received signal {signum}, shutting down...")
    if 'projection_service' in globals():
        projection_service.shutdown()
    sys.exit(0)


if __name__ == "__main__":
    import signal
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and run consumer
    projection_service = ProjectionConsumerService()
    projection_service.run()
