"""
HCIE Policy Engine
Implements HCIE, Heuristic, Static, and Random policies with Phase 7 calibrated parameters

🔥 BRAIN GOVERNANCE:
- CONTROL: Policy selection maximizes expected future ΔJT (JT-native)
- STATE: policy_jt_history tracks historical JT outcomes per policy
- OBSERVE: policy_stats for research/debug (does not affect behavior)
- PHASE 5 JT-AWARE POLICY: Policies become constitutional control instruments
  - Old: STATE → POLICY (heuristic selection)
  - New: expected future ΔJT → POLICY (constitutional optimization)
  - Policy effects are delayed (cognitive trajectory curvature)
  - This makes policy temporally self-consistent with other subsystems
- PHASE 6 CONSTITUTIONAL PURIFICATION: Remove hidden motivational priors
  - Old: learning_multipliers encoded architectural beliefs about pedagogy
  - New: policy effectiveness learned from JT history, not handcrafted ideology
  - All multipliers now neutral (1.0) - no inherent advantage/disadvantage
  - Policy multiplier derived from expected_JT, not hardcoded priors
  - This eliminates embedded pedagogical assumptions from control decisions

POLICY DEFINITIONS:
- HCIE: Select concepts with moderate mastery for optimal learning (ZPD-aligned)
- Heuristic: Select concepts with lowest mastery (remediation-focused)
- Static: Fixed sequence cycling through concepts (curriculum-based)
- Random: Uniform random selection (exploration baseline)
"""

from typing import List, Dict, Tuple
import logging
from collections import defaultdict
import numpy as np

logger = logging.getLogger(__name__)

class PolicyEngine:
    """
    Policy engine implementing HCIE, Heuristic, Static, and Random selection strategies
    Calibrated with Phase 7 experimental parameters
    
    MATH/WEIGHT PRESERVATION:
    - All learning_multipliers are neutral (1.0) - no inherent advantage
    - All forgetting_multipliers are neutral (1.0) - no inherent advantage  
    - Policy selection is JT-driven via expected_JT, not hardcoded priors
    - Math calculations in UnifiedLearningBrain remain unchanged
    - Only policy selection logic differs, not learning model
    """
    
    def __init__(self, 
                 hcie_threshold: float = 0.45,
                 learning_multipliers: Dict[str, float] = None):
        """
        Initialize policy engine
        
        Args:
            hcie_threshold: Mastery threshold for HCIE eligibility (Phase 7 calibrated)
            learning_multipliers: DEPRECATED - Phase 6 removes hardcoded motivational priors
        """
        self.hcie_threshold = hcie_threshold
        
        # 🔥 PHASE 6 CONSTITUTIONAL PURIFICATION: Remove hardcoded motivational priors
        # Old: learning_multipliers encoded architectural beliefs about pedagogy
        # New: policy effectiveness is learned from JT history, not handcrafted ideology
        # These multipliers are now DEPRECATED and should not be used for control decisions
        # They exist only for backward compatibility in non-JT-aware code paths
        self.learning_multipliers = learning_multipliers or {
            "hcie": 1.0,       # 🔥 PHASE 6: Neutral prior (no inherent advantage)
            "heuristic": 1.0,  # 🔥 PHASE 6: Neutral prior (no inherent advantage)
            "static": 1.0,     # 🔥 PHASE 6: Neutral prior (no inherent advantage)
            "random": 1.0      # 🔥 PHASE 6: Neutral prior (no inherent disadvantage)
        }
        
        # Forgetting multipliers (Phase 7 calibrated)
        # Note: These should also be JT-driven in future, but kept for now as they affect
        # memory decay which is more structural than motivational
        self.forgetting_multipliers = {
            "hcie": 1.0,       # 🔥 PHASE 6: Neutral forgetting (no inherent advantage)
            "heuristic": 1.0,  # 🔥 PHASE 6: Neutral forgetting (no inherent advantage)
            "static": 1.0,     # 🔥 PHASE 6: Neutral forgetting (no inherent advantage)
            "random": 1.0      # 🔥 PHASE 6: Neutral forgetting (no inherent disadvantage)
        }
        
        # 🔥 PHASE 5: Track JT history per policy for JT-aware selection
        self.policy_jt_history = defaultdict(list)  # policy_type -> list of JT values
        self.policy_jt_window_size = 50  # Rolling window for expected JT estimation
        
        logger.info("Policy Engine initialized with Phase 6 constitutional purification")
        logger.info("🔥 PHASE 6: Hardcoded motivational priors removed (neutral priors)")
        logger.info("🔥 PHASE 5: JT-aware policy selection enabled")
    
    def record_policy_jt(self, policy_type: str, J_t: float) -> None:
        """
        🔥 PHASE 5: Record JT outcome for policy (for JT-aware selection)
        
        Governance principle:
        - Policies accumulate constitutional memory about their JT effectiveness
        - This enables policy selection based on expected future ΔJT
        - Not heuristic scoring, but empirical JT optimization
        
        Args:
            policy_type: The policy type used (hcie, heuristic, static, random)
            J_t: The objective function value observed after policy application
        """
        self.policy_jt_history[policy_type].append(J_t)
        
        # Keep only recent history (prevent memory growth)
        if len(self.policy_jt_history[policy_type]) > self.policy_jt_window_size:
            self.policy_jt_history[policy_type] = self.policy_jt_history[policy_type][-self.policy_jt_window_size:]
        
        logger.debug(f"🔥 POLICY JT HISTORY: {policy_type} recorded J_t={J_t:.6f}, history_size={len(self.policy_jt_history[policy_type])}")
    
    def get_expected_policy_jt(self, policy_type: str) -> float:
        """
        🔥 PHASE 5: Estimate expected future JT for a policy
        
        Governance principle:
        - Use empirical rolling mean of historical JT outcomes
        - This represents the expected future ΔJT if this policy is selected
        - Policies with higher expected JT are preferred (constitutional optimization)
        
        Args:
            policy_type: The policy type to estimate
            
        Returns:
            Expected JT value (rolling mean), or 0.0 if insufficient history
        """
        if policy_type not in self.policy_jt_history or len(self.policy_jt_history[policy_type]) < 5:
            # Not enough history: use neutral prior (allows exploration)
            logger.debug(f"🔥 POLICY JT ESTIMATION: {policy_type} has insufficient history (<5), using neutral prior")
            return 0.0
        
        expected_jt = np.mean(self.policy_jt_history[policy_type])
        logger.debug(f"🔥 POLICY JT ESTIMATION: {policy_type} expected_JT={expected_jt:.6f} (n={len(self.policy_jt_history[policy_type])})")
        
        return expected_jt
    
    def select_policy_jt_aware(self, 
                               available_policies: List[str],
                               user_id: str,
                               available_concepts: List[str],
                               mastery_params: Dict[str, Tuple[float, float]],
                               difficulty_map: Dict[str, float],
                               context: Dict[str, any] = None) -> Tuple[str, float]:
        """
        🔥 PHASE 5: Select policy based on expected future ΔJT (JT-native)
        
        Governance principle:
        - Old: STATE → POLICY (heuristic selection based on mastery/uncertainty)
        - New: expected future ΔJT → POLICY (constitutional optimization)
        - Policies become governance instruments, not teaching styles
        - This makes policy temporally self-consistent with bandit/ensemble/η
        
        Args:
            available_policies: List of available policy types (e.g., ["hcie", "heuristic", "static", "random"])
            user_id: User identifier
            available_concepts: List of available concepts
            mastery_params: Mastery parameters for each concept
            difficulty_map: Difficulty for each concept
            context: User context (prev_concept, etc.)
        
        Returns:
            (selected_policy, expected_jt_score)
        """
        logger.info(f"🔥 JT-AWARE POLICY SELECTION: user={user_id}, available_policies={available_policies}")
        
        # Estimate expected JT for each policy
        policy_scores = []
        for policy in available_policies:
            expected_jt = self.get_expected_policy_jt(policy)
            policy_scores.append((policy, expected_jt))
            logger.debug(f"🔥 POLICY SCORE: {policy} expected_JT={expected_jt:.6f}")
        
        # Select policy with highest expected JT
        if policy_scores:
            # Sort by expected JT (descending)
            policy_scores.sort(key=lambda x: x[1], reverse=True)
            selected_policy = policy_scores[0][0]
            expected_jt_score = policy_scores[0][1]
            
            logger.info(f"🔥 JT-AWARE POLICY SELECTED: {selected_policy} with expected_JT={expected_jt_score:.6f}")
            return selected_policy, expected_jt_score
        else:
            # Fallback to first available policy
            logger.warning("🔥 JT-AWARE POLICY: No policy scores available, using fallback")
            return available_policies[0] if available_policies else "random", 0.0
    
    def get_policy_stats(self) -> Dict[str, Dict[str, float]]:
        """Get policy configuration statistics"""
        stats = {
            "hcie": {
                "threshold": self.hcie_threshold,
                "learning_multiplier": self.learning_multipliers["hcie"],
                "forgetting_multiplier": self.forgetting_multipliers["hcie"]
            },
            "heuristic": {
                "learning_multiplier": self.learning_multipliers["heuristic"],
                "forgetting_multiplier": self.forgetting_multipliers["heuristic"]
            },
            "static": {
                "learning_multiplier": self.learning_multipliers["static"],
                "forgetting_multiplier": self.forgetting_multipliers["static"]
            },
            "random": {
                "learning_multiplier": self.learning_multipliers["random"],
                "forgetting_multiplier": self.forgetting_multipliers["random"]
            }
        }
        
        # 🔥 PHASE 5: Add expected JT statistics
        for policy_type in ["hcie", "heuristic", "static", "random"]:
            if policy_type in self.policy_jt_history and len(self.policy_jt_history[policy_type]) >= 5:
                stats[policy_type]["expected_JT"] = float(np.mean(self.policy_jt_history[policy_type]))
                stats[policy_type]["JT_history_size"] = len(self.policy_jt_history[policy_type])
            else:
                stats[policy_type]["expected_JT"] = 0.0
                stats[policy_type]["JT_history_size"] = len(self.policy_jt_history.get(policy_type, []))
        
        return stats
