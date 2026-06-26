#!/usr/bin/env python3
"""
Test SYSTEM INTEGRITY instead of system comparison
This validates that UnifiedLearningBrain is actually being used correctly
"""

import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any

class SystemIntegrityTester:
    """Tests if the system is actually working or just faking it"""
    
    def __init__(self):
        self.test_results = []
        self._initialize_systems()
    
    def _initialize_systems(self):
        """Initialize the system components"""
        try:
            from app.services.service_factory import ServiceFactory
            from core.learning.unified_brain import UnifiedLearningBrain
            
            self.sf = ServiceFactory()
            self.task_service = self.sf.get_task_service()
            self.unified_brain = UnifiedLearningBrain(system_mode="jt")
            
            print("✅ System initialized for integrity testing")
            
        except Exception as e:
            print(f"❌ System initialization failed: {e}")
    
    def test_write_read_consistency(self, user_id: str, concept_id: str) -> Dict[str, Any]:
        """Test CRITICAL: Write → Read consistency"""
        
        print(f"\n🔍 Testing WRITE → READ consistency for {user_id}/{concept_id}")
        print("-" * 50)
        
        # Step 1: Get initial mastery (READ)
        initial_read = self.unified_brain.process_event(
            user_id=user_id,
            concept=concept_id,
            interaction=None,
            mode="read"
        )
        initial_mastery = initial_read.mastery
        
        print(f"📖 Initial READ mastery: {initial_mastery:.6f}")
        
        # Step 2: Perform WRITE operation
        interaction = {
            "task_id": "integrity_test_task",
            "user_id": user_id,
            "concept_id": concept_id,
            "correctness": 0.9,  # High performance
            "response_time": 20.0,
            "difficulty": 0.5,
            "timestamp": datetime.utcnow().isoformat(),
            "attempts": 1,
            "hints_used": 0,
            "frustration": 0.1,
            "engagement": 0.9
        }
        
        write_result = self.unified_brain.process_event(
            user_id=user_id,
            concept=concept_id,
            interaction=interaction,
            mode="write"
        )
        write_mastery = write_result.mastery
        
        print(f"✍️  WRITE mastery: {write_mastery:.6f}")
        
        # Step 3: Read again to check consistency
        final_read = self.unified_brain.process_event(
            user_id=user_id,
            concept=concept_id,
            interaction=None,
            mode="read"
        )
        final_mastery = final_read.mastery
        
        print(f"📖 Final READ mastery: {final_mastery:.6f}")
        
        # CRITICAL CHECKS
        mastery_changed = abs(write_mastery - initial_mastery) > 0.001
        consistency = abs(final_mastery - write_mastery) < 0.001
        
        print(f"\n🔍 INTEGRITY CHECKS:")
        print(f"   Mastery changed after WRITE: {'✅' if mastery_changed else '❌'}")
        print(f"   READ consistency after WRITE: {'✅' if consistency else '❌'}")
        
        if not mastery_changed:
            print(f"   ❌ WRITE operation had no effect!")
        
        if not consistency:
            print(f"   ❌ READ returned different value than WRITE!")
            print(f"   ❌ This indicates state persistence failure!")
        
        return {
            "test_type": "write_read_consistency",
            "user_id": user_id,
            "concept_id": concept_id,
            "initial_mastery": initial_mastery,
            "write_mastery": write_mastery,
            "final_mastery": final_mastery,
            "mastery_changed": mastery_changed,
            "consistency": consistency,
            "passed": mastery_changed and consistency
        }
    
    def test_task_service_integration(self, user_id: str, concept_id: str) -> Dict[str, Any]:
        """Test if TaskService actually uses UnifiedLearningBrain"""
        
        print(f"\n🔍 Testing TaskService integration for {user_id}/{concept_id}")
        print("-" * 50)
        
        # Step 1: Get mastery via TaskService
        candidates = self.task_service._get_candidate_tasks(user_id, concept_filter=[concept_id])
        task_service_mastery = self.task_service._get_mastery_context(user_id, candidates)
        
        print(f"🔧 TaskService mastery: {task_service_mastery}")
        
        # Step 2: Get mastery directly from UnifiedLearningBrain
        direct_result = self.unified_brain.process_event(
            user_id=user_id,
            concept=concept_id,
            interaction=None,
            mode="read"
        )
        direct_mastery = direct_result.mastery
        
        print(f"🧠 Direct UnifiedBrain mastery: {direct_mastery:.6f}")
        
        # CRITICAL CHECK: Are they the same?
        task_service_value = task_service_mastery.get(concept_id, 0.0)
        integration_consistency = abs(task_service_value - direct_mastery) < 0.001
        
        print(f"\n🔍 INTEGRITY CHECKS:")
        print(f"   TaskService mastery: {task_service_value:.6f}")
        print(f"   Direct mastery: {direct_mastery:.6f}")
        print(f"   Integration consistency: {'✅' if integration_consistency else '❌'}")
        
        if not integration_consistency:
            print(f"   ❌ TaskService is NOT using UnifiedLearningBrain!")
            print(f"   ❌ This means you have two disconnected systems!")
        
        return {
            "test_type": "task_service_integration",
            "user_id": user_id,
            "concept_id": concept_id,
            "task_service_mastery": task_service_value,
            "direct_mastery": direct_mastery,
            "integration_consistency": integration_consistency,
            "passed": integration_consistency
        }
    
    def test_submission_loop(self, user_id: str, concept_id: str) -> Dict[str, Any]:
        """Test the complete submission loop"""
        
        print(f"\n🔍 Testing complete submission loop for {user_id}/{concept_id}")
        print("-" * 50)
        
        # Step 1: Get a task
        candidates = self.task_service._get_candidate_tasks(user_id, concept_filter=[concept_id])
        task = candidates[0] if candidates else {"task_id": "fallback", "concept_id": concept_id}
        
        print(f"📋 Selected task: {task['task_id']}")
        
        # Step 2: Get mastery before submission
        before_mastery = self.task_service._get_mastery_context(user_id, candidates).get(concept_id, 0.0)
        print(f"📖 Before submission mastery: {before_mastery:.6f}")
        
        # Step 3: Submit answer
        from app.models.requests import TaskSubmission
        submission = TaskSubmission(
            user_id=user_id,
            task_id=task['task_id'],
            node_id=concept_id,
            answer='correct_answer',
            response_time=25.0,
            representation='text',
            learner_mode='lyapunov'
        )
        
        result = self.task_service.process_submission(submission)
        print(f"✅ Submission processed: {result.get('success', False)}")
        
        # Step 4: Get mastery after submission
        after_mastery = self.task_service._get_mastery_context(user_id, candidates).get(concept_id, 0.0)
        print(f"📖 After submission mastery: {after_mastery:.6f}")
        
        # CRITICAL CHECK: Did mastery actually change?
        mastery_changed = abs(after_mastery - before_mastery) > 0.001
        
        print(f"\n🔍 INTEGRITY CHECKS:")
        print(f"   Mastery changed: {'✅' if mastery_changed else '❌'}")
        print(f"   Change amount: {after_mastery - before_mastery:+.6f}")
        
        if not mastery_changed:
            print(f"   ❌ Submission had no effect on mastery!")
            print(f"   ❌ Learning loop is broken!")
        
        return {
            "test_type": "submission_loop",
            "user_id": user_id,
            "concept_id": concept_id,
            "before_mastery": before_mastery,
            "after_mastery": after_mastery,
            "mastery_changed": mastery_changed,
            "passed": mastery_changed
        }
    
    def test_candidate_diversity(self, user_id: str, concept_id: str) -> Dict[str, Any]:
        """Test if candidates are actually diverse"""
        
        print(f"\n🔍 Testing candidate diversity for {user_id}/{concept_id}")
        print("-" * 50)
        
        # Get candidates
        candidates = self.task_service._get_candidate_tasks(user_id, concept_filter=[concept_id])
        
        print(f"📊 Total candidates: {len(candidates)}")
        
        # Analyze diversity
        task_ids = [c.get('task_id', 'unknown') for c in candidates]
        unique_tasks = set(task_ids)
        
        print(f"📋 Task IDs: {task_ids}")
        print(f"🎯 Unique tasks: {len(unique_tasks)}")
        
        # CRITICAL CHECK: Are candidates actually diverse?
        is_diverse = len(unique_tasks) > 1
        
        print(f"\n🔍 INTEGRITY CHECKS:")
        print(f"   Candidates diverse: {'✅' if is_diverse else '❌'}")
        
        if not is_diverse:
            print(f"   ❌ All candidates are identical!")
            print(f"   ❌ Bandit selection is meaningless!")
            print(f"   ❌ This explains why Jₜ = 0!")
        
        return {
            "test_type": "candidate_diversity",
            "user_id": user_id,
            "concept_id": concept_id,
            "total_candidates": len(candidates),
            "unique_candidates": len(unique_tasks),
            "task_ids": task_ids,
            "is_diverse": is_diverse,
            "passed": is_diverse
        }
    
    def test_transfer_propagation(self, user_id: str, source_concept: str, target_concept: str) -> Dict[str, Any]:
        """Test if transfer learning actually propagates"""
        
        print(f"\n🔍 Testing transfer propagation {source_concept} → {target_concept}")
        print("-" * 50)
        
        # Step 1: Get initial mastery for both concepts
        source_before = self.unified_brain.process_event(
            user_id=user_id, concept=source_concept, interaction=None, mode="read"
        ).mastery
        
        target_before = self.unified_brain.process_event(
            user_id=user_id, concept=target_concept, interaction=None, mode="read"
        ).mastery
        
        print(f"📖 Before - Source: {source_before:.6f}, Target: {target_before:.6f}")
        
        # Step 2: Update source concept
        interaction = {
            "task_id": "transfer_test_task",
            "user_id": user_id,
            "concept_id": source_concept,
            "correctness": 0.9,
            "response_time": 20.0,
            "difficulty": 0.5,
            "timestamp": datetime.utcnow().isoformat(),
            "attempts": 1,
            "hints_used": 0,
            "frustration": 0.1,
            "engagement": 0.9
        }
        
        self.unified_brain.process_event(
            user_id=user_id, concept=source_concept, interaction=interaction, mode="write"
        )
        
        # Step 3: Check if target concept changed
        source_after = self.unified_brain.process_event(
            user_id=user_id, concept=source_concept, interaction=None, mode="read"
        ).mastery
        
        target_after = self.unified_brain.process_event(
            user_id=user_id, concept=target_concept, interaction=None, mode="read"
        ).mastery
        
        print(f"📖 After - Source: {source_after:.6f}, Target: {target_after:.6f}")
        
        # CRITICAL CHECK: Did transfer happen?
        source_changed = abs(source_after - source_before) > 0.001
        target_changed = abs(target_after - target_before) > 0.001
        
        print(f"\n🔍 INTEGRITY CHECKS:")
        print(f"   Source mastery changed: {'✅' if source_changed else '❌'}")
        print(f"   Target mastery changed: {'✅' if target_changed else '❌'}")
        print(f"   Transfer occurred: {'✅' if source_changed and target_changed else '❌'}")
        
        if source_changed and not target_changed:
            print(f"   ❌ Transfer learning is not working!")
            print(f"   ❌ Source updated but target didn't receive transfer!")
        
        return {
            "test_type": "transfer_propagation",
            "user_id": user_id,
            "source_concept": source_concept,
            "target_concept": target_concept,
            "source_before": source_before,
            "source_after": source_after,
            "target_before": target_before,
            "target_after": target_after,
            "transfer_occurred": source_changed and target_changed,
            "passed": source_changed and target_changed
        }
    
    def run_integrity_suite(self, user_id: str = "integrity_test_user") -> Dict[str, Any]:
        """Run the complete integrity test suite"""
        
        print("🚀 SYSTEM INTEGRITY TEST SUITE")
        print("=" * 60)
        print("This tests if your system is REAL or FAKE")
        print("=" * 60)
        
        test_cases = [
            ("k2_algorithms", "k5_algorithms"),  # Transfer pair
            ("k5_algorithms", "k8_algorithms"),  # Transfer pair
            ("k2_algorithms", "k2_algorithms"),  # Self-test
        ]
        
        results = []
        
        for concept_id, target_concept in test_cases:
            print(f"\n🧪 Testing concept: {concept_id}")
            
            # Test 1: Write → Read consistency
            result1 = self.test_write_read_consistency(user_id, concept_id)
            results.append(result1)
            
            # Test 2: TaskService integration
            result2 = self.test_task_service_integration(user_id, concept_id)
            results.append(result2)
            
            # Test 3: Submission loop
            result3 = self.test_submission_loop(user_id, concept_id)
            results.append(result3)
            
            # Test 4: Candidate diversity
            result4 = self.test_candidate_diversity(user_id, concept_id)
            results.append(result4)
            
            # Test 5: Transfer propagation (if different concepts)
            if concept_id != target_concept:
                result5 = self.test_transfer_propagation(user_id, concept_id, target_concept)
                results.append(result5)
        
        # Generate summary
        passed_tests = sum(1 for r in results if r.get('passed', False))
        total_tests = len(results)
        
        print(f"\n" + "=" * 60)
        print(f"📊 INTEGRITY TEST SUMMARY")
        print(f"=" * 60)
        print(f"Tests passed: {passed_tests}/{total_tests} ({passed_tests/total_tests*100:.1f}%)")
        
        if passed_tests == total_tests:
            print(f"🎉 ALL TESTS PASSED - Your system is REAL!")
        else:
            print(f"❌ SOME TESTS FAILED - Your system has FAKE components!")
            
            # List failed tests
            failed_tests = [r for r in results if not r.get('passed', False)]
            print(f"\n🔍 FAILED TESTS:")
            for failed in failed_tests:
                print(f"   ❌ {failed['test_type']} for {failed.get('concept_id', 'unknown')}")
        
        # Generate report
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "pass_rate": passed_tests / total_tests,
            "system_integrity": passed_tests == total_tests,
            "detailed_results": results
        }
        
        with open("system_integrity_report.json", "w") as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📄 Detailed report saved to: system_integrity_report.json")
        
        return report

def main():
    """Run the system integrity test"""
    
    tester = SystemIntegrityTester()
    report = tester.run_integrity_suite()
    
    if report["system_integrity"]:
        print(f"\n🎯 CONCLUSION: Your system is INTEGRITY-VALIDATED!")
        print(f"   You can proceed with confidence.")
    else:
        print(f"\n🚨 CONCLUSION: Your system has INTEGRITY ISSUES!")
        print(f"   Fix the failed tests before proceeding.")

if __name__ == "__main__":
    main()
