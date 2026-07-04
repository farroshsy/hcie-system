"""
Adaptive Transfer Learning Engine
Combines static, learned, and online transfer weights
"""

import logging
from typing import Dict, Optional
from datetime import datetime
import json
import numpy as np
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

try:
    from .transfer_learning_engine import TransferLearningEngine, ConceptDependency
except ImportError:
    from transfer_learning_engine import TransferLearningEngine, ConceptDependency

class AdaptiveTransferEngine(TransferLearningEngine):
    """Adaptive transfer engine that learns from real interactions"""
    
    def __init__(self, 
                 learning_rate: float = 0.1,
                 min_samples: int = 5,
                 smoothing_factor: float = 0.9,
                 max_history_size: int = 1000):
        """
        Initialize adaptive transfer engine
        
        Args:
            learning_rate: Rate at which to update transfer weights
            min_samples: Minimum samples before trusting learned weights
            smoothing_factor: Exponential smoothing for online updates
            max_history_size: Maximum interaction history to keep
        """
        super().__init__()
        
        self.learning_rate = learning_rate
        self.min_samples = min_samples
        self.smoothing_factor = smoothing_factor
        self.max_history_size = max_history_size
        
        # Online learning components
        self.learned_weights = defaultdict(lambda: defaultdict(float))
        self.weight_samples = defaultdict(lambda: defaultdict(int))
        self.interaction_history = deque(maxlen=max_history_size)
        self.concept_performance = defaultdict(lambda: defaultdict(list))
        
        # Adaptive beta per concept
        self.concept_betas = defaultdict(float)
        self.beta_learning_rate = 0.05
        
        logger.info("Adaptive Transfer Engine initialized")
    
    def load_learned_weights(self, weights_file: str):
        """Load pre-learned transfer weights"""
        try:
            with open(weights_file, 'r') as f:
                data = json.load(f)
            
            self.learned_weights = defaultdict(lambda: defaultdict(float))
            for source, targets in data['learned_weights'].items():
                for target, weight in targets.items():
                    self.learned_weights[source][target] = weight
            
            logger.info(f"Loaded {len(self.learned_weights)} learned transfer weights")
            
        except Exception as e:
            logger.error(f"Failed to load learned weights: {e}")
    
    def get_effective_transfer_weight(self, source_concept: str, target_concept: str) -> float:
        """
        Get effective transfer weight combining static, learned, and online components
        
        Args:
            source_concept: Source concept
            target_concept: Target concept
            
        Returns:
            Effective transfer weight
        """
        # Static weight (from database)
        static_weight = 0.0
        if source_concept in self.dependencies:
            for dep in self.dependencies[source_concept]:
                if dep.target_concept == target_concept:
                    static_weight = float(dep.transfer_weight)
                    break
        
        # Learned weight (from historical data)
        learned_weight = self.learned_weights[source_concept][target_concept]
        
        # Sample count for confidence
        sample_count = self.weight_samples[source_concept][target_concept]
        
        # Combine weights with confidence-based weighting
        if sample_count >= self.min_samples:
            # Trust learned weights more with more samples
            confidence = min(1.0, sample_count / (2 * self.min_samples))
            effective_weight = confidence * learned_weight + (1 - confidence) * static_weight
        else:
            # Use static weight with small learned adjustment
            effective_weight = static_weight + 0.1 * learned_weight
        
        return min(1.0, effective_weight)
    
    def record_interaction(self, 
                          user_id: str,
                          source_concept: str, 
                          target_concept: str,
                          mastery_before: float,
                          mastery_after: float,
                          beta: float,
                          correct: bool):
        """
        Record interaction for online learning
        
        Args:
            user_id: User identifier
            source_concept: Concept being learned
            target_concept: Next concept (potential transfer target)
            mastery_before: Mastery before interaction
            mastery_after: Mastery after interaction
            beta: Beta parameter used
            correct: Whether answer was correct
        """
        interaction = {
            'user_id': user_id,
            'source_concept': source_concept,
            'target_concept': target_concept,
            'mastery_before': mastery_before,
            'mastery_after': mastery_after,
            'mastery_change': mastery_after - mastery_before,
            'beta': beta,
            'correct': correct,
            'timestamp': datetime.now()
        }
        
        self.interaction_history.append(interaction)
        
        # Update concept performance tracking
        self.concept_performance[source_concept]['mastery_changes'].append(interaction['mastery_change'])
        self.concept_performance[source_concept]['betas'].append(beta)
        self.concept_performance[source_concept]['correct_rates'].append(1.0 if correct else 0.0)
        
        # Update adaptive beta for this concept
        self._update_concept_beta(source_concept)
    
    def _update_concept_beta(self, concept: str):
        """Update adaptive beta for a concept based on performance"""
        if len(self.concept_performance[concept]['mastery_changes']) < 5:
            return  # Not enough data
        
        mastery_changes = self.concept_performance[concept]['mastery_changes'][-10:]  # Last 10
        betas = self.concept_performance[concept]['betas'][-10:]
        correct_rates = self.concept_performance[concept]['correct_rates'][-10:]
        
        # Calculate performance metrics
        avg_mastery_change = np.mean(mastery_changes)
        avg_correct_rate = np.mean(correct_rates)
        
        # Find best performing beta in recent history
        beta_performance = defaultdict(list)
        for i, beta in enumerate(betas):
            performance = mastery_changes[i] * (1.0 + correct_rates[i])  # Weight by correctness
            beta_performance[beta].append(performance)
        
        best_beta = 0.5  # Default
        best_performance = 0.0
        
        for beta, performances in beta_performance.items():
            avg_performance = np.mean(performances)
            if len(performances) >= 3 and avg_performance > best_performance:
                best_performance = avg_performance
                best_beta = beta
        
        # Update concept beta with smoothing
        current_beta = self.concept_betas[concept]
        self.concept_betas[concept] = (
            self.smoothing_factor * current_beta + 
            (1 - self.smoothing_factor) * best_beta
        )
    
    def update_transfer_weights_online(self):
        """Update transfer weights based on recent interactions"""
        if len(self.interaction_history) < 10:
            return  # Not enough data
        
        # Process recent interactions for transfer learning
        recent_interactions = list(self.interaction_history)[-50:]  # Last 50
        
        for interaction in recent_interactions:
            source = interaction['source_concept']
            target = interaction['target_concept']
            mastery_change = interaction['mastery_change']
            
            # Only update for meaningful learning events
            if abs(mastery_change) > 0.001 and source != target:
                # Calculate transfer effect
                transfer_effect = self._calculate_transfer_effect(interaction)
                
                if transfer_effect > 0.001:  # Positive transfer
                    # More aggressive learning (your current one is too slow)
                    learning_rate = 0.3

                    current_weight = self.learned_weights[source][target]
                    new_weight = (
                        (1 - learning_rate) * current_weight +
                        learning_rate * transfer_effect
                    )
                    
                    self.learned_weights[source][target] = new_weight
                    self.weight_samples[source][target] += 1
        
        logger.info(f"Updated transfer weights based on {len(recent_interactions)} recent interactions")
    
    def _calculate_transfer_effect(self, interaction: Dict) -> float:
        """
        Improved transfer calculation with realistic scaling
        """
        mastery_change = interaction['mastery_change']
        beta = interaction['beta']
        correct = interaction['correct']

        # Base signal
        base = abs(mastery_change)

        # Stronger scaling factors
        mastery_factor = max(0.3, interaction['mastery_after'])
        beta_factor = 0.5 + beta
        correctness_factor = 1.5 if correct else 0.7

        # Amplified transfer signal
        transfer = base * (1 + 2 * mastery_factor) * beta_factor * correctness_factor

        # 🔥 MAXIMUM TRANSFER: Allow much stronger transfer signals
        return min(0.2, max(0.0, transfer))
    
    def get_adaptive_beta(self, concept: str) -> float:
        """Get adaptive beta for a concept"""
        if concept in self.concept_betas:
            return self.concept_betas[concept]
        return 0.5  # Default beta
    
    def calculate_transfer_with_adaptive_weights(self, 
                                                source_concept: str, 
                                                target_concept: str,
                                                mastery_change: float,
                                                beta: Optional[float] = None) -> float:
        """
        Calculate transfer amount using adaptive weights
        
        Args:
            source_concept: Source concept
            target_concept: Target concept
            mastery_change: Amount of mastery change in source
            beta: Beta parameter (optional, will use adaptive if not provided)
            
        Returns:
            Transfer amount to apply to target
        """
        # Get effective transfer weight
        effective_weight = self.get_effective_transfer_weight(source_concept, target_concept)
        
        if effective_weight == 0.0:
            return 0.0
        
        # Use adaptive beta if not provided
        if beta is None:
            beta = self.get_adaptive_beta(source_concept)
        
        # Calculate base transfer
        base_transfer = effective_weight * abs(mastery_change)
        
        # Apply dependency type modifiers (from static weights)
        type_modifier = 1.0
        if source_concept in self.dependencies:
            for dep in self.dependencies[source_concept]:
                if dep.target_concept == target_concept:
                    if dep.dependency_type == 'prerequisite':
                        type_modifier = 1.2
                    elif dep.dependency_type == 'related':
                        type_modifier = 1.0
                    elif dep.dependency_type == 'advanced':
                        type_modifier = 0.8
                    break
        
        # Apply confidence modifiers
        confidence_modifier = 1.0
        sample_count = self.weight_samples[source_concept][target_concept]
        if sample_count >= self.min_samples:
            confidence_modifier = min(1.2, 1.0 + sample_count / (2 * self.min_samples))
        
        transfer_amount = base_transfer * type_modifier * confidence_modifier * beta
        
        # Apply limits with reasonable upper bound
        max_transfer = min(0.2, self.max_transfer_boost * abs(mastery_change))
        transfer_amount = min(transfer_amount, max_transfer)
        
        return transfer_amount
    
    def get_transfer_statistics(self) -> Dict:
        """Get comprehensive transfer statistics"""
        stats = {
            'total_learned_weights': sum(len(targets) for targets in self.learned_weights.values()),
            'total_interactions': len(self.interaction_history),
            'concepts_with_adaptive_beta': len(self.concept_betas),
            'avg_beta': np.mean(list(self.concept_betas.values())) if self.concept_betas else 0.5,
            'weight_sample_distribution': {},
            'recent_transfer_effects': []
        }
        
        # Sample distribution
        sample_counts = []
        for source, targets in self.weight_samples.items():
            for target, count in targets.items():
                sample_counts.append(count)
        
        if sample_counts:
            stats['weight_sample_distribution'] = {
                'min': min(sample_counts),
                'max': max(sample_counts),
                'mean': np.mean(sample_counts),
                'median': np.median(sample_counts)
            }
        
        # Recent transfer effects
        recent_interactions = list(self.interaction_history)[-10:]
        for interaction in recent_interactions:
            if interaction['mastery_change'] > 0.001:
                transfer_effect = self._calculate_transfer_effect(interaction)
                stats['recent_transfer_effects'].append({
                    'source': interaction['source_concept'],
                    'target': interaction['target_concept'],
                    'effect': transfer_effect,
                    'beta': interaction['beta']
                })
        
        return stats
    
    def export_adaptive_state(self, filepath: str):
        """Export adaptive learning state"""
        state = {
            'learned_weights': dict(self.learned_weights),
            'weight_samples': dict(self.weight_samples),
            'concept_betas': dict(self.concept_betas),
            'statistics': self.get_transfer_statistics(),
            'metadata': {
                'exported_at': datetime.now().isoformat(),
                'learning_rate': self.learning_rate,
                'smoothing_factor': self.smoothing_factor,
                'min_samples': self.min_samples
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)
        
        logger.info(f"Adaptive state exported to {filepath}")
    
    def import_adaptive_state(self, filepath: str):
        """Import adaptive learning state"""
        try:
            with open(filepath, 'r') as f:
                state = json.load(f)
            
            self.learned_weights = defaultdict(lambda: defaultdict(float), state['learned_weights'])
            self.weight_samples = defaultdict(lambda: defaultdict(int), state['weight_samples'])
            self.concept_betas = defaultdict(float, state['concept_betas'])
            
            logger.info(f"Adaptive state imported from {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to import adaptive state: {e}")
