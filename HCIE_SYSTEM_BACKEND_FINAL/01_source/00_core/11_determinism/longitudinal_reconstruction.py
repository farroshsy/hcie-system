"""
C2.3.4 - Longitudinal Reconstruction

Rebuild multi-week learner evolution including:
- Misconception evolution
- Pacing evolution
- Adaptation evolution
- Transfer readiness evolution
- Policy exposure history

Enables cohort science, educational longitudinal analysis, pedagogical memory validation.

Focus on pedagogical semantic trajectories (learning), NOT infrastructure replay.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from enum import Enum
import logging

from core.replay.deterministic_replay_engine import (
    ReplayEvent,
    ReplayEventType,
    ReplayCognitionState,
    ReplayProjectionState,
    ReplayAdaptationState,
    ReplayResult,
    DeterministicReplayEngine
)

logger = logging.getLogger(__name__)


class EvolutionType(Enum):
    """Types of pedagogical evolution to track."""
    MASTERY_EVOLUTION = "mastery_evolution"
    MISCONCEPTION_EVOLUTION = "misconception_evolution"
    PACING_EVOLUTION = "pacing_evolution"
    ADAPTATION_EVOLUTION = "adaptation_evolution"
    TRANSFER_READINESS_EVOLUTION = "transfer_readiness_evolution"
    POLICY_EXPOSURE_EVOLUTION = "policy_exposure_evolution"


@dataclass
class EvolutionPoint:
    """
    Represents a single point in a learner's evolution trajectory.
    
    Captures the state at a specific moment in time.
    """
    timestamp: datetime
    session_id: Optional[str]
    
    # Cognitive state
    mastery: float
    uncertainty: float
    zpd_score: float
    
    # Concept-specific state
    concept_id: Optional[str]
    concept_mastery: float
    
    # Adaptation context
    adaptation_type: Optional[str]
    policy_version: Optional[str]
    
    # Session context
    session_phase: str  # early, middle, late
    tasks_completed: int


@dataclass
class EvolutionTrajectory:
    """
    Represents a learner's evolution over time.
    
    Tracks how pedagogical state changes across sessions and time.
    """
    user_id: str
    start_date: datetime
    end_date: datetime
    
    # Evolution points
    evolution_points: List[EvolutionPoint] = field(default_factory=list)
    
    # Summary statistics
    total_sessions: int = 0
    total_tasks_completed: int = 0
    total_concepts_encountered: int = 0
    
    # Evolution metrics
    mastery_delta: float = 0.0
    uncertainty_delta: float = 0.0
    pacing_stability_score: float = 1.0
    
    # Policy exposure
    policy_exposure_history: Dict[str, int] = field(default_factory=dict)


@dataclass
class LongitudinalReconstructionReport:
    """
    Comprehensive longitudinal reconstruction report.
    
    Summarizes multi-week learner evolution analysis.
    """
    user_id: str
    reconstruction_timestamp: datetime
    
    # Time range
    start_date: datetime
    end_date: datetime
    duration_days: int
    
    # Evolution trajectories
    mastery_trajectory: EvolutionTrajectory = field(default_factory=lambda: EvolutionTrajectory(user_id="", start_date=datetime.min, end_date=datetime.min))
    misconception_trajectory: EvolutionTrajectory = field(default_factory=lambda: EvolutionTrajectory(user_id="", start_date=datetime.min, end_date=datetime.min))
    pacing_trajectory: EvolutionTrajectory = field(default_factory=lambda: EvolutionTrajectory(user_id="", start_date=datetime.min, end_date=datetime.min))
    adaptation_trajectory: EvolutionTrajectory = field(default_factory=lambda: EvolutionTrajectory(user_id="", start_date=datetime.min, end_date=datetime.min))
    
    # Pedagogical memory validation
    adaptation_has_memory: bool = False
    pacing_evolves: bool = False
    pedagogy_develops: bool = False
    
    # Cohort analysis
    cohort_id: Optional[str] = None
    cohort_comparisons: Dict[str, float] = field(default_factory=dict)


class LongitudinalReconstructor:
    """
    Rebuilds multi-week learner evolution from persisted events.
    
    Enables cohort science, educational longitudinal analysis, and
    pedagogical memory validation.
    """
    
    def __init__(self, replay_engine: DeterministicReplayEngine):
        """
        Initialize longitudinal reconstructor.
        
        Args:
            replay_engine: Engine for replaying event streams
        """
        self._replay_engine = replay_engine
    
    def reconstruct_longitudinal_evolution(
        self,
        user_id: str,
        events: List[ReplayEvent],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> LongitudinalReconstructionReport:
        """
        Reconstruct longitudinal learner evolution from event stream.
        
        Args:
            user_id: User ID to reconstruct
            events: Complete event stream across all sessions
            start_date: Optional start date for reconstruction window
            end_date: Optional end date for reconstruction window
            
        Returns:
            LongitudinalReconstructionReport with comprehensive evolution analysis
        """
        logger.info(f"🔄 Reconstructing longitudinal evolution for user {user_id}")
        
        # Filter events by date range if provided
        if start_date or end_date:
            events = self._filter_events_by_date_range(events, start_date, end_date)
        
        # Determine actual date range
        if not events:
            start_date = datetime.utcnow() - timedelta(days=30)
            end_date = datetime.utcnow()
        else:
            timestamps = [e.timestamp for e in events if e.timestamp]
            start_date = min(timestamps) if timestamps else datetime.utcnow() - timedelta(days=30)
            end_date = max(timestamps) if timestamps else datetime.utcnow()
        
        # Build report
        report = LongitudinalReconstructionReport(
            user_id=user_id,
            reconstruction_timestamp=datetime.utcnow(),
            start_date=start_date,
            end_date=end_date,
            duration_days=(end_date - start_date).days
        )
        
        # Extract evolution points from events
        evolution_points = self._extract_evolution_points(events)
        
        # Build evolution trajectories
        report.mastery_trajectory = self._build_mastery_trajectory(user_id, evolution_points, start_date, end_date)
        report.misconception_trajectory = self._build_misconception_trajectory(user_id, evolution_points, start_date, end_date)
        report.pacing_trajectory = self._build_pacing_trajectory(user_id, evolution_points, start_date, end_date)
        report.adaptation_trajectory = self._build_adaptation_trajectory(user_id, evolution_points, start_date, end_date)
        
        # Validate pedagogical memory
        report.adaptation_has_memory = self._validate_adaptation_memory(report.adaptation_trajectory)
        report.pacing_evolves = self._validate_pacing_evolution(report.pacing_trajectory)
        report.pedagogy_develops = self._validate_pedagogy_development(report)
        
        logger.info(f"✅ Longitudinal reconstruction completed for user {user_id}: {report.duration_days} days")
        
        return report
    
    def _filter_events_by_date_range(
        self,
        events: List[ReplayEvent],
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> List[ReplayEvent]:
        """Filter events by date range."""
        filtered = events
        if start_date:
            filtered = [e for e in filtered if e.timestamp and e.timestamp >= start_date]
        if end_date:
            filtered = [e for e in filtered if e.timestamp and e.timestamp <= end_date]
        return filtered
    
    def _extract_evolution_points(self, events: List[ReplayEvent]) -> List[EvolutionPoint]:
        """
        Extract evolution points from event stream.
        
        Args:
            events: Event stream
            
        Returns:
            List of evolution points
        """
        points = []
        
        for event in events:
            if event.event_type == ReplayEventType.TASK_ATTEMPT_SUBMITTED:
                payload = event.payload or {}
                point = EvolutionPoint(
                    timestamp=event.timestamp or datetime.utcnow(),
                    session_id=payload.get("session_id"),
                    mastery=payload.get("mastery", 0.5),
                    uncertainty=payload.get("uncertainty", 0.3),
                    zpd_score=payload.get("zpd_score", 0.4),
                    concept_id=payload.get("concept_id"),
                    concept_mastery=payload.get("concept_mastery", 0.5),
                    adaptation_type=None,  # Will be filled from adaptation events
                    policy_version=event.policy_version,
                    session_phase=self._infer_session_phase(payload.get("tasks_completed", 0)),
                    tasks_completed=payload.get("tasks_completed", 0)
                )
                points.append(point)
            elif event.event_type == ReplayEventType.ADAPTATION_GENERATED:
                payload = event.payload or {}
                # Update latest point with adaptation info
                if points:
                    points[-1].adaptation_type = payload.get("adaptation_type")
                    points[-1].policy_version = event.policy_version
        
        return points
    
    def _infer_session_phase(self, tasks_completed: int) -> str:
        """Infer session phase from tasks completed."""
        if tasks_completed < 3:
            return "early"
        elif tasks_completed < 7:
            return "middle"
        else:
            return "late"
    
    def _build_mastery_trajectory(
        self,
        user_id: str,
        points: List[EvolutionPoint],
        start_date: datetime,
        end_date: datetime
    ) -> EvolutionTrajectory:
        """Build mastery evolution trajectory."""
        trajectory = EvolutionTrajectory(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            evolution_points=points
        )
        
        if not points:
            return trajectory
        
        trajectory.total_tasks_completed = sum(p.tasks_completed for p in points)
        trajectory.total_concepts_encountered = len(set(p.concept_id for p in points if p.concept_id))
        
        if len(points) >= 2:
            trajectory.mastery_delta = points[-1].mastery - points[0].mastery
            trajectory.uncertainty_delta = points[-1].uncertainty - points[0].uncertainty
        
        # Count policy exposure
        for point in points:
            if point.policy_version:
                trajectory.policy_exposure_history[point.policy_version] = trajectory.policy_exposure_history.get(point.policy_version, 0) + 1
        
        return trajectory
    
    def _build_misconception_trajectory(
        self,
        user_id: str,
        points: List[EvolutionPoint],
        start_date: datetime,
        end_date: datetime
    ) -> EvolutionTrajectory:
        """Build misconception evolution trajectory."""
        # Simplified - in production would track actual misconceptions
        trajectory = EvolutionTrajectory(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            evolution_points=points
        )
        
        # Track concept mastery as proxy for misconception evolution
        concept_points = [p for p in points if p.concept_id and p.concept_mastery is not None]
        trajectory.evolution_points = concept_points
        trajectory.total_concepts_encountered = len(set(p.concept_id for p in concept_points))
        
        return trajectory
    
    def _build_pacing_trajectory(
        self,
        user_id: str,
        points: List[EvolutionPoint],
        start_date: datetime,
        end_date: datetime
    ) -> EvolutionTrajectory:
        """Build pacing evolution trajectory."""
        trajectory = EvolutionTrajectory(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            evolution_points=points
        )
        
        # Pacing stability based on task completion consistency
        if len(points) >= 2:
            task_intervals = []
            for i in range(1, len(points)):
                if points[i-1].timestamp and points[i].timestamp:
                    interval = (points[i].timestamp - points[i-1].timestamp).total_seconds()
                    task_intervals.append(interval)
            
            if task_intervals:
                avg_interval = sum(task_intervals) / len(task_intervals)
                variance = sum((x - avg_interval) ** 2 for x in task_intervals) / len(task_intervals)
                trajectory.pacing_stability_score = 1.0 / (1.0 + variance / (avg_interval ** 2 + 1))
        
        return trajectory
    
    def _build_adaptation_trajectory(
        self,
        user_id: str,
        points: List[EvolutionPoint],
        start_date: datetime,
        end_date: datetime
    ) -> EvolutionTrajectory:
        """Build adaptation evolution trajectory."""
        trajectory = EvolutionTrajectory(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            evolution_points=points
        )
        
        # Track adaptation types
        adaptation_points = [p for p in points if p.adaptation_type]
        trajectory.evolution_points = adaptation_points
        
        # Count policy exposure
        for point in adaptation_points:
            if point.policy_version:
                trajectory.policy_exposure_history[point.policy_version] = trajectory.policy_exposure_history.get(point.policy_version, 0) + 1
        
        return trajectory
    
    def _validate_adaptation_memory(self, trajectory: EvolutionTrajectory) -> bool:
        """
        Validate that adaptation has memory across sessions.
        
        Args:
            trajectory: Adaptation trajectory
            
        Returns:
            True if adaptation shows memory, False otherwise
        """
        # Adaptation has memory if:
        # 1. Multiple policy versions encountered (policy evolution)
        # 2. Adaptation types vary based on session phase
        if len(trajectory.policy_exposure_history) > 1:
            return True
        
        points_by_phase = {}
        for point in trajectory.evolution_points:
            phase = point.session_phase
            if phase not in points_by_phase:
                points_by_phase[phase] = []
            points_by_phase[phase].append(point)
        
        # Check if adaptation types differ by phase
        early_adaptations = set(p.adaptation_type for p in points_by_phase.get("early", []) if p.adaptation_type)
        late_adaptations = set(p.adaptation_type for p in points_by_phase.get("late", []) if p.adaptation_type)
        
        if early_adaptations and late_adaptations and early_adaptations != late_adaptations:
            return True
        
        return False
    
    def _validate_pacing_evolution(self, trajectory: EvolutionTrajectory) -> bool:
        """
        Validate that pacing evolves over time.
        
        Args:
            trajectory: Pacing trajectory
            
        Returns:
            True if pacing evolves, False otherwise
        """
        # Pacing evolves if stability score is not perfect
        return trajectory.pacing_stability_score < 0.95
    
    def _validate_pedagogy_development(self, report: LongitudinalReconstructionReport) -> bool:
        """
        Validate that pedagogy develops over time.
        
        Args:
            report: Longitudinal reconstruction report
            
        Returns:
            True if pedagogy develops, False otherwise
        """
        # Pedagogy develops if:
        # 1. Adaptation has memory
        # 2. Pacing evolves
        # 3. Mastery shows positive growth
        has_adaptation_memory = report.adaptation_has_memory
        has_pacing_evolution = report.pacing_evolves
        has_mastery_growth = report.mastery_trajectory.mastery_delta > 0.05
        
        return has_adaptation_memory and (has_pacing_evolution or has_mastery_growth)
