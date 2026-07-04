import requests
import json

def test_single_interaction():
    """Test single interaction with debugging"""
    base_url = "http://127.0.0.1:8001/api/v1/tasks/submit"
    
    submission = {
        "user_id": "single_test_user",
        "task_id": "q1",
        "node_id": "ct_abstraction",
        "representation": "visual",
        "answer": "Wrong",  # Incorrect answer
        "response_time": 12.0,
        "mode": "ct"
    }
    
    print("=== Single Test ===")
    print("Submission:", json.dumps(submission, indent=2))
    
    try:
        response = requests.post(base_url, json=submission)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("Response:", json.dumps(result, indent=2))
        else:
            print("Error:", response.text)
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_single_interaction()
