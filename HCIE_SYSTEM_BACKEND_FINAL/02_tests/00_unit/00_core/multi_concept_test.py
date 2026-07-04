#!/usr/bin/env python3
"""
Multi-Concept Learning Test
Tests learning across multiple CT concepts and transfer effects
"""

import requests
import time
import json
from datetime import datetime

class MultiConceptTester:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.results = []
    
    def test_multi_concept_learning(self, target_mastery=0.7, events_per_concept=50):
        """Test learning across multiple CT concepts"""
        print("\n" + "="*70)
        print("MULTI-CONCEPT LEARNING TEST")
        print("="*70)
        print(f"Target mastery: {target_mastery}")
        print(f"Events per concept: {events_per_concept}")
        print("Testing learning across multiple CT concepts and transfer effects...")
        
        # Define CT concepts to test
        concepts = [
            {"name": "ct_algorithm_design", "task_id": "EdNet_002", "answer": "85"},
            {"name": "ct_problem_identification", "task_id": "EdNet_001", "answer": "No validation"},
            {"name": "ct_abstraction", "task_id": "q1", "answer": "No validation"},
            {"name": "ct_algorithm_tracing", "task_id": "q2", "answer": "5"},
            {"name": "ct_pattern_recognition", "task_id": "q3", "answer": "Details"}
        ]
        
        user_id = "multi_concept_user"
        concept_results = {}
        
        for concept in concepts:
            print(f"\n--- Learning {concept['name']} ---")
            
            result = self._test_concept_learning(user_id, concept, target_mastery, events_per_concept)
            
            if result:
                concept_results[concept['name']] = result
                print(f"  Events to mastery {target_mastery}: {result['events_needed']}")
                print(f"  Final mastery: {result['final_mastery']:.3f}")
                print(f"  Average mastery per event: {result['avg_mastery_per_event']:+.6f}")
            else:
                print(f"  Concept {concept['name']} failed to reach target mastery")
        
        # Analyze multi-concept effects
        self._analyze_multi_concept_effects(concept_results)
    
    def _test_concept_learning(self, user_id, concept, target_mastery, max_events):
        """Test learning for a specific concept"""
        mastery_history = []
        
        for i in range(max_events):
            try:
                # Submit always-correct answer for this concept
                task_submission = {
                    "user_id": user_id,
                    "task_id": concept["task_id"],
                    "node_id": concept["name"],
                    "representation": "multiple_choice",
                    "answer": concept["answer"],
                    "response_time": 10.0,
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
                    
                    # Validate evaluation pipeline
                    assert result.get("correct", False), f"Evaluation pipeline broken for {concept['name']}"
                    
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
                    
                    if i % 10 == 0:  # Print every 10th event
                        print(f"  Event {i+1:3d}: Mastery: {mastery_before:.3f} → {mastery_after:.3f} (Δ: {mastery_change:+.3f})")
                    
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
        
        # Analyze this concept's learning
        if mastery_history:
            final_mastery = mastery_history[-1]["mastery_after"]
            events_needed = len(mastery_history)
            
            initial_mastery = mastery_history[0]["mastery_before"]
            total_mastery_gain = final_mastery - initial_mastery
            avg_mastery_per_event = total_mastery_gain / events_needed
            
            return {
                "concept": concept["name"],
                "events_needed": events_needed,
                "final_mastery": final_mastery,
                "total_mastery_gain": total_mastery_gain,
                "avg_mastery_per_event": avg_mastery_per_event,
                "target_reached": final_mastery >= target_mastery,
                "mastery_history": mastery_history
            }
        else:
            return None
    
    def _analyze_multi_concept_effects(self, concept_results):
        """Analyze multi-concept learning effects"""
        print(f"\n" + "="*70)
        print("MULTI-CONCEPT ANALYSIS")
        print("="*70)
        
        if not concept_results:
            print("No concept results to analyze")
            return
        
        # Sort by events needed (fewer is better)
        sorted_results = sorted(concept_results.items(), key=lambda x: x[1]["events_needed"])
        
        print(f"Concept Learning Comparison:")
        print(f"{'Concept':<25} {'Events':<8} {'Final Mastery':<15} {'Avg Mastery/Event':<18}")
        print("-" * 70)
        
        total_events = 0
        total_mastery_gain = 0
        concepts_reached_target = 0
        
        for concept_name, result in sorted_results:
            print(f"{concept_name:<25} {result['events_needed']:<8} {result['final_mastery']:<15.3f} {result['avg_mastery_per_event']:<+18.6f}")
            
            total_events += result["events_needed"]
            total_mastery_gain += result["total_mastery_gain"]
            if result["target_reached"]:
                concepts_reached_target += 1
        
        # Calculate overall metrics
        avg_events_per_concept = total_events / len(concept_results)
        avg_mastery_per_event = total_mastery_gain / total_events
        target_success_rate = concepts_reached_target / len(concept_results)
        
        print(f"\n📊 Multi-Concept Metrics:")
        print(f"  Total concepts tested: {len(concept_results)}")
        print(f"  Concepts reaching target: {concepts_reached_target}/{len(concept_results)} ({target_success_rate*100:.1f}%)")
        print(f"  Average events per concept: {avg_events_per_concept:.1f}")
        print(f"  Average mastery per event: {avg_mastery_per_event:+.6f}")
        print(f"  Overall target success rate: {target_success_rate*100:.1f}%")
        
        # Analyze transfer effects (if any)
        if len(concept_results) > 1:
            print(f"\n🔄 Transfer Effects Analysis:")
            
            # Check if later concepts learn faster (positive transfer)
            events_by_order = [result["events_needed"] for _, result in sorted_results]
            
            if len(events_by_order) >= 2:
                first_half_avg = sum(events_by_order[:len(events_by_order)//2]) / (len(events_by_order)//2)
                second_half_avg = sum(events_by_order[len(events_by_order)//2:]) / (len(events_by_order) - len(events_by_order)//2)
                
                transfer_effect = (first_half_avg - second_half_avg) / first_half_avg * 100
                
                print(f"  First half concepts avg events: {first_half_avg:.1f}")
                print(f"  Second half concepts avg events: {second_half_avg:.1f}")
                print(f"  Transfer effect: {transfer_effect:+.1f}%")
                
                if transfer_effect > 5:
                    print(f"  → Positive transfer detected")
                elif transfer_effect < -5:
                    print(f"  → Negative transfer detected")
                else:
                    print(f"  → No significant transfer effect")
        
        # Save results
        multi_concept_results = {
            "concept_results": {k: v for k, v in concept_results.items()},
            "summary": {
                "total_concepts": len(concept_results),
                "concepts_reached_target": concepts_reached_target,
                "target_success_rate": target_success_rate,
                "avg_events_per_concept": avg_events_per_concept,
                "avg_mastery_per_event": avg_mastery_per_event
            }
        }
        
        with open("multi_concept_report.json", "w") as f:
            json.dump(multi_concept_results, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: multi_concept_report.json")

if __name__ == "__main__":
    tester = MultiConceptTester()
    
    print("="*70)
    print("MULTI-CONCEPT LEARNING")
    print("="*70)
    print("Testing learning across multiple CT concepts and transfer effects")
    print("This is critical for understanding cross-concept learning dynamics")
    
    tester.test_multi_concept_learning(target_mastery=0.7, events_per_concept=50)
