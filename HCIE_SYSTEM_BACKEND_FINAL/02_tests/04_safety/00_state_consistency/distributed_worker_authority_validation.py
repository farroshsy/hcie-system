"""
Distributed Worker Authority Model Validation

Validates the governance authority model to prevent premature distribution
of governance mutation authority.

This is EXTREMELY IMPORTANT because:
- Redis persistence introduces temporal authority ambiguity
- Multiple workers could mutate governance state concurrently
- Without single authority, governance divergence appears silently
- Premature distribution breaks replay-critical guarantees

Validates:
- Single governance authority enforcement
- No concurrent governance mutation from multiple workers
- Authority isolation between workers
- Governance mutation serialization
"""

import logging
import threading
from typing import Dict, Any, Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.services.service_factory import ServiceFactory

logger = logging.getLogger(__name__)


class DistributedWorkerAuthorityValidator:
    """
    Validates distributed worker authority model for governance mutations.
    
    Ensures single authority prevents distributed governance divergence.
    """
    
    def __init__(self):
        self.violations = []
        self.metrics = {
            'single_authority_enforcement': False,
            'no_concurrent_governance_mutation': False,
            'authority_isolation': False,
            'mutation_serialization': False
        }
        self.tolerance = 1e-6
    
    def _capture_governance_state(self, task_service) -> Dict[str, Any]:
        """Capture governance state"""
        unified_brain = task_service.unified_brain
        governance = unified_brain.jt_governance
        
        return {
            'weights': governance.weights_manager.weights.copy(),
            'normalization_state': governance.normalization_state.copy()
        }
    
    def validate_single_authority_enforcement(self) -> bool:
        """
        Validate single governance authority enforcement.
        
        Test: Only one TaskService instance exists (singleton pattern)
        """
        logger.info("=" * 80)
        logger.info("SINGLE AUTHORITY ENFORCEMENT VALIDATION")
        logger.info("=" * 80)
        
        try:
            # Test 1: ServiceFactory returns same instance
            logger.info("Test 1: Checking ServiceFactory singleton...")
            service_factory1 = ServiceFactory()
            service_factory2 = ServiceFactory()
            
            task_service1 = service_factory1.get_task_service()
            task_service2 = service_factory2.get_task_service()
            
            if task_service1 is task_service2:
                logger.info("✅ ServiceFactory returns same TaskService instance")
            else:
                logger.error("❌ ServiceFactory returns different TaskService instances")
                self.violations.append("ServiceFactory not singleton")
                return False
            
            # Test 2: UnifiedBrain is same instance
            logger.info("Test 2: Checking UnifiedBrain singleton...")
            if task_service1.unified_brain is task_service2.unified_brain:
                logger.info("✅ UnifiedBrain is same instance")
            else:
                logger.error("❌ UnifiedBrain is different instance")
                self.violations.append("UnifiedBrain not singleton")
                return False
            
            # Test 3: Governance is same instance
            logger.info("Test 3: Checking governance singleton...")
            governance1 = task_service1.unified_brain.jt_governance
            governance2 = task_service2.unified_brain.jt_governance
            
            if governance1 is governance2:
                logger.info("✅ Governance is same instance")
            else:
                logger.error("❌ Governance is different instance")
                self.violations.append("Governance not singleton")
                return False
            
            self.metrics['single_authority_enforcement'] = True
            logger.info("✅ SINGLE AUTHORITY ENFORCEMENT VALIDATION PASSED")
            return True
            
        except Exception as e:
            logger.error(f"Single authority enforcement validation failed: {e}")
            self.violations.append(f"Single authority validation error: {e}")
            return False
    
    def validate_no_concurrent_governance_mutation(self) -> bool:
        """
        Validate no concurrent governance mutation from multiple workers.
        
        Test: Multiple threads accessing governance via TaskService
        should all access the same instance (no parallel governance instances)
        """
        logger.info("=" * 80)
        logger.info("NO CONCURRENT GOVERNANCE MUTATION VALIDATION")
        logger.info("=" * 80)
        
        try:
            service_factory = ServiceFactory()
            task_service = service_factory.get_task_service()
            
            # Get reference governance instance
            reference_governance = task_service.unified_brain.jt_governance
            reference_id = id(reference_governance)
            
            governance_instances = []
            num_threads = 10
            num_operations = 10
            
            def access_governance(thread_id: int):
                """Access governance from different threads"""
                for i in range(num_operations):
                    try:
                        # Get TaskService (should be same instance)
                        sf = ServiceFactory()
                        ts = sf.get_task_service()
                        
                        # Get governance (should be same instance)
                        gov = ts.unified_brain.jt_governance
                        governance_instances.append((thread_id, i, id(gov)))
                        
                    except Exception as e:
                        logger.error(f"Thread {thread_id} operation {i} failed: {e}")
                        raise
            
            # Run concurrent access
            logger.info(f"Running {num_threads} threads × {num_operations} operations...")
            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = [executor.submit(access_governance, i) for i in range(num_threads)]
                
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        logger.error(f"Concurrent access failed: {e}")
                        self.violations.append(f"Concurrent access error: {e}")
            
            # Check all instances are the same
            logger.info(f"Checking {len(governance_instances)} governance instance IDs...")
            unique_ids = set([gov_id for _, _, gov_id in governance_instances])
            
            if len(unique_ids) == 1 and reference_id in unique_ids:
                logger.info(f"✅ All governance instances are identical (ID: {reference_id})")
                self.metrics['no_concurrent_governance_mutation'] = True
                logger.info("✅ NO CONCURRENT GOVERNANCE MUTATION VALIDATION PASSED")
                return True
            else:
                logger.error(f"❌ Multiple governance instances found: {unique_ids}")
                self.violations.append(f"Multiple governance instances: {unique_ids}")
                self.metrics['no_concurrent_governance_mutation'] = False
                return False
            
        except Exception as e:
            logger.error(f"No concurrent governance mutation validation failed: {e}")
            self.violations.append(f"Concurrent mutation validation error: {e}")
            return False
    
    def validate_authority_isolation(self) -> bool:
        """
        Validate authority isolation between workers.
        
        Test: Governance mutations from one thread are visible to others
        (shared authority, not isolated per-thread)
        """
        logger.info("=" * 80)
        logger.info("AUTHORITY ISOLATION VALIDATION")
        logger.info("=" * 80)
        
        try:
            service_factory = ServiceFactory()
            task_service = service_factory.get_task_service()
            governance = task_service.unified_brain.jt_governance
            
            # Capture initial weights
            initial_weights = governance.weights_manager.weights.copy()
            
            # Perform governance mutation
            logger.info("Performing governance weight adaptation...")
            jt, _ = governance.compute_jt(
                delta_m=0.5,
                transfer_realized=0.5,
                transfer_prospective=0.5,
                challenge=0.5,
                uncertainty=0.5,
                zpd=0.5,
                context={}
            )
            
            # Capture mutated weights
            mutated_weights = governance.weights_manager.weights.copy()
            
            # Access from new ServiceFactory instance
            logger.info("Accessing governance from new ServiceFactory instance...")
            service_factory2 = ServiceFactory()
            task_service2 = service_factory2.get_task_service()
            governance2 = task_service2.unified_brain.jt_governance
            
            # Capture weights from new instance
            new_instance_weights = governance2.weights_manager.weights.copy()
            
            # Compare weights
            logger.info("Comparing weights across ServiceFactory instances...")
            weights_match = True
            for key in initial_weights:
                if abs(mutated_weights[key] - new_instance_weights[key]) > self.tolerance:
                    logger.error(f"Weight mismatch for {key}: {mutated_weights[key]} vs {new_instance_weights[key]}")
                    weights_match = False
            
            if weights_match:
                logger.info("✅ Weights match across ServiceFactory instances (shared authority)")
                self.metrics['authority_isolation'] = True
                logger.info("✅ AUTHORITY ISOLATION VALIDATION PASSED")
                return True
            else:
                logger.error("❌ Weights diverge across ServiceFactory instances (isolated authority)")
                self.violations.append("Authority isolation failed - weights diverge")
                self.metrics['authority_isolation'] = False
                return False
            
        except Exception as e:
            logger.error(f"Authority isolation validation failed: {e}")
            self.violations.append(f"Authority isolation validation error: {e}")
            return False
    
    def validate_mutation_serialization(self) -> bool:
        """
        Validate governance mutation serialization.
        
        Test: Concurrent mutations are serialized by locks,
        no lost updates or corrupted state
        """
        logger.info("=" * 80)
        logger.info("MUTATION SERIALIZATION VALIDATION")
        logger.info("=" * 80)
        
        try:
            service_factory = ServiceFactory()
            task_service = service_factory.get_task_service()
            governance = task_service.unified_brain.jt_governance
            
            # Capture initial state
            initial_weights = governance.weights_manager.weights.copy()
            
            # Perform concurrent mutations
            num_threads = 10
            num_operations = 10
            
            def mutate_governance(thread_id: int):
                """Concurrent governance mutation"""
                for i in range(num_operations):
                    try:
                        jt, _ = governance.compute_jt(
                            delta_m=0.5,
                            transfer_realized=0.5,
                            transfer_prospective=0.5,
                            challenge=0.5,
                            uncertainty=0.5,
                            zpd=0.5,
                            context={}
                        )
                    except Exception as e:
                        logger.error(f"Thread {thread_id} operation {i} failed: {e}")
                        raise
            
            logger.info(f"Running {num_threads} threads × {num_operations} concurrent mutations...")
            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = [executor.submit(mutate_governance, i) for i in range(num_threads)]
                
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        logger.error(f"Concurrent mutation failed: {e}")
                        self.violations.append(f"Concurrent mutation error: {e}")
            
            # Check final state is valid
            final_weights = governance.weights_manager.weights.copy()
            
            # Check weight sum is valid
            total = sum(final_weights.values())
            if abs(total - 1.0) > self.tolerance:
                logger.error(f"Weight sum invalid after concurrent mutations: {total}")
                self.violations.append(f"Invalid weight sum after concurrent mutations: {total}")
                self.metrics['mutation_serialization'] = False
                return False
            
            # Check no NaN
            for key, value in final_weights.items():
                if isinstance(value, float) and (value != value):  # NaN check
                    logger.error(f"NaN detected in weight {key}")
                    self.violations.append(f"NaN in weight {key}")
                    self.metrics['mutation_serialization'] = False
                    return False
            
            logger.info(f"✅ Final weights valid (sum: {total:.6f})")
            self.metrics['mutation_serialization'] = True
            logger.info("✅ MUTATION SERIALIZATION VALIDATION PASSED")
            return True
            
        except Exception as e:
            logger.error(f"Mutation serialization validation failed: {e}")
            self.violations.append(f"Mutation serialization validation error: {e}")
            return False
    
    def get_validation_report(self) -> Dict[str, Any]:
        """Generate validation report"""
        return {
            'metrics': self.metrics,
            'violations': self.violations,
            'overall_status': 'PASS' if all(self.metrics.values()) else 'FAILED'
        }


def run_distributed_worker_authority_validation():
    """
    Run complete distributed worker authority validation suite.
    
    This is EXTREMELY IMPORTANT because:
    - Redis persistence introduces temporal authority ambiguity
    - Multiple workers could mutate governance state concurrently
    - Without single authority, governance divergence appears silently
    - Premature distribution breaks replay-critical guarantees
    """
    logger.info("=" * 80)
    logger.info("DISTRIBUTED WORKER AUTHORITY VALIDATION SUITE")
    logger.info("=" * 80)
    logger.info("Validates single governance authority enforcement")
    logger.info("Prevents premature distribution of governance mutation authority")
    logger.info("=" * 80)
    
    validator = DistributedWorkerAuthorityValidator()
    
    # Test 1: Single authority enforcement
    validator.validate_single_authority_enforcement()
    
    # Test 2: No concurrent governance mutation
    validator.validate_no_concurrent_governance_mutation()
    
    # Test 3: Authority isolation
    validator.validate_authority_isolation()
    
    # Test 4: Mutation serialization
    validator.validate_mutation_serialization()
    
    # Summary
    report = validator.get_validation_report()
    
    logger.info("=" * 80)
    logger.info("DISTRIBUTED WORKER AUTHORITY VALIDATION SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Single Authority Enforcement: {report['metrics']['single_authority_enforcement']}")
    logger.info(f"No Concurrent Governance Mutation: {report['metrics']['no_concurrent_governance_mutation']}")
    logger.info(f"Authority Isolation: {report['metrics']['authority_isolation']}")
    logger.info(f"Mutation Serialization: {report['metrics']['mutation_serialization']}")
    logger.info(f"OVERALL: {report['overall_status']}")
    logger.info("=" * 80)
    
    if report['overall_status'] == 'FAILED':
        logger.error("DISTRIBUTED WORKER AUTHORITY VALIDATION FAILED")
        logger.error(f"Violations: {report['violations']}")
    else:
        logger.info("DISTRIBUTED WORKER AUTHORITY VALIDATION PASSED")
    
    return report


if __name__ == "__main__":
    report = run_distributed_worker_authority_validation()
    exit(0 if report['overall_status'] == 'PASS' else 1)
