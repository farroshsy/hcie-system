"""
Experiment Domain Service
Handles A/B testing and experiment assignment
"""

import logging
import random
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class ExperimentService:
    """Experiment domain service - manages experiments and assignments"""
    
    def __init__(self, experiment_repo, user_repo):
        self.experiment_repo = experiment_repo
        self.user_repo = user_repo
    
    def get_active_experiments(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Get all active experiments for a tenant"""
        try:
            return self.experiment_repo.get_active_experiments(tenant_id)
        except Exception as e:
            logger.error(f"❌ Failed to get active experiments for tenant {tenant_id}: {e}")
            return []
    
    def assign_user_to_experiment(self, user_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Assign user to appropriate experiment group"""
        try:
            # Get active experiments for tenant
            active_experiments = self.get_active_experiments(tenant_id)
            
            if not active_experiments:
                logger.info(f"📊 No active experiments for tenant {tenant_id}")
                return None
            
            # For now, assign to first active experiment
            # TODO: Add sophisticated assignment logic (multi-armed bandit, etc.)
            experiment = active_experiments[0]
            
            # Parse experiment groups
            import json
            groups = json.loads(experiment.get('groups', '["hcie", "random"]'))
            
            # Random assignment (can be enhanced with ML-based assignment)
            assigned_group = random.choice(groups)
            
            # Update user with experiment assignment
            self.user_repo.update_experiment_assignment(
                user_id=user_id,
                experiment_id=experiment['id'],
                experiment_group=assigned_group
            )
            
            logger.info(f"🧪 Assigned user {user_id} to experiment {experiment['name']} - group {assigned_group}")
            
            return {
                'experiment_id': experiment['id'],
                'experiment_name': experiment['name'],
                'experiment_group': assigned_group,
                'groups': groups
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to assign user {user_id} to experiment: {e}")
            return None
    
    def get_user_experiment_assignment(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user's current experiment assignment"""
        try:
            user = self.user_repo.get_by_id(user_id)
            if not user:
                return None
            
            experiment_id = user.get('experiment_id')
            experiment_group = user.get('experiment_group')
            
            if not experiment_id or not experiment_group:
                return None
            
            # Get experiment details
            experiment = self.experiment_repo.get_experiment(experiment_id)
            if not experiment:
                return None
            
            return {
                'experiment_id': experiment_id,
                'experiment_name': experiment.get('name'),
                'experiment_group': experiment_group,
                'groups': json.loads(experiment.get('groups', '[]')),
                'status': experiment.get('status')
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get experiment assignment for user {user_id}: {e}")
            return None
    
    def create_experiment(self, tenant_id: str, name: str, groups: List[str], 
                         description: str = None) -> Optional[Dict[str, Any]]:
        """Create new experiment"""
        try:
            import json
            
            experiment_data = {
                'tenant_id': tenant_id,
                'name': name,
                'groups': json.dumps(groups),
                'status': 'created',
                'description': description
            }
            
            experiment = self.experiment_repo.create_experiment(**experiment_data)
            
            logger.info(f"🧪 Created experiment: {name} for tenant {tenant_id}")
            return experiment
            
        except Exception as e:
            logger.error(f"❌ Failed to create experiment {name}: {e}")
            return None
    
    def update_experiment_status(self, experiment_id: str, status: str) -> bool:
        """Update experiment status"""
        try:
            self.experiment_repo.update_experiment_status(experiment_id, status)
            logger.info(f"🧪 Updated experiment {experiment_id} status to {status}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to update experiment {experiment_id} status: {e}")
            return False
