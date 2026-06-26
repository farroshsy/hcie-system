"""
Behavioral Policies for Phase 3 Policy Divergence

Implements 9 meaningful behavioral policies as configuration/parameter sets
for the shared runtime layer (UnifiedBrain, ContextualBandit, Transfer Engine).

Architecture: Policies influence behavior through existing mechanisms:
- Adaptor action scoring (governance weights)
- Exploration behavior (bandit uncertainty_weight)
- Candidate filtering (difficulty/mastery constraints)
- Reward interpretation (policy_multiplier)
- Governance weighting (JT constitutional weights)

Reference: PLOT_AND_POLICY_FORMALIZATION.md - Part 2: Meaningful Policy Divergence
Reference: VALIDATED_RUNTIME_FLOW.md - Actual runtime spine
Reference: JT_GOVERNANCE_CONSTITUTION.md - JT governance semantics
Reference: COMPLETE_MATHEMATICAL_INVENTORY.md - Signal hierarchy
"""

from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class PolicyConfiguration:
    """
    Policy configuration as parameter set for shared runtime layer
    
    Policies do NOT reimplement logic - they configure existing components:
    - UnifiedBrain: governance_weights, policy_multiplier, energy constraints
    - ContextualBandit: uncertainty_weight, exploration parameters
    - Transfer Engine: transfer_enabled, transfer_multiplier
    - Ensemble: learner weights
    """
    
    def __init__(self, policy_name: str, config: Dict[str, Any]):
        """
        Initialize policy configuration
        
        Args:
            policy_name: Name of policy
            config: Configuration parameters for shared runtime
        """
        self.policy_name = policy_name
        self.config = config
    
    def get_governance_weights(self) -> Dict[str, float]:
        """Get JT governance weights (6D: w1-w6)"""
        # 🔥 6D Migration: Return w1-w6 keys for ConstitutionalJTGovernance compatibility
        # w1=delta_m, w2=transfer_realized, w3=transfer_prospective, w4=challenge, w5=uncertainty, w6=zpd
        legacy_weights = self.config.get("governance_weights", {})
        if legacy_weights:
            # Map old 5D keys to new 6D keys (transfer maps to w2, w3 stays at default)
            return {
                "w1": legacy_weights.get("mastery", 0.25),
                "w2": legacy_weights.get("transfer", 0.15),
                "w3": 0.15,  # transfer_prospective - dormant in Phase A
                "w4": legacy_weights.get("challenge", 0.15),
                "w5": legacy_weights.get("uncertainty", 0.15),
                "w6": legacy_weights.get("zpd", 0.15),
            }
        # Default 6D weights
        return {
            "w1": 0.25,  # delta_m
            "w2": 0.15,  # transfer_realized
            "w3": 0.15,  # transfer_prospective (dormant in Phase A)
            "w4": 0.15,  # challenge
            "w5": 0.15,  # uncertainty
            "w6": 0.15,  # zpd
        }
    
    def get_policy_multiplier(self) -> float:
        """Get policy learning rate multiplier"""
        return self.config.get("policy_multiplier", 1.0)
    
    def get_bandit_config(self) -> Dict[str, Any]:
        """Get bandit configuration (uncertainty_weight, exploration)"""
        return self.config.get("bandit_config", {
            "uncertainty_weight": 0.1,
            "learning_gain_weight": 0.05,
            "exploration_rate": 0.1,
            "jt_aware_exploration": False
        })
    
    def get_transfer_config(self) -> Dict[str, Any]:
        """Get transfer learning configuration"""
        return self.config.get("transfer_config", {
            "transfer_enabled": False,
            "transfer_multiplier": 1.0
        })
    
    def get_ensemble_weights(self) -> Dict[str, float]:
        """Get ensemble learner weights (Lyapunov, Bayesian, Kalman)"""
        return self.config.get("ensemble_weights", {
            "lyapunov": 0.33,
            "bayesian": 0.33,
            "kalman": 0.34
        })
    
    def get_energy_config(self) -> Dict[str, Any]:
        """Get energy constraint configuration"""
        return self.config.get("energy_config", {
            "total_energy": 0.05,
            "alpha": 0.75,
            "gamma": 0.3
        })
    
    def get_candidate_filtering(self) -> Dict[str, Any]:
        """Get candidate filtering constraints"""
        return self.config.get("candidate_filtering", {
            "zpd_filter": False,
            "difficulty_filter": False,
            "min_mastery": 0.0,
            "max_mastery": 1.0
        })
    
    def get_characteristics(self) -> Dict[str, Any]:
        """Get policy characteristics for analysis"""
        return {
            "policy_name": self.policy_name,
            "exploration": self.config.get("exploration_type", "unknown"),
            "exploitation": self.config.get("exploitation_type", "unknown"),
            "governance": self.config.get("governance_type", "none"),
            "transfer": self.config.get("transfer_enabled", False),
            "zpd": self.config.get("zpd_support", "none"),
            "challenge": self.config.get("challenge_support", False)
        }


class PolicyFactory:
    """Factory for creating policy configurations"""
    
    @staticmethod
    def create_policy(policy_name: str, concepts: List[str] = None) -> PolicyConfiguration:
        """
        Create policy configuration by name
        
        Args:
            policy_name: Name of policy
            concepts: List of available concepts (for static curriculum)
            
        Returns:
            PolicyConfiguration instance
        """
        concepts = concepts or []
        
        if policy_name == "random":
            return PolicyFactory._random_policy()
        elif policy_name == "static":
            return PolicyFactory._static_policy(concepts)
        elif policy_name == "mastery_greedy":
            return PolicyFactory._mastery_greedy_policy()
        elif policy_name == "uncertainty_reduction":
            return PolicyFactory._uncertainty_reduction_policy()
        elif policy_name == "zpd_aligned":
            return PolicyFactory._zpd_aligned_policy()
        elif policy_name == "epsilon_greedy":
            return PolicyFactory._epsilon_greedy_policy()
        elif policy_name == "ucb":
            return PolicyFactory._ucb_policy()
        elif policy_name == "thompson":
            return PolicyFactory._thompson_policy()
        elif policy_name == "hcie":
            return PolicyFactory._hcie_policy()
        else:
            raise ValueError(f"Unknown policy: {policy_name}")
    
    @staticmethod
    def _random_policy() -> PolicyConfiguration:
        """
        Policy 1: Random Baseline
        
        Configuration:
        - No governance (equal weights)
        - No transfer
        - Pure exploration (uncertainty_weight = 1.0)
        - No candidate filtering
        """
        return PolicyConfiguration("random", {
            "exploration_type": "pure",
            "exploitation_type": "none",
            "governance_type": "none",
            "governance_weights": {
                "mastery": 0.2,
                "transfer": 0.0,
                "challenge": 0.2,
                "uncertainty": 0.2,
                "zpd": 0.4
            },
            "policy_multiplier": 0.97,
            "bandit_config": {
                "uncertainty_weight": 1.0,
                "learning_gain_weight": 0.0,
                "exploration_rate": 1.0,
                "jt_aware_exploration": False
            },
            "transfer_config": {
                "transfer_enabled": False,
                "transfer_multiplier": 0.0
            },
            "candidate_filtering": {
                "zpd_filter": False,
                "difficulty_filter": False
            }
        })
    
    @staticmethod
    def _static_policy(concepts: List[str]) -> PolicyConfiguration:
        """
        Policy 2: Static Curriculum
        
        Configuration:
        - No adaptation
        - Fixed sequence (stored in curriculum_sequence)
        - No exploration
        - No governance
        """
        return PolicyConfiguration("static", {
            "exploration_type": "none",
            "exploitation_type": "none",
            "governance_type": "none",
            "governance_weights": {
                "mastery": 0.2,
                "transfer": 0.0,
                "challenge": 0.2,
                "uncertainty": 0.0,
                "zpd": 0.6
            },
            "policy_multiplier": 1.0,
            "bandit_config": {
                "uncertainty_weight": 0.0,
                "learning_gain_weight": 0.0,
                "exploration_rate": 0.0,
                "jt_aware_exploration": False
            },
            "transfer_config": {
                "transfer_enabled": False,
                "transfer_multiplier": 0.0
            },
            "candidate_filtering": {
                "zpd_filter": False,
                "difficulty_filter": False
            },
            "curriculum_sequence": concepts  # Fixed sequence
        })
    
    @staticmethod
    def _mastery_greedy_policy() -> PolicyConfiguration:
        """
        Policy 3: Mastery-Only Greedy
        
        Configuration:
        - Pure exploitation (mastery weight = 1.0)
        - No exploration (uncertainty_weight = 0.0)
        - No transfer
        - High mastery weight in JT
        """
        return PolicyConfiguration("mastery_greedy", {
            "exploration_type": "none",
            "exploitation_type": "pure",
            "governance_type": "mastery-focused",
            "governance_weights": {
                "mastery": 1.0,
                "transfer": 0.0,
                "challenge": 0.0,
                "uncertainty": 0.0,
                "zpd": 0.0
            },
            "policy_multiplier": 1.0,
            "bandit_config": {
                "uncertainty_weight": 0.0,
                "learning_gain_weight": 0.1,
                "exploration_rate": 0.0,
                "jt_aware_exploration": False
            },
            "transfer_config": {
                "transfer_enabled": False,
                "transfer_multiplier": 0.0
            },
            "candidate_filtering": {
                "zpd_filter": False,
                "difficulty_filter": False,
                "min_mastery": 0.3  # Prefer concepts with some mastery
            }
        })
    
    @staticmethod
    def _uncertainty_reduction_policy() -> PolicyConfiguration:
        """
        Policy 4: Uncertainty-Reduction
        
        Configuration:
        - Pure exploration (uncertainty_weight = 1.0)
        - No exploitation
        - High uncertainty weight in JT
        """
        return PolicyConfiguration("uncertainty_reduction", {
            "exploration_type": "pure",
            "exploitation_type": "none",
            "governance_type": "uncertainty-focused",
            "governance_weights": {
                "mastery": 0.0,
                "transfer": 0.0,
                "challenge": 0.0,
                "uncertainty": 1.0,
                "zpd": 0.0
            },
            "policy_multiplier": 1.0,
            "bandit_config": {
                "uncertainty_weight": 1.0,
                "learning_gain_weight": 0.0,
                "exploration_rate": 1.0,
                "jt_aware_exploration": False
            },
            "transfer_config": {
                "transfer_enabled": False,
                "transfer_multiplier": 0.0
            },
            "candidate_filtering": {
                "zpd_filter": False,
                "difficulty_filter": False,
                "min_mastery": 0.0
            }
        })
    
    @staticmethod
    def _zpd_aligned_policy() -> PolicyConfiguration:
        """
        Policy 5: ZPD-Aligned
        
        Configuration:
        - Challenge-appropriate selection
        - ZPD filtering enabled
        - High ZPD weight in JT
        """
        return PolicyConfiguration("zpd_aligned", {
            "exploration_type": "none",
            "exploitation_type": "none",
            "governance_type": "zpd-focused",
            "governance_weights": {
                "mastery": 0.2,
                "transfer": 0.0,
                "challenge": 0.4,
                "uncertainty": 0.0,
                "zpd": 0.4
            },
            "policy_multiplier": 1.0,
            "bandit_config": {
                "uncertainty_weight": 0.1,
                "learning_gain_weight": 0.05,
                "exploration_rate": 0.1,
                "jt_aware_exploration": False
            },
            "transfer_config": {
                "transfer_enabled": False,
                "transfer_multiplier": 0.0
            },
            "candidate_filtering": {
                "zpd_filter": True,
                "zpd_threshold": 0.2,
                "difficulty_filter": False
            },
            "zpd_support": "static",
            "challenge_support": True
        })
    
    @staticmethod
    def _epsilon_greedy_policy() -> PolicyConfiguration:
        """
        Policy 6: Epsilon-Greedy with Mastery
        
        Configuration:
        - Fixed exploration rate (ε = 0.1)
        - Simple exploration-exploitation balance
        - No JT governance
        """
        return PolicyConfiguration("epsilon_greedy", {
            "exploration_type": "fixed",
            "exploitation_type": "fixed",
            "governance_type": "none",
            "governance_weights": {
                "mastery": 0.5,
                "transfer": 0.0,
                "challenge": 0.0,
                "uncertainty": 0.0,
                "zpd": 0.5
            },
            "policy_multiplier": 1.0,
            "bandit_config": {
                "uncertainty_weight": 0.1,
                "learning_gain_weight": 0.05,
                "exploration_rate": 0.1,
                "jt_aware_exploration": False
            },
            "transfer_config": {
                "transfer_enabled": False,
                "transfer_multiplier": 0.0
            },
            "candidate_filtering": {
                "zpd_filter": False,
                "difficulty_filter": False
            }
        })
    
    @staticmethod
    def _ucb_policy() -> PolicyConfiguration:
        """
        Policy 7: UCB with Mastery
        
        Configuration:
        - Optimism in face of uncertainty
        - Adaptive exploration (uncertainty decreases over time)
        - No JT governance
        """
        return PolicyConfiguration("ucb", {
            "exploration_type": "adaptive",
            "exploitation_type": "adaptive",
            "governance_type": "ucb-based",
            "governance_weights": {
                "mastery": 0.6,
                "transfer": 0.0,
                "challenge": 0.0,
                "uncertainty": 0.4,
                "zpd": 0.0
            },
            "policy_multiplier": 1.0,
            "bandit_config": {
                "uncertainty_weight": 0.2,
                "learning_gain_weight": 0.05,
                "exploration_rate": "adaptive",
                "ucb_exploration_bonus": 2.0,
                "jt_aware_exploration": False
            },
            "transfer_config": {
                "transfer_enabled": False,
                "transfer_multiplier": 0.0
            },
            "candidate_filtering": {
                "zpd_filter": False,
                "difficulty_filter": False
            }
        })
    
    @staticmethod
    def _thompson_policy() -> PolicyConfiguration:
        """
        Policy 8: Thompson Sampling with Mastery
        
        Configuration:
        - Bayesian exploration
        - Adaptive exploration
        - No JT governance
        """
        return PolicyConfiguration("thompson", {
            "exploration_type": "adaptive",
            "exploitation_type": "adaptive",
            "governance_type": "thompson-based",
            "governance_weights": {
                "mastery": 0.6,
                "transfer": 0.0,
                "challenge": 0.0,
                "uncertainty": 0.4,
                "zpd": 0.0
            },
            "policy_multiplier": 1.0,
            "bandit_config": {
                "uncertainty_weight": 0.1,
                "learning_gain_weight": 0.05,
                "exploration_rate": "adaptive",
                "thompson_sampling": True,
                "jt_aware_exploration": False
            },
            "transfer_config": {
                "transfer_enabled": False,
                "transfer_multiplier": 0.0
            },
            "candidate_filtering": {
                "zpd_filter": False,
                "difficulty_filter": False
            }
        })
    
    @staticmethod
    def _hcie_policy() -> PolicyConfiguration:
        """
        Policy 9: HCIE (JT-Governed Thompson Sampling)
        
        Configuration:
        - Multi-learner synthesis
        - JT-centric governance (all 5 components)
        - JT-aware exploration (adapts to volatility)
        - Transfer learning enabled
        - ZPD alignment
        - Challenge-appropriate selection
        """
        return PolicyConfiguration("hcie", {
            "exploration_type": "adaptive (JT)",
            "exploitation_type": "adaptive (JT)",
            "governance_type": "JT-centric",
            "governance_weights": {
                "mastery": 0.3,
                "transfer": 0.2,
                "challenge": 0.2,
                "uncertainty": 0.2,
                "zpd": 0.1
            },
            "policy_multiplier": 1.12,  # Expected JT from governance history
            "bandit_config": {
                "uncertainty_weight": 0.1,
                "learning_gain_weight": 0.05,
                "exploration_rate": "adaptive",
                "thompson_sampling": True,
                "jt_aware_exploration": True,  # KEY: adapts to JT volatility
                "jt_window_size": 20
            },
            "transfer_config": {
                "transfer_enabled": True,
                "transfer_multiplier": 1.0
            },
            "ensemble_weights": {
                "lyapunov": 0.33,
                "bayesian": 0.33,
                "kalman": 0.34
            },
            "candidate_filtering": {
                "zpd_filter": True,
                "zpd_threshold": 0.2,
                "difficulty_filter": True,
                "challenge_alignment": True
            },
            "zpd_support": "adaptive",
            "challenge_support": True,
            "transfer_support": True
        })
    
    @staticmethod
    def get_all_policy_names() -> List[str]:
        """Return list of all available policy names"""
        return [
            "random",
            "static",
            "mastery_greedy",
            "uncertainty_reduction",
            "zpd_aligned",
            "epsilon_greedy",
            "ucb",
            "thompson",
            "hcie"
        ]


def compute_policy_divergence(policy1: PolicyConfiguration, policy2: PolicyConfiguration) -> Dict[str, Any]:
    """
    Compute divergence metrics between two policies
    
    Args:
        policy1: First policy configuration
        policy2: Second policy configuration
        
    Returns:
        Divergence metrics
    """
    # Compute governance weight divergence
    weights1 = policy1.get_governance_weights()
    weights2 = policy2.get_governance_weights()
    weight_divergence = sum(abs(weights1[k] - weights2[k]) for k in weights1)
    
    # Compute bandit config divergence
    bandit1 = policy1.get_bandit_config()
    bandit2 = policy2.get_bandit_config()
    bandit_divergence = 0
    for key in ["uncertainty_weight", "learning_gain_weight", "exploration_rate"]:
        if key in bandit1 and key in bandit2:
            if isinstance(bandit1[key], (int, float)) and isinstance(bandit2[key], (int, float)):
                bandit_divergence += abs(bandit1[key] - bandit2[key])
            else:
                bandit_divergence += 1 if bandit1[key] != bandit2[key] else 0
    
    # Compute characteristic divergence
    char1 = policy1.get_characteristics()
    char2 = policy2.get_characteristics()
    characteristic_divergence = sum(
        1 for k in char1 if k != "policy_name" and char1[k] != char2[k]
    )
    
    return {
        "governance_weight_divergence": weight_divergence,
        "bandit_config_divergence": bandit_divergence,
        "characteristic_divergence": characteristic_divergence,
        "policy1_characteristics": char1,
        "policy2_characteristics": char2
    }


if __name__ == "__main__":
    # Test all policy configurations
    print("🧪 Testing Behavioral Policy Configurations")
    print("=" * 60)
    
    concepts = ["concept_001", "concept_002", "concept_003", "concept_004", "concept_005"]
    
    # Test each policy
    for policy_name in PolicyFactory.get_all_policy_names():
        print(f"\n📊 Policy: {policy_name}")
        policy = PolicyFactory.create_policy(policy_name, concepts)
        
        print(f"  Governance Weights: {policy.get_governance_weights()}")
        print(f"  Policy Multiplier: {policy.get_policy_multiplier()}")
        print(f"  Bandit Config: {policy.get_bandit_config()}")
        print(f"  Transfer Config: {policy.get_transfer_config()}")
        print(f"  Characteristics: {policy.get_characteristics()}")
    
    # Test policy divergence
    print("\n" + "=" * 60)
    print("📊 Testing Policy Divergence")
    print("=" * 60)
    
    policy1 = PolicyFactory.create_policy("random", concepts)
    policy2 = PolicyFactory.create_policy("mastery_greedy", concepts)
    divergence = compute_policy_divergence(policy1, policy2)
    
    print("\nRandom vs Mastery-Greedy:")
    print(f"  Governance Weight Divergence: {divergence['governance_weight_divergence']}")
    print(f"  Bandit Config Divergence: {divergence['bandit_config_divergence']}")
    print(f"  Characteristic Divergence: {divergence['characteristic_divergence']}")
    
    print("\n✅ All policy configurations implemented successfully")
