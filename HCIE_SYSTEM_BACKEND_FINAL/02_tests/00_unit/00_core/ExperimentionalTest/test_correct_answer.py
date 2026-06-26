import requests
import json

def test_correct_answer():
    """Test with correct answer to see proper mastery increase"""
    base_url = "http://127.0.0.1:8001/api/v1/tasks/submit"
    
    submission = {
        "user_id": "correct_test_user",
        "task_id": "q1",
        "node_id": "ct_abstraction",
        "representation": "visual",
        "answer": "Details",  # Correct answer
        "response_time": 8.0,
        "mode": "ct"
    }
    
    print("=== Correct Answer Test ===")
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
            
            # Expected behavior
            if 0.25 <= mastery_before <= 0.35:
                print("SUCCESS: Starting at novice level (~0.3)")
            else:
                print("ISSUE: Unexpected starting mastery")
                
            if mastery_change > 0 and mastery_after <= 1.0:
                print("SUCCESS: Correct answer increased mastery within bounds")
            else:
                print(f"ISSUE: Mastery change {mastery_change:+.3f} is unexpected or mastery > 1.0")
        else:
            print("Error:", response.text)
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_correct_answer()
