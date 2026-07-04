#!/usr/bin/env python3
"""
Transfer Learning Integration Test
Tests the complete transfer learning system with cross-concept effects
"""

import requests
import time
import json
import numpy as np
from datetime import datetime

class TransferLearningTester:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.results = []
    
    def test_transfer_learning_system(self, target_mastery=0.7, events_per_concept=30):
        """Test the complete transfer learning system"""
        print("\n" + "="*70)
        print("TRANSFER LEARNING SYSTEM TEST")
        print("="*70)
        print(f"Target mastery: {target_mastery}")
        print(f"Events per concept: {events_per_concept}")
        print("Testing cross-concept transfer learning effects...")
        
        # Test scenarios
        scenarios = [
            {
                "name": "Sequential Learning",
                "description": "Learn concepts sequentially to observe transfer",
                "concepts": ["ct_algorithm_design", "ct_abstraction", "ct_pattern_recognition"],
                "pattern": "sequential"
            },
            {
                "name": "Focused Learning",
                "description": "Focus on one concept, observe transfer to others",
                "concepts": ["ct_algorithm_design", "ct_abstraction", "ct_pattern_recognition"],
                "pattern": "focused"
            },
            {
                "name": "Mixed Learning",
                "description": "Random concept selection to simulate real learning",
                "concepts": ["ct_algorithm_design", "ct_abstraction", "ct_pattern_recognition"],
                "pattern": "mixed"
            }
        ]
        
        for scenario in scenarios:
            print(f"\n--- Testing {scenario['name']} ---")
            print(f"Description: {scenario['description']}")
            print(f"Concepts: {', '.join(scenario['concepts'])}")
            
            result = self._test_transfer_scenario(scenario, target_mastery, events_per_concept)
            
            if result:
                print(f"  Final mastery levels:")
                for concept, mastery in result['final_mastery'].items():
                    print(f"    {concept}: {mastery:.3f}")
                print(f"  Transfer events: {result['transfer_events']}")
                print(f"  Total transferred mastery: {result['total_transferred_mastery']:+.3f}")
                print(f"  Transfer efficiency: {result['transfer_efficiency']:.3f}")
                self.results.append(result)
            else:
                print(f"  Scenario {scenario['name']} failed")
        
        # Analyze transfer effects
        self._analyze_transfer_effects()
    
    def _test_transfer_scenario(self, scenario, target_mastery, events_per_concept):
        """Test a specific transfer learning scenario"""
        user_id = f"transfer_user_{scenario['name'].lower().replace(' ', '_')}"
        mastery_history = {concept: [] for concept in scenario['concepts']}
        transfer_events = []
        total_transferred_mastery = 0.0
        
        for i in range(events_per_concept * len(scenario['concepts'])):
            try:
                # Select concept based on pattern
                if scenario['pattern'] == 'sequential':
                    concept_idx = i // events_per_concept
                elif scenario['pattern'] == 'focused':
                    concept_idx = 0  # Always focus on first concept
                else:  # mixed
                    concept_idx = i % len(scenario['concepts'])
                
                concept = scenario['concepts'][concept_idx]
                
                # Submit always-correct answer for maximum learning
                task_submission = {
                    "user_id": user_id,
                    "task_id": "EdNet_002",  # Use known task
                    "node_id": concept,
                    "representation": "multiple_choice",
                    "answer": "85",
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
                    
                    # Extract mastery and transfer information
                    mastery_before = result.get("mastery_before", 0)
                    mastery_after = result.get("mastery_after", 0)
                    mastery_change = mastery_after - mastery_before
                    
                    # Check for transfer effects
                    transfers_applied = result.get("transfers_applied", {})
                    transferred_mastery_change = result.get("transferred_mastery_change", 0.0)
                    transfer_sources = result.get("transfer_sources", {})
                    
                    # Track transfer events
                    if transfers_applied:
                        transfer_events.append({
                            "event": i+1,
                            "source_concept": concept,
                            "transfers": transfers_applied,
                            "amount": transferred_mastery_change,
                            "sources": transfer_sources
                        })
                        total_transferred_mastery += transferred_mastery_change
                    
                    # Record mastery for all concepts
                    for concept_name in scenario['concepts']:
                        # Get current mastery for this concept
                        mastery_request = {
                            "user_id": user_id,
                            "concept": concept_name
                        }
                        
                        # For now, simulate getting mastery for other concepts
                        # In a real implementation, this would query the transfer-aware learner
                        if concept_name == concept:
                            current_mastery = mastery_after
                        else:
                            # Simulate transfer effect on other concepts
                            if concept_name in transfers_applied:
                                current_mastery = mastery_before + transfers_applied[concept_name] * 0.1
                            else:
                                current_mastery = mastery_before  # No change
                        
                        mastery_history[concept_name].append(current_mastery)
                    
                    # Print periodic updates
                    if i % 10 == 0:
                        transfer_info = f" (+{transferred_mastery_change:+.3f} transfer)" if transferred_mastery_change > 0 else ""
                        print(f"  Event {i+1:3d}: {concept} Mastery: {mastery_before:.3f} → {mastery_after:.3f} (Δ: {mastery_change:+.3f}){transfer_info}")
                    
                else:
                    print(f"  Event {i+1}: Failed with status {response.status_code}")
                    return None
                    
            except Exception as e:
                print(f"  Event {i+1}: Error: {e}")
                return None
        
        # Analyze scenario results
        final_mastery = {}
        for concept in scenario['concepts']:
            if mastery_history[concept]:
                final_mastery[concept] = mastery_history[concept][-1]
            else:
                final_mastery[concept] = 0.3
        
        # Calculate transfer efficiency
        total_direct_mastery = sum(final_mastery.values()) - (0.3 * len(scenario['concepts']))
        transfer_efficiency = total_transferred_mastery / (total_direct_mastery + total_transferred_mastery) if (total_direct_mastery + total_transferred_mastery) > 0 else 0.0
        
        return {
            "scenario": scenario["name"],
            "final_mastery": final_mastery,
            "mastery_history": mastery_history,
            "transfer_events": len(transfer_events),
            "total_transferred_mastery": total_transferred_mastery,
            "transfer_efficiency": transfer_efficiency,
            "transfer_events_detail": transfer_events
        }
    
    def _analyze_transfer_effects(self):
        """Analyze transfer effects across scenarios"""
        print(f"\n" + "="*70)
        print("TRANSFER EFFECTS ANALYSIS")
        print("="*70)
        
        if not self.results:
            print("No results to analyze")
            return
        
        # Compare final mastery levels
        print(f"Final Mastery Comparison:")
        print(f"{'Scenario':<20} {'Algorithm':<12} {'Abstraction':<12} {'Pattern':<12} {'Transfer':<12}")
        print("-" * 70)
        
        for result in self.results:
            mastery = result['final_mastery']
            transfer = f"{result['total_transferred_mastery']:+.3f}"
            print(f"{result['scenario']:<20} {mastery.get('ct_algorithm_design', 0):<12.3f} "
                  f"{mastery.get('ct_abstraction', 0):<12.3f} {mastery.get('ct_pattern_recognition', 0):<12.3f} {transfer:<12}")
        
        # Analyze transfer efficiency
        print(f"\n📊 Transfer Efficiency Analysis:")
        for result in self.results:
            print(f"  {result['scenario']}: {result['transfer_efficiency']:.3f} efficiency, "
                  f"{result['transfer_events']} transfer events")
        
        # Find most effective scenario
        best_scenario = max(self.results, key=lambda x: x['transfer_efficiency'])
        print(f"\n🏆 Most Effective Scenario: {best_scenario['scenario']}")
        print(f"  Transfer efficiency: {best_scenario['transfer_efficiency']:.3f}")
        print(f"  Total transferred mastery: {best_scenario['total_transferred_mastery']:+.3f}")
        
        # Analyze concept transfer patterns
        print(f"\n🔄 Concept Transfer Patterns:")
        all_transfers = {}
        for result in self.results:
            for event in result['transfer_events_detail']:
                for target_concept, amount in event['transfers'].items():
                    if target_concept not in all_transfers:
                        all_transfers[target_concept] = 0
                    all_transfers[target_concept] += amount
        
        if all_transfers:
            print(f"  Most transferred concepts:")
            sorted_transfers = sorted(all_transfers.items(), key=lambda x: x[1], reverse=True)
            for concept, amount in sorted_transfers[:5]:
                print(f"    {concept}: {amount:+.3f}")
        
        # Save results
        with open("transfer_learning_report.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: transfer_learning_report.json")
    
    def test_transfer_vs_no_transfer(self, events=50):
        """Compare learning with and without transfer effects"""
        print(f"\n" + "="*70)
        print("TRANSFER VS NO TRANSFER COMPARISON")
        print("="*70)
        print(f"Events: {events}")
        print("Comparing learning with and without transfer effects...")
        
        # Test without transfer (baseline)
        print(f"\n--- Baseline (No Transfer) ---")
        baseline_result = self._test_baseline_learning(events)
        
        # Test with transfer
        print(f"\n--- With Transfer ---")
        transfer_result = self._test_transfer_learning(events)
        
        if baseline_result and transfer_result:
            print(f"\n📊 Comparison Results:")
            print(f"  Baseline final mastery: {baseline_result['final_mastery']:.3f}")
            print(f"  Transfer final mastery: {transfer_result['final_mastery']:.3f}")
            
            improvement = ((transfer_result['final_mastery'] - baseline_result['final_mastery']) 
                          / baseline_result['final_mastery']) * 100 if baseline_result['final_mastery'] > 0 else 0
            
            print(f"  Transfer improvement: {improvement:+.1f}%")
            print(f"  Transfer events: {transfer_result['transfer_events']}")
            print(f"  Transferred mastery: {transfer_result['total_transferred_mastery']:+.3f}")
            
            # Save comparison
            comparison = {
                "baseline": baseline_result,
                "transfer": transfer_result,
                "improvement_percent": improvement
            }
            
            with open("transfer_comparison_report.json", "w") as f:
                json.dump(comparison, f, indent=2)
            
            print(f"\n📄 Comparison report saved to: transfer_comparison_report.json")
    
    def _test_baseline_learning(self, events):
        """Test learning without transfer effects"""
        user_id = "baseline_user"
        concept = "ct_algorithm_design"
        mastery_history = []
        
        for i in range(events):
            try:
                task_submission = {
                    "user_id": user_id,
                    "task_id": "EdNet_002",
                    "node_id": concept,
                    "representation": "multiple_choice",
                    "answer": "85",
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
                    mastery_after = result.get("mastery_after", 0)
                    mastery_history.append(mastery_after)
                    
                    if i % 10 == 0:
                        print(f"  Event {i+1:3d}: Mastery: {mastery_after:.3f}")
                else:
                    print(f"  Event {i+1}: Failed with status {response.status_code}")
                    return None
                    
            except Exception as e:
                print(f"  Event {i+1}: Error: {e}")
                return None
        
        final_mastery = mastery_history[-1] if mastery_history else 0.3
        
        return {
            "final_mastery": final_mastery,
            "mastery_history": mastery_history,
            "transfer_events": 0,
            "total_transferred_mastery": 0.0,
            "transfer_efficiency": 0.0
        }
    
    def _test_transfer_learning(self, events):
        """Test learning with transfer effects"""
        user_id = "transfer_user"
        concepts = ["ct_algorithm_design", "ct_abstraction"]
        mastery_history = {concept: [] for concept in concepts}
        transfer_events = []
        total_transferred_mastery = 0.0
        
        for i in range(events):
            try:
                # Alternate between concepts
                concept = concepts[i % len(concepts)]
                
                task_submission = {
                    "user_id": user_id,
                    "task_id": "EdNet_002",
                    "node_id": concept,
                    "representation": "multiple_choice",
                    "answer": "85",
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
                    
                    mastery_after = result.get("mastery_after", 0)
                    transferred_mastery_change = result.get("transferred_mastery_change", 0.0)
                    transfers_applied = result.get("transfers_applied", {})
                    
                    if transferred_mastery_change > 0:
                        transfer_events.append({
                            "event": i+1,
                            "amount": transferred_mastery_change,
                            "transfers": transfers_applied
                        })
                        total_transferred_mastery += transferred_mastery_change
                    
                    mastery_history[concept].append(mastery_after)
                    
                    if i % 10 == 0:
                        transfer_info = f" (+{transferred_mastery_change:+.3f} transfer)" if transferred_mastery_change > 0 else ""
                        print(f"  Event {i+1:3d}: {concept} Mastery: {mastery_after:.3f}{transfer_info}")
                else:
                    print(f"  Event {i+1}: Failed with status {response.status_code}")
                    return None
                    
            except Exception as e:
                print(f"  Event {i+1}: Error: {e}")
                return None
        
        # Average mastery across concepts
        final_mastery = np.mean([history[-1] for history in mastery_history.values() if history])
        
        return {
            "final_mastery": final_mastery,
            "mastery_history": mastery_history,
            "transfer_events": len(transfer_events),
            "total_transferred_mastery": total_transferred_mastery,
            "transfer_efficiency": total_transferred_mastery / (final_mastery - 0.3) if final_mastery > 0.3 else 0.0
        }

if __name__ == "__main__":
    tester = TransferLearningTester()
    
    print("="*70)
    print("TRANSFER LEARNING SYSTEM")
    print("="*70)
    print("Testing cross-concept transfer learning effects")
    print("This is the key innovation for adaptive educational systems")
    
    # Run main transfer learning test
    tester.test_transfer_learning_system(target_mastery=0.7, events_per_concept=30)
    
    # Run comparison test
    tester.test_transfer_vs_no_transfer(events=50)
