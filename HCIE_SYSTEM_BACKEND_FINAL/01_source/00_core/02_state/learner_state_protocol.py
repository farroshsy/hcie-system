"""
🔥 Learner State Protocol
Typed interface for all learner states to ensure consistency

This eliminates dictionary-based state access bugs and provides type safety
"""

from dataclasses import dataclass
from typing import Union, Optional
from enum import Enum

class LearnerType(Enum):
    LYAPUNOV = "lyapunov"
    BAYESIAN = "bayesian"
    KALMAN = "kalman"

@dataclass
class LyapunovState:
    """Typed state for Lyapunov learner"""
    mastery: float
    alpha: Optional[float] = None
    beta: Optional[float] = None
    covariance: Optional[float] = None

@dataclass
class BayesianState:
    """Typed state for Bayesian learner"""
    alpha: float
    beta: float
    mastery: Optional[float] = None  # Computed from alpha/beta

@dataclass
class KalmanState:
    """Typed state for Kalman learner"""
    mastery: float
    covariance: float
    mean: Optional[float] = None

@dataclass
class LearnerState:
    """Union type for all learner states"""
    learner_type: LearnerType
    state: Union[LyapunovState, BayesianState, KalmanState]
    
    def get_mastery(self) -> float:
        """Get mastery regardless of learner type"""
        if self.learner_type == LearnerType.LYAPUNOV:
            return self.state.mastery
        elif self.learner_type == LearnerType.BAYESIAN:
            if self.state.alpha is not None and self.state.beta is not None:
                return self.state.alpha / (self.state.alpha + self.state.beta)
            return 0.3  # fallback
        elif self.learner_type == LearnerType.KALMAN:
            return self.state.mastery
        else:
            return 0.3
    
    def get_alpha_beta(self) -> tuple[float, float]:
        """Get alpha/beta for Bayesian learner"""
        if self.learner_type == LearnerType.BAYESIAN:
            return (self.state.alpha, self.state.beta)
        else:
            return (1.0, 1.0)  # fallback
    
    def get_covariance(self) -> float:
        """Get covariance for Kalman learner"""
        if self.learner_type == LearnerType.KALMAN:
            return self.state.covariance
        else:
            return 0.01  # fallback
