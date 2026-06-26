"""
Test Two-Level Decision Hierarchy

Tests the integrated two-level decision system:
- Level 1: Transfer-aware bandit selects concept (inter-concept)
- Level 2: Normal bandit selects task within concept (intra-concept)
"""

import sys
import os
import json
import requests

# Add path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.utils.id_normalization import normalize_user_id

def test_normal_bandit_mode():
    """Test normal bandit mode (single-concept learning)"""
    print("🧪 Testing Normal Bandit Mode (Single-Concept)")
    print("=" * 60)
    
    # API base URL
    api_url = "http://localhost:8001"
    
    # Use normalized user_id from earlier test
    original_user_id = "test_user_b31a_001"
    normalized_user_id = normalize_user_id(original_user_id)
    print(f"📝 Using normalized user_id: {normalized_user_id} (from: {original_user_id})")
    
    # Call normal bandit recommendation endpoint
    endpoint = f"{api_url}/api/learning/decision/next-action/{normalized_user_id}"
    print(f"\n🔍 Calling endpoint: {endpoint}")
    
    try:
        response = requests.get(endpoint)
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Normal Bandit Mode SUCCESS")
            print(f"   Recommended Concept: {result.get('recommended_concept')}")
            print(f"   Selection Engine: {result.get('selection_engine', 'N/A')}")
            print(f"   Recommendation Reason: {result.get('recommendation_reason', 'N/A')}")
            return True
        else:
            print(f"\n❌ Normal Bandit Mode FAILED")
            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"\n❌ Normal Bandit Mode ERROR: {e}")
        return False

def test_transfer_aware_mode():
    """Test transfer-aware mode (multi-concept with transfer)"""
    print("\n🧪 Testing Transfer-Aware Mode (Multi-Concept with Transfer)")
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
            print(f"\n✅ Transfer-Aware Mode SUCCESS")
            print(f"   Recommended Concept: {result.get('recommended_concept')}")
            print(f"   Mastery: {result.get('mastery', 'N/A')}")
            print(f"   Mastery Gap: {result.get('mastery_gap', 'N/A')}")
            print(f"   Transfer Bonus: {result.get('transfer_bonus', 'N/A')}")
            print(f"   Exploration Cost: {result.get('exploration_cost', 'N/A')}")
            print(f"   Score: {result.get('score', 'N/A')}")
            print(f"   Selection Engine: {result.get('selection_engine', 'N/A')}")
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
            print(f"\n❌ Transfer-Aware Mode FAILED")
            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"\n❌ Transfer-Aware Mode ERROR: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Two-Level Decision Hierarchy")
    print("=" * 60)
    
    # Test both modes
    normal_success = test_normal_bandit_mode()
    transfer_aware_success = test_transfer_aware_mode()
    
    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    print(f"   Normal Bandit Mode: {'✅ PASSED' if normal_success else '❌ FAILED'}")
    print(f"   Transfer-Aware Mode: {'✅ PASSED' if transfer_aware_success else '❌ FAILED'}")
    print("=" * 60)
    
    all_success = normal_success and transfer_aware_success
    sys.exit(0 if all_success else 1)
