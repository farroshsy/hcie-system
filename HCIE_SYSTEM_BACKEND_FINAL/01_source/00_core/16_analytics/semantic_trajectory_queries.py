"""
C2.2 - Research Analytics Layer

Semantic trajectory queries for extracting learner learning trajectories from persisted events.
Focus on pedagogical semantic trajectories (learning), NOT infrastructure metrics (machines).

This is separate from backend observability (Grafana) - focuses on educational science research.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class TrajectoryPoint:
    """
    A single point in a learner's semantic trajectory.
    
    Represents the learner's state at a specific moment in time,
    capturing mastery, concept, and pedagogical context.
    """
    timestamp: datetime
    user_id: str
    concept_id: str
    mastery: float
    uncertainty: float
    zpd_score: float
    session_id: Optional[str] = None
    task_id: Optional[str] = None
    adaptation_type: Optional[str] = None
    policy_version: Optional[str] = None
    experiment_id: Optional[str] = None


@dataclass
class ConceptProgression:
    """
    Tracks a learner's progression through a specific concept.
    
    Analyzes mastery evolution, pacing, and intervention patterns
    for a single concept across sessions.
    """
    concept_id: str
    user_id: str
    first_encounter: datetime
    last_encounter: datetime
    initial_mastery: float
    final_mastery: float
    mastery_growth: float
    total_attempts: int
    successful_attempts: int
    adaptations_received: int
    misconception_count: int
    pacing_changes: int


@dataclass
class LearnerTrajectory:
    """
    Complete semantic trajectory for a learner across all concepts and sessions.
    
    Aggregates concept progressions, pacing patterns, and adaptation effectiveness
    into a holistic view of the learner's learning journey.
    """
    user_id: str
    trajectory_points: List[TrajectoryPoint]
    concept_progressions: Dict[str, ConceptProgression]
    total_sessions: int
    total_attempts: int
    total_adaptations: int
    overall_mastery_growth: float
    pacing_stability_score: float
    adaptation_effectiveness_score: float


class SemanticTrajectoryQueries:
    """
    SQL queries and analysis functions for extracting semantic trajectories.
    
    Focus on pedagogical semantic trajectories:
    - Mastery evolution over time
    - Concept progression patterns
    - Pacing stability
    - Misconception recurrence
    - Adaptation effectiveness
    
    NOT infrastructure metrics (machines, latency, throughput).
    """
    
    # SQL Queries for trajectory extraction
    
    QUERY_LEARNER_MASTERY_EVOLUTION = """
    -- Extract mastery evolution for a learner over time
    SELECT 
        lp.timestamp,
        lp.user_id,
        lp.concept_id,
        lp.mastery,
        lp.uncertainty,
        lp.zpd_score,
        ls.session_id,
        ta.task_id,
        ae.adaptation_type,
        ae.policy_version,
        ae.experiment_id
    FROM learner_progress lp
    LEFT JOIN learning_sessions ls ON lp.user_id = ls.user_id 
        AND lp.timestamp BETWEEN ls.started_at AND COALESCE(ls.completed_at, ls.paused_at, NOW())
    LEFT JOIN task_attempts ta ON lp.user_id = ta.user_id 
        AND ABS(EXTRACT(EPOCH FROM (lp.timestamp - ta.submitted_at))) < 60
    LEFT JOIN adaptation_events ae ON lp.user_id = ae.user_id 
        AND ABS(EXTRACT(EPOCH FROM (lp.timestamp - ae.created_at))) < 60
    WHERE lp.user_id = :user_id
    ORDER BY lp.timestamp ASC
    """
    
    QUERY_CONCEPT_PROGRESSION = """
    -- Extract concept-specific progression for a learner
    SELECT 
        lp.concept_id,
        lp.user_id,
        MIN(lp.timestamp) as first_encounter,
        MAX(lp.timestamp) as last_encounter,
        (SELECT mastery FROM learner_progress lp2 
         WHERE lp2.user_id = lp.user_id AND lp2.concept_id = lp.concept_id 
         ORDER BY lp2.timestamp ASC LIMIT 1) as initial_mastery,
        (SELECT mastery FROM learner_progress lp3 
         WHERE lp3.user_id = lp.user_id AND lp3.concept_id = lp.concept_id 
         ORDER BY lp3.timestamp DESC LIMIT 1) as final_mastery,
        COUNT(DISTINCT ta.task_id) as total_attempts,
        COUNT(DISTINCT CASE WHEN ta.is_correct THEN ta.task_id END) as successful_attempts,
        COUNT(DISTINCT ae.event_id) as adaptations_received,
        COUNT(DISTINCT CASE WHEN ta.misconception_id IS NOT NULL THEN ta.task_id END) as misconception_count
    FROM learner_progress lp
    LEFT JOIN task_attempts ta ON lp.user_id = ta.user_id AND lp.concept_id = ta.concept_id
    LEFT JOIN adaptation_events ae ON lp.user_id = ae.user_id AND lp.concept_id = ae.concept_id
    WHERE lp.user_id = :user_id
    GROUP BY lp.concept_id, lp.user_id
    ORDER BY lp.concept_id
    """
    
    QUERY_PACING_PATTERNS = """
    -- Extract pacing patterns for a learner across sessions
    SELECT 
        ls.session_id,
        ls.user_id,
        ls.started_at,
        ls.completed_at,
        COUNT(ta.task_id) as tasks_completed,
        EXTRACT(EPOCH FROM (COALESCE(ls.completed_at, NOW()) - ls.started_at)) / 60 as session_duration_minutes,
        COUNT(ta.task_id)::float / 
            NULLIF(EXTRACT(EPOCH FROM (COALESCE(ls.completed_at, NOW()) - ls.started_at)) / 60, 0) as tasks_per_minute,
        COUNT(ae.event_id) as adaptations_in_session
    FROM learning_sessions ls
    LEFT JOIN task_attempts ta ON ls.session_id = ta.session_id
    LEFT JOIN adaptation_events ae ON ls.session_id = ae.session_id
    WHERE ls.user_id = :user_id
    GROUP BY ls.session_id, ls.user_id, ls.started_at, ls.completed_at
    ORDER BY ls.started_at ASC
    """
    
    QUERY_MISCONCEPTION_RECURRENCE = """
    -- Extract misconception recurrence patterns for a learner
    SELECT 
        ta.misconception_id,
        ta.user_id,
        COUNT(ta.task_id) as occurrence_count,
        MIN(ta.submitted_at) as first_occurrence,
        MAX(ta.submitted_at) as last_occurrence,
        COUNT(DISTINCT ls.session_id) as sessions_affected,
        AVG(ta.is_correct::int) as accuracy_after_misconception
    FROM task_attempts ta
    LEFT JOIN learning_sessions ls ON ta.session_id = ls.session_id
    WHERE ta.user_id = :user_id
        AND ta.misconception_id IS NOT NULL
    GROUP BY ta.misconception_id, ta.user_id
    ORDER BY occurrence_count DESC
    """
    
    QUERY_ADAPTATION_EFFECTIVENESS = """
    -- Extract adaptation effectiveness for a learner
    SELECT 
        ae.adaptation_type,
        ae.policy_version,
        ae.experiment_id,
        ae.user_id,
        COUNT(ae.event_id) as adaptation_count,
        AVG(
            CASE 
                WHEN ta.is_correct THEN 1.0 
                ELSE 0.0 
            END
        ) as post_adaptation_accuracy,
        AVG(lp.mastery) as average_mastery_after,
        AVG(lp.uncertainty) as average_uncertainty_after
    FROM adaptation_events ae
    LEFT JOIN task_attempts ta ON ae.user_id = ta.user_id 
        AND ae.session_id = ta.session_id
        AND ta.submitted_at > ae.created_at
        AND ta.submitted_at < (ae.created_at + INTERVAL '10 minutes')
    LEFT JOIN learner_progress lp ON ae.user_id = lp.user_id 
        AND lp.timestamp > ae.created_at
        AND lp.timestamp < (ae.created_at + INTERVAL '10 minutes')
    WHERE ae.user_id = :user_id
    GROUP BY ae.adaptation_type, ae.policy_version, ae.experiment_id, ae.user_id
    ORDER BY adaptation_count DESC
    """
    
    def __init__(self, db_store=None):
        """
        Initialize semantic trajectory queries.
        
        Args:
            db_store: Database connection for executing queries
        """
        self._db_store = db_store
    
    def extract_learner_trajectory(self, user_id: str) -> LearnerTrajectory:
        """
        Extract complete semantic trajectory for a learner.
        
        Aggregates mastery evolution, concept progression, pacing patterns,
        and adaptation effectiveness into a holistic view.
        
        Args:
            user_id: User ID to extract trajectory for
            
        Returns:
            LearnerTrajectory with complete semantic journey
        """
        logger.info(f"🔍 Extracting semantic trajectory for user {user_id}")
        
        # Extract trajectory points (mastery evolution over time)
        trajectory_points = self._extract_mastery_evolution(user_id)
        
        # Extract concept progressions
        concept_progressions = self._extract_concept_progressions(user_id)
        
        # Calculate aggregate metrics
        total_sessions = len(set(tp.session_id for tp in trajectory_points if tp.session_id))
        total_attempts = len(set(tp.task_id for tp in trajectory_points if tp.task_id))
        total_adaptations = len(set(tp.adaptation_type for tp in trajectory_points if tp.adaptation_type))
        
        # Calculate overall mastery growth
        if trajectory_points:
            initial_mastery = trajectory_points[0].mastery
            final_mastery = trajectory_points[-1].mastery
            overall_mastery_growth = final_mastery - initial_mastery
        else:
            overall_mastery_growth = 0.0
        
        # Calculate pacing stability (lower is more stable)
        pacing_stability_score = self._calculate_pacing_stability(user_id)
        
        # Calculate adaptation effectiveness
        adaptation_effectiveness_score = self._calculate_adaptation_effectiveness(user_id)
        
        return LearnerTrajectory(
            user_id=user_id,
            trajectory_points=trajectory_points,
            concept_progressions=concept_progressions,
            total_sessions=total_sessions,
            total_attempts=total_attempts,
            total_adaptations=total_adaptations,
            overall_mastery_growth=overall_mastery_growth,
            pacing_stability_score=pacing_stability_score,
            adaptation_effectiveness_score=adaptation_effectiveness_score
        )
    
    def _extract_mastery_evolution(self, user_id: str) -> List[TrajectoryPoint]:
        """Extract mastery evolution over time for a learner."""
        if not self._db_store:
            logger.warning("No database store available for mastery evolution query")
            return []
        
        try:
            results = self._db_store.fetch_all(
                self.QUERY_LEARNER_MASTERY_EVOLUTION,
                {"user_id": user_id}
            )
            
            trajectory_points = []
            for row in results:
                trajectory_points.append(TrajectoryPoint(
                    timestamp=row["timestamp"],
                    user_id=row["user_id"],
                    concept_id=row["concept_id"],
                    mastery=row["mastery"],
                    uncertainty=row["uncertainty"],
                    zpd_score=row["zpd_score"],
                    session_id=row.get("session_id"),
                    task_id=row.get("task_id"),
                    adaptation_type=row.get("adaptation_type"),
                    policy_version=row.get("policy_version"),
                    experiment_id=row.get("experiment_id")
                ))
            
            logger.debug(f"Extracted {len(trajectory_points)} trajectory points for user {user_id}")
            return trajectory_points
            
        except Exception as e:
            logger.error(f"Failed to extract mastery evolution for user {user_id}: {e}")
            return []
    
    def _extract_concept_progressions(self, user_id: str) -> Dict[str, ConceptProgression]:
        """Extract concept-specific progressions for a learner."""
        if not self._db_store:
            logger.warning("No database store available for concept progression query")
            return {}
        
        try:
            results = self._db_store.fetch_all(
                self.QUERY_CONCEPT_PROGRESSION,
                {"user_id": user_id}
            )
            
            concept_progressions = {}
            for row in results:
                concept_id = row["concept_id"]
                initial_mastery = row.get("initial_mastery", 0.0)
                final_mastery = row.get("final_mastery", 0.0)
                mastery_growth = final_mastery - initial_mastery
                
                concept_progressions[concept_id] = ConceptProgression(
                    concept_id=concept_id,
                    user_id=row["user_id"],
                    first_encounter=row["first_encounter"],
                    last_encounter=row["last_encounter"],
                    initial_mastery=initial_mastery,
                    final_mastery=final_mastery,
                    mastery_growth=mastery_growth,
                    total_attempts=row["total_attempts"],
                    successful_attempts=row["successful_attempts"],
                    adaptations_received=row["adaptations_received"],
                    misconception_count=row["misconception_count"],
                    pacing_changes=0  # To be calculated separately
                )
            
            logger.debug(f"Extracted {len(concept_progressions)} concept progressions for user {user_id}")
            return concept_progressions
            
        except Exception as e:
            logger.error(f"Failed to extract concept progressions for user {user_id}: {e}")
            return {}
    
    def _calculate_pacing_stability(self, user_id: str) -> float:
        """
        Calculate pacing stability score for a learner.
        
        Lower score = more stable pacing (less variation in task completion rate).
        Higher score = unstable pacing (large variation in task completion rate).
        
        Args:
            user_id: User ID to calculate pacing stability for
            
        Returns:
            Pacing stability score (0-1, where 0 is most stable)
        """
        if not self._db_store:
            return 0.5  # Neutral score if no data
        
        try:
            results = self._db_store.fetch_all(
                self.QUERY_PACING_PATTERNS,
                {"user_id": user_id}
            )
            
            if len(results) < 2:
                return 0.5  # Not enough data to calculate stability
            
            # Calculate coefficient of variation for tasks_per_minute
            tasks_per_minute = [row["tasks_per_minute"] for row in results if row["tasks_per_minute"]]
            
            if not tasks_per_minute:
                return 0.5
            
            import statistics
            mean = statistics.mean(tasks_per_minute)
            if mean == 0:
                return 0.5
            
            stdev = statistics.stdev(tasks_per_minute) if len(tasks_per_minute) > 1 else 0
            cv = (stdev / mean) if mean > 0 else 0
            
            # Normalize to 0-1 range (typical CV range for pacing is 0-2)
            stability_score = min(cv / 2.0, 1.0)
            
            logger.debug(f"Pacing stability score for user {user_id}: {stability_score:.3f}")
            return stability_score
            
        except Exception as e:
            logger.error(f"Failed to calculate pacing stability for user {user_id}: {e}")
            return 0.5
    
    def _calculate_adaptation_effectiveness(self, user_id: str) -> float:
        """
        Calculate adaptation effectiveness score for a learner.
        
        Higher score = adaptations are effective (improve accuracy/mastery).
        Lower score = adaptations are ineffective (no improvement).
        
        Args:
            user_id: User ID to calculate adaptation effectiveness for
            
        Returns:
            Adaptation effectiveness score (0-1, where 1 is most effective)
        """
        if not self._db_store:
            return 0.5  # Neutral score if no data
        
        try:
            results = self._db_store.fetch_all(
                self.QUERY_ADAPTATION_EFFECTIVENESS,
                {"user_id": user_id}
            )
            
            if not results:
                return 0.5
            
            # Calculate average post-adaptation accuracy and mastery growth
            accuracies = [row["post_adaptation_accuracy"] for row in results if row["post_adaptation_accuracy"] is not None]
            mastery_after = [row["average_mastery_after"] for row in results if row["average_mastery_after"] is not None]
            
            if not accuracies:
                return 0.5
            
            avg_accuracy = sum(accuracies) / len(accuracies)
            avg_mastery = sum(mastery_after) / len(mastery_after) if mastery_after else 0.5
            
            # Effectiveness is combination of accuracy and mastery
            effectiveness_score = (avg_accuracy + avg_mastery) / 2.0
            
            logger.debug(f"Adaptation effectiveness score for user {user_id}: {effectiveness_score:.3f}")
            return effectiveness_score
            
        except Exception as e:
            logger.error(f"Failed to calculate adaptation effectiveness for user {user_id}: {e}")
            return 0.5
    
    def extract_misconception_recurrence(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Extract misconception recurrence patterns for a learner.
        
        Identifies recurring misconceptions, their frequency, and impact on accuracy.
        
        Args:
            user_id: User ID to extract misconception recurrence for
            
        Returns:
            List of misconception recurrence patterns
        """
        if not self._db_store:
            logger.warning("No database store available for misconception recurrence query")
            return []
        
        try:
            results = self._db_store.fetch_all(
                self.QUERY_MISCONCEPTION_RECURRENCE,
                {"user_id": user_id}
            )
            
            recurrence_patterns = []
            for row in results:
                recurrence_patterns.append({
                    "misconception_id": row["misconception_id"],
                    "occurrence_count": row["occurrence_count"],
                    "first_occurrence": row["first_occurrence"],
                    "last_occurrence": row["last_occurrence"],
                    "sessions_affected": row["sessions_affected"],
                    "accuracy_after": row["accuracy_after_misconception"]
                })
            
            logger.debug(f"Extracted {len(recurrence_patterns)} misconception patterns for user {user_id}")
            return recurrence_patterns
            
        except Exception as e:
            logger.error(f"Failed to extract misconception recurrence for user {user_id}: {e}")
            return []
