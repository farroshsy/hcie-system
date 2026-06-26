"""
Research-Grade Mathematical Logging System

Provides mathematically interpretable logs for research validation:
- Every learning decision with mathematical reasoning
- Ensemble variance calculations with formulas
- Policy effectiveness with multipliers and weights
- Transfer learning with dependency graphs
- ZPD alignment with distance calculations
- System performance with approximation gap analysis

All logs are structured for research paper inclusion and statistical analysis.
"""

import logging
import json
import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class MathematicalLogEntry:
    """Research-grade log entry with mathematical precision"""
    timestamp: str
    user_id: str
    concept: str
    event_type: str
    
    # Mathematical state
    mastery_before: float
    mastery_after: float
    learning_gain: float
    uncertainty_before: float
    uncertainty_after: float
    
    # Ensemble calculations
    lyapunov_mastery: float
    bayesian_mastery: float
    kalman_mastery: float
    ensemble_variance: float
    ensemble_weights: List[float]
    
    # Policy calculations
    policy: str
    policy_multiplier: float
    base_learning_rate: float
    adjusted_learning_rate: float
    
    # Transfer calculations
    transfer_amount: float
    transfer_sources: List[str]
    transfer_efficiency: float
    dependency_weights: Dict[str, float]
    
    # ZPD calculations
    difficulty: float
    zpd_target: float
    zpd_alignment_error: float
    zpd_score: float
    
    # System performance
    processing_delay: float
    approximation_gap: float
    consistency_lag: float
    
    # Mathematical formulas used
    formulas: List[str]
    
    # Event identity for deduplication
    event_id: str
    interaction_id: str
    
    # Research metadata
    experiment_id: Optional[str] = None
    group_assignment: Optional[str] = None


class ResearchLogger:
    """
    Research-grade logging for mathematical interpretability
    
    Every log entry includes:
    1. Exact mathematical formulas used
    2. All intermediate calculations
    3. Parameter values and sources
    4. Statistical significance indicators
    """
    
    def __init__(self, log_file: str = "research_logs.json"):
        self.log_file = log_file
        self.log_entries = []
        
        # Research configuration
        self.formulas_registry = {
            "lyapunov_update": "m_{t+1} = m_t + η(y - m_t) - λm_t + ε",
            "bayesian_update": "α' = α + y, β' = β + (1-y)",
            "kalman_update": "μ_{t+1} = μ_t + K(y - μ_t), K = σ²/(σ² + σ_obs²)",
            "ensemble_weighted": "M_ensemble = Σ_i w_i * M_i",
            "policy_multiplier": "η_adj = η_base * multiplier_policy",
            "transfer_amount": "T = η_gain * confidence * weight_dep * type_modifier",
            "zpd_alignment": "zpd_score = 1 - |mastery - (mastery + 0.1)|",
            "approximation_gap": "Δ = ||ideal(S_t) - implemented(S_t)||"
        }
    
    def log(self, entry_type: str, data: Dict[str, Any]) -> None:
        """
        Generic log method for research data
        
        Args:
            entry_type: Type of log entry (e.g., "governance_metrics")
            data: Dictionary of data to log
        """
        # Store as a simple dictionary entry
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "entry_type": entry_type,
            "data": data
        }
        self.log_entries.append(log_entry)
        
        # Write to file
        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(log_entry, default=str) + '\n')
        except Exception as e:
            logger.error(f"Failed to write research log: {e}")
    
    def log_learning_event(self, log_entry: MathematicalLogEntry) -> None:
        """
        Log a complete learning event with mathematical precision
        
        Args:
            log_entry: Complete mathematical log entry
        """
        # Add mathematical analysis
        log_entry = self._add_mathematical_analysis(log_entry)
        
        # Store entry
        self.log_entries.append(log_entry)
        
        # Write to file
        self._write_to_file(log_entry)
        
        # Log to console
        self._log_to_console(log_entry)
    
    def _add_mathematical_analysis(self, entry: MathematicalLogEntry) -> MathematicalLogEntry:
        """Add mathematical analysis and interpretations"""
        
        # Calculate learning rate efficiency
        learning_efficiency = entry.learning_gain / entry.adjusted_learning_rate if entry.adjusted_learning_rate > 0 else 0
        
        # Calculate ensemble agreement
        ensemble_std = np.sqrt(entry.ensemble_variance)
        ensemble_agreement = 1.0 - min(ensemble_std, 1.0)
        
        # Calculate transfer effectiveness
        transfer_effectiveness = entry.transfer_efficiency * entry.transfer_amount if entry.transfer_amount > 0 else 0
        
        # Calculate ZPD optimality
        zpd_optimal = 1.0 if entry.zpd_alignment_error < 0.05 else (0.5 if entry.zpd_alignment_error < 0.1 else 0.0)
        
        # Calculate system quality score
        system_quality = (
            0.3 * ensemble_agreement +
            0.2 * learning_efficiency +
            0.2 * transfer_effectiveness +
            0.2 * zpd_optimal +
            0.1 * (1.0 - min(entry.approximation_gap, 1.0))
        )
        
        # Add research interpretations
        research_insights = [
            f"Learning efficiency: {learning_efficiency:.4f} (gain/rate ratio)",
            f"Ensemble agreement: {ensemble_agreement:.4f} (lower variance = higher agreement)",
            f"Transfer effectiveness: {transfer_effectiveness:.4f} (efficiency × amount)",
            f"ZPD optimality: {zpd_optimal:.1f} (error < 0.05 = optimal)",
            f"System quality: {system_quality:.4f} (overall performance score)"
        ]
        
        # Store insights in entry (as additional field)
        entry.research_insights = research_insights
        entry.system_quality = system_quality
        
        return entry
    
    def _write_to_file(self, entry: MathematicalLogEntry) -> None:
        """Write log entry to research file"""
        try:
            with open(self.log_file, 'a') as f:
                # Convert to dict and add formula explanations
                log_dict = asdict(entry)
                log_dict['formula_explanations'] = self._get_formula_explanations(entry)
                
                f.write(json.dumps(log_dict, default=str) + '\n')
        except Exception as e:
            logger.error(f"Failed to write research log: {e}")
    
    def _log_to_console(self, entry: MathematicalLogEntry) -> None:
        """Log mathematical details to console for research"""
        
        print(f"\n{'='*80}")
        print(f"🔬 RESEARCH LOG: {entry.event_type.upper()}")
        print(f"{'='*80}")
        print(f"📅 Timestamp: {entry.timestamp}")
        print(f"👤 User: {entry.user_id}")
        print(f"🧠 Concept: {entry.concept}")
        
        print("\n📊 LEARNING STATE:")
        print(f"   Mastery: {entry.mastery_before:.4f} → {entry.mastery_after:.4f} (Δ{entry.learning_gain:+.4f})")
        print(f"   Uncertainty: {entry.uncertainty_before:.4f} → {entry.uncertainty_after:.4f}")
        
        print("\n🎭 ENSEMBLE CALCULATIONS:")
        print(f"   Lyapunov: {entry.lyapunov_mastery:.4f}")
        print(f"   Bayesian: {entry.bayesian_mastery:.4f}")
        print(f"   Kalman: {entry.kalman_mastery:.4f}")
        print(f"   Variance: {entry.ensemble_variance:.4f}")
        print(f"   Weights: [{', '.join([f'{w:.3f}' for w in entry.ensemble_weights])}]")
        
        print("\n🎛 POLICY EFFECTIVENESS:")
        print(f"   Policy: {entry.policy.upper()}")
        print(f"   Base Rate: {entry.base_learning_rate:.4f}")
        print(f"   Multiplier: {entry.policy_multiplier:.2f}x")
        print(f"   Adjusted Rate: {entry.adjusted_learning_rate:.4f}")
        
        print("\n🔄 TRANSFER LEARNING:")
        print(f"   Transfer Amount: {entry.transfer_amount:.4f}")
        print(f"   Transfer Efficiency: {entry.transfer_efficiency:.3f}")
        print(f"   Sources: {entry.transfer_sources}")
        print(f"   Dependencies: {entry.dependency_weights}")
        
        print("\n🎯 ZPD ALIGNMENT:")
        print(f"   Difficulty: {entry.difficulty:.3f}")
        print(f"   ZPD Target: {entry.zpd_target:.3f}")
        print(f"   Alignment Error: {entry.zpd_alignment_error:.3f}")
        print(f"   ZPD Score: {entry.zpd_score:.3f}")
        
        print("\n⚙️ SYSTEM PERFORMANCE:")
        print(f"   Processing Delay: {entry.processing_delay:.3f}s")
        print(f"   Approximation Gap: {entry.approximation_gap:.3f}")
        print(f"   Consistency Lag: {entry.consistency_lag:.3f}s")
        
        print("\n🧮 MATHEMATICAL FORMULAS:")
        for formula in entry.formulas:
            print(f"   • {formula}")
        
        if hasattr(entry, 'research_insights'):
            print("\n💡 RESEARCH INSIGHTS:")
            for insight in entry.research_insights:
                print(f"   • {insight}")
        
        print(f"{'='*80}\n")
    
    def _get_formula_explanations(self, entry: MathematicalLogEntry) -> Dict[str, str]:
        """Get detailed explanations for formulas used"""
        explanations = {}
        
        for formula_key in entry.formulas:
            if formula_key in self.formulas_registry:
                formula = self.formulas_registry[formula_key]
                explanations[formula_key] = {
                    "formula": formula,
                    "explanation": self._explain_formula(formula_key, formula)
                }
        
        return explanations
    
    def _explain_formula(self, key: str, formula: str) -> str:
        """Provide mathematical explanation for formula"""
        explanations = {
            "lyapunov_update": "Lyapunov stability-based learning: η=learning rate, λ=decay rate, ε=noise",
            "bayesian_update": "Beta-binomial conjugate update: α=successes, β=failures, y=observation",
            "kalman_update": "Kalman filter: K=Kalman gain, μ=mean, σ²=variance, σ_obs²=observation variance",
            "ensemble_weighted": "Weighted average of ensemble predictions with confidence-based weights",
            "policy_multiplier": "Policy-specific learning rate adjustment (HCIE=1.12x, Heuristic=1.05x, Static=1.0x, Random=0.97x)",
            "transfer_amount": "Transfer learning: combines learning gain, confidence, dependency weights, and type modifiers",
            "zpd_alignment": "Zone of Proximal Development: optimal difficulty = mastery + 0.1",
            "approximation_gap": "Distance between ideal unified state and implemented distributed state"
        }
        
        return explanations.get(key, "Mathematical formula for learning system component")
    
    def get_research_summary(self) -> Dict[str, Any]:
        """Generate research summary for paper inclusion"""
        
        if not self.log_entries:
            return {"status": "no_data", "message": "No log entries available"}
        
        # Calculate aggregate statistics
        total_events = len(self.log_entries)
        
        # Learning statistics
        learning_gains = [e.learning_gain for e in self.log_entries]
        avg_learning_gain = np.mean(learning_gains)
        learning_gain_std = np.std(learning_gains)
        
        # Ensemble statistics
        ensemble_variances = [e.ensemble_variance for e in self.log_entries]
        avg_ensemble_variance = np.mean(ensemble_variances)
        
        # Policy statistics
        policy_multipliers = [e.policy_multiplier for e in self.log_entries]
        avg_policy_multiplier = np.mean(policy_multipliers)
        
        # Transfer statistics
        transfer_amounts = [e.transfer_amount for e in self.log_entries]
        avg_transfer_amount = np.mean(transfer_amounts)
        
        # ZPD statistics
        zpd_scores = [e.zpd_score for e in self.log_entries]
        avg_zpd_score = np.mean(zpd_scores)
        
        # System statistics
        approximation_gaps = [e.approximation_gap for e in self.log_entries]
        avg_approximation_gap = np.mean(approximation_gaps)
        
        # Quality scores
        system_qualities = [getattr(e, 'system_quality', 0.0) for e in self.log_entries]
        avg_system_quality = np.mean(system_qualities)
        
        return {
            "research_summary": {
                "total_events": total_events,
                "time_period": {
                    "start": self.log_entries[0].timestamp,
                    "end": self.log_entries[-1].timestamp
                }
            },
            "learning_performance": {
                "average_learning_gain": avg_learning_gain,
                "learning_gain_std": learning_gain_std,
                "learning_efficiency": avg_learning_gain / avg_policy_multiplier if avg_policy_multiplier > 0 else 0
            },
            "ensemble_analysis": {
                "average_variance": avg_ensemble_variance,
                "ensemble_agreement": 1.0 - min(np.sqrt(avg_ensemble_variance), 1.0)
            },
            "policy_effectiveness": {
                "average_multiplier": avg_policy_multiplier,
                "policy_distribution": self._get_policy_distribution()
            },
            "transfer_analysis": {
                "average_transfer_amount": avg_transfer_amount,
                "transfer_coverage": len([e for e in self.log_entries if e.transfer_amount > 0]) / total_events
            },
            "zpd_analysis": {
                "average_zpd_score": avg_zpd_score,
                "zpd_optimality_rate": len([e for e in self.log_entries if e.zpd_score > 0.9]) / total_events
            },
            "system_performance": {
                "average_approximation_gap": avg_approximation_gap,
                "system_quality_score": avg_system_quality
            },
            "statistical_significance": {
                "sample_size": total_events,
                "confidence_level": 0.95,
                "margin_of_error": 1.96 * learning_gain_std / np.sqrt(total_events)
            }
        }
    
    def _get_policy_distribution(self) -> Dict[str, float]:
        """Calculate distribution of policies used"""
        policy_counts = {}
        for entry in self.log_entries:
            policy = entry.policy
            policy_counts[policy] = policy_counts.get(policy, 0) + 1
        
        total = len(self.log_entries)
        return {policy: count/total for policy, count in policy_counts.items()}
    
    def export_for_paper(self, filename: str = "research_data.json") -> None:
        """Export data formatted for research paper inclusion"""
        
        research_data = {
            "metadata": {
                "system": "HCIE Adaptive Learning System",
                "version": "2.0",
                "export_date": datetime.now().isoformat(),
                "description": "Mathematically interpretable learning system logs"
            },
            "summary": self.get_research_summary(),
            "detailed_logs": [asdict(entry) for entry in self.log_entries[-100:]],  # Last 100 entries
            "formulas": self.formulas_registry,
            "statistical_analysis": self._generate_statistical_analysis()
        }
        
        with open(filename, 'w') as f:
            json.dump(research_data, f, default=str, indent=2)
        
        print(f"📄 Research data exported to {filename}")
    
    def _generate_statistical_analysis(self) -> Dict[str, Any]:
        """Generate statistical analysis for research paper"""
        
        if len(self.log_entries) < 30:
            return {"status": "insufficient_data", "message": "Need at least 30 samples for statistical analysis"}
        
        # Learning gains analysis
        learning_gains = np.array([e.learning_gain for e in self.log_entries])
        
        # Perform t-test against baseline (假设baseline = 0.05)
        from scipy import stats
        baseline_gain = 0.05
        t_stat, p_value = stats.ttest_1samp(learning_gains, baseline_gain)
        
        # Effect size (Cohen's d)
        effect_size = (np.mean(learning_gains) - baseline_gain) / np.std(learning_gains)
        
        # Confidence interval
        mean_gain = np.mean(learning_gains)
        std_error = stats.sem(learning_gains)
        confidence_interval = (
            mean_gain - 1.96 * std_error,
            mean_gain + 1.96 * std_error
        )
        
        return {
            "hypothesis_test": {
                "null_hypothesis": "Learning gain = baseline (0.05)",
                "alternative_hypothesis": "Learning gain > baseline",
                "t_statistic": t_stat,
                "p_value": p_value,
                "statistically_significant": p_value < 0.05,
                "significance_level": 0.05
            },
            "effect_size": {
                "cohens_d": effect_size,
                "interpretation": self._interpret_effect_size(effect_size)
            },
            "confidence_interval": {
                "level": 0.95,
                "lower_bound": confidence_interval[0],
                "upper_bound": confidence_interval[1],
                "mean": mean_gain
            },
            "sample_characteristics": {
                "sample_size": len(learning_gains),
                "mean": mean_gain,
                "standard_deviation": np.std(learning_gains),
                "standard_error": std_error,
                "min": np.min(learning_gains),
                "max": np.max(learning_gains)
            }
        }
    
    def _interpret_effect_size(self, cohens_d: float) -> str:
        """Interpret Cohen's d effect size"""
        abs_d = abs(cohens_d)
        
        if abs_d < 0.2:
            return "Negligible effect"
        elif abs_d < 0.5:
            return "Small effect"
        elif abs_d < 0.8:
            return "Medium effect"
        else:
            return "Large effect"


# Global research logger instance
research_logger = ResearchLogger()
