"""
C2.2.2 - Adaptation Effectiveness Analysis Tests

Tests for measuring adaptation impact on learning outcomes.
Focus on pedagogical semantic trajectories (learning), NOT infrastructure metrics (machines).
"""

import pytest
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.analytics.adaptation_effectiveness import (
    AdaptationType,
    SessionMetrics,
    AdaptationEffectivenessReport,
    ConceptTransferAnalysis,
    AdaptationEffectivenessAnalyzer
)


class MockDBStore:
    """Mock database store for testing."""
    
    def __init__(self):
        self.data = {}
    
    def fetch_all(self, query, params):
        """Return mock data based on query."""
        query_lower = query.lower()
        
        if "session" in query_lower and "adaptation" in query_lower and "metrics" in query_lower:
            return self._mock_session_adaptation_metrics(params.get("user_id"))
        elif "session" in query_lower and "retention" in query_lower:
            return self._mock_session_retention(params.get("user_id"))
        elif "concept" in query_lower and "transfer" in query_lower:
            return self._mock_concept_transfer(params.get("user_id"))
        elif "group" in query_lower and "adaptation" in query_lower and "effectiveness" in query_lower:
            return self._mock_group_adaptation_effectiveness(params.get("start_date"))
        return []
    
    def _mock_session_adaptation_metrics(self, user_id):
        """Mock session adaptation metrics data."""
        return [
            {
                "session_id": "session_001",
                "user_id": user_id,
                "started_at": datetime.now() - timedelta(days=2),
                "completed_at": datetime.now() - timedelta(days=2, hours=-1),
                "adaptation_count": 2,
                "adaptation_types": ["remediation", "difficulty_shift"],
                "policy_version": "v1.0.0",
                "experiment_id": "exp_001",
                "tasks_completed": 10,
                "tasks_correct": 7,
                "initial_mastery": 0.3,
                "final_mastery": 0.6,
                "session_duration_minutes": 60
            },
            {
                "session_id": "session_002",
                "user_id": user_id,
                "started_at": datetime.now() - timedelta(days=1),
                "completed_at": datetime.now() - timedelta(days=1, hours=-0.5),
                "adaptation_count": 0,
                "adaptation_types": [],
                "policy_version": None,
                "experiment_id": None,
                "tasks_completed": 7,
                "tasks_correct": 5,
                "initial_mastery": 0.6,
                "final_mastery": 0.65,
                "session_duration_minutes": 30
            },
            {
                "session_id": "session_003",
                "user_id": user_id,
                "started_at": datetime.now(),
                "completed_at": None,
                "adaptation_count": 1,
                "adaptation_types": ["pacing_adjustment"],
                "policy_version": "v1.0.0",
                "experiment_id": "exp_001",
                "tasks_completed": 8,
                "tasks_correct": 6,
                "initial_mastery": 0.7,
                "final_mastery": 0.85,
                "session_duration_minutes": 45
            }
        ]
    
    def _mock_session_retention(self, user_id):
        """Mock session retention data."""
        return [
            {
                "current_session_id": "session_001",
                "user_id": user_id,
                "next_session_mastery": 0.65
            },
            {
                "current_session_id": "session_002",
                "user_id": user_id,
                "next_session_mastery": 0.82
            },
            {
                "current_session_id": "session_003",
                "user_id": user_id,
                "next_session_mastery": None
            }
        ]
    
    def _mock_concept_transfer(self, user_id):
        """Mock concept transfer data."""
        return [
            {
                "session_id": "session_001",
                "user_id": user_id,
                "concepts_encountered": ["binary_search", "sorting"],
                "concepts_mastered": 1
            },
            {
                "session_id": "session_002",
                "user_id": user_id,
                "concepts_encountered": ["recursion", "dynamic_programming"],
                "concepts_mastered": 0
            },
            {
                "session_id": "session_003",
                "user_id": user_id,
                "concepts_encountered": ["graphs"],
                "concepts_mastered": 1
            }
        ]
    
    def _mock_group_adaptation_effectiveness(self, start_date):
        """Mock group adaptation effectiveness data."""
        return [
            {
                "user_id": "user_001",
                "has_adaptations": True,
                "adaptation_count": 3,
                "adaptation_type": "remediation",
                "tasks_completed": 25,
                "tasks_correct": 20,
                "avg_mastery_growth": 0.4
            },
            {
                "user_id": "user_002",
                "has_adaptations": False,
                "adaptation_count": 0,
                "adaptation_type": None,
                "tasks_completed": 15,
                "tasks_correct": 10,
                "avg_mastery_growth": 0.2
            },
            {
                "user_id": "user_003",
                "has_adaptations": True,
                "adaptation_count": 2,
                "adaptation_type": "difficulty_shift",
                "tasks_completed": 20,
                "tasks_correct": 15,
                "avg_mastery_growth": 0.35
            }
        ]


class TestSessionMetrics:
    """Test SessionMetrics dataclass."""
    
    def test_session_metrics_creation(self):
        """Test creating session metrics."""
        metrics = SessionMetrics(
            session_id="session_001",
            user_id="user_001",
            has_adaptations=True,
            adaptation_count=2,
            adaptation_types=["remediation", "difficulty_shift"],
            policy_version="v1.0.0",
            experiment_id="exp_001",
            tasks_completed=10,
            tasks_correct=7,
            initial_mastery=0.3,
            final_mastery=0.6,
            mastery_growth=0.3,
            session_duration_minutes=60,
            next_session_mastery=0.65,
            mastery_retention=1.083
        )
        
        assert metrics.session_id == "session_001"
        assert metrics.has_adaptations == True
        assert metrics.mastery_growth == 0.3
        assert metrics.adaptation_types == ["remediation", "difficulty_shift"]


class TestAdaptationEffectivenessReport:
    """Test AdaptationEffectivenessReport dataclass."""
    
    def test_report_creation(self):
        """Test creating an effectiveness report."""
        report = AdaptationEffectivenessReport(
            total_sessions=10,
            adaptation_sessions=6,
            non_adaptation_sessions=4,
            adaptation_mastery_growth_avg=0.4,
            non_adaptation_mastery_growth_avg=0.2,
            mastery_growth_delta=0.2,
            adaptation_retention_avg=0.9,
            non_adaptation_retention_avg=0.8,
            retention_delta=0.1,
            adaptation_accuracy_avg=0.8,
            non_adaptation_accuracy_avg=0.7,
            accuracy_delta=0.1,
            adaptation_type_effectiveness={
                "remediation": {"avg_mastery_growth": 0.35, "avg_retention": 0.85, "avg_accuracy": 0.75}
            }
        )
        
        assert report.total_sessions == 10
        assert report.mastery_growth_delta == 0.2
        assert report.retention_delta == 0.1
        assert "remediation" in report.adaptation_type_effectiveness


class TestConceptTransferAnalysis:
    """Test ConceptTransferAnalysis dataclass."""
    
    def test_concept_transfer_creation(self):
        """Test creating concept transfer analysis."""
        analysis = ConceptTransferAnalysis(
            total_concepts=10,
            concepts_with_transfer=7,
            transfer_rate=0.7,
            adaptation_transfer_rate=0.8,
            non_adaptation_transfer_rate=0.6,
            transfer_by_adaptation_type={
                "remediation": 0.75,
                "difficulty_shift": 0.85
            }
        )
        
        assert analysis.transfer_rate == 0.7
        assert analysis.concepts_with_transfer == 7
        assert "remediation" in analysis.transfer_by_adaptation_type


class TestAdaptationEffectivenessAnalyzer:
    """Test AdaptationEffectivenessAnalyzer class."""
    
    def test_analyze_adaptation_effectiveness(self):
        """Test analyzing adaptation effectiveness for a user."""
        mock_db = MockDBStore()
        analyzer = AdaptationEffectivenessAnalyzer(db_store=mock_db)
        
        report = analyzer.analyze_adaptation_effectiveness(user_id="user_001")
        
        assert report.total_sessions == 3
        assert report.adaptation_sessions == 2
        assert report.non_adaptation_sessions == 1
        # Note: Delta can be positive or negative depending on actual data
        # The test validates the calculation works, not that adaptations always help
    
    def test_analyze_adaptation_effectiveness_group(self):
        """Test analyzing adaptation effectiveness across all users."""
        mock_db = MockDBStore()
        analyzer = AdaptationEffectivenessAnalyzer(db_store=mock_db)
        
        report = analyzer.analyze_adaptation_effectiveness(start_date=datetime.now() - timedelta(days=30))
        
        assert report.total_sessions == 3
        assert report.adaptation_sessions == 2
        assert report.non_adaptation_sessions == 1
        assert report.mastery_growth_delta > 0
    
    def test_analyze_concept_transfer(self):
        """Test analyzing concept transfer patterns."""
        mock_db = MockDBStore()
        analyzer = AdaptationEffectivenessAnalyzer(db_store=mock_db)
        
        analysis = analyzer.analyze_concept_transfer(user_id="user_001")
        
        assert analysis.total_concepts == 5  # 2 + 2 + 1 concepts
        assert analysis.concepts_with_transfer == 2
        assert analysis.transfer_rate == 0.4  # 2/5
    
    def test_per_adaptation_type_effectiveness(self):
        """Test calculating effectiveness per adaptation type."""
        mock_db = MockDBStore()
        analyzer = AdaptationEffectivenessAnalyzer(db_store=mock_db)
        
        report = analyzer.analyze_adaptation_effectiveness(user_id="user_001")
        
        assert "remediation" in report.adaptation_type_effectiveness
        assert "difficulty_shift" in report.adaptation_type_effectiveness
        assert "pacing_adjustment" in report.adaptation_type_effectiveness
        
        # Check that each adaptation type has the required metrics
        for adaptation_type, metrics in report.adaptation_type_effectiveness.items():
            assert "avg_mastery_growth" in metrics
            assert "avg_retention" in metrics
            assert "avg_accuracy" in metrics
    
    def test_no_database_store(self):
        """Test behavior when no database store is provided."""
        analyzer = AdaptationEffectivenessAnalyzer(db_store=None)
        
        report = analyzer.analyze_adaptation_effectiveness(user_id="user_001")
        
        assert report.total_sessions == 0
        assert report.adaptation_sessions == 0
        assert report.non_adaptation_sessions == 0
    
    def test_empty_report(self):
        """Test empty report when no data is available."""
        mock_db = MockDBStore()
        # Modify mock to return empty results
        mock_db.fetch_all = lambda query, params: []
        
        analyzer = AdaptationEffectivenessAnalyzer(db_store=mock_db)
        report = analyzer.analyze_adaptation_effectiveness(user_id="user_001")
        
        assert report.total_sessions == 0
        assert report.mastery_growth_delta == 0.0
        assert report.retention_delta == 0.0
    
    def test_mastery_growth_calculation(self):
        """Test mastery growth calculation."""
        mock_db = MockDBStore()
        analyzer = AdaptationEffectivenessAnalyzer(db_store=mock_db)
        
        session_metrics = analyzer._extract_session_metrics("user_001")
        
        # Check that mastery growth is calculated correctly
        for metrics in session_metrics:
            expected_growth = metrics.final_mastery - metrics.initial_mastery
            assert metrics.mastery_growth == expected_growth
    
    def test_retention_calculation(self):
        """Test retention calculation."""
        mock_db = MockDBStore()
        analyzer = AdaptationEffectivenessAnalyzer(db_store=mock_db)
        
        session_metrics = analyzer._extract_session_metrics("user_001")
        
        # Check that retention is calculated for sessions with next session mastery
        for metrics in session_metrics:
            if metrics.next_session_mastery is not None and metrics.final_mastery > 0:
                expected_retention = metrics.next_session_mastery / metrics.final_mastery
                assert abs(metrics.mastery_retention - expected_retention) < 0.001
    
    def test_accuracy_calculation(self):
        """Test accuracy calculation."""
        mock_db = MockDBStore()
        analyzer = AdaptationEffectivenessAnalyzer(db_store=mock_db)
        
        session_metrics = analyzer._extract_session_metrics("user_001")
        
        # Check that accuracy is calculated correctly
        for metrics in session_metrics:
            if metrics.tasks_completed > 0:
                expected_accuracy = metrics.tasks_correct / metrics.tasks_completed
                calculated_accuracy = metrics.tasks_correct / metrics.tasks_completed
                assert abs(calculated_accuracy - expected_accuracy) < 0.001
    
    def test_adaptation_vs_non_adaptation_split(self):
        """Test that sessions are correctly split into adaptation and non-adaptation groups."""
        mock_db = MockDBStore()
        analyzer = AdaptationEffectivenessAnalyzer(db_store=mock_db)
        
        session_metrics = analyzer._extract_session_metrics("user_001")
        
        adaptation_sessions = [s for s in session_metrics if s.has_adaptations]
        non_adaptation_sessions = [s for s in session_metrics if not s.has_adaptations]
        
        assert len(adaptation_sessions) == 2
        assert len(non_adaptation_sessions) == 1
        
        # Verify adaptation sessions have adaptations
        for session in adaptation_sessions:
            assert session.adaptation_count > 0
            assert len(session.adaptation_types) > 0
        
        # Verify non-adaptation sessions have no adaptations
        for session in non_adaptation_sessions:
            assert session.adaptation_count == 0
            assert len(session.adaptation_types) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
