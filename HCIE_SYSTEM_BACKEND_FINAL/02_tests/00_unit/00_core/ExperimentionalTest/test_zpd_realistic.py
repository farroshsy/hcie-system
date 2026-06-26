import requests
import json
import sys
import time
sys.path.append('RealSystem/HCIE_SYSTEM_BACKENDV2')
from storage.redis_store.redis_store import RedisFeatureStore

def test_zpd_realistic():
    """Test ZPD effect with realistic mastery progression"""
    base_url = "http://127.0.0.1:8001/api/v1/tasks/submit"
    
    print("=== Realistic ZPD Effect Test ===")
    print("Step\tMastery Before\tDifficulty\tMastery After\tChange\tReward\tZPD Status")
    print("-" * 85)
    
    user_id = "zpd_realistic_user"
    redis_store = RedisFeatureStore()
    
    # Clear user data
    redis_store.clear_user_data(user_id)
    
    # Test sequence: Start novice, progress through difficulty levels
    test_sequence = [
        {"answer": "+2", "description": "Start at novice level"},
        {"answer": "+2", "description": "Build some mastery"},
        {"answer": "+2", "description": "Reach intermediate level"},
        {"answer": "+2", "description": "Continue learning"},
        {"answer": "+2", "description": "Approach mastery"},
    ]
    
    for i, step in enumerate(test_sequence):
        submission = {
            "user_id": user_id,
            "task_id": "q19",  # Same task, difficulty 0.4
            "node_id": "ct_abstraction",
            "representation": "interactive",
            "answer": step["answer"],
            "response_time": 8.0,
            "mode": "ct"
        }
        
        try:
            response = requests.post(base_url, json=submission)
            if response.status_code == 200:
                result = response.json()
                mastery_before = result.get("mastery_before", 0)
                mastery_after = result.get("mastery_after", 0)
                mastery_change = mastery_after - mastery_before
                reward = result.get("reward", 0)
                difficulty = result.get("difficulty", 0.4)
                
                # Calculate ZPD status
                zpd_diff = abs(mastery_before - difficulty)
                if zpd_diff <= 0.1:
                    zpd_status = "IN ZPD"
                elif mastery_before < difficulty - 0.1:
                    zpd_status = "TOO HARD"
                else:
                    zpd_status = "TOO EASY"
                
                print(f"{i+1:2d}\t{mastery_before:.3f}\t\t{difficulty:.1f}\t\t{mastery_after:.3f}\t\t{mastery_change:+.3f}\t\t{reward:.3f}\t\t{zpd_status}")
                print(f"    {step['description']}")
                
            else:
                print(f"{i+1:2d}\tError: {response.status_code}")
                
        except Exception as e:
            print(f"{i+1:2d}\tException: {e}")
        
        time.sleep(0.2)
    
    print("\n=== ZPD Analysis ===")
    print("This test shows how learning changes as mastery approaches task difficulty.")
    print("Optimal learning occurs when mastery is in the ZPD (±0.1 of difficulty).")

if __name__ == "__main__":
    test_zpd_realistic()
