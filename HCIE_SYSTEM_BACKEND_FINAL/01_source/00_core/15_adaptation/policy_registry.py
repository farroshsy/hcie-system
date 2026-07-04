"""
Adaptation Policy Registry
Version-frozen policy registry for deterministic adaptation derivation
"""

from typing import Dict, Any
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class AdaptationPolicy(ABC):
    """
    Abstract base class for adaptation policies
    
    Policies MUST be:
    - Deterministic (same inputs → same outputs)
    - Self-contained (no external dependencies)
    - Versioned (explicit version tracking)
    - Pure functions (no side effects)
    """
    
    def __init__(self, version: str):
        self.version = version
    
    @abstractmethod
    def classify_adaptation_type(
        self, 
        cognition_snapshot: Dict[str, Any]
    ) -> str:
        """
        Classify adaptation type based on cognition state
        
        Returns one of:
        - remediation
        - pacing_adjustment
        - difficulty_shift
        - transfer_opportunity
        - prerequisite_review
        - confidence_support
        - milestone_acknowledgement
        """
        pass
    
    @abstractmethod
    def derive_recommendation(
        self,
        cognition_snapshot: Dict[str, Any],
        adaptation_type: str
    ) -> Dict[str, Any]:
        """
        Derive pedagogical recommendation
        
        Returns:
        - suggested_tasks: list of task IDs
        - pacing_adjustment: optional pacing suggestion
        - difficulty_shift: optional difficulty suggestion
        - intervention_hints: list of intervention suggestions
        - confidence_score: optional adaptation confidence (0-1)
        """
        pass
    
    @abstractmethod
    def get_policy_inputs_schema_version(self) -> str:
        """
        Get the schema version of cognition inputs this policy expects
        Separate from event schema version for future-proofing
        """
        pass


class DeterministicPolicyV1(AdaptationPolicy):
    """
    Deterministic adaptation policy v1.0.0
    
    Phase 1: Simple threshold-based adaptation
    - Remediation: mastery < 0.3 and uncertainty > 0.5
    - Pacing adjustment: zpd_score indicates pacing needs
    - Difficulty shift: mastery indicates difficulty adjustment
    - Transfer opportunity: high mastery in prerequisite
    - Prerequisite review: struggling on advanced concept
    - Confidence support: high uncertainty despite correct answers
    - Milestone acknowledgement: mastery > 0.8 threshold
    """
    
    def __init__(self):
        super().__init__("v1.0.0")
        self.policy_inputs_schema_version = "1.0.0"
    
    def classify_adaptation_type(
        self, 
        cognition_snapshot: Dict[str, Any]
    ) -> str:
        """
        Classify adaptation type using deterministic threshold logic
        """
        mastery = cognition_snapshot.get('mastery', 0.0)
        uncertainty = cognition_snapshot.get('uncertainty', 1.0)
        zpd_score = cognition_snapshot.get('zpd_score', 0.0)
        
        # Priority order of adaptation types
        # Milestone acknowledgement (highest priority)
        if mastery >= 0.8:
            return "milestone_acknowledgement"
        
        # Remediation (struggling learner)
        if mastery < 0.3 and uncertainty > 0.5:
            return "remediation"
        
        # Confidence support (uncertain but performing)
        if mastery >= 0.5 and uncertainty > 0.6:
            return "confidence_support"
        
        # Difficulty shift (adjust challenge level)
        if mastery < 0.5:
            return "difficulty_shift"
        
        # Pacing adjustment (based on zpd)
        if zpd_score < 0.3 or zpd_score > 0.7:
            return "pacing_adjustment"
        
        # Default: no adaptation needed
        return "pacing_adjustment"  # Neutral default
    
    def derive_recommendation(
        self,
        cognition_snapshot: Dict[str, Any],
        adaptation_type: str
    ) -> Dict[str, Any]:
        """
        Derive pedagogical recommendation based on adaptation type
        
        Deterministic logic: same cognition + same type = same recommendation
        """
        mastery = cognition_snapshot.get('mastery', 0.0)
        uncertainty = cognition_snapshot.get('uncertainty', 1.0)
        
        recommendation = {
            "suggested_tasks": [],
            "pacing_adjustment": None,
            "difficulty_shift": None,
            "intervention_hints": [],
            "confidence_score": None
        }
        
        if adaptation_type == "remediation":
            recommendation["intervention_hints"] = [
                "Review prerequisite concepts",
                "Provide step-by-step guidance",
                "Offer additional practice opportunities"
            ]
            recommendation["difficulty_shift"] = "decrease"
            recommendation["confidence_score"] = 0.9
        
        elif adaptation_type == "pacing_adjustment":
            zpd_score = cognition_snapshot.get('zpd_score', 0.0)
            if zpd_score < 0.3:
                recommendation["pacing_adjustment"] = "slow_down"
                recommendation["intervention_hints"] = [
                    "Reduce task frequency",
                    "Provide more reflection time"
                ]
            elif zpd_score > 0.7:
                recommendation["pacing_adjustment"] = "speed_up"
                recommendation["intervention_hints"] = [
                    "Increase task frequency",
                    "Introduce more challenging content"
                ]
            recommendation["confidence_score"] = 0.8
        
        elif adaptation_type == "difficulty_shift":
            if mastery < 0.3:
                recommendation["difficulty_shift"] = "decrease"
                recommendation["intervention_hints"] = [
                    "Provide simpler tasks",
                    "Break down complex problems"
                ]
            elif mastery < 0.5:
                recommendation["difficulty_shift"] = "maintain"
                recommendation["intervention_hints"] = [
                    "Continue at current difficulty",
                    "Monitor progress closely"
                ]
            recommendation["confidence_score"] = 0.85
        
        elif adaptation_type == "confidence_support":
            recommendation["intervention_hints"] = [
                "Provide positive reinforcement",
                "Show progress visualization",
                "Offer confidence-building feedback"
            ]
            recommendation["confidence_score"] = 0.75
        
        elif adaptation_type == "milestone_acknowledgement":
            recommendation["intervention_hints"] = [
                "Celebrate achievement",
                "Unlock next level",
                "Provide milestone badge"
            ]
            recommendation["confidence_score"] = 0.95
        
        return recommendation
    
    def get_policy_inputs_schema_version(self) -> str:
        return self.policy_inputs_schema_version


class AdaptationPolicyRegistry:
    """
    Version-frozen adaptation policy registry
    
    Policies are registered at startup and cannot be mutated at runtime.
    This prevents policy drift during replay and ensures deterministic behavior.
    """
    
    # Version-frozen policy registry
    POLICY_REGISTRY: Dict[str, AdaptationPolicy] = {
        "v1.0.0": DeterministicPolicyV1(),
    }
    
    @staticmethod
    def get_policy(version: str) -> AdaptationPolicy:
        """
        Get policy by version
        
        Raises ValueError if version not found
        """
        if version not in AdaptationPolicyRegistry.POLICY_REGISTRY:
            raise ValueError(
                f"Policy version {version} not found. "
                f"Available versions: {list(AdaptationPolicyRegistry.POLICY_REGISTRY.keys())}"
            )
        return AdaptationPolicyRegistry.POLICY_REGISTRY[version]
    
    @staticmethod
    def get_active_policy() -> AdaptationPolicy:
        """
        Get the currently active policy version
        
        For Phase 1, this is always v1.0.0
        """
        return AdaptationPolicyRegistry.get_policy("v1.0.0")
    
    @staticmethod
    def list_available_versions() -> list:
        """
        List all available policy versions
        """
        return list(AdaptationPolicyRegistry.POLICY_REGISTRY.keys())
    
    @staticmethod
    def is_version_available(version: str) -> bool:
        """
        Check if a policy version is available
        """
        return version in AdaptationPolicyRegistry.POLICY_REGISTRY
    
    # ⚠️ Runtime policy registration is DISABLED
    # Policies must be version-controlled in code, not dynamically loaded
    # This prevents policy drift during replay and ensures deterministic behavior
    
    @staticmethod
    def _register_policy(version: str, policy: AdaptationPolicy) -> None:
        """
        Internal policy registration for initialization only
        
        This method is intentionally private to prevent runtime mutation.
        Policy versions must be added via code changes, not runtime loading.
        """
        AdaptationPolicyRegistry.POLICY_REGISTRY[version] = policy
        logger.info(f"✅ Registered policy version {version}")
