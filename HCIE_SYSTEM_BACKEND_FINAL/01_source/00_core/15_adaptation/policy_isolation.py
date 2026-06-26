"""
Policy Version Isolation - Runtime Ontology Separation Layer

This module provides the first true runtime ontology separation layer in the pedagogical engine.
Each policy version is an isolated executable pedagogy with its own:
- Adaptation parameters
- Thresholds
- Remediation semantics
- Pacing logic
- Recommendation transforms
- UX semantics transforms

This is NOT configuration. This is isolated pedagogical runtime.
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


# ============================================================================
# Immutable Semantic Objects (Version-Safe for Replay Science)
# ============================================================================

@dataclass(frozen=True)
class PacingDecision:
    """Immutable pacing decision for version-safe replay semantics"""
    should_advance: bool
    session_length: int
    policy_version: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RemediationDecision:
    """Immutable remediation decision for version-safe replay semantics"""
    should_remediate: bool
    remediation_type: str
    target_concepts: list
    policy_version: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DifficultyDecision:
    """Immutable difficulty decision for version-safe replay semantics"""
    difficulty_adjustment: float
    should_increase: bool
    policy_version: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class UXSemanticProjection:
    """Immutable UX semantic projection for version-safe replay semantics"""
    readiness: str
    confidence_stability: str
    challenge_suitability: str
    pacing_responsiveness: str
    cognitive_stability: str
    transfer_readiness: str
    learning_momentum: str
    uncertainty_band: str
    next_concept_guidance: str
    pedagogical_state: str
    recommended_action: str
    policy_version: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ============================================================================
# Strategy Protocols (Base Classes)
# ============================================================================

class PacingStrategy:
    """
    Base class for policy-specific pacing strategy.
    
    Defines how the policy controls task sequencing, session length,
    and learning velocity.
    """
    
    def should_advance_to_next_concept(
        self,
        mastery: float,
        uncertainty: float,
        tasks_completed: int
    ) -> bool:
        """Determine if learner should advance to next concept"""
        raise NotImplementedError
    
    def calculate_session_length(
        self,
        learner_engagement: float,
        difficulty_level: float
    ) -> int:
        """Calculate optimal session length in tasks"""
        raise NotImplementedError


class RemediationStrategy:
    """
    Base class for policy-specific remediation strategy.
    
    Defines how the policy responds to errors, misconceptions,
    and learning difficulties.
    """
    
    def should_trigger_remediation(
        self,
        recent_errors: int,
        mastery: float,
        misconception_severity: float
    ) -> bool:
        """Determine if remediation intervention is needed"""
        raise NotImplementedError
    
    def select_remediation_type(
        self,
        error_pattern: str,
        mastery_level: float
    ) -> str:
        """Select remediation type (e.g., 'explanation', 'scaffold', 'retry')"""
        raise NotImplementedError


class DifficultyStrategy:
    """
    Base class for policy-specific difficulty modulation strategy.
    
    Defines how the policy adjusts task difficulty based on
        learner performance.
    """
    
    def calculate_difficulty_adjustment(
        self,
        current_difficulty: float,
        recent_correctness: float,
        mastery_velocity: float
    ) -> float:
        """Calculate difficulty adjustment factor"""
        raise NotImplementedError
    
    def should_increase_difficulty(
        self,
        mastery: float,
        recent_performance: float
    ) -> bool:
        """Determine if difficulty should increase"""
        raise NotImplementedError


class UXTransformer:
    """
    Base class for policy-specific UX semantics transformation.
    
    Defines how the policy transforms cognition internals into
    learner-facing pedagogical semantics.
    """
    
    def transform_readiness(
        self,
        mastery: float,
        uncertainty: float,
        zpd_score: float
    ) -> str:
        """Transform readiness state into pedagogical label"""
        raise NotImplementedError
    
    def transform_confidence_stability(
        self,
        uncertainty: float,
        bayesian_alpha: float,
        bayesian_beta: float
    ) -> str:
        """Transform confidence stability into pedagogical label"""
        raise NotImplementedError


# ============================================================================
# Concrete Policy Strategy Implementations
# ============================================================================

class DefaultPacingStrategy:
    """Default pacing strategy for v1.0.0 baseline policy"""
    
    def should_advance_to_next_concept(
        self,
        mastery: float,
        uncertainty: float,
        tasks_completed: int
    ) -> bool:
        """Advance when mastery >= 0.75 and tasks_completed >= 5"""
        return mastery >= 0.75 and tasks_completed >= 5
    
    def calculate_session_length(
        self,
        learner_engagement: float,
        difficulty_level: float
    ) -> int:
        """Session length between 5-15 tasks based on engagement"""
        base_length = 10
        engagement_adjustment = int(learner_engagement * 5)
        difficulty_adjustment = int(difficulty_level * 3)
        return max(5, min(15, base_length + engagement_adjustment - difficulty_adjustment))


class DefaultRemediationStrategy:
    """Default remediation strategy for v1.0.0 baseline policy"""
    
    def should_trigger_remediation(
        self,
        recent_errors: int,
        mastery: float,
        misconception_severity: float
    ) -> bool:
        """Trigger remediation after 3 consecutive errors or high misconception severity"""
        return recent_errors >= 3 or misconception_severity > 0.7
    
    def select_remediation_type(
        self,
        error_pattern: str,
        mastery_level: float
    ) -> str:
        """Select remediation based on mastery level"""
        if mastery_level < 0.3:
            return "scaffold"
        elif mastery_level < 0.6:
            return "explanation"
        else:
            return "retry"


class DefaultDifficultyStrategy:
    """Default difficulty modulation strategy for v1.0.0 baseline policy"""
    
    def calculate_difficulty_adjustment(
        self,
        current_difficulty: float,
        recent_correctness: float,
        mastery_velocity: float
    ) -> float:
        """Adjust difficulty based on recent performance"""
        if recent_correctness > 0.8:
            return 0.1  # Increase difficulty
        elif recent_correctness < 0.5:
            return -0.1  # Decrease difficulty
        return 0.0  # Maintain difficulty
    
    def should_increase_difficulty(
        self,
        mastery: float,
        recent_performance: float
    ) -> bool:
        """Increase difficulty when mastery > 0.7 and performance > 0.8"""
        return mastery > 0.7 and recent_performance > 0.8


class DefaultUXTransformer:
    """Default UX semantics transformer for v1.0.0 baseline policy"""
    
    def transform_readiness(
        self,
        mastery: float,
        uncertainty: float,
        zpd_score: float
    ) -> str:
        """Transform readiness into pedagogical label"""
        if mastery > 0.8 and uncertainty < 0.2:
            return "ready_to_advance"
        elif mastery > 0.6 and uncertainty < 0.4:
            return "developing"
        elif mastery > 0.4:
            return "needs_practice"
        else:
            return "needs_support"
    
    def transform_confidence_stability(
        self,
        uncertainty: float,
        bayesian_alpha: float,
        bayesian_beta: float
    ) -> str:
        """Transform confidence stability into pedagogical label"""
        if uncertainty < 0.2:
            return "very_stable"
        elif uncertainty < 0.4:
            return "stable"
        elif uncertainty < 0.6:
            return "developing"
        else:
            return "unstable"


class AggressivePacingStrategy:
    """Aggressive pacing strategy for experimental policy v1.1.0"""
    
    def should_advance_to_next_concept(
        self,
        mastery: float,
        uncertainty: float,
        tasks_completed: int
    ) -> bool:
        """Advance more aggressively: mastery >= 0.7 and tasks_completed >= 3"""
        return mastery >= 0.7 and tasks_completed >= 3
    
    def calculate_session_length(
        self,
        learner_engagement: float,
        difficulty_level: float
    ) -> int:
        """Longer sessions: 8-20 tasks"""
        base_length = 14
        engagement_adjustment = int(learner_engagement * 6)
        difficulty_adjustment = int(difficulty_level * 4)
        return max(8, min(20, base_length + engagement_adjustment - difficulty_adjustment))


class ConservativePacingStrategy:
    """Conservative pacing strategy for experimental policy v1.2.0"""
    
    def should_advance_to_next_concept(
        self,
        mastery: float,
        uncertainty: float,
        tasks_completed: int
    ) -> bool:
        """Advance more conservatively: mastery >= 0.85 and tasks_completed >= 8"""
        return mastery >= 0.85 and tasks_completed >= 8
    
    def calculate_session_length(
        self,
        learner_engagement: float,
        difficulty_level: float
    ) -> int:
        """Shorter sessions: 4-10 tasks"""
        base_length = 7
        engagement_adjustment = int(learner_engagement * 3)
        difficulty_adjustment = int(difficulty_level * 3)
        return max(4, min(10, base_length + engagement_adjustment - difficulty_adjustment))


# ============================================================================
# Policy Runtime Class
# ============================================================================

@dataclass
class PolicyRuntime:
    """
    Isolated pedagogical execution environment for a specific policy version.
    
    Each PolicyRuntime encapsulates all policy-specific logic:
    - Adaptation parameters
    - Thresholds
    - Remediation semantics
    - Pacing logic
    - Recommendation transforms
    - UX semantics transforms
    
    This ensures policy composition instead of policy branching logic.
    Each policy version behaves as a separate pedagogical universe.
    """
    
    policy_version: str
    pacing_strategy: PacingStrategy
    remediation_strategy: RemediationStrategy
    difficulty_strategy: DifficultyStrategy
    ux_transformer: UXTransformer
    
    # Policy-specific adaptation parameters (isolated config)
    adaptation_parameters: Dict[str, Any]
    
    # Policy-specific thresholds (isolated config)
    thresholds: Dict[str, float]
    
    def should_trigger_adaptation(
        self,
        cognition_snapshot: Dict[str, Any]
    ) -> bool:
        """
        Determine if adaptation should be triggered based on policy thresholds.
        
        Uses policy-specific thresholds for decision making.
        """
        mastery = cognition_snapshot.get("mastery", 0.0)
        uncertainty = cognition_snapshot.get("uncertainty", 1.0)
        zpd_score = cognition_snapshot.get("zpd_score", 0.0)
        
        # Policy-specific threshold check
        mastery_threshold = self.thresholds.get("mastery_adaptation_threshold", 0.6)
        uncertainty_threshold = self.thresholds.get("uncertainty_adaptation_threshold", 0.4)
        
        # Adaptation triggered when mastery crosses threshold or uncertainty is high
        return mastery < mastery_threshold or uncertainty > uncertainty_threshold
    
    def get_adaptation_parameters(
        self,
        cognition_snapshot: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get policy-specific adaptation parameters.
        
        Returns isolated configuration for this policy version.
        """
        return {
            **self.adaptation_parameters,
            "policy_version": self.policy_version
        }
    
    def transform_ux_semantics(
        self,
        cognition_snapshot: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Transform cognition internals into pedagogical UX semantics.
        
        Uses policy-specific UX transformer.
        """
        mastery = cognition_snapshot.get("mastery", 0.0)
        uncertainty = cognition_snapshot.get("uncertainty", 1.0)
        zpd_score = cognition_snapshot.get("zpd_score", 0.0)
        bayesian_alpha = cognition_snapshot.get("bayesian_alpha", 1.0)
        bayesian_beta = cognition_snapshot.get("bayesian_beta", 1.0)
        
        return {
            "readiness": self.ux_transformer.transform_readiness(mastery, uncertainty, zpd_score),
            "confidence_stability": self.ux_transformer.transform_confidence_stability(
                uncertainty, bayesian_alpha, bayesian_beta
            )
        }
    
    def calculate_pacing_decision(
        self,
        cognition_snapshot: Dict[str, Any],
        tasks_completed: int,
        learner_engagement: float
    ) -> Dict[str, Any]:
        """
        Calculate pacing decision using policy-specific pacing strategy.
        
        Returns decision about concept advancement and session length.
        """
        mastery = cognition_snapshot.get("mastery", 0.0)
        uncertainty = cognition_snapshot.get("uncertainty", 1.0)
        difficulty_level = cognition_snapshot.get("difficulty_level", 0.5)
        
        should_advance = self.pacing_strategy.should_advance_to_next_concept(
            mastery, uncertainty, tasks_completed
        )
        
        session_length = self.pacing_strategy.calculate_session_length(
            learner_engagement, difficulty_level
        )
        
        return {
            "should_advance": should_advance,
            "session_length": session_length,
            "policy_version": self.policy_version
        }
    
    def calculate_remediation_decision(
        self,
        recent_errors: int,
        error_pattern: str,
        cognition_snapshot: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate remediation decision using policy-specific remediation strategy.
        
        Returns decision about whether to trigger remediation and what type.
        """
        mastery = cognition_snapshot.get("mastery", 0.0)
        misconception_severity = cognition_snapshot.get("misconception_severity", 0.0)
        
        should_remediate = self.remediation_strategy.should_trigger_remediation(
            recent_errors, mastery, misconception_severity
        )
        
        remediation_type = None
        if should_remediate:
            remediation_type = self.remediation_strategy.select_remediation_type(
                error_pattern, mastery
            )
        
        return {
            "should_remediate": should_remediate,
            "remediation_type": remediation_type,
            "policy_version": self.policy_version
        }
    
    def calculate_difficulty_decision(
        self,
        current_difficulty: float,
        recent_correctness: float,
        cognition_snapshot: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate difficulty decision using policy-specific difficulty strategy.
        
        Returns decision about difficulty adjustment.
        """
        mastery = cognition_snapshot.get("mastery", 0.0)
        mastery_velocity = cognition_snapshot.get("mastery_velocity", 0.0)
        
        adjustment = self.difficulty_strategy.calculate_difficulty_adjustment(
            current_difficulty, recent_correctness, mastery_velocity
        )
        
        should_increase = self.difficulty_strategy.should_increase_difficulty(
            mastery, recent_correctness
        )
        
        return {
            "difficulty_adjustment": adjustment,
            "should_increase": should_increase,
            "policy_version": self.policy_version
        }


# ============================================================================
# Policy Runtime Registry
# ============================================================================

class PolicyRuntimeRegistry:
    """
    Registry for isolated policy runtime instances.
    
    Manages PolicyRuntime instances by policy version.
    Ensures each policy version has its own isolated pedagogical universe.
    """
    
    def __init__(self):
        self._runtimes: Dict[str, PolicyRuntime] = {}
        self._initialize_default_policies()
    
    def _initialize_default_policies(self):
        """Initialize default policy runtimes"""
        
        # v1.0.0 - Baseline policy with default strategies
        self.register_runtime(
            PolicyRuntime(
                policy_version="v1.0.0",
                pacing_strategy=DefaultPacingStrategy(),
                remediation_strategy=DefaultRemediationStrategy(),
                difficulty_strategy=DefaultDifficultyStrategy(),
                ux_transformer=DefaultUXTransformer(),
                adaptation_parameters={
                    "adaptation_sensitivity": 0.5,
                    "response_urgency": "normal",
                    "intervention_threshold": 0.6
                },
                thresholds={
                    "mastery_adaptation_threshold": 0.6,
                    "uncertainty_adaptation_threshold": 0.4,
                    "zpd_target_min": 0.3,
                    "zpd_target_max": 0.7
                }
            )
        )
        
        # v1.1.0 - Aggressive pacing experimental policy
        self.register_runtime(
            PolicyRuntime(
                policy_version="v1.1.0",
                pacing_strategy=AggressivePacingStrategy(),
                remediation_strategy=DefaultRemediationStrategy(),
                difficulty_strategy=DefaultDifficultyStrategy(),
                ux_transformer=DefaultUXTransformer(),
                adaptation_parameters={
                    "adaptation_sensitivity": 0.7,
                    "response_urgency": "high",
                    "intervention_threshold": 0.5
                },
                thresholds={
                    "mastery_adaptation_threshold": 0.5,
                    "uncertainty_adaptation_threshold": 0.5,
                    "zpd_target_min": 0.4,
                    "zpd_target_max": 0.8
                }
            )
        )
        
        # v1.2.0 - Conservative pacing experimental policy
        self.register_runtime(
            PolicyRuntime(
                policy_version="v1.2.0",
                pacing_strategy=ConservativePacingStrategy(),
                remediation_strategy=DefaultRemediationStrategy(),
                difficulty_strategy=DefaultDifficultyStrategy(),
                ux_transformer=DefaultUXTransformer(),
                adaptation_parameters={
                    "adaptation_sensitivity": 0.3,
                    "response_urgency": "low",
                    "intervention_threshold": 0.7
                },
                thresholds={
                    "mastery_adaptation_threshold": 0.7,
                    "uncertainty_adaptation_threshold": 0.3,
                    "zpd_target_min": 0.2,
                    "zpd_target_max": 0.6
                }
            )
        )
        
        logger.info(f"Initialized {len(self._runtimes)} policy runtimes")
    
    def register_runtime(self, runtime: PolicyRuntime) -> None:
        """Register a new policy runtime"""
        self._runtimes[runtime.policy_version] = runtime
        logger.debug(f"Registered policy runtime: {runtime.policy_version}")
    
    def get_runtime(self, policy_version: str) -> Optional[PolicyRuntime]:
        """Get policy runtime by version"""
        return self._runtimes.get(policy_version)
    
    def list_versions(self) -> list[str]:
        """List all registered policy versions"""
        return list(self._runtimes.keys())
    
    def has_version(self, policy_version: str) -> bool:
        """Check if policy version is registered"""
        return policy_version in self._runtimes


# Global registry instance
_policy_runtime_registry = None


def get_policy_runtime_registry() -> PolicyRuntimeRegistry:
    """Get global policy runtime registry instance"""
    global _policy_runtime_registry
    if _policy_runtime_registry is None:
        _policy_runtime_registry = PolicyRuntimeRegistry()
    return _policy_runtime_registry
