"""
Real Bandit Integration - Thompson Sampling Decision Authority
Replaces fake smoothing with proper contextual bandit
"""

import logging
from typing import Dict, Any, List, Tuple
from core.bandit.bandit import ContextualBandit

logger = logging.getLogger(__name__)

class RealBanditIntegration:
    """
    Real contextual bandit integration using Thompson Sampling
    Replaces deterministic rules with probabilistic adaptive decisions
    """
    
    def __init__(self, redis_store=None):
        """Initialize with real contextual bandit and persistence"""
        self.bandit = ContextualBandit()
        self.arm_registry = ArmRegistry()
        self.redis_store = redis_store  # For additional persistence if needed
        
        # ✅ ContextualBandit already has Redis persistence built-in!
        logger.info(f"🔥 RealBanditIntegration initialized with Redis persistence: {self.bandit.redis_client is not None}")
        
    def select_action_with_learner_priors(self, user_id: str, state: Dict[str, Any], context: Dict[str, Any], 
                                       learner_insights: Dict[str, Any]) -> Dict[str, Any]:
        """
        Select action using Thompson Sampling with learner-informed priors
        This is the key integration point for unified learning decision making
        """
        # Extract learner-informed mastery and uncertainty
        ensemble_mastery = learner_insights.get("ensemble_mastery", {})
        ensemble_uncertainty = learner_insights.get("ensemble_uncertainty", {})
        
        logger.info(f"🧠 BANDIT WITH LEARNER PRIORS: user={user_id}")
        logger.info(f"  ensemble_mastery: {ensemble_mastery}")
        logger.info(f"  ensemble_uncertainty: {ensemble_uncertainty}")
        
        # Build candidate arms
        candidate_arms = self.arm_registry.build_candidate_arms(state, context)
        
        # Build context for each arm
        contexts = []
        for arm in candidate_arms:
            arm_context = self._build_arm_context(state, context, arm)
            contexts.append(arm_context)
        
        # Use REAL Thompson Sampling from ContextualBandit with learner-informed mastery
        candidates = []
        for i, arm in enumerate(candidate_arms):
            concept, difficulty, representation = self.arm_registry.parse_arm(arm)
            
            # 🔥 LEARNER-INFORMED MASTERY CONTEXT
            concept_mastery = ensemble_mastery.get(concept, 0.5)  # Default to 0.5 if not available
            concept_uncertainty = ensemble_uncertainty.get(concept, 0.5)
            
            candidates.append({
                "arm": arm,
                "concept_id": concept,
                "task_id": arm,
                "difficulty": float(difficulty),
                "concept": concept,
                "representation": representation,
                "context": contexts[i],
                # 🔥 LEARNER-INFORMED PRIORS
                "learner_mastery": concept_mastery,
                "learner_uncertainty": concept_uncertainty,
                "transfer_potential": learner_insights.get("transfer_potential", {}).get(f"lyapunov_{concept}", 0.0)
            })
        
        # Create mastery context with learner insights
        mastery_context = ensemble_mastery.copy()
        
        # 🔥 KEY: Use learner-informed mastery for Thompson sampling
        selected_task = self.bandit.select_arm_contextual_thompson(user_id, candidates, mastery_context)
        
        if selected_task:
            # Add learner insights to response
            selected_task["learner_inference"] = {
                "ensemble_mastery": ensemble_mastery,
                "ensemble_uncertainty": ensemble_uncertainty,
                "transfer_potential": learner_insights.get("transfer_potential", {}),
                "used_learner_priors": True
            }
            
            logger.info(f"🧠 LEARNER-INFORMED SELECTION: user={user_id}")
            logger.info(f"  selected: {selected_task.get('task_id')}")
            logger.info(f"  learner_mastery: {selected_task.get('learner_mastery')}")
            logger.info(f"  thompson_sample: {selected_task.get('thompson_sample')}")
            
            return selected_task
        else:
            # Fallback to regular selection
            logger.warning("⚠️ Learner-informed selection failed, fallback to regular bandit")
            return self.select_action(user_id, state, context)
    
    def select_action(self, user_id: str, state: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Select action using Thompson Sampling - NOT deterministic rules
        """
        # Build candidate arms
        candidate_arms = self.arm_registry.build_candidate_arms(state, context)
        
        # Build context for each arm
        contexts = []
        for arm in candidate_arms:
            arm_context = self._build_arm_context(state, context, arm)
            contexts.append(arm_context)
        
        # Use REAL Thompson Sampling from ContextualBandit
        # Convert to candidate format for ContextualBandit
        candidates = []
        for i, arm in enumerate(candidate_arms):
            concept, difficulty, representation = self.arm_registry.parse_arm(arm)
            candidates.append({
                "arm": arm,
                "concept_id": concept,  # Expected by old bandit
                "task_id": arm,  # Required field
                "difficulty": float(difficulty),  # NUMERIC - critical!
                "concept": concept,
                "representation": representation,
                "context": contexts[i]
            })
        
        # Build mastery context for old bandit
        mastery_context = {}
        concepts = state.get("mastery", {}).get("concepts", {})
        for concept in concepts:
            mastery_context[concept] = float(concepts[concept])
        
        # Use REAL contextual Thompson sampling
        selected_candidate = self.bandit.select_arm_contextual_thompson(
            user_id=user_id,  # ✅ REAL per-user learning
            candidates=candidates,
            mastery_context=mastery_context
        )
        
        selected_arm = selected_candidate["arm"]
        selected_arm_index = candidate_arms.index(selected_arm)
        
        # Extract real Thompson samples from candidates
        thompson_samples = [c.get("thompson_sample", 0.5) for c in candidates]
        
        logger.info(f"🎯 REAL Thompson Sampling: {selected_arm} (index {selected_arm_index})")
        logger.info(f"   Hybrid score: {selected_candidate.get('hybrid_score', 0.0):.3f}")
        logger.info(f"   Candidates evaluated: {len(candidates)}")
        
        # Extract arm components
        concept, difficulty, representation = self.arm_registry.parse_arm(selected_arm)
        
        return {
            "selected_arm": selected_arm,
            "concept": concept,
            "difficulty": difficulty,
            "representation": representation,
            "next_task": f"{concept}_{difficulty}_task",  # Add missing next_task field
            "thompson_samples": thompson_samples,
            "confidence": self._calculate_confidence(thompson_samples),
            "reasoning": {
                "strategy": "thompson_sampling",
                "arms_considered": len(candidate_arms),
                "selected_index": selected_arm_index,
                "exploration_bonus": thompson_samples[selected_arm_index]
            }
        }
    
    def update_bandit(self, user_id: str, arm: str, reward: float, context: Dict[str, Any]) -> None:
        """
        Update bandit with actual outcome - NOT smoothing
        Uses proper Thompson Sampling alpha/beta updates
        """
        # Update using ContextualBandit's update method
        self.bandit.update(
            user_id=user_id,  # ✅ REAL per-user learning
            arm=arm,
            reward=reward,
            context=context
        )
        
        logger.info(f"🎯 Bandit Update: {arm}")
        logger.info(f"   Reward: {reward:.3f}")
        logger.info(f"   Context: {context}")
        
        # Get updated alpha/beta for logging
        alpha, beta = self.bandit._get_alpha_beta(user_id, arm)
        success_rate = alpha / (alpha + beta)
        logger.info(f"   Alpha: {alpha:.3f} → Beta: {beta:.3f}")
        logger.info(f"   Success Rate: {success_rate:.3f}")
        
        # ✅ Redis persistence is automatic in ContextualBandit!
        if self.bandit.redis_client:
            logger.info(f"   🗄️  Persisted to Redis: bandit:{user_id}:{arm}")
        else:
            logger.warning("   ⚠️  No Redis persistence - using memory only")
    
    def _build_arm_context(self, state: Dict[str, Any], request_context: Dict[str, Any], arm: str) -> Dict[str, Any]:
        """
        Build rich context for bandit decision
        This is what makes the bandit "contextual"
        """
        concept, difficulty, representation = self.arm_registry.parse_arm(arm)
        
        # Get concept mastery
        concepts = state.get("mastery", {}).get("concepts", {})
        concept_mastery = concepts.get(concept, 0.0)
        
        # Calculate uncertainty
        uncertainty = 1.0 - concept_mastery
        
        # Get bandit state for this arm
        try:
            alpha, beta = self.bandit._get_alpha_beta("default", arm)
            success_rate = alpha / (alpha + beta)
            arm_confidence = max(alpha, beta) / (alpha + beta)
        except:
            success_rate = 0.5  # Prior
            arm_confidence = 0.5
        
        # Build NUMERIC context for bandit calculations
        context = {
            "mastery": float(concept_mastery),
            "uncertainty": float(uncertainty),
            "global_mastery": float(state.get("mastery", {}).get("global", 0.5)),
            "difficulty": float(difficulty),  # NUMERIC - critical for math!
            "concept": str(concept),  # String OK for identification
            "representation": str(representation),  # String OK for identification
            "success_rate": float(success_rate),
            "arm_confidence": float(arm_confidence),
            "learning_gain": self._estimate_learning_gain(concept_mastery, float(difficulty)),
            "policy_weight": 1.0  # Default policy weight
        }
        
        return context
    
    def check_persistence_status(self, user_id: str) -> Dict[str, Any]:
        """Check Redis persistence status for a user"""
        if not self.bandit.redis_client:
            return {
                "redis_connected": False,
                "message": "Redis not available - using memory-only storage"
            }
        
        try:
            # Check if user has persisted state in Redis
            key = f"bandit:{user_id}:ct_abstraction|medium|text"  # Common arm pattern
            exists = self.bandit.redis_client.exists(key)
            
            # Get regret tracking status
            regret_keys = [
                f"bandit:regret:lr:{user_id}",
                f"bandit:regret:dr:{user_id}",
                f"bandit:regret:steps:{user_id}"
            ]
            
            regret_exists = any(self.bandit.redis_client.exists(key) for key in regret_keys)
            
            return {
                "redis_connected": True,
                "user_id": user_id,
                "has_persisted_state": exists,
                "has_regret_tracking": regret_exists,
                "message": "Redis persistence active"
            }
            
        except Exception as e:
            return {
                "redis_connected": True,
                "error": str(e),
                "message": f"Redis check failed: {e}"
            }
    
    def _calculate_confidence(self, thompson_samples: List[float]) -> float:
        """Calculate decision confidence from Thompson samples"""
        if not thompson_samples:
            return 0.5
        
        # Confidence = how much better the selected arm is than others
        selected_value = max(thompson_samples)
        avg_others = sum(v for i, v in enumerate(thompson_samples) if i != thompson_samples.index(selected_value)) / (len(thompson_samples) - 1)
        
        # Normalize to [0, 1]
        confidence = max(0.0, min(1.0, (selected_value - avg_others) / selected_value))
        return confidence
    
    def _estimate_learning_gain(self, mastery: float, difficulty: float) -> float:
        """Estimate potential learning gain from this interaction"""
        # Optimal learning zone: not too easy, not too hard
        if mastery < 0.3:
            # Struggling learner - need easier tasks
            optimal_difficulty = 0.3
        elif mastery > 0.8:
            # Advanced learner - need harder tasks  
            optimal_difficulty = 0.8
        else:
            # Intermediate - current zone is good
            optimal_difficulty = mastery
        
        # Learning gain = inverse of difficulty mismatch
        difficulty_mismatch = abs(float(difficulty) - float(optimal_difficulty))
        learning_gain = max(0.0, 1.0 - difficulty_mismatch * 2)
        
        return float(learning_gain)
    
    def _estimate_transfer_potential(self, concept: str, state: Dict[str, Any]) -> float:
        """Estimate transfer learning potential"""
        # Check if this concept has related concepts with high mastery
        concepts = state.get("mastery", {}).get("concepts", {})
        
        # Hardcoded transfer relationships (same as V2 engine)
        transfer_graph = {
            "ct_decomposition": ["ct_algorithm"],
            "ct_algorithm": ["ct_abstraction"],
            "ct_abstraction": ["ct_generalization"]
        }
        
        if concept in transfer_graph:
            related = transfer_graph[concept]
            related_mastery = [concepts.get(c, 0.0) for c in related]
            avg_related_mastery = sum(related_mastery) / len(related_mastery) if related_mastery else 0.0
            return avg_related_mastery
        
        return 0.0

class ArmRegistry:
    """
    Registry for standardizing arm definitions
    Ensures consistent arm format across the system
    """
    
    def __init__(self):
        self.concepts = ["ct_algorithm", "ct_abstraction", "ct_decomposition", "ct_generalization"]
        self.difficulties = [0.3, 0.5, 0.7]  # NUMERIC difficulties for bandit math
        self.difficulty_labels = ["easy", "medium", "hard"]  # Keep labels for display
        self.representations = ["text", "visual", "interactive"]
    
    def build_candidate_arms(self, state: Dict[str, Any], context: Dict[str, Any]) -> List[str]:
        """Build all candidate arms for current context"""
        arms = []
        
        # Get user's preferred difficulty
        preferred_difficulty = context.get("difficulty_preference", "medium")
        
        # Get mastered concepts (prioritize related concepts)
        concepts = state.get("mastery", {}).get("concepts", {})
        mastered_concepts = [c for c, m in concepts.items() if m > 0.7]
        struggling_concepts = [c for c, m in concepts.items() if m < 0.3]
        
        # Build arms based on learning state
        if struggling_concepts:
            # Focus on struggling concepts with easier difficulty
            focus_concepts = struggling_concepts[:2]  # Top 2 struggling
            focus_difficulties = [0.3, 0.5]  # easy, medium
        elif mastered_concepts:
            # Focus on advanced concepts for mastered users
            focus_concepts = mastered_concepts[:2]  # Top 2 mastered
            focus_difficulties = [0.5, 0.7]  # medium, hard
        else:
            # Default: all concepts
            focus_concepts = self.concepts[:3]  # Top 3 concepts
            focus_difficulties = self.difficulties
        
        # Generate arms
        for concept in focus_concepts:
            for difficulty in focus_difficulties:
                for representation in self.representations[:2]:  # Limit representations
                    arm = self.create_arm(concept, difficulty, representation)
                    arms.append(arm)
        
        logger.info(f"🎯 Generated {len(arms)} candidate arms")
        return arms
    
    def create_arm(self, concept: str, difficulty: str, representation: str) -> str:
        """Create standardized arm identifier"""
        return f"{concept}|{difficulty}|{representation}"
    
    def parse_arm(self, arm: str) -> Tuple[str, str, str]:
        """Parse arm into components"""
        parts = arm.split("|")
        if len(parts) == 3:
            return parts[0], parts[1], parts[2]
        else:
            # Fallback for malformed arms
            return "ct_algorithm", "medium", "text"

# Factory function
def create_real_bandit_integration(redis_store=None):
    """Create real bandit integration"""
    return RealBanditIntegration()
