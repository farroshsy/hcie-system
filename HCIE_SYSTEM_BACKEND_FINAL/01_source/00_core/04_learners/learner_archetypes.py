"""
Learner Archetypes as Unified Brain Parameter Configurations

Implements 6 learner archetypes as Unified Brain policy configurations.
This ensures evaluation validity - archetypes use the same Unified Brain cognition logic
with different parameter tuning, not separate math engines.

Archetypes:
1. Novice: Slow learning, high uncertainty, needs structured guidance
2. Unstable: Inconsistent performance, variable mastery, high variance
3. Transfer-Heavy: Strong transfer learning, builds on prior knowledge effectively
4. Forgetting: Rapid forgetting, needs frequent reinforcement
5. Exploration-Sensitive: Highly sensitive to exploration, benefits from variety
6. Challenge-Seeking: Prefers challenging tasks, high ZPD alignment

VALIDITY NOTE: These are parameter configurations for Unified Brain, not separate calculation engines.
Experiments using these configurations evaluate the real system with different learner characteristics.
"""

from typing import Dict
from enum import Enum


class ArchetypeType(Enum):
    NOVICE = "novice"
    UNSTABLE = "unstable"
    TRANSFER_HEAVY = "transfer_heavy"
    FORGETTING = "forgetting"
    EXPLORATION_SENSITIVE = "exploration_sensitive"
    CHALLENGE_SEEKING = "challenge_seeking"


class LearnerArchetypeConfig:
    """
    Learner archetype configurations as Unified Brain policy parameters.
    
    These configurations tune Unified Brain's existing cognition logic to simulate
    different learner types, ensuring evaluation validity.
    """
    
    @staticmethod
    def get_archetype_config(archetype_type: ArchetypeType) -> Dict[str, float]:
        """
        Get Unified Brain policy configuration for an archetype.
        
        Args:
            archetype_type: Learner archetype type
            
        Returns:
            Policy configuration dictionary for Unified Brain
        """
        configs = {
            ArchetypeType.NOVICE: {
                # Novice: Slow learning, high uncertainty, low transfer
                'learning_rate': 0.1,
                'exploration_rate': 0.3,
                'transfer_weight': 0.2,
                'uncertainty_weight': 0.8,
                'zpd_weight': 0.3,
                'challenge_weight': 0.2,
                'mastery_weight': 0.7,
                'lyapunov_weight': 0.5,
                'bayesian_weight': 0.5,
                'kalman_weight': 0.5
            },
            ArchetypeType.UNSTABLE: {
                # Unstable: Variable learning, high variance
                'learning_rate': 0.2,
                'exploration_rate': 0.5,
                'transfer_weight': 0.4,
                'uncertainty_weight': 0.5,
                'zpd_weight': 0.5,
                'challenge_weight': 0.5,
                'mastery_weight': 0.5,
                'lyapunov_weight': 0.5,
                'bayesian_weight': 0.5,
                'kalman_weight': 0.5,
                # Add variance parameter for stochasticity
                'cognition_variance': 0.1
            },
            ArchetypeType.TRANSFER_HEAVY: {
                # Transfer-Heavy: High transfer, builds on prior knowledge
                'learning_rate': 0.3,
                'exploration_rate': 0.5,
                'transfer_weight': 0.8,
                'uncertainty_weight': 0.3,
                'zpd_weight': 0.5,
                'challenge_weight': 0.5,
                'mastery_weight': 0.6,
                'lyapunov_weight': 0.6,
                'bayesian_weight': 0.6,
                'kalman_weight': 0.6
            },
            ArchetypeType.FORGETTING: {
                # Forgetting: Rapid forgetting, needs reinforcement
                'learning_rate': 0.25,
                'exploration_rate': 0.4,
                'transfer_weight': 0.3,
                'uncertainty_weight': 0.6,
                'zpd_weight': 0.4,
                'challenge_weight': 0.4,
                'mastery_weight': 0.5,
                'lyapunov_weight': 0.4,
                'bayesian_weight': 0.4,
                'kalman_weight': 0.4,
                # Forgetting rate parameter (requires Unified Brain support)
                'forgetting_rate': 0.15
            },
            ArchetypeType.EXPLORATION_SENSITIVE: {
                # Exploration-Sensitive: Benefits from variety, novelty bonus
                'learning_rate': 0.3,
                'exploration_rate': 0.7,
                'transfer_weight': 0.5,
                'uncertainty_weight': 0.4,
                'zpd_weight': 0.5,
                'challenge_weight': 0.4,
                'mastery_weight': 0.5,
                'lyapunov_weight': 0.5,
                'bayesian_weight': 0.5,
                'kalman_weight': 0.5,
                # Novelty bonus parameter (requires Unified Brain support)
                'novelty_bonus': 0.15
            },
            ArchetypeType.CHALLENGE_SEEKING: {
                # Challenge-Seeking: Prefers challenge, high ZPD alignment
                'learning_rate': 0.4,
                'exploration_rate': 0.5,
                'transfer_weight': 0.7,
                'uncertainty_weight': 0.3,
                'zpd_weight': 0.8,
                'challenge_weight': 0.7,
                'mastery_weight': 0.6,
                'lyapunov_weight': 0.6,
                'bayesian_weight': 0.6,
                'kalman_weight': 0.6
            }
        }
        
        return configs.get(archetype_type, configs[ArchetypeType.NOVICE])
    
    @staticmethod
    def get_all_archetype_configs() -> Dict[ArchetypeType, Dict[str, float]]:
        """
        Get all archetype configurations.
        
        Returns:
            Dictionary mapping archetype types to policy configurations
        """
        return {
            archetype_type: LearnerArchetypeConfig.get_archetype_config(archetype_type)
            for archetype_type in ArchetypeType
        }
    
    @staticmethod
    def get_archetype_description(archetype_type: ArchetypeType) -> str:
        """
        Get human-readable description of an archetype.
        
        Args:
            archetype_type: Learner archetype type
            
        Returns:
            Description string
        """
        descriptions = {
            ArchetypeType.NOVICE: "Novice: Slow learning (0.1), high uncertainty (0.8), low transfer (0.2)",
            ArchetypeType.UNSTABLE: "Unstable: Variable learning (0.2), high variance (0.1)",
            ArchetypeType.TRANSFER_HEAVY: "Transfer-Heavy: High transfer (0.8), builds on prior knowledge",
            ArchetypeType.FORGETTING: "Forgetting: Rapid forgetting (0.15), needs reinforcement",
            ArchetypeType.EXPLORATION_SENSITIVE: "Exploration-Sensitive: Benefits from variety (0.7), novelty bonus (0.15)",
            ArchetypeType.CHALLENGE_SEEKING: "Challenge-Seeking: High learning rate (0.4), prefers challenge (0.7), high ZPD (0.8)"
        }
        
        return descriptions.get(archetype_type, "Unknown archetype")
