import requests
import json

def test_incorrect_answers():
    """Test incorrect answer behavior"""
    base_url = "http://127.0.0.1:8001/api/v1/tasks/submit"
    
    user_id = "incorrect_test_user"
    
    print("=== Incorrect Answer Test ===")
    print("Interaction\tCorrect\tMastery Before\tMastery After\tChange")
    print("-" * 65)
    
    for i in range(5):
        submission = {
            "user_id": user_id,
            "task_id": f"q{i}",
            "node_id": "ct_abstraction",
            "representation": "visual", 
            "answer": "Wrong",  # Always incorrect
            "response_time": 12.0,
            "mode": "ct"
        }
        
        try:
            response = requests.post(base_url, json=submission)
            if response.status_code == 200:
                result = response.json()
                mastery_before = result.get("mastery_before", 0)
                mastery_after = result.get("mastery_after", 0)
                mastery_change = mastery_after - mastery_before
                
                print(f"{i+1:2d}\t\t{result.get('correct', False)}\t\t{mastery_before:.3f}\t\t{mastery_after:.3f}\t\t{mastery_change:+.3f}")
            else:
                print(f"Error in interaction {i+1}: {response.status_code}")
                
        except Exception as e:
            print(f"Exception in interaction {i+1}: {e}")

if __name__ == "__main__":
    test_incorrect_answers()
