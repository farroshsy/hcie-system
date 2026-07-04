"""
Task State Reconstruction Service - Domain logic for state management
Moved from ServiceFactory to proper dependency injection
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class TaskStateReconstructionService:
    """Service for task state reconstruction with explicit dependency injection"""
    
    def __init__(self, user_repo=None, experiment_repo=None, analytics_service=None):
        """Initialize TaskService with explicit dependencies"""
        self.user_repo = user_repo
        self.experiment_repo = experiment_repo
        self.analytics_service = analytics_service
        
        # State management - properly initialized
        self.bandit = {}  # ✅ Initialize to avoid runtime crash
        self.step_count = {}
        self.total_users = 0
        self.total_steps = 0
        
        logger.info("✅ TaskStateReconstructionService initialized with explicit DI")
    
    def get_task_service(self) -> 'TaskStateReconstructionService':
        """Get task service (legacy compatibility during transition)"""
        return self
    
    def reconstruct_user_state(self) -> Dict[str, Any]:
        """Reconstruct user state from interaction history"""
        logger.info("🔄 Starting state reconstruction")
        
        if not self.user_repo:
            logger.warning("⚠️ No user repository available")
            return {}
        
        try:
            # Get all users
            users = self.user_repo.get_all_users()
            self.total_users = len(users)
            
            # Reconstruct state for each user
            for user in users:
                user_id = user['id']
                interactions = self.user_repo.get_user_interactions(user_id)
                
                if interactions:
                    # Process interactions in chronological order (oldest → newest)
                    interactions.sort(key=lambda x: x['timestamp'])
                    
                    # Initialize or update bandit state
                    if user_id not in self.bandit:
                        self.bandit[user_id] = {}
                    
                    # Process each interaction
                    for interaction in interactions:
                        self._process_interaction(user_id, interaction)
                    
                    self.step_count[user_id] = len(interactions)
                    self.total_steps += len(interactions)
            
            logger.info(f"✅ State reconstruction completed: {len(self.bandit)} users, {self.total_steps} total steps")
            
            return {
                "total_users": len(self.bandit),
                "total_steps": self.total_steps,
                "bandit_state": self.bandit
            }
            
        except Exception as e:
            logger.error(f"❌ State reconstruction failed: {e}")
            return {}
    
    def _process_interaction(self, user_id: str, interaction: Dict[str, Any]) -> None:
        """Process a single interaction for bandit learning"""
        try:
            # Extract interaction data
            task_id = interaction.get('task_id')
            answer = interaction.get('answer')
            is_correct = interaction.get('is_correct', False)
            
            # Update bandit state
            if user_id not in self.bandit:
                self.bandit[user_id] = {
                    'alpha': 1.0,
                    'beta': 1.0,
                    'step_count': 0
                }
            
            bandit = self.bandit[user_id]
            bandit['step_count'] += 1
            
            if is_correct:
                bandit['beta'] += 1
            else:
                bandit['alpha'] += 1
            
            # Update task mastery
            if task_id and task_id in bandit:
                if task_id not in bandit:
                    bandit[task_id] = {'alpha': 1.0, 'beta': 1.0}
                
                bandit[task_id]['alpha'] += 1
                bandit[task_id]['beta'] += 1
            
            logger.debug(f"Processed interaction for user {user_id}, task {task_id}, correct: {is_correct}")
            
        except Exception as e:
            logger.error(f"❌ Failed to process interaction: {e}")
    
    def get_user_state(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get current bandit state for user"""
        return self.bandit.get(user_id) if self.bandit else None
    
    def get_user_step_count(self, user_id: str) -> int:
        """Get step count for user"""
        return self.step_count.get(user_id, 0)
    
    def get_total_users(self) -> int:
        """Get total reconstructed users"""
        return self.total_users
    
    def get_total_steps(self) -> int:
        """Get total steps processed"""
        return self.total_steps
