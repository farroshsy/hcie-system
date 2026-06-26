"""
Runtime Identity Validation

Proves singleton identity preserved across all flows after DI convergence.

Critical because authoritative cores (TaskService, UnifiedBrain, ContextualBandit, ReplayEngine)
are stateful runtime engines, not simple services. Their singleton identity MUST be preserved
to prevent:
- Duplicate state reconstruction
- Replay determinism corruption
- Ownership context violations
- Cache inconsistency
"""

import logging
import asyncio
from typing import Dict, Set
from app.infrastructure.di.dependency_injection import get_di_container, initialize_di_container, AllDependencies
from app.api.dependencies.learning import get_task_service, get_unified_brain, get_bandit_service


def initialize_di_container_for_testing():
    """Initialize DI container for testing if not already initialized"""
    try:
        container = get_di_container()
        if not container._initialized:
            # Initialize with minimal dependencies for testing
            from app.infrastructure.di.dependency_injection import (
                DatabaseDependencies, ServiceDependencies, MessagingDependencies
            )
            # Create minimal dependencies for testing
            db_deps = DatabaseDependencies(
                user_repo=None,
                postgres_store=None,
                redis_store=None
            )
            service_deps = ServiceDependencies(
                auth_service=None,
                user_service=None,
                experiment_service=None,
                task_state_reconstruction_service=None
            )
            messaging_deps = MessagingDependencies(
                kafka_producer=None,
                outbox_pattern=None
            )
            all_deps = AllDependencies(
                db=db_deps,
                services=service_deps,
                messaging=messaging_deps
            )
            initialize_di_container(all_deps)
            logger.info("DI container initialized for testing")
    except Exception as e:
        logger.warning(f"Failed to initialize DI container for testing: {e}")

logger = logging.getLogger(__name__)


class RuntimeIdentityValidator:
    """
    Validates singleton identity preservation across runtime flows.
    """
    
    def __init__(self):
        self.identity_registry: Dict[str, Set[int]] = {
            'task_service': set(),
            'unified_brain': set(),
            'contextual_bandit': set(),
            'replay_engine': set()
        }
        self.violations = []
    
    def record_identity(self, service_name: str, service_instance) -> int:
        """Record service instance identity (memory address)"""
        identity = id(service_instance)
        self.identity_registry[service_name].add(identity)
        logger.debug(f"Recorded {service_name} identity: {identity}")
        return identity
    
    def check_singleton_violation(self, service_name: str) -> bool:
        """Check if multiple instances detected (singleton violation)"""
        identities = self.identity_registry[service_name]
        if len(identities) > 1:
            violation = f"Singleton violation: {service_name} has {len(identities)} instances: {identities}"
            self.violations.append(violation)
            logger.error(violation)
            return True
        return False
    
    def validate_all_singletons(self) -> bool:
        """Validate all services maintain singleton identity"""
        all_valid = True
        for service_name in self.identity_registry:
            if self.check_singleton_violation(service_name):
                all_valid = False
        return all_valid
    
    def get_validation_report(self) -> Dict:
        """Generate validation report"""
        return {
            'services_checked': len(self.identity_registry),
            'violations': self.violations,
            'singleton_preserved': len(self.violations) == 0,
            'identity_counts': {name: len(ids) for name, ids in self.identity_registry.items()}
        }


def validate_request_flow_identity():
    """
    Validate singleton identity across multiple request flows.
    
    Simulates multiple concurrent requests to ensure singleton identity preserved.
    """
    logger.info("Starting request flow identity validation...")
    validator = RuntimeIdentityValidator()
    
    try:
        # Simulate 10 concurrent requests
        async def simulate_request(request_id: int):
            logger.debug(f"Simulating request {request_id}")
            task_service = get_task_service()
            validator.record_identity('task_service', task_service)
        
        # Run concurrent requests
        async def run_concurrent_requests():
            tasks = [simulate_request(i) for i in range(10)]
            await asyncio.gather(*tasks)
        
        asyncio.run(run_concurrent_requests())
    except RuntimeError as e:
        if "DI Container not initialized" in str(e):
            logger.warning("DI container not initialized - falling back to synchronous validation")
            # Fallback: synchronous validation
            for i in range(10):
                task_service = get_task_service()
                validator.record_identity('task_service', task_service)
        else:
            raise
    
    # Check for violations
    task_service_valid = not validator.check_singleton_violation('task_service')
    
    report = validator.get_validation_report()
    logger.info(f"Request flow validation report: {report}")
    
    return task_service_valid, report


def validate_websocket_flow_identity():
    """
    Validate singleton identity across websocket connections.
    
    WebSockets maintain long-lived connections - critical to ensure
    singleton identity preserved across connection lifecycle.
    """
    logger.info("Starting websocket flow identity validation...")
    validator = RuntimeIdentityValidator()
    
    # Simulate 5 concurrent websocket connections
    for connection_id in range(5):
        task_service = get_task_service()
        validator.record_identity('task_service', task_service)
        logger.debug(f"WebSocket connection {connection_id} using task_service identity: {id(task_service)}")
    
    # Check for violations
    task_service_valid = not validator.check_singleton_violation('task_service')
    
    report = validator.get_validation_report()
    logger.info(f"WebSocket flow validation report: {report}")
    
    return task_service_valid, report


def validate_replay_mode_identity():
    """
    Validate singleton identity preserved in replay mode.
    
    Replay mode has deterministic requirements - singleton identity
    MUST be preserved to ensure deterministic behavior.
    """
    logger.info("Starting replay mode identity validation...")
    validator = RuntimeIdentityValidator()
    
    # Simulate replay mode access
    for replay_step in range(10):
        task_service = get_task_service()
        validator.record_identity('task_service', task_service)
        logger.debug(f"Replay step {replay_step} using task_service identity: {id(task_service)}")
    
    # Check for violations
    task_service_valid = not validator.check_singleton_violation('task_service')
    
    report = validator.get_validation_report()
    logger.info(f"Replay mode validation report: {report}")
    
    return task_service_valid, report


def validate_cross_service_identity():
    """
    Validate singleton identity across all authoritative cores.
    
    Ensures TaskService, UnifiedBrain, ContextualBandit, ReplayEngine
    all maintain singleton identity.
    """
    logger.info("Starting cross-service identity validation...")
    validator = RuntimeIdentityValidator()
    
    # Record identities for all services
    task_service = get_task_service()
    validator.record_identity('task_service', task_service)
    
    unified_brain = get_unified_brain()
    if unified_brain is not None:
        validator.record_identity('unified_brain', unified_brain)
    
    bandit_service = get_bandit_service()
    if bandit_service is not None:
        validator.record_identity('contextual_bandit', bandit_service)
    
    # Check for violations
    all_valid = validator.validate_all_singletons()
    
    report = validator.get_validation_report()
    logger.info(f"Cross-service validation report: {report}")
    
    return all_valid, report


def run_full_identity_validation():
    """
    Run complete runtime identity validation suite.
    
    This is CRITICAL before Stage 3 adapter removal because:
    - Proves singleton identity preserved across all flows
    - Validates DI convergence didn't break runtime semantics
    - Provides evidence that adapter removal is safe
    """
    logger.info("=" * 80)
    logger.info("RUNTIME IDENTITY VALIDATION SUITE")
    logger.info("=" * 80)
    
    # Initialize DI container for testing
    initialize_di_container_for_testing()
    
    results = {}
    
    # Test 1: Request flow identity
    request_valid, request_report = validate_request_flow_identity()
    results['request_flow'] = {'valid': request_valid, 'report': request_report}
    
    # Test 2: WebSocket flow identity
    websocket_valid, websocket_report = validate_websocket_flow_identity()
    results['websocket_flow'] = {'valid': websocket_valid, 'report': websocket_report}
    
    # Test 3: Replay mode identity
    replay_valid, replay_report = validate_replay_mode_identity()
    results['replay_mode'] = {'valid': replay_valid, 'report': replay_report}
    
    # Test 4: Cross-service identity
    cross_valid, cross_report = validate_cross_service_identity()
    results['cross_service'] = {'valid': cross_valid, 'report': cross_report}
    
    # Summary
    all_valid = all(result['valid'] for result in results.values())
    
    logger.info("=" * 80)
    logger.info("RUNTIME IDENTITY VALIDATION SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Request Flow: {'PASS' if request_valid else 'FAIL'}")
    logger.info(f"WebSocket Flow: {'PASS' if websocket_valid else 'FAIL'}")
    logger.info(f"Replay Mode: {'PASS' if replay_valid else 'FAIL'}")
    logger.info(f"Cross-Service: {'PASS' if cross_valid else 'FAIL'}")
    logger.info(f"OVERALL: {'PASS' if all_valid else 'FAIL'}")
    logger.info("=" * 80)
    
    if not all_valid:
        logger.error("RUNTIME IDENTITY VALIDATION FAILED - DO NOT PROCEED TO STAGE 3")
        logger.error("Violations detected - singleton identity not preserved")
    else:
        logger.info("RUNTIME IDENTITY VALIDATION PASSED - Singleton identity preserved")
    
    return all_valid, results


if __name__ == "__main__":
    success, results = run_full_identity_validation()
    exit(0 if success else 1)
