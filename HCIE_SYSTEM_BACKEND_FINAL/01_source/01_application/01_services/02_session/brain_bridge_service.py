"""
Brain Bridge Service - Runtime Coordinator to Unified Brain Integration

This service bridges Session Runtime with Unified Brain:
- Translates Session Runtime concepts to Unified Brain concepts
- Writes outbox events for distributed cognition processing
- Extracts pedagogical-safe state from governance internals
- Maintains architectural separation between cognition and pedagogy

Key Design Principles:
- Unified Brain is the canonical cognition authority
- Runtime Coordinator orchestrates, does NOT simulate cognition
- Only ProjectionService translates cognition to pedagogical state
- Frontend NEVER sees JT, ensemble weights, bandit state, governance internals
- B3.1a: Outbox-backed event emission instead of direct calls
"""

from typing import Dict, Any, Optional
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)

try:
    from core.learning.unified_brain import (
        process_learning_event,
        LearningResult
    )
    UNIFIED_BRAIN_AVAILABLE = True
except ImportError:
    UNIFIED_BRAIN_AVAILABLE = False
    print("⚠️ Unified Brain not available, using placeholder cognition")

try:
    from core.telemetry.trace_context import (
        get_trace_context,
        set_trace_context,
        create_trace_context,
        inject_trace_to_event,
        extract_trace_from_event,
        TraceContext
    )
    TRACE_CONTEXT_AVAILABLE = True
except ImportError:
    TRACE_CONTEXT_AVAILABLE = False
    print("⚠️ Trace context not available")


class BrainBridgeService:
    """
    Bridge between Session Runtime and Unified Brain.
    
    This service:
    - Translates session runtime concepts to unified brain concepts
    - Writes outbox events for distributed cognition processing (B3.1a)
    - Extracts pedagogical-safe state from governance internals
    - Maintains architectural separation
    
    B3.1a: Changed from direct Unified Brain calls to outbox event emission
    """
    
    def __init__(
        self,
        db_store=None,
        event_bus=None,
        deterministic_config=None
    ):
        """
        Initialize brain bridge service.
        
        Args:
            db_store: Database store for outbox pattern (required for B3.1a)
            event_bus: Event bus for outbox pattern (optional)
            deterministic_config: DeterministicModeConfig for deterministic event generation (optional)
        
        Raises:
            RuntimeError: If Unified Brain is not available
            RuntimeError: If db_store is not provided (required for outbox pattern)
        """
        if not UNIFIED_BRAIN_AVAILABLE:
            raise RuntimeError("Unified Brain is not available - cannot initialize BrainBridgeService")
        
        self.db_store = db_store
        self.event_bus = event_bus
        self.deterministic_config = deterministic_config  # 🔥 DETERMINISTIC RUNTIME
        
        # B3.1a: Outbox pattern is REQUIRED
        if not self.db_store:
            raise RuntimeError("db_store is required for BrainBridgeService (B3.1a outbox-backed cognition)")
        
        try:
            from app.infrastructure.outbox.outbox_pattern import get_outbox_pattern
            self.outbox_pattern = get_outbox_pattern(self.db_store, self.event_bus)
        except ImportError as e:
            raise RuntimeError(f"Outbox pattern not available: {e}")
    
    def get_mastery_state(
        self,
        user_id: str,
        concept_id: str
    ) -> Dict[str, float]:
        """
        Get mastery state for a user-concept pair from Unified Brain.
        
        Args:
            user_id: User identifier
            concept_id: Concept identifier
        
        Returns:
            Dict with mastery, uncertainty, confidence
        
        Raises:
            RuntimeError: If Unified Brain read fails
        """
        try:
            result = process_learning_event(
                user_id=user_id,
                concept=concept_id,
                mode="read"
            )
            
            return {
                "mastery": result.mastery,
                "uncertainty": result.uncertainty,
                "confidence": result.confidence,
            }
        except Exception as e:
            raise RuntimeError(f"Failed to get mastery from Unified Brain: {e}")
    
    def process_interaction(
        self,
        user_id: str,
        concept_id: str,
        correct: bool,
        response_time: Optional[float] = None,
        trace_context: Optional[TraceContext] = None
    ) -> Dict[str, Any]:
        """
        Process learning interaction via outbox event emission (B3.1a).
        
        This method writes an outbox event for distributed cognition processing.
        The actual cognition happens asynchronously in the learning-consumer.
        
        Args:
            user_id: User identifier
            concept_id: Concept identifier
            correct: Whether the interaction was correct
            response_time: Time taken to respond (seconds)
            trace_context: Optional trace context for distributed tracing (B3.6)
        
        Returns:
            Dict with event_id for tracking cognition result (async processing)
        
        Raises:
            RuntimeError: If outbox pattern is not available
            RuntimeError: If outbox write fails
        """
        # B3.6: Generate or use provided trace context
        if TRACE_CONTEXT_AVAILABLE and trace_context is None:
            trace_context = get_trace_context()
            if trace_context is None:
                trace_context = create_trace_context(
                    user_id=user_id,
                    source="brain_bridge",
                    component="outbox_emission"
                )
        
        # B3.1a: Write outbox event for distributed cognition
        # 🔥 DETERMINISTIC RUNTIME: Use deterministic UUID generation when in deterministic mode
        if self.deterministic_config and self.deterministic_config.deterministic_uuids:
            from core.determinism.deterministic_uuid import DeterministicUUIDGenerator
            uuid_gen = DeterministicUUIDGenerator(seed=self.deterministic_config.seed)
            event_id = str(uuid_gen.generate(event_type="learning_interaction"))
        else:
            event_id = str(uuid.uuid4())
        
        # Prepare event payload for existing learning-consumer
        # Use existing learning_interaction event type (B3.1a: reuse existing topology)
        # Match production schema: interaction must be a dict with correct/response_time
        # 🔥 F-002 fix: Include Tier1 canonical fields for proper Kafka integration
        # Read current canonical state from database to provide context for learning consumer
        try:
            # Read canonical state directly from database
            from storage.postgres_store.interaction_store import PostgresInteractionStore
            postgres_store = PostgresInteractionStore()
            
            # Query learning_state table for current canonical state
            sql = """
            SELECT state_data FROM learning_state
            WHERE user_id = %s AND concept = %s
            ORDER BY updated_at DESC
            LIMIT 1
            """
            result = postgres_store.execute_read(sql, (user_id, concept_id), fetch_one=True)
            
            if result and result['state_data']:
                current_state = result['state_data']
            else:
                # Use default cold-start values if no state exists
                current_state = {
                    "mastery": 0.3,
                    "uncertainty": 0.2,
                    "zpd_score": 0.5,
                    "bayesian_alpha": 1.0,
                    "bayesian_beta": 2.33,
                    "kalman_mastery": 0.3,
                    "kalman_covariance": 0.05,
                    "lyapunov_mastery": 0.3
                }
        except Exception as e:
            logger.warning(f"Failed to read canonical state for {user_id}/{concept_id}: {e}, using defaults")
            current_state = {
                "mastery": 0.3,
                "uncertainty": 0.2,
                "zpd_score": 0.5,
                "bayesian_alpha": 1.0,
                "bayesian_beta": 2.33,
                "kalman_mastery": 0.3,
                "kalman_covariance": 0.05,
                "lyapunov_mastery": 0.3
            }
        
        event_payload = {
            "event_id": event_id,
            "event_type": "learning_interaction",
            "user_id": user_id,
            "concept": concept_id,
            "interaction": {
                "correct": correct,
                "response_time": response_time or 1.0
            },
            "mode": "write",
            "source": "session_runtime",
            "timestamp": datetime.utcnow().isoformat(),
            # Tier1 canonical fields required by learning consumer
            "mastery": current_state.get("mastery", 0.3),
            "uncertainty": current_state.get("uncertainty", 0.2),
            "zpd_score": current_state.get("zpd_score", 0.5),
            "bayesian_alpha": current_state.get("bayesian_alpha", 1.0),
            "bayesian_beta": current_state.get("bayesian_beta", 2.33),
            "kalman_mastery": current_state.get("kalman_mastery", 0.3),
            "kalman_covariance": current_state.get("kalman_covariance", 0.05),
            "lyapunov_mastery": current_state.get("lyapunov_mastery", 0.3)
        }
        
        # B3.6: Inject trace context into event payload
        if TRACE_CONTEXT_AVAILABLE and trace_context:
            event_payload = inject_trace_to_event(event_payload, trace_context)
        
        # Write to outbox
        if not self.outbox_pattern:
            raise RuntimeError("Outbox pattern not available - cannot process interaction")
        
        try:
            # 🔥 DETERMINISTIC RUNTIME: Pass deterministic metadata to create_event
            deterministic_mode = self.deterministic_config.deterministic if self.deterministic_config else None
            deterministic_seed = self.deterministic_config.seed if self.deterministic_config else None
            
            event = self.outbox_pattern.create_event(
                event_id=event_id,
                event_type="learning_interaction",
                payload=event_payload,
                topic="user-interactions",
                deterministic_mode=deterministic_mode,
                deterministic_seed=deterministic_seed
            )
            self.outbox_pattern.save_event(event)
            
            return {
                "event_id": event_id,
                "status": "pending_cognition",
                "message": "Task attempt submitted for distributed cognition processing",
                "trace_id": trace_context.trace_id if trace_context else None
            }
        except Exception as e:
            raise RuntimeError(f"Failed to write outbox event: {e}")
    
    def get_all_mastery(
        self,
        user_id: str,
        concept_ids: list
    ) -> Dict[str, float]:
        """
        Get mastery for multiple concepts for a user.
        
        Args:
            user_id: User identifier
            concept_ids: List of concept identifiers
        
        Returns:
            Dict of concept_id -> mastery (0-1 scale)
        """
        mastery_state = {}
        for concept_id in concept_ids:
            state = self.get_mastery_state(user_id, concept_id)
            mastery_state[concept_id] = state["mastery"]
        return mastery_state
    
    def get_adaptation_signal(
        self,
        user_id: str,
        concept_id: str
    ) -> Optional[str]:
        """
        Get adaptation signal from Unified Brain (policy).
        
        Args:
            user_id: User identifier
            concept_id: Concept identifier
        
        Returns:
            Policy string (e.g., "hcie", "dag", "random") or None
        
        Raises:
            RuntimeError: If Unified Brain read fails
        """
        try:
            result = process_learning_event(
                user_id=user_id,
                concept=concept_id,
                mode="read"
            )
            return result.policy
        except Exception as e:
            raise RuntimeError(f"Failed to get adaptation signal from Unified Brain: {e}")
    
    def get_zpd_alignment(
        self,
        user_id: str,
        concept_id: str
    ) -> Dict[str, float]:
        """
        Get ZPD alignment metrics from Unified Brain.
        
        Args:
            user_id: User identifier
            concept_id: Concept identifier
        
        Returns:
            Dict with zpd_score, zpd_alignment_error, zpd_target
        
        Raises:
            RuntimeError: If Unified Brain read fails
        """
        try:
            result = process_learning_event(
                user_id=user_id,
                concept=concept_id,
                mode="read"
            )
            return {
                "zpd_score": result.zpd_score,
                "zpd_alignment_error": result.zpd_alignment_error,
                "zpd_target": result.zpd_target
            }
        except Exception as e:
            raise RuntimeError(f"Failed to get ZPD alignment from Unified Brain: {e}")
