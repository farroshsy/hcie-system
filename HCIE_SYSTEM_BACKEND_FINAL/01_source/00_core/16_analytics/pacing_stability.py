"""
C2.2.4 - Pacing Stability Analysis

Analysis to measure pacing stability across sessions, identify pacing oscillation,
and measure pacing adaptation effectiveness on learner engagement.

Focus on pedagogical semantic trajectories (learning), NOT infrastructure metrics (machines).
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import logging
import statistics

logger = logging.getLogger(__name__)


class PacingStabilityLevel(Enum):
    """Classification of pacing stability."""
    STABLE = "stable"
    MODERATELY_STABLE = "moderately_stable"
    UNSTABLE = "unstable"
    HIGHLY_UNSTABLE = "highly_unstable"


@dataclass
class SessionPacingMetrics:
    """
    Pacing metrics for a single session.
    
    Tracks task completion rate, time between tasks, and adaptation pacing signals.
    """
    session_id: str
    user_id: str
    started_at: datetime
    completed_at: Optional[datetime]
    tasks_completed: int
    total_session_duration_minutes: float
    
    # Pacing metrics
    average_task_duration_minutes: float
    task_duration_std_dev: float
    min_task_duration_minutes: float
    max_task_duration_minutes: float
    
    # Adaptation pacing signals
    pacing_adaptation_count: int
    pacing_adjustment_type: Optional[str]
    
    # Engagement metrics
    engagement_score: float  # 0-1, higher = more engaged
    completion_rate: float  # tasks_completed / expected_tasks


@dataclass
class PacingOscillationPattern:
    """
    Pattern analysis for pacing oscillation.
    
    Detects patterns of speed-up/slow-down cycles in learner behavior.
    """
    user_id: str
    oscillation_count: int
    oscillation_amplitude_avg: float
    oscillation_frequency_per_hour: float
    
    # Oscillation classification
    is_oscillating: bool
    oscillation_severity: PacingStabilityLevel
    
    # Context
    total_sessions_analyzed: int
    sessions_with_oscillation: int


@dataclass
class PacingStabilityReport:
    """
    Comprehensive report on pacing stability and adaptation effectiveness.
    
    Aggregates session pacing metrics into actionable insights.
    """
    total_sessions: int
    stable_sessions: int
    unstable_sessions: int
    average_pacing_stability_score: float  # 0-1, higher = more stable
    
    # Oscillation analysis
    oscillating_users: int
    average_oscillation_severity: float
    
    # Pacing adaptation effectiveness
    sessions_with_pacing_adaptations: int
    pacing_adaptation_effectiveness: float  # 0-1, higher = more effective
    
    # Engagement correlation
    pacing_engagement_correlation: float  # correlation between pacing stability and engagement
    pacing_completion_correlation: float  # correlation between pacing stability and completion


class PacingStabilityAnalyzer:
    """
    Analyzer for pacing stability and adaptation effectiveness.
    
    Focus on pedagogical semantic trajectories:
    - Measure pacing stability across sessions
    - Identify pacing oscillation patterns
    - Measure pacing adaptation effectiveness on learner engagement
    
    NOT infrastructure metrics (machines, latency, throughput).
    """
    
    QUERY_SESSION_PACING_METRICS = """
    -- Extract pacing metrics for a user's sessions
    SELECT 
        ls.session_id,
        ls.user_id,
        ls.started_at,
        ls.completed_at,
        ls.tasks_completed,
        EXTRACT(EPOCH FROM (COALESCE(ls.completed_at, NOW()) - ls.started_at)) / 60 as total_duration_minutes,
        AVG(EXTRACT(EPOCH FROM (ta.submitted_at - ta.session_task_order::float * 60)) / 60) as avg_task_duration,
        STDDEV(EXTRACT(EPOCH FROM (ta.submitted_at - ta.session_task_order::float * 60)) / 60) as task_duration_stddev,
        MIN(EXTRACT(EPOCH FROM (ta.submitted_at - ta.session_task_order::float * 60)) / 60) as min_task_duration,
        MAX(EXTRACT(EPOCH FROM (ta.submitted_at - ta.session_task_order::float * 60)) / 60) as max_task_duration,
        COUNT(DISTINCT ae.event_id) FILTER WHERE ae.adaptation_type = 'pacing_adjustment' as pacing_adaptation_count,
        MAX(ae.adaptation_type) FILTER WHERE ae.adaptation_type = 'pacing_adjustment' as pacing_adjustment_type
    FROM learning_sessions ls
    LEFT JOIN task_attempts ta ON ls.session_id = ta.session_id
    LEFT JOIN adaptation_events ae ON ls.session_id = ae.session_id
    WHERE ls.user_id = :user_id
        AND ls.completed_at IS NOT NULL
    GROUP BY ls.session_id, ls.user_id, ls.started_at, ls.completed_at, ls.tasks_completed
    ORDER BY ls.started_at ASC
    """
    
    QUERY_GROUP_PACING_METRICS = """
    -- Extract aggregate pacing metrics across all users
    SELECT 
        ls.user_id,
        COUNT(DISTINCT ls.session_id) as total_sessions,
        AVG(EXTRACT(EPOCH FROM (COALESCE(ls.completed_at, NOW()) - ls.started_at)) / 60) as avg_session_duration,
        STDDEV(EXTRACT(EPOCH FROM (COALESCE(ls.completed_at, NOW()) - ls.started_at)) / 60) as session_duration_stddev,
        AVG(ls.tasks_completed) as avg_tasks_completed,
        COUNT(DISTINCT ae.event_id) FILTER WHERE ae.adaptation_type = 'pacing_adjustment' as pacing_adaptation_count
    FROM learning_sessions ls
    LEFT JOIN adaptation_events ae ON ls.session_id = ae.session_id
    WHERE ls.completed_at IS NOT NULL
    GROUP BY ls.user_id
    ORDER BY total_sessions DESC
    """
    
    QUERY_PACING_ENGAGEMENT_CORRELATION = """
    -- Extract correlation between pacing stability and engagement
    SELECT 
        ls.session_id,
        ls.user_id,
        ls.tasks_completed,
        EXTRACT(EPOCH FROM (COALESCE(ls.completed_at, NOW()) - ls.started_at)) / 60 as session_duration,
        STDDEV(EXTRACT(EPOCH FROM (ta.submitted_at - ta.session_task_order::float * 60)) / 60) as task_duration_stddev,
        AVG(CASE WHEN ta.is_correct THEN 1.0 ELSE 0.0 END) as accuracy
    FROM learning_sessions ls
    LEFT JOIN task_attempts ta ON ls.session_id = ta.session_id
    WHERE ls.completed_at IS NOT NULL
    GROUP BY ls.session_id, ls.user_id, ls.tasks_completed
    """
    
    def __init__(self, db_store=None):
        """
        Initialize pacing stability analyzer.
        
        Args:
            db_store: Database connection for executing queries
        """
        self._db_store = db_store
    
    def analyze_session_pacing(self, user_id: str) -> List[SessionPacingMetrics]:
        """
        Analyze pacing metrics for a learner's sessions.
        
        Measures task completion rates, time between tasks, and adaptation pacing signals.
        
        Args:
            user_id: User ID to analyze pacing for
            
        Returns:
            List of SessionPacingMetrics for each session
        """
        logger.info(f"🔍 Analyzing pacing stability for user {user_id}")
        
        if not self._db_store:
            logger.warning("No database store available for pacing analysis")
            return []
        
        try:
            results = self._db_store.fetch_all(
                self.QUERY_SESSION_PACING_METRICS,
                {"user_id": user_id}
            )
            
            metrics = []
            for row in results:
                # Calculate engagement score based on task completion consistency
                task_duration_stddev = row["task_duration_stddev"] or 0
                avg_task_duration = row["avg_task_duration"] or 1.0
                
                # Lower standard deviation relative to mean = more consistent pacing = higher engagement
                if avg_task_duration > 0:
                    pacing_consistency = 1.0 - min(task_duration_stddev / avg_task_duration, 1.0)
                else:
                    pacing_consistency = 0.5
                
                # Engagement score combines pacing consistency with task completion
                tasks_completed = row["tasks_completed"] or 0
                engagement_score = (pacing_consistency + min(tasks_completed / 10.0, 1.0)) / 2.0
                
                # Completion rate (assuming 10 tasks per session as baseline)
                completion_rate = min(tasks_completed / 10.0, 1.0)
                
                metrics.append(SessionPacingMetrics(
                    session_id=row["session_id"],
                    user_id=user_id,
                    started_at=row["started_at"],
                    completed_at=row["completed_at"],
                    tasks_completed=tasks_completed,
                    total_session_duration_minutes=row["total_duration_minutes"] or 0,
                    average_task_duration_minutes=row["avg_task_duration"] or 0,
                    task_duration_std_dev=task_duration_stddev,
                    min_task_duration_minutes=row["min_task_duration"] or 0,
                    max_task_duration_minutes=row["max_task_duration"] or 0,
                    pacing_adaptation_count=row["pacing_adaptation_count"] or 0,
                    pacing_adjustment_type=row["pacing_adjustment_type"],
                    engagement_score=engagement_score,
                    completion_rate=completion_rate
                ))
            
            logger.debug(f"Analyzed {len(metrics)} session pacing metrics for user {user_id}")
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to analyze pacing for user {user_id}: {e}")
            return []
    
    def detect_pacing_oscillation(self, user_id: str) -> PacingOscillationPattern:
        """
        Detect pacing oscillation patterns in learner behavior.
        
        Identifies speed-up/slow-down cycles that may indicate pacing instability.
        
        Args:
            user_id: User ID to analyze oscillation for
            
        Returns:
            PacingOscillationPattern with oscillation analysis
        """
        logger.info(f"🔍 Detecting pacing oscillation for user {user_id}")
        
        session_metrics = self.analyze_session_pacing(user_id)
        
        if len(session_metrics) < 3:
            # Need at least 3 sessions to detect oscillation
            return PacingOscillationPattern(
                user_id=user_id,
                oscillation_count=0,
                oscillation_amplitude_avg=0.0,
                oscillation_frequency_per_hour=0.0,
                is_oscillating=False,
                oscillation_severity=PacingStabilityLevel.STABLE,
                total_sessions_analyzed=len(session_metrics),
                sessions_with_oscillation=0
            )
        
        try:
            # Extract task durations over time
            task_durations = [m.average_task_duration_minutes for m in session_metrics]
            
            # Detect oscillations using simple sign changes in differences
            oscillation_count = 0
            for i in range(1, len(task_durations) - 1):
                diff1 = task_durations[i] - task_durations[i - 1]
                diff2 = task_durations[i + 1] - task_durations[i]
                # Sign change indicates oscillation
                if (diff1 > 0 and diff2 < 0) or (diff1 < 0 and diff2 > 0):
                    oscillation_count += 1
            
            # Calculate oscillation amplitude
            if len(task_durations) > 1:
                amplitude_sum = sum(abs(task_durations[i] - task_durations[i - 1]) for i in range(1, len(task_durations)))
                oscillation_amplitude_avg = amplitude_sum / (len(task_durations) - 1)
            else:
                oscillation_amplitude_avg = 0.0
            
            # Calculate oscillation frequency (oscillations per hour)
            total_time_hours = sum(m.total_session_duration_minutes / 60.0 for m in session_metrics)
            if total_time_hours > 0:
                oscillation_frequency_per_hour = oscillation_count / total_time_hours
            else:
                oscillation_frequency_per_hour = 0.0
            
            # Determine if oscillating (more than 1 oscillation per 2 hours)
            is_oscillating = oscillation_frequency_per_hour > 0.5
            
            # Determine oscillation severity
            if oscillation_frequency_per_hour > 2.0:
                oscillation_severity = PacingStabilityLevel.HIGHLY_UNSTABLE
            elif oscillation_frequency_per_hour > 1.0:
                oscillation_severity = PacingStabilityLevel.UNSTABLE
            elif oscillation_frequency_per_hour > 0.5:
                oscillation_severity = PacingStabilityLevel.MODERATELY_STABLE
            else:
                oscillation_severity = PacingStabilityLevel.STABLE
            
            # Count sessions with oscillation (based on task duration variance)
            sessions_with_oscillation = sum(
                1 for m in session_metrics 
                if m.task_duration_std_dev > m.average_task_duration_minutes * 0.5
            )
            
            return PacingOscillationPattern(
                user_id=user_id,
                oscillation_count=oscillation_count,
                oscillation_amplitude_avg=oscillation_amplitude_avg,
                oscillation_frequency_per_hour=oscillation_frequency_per_hour,
                is_oscillating=is_oscillating,
                oscillation_severity=oscillation_severity,
                total_sessions_analyzed=len(session_metrics),
                sessions_with_oscillation=sessions_with_oscillation
            )
            
        except Exception as e:
            logger.error(f"Failed to detect oscillation for user {user_id}: {e}")
            return PacingOscillationPattern(
                user_id=user_id,
                oscillation_count=0,
                oscillation_amplitude_avg=0.0,
                oscillation_frequency_per_hour=0.0,
                is_oscillating=False,
                oscillation_severity=PacingStabilityLevel.STABLE,
                total_sessions_analyzed=len(session_metrics),
                sessions_with_oscillation=0
            )
    
    def generate_pacing_stability_report(self) -> PacingStabilityReport:
        """
        Generate aggregate pacing stability report across all learners.
        
        Analyzes pacing stability, oscillation patterns, and adaptation effectiveness.
        
        Returns:
            PacingStabilityReport with comprehensive stability metrics
        """
        logger.info("🔍 Generating pacing stability report")
        
        if not self._db_store:
            logger.warning("No database store available for pacing report")
            return self._empty_report()
        
        try:
            # Extract group pacing metrics
            results = self._db_store.fetch_all(
                self.QUERY_GROUP_PACING_METRICS,
                {}
            )
            
            # Extract pacing-engagement correlation data
            correlation_data = self._db_store.fetch_all(
                self.QUERY_PACING_ENGAGEMENT_CORRELATION,
                {}
            )
            
            # Calculate aggregate metrics
            total_sessions = sum(row["total_sessions"] for row in results)
            
            # Determine stable vs unstable sessions based on duration variance
            stable_sessions = sum(
                row["total_sessions"] for row in results
                if (row["session_duration_stddev"] or 0) < (row["avg_session_duration"] or 1) * 0.3
            )
            unstable_sessions = total_sessions - stable_sessions
            
            # Calculate average pacing stability score
            if len(results) > 0:
                stability_scores = []
                for row in results:
                    avg_duration = row["avg_session_duration"] or 1
                    duration_stddev = row["session_duration_stddev"] or 0
                    stability_score = 1.0 - min(duration_stddev / avg_duration, 1.0)
                    stability_scores.append(stability_score)
                average_pacing_stability_score = statistics.mean(stability_scores)
            else:
                average_pacing_stability_score = 0.0
            
            # Count oscillating users
            oscillating_users = 0
            total_oscillation_severity = 0.0
            
            for row in results:
                # Simple oscillation detection based on session duration variance
                avg_duration = row["avg_session_duration"] or 1
                duration_stddev = row["session_duration_stddev"] or 0
                if duration_stddev > avg_duration * 0.5:
                    oscillating_users += 1
                    # Map variance to severity (0-1)
                    severity = min(duration_stddev / avg_duration, 1.0)
                    total_oscillation_severity += severity
            
            average_oscillation_severity = (
                total_oscillation_severity / oscillating_users
                if oscillating_users > 0 else 0.0
            )
            
            # Count sessions with pacing adaptations
            sessions_with_pacing_adaptations = sum(
                row["pacing_adaptation_count"] or 0 for row in results
            )
            
            # Calculate pacing adaptation effectiveness
            # (sessions with adaptations that are stable / total sessions with adaptations)
            pacing_adaptation_effectiveness = 0.0
            if sessions_with_pacing_adaptations > 0:
                stable_with_adaptations = sum(
                    1 for row in results
                    if (row["pacing_adaptation_count"] or 0) > 0
                    and (row["session_duration_stddev"] or 0) < (row["avg_session_duration"] or 1) * 0.3
                )
                pacing_adaptation_effectiveness = stable_with_adaptations / sessions_with_pacing_adaptations
            
            # Calculate pacing-engagement correlation
            pacing_engagement_correlation = self._calculate_correlation(
                correlation_data,
                "task_duration_stddev",
                "accuracy"
            )
            
            # Calculate pacing-completion correlation
            pacing_completion_correlation = self._calculate_correlation(
                correlation_data,
                "task_duration_stddev",
                "tasks_completed"
            )
            
            return PacingStabilityReport(
                total_sessions=total_sessions,
                stable_sessions=stable_sessions,
                unstable_sessions=unstable_sessions,
                average_pacing_stability_score=average_pacing_stability_score,
                oscillating_users=oscillating_users,
                average_oscillation_severity=average_oscillation_severity,
                sessions_with_pacing_adaptations=sessions_with_pacing_adaptations,
                pacing_adaptation_effectiveness=pacing_adaptation_effectiveness,
                pacing_engagement_correlation=pacing_engagement_correlation,
                pacing_completion_correlation=pacing_completion_correlation
            )
            
        except Exception as e:
            logger.error(f"Failed to generate pacing stability report: {e}")
            return self._empty_report()
    
    def _calculate_correlation(
        self,
        data: List[Dict[str, Any]],
        x_field: str,
        y_field: str
    ) -> float:
        """
        Calculate Pearson correlation coefficient between two fields.
        
        Args:
            data: List of data records
            x_field: Field name for x values
            y_field: Field name for y values
            
        Returns:
            Correlation coefficient (-1 to 1)
        """
        try:
            x_values = [row.get(x_field, 0) or 0 for row in data]
            y_values = [row.get(y_field, 0) or 0 for row in data]
            
            if len(x_values) < 2:
                return 0.0
            
            # Calculate means
            mean_x = statistics.mean(x_values)
            mean_y = statistics.mean(y_values)
            
            # Calculate covariance and standard deviations
            covariance = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_values, y_values))
            std_x = statistics.pstdev(x_values)
            std_y = statistics.pstdev(y_values)
            
            # Calculate correlation
            if std_x > 0 and std_y > 0:
                return covariance / (len(x_values) * std_x * std_y)
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"Failed to calculate correlation: {e}")
            return 0.0
    
    def _empty_report(self) -> PacingStabilityReport:
        """Return an empty report when no data is available."""
        return PacingStabilityReport(
            total_sessions=0,
            stable_sessions=0,
            unstable_sessions=0,
            average_pacing_stability_score=0.0,
            oscillating_users=0,
            average_oscillation_severity=0.0,
            sessions_with_pacing_adaptations=0,
            pacing_adaptation_effectiveness=0.0,
            pacing_engagement_correlation=0.0,
            pacing_completion_correlation=0.0
        )
