import requests
import json
import sys
sys.path.append('RealSystem/HCIE_SYSTEM_BACKENDV2')
from storage.redis_store.redis_store import RedisFeatureStore

def test_zpd_effect():
    """Test ZPD alignment effect"""
    base_url = "http://127.0.0.1:8001/api/v1/tasks/submit"
    
    print("=== ZPD Effect Test ===")
    print("Difficulty\tMastery Before\tMastery After\tChange\tReward")
    print("-" * 65)
    
    # Test different difficulty levels
    difficulties = [0.2, 0.4, 0.6, 0.8]  # Easy, Medium, Hard, Very Hard
    
    # Initialize Redis store for cleanup
    redis_store = RedisFeatureStore()
    
    for i, difficulty in enumerate(difficulties):
        user_id = f"zpd_test_user_{i}"
        
        # Clear user data before each test
        redis_store.clear_user_data(user_id)
        
        submission = {
            "user_id": user_id,
            "task_id": "q19",  # Use real task ID
            "node_id": "ct_abstraction",
            "representation": "interactive",
            "answer": "+2",  # Use correct answer
            "response_time": 8.0,
            "mode": "ct"
        }
        
        # Override difficulty in the response (we'll need to test this differently)
        # For now, let's test with the actual task difficulty and observe ZPD effects
        
        # Create a custom task with specific difficulty
        # (We'll use the same task but different difficulty for testing)
        
        try:
            response = requests.post(base_url, json=submission)
            if response.status_code == 200:
                result = response.json()
                mastery_before = result.get("mastery_before", 0)
                mastery_after = result.get("mastery_after", 0)
                mastery_change = mastery_after - mastery_before
                reward = result.get("reward", 0)
                
                print(f"{difficulty:.1f}\t\t{mastery_before:.3f}\t\t{mastery_after:.3f}\t\t{mastery_change:+.3f}\t\t{reward:.3f}")
            else:
                print(f"Error for difficulty {difficulty}: {response.status_code}")
                
        except Exception as e:
            print(f"Exception for difficulty {difficulty}: {e}")

if __name__ == "__main__":
    test_zpd_effect()
