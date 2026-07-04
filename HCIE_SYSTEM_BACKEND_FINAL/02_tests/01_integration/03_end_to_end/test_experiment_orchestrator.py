"""
Test experiment orchestrator

Verifies that the experiment orchestrator correctly integrates all infrastructure components
and coordinates experiment execution with reproducibility.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
from core.learning.learner_archetypes import ArchetypeType


class MockDBClient:
    """Mock database client for testing"""
    
    def __init__(self):
        self.data = {
            "experiments": [],
            "experiment_runs": [],
            "cohort_assignments": [],
            "interaction_trajectories": []
        }
    
    def insert(self, table, data):
        """Insert data into table"""
        if "id" not in data:
            data["id"] = f"{table}_{len(self.data[table]) + 1}"
        self.data[table].append(data)
        return data["id"]
    
    def update(self, table, query, updates):
        """Update data in table"""
        for item in self.data[table]:
            match = True
            for key, value in query.items():
                if item.get(key) != value:
                    match = False
                    break
            if match:
                item.update(updates)
    
    def query(self, table, query):
        """Query data from table"""
        results = []
        for item in self.data[table]:
            match = True
            for key, value in query.items():
                if item.get(key) != value:
                    match = False
                    break
            if match:
                results.append(item)
        return results


def test_experiment_orchestrator_initialization():
    """Test experiment orchestrator initialization"""
    print("🧪 Testing Experiment Orchestrator Initialization")
    print("=" * 60)
    
    # Patch the problematic imports to avoid Settings validation
    with patch('infrastructure.experiment.experiment_orchestrator.UnifiedLearningBrain'):
        with patch('infrastructure.experiment.experiment_orchestrator.CohortRunner'):
            with patch('infrastructure.experiment.experiment_orchestrator.ExperimentControlAPI'):
                with patch('infrastructure.experiment.experiment_orchestrator.InteractionScheduler'):
                    with patch('infrastructure.experiment.experiment_orchestrator.TrajectoryRecorder'):
                        with patch('infrastructure.experiment.experiment_orchestrator.EvaluationEngine'):
                            with patch('infrastructure.experiment.experiment_orchestrator.StatisticalAggregator'):
                                from infrastructure.experiment.experiment_orchestrator import ExperimentOrchestrator
                                
                                # Create mock components
                                mock_brain = Mock()
                                mock_db = MockDBClient()
                                
                                # Initialize orchestrator
                                orchestrator = ExperimentOrchestrator(
                                    unified_brain=mock_brain,
                                    db_client=mock_db
                                )
                                
                                # Verify components are initialized
                                assert orchestrator.unified_brain == mock_brain
                                assert orchestrator.db_client == mock_db
                                assert orchestrator.cohort_runner is not None
                                assert orchestrator.experiment_api is not None
                                assert orchestrator.interaction_scheduler is not None
    
    print("  ✅ Orchestrator initialized with all components")
    print("✅ Experiment orchestrator initialization test passed\n")
    return True


def test_seed_reproducibility():
    """Test seed reproducibility"""
    print("🧪 Testing Seed Reproducibility")
    print("=" * 60)
    
    with patch('infrastructure.experiment.experiment_orchestrator.UnifiedLearningBrain'):
        with patch('infrastructure.experiment.experiment_orchestrator.CohortRunner'):
            with patch('infrastructure.experiment.experiment_orchestrator.ExperimentControlAPI'):
                with patch('infrastructure.experiment.experiment_orchestrator.InteractionScheduler'):
                    with patch('infrastructure.experiment.experiment_orchestrator.TrajectoryRecorder'):
                        with patch('infrastructure.experiment.experiment_orchestrator.EvaluationEngine'):
                            with patch('infrastructure.experiment.experiment_orchestrator.StatisticalAggregator'):
                                from infrastructure.experiment.experiment_orchestrator import ExperimentOrchestrator
                                
                                mock_brain = Mock()
                                mock_db = MockDBClient()
                                
                                orchestrator = ExperimentOrchestrator(
                                    unified_brain=mock_brain,
                                    db_client=mock_db
                                )
                                
                                # Set seed
                                orchestrator.set_seed(42)
                                assert orchestrator.current_seed == 42
    
    print("  ✅ Seed set correctly")
    print("✅ Seed reproducibility test passed\n")
    return True


def test_create_experiment():
    """Test experiment creation"""
    print("🧪 Testing Experiment Creation")
    print("=" * 60)
    
    with patch('infrastructure.experiment.experiment_orchestrator.UnifiedLearningBrain'):
        with patch('infrastructure.experiment.experiment_orchestrator.CohortRunner'):
            with patch('infrastructure.experiment.experiment_orchestrator.ExperimentControlAPI'):
                with patch('infrastructure.experiment.experiment_orchestrator.InteractionScheduler'):
                    with patch('infrastructure.experiment.experiment_orchestrator.TrajectoryRecorder'):
                        with patch('infrastructure.experiment.experiment_orchestrator.EvaluationEngine'):
                            with patch('infrastructure.experiment.experiment_orchestrator.StatisticalAggregator'):
                                from infrastructure.experiment.experiment_orchestrator import ExperimentOrchestrator
                                
                                mock_brain = Mock()
                                mock_db = MockDBClient()
                                
                                orchestrator = ExperimentOrchestrator(
                                    unified_brain=mock_brain,
                                    db_client=mock_db
                                )
                                
                                # Create experiment
                                experiment_id = orchestrator.create_experiment(
                                    experiment_id="test_experiment",
                                    experiment_name="Test Experiment",
                                    description="Test description"
                                )
                                
                                assert experiment_id == "test_experiment"
                                
                                # Verify experiment was created
                                experiments = mock_db.query("experiments", {"id": "test_experiment"})
                                assert len(experiments) == 1
                                assert experiments[0]["name"] == "Test Experiment"
                                assert experiments[0]["status"] == "created"
    
    print("  ✅ Experiment created successfully")
    print("✅ Experiment creation test passed\n")
    return True


def test_create_cohort_config():
    """Test cohort configuration creation"""
    print("🧪 Testing Cohort Configuration Creation")
    print("=" * 60)
    
    with patch('infrastructure.experiment.experiment_orchestrator.UnifiedLearningBrain'):
        with patch('infrastructure.experiment.experiment_orchestrator.CohortRunner'):
            with patch('infrastructure.experiment.experiment_orchestrator.ExperimentControlAPI'):
                with patch('infrastructure.experiment.experiment_orchestrator.InteractionScheduler'):
                    with patch('infrastructure.experiment.experiment_orchestrator.TrajectoryRecorder'):
                        with patch('infrastructure.experiment.experiment_orchestrator.EvaluationEngine'):
                            with patch('infrastructure.experiment.experiment_orchestrator.StatisticalAggregator'):
                                from infrastructure.experiment.experiment_orchestrator import ExperimentOrchestrator
                                
                                mock_brain = Mock()
                                mock_db = MockDBClient()
                                
                                orchestrator = ExperimentOrchestrator(
                                    unified_brain=mock_brain,
                                    db_client=mock_db
                                )
                                
                                # Create cohort config
                                config = orchestrator.create_cohort_config(
                                    policy="hcie",
                                    learner_archetype=ArchetypeType.NOVICE,
                                    num_learners=10,
                                    num_concepts=20,
                                    num_interactions=50,
                                    seed=42
                                )
                                
                                assert config["policy"] == "hcie"
                                assert config["learner_archetype"] == "novice"
                                assert config["num_learners"] == 10
                                assert config["num_concepts"] == 20
                                assert config["num_interactions"] == 50
                                assert config["seed"] == 42
                                assert "archetype_config" in config
                                assert "learning_rate" in config["archetype_config"]
    
    print("  ✅ Cohort config created with archetype configuration")
    print(f"  ✅ Archetype config has {len(config['archetype_config'])} parameters")
    print("✅ Cohort configuration creation test passed\n")
    return True


def test_get_experiment_status():
    """Test getting experiment status"""
    print("🧪 Testing Get Experiment Status")
    print("=" * 60)
    
    with patch('infrastructure.experiment.experiment_orchestrator.UnifiedLearningBrain'):
        with patch('infrastructure.experiment.experiment_orchestrator.CohortRunner'):
            with patch('infrastructure.experiment.experiment_orchestrator.ExperimentControlAPI'):
                with patch('infrastructure.experiment.experiment_orchestrator.InteractionScheduler'):
                    with patch('infrastructure.experiment.experiment_orchestrator.TrajectoryRecorder'):
                        with patch('infrastructure.experiment.experiment_orchestrator.EvaluationEngine'):
                            with patch('infrastructure.experiment.experiment_orchestrator.StatisticalAggregator'):
                                from infrastructure.experiment.experiment_orchestrator import ExperimentOrchestrator
                                
                                mock_brain = Mock()
                                mock_db = MockDBClient()
                                
                                orchestrator = ExperimentOrchestrator(
                                    unified_brain=mock_brain,
                                    db_client=mock_db
                                )
                                
                                # Create experiment
                                orchestrator.create_experiment(
                                    experiment_id="test_experiment",
                                    experiment_name="Test Experiment"
                                )
                                
                                # Get status
                                status = orchestrator.get_experiment_status("test_experiment")
                                
                                assert status["experiment_id"] == "test_experiment"
                                assert status["name"] == "Test Experiment"
                                assert status["status"] == "created"
                                assert status["num_runs"] == 0
    
    print("  ✅ Experiment status retrieved successfully")
    print("✅ Get experiment status test passed\n")
    return True


def test_stop_experiment():
    """Test stopping experiment"""
    print("🧪 Testing Stop Experiment")
    print("=" * 60)
    
    with patch('infrastructure.experiment.experiment_orchestrator.UnifiedLearningBrain'):
        with patch('infrastructure.experiment.experiment_orchestrator.CohortRunner'):
            with patch('infrastructure.experiment.experiment_orchestrator.ExperimentControlAPI'):
                with patch('infrastructure.experiment.experiment_orchestrator.InteractionScheduler'):
                    with patch('infrastructure.experiment.experiment_orchestrator.TrajectoryRecorder'):
                        with patch('infrastructure.experiment.experiment_orchestrator.EvaluationEngine'):
                            with patch('infrastructure.experiment.experiment_orchestrator.StatisticalAggregator'):
                                from infrastructure.experiment.experiment_orchestrator import ExperimentOrchestrator
                                
                                mock_brain = Mock()
                                mock_db = MockDBClient()
                                
                                orchestrator = ExperimentOrchestrator(
                                    unified_brain=mock_brain,
                                    db_client=mock_db
                                )
                                
                                # Create experiment
                                orchestrator.create_experiment(
                                    experiment_id="test_experiment",
                                    experiment_name="Test Experiment"
                                )
                                
                                # Stop experiment
                                orchestrator.stop_experiment("test_experiment")
                                
                                # Verify status
                                status = orchestrator.get_experiment_status("test_experiment")
                                assert status["status"] == "stopped"
    
    print("  ✅ Experiment stopped successfully")
    print("✅ Stop experiment test passed\n")
    return True


def test_all():
    """Run all experiment orchestrator tests"""
    print("🧪 Experiment Orchestrator Tests")
    print("=" * 60)
    
    try:
        test_experiment_orchestrator_initialization()
        test_seed_reproducibility()
        test_create_experiment()
        test_create_cohort_config()
        test_get_experiment_status()
        test_stop_experiment()
        
        print("=" * 60)
        print("✅ All experiment orchestrator tests passed")
        print("=" * 60)
        print("\n📊 Summary:")
        print("  - Orchestrator initializes with all components")
        print("  - Seed reproducibility supported")
        print("  - Experiment creation works")
        print("  - Cohort configuration includes archetype configs")
        print("  - Experiment status monitoring works")
        print("  - Experiment can be stopped")
        
        return True
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_all()
