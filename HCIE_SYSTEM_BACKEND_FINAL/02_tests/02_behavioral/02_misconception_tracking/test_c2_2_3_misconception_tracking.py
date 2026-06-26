"""
C2.2.3 - Misconception Recurrence Tracking Tests

Tests for tracking recurring misconceptions across sessions, measuring remediation success,
and identifying stubborn misconceptions needing alternative interventions.

Focus on pedagogical semantic trajectories (learning), NOT infrastructure metrics (machines).
"""

import pytest
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.analytics.misconception_tracking import (
    MisconceptionSeverity,
    MisconceptionOccurrence,
    MisconceptionPattern,
    RemediationEffectivenessReport,
    MisconceptionTrackingSystem
)


class MockDBStore:
    """Mock database store for testing."""
    
    def __init__(self):
        self.data = {}
    
    def fetch_all(self, query, params):
        """Return mock data based on query."""
        query_lower = query.lower()
        
        # Check for pattern query with user_id parameter (user-specific)
        if "misconception" in query_lower and "pattern" in query_lower and ":user_id" in query_lower:
            return self._mock_misconception_pattern(params.get("user_id"))
        # Check for group pattern query (aggregate, no user_id)
        elif "misconception" in query_lower and "pattern" in query_lower and "group" in query_lower:
            return self._mock_group_misconception_pattern()
        # Check for remediation by adaptation type
        elif "remediation" in query_lower and "adaptation" in query_lower:
            return self._mock_remediation_by_adaptation_type()
        # Check for concepts for misconception
        elif "concept" in query_lower and "misconception" in query_lower and "distinct" in query_lower:
            return self._mock_concepts_for_misconception(
                params.get("user_id"), 
                params.get("misconception_id")
            )
        return []
    
    def _mock_misconception_occurrences(self, user_id):
        """Mock misconception occurrences data."""
        return [
            {
                "misconception_id": "off_by_one",
                "user_id": user_id,
                "concept_id": "binary_search",
                "session_id": "session_001",
                "task_id": "task_001",
                "occurred_at": datetime.now() - timedelta(days=5),
                "is_correct": False,
                "adaptation_type": "remediation",
                "policy_version": "v1.0.0"
            },
            {
                "misconception_id": "off_by_one",
                "user_id": user_id,
                "concept_id": "binary_search",
                "session_id": "session_002",
                "task_id": "task_005",
                "occurred_at": datetime.now() - timedelta(days=3),
                "is_correct": False,
                "adaptation_type": "remediation",
                "policy_version": "v1.0.0"
            },
            {
                "misconception_id": "off_by_one",
                "user_id": user_id,
                "concept_id": "sorting",
                "session_id": "session_003",
                "task_id": "task_010",
                "occurred_at": datetime.now() - timedelta(days=1),
                "is_correct": True,
                "adaptation_type": None,
                "policy_version": None
            }
        ]
    
    def _mock_misconception_pattern(self, user_id):
        """Mock misconception pattern data."""
        return [
            {
                "misconception_id": "off_by_one",
                "user_id": user_id,
                "total_occurrences": 3,
                "first_occurrence": datetime.now() - timedelta(days=5),
                "last_occurrence": datetime.now() - timedelta(days=1),
                "sessions_affected": 3,
                "concepts_affected": 2,
                "remediation_attempts": 2,
                "successful_remediations": 1,
                "recurrence_after_remediation": 1
            }
        ]
    
    def _mock_group_misconception_pattern(self):
        """Mock group misconception pattern data."""
        return [
            {
                "misconception_id": "off_by_one",
                "total_occurrences": 15,
                "first_occurrence": datetime.now() - timedelta(days=30),
                "last_occurrence": datetime.now(),
                "sessions_affected": 10,
                "users_affected": 5,
                "remediation_attempts": 8,
                "successful_remediations": 3
            },
            {
                "misconception_id": "infinite_loop",
                "total_occurrences": 5,
                "first_occurrence": datetime.now() - timedelta(days=15),
                "last_occurrence": datetime.now() - timedelta(days=2),
                "sessions_affected": 3,
                "users_affected": 2,
                "remediation_attempts": 4,
                "successful_remediations": 3
            }
        ]
    
    def _mock_remediation_by_adaptation_type(self):
        """Mock remediation effectiveness by adaptation type."""
        return [
            {
                "adaptation_type": "remediation",
                "total_attempts": 10,
                "successful_remediations": 6
            },
            {
                "adaptation_type": "difficulty_shift",
                "total_attempts": 5,
                "successful_remediations": 4
            },
            {
                "adaptation_type": "prerequisite_review",
                "total_attempts": 3,
                "successful_remediations": 1
            }
        ]
    
    def _mock_concepts_for_misconception(self, user_id, misconception_id):
        """Mock concepts affected by a misconception."""
        return [
            {"concept_id": "binary_search"},
            {"concept_id": "sorting"}
        ]


class TestMisconceptionSeverity:
    """Test MisconceptionSeverity enum."""
    
    def test_severity_values(self):
        """Test that severity enum has expected values."""
        assert MisconceptionSeverity.LOW.value == "low"
        assert MisconceptionSeverity.MEDIUM.value == "medium"
        assert MisconceptionSeverity.HIGH.value == "high"
        assert MisconceptionSeverity.CRITICAL.value == "critical"


class TestMisconceptionOccurrence:
    """Test MisconceptionOccurrence dataclass."""
    
    def test_misconception_occurrence_creation(self):
        """Test creating a misconception occurrence."""
        occurrence = MisconceptionOccurrence(
            misconception_id="off_by_one",
            user_id="user_001",
            concept_id="binary_search",
            session_id="session_001",
            task_id="task_001",
            occurred_at=datetime.now(),
            is_correct_after=False,
            remediation_attempted=True,
            adaptation_type="remediation",
            policy_version="v1.0.0"
        )
        
        assert occurrence.misconception_id == "off_by_one"
        assert occurrence.is_correct_after == False
        assert occurrence.remediation_attempted == True


class TestMisconceptionPattern:
    """Test MisconceptionPattern dataclass."""
    
    def test_misconception_pattern_creation(self):
        """Test creating a misconception pattern."""
        pattern = MisconceptionPattern(
            misconception_id="off_by_one",
            user_id="user_001",
            total_occurrences=3,
            first_occurrence=datetime.now() - timedelta(days=5),
            last_occurrence=datetime.now(),
            sessions_affected=2,
            concepts_affected={"binary_search", "sorting"},
            remediation_attempts=2,
            successful_remediations=1,
            remediation_success_rate=0.5,
            recurrence_after_remediation=1,
            average_recurrence_interval_days=2.5,
            stubbornness_score=0.6,
            severity=MisconceptionSeverity.HIGH,
            recommended_alternative_intervention="prerequisite_review"
        )
        
        assert pattern.misconception_id == "off_by_one"
        assert pattern.total_occurrences == 3
        assert pattern.stubbornness_score == 0.6
        assert pattern.severity == MisconceptionSeverity.HIGH


class TestRemediationEffectivenessReport:
    """Test RemediationEffectivenessReport dataclass."""
    
    def test_report_creation(self):
        """Test creating a remediation effectiveness report."""
        report = RemediationEffectivenessReport(
            total_misconceptions=10,
            stubborn_misconceptions=["off_by_one", "infinite_loop"],
            successfully_remediated=["boundary_case"],
            average_remediation_success_rate=0.6,
            critical_misconceptions=2,
            high_misconceptions=3,
            medium_misconceptions=3,
            low_misconceptions=2,
            most_effective_adaptation_types={
                "difficulty_shift": 0.8,
                "remediation": 0.6
            },
            least_effective_adaptation_types={
                "prerequisite_review": 0.33,
                "remediation": 0.6
            }
        )
        
        assert report.total_misconceptions == 10
        assert len(report.stubborn_misconceptions) == 2
        assert report.average_remediation_success_rate == 0.6
        assert "difficulty_shift" in report.most_effective_adaptation_types


class TestMisconceptionTrackingSystem:
    """Test MisconceptionTrackingSystem class."""
    
    def test_track_misconception_recurrence(self):
        """Test tracking misconception recurrence for a user."""
        mock_db = MockDBStore()
        tracker = MisconceptionTrackingSystem(db_store=mock_db)
        
        patterns = tracker.track_misconception_recurrence(user_id="user_001")
        
        assert len(patterns) == 1
        assert patterns[0].misconception_id == "off_by_one"
        assert patterns[0].total_occurrences == 3
        assert patterns[0].sessions_affected == 3
        assert patterns[0].remediation_attempts == 2
        assert patterns[0].successful_remediations == 1
    
    def test_remediation_success_rate_calculation(self):
        """Test remediation success rate calculation."""
        mock_db = MockDBStore()
        tracker = MisconceptionTrackingSystem(db_store=mock_db)
        
        patterns = tracker.track_misconception_recurrence(user_id="user_001")
        
        # 1 successful remediation out of 2 attempts = 0.5
        assert patterns[0].remediation_success_rate == 0.5
    
    def test_stubbornness_score_calculation(self):
        """Test stubbornness score calculation."""
        mock_db = MockDBStore()
        tracker = MisconceptionTrackingSystem(db_store=mock_db)
        
        patterns = tracker.track_misconception_recurrence(user_id="user_001")
        
        # Stubbornness score should be calculated based on occurrences, success rate, and recurrence
        assert 0 <= patterns[0].stubbornness_score <= 1
    
    def test_severity_determination(self):
        """Test severity level determination."""
        mock_db = MockDBStore()
        tracker = MisconceptionTrackingSystem(db_store=mock_db)
        
        patterns = tracker.track_misconception_recurrence(user_id="user_001")
        
        # Severity should be one of the enum values
        assert isinstance(patterns[0].severity, MisconceptionSeverity)
    
    def test_concepts_affected(self):
        """Test concepts affected by misconception."""
        mock_db = MockDBStore()
        tracker = MisconceptionTrackingSystem(db_store=mock_db)
        
        patterns = tracker.track_misconception_recurrence(user_id="user_001")
        
        # Should have concepts affected
        assert len(patterns[0].concepts_affected) > 0
        assert "binary_search" in patterns[0].concepts_affected or "sorting" in patterns[0].concepts_affected
    
    def test_generate_remediation_effectiveness_report(self):
        """Test generating aggregate remediation effectiveness report."""
        mock_db = MockDBStore()
        tracker = MisconceptionTrackingSystem(db_store=mock_db)
        
        report = tracker.generate_remediation_effectiveness_report()
        
        assert report.total_misconceptions == 2
        assert len(report.stubborn_misconceptions) >= 0
        assert len(report.successfully_remediated) >= 0
        assert 0 <= report.average_remediation_success_rate <= 1
    
    def test_adaptation_type_effectiveness(self):
        """Test effectiveness analysis by adaptation type."""
        mock_db = MockDBStore()
        tracker = MisconceptionTrackingSystem(db_store=mock_db)
        
        report = tracker.generate_remediation_effectiveness_report()
        
        # Should have adaptation type effectiveness data
        assert len(report.most_effective_adaptation_types) > 0
        assert len(report.least_effective_adaptation_types) > 0
        
        # Check that effectiveness values are valid
        for adaptation_type, effectiveness in report.most_effective_adaptation_types.items():
            assert 0 <= effectiveness <= 1
    
    def test_severity_classification_in_report(self):
        """Test severity classification in aggregate report."""
        mock_db = MockDBStore()
        tracker = MisconceptionTrackingSystem(db_store=mock_db)
        
        report = tracker.generate_remediation_effectiveness_report()
        
        # Should have severity counts
        total_severity_count = (
            report.critical_misconceptions +
            report.high_misconceptions +
            report.medium_misconceptions +
            report.low_misconceptions
        )
        
        assert total_severity_count >= report.total_misconceptions
    
    def test_no_database_store(self):
        """Test behavior when no database store is provided."""
        tracker = MisconceptionTrackingSystem(db_store=None)
        
        patterns = tracker.track_misconception_recurrence(user_id="user_001")
        
        assert len(patterns) == 0
    
    def test_empty_report_when_no_data(self):
        """Test empty report when no data is available."""
        mock_db = MockDBStore()
        # Modify mock to return empty results
        mock_db.fetch_all = lambda query, params: []
        
        tracker = MisconceptionTrackingSystem(db_store=mock_db)
        report = tracker.generate_remediation_effectiveness_report()
        
        assert report.total_misconceptions == 0
        assert len(report.stubborn_misconceptions) == 0
        assert report.average_remediation_success_rate == 0.0
    
    def test_stubbornness_score_high_occurrences(self):
        """Test that high occurrence count increases stubbornness score."""
        tracker = MisconceptionTrackingSystem(db_store=None)
        
        # High occurrences, low success rate, high recurrence
        score = tracker._calculate_stubbornness_score(
            total_occurrences=10,
            remediation_success_rate=0.1,
            recurrence_after_remediation=5
        )
        
        # Should be high (close to 1)
        assert score > 0.8
    
    def test_stubbornness_score_low_occurrences(self):
        """Test that low occurrence count decreases stubbornness score."""
        tracker = MisconceptionTrackingSystem(db_store=None)
        
        # Low occurrences, high success rate, low recurrence
        score = tracker._calculate_stubbornness_score(
            total_occurrences=1,
            remediation_success_rate=0.9,
            recurrence_after_remediation=0
        )
        
        # Should be low (close to 0)
        assert score < 0.5
    
    def test_severity_critical_threshold(self):
        """Test critical severity threshold."""
        tracker = MisconceptionTrackingSystem(db_store=None)
        
        severity = tracker._determine_severity(
            total_occurrences=10,
            remediation_success_rate=0.1,
            stubbornness_score=0.9
        )
        
        assert severity == MisconceptionSeverity.CRITICAL
    
    def test_severity_low_threshold(self):
        """Test low severity threshold."""
        tracker = MisconceptionTrackingSystem(db_store=None)
        
        severity = tracker._determine_severity(
            total_occurrences=1,
            remediation_success_rate=0.8,
            stubbornness_score=0.2
        )
        
        assert severity == MisconceptionSeverity.LOW
    
    def test_alternative_intervention_recommendation(self):
        """Test alternative intervention recommendation."""
        tracker = MisconceptionTrackingSystem(db_store=None)
        
        # Stubborn misconception with low success rate
        recommendation = tracker._recommend_alternative_intervention(
            misconception_id="off_by_one",
            remediation_success_rate=0.2,
            stubbornness_score=0.8
        )
        
        # Should recommend an alternative intervention
        assert recommendation is not None
    
    def test_no_alternative_intervention_for_non_stubborn(self):
        """Test that non-stubborn misconceptions get no alternative recommendation."""
        tracker = MisconceptionTrackingSystem(db_store=None)
        
        # Non-stubborn misconception
        recommendation = tracker._recommend_alternative_intervention(
            misconception_id="off_by_one",
            remediation_success_rate=0.8,
            stubbornness_score=0.3
        )
        
        # Should not recommend alternative intervention
        assert recommendation is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
