"""
C2.2.3 - Misconception Recurrence Tracking

Tracking system to identify recurring misconceptions across sessions, measure remediation success,
and identify stubborn misconceptions needing alternative interventions.

Focus on pedagogical semantic trajectories (learning), NOT infrastructure metrics (machines).
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Set
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class MisconceptionSeverity(Enum):
    """Classification of misconception severity."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class MisconceptionOccurrence:
    """
    A single occurrence of a misconception.
    
    Tracks when and where a misconception appeared in a learner's journey.
    """
    misconception_id: str
    user_id: str
    concept_id: str
    session_id: str
    task_id: str
    occurred_at: datetime
    is_correct_after: bool
    remediation_attempted: bool
    adaptation_type: Optional[str]
    policy_version: Optional[str]


@dataclass
class MisconceptionPattern:
    """
    Pattern analysis for a specific misconception.
    
    Tracks recurrence, remediation success, and stubbornness indicators.
    """
    misconception_id: str
    user_id: Optional[str]  # None for aggregate analysis
    total_occurrences: int
    first_occurrence: datetime
    last_occurrence: datetime
    sessions_affected: int
    concepts_affected: Set[str]
    
    # Remediation metrics
    remediation_attempts: int
    successful_remediations: int
    remediation_success_rate: float
    
    # Stubbornness indicators
    recurrence_after_remediation: int
    average_recurrence_interval_days: float
    stubbornness_score: float  # 0-1, higher = more stubborn
    
    # Context
    severity: MisconceptionSeverity
    recommended_alternative_intervention: Optional[str]


@dataclass
class RemediationEffectivenessReport:
    """
    Report on remediation effectiveness across all misconceptions.
    
    Aggregates misconception patterns into actionable insights.
    """
    total_misconceptions: int
    stubborn_misconceptions: List[str]  # misconceptions needing alternative interventions
    successfully_remediated: List[str]  # misconceptions with high remediation success
    average_remediation_success_rate: float
    
    # By severity
    critical_misconceptions: int
    high_misconceptions: int
    medium_misconceptions: int
    low_misconceptions: int
    
    # Remediation patterns
    most_effective_adaptation_types: Dict[str, float]
    least_effective_adaptation_types: Dict[str, float]


class MisconceptionTrackingSystem:
    """
    Tracking system for misconception recurrence and remediation effectiveness.
    
    Focus on pedagogical semantic trajectories:
    - Identify recurring misconceptions across sessions
    - Measure remediation success
    - Identify stubborn misconceptions needing alternative interventions
    
    NOT infrastructure metrics (machines, latency, throughput).
    """
    
    QUERY_MISCONCEPTION_OCCURRENCES = """
    -- Extract all misconception occurrences for a user
    SELECT 
        ta.misconception_id,
        ta.user_id,
        ta.concept_id,
        ta.session_id,
        ta.task_id,
        ta.submitted_at as occurred_at,
        ta.is_correct,
        ae.adaptation_type,
        ae.policy_version
    FROM task_attempts ta
    LEFT JOIN adaptation_events ae ON ta.session_id = ae.session_id 
        AND ABS(EXTRACT(EPOCH FROM (ta.submitted_at - ae.created_at))) < 300
    WHERE ta.user_id = :user_id
        AND ta.misconception_id IS NOT NULL
    ORDER BY ta.submitted_at ASC
    """
    
    QUERY_MISCONCEPTION_PATTERN = """
    -- Extract misconception pattern data for a user
    SELECT 
        ta.misconception_id,
        ta.user_id,
        COUNT(ta.task_id) as total_occurrences,
        MIN(ta.submitted_at) as first_occurrence,
        MAX(ta.submitted_at) as last_occurrence,
        COUNT(DISTINCT ta.session_id) as sessions_affected,
        COUNT(DISTINCT ta.concept_id) as concepts_affected,
        COUNT(DISTINCT ae.event_id) as remediation_attempts,
        COUNT(DISTINCT CASE WHEN ta.is_correct THEN ta.task_id END) as successful_remediations,
        COUNT(DISTINCT CASE WHEN ae.event_id IS NOT NULL THEN ta.task_id END FILTER WHERE NOT ta.is_correct) as recurrence_after_remediation
    FROM task_attempts ta
    LEFT JOIN adaptation_events ae ON ta.session_id = ae.session_id 
        AND ABS(EXTRACT(EPOCH FROM (ta.submitted_at - ae.created_at))) < 300
    WHERE ta.user_id = :user_id
        AND ta.misconception_id IS NOT NULL
    GROUP BY ta.misconception_id, ta.user_id
    ORDER BY total_occurrences DESC
    """
    
    QUERY_GROUP_MISCONCEPTION_PATTERN = """
    -- Extract aggregate misconception patterns across all users
    SELECT 
        ta.misconception_id,
        COUNT(DISTINCT ta.task_id) as total_occurrences,
        MIN(ta.submitted_at) as first_occurrence,
        MAX(ta.submitted_at) as last_occurrence,
        COUNT(DISTINCT ta.session_id) as sessions_affected,
        COUNT(DISTINCT ta.user_id) as users_affected,
        COUNT(DISTINCT ae.event_id) as remediation_attempts,
        COUNT(DISTINCT CASE WHEN ta.is_correct THEN ta.task_id END) as successful_remediations
    FROM task_attempts ta
    LEFT JOIN adaptation_events ae ON ta.session_id = ae.session_id 
        AND ABS(EXTRACT(EPOCH FROM (ta.submitted_at - ae.created_at))) < 300
    WHERE ta.misconception_id IS NOT NULL
    GROUP BY ta.misconception_id
    ORDER BY total_occurrences DESC
    """
    
    QUERY_REMEDIATION_BY_ADAPTATION_TYPE = """
    -- Extract remediation effectiveness by adaptation type
    SELECT 
        ae.adaptation_type,
        COUNT(DISTINCT ta.task_id) as total_attempts,
        COUNT(DISTINCT CASE WHEN ta.is_correct THEN ta.task_id END) as successful_remediations
    FROM task_attempts ta
    LEFT JOIN adaptation_events ae ON ta.session_id = ae.session_id 
        AND ABS(EXTRACT(EPOCH FROM (ta.submitted_at - ae.created_at))) < 300
    WHERE ta.misconception_id IS NOT NULL
        AND ae.adaptation_type IS NOT NULL
    GROUP BY ae.adaptation_type
    ORDER BY total_attempts DESC
    """
    
    def __init__(self, db_store=None):
        """
        Initialize misconception tracking system.
        
        Args:
            db_store: Database connection for executing queries
        """
        self._db_store = db_store
    
    def track_misconception_recurrence(
        self,
        user_id: str
    ) -> List[MisconceptionPattern]:
        """
        Track misconception recurrence patterns for a learner.
        
        Identifies recurring misconceptions across sessions and measures remediation success.
        
        Args:
            user_id: User ID to track misconceptions for
            
        Returns:
            List of MisconceptionPattern for each misconception encountered
        """
        logger.info(f"🔍 Tracking misconception recurrence for user {user_id}")
        
        if not self._db_store:
            logger.warning("No database store available for misconception tracking")
            return []
        
        try:
            # Extract misconception pattern data
            results = self._db_store.fetch_all(
                self.QUERY_MISCONCEPTION_PATTERN,
                {"user_id": user_id}
            )
            
            patterns = []
            for row in results:
                # Calculate remediation success rate
                remediation_attempts = row["remediation_attempts"] or 0
                successful_remediations = row["successful_remediations"] or 0
                remediation_success_rate = (
                    successful_remediations / remediation_attempts 
                    if remediation_attempts > 0 else 0.0
                )
                
                # Calculate average recurrence interval
                first_occurrence = row["first_occurrence"]
                last_occurrence = row["last_occurrence"]
                total_occurrences = row["total_occurrences"]
                
                if total_occurrences > 1 and first_occurrence and last_occurrence:
                    time_span_days = (last_occurrence - first_occurrence).days
                    average_recurrence_interval_days = time_span_days / (total_occurrences - 1)
                else:
                    average_recurrence_interval_days = 0.0
                
                # Calculate stubbornness score
                recurrence_after_remediation = row["recurrence_after_remediation"] or 0
                stubbornness_score = self._calculate_stubbornness_score(
                    total_occurrences,
                    remediation_success_rate,
                    recurrence_after_remediation
                )
                
                # Determine severity
                severity = self._determine_severity(
                    total_occurrences,
                    remediation_success_rate,
                    stubbornness_score
                )
                
                # Get concepts affected
                concepts_affected = self._get_concepts_for_misconception(
                    user_id, row["misconception_id"]
                )
                
                patterns.append(MisconceptionPattern(
                    misconception_id=row["misconception_id"],
                    user_id=user_id,
                    total_occurrences=total_occurrences,
                    first_occurrence=first_occurrence,
                    last_occurrence=last_occurrence,
                    sessions_affected=row["sessions_affected"],
                    concepts_affected=concepts_affected,
                    remediation_attempts=remediation_attempts,
                    successful_remediations=successful_remediations,
                    remediation_success_rate=remediation_success_rate,
                    recurrence_after_remediation=recurrence_after_remediation,
                    average_recurrence_interval_days=average_recurrence_interval_days,
                    stubbornness_score=stubbornness_score,
                    severity=severity,
                    recommended_alternative_intervention=self._recommend_alternative_intervention(
                        row["misconception_id"],
                        remediation_success_rate,
                        stubbornness_score
                    )
                ))
            
            logger.debug(f"Tracked {len(patterns)} misconception patterns for user {user_id}")
            return patterns
            
        except Exception as e:
            logger.error(f"Failed to track misconception recurrence for user {user_id}: {e}")
            return []
    
    def generate_remediation_effectiveness_report(self) -> RemediationEffectivenessReport:
        """
        Generate aggregate report on remediation effectiveness.
        
        Analyzes all misconceptions across all users to identify:
        - Stubborn misconceptions needing alternative interventions
        - Successfully remediated misconceptions
        - Most/least effective adaptation types
        
        Returns:
            RemediationEffectivenessReport with comprehensive effectiveness metrics
        """
        logger.info("🔍 Generating remediation effectiveness report")
        
        if not self._db_store:
            logger.warning("No database store available for remediation report")
            return self._empty_report()
        
        try:
            # Extract group misconception patterns
            misconception_results = self._db_store.fetch_all(
                self.QUERY_GROUP_MISCONCEPTION_PATTERN,
                {}
            )
            
            # Extract remediation effectiveness by adaptation type
            adaptation_results = self._db_store.fetch_all(
                self.QUERY_REMEDIATION_BY_ADAPTATION_TYPE,
                {}
            )
            
            # Calculate aggregate metrics
            total_misconceptions = len(misconception_results)
            
            # Identify stubborn and successfully remediated misconceptions
            stubborn_misconceptions = []
            successfully_remediated = []
            
            total_remediation_attempts = 0
            total_successful_remediations = 0
            
            severity_counts = {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            }
            
            for row in misconception_results:
                total_occurrences = row["total_occurrences"]
                remediation_attempts = row["remediation_attempts"] or 0
                successful_remediations = row["successful_remediations"] or 0
                
                total_remediation_attempts += remediation_attempts
                total_successful_remediations += successful_remediations
                
                remediation_success_rate = (
                    successful_remediations / remediation_attempts 
                    if remediation_attempts > 0 else 0.0
                )
                
                stubbornness_score = self._calculate_stubbornness_score(
                    total_occurrences,
                    remediation_success_rate,
                    0  # Not available in aggregate query
                )
                
                if stubbornness_score > 0.7:
                    stubborn_misconceptions.append(row["misconception_id"])
                
                if remediation_success_rate > 0.8 and remediation_attempts > 0:
                    successfully_remediated.append(row["misconception_id"])
                
                # Determine severity
                severity = self._determine_severity(
                    total_occurrences,
                    remediation_success_rate,
                    stubbornness_score
                )
                severity_counts[severity.value] += 1
            
            # Calculate average remediation success rate
            average_remediation_success_rate = (
                total_successful_remediations / total_remediation_attempts
                if total_remediation_attempts > 0 else 0.0
            )
            
            # Calculate effectiveness by adaptation type
            most_effective_adaptation_types = {}
            least_effective_adaptation_types = {}
            
            for row in adaptation_results:
                adaptation_type = row["adaptation_type"]
                total_attempts = row["total_attempts"]
                successful_remediations = row["successful_remediations"]
                
                effectiveness = (
                    successful_remediations / total_attempts
                    if total_attempts > 0 else 0.0
                )
                
                most_effective_adaptation_types[adaptation_type] = effectiveness
                least_effective_adaptation_types[adaptation_type] = effectiveness
            
            # Sort by effectiveness
            most_effective_adaptation_types = dict(
                sorted(most_effective_adaptation_types.items(), key=lambda x: x[1], reverse=True)
            )
            least_effective_adaptation_types = dict(
                sorted(least_effective_adaptation_types.items(), key=lambda x: x[1])
            )
            
            return RemediationEffectivenessReport(
                total_misconceptions=total_misconceptions,
                stubborn_misconceptions=stubborn_misconceptions,
                successfully_remediated=successfully_remediated,
                average_remediation_success_rate=average_remediation_success_rate,
                critical_misconceptions=severity_counts["critical"],
                high_misconceptions=severity_counts["high"],
                medium_misconceptions=severity_counts["medium"],
                low_misconceptions=severity_counts["low"],
                most_effective_adaptation_types=most_effective_adaptation_types,
                least_effective_adaptation_types=least_effective_adaptation_types
            )
            
        except Exception as e:
            logger.error(f"Failed to generate remediation effectiveness report: {e}")
            return self._empty_report()
    
    def _get_concepts_for_misconception(
        self,
        user_id: str,
        misconception_id: str
    ) -> Set[str]:
        """Get all concepts affected by a specific misconception for a user."""
        if not self._db_store:
            return set()
        
        try:
            results = self._db_store.fetch_all(
                """
                SELECT DISTINCT concept_id
                FROM task_attempts
                WHERE user_id = :user_id AND misconception_id = :misconception_id
                """,
                {"user_id": user_id, "misconception_id": misconception_id}
            )
            
            return {row["concept_id"] for row in results if row["concept_id"]}
            
        except Exception as e:
            logger.error(f"Failed to get concepts for misconception {misconception_id}: {e}")
            return set()
    
    def _calculate_stubbornness_score(
        self,
        total_occurrences: int,
        remediation_success_rate: float,
        recurrence_after_remediation: int
    ) -> float:
        """
        Calculate stubbornness score for a misconception.
        
        Higher score = more stubborn (harder to remediate).
        
        Args:
            total_occurrences: Total number of times misconception occurred
            remediation_success_rate: Success rate of remediation attempts
            recurrence_after_remediation: Number of recurrences after remediation
            
        Returns:
            Stubbornness score (0-1)
        """
        # Base stubbornness from occurrence count
        occurrence_score = min(total_occurrences / 10.0, 1.0)
        
        # Stubbornness increases with low remediation success
        remediation_score = 1.0 - remediation_success_rate
        
        # Stubbornness increases with recurrence after remediation
        recurrence_score = min(recurrence_after_remediation / 5.0, 1.0)
        
        # Weighted combination
        stubbornness_score = (
            0.4 * occurrence_score +
            0.4 * remediation_score +
            0.2 * recurrence_score
        )
        
        return stubbornness_score
    
    def _determine_severity(
        self,
        total_occurrences: int,
        remediation_success_rate: float,
        stubbornness_score: float
    ) -> MisconceptionSeverity:
        """
        Determine severity level for a misconception.
        
        Args:
            total_occurrences: Total number of occurrences
            remediation_success_rate: Success rate of remediation
            stubbornness_score: Stubbornness score
            
        Returns:
            MisconceptionSeverity classification
        """
        if stubbornness_score > 0.8 or (total_occurrences > 5 and remediation_success_rate < 0.2):
            return MisconceptionSeverity.CRITICAL
        elif stubbornness_score > 0.6 or (total_occurrences > 3 and remediation_success_rate < 0.4):
            return MisconceptionSeverity.HIGH
        elif stubbornness_score > 0.4 or total_occurrences > 2:
            return MisconceptionSeverity.MEDIUM
        else:
            return MisconceptionSeverity.LOW
    
    def _recommend_alternative_intervention(
        self,
        misconception_id: str,
        remediation_success_rate: float,
        stubbornness_score: float
    ) -> Optional[str]:
        """
        Recommend alternative intervention for stubborn misconceptions.
        
        Args:
            misconception_id: ID of the misconception
            remediation_success_rate: Current remediation success rate
            stubbornness_score: Stubbornness score
            
        Returns:
            Recommended alternative intervention type or None
        """
        if stubbornness_score > 0.7:
            # Stubborn misconceptions need alternative approaches
            if remediation_success_rate < 0.3:
                return "multimodal_intervention"
            elif remediation_success_rate < 0.5:
                return "prerequisite_review"
            else:
                return "transfer_opportunity"
        
        return None
    
    def _empty_report(self) -> RemediationEffectivenessReport:
        """Return an empty report when no data is available."""
        return RemediationEffectivenessReport(
            total_misconceptions=0,
            stubborn_misconceptions=[],
            successfully_remediated=[],
            average_remediation_success_rate=0.0,
            critical_misconceptions=0,
            high_misconceptions=0,
            medium_misconceptions=0,
            low_misconceptions=0,
            most_effective_adaptation_types={},
            least_effective_adaptation_types={}
        )
