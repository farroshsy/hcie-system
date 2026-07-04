"""
C2.2.2 - Adaptation Effectiveness Analysis

Analysis pipeline to measure adaptation impact on learning outcomes.
Focus on pedagogical semantic trajectories (learning), NOT infrastructure metrics (machines).

Compares:
- Adaptation-triggered vs non-adaptation sessions
- Mastery growth in both groups
- Retention rates
- Concept transfer patterns
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class AdaptationType(Enum):
    """Classification of adaptation types for analysis."""
    REMEDIATION = "remediation"
    PACING_ADJUSTMENT = "pacing_adjustment"
    DIFFICULTY_SHIFT = "difficulty_shift"
    TRANSFER_OPPORTUNITY = "transfer_opportunity"
    PREREQUISITE_REVIEW = "prerequisite_review"
    CONFIDENCE_SUPPORT = "confidence_support"
    MILESTONE_ACKNOWLEDGEMENT = "milestone_acknowledgement"


@dataclass
class SessionMetrics:
    """
    Metrics for a single learning session.
    
    Captures session-level learning outcomes for adaptation effectiveness analysis.
    """
    session_id: str
    user_id: str
    has_adaptations: bool
    adaptation_count: int
    adaptation_types: List[str]
    policy_version: Optional[str]
    experiment_id: Optional[str]
    
    # Learning outcomes
    tasks_completed: int
    tasks_correct: int
    initial_mastery: float
    final_mastery: float
    mastery_growth: float
    session_duration_minutes: float
    
    # Retention metrics
    next_session_mastery: Optional[float] = None
    mastery_retention: Optional[float] = None
    
    # Concept transfer
    concepts_encountered: List[str] = None
    concepts_mastered: List[str] = None


@dataclass
class AdaptationEffectivenessReport:
    """
    Comprehensive report on adaptation effectiveness.
    
    Aggregates session-level metrics into group comparisons and statistical summaries.
    """
    total_sessions: int
    adaptation_sessions: int
    non_adaptation_sessions: int
    
    # Mastery growth comparison
    adaptation_mastery_growth_avg: float
    non_adaptation_mastery_growth_avg: float
    mastery_growth_delta: float
    
    # Retention comparison
    adaptation_retention_avg: float
    non_adaptation_retention_avg: float
    retention_delta: float
    
    # Task performance comparison
    adaptation_accuracy_avg: float
    non_adaptation_accuracy_avg: float
    accuracy_delta: float
    
    # Per-adaptation-type effectiveness
    adaptation_type_effectiveness: Dict[str, Dict[str, float]]
    
    # Statistical significance
    statistical_significance: Optional[Dict[str, float]] = None


@dataclass
class ConceptTransferAnalysis:
    """
    Analysis of concept transfer across sessions.
    
    Measures how adaptations affect knowledge transfer between concepts.
    """
    total_concepts: int
    concepts_with_transfer: int
    transfer_rate: float
    
    adaptation_transfer_rate: float
    non_adaptation_transfer_rate: float
    
    transfer_by_adaptation_type: Dict[str, float]


class AdaptationEffectivenessAnalyzer:
    """
    Analysis pipeline for measuring adaptation impact on learning outcomes.
    
    Focus on pedagogical semantic trajectories:
    - Compare adaptation-triggered vs non-adaptation sessions
    - Measure mastery growth differences
    - Measure retention differences
    - Measure concept transfer differences
    
    NOT infrastructure metrics (machines, latency, throughput).
    """
    
    QUERY_SESSION_ADAPTATION_METRICS = """
    -- Extract session-level metrics with adaptation information
    SELECT 
        ls.session_id,
        ls.user_id,
        ls.started_at,
        ls.completed_at,
        COUNT(DISTINCT ae.event_id) as adaptation_count,
        ARRAY_AGG(DISTINCT ae.adaptation_type) FILTER (WHERE ae.adaptation_type IS NOT NULL) as adaptation_types,
        MAX(ae.policy_version) as policy_version,
        MAX(ae.experiment_id) as experiment_id,
        COUNT(DISTINCT ta.task_id) as tasks_completed,
        COUNT(DISTINCT CASE WHEN ta.is_correct THEN ta.task_id END) as tasks_correct,
        (SELECT lp1.mastery FROM learner_progress lp1 
         WHERE lp1.user_id = ls.user_id 
         AND lp1.timestamp >= ls.started_at 
         ORDER BY lp1.timestamp ASC LIMIT 1) as initial_mastery,
        (SELECT lp2.mastery FROM learner_progress lp2 
         WHERE lp2.user_id = ls.user_id 
         AND lp2.timestamp <= COALESCE(ls.completed_at, NOW()) 
         ORDER BY lp2.timestamp DESC LIMIT 1) as final_mastery,
        EXTRACT(EPOCH FROM (COALESCE(ls.completed_at, NOW()) - ls.started_at)) / 60 as session_duration_minutes
    FROM learning_sessions ls
    LEFT JOIN adaptation_events ae ON ls.session_id = ae.session_id
    LEFT JOIN task_attempts ta ON ls.session_id = ta.session_id
    WHERE ls.user_id = :user_id
    GROUP BY ls.session_id, ls.user_id, ls.started_at, ls.completed_at
    ORDER BY ls.started_at ASC
    """
    
    QUERY_SESSION_RETENTION = """
    -- Extract retention metrics (mastery in next session)
    SELECT 
        ls1.session_id as current_session_id,
        ls1.user_id,
        (SELECT lp.mastery FROM learner_progress lp 
         WHERE lp.user_id = ls1.user_id 
         AND lp.timestamp >= ls2.started_at 
         ORDER BY lp.timestamp ASC LIMIT 1) as next_session_mastery
    FROM learning_sessions ls1
    LEFT JOIN learning_sessions ls2 ON ls1.user_id = ls2.user_id 
        AND ls2.started_at > ls1.completed_at
        AND ls2.started_at = (
            SELECT MIN(ls3.started_at) 
            FROM learning_sessions ls3 
            WHERE ls3.user_id = ls1.user_id 
            AND ls3.started_at > ls1.completed_at
        )
    WHERE ls1.user_id = :user_id
    """
    
    QUERY_CONCEPT_TRANSFER = """
    -- Extract concept transfer patterns
    SELECT 
        ls.session_id,
        ls.user_id,
        ARRAY_AGG(DISTINCT ta.concept_id) as concepts_encountered,
        COUNT(DISTINCT CASE WHEN lp.mastery > 0.8 THEN lp.concept_id END) as concepts_mastered
    FROM learning_sessions ls
    LEFT JOIN task_attempts ta ON ls.session_id = ta.session_id
    LEFT JOIN learner_progress lp ON ls.user_id = lp.user_id 
        AND lp.timestamp >= ls.started_at 
        AND lp.timestamp <= COALESCE(ls.completed_at, NOW())
    WHERE ls.user_id = :user_id
    GROUP BY ls.session_id, ls.user_id
    ORDER BY ls.started_at ASC
    """
    
    QUERY_GROUP_ADAPTATION_EFFECTIVENESS = """
    -- Aggregate adaptation effectiveness across all users
    SELECT 
        ls.user_id,
        COUNT(DISTINCT ae.event_id) > 0 as has_adaptations,
        COUNT(DISTINCT ae.event_id) as adaptation_count,
        MAX(ae.adaptation_type) as adaptation_type,
        COUNT(DISTINCT ta.task_id) as tasks_completed,
        COUNT(DISTINCT CASE WHEN ta.is_correct THEN ta.task_id END) as tasks_correct,
        AVG(
            (SELECT lp_final.mastery FROM learner_progress lp_final 
             WHERE lp_final.user_id = ls.user_id 
             AND lp_final.timestamp <= COALESCE(ls.completed_at, NOW()) 
             ORDER BY lp_final.timestamp DESC LIMIT 1) -
            (SELECT lp_initial.mastery FROM learner_progress lp_initial 
             WHERE lp_initial.user_id = ls.user_id 
             AND lp_initial.timestamp >= ls.started_at 
             ORDER BY lp_initial.timestamp ASC LIMIT 1)
        ) as avg_mastery_growth
    FROM learning_sessions ls
    LEFT JOIN adaptation_events ae ON ls.session_id = ae.session_id
    LEFT JOIN task_attempts ta ON ls.session_id = ta.session_id
    WHERE ls.started_at >= :start_date
    GROUP BY ls.user_id, ae.adaptation_type
    """
    
    def __init__(self, db_store=None):
        """
        Initialize adaptation effectiveness analyzer.
        
        Args:
            db_store: Database connection for executing queries
        """
        self._db_store = db_store
    
    def analyze_adaptation_effectiveness(
        self, 
        user_id: Optional[str] = None,
        start_date: Optional[datetime] = None
    ) -> AdaptationEffectivenessReport:
        """
        Analyze adaptation effectiveness for a user or across all users.
        
        Compares learning outcomes between adaptation-triggered and non-adaptation sessions.
        
        Args:
            user_id: User ID to analyze (None for all users)
            start_date: Start date for analysis window (None for all time)
            
        Returns:
            AdaptationEffectivenessReport with comprehensive effectiveness metrics
        """
        logger.info(f"🔍 Analyzing adaptation effectiveness for user {user_id}")
        
        # Extract session metrics
        if user_id:
            session_metrics = self._extract_session_metrics(user_id)
        else:
            session_metrics = self._extract_group_session_metrics(start_date)
        
        if not session_metrics:
            logger.warning("No session metrics found for analysis")
            return self._empty_report()
        
        # Split into adaptation and non-adaptation groups
        adaptation_sessions = [s for s in session_metrics if s.has_adaptations]
        non_adaptation_sessions = [s for s in session_metrics if not s.has_adaptations]
        
        # Calculate mastery growth comparison
        adaptation_mastery_growth = self._calculate_average_mastery_growth(adaptation_sessions)
        non_adaptation_mastery_growth = self._calculate_average_mastery_growth(non_adaptation_sessions)
        mastery_growth_delta = adaptation_mastery_growth - non_adaptation_mastery_growth
        
        # Calculate retention comparison
        adaptation_retention = self._calculate_average_retention(adaptation_sessions)
        non_adaptation_retention = self._calculate_average_retention(non_adaptation_sessions)
        retention_delta = adaptation_retention - non_adaptation_retention
        
        # Calculate accuracy comparison
        adaptation_accuracy = self._calculate_average_accuracy(adaptation_sessions)
        non_adaptation_accuracy = self._calculate_average_accuracy(non_adaptation_sessions)
        accuracy_delta = adaptation_accuracy - non_adaptation_accuracy
        
        # Calculate per-adaptation-type effectiveness
        adaptation_type_effectiveness = self._calculate_per_adaptation_type_effectiveness(adaptation_sessions)
        
        return AdaptationEffectivenessReport(
            total_sessions=len(session_metrics),
            adaptation_sessions=len(adaptation_sessions),
            non_adaptation_sessions=len(non_adaptation_sessions),
            adaptation_mastery_growth_avg=adaptation_mastery_growth,
            non_adaptation_mastery_growth_avg=non_adaptation_mastery_growth,
            mastery_growth_delta=mastery_growth_delta,
            adaptation_retention_avg=adaptation_retention,
            non_adaptation_retention_avg=non_adaptation_retention,
            retention_delta=retention_delta,
            adaptation_accuracy_avg=adaptation_accuracy,
            non_adaptation_accuracy_avg=non_adaptation_accuracy,
            accuracy_delta=accuracy_delta,
            adaptation_type_effectiveness=adaptation_type_effectiveness
        )
    
    def analyze_concept_transfer(
        self,
        user_id: Optional[str] = None
    ) -> ConceptTransferAnalysis:
        """
        Analyze concept transfer patterns.
        
        Measures how adaptations affect knowledge transfer between concepts.
        
        Args:
            user_id: User ID to analyze (None for all users)
            
        Returns:
            ConceptTransferAnalysis with transfer metrics
        """
        logger.info(f"🔍 Analyzing concept transfer for user {user_id}")
        
        if not self._db_store:
            logger.warning("No database store available for concept transfer analysis")
            return ConceptTransferAnalysis(
                total_concepts=0,
                concepts_with_transfer=0,
                transfer_rate=0.0,
                adaptation_transfer_rate=0.0,
                non_adaptation_transfer_rate=0.0,
                transfer_by_adaptation_type={}
            )
        
        try:
            results = self._db_store.fetch_all(
                self.QUERY_CONCEPT_TRANSFER,
                {"user_id": user_id} if user_id else {}
            )
            
            if not results:
                return ConceptTransferAnalysis(
                    total_concepts=0,
                    concepts_with_transfer=0,
                    transfer_rate=0.0,
                    adaptation_transfer_rate=0.0,
                    non_adaptation_transfer_rate=0.0,
                    transfer_by_adaptation_type={}
                )
            
            # Calculate transfer metrics
            total_concepts = sum(len(r.get("concepts_encountered", [])) for r in results)
            concepts_mastered = sum(r.get("concepts_mastered", 0) for r in results)
            transfer_rate = concepts_mastered / total_concepts if total_concepts > 0 else 0.0
            
            return ConceptTransferAnalysis(
                total_concepts=total_concepts,
                concepts_with_transfer=concepts_mastered,
                transfer_rate=transfer_rate,
                adaptation_transfer_rate=0.0,  # To be calculated with adaptation data
                non_adaptation_transfer_rate=0.0,  # To be calculated with adaptation data
                transfer_by_adaptation_type={}
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze concept transfer: {e}")
            return ConceptTransferAnalysis(
                total_concepts=0,
                concepts_with_transfer=0,
                transfer_rate=0.0,
                adaptation_transfer_rate=0.0,
                non_adaptation_transfer_rate=0.0,
                transfer_by_adaptation_type={}
            )
    
    def _extract_session_metrics(self, user_id: str) -> List[SessionMetrics]:
        """Extract session-level metrics for a user."""
        if not self._db_store:
            logger.warning("No database store available for session metrics")
            return []
        
        try:
            results = self._db_store.fetch_all(
                self.QUERY_SESSION_ADAPTATION_METRICS,
                {"user_id": user_id}
            )
            
            # Extract retention metrics
            retention_results = self._db_store.fetch_all(
                self.QUERY_SESSION_RETENTION,
                {"user_id": user_id}
            )
            retention_map = {
                r["current_session_id"]: r["next_session_mastery"]
                for r in retention_results
            }
            
            session_metrics = []
            for row in results:
                session_id = row["session_id"]
                initial_mastery = row.get("initial_mastery", 0.0) or 0.0
                final_mastery = row.get("final_mastery", 0.0) or 0.0
                mastery_growth = final_mastery - initial_mastery
                
                next_session_mastery = retention_map.get(session_id)
                mastery_retention = None
                if next_session_mastery is not None and final_mastery > 0:
                    mastery_retention = next_session_mastery / final_mastery
                
                has_adaptations = row["adaptation_count"] > 0
                adaptation_types = row.get("adaptation_types", []) or []
                
                session_metrics.append(SessionMetrics(
                    session_id=session_id,
                    user_id=row["user_id"],
                    has_adaptations=has_adaptations,
                    adaptation_count=row["adaptation_count"],
                    adaptation_types=adaptation_types,
                    policy_version=row.get("policy_version"),
                    experiment_id=row.get("experiment_id"),
                    tasks_completed=row["tasks_completed"],
                    tasks_correct=row["tasks_correct"],
                    initial_mastery=initial_mastery,
                    final_mastery=final_mastery,
                    mastery_growth=mastery_growth,
                    session_duration_minutes=row["session_duration_minutes"],
                    next_session_mastery=next_session_mastery,
                    mastery_retention=mastery_retention
                ))
            
            logger.debug(f"Extracted {len(session_metrics)} session metrics for user {user_id}")
            return session_metrics
            
        except Exception as e:
            logger.error(f"Failed to extract session metrics for user {user_id}: {e}")
            return []
    
    def _extract_group_session_metrics(self, start_date: Optional[datetime]) -> List[SessionMetrics]:
        """Extract group-level session metrics across all users."""
        if not self._db_store:
            logger.warning("No database store available for group session metrics")
            return []
        
        try:
            results = self._db_store.fetch_all(
                self.QUERY_GROUP_ADAPTATION_EFFECTIVENESS,
                {"start_date": start_date or datetime.now() - timedelta(days=30)}
            )
            
            session_metrics = []
            for row in results:
                has_adaptations = row["has_adaptations"]
                adaptation_type = row.get("adaptation_type")
                
                session_metrics.append(SessionMetrics(
                    session_id="",  # Group analysis doesn't have session IDs
                    user_id=row["user_id"],
                    has_adaptations=has_adaptations,
                    adaptation_count=row["adaptation_count"],
                    adaptation_types=[adaptation_type] if adaptation_type else [],
                    policy_version=None,
                    experiment_id=None,
                    tasks_completed=row["tasks_completed"],
                    tasks_correct=row["tasks_correct"],
                    initial_mastery=0.0,  # Not available in group query
                    final_mastery=0.0,  # Not available in group query
                    mastery_growth=row.get("avg_mastery_growth", 0.0) or 0.0,
                    session_duration_minutes=0.0,  # Not available in group query
                    next_session_mastery=None,
                    mastery_retention=None
                ))
            
            logger.debug(f"Extracted {len(session_metrics)} group session metrics")
            return session_metrics
            
        except Exception as e:
            logger.error(f"Failed to extract group session metrics: {e}")
            return []
    
    def _calculate_average_mastery_growth(self, sessions: List[SessionMetrics]) -> float:
        """Calculate average mastery growth for a group of sessions."""
        if not sessions:
            return 0.0
        return sum(s.mastery_growth for s in sessions) / len(sessions)
    
    def _calculate_average_retention(self, sessions: List[SessionMetrics]) -> float:
        """Calculate average retention for a group of sessions."""
        valid_retentions = [s.mastery_retention for s in sessions if s.mastery_retention is not None]
        if not valid_retentions:
            return 0.0
        return sum(valid_retentions) / len(valid_retentions)
    
    def _calculate_average_accuracy(self, sessions: List[SessionMetrics]) -> float:
        """Calculate average accuracy for a group of sessions."""
        if not sessions:
            return 0.0
        valid_accuracies = []
        for s in sessions:
            if s.tasks_completed > 0:
                accuracy = s.tasks_correct / s.tasks_completed
                valid_accuracies.append(accuracy)
        if not valid_accuracies:
            return 0.0
        return sum(valid_accuracies) / len(valid_accuracies)
    
    def _calculate_per_adaptation_type_effectiveness(
        self, 
        sessions: List[SessionMetrics]
    ) -> Dict[str, Dict[str, float]]:
        """Calculate effectiveness metrics per adaptation type."""
        adaptation_type_metrics = {}
        
        for session in sessions:
            for adaptation_type in session.adaptation_types:
                if adaptation_type not in adaptation_type_metrics:
                    adaptation_type_metrics[adaptation_type] = {
                        "mastery_growth": [],
                        "retention": [],
                        "accuracy": []
                    }
                
                adaptation_type_metrics[adaptation_type]["mastery_growth"].append(session.mastery_growth)
                if session.mastery_retention is not None:
                    adaptation_type_metrics[adaptation_type]["retention"].append(session.mastery_retention)
                if session.tasks_completed > 0:
                    accuracy = session.tasks_correct / session.tasks_completed
                    adaptation_type_metrics[adaptation_type]["accuracy"].append(accuracy)
        
        # Calculate averages per adaptation type
        effectiveness = {}
        for adaptation_type, metrics in adaptation_type_metrics.items():
            effectiveness[adaptation_type] = {
                "avg_mastery_growth": sum(metrics["mastery_growth"]) / len(metrics["mastery_growth"]) if metrics["mastery_growth"] else 0.0,
                "avg_retention": sum(metrics["retention"]) / len(metrics["retention"]) if metrics["retention"] else 0.0,
                "avg_accuracy": sum(metrics["accuracy"]) / len(metrics["accuracy"]) if metrics["accuracy"] else 0.0
            }
        
        return effectiveness
    
    def _empty_report(self) -> AdaptationEffectivenessReport:
        """Return an empty report when no data is available."""
        return AdaptationEffectivenessReport(
            total_sessions=0,
            adaptation_sessions=0,
            non_adaptation_sessions=0,
            adaptation_mastery_growth_avg=0.0,
            non_adaptation_mastery_growth_avg=0.0,
            mastery_growth_delta=0.0,
            adaptation_retention_avg=0.0,
            non_adaptation_retention_avg=0.0,
            retention_delta=0.0,
            adaptation_accuracy_avg=0.0,
            non_adaptation_accuracy_avg=0.0,
            accuracy_delta=0.0,
            adaptation_type_effectiveness={}
        )
