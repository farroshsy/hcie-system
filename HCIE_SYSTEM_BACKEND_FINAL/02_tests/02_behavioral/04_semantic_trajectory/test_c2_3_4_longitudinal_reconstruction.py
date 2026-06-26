"""
C2.3.4 - Longitudinal Reconstruction Tests

Tests for rebuilding multi-week learner evolution.

Focus on pedagogical semantic trajectories (learning), NOT infrastructure replay.
"""

import pytest
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.replay.longitudinal_reconstruction import (
    EvolutionType,
    EvolutionPoint,
    EvolutionTrajectory,
    LongitudinalReconstructionReport,
    LongitudinalReconstructor
)
from core.replay.deterministic_replay_engine import (
    ReplayEventType,
    ReplayEvent,
    DeterministicReplayEngine
)


class TestEvolutionType:
    """Test EvolutionType enum."""
    
    def test_evolution_type_values(self):
        """Test that evolution type enum has expected values."""
        assert EvolutionType.MASTERY_EVOLUTION.value == "mastery_evolution"
        assert EvolutionType.MISCONCEPTION_EVOLUTION.value == "misconception_evolution"
        assert EvolutionType.PACING_EVOLUTION.value == "pacing_evolution"
        assert EvolutionType.ADAPTATION_EVOLUTION.value == "adaptation_evolution"
        assert EvolutionType.TRANSFER_READINESS_EVOLUTION.value == "transfer_readiness_evolution"
        assert EvolutionType.POLICY_EXPOSURE_EVOLUTION.value == "policy_exposure_evolution"


class TestEvolutionPoint:
    """Test EvolutionPoint dataclass."""
    
    def test_evolution_point_creation(self):
        """Test creating evolution point."""
        point = EvolutionPoint(
            timestamp=datetime.now(),
            session_id="session_001",
            mastery=0.7,
            uncertainty=0.3,
            zpd_score=0.5,
            concept_id="binary_search",
            concept_mastery=0.8,
            adaptation_type="remediation",
            policy_version="v1.0.0",
            session_phase="middle",
            tasks_completed=5
        )
        
        assert point.mastery == 0.7
        assert point.concept_id == "binary_search"
        assert point.adaptation_type == "remediation"
        assert point.session_phase == "middle"


class TestEvolutionTrajectory:
    """Test EvolutionTrajectory dataclass."""
    
    def test_trajectory_creation(self):
        """Test creating evolution trajectory."""
        trajectory = EvolutionTrajectory(
            user_id="user_001",
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now()
        )
        
        assert trajectory.user_id == "user_001"
        assert len(trajectory.evolution_points) == 0
        assert trajectory.total_sessions == 0
        assert trajectory.mastery_delta == 0.0


class TestLongitudinalReconstructionReport:
    """Test LongitudinalReconstructionReport dataclass."""
    
    def test_report_creation(self):
        """Test creating longitudinal reconstruction report."""
        report = LongitudinalReconstructionReport(
            user_id="user_001",
            reconstruction_timestamp=datetime.now(),
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now(),
            duration_days=30
        )
        
        assert report.user_id == "user_001"
        assert report.duration_days == 30
        assert report.adaptation_has_memory is False
        assert report.pacing_evolves is False


class TestLongitudinalReconstructor:
    """Test LongitudinalReconstructor class."""
    
    def test_reconstructor_initialization(self):
        """Test reconstructor initialization."""
        engine = DeterministicReplayEngine()
        reconstructor = LongitudinalReconstructor(engine)
        
        assert reconstructor is not None
        assert reconstructor._replay_engine is not None
    
    def test_filter_events_by_date_range(self):
        """Test filtering events by date range."""
        engine = DeterministicReplayEngine()
        reconstructor = LongitudinalReconstructor(engine)
        
        events = [
            ReplayEvent(
                event_id="event_001",
                event_type=ReplayEventType.TASK_ATTEMPT_SUBMITTED,
                user_id="user_001",
                timestamp=datetime(2024, 1, 1),
                causation_id="causation_001",
                trace_id="trace_001",
                payload={},
                experiment_id=None,
                policy_version="v1.0.0",
                cohort_id=None,
                assignment_hash=None,
                policy_snapshot_id=None,
                schema_version="1.0.0"
            ),
            ReplayEvent(
                event_id="event_002",
                event_type=ReplayEventType.TASK_ATTEMPT_SUBMITTED,
                user_id="user_001",
                timestamp=datetime(2024, 1, 15),
                causation_id="causation_002",
                trace_id="trace_002",
                payload={},
                experiment_id=None,
                policy_version="v1.0.0",
                cohort_id=None,
                assignment_hash=None,
                policy_snapshot_id=None,
                schema_version="1.0.0"
            ),
            ReplayEvent(
                event_id="event_003",
                event_type=ReplayEventType.TASK_ATTEMPT_SUBMITTED,
                user_id="user_001",
                timestamp=datetime(2024, 2, 1),
                causation_id="causation_003",
                trace_id="trace_003",
                payload={},
                experiment_id=None,
                policy_version="v1.0.0",
                cohort_id=None,
                assignment_hash=None,
                policy_snapshot_id=None,
                schema_version="1.0.0"
            )
        ]
        
        # Filter to January 2024
        filtered = reconstructor._filter_events_by_date_range(
            events,
            datetime(2024, 1, 1),
            datetime(2024, 1, 31)
        )
        
        assert len(filtered) == 2
    
    def test_extract_evolution_points(self):
        """Test extracting evolution points from events."""
        engine = DeterministicReplayEngine()
        reconstructor = LongitudinalReconstructor(engine)
        
        events = [
            ReplayEvent(
                event_id="event_001",
                event_type=ReplayEventType.TASK_ATTEMPT_SUBMITTED,
                user_id="user_001",
                timestamp=datetime.now(),
                causation_id="causation_001",
                trace_id="trace_001",
                payload={
                    "session_id": "session_001",
                    "mastery": 0.5,
                    "uncertainty": 0.3,
                    "zpd_score": 0.4,
                    "concept_id": "binary_search",
                    "concept_mastery": 0.6,
                    "tasks_completed": 3
                },
                experiment_id=None,
                policy_version="v1.0.0",
                cohort_id=None,
                assignment_hash=None,
                policy_snapshot_id=None,
                schema_version="1.0.0"
            ),
            ReplayEvent(
                event_id="event_002",
                event_type=ReplayEventType.ADAPTATION_GENERATED,
                user_id="user_001",
                timestamp=datetime.now(),
                causation_id="event_001",
                trace_id="trace_001",
                payload={
                    "adaptation_type": "remediation",
                    "policy_version": "v1.0.0"
                },
                experiment_id=None,
                policy_version="v1.0.0",
                cohort_id=None,
                assignment_hash=None,
                policy_snapshot_id=None,
                schema_version="1.0.0"
            )
        ]
        
        points = reconstructor._extract_evolution_points(events)
        
        assert len(points) == 1
        assert points[0].mastery == 0.5
        assert points[0].concept_id == "binary_search"
        assert points[0].adaptation_type == "remediation"
    
    def test_infer_session_phase(self):
        """Test inferring session phase from tasks completed."""
        engine = DeterministicReplayEngine()
        reconstructor = LongitudinalReconstructor(engine)
        
        assert reconstructor._infer_session_phase(1) == "early"
        assert reconstructor._infer_session_phase(5) == "middle"
        assert reconstructor._infer_session_phase(10) == "late"
    
    def test_build_mastery_trajectory(self):
        """Test building mastery evolution trajectory."""
        engine = DeterministicReplayEngine()
        reconstructor = LongitudinalReconstructor(engine)
        
        points = [
            EvolutionPoint(
                timestamp=datetime.now() - timedelta(days=10),
                session_id="session_001",
                mastery=0.5,
                uncertainty=0.3,
                zpd_score=0.4,
                concept_id="binary_search",
                concept_mastery=0.6,
                adaptation_type="remediation",
                policy_version="v1.0.0",
                session_phase="early",
                tasks_completed=3
            ),
            EvolutionPoint(
                timestamp=datetime.now(),
                session_id="session_002",
                mastery=0.7,
                uncertainty=0.2,
                zpd_score=0.6,
                concept_id="sorting",
                concept_mastery=0.8,
                adaptation_type="difficulty_shift",
                policy_version="v1.1.0",
                session_phase="middle",
                tasks_completed=5
            )
        ]
        
        trajectory = reconstructor._build_mastery_trajectory(
            "user_001",
            points,
            datetime.now() - timedelta(days=30),
            datetime.now()
        )
        
        assert trajectory.user_id == "user_001"
        assert abs(trajectory.mastery_delta - 0.2) < 0.001
        assert abs(trajectory.uncertainty_delta - (-0.1)) < 0.001
        assert trajectory.total_concepts_encountered == 2
        assert trajectory.policy_exposure_history["v1.0.0"] == 1
        assert trajectory.policy_exposure_history["v1.1.0"] == 1
    
    def test_build_pacing_trajectory(self):
        """Test building pacing evolution trajectory."""
        engine = DeterministicReplayEngine()
        reconstructor = LongitudinalReconstructor(engine)
        
        base_time = datetime.now()
        points = [
            EvolutionPoint(
                timestamp=base_time,
                session_id="session_001",
                mastery=0.5,
                uncertainty=0.3,
                zpd_score=0.4,
                concept_id="binary_search",
                concept_mastery=0.6,
                adaptation_type="remediation",
                policy_version="v1.0.0",
                session_phase="early",
                tasks_completed=3
            ),
            EvolutionPoint(
                timestamp=base_time + timedelta(seconds=100),
                session_id="session_001",
                mastery=0.6,
                uncertainty=0.25,
                zpd_score=0.5,
                concept_id="binary_search",
                concept_mastery=0.7,
                adaptation_type="remediation",
                policy_version="v1.0.0",
                session_phase="middle",
                tasks_completed=6
            )
        ]
        
        trajectory = reconstructor._build_pacing_trajectory(
            "user_001",
            points,
            datetime.now() - timedelta(days=30),
            datetime.now()
        )
        
        assert trajectory.user_id == "user_001"
        assert trajectory.pacing_stability_score > 0  # Should be high for consistent pacing
    
    def test_build_adaptation_trajectory(self):
        """Test building adaptation evolution trajectory."""
        engine = DeterministicReplayEngine()
        reconstructor = LongitudinalReconstructor(engine)
        
        points = [
            EvolutionPoint(
                timestamp=datetime.now(),
                session_id="session_001",
                mastery=0.5,
                uncertainty=0.3,
                zpd_score=0.4,
                concept_id="binary_search",
                concept_mastery=0.6,
                adaptation_type="remediation",
                policy_version="v1.0.0",
                session_phase="early",
                tasks_completed=3
            ),
            EvolutionPoint(
                timestamp=datetime.now(),
                session_id="session_002",
                mastery=0.7,
                uncertainty=0.2,
                zpd_score=0.6,
                concept_id="sorting",
                concept_mastery=0.8,
                adaptation_type="difficulty_shift",
                policy_version="v1.1.0",
                session_phase="middle",
                tasks_completed=5
            )
        ]
        
        trajectory = reconstructor._build_adaptation_trajectory(
            "user_001",
            points,
            datetime.now() - timedelta(days=30),
            datetime.now()
        )
        
        assert trajectory.user_id == "user_001"
        assert len(trajectory.evolution_points) == 2
        assert trajectory.policy_exposure_history["v1.0.0"] == 1
        assert trajectory.policy_exposure_history["v1.1.0"] == 1
    
    def test_validate_adaptation_memory_true(self):
        """Test validating adaptation memory with multiple policies."""
        engine = DeterministicReplayEngine()
        reconstructor = LongitudinalReconstructor(engine)
        
        trajectory = EvolutionTrajectory(
            user_id="user_001",
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now(),
            policy_exposure_history={"v1.0.0": 5, "v1.1.0": 3}
        )
        
        has_memory = reconstructor._validate_adaptation_memory(trajectory)
        
        assert has_memory is True
    
    def test_validate_adaptation_memory_false(self):
        """Test validating adaptation memory with single policy."""
        engine = DeterministicReplayEngine()
        reconstructor = LongitudinalReconstructor(engine)
        
        trajectory = EvolutionTrajectory(
            user_id="user_001",
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now(),
            policy_exposure_history={"v1.0.0": 10}
        )
        
        has_memory = reconstructor._validate_adaptation_memory(trajectory)
        
        assert has_memory is False
    
    def test_validate_pacing_evolution_true(self):
        """Test validating pacing evolution with instability."""
        engine = DeterministicReplayEngine()
        reconstructor = LongitudinalReconstructor(engine)
        
        trajectory = EvolutionTrajectory(
            user_id="user_001",
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now(),
            pacing_stability_score=0.8  # Below 0.95 threshold
        )
        
        evolves = reconstructor._validate_pacing_evolution(trajectory)
        
        assert evolves is True
    
    def test_validate_pacing_evolution_false(self):
        """Test validating pacing evolution with stability."""
        engine = DeterministicReplayEngine()
        reconstructor = LongitudinalReconstructor(engine)
        
        trajectory = EvolutionTrajectory(
            user_id="user_001",
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now(),
            pacing_stability_score=0.98  # Above 0.95 threshold
        )
        
        evolves = reconstructor._validate_pacing_evolution(trajectory)
        
        assert evolves is False
    
    def test_validate_pedagogy_development_true(self):
        """Test validating pedagogy development with all factors."""
        engine = DeterministicReplayEngine()
        reconstructor = LongitudinalReconstructor(engine)
        
        report = LongitudinalReconstructionReport(
            user_id="user_001",
            reconstruction_timestamp=datetime.now(),
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now(),
            duration_days=30,
            adaptation_has_memory=True,
            pacing_evolves=True
        )
        report.mastery_trajectory.mastery_delta = 0.2
        
        develops = reconstructor._validate_pedagogy_development(report)
        
        assert develops is True
    
    def test_validate_pedagogy_development_false(self):
        """Test validating pedagogy development without factors."""
        engine = DeterministicReplayEngine()
        reconstructor = LongitudinalReconstructor(engine)
        
        report = LongitudinalReconstructionReport(
            user_id="user_001",
            reconstruction_timestamp=datetime.now(),
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now(),
            duration_days=30,
            adaptation_has_memory=False,
            pacing_evolves=False
        )
        report.mastery_trajectory.mastery_delta = 0.0
        
        develops = reconstructor._validate_pedagogy_development(report)
        
        assert develops is False
    
    def test_reconstruct_longitudinal_evolution_empty_events(self):
        """Test reconstructing longitudinal evolution with empty event stream."""
        engine = DeterministicReplayEngine()
        reconstructor = LongitudinalReconstructor(engine)
        
        report = reconstructor.reconstruct_longitudinal_evolution(
            user_id="user_001",
            events=[]
        )
        
        assert report.user_id == "user_001"
        assert report.duration_days >= 0
        assert report.adaptation_has_memory is False
        assert report.pacing_evolves is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
