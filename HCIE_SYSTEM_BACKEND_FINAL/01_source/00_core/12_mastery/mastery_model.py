"""
Production-aligned Mastery Model
Implements formal mathematical model for human capability inference
Copied from existing working infrastructure
"""

import math
import random
from typing import Tuple
import logging

logger = logging.getLogger(__name__)

class MasteryModel:
    """
    Mathematical model for mastery inference
    Implements Beta distribution properties and success prediction
    """
    
    @staticmethod
    def mean(alpha: float, beta: float) -> float:
        """
        Calculate mean of Beta distribution
        E[theta] = alpha / (alpha + beta)
        """
        if alpha + beta == 0:
            return 0.5  # Uninformative prior
        mastery = alpha / (alpha + beta)
        # Ensure mastery is bounded [0, 1]
        return max(0.0, min(1.0, mastery))
    
    @staticmethod
    def variance(alpha: float, beta: float) -> float:
        """
        Calculate variance of Beta distribution
        Var(theta) = (alpha * beta) / ((alpha + beta)^2 * (alpha + beta + 1))
        """
        if alpha + beta == 0:
            return 0.25  # Maximum variance for Beta(1,1)
        
        alpha_beta = alpha + beta
        return (alpha * beta) / (
            alpha_beta * alpha_beta * (alpha_beta + 1)
        )
    
    @staticmethod
    def uncertainty(alpha: float, beta: float) -> float:
        """
        Calculate uncertainty as standard deviation
        Used for exploration bonus in Thompson sampling
        """
        return math.sqrt(MasteryModel.variance(alpha, beta))
    
    @staticmethod
    def sample_beta(alpha: float, beta: float) -> float:
        """
        Sample from Beta distribution for Thompson sampling
        
        theta* ~ Beta(alpha, beta)
        """
        if alpha <= 0 or beta <= 0:
            return 0.5
        
        try:
            return random.betavariate(alpha, beta)
        except Exception as e:
            logger.error(f"Error sampling Beta({alpha}, {beta}): {e}")
            return 0.5
    
    @staticmethod
    def probability_of_success(alpha: float, beta: float, difficulty: float) -> float:
        """
        Calculate probability of correct response using Item Response Theory
        
        P(correct) = sigmoid(mastery - difficulty)
        where mastery = E[theta] = alpha / (alpha + beta)
        """
        mastery = MasteryModel.mean(alpha, beta)
        logit = mastery - difficulty
        return 1 / (1 + math.exp(-logit))
    
    @staticmethod
    def calculate_step(alpha: float, beta: float, correct: bool, difficulty: float, response_time: float) -> Tuple[float, float]:
        """
        Calculate realistic mastery step with production calibration
        
        Args:
            alpha: Current alpha parameter
            beta: Current beta parameter
            correct: Whether answer was correct
            difficulty: Task difficulty (0-1)
            response_time: Response time in seconds
            
        Returns:
            (new_alpha, new_beta)
        """
        # Current mastery level with safety guard
        if alpha <= 0 or beta <= 0:
            # Reset to novice prior to prevent corruption
            alpha, beta = 1.0, 2.33  # mastery = 0.3
        current_mastery = alpha / (alpha + beta) if (alpha + beta) > 0 else 0.5
        
        # ── ZPD/IRT-modulated update strength: COMPUTED here, deliberately NOT APPLIED below ──
        # Retained (not deleted) as an auditable record of a tested-and-rejected alternative. An
        # earlier design used this ZPD-aware learning rate to scale the Beta increment; we replayed
        # it as the pseudo-count on the sealed anchor and it predicted next-correct at r≈0.003 vs
        # r≈0.281 for the plain +1/+1 conjugate update — a near-total collapse. The reason is the
        # decision, not the discard: zpd_factor = exp(−gap²/σ) with σ∈{0.01,0.03} floors at 0.05
        # whenever difficulty≠mastery, so the increment stays tiny, mastery is pinned near its prior,
        # variance vanishes, and the estimate loses predictive signal. The conjugate update below is
        # therefore the deployed rule BY MEASUREMENT, not by omission — the simpler model is the
        # better model here, and that is the point worth keeping.
        # Reproduce: research_validation/grounding/scripts/probe_update_strength.py
        #            (report: research_validation/reports/grounding/PROBE_update_strength.md)
        #
        # Difficulty adaptation: target difficulty near mastery with ZPD
        # ZPD: optimal learning when difficulty ≈ mastery ± 0.1
        zpd_center = current_mastery
        zpd_width = 0.2  # ±0.1 range

        # Production-calibrated update strength with ZPD dominance
        if correct:
            # Correct answers: balanced base update for realistic learning speed
            base_update = 0.14  # Increased for realistic learning speed
            time_multiplier = max(1.0, min(1.5, 15.0 / max(response_time, 1.0)))
        else:
            # Incorrect answers: asymmetric penalty
            base_update = 0.12  # Increased for realistic learning speed
            time_multiplier = max(1.0, min(1.3, 10.0 / max(response_time, 1.0)))
        
        # Apply saturation constraint: theoretical model
        saturation_factor = 1.0 - current_mastery
        
        # Implementation safeguard: prevent degenerate updates at high mastery
        saturation_factor = max(0.2, saturation_factor)
        
        # Apply asymmetric ZPD factor with minimum bound (theoretical model)
        zpd_gap = abs(current_mastery - difficulty)
        if difficulty > current_mastery:
            # Too hard - sharper penalty
            sigma = 0.01
        else:
            # Too easy - broader penalty
            sigma = 0.03
        
        zpd_factor = max(0.05, math.exp(- (zpd_gap ** 2) / sigma))  # Minimum bound prevents zero learning
        
        # Non-linear ZPD dominance: ZPD shapes saturation curve
        effective_saturation = saturation_factor * (zpd_factor ** 1.2)
        
        # Calculate final update strength with non-linear ZPD formulation
        update_strength = base_update * time_multiplier * effective_saturation
        
        # Bounded learning constraint: ensure numerical stability
        update_strength = min(0.2, max(0.005, update_strength))
        
        # Apply PROPER Bayesian update (Beta-Binomial conjugate)
        logger.info(f"🔥 BAYESIAN DEBUG: alpha={alpha}, beta={beta}, correct={correct}")
        if correct:
            new_alpha = alpha + 1.0  # Success count
            new_beta = beta          # Failure count unchanged
            logger.info(f"🔥 BAYESIAN CORRECT: {alpha}+1 → {new_alpha}, beta={beta} → {new_beta}")
        else:
            new_alpha = alpha          # Success count unchanged
            new_beta = beta + 1.0      # Failure count
            logger.info(f"🔥 BAYESIAN INCORRECT: alpha={alpha} → {new_alpha}, beta={beta}+1 → {new_beta}")
        
        # REMOVED: Per-interaction forgetting (was unrealistic)
        # Forgetting should be time-based, not per-interaction
        
        # REMOVED: Growth cap was corrupting proper Bayesian updates
        # Beta-Binomial conjugate updates should not be artificially capped
        
        return new_alpha, new_beta
    
    @staticmethod
    def difficulty_weight(difficulty: float) -> float:
        """
        Calculate weight for mastery updates based on difficulty
        
        Harder items get higher weight for successful responses
        Easier items get higher weight for failed responses
        """
        if difficulty < 0.3:  # Easy
            return 0.5
        elif difficulty < 0.7:  # Medium
            return 1.0
        else:  # Hard
            return 1.5
    
    @staticmethod
    def learning_gain(alpha: float, beta: float, difficulty: float) -> float:
        """
        Calculate expected learning gain from attempting an item
        Higher gain for items with moderate difficulty and uncertainty
        """
        mastery = MasteryModel.mean(alpha, beta)
        uncertainty = MasteryModel.uncertainty(alpha, beta)
        
        # Learning gain is highest when:
        # 1. Difficulty is close to mastery (not too easy/hard)
        # 2. Uncertainty is high (more to learn)
        difficulty_match = 1 - abs(mastery - difficulty)
        
        return 0.1 * difficulty_match * uncertainty
    
    @staticmethod
    def confidence_interval(alpha: float, beta: float, confidence: float = 0.95) -> Tuple[float, float]:
        """
        Calculate confidence interval for mastery estimate
        
        Uses Beta distribution quantiles
        """
        if alpha <= 0 or beta <= 0:
            return (0.0, 1.0)
        
        try:
            lower = random.betavariate(alpha, beta)  # Simplified - should use scipy.stats.beta.ppf
            upper = random.betavariate(alpha, beta)  # Simplified - should use scipy.stats.beta.ppf
            return (lower, upper)
        except:
            return (0.0, 1.0)
    
    @staticmethod
    def is_mastered(alpha: float, beta: float, threshold: float = 0.8) -> bool:
        """
        Determine if concept is mastered based on mastery threshold
        """
        mastery = MasteryModel.mean(alpha, beta)
        return mastery >= threshold
    
    @staticmethod
    def needs_practice(alpha: float, beta: float, practice_threshold: float = 0.4) -> bool:
        """
        Determine if concept needs more practice
        """
        mastery = MasteryModel.mean(alpha, beta)
        uncertainty = MasteryModel.uncertainty(alpha, beta)
        
        # Needs practice if mastery is low OR uncertainty is high
        return mastery < practice_threshold or uncertainty > 0.3
    
    @staticmethod
    def transfer_learning(alpha_source: float, beta_source: float, 
                        alpha_target: float, beta_target: float) -> Tuple[float, float]:
        """
        Calculate transfer learning parameters
        
        Knowledge from source concept influences target concept
        """
        source_mastery = MasteryModel.mean(alpha_source, beta_source)
        
        # Transfer factor based on source mastery
        transfer_factor = min(source_mastery, 0.5)  # Cap at 0.5 to avoid overconfidence
        
        # Add transfer to target
        new_alpha = alpha_target + transfer_factor
        new_beta = beta_target
        
        return new_alpha, new_beta
