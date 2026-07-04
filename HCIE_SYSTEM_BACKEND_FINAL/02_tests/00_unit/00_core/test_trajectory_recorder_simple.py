"""
Simple direct test of trajectory recorder to isolate the issue
"""

import os
import sys
import logging

# Set environment variables BEFORE imports
os.environ["DATABASE_URL"] = "postgresql://hcie_user:hcie_password@postgres:5432/hcie"
os.environ["DOCKER_ENV"] = "true"

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from storage.postgres_store.interaction_store import PostgresInteractionStore
from infrastructure.experiment.trajectory_recorder import PostgresInteractionStoreAdapter

def test_trajectory_recorder():
    """Test trajectory recorder directly"""
    print("🔥 Testing trajectory recorder directly")
    print("=" * 60)
    
    try:
        # Initialize PostgresInteractionStore
        postgres_store = PostgresInteractionStore()
        print("✅ PostgresInteractionStore initialized")
        
        # Initialize PostgresInteractionStoreAdapter
        adapter = PostgresInteractionStoreAdapter(postgres_store)
        print("✅ PostgresInteractionStoreAdapter initialized")
        
        # Test insert
        test_record = {
            "experiment_run_id": "test_run_001",
            "user_id": "test_user_001",
            "concept": "test_concept_001",
            "interaction_id": "test_interaction_001",
            "event_id": "test_event_001",
            "interaction_number": 1,
            "mastery_before": 0.5,
            "mastery_after": 0.6,
            "uncertainty_before": 0.3,
            "uncertainty_after": 0.2
        }
        
        print("📝 Inserting test record...")
        adapter.insert("experiment_trajectories", test_record)
        print("✅ Test record inserted successfully")
        
        # Test query
        print("📝 Querying test record...")
        results = adapter.query("experiment_trajectories", {"experiment_run_id": "test_run_001"})
        print(f"✅ Query returned {len(results)} records")
        
        if results:
            print(f"📊 First record: {results[0]}")
        
        print()
        print("=" * 60)
        print("✅ Trajectory recorder test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Trajectory recorder test FAILED: {e}")
        import traceback
        traceback.print_exc()
        print()
        print("=" * 60)
        print("❌ Trajectory recorder test FAILED")
        return False

if __name__ == "__main__":
    success = test_trajectory_recorder()
    sys.exit(0 if success else 1)
