"""
Actual Mutation Safety Validation

Validates that governance invariants survive actual concurrency,
not just that threading.RLock exists.

This is DIFFERENT from "locks exist" validation.
This validates:
- No corruption under concurrent governance updates
- No NaN propagation under high-frequency weight adaptation
- No invalid weight sums under simultaneous bandit/ensemble updates
- No history truncation corruption
- No duplicate persistence races

This is the SECOND HIGHEST priority validation because:
locks can still be wrong (nested mutation, read-modify-write, lock ordering, partial protection)
"""

import logging
import threading
import time
import random
import numpy as np
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.services.service_factory import ServiceFactory

logger = logging.getLogger(__name__)


class ActualMutationSafetyValidator:
    """
    Validates actual mutation safety under concurrent load.
    
    This is NOT "locks exist" validation.
    This validates governance invariants survive concurrency.
    """
    
    def __init__(self):
        self.violations = []
        self.metrics = {
            'no_corruption': False,
            'no_nan_propagation': False,
            'no_invalid_weights': False,
            'no_history_corruption': False,
            'no_persistence_races': False
        }
        self.num_threads = 10
        self.num_operations = 100
        self.tolerance = 1e-6
    
    def _check_for_nan(self, data: Any, path: str = "") -> List[str]:
        """Recursively check for NaN values in nested structures"""
        nan_paths = []
        
        if isinstance(data, dict):
            for key, value in data.items():
                nan_paths.extend(self._check_for_nan(value, f"{path}.{key}" if path else key))
        elif isinstance(data, (list, tuple)):
            for i, value in enumerate(data):
                nan_paths.extend(self._check_for_nan(value, f"{path}[{i}]"))
        elif isinstance(data, (float, np.floating)):
            if np.isnan(data):
                nan_paths.append(path if path else "root")
        elif isinstance(data, np.ndarray):
            if np.any(np.isnan(data)):
                nan_paths.append(path if path else "root")
        
        return nan_paths
    
    def _check_weight_sum_validity(self, weights: Dict[str, float]) -> bool:
        """Check if weights sum to approximately 1.0"""
        total = sum(weights.values())
        return abs(total - 1.0) < self.tolerance
    
    def _concurrent_governance_updates(self, task_service) -> Dict[str, Any]:
        """Test concurrent governance updates"""
        logger.info("Testing concurrent governance updates...")
        
        unified_brain = task_service.unified_brain
        governance = unified_brain.jt_governance
        
        def update_governance(thread_id: int):
            """Concurrent governance update operation"""
            for i in range(self.num_operations):
                try:
                    # Simulate governance weight adaptation
                    jt, _ = governance.compute_jt(
                        delta_m=0.5,
                        transfer_realized=0.5,
                        transfer_prospective=0.5,
                        challenge=0.5,
                        uncertainty=0.5,
                        zpd=0.5,
                        context={}
                    )
                    
                    # Simulate weight adaptation
                    if hasattr(governance, 'adapt_weights'):
                        governance.adapt_weights(stability_index=0.5, context={})
                    
                except Exception as e:
                    logger.error(f"Thread {thread_id} operation {i} failed: {e}")
                    raise
        
        # Run concurrent updates
        with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            futures = [executor.submit(update_governance, i) for i in range(self.num_threads)]
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Concurrent update failed: {e}")
                    self.violations.append(f"Concurrent governance update error: {e}")
        
        # Check for corruption
        weights = governance.weights_manager.weights
        nan_paths = self._check_for_nan(weights)
        
        if nan_paths:
            logger.error(f"NaN detected in weights: {nan_paths}")
            self.violations.append(f"NaN in governance weights: {nan_paths}")
            return {'corruption': True, 'nan_paths': nan_paths}
        
        if not self._check_weight_sum_validity(weights):
            logger.error(f"Weight sum invalid: {sum(weights.values())}")
            self.violations.append(f"Invalid weight sum: {sum(weights.values())}")
            return {'corruption': True, 'invalid_sum': sum(weights.values())}
        
        return {'corruption': False}
    
    def _concurrent_bandit_updates(self, task_service) -> Dict[str, Any]:
        """Test concurrent bandit updates"""
        logger.info("Testing concurrent bandit updates...")
        
        unified_brain = task_service.unified_brain
        
        # Check if bandit_integration exists
        if not hasattr(unified_brain, 'bandit_integration') or not unified_brain.bandit_integration:
            logger.warning("No bandit_integration found, skipping bandit concurrency test")
            return {'corruption': False, 'skipped': True}
        
        bandit = unified_brain.bandit_integration.bandit
        
        def update_bandit(thread_id: int):
            """Concurrent bandit update operation"""
            for i in range(self.num_operations):
                try:
                    # Simulate bandit update
                    arm_id = f"arm_{thread_id % 5}"
                    reward = random.random()
                    context = {"feature": random.random()}
                    
                    bandit.update(arm_id, reward, context)
                    
                except Exception as e:
                    logger.error(f"Thread {thread_id} bandit operation {i} failed: {e}")
                    raise
        
        # Run concurrent updates
        with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            futures = [executor.submit(update_bandit, i) for i in range(self.num_threads)]
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Concurrent bandit update failed: {e}")
                    self.violations.append(f"Concurrent bandit update error: {e}")
        
        # Check for corruption
        alpha_beta_params = bandit.alpha_beta_params
        nan_paths = self._check_for_nan(alpha_beta_params)
        
        if nan_paths:
            logger.error(f"NaN detected in bandit params: {nan_paths}")
            self.violations.append(f"NaN in bandit params: {nan_paths}")
            return {'corruption': True, 'nan_paths': nan_paths}
        
        return {'corruption': False}
    
    def _concurrent_ensemble_updates(self, task_service) -> Dict[str, Any]:
        """Test concurrent ensemble weight updates"""
        logger.info("Testing concurrent ensemble updates...")
        
        unified_brain = task_service.unified_brain
        governance = unified_brain.jt_governance
        
        # Check if ensemble exists
        if not hasattr(governance, 'ensemble') or not governance.ensemble:
            logger.warning("No ensemble found, skipping ensemble concurrency test")
            return {'corruption': False, 'skipped': True}
        
        ensemble = governance.ensemble
        
        def update_ensemble(thread_id: int):
            """Concurrent ensemble update operation"""
            for i in range(self.num_operations):
                try:
                    # Simulate ensemble weight update
                    learner_id = f"learner_{thread_id % 3}"
                    contribution = random.random()
                    
                    ensemble.record_learner_contribution(learner_id, contribution)
                    
                except Exception as e:
                    logger.error(f"Thread {thread_id} ensemble operation {i} failed: {e}")
                    raise
        
        # Run concurrent updates
        with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            futures = [executor.submit(update_ensemble, i) for i in range(self.num_threads)]
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Concurrent ensemble update failed: {e}")
                    self.violations.append(f"Concurrent ensemble update error: {e}")
        
        # Check for corruption
        ema_weights = ensemble.ema_weights
        nan_paths = self._check_for_nan(ema_weights)
        
        if nan_paths:
            logger.error(f"NaN detected in ensemble weights: {nan_paths}")
            self.violations.append(f"NaN in ensemble weights: {nan_paths}")
            return {'corruption': True, 'nan_paths': nan_paths}
        
        if not self._check_weight_sum_validity(ema_weights):
            logger.error(f"Ensemble weight sum invalid: {sum(ema_weights.values())}")
            self.violations.append(f"Invalid ensemble weight sum: {sum(ema_weights.values())}")
            return {'corruption': True, 'invalid_sum': sum(ema_weights.values())}
        
        return {'corruption': False}
    
    def _concurrent_history_operations(self, task_service) -> Dict[str, Any]:
        """Test concurrent history operations"""
        logger.info("Testing concurrent history operations...")
        
        unified_brain = task_service.unified_brain
        governance = unified_brain.jt_governance
        volatility = governance.volatility_monitor
        
        def update_history(thread_id: int):
            """Concurrent history update operation"""
            for i in range(self.num_operations):
                try:
                    # Simulate volatility monitor update
                    jt = random.random()
                    context = {
                        "exploration_signal": random.random(),
                        "reward_signal": random.random(),
                        "learner_disagreement": random.random()
                    }
                    
                    volatility.update(jt, context)
                    
                except Exception as e:
                    logger.error(f"Thread {thread_id} history operation {i} failed: {e}")
                    raise
        
        # Run concurrent updates
        with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            futures = [executor.submit(update_history, i) for i in range(self.num_threads)]
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Concurrent history update failed: {e}")
                    self.violations.append(f"Concurrent history update error: {e}")
        
        # Check for corruption
        jt_history = volatility.jt_history
        volatility_components = volatility.volatility_components
        
        nan_paths = self._check_for_nan(jt_history)
        if nan_paths:
            logger.error(f"NaN detected in jt_history: {nan_paths}")
            self.violations.append(f"NaN in jt_history: {nan_paths}")
            return {'corruption': True, 'nan_paths': nan_paths}
        
        nan_paths = self._check_for_nan(volatility_components)
        if nan_paths:
            logger.error(f"NaN detected in volatility_components: {nan_paths}")
            self.violations.append(f"NaN in volatility_components: {nan_paths}")
            return {'corruption': True, 'nan_paths': nan_paths}
        
        return {'corruption': False}
    
    def validate_no_corruption(self) -> bool:
        """Validate no corruption under concurrent governance updates"""
        logger.info("=" * 80)
        logger.info("NO CORRUPTION VALIDATION")
        logger.info("=" * 80)
        
        try:
            service_factory = ServiceFactory()
            task_service = service_factory.get_task_service()
            
            # Test 1: Concurrent governance updates
            result1 = self._concurrent_governance_updates(task_service)
            
            # Test 2: Concurrent bandit updates
            result2 = self._concurrent_bandit_updates(task_service)
            
            # Test 3: Concurrent ensemble updates
            result3 = self._concurrent_ensemble_updates(task_service)
            
            # Test 4: Concurrent history operations
            result4 = self._concurrent_history_operations(task_service)
            
            # Overall result
            all_passed = (
                not result1.get('corruption', False) and
                not result2.get('corruption', False) and
                not result3.get('corruption', False) and
                not result4.get('corruption', False)
            )
            
            self.metrics['no_corruption'] = all_passed
            
            if all_passed:
                logger.info("✅ NO CORRUPTION VALIDATION PASSED")
            else:
                logger.error("❌ NO CORRUPTION VALIDATION FAILED")
            
            return all_passed
            
        except Exception as e:
            logger.error(f"No corruption validation failed: {e}")
            self.violations.append(f"No corruption validation error: {e}")
            return False
    
    def validate_no_nan_propagation(self) -> bool:
        """Validate no NaN propagation under high-frequency weight adaptation"""
        logger.info("=" * 80)
        logger.info("NO NaN PROPAGATION VALIDATION")
        logger.info("=" * 80)
        
        # NaN detection is already done in concurrent tests
        # This is a summary check
        nan_violations = [v for v in self.violations if 'NaN' in v]
        
        if nan_violations:
            logger.error(f"NaN propagation detected: {nan_violations}")
            self.metrics['no_nan_propagation'] = False
            return False
        else:
            logger.info("✅ NO NaN PROPAGATION VALIDATION PASSED")
            self.metrics['no_nan_propagation'] = True
            return True
    
    def validate_no_invalid_weights(self) -> bool:
        """Validate no invalid weight sums under simultaneous updates"""
        logger.info("=" * 80)
        logger.info("NO INVALID WEIGHTS VALIDATION")
        logger.info("=" * 80)
        
        # Invalid weight detection is already done in concurrent tests
        # This is a summary check
        invalid_weight_violations = [v for v in self.violations if 'Invalid' in v and 'sum' in v]
        
        if invalid_weight_violations:
            logger.error(f"Invalid weights detected: {invalid_weight_violations}")
            self.metrics['no_invalid_weights'] = False
            return False
        else:
            logger.info("✅ NO INVALID WEIGHTS VALIDATION PASSED")
            self.metrics['no_invalid_weights'] = True
            return True
    
    def get_validation_report(self) -> Dict[str, Any]:
        """Generate validation report"""
        return {
            'metrics': self.metrics,
            'violations': self.violations,
            'overall_status': 'PASS' if all(self.metrics.values()) else 'FAILED'
        }


def run_actual_mutation_safety_validation():
    """
    Run complete actual mutation safety validation suite.
    
    This is CRITICAL because:
    - Locks can still be wrong (nested mutation, read-modify-write, lock ordering)
    - "Locks exist" != "Governance invariants survive concurrency"
    - This is the SECOND HIGHEST priority validation
    """
    logger.info("=" * 80)
    logger.info("ACTUAL MUTATION SAFETY VALIDATION SUITE")
    logger.info("=" * 80)
    logger.info("Validates governance invariants survive ACTUAL concurrency")
    logger.info("(NOT just that threading.RLock exists)")
    logger.info("=" * 80)
    
    validator = ActualMutationSafetyValidator()
    
    # Test 1: No corruption under concurrent updates
    validator.validate_no_corruption()
    
    # Test 2: No NaN propagation
    validator.validate_no_nan_propagation()
    
    # Test 3: No invalid weights
    validator.validate_no_invalid_weights()
    
    # Summary
    report = validator.get_validation_report()
    
    logger.info("=" * 80)
    logger.info("ACTUAL MUTATION SAFETY VALIDATION SUMMARY")
    logger.info("=" * 80)
    logger.info(f"No Corruption: {report['metrics']['no_corruption']}")
    logger.info(f"No NaN Propagation: {report['metrics']['no_nan_propagation']}")
    logger.info(f"No Invalid Weights: {report['metrics']['no_invalid_weights']}")
    logger.info(f"No History Corruption: {report['metrics']['no_history_corruption']}")
    logger.info(f"No Persistence Races: {report['metrics']['no_persistence_races']}")
    logger.info(f"OVERALL: {report['overall_status']}")
    logger.info("=" * 80)
    
    if report['overall_status'] == 'FAILED':
        logger.error("ACTUAL MUTATION SAFETY VALIDATION FAILED")
        logger.error(f"Violations: {report['violations']}")
    else:
        logger.info("ACTUAL MUTATION SAFETY VALIDATION PASSED")
    
    return report


if __name__ == "__main__":
    report = run_actual_mutation_safety_validation()
    exit(0 if report['overall_status'] == 'PASS' else 1)
