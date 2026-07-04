#!/usr/bin/env python3
"""
Learning Efficiency Test
Measures how many interactions are needed to reach mastery = 0.8
"""

import requests
import time
import json
from datetime import datetime

class LearningEfficiencyTester:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.results = []
    
    def test_learning_efficiency(self, target_mastery=0.8, max_events=200):
        """Test learning efficiency by measuring interactions to reach target mastery"""
        print("\n" + "="*70)
        print("LEARNING EFFICIENCY TEST")
        print("="*70)
        print(f"Target mastery: {target_mastery}")
        print(f"Maximum events: {max_events}")
        print(f"Measuring interactions needed to reach mastery threshold...")
        
        user_id = "efficiency_user"
        mastery_history = []
        
        for i in range(max_events):
            try:
                # Submit always-correct answer to maximize learning
                task_submission = {
                    "user_id": user_id,
                    "task_id": "EdNet_002",  # Known task with correct answer "85"
                    "node_id": "ct_algorithm_design",
                    "representation": "multiple_choice",
                    "answer": "85",  # Always correct for fastest learning
                    "response_time": 10.0,  # Consistent response time
                    "mode": "hcie",
                    "difficulty": 0.7
                }
                
                response = requests.post(
                    f"{self.base_url}/api/v1/tasks/submit",
                    json=task_submission,
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Validate we're actually learning
                    assert result.get("correct", False), f"Evaluation pipeline broken at event {i+1}"
                    
                    mastery_before = result.get("mastery_before", 0)
                    mastery_after = result.get("mastery_after", 0)
                    mastery_change = mastery_after - mastery_before
                    reward = result.get("reward", 0)
                    
                    mastery_history.append({
                        "event": i+1,
                        "mastery_before": mastery_before,
                        "mastery_after": mastery_after,
                        "mastery_change": mastery_change,
                        "reward": reward,
                        "timestamp": time.time()
                    })
                    
                    print(f"  Event {i+1:3d}: Mastery: {mastery_before:.3f} → {mastery_after:.3f} (Δ: {mastery_change:+.3f}), Reward: {reward:.3f}")
                    
                    # Check if target mastery reached
                    if mastery_after >= target_mastery:
                        events_needed = i + 1
                        break
                else:
                    print(f"  Event {i+1}: Failed with status {response.status_code}")
                    return None
                    
            except Exception as e:
                print(f"  Event {i+1}: Error: {e}")
                return None
        
        # Analyze efficiency
        if mastery_history:
            final_mastery = mastery_history[-1]["mastery_after"]
            events_needed = len(mastery_history)
            
            # Calculate learning metrics
            initial_mastery = mastery_history[0]["mastery_before"]
            total_mastery_gain = final_mastery - initial_mastery
            avg_mastery_per_event = total_mastery_gain / events_needed
            
            # Calculate learning curve parameters
            if events_needed < max_events:
                efficiency_score = "HIGH"
            elif events_needed < max_events * 0.8:
                efficiency_score = "MEDIUM"
            else:
                efficiency_score = "LOW"
            
            print(f"\n  Learning Efficiency Analysis:")
            print(f"    Initial mastery: {initial_mastery:.3f}")
            print(f"    Final mastery: {final_mastery:.3f}")
            print(f"    Total mastery gain: {total_mastery_gain:+.3f}")
            print(f"    Events to mastery {target_mastery}: {events_needed}")
            print(f"    Average mastery per event: {avg_mastery_per_event:+.6f}")
            print(f"    Efficiency score: {efficiency_score}")
            
            # Project to mastery 0.8 if not reached
            if final_mastery < target_mastery:
                remaining_mastery = target_mastery - final_mastery
                projected_events = int(remaining_mastery / avg_mastery_per_event)
                print(f"    Projected events to mastery {target_mastery}: ~{projected_events}")
            
            return {
                "events_needed": events_needed,
                "final_mastery": final_mastery,
                "total_mastery_gain": total_mastery_gain,
                "avg_mastery_per_event": avg_mastery_per_event,
                "efficiency_score": efficiency_score,
                "target_reached": final_mastery >= target_mastery,
                "mastery_history": mastery_history
            }
        else:
            print("  No learning data collected")
            return None

if __name__ == "__main__":
    tester = LearningEfficiencyTester()
    
    print("="*70)
    print("LEARNING EFFICIENCY MEASUREMENT")
    print("="*70)
    print("Measuring interactions needed to reach mastery = 0.8")
    print("This metric is critical for academic papers and product decisions")
    
    result = tester.test_learning_efficiency(target_mastery=0.8, max_events=200)
    
    if result:
        print(f"\n🎯 LEARNING EFFICIENCY RESULT:")
        print(f"   Events to mastery 0.8: {result['events_needed']}")
        print(f"   Efficiency score: {result['efficiency_score']}")
        print(f"   Target reached: {'✓ YES' if result['target_reached'] else '✗ NO'}")
        
        # Save results
        with open("learning_efficiency_report.json", "w") as f:
            json.dump(result, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: learning_efficiency_report.json")
    else:
        print("\n❌ Learning efficiency test failed")
