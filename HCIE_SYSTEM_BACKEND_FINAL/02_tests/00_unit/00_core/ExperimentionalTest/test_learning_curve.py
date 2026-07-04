import requests
import json
import time

def test_learning_curve():
    """Test long-term learning trajectory"""
    base_url = "http://127.0.0.1:8001/api/v1/tasks/submit"
    
    # Test user
    user_id = "trajectory_test_user"
    
    # Track mastery progression
    mastery_history = []
    
    print("=== Learning Curve Test ===")
    print(f"Testing user: {user_id}")
    print("Interaction\tMastery Before\tMastery After\tChange\tReward")
    print("-" * 70)
    
    for i in range(20):
        # Create submission (mostly correct answers with some mistakes)
        submission = {
            "user_id": user_id,
            "task_id": f"q{i}",
            "node_id": "ct_abstraction", 
            "representation": "visual",
            "answer": "Details" if i % 8 != 5 else "Wrong",  # 1 mistake every 8
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
                
                mastery_history.append({
                    "interaction": i + 1,
                    "mastery_before": mastery_before,
                    "mastery_after": mastery_after,
                    "mastery_change": mastery_change,
                    "reward": reward,
                    "correct": result.get("correct", False)
                })
                
                print(f"{i+1:2d}\t\t{mastery_before:.3f}\t\t{mastery_after:.3f}\t\t{mastery_change:+.3f}\t\t{reward:.3f}")
                
            else:
                print(f"Error in interaction {i+1}: {response.status_code}")
                
        except Exception as e:
            print(f"Exception in interaction {i+1}: {e}")
        
        time.sleep(0.1)  # Small delay between requests
    
    # Analyze results
    print("\n=== Analysis ===")
    if mastery_history:
        initial_mastery = mastery_history[0]["mastery_before"]
        final_mastery = mastery_history[-1]["mastery_after"]
        total_change = final_mastery - initial_mastery
        
        print(f"Initial mastery: {initial_mastery:.3f}")
        print(f"Final mastery: {final_mastery:.3f}")
        print(f"Total change: {total_change:+.3f}")
        
        # Check for stability issues
        max_change = max(abs(h["mastery_change"]) for h in mastery_history)
        print(f"Max single change: {max_change:.3f}")
        
        if max_change > 0.1:
            print("WARNING: Large single changes detected - system may be unstable")
        elif total_change < 0.1:
            print("WARNING: Very little learning - system may be too conservative")
        else:
            print("SUCCESS: Reasonable learning trajectory")
    
    return mastery_history

if __name__ == "__main__":
    test_learning_curve()
