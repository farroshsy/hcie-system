import requests
import json

def test_fresh_user():
    """Test with completely fresh user"""
    base_url = "http://127.0.0.1:8001/api/v1/tasks/submit"
    
    submission = {
        "user_id": "completely_fresh_user",
        "task_id": "q1",
        "node_id": "ct_abstraction",
        "representation": "visual",
        "answer": "Wrong",  # Incorrect answer
        "response_time": 12.0,
        "mode": "ct"
    }
    
    print("=== Fresh User Test ===")
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
            print(f"Mastery Before: {mastery_before:.3f}")
            print(f"Mastery After: {mastery_after:.3f}")
            print(f"Mastery Change: {mastery_change:+.3f}")
            
            if mastery_before < 0.4:
                print("SUCCESS: Starting at novice level (~0.3)")
            else:
                print("ISSUE: Still starting at high mastery level")
                
            if mastery_change < 0:
                print("SUCCESS: Incorrect answer decreased mastery")
            else:
                print("ISSUE: Incorrect answer increased mastery")
        else:
            print("Error:", response.text)
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_fresh_user()
