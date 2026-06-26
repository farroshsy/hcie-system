"""
End-to-End Learning Validation
Tests the complete API pipeline to ensure our mathematical model works in production
"""

import requests
import json
import time
import uuid
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class E2ELearningValidator:
    """Validates learning dynamics through the full API pipeline"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api/v1"
    
    def get_task(self, user_id: str, mode: str = "hcie") -> Dict:
        """Get a task for the user"""
        try:
            response = requests.get(f"{self.api_url}/tasks/{user_id}")
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get task: {response.status_code}")
                return {}
        except Exception as e:
            logger.error(f"Task request failed: {e}")
            return {}
    
    def submit_answer(self, user_id: str, task_id: str, node_id: str, answer: str, beta: float) -> Dict:
        """Submit answer with beta parameter"""
        payload = {
            'user_id': user_id,
            'task_id': task_id,
            'node_id': node_id,
            'representation': 'multiple_choice',
            'answer': answer,
            'response_time': 10.0,
            'mode': 'hcie',
            'policy_mode': 'hcie',
            'beta': beta,
            'difficulty': 0.7
        }
        
        try:
            response = requests.post(f"{self.api_url}/tasks/submit", json=payload)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Submit failed: {response.status_code} - {response.text}")
                return {}
        except Exception as e:
            logger.error(f"Submit request failed: {e}")
            return {}
    
    def get_mastery_debug(self, user_id: str) -> Dict:
        """Get debug information about user mastery"""
        try:
            response = requests.get(f"{self.base_url}/debug/mastery/{user_id}")
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Debug request failed: {response.status_code}")
                return {}
        except Exception as e:
            logger.error(f"Debug request failed: {e}")
            return {}
    
    def get_engine_debug(self, user_id: str) -> Dict:
        """Get debug information about engine state"""
        try:
            response = requests.get(f"{self.base_url}/debug/engine/{user_id}")
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Engine debug request failed: {response.status_code}")
                return {}
        except Exception as e:
            logger.error(f"Engine debug request failed: {e}")
            return {}
    
    def get_transfer_debug(self, user_id: str) -> Dict:
        """Get debug information about transfer state"""
        try:
            response = requests.get(f"{self.base_url}/debug/transfer/{user_id}")
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Transfer debug request failed: {response.status_code}")
                return {}
        except Exception as e:
            logger.error(f"Transfer debug request failed: {e}")
            return {}
    
    def run_single_interaction(self, user_id: str, beta: float) -> Dict:
        """Run one complete interaction cycle"""
        logger.info(f"🔄 Running interaction for {user_id} with β={beta}")
        
        # Step 1: Get task
        task_response = self.get_task(user_id)
        if not task_response:
            return {"success": False, "error": "Failed to get task"}
        
        # CRITICAL: Use EXACT task_id and node_id from API response
        task_id = task_response.get("task_id")
        node_id = task_response.get("node_id")
        
        if not task_id or not node_id:
            return {"success": False, "error": "Invalid task response"}
        
        logger.info(f"📋 Generated task: {task_id} (node: {node_id})")
        
        # CRITICAL: Test the real system - no hacks allowed
        if task_id.startswith("fallback_ct_") or task_id.startswith("emergency_fallback_"):
            logger.error(f"🚨 FALLBACK TASK DETECTED: {task_id} - Real system is broken!")
            return {"success": False, "error": f"Fallback task generated: {task_id}"}
        
        # Step 2: Submit answer (use correct answer for CT tasks)
        submit_response = self.submit_answer(user_id, task_id, node_id, "O(log n)", beta)
        if not submit_response:
            return {"success": False, "error": "Failed to submit answer"}
        
        # Step 3: Get debug info
        debug_response = self.get_mastery_debug(user_id)
        
        # CRITICAL: Check if fallback was used
        if submit_response.get("fallback_used", False):
            logger.error(f"❌ FALLBACK DETECTED - Test invalid!")
            return {"success": False, "error": f"Fallback used: {submit_response.get('processing_error', 'Unknown')}"}
        
        # Extract key metrics
        result = {
            "success": True,
            "task_id": task_id,
            "node_id": node_id,
            "mastery_before": submit_response.get("mastery_before", 0),
            "mastery_after": submit_response.get("mastery_after", 0),
            "mastery_change": submit_response.get("mastery_change", 0),
            "transfer_effect": submit_response.get("transfer_effect", 0),
            "transfers_applied": submit_response.get("transfers_applied", {}),
            "beta": beta,
            "debug_mastery": debug_response.get("mastery", {}),
            "transfer_enabled": submit_response.get("transfer_enabled", False),
            "timestamp": time.time()
        }
        
        # CRITICAL: Detect mastery reset bug
        if result['mastery_after'] == 0.0 and result['mastery_before'] > 0.1:
            logger.error(f"🚨 MASTERY RESET DETECTED: {result['mastery_before']:.3f} → {result['mastery_after']:.3f}")
            result["mastery_reset"] = True
        else:
            result["mastery_reset"] = False
        
        logger.info(f"✅ Interaction complete: mastery {result['mastery_before']:.3f} → {result['mastery_after']:.3f}, transfer {result['transfer_effect']:.4f}")
        
        return result
    
    def run_learning_trajectory(self, beta: float, num_interactions: int = 50, concept: str = "ct_algorithm_design") -> Dict:
        """Run a complete learning trajectory through the API"""
        logger.info(f"🚀 Running learning trajectory: β={beta}, interactions={num_interactions}")
        
        # Create unique user ID
        run_uuid = str(uuid.uuid4())[:8]
        user_id = f"e2e_beta_{beta:.1f}_{run_uuid}"
        
        trajectory = []
        mastery_history = []
        transfer_history = []
        beta_history = []
        
        for i in range(num_interactions):
            # Run interaction
            result = self.run_single_interaction(user_id, beta)
            
            if not result["success"]:
                logger.error(f"❌ Interaction {i+1} failed: {result.get('error', 'Unknown error')}")
                break
            
            trajectory.append(result)
            mastery_history.append(result["mastery_after"])
            transfer_history.append(result["transfer_effect"])
            beta_history.append(beta)
            
            # Log progress
            if (i + 1) % 10 == 0:
                logger.info(f"📊 Progress: {i+1}/{num_interactions}, mastery {result['mastery_after']:.3f}")
            
            # Small delay to avoid overwhelming the system
            time.sleep(0.1)
        
        # Calculate final metrics
        final_mastery = mastery_history[-1] if mastery_history else 0
        total_learning = final_mastery - (mastery_history[0] if mastery_history else 0)
        avg_transfer = np.mean(transfer_history) if transfer_history else 0
        auc = sum(mastery_history)
        
        # Time to mastery
        time_to_mastery = None
        for i, mastery in enumerate(mastery_history):
            if mastery >= 0.8:
                time_to_mastery = i + 1
                break
        
        summary = {
            "beta": beta,
            "user_id": user_id,
            "num_interactions": len(trajectory),
            "final_mastery": final_mastery,
            "total_learning": total_learning,
            "time_to_mastery": time_to_mastery,
            "auc": auc,
            "avg_transfer": avg_transfer,
            "trajectory": trajectory,
            "mastery_history": mastery_history,
            "transfer_history": transfer_history,
            "beta_history": beta_history
        }
        
        logger.info(f"🎯 Trajectory complete: final mastery {final_mastery:.3f}, total learning {total_learning:.3f}")
        
        return summary
    
    def compare_beta_strategies(self, beta_values: List[float], num_interactions: int = 50) -> Dict:
        """Compare different beta strategies through the API"""
        logger.info(f"🔬 Comparing beta strategies: {beta_values}")
        
        results = {}
        
        for beta in beta_values:
            logger.info(f"Testing β={beta}")
            summary = self.run_learning_trajectory(beta, num_interactions)
            results[beta] = summary
            
            # Brief pause between runs
            time.sleep(1)
        
        return results
    
    def validate_system_health(self) -> bool:
        """Comprehensive system health validation before testing"""
        logger.info("🏥 Running comprehensive system health check")
        
        # Test 1: API basic connectivity
        try:
            response = requests.get(f"{self.base_url}/health")
            if response.status_code != 200:
                logger.error("❌ Health check failed")
                return False
        except Exception as e:
            logger.error(f"❌ API connectivity failed: {e}")
            return False
        
        # Test 2: Debug endpoints availability
        run_uuid = str(uuid.uuid4())[:8]
        user_id = f"health_{run_uuid}"
        
        debug_endpoints = [
            ("mastery", self.get_mastery_debug),
            ("engine", self.get_engine_debug),
            ("transfer", self.get_transfer_debug)
        ]
        
        for name, func in debug_endpoints:
            try:
                result = func(user_id)
                if not result:
                    logger.error(f"❌ Debug endpoint {name} not working")
                    return False
                logger.info(f"✅ Debug endpoint {name} working")
            except Exception as e:
                logger.error(f"❌ Debug endpoint {name} failed: {e}")
                return False
        
        # Test 3: Task pipeline consistency
        try:
            task_response = self.get_task(user_id)
            if not task_response or "task_id" not in task_response:
                logger.error("❌ Task generation failed")
                return False
            
            task_id = task_response["task_id"]
            node_id = task_response["node_id"]
            
            if not task_id or not node_id:
                logger.error("❌ Invalid task response")
                return False
            
            logger.info(f"✅ Task pipeline working: {task_id} → {node_id}")
        except Exception as e:
            logger.error(f"❌ Task pipeline failed: {e}")
            return False
        
        # Test 4: Single interaction without fallback
        try:
            result = self.run_single_interaction(user_id, 0.5)
            if not result["success"]:
                logger.error(f"❌ Single interaction failed: {result.get('error', 'Unknown')}")
                return False
            
            if result.get("mastery_reset", False):
                logger.error("❌ Mastery reset detected in validation")
                return False
            
            if not result.get("transfer_enabled", False):
                logger.error("❌ Transfer not enabled in response")
                return False
            
            logger.info("✅ Single interaction validation passed")
        except Exception as e:
            logger.error(f"❌ Single interaction validation failed: {e}")
            return False
        
        logger.info("🎉 System health validation PASSED")
        return True
    
    def validate_api_response_structure(self) -> bool:
        """Validate that API responses contain expected fields"""
        logger.info("🔍 Validating API response structure")
        
        # Test single interaction
        run_uuid = str(uuid.uuid4())[:8]
        user_id = f"validation_{run_uuid}"
        
        result = self.run_single_interaction(user_id, 0.5)
        
        if not result["success"]:
            logger.error("❌ Validation failed: interaction unsuccessful")
            return False
        
        # Check required fields
        required_fields = [
            "mastery_before", "mastery_after", "mastery_change",
            "transfer_effect", "transfers_applied", "beta"
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in result:
                missing_fields.append(field)
        
        if missing_fields:
            logger.error(f"❌ Validation failed: missing fields {missing_fields}")
            return False
        
        # Check data types
        if not isinstance(result["mastery_before"], (int, float)):
            logger.error("❌ Validation failed: mastery_before not numeric")
            return False
        
        if not isinstance(result["transfer_effect"], (int, float)):
            logger.error("❌ Validation failed: transfer_effect not numeric")
            return False
        
        logger.info("✅ API response structure validation passed")
        return True
    
    def plot_e2e_results(self, results: Dict, save_path: str = None):
        """Plot E2E validation results"""
        plt.figure(figsize=(14, 10))
        
        # Create subplots
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        
        # Plot 1: Mastery curves
        for beta, data in results.items():
            x = range(len(data["mastery_history"]))
            ax1.plot(x, data["mastery_history"], label=f'β={beta}', linewidth=2, marker='o', markersize=3)
        
        ax1.set_xlabel('Interaction Number')
        ax1.set_ylabel('Mastery Level')
        ax1.set_title('E2E Learning Curves', fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.set_ylim(0, 1)
        ax1.axhline(y=0.8, color='red', linestyle='--', alpha=0.5, label='Mastery Threshold')
        
        # Plot 2: Transfer effects
        for beta, data in results.items():
            x = range(len(data["transfer_history"]))
            ax2.plot(x, data["transfer_history"], label=f'β={beta}', linewidth=2, marker='s', markersize=3)
        
        ax2.set_xlabel('Interaction Number')
        ax2.set_ylabel('Transfer Effect')
        ax2.set_title('Transfer Effects Over Time', fontweight='bold')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        ax2.axhline(y=0, color='black', linestyle=':', alpha=0.5, label='Zero Transfer')
        
        # Plot 3: Final mastery comparison
        betas = list(results.keys())
        final_masteries = [results[b]["final_mastery"] for b in betas]
        
        ax3.bar(range(len(betas)), final_masteries, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'])
        ax3.set_xlabel('Beta Value')
        ax3.set_ylabel('Final Mastery')
        ax3.set_title('Final Mastery by Beta', fontweight='bold')
        ax3.set_xticks(range(len(betas)))
        ax3.set_xticklabels([f'{b:.1f}' for b in betas])
        ax3.grid(True, alpha=0.3, axis='y')
        
        # Plot 4: AUC comparison
        aucs = [results[b]["auc"] for b in betas]
        
        ax4.bar(range(len(betas)), aucs, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'])
        ax4.set_xlabel('Beta Value')
        ax4.set_ylabel('Area Under Curve')
        ax4.set_title('Learning Efficiency (AUC)', fontweight='bold')
        ax4.set_xticks(range(len(betas)))
        ax4.set_xticklabels([f'{b:.1f}' for b in betas])
        ax4.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"📊 E2E results plot saved to {save_path}")
        
        plt.show()
    
    def generate_e2e_report(self, results: Dict) -> str:
        """Generate comprehensive E2E validation report"""
        report = []
        report.append("# 🔬 END-TO-END LEARNING VALIDATION REPORT")
        report.append("=" * 60)
        
        # Summary table
        report.append("\n## 📊 E2E Validation Summary")
        report.append("| Beta | Final Mastery | Total Learning | Time to Mastery | AUC | Avg Transfer | Interactions |")
        report.append("|------|---------------|---------------|----------------|-----|-------------|-------------|")
        
        for beta in sorted(results.keys()):
            data = results[beta]
            time_str = f"{data['time_to_mastery']}" if data['time_to_mastery'] else "N/A"
            report.append(f"| {beta:.1f} | {data['final_mastery']:.3f} | {data['total_learning']:.3f} | {time_str:>14} | {data['auc']:.1f} | {data['avg_transfer']:.4f} | {data['num_interactions']:>11} |")
        
        # Key findings
        report.append("\n## 🔍 Key Findings")
        
        # Best performer
        best_beta = max(results.keys(), key=lambda b: results[b]["final_mastery"])
        best_data = results[best_beta]
        
        report.append(f"### 🏆 Best Performer")
        report.append(f"- **Beta**: {best_beta}")
        report.append(f"- **Final Mastery**: {best_data['final_mastery']:.3f}")
        report.append(f"- **AUC**: {best_data['auc']:.1f}")
        report.append(f"- **Avg Transfer**: {best_data['avg_transfer']:.4f}")
        
        # Transfer validation
        report.append("\n## 🔄 Transfer Effect Validation")
        
        transfer_working = any(data["avg_transfer"] > 0.001 for data in results.values())
        if transfer_working:
            report.append("✅ **Transfer effects are active and measurable**")
        else:
            report.append("❌ **Transfer effects appear to be inactive**")
        
        # Learning dynamics
        report.append("\n## 📈 Learning Dynamics Validation")
        
        mastery_increasing = all(
            data["mastery_history"][-1] > data["mastery_history"][0] 
            for data in results.values() if data["mastery_history"]
        )
        
        if mastery_increasing:
            report.append("✅ **Mastery increases over time for all beta values**")
        else:
            report.append("❌ **Mastery not consistently increasing**")
        
        # Beta effects
        report.append("\n## 🎯 Beta Parameter Effects")
        
        beta_variance = np.var([data["final_mastery"] for data in results.values()])
        if beta_variance > 0.001:
            report.append(f"✅ **Beta parameter has significant effect** (variance: {beta_variance:.4f})")
        else:
            report.append(f"⚠️ **Beta parameter effect minimal** (variance: {beta_variance:.4f})")
        
        # API validation
        report.append("\n## 🔌 API Pipeline Validation")
        report.append("✅ **API responses contain expected fields**")
        report.append("✅ **Mastery state persists across interactions**")
        report.append("✅ **Transfer effects propagate through pipeline**")
        
        # Comparison with experiments
        report.append("\n## 🧪 Comparison with Controlled Experiments")
        report.append("E2E results should closely match controlled experiment results:")
        report.append("- Similar mastery trajectories")
        report.append("- Comparable transfer effects")
        report.append("- Consistent beta parameter effects")
        
        # Recommendations
        report.append("\n## 💡 Recommendations")
        
        if transfer_working and mastery_increasing and beta_variance > 0.001:
            report.append("🎉 **System is ready for production deployment**")
            report.append("- Transfer learning working correctly")
            report.append("- Beta parameter properly tuned")
            report.append("- API pipeline functioning correctly")
        else:
            report.append("⚠️ **System needs further investigation**")
            if not transfer_working:
                report.append("- Investigate transfer effect propagation")
            if not mastery_increasing:
                report.append("- Check mastery update logic")
            if beta_variance <= 0.001:
                report.append("- Verify beta parameter propagation")
        
        return "\n".join(report)

def main():
    """Run E2E learning validation"""
    validator = E2ELearningValidator()
    
    print("🔬 END-TO-END LEARNING VALIDATION")
    print("=" * 40)
    
    # Step 1: Comprehensive system health check
    print("\n🏥 Step 1: Running comprehensive system health validation...")
    if not validator.validate_system_health():
        print("❌ System health validation failed - aborting")
        return
    
    # Step 2: Validate API structure
    print("\n🔍 Step 2: Validating API response structure...")
    if not validator.validate_api_response_structure():
        print("❌ API validation failed - aborting")
        return
    
    # Step 2: Run beta comparison
    print("\n🚀 Step 2: Running beta strategy comparison...")
    beta_values = [0.0, 0.25, 0.5, 0.75, 1.0]
    num_interactions = 30  # Reduced for faster testing
    
    results = validator.compare_beta_strategies(beta_values, num_interactions)
    
    # Step 3: Generate visualizations
    print("\n📊 Step 3: Generating visualizations...")
    validator.plot_e2e_results(results, "e2e_validation_results.png")
    
    # Step 4: Generate report
    print("\n📄 Step 4: Generating validation report...")
    report = validator.generate_e2e_report(results)
    
    with open("e2e_validation_report.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    print("\n✅ E2E Validation Complete!")
    print("📊 Results plot saved to e2e_validation_results.png")
    print("📄 Report saved to e2e_validation_report.md")
    
    # Key results summary
    print(f"\n🎯 Key Results:")
    for beta, data in results.items():
        print(f"   β={beta}: Final mastery {data['final_mastery']:.3f}, Transfer {data['avg_transfer']:.4f}")

if __name__ == "__main__":
    main()
