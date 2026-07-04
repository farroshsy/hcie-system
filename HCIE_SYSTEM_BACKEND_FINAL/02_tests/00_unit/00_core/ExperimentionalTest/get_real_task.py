import requests
import json

def get_real_task():
    """Get a real task to see the correct answer format"""
    try:
        response = requests.get("http://127.0.0.1:8001/api/v1/tasks/test_real_user?mode=ct")
        if response.status_code == 200:
            task = response.json()
            print("=== Real Task Details ===")
            print(f"Task ID: {task.get('task_id')}")
            print(f"Question: {task.get('question')}")
            print(f"Correct Answer: '{task.get('correct_answer')}'")
            print(f"Difficulty: {task.get('difficulty')}")
            print(f"Node ID: {task.get('node_id')}")
            return task
        else:
            print(f"Error: {response.status_code}")
            return None
    except Exception as e:
        print(f"Exception: {e}")
        return None

if __name__ == "__main__":
    task = get_real_task()
