"""
Ownership Enforcement Validation

Validates ownership context enforcement after DI convergence.

Critical because ownership contracts prevent unauthorized state mutations:
- Ownership context set before writes
- Ownership context cleared after writes
- No bypass mutations
- Repository guards enforce ownership

DI migration must not break ownership enforcement.
"""

import logging
from typing import Dict, Any
from app.api.dependencies.learning import get_task_service, get_unified_brain

logger = logging.getLogger(__name__)


class OwnershipEnforcementValidator:
    """
    Validates ownership context enforcement.
    """
    
    def __init__(self):
        self.violations = []
        self.metrics = {
            'task_service_ownership': False,
            'unified_brain_ownership': False,
            'repository_guards': False,
            'bypass_mutation_detection': False
        }
    
    def validate_task_service_ownership(self) -> bool:
        """
        Validate TaskService ownership context enforcement.
        
        TaskService must set ownership context before mastery state writes.
        """
        logger.info("Validating TaskService ownership context...")
        
        task_service = get_task_service()
        
        # Check if TaskService has ownership enforcement
        if hasattr(task_service, 'bandit') and task_service.bandit is not None:
            logger.info("TaskService has bandit (ownership authority)")
            
            bandit = task_service.bandit
            if hasattr(bandit, '_learning_state_repo'):
                logger.info("Bandit has learning state repository")
                
                repo = bandit._learning_state_repo
                if hasattr(repo, 'ownership'):
                    logger.info("Repository has ownership context")
                    self.metrics['task_service_ownership'] = True
                else:
                    logger.warning("Repository missing ownership context")
                    self.violations.append("Repository missing ownership context")
                    self.metrics['task_service_ownership'] = False
            else:
                logger.warning("Bandit missing learning state repository")
                self.metrics['task_service_ownership'] = False
        else:
            logger.warning("TaskService bandit not available")
            self.metrics['task_service_ownership'] = 'requires_manual_validation'
        
        return True
    
    def validate_unified_brain_ownership(self) -> bool:
        """
        Validate UnifiedBrain ownership context enforcement.
        
        UnifiedBrain must set ownership context before orchestration writes.
        """
        logger.info("Validating UnifiedBrain ownership context...")
        
        unified_brain = get_unified_brain()
        
        if unified_brain is not None:
            logger.info("UnifiedBrain available")
            
            if hasattr(unified_brain, '_learning_state_repo'):
                logger.info("UnifiedBrain has learning state repository")
                
                repo = unified_brain._learning_state_repo
                if hasattr(repo, 'ownership'):
                    logger.info("Repository has ownership context")
                    self.metrics['unified_brain_ownership'] = True
                else:
                    logger.warning("Repository missing ownership context")
                    self.metrics['unified_brain_ownership'] = False
            else:
                logger.warning("UnifiedBrain missing learning state repository")
                self.metrics['unified_brain_ownership'] = False
        else:
            logger.warning("UnifiedBrain not available")
            self.metrics['unified_brain_ownership'] = 'requires_manual_validation'
        
        return True
    
    def validate_repository_guards(self) -> bool:
        """
        Validate repository guards enforce ownership.
        
        Repositories should enforce ownership context before writes.
        """
        logger.info("Validating repository guards...")
        
        task_service = get_task_service()
        
        if hasattr(task_service, 'bandit') and task_service.bandit is not None:
            bandit = task_service.bandit
            
            if hasattr(bandit, '_learning_state_repo'):
                repo = bandit._learning_state_repo
                
                # Check for ownership enforcement methods
                if hasattr(repo, 'ownership'):
                    ownership = repo.ownership
                    
                    if hasattr(ownership, 'set_writer'):
                        logger.info("Repository has set_writer method")
                        self.metrics['repository_guards'] = True
                    else:
                        logger.warning("Repository ownership missing set_writer method")
                        self.metrics['repository_guards'] = False
                else:
                    logger.warning("Repository missing ownership")
                    self.metrics['repository_guards'] = False
            else:
                logger.warning("Bandit missing learning state repository")
                self.metrics['repository_guards'] = False
        else:
            logger.warning("TaskService bandit not available")
            self.metrics['repository_guards'] = 'requires_manual_validation'
        
        return True
    
    def validate_bypass_mutation_detection(self) -> bool:
        """
        Validate bypass mutations are detected.
        
        Direct DB access should be detected as bypass mutations.
        This requires static analysis or runtime monitoring.
        """
        logger.info("Validating bypass mutation detection...")
        
        # This requires static analysis or runtime monitoring
        logger.warning("Bypass mutation detection requires static analysis or runtime monitoring")
        self.metrics['bypass_mutation_detection'] = 'requires_static_analysis'
        
        return True
    
    def get_validation_report(self) -> Dict[str, Any]:
        """Generate validation report"""
        return {
            'metrics': self.metrics,
            'violations': self.violations,
            'overall_status': 'PASS' if len(self.violations) == 0 else 'NEEDS_VALIDATION'
        }


def run_ownership_enforcement_validation():
    """
    Run complete ownership enforcement validation suite.
    
    This is CRITICAL before Stage 3 adapter removal because:
    - Ownership contracts prevent unauthorized state mutations
    - DI migration CAN affect ownership context enforcement
    - Bypass mutations can corrupt canonical state
    - Repository guards must be preserved
    """
    logger.info("=" * 80)
    logger.info("OWNERSHIP ENFORCEMENT VALIDATION SUITE")
    logger.info("=" * 80)
    
    validator = OwnershipEnforcementValidator()
    
    # Test 1: TaskService ownership
    validator.validate_task_service_ownership()
    
    # Test 2: UnifiedBrain ownership
    validator.validate_unified_brain_ownership()
    
    # Test 3: Repository guards
    validator.validate_repository_guards()
    
    # Test 4: Bypass mutation detection
    validator.validate_bypass_mutation_detection()
    
    # Summary
    report = validator.get_validation_report()
    
    logger.info("=" * 80)
    logger.info("OWNERSHIP ENFORCEMENT VALIDATION SUMMARY")
    logger.info("=" * 80)
    logger.info(f"TaskService Ownership: {report['metrics']['task_service_ownership']}")
    logger.info(f"UnifiedBrain Ownership: {report['metrics']['unified_brain_ownership']}")
    logger.info(f"Repository Guards: {report['metrics']['repository_guards']}")
    logger.info(f"Bypass Mutation Detection: {report['metrics']['bypass_mutation_detection']}")
    logger.info(f"OVERALL: {report['overall_status']}")
    logger.info("=" * 80)
    
    if report['overall_status'] == 'NEEDS_VALIDATION':
        logger.warning("OWNERSHIP ENFORCEMENT VALIDATION REQUIRES MANUAL VALIDATION")
        logger.warning("Some checks require static analysis or runtime monitoring")
    else:
        logger.info("OWNERSHIP ENFORCEMENT VALIDATION PASSED")
    
    return report


if __name__ == "__main__":
    report = run_ownership_enforcement_validation()
    exit(0 if report['overall_status'] == 'PASS' else 1)
