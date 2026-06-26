"""
Unified State Model for All Learners
Provides a single structured state format to eliminate tuple/float inconsistencies
"""

from dataclasses import dataclass
from typing import Optional
import logging

logger = logging.getLogger(__name__)

@dataclass
class LearnerState:
    """Unified state representation for all learners"""
    mastery: float                    # Always present - 0.0 to 1.0
    alpha: Optional[float] = None     # Bayesian alpha parameter
    beta: Optional[float] = None      # Bayesian beta parameter  
    covariance: Optional[float] = None  # Kalman covariance
    
    def __post_init__(self):
        """Validate state after initialization"""
        if not 0.0 <= self.mastery <= 1.0:
            logger.warning(f"Mastery {self.mastery} out of bounds, clamping to [0,1]")
            self.mastery = max(0.0, min(1.0, self.mastery))
    
    @classmethod
    def create_lyapunov(cls, mastery: float) -> 'LearnerState':
        """Create state for Lyapunov learner"""
        return cls(mastery=mastery)
    
    @classmethod
    def create_bayesian(cls, alpha: float, beta: float) -> 'LearnerState':
        """Create state for Bayesian learner"""
        mastery = alpha / (alpha + beta) if (alpha + beta) > 0 else 0.3
        return cls(mastery=mastery, alpha=alpha, beta=beta)
    
    @classmethod
    def create_kalman(cls, mastery: float, covariance: float) -> 'LearnerState':
        """Create state for Kalman learner"""
        return cls(mastery=mastery, covariance=covariance)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for logging/debugging"""
        return {
            'mastery': self.mastery,
            'alpha': self.alpha,
            'beta': self.beta,
            'covariance': self.covariance
        }
