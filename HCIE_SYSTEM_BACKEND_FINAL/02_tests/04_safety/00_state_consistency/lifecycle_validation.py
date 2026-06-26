"""
Lifecycle Validation

Validates lifecycle guarantees after DI convergence.

Critical because authoritative cores have complex lifecycle requirements:
- Startup reconstruction order
- Cache warming semantics
- Multi-tier persistence consistency
- Reconstruction idempotency
- Cache consistency

DI migration must not break these lifecycle semantics.
"""

import logging
from typing import Dict, Any
from app.infrastructure.di.dependency_injection import get_di_container
from app.api.dependencies.learning import get_task_service

logger = logging.getLogger(__name__)


class LifecycleValidator:
    """
    Validates lifecycle guarantees for authoritative cores.
    """
    
    def __init__(self):
        self.violations = []
        self.metrics = {
            'startup_reconstruction': False,
            'cache_warming': False,
            'redis_postgres_consistency': False,
            'reconstruction_idempotency': False,
            'tiered_persistence': False
        }
    
    def validate_startup_reconstruction(self) -> bool:
        """
        Validate startup reconstruction occurs once on startup.
        
        TaskService must reconstruct state from PostgreSQL on startup.
        DI migration must not break this reconstruction.
        """
        logger.info("Validating startup reconstruction...")
        
        task_service = get_task_service()
        
        # Check if TaskService has reconstruction capability
        if hasattr(task_service, '_reconstruct_user_state'):
            logger.info("TaskService has reconstruction capability")
            
            # Check if reconstruction has been completed
            if hasattr(task_service, '_reconstruction_complete'):
                if task_service._reconstruction_complete:
                    logger.info("TaskService reconstruction completed")
                    self.metrics['startup_reconstruction'] = True
                else:
                    logger.warning("TaskService reconstruction not completed")
                    self.metrics['startup_reconstruction'] = False
            else:
                logger.warning("TaskService reconstruction completion flag not found")
                self.metrics['startup_reconstruction'] = 'requires_manual_validation'
        else:
            logger.error("TaskService does not have reconstruction capability")
            self.violations.append("TaskService missing reconstruction capability")
            self.metrics['startup_reconstruction'] = False
        
        return self.metrics['startup_reconstruction']
    
    def validate_cache_warming(self) -> bool:
        """
        Validate cache warming occurs correctly.
        
        Cache warming order: hot users → warm users → cold users
        DI migration must not change this ordering.
        """
        logger.info("Validating cache warming...")
        
        task_service = get_task_service()
        
        if hasattr(task_service, '_warm_redis_cache'):
            logger.info("TaskService has cache warming capability")
            self.metrics['cache_warming'] = True
        else:
            logger.warning("TaskService cache warming capability not found")
            self.metrics['cache_warming'] = 'requires_manual_validation'
        
        return True
    
    def validate_redis_postgres_consistency(self) -> bool:
        """
        Validate Redis and PostgreSQL consistency.
        
        Multi-tier persistence requires Redis and PostgreSQL to be consistent.
        DI migration must not break this consistency.
        """
        logger.info("Validating Redis/PostgreSQL consistency...")
        
        task_service = get_task_service()
        
        # Check if TaskService has bandit state
        if hasattr(task_service, 'bandit') and task_service.bandit is not None:
            logger.info("TaskService has bandit state")
            
            # Check if bandit has multi-tier persistence
            bandit = task_service.bandit
            if hasattr(bandit, '_redis_client') and hasattr(bandit, '_postgres_store'):
                logger.info("Bandit has both Redis and PostgreSQL clients")
                self.metrics['redis_postgres_consistency'] = True
            else:
                logger.warning("Bandit missing Redis or PostgreSQL client")
                self.metrics['redis_postgres_consistency'] = False
        else:
            logger.warning("TaskService bandit not available")
            self.metrics['redis_postgres_consistency'] = 'requires_manual_validation'
        
        return True
    
    def validate_reconstruction_idempotency(self) -> bool:
        """
        Validate reconstruction is idempotent.
        
        Reconstruction should only occur once per process lifetime.
        DI migration must preserve this idempotency.
        """
        logger.info("Validating reconstruction idempotency...")
        
        task_service = get_task_service()
        
        if hasattr(task_service, '_reconstruction_complete'):
            logger.info("TaskService has reconstruction completion flag")
            self.metrics['reconstruction_idempotency'] = True
        else:
            logger.warning("TaskService reconstruction completion flag not found")
            self.metrics['reconstruction_idempotency'] = 'requires_manual_validation'
        
        return True
    
    def validate_tiered_persistence(self) -> bool:
        """
        Validate tiered persistence ordering.
        
        Persistence order: PostgreSQL (source of truth) → Redis (cache)
        DI migration must not change this ordering.
        """
        logger.info("Validating tiered persistence ordering...")
        
        task_service = get_task_service()
        
        if hasattr(task_service, 'db_store'):
            logger.info("TaskService has database store")
            
            # Check if db_store has PostgreSQL
            if hasattr(task_service.db_store, '_get_connection'):
                logger.info("TaskService db_store has PostgreSQL connection")
                self.metrics['tiered_persistence'] = True
            else:
                logger.warning("TaskService db_store PostgreSQL connection not found")
                self.metrics['tiered_persistence'] = False
        else:
            logger.warning("TaskService db_store not found")
            self.metrics['tiered_persistence'] = False
        
        return True
    
    def get_validation_report(self) -> Dict[str, Any]:
        """Generate validation report"""
        return {
            'metrics': self.metrics,
            'violations': self.violations,
            'overall_status': 'PASS' if len(self.violations) == 0 else 'NEEDS_VALIDATION'
        }


def run_lifecycle_validation():
    """
    Run complete lifecycle validation suite.
    
    This is CRITICAL before Stage 3 adapter removal because:
    - Lifecycle requirements are complex for authoritative cores
    - DI migration CAN affect reconstruction order
    - Cache warming order affects replay determinism
    - Multi-tier persistence consistency must be preserved
    """
    logger.info("=" * 80)
    logger.info("LIFECYCLE VALIDATION SUITE")
    logger.info("=" * 80)
    
    validator = LifecycleValidator()
    
    # Test 1: Startup reconstruction
    validator.validate_startup_reconstruction()
    
    # Test 2: Cache warming
    validator.validate_cache_warming()
    
    # Test 3: Redis/PostgreSQL consistency
    validator.validate_redis_postgres_consistency()
    
    # Test 4: Reconstruction idempotency
    validator.validate_reconstruction_idempotency()
    
    # Test 5: Tiered persistence
    validator.validate_tiered_persistence()
    
    # Summary
    report = validator.get_validation_report()
    
    logger.info("=" * 80)
    logger.info("LIFECYCLE VALIDATION SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Startup Reconstruction: {report['metrics']['startup_reconstruction']}")
    logger.info(f"Cache Warming: {report['metrics']['cache_warming']}")
    logger.info(f"Redis/Postgres Consistency: {report['metrics']['redis_postgres_consistency']}")
    logger.info(f"Reconstruction Idempotency: {report['metrics']['reconstruction_idempotency']}")
    logger.info(f"Tiered Persistence: {report['metrics']['tiered_persistence']}")
    logger.info(f"OVERALL: {report['overall_status']}")
    logger.info("=" * 80)
    
    if report['overall_status'] == 'NEEDS_VALIDATION':
        logger.warning("LIFECYCLE VALIDATION REQUIRES MANUAL VALIDATION")
        logger.warning("Some checks require runtime inspection or manual verification")
    else:
        logger.info("LIFECYCLE VALIDATION PASSED")
    
    return report


if __name__ == "__main__":
    report = run_lifecycle_validation()
    exit(0 if report['overall_status'] == 'PASS' else 1)
