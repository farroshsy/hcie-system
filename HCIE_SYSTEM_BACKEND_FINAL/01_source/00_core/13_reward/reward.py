"""
Reward Function for Mathematical Model
Production-aligned implementation of comprehensive reward calculation
Copied from existing working infrastructure
"""

import math
from typing import Dict, Optional
import logging
from ..mastery.mastery_model import MasteryModel
from ..bandit.bandit import ContextualBandit
from ..policy.policy import PolicyEngine

logger = logging.getLogger(__name__)

class RewardCalculator:
    """
    Computes comprehensive rewards following mathematical model
    R_t = f(correct, time, difficulty, consistency, learning)
    """
    
    def __init__(self,
                 correctness_weight: float = 0.5,
                 speed_weight: float = 0.3,
                 difficulty_weight: float = 0.2,
                 time_threshold: float = 30.0,
                 consistency_bonus: float = 0.1):
        """
        Initialize reward calculator
        
        Args:
            correctness_weight: Weight for answer correctness (w_correct)
            speed_weight: Weight for response time (w_speed)
            difficulty_weight: Weight for task difficulty (w_difficulty)
            time_threshold: Expected time threshold (T_threshold)
            consistency_bonus: Bonus for consistent performance
        """
        self.correctness_weight = correctness_weight
        self.speed_weight = speed_weight
        self.difficulty_weight = difficulty_weight
        self.time_threshold = time_threshold
        self.consistency_bonus = consistency_bonus
        
        logger.info("Reward Calculator initialized")
    
    def calculate_reward(self, 
                        correct: bool,
                        time_taken: float,
                        difficulty: float,
                        response_consistency: Optional[float] = None,
                        learning_progress: Optional[float] = None) -> float:
        """Alias for compute_reward for compatibility"""
        return self.compute_reward(correct, time_taken, difficulty, response_consistency, learning_progress)
    
    def compute_reward(self,
                      correct: bool,
                      time_taken: float,
                      difficulty: float,
                      response_consistency: Optional[float] = None,
                      learning_progress: Optional[float] = None) -> float:
        """
        Compute comprehensive reward following mathematical model
        
        R_t = 0.5 * correct + 0.3 * speed_score + 0.2 * difficulty_adjust
        
        Args:
            correct: Whether answer was correct
            time_taken: Time taken to answer (seconds)
            difficulty: Task difficulty (0-1)
            response_consistency: Consistency with previous answers (0-1)
            learning_progress: Evidence of learning progress (0-1)
        
        Returns:
            Reward value in [0, 1]
        """
        try:
            # Base correctness component
            correctness_score = self.correctness_weight * (1.0 if correct else 0.0)
            
            # Speed component: faster is better, but with diminishing returns
            speed_score = self._calculate_speed_score(time_taken)
            speed_component = self.speed_weight * speed_score
            
            # Difficulty adjustment: harder tasks give more reward
            difficulty_adjust = 1.0 + difficulty
            difficulty_component = self.difficulty_weight * difficulty_adjust
            
            # Base reward
            base_reward = correctness_score + speed_component + difficulty_component
            
            # Apply consistency bonus if available
            if response_consistency is not None:
                consistency_reward = self.consistency_bonus * response_consistency
                base_reward += consistency_reward
            
            # Apply learning progress bonus if available
            if learning_progress is not None:
                learning_reward = 0.05 * learning_progress  # Small bonus for learning
                base_reward += learning_reward
            
            # Normalize to [0, 1] range
            normalized_reward = min(1.0, max(0.0, base_reward))
            
            # DEBUG: Log detailed breakdown
            logger.info(f"REWARD DEBUG: correct={correct}, time={time_taken:.1f}s, difficulty={difficulty:.2f}")
            logger.info(f"  correctness_score={correctness_score:.3f}, speed_score={speed_score:.3f}, speed_component={speed_component:.3f}")
            logger.info(f"  difficulty_adjust={difficulty_adjust:.3f}, difficulty_component={difficulty_component:.3f}")
            logger.info(f"  base_reward={base_reward:.3f}, normalized_reward={normalized_reward:.3f}")
            
            return normalized_reward
            
        except Exception as e:
            logger.error(f"Error computing reward: {e}")
            return 0.5  # Default reward
    
    def _calculate_speed_score(self, time_taken: float) -> float:
        """
        Calculate speed score with diminishing returns
        
        speed_score = max(0, 1 - time_taken / T_threshold)
        """
        if time_taken <= 0:
            return 1.0
        
        # Linear decay with threshold
        raw_score = max(0.0, 1.0 - time_taken / self.time_threshold)
        
        # Apply diminishing returns for very fast responses
        if raw_score > 0.9:
            # Cap very fast responses to avoid gaming the system
            return 0.9 + 0.1 * (raw_score - 0.9)
        
        return raw_score
    
    def compute_detailed_reward(self,
                               correct: bool,
                               time_taken: float,
                               difficulty: float,
                               response_consistency: Optional[float] = None,
                               learning_progress: Optional[float] = None,
                               user_mastery: Optional[float] = None) -> Dict[str, float]:
        """
        Compute detailed reward with component breakdown
        
        Returns:
            Dictionary with all reward components
        """
        try:
            # Individual components
            correctness_component = self.correctness_weight * (1.0 if correct else 0.0)
            speed_score = self._calculate_speed_score(time_taken)
            speed_component = self.speed_weight * speed_score
            difficulty_adjust = 1.0 + difficulty
            difficulty_component = self.difficulty_weight * difficulty_adjust
            
            # Bonus components
            consistency_component = 0.0
            if response_consistency is not None:
                consistency_component = self.consistency_bonus * response_consistency
            
            learning_component = 0.0
            if learning_progress is not None:
                learning_component = 0.05 * learning_progress
            
            # Mastery adjustment (optional)
            mastery_adjustment = 1.0
            if user_mastery is not None:
                # Adjust reward based on mastery level
                if user_mastery < 0.3:
                    mastery_adjustment = 1.2  # Bonus for learning new skills
                elif user_mastery > 0.8:
                    mastery_adjustment = 0.9  # Slight penalty for very easy tasks
            
            # Calculate total reward
            total_reward = (
                correctness_component + 
                speed_component + 
                difficulty_component + 
                consistency_component + 
                learning_component
            ) * mastery_adjustment
            
            # Normalize
            total_reward = min(1.0, max(0.0, total_reward))
            
            return {
                "total_reward": total_reward,
                "correctness_component": correctness_component,
                "speed_component": speed_component,
                "difficulty_component": difficulty_component,
                "consistency_component": consistency_component,
                "learning_component": learning_component,
                "speed_score": speed_score,
                "mastery_adjustment": mastery_adjustment,
                "normalized": True
            }
            
        except Exception as e:
            logger.error(f"Error computing detailed reward: {e}")
            return {"total_reward": 0.5, "error": str(e)}
    
    def analyze_reward_distribution(self,
                                  rewards: list[float],
                                  time_window: Optional[int] = None) -> Dict[str, float]:
        """
        Analyze reward distribution over time
        
        Args:
            rewards: List of reward values
            time_window: Optional time window for analysis
        
        Returns:
            Distribution statistics
        """
        try:
            if not rewards:
                return {"error": "No rewards provided"}
            
            # Basic statistics
            mean_reward = sum(rewards) / len(rewards)
            variance = sum((r - mean_reward) ** 2 for r in rewards) / len(rewards)
            std_dev = math.sqrt(variance)
            
            # Percentiles
            sorted_rewards = sorted(rewards)
            n = len(sorted_rewards)
            
            p25 = sorted_rewards[int(0.25 * n)] if n > 0 else 0
            p50 = sorted_rewards[int(0.5 * n)] if n > 0 else 0
            p75 = sorted_rewards[int(0.75 * n)] if n > 0 else 0
            
            # Trend analysis (if time window provided)
            trend = 0.0
            if time_window and len(rewards) > 1:
                recent_rewards = rewards[-time_window:]
                if len(recent_rewards) > 1:
                    early_avg = sum(recent_rewards[:len(recent_rewards)//2]) / (len(recent_rewards)//2)
                    late_avg = sum(recent_rewards[len(recent_rewards)//2:]) / (len(recent_rewards) - len(recent_rewards)//2)
                    trend = (late_avg - early_avg) / max(early_avg, 0.01)
            
            return {
                "mean": mean_reward,
                "std_dev": std_dev,
                "variance": variance,
                "min": min(rewards),
                "max": max(rewards),
                "p25": p25,
                "p50": p50,
                "p75": p75,
                "trend": trend,
                "sample_size": len(rewards),
                "time_window": time_window
            }
            
        except Exception as e:
            logger.error(f"Error analyzing reward distribution: {e}")
            return {"error": str(e)}
