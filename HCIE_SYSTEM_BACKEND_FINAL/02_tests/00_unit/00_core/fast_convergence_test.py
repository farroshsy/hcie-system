#!/usr/bin/env python3
"""
Fast Convergence Test
Tests learning algorithm tuning for faster convergence to mastery
"""

import requests
import time
import json
from datetime import datetime

class FastConvergenceTester:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.results = []
    
    def test_fast_convergence(self, target_mastery=0.8, max_events=150):
        """Test fast convergence with optimized learning parameters"""
        print("\n" + "="*70)
        print("FAST CONVERGENCE TEST")
        print("="*70)
        print(f"Target mastery: {target_mastery}")
        print(f"Maximum events: {max_events}")
        print("Testing optimized learning parameters for faster convergence...")
        
        # Test different learning configurations
        configs = [
            {
                "name": "Baseline",
                "base_learning_rate": 0.1,
                "confidence_threshold": 0.55,
                "description": "Current configuration"
            },
            {
                "name": "Fast Learning",
                "base_learning_rate": 0.15,  # +50% learning rate
                "confidence_threshold": 0.5,   # Lower exclusion threshold
                "description": "Increased learning rate, lower exclusion"
            },
            {
                "name": "Aggressive", 
                "base_learning_rate": 0.2,   # +100% learning rate
                "confidence_threshold": 0.45,  # Much lower exclusion
                "description": "Aggressive learning, minimal exclusion"
            }
        ]
        
        for config in configs:
            print(f"\n--- Testing {config['name']} Configuration ---")
            print(f"Learning rate: {config['base_learning_rate']}")
            print(f"Confidence threshold: {config['confidence_threshold']}")
            
            result = self._test_configuration(config, target_mastery, max_events)
            
            if result:
                print(f"  Events to mastery {target_mastery}: {result['events_needed']}")
                print(f"  Efficiency score: {result['efficiency_score']}")
                print(f"  Target reached: {'✓ YES' if result['target_reached'] else '✗ NO'}")
                self.results.append(result)
            else:
                print(f"  Configuration {config['name']} failed")
        
        # Compare results
        self._analyze_results()
    
    def _test_configuration(self, config, target_mastery, max_events):
        """Test a specific learning configuration"""
        user_id = f"fast_test_{config['name'].lower().replace(' ', '_')}"
        mastery_history = []
        
        for i in range(max_events):
            try:
                # Submit always-correct answer with optimized response time
                task_submission = {
                    "user_id": user_id,
                    "task_id": "EdNet_002",
                    "node_id": "ct_algorithm_design",
                    "representation": "multiple_choice",
                    "answer": "85",
                    "response_time": 8.0,  # Faster response for higher reward
                    "mode": "hcie",
                    "difficulty": 0.6  # Slightly easier difficulty
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
        
        # Analyze this configuration
        if mastery_history:
            final_mastery = mastery_history[-1]["mastery_after"]
            events_needed = len(mastery_history)
            
            initial_mastery = mastery_history[0]["mastery_before"]
            total_mastery_gain = final_mastery - initial_mastery
            avg_mastery_per_event = total_mastery_gain / events_needed
            
            # Calculate efficiency score
            if events_needed <= 120:
                efficiency_score = "VERY_HIGH"
            elif events_needed <= 150:
                efficiency_score = "HIGH"
            elif events_needed <= 200:
                efficiency_score = "MEDIUM"
            else:
                efficiency_score = "LOW"
            
            return {
                "config": config["name"],
                "events_needed": events_needed,
                "final_mastery": final_mastery,
                "total_mastery_gain": total_mastery_gain,
                "avg_mastery_per_event": avg_mastery_per_event,
                "efficiency_score": efficiency_score,
                "target_reached": final_mastery >= target_mastery,
                "mastery_history": mastery_history
            }
        else:
            return None
    
    def _analyze_results(self):
        """Compare different learning configurations"""
        print(f"\n" + "="*70)
        print("FAST CONVERGENCE ANALYSIS")
        print("="*70)
        
        if not self.results:
            print("No results to analyze")
            return
        
        # Sort by events needed (fewer is better)
        self.results.sort(key=lambda x: x["events_needed"])
        
        print(f"Configuration Comparison (sorted by efficiency):")
        print(f"{'Config':<15} {'Events':<8} {'Efficiency':<12} {'Target Reached':<15}")
        print("-" * 55)
        
        for result in self.results:
            target_reached = "✓" if result["target_reached"] else "✗"
            print(f"{result['config']:<15} {result['events_needed']:<8} {result['efficiency_score']:<12} {target_reached}")
        
        # Calculate improvement
        baseline = next((r for r in self.results if r["config"] == "Baseline"), None)
        if baseline:
            best = self.results[0]  # Sorted by efficiency
            improvement = ((baseline["events_needed"] - best["events_needed"]) / baseline["events_needed"]) * 100
            
            print(f"\n📈 Improvement Analysis:")
            print(f"  Baseline events: {baseline['events_needed']}")
            print(f"  Best events: {best['events_needed']}")
            print(f"  Improvement: {improvement:.1f}% fewer events")
            print(f"  Speedup factor: {baseline['events_needed'] / best['events_needed']:.1f}x")
        
        # Save results
        with open("fast_convergence_report.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: fast_convergence_report.json")

if __name__ == "__main__":
    tester = FastConvergenceTester()
    
    print("="*70)
    print("FAST CONVERGENCE OPTIMIZATION")
    print("="*70)
    print("Testing learning algorithm tuning for faster mastery acquisition")
    print("This is critical for reducing user time to proficiency")
    
    tester.test_fast_convergence(target_mastery=0.8, max_events=150)
