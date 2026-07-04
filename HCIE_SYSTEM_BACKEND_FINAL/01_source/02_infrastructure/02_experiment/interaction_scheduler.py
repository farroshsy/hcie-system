"""
Interaction Scheduler for Experiment Infrastructure (Orchestration Layer Only)

ORCHESTRATION RESPONSIBILITIES (NOT Cognition):
- Order interactions (when to trigger)
- Inject experimental conditions (cohort assignment, timing, difficulty)
- Assign policies (policy name → configuration)
- Assign archetypes (learner archetype name → parameters)
- Route events to production runtime
- Collect results for analysis

COGNITION RESPONSIBILITIES (Runtime Layer):
- Concept selection (done by UnifiedBrain with policy configuration)
- Candidate filtering (done by UnifiedBrain with policy configuration)
- JT computation (done by UnifiedBrain with policy configuration)
- Thompson sampling/UCB (done by UnifiedBrain with policy configuration)
- All learning logic (done by UnifiedBrain)

This separation prevents semantic fragmentation and ensures production integrity.
"""

import random
import numpy as np
from typing import Dict, Any, Optional, List

from infrastructure.experiment.interaction_keys import normalize_interaction_for_brain
import logging

logger = logging.getLogger(__name__)


def sigmoid(x: float) -> float:
    """Sigmoid function for probability mapping"""
    return 1.0 / (1.0 + np.exp(-np.clip(x, -10, 10)))


def compute_correctness_probability(mastery: float, difficulty: float) -> float:
    """
    Compute probability of correct response based on mastery-difficulty relationship.
    
    This creates a true contextual bandit environment where:
    - Higher mastery → higher correctness probability
    - Higher difficulty → lower correctness probability
    - Actions (concept selection) affect outcomes through difficulty
    
    Args:
        mastery: Learner's mastery level [0, 1]
        difficulty: Concept difficulty [0, 1]
        
    Returns:
        Probability of correct response [0, 1]
    """
    # Log-odds model: p_correct = sigmoid(mastery - difficulty)
    # This creates proper action-reward coupling
    log_odds = mastery - difficulty
    p_correct = sigmoid(log_odds)
    return np.clip(p_correct, 0.05, 0.95)  # Prevent extreme probabilities

# Phase 2: Import synthetic behavioral priors (for interaction data simulation only)
try:
    from infrastructure.experiment.synthetic_behavioral_priors import SyntheticBehavioralPriors, PriorParameters
    SYNTHETIC_PRIORS_AVAILABLE = True
except ImportError:
    SYNTHETIC_PRIORS_AVAILABLE = False
    logger.warning("Synthetic behavioral priors not available, using fallback behavior")

# Phase 3: Import behavioral policies (as configuration for runtime layer)
try:
    from infrastructure.experiment.behavioral_policies import PolicyFactory, PolicyConfiguration
    BEHAVIORAL_POLICIES_AVAILABLE = True
except ImportError:
    BEHAVIORAL_POLICIES_AVAILABLE = False
    logger.warning("Behavioral policies not available, using fallback implementations")


class InteractionScheduler:
    """
    ORCHESTRATION LAYER ONLY - Does NOT implement cognition logic
    
    RESPONSIBILITIES:
    - Order interactions (timing, sequencing)
    - Inject experimental conditions (policy assignment, archetype assignment)
    - Route events to runtime layer (UnifiedBrain)
    - Generate interaction data for simulation (correctness, response time)
    
    NOT RESPONSIBILITIES:
    - Concept selection (done by UnifiedBrain)
    - Candidate filtering (done by UnifiedBrain)
    - Policy selection logic (done by UnifiedBrain with policy configuration)
    """
    
    def __init__(self, concepts: List[str], use_synthetic_priors: bool = True, use_behavioral_policies: bool = True):
        """
        Initialize interaction scheduler
        
        Args:
            concepts: List of available concepts
            use_synthetic_priors: Whether to use Phase 2 synthetic behavioral priors (for interaction data simulation only)
            use_behavioral_policies: Whether to use Phase 3 behavioral policy configurations (for runtime layer)
        """
        self.concepts = concepts
        self.use_synthetic_priors = use_synthetic_priors and SYNTHETIC_PRIORS_AVAILABLE
        self.use_behavioral_policies = use_behavioral_policies and BEHAVIORAL_POLICIES_AVAILABLE
        
        # Phase 2: Initialize synthetic behavioral priors (for interaction data simulation only)
        if self.use_synthetic_priors:
            self.synthetic_priors = SyntheticBehavioralPriors()
            logger.info("🔥 Phase 2: Using synthetic behavioral priors for interaction data simulation")
        else:
            logger.warning("Phase 2: Synthetic priors disabled, using fallback behavior")
        
        # Phase 3: Initialize behavioral policy configurations (for runtime layer, not orchestration)
        if self.use_behavioral_policies:
            self.policy_configs = {}
            for policy_name in PolicyFactory.get_all_policy_names():
                self.policy_configs[policy_name] = PolicyFactory.create_policy(policy_name, concepts)
            logger.info("🔥 Phase 3: Behavioral policy configurations loaded (will be passed to runtime layer)")
        else:
            logger.warning("Phase 3: Behavioral policies disabled, using fallback implementations")
            self.policy_configs = {}
        
        # Archetype handlers (for interaction data simulation only)
        self.archetype_handlers = {
            "novice": self._archetype_novice,
            "unstable": self._archetype_unstable,
            "transfer_heavy": self._archetype_transfer_heavy,
            "forgetting": self._archetype_forgetting,
            "exploration_sensitive": self._archetype_exploration_sensitive,
            "challenge_seeking": self._archetype_challenge_seeking
        }
    
    def schedule_next(
        self,
        user_id: str,
        config: Dict[str, Any],
        interaction_number: int,
        current_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        ORCHESTRATION ONLY: Schedule next interaction (concept selection done by runtime layer)
        
        Args:
            user_id: User identifier
            config: Experiment configuration (policy, archetype, timing conditions, etc.)
            interaction_number: Current interaction number
            current_state: Current learner state (if available)
            
        Returns:
            Scheduled interaction with policy configuration (concept selection deferred to runtime)
        """
        try:
            policy = config.get("policy", "hcie")
            archetype = config.get("learner_archetype", "novice")
            
            # Get policy configuration (will be passed to runtime layer)
            policy_config = None
            if self.use_behavioral_policies and policy in self.policy_configs:
                policy_config = self.policy_configs[policy]
            
            # ORCHESTRATION: Extract experimental conditions
            timing_condition = config.get("timing_condition", "normal")
            difficulty_condition = config.get("difficulty_condition", "normal")
            
            # ORCHESTRATION: Return orchestration data (concept selection deferred to runtime)
            scheduled = {
                "concept": None,  # Will be selected by UnifiedBrain with policy configuration
                "policy": policy,
                "policy_config": policy_config,  # Configuration for runtime layer
                "archetype": archetype,
                "timing_condition": timing_condition,
                "difficulty_condition": difficulty_condition,
                "interaction_number": interaction_number,
                "state_before": current_state or {}
            }
            
            return scheduled
            
        except Exception as e:
            logger.error(f"Failed to schedule interaction: {e}")
            raise
    
    def simulate_interaction_data(
        self,
        concept: str,
        archetype: str,
        interaction_number: int
    ) -> Dict[str, Any]:
        """
        SIMULATION ONLY: Generate interaction data (correctness, response time) based on archetype
        
        This is for experiment simulation only - production uses actual learner responses.
        
        Args:
            concept: Selected concept (by runtime layer)
            archetype: Learner archetype
            interaction_number: Current interaction number
            
        Returns:
            Interaction data (correctness, response time, etc.)
        """
        archetype_handler = self.archetype_handlers.get(archetype, self._archetype_novice)
        return normalize_interaction_for_brain(
            archetype_handler(concept=concept, interaction_number=interaction_number)
        )
    
    def _archetype_novice(self, concept: str, interaction_number: int) -> Dict[str, Any]:
        """
        Novice archetype: low correctness, slow response time
        Phase 2: Uses synthetic priors for ecological validity
        """
        if self.use_synthetic_priors:
            # Use synthetic priors with low initial mastery
            mastery = self.synthetic_priors.power_law_prior(0.1, interaction_number)
            response = self.synthetic_priors.generate_synthetic_response(
                mastery=mastery,
                difficulty=0.7,
                interaction_number=interaction_number,
                time_since_last_practice=1.0,
                spacing_interval=1.0
            )
            return {
                "correctness": response["correctness"],
                "response_time": response["response_time_ms"] / 1000.0,  # Convert to seconds
                "difficulty": 0.7,
                "mastery": mastery
            }
        else:
            # Fallback behavior: use proper reward function for true contextual bandit environment
            mastery = 0.1 + interaction_number * 0.01  # Slow learning for novice
            mastery = np.clip(mastery, 0.0, 1.0)
            difficulty = 0.7
            p_correct = compute_correctness_probability(mastery, difficulty)
            return {
                "correctness": random.random() < p_correct,
                "response_time": random.uniform(5.0, 15.0),
                "difficulty": difficulty,
                "mastery": mastery
            }
    
    def _archetype_unstable(self, concept: str, interaction_number: int) -> Dict[str, Any]:
        """
        Unstable archetype: variable correctness, variable response time
        Phase 2: Uses synthetic priors with stochastic variability
        """
        if self.use_synthetic_priors:
            # Use synthetic priors with moderate mastery
            mastery = self.synthetic_priors.power_law_prior(0.3, interaction_number)
            # Add stochastic variability
            mastery += np.random.normal(0, 0.1)
            mastery = np.clip(mastery, 0.0, 1.0)
            response = self.synthetic_priors.generate_synthetic_response(
                mastery=mastery,
                difficulty=0.5,
                interaction_number=interaction_number,
                time_since_last_practice=0.5,
                spacing_interval=0.5
            )
            return {
                "correctness": response["correctness"],
                "response_time": response["response_time_ms"] / 1000.0,
                "difficulty": 0.5,
                "mastery": mastery
            }
        else:
            # Fallback behavior: use proper reward function with stochastic variability
            mastery = 0.3 + interaction_number * 0.015
            mastery += np.random.normal(0, 0.1)  # Add variability
            mastery = np.clip(mastery, 0.0, 1.0)
            difficulty = 0.5
            p_correct = compute_correctness_probability(mastery, difficulty)
            return {
                "correctness": random.random() < p_correct,
                "response_time": random.uniform(2.0, 20.0),
                "difficulty": difficulty,
                "mastery": mastery
            }
    
    def _archetype_transfer_heavy(self, concept: str, interaction_number: int) -> Dict[str, Any]:
        """
        Transfer-heavy archetype: high correctness on related concepts
        Phase 2: Uses synthetic priors with spacing benefit
        """
        if self.use_synthetic_priors:
            # Use synthetic priors with high initial mastery and spacing benefit
            mastery = self.synthetic_priors.combined_mastery_prior(
                initial_mastery=0.5,
                interaction_number=interaction_number,
                time_since_last_practice=2.0,
                spacing_interval=5.0  # High spacing benefit
            )
            response = self.synthetic_priors.generate_synthetic_response(
                mastery=mastery,
                difficulty=0.4,
                interaction_number=interaction_number,
                time_since_last_practice=2.0,
                spacing_interval=5.0
            )
            return {
                "correctness": response["correctness"],
                "response_time": response["response_time_ms"] / 1000.0,
                "difficulty": 0.4,
                "mastery": mastery
            }
        else:
            # Fallback behavior: use proper reward function with high initial mastery
            mastery = 0.5 + interaction_number * 0.02  # Faster learning
            mastery = np.clip(mastery, 0.0, 1.0)
            difficulty = 0.4
            p_correct = compute_correctness_probability(mastery, difficulty)
            return {
                "correctness": random.random() < p_correct,
                "response_time": random.uniform(3.0, 8.0),
                "difficulty": difficulty,
                "mastery": mastery
            }
    
    def _archetype_forgetting(self, concept: str, interaction_number: int) -> Dict[str, Any]:
        """
        Forgetting archetype: correctness decreases over time
        Phase 2: Uses forgetting curve prior
        """
        if self.use_synthetic_priors:
            # Use synthetic priors with forgetting curve
            time_since_last = interaction_number * 2.0  # Simulate time passing
            retention = self.synthetic_priors.forgetting_prior(time_since_last)
            mastery = 0.7 * retention  # Decay mastery based on forgetting
            response = self.synthetic_priors.generate_synthetic_response(
                mastery=mastery,
                difficulty=0.5,
                interaction_number=interaction_number,
                time_since_last_practice=time_since_last,
                spacing_interval=0.0
            )
            return {
                "correctness": response["correctness"],
                "response_time": response["response_time_ms"] / 1000.0,
                "difficulty": 0.5,
                "mastery": mastery,
                "retention": retention
            }
        else:
            # Fallback behavior: use proper reward function with forgetting decay
            decay = min(0.5, interaction_number * 0.02)
            mastery = 0.7 - decay
            mastery = np.clip(mastery, 0.0, 1.0)
            difficulty = 0.5
            p_correct = compute_correctness_probability(mastery, difficulty)
            return {
                "correctness": random.random() < p_correct,
                "response_time": random.uniform(4.0, 10.0),
                "difficulty": difficulty,
                "mastery": mastery
            }
    
    def _archetype_exploration_sensitive(self, concept: str, interaction_number: int) -> Dict[str, Any]:
        """
        Exploration-sensitive archetype: performs better on familiar concepts
        Phase 2: Uses spacing effect prior
        """
        if self.use_synthetic_priors:
            # Use synthetic priors with spacing benefit for familiar concepts
            mastery = self.synthetic_priors.combined_mastery_prior(
                initial_mastery=0.4,
                interaction_number=interaction_number,
                time_since_last_practice=1.0,
                spacing_interval=3.0  # Moderate spacing benefit
            )
            response = self.synthetic_priors.generate_synthetic_response(
                mastery=mastery,
                difficulty=0.5,
                interaction_number=interaction_number,
                time_since_last_practice=1.0,
                spacing_interval=3.0
            )
            return {
                "correctness": response["correctness"],
                "response_time": response["response_time_ms"] / 1000.0,
                "difficulty": 0.5,
                "mastery": mastery
            }
        else:
            # Fallback behavior: use proper reward function with spacing benefit
            mastery = 0.4 + interaction_number * 0.018
            mastery = np.clip(mastery, 0.0, 1.0)
            difficulty = 0.5
            p_correct = compute_correctness_probability(mastery, difficulty)
            return {
                "correctness": random.random() < p_correct,
                "response_time": random.uniform(4.0, 12.0),
                "difficulty": difficulty,
                "mastery": mastery
            }
    
    def _archetype_challenge_seeking(self, concept: str, interaction_number: int) -> Dict[str, Any]:
        """
        Challenge-seeking archetype: prefers difficult concepts
        Phase 2: Uses IRT prior with high difficulty
        """
        if self.use_synthetic_priors:
            # Use synthetic priors with IRT for high difficulty
            mastery = self.synthetic_priors.power_law_prior(0.5, interaction_number)
            difficulty = 0.9  # High difficulty
            response = self.synthetic_priors.generate_synthetic_response(
                mastery=mastery,
                difficulty=difficulty,
                interaction_number=interaction_number,
                time_since_last_practice=1.0,
                spacing_interval=1.0
            )
            return {
                "correctness": response["correctness"],
                "response_time": response["response_time_ms"] / 1000.0,
                "difficulty": difficulty,
                "mastery": mastery
            }
        else:
            # Fallback behavior: use proper reward function with high difficulty
            mastery = 0.5 + interaction_number * 0.015
            mastery = np.clip(mastery, 0.0, 1.0)
            difficulty = 0.9  # High difficulty
            p_correct = compute_correctness_probability(mastery, difficulty)
            return {
                "correctness": random.random() < p_correct,
                "response_time": random.uniform(8.0, 20.0),
                "difficulty": difficulty,
                "mastery": mastery
            }
