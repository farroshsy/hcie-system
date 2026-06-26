import requests
import json
import time

def test_learning_trajectory():
    """Test learning trajectory with multiple correct/incorrect answers"""
    base_url = "http://127.0.0.1:8001/api/v1/tasks/submit"
    
    user_id = "trajectory_user"
    
    # Test sequence: 3 correct, 2 incorrect, 2 correct
    test_sequence = [
        {"answer": "+2", "expected_correct": True, "description": "Correct 1"},
        {"answer": "+2", "expected_correct": True, "description": "Correct 2"},
        {"answer": "+2", "expected_correct": True, "description": "Correct 3"},
        {"answer": "Wrong", "expected_correct": False, "description": "Incorrect 1"},
        {"answer": "Wrong", "expected_correct": False, "description": "Incorrect 2"},
        {"answer": "+2", "expected_correct": True, "description": "Correct 4"},
        {"answer": "+2", "expected_correct": True, "description": "Correct 5"},
    ]
    
    print("=== Learning Trajectory Test ===")
    print(f"Testing user: {user_id}")
    print("Interaction\tExpected\tActual\tMastery Before\tMastery After\tChange\tReward")
    print("-" * 85)
    
    mastery_history = []
    
    for i, test_case in enumerate(test_sequence):
        submission = {
            "user_id": user_id,
            "task_id": "q19",  # Same task for consistent testing
            "node_id": "ct_abstraction",
            "representation": "interactive",
            "answer": test_case["answer"],
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
                actual_correct = result.get("correct", False)
                reward = result.get("reward", 0)
                
                mastery_history.append({
                    "interaction": i + 1,
                    "mastery_before": mastery_before,
                    "mastery_after": mastery_after,
                    "mastery_change": mastery_change,
                    "correct": actual_correct,
                    "reward": reward
                })
                
                expected = "T" if test_case["expected_correct"] else "F"
                actual = "T" if actual_correct else "F"
                
                print(f"{i+1:2d}\t\t{expected}\t\t{actual}\t\t{mastery_before:.3f}\t\t{mastery_after:.3f}\t\t{mastery_change:+.3f}\t\t{reward:.3f}")
                
            else:
                print(f"{i+1:2d}\t\tError: {response.status_code}")
                
        except Exception as e:
            print(f"{i+1:2d}\t\tException: {e}")
        
        time.sleep(0.1)  # Small delay between requests
    
    # Analyze results
    print("\n=== Trajectory Analysis ===")
    if mastery_history:
        initial_mastery = mastery_history[0]["mastery_before"]
        final_mastery = mastery_history[-1]["mastery_after"]
        total_change = final_mastery - initial_mastery
        
        print(f"Initial mastery: {initial_mastery:.3f}")
        print(f"Final mastery: {final_mastery:.3f}")
        print(f"Total change: {total_change:+.3f}")
        
        # Separate correct vs incorrect
        correct_changes = [h["mastery_change"] for h in mastery_history if h["correct"]]
        incorrect_changes = [h["mastery_change"] for h in mastery_history if not h["correct"]]
        
        if correct_changes:
            avg_correct_change = sum(correct_changes) / len(correct_changes)
            print(f"Average change for correct answers: {avg_correct_change:+.3f}")
        
        if incorrect_changes:
            avg_incorrect_change = sum(incorrect_changes) / len(incorrect_changes)
            print(f"Average change for incorrect answers: {avg_incorrect_change:+.3f}")
        
        # Check for expected behavior
        if correct_changes and all(c > 0 for c in correct_changes):
            print("SUCCESS: All correct answers increased mastery")
        else:
            print("ISSUE: Some correct answers did not increase mastery")
            
        if incorrect_changes and all(c < 0 for c in incorrect_changes):
            print("SUCCESS: All incorrect answers decreased mastery")
        else:
            print("ISSUE: Some incorrect answers did not decrease mastery")

if __name__ == "__main__":
    test_learning_trajectory()
