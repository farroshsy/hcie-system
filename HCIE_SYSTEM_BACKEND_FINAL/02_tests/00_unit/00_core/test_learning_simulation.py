#!/usr/bin/env python3
"""
Learning Simulation Script for Testing Metrics
Generates realistic learning events to populate dashboard
"""

import requests
import time
import random
import json

BASE_URL = "http://localhost:8001"

def generate_learning_events(num_users=20):
    """Generate realistic learning events"""
    
    concepts = [
        "k2_computing_systems_devices",
        "k5_algorithms", 
        "k8_algorithms"
    ]
    
    for i in range(num_users):
        user_id = f"sim_user_{i+1:03d}"
        concept = random.choice(concepts)
        correct = random.choice([True, False])
        response_time = random.uniform(2.0, 15.0)
        
        try:
            # Start session
            session_response = requests.get(f"{BASE_URL}/api/learning/frontend/session?user_id={user_id}")
            if session_response.status_code == 200:
                session_data = session_response.json()
                print(f"✅ Session {user_id}: {session_data.get('concept_label', concept)}")
                
                # Submit answer
                answer_data = {
                    "concept": concept,
                    "correct": correct,
                    "response_time": response_time,
                    "user_id": user_id
                }
                
                answer_response = requests.post(
                    f"{BASE_URL}/api/learning/frontend/answer",
                    json=answer_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if answer_response.status_code == 200:
                    answer_data = answer_response.json()
                    print(f"✅ Answer {user_id}: {concept}, correct={correct}, time={response_time:.1f}s -> {answer_data.get('processing_id', 'N/A')}")
                else:
                    print(f"❌ Answer failed {user_id}: {answer_response.status_code} - {answer_response.text}")
            else:
                print(f"❌ Session failed {user_id}: {session_response.status_code}")
                
        except Exception as e:
            print(f"❌ Error {user_id}: {e}")
        
        # Small delay between users
        time.sleep(0.2)

if __name__ == "__main__":
    print("🎯 Starting Learning Simulation...")
    print("=" * 50)
    
    # Generate first batch
    generate_learning_events(15)
    
    print("\n⏳ Waiting for processing...")
    time.sleep(3)
    
    # Generate second batch with different concepts
    print("\n🎯 Second batch...")
    generate_learning_events(10)
    
    print("\n✅ Simulation complete!")
    print("🔬 Check your Grafana dashboard for updated metrics!")
