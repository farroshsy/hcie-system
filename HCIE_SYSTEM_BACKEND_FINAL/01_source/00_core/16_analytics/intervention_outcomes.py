"""
C2.2.5 - Intervention Outcome Analysis

Analysis to measure intervention effectiveness, compare different intervention types,
and measure intervention timing impact on learning outcomes.

Focus on pedagogical semantic trajectories (learning), NOT infrastructure metrics (machines).
"""

from dataclasses import dataclass
from typing import List
from datetime import datetime
from enum import Enum
import logging
import statistics

logger = logging.getLogger(__name__)


class InterventionTiming(Enum):
    """Classification of intervention timing."""
    EARLY = "early"  # Before mastery threshold
    MIDDLE = "middle"  # During learning phase
    LATE = "late"  # After mastery threshold


@dataclass
class InterventionEvent:
    """
    A single intervention event.
    
    Tracks when and where an intervention occurred and its immediate outcome.
    """
    intervention_id: str
    user_id: str
    session_id: str
    intervention_type: str
    occurred_at: datetime
    timing: InterventionTiming
    target_concept_id: str
    policy_version: str
    
    # Immediate outcome
    immediate_correctness: float  # 0-1, correctness of next task after intervention
    mastery_before: float
    mastery_after: float
    mastery_delta: float


@dataclass
class InterventionEffectiveness:
    """
    Effectiveness analysis for a specific intervention type.
    
    Measures how well interventions of a given type improve learning outcomes.
    """
    intervention_type: str
    total_interventions: int
    successful_interventions: int  # interventions that led to mastery improvement
    effectiveness_rate: float  # 0-1
    
    # Learning impact
    average_mastery_delta: float
    average_correctness_after: float
    
    # Timing breakdown
    early_interventions: int
    early_success_rate: float
    middle_interventions: int
    middle_success_rate: float
    late_interventions: int
    late_success_rate: float


@dataclass
class InterventionOutcomeReport:
    """
    Comprehensive report on intervention outcomes.
    
    Aggregates intervention effectiveness across all intervention types and timing.
    """
    total_interventions: int
    overall_effectiveness_rate: float  # 0-1
    average_mastery_improvement: float
    
    # Most effective intervention types
    most_effective_interventions: List[str]
    least_effective_interventions: List[str]
    
    # Timing analysis
    early_intervention_effectiveness: float
    middle_intervention_effectiveness: float
    late_intervention_effectiveness: float
    optimal_timing: InterventionTiming
    
    # Per-intervention-type breakdown
    intervention_effectiveness: List[InterventionEffectiveness]


class InterventionOutcomeAnalyzer:
    """
    Analyzer for intervention effectiveness and timing impact.
    
    Focus on pedagogical semantic trajectories:
    - Measure intervention effectiveness
    - Compare different intervention types
    - Measure intervention timing impact on learning outcomes
    
    NOT infrastructure metrics (machines, latency, throughput).
    """
    
    QUERY_INTERVENTION_EVENTS = """
    -- Extract intervention events for a user
    SELECT 
        ae.event_id as intervention_id,
        ae.user_id,
        ae.session_id,
        ae.adaptation_type as intervention_type,
        ae.created_at as occurred_at,
        ae.concept_id as target_concept_id,
        ae.policy_version,
        lp.mastery as mastery_before,
        lp_after.mastery as mastery_after,
        ta_after.is_correct as immediate_correctness
    FROM adaptation_events ae
    JOIN learner_progress lp ON ae.user_id = lp.user_id 
        AND ae.concept_id = lp.concept_id
        AND lp.updated_at <= ae.created_at
    LEFT JOIN learner_progress lp_after ON ae.user_id = lp_after.user_id 
        AND ae.concept_id = lp_after.concept_id
        AND lp_after.updated_at > ae.created_at
        AND lp_after.updated_at <= (ae.created_at + INTERVAL '1 hour')
    LEFT JOIN task_attempts ta_after ON ae.session_id = ta_after.session_id
        AND ta_after.submitted_at > ae.created_at
        AND ta_after.submitted_at <= (ae.created_at + INTERVAL '30 minutes')
    WHERE ae.user_id = :user_id
        AND ae.adaptation_type IN ('remediation', 'difficulty_shift', 'prerequisite_review', 'confidence_support')
    ORDER BY ae.created_at ASC
    """
    
    QUERY_GROUP_INTERVENTION_EFFECTIVENESS = """
    -- Extract aggregate intervention effectiveness across all users
    SELECT 
        ae.adaptation_type as intervention_type,
        COUNT(DISTINCT ae.event_id) as total_interventions,
        AVG(lp_after.mastery - lp.mastery) as avg_mastery_delta,
        AVG(CASE WHEN ta_after.is_correct THEN 1.0 ELSE 0.0 END) as avg_correctness_after,
        COUNT(DISTINCT CASE WHEN lp_after.mastery > lp.mastery THEN ae.event_id END) as successful_interventions
    FROM adaptation_events ae
    JOIN learner_progress lp ON ae.user_id = lp.user_id 
        AND ae.concept_id = lp.concept_id
        AND lp.updated_at <= ae.created_at
    LEFT JOIN learner_progress lp_after ON ae.user_id = lp_after.user_id 
        AND ae.concept_id = lp_after.concept_id
        AND lp_after.updated_at > ae.created_at
        AND lp_after.updated_at <= (ae.created_at + INTERVAL '1 hour')
    LEFT JOIN task_attempts ta_after ON ae.session_id = ta_after.session_id
        AND ta_after.submitted_at > ae.created_at
        AND ta_after.submitted_at <= (ae.created_at + INTERVAL '30 minutes')
    WHERE ae.adaptation_type IN ('remediation', 'difficulty_shift', 'prerequisite_review', 'confidence_support')
    GROUP BY ae.adaptation_type
    ORDER BY total_interventions DESC
    """
    
    QUERY_INTERVENTION_TIMING = """
    -- Extract intervention timing and effectiveness
    SELECT 
        ae.event_id,
        ae.user_id,
        ae.adaptation_type,
        ae.created_at,
        lp.mastery as mastery_before,
        lp_after.mastery as mastery_after,
        CASE 
            WHEN lp.mastery < 0.3 THEN 'early'
            WHEN lp.mastery < 0.7 THEN 'middle'
            ELSE 'late'
        END as timing_category
    FROM adaptation_events ae
    JOIN learner_progress lp ON ae.user_id = lp.user_id 
        AND ae.concept_id = lp.concept_id
        AND lp.updated_at <= ae.created_at
    LEFT JOIN learner_progress lp_after ON ae.user_id = lp_after.user_id 
        AND ae.concept_id = lp_after.concept_id
        AND lp_after.updated_at > ae.created_at
        AND lp_after.updated_at <= (ae.created_at + INTERVAL '1 hour')
    WHERE ae.adaptation_type IN ('remediation', 'difficulty_shift', 'prerequisite_review', 'confidence_support')
    """
    
    def __init__(self, db_store=None):
        """
        Initialize intervention outcome analyzer.
        
        Args:
            db_store: Database connection for executing queries
        """
        self._db_store = db_store
    
    def analyze_intervention_events(self, user_id: str) -> List[InterventionEvent]:
        """
        Analyze intervention events for a learner.
        
        Extracts intervention events and measures immediate learning outcomes.
        
        Args:
            user_id: User ID to analyze interventions for
            
        Returns:
            List of InterventionEvent for each intervention
        """
        logger.info(f"🔍 Analyzing intervention events for user {user_id}")
        
        if not self._db_store:
            logger.warning("No database store available for intervention analysis")
            return []
        
        try:
            results = self._db_store.fetch_all(
                self.QUERY_INTERVENTION_EVENTS,
                {"user_id": user_id}
            )
            
            events = []
            for row in results:
                mastery_before = row["mastery_before"] or 0.0
                mastery_after = row["mastery_after"] or mastery_before
                mastery_delta = mastery_after - mastery_before
                
                # Determine timing based on mastery before intervention
                if mastery_before < 0.3:
                    timing = InterventionTiming.EARLY
                elif mastery_before < 0.7:
                    timing = InterventionTiming.MIDDLE
                else:
                    timing = InterventionTiming.LATE
                
                events.append(InterventionEvent(
                    intervention_id=row["intervention_id"],
                    user_id=user_id,
                    session_id=row["session_id"],
                    intervention_type=row["intervention_type"],
                    occurred_at=row["occurred_at"],
                    timing=timing,
                    target_concept_id=row["target_concept_id"],
                    policy_version=row["policy_version"],
                    immediate_correctness=row["immediate_correctness"] or 0.0,
                    mastery_before=mastery_before,
                    mastery_after=mastery_after,
                    mastery_delta=mastery_delta
                ))
            
            logger.debug(f"Analyzed {len(events)} intervention events for user {user_id}")
            return events
            
        except Exception as e:
            logger.error(f"Failed to analyze interventions for user {user_id}: {e}")
            return []
    
    def analyze_intervention_effectiveness(self, intervention_type: str) -> InterventionEffectiveness:
        """
        Analyze effectiveness of a specific intervention type.
        
        Measures how well interventions of a given type improve learning outcomes.
        
        Args:
            intervention_type: Type of intervention to analyze
            
        Returns:
            InterventionEffectiveness with effectiveness metrics
        """
        logger.info(f"🔍 Analyzing effectiveness of {intervention_type} interventions")
        
        if not self._db_store:
            logger.warning("No database store available for intervention effectiveness analysis")
            return self._empty_effectiveness(intervention_type)
        
        try:
            # Get all intervention events with timing
            results = self._db_store.fetch_all(
                self.QUERY_INTERVENTION_TIMING,
                {}
            )
            
            # Filter by intervention type
            type_results = [r for r in results if r["adaptation_type"] == intervention_type]
            
            if not type_results:
                return self._empty_effectiveness(intervention_type)
            
            total_interventions = len(type_results)
            successful_interventions = sum(
                1 for r in type_results 
                if r["mastery_after"] > r["mastery_before"]
            )
            effectiveness_rate = successful_interventions / total_interventions if total_interventions > 0 else 0.0
            
            # Calculate average mastery delta
            mastery_deltas = [r["mastery_after"] - r["mastery_before"] for r in type_results]
            average_mastery_delta = statistics.mean(mastery_deltas) if mastery_deltas else 0.0
            
            # Calculate average correctness after intervention
            # (This would need to be joined with task_attempts in a real implementation)
            average_correctness_after = 0.0  # Placeholder
            
            # Timing breakdown
            early_results = [r for r in type_results if r["timing_category"] == "early"]
            middle_results = [r for r in type_results if r["timing_category"] == "middle"]
            late_results = [r for r in type_results if r["timing_category"] == "late"]
            
            early_interventions = len(early_results)
            early_success_rate = (
                sum(1 for r in early_results if r["mastery_after"] > r["mastery_before"]) / early_interventions
                if early_interventions > 0 else 0.0
            )
            
            middle_interventions = len(middle_results)
            middle_success_rate = (
                sum(1 for r in middle_results if r["mastery_after"] > r["mastery_before"]) / middle_interventions
                if middle_interventions > 0 else 0.0
            )
            
            late_interventions = len(late_results)
            late_success_rate = (
                sum(1 for r in late_results if r["mastery_after"] > r["mastery_before"]) / late_interventions
                if late_interventions > 0 else 0.0
            )
            
            return InterventionEffectiveness(
                intervention_type=intervention_type,
                total_interventions=total_interventions,
                successful_interventions=successful_interventions,
                effectiveness_rate=effectiveness_rate,
                average_mastery_delta=average_mastery_delta,
                average_correctness_after=average_correctness_after,
                early_interventions=early_interventions,
                early_success_rate=early_success_rate,
                middle_interventions=middle_interventions,
                middle_success_rate=middle_success_rate,
                late_interventions=late_interventions,
                late_success_rate=late_success_rate
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze intervention effectiveness for {intervention_type}: {e}")
            return self._empty_effectiveness(intervention_type)
    
    def generate_intervention_outcome_report(self) -> InterventionOutcomeReport:
        """
        Generate aggregate intervention outcome report.
        
        Analyzes intervention effectiveness across all types and timing.
        
        Returns:
            InterventionOutcomeReport with comprehensive outcome metrics
        """
        logger.info("🔍 Generating intervention outcome report")
        
        if not self._db_store:
            logger.warning("No database store available for intervention report")
            return self._empty_report()
        
        try:
            # Get group intervention effectiveness
            results = self._db_store.fetch_all(
                self.QUERY_GROUP_INTERVENTION_EFFECTIVENESS,
                {}
            )
            
            # Get timing data
            timing_results = self._db_store.fetch_all(
                self.QUERY_INTERVENTION_TIMING,
                {}
            )
            
            # Calculate aggregate metrics
            total_interventions = sum(row["total_interventions"] for row in results)
            successful_interventions = sum(row["successful_interventions"] for row in results)
            overall_effectiveness_rate = (
                successful_interventions / total_interventions
                if total_interventions > 0 else 0.0
            )
            
            # Calculate average mastery improvement
            mastery_deltas = [row["avg_mastery_delta"] for row in results if row["avg_mastery_delta"]]
            average_mastery_improvement = statistics.mean(mastery_deltas) if mastery_deltas else 0.0
            
            # Determine most/least effective interventions
            intervention_types = [(r["adaptation_type"], r["successful_interventions"] / r["total_interventions"]) for r in results]
            intervention_types.sort(key=lambda x: x[1], reverse=True)
            
            most_effective_interventions = [t[0] for t in intervention_types[:3]]
            least_effective_interventions = [t[0] for t in intervention_types[-3:]]
            
            # Timing analysis
            early_results = [r for r in timing_results if r["timing_category"] == "early"]
            middle_results = [r for r in timing_results if r["timing_category"] == "middle"]
            late_results = [r for r in timing_results if r["timing_category"] == "late"]
            
            early_intervention_effectiveness = (
                sum(1 for r in early_results if r["mastery_after"] > r["mastery_before"]) / len(early_results)
                if early_results else 0.0
            )
            
            middle_intervention_effectiveness = (
                sum(1 for r in middle_results if r["mastery_after"] > r["mastery_before"]) / len(middle_results)
                if middle_results else 0.0
            )
            
            late_intervention_effectiveness = (
                sum(1 for r in late_results if r["mastery_after"] > r["mastery_before"]) / len(late_results)
                if late_results else 0.0
            )
            
            # Determine optimal timing
            timing_effectiveness = {
                InterventionTiming.EARLY: early_intervention_effectiveness,
                InterventionTiming.MIDDLE: middle_intervention_effectiveness,
                InterventionTiming.LATE: late_intervention_effectiveness
            }
            optimal_timing = max(timing_effectiveness.items(), key=lambda x: x[1])[0]
            
            # Per-intervention-type effectiveness
            intervention_effectiveness = []
            for row in results:
                intervention_type = row["adaptation_type"]
                effectiveness = self.analyze_intervention_effectiveness(intervention_type)
                intervention_effectiveness.append(effectiveness)
            
            return InterventionOutcomeReport(
                total_interventions=total_interventions,
                overall_effectiveness_rate=overall_effectiveness_rate,
                average_mastery_improvement=average_mastery_improvement,
                most_effective_interventions=most_effective_interventions,
                least_effective_interventions=least_effective_interventions,
                early_intervention_effectiveness=early_intervention_effectiveness,
                middle_intervention_effectiveness=middle_intervention_effectiveness,
                late_intervention_effectiveness=late_intervention_effectiveness,
                optimal_timing=optimal_timing,
                intervention_effectiveness=intervention_effectiveness
            )
            
        except Exception as e:
            logger.error(f"Failed to generate intervention outcome report: {e}")
            return self._empty_report()
    
    def _empty_effectiveness(self, intervention_type: str) -> InterventionEffectiveness:
        """Return empty effectiveness when no data is available."""
        return InterventionEffectiveness(
            intervention_type=intervention_type,
            total_interventions=0,
            successful_interventions=0,
            effectiveness_rate=0.0,
            average_mastery_delta=0.0,
            average_correctness_after=0.0,
            early_interventions=0,
            early_success_rate=0.0,
            middle_interventions=0,
            middle_success_rate=0.0,
            late_interventions=0,
            late_success_rate=0.0
        )
    
    def _empty_report(self) -> InterventionOutcomeReport:
        """Return empty report when no data is available."""
        return InterventionOutcomeReport(
            total_interventions=0,
            overall_effectiveness_rate=0.0,
            average_mastery_improvement=0.0,
            most_effective_interventions=[],
            least_effective_interventions=[],
            early_intervention_effectiveness=0.0,
            middle_intervention_effectiveness=0.0,
            late_intervention_effectiveness=0.0,
            optimal_timing=InterventionTiming.MIDDLE,
            intervention_effectiveness=[]
        )
