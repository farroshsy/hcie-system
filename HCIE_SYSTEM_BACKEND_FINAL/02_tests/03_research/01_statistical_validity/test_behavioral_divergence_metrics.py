"""
Test behavioral divergence metrics

Verifies that behavioral divergence metrics correctly measure actual behavioral
differences between policies, not just configuration differences.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.experiment.behavioral_divergence import (
    compute_trajectory_divergence,
    compute_kl_divergence,
    compute_regret_divergence,
    compute_jt_trajectory_divergence,
    compute_comprehensive_divergence,
    format_divergence_report
)


def test_trajectory_divergence():
    """Test trajectory divergence metric"""
    print("🧪 Testing Trajectory Divergence")
    print("=" * 60)
    
    # Test 1: Identical trajectories
    trajectory_a = ["concept_001", "concept_002", "concept_003"]
    trajectory_b = ["concept_001", "concept_002", "concept_003"]
    div = compute_trajectory_divergence(trajectory_a, trajectory_b)
    assert div == 0.0, "Identical trajectories should have 0 divergence"
    print(f"  ✅ Identical trajectories: {div:.4f}")
    
    # Test 2: Completely different trajectories
    trajectory_a = ["concept_001", "concept_002", "concept_003"]
    trajectory_b = ["concept_004", "concept_005", "concept_006"]
    div = compute_trajectory_divergence(trajectory_a, trajectory_b)
    assert div == 1.0, "Completely different trajectories should have 1.0 divergence"
    print(f"  ✅ Completely different trajectories: {div:.4f}")
    
    # Test 3: Partially different trajectories
    trajectory_a = ["concept_001", "concept_002", "concept_003"]
    trajectory_b = ["concept_001", "concept_005", "concept_003"]
    div = compute_trajectory_divergence(trajectory_a, trajectory_b)
    assert 0 < div < 1, "Partially different trajectories should have 0 < divergence < 1"
    print(f"  ✅ Partially different trajectories: {div:.4f}")
    
    print("✅ Trajectory divergence tests passed\n")
    return True


def test_kl_divergence():
    """Test KL divergence metric"""
    print("🧪 Testing KL Divergence")
    print("=" * 60)
    
    # Test 1: Identical distributions
    dist_a = {"concept_001": 0.5, "concept_002": 0.5}
    dist_b = {"concept_001": 0.5, "concept_002": 0.5}
    div = compute_kl_divergence(dist_a, dist_b)
    assert div < 0.01, "Identical distributions should have near-zero divergence"
    print(f"  ✅ Identical distributions: {div:.4f}")
    
    # Test 2: Completely different distributions
    dist_a = {"concept_001": 1.0, "concept_002": 0.0}
    dist_b = {"concept_001": 0.0, "concept_002": 1.0}
    div = compute_kl_divergence(dist_a, dist_b)
    assert div > 0, "Different distributions should have positive divergence"
    print(f"  ✅ Completely different distributions: {div:.4f}")
    
    # Test 3: Partially different distributions
    dist_a = {"concept_001": 0.7, "concept_002": 0.3}
    dist_b = {"concept_001": 0.5, "concept_002": 0.5}
    div = compute_kl_divergence(dist_a, dist_b)
    assert div > 0, "Partially different distributions should have positive divergence"
    print(f"  ✅ Partially different distributions: {div:.4f}")
    
    print("✅ KL divergence tests passed\n")
    return True


def test_regret_divergence():
    """Test regret divergence metric"""
    print("🧪 Testing Regret Divergence")
    print("=" * 60)
    
    # Test 1: Identical regret curves
    regret_a = [1.0, 2.0, 3.0, 4.0]
    regret_b = [1.0, 2.0, 3.0, 4.0]
    div = compute_regret_divergence(regret_a, regret_b)
    assert div == 0.0, "Identical regret curves should have 0 divergence"
    print(f"  ✅ Identical regret curves: {div:.4f}")
    
    # Test 2: Different regret curves
    regret_a = [1.0, 2.0, 3.0, 4.0]
    regret_b = [2.0, 4.0, 6.0, 8.0]
    div = compute_regret_divergence(regret_a, regret_b)
    assert div > 0, "Different regret curves should have positive divergence"
    print(f"  ✅ Different regret curves: {div:.4f}")
    
    # Test 3: Partially different regret curves
    regret_a = [1.0, 2.0, 3.0, 4.0]
    regret_b = [1.0, 3.0, 3.0, 5.0]
    div = compute_regret_divergence(regret_a, regret_b)
    assert div > 0, "Partially different regret curves should have positive divergence"
    print(f"  ✅ Partially different regret curves: {div:.4f}")
    
    print("✅ Regret divergence tests passed\n")
    return True


def test_jt_trajectory_divergence():
    """Test JT trajectory divergence metric"""
    print("🧪 Testing JT Trajectory Divergence")
    print("=" * 60)
    
    # Test 1: Identical JT trajectories
    jt_a = [
        {"mastery": 0.5, "transfer": 0.3, "challenge": 0.4, "uncertainty": 0.6, "zpd": 0.5},
        {"mastery": 0.6, "transfer": 0.4, "challenge": 0.5, "uncertainty": 0.5, "zpd": 0.6}
    ]
    jt_b = [
        {"mastery": 0.5, "transfer": 0.3, "challenge": 0.4, "uncertainty": 0.6, "zpd": 0.5},
        {"mastery": 0.6, "transfer": 0.4, "challenge": 0.5, "uncertainty": 0.5, "zpd": 0.6}
    ]
    div = compute_jt_trajectory_divergence(jt_a, jt_b)
    assert div < 0.01, "Identical JT trajectories should have near-zero divergence"
    print(f"  ✅ Identical JT trajectories: {div:.4f}")
    
    # Test 2: Different JT trajectories
    jt_a = [
        {"mastery": 0.5, "transfer": 0.3, "challenge": 0.4, "uncertainty": 0.6, "zpd": 0.5},
        {"mastery": 0.6, "transfer": 0.4, "challenge": 0.5, "uncertainty": 0.5, "zpd": 0.6}
    ]
    jt_b = [
        {"mastery": 0.8, "transfer": 0.7, "challenge": 0.8, "uncertainty": 0.2, "zpd": 0.9},
        {"mastery": 0.9, "transfer": 0.8, "challenge": 0.9, "uncertainty": 0.1, "zpd": 0.95}
    ]
    div = compute_jt_trajectory_divergence(jt_a, jt_b)
    assert div > 0, "Different JT trajectories should have positive divergence"
    print(f"  ✅ Different JT trajectories: {div:.4f}")
    
    print("✅ JT trajectory divergence tests passed\n")
    return True


def test_comprehensive_divergence():
    """Test comprehensive divergence metric"""
    print("🧪 Testing Comprehensive Divergence")
    print("=" * 60)
    
    # Test comprehensive divergence with sample data
    trajectory_a = ["concept_001", "concept_002", "concept_003"]
    trajectory_b = ["concept_001", "concept_005", "concept_003"]
    
    dist_a = {"concept_001": 0.5, "concept_002": 0.3, "concept_003": 0.2}
    dist_b = {"concept_001": 0.4, "concept_002": 0.4, "concept_003": 0.2}
    
    regret_a = [1.0, 2.0, 3.0]
    regret_b = [1.0, 3.0, 4.0]
    
    jt_a = [
        {"mastery": 0.5, "transfer": 0.3, "challenge": 0.4, "uncertainty": 0.6, "zpd": 0.5}
    ]
    jt_b = [
        {"mastery": 0.6, "transfer": 0.4, "challenge": 0.5, "uncertainty": 0.5, "zpd": 0.6}
    ]
    
    metrics = compute_comprehensive_divergence(
        trajectory_a, trajectory_b,
        dist_a, dist_b,
        regret_a, regret_b,
        jt_a, jt_b
    )
    
    print(f"  ✅ Trajectory divergence: {metrics['trajectory_divergence']:.4f}")
    print(f"  ✅ KL divergence: {metrics['kl_divergence']:.4f}")
    print(f"  ✅ Regret divergence: {metrics['regret_divergence']:.4f}")
    print(f"  ✅ JT trajectory divergence: {metrics['jt_trajectory_divergence']:.4f}")
    print(f"  ✅ Weighted divergence: {metrics['weighted_divergence']:.4f}")
    
    # Verify all metrics are present
    assert 'trajectory_divergence' in metrics
    assert 'kl_divergence' in metrics
    assert 'regret_divergence' in metrics
    assert 'jt_trajectory_divergence' in metrics
    assert 'weighted_divergence' in metrics
    
    # Verify weighted divergence is within bounds
    assert 0 <= metrics['weighted_divergence'] <= 1
    
    print("✅ Comprehensive divergence tests passed\n")
    return True


def test_format_divergence_report():
    """Test divergence report formatting"""
    print("🧪 Testing Divergence Report Formatting")
    print("=" * 60)
    
    metrics = {
        'trajectory_divergence': 0.33,
        'kl_divergence': 0.25,
        'regret_divergence': 0.50,
        'jt_trajectory_divergence': 0.40,
        'weighted_divergence': 0.37
    }
    
    report = format_divergence_report(metrics)
    print(report)
    
    # Verify report contains all metrics
    assert 'trajectory_divergence' in report
    assert 'kl_divergence' in report
    assert 'regret_divergence' in report
    assert 'jt_trajectory_divergence' in report
    assert 'weighted_divergence' in report
    
    print("✅ Divergence report formatting tests passed\n")
    return True


def test_all():
    """Run all behavioral divergence tests"""
    print("🧪 Behavioral Divergence Metrics Tests")
    print("=" * 60)
    
    try:
        test_trajectory_divergence()
        test_kl_divergence()
        test_regret_divergence()
        test_jt_trajectory_divergence()
        test_comprehensive_divergence()
        test_format_divergence_report()
        
        print("=" * 60)
        print("✅ All behavioral divergence metrics tests passed")
        print("=" * 60)
        print("\n📊 Summary:")
        print("  - Trajectory divergence: Measures concept selection sequence differences")
        print("  - KL divergence: Measures distributional differences in action selection")
        print("  - Regret divergence: Measures cumulative regret differences")
        print("  - JT trajectory divergence: Measures Joint Trajectory evolution differences")
        print("  - Comprehensive divergence: Weighted combination of all metrics")
        
        return True
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_all()
