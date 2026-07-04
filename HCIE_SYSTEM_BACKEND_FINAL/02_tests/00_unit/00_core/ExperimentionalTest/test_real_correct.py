import requests
import json

def test_real_correct_answer():
    """Test with real task ID and correct answer"""
    base_url = "http://127.0.0.1:8001/api/v1/tasks/submit"
    
    submission = {
        "user_id": "real_correct_user",
        "task_id": "q19",  # Real task ID
        "node_id": "ct_abstraction",
        "representation": "interactive",
        "answer": "None",  # Real correct answer
        "response_time": 8.0,
        "mode": "ct"
    }
    
    print("=== Real Correct Answer Test ===")
    print("Submission:", json.dumps(submission, indent=2))
    
    try:
        response = requests.post(base_url, json=submission)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("Response:", json.dumps(result, indent=2))
            
            # Check key values
            mastery_before = result.get("mastery_before", 0)
            mastery_after = result.get("mastery_after", 0)
            mastery_change = mastery_after - mastery_before
            
            print(f"\n=== Analysis ===")
            print(f"Correct: {result.get('correct')}")
            print(f"Mastery Before: {mastery_before:.3f}")
            print(f"Mastery After: {mastery_after:.3f}")
            print(f"Mastery Change: {mastery_change:+.3f}")
            
            if result.get('correct'):
                print("SUCCESS: Correct answer detected!")
                if mastery_change > 0:
                    print("SUCCESS: Mastery increased for correct answer!")
                else:
                    print("ISSUE: Mastery should increase for correct answer")
            else:
                print("ISSUE: Answer marked as incorrect")
        else:
            print("Error:", response.text)
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_real_correct_answer()
