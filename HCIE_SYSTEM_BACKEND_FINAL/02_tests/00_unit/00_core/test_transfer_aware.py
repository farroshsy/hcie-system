"""
Test Transfer-Aware Bandit Flow

Tests the transfer-aware recommendation system that combines:
- Multi-armed bandit for concept selection
- DAG transfer learning for transfer bonuses
- Transfer engine for learned transfer weights
"""

import sys
import os
import json
import requests

# Add path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.utils.id_normalization import normalize_user_id

def test_transfer_aware_recommendation():
    """Test transfer-aware recommendation endpoint"""
    print("🧪 Testing Transfer-Aware Recommendation")
    print("=" * 60)
    
    # API base URL
    api_url = "http://localhost:8001"
    
    # Use normalized user_id from earlier test
    original_user_id = "test_user_b31a_001"
    normalized_user_id = normalize_user_id(original_user_id)
    print(f"📝 Using normalized user_id: {normalized_user_id} (from: {original_user_id})")
    
    # Call transfer-aware recommendation endpoint
    endpoint = f"{api_url}/api/learning/decision/transfer-aware/{normalized_user_id}"
    print(f"\n🔍 Calling endpoint: {endpoint}")
    
    try:
        response = requests.get(endpoint)
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Transfer-Aware Recommendation SUCCESS")
            print(f"   Recommended Concept: {result.get('recommended_concept')}")
            print(f"   Mastery: {result.get('mastery', 'N/A')}")
            print(f"   Mastery Gap: {result.get('mastery_gap', 'N/A')}")
            print(f"   Transfer Bonus: {result.get('transfer_bonus', 'N/A')}")
            print(f"   Exploration Cost: {result.get('exploration_cost', 'N/A')}")
            print(f"   Score: {result.get('score', 'N/A')}")
            print(f"   Recommendation Reason: {result.get('recommendation_reason', 'N/A')}")
            
            # Check transfer relationships
            transfer_relationships = result.get('transfer_relationships', [])
            print(f"\n   Transfer Relationships ({len(transfer_relationships)}):")
            for rel in transfer_relationships[:5]:  # Show first 5
                print(f"     - {rel.get('source_concept')} → {rel.get('target_concept')}: "
                      f"weight={rel.get('transfer_weight', 'N/A')}, "
                      f"type={rel.get('dependency_type', 'N/A')}")
            
            return True
        else:
            print(f"\n❌ Transfer-Aware Recommendation FAILED")
            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"\n❌ Transfer-Aware Recommendation ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_transfer_aware_recommendation()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Transfer-Aware Flow Test PASSED")
    else:
        print("❌ Transfer-Aware Flow Test FAILED")
    print("=" * 60)
    
    sys.exit(0 if success else 1)
