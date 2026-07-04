"""
Research Observability

Build learner trajectory explorer, replay comparison viewer, semantic drift explorer, 
adaptation lineage viewer, pacing evolution explorer, misconception evolution explorer.

Focus on pedagogical semantic trajectories (learning), NOT infrastructure metrics (machines).
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class VisualizationType(Enum):
    """Types of research visualizations."""
    LEARNER_TRAJECTORY = "learner_trajectory"
    REPLAY_COMPARISON = "replay_comparison"
    SEMANTIC_DRIFT = "semantic_drift"
    ADAPTATION_LINEAGE = "adaptation_lineage"
    PACING_EVOLUTION = "pacing_evolution"
    MISCONCEPTION_EVOLUTION = "misconception_evolution"


@dataclass
class TrajectoryDataPoint:
    """Single data point in a learner trajectory."""
    timestamp: datetime
    mastery: float
    uncertainty: float
    zpd_score: float
    concept_id: Optional[str]
    adaptation_type: Optional[str]
    policy_version: Optional[str]


@dataclass
class TrajectoryVisualization:
    """Visualization data for learner trajectory."""
    user_id: str
    visualization_type: VisualizationType
    data_points: List[TrajectoryDataPoint] = field(default_factory=list)
    
    # Summary metrics
    total_points: int = 0
    time_span_days: int = 0
    mastery_range: Tuple[float, float] = (0.0, 1.0)
    
    # Annotations
    key_events: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ResearchObservabilityReport:
    """Comprehensive research observability report."""
    user_id: str
    generated_at: datetime
    
    # Visualizations
    learner_trajectory: Optional[TrajectoryVisualization] = None
    replay_comparison: Optional[TrajectoryVisualization] = None
    semantic_drift: Optional[TrajectoryVisualization] = None
    adaptation_lineage: Optional[TrajectoryVisualization] = None
    pacing_evolution: Optional[TrajectoryVisualization] = None
    misconception_evolution: Optional[TrajectoryVisualization] = None
    
    # Metadata
    total_visualizations: int = 0
    data_quality_score: float = 1.0


class ResearchObservabilityService:
    """
    Service for building research observability visualizations.
    
    Focuses on pedagogical semantic trajectories (learning), NOT infrastructure metrics.
    """
    
    def generate_trajectory_visualization(
        self,
        user_id: str,
        trajectory_data: List[Dict[str, Any]]
    ) -> TrajectoryVisualization:
        """
        Generate learner trajectory visualization.
        
        Args:
            user_id: User ID
            trajectory_data: Raw trajectory data
            
        Returns:
            TrajectoryVisualization with processed data
        """
        logger.info(f"🔄 Generating trajectory visualization for user {user_id}")
        
        viz = TrajectoryVisualization(
            user_id=user_id,
            visualization_type=VisualizationType.LEARNER_TRAJECTORY
        )
        
        # Process data points
        for point in trajectory_data:
            viz.data_points.append(TrajectoryDataPoint(
                timestamp=point.get("timestamp", datetime.utcnow()),
                mastery=point.get("mastery", 0.5),
                uncertainty=point.get("uncertainty", 0.3),
                zpd_score=point.get("zpd_score", 0.4),
                concept_id=point.get("concept_id"),
                adaptation_type=point.get("adaptation_type"),
                policy_version=point.get("policy_version")
            ))
        
        # Compute summary metrics
        viz.total_points = len(viz.data_points)
        if viz.data_points:
            timestamps = [p.timestamp for p in viz.data_points if p.timestamp]
            if timestamps:
                viz.time_span_days = (max(timestamps) - min(timestamps)).days
            masteries = [p.mastery for p in viz.data_points]
            viz.mastery_range = (min(masteries), max(masteries))
        
        logger.info(f"✅ Trajectory visualization generated: {viz.total_points} points")
        
        return viz
    
    def generate_replay_comparison(
        self,
        user_id: str,
        original_trajectory: List[Dict[str, Any]],
        replay_trajectory: List[Dict[str, Any]]
    ) -> TrajectoryVisualization:
        """
        Generate replay comparison visualization.
        
        Args:
            user_id: User ID
            original_trajectory: Original trajectory data
            replay_trajectory: Replay trajectory data
            
        Returns:
            TrajectoryVisualization with comparison data
        """
        logger.info(f"🔄 Generating replay comparison for user {user_id}")
        
        viz = TrajectoryVisualization(
            user_id=user_id,
            visualization_type=VisualizationType.REPLAY_COMPARISON
        )
        
        # Process both trajectories
        for point in original_trajectory:
            viz.data_points.append(TrajectoryDataPoint(
                timestamp=point.get("timestamp", datetime.utcnow()),
                mastery=point.get("mastery", 0.5),
                uncertainty=point.get("uncertainty", 0.3),
                zpd_score=point.get("zpd_score", 0.4),
                concept_id=point.get("concept_id"),
                adaptation_type=point.get("adaptation_type"),
                policy_version="original"
            ))
        
        for point in replay_trajectory:
            viz.data_points.append(TrajectoryDataPoint(
                timestamp=point.get("timestamp", datetime.utcnow()),
                mastery=point.get("mastery", 0.5),
                uncertainty=point.get("uncertainty", 0.3),
                zpd_score=point.get("zpd_score", 0.4),
                concept_id=point.get("concept_id"),
                adaptation_type=point.get("adaptation_type"),
                policy_version="replay"
            ))
        
        viz.total_points = len(viz.data_points)
        
        # Add key event annotations
        viz.key_events = [
            {"type": "replay_start", "timestamp": datetime.utcnow()},
            {"type": "replay_end", "timestamp": datetime.utcnow()}
        ]
        
        logger.info(f"✅ Replay comparison generated: {viz.total_points} points")
        
        return viz
    
    def generate_semantic_drift_viz(
        self,
        user_id: str,
        drift_data: List[Dict[str, Any]]
    ) -> TrajectoryVisualization:
        """
        Generate semantic drift visualization.
        
        Args:
            user_id: User ID
            drift_data: Semantic drift data
            
        Returns:
            TrajectoryVisualization with drift data
        """
        logger.info(f"🔄 Generating semantic drift visualization for user {user_id}")
        
        viz = TrajectoryVisualization(
            user_id=user_id,
            visualization_type=VisualizationType.SEMANTIC_DRIFT
        )
        
        for point in drift_data:
            viz.data_points.append(TrajectoryDataPoint(
                timestamp=point.get("timestamp", datetime.utcnow()),
                mastery=point.get("drift_magnitude", 0.0),
                uncertainty=0.0,
                zpd_score=0.0,
                concept_id=point.get("concept_id"),
                adaptation_type=point.get("drift_type"),
                policy_version=point.get("policy_version")
            ))
        
        viz.total_points = len(viz.data_points)
        
        logger.info(f"✅ Semantic drift visualization generated: {viz.total_points} points")
        
        return viz
    
    def generate_comprehensive_report(
        self,
        user_id: str,
        trajectory_data: List[Dict[str, Any]]
    ) -> ResearchObservabilityReport:
        """
        Generate comprehensive research observability report.
        
        Args:
            user_id: User ID
            trajectory_data: Trajectory data
            
        Returns:
            ResearchObservabilityReport with all visualizations
        """
        logger.info(f"🔄 Generating comprehensive observability report for user {user_id}")
        
        report = ResearchObservabilityReport(
            user_id=user_id,
            generated_at=datetime.utcnow()
        )
        
        # Generate learner trajectory visualization
        report.learner_trajectory = self.generate_trajectory_visualization(
            user_id,
            trajectory_data
        )
        
        # Generate pacing evolution visualization
        report.pacing_evolution = self.generate_trajectory_visualization(
            user_id,
            trajectory_data
        )
        report.pacing_evolution.visualization_type = VisualizationType.PACING_EVOLUTION
        
        # Generate adaptation lineage visualization
        report.adaptation_lineage = self.generate_trajectory_visualization(
            user_id,
            trajectory_data
        )
        report.adaptation_lineage.visualization_type = VisualizationType.ADAPTATION_LINEAGE
        
        # Count total visualizations
        report.total_visualizations = sum(
            1 for viz in [
                report.learner_trajectory,
                report.pacing_evolution,
                report.adaptation_lineage
            ] if viz is not None
        )
        
        # Compute data quality score
        if report.learner_trajectory:
            report.data_quality_score = min(
                report.learner_trajectory.total_points / 10.0,
                1.0
            )
        
        logger.info(f"✅ Comprehensive report generated: {report.total_visualizations} visualizations")
        
        return report
