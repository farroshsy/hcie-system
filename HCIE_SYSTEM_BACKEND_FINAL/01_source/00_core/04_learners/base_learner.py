"""
Base Learner Interface for Pluggable Learning Models
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import numpy as np


class BaseLearner(ABC):
    """Abstract base class for all learning models"""
    
    def __init__(self, redis_store=None):
        self.redis_store = redis_store
    
    @abstractmethod
    def update(self, user_id: str, concept_id: str, interaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update mastery based on interaction
        
        Args:
            user_id: User identifier
            concept_id: Concept identifier  
            interaction: Interaction data containing correct, response_time, difficulty, etc.
            
        Returns:
            Dict containing mastery_after and other metrics
        """
        pass
    
    @abstractmethod
    def get_state(self, user_id: str, concept_id: str):
        """Get current learning state for user/concept"""
        pass
    
    @abstractmethod
    def set_state(self, user_id: str, concept_id: str, state):
        """Set learning state for user/concept"""
        pass
    
    def _redis_key(self, user_id: str, concept_id: str, suffix: str = "") -> str:
        """Generate Redis key with model prefix"""
        model_name = self.__class__.__name__.lower().replace("learner", "")
        return f"{model_name}:{user_id}:{concept_id}{suffix}"
