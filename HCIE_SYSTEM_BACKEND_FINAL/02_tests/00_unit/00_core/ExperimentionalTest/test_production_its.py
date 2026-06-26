import requests
import json
import time
import sys
sys.path.append('RealSystem/HCIE_SYSTEM_BACKENDV2')
from storage.redis_store.redis_store import RedisFeatureStore

def test_production_its():
    """Test production-grade ITS with realistic scenarios"""
    base_url = "http://127.0.0.1:8001/api/v1/tasks/submit"
    
    # Test scenarios with different difficulty levels
    test_scenarios = [
        {
            "name": "Novice Learning Path",
            "user_id": "novice_user",
            "sequence": [
                {"task_id": "q19", "answer": "+2", "description": "Learn abstraction (easy)"},
                {"task_id": "q19", "answer": "+2", "description": "Reinforce abstraction"},
                {"task_id": "q19", "answer": "Wrong", "description": "Make mistake - learn from error"},
                {"task_id": "q19", "answer": "+2", "description": "Recover from mistake"},
                {"task_id": "q19", "answer": "+2", "description": "Solidify knowledge"},
            ]
        },
        {
            "name": "Challenge Scenario",
            "user_id": "challenge_user", 
            "sequence": [
                {"task_id": "q19", "answer": "Wrong", "description": "Start with failure"},
                {"task_id": "q19", "answer": "Wrong", "description": "Struggle continues"},
                {"task_id": "q19", "answer": "+2", "description": "Breakthrough!"},
                {"task_id": "q19", "answer": "+2", "description": "Build confidence"},
                {"task_id": "q19", "answer": "+2", "description": "Achieve mastery"},
            ]
        },
        {
            "name": "Forgetting Test",
            "user_id": "forgetting_user",
            "sequence": [
                {"task_id": "q19", "answer": "+2", "description": "Learn skill"},
                {"task_id": "q19", "answer": "+2", "description": "Reinforce"},
                {"task_id": "q19", "answer": "+2", "description": "Master concept"},
                {"task_id": "q19", "answer": "Wrong", "description": "Make mistake"},
                {"task_id": "q19", "answer": "Wrong", "description": "Forgetting effect"},
                {"task_id": "q19", "answer": "+2", "description": "Re-learn"},
            ]
        }
    ]
    
    print("=== Production-Grade ITS Test ===")
    
    # Initialize Redis store for cleanup
    redis_store = RedisFeatureStore()
    
    for scenario in test_scenarios:
        print(f"\n{'='*60}")
        print(f"Scenario: {scenario['name']}")
        print(f"{'='*60}")
        
        # Clear user data before each scenario
        redis_store.clear_user_data(scenario['user_id'])
        print(f"Cleared data for user: {scenario['user_id']}")
        
        print("Step\tAnswer\tCorrect\tMastery Before\tMastery After\tChange\tReward")
        print("-" * 80)
        
        mastery_history = []
        
        for i, step in enumerate(scenario["sequence"]):
            submission = {
                "user_id": scenario["user_id"],
                "task_id": step["task_id"],
                "node_id": "ct_abstraction",
                "representation": "interactive",
                "answer": step["answer"],
                "response_time": 8.0 + (i * 0.5),  # Varying response times
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
                    
                    mastery_history.append({
                        "step": i + 1,
                        "mastery_before": mastery_before,
                        "mastery_after": mastery_after,
                        "mastery_change": mastery_change,
                        "correct": correct,
                        "reward": reward
                    })
                    
                    correct_mark = "T" if correct else "F"
                    print(f"{i+1:2d}\t{step['answer']:8s}\t{correct_mark}\t\t{mastery_before:.3f}\t\t{mastery_after:.3f}\t\t{mastery_change:+.3f}\t\t{reward:.3f}")
                    
                else:
                    print(f"{i+1:2d}\tError: {response.status_code}")
                    
            except Exception as e:
                print(f"{i+1:2d}\tException: {e}")
            
            time.sleep(0.2)  # Small delay between requests
        
        # Analyze scenario results
        if mastery_history:
            initial_mastery = mastery_history[0]["mastery_before"]
            final_mastery = mastery_history[-1]["mastery_after"]
            total_change = final_mastery - initial_mastery
            
            correct_count = sum(1 for h in mastery_history if h["correct"])
            incorrect_count = len(mastery_history) - correct_count
            
            correct_changes = [h["mastery_change"] for h in mastery_history if h["correct"]]
            incorrect_changes = [h["mastery_change"] for h in mastery_history if not h["correct"]]
            
            avg_correct = sum(correct_changes) / len(correct_changes) if correct_changes else 0
            avg_incorrect = sum(incorrect_changes) / len(incorrect_changes) if incorrect_changes else 0
            
            print(f"\nScenario Analysis:")
            print(f"  Initial mastery: {initial_mastery:.3f}")
            print(f"  Final mastery: {final_mastery:.3f}")
            print(f"  Total change: {total_change:+.3f}")
            print(f"  Correct answers: {correct_count}/{len(mastery_history)}")
            print(f"  Avg correct change: {avg_correct:+.3f}")
            print(f"  Avg incorrect change: {avg_incorrect:+.3f}")
            
            # Check for production-grade behavior
            if correct_changes and all(c > 0 for c in correct_changes):
                print(f"  SUCCESS: All correct answers increased mastery")
            else:
                print(f"  ISSUE: Some correct answers didn't increase mastery")
                
            if incorrect_changes and all(c < 0 for c in incorrect_changes):
                print(f"  SUCCESS: All incorrect answers decreased mastery")
            else:
                print(f"  ISSUE: Some incorrect answers didn't decrease mastery")
                
            # Check if net learning makes sense
            if correct_count > incorrect_count and total_change > 0:
                print(f"  SUCCESS: More correct than incorrect, net positive learning")
            elif correct_count < incorrect_count and total_change < 0:
                print(f"  SUCCESS: More incorrect than correct, net negative learning")
            else:
                print(f"  WARNING: Learning pattern may be unrealistic")

if __name__ == "__main__":
    test_production_its()
