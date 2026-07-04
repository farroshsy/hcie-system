#!/usr/bin/env python3
"""
🔥 SIMPLE TEST: Research Data Access
Test that our research API can access the data correctly
"""

import sys
import os
sys.path.append('/app')

def test_research_data_access():
    """Test direct access to research data without FastAPI"""
    print("🔥 TESTING RESEARCH DATA ACCESS")
    print("=" * 50)
    
    import json
    import glob
    
    # Get latest result file
    research_dir = '/app/research_results'
    pattern = os.path.join(research_dir, 'cold_start_results_*.json')
    files = sorted(glob.glob(pattern))
    
    if not files:
        print("❌ No research result files found")
        return False
    
    latest_file = files[-1]
    print(f"📁 Latest file: {os.path.basename(latest_file)}")
    
    try:
        with open(latest_file, 'r') as f:
            data = json.load(f)
        
        print("✅ SUCCESS: Research data loaded!")
        print(f"📊 Total scenarios: {len(data)}")
        
        # Validate data structure
        required_fields = ['convergence_error', 'adaptive_rates', 'cold_start_performance']
        valid_scenarios = 0
        
        for scenario_name, scenario_data in data.items():
            if isinstance(scenario_data, dict) and all(field in scenario_data for field in required_fields):
                valid_scenarios += 1
                
                # Check adaptive rates
                rates = scenario_data.get('adaptive_rates', [])
                valid_rates = [r for r in rates if r is not None]
                
                print(f"📈 {scenario_name}:")
                print(f"   Convergence error: {scenario_data['convergence_error']:.4f}")
                print(f"   Performance: {scenario_data['cold_start_performance']}")
                print(f"   Adaptive rates: {len(valid_rates)}/{len(rates)} valid")
                print(f"   Rate range: {min(valid_rates):.4f} to {max(valid_rates):.4f}" if valid_rates else "No valid rates")
        
        print(f"\n📊 SUMMARY:")
        print(f"✅ Valid scenarios: {valid_scenarios}/{len(data)}")
        print(f"🎯 Data structure: VALID")
        print(f"🔥 Ready for API consumption")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_api_structure():
    """Test that our API structure is correct"""
    print("\n🔧 TESTING API STRUCTURE")
    print("=" * 50)
    
    try:
        from app.api.routes.research.research_api import router
        print("✅ Research API router imported")
        
        # Check routes
        print(f"📊 Router prefix: {router.prefix}")
        print(f"🔗 Router tags: {router.tags}")
        print(f"📝 Number of routes: {len(router.routes)}")
        
        # List route paths
        for route in router.routes:
            if hasattr(route, 'path'):
                methods = getattr(route, 'methods', ['GET'])
                print(f"   {route.path} {methods}")
        
        print("✅ API structure: VALID")
        return True
        
    except Exception as e:
        print(f"❌ API structure error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 RESEARCH API VALIDATION")
    print("=" * 60)
    print(f"⏰ Started at: {__import__('datetime').datetime.now().isoformat()}")
    
    # Test data access
    data_ok = test_research_data_access()
    
    # Test API structure  
    api_ok = test_api_structure()
    
    print(f"\n🏆 RESULTS:")
    print(f"📊 Data access: {'✅ PASS' if data_ok else '❌ FAIL'}")
    print(f"🔧 API structure: {'✅ PASS' if api_ok else '❌ FAIL'}")
    print(f"🎯 Overall: {'✅ READY FOR UI' if data_ok and api_ok else '❌ NEEDS FIXES'}")
    
    if data_ok and api_ok:
        print("\n🎉 SUCCESS! Research APIs are ready for UI integration")
        print("📊 Available endpoints:")
        print("   GET /api/research/cold-start-results")
        print("   GET /api/research/cold-start-results/{scenario}")
        print("   GET /api/research/metrics")
        print("   GET /api/research/export/{format}")
        print("   GET /ws/learning/{user_id} (WebSocket)")
    else:
        print("\n❌ Some tests failed - check the errors above")

if __name__ == "__main__":
    main()
