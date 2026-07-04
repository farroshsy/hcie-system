"""
UX Semantics - Pedagogical Projection Layer

C1.1.4 - Projection UX Semantics Transition

Transforms cognition internals into pedagogical semantics for frontend consumption.

Architectural Principle:
- Frontend should expose pedagogy semantics, NOT cognition implementation internals
- Cognition internals (mastery, uncertainty, bayesian_alpha, kalman_covariance, lyapunov_mastery)
  are backend implementation details
- UX semantics (readiness, confidence stability, challenge suitability, pacing responsiveness)
  are pedagogically meaningful to learners

This transformation layer bridges the gap between:
- Internal cognitive models (research-grade, precise, implementation-specific)
- External UX semantics (learner-facing, pedagogical, interpretable)
"""

from dataclasses import dataclass

from .ux_semantics import (
    ReadinessLevel,
    ConfidenceStability,
    ChallengeSuitability,
    PacingResponsiveness,
    CognitiveStability,
    TransferReadiness,
)

"""Extracted from `HCIE_SYSTEM_BACKENDV2/core/projection/ux_semantics.py` by tools/migrate/split_session_and_ux.py.

Symbols: UXSemantics, UXSemanticsTransformer.
"""

@dataclass
class UXSemantics:
    """
    Pedagogical UX semantics derived from cognition internals.
    
    These are frontend-native learner semantics, not cognition implementation internals.
    """
    # Core UX Semantics
    readiness: ReadinessLevel
    confidence_stability: ConfidenceStability
    challenge_suitability: ChallengeSuitability
    pacing_responsiveness: PacingResponsiveness
    cognitive_stability: CognitiveStability
    transfer_readiness: TransferReadiness
    
    # Semantic Guidance (NOT metrics)
    learning_momentum: str  # "building", "maintaining", "declining"
    uncertainty_band: str  # "narrow", "moderate", "wide"
    next_concept_guidance: str  # "continue", "review", "advance"
    
    # Pedagogical Narrative (NOT numerical summaries)
    pedagogical_state: str  # Human-readable state description
    recommended_action: str  # Human-readable action recommendation

class UXSemanticsTransformer:
    """
    Transforms cognition internals into UX semantics.
    
    This is the bridge between:
    - Research-grade cognitive models (precise, implementation-specific)
    - Learner-facing pedagogical semantics (interpretable, actionable)
    """
    
    @staticmethod
    def compute_readiness(mastery: float, zpd_score: float) -> ReadinessLevel:
        """
        Compute readiness level from mastery and ZPD score.
        
        Pedagogical interpretation:
        - mastery < 0.5: Not ready for next concept
        - mastery 0.5-0.7: Approaching readiness
        - mastery 0.7-0.9: Ready for next concept
        - mastery > 0.9: Mastery achieved
        """
        if mastery < 0.5:
            return ReadinessLevel.NOT_READY
        elif mastery < 0.7:
            return ReadinessLevel.APPROACHING
        elif mastery < 0.9:
            return ReadinessLevel.READY
        else:
            return ReadinessLevel.MASTERY
    
    @staticmethod
    def compute_confidence_stability(uncertainty: float, kalman_covariance: float) -> ConfidenceStability:
        """
        Compute confidence stability from uncertainty and Kalman covariance.
        
        Pedagogical interpretation:
        - High uncertainty or high covariance: Unstable confidence
        - Moderate uncertainty/covariance: Stabilizing
        - Low uncertainty/covariance: Stable confidence
        """
        combined_instability = uncertainty + kalman_covariance
        if combined_instability > 0.5:
            return ConfidenceStability.UNSTABLE
        elif combined_instability > 0.3:
            return ConfidenceStability.STABILIZING
        else:
            return ConfidenceStability.STABLE
    
    @staticmethod
    def compute_challenge_suitability(zpd_score: float, current_mastery: float) -> ChallengeSuitability:
        """
        Compute challenge suitability from ZPD score and current mastery.
        
        Pedagogical interpretation:
        - ZPD score too high relative to mastery: Too hard
        - ZPD score appropriate: Appropriate challenge
        - ZPD score too low relative to mastery: Too easy
        """
        zpd_gap = zpd_score - current_mastery
        if zpd_gap > 0.3:
            return ChallengeSuitability.TOO_HARD
        elif zpd_gap < -0.2:
            return ChallengeSuitability.TOO_EASY
        else:
            return ChallengeSuitability.APPROPRIATE
    
    @staticmethod
    def compute_pacing_responsiveness(adaptive_rate: float, streak_length: int) -> PacingResponsiveness:
        """
        Compute pacing responsiveness from adaptive rate and streak length.
        
        Pedagogical interpretation:
        - High adaptive rate with low streak: Too fast
        - Moderate adaptive rate with good streak: Well-paced
        - Low adaptive rate with high streak: Too slow
        """
        if adaptive_rate > 0.8 and streak_length < 3:
            return PacingResponsiveness.TOO_FAST
        elif adaptive_rate < 0.3 and streak_length > 5:
            return PacingResponsiveness.TOO_SLOW
        else:
            return PacingResponsiveness.WELL_PACED
    
    @staticmethod
    def compute_cognitive_stability(lyapunov_mastery: float, recent_mastery_variance: float) -> CognitiveStability:
        """
        Compute cognitive stability from Lyapunov mastery and recent variance.
        
        Pedagogical interpretation:
        - High Lyapunov or high variance: Fluctuating
        - Moderate Lyapunov/variance: Converging
        - Low Lyapunov/variance: Stable
        """
        combined_instability = lyapunov_mastery + recent_mastery_variance
        if combined_instability > 0.4:
            return CognitiveStability.FLUCTUATING
        elif combined_instability > 0.2:
            return CognitiveStability.CONVERGING
        else:
            return CognitiveStability.STABLE
    
    @staticmethod
    def compute_transfer_readiness(mastery: float, transfer_amounts: dict) -> TransferReadiness:
        """
        Compute transfer readiness from mastery and transfer amounts.
        
        Pedagogical interpretation:
        - High mastery with high transfer amounts: High transfer readiness
        - Moderate mastery with moderate transfer: Moderate transfer readiness
        - Low mastery or low transfer: Low transfer readiness
        """
        avg_transfer = sum(transfer_amounts.values()) / len(transfer_amounts) if transfer_amounts else 0
        combined_readiness = (mastery + avg_transfer) / 2
        
        if combined_readiness > 0.8:
            return TransferReadiness.HIGH
        elif combined_readiness > 0.5:
            return TransferReadiness.MODERATE
        else:
            return TransferReadiness.LOW
    
    @staticmethod
    def compute_learning_momentum(recent_correctness: float, streak_trend: str) -> str:
        """
        Compute learning momentum from recent correctness and streak trend.
        
        Pedagogical interpretation:
        - High correctness with positive trend: Building momentum
        - Stable correctness: Maintaining momentum
        - Low correctness with negative trend: Declining momentum
        """
        if recent_correctness > 0.7 and streak_trend == "increasing":
            return "building"
        elif recent_correctness > 0.6:
            return "maintaining"
        else:
            return "declining"
    
    @staticmethod
    def compute_uncertainty_band(uncertainty: float, confidence: float) -> str:
        """
        Compute uncertainty band from uncertainty and confidence.
        
        Pedagogical interpretation:
        - Low uncertainty, high confidence: Narrow band (certain)
        - Moderate uncertainty/confidence: Moderate band
        - High uncertainty, low confidence: Wide band (uncertain)
        """
        combined_uncertainty = uncertainty + (1 - confidence)
        if combined_uncertainty < 0.3:
            return "narrow"
        elif combined_uncertainty < 0.6:
            return "moderate"
        else:
            return "wide"
    
    @staticmethod
    def compute_next_concept_guidance(
        readiness: ReadinessLevel,
        challenge_suitability: ChallengeSuitability
    ) -> str:
        """
        Compute next concept guidance from readiness and challenge suitability.
        
        Pedagogical interpretation:
        - Ready with appropriate challenge: Continue
        - Not ready or too hard: Review
        - Mastery achieved: Advance
        """
        if readiness == ReadinessLevel.MASTERY:
            return "advance"
        elif readiness == ReadinessLevel.NOT_READY or challenge_suitability == ChallengeSuitability.TOO_HARD:
            return "review"
        else:
            return "continue"
    
    @staticmethod
    def generate_pedagogical_state(
        readiness: ReadinessLevel,
        confidence_stability: ConfidenceStability,
        challenge_suitability: ChallengeSuitability
    ) -> str:
        """
        Generate human-readable pedagogical state.
        
        This is the pedagogical narrative, NOT a metric summary.
        """
        states = {
            (ReadinessLevel.NOT_READY, ConfidenceStability.UNSTABLE, ChallengeSuitability.TOO_HARD):
                "Building foundational understanding - needs more practice",
            (ReadinessLevel.APPROACHING, ConfidenceStability.STABILIZING, ChallengeSuitability.APPROPRIATE):
                "Developing competence - on right track",
            (ReadinessLevel.READY, ConfidenceStability.STABLE, ChallengeSuitability.APPROPRIATE):
                "Ready for next challenge - confident understanding",
            (ReadinessLevel.MASTERY, ConfidenceStability.STABLE, ChallengeSuitability.TOO_EASY):
                "Mastered concept - ready to advance",
        }
        return states.get(
            (readiness, confidence_stability, challenge_suitability),
            "Continuing learning journey"
        )
    
    @staticmethod
    def generate_recommended_action(
        readiness: ReadinessLevel,
        challenge_suitability: ChallengeSuitability,
        pacing_responsiveness: PacingResponsiveness
    ) -> str:
        """
        Generate human-readable action recommendation.
        
        This is pedagogical guidance, NOT automated decision making.
        """
        if challenge_suitability == ChallengeSuitability.TOO_HARD:
            return "Try easier problems to build confidence"
        elif challenge_suitability == ChallengeSuitability.TOO_EASY:
            return "Ready for more challenging problems"
        elif pacing_responsiveness == PacingResponsiveness.TOO_FAST:
            return "Take time to understand each step"
        elif pacing_responsiveness == PacingResponsiveness.TOO_SLOW:
            return "Increase pace to maintain engagement"
        elif readiness == ReadinessLevel.NOT_READY:
            return "Review fundamentals before advancing"
        else:
            return "Continue with current learning path"
    
    @classmethod
    def transform(cls, cognition_state: dict) -> UXSemantics:
        """
        Transform cognition state into UX semantics.
        
        Args:
            cognition_state: Dictionary containing cognition internals
                - mastery: float
                - uncertainty: float
                - confidence: float
                - bayesian_alpha: float
                - bayesian_beta: float
                - kalman_mastery: float
                - kalman_covariance: float
                - lyapunov_mastery: float
                - zpd_score: float
                - zpd_target: float
                - J_value: float
                - adaptive_rate: float
                - transfer_amounts: dict
                - streak_length: int
                - recent_correctness: float
                - streak_trend: str
                - recent_mastery_variance: float
        
        Returns:
            UXSemantics: Pedagogical UX semantics for frontend consumption
        """
        # Extract cognition internals
        mastery = cognition_state.get('mastery', 0.5)
        uncertainty = cognition_state.get('uncertainty', 0.5)
        confidence = cognition_state.get('confidence', 0.5)
        kalman_mastery = cognition_state.get('kalman_mastery', 0.5)
        kalman_covariance = cognition_state.get('kalman_covariance', 0.5)
        lyapunov_mastery = cognition_state.get('lyapunov_mastery', 0.5)
        zpd_score = cognition_state.get('zpd_score', 0.5)
        adaptive_rate = cognition_state.get('adaptive_rate', 0.5)
        transfer_amounts = cognition_state.get('transfer_amounts', {})
        streak_length = cognition_state.get('streak_length', 0)
        recent_correctness = cognition_state.get('recent_correctness', 0.5)
        streak_trend = cognition_state.get('streak_trend', 'stable')
        recent_mastery_variance = cognition_state.get('recent_mastery_variance', 0.5)
        
        # Compute UX semantics
        readiness = cls.compute_readiness(mastery, zpd_score)
        confidence_stability = cls.compute_confidence_stability(uncertainty, kalman_covariance)
        challenge_suitability = cls.compute_challenge_suitability(zpd_score, mastery)
        pacing_responsiveness = cls.compute_pacing_responsiveness(adaptive_rate, streak_length)
        cognitive_stability = cls.compute_cognitive_stability(lyapunov_mastery, recent_mastery_variance)
        transfer_readiness = cls.compute_transfer_readiness(mastery, transfer_amounts)
        learning_momentum = cls.compute_learning_momentum(recent_correctness, streak_trend)
        uncertainty_band = cls.compute_uncertainty_band(uncertainty, confidence)
        next_concept_guidance = cls.compute_next_concept_guidance(readiness, challenge_suitability)
        pedagogical_state = cls.generate_pedagogical_state(readiness, confidence_stability, challenge_suitability)
        recommended_action = cls.generate_recommended_action(readiness, challenge_suitability, pacing_responsiveness)
        
        return UXSemantics(
            readiness=readiness,
            confidence_stability=confidence_stability,
            challenge_suitability=challenge_suitability,
            pacing_responsiveness=pacing_responsiveness,
            cognitive_stability=cognitive_stability,
            transfer_readiness=transfer_readiness,
            learning_momentum=learning_momentum,
            uncertainty_band=uncertainty_band,
            next_concept_guidance=next_concept_guidance,
            pedagogical_state=pedagogical_state,
            recommended_action=recommended_action
        )


# --- traceability ---------------------------------------------------------
__sliced_from__ = 'HCIE_SYSTEM_BACKENDV2/core/projection/ux_semantics.py'
__symbol_ranges__ = {
    'UXSemantics': (68, 91),
    'UXSemanticsTransformer': (93, 387),
}
