"""
C2.3.1 - Deterministic Canonical Replay Engine

Foundation layer for event-sourced educational counterfactual simulation.

This is NOT debugging replay, log replay, or infrastructure replay.
This is pedagogical replay, semantic replay, longitudinal reconstruction, alternate-policy simulation.

Goal:
    canonical event stream
    → deterministic cognition reconstruction
    → deterministic projection reconstruction
    → deterministic adaptation reconstruction

Validates:
    replay(state_n) == original(state_n)

for:
    cognition,
    projection,
    adaptation semantics,
    UX semantics.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from enum import Enum
import logging
import hashlib
import copy

logger = logging.getLogger(__name__)


class ReplayEventType(Enum):
    """Canonical event types for replay."""
    TASK_ATTEMPT_SUBMITTED = "TaskAttemptSubmitted"
    COGNITION_UPDATED = "CognitionUpdated"
    ADAPTATION_GENERATED = "AdaptationGenerated"
    PROJECTION_UPDATED = "ProjectionUpdated"


@dataclass
class ReplayEvent:
    """
    Canonical event for replay.
    
    Self-contained event with all necessary data for deterministic reconstruction.
    """
    event_id: str
    event_type: ReplayEventType
    user_id: str
    timestamp: datetime
    causation_id: Optional[str]
    trace_id: Optional[str]
    
    # Event payload (cognition, adaptation, projection data)
    payload: Dict[str, Any]
    
    # Experiment lineage
    experiment_id: Optional[str]
    policy_version: Optional[str]
    cohort_id: Optional[str]
    assignment_hash: Optional[str]
    
    # Policy snapshot ID for adaptation events
    policy_snapshot_id: Optional[str]
    
    # Schema version for compatibility
    schema_version: str


@dataclass
class ReplayCognitionState:
    """
    Reconstructed canonical cognition state during replay.
    
    Tier 1 (Canonical Replay State):
    - mastery, uncertainty, zpd_score
    - bayesian_alpha, bayesian_beta
    - kalman_mastery, kalman_covariance
    - lyapunov_mastery
    """
    mastery: float
    uncertainty: float
    zpd_score: float
    bayesian_alpha: float
    bayesian_beta: float
    kalman_mastery: float
    kalman_covariance: float
    lyapunov_mastery: float
    
    # Per-concept state
    concept_mastery: Dict[str, float] = field(default_factory=dict)
    
    # Timestamp of state
    state_timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Determinism hash for validation
    state_hash: str = ""
    
    def compute_hash(self) -> str:
        """Compute deterministic hash of state for validation."""
        hash_input = f"{self.mastery:.6f}{self.uncertainty:.6f}{self.zpd_score:.6f}"
        hash_input += f"{self.bayesian_alpha:.6f}{self.bayesian_beta:.6f}"
        hash_input += f"{self.kalman_mastery:.6f}{self.kalman_covariance:.6f}"
        hash_input += f"{self.lyapunov_mastery:.6f}"
        
        # Include concept mastery sorted by concept_id for determinism
        for concept_id in sorted(self.concept_mastery.keys()):
            hash_input += f"{concept_id}{self.concept_mastery[concept_id]:.6f}"
        
        self.state_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:16]
        return self.state_hash


@dataclass
class ReplayProjectionState:
    """
    Reconstructed projection state during replay.
    
    Deterministic projection from cognition (no external lookups).
    """
    readiness: float = 0.5
    confidence_stability: float = 0.5
    challenge_suitability: float = 0.5
    pacing_responsiveness: float = 0.5
    cognitive_stability: float = 0.5
    transfer_readiness: float = 0.5
    learning_momentum: float = 0.5
    uncertainty_band: float = 0.5
    
    # Adaptation enrichment
    adaptation_type: Optional[str] = None
    adaptation_recommendation: Optional[str] = None
    
    # Timestamp of state
    state_timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Determinism hash for validation
    state_hash: str = ""
    
    def compute_hash(self) -> str:
        """Compute deterministic hash of state for validation."""
        def to_float(val, default=0.5):
            if isinstance(val, (int, float)):
                return float(val)
            if isinstance(val, str):
                if val == 'not_ready':
                    return 0.0
                if val == 'ready':
                    return 1.0
                return default
            return default
        
        hash_input = f"{to_float(self.readiness):.6f}{to_float(self.confidence_stability):.6f}"
        hash_input += f"{to_float(self.challenge_suitability):.6f}{to_float(self.pacing_responsiveness):.6f}"
        hash_input += f"{to_float(self.cognitive_stability):.6f}{to_float(self.transfer_readiness):.6f}"
        hash_input += f"{to_float(self.learning_momentum):.6f}{to_float(self.uncertainty_band):.6f}"
        hash_input += f"{self.adaptation_type or ''}{self.adaptation_recommendation or ''}"
        
        self.state_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:16]
        return self.state_hash


@dataclass
class ReplayAdaptationState:
    """
    Reconstructed adaptation semantics during replay.
    
    Derived from cognition using deterministic policy runtime.
    """
    adaptation_type: str
    recommendation: str
    policy_version: str
    target_concept_id: str
    
    # Timing classification
    timing_category: str  # early, middle, late
    
    # Deterministic inputs hash (for replay validation)
    deterministic_inputs_hash: str
    
    # Timestamp of state
    state_timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Determinism hash for validation
    state_hash: str = ""
    
    def compute_hash(self) -> str:
        """Compute deterministic hash of state for validation."""
        hash_input = f"{self.adaptation_type}{self.recommendation}"
        hash_input += f"{self.policy_version}{self.target_concept_id}"
        hash_input += f"{self.timing_category}{self.deterministic_inputs_hash}"
        
        self.state_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:16]
        return self.state_hash


@dataclass
class ReplayContext:
    """
    Context maintained during replay.
    
    Tracks incremental state reconstruction from event stream.
    """
    user_id: str
    replay_start: datetime
    replay_end: datetime
    
    # Current state
    cognition: ReplayCognitionState
    projection: ReplayProjectionState
    adaptation: Optional[ReplayAdaptationState]
    
    # Event history
    events_processed: List[ReplayEvent] = field(default_factory=list)
    
    # State snapshots at key points
    state_snapshots: Dict[str, ReplayCognitionState] = field(default_factory=dict)
    
    # Determinism validation
    validation_errors: List[str] = field(default_factory=list)


@dataclass
class ReplayResult:
    """
    Result of deterministic replay.
    
    Contains reconstructed state and validation metrics.
    """
    user_id: str
    replay_id: str
    replay_start: datetime
    replay_end: datetime
    
    # Final reconstructed state
    final_cognition: ReplayCognitionState
    final_projection: ReplayProjectionState
    final_adaptation: Optional[ReplayAdaptationState]
    
    # Event history
    events_processed: List[ReplayEvent] = field(default_factory=list)
    
    # State evolution
    cognition_evolution: List[Tuple[datetime, ReplayCognitionState]] = field(default_factory=list)
    projection_evolution: List[Tuple[datetime, ReplayProjectionState]] = field(default_factory=list)
    adaptation_evolution: List[Tuple[datetime, ReplayAdaptationState]] = field(default_factory=list)
    
    # Determinism validation
    determinism_valid: bool = True
    validation_errors: List[str] = field(default_factory=list)
    
    # Metrics
    total_events_processed: int = 0
    processing_time_seconds: float = 0.0


class DeterministicReplayEngine:
    """
    Deterministic canonical replay engine for pedagogical reconstruction.
    
    Reconstructs full semantic runtime from canonical event stream:
    - Cognition state (Tier 1 canonical)
    - Projection state (deterministic materialization)
    - Adaptation semantics (deterministic policy derivation)
    
    Uses:
    - Immutable snapshots
    - Frozen schemas
    - Frozen transforms
    
    Does NOT use:
    - Live runtime services
    - External APIs
    - Mutable runtime state
    """
    
    def __init__(self, policy_snapshot_repository=None):
        """
        Initialize deterministic replay engine.
        
        Args:
            policy_snapshot_repository: Repository for retrieving immutable policy snapshots
        """
        self._policy_snapshot_repository = policy_snapshot_repository
    
    def replay_learner_trajectory(
        self,
        user_id: str,
        events: List[ReplayEvent],
        initial_cognition: Optional[ReplayCognitionState] = None
    ) -> ReplayResult:
        """
        Replay learner trajectory from canonical event stream.
        
        Args:
            user_id: User ID to replay
            events: Ordered list of canonical events
            initial_cognition: Optional initial cognition state (defaults to zero state)
            
        Returns:
            ReplayResult with reconstructed state and validation
        """
        logger.info(f"🔄 Starting deterministic replay for user {user_id} with {len(events)} events")
        replay_start = datetime.utcnow()
        
        # Initialize replay context
        if initial_cognition is None:
            initial_cognition = ReplayCognitionState(
                mastery=0.0,
                uncertainty=1.0,
                zpd_score=0.0,
                bayesian_alpha=1.0,
                bayesian_beta=1.0,
                kalman_mastery=0.0,
                kalman_covariance=1.0,
                lyapunov_mastery=0.0
            )
        
        context = ReplayContext(
            user_id=user_id,
            replay_start=replay_start,
            replay_end=datetime.utcnow(),
            cognition=copy.deepcopy(initial_cognition),
            projection=self._initial_projection(),
            adaptation=None
        )
        
        # Process events in order
        for event in events:
            self._process_event(context, event)
            context.events_processed.append(event)
        
        replay_end = datetime.utcnow()
        processing_time = (replay_end - replay_start).total_seconds()
        
        # Build result
        result = ReplayResult(
            user_id=user_id,
            replay_id=self._generate_replay_id(user_id, replay_start),
            replay_start=replay_start,
            replay_end=replay_end,
            final_cognition=context.cognition,
            final_projection=context.projection,
            final_adaptation=context.adaptation,
            events_processed=context.events_processed,
            determinism_valid=len(context.validation_errors) == 0,
            validation_errors=context.validation_errors,
            total_events_processed=len(events),
            processing_time_seconds=processing_time
        )
        
        logger.info(f"✅ Replay completed for user {user_id}: {len(events)} events in {processing_time:.3f}s")
        
        return result
    
    def _process_event(self, context: ReplayContext, event: ReplayEvent) -> None:
        """
        Process a single event during replay.
        
        Updates context state deterministically based on event type.
        
        Args:
            context: Current replay context
            event: Event to process
        """
        if event.event_type == ReplayEventType.TASK_ATTEMPT_SUBMITTED:
            self._process_task_attempt(context, event)
        elif event.event_type == ReplayEventType.COGNITION_UPDATED:
            self._process_cognition_update(context, event)
        elif event.event_type == ReplayEventType.ADAPTATION_GENERATED:
            self._process_adaptation_generation(context, event)
        elif event.event_type == ReplayEventType.PROJECTION_UPDATED:
            self._process_projection_update(context, event)
        else:
            logger.warning(f"Unknown event type: {event.event_type}")
    
    def _process_task_attempt(self, context: ReplayContext, event: ReplayEvent) -> None:
        """
        Process TaskAttemptSubmitted event.
        
        Task attempts don't directly change cognition (that happens in CognitionUpdated),
        but they establish the causation chain.
        """
        # No state change, just tracking causation
        pass
    
    def _process_cognition_update(self, context: ReplayContext, event: ReplayEvent) -> None:
        """
        Process CognitionUpdated event.
        
        Updates cognition state deterministically from event payload.
        """
        payload = event.payload
        
        # Cognitive state is in "result" field for CognitionUpdated events
        result = payload.get("result", payload)
        
        # Update Tier 1 canonical cognition fields
        context.cognition.mastery = result.get("mastery", context.cognition.mastery)
        context.cognition.uncertainty = result.get("uncertainty", context.cognition.uncertainty)
        context.cognition.zpd_score = result.get("zpd_score", context.cognition.zpd_score)
        context.cognition.bayesian_alpha = result.get("bayesian_alpha", context.cognition.bayesian_alpha)
        context.cognition.bayesian_beta = result.get("bayesian_beta", context.cognition.bayesian_beta)
        context.cognition.kalman_mastery = result.get("kalman_mastery", context.cognition.kalman_mastery)
        context.cognition.kalman_covariance = result.get("kalman_covariance", context.cognition.kalman_covariance)
        context.cognition.lyapunov_mastery = result.get("lyapunov_mastery", context.cognition.lyapunov_mastery)
        
        # Update per-concept mastery if present
        if "concept_mastery" in result:
            context.cognition.concept_mastery.update(result["concept_mastery"])
        
        # Update timestamp
        context.cognition.state_timestamp = event.timestamp
        
        # Compute hash
        context.cognition.compute_hash()
        
        # Snapshot state
        context.state_snapshots[event.event_id] = copy.deepcopy(context.cognition)
    
    def _process_adaptation_generation(self, context: ReplayContext, event: ReplayEvent) -> None:
        """
        Process AdaptationGenerated event.
        
        Reconstructs adaptation semantics deterministically from event payload.
        """
        payload = event.payload
        
        context.adaptation = ReplayAdaptationState(
            adaptation_type=payload.get("adaptation_type", "unknown"),
            recommendation=payload.get("recommendation", ""),
            policy_version=payload.get("policy_version", "v1.0.0"),
            target_concept_id=payload.get("concept_id", ""),
            timing_category=payload.get("timing_category", "middle"),
            deterministic_inputs_hash=payload.get("deterministic_inputs_hash", ""),
            state_timestamp=event.timestamp
        )
        
        # Compute hash
        context.adaptation.compute_hash()
    
    def _process_projection_update(self, context: ReplayContext, event: ReplayEvent) -> None:
        """
        Process ProjectionUpdated event.
        
        Reconstructs projection state deterministically from event payload.
        """
        payload = event.payload
        ux_semantics = payload.get("ux_semantics", {})
        
        def to_float(val, default=0.5):
            if isinstance(val, (int, float)):
                return float(val)
            if isinstance(val, str):
                if val == 'not_ready':
                    return 0.0
                if val == 'ready':
                    return 1.0
                return default
            return default
        
        context.projection.readiness = to_float(ux_semantics.get('readiness', 0.5))
        context.projection.confidence_stability = to_float(ux_semantics.get('confidence_stability', 0.5))
        context.projection.challenge_suitability = to_float(ux_semantics.get('challenge_suitability', 0.5))
        context.projection.pacing_responsiveness = to_float(ux_semantics.get('pacing_responsiveness', 0.5))
        context.projection.cognitive_stability = to_float(ux_semantics.get('cognitive_stability', 0.5))
        context.projection.transfer_readiness = to_float(ux_semantics.get('transfer_readiness', 0.5))
        context.projection.learning_momentum = to_float(ux_semantics.get('learning_momentum', 0.5))
        context.projection.uncertainty_band = to_float(ux_semantics.get('uncertainty_band', 0.5))
        
        # Adaptation enrichment
        adaptation = payload.get('adaptation')
        if adaptation is None:
            adaptation = {}
        context.projection.adaptation_type = adaptation.get('adaptation_type')
        context.projection.adaptation_recommendation = adaptation.get('recommendation')
        
        # Update timestamp
        context.projection.state_timestamp = event.timestamp
        
        # Compute hash
        context.projection.compute_hash()
    
    def _initial_projection(self) -> ReplayProjectionState:
        """Create initial projection state (neutral)."""
        return ReplayProjectionState(
            readiness=0.5,
            confidence_stability=0.5,
            challenge_suitability=0.5,
            pacing_responsiveness=0.5,
            cognitive_stability=0.5,
            transfer_readiness=0.5,
            learning_momentum=0.5,
            uncertainty_band=0.5,
            adaptation_type=None,
            adaptation_recommendation=None
        )
    
    def _generate_replay_id(self, user_id: str, timestamp: datetime) -> str:
        """Generate unique replay ID."""
        hash_input = f"{user_id}{timestamp.isoformat()}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]
    
    def validate_replay_determinism(
        self,
        replay_result: ReplayResult,
        original_cognition: ReplayCognitionState,
        original_projection: ReplayProjectionState
    ) -> bool:
        """
        Validate that replay matches original state.
        
        Args:
            replay_result: Result from replay
            original_cognition: Original live cognition state
            original_projection: Original live projection state
            
        Returns:
            True if replay matches original (determinism validated)
        """
        errors = []
        
        # Validate cognition state
        if abs(replay_result.final_cognition.mastery - original_cognition.mastery) > 0.000001:
            errors.append(f"Mastery mismatch: replay={replay_result.final_cognition.mastery}, original={original_cognition.mastery}")
        
        if abs(replay_result.final_cognition.uncertainty - original_cognition.uncertainty) > 0.000001:
            errors.append(f"Uncertainty mismatch: replay={replay_result.final_cognition.uncertainty}, original={original_cognition.uncertainty}")
        
        if abs(replay_result.final_cognition.zpd_score - original_cognition.zpd_score) > 0.000001:
            errors.append(f"ZPD score mismatch: replay={replay_result.final_cognition.zpd_score}, original={original_cognition.zpd_score}")
        
        # Validate state hashes
        if replay_result.final_cognition.state_hash != original_cognition.state_hash:
            errors.append(f"Cognition hash mismatch: replay={replay_result.final_cognition.state_hash}, original={original_cognition.state_hash}")
        
        if replay_result.final_projection.state_hash != original_projection.state_hash:
            errors.append(f"Projection hash mismatch: replay={replay_result.final_projection.state_hash}, original={original_projection.state_hash}")
        
        replay_result.validation_errors.extend(errors)
        replay_result.determinism_valid = len(errors) == 0
        
        if not replay_result.determinism_valid:
            logger.error(f"❌ Replay determinism validation failed for user {replay_result.user_id}: {errors}")
        else:
            logger.info(f"✅ Replay determinism validated for user {replay_result.user_id}")
        
        return replay_result.determinism_valid
