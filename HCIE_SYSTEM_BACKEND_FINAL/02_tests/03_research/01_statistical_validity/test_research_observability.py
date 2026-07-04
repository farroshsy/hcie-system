"""
Research Observability Tests

Tests for learner trajectory explorer and semantic trajectory visualizations.

Focus on pedagogical semantic trajectories (learning), NOT infrastructure replay.
"""

import pytest
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.research.observability import (
    VisualizationType,
    TrajectoryDataPoint,
    TrajectoryVisualization,
    ResearchObservabilityReport,
    ResearchObservabilityService
)


class TestVisualizationType:
    """Test VisualizationType enum."""
    
    def test_visualization_type_values(self):
        """Test that visualization type enum has expected values."""
        assert VisualizationType.LEARNER_TRAJECTORY.value == "learner_trajectory"
        assert VisualizationType.REPLAY_COMPARISON.value == "replay_comparison"
        assert VisualizationType.SEMANTIC_DRIFT.value == "semantic_drift"
        assert VisualizationType.ADAPTATION_LINEAGE.value == "adaptation_lineage"
        assert VisualizationType.PACING_EVOLUTION.value == "pacing_evolution"
        assert VisualizationType.MISCONCEPTION_EVOLUTION.value == "misconception_evolution"


class TestTrajectoryDataPoint:
    """Test TrajectoryDataPoint dataclass."""
    
    def test_trajectory_data_point_creation(self):
        """Test creating trajectory data point."""
        point = TrajectoryDataPoint(
            timestamp=datetime.now(),
            mastery=0.7,
            uncertainty=0.3,
            zpd_score=0.5,
            concept_id="binary_search",
            adaptation_type="remediation",
            policy_version="v1.0.0"
        )
        
        assert point.mastery == 0.7
        assert point.concept_id == "binary_search"
        assert point.adaptation_type == "remediation"


class TestTrajectoryVisualization:
    """Test TrajectoryVisualization dataclass."""
    
    def test_trajectory_visualization_creation(self):
        """Test creating trajectory visualization."""
        viz = TrajectoryVisualization(
            user_id="user_001",
            visualization_type=VisualizationType.LEARNER_TRAJECTORY
        )
        
        assert viz.user_id == "user_001"
        assert viz.visualization_type == VisualizationType.LEARNER_TRAJECTORY
        assert viz.total_points == 0


class TestResearchObservabilityReport:
    """Test ResearchObservabilityReport dataclass."""
    
    def test_report_creation(self):
        """Test creating research observability report."""
        report = ResearchObservabilityReport(
            user_id="user_001",
            generated_at=datetime.now()
        )
        
        assert report.user_id == "user_001"
        assert report.total_visualizations == 0
        assert report.data_quality_score == 1.0


class TestResearchObservabilityService:
    """Test ResearchObservabilityService class."""
    
    def test_service_initialization(self):
        """Test service initialization."""
        service = ResearchObservabilityService()
        
        assert service is not None
    
    def test_generate_trajectory_visualization(self):
        """Test generating learner trajectory visualization."""
        service = ResearchObservabilityService()
        
        trajectory_data = [
            {
                "timestamp": datetime.now() - timedelta(days=10),
                "mastery": 0.5,
                "uncertainty": 0.3,
                "zpd_score": 0.4,
                "concept_id": "binary_search",
                "adaptation_type": "remediation",
                "policy_version": "v1.0.0"
            },
            {
                "timestamp": datetime.now(),
                "mastery": 0.7,
                "uncertainty": 0.2,
                "zpd_score": 0.6,
                "concept_id": "sorting",
                "adaptation_type": "difficulty_shift",
                "policy_version": "v1.1.0"
            }
        ]
        
        viz = service.generate_trajectory_visualization("user_001", trajectory_data)
        
        assert viz.user_id == "user_001"
        assert viz.visualization_type == VisualizationType.LEARNER_TRAJECTORY
        assert viz.total_points == 2
        assert viz.time_span_days == 10
        assert viz.mastery_range == (0.5, 0.7)
        assert len(viz.data_points) == 2
    
    def test_generate_trajectory_visualization_empty(self):
        """Test generating trajectory visualization with empty data."""
        service = ResearchObservabilityService()
        
        viz = service.generate_trajectory_visualization("user_001", [])
        
        assert viz.user_id == "user_001"
        assert viz.total_points == 0
        assert viz.time_span_days == 0
    
    def test_generate_replay_comparison(self):
        """Test generating replay comparison visualization."""
        service = ResearchObservabilityService()
        
        original_trajectory = [
            {
                "timestamp": datetime.now(),
                "mastery": 0.6,
                "uncertainty": 0.3,
                "zpd_score": 0.5,
                "concept_id": "binary_search",
                "adaptation_type": "remediation"
            }
        ]
        
        replay_trajectory = [
            {
                "timestamp": datetime.now(),
                "mastery": 0.7,
                "uncertainty": 0.2,
                "zpd_score": 0.6,
                "concept_id": "binary_search",
                "adaptation_type": "difficulty_shift"
            }
        ]
        
        viz = service.generate_replay_comparison(
            "user_001",
            original_trajectory,
            replay_trajectory
        )
        
        assert viz.user_id == "user_001"
        assert viz.visualization_type == VisualizationType.REPLAY_COMPARISON
        assert viz.total_points == 2
        assert len(viz.key_events) == 2
        assert viz.key_events[0]["type"] == "replay_start"
        assert viz.key_events[1]["type"] == "replay_end"
    
    def test_generate_semantic_drift_viz(self):
        """Test generating semantic drift visualization."""
        service = ResearchObservabilityService()
        
        drift_data = [
            {
                "timestamp": datetime.now(),
                "drift_magnitude": 0.8,
                "drift_type": "adaptation_type",
                "concept_id": "binary_search",
                "policy_version": "v1.0.0"
            },
            {
                "timestamp": datetime.now(),
                "drift_magnitude": 0.5,
                "drift_type": "recommendation_semantics",
                "concept_id": "sorting",
                "policy_version": "v1.1.0"
            }
        ]
        
        viz = service.generate_semantic_drift_viz("user_001", drift_data)
        
        assert viz.user_id == "user_001"
        assert viz.visualization_type == VisualizationType.SEMANTIC_DRIFT
        assert viz.total_points == 2
        # drift_magnitude is stored in mastery field for visualization
        assert viz.data_points[0].mastery == 0.8
        assert viz.data_points[0].adaptation_type == "adaptation_type"
    
    def test_generate_comprehensive_report(self):
        """Test generating comprehensive observability report."""
        service = ResearchObservabilityService()
        
        trajectory_data = [
            {
                "timestamp": datetime.now(),
                "mastery": 0.6,
                "uncertainty": 0.3,
                "zpd_score": 0.5,
                "concept_id": "binary_search",
                "adaptation_type": "remediation",
                "policy_version": "v1.0.0"
            }
        ]
        
        report = service.generate_comprehensive_report("user_001", trajectory_data)
        
        assert report.user_id == "user_001"
        assert report.total_visualizations == 3
        assert report.learner_trajectory is not None
        assert report.pacing_evolution is not None
        assert report.adaptation_lineage is not None
        assert report.data_quality_score > 0  # Should be 0.1 for 1 point
        assert report.learner_trajectory.visualization_type == VisualizationType.LEARNER_TRAJECTORY
        assert report.pacing_evolution.visualization_type == VisualizationType.PACING_EVOLUTION
        assert report.adaptation_lineage.visualization_type == VisualizationType.ADAPTATION_LINEAGE


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
