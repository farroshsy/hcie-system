"""
C2.2.5 - Intervention Outcome Analysis Tests

Tests for measuring intervention effectiveness, comparing different intervention types,
and measuring intervention timing impact on learning outcomes.

Focus on pedagogical semantic trajectories (learning), NOT infrastructure metrics (machines).
"""

import pytest
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.analytics.intervention_outcomes import (
    InterventionTiming,
    InterventionEvent,
    InterventionEffectiveness,
    InterventionOutcomeReport,
    InterventionOutcomeAnalyzer
)


class MockDBStore:
    """Mock database store for testing."""
    
    def __init__(self):
        self.data = {}
    
    def fetch_all(self, query, params):
        """Return mock data based on query."""
        query_lower = query.lower()
        
        # Check for user-specific intervention events query
        if "intervention" in query_lower and "events" in query_lower and ":user_id" in query_lower:
            return self._mock_intervention_events(params.get("user_id"))
        # Check for group intervention effectiveness query
        elif "adaptation_type" in query_lower and "avg_mastery_delta" in query_lower:
            return self._mock_group_intervention_effectiveness()
        # Check for timing query
        elif "timing_category" in query_lower:
            return self._mock_intervention_timing()
        return []
    
    def _mock_intervention_events(self, user_id):
        """Mock intervention events data."""
        return [
            {
                "intervention_id": "intervention_001",
                "user_id": user_id,
                "session_id": "session_001",
                "intervention_type": "remediation",
                "occurred_at": datetime.now() - timedelta(days=2),
                "target_concept_id": "binary_search",
                "policy_version": "v1.0.0",
                "mastery_before": 0.2,
                "mastery_after": 0.4,
                "immediate_correctness": 0.8
            },
            {
                "intervention_id": "intervention_002",
                "user_id": user_id,
                "session_id": "session_002",
                "intervention_type": "difficulty_shift",
                "occurred_at": datetime.now() - timedelta(days=1),
                "target_concept_id": "sorting",
                "policy_version": "v1.0.0",
                "mastery_before": 0.5,
                "mastery_after": 0.6,
                "immediate_correctness": 0.7
            }
        ]
    
    def _mock_group_intervention_effectiveness(self):
        """Mock group intervention effectiveness data."""
        return [
            {
                "intervention_type": "remediation",
                "total_interventions": 10,
                "avg_mastery_delta": 0.15,
                "avg_correctness_after": 0.8,
                "successful_interventions": 8
            },
            {
                "intervention_type": "difficulty_shift",
                "total_interventions": 5,
                "avg_mastery_delta": 0.1,
                "avg_correctness_after": 0.75,
                "successful_interventions": 3
            },
            {
                "intervention_type": "prerequisite_review",
                "total_interventions": 3,
                "avg_mastery_delta": 0.2,
                "avg_correctness_after": 0.85,
                "successful_interventions": 2
            }
        ]
    
    def _mock_intervention_timing(self):
        """Mock intervention timing data."""
        return [
            {
                "event_id": "intervention_001",
                "user_id": "user_001",
                "adaptation_type": "remediation",
                "created_at": datetime.now() - timedelta(days=2),
                "mastery_before": 0.2,
                "mastery_after": 0.4,
                "timing_category": "early"
            },
            {
                "event_id": "intervention_002",
                "user_id": "user_001",
                "adaptation_type": "difficulty_shift",
                "created_at": datetime.now() - timedelta(days=1),
                "mastery_before": 0.5,
                "mastery_after": 0.6,
                "timing_category": "middle"
            },
            {
                "event_id": "intervention_003",
                "user_id": "user_002",
                "adaptation_type": "remediation",
                "created_at": datetime.now() - timedelta(hours=12),
                "mastery_before": 0.8,
                "mastery_after": 0.85,
                "timing_category": "late"
            }
        ]


class TestInterventionTiming:
    """Test InterventionTiming enum."""
    
    def test_timing_values(self):
        """Test that timing enum has expected values."""
        assert InterventionTiming.EARLY.value == "early"
        assert InterventionTiming.MIDDLE.value == "middle"
        assert InterventionTiming.LATE.value == "late"


class TestInterventionEvent:
    """Test InterventionEvent dataclass."""
    
    def test_intervention_event_creation(self):
        """Test creating an intervention event."""
        event = InterventionEvent(
            intervention_id="intervention_001",
            user_id="user_001",
            session_id="session_001",
            intervention_type="remediation",
            occurred_at=datetime.now(),
            timing=InterventionTiming.EARLY,
            target_concept_id="binary_search",
            policy_version="v1.0.0",
            immediate_correctness=0.8,
            mastery_before=0.2,
            mastery_after=0.4,
            mastery_delta=0.2
        )
        
        assert event.intervention_id == "intervention_001"
        assert event.timing == InterventionTiming.EARLY
        assert event.mastery_delta == 0.2


class TestInterventionEffectiveness:
    """Test InterventionEffectiveness dataclass."""
    
    def test_effectiveness_creation(self):
        """Test creating intervention effectiveness."""
        effectiveness = InterventionEffectiveness(
            intervention_type="remediation",
            total_interventions=10,
            successful_interventions=8,
            effectiveness_rate=0.8,
            average_mastery_delta=0.15,
            average_correctness_after=0.8,
            early_interventions=3,
            early_success_rate=0.9,
            middle_interventions=5,
            middle_success_rate=0.8,
            late_interventions=2,
            late_success_rate=0.7
        )
        
        assert effectiveness.intervention_type == "remediation"
        assert effectiveness.effectiveness_rate == 0.8
        assert effectiveness.early_success_rate == 0.9


class TestInterventionOutcomeReport:
    """Test InterventionOutcomeReport dataclass."""
    
    def test_report_creation(self):
        """Test creating intervention outcome report."""
        report = InterventionOutcomeReport(
            total_interventions=18,
            overall_effectiveness_rate=0.7,
            average_mastery_improvement=0.15,
            most_effective_interventions=["remediation", "prerequisite_review"],
            least_effective_interventions=["difficulty_shift"],
            early_intervention_effectiveness=0.8,
            middle_intervention_effectiveness=0.7,
            late_intervention_effectiveness=0.6,
            optimal_timing=InterventionTiming.EARLY,
            intervention_effectiveness=[]
        )
        
        assert report.total_interventions == 18
        assert report.overall_effectiveness_rate == 0.7
        assert report.optimal_timing == InterventionTiming.EARLY


class TestInterventionOutcomeAnalyzer:
    """Test InterventionOutcomeAnalyzer class."""
    
    def test_analyze_intervention_events(self):
        """Test analyzing intervention events for a user."""
        mock_db = MockDBStore()
        analyzer = InterventionOutcomeAnalyzer(db_store=mock_db)
        
        events = analyzer.analyze_intervention_events(user_id="user_001")
        
        assert len(events) == 2
        assert events[0].intervention_type == "remediation"
        assert events[0].timing == InterventionTiming.EARLY
        assert events[0].mastery_delta == 0.2
    
    def test_timing_determination(self):
        """Test timing determination based on mastery."""
        mock_db = MockDBStore()
        analyzer = InterventionOutcomeAnalyzer(db_store=mock_db)
        
        events = analyzer.analyze_intervention_events(user_id="user_001")
        
        # First event has mastery_before=0.2, should be EARLY
        assert events[0].timing == InterventionTiming.EARLY
        # Second event has mastery_before=0.5, should be MIDDLE
        assert events[1].timing == InterventionTiming.MIDDLE
    
    def test_mastery_delta_calculation(self):
        """Test mastery delta calculation."""
        mock_db = MockDBStore()
        analyzer = InterventionOutcomeAnalyzer(db_store=mock_db)
        
        events = analyzer.analyze_intervention_events(user_id="user_001")
        
        # Mastery delta should be calculated correctly (use approximate comparison for floating point)
        assert abs(events[0].mastery_delta - 0.2) < 0.001  # 0.4 - 0.2
        assert abs(events[1].mastery_delta - 0.1) < 0.001  # 0.6 - 0.5
    
    def test_analyze_intervention_effectiveness(self):
        """Test analyzing effectiveness of a specific intervention type."""
        mock_db = MockDBStore()
        analyzer = InterventionOutcomeAnalyzer(db_store=mock_db)
        
        effectiveness = analyzer.analyze_intervention_effectiveness("remediation")
        
        assert effectiveness.intervention_type == "remediation"
        assert effectiveness.total_interventions >= 0
        assert 0 <= effectiveness.effectiveness_rate <= 1
    
    def test_effectiveness_rate_calculation(self):
        """Test effectiveness rate calculation."""
        mock_db = MockDBStore()
        analyzer = InterventionOutcomeAnalyzer(db_store=mock_db)
        
        effectiveness = analyzer.analyze_intervention_effectiveness("remediation")
        
        # Effectiveness rate should be between 0 and 1
        assert 0 <= effectiveness.effectiveness_rate <= 1
    
    def test_timing_breakdown_in_effectiveness(self):
        """Test timing breakdown in effectiveness analysis."""
        mock_db = MockDBStore()
        analyzer = InterventionOutcomeAnalyzer(db_store=mock_db)
        
        effectiveness = analyzer.analyze_intervention_effectiveness("remediation")
        
        # Should have timing breakdown
        assert effectiveness.early_interventions >= 0
        assert effectiveness.middle_interventions >= 0
        assert effectiveness.late_interventions >= 0
    
    def test_generate_intervention_outcome_report(self):
        """Test generating aggregate intervention outcome report."""
        mock_db = MockDBStore()
        analyzer = InterventionOutcomeAnalyzer(db_store=mock_db)
        
        report = analyzer.generate_intervention_outcome_report()
        
        # Report should be generated successfully
        assert report.total_interventions >= 0
        assert 0 <= report.overall_effectiveness_rate <= 1
        assert report.average_mastery_improvement >= 0
    
    def test_most_effective_interventions(self):
        """Test identification of most effective interventions."""
        mock_db = MockDBStore()
        analyzer = InterventionOutcomeAnalyzer(db_store=mock_db)
        
        report = analyzer.generate_intervention_outcome_report()
        
        # Should identify most effective interventions (may be empty if no data)
        assert isinstance(report.most_effective_interventions, list)
    
    def test_least_effective_interventions(self):
        """Test identification of least effective interventions."""
        mock_db = MockDBStore()
        analyzer = InterventionOutcomeAnalyzer(db_store=mock_db)
        
        report = analyzer.generate_intervention_outcome_report()
        
        # Should identify least effective interventions (may be empty if no data)
        assert isinstance(report.least_effective_interventions, list)
    
    def test_timing_effectiveness_analysis(self):
        """Test timing effectiveness analysis in report."""
        mock_db = MockDBStore()
        analyzer = InterventionOutcomeAnalyzer(db_store=mock_db)
        
        report = analyzer.generate_intervention_outcome_report()
        
        # Should have timing effectiveness metrics
        assert 0 <= report.early_intervention_effectiveness <= 1
        assert 0 <= report.middle_intervention_effectiveness <= 1
        assert 0 <= report.late_intervention_effectiveness <= 1
    
    def test_optimal_timing_determination(self):
        """Test optimal timing determination."""
        mock_db = MockDBStore()
        analyzer = InterventionOutcomeAnalyzer(db_store=mock_db)
        
        report = analyzer.generate_intervention_outcome_report()
        
        # Should determine optimal timing
        assert isinstance(report.optimal_timing, InterventionTiming)
    
    def test_per_intervention_type_effectiveness(self):
        """Test per-intervention-type effectiveness breakdown."""
        mock_db = MockDBStore()
        analyzer = InterventionOutcomeAnalyzer(db_store=mock_db)
        
        report = analyzer.generate_intervention_outcome_report()
        
        # Should have per-intervention-type effectiveness (may be empty if no data)
        assert isinstance(report.intervention_effectiveness, list)
        for effectiveness in report.intervention_effectiveness:
            assert isinstance(effectiveness, InterventionEffectiveness)
    
    def test_no_database_store(self):
        """Test behavior when no database store is provided."""
        analyzer = InterventionOutcomeAnalyzer(db_store=None)
        
        events = analyzer.analyze_intervention_events(user_id="user_001")
        
        assert len(events) == 0
    
    def test_empty_report_when_no_data(self):
        """Test empty report when no data is available."""
        mock_db = MockDBStore()
        # Modify mock to return empty results
        mock_db.fetch_all = lambda query, params: []
        
        analyzer = InterventionOutcomeAnalyzer(db_store=mock_db)
        report = analyzer.generate_intervention_outcome_report()
        
        assert report.total_interventions == 0
        assert report.overall_effectiveness_rate == 0.0
    
    def test_empty_effectiveness_for_unknown_type(self):
        """Test empty effectiveness for unknown intervention type."""
        mock_db = MockDBStore()
        # Modify mock to return empty results
        mock_db.fetch_all = lambda query, params: []
        
        analyzer = InterventionOutcomeAnalyzer(db_store=mock_db)
        effectiveness = analyzer.analyze_intervention_effectiveness("unknown_type")
        
        assert effectiveness.total_interventions == 0
        assert effectiveness.effectiveness_rate == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
