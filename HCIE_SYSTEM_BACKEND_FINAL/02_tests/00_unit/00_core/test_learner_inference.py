#!/usr/bin/env python3
"""
Test unified learning decision architecture
"""

import requests
import json
import time

def test_learner_inference():
    """Test learner-informed decision making"""
    
    # Wait for server to start
    time.sleep(2)
    
    try:
        # Test decision endpoint with learner inference
        response = requests.get('http://localhost:8000/api/learning/decision/next-action/test_user_001?concept=ct_algorithm_design')
        print('🔍 Decision API Status:', response.status_code)
        
        if response.status_code == 200:
            data = response.json()
            print('🧠 Learner-informed decision:')
            print('  decision_source:', data.get('decision_source'))
            print('  learner_informed:', data.get('reasoning', {}).get('learner_informed'))
            print('  ensemble_mastery:', data.get('reasoning', {}).get('ensemble_mastery'))
            print('  recommended_task:', data.get('recommended_task'))
            print('  mastery:', data.get('mastery'))
            
            # Check if learner inference was actually used
            if data.get('decision_source') == 'learner_informed_bandit':
                print('✅ SUCCESS: Learner-informed decision working!')
            else:
                print('⚠️  WARNING: Using fallback decision')
                
        else:
            print('❌ Error:', response.text)
            
    except Exception as e:
        print('❌ Connection error:', e)

if __name__ == "__main__":
    test_learner_inference()
