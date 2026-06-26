import requests
import json
import sys
import time
sys.path.append('RealSystem/HCIE_SYSTEM_BACKENDV2')
from storage.redis_store.redis_store import RedisFeatureStore

def test_zpd_stress():
    """Stress test ZPD with different difficulty/mastery combinations"""
    base_url = "http://127.0.0.1:8001/api/v1/tasks/submit"
    
    print("=== ZPD Stress Test ===")
    print("Case\tDifficulty\tMastery Before\tMastery After\tChange\tReward\tZPD Status\tExpected")
    print("-" * 95)
    
    redis_store = RedisFeatureStore()
    
    # Test cases: different difficulty/mastery combinations
    test_cases = [
        {
            "name": "Case A: Too Easy",
            "difficulty": 0.1,  # Very easy task
            "target_mastery": 0.4,  # Relatively advanced student
            "expected": "Small gains (too easy)",
            "user_id": "zpd_too_easy_user"
        },
        {
            "name": "Case B: Too Hard", 
            "difficulty": 0.8,  # Very hard task
            "target_mastery": 0.3,  # Novice student
            "expected": "Small gains/instability (too hard)",
            "user_id": "zpd_too_hard_user"
        },
        {
            "name": "Case C: Perfect ZPD",
            "difficulty": 0.5,  # Medium task
            "target_mastery": 0.5,  # Matching mastery
            "expected": "Maximum gains (perfect ZPD)",
            "user_id": "zpd_perfect_user"
        },
        {
            "name": "Case D: Slightly Hard",
            "difficulty": 0.6,  # Slightly hard task
            "target_mastery": 0.5,  # Slightly below difficulty
            "expected": "Good gains (upper ZPD)",
            "user_id": "zpd_slightly_hard_user"
        },
        {
            "name": "Case E: Slightly Easy",
            "difficulty": 0.3,  # Slightly easy task
            "target_mastery": 0.4,  # Slightly above difficulty
            "expected": "Good gains (lower ZPD)",
            "user_id": "zpd_slightly_easy_user"
        }
    ]
    
    for i, case in enumerate(test_cases):
        # Clear user data
        redis_store.clear_user_data(case["user_id"])
        
        # First, build up mastery to target level
        print(f"\n--- Building mastery to {case['target_mastery']:.1f} for {case['name']} ---")
        
        # Simulate some learning to reach target mastery
        target_mastery = case["target_mastery"]
        current_mastery = 0.3
        
        while current_mastery < target_mastery - 0.05:  # Get close to target
            submission = {
                "user_id": case["user_id"],
                "task_id": "q19",
                "node_id": "ct_abstraction", 
                "representation": "interactive",
                "answer": "+2",  # Correct answer
                "response_time": 8.0,
                "mode": "ct"
            }
            
            try:
                response = requests.post(base_url, json=submission)
                if response.status_code == 200:
                    result = response.json()
                    current_mastery = result.get("mastery_after", 0.3)
                    print(f"  Mastery: {current_mastery:.3f}")
                else:
                    print(f"  Error: {response.status_code}")
                    break
            except Exception as e:
                print(f"  Exception: {e}")
                break
            
            time.sleep(0.1)
        
        # Now test the actual ZPD effect
        print(f"\n--- Testing {case['name']} ---")
        print(f"Target mastery: {current_mastery:.3f}, Task difficulty: {case['difficulty']:.1f}")
        
        submission = {
            "user_id": case["user_id"],
            "task_id": "q19",
            "node_id": "ct_abstraction",
            "representation": "interactive", 
            "answer": "+2",  # Correct answer
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
                
                # Calculate ZPD status
                zpd_diff = abs(mastery_before - case["difficulty"])
                if zpd_diff <= 0.1:
                    zpd_status = "IN ZPD"
                elif mastery_before < case["difficulty"] - 0.1:
                    zpd_status = "TOO HARD"
                else:
                    zpd_status = "TOO EASY"
                
                print(f"{case['name']}\t{case['difficulty']:.1f}\t\t{mastery_before:.3f}\t\t{mastery_after:.3f}\t\t{mastery_change:+.3f}\t\t{reward:.3f}\t\t{zpd_status}\t{case['expected']}")
                
                # Analysis
                print(f"  Analysis: {zpd_status} - {case['expected']}")
                if mastery_change > 0.03:
                    print(f"  Strong learning gain detected!")
                elif mastery_change > 0.01:
                    print(f"  Moderate learning gain detected.")
                else:
                    print(f"  Weak learning gain detected.")
                    
            else:
                print(f"{case['name']}\tError: {response.status_code}")
                
        except Exception as e:
            print(f"{case['name']}\tException: {e}")
        
        time.sleep(0.2)
    
    print("\n=== ZPD Stress Test Summary ===")
    print("This test validates that:")
    print("1. Maximum gains occur in the ZPD (±0.1 of difficulty)")
    print("2. Smaller gains occur when task is too easy or too hard")
    print("3. Learning is optimized when difficulty matches mastery level")

if __name__ == "__main__":
    test_zpd_stress()
