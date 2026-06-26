import requests
import json
import time

def test_challenge_scenario_only():
    """Test only the challenge scenario to isolate the issue"""
    base_url = "http://127.0.0.1:8001/api/v1/tasks/submit"
    
    user_id = "challenge_isolated_user"
    
    print("=== Challenge Scenario Only Test ===")
    print("Step\tAnswer\tCorrect\tMastery Before\tMastery After\tChange\tReward")
    print("-" * 75)
    
    # Test only the problematic sequence
    test_sequence = [
        {"answer": "Wrong", "description": "Step 1: Start with failure"},
        {"answer": "Wrong", "description": "Step 2: Continue struggling"},
        {"answer": "+2", "description": "Step 3: Breakthrough!"},
        {"answer": "+2", "description": "Step 4: Build confidence"},
        {"answer": "+2", "description": "Step 5: Achieve mastery"},
    ]
    
    for i, step in enumerate(test_sequence):
        submission = {
            "user_id": user_id,
            "task_id": "q19",
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
                correct = result.get("correct", False)
                reward = result.get("reward", 0)
                
                correct_mark = "T" if correct else "F"
                print(f"{i+1:2d}\t{step['answer']:8s}\t{correct_mark}\t\t{mastery_before:.3f}\t\t{mastery_after:.3f}\t\t{mastery_change:+.3f}\t\t{reward:.3f}")
                
                # Debug output
                print(f"    DEBUG: {step['description']}")
                if mastery_change == 0.0:
                    print(f"    WARNING: No mastery change detected!")
                
            else:
                print(f"{i+1:2d}\tError: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"{i+1:2d}\tException: {e}")
        
        time.sleep(0.5)  # Longer delay to see logs

if __name__ == "__main__":
    test_challenge_scenario_only()
