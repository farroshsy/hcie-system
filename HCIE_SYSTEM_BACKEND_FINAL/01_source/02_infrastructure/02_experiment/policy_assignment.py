"""
Policy Assignment Extension

Deterministic policy assignment for experiments.
Extends existing assignment mechanism in unified_brain.py to support experimental policies.

Design Principles:
- Deterministic assignment (same user_id + same seed → same policy)
- Seed-based reproducibility
- Support for multiple policy lists
- Integration with existing experiment infrastructure
"""

import hashlib
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


def assign_experiment_policy(
    user_id: str,
    policy_seed: int,
    policies: List[str]
) -> str:
    """
    Deterministic assignment to experimental policies
    
    Same user_id + same seed → same policy assignment
    This ensures reproducibility across experiment runs.
    
    Args:
        user_id: User identifier
        policy_seed: Seed for deterministic assignment
        policies: List of available policies
        
    Returns:
        Assigned policy
        
    Example:
        >>> assign_experiment_policy("user_001", 42, ["random", "static", "heuristic", "hcie"])
        "heuristic"
    """
    hash_val = int(hashlib.md5(f"{user_id}_{policy_seed}".encode(), usedforsecurity=False).hexdigest(), 16)
    policy_idx = hash_val % len(policies)
    return policies[policy_idx]


def assign_cohort_policy(
    user_id: str,
    cohort_seed: int,
    cohort_assignments: Dict[str, List[str]]
) -> str:
    """
    Assign user to cohort based on seed
    
    Args:
        user_id: User identifier
        cohort_seed: Seed for deterministic cohort assignment
        cohort_assignments: Dict mapping cohort names to policy lists
        
    Returns:
        Assigned cohort name
    """
    hash_val = int(hashlib.md5(f"{user_id}_{cohort_seed}".encode(), usedforsecurity=False).hexdigest(), 16)
    cohort_names = list(cohort_assignments.keys())
    cohort_idx = hash_val % len(cohort_names)
    return cohort_names[cohort_idx]


def generate_policy_distribution(
    num_users: int,
    policies: List[str],
    distribution_type: str = "balanced"
) -> Dict[str, int]:
    """
    Generate policy distribution for cohort
    
    Args:
        num_users: Number of users in cohort
        policies: List of available policies
        distribution_type: "balanced" (equal) or "random" (unequal)
        
    Returns:
        Dict mapping policy to number of users
    """
    if distribution_type == "balanced":
        users_per_policy = num_users // len(policies)
        remainder = num_users % len(policies)
        
        distribution = {}
        for i, policy in enumerate(policies):
            distribution[policy] = users_per_policy + (1 if i < remainder else 0)
        
        return distribution
    
    elif distribution_type == "random":
        import random
        distribution = {policy: 0 for policy in policies}
        
        for _ in range(num_users):
            policy = random.choice(policies)
            distribution[policy] += 1
        
        return distribution
    
    else:
        raise ValueError(f"Invalid distribution type: {distribution_type}")


class PolicyAssigner:
    """
    Policy assignment manager for experiments
    
    RESPONSIBILITIES:
    - Deterministic policy assignment
    - Cohort management
    - Distribution tracking
    - Reproducibility guarantees
    """
    
    def __init__(self):
        """Initialize policy assigner"""
        self.assignments: Dict[str, Dict[str, Any]] = {}
    
    def assign_user(
        self,
        user_id: str,
        policy_seed: int,
        policies: List[str],
        cohort_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Assign policy to user
        
        Args:
            user_id: User identifier
            policy_seed: Seed for deterministic assignment
            policies: List of available policies
            cohort_id: Optional cohort identifier
            
        Returns:
            Assignment details
        """
        policy = assign_experiment_policy(user_id, policy_seed, policies)
        
        assignment = {
            "user_id": user_id,
            "policy": policy,
            "policy_seed": policy_seed,
            "cohort_id": cohort_id,
            "assigned_at": None
        }
        
        self.assignments[user_id] = assignment
        
        logger.debug(f"Assigned policy {policy} to user {user_id}")
        
        return assignment
    
    def get_assignment(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get assignment for user
        
        Args:
            user_id: User identifier
            
        Returns:
            Assignment details or None if not assigned
        """
        return self.assignments.get(user_id)
    
    def get_distribution(self, cohort_id: Optional[str] = None) -> Dict[str, int]:
        """
        Get policy distribution
        
        Args:
            cohort_id: Optional cohort filter
            
        Returns:
            Dict mapping policy to count
        """
        distribution = {}
        
        for user_id, assignment in self.assignments.items():
            if cohort_id is None or assignment.get("cohort_id") == cohort_id:
                policy = assignment["policy"]
                distribution[policy] = distribution.get(policy, 0) + 1
        
        return distribution
    
    def clear_assignments(self):
        """Clear all assignments"""
        self.assignments.clear()


# Example usage and testing
if __name__ == "__main__":
    # Test deterministic assignment
    policies = ["random", "static", "heuristic", "hcie"]
    
    # Same user + same seed should always return same policy
    policy1 = assign_experiment_policy("user_001", 42, policies)
    policy2 = assign_experiment_policy("user_001", 42, policies)
    assert policy1 == policy2, "Deterministic assignment failed"
    
    # Different users with same seed should return different policies (likely)
    policy3 = assign_experiment_policy("user_002", 42, policies)
    print(f"User 001: {policy1}, User 002: {policy3}")
    
    # Test distribution generation
    distribution = generate_policy_distribution(100, policies, "balanced")
    print(f"Balanced distribution: {distribution}")
    
    # Test policy assigner
    assigner = PolicyAssigner()
    assigner.assign_user("user_001", 42, policies, "cohort_001")
    assigner.assign_user("user_002", 42, policies, "cohort_001")
    
    dist = assigner.get_distribution("cohort_001")
    print(f"Cohort distribution: {dist}")
    
    print("Policy assignment extension tests passed!")
