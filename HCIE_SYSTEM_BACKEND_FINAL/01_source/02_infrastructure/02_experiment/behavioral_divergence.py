"""
Behavioral Divergence Metrics

Measures actual behavioral differences between policies, not just configuration differences.
This is critical for validating that policy configurations lead to meaningful behavioral changes.

Metrics:
- Trajectory Divergence: How different the sequence of concepts selected is
- KL Divergence: Distributional difference in action selection
- Regret Divergence: Difference in cumulative regret
- JT Trajectory Divergence: Difference in Joint Trajectory evolution
"""

import numpy as np
from typing import List, Dict, Optional
from scipy.stats import entropy
from scipy.spatial.distance import euclidean


def compute_trajectory_divergence(trajectory_a: List[str], trajectory_b: List[str]) -> float:
    """
    Compute trajectory divergence between two concept selection sequences.
    
    Uses Levenshtein distance normalized by sequence length to measure
    how different the actual concept selection sequences are.
    
    Args:
        trajectory_a: List of concept IDs selected by policy A
        trajectory_b: List of concept IDs selected by policy B
        
    Returns:
        Normalized divergence score (0 = identical, 1 = completely different)
    """
    if not trajectory_a and not trajectory_b:
        return 0.0
    
    if not trajectory_a or not trajectory_b:
        return 1.0
    
    # Compute Levenshtein distance
    len_a, len_b = len(trajectory_a), len(trajectory_b)
    
    # Create DP table
    dp = [[0] * (len_b + 1) for _ in range(len_a + 1)]
    
    for i in range(len_a + 1):
        dp[i][0] = i
    for j in range(len_b + 1):
        dp[0][j] = j
    
    for i in range(1, len_a + 1):
        for j in range(1, len_b + 1):
            if trajectory_a[i-1] == trajectory_b[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
    
    levenshtein_distance = dp[len_a][len_b]
    
    # Normalize by max length
    max_len = max(len_a, len_b)
    normalized_divergence = levenshtein_distance / max_len
    
    return normalized_divergence


def compute_kl_divergence(distribution_a: Dict[str, float], distribution_b: Dict[str, float], epsilon: float = 1e-10) -> float:
    """
    Compute KL divergence between two action selection distributions.
    
    Measures how different the probability distributions over concepts are.
    KL divergence is asymmetric (D_KL(P || Q) != D_KL(Q || P)).
    
    Args:
        distribution_a: Probability distribution over concepts for policy A
        distribution_b: Probability distribution over concepts for policy B
        epsilon: Small value to avoid log(0)
        
    Returns:
        KL divergence score (0 = identical, higher = more different)
    """
    # Ensure both distributions have the same keys
    all_concepts = set(distribution_a.keys()) | set(distribution_b.keys())
    
    # Normalize distributions
    p = np.array([distribution_a.get(concept, 0.0) + epsilon for concept in all_concepts])
    q = np.array([distribution_b.get(concept, 0.0) + epsilon for concept in all_concepts])
    
    # Normalize to sum to 1
    p = p / p.sum()
    q = q / q.sum()
    
    # Compute KL divergence
    kl_div = entropy(p, q)
    
    return kl_div


def compute_regret_divergence(regret_a: List[float], regret_b: List[float]) -> float:
    """
    Compute divergence in cumulative regret between two policies.
    
    Measures how different the regret accumulation patterns are.
    Uses area between regret curves normalized by total area.
    
    Args:
        regret_a: List of cumulative regret values for policy A
        regret_b: List of cumulative regret values for policy B
        
    Returns:
        Normalized regret divergence (0 = identical, higher = more different)
    """
    if not regret_a and not regret_b:
        return 0.0
    
    if not regret_a or not regret_b:
        return 1.0
    
    # Ensure same length
    min_len = min(len(regret_a), len(regret_b))
    regret_a = regret_a[:min_len]
    regret_b = regret_b[:min_len]
    
    # Compute area between curves
    area_between = np.abs(np.array(regret_a) - np.array(regret_b)).sum()
    
    # Normalize by total area under both curves
    total_area = (np.array(regret_a).sum() + np.array(regret_b).sum())
    
    if total_area == 0:
        return 0.0
    
    normalized_divergence = area_between / total_area
    
    return normalized_divergence


def compute_jt_trajectory_divergence(jt_trajectory_a: List[Dict[str, float]], 
                                     jt_trajectory_b: List[Dict[str, float]]) -> float:
    """
    Compute divergence in Joint Trajectory (JT) evolution between two policies.
    
    Measures how different the JT component evolution is over time.
    JT components: mastery, transfer, challenge, uncertainty, zpd
    
    Args:
        jt_trajectory_a: List of JT state dictionaries for policy A
        jt_trajectory_b: List of JT state dictionaries for policy B
        
    Returns:
        Normalized JT trajectory divergence (0 = identical, higher = more different)
    """
    if not jt_trajectory_a and not jt_trajectory_b:
        return 0.0
    
    if not jt_trajectory_a or not jt_trajectory_b:
        return 1.0
    
    # Ensure same length
    min_len = min(len(jt_trajectory_a), len(jt_trajectory_b))
    jt_trajectory_a = jt_trajectory_a[:min_len]
    jt_trajectory_b = jt_trajectory_b[:min_len]
    
    # Compute Euclidean distance between JT vectors at each timestep
    divergences = []
    for jt_a, jt_b in zip(jt_trajectory_a, jt_trajectory_b):
        # Extract JT components (mastery, transfer, challenge, uncertainty, zpd)
        components = ['mastery', 'transfer', 'challenge', 'uncertainty', 'zpd']
        
        vector_a = np.array([jt_a.get(comp, 0.0) for comp in components])
        vector_b = np.array([jt_b.get(comp, 0.0) for comp in components])
        
        distance = euclidean(vector_a, vector_b)
        divergences.append(distance)
    
    # Average divergence across timesteps
    avg_divergence = np.mean(divergences)
    
    # Normalize by maximum possible distance (sqrt(5) since 5 components)
    max_distance = np.sqrt(5.0)
    normalized_divergence = avg_divergence / max_distance
    
    return normalized_divergence


def compute_comprehensive_divergence(trajectory_a: List[str],
                                    trajectory_b: List[str],
                                    distribution_a: Dict[str, float],
                                    distribution_b: Dict[str, float],
                                    regret_a: List[float],
                                    regret_b: List[float],
                                    jt_trajectory_a: List[Dict[str, float]],
                                    jt_trajectory_b: List[Dict[str, float]],
                                    weights: Optional[Dict[str, float]] = None) -> Dict[str, float]:
    """
    Compute comprehensive behavioral divergence across all metrics.
    
    Args:
        trajectory_a, trajectory_b: Concept selection sequences
        distribution_a, distribution_b: Action selection distributions
        regret_a, regret_b: Cumulative regret values
        jt_trajectory_a, jt_trajectory_b: JT evolution trajectories
        weights: Optional weights for each metric (default: equal weights)
        
    Returns:
        Dictionary containing all divergence metrics and weighted average
    """
    if weights is None:
        weights = {
            'trajectory': 0.25,
            'kl_divergence': 0.25,
            'regret': 0.25,
            'jt_trajectory': 0.25
        }
    
    # Compute individual metrics
    trajectory_div = compute_trajectory_divergence(trajectory_a, trajectory_b)
    kl_div = compute_kl_divergence(distribution_a, distribution_b)
    regret_div = compute_regret_divergence(regret_a, regret_b)
    jt_div = compute_jt_trajectory_divergence(jt_trajectory_a, jt_trajectory_b)
    
    # Compute weighted average
    weighted_divergence = (
        weights['trajectory'] * trajectory_div +
        weights['kl_divergence'] * kl_div +
        weights['regret'] * regret_div +
        weights['jt_trajectory'] * jt_div
    )
    
    return {
        'trajectory_divergence': trajectory_div,
        'kl_divergence': kl_div,
        'regret_divergence': regret_div,
        'jt_trajectory_divergence': jt_div,
        'weighted_divergence': weighted_divergence
    }


def format_divergence_report(divergence_metrics: Dict[str, float]) -> str:
    """
    Format divergence metrics as a readable report.
    
    Args:
        divergence_metrics: Dictionary of divergence metrics
        
    Returns:
        Formatted report string
    """
    report = "Behavioral Divergence Report\n"
    report += "=" * 50 + "\n"
    
    for metric, value in divergence_metrics.items():
        if metric == 'weighted_divergence':
            report += f"\n{metric}: {value:.4f}\n"
        else:
            report += f"{metric}: {value:.4f}\n"
    
    return report
