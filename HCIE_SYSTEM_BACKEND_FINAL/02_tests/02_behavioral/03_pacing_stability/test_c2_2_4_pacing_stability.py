"""
C2.2.4 - Pacing Stability Analysis Tests

Tests for measuring pacing stability across sessions, identifying pacing oscillation,
and measuring pacing adaptation effectiveness on learner engagement.

Focus on pedagogical semantic trajectories (learning), NOT infrastructure metrics (machines).
"""

import pytest
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.analytics.pacing_stability import (
    PacingStabilityLevel,
    SessionPacingMetrics,
    PacingOscillationPattern,
    PacingStabilityReport,
    PacingStabilityAnalyzer
)


class MockDBStore:
    """Mock database store for testing."""
    
    def __init__(self):
        self.data = {}
    
    def fetch_all(self, query, params):
        """Return mock data based on query."""
        query_lower = query.lower()
        
        if "session" in query_lower and "pacing" in query_lower and ":user_id" in query_lower:
            return self._mock_session_pacing_metrics(params.get("user_id"))
        elif "group" in query_lower and "pacing" in query_lower:
            return self._mock_group_pacing_metrics()
        elif "correlation" in query_lower:
            return self._mock_pacing_correlation_data()
        return []
    
    def _mock_session_pacing_metrics(self, user_id):
        """Mock session pacing metrics data."""
        return [
            {
                "session_id": "session_001",
                "user_id": user_id,
                "started_at": datetime.now() - timedelta(days=3),
                "completed_at": datetime.now() - timedelta(days=3, hours=-1),
                "tasks_completed": 8,
                "total_duration_minutes": 60.0,
                "avg_task_duration": 7.5,
                "task_duration_stddev": 1.2,
                "min_task_duration": 5.0,
                "max_task_duration": 10.0,
                "pacing_adaptation_count": 1,
                "pacing_adjustment_type": "pacing_adjustment"
            },
            {
                "session_id": "session_002",
                "user_id": user_id,
                "started_at": datetime.now() - timedelta(days=2),
                "completed_at": datetime.now() - timedelta(days=2, hours=-0.5),
                "tasks_completed": 10,
                "total_duration_minutes": 50.0,
                "avg_task_duration": 5.0,
                "task_duration_stddev": 0.8,
                "min_task_duration": 4.0,
                "max_task_duration": 6.0,
                "pacing_adaptation_count": 0,
                "pacing_adjustment_type": None
            },
            {
                "session_id": "session_003",
                "user_id": user_id,
                "started_at": datetime.now() - timedelta(days=1),
                "completed_at": datetime.now() - timedelta(days=1, hours=-1.5),
                "tasks_completed": 6,
                "total_duration_minutes": 90.0,
                "avg_task_duration": 15.0,
                "task_duration_stddev": 3.0,
                "min_task_duration": 10.0,
                "max_task_duration": 20.0,
                "pacing_adaptation_count": 2,
                "pacing_adjustment_type": "pacing_adjustment"
            }
        ]
    
    def _mock_group_pacing_metrics(self):
        """Mock group pacing metrics data."""
        return [
            {
                "user_id": "user_001",
                "total_sessions": 5,
                "avg_session_duration": 60.0,
                "session_duration_stddev": 10.0,
                "avg_tasks_completed": 8,
                "pacing_adaptation_count": 3
            },
            {
                "user_id": "user_002",
                "total_sessions": 3,
                "avg_session_duration": 50.0,
                "session_duration_stddev": 5.0,
                "avg_tasks_completed": 10,
                "pacing_adaptation_count": 1
            },
            {
                "user_id": "user_003",
                "total_sessions": 4,
                "avg_session_duration": 70.0,
                "session_duration_stddev": 25.0,
                "avg_tasks_completed": 6,
                "pacing_adaptation_count": 4
            }
        ]
    
    def _mock_pacing_correlation_data(self):
        """Mock pacing-engagement correlation data."""
        return [
            {
                "session_id": "session_001",
                "user_id": "user_001",
                "tasks_completed": 8,
                "session_duration": 60.0,
                "task_duration_stddev": 1.2,
                "accuracy": 0.8
            },
            {
                "session_id": "session_002",
                "user_id": "user_001",
                "tasks_completed": 10,
                "session_duration": 50.0,
                "task_duration_stddev": 0.8,
                "accuracy": 0.9
            },
            {
                "session_id": "session_003",
                "user_id": "user_002",
                "tasks_completed": 6,
                "session_duration": 90.0,
                "task_duration_stddev": 3.0,
                "accuracy": 0.6
            }
        ]


class TestPacingStabilityLevel:
    """Test PacingStabilityLevel enum."""
    
    def test_stability_values(self):
        """Test that stability enum has expected values."""
        assert PacingStabilityLevel.STABLE.value == "stable"
        assert PacingStabilityLevel.MODERATELY_STABLE.value == "moderately_stable"
        assert PacingStabilityLevel.UNSTABLE.value == "unstable"
        assert PacingStabilityLevel.HIGHLY_UNSTABLE.value == "highly_unstable"


class TestSessionPacingMetrics:
    """Test SessionPacingMetrics dataclass."""
    
    def test_session_pacing_metrics_creation(self):
        """Test creating session pacing metrics."""
        metrics = SessionPacingMetrics(
            session_id="session_001",
            user_id="user_001",
            started_at=datetime.now(),
            completed_at=datetime.now() + timedelta(hours=1),
            tasks_completed=10,
            total_session_duration_minutes=60.0,
            average_task_duration_minutes=6.0,
            task_duration_std_dev=1.5,
            min_task_duration_minutes=4.0,
            max_task_duration_minutes=10.0,
            pacing_adaptation_count=1,
            pacing_adjustment_type="pacing_adjustment",
            engagement_score=0.8,
            completion_rate=1.0
        )
        
        assert metrics.session_id == "session_001"
        assert metrics.engagement_score == 0.8
        assert metrics.pacing_adaptation_count == 1


class TestPacingOscillationPattern:
    """Test PacingOscillationPattern dataclass."""
    
    def test_oscillation_pattern_creation(self):
        """Test creating oscillation pattern."""
        pattern = PacingOscillationPattern(
            user_id="user_001",
            oscillation_count=3,
            oscillation_amplitude_avg=5.0,
            oscillation_frequency_per_hour=1.5,
            is_oscillating=True,
            oscillation_severity=PacingStabilityLevel.UNSTABLE,
            total_sessions_analyzed=5,
            sessions_with_oscillation=3
        )
        
        assert pattern.user_id == "user_001"
        assert pattern.is_oscillating == True
        assert pattern.oscillation_severity == PacingStabilityLevel.UNSTABLE


class TestPacingStabilityReport:
    """Test PacingStabilityReport dataclass."""
    
    def test_report_creation(self):
        """Test creating pacing stability report."""
        report = PacingStabilityReport(
            total_sessions=10,
            stable_sessions=7,
            unstable_sessions=3,
            average_pacing_stability_score=0.7,
            oscillating_users=2,
            average_oscillation_severity=0.5,
            sessions_with_pacing_adaptations=4,
            pacing_adaptation_effectiveness=0.75,
            pacing_engagement_correlation=-0.3,
            pacing_completion_correlation=-0.2
        )
        
        assert report.total_sessions == 10
        assert report.average_pacing_stability_score == 0.7
        assert report.pacing_adaptation_effectiveness == 0.75


class TestPacingStabilityAnalyzer:
    """Test PacingStabilityAnalyzer class."""
    
    def test_analyze_session_pacing(self):
        """Test analyzing pacing metrics for a user."""
        mock_db = MockDBStore()
        analyzer = PacingStabilityAnalyzer(db_store=mock_db)
        
        metrics = analyzer.analyze_session_pacing(user_id="user_001")
        
        assert len(metrics) == 3
        assert metrics[0].session_id == "session_001"
        assert metrics[0].tasks_completed == 8
        assert metrics[0].pacing_adaptation_count == 1
    
    def test_engagement_score_calculation(self):
        """Test engagement score calculation."""
        mock_db = MockDBStore()
        analyzer = PacingStabilityAnalyzer(db_store=mock_db)
        
        metrics = analyzer.analyze_session_pacing(user_id="user_001")
        
        # Engagement score should be between 0 and 1
        for metric in metrics:
            assert 0 <= metric.engagement_score <= 1
    
    def test_completion_rate_calculation(self):
        """Test completion rate calculation."""
        mock_db = MockDBStore()
        analyzer = PacingStabilityAnalyzer(db_store=mock_db)
        
        metrics = analyzer.analyze_session_pacing(user_id="user_001")
        
        # Completion rate should be between 0 and 1
        for metric in metrics:
            assert 0 <= metric.completion_rate <= 1
    
    def test_detect_pacing_oscillation(self):
        """Test detecting pacing oscillation patterns."""
        mock_db = MockDBStore()
        analyzer = PacingStabilityAnalyzer(db_store=mock_db)
        
        pattern = analyzer.detect_pacing_oscillation(user_id="user_001")
        
        assert pattern.user_id == "user_001"
        assert pattern.total_sessions_analyzed == 3
        assert pattern.oscillation_count >= 0
    
    def test_oscillation_severity_determination(self):
        """Test oscillation severity determination."""
        mock_db = MockDBStore()
        analyzer = PacingStabilityAnalyzer(db_store=mock_db)
        
        pattern = analyzer.detect_pacing_oscillation(user_id="user_001")
        
        # Severity should be one of the enum values
        assert isinstance(pattern.oscillation_severity, PacingStabilityLevel)
    
    def test_insufficient_sessions_for_oscillation(self):
        """Test oscillation detection with insufficient sessions."""
        mock_db = MockDBStore()
        # Modify mock to return only 1 session
        mock_db.fetch_all = lambda query, params: mock_db._mock_session_pacing_metrics("user_001")[:1]
        
        analyzer = PacingStabilityAnalyzer(db_store=mock_db)
        pattern = analyzer.detect_pacing_oscillation(user_id="user_001")
        
        assert pattern.is_oscillating == False
        assert pattern.oscillation_severity == PacingStabilityLevel.STABLE
    
    def test_generate_pacing_stability_report(self):
        """Test generating aggregate pacing stability report."""
        mock_db = MockDBStore()
        analyzer = PacingStabilityAnalyzer(db_store=mock_db)
        
        report = analyzer.generate_pacing_stability_report()
        
        assert report.total_sessions == 12  # 5 + 3 + 4
        assert report.stable_sessions >= 0
        assert report.unstable_sessions >= 0
        assert 0 <= report.average_pacing_stability_score <= 1
    
    def test_oscillation_detection_in_report(self):
        """Test oscillation detection in aggregate report."""
        mock_db = MockDBStore()
        analyzer = PacingStabilityAnalyzer(db_store=mock_db)
        
        report = analyzer.generate_pacing_stability_report()
        
        assert report.oscillating_users >= 0
        assert 0 <= report.average_oscillation_severity <= 1
    
    def test_pacing_adaptation_effectiveness(self):
        """Test pacing adaptation effectiveness calculation."""
        mock_db = MockDBStore()
        analyzer = PacingStabilityAnalyzer(db_store=mock_db)
        
        report = analyzer.generate_pacing_stability_report()
        
        # Should have pacing adaptation effectiveness
        assert 0 <= report.pacing_adaptation_effectiveness <= 1
        assert report.sessions_with_pacing_adaptations >= 0
    
    def test_correlation_calculations(self):
        """Test correlation calculations in report."""
        mock_db = MockDBStore()
        analyzer = PacingStabilityAnalyzer(db_store=mock_db)
        
        report = analyzer.generate_pacing_stability_report()
        
        # Correlation should be between -1 and 1
        assert -1 <= report.pacing_engagement_correlation <= 1
        assert -1 <= report.pacing_completion_correlation <= 1
    
    def test_no_database_store(self):
        """Test behavior when no database store is provided."""
        analyzer = PacingStabilityAnalyzer(db_store=None)
        
        metrics = analyzer.analyze_session_pacing(user_id="user_001")
        
        assert len(metrics) == 0
    
    def test_empty_report_when_no_data(self):
        """Test empty report when no data is available."""
        mock_db = MockDBStore()
        # Modify mock to return empty results
        mock_db.fetch_all = lambda query, params: []
        
        analyzer = PacingStabilityAnalyzer(db_store=mock_db)
        report = analyzer.generate_pacing_stability_report()
        
        assert report.total_sessions == 0
        assert report.average_pacing_stability_score == 0.0
    
    def test_correlation_calculation_with_insufficient_data(self):
        """Test correlation calculation with insufficient data."""
        analyzer = PacingStabilityAnalyzer(db_store=None)
        
        correlation = analyzer._calculate_correlation(
            [{"x": 1, "y": 2}],
            "x",
            "y"
        )
        
        # Should return 0 for insufficient data
        assert correlation == 0.0
    
    def test_correlation_calculation_with_zero_std(self):
        """Test correlation calculation when standard deviation is zero."""
        analyzer = PacingStabilityAnalyzer(db_store=None)
        
        # All x values are the same, std_x = 0
        correlation = analyzer._calculate_correlation(
            [{"x": 1, "y": 2}, {"x": 1, "y": 3}],
            "x",
            "y"
        )
        
        # Should return 0 when std is zero
        assert correlation == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
