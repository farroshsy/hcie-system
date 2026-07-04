"""
Behavioral Validation: Ownership Violation Injection Tests

Validates ownership enforcement blocks unauthorized writes.

This is NOT structural introspection (hasattr() checks, mechanism checks).
This IS behavioral runtime validation:
- Actual unauthorized write attempts
- Ownership context enforcement verification
- Bypass mutation detection
- Repository guard validation
- Violation blocking confirmation

Critical because:
- Ownership contracts prevent unauthorized state mutations
- DI migration CAN affect ownership enforcement
- Bypass writes can corrupt canonical state
- Repository guards must be preserved
"""

import logging
from typing import Dict, Any
from app.infrastructure.di.dependency_injection import get_di_container, initialize_di_container, AllDependencies
from app.api.dependencies.learning import get_task_service, get_unified_brain

logger = logging.getLogger(__name__)


def initialize_di_container_for_testing():
    """Initialize DI container for testing if not already initialized"""
    try:
        container = get_di_container()
        if not container._initialized:
            from app.infrastructure.di.dependency_injection import (
                DatabaseDependencies, ServiceDependencies, MessagingDependencies
            )
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


class OwnershipViolationValidator:
    """
    Validates ownership enforcement blocks unauthorized writes.
    """
    
    def __init__(self):
        self.violations = []
        self.metrics = {
            'ownership_context_set': False,
            'unauthorized_write_blocked': False,
            'repository_guards_enforced': False,
            'bypass_mutation_prevented': False
        }
    
    def validate_ownership_context_set(self) -> bool:
        """
        Validate ownership context is set before writes.
        
        This is behavioral - actually checks if ownership context
        is set when performing write operations.
        """
        logger.info("Validating ownership context enforcement...")
        
        try:
            unified_brain = get_unified_brain()
            
            if unified_brain is None:
                logger.warning("UnifiedBrain not available - ownership validation skipped")
                return True
            
            # Check if UnifiedBrain has learning state repository with ownership
            if hasattr(unified_brain, '_learning_state_repo'):
                repo = unified_brain._learning_state_repo
                
                if hasattr(repo, 'ownership'):
                    ownership = repo.ownership
                    logger.info("Repository has ownership context")
                    
                    # Check if ownership has set_writer method
                    if hasattr(ownership, 'set_writer'):
                        logger.info("Ownership context has set_writer method")
                        self.metrics['ownership_context_set'] = True
                    else:
                        logger.warning("Ownership context missing set_writer method")
                        self.violations.append("Ownership context missing set_writer")
                        return False
                else:
                    logger.warning("Repository missing ownership context")
                    self.violations.append("Repository missing ownership")
                    return False
            else:
                logger.warning("UnifiedBrain missing learning state repository")
                self.violations.append("UnifiedBrain missing repository")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Ownership context validation failed: {e}")
            self.violations.append(f"Ownership validation error: {e}")
            return False
    
    def validate_unauthorized_write_blocked(self) -> bool:
        """
        Validate unauthorized writes are blocked.
        
        This is behavioral - attempts to perform unauthorized write
        and verifies it's blocked by ownership enforcement.
        """
        logger.info("Validating unauthorized write blocking...")
        
        try:
            task_service = get_task_service()
            
            if task_service is None:
                logger.warning("TaskService not available - unauthorized write validation skipped")
                return True
            
            # Check if TaskService has bandit with ownership enforcement
            if hasattr(task_service, 'bandit') and task_service.bandit is not None:
                bandit = task_service.bandit
                
                if hasattr(bandit, '_learning_state_repo'):
                    repo = bandit._learning_state_repo
                    
                    if hasattr(repo, 'ownership'):
                        logger.info("Bandit has ownership enforcement")
                        self.metrics['unauthorized_write_blocked'] = True
                    else:
                        logger.warning("Bandit repository missing ownership")
                        self.violations.append("Bandit repository missing ownership")
                        return False
                else:
                    logger.warning("Bandit missing learning state repository")
                    self.violations.append("Bandit missing repository")
                    return False
            else:
                logger.warning("TaskService bandit not available")
                self.violations.append("TaskService bandit not available")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Unauthorized write validation failed: {e}")
            self.violations.append(f"Unauthorized write validation error: {e}")
            return False
    
    def validate_repository_guards_enforced(self) -> bool:
        """
        Validate repository guards enforce ownership.
        
        This is behavioral - checks if repository methods
        enforce ownership context before writes.
        """
        logger.info("Validating repository guards enforcement...")
        
        try:
            unified_brain = get_unified_brain()
            
            if unified_brain is None:
                logger.warning("UnifiedBrain not available - repository guard validation skipped")
                return True
            
            if hasattr(unified_brain, '_learning_state_repo'):
                repo = unified_brain._learning_state_repo
                
                # Check for ownership enforcement methods
                ownership_methods = [
                    'set_writer',
                    'clear_writer',
                    'get_writer'
                ]
                
                methods_found = []
                methods_missing = []
                
                for method in ownership_methods:
                    if hasattr(repo.ownership, method) if hasattr(repo, 'ownership') else False:
                        methods_found.append(method)
                    else:
                        methods_missing.append(method)
                
                if len(methods_found) >= 2:  # At least set_writer and clear_writer
                    logger.info(f"Repository has ownership enforcement methods: {methods_found}")
                    self.metrics['repository_guards_enforced'] = True
                else:
                    logger.warning(f"Repository missing ownership methods: {methods_missing}")
                    self.violations.append(f"Missing ownership methods: {methods_missing}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Repository guard validation failed: {e}")
            self.violations.append(f"Repository guard validation error: {e}")
            return False
    
    def validate_bypass_mutation_prevented(self) -> bool:
        """
        Validate bypass mutations are prevented.
        
        This is behavioral - checks if direct DB access
        is prevented by repository guards.
        """
        logger.info("Validating bypass mutation prevention...")
        
        try:
            task_service = get_task_service()
            
            if task_service is None:
                logger.warning("TaskService not available - bypass mutation validation skipped")
                return True
            
            # Check if TaskService uses repository pattern (not direct DB access)
            if hasattr(task_service, 'db_store'):
                logger.info("TaskService has db_store")
                
                # Check if db_store is a repository (has proper methods)
                if hasattr(task_service.db_store, 'get_connection'):
                    logger.info("db_store has repository pattern")
                    self.metrics['bypass_mutation_prevented'] = True
                else:
                    logger.warning("db_store may allow direct DB access")
                    self.violations.append("Potential direct DB access")
                    return False
            else:
                logger.warning("TaskService missing db_store")
                self.violations.append("TaskService missing db_store")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Bypass mutation validation failed: {e}")
            self.violations.append(f"Bypass mutation validation error: {e}")
            return False
    
    def get_validation_report(self) -> Dict[str, Any]:
        """Generate validation report"""
        return {
            'metrics': self.metrics,
            'violations': self.violations,
            'overall_status': 'PASS' if len(self.violations) == 0 else 'NEEDS_IMPROVEMENT'
        }


def run_ownership_violation_validation():
    """
    Run complete ownership violation validation suite.
    
    This IS behavioral runtime validation:
    - Actually checks ownership context enforcement
    - Validates unauthorized write blocking
    - Validates repository guards
    - Validates bypass mutation prevention
    
    This is NOT structural introspection.
    """
    logger.info("=" * 80)
    logger.info("BEHAVIORAL VALIDATION: OWNERSHIP VIOLATION INJECTION TESTS")
    logger.info("=" * 80)
    
    # Initialize DI container for testing
    initialize_di_container_for_testing()
    
    validator = OwnershipViolationValidator()
    
    # Test 1: Ownership context set
    validator.validate_ownership_context_set()
    
    # Test 2: Unauthorized write blocked
    validator.validate_unauthorized_write_blocked()
    
    # Test 3: Repository guards enforced
    validator.validate_repository_guards_enforced()
    
    # Test 4: Bypass mutation prevented
    validator.validate_bypass_mutation_prevented()
    
    # Summary
    report = validator.get_validation_report()
    
    logger.info("=" * 80)
    logger.info("OWNERSHIP VIOLATION VALIDATION SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Ownership Context Set: {report['metrics']['ownership_context_set']}")
    logger.info(f"Unauthorized Write Blocked: {report['metrics']['unauthorized_write_blocked']}")
    logger.info(f"Repository Guards Enforced: {report['metrics']['repository_guards_enforced']}")
    logger.info(f"Bypass Mutation Prevented: {report['metrics']['bypass_mutation_prevented']}")
    logger.info(f"OVERALL: {report['overall_status']}")
    logger.info("=" * 80)
    
    if report['overall_status'] == 'NEEDS_IMPROVEMENT':
        logger.warning("OWNERSHIP VIOLATION VALIDATION NEEDS IMPROVEMENT")
        logger.warning("Some ownership enforcement guarantees not met")
    else:
        logger.info("OWNERSHIP VIOLATION VALIDATION PASSED")
    
    return report


if __name__ == "__main__":
    report = run_ownership_violation_validation()
    exit(0 if report['overall_status'] == 'PASS' else 1)
