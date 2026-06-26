"""
Test Phase 1 Infrastructure Components

Validates database schema and core services work with the real system.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
pytest.skip(
    "phase-1 infra e2e: infrastructure.experiment.StatisticalAggregator was retired and this needs the full live stack.",
    allow_module_level=True,
)

from infrastructure.experiment import (
    TrajectoryRecorder,
    EvaluationEngine,
    StatisticalAggregator,
    ReplayEngine,
    CohortRunner,
    InteractionScheduler,
    ExperimentControlAPI
)
import psycopg2
from datetime import datetime


def test_database_schema():
    """Test that Phase 1 database tables exist"""
    print("🔍 Testing database schema...")
    
    # Use docker exec to check tables (more reliable for local testing)
    try:
        import subprocess
        
        # Check experiment_runs table
        result = subprocess.run(
            ["docker", "exec", "docker-postgres-1", "psql", "-U", "hcie_user", "-d", "hcie", 
             "-c", "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'experiment_runs');"],
            capture_output=True, text=True
        )
        assert "t" in result.stdout, "experiment_runs table not found"
        print("✅ experiment_runs table exists")
        
        # Check cohort_assignments table
        result = subprocess.run(
            ["docker", "exec", "docker-postgres-1", "psql", "-U", "hcie_user", "-d", "hcie", 
             "-c", "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'cohort_assignments');"],
            capture_output=True, text=True
        )
        assert "t" in result.stdout, "cohort_assignments table not found"
        print("✅ cohort_assignments table exists")
        
        # Check trajectory_records table
        result = subprocess.run(
            ["docker", "exec", "docker-postgres-1", "psql", "-U", "hcie_user", "-d", "hcie", 
             "-c", "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'trajectory_records');"],
            capture_output=True, text=True
        )
        assert "t" in result.stdout, "trajectory_records table not found"
        print("✅ trajectory_records table exists")
        
        return True
        
    except Exception as e:
        print(f"❌ Database schema test failed: {e}")
        return False


def test_interaction_scheduler():
    """Test InteractionScheduler with 9 policies and 6 archetypes"""
    print("\n🔍 Testing InteractionScheduler...")
    
    try:
        concepts = [f"concept_{i}" for i in range(20)]
        scheduler = InteractionScheduler(concepts)
        
        # Test all 9 policies
        policies = ["random", "static", "mastery_greedy", "uncertainty_reduction", 
                   "zpd_aligned", "epsilon_greedy", "ucb", "thompson", "hcie"]
        
        for policy in policies:
            scheduled = scheduler.schedule_next(
                user_id="test_user",
                config={"policy": policy, "learner_archetype": "novice"},
                interaction_number=1
            )
            concept = scheduled["concept"]
            assert concept in concepts, f"Policy {policy} returned invalid concept"
            print(f"✅ Policy {policy}: selected {concept}")
        
        # Test all 6 archetypes
        archetypes = ["novice", "unstable", "transfer_heavy", "forgetting", 
                     "exploration_sensitive", "challenge_seeking"]
        
        for archetype in archetypes:
            scheduled = scheduler.schedule_next(
                user_id="test_user",
                config={"policy": "random", "learner_archetype": archetype},
                interaction_number=1
            )
            interaction_data = scheduled["interaction_data"]
            assert "correctness" in interaction_data, f"Archetype {archetype} missing correctness"
            assert "response_time" in interaction_data, f"Archetype {archetype} missing response_time"
            print(f"✅ Archetype {archetype}: generated interaction data")
        
        return True
        
    except Exception as e:
        print(f"❌ InteractionScheduler test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_service_instantiation():
    """Test that all services can be instantiated"""
    print("\n🔍 Testing service instantiation...")
    
    try:
        # Mock database client for instantiation test
        class MockDBClient:
            def insert(self, table, data):
                return "mock_id"
            def query(self, table, query):
                return []
            def update(self, table, query, data):
                pass
        
        db_client = MockDBClient()
        
        # Test TrajectoryRecorder
        trajectory_recorder = TrajectoryRecorder(db_client)
        print("✅ TrajectoryRecorder instantiated")
        
        # Test EvaluationEngine
        evaluation_engine = EvaluationEngine(db_client)
        print("✅ EvaluationEngine instantiated")
        
        # Test StatisticalAggregator
        statistical_aggregator = StatisticalAggregator(db_client)
        print("✅ StatisticalAggregator instantiated")
        
        # Test InteractionScheduler (doesn't need db_client)
        concepts = [f"concept_{i}" for i in range(20)]
        interaction_scheduler = InteractionScheduler(concepts)
        print("✅ InteractionScheduler instantiated")
        
        # Test CohortRunner (needs unified_brain, will skip for now)
        print("⚠️  CohortRunner skipped (needs UnifiedBrain)")
        
        # Test ReplayEngine (needs unified_brain, will skip for now)
        print("⚠️  ReplayEngine skipped (needs UnifiedBrain)")
        
        # Test ExperimentControlAPI (needs all services, will skip for now)
        print("⚠️  ExperimentControlAPI skipped (needs all services)")
        
        return True
        
    except Exception as e:
        print(f"❌ Service instantiation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all Phase 1 infrastructure tests"""
    print("=" * 60)
    print("PHASE 1 INFRASTRUCTURE VALIDATION")
    print("=" * 60)
    
    results = []
    
    # Test database schema
    results.append(("Database Schema", test_database_schema()))
    
    # Test service instantiation
    results.append(("Service Instantiation", test_service_instantiation()))
    
    # Test interaction scheduler
    results.append(("Interaction Scheduler", test_interaction_scheduler()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    print("=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED")
        print("Phase 1 infrastructure is ready for use.")
    else:
        print("❌ SOME TESTS FAILED")
        print("Please fix the issues before proceeding.")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
