#!/usr/bin/env python3
"""
Real-User Simulation Test
Tests learning under realistic conditions with noise, forgetting, and regression
"""

import requests
import time
import json
import random
from datetime import datetime

class RealUserSimulationTester:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.results = []
    
    def test_real_user_simulation(self, total_events=200, target_mastery=0.7):
        """Test learning under realistic user conditions"""
        print("\n" + "="*70)
        print("REAL-USER SIMULATION TEST")
        print("="*70)
        print(f"Total events: {total_events}")
        print(f"Target mastery: {target_mastery}")
        print("Testing learning under realistic conditions with noise and forgetting...")
        
        # Test different simulation scenarios
        scenarios = [
            {
                "name": "Optimal Learner",
                "correctness_rate": 0.9,
                "response_time_mean": 8.0,
                "response_time_std": 2.0,
                "forgetting_enabled": False,
                "description": "Ideal learning conditions"
            },
            {
                "name": "Average Learner",
                "correctness_rate": 0.7,
                "response_time_mean": 12.0,
                "response_time_std": 5.0,
                "forgetting_enabled": False,
                "description": "Typical student performance"
            },
            {
                "name": "Struggling Learner",
                "correctness_rate": 0.5,
                "response_time_mean": 20.0,
                "response_time_std": 8.0,
                "forgetting_enabled": False,
                "description": "Below-average performance"
            },
            {
                "name": "Realistic with Forgetting",
                "correctness_rate": 0.7,
                "response_time_mean": 12.0,
                "response_time_std": 5.0,
                "forgetting_enabled": True,
                "description": "Average learner with forgetting effects"
            }
        ]
        
        for scenario in scenarios:
            print(f"\n--- Testing {scenario['name']} ---")
            print(f"Correctness rate: {scenario['correctness_rate']}")
            print(f"Response time: {scenario['response_time_mean']}±{scenario['response_time_std']}s")
            print(f"Forgetting: {'Enabled' if scenario['forgetting_enabled'] else 'Disabled'}")
            
            result = self._test_scenario(scenario, total_events, target_mastery)
            
            if result:
                print(f"  Final mastery: {result['final_mastery']:.3f}")
                print(f"  Target reached: {'✓ YES' if result['target_reached'] else '✗ NO'}")
                print(f"  Average mastery per event: {result['avg_mastery_per_event']:+.6f}")
                print(f"  Regression events: {result['regression_events']}")
                print(f"  Forgetting rate: {result['forgetting_rate']:.3f}")
                self.results.append(result)
            else:
                print(f"  Scenario {scenario['name']} failed")
        
        # Compare scenarios
        self._analyze_scenarios()
    
    def _test_scenario(self, scenario, total_events, target_mastery):
        """Test a specific user scenario"""
        user_id = f"real_user_{scenario['name'].lower().replace(' ', '_')}"
        mastery_history = []
        regression_events = 0
        forgetting_events = 0
        
        for i in range(total_events):
            try:
                # Determine if this answer is correct based on scenario
                is_correct = random.random() < scenario['correctness_rate']
                
                # Generate realistic response time
                response_time = max(5.0, random.gauss(scenario['response_time_mean'], scenario['response_time_std']))
                
                # Simulate forgetting (occasionally submit wrong answer even with high correctness rate)
                if scenario['forgetting_enabled'] and i > 20:  # Start forgetting after some learning
                    forgetting_probability = 0.1 * (i / total_events)  # Increase forgetting over time
                    if random.random() < forgetting_probability:
                        is_correct = False
                        forgetting_events += 1
                
                # Submit answer
                task_submission = {
                    "user_id": user_id,
                    "task_id": "EdNet_002",
                    "node_id": "ct_algorithm_design",
                    "representation": "multiple_choice",
                    "answer": "85" if is_correct else "42",
                    "response_time": response_time,
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
                    
                    mastery_before = result.get("mastery_before", 0)
                    mastery_after = result.get("mastery_after", 0)
                    mastery_change = mastery_after - mastery_before
                    reward = result.get("reward", 0)
                    
                    # Track regression events (mastery decreases)
                    if mastery_change < -0.001:  # Significant decrease
                        regression_events += 1
                    
                    mastery_history.append({
                        "event": i+1,
                        "mastery_before": mastery_before,
                        "mastery_after": mastery_after,
                        "mastery_change": mastery_change,
                        "reward": reward,
                        "is_correct": is_correct,
                        "response_time": response_time,
                        "timestamp": time.time()
                    })
                    
                    # Print periodic updates
                    if i % 25 == 0:
                        status = "✓" if is_correct else "✗"
                        print(f"  Event {i+1:3d}: {status} Mastery: {mastery_before:.3f} → {mastery_after:.3f} (Δ: {mastery_change:+.3f})")
                    
                    # Check if target mastery reached
                    if mastery_after >= target_mastery and not scenario['forgetting_enabled']:
                        events_needed = i + 1
                        break
                else:
                    print(f"  Event {i+1}: Failed with status {response.status_code}")
                    return None
                    
            except Exception as e:
                print(f"  Event {i+1}: Error: {e}")
                return None
        
        # Analyze scenario results
        if mastery_history:
            final_mastery = mastery_history[-1]["mastery_after"]
            events_needed = len(mastery_history)
            
            initial_mastery = mastery_history[0]["mastery_before"]
            total_mastery_gain = final_mastery - initial_mastery
            avg_mastery_per_event = total_mastery_gain / events_needed
            
            # Calculate forgetting rate
            forgetting_rate = forgetting_events / events_needed if scenario['forgetting_enabled'] else 0.0
            
            # Calculate stability (how often mastery regresses)
            stability_rate = 1.0 - (regression_events / events_needed)
            
            return {
                "scenario": scenario["name"],
                "events_needed": events_needed,
                "final_mastery": final_mastery,
                "total_mastery_gain": total_mastery_gain,
                "avg_mastery_per_event": avg_mastery_per_event,
                "target_reached": final_mastery >= target_mastery,
                "regression_events": regression_events,
                "forgetting_events": forgetting_events,
                "forgetting_rate": forgetting_rate,
                "stability_rate": stability_rate,
                "mastery_history": mastery_history
            }
        else:
            return None
    
    def _analyze_scenarios(self):
        """Compare different user scenarios"""
        print(f"\n" + "="*70)
        print("REAL-USER SIMULATION ANALYSIS")
        print("="*70)
        
        if not self.results:
            print("No scenario results to analyze")
            return
        
        print(f"Scenario Comparison:")
        print(f"{'Scenario':<20} {'Final Mastery':<15} {'Target':<8} {'Stability':<12} {'Forgetting':<12}")
        print("-" * 70)
        
        for result in self.results:
            target_reached = "✓" if result["target_reached"] else "✗"
            print(f"{result['scenario']:<20} {result['final_mastery']:<15.3f} {target_reached:<8} {result['stability_rate']:<12.1%} {result['forgetting_rate']:<12.1%}")
        
        # Analyze impact of different factors
        print(f"\n📊 Factor Analysis:")
        
        # Impact of correctness rate
        optimal = next((r for r in self.results if r["scenario"] == "Optimal Learner"), None)
        average = next((r for r in self.results if r["scenario"] == "Average Learner"), None)
        struggling = next((r for r in self.results if r["scenario"] == "Struggling Learner"), None)
        
        if optimal and average and struggling:
            print(f"  Impact of Correctness Rate:")
            print(f"    Optimal (90% correct): {optimal['final_mastery']:.3f} mastery")
            print(f"    Average (70% correct): {average['final_mastery']:.3f} mastery")
            print(f"    Struggling (50% correct): {struggling['final_mastery']:.3f} mastery")
            
            mastery_drop_optimal_to_average = ((optimal['final_mastery'] - average['final_mastery']) / optimal['final_mastery']) * 100
            mastery_drop_average_to_struggling = ((average['final_mastery'] - struggling['final_mastery']) / average['final_mastery']) * 100
            
            print(f"    Optimal→Average: {mastery_drop_optimal_to_average:.1f}% mastery loss")
            print(f"    Average→Struggling: {mastery_drop_average_to_struggling:.1f}% mastery loss")
        
        # Impact of forgetting
        with_forgetting = next((r for r in self.results if r["scenario"] == "Realistic with Forgetting"), None)
        if with_forgetting and average:
            forgetting_impact = ((average['final_mastery'] - with_forgetting['final_mastery']) / average['final_mastery']) * 100
            print(f"\n  Impact of Forgetting:")
            print(f"    Without forgetting: {average['final_mastery']:.3f} mastery")
            print(f"    With forgetting: {with_forgetting['final_mastery']:.3f} mastery")
            print(f"    Forgetting impact: {forgetting_impact:.1f}% mastery loss")
            print(f"    Forgetting rate: {with_forgetting['forgetting_rate']:.1%}")
        
        # Stability analysis
        print(f"\n🔄 Stability Analysis:")
        for result in self.results:
            print(f"    {result['scenario']}: {result['stability_rate']:.1%} stable, {result['regression_events']} regression events")
        
        # Save results
        with open("real_user_simulation_report.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: real_user_simulation_report.json")

if __name__ == "__main__":
    tester = RealUserSimulationTester()
    
    print("="*70)
    print("REAL-USER SIMULATION")
    print("="*70)
    print("Testing learning under realistic conditions with noise and forgetting")
    print("This is critical for understanding real-world learning dynamics")
    
    tester.test_real_user_simulation(total_events=200, target_mastery=0.7)
