"""
Transfer-Aware Confidence-Weighted Learner
Extends the confidence-weighted learner with cross-concept transfer capabilities
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import numpy as np
from .confidence_weighted_learner import ConfidenceWeightedLearner
from ..transfer.transfer_learning_engine import TransferLearningEngine, TransferEvent

logger = logging.getLogger(__name__)

@dataclass
class TransferLearningUpdate:
    """Represents a transfer learning update"""
    user_id: str
    concept: str
    direct_mastery_change: float
    transferred_mastery_change: float
    total_mastery_change: float
    transfer_sources: Dict[str, float]
    confidence: float
    timestamp: str

class TransferAwareLearner(ConfidenceWeightedLearner):
    """
    Transfer-Aware Confidence-Weighted Learner
    
    Extends the base confidence-weighted learner with:
    1. Cross-concept skill transfer
    2. Shared latent skill space updates
    3. Transfer decay and forgetting
    4. Enhanced mastery tracking with transfer sources
    """
    
    def __init__(self, 
                 base_learning_rate: float = 0.1,
                 transfer_engine: Optional[TransferLearningEngine] = None,
                 transfer_weight: float = 0.8,  # Increased from 0.3
                 min_transfer_threshold: float = 0.0005,  # Lowered from 0.01
                 redis_store=None):
        """
        Initialize transfer-aware learner
        
        Args:
            base_learning_rate: Base learning rate for direct updates
            transfer_engine: Transfer learning engine instance
            transfer_weight: Weight given to transferred mastery
            min_transfer_threshold: Minimum transfer amount to apply
            redis_store: Redis store for persistent mastery storage
        """
        super().__init__(base_learning_rate)
        
        self.transfer_engine = transfer_engine or TransferLearningEngine()
        self.transfer_weight = transfer_weight
        self.min_transfer_threshold = min_transfer_threshold
        self.redis_store = redis_store
        
        # Add in-memory persistence for mastery state (backup)
        self.mastery_store = {}  # {(user_id, concept): mastery_value}
        logger.info("TransferAwareLearner initialized with Redis persistence")
        
        # Enhanced mastery tracking with transfer sources
        self.user_mastery_with_transfer: Dict[str, Dict[str, float]] = {}
        self.transfer_sources: Dict[str, Dict[str, List[str]]] = {}
        
        # Transfer learning history
        self.transfer_updates: List[TransferLearningUpdate] = []
        
        # Transfer learning analytics
        self.transfer_analytics = {
            "total_transfer_events": 0,
            "total_transferred_mastery": 0.0,
            "avg_transfer_per_event": 0.0,
            "most_transferred_concepts": {},
            "transfer_efficiency": {}
        }
        
        logger.info("Transfer-Aware Confidence-Weighted Learner initialized")
        
        # Initialize user_mastery for transfer learning
        self.user_mastery = {}
    
    # _preload_mastery method removed - Redis is now single source of truth
    
    def update_learning_with_transfer(self, 
                                  user_id: str, 
                                  concept: str, 
                                  interaction_data: Dict[str, Any], 
                                  confidence: float = 0.8) -> Dict[str, Any]:
        """
        Update learning with transfer learning effects
        
        Args:
            user_id: User identifier
            concept: Concept that was updated
            interaction_data: Interaction data dictionary
            confidence: Confidence in the update
            
        Returns:
            Dict: Updated mastery with transfer information
        """
        # Get current mastery state (Redis is single source of truth)
        current_mastery = self.get_mastery(user_id, concept)
        
        # Perform base confidence-weighted update
        is_correct = interaction_data.get("correct", False)
        response_time = interaction_data.get("response_time", 0.0)
        
        # Signal envelope (renamed from ct_mapping in Phase 14c).
        signal_mapping = {
            "confidence": confidence,
            "data_source": "transfer_learning",
        }

        base_result = self.update_mastery_with_confidence(
            current_mastery=current_mastery,
            is_correct=is_correct,
            response_time=response_time,
            signal_mapping=signal_mapping,
        )
        
        # Extract mastery changes from base update
        mastery_before = float(current_mastery)
        base_mastery_after = float(base_result.get("mastery_after", mastery_before))
        direct_mastery_change = base_mastery_after - mastery_before
        
        # 🔥 CLEAN ARCHITECTURE: Learner = pure learning only
        # Transfer handled by Factory (single source of truth)
        transfer_updates = {}  # Factory will compute transfer
        
        # 🔥 CLEAN ARCHITECTURE: No transfer logic in learner
        # Factory handles all transfer computation and application
        logger.info("🔥 LEARNER: Pure learning only (transfer handled by factory)")
        
        # 🔥 CORRECT STABLE DYNAMICAL SYSTEM: m_{t+1} = m_t + η(y - m_t) + βT - λm_t
        import numpy as np
        
        # --- PARAMETERS (prevent instant convergence) ---
        eta = 0.03              # slower learning rate
        lambda_decay = 0.002    # forgetting rate
        beta = interaction_data.get("beta", 0.5)
        
        # --- SIGNALS ---
        y = 1.0 if is_correct else 0.0
        
        # 🔥 LEARNING SIGNAL (correct term)
        learning_gain = eta * (y - current_mastery)
        
        # 🔥 CLEAN ARCHITECTURE: Factory handles transfer
        transfer_bonus = 0.0  # Factory will compute
        transfer_gain = 0.0  # Factory will apply
        
        # 🔥 MINIMUM LEARNING NOISE (prevent flatline)
        noise = np.random.normal(0, 0.01)
        
        # --- CORRECT UPDATE EQUATION ---
        new_mastery = (
            current_mastery
            + learning_gain
            + transfer_gain
            - lambda_decay * current_mastery
            + noise
        )
        
        # Bound to [0,1]
        final_mastery = max(0.0, min(1.0, new_mastery))
        
        # Calculate effective gain for logging
        effective_gain = final_mastery - current_mastery
        
        logger.info(f"🔥 CORRECT UPDATE: learning_gain={learning_gain:.4f}, transfer_gain={transfer_gain:.4f}, noise={noise:.4f}, decay={lambda_decay * current_mastery:.4f}")
        logger.info(f"🔥 MASTERY: {current_mastery:.3f} → {final_mastery:.3f} (Δ={effective_gain:.4f})")
        logger.info(f"🔥 LEARNER: Pure learning only (beta={beta})")
        
        # Store transfer-enhanced mastery
        self._store_final_mastery(user_id, concept, final_mastery)
        
        # 🔥 CLEAN ARCHITECTURE: No phantom transfer events
        # Factory handles all transfer events (single source of truth)
        logger.debug("🔥 LEARNER: No transfer events (factory handles)")
        
        # Update analytics
        # Note: _update_transfer_analytics expects TransferLearningUpdate, but we're passing TransferEvent
        # This is a minor analytics issue, not critical for transfer functionality
        
        # Return enhanced result with transfer-enhanced mastery
        enhanced_result = base_result.copy()
        enhanced_result.update({
            "mastery_after": final_mastery,  # Override with transfer-enhanced
            "transfers_applied": {},  # Factory handles transfer
            "transferred_mastery_change": final_mastery - base_mastery_after,
            "total_transferred_mastery_change": final_mastery - mastery_before,
            "transfer_sources": self.get_transfer_sources(user_id, concept),
            "transfer_effective_gain": effective_gain,
            "transfer_effect": transfer_gain
        })
        
        return enhanced_result
    
    def _store_final_mastery(self, user_id: str, concept: str, mastery: float):
        """Store final mastery with transfer effects (single authority)"""
        # Update user_mastery state
        if user_id not in self.user_mastery:
            self.user_mastery[user_id] = {}
        
        # 🔥 FIX: Store mastery directly (avoid 0.5 attractor)
        self.user_mastery[user_id][concept] = {"mastery": mastery}
        
        # Update Redis store (primary storage)
        if self.redis_store:
            try:
                logger.info(f"🔴 REDIS WRITE: {user_id}/{concept} = {mastery:.3f}")
                self.redis_store.set_mastery(user_id, concept, mastery)
                logger.info(f"✅ REDIS WRITE SUCCESS: {user_id}/{concept} = {mastery:.3f}")
            except Exception as e:
                logger.error(f"❌ REDIS WRITE FAILED: {user_id}/{concept} - {e}")
        else:
            logger.warning(f"⚠️ NO REDIS STORE AVAILABLE for {user_id}/{concept}")
        
        # Memory store is now optional cache only (not authoritative)
        # self.mastery_store[(user_id, concept)] = mastery  # REMOVED - Redis is source of truth
        logger.info(f"💾 Stored transfer-enhanced mastery in Redis: {user_id}/{concept} = {mastery:.3f}")
    
    def _apply_transfer_update(self, 
                             user_id: str, 
                             target_concept: str, 
                             transfer_amount: float, 
                             source_concept: str,
                             confidence: float):
        """Apply transfer update to target concept"""
        # Get current alpha/beta parameters for target concept
        if user_id not in self.user_mastery:
            self.user_mastery[user_id] = {}
        
        if target_concept not in self.user_mastery[user_id]:
            self.user_mastery[user_id][target_concept] = {"alpha": 1.0, "beta": 1.0}
        
        current_state = self.user_mastery[user_id][target_concept]
        alpha, beta = float(current_state["alpha"]), float(current_state["beta"])
        
        # Calculate transfer update (scaled by transfer weight)
        transfer_effect = float(transfer_amount) * self.transfer_weight * confidence
        
        # Apply transfer as a boosted Bayesian update
        if transfer_effect > 0:
            # Positive transfer - increase confidence with boost
            alpha_new = alpha + float(transfer_effect) * float(self.base_learning_rate) * 2.0  # 2x boost
            beta_new = beta  # Keep beta unchanged for positive transfer
        else:
            # Negative transfer - decrease confidence
            alpha_new = alpha  # Keep alpha unchanged for negative transfer
            beta_new = beta + abs(float(transfer_effect)) * float(self.base_learning_rate)
        
        # Ensure valid parameters
        alpha_new = max(0.1, min(100.0, alpha_new))
        beta_new = max(0.1, min(100.0, beta_new))
        
        # Update mastery state
        if user_id not in self.user_mastery:
            self.user_mastery[user_id] = {}
        self.user_mastery[user_id][target_concept] = {"alpha": alpha_new, "beta": beta_new}
    
    def _update_mastery_with_transfer(self,
                                   user_id: str,
                                   concept: str,
                                   direct_change: float,
                                   transferred_change: float,
                                   transfer_sources: Dict[str, List[str]]):
        """Update enhanced mastery tracking with transfer information"""
        if user_id not in self.user_mastery_with_transfer:
            self.user_mastery_with_transfer[user_id] = {}
        
        if concept not in self.user_mastery_with_transfer[user_id]:
            self.user_mastery_with_transfer[user_id][concept] = {
                "direct_mastery": 0.3,
                "transferred_mastery": 0.0,
                "total_mastery": 0.3
            }
        
        # Update mastery components
        current = self.user_mastery_with_transfer[user_id][concept]
        current["direct_mastery"] += float(direct_change)
        current["transferred_mastery"] += float(transferred_change)
        current["total_mastery"] = float(current["direct_mastery"]) + float(current["transferred_mastery"])
        
        # Apply bounds
        current["direct_mastery"] = max(0.0, min(1.0, current["direct_mastery"]))
        current["transferred_mastery"] = max(0.0, min(1.0, current["transferred_mastery"]))
        current["total_mastery"] = max(0.0, min(1.0, current["total_mastery"]))
        
        # Update transfer sources tracking
        if user_id not in self.transfer_sources:
            self.transfer_sources[user_id] = {}
        
        if concept not in self.transfer_sources[user_id]:
            self.transfer_sources[user_id][concept] = []
        
        for source_concept, sources in transfer_sources.items():
            self.transfer_sources[user_id][concept].extend(sources)
    
    def get_mastery(self, user_id: str, concept: str) -> float:
        """Get mastery for a user and concept - Redis as single source of truth"""
        if self.redis_store:
            try:
                logger.info(f"🔴 REDIS READ: {user_id}/{concept}")
                mastery_result = self.redis_store.get_mastery(user_id, concept)
                
                # Handle different return types from Redis
                if isinstance(mastery_result, tuple):
                    # If it's a tuple (alpha, beta), convert to mastery
                    if len(mastery_result) == 2:
                        alpha, beta = mastery_result
                        mastery = alpha / (alpha + beta) if (alpha + beta) > 0 else 0.3
                    else:
                        mastery = 0.3
                elif isinstance(mastery_result, (int, float)):
                    mastery = float(mastery_result)
                else:
                    # Try to convert string to float
                    try:
                        mastery = float(mastery_result)
                    except:
                        mastery = 0.3
                
                logger.info(f"✅ REDIS READ SUCCESS: {user_id}/{concept} = {mastery:.3f} (type: {type(mastery_result)})")
                return mastery
            except Exception as e:
                logger.error(f"❌ REDIS READ FAILED: {user_id}/{concept} - {e}")
                # Fallback to memory store
                if (user_id, concept) in self.mastery_store:
                    return self.mastery_store[(user_id, concept)]
                return 0.3  # Default mastery
        else:
            raise RuntimeError("Redis store not available - cannot get mastery")
    
    def get_mastery_with_transfer(self, user_id: str, concept: str) -> Dict[str, float]:
        """Get detailed mastery information including transfer components"""
        if user_id not in self.user_mastery_with_transfer:
            if user_id not in self.user_mastery:
                return {"mastery": 0.3, "direct_mastery": 0.3, "transferred_mastery": 0.0}
            else:
                # Fallback to basic mastery
                basic_mastery = self.get_mastery(user_id, concept)
                return {
                    "mastery": basic_mastery,
                    "direct_mastery": basic_mastery,
                    "transferred_mastery": 0.0
                }
        
        if concept not in self.user_mastery_with_transfer[user_id]:
            return {"mastery": 0.3, "direct_mastery": 0.3, "transferred_mastery": 0.0}
        
        mastery_data = self.user_mastery_with_transfer[user_id][concept]
        
        return {
            "mastery": mastery_data["total_mastery"],
            "direct_mastery": mastery_data["direct_mastery"],
            "transferred_mastery": mastery_data["transferred_mastery"]
        }
    
    def get_transfer_sources(self, user_id: str, concept: str) -> List[str]:
        """Get list of concepts that contributed transfer to this concept"""
        if user_id not in self.transfer_sources:
            return []
        
        if concept not in self.transfer_sources[user_id]:
            return []
        
        return list(set(self.transfer_sources[user_id][concept]))  # Remove duplicates
    
    def _update_transfer_analytics(self, transfer_update: TransferLearningUpdate):
        """Update transfer learning analytics"""
        self.transfer_analytics["total_transfer_events"] += 1
        self.transfer_analytics["total_transferred_mastery"] += abs(transfer_update.transferred_mastery_change)
        
        # Update average
        total_events = self.transfer_analytics["total_transfer_events"]
        if total_events > 0:
            self.transfer_analytics["avg_transfer_per_event"] = (
                self.transfer_analytics["total_transferred_mastery"] / total_events
            )
        
        # Track most transferred concepts
        for target_concept in transfer_update.transfer_sources.keys():
            if target_concept not in self.transfer_analytics["most_transferred_concepts"]:
                self.transfer_analytics["most_transferred_concepts"][target_concept] = 0
            self.transfer_analytics["most_transferred_concepts"][target_concept] += 1
    
    def get_transfer_analytics(self) -> Dict:
        """Get comprehensive transfer learning analytics"""
        return {
            **self.transfer_analytics,
            "transfer_efficiency": self._calculate_transfer_efficiency(),
            "concept_transfer_graph": self.transfer_engine.get_concept_dependency_graph(),
            "recent_transfer_updates": self.transfer_updates[-10:] if self.transfer_updates else []
        }
    
    def _calculate_transfer_efficiency(self) -> Dict[str, float]:
        """Calculate transfer efficiency metrics"""
        if not self.transfer_updates:
            return {"efficiency_score": 0.0, "direct_vs_transfer_ratio": 0.0}
        
        total_direct = sum(abs(u.direct_mastery_change) for u in self.transfer_updates)
        total_transferred = sum(abs(u.transferred_mastery_change) for u in self.transfer_updates)
        
        efficiency_score = total_transferred / (total_direct + total_transferred) if (total_direct + total_transferred) > 0 else 0.0
        direct_vs_transfer_ratio = total_transferred / total_direct if total_direct > 0 else 0.0
        
        return {
            "efficiency_score": efficiency_score,
            "direct_vs_transfer_ratio": direct_vs_transfer_ratio,
            "total_direct": total_direct,
            "total_transferred": total_transferred
        }
    
    def simulate_learning_path(self, 
                               user_id: str, 
                               concepts: List[str], 
                               steps: int = 100) -> Dict[str, List[float]]:
        """
        Simulate learning path across multiple concepts with transfer effects
        
        Args:
            user_id: User identifier
            concepts: List of concepts to simulate
            steps: Number of learning steps
            
        Returns:
            Dictionary with mastery progression for each concept
        """
        progression = {concept: [] for concept in concepts}
        
        # Initialize mastery
        for concept in concepts:
            mastery = self.get_mastery_with_transfer(user_id, concept)
            progression[concept].append(mastery["total_mastery"])
        
        # Simulate learning steps
        for step in range(steps):
            # Pick a concept to focus on (round-robin for simplicity)
            current_concept = concepts[step % len(concepts)]
            
            # Simulate a correct interaction
            interaction_data = {
                "correct": True,
                "response_time": 10.0,
                "difficulty": 0.7
            }
            
            # Update with transfer
            result = self.update_learning_with_transfer(
                user_id, current_concept, interaction_data, confidence=0.8
            )
            
            # Record mastery for all concepts
            for concept in concepts:
                mastery = self.get_mastery_with_transfer(user_id, concept)
                progression[concept].append(mastery["total_mastery"])
        
        return progression
