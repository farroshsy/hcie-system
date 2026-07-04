"""
C2.2.1 - Semantic Trajectory Queries Tests

Tests for extracting learner learning trajectories from persisted events.
Focus on pedagogical semantic trajectories (learning), NOT infrastructure metrics (machines).
"""

import pytest
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.analytics.semantic_trajectory_queries import (
    TrajectoryPoint,
    ConceptProgression,
    LearnerTrajectory,
    SemanticTrajectoryQueries
)


class MockDBStore:
    """Mock database store for testing."""
    
    def __init__(self):
        self.data = {}
    
    def fetch_all(self, query, params):
        """Return mock data based on query."""
        query_lower = query.lower()
        if "mastery" in query_lower and "evolution" in query_lower:
            return self._mock_mastery_evolution(params.get("user_id"))
        elif "concept" in query_lower and "progression" in query_lower:
            return self._mock_concept_progression(params.get("user_id"))
        elif "pacing" in query_lower and "patterns" in query_lower:
            return self._mock_pacing_patterns(params.get("user_id"))
        elif "misconception" in query_lower and "recurrence" in query_lower:
            return self._mock_misconception_recurrence(params.get("user_id"))
        elif "adaptation" in query_lower and "effectiveness" in query_lower:
            return self._mock_adaptation_effectiveness(params.get("user_id"))
        return []
    
    def _mock_mastery_evolution(self, user_id):
        """Mock mastery evolution data."""
        return [
            {
                "timestamp": datetime.now() - timedelta(days=2),
                "user_id": user_id,
                "concept_id": "binary_search",
                "mastery": 0.3,
                "uncertainty": 0.5,
                "zpd_score": 0.4,
                "session_id": "session_001",
                "task_id": "task_001",
                "adaptation_type": "remediation",
                "policy_version": "v1.0.0",
                "experiment_id": "exp_001"
            },
            {
                "timestamp": datetime.now() - timedelta(days=1),
                "user_id": user_id,
                "concept_id": "binary_search",
                "mastery": 0.6,
                "uncertainty": 0.3,
                "zpd_score": 0.7,
                "session_id": "session_001",
                "task_id": "task_002",
                "adaptation_type": None,
                "policy_version": "v1.0.0",
                "experiment_id": "exp_001"
            },
            {
                "timestamp": datetime.now(),
                "user_id": user_id,
                "concept_id": "binary_search",
                "mastery": 0.8,
                "uncertainty": 0.2,
                "zpd_score": 0.85,
                "session_id": "session_002",
                "task_id": "task_003",
                "adaptation_type": "difficulty_shift",
                "policy_version": "v1.0.0",
                "experiment_id": "exp_001"
            }
        ]
    
    def _mock_concept_progression(self, user_id):
        """Mock concept progression data."""
        return [
            {
                "concept_id": "binary_search",
                "user_id": user_id,
                "first_encounter": datetime.now() - timedelta(days=2),
                "last_encounter": datetime.now(),
                "initial_mastery": 0.3,
                "final_mastery": 0.8,
                "total_attempts": 10,
                "successful_attempts": 7,
                "adaptations_received": 3,
                "misconception_count": 2
            }
        ]
    
    def _mock_pacing_patterns(self, user_id):
        """Mock pacing patterns data."""
        return [
            {
                "session_id": "session_001",
                "user_id": user_id,
                "started_at": datetime.now() - timedelta(days=2),
                "completed_at": datetime.now() - timedelta(days=2, hours=-1),
                "tasks_completed": 5,
                "session_duration_minutes": 60,
                "tasks_per_minute": 0.083,
                "adaptations_in_session": 2
            },
            {
                "session_id": "session_002",
                "user_id": user_id,
                "started_at": datetime.now() - timedelta(days=1),
                "completed_at": datetime.now() - timedelta(days=1, hours=-0.5),
                "tasks_completed": 7,
                "session_duration_minutes": 30,
                "tasks_per_minute": 0.233,
                "adaptations_in_session": 1
            }
        ]
    
    def _mock_misconception_recurrence(self, user_id):
        """Mock misconception recurrence data."""
        return [
            {
                "misconception_id": "off_by_one",
                "user_id": user_id,
                "occurrence_count": 3,
                "first_occurrence": datetime.now() - timedelta(days=2),
                "last_occurrence": datetime.now() - timedelta(days=1),
                "sessions_affected": 2,
                "accuracy_after_misconception": 0.4
            }
        ]
    
    def _mock_adaptation_effectiveness(self, user_id):
        """Mock adaptation effectiveness data."""
        return [
            {
                "adaptation_type": "remediation",
                "policy_version": "v1.0.0",
                "experiment_id": "exp_001",
                "user_id": user_id,
                "adaptation_count": 2,
                "post_adaptation_accuracy": 0.7,
                "average_mastery_after": 0.6,
                "average_uncertainty_after": 0.3
            }
        ]


class TestTrajectoryPoint:
    """Test TrajectoryPoint dataclass."""
    
    def test_trajectory_point_creation(self):
        """Test creating a trajectory point."""
        point = TrajectoryPoint(
            timestamp=datetime.now(),
            user_id="user_001",
            concept_id="binary_search",
            mastery=0.7,
            uncertainty=0.3,
            zpd_score=0.75,
            session_id="session_001",
            task_id="task_001",
            adaptation_type="remediation",
            policy_version="v1.0.0",
            experiment_id="exp_001"
        )
        
        assert point.user_id == "user_001"
        assert point.concept_id == "binary_search"
        assert point.mastery == 0.7
        assert point.adaptation_type == "remediation"


class TestConceptProgression:
    """Test ConceptProgression dataclass."""
    
    def test_concept_progression_creation(self):
        """Test creating a concept progression."""
        progression = ConceptProgression(
            concept_id="binary_search",
            user_id="user_001",
            first_encounter=datetime.now() - timedelta(days=2),
            last_encounter=datetime.now(),
            initial_mastery=0.3,
            final_mastery=0.8,
            mastery_growth=0.5,
            total_attempts=10,
            successful_attempts=7,
            adaptations_received=3,
            misconception_count=2,
            pacing_changes=1
        )
        
        assert progression.concept_id == "binary_search"
        assert progression.mastery_growth == 0.5
        assert progression.total_attempts == 10
        assert progression.successful_attempts == 7


class TestLearnerTrajectory:
    """Test LearnerTrajectory dataclass."""
    
    def test_learner_trajectory_creation(self):
        """Test creating a learner trajectory."""
        trajectory = LearnerTrajectory(
            user_id="user_001",
            trajectory_points=[],
            concept_progressions={},
            total_sessions=5,
            total_attempts=50,
            total_adaptations=10,
            overall_mastery_growth=0.5,
            pacing_stability_score=0.3,
            adaptation_effectiveness_score=0.8
        )
        
        assert trajectory.user_id == "user_001"
        assert trajectory.total_sessions == 5
        assert trajectory.overall_mastery_growth == 0.5
        assert trajectory.adaptation_effectiveness_score == 0.8


class TestSemanticTrajectoryQueries:
    """Test SemanticTrajectoryQueries class."""
    
    def test_extract_learner_trajectory(self):
        """Test extracting complete learner trajectory."""
        mock_db = MockDBStore()
        queries = SemanticTrajectoryQueries(db_store=mock_db)
        
        trajectory = queries.extract_learner_trajectory("user_001")
        
        assert trajectory.user_id == "user_001"
        assert len(trajectory.trajectory_points) == 3
        assert len(trajectory.concept_progressions) == 1
        assert trajectory.total_sessions == 2  # session_001 and session_002
        assert trajectory.total_attempts == 3
        assert trajectory.total_adaptations == 2
        assert trajectory.overall_mastery_growth > 0
    
    def test_extract_mastery_evolution(self):
        """Test extracting mastery evolution over time."""
        mock_db = MockDBStore()
        queries = SemanticTrajectoryQueries(db_store=mock_db)
        
        points = queries._extract_mastery_evolution("user_001")
        
        assert len(points) == 3
        assert points[0].mastery == 0.3
        assert points[1].mastery == 0.6
        assert points[2].mastery == 0.8
        assert points[0].timestamp < points[1].timestamp < points[2].timestamp
    
    def test_extract_concept_progressions(self):
        """Test extracting concept progressions."""
        mock_db = MockDBStore()
        queries = SemanticTrajectoryQueries(db_store=mock_db)
        
        progressions = queries._extract_concept_progressions("user_001")
        
        assert len(progressions) == 1
        assert "binary_search" in progressions
        assert progressions["binary_search"].initial_mastery == 0.3
        assert progressions["binary_search"].final_mastery == 0.8
        assert progressions["binary_search"].mastery_growth == 0.5
    
    def test_calculate_pacing_stability(self):
        """Test calculating pacing stability score."""
        mock_db = MockDBStore()
        queries = SemanticTrajectoryQueries(db_store=mock_db)
        
        stability_score = queries._calculate_pacing_stability("user_001")
        
        assert 0 <= stability_score <= 1
        # With variation in tasks_per_minute (0.083 vs 0.233), score should be > 0
        assert stability_score > 0
    
    def test_calculate_adaptation_effectiveness(self):
        """Test calculating adaptation effectiveness score."""
        mock_db = MockDBStore()
        queries = SemanticTrajectoryQueries(db_store=mock_db)
        
        effectiveness_score = queries._calculate_adaptation_effectiveness("user_001")
        
        assert 0 <= effectiveness_score <= 1
        # With post_adaptation_accuracy 0.7 and mastery_after 0.6, score should be ~0.65
        assert effectiveness_score > 0.5
    
    def test_extract_misconception_recurrence(self):
        """Test extracting misconception recurrence patterns."""
        mock_db = MockDBStore()
        queries = SemanticTrajectoryQueries(db_store=mock_db)
        
        recurrence_patterns = queries.extract_misconception_recurrence("user_001")
        
        assert len(recurrence_patterns) == 1
        assert recurrence_patterns[0]["misconception_id"] == "off_by_one"
        assert recurrence_patterns[0]["occurrence_count"] == 3
        assert recurrence_patterns[0]["sessions_affected"] == 2
    
    def test_no_database_store(self):
        """Test behavior when no database store is provided."""
        queries = SemanticTrajectoryQueries(db_store=None)
        
        trajectory = queries.extract_learner_trajectory("user_001")
        
        assert trajectory.user_id == "user_001"
        assert len(trajectory.trajectory_points) == 0
        assert len(trajectory.concept_progressions) == 0
        assert trajectory.total_sessions == 0
        assert trajectory.total_attempts == 0
        assert trajectory.total_adaptations == 0
    
    def test_trajectory_point_ordering(self):
        """Test that trajectory points are ordered by timestamp."""
        mock_db = MockDBStore()
        queries = SemanticTrajectoryQueries(db_store=mock_db)
        
        points = queries._extract_mastery_evolution("user_001")
        
        for i in range(len(points) - 1):
            assert points[i].timestamp < points[i + 1].timestamp
    
    def test_concept_progression_mastery_growth_calculation(self):
        """Test that mastery growth is calculated correctly."""
        mock_db = MockDBStore()
        queries = SemanticTrajectoryQueries(db_store=mock_db)
        
        progressions = queries._extract_concept_progressions("user_001")
        
        progression = progressions["binary_search"]
        assert progression.mastery_growth == progression.final_mastery - progression.initial_mastery
        assert progression.mastery_growth == 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
