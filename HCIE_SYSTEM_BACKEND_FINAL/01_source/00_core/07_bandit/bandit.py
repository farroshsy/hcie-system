"""
Contextual Thompson Sampling Bandit
Production-aligned implementation of formal mathematical model
Copied from existing working infrastructure

🔥 BRAIN GOVERNANCE:
- CONTROL: select_action() chooses tasks to maximize expected JT (JT-native)
- STATE: alpha_beta_params track learner performance (inform CONTROL)
- OBSERVE: regret tracking for research/debug (does not affect behavior)
- JT-NATIVE: Bandit uses historical JT for selection (not heuristic learning_gain)
- JT-AWARE EXPLORATION: Exploration pressure adapts to JT volatility (governance response)
  - Stable JT → exploit current knowledge (low exploration)
  - Unstable JT → explore more aggressively (high exploration)
- PHASE 4 REWARD GEOMETRY: Sigmoid-based JT normalization for near-equilibrium sensitivity
  - Linear normalization wastes resolution near zero where cognition actually lives
  - Sigmoid amplifies subtle JT differences that matter for control-theoretic cognition
  - Enhanced equilibrium gradients improve policy discrimination and learner specialization
"""

import random
import math
import threading
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict
import numpy as np
import logging
import redis

logger = logging.getLogger(__name__)


def _convert_numpy(val):
    """🔥 Convert numpy types to native Python types for SQL compatibility"""
    if isinstance(val, (np.integer, np.floating)):
        return val.item()
    elif isinstance(val, np.ndarray):
        return val.tolist()
    return val

class ContextualBandit:
    """
    Contextual Thompson Sampling implementation
    Selects tasks based on mastery, representation, and uncertainty
    """
    
    def __init__(self, 
                 uncertainty_weight: float = 0.1,
                 learning_gain_weight: float = 0.05,
                 representations: List[str] = None,
                 rng_stream=None,
                 pg_store=None):
        """
        Initialize contextual bandit
        
        Args:
            uncertainty_weight: gamma parameter for exploration bonus
            learning_gain_weight: eta parameter for learning gain
            representations: Available representation types
            rng_stream: Optional RNG stream for deterministic Thompson sampling (Priority 2)
            pg_store: Optional SQL execution store injected by application DI
        """
        self.uncertainty_weight = uncertainty_weight
        self.learning_gain_weight = learning_gain_weight
        self.representations = representations or ["text", "visual", "interactive"]
        self.rng_stream = rng_stream  # 🔥 PRIORITY 2: Deterministic RNG stream for Thompson sampling
        
        # 🔥 PHASE 2D: Thread safety lock for replay-critical bandit state
        # Protects: alpha_beta_params, arm_rewards, arm_contexts, jt_history modifications
        self._lock = threading.RLock()

        logger.info("Contextual Bandit initialized")

        # Simple state tracking for updates (TODO: move to Redis)
        self.arm_rewards = defaultdict(list)
        self.arm_contexts = defaultdict(list)

        # 🔥 JT-AWARE EXPLORATION: Track JT history for volatility calculation
        self.jt_history = defaultdict(list)  # user_id -> list of recent JT values
        self.jt_window_size = 20  # Rolling window for volatility calculation
        self.base_uncertainty_weight = uncertainty_weight  # Store base weight
        
        # STATE: α/β parameters for Thompson sampling (used in CONTROL decisions)
        self.alpha_beta_params = {}  # arm -> [alpha, beta]

        # OBSERVE: Cumulative regret tracking (research/debug only, does not affect behavior)
        self.cumulative_learning_regret = defaultdict(float)
        self.cumulative_decision_regret = defaultdict(float)
        self.step_count = defaultdict(int)
        
        # 🔥 PERSISTENT REDIS STATE: Long-term learning
        try:
            self.redis_client = redis.Redis(
                host='redis',
                port=6379,
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info("🔥 BANDIT: Redis connected for persistent learning")
        except Exception as e:
            logger.warning(f"🔥 BANDIT: Redis connection failed, using memory-only: {e}")
            self.redis_client = None
        
        # 🔥 SQL BACKUP PERSISTENCE: Production resilience via DI
        self.pg_store = pg_store
        if self.pg_store:
            logger.info("🔥 BANDIT: SQL backup persistence enabled")
        else:
            logger.warning("🔥 BANDIT: SQL backup not configured, using memory-only")
    
    def sample_beta(self, alpha: float, beta: float) -> float:
        """
        Sample from Beta distribution for Thompson sampling
        
        theta* ~ Beta(alpha, beta)
        
        🔥 PRIORITY 2: Uses deterministic RNG stream when available
        """
        if alpha <= 0 or beta <= 0:
            return 0.5
        
        try:
            # 🔥 PRIORITY 2: Use deterministic RNG stream if available
            if self.rng_stream is not None:
                # Use numpy's beta distribution with deterministic RNG stream
                return self.rng_stream.beta(alpha, beta)
            else:
                # Fallback to Python's random module (non-deterministic)
                return random.betavariate(alpha, beta)
        except Exception as e:
            logger.error(f"Error sampling Beta({alpha}, {beta}): {e}")
            return 0.5
    
    def calculate_thompson_score(self,
                                mastery_sample: float,
                                representation_sample: float,
                                uncertainty: float,
                                difficulty: float,
                                learning_gain: float) -> float:
        """
        CONTROL: Thompson sampling score for action selection

        🔥 JT-NATIVE: learning_gain is now historical JT (not heuristic)
        Score = theta_sample + phi_sample + gamma * uncertainty + eta * historical_JT - difficulty

        This makes exploration governance-native - the bandit now optimizes expected JT
        instead of heuristic learning gain.
        """
        return (
            mastery_sample +
            representation_sample +
            self.uncertainty_weight * uncertainty +
            self.learning_gain_weight * learning_gain -
            difficulty
        )
    
    def reset_bandit_state(self, user_id: str = None):
        """
        🔥 CRITICAL FOR EXPERIMENTS: Reset bandit to clean state
        
        🔥 PHASE 2D: Thread-safe with lock protecting alpha_beta_params, arm_rewards, arm_contexts

        This ensures valid comparison between reward and Jₜ systems
        by removing any prior learning that could contaminate results.
        
        Args:
            user_id: Specific user to reset, or None for all users
        """
        with self._lock:
            if user_id:
                # Reset specific user
                if user_id in self.alpha_beta_params:
                    for arm in self.alpha_beta_params[user_id]:
                        self.alpha_beta_params[user_id][arm] = (1.0, 1.0)  # Fresh prior
                    logger.info(f"🔥 BANDIT RESET: Reset user {user_id} to fresh priors")
                
                # Clear Redis for this user
                if self.redis_client:
                    try:
                        # Clear all keys for this user
                        pattern = f"bandit:{user_id}:*"
                        keys = self.redis_client.keys(pattern)
                        if keys:
                            self.redis_client.delete(*keys)
                            logger.info(f"🔥 BANDIT RESET: Cleared {len(keys)} Redis keys for {user_id}")
                    except Exception as e:
                        logger.warning(f"🔥 BANDIT RESET: Failed to clear Redis for {user_id}: {e}")
            else:
                # Reset all users
                self.alpha_beta_params.clear()
                self.arm_rewards.clear()
                self.arm_contexts.clear()
                logger.info("🔥 BANDIT RESET: Reset ALL users to fresh priors")
                
                # Clear all Redis bandit data
                if self.redis_client:
                    try:
                        pattern = "bandit:*"
                        keys = self.redis_client.keys(pattern)
                        if keys:
                            self.redis_client.delete(*keys)
                            logger.info(f"🔥 BANDIT RESET: Cleared {len(keys)} Redis keys for ALL users")
                    except Exception as e:
                        logger.warning(f"🔥 BANDIT RESET: Failed to clear Redis: {e}")

    def _get_alpha_beta(self, user_id: str, arm: str, mastery_context: Dict[str, float] = None, task_difficulty: float = 0.5) -> Tuple[float, float]:
        """
        Get α/β parameters from Redis, SQL backup, or memory with mastery-aligned cold start
        
        Args:
            user_id: User identifier
            arm: Task identifier
            mastery_context: Dict of concept_id -> mastery for cold start alignment
            
        Returns:
            (alpha, beta) parameters
        """
        key = f"bandit:{user_id}:{arm}"
        
        # Try Redis first (fast path)
        if self.redis_client:
            try:
                stored = self.redis_client.get(key)
                if stored:
                    alpha, beta = map(float, stored.split(','))
                    return alpha, beta
            except Exception as e:
                logger.warning(f"🔥 REDIS GET failed for {key}: {e}")
        
        # Fallback to SQL backup (recovery path)
        if self.pg_store:
            try:
                sql = """
                SELECT alpha, beta FROM bandit_state
                WHERE user_id = %s AND arm = %s
                """
                result = self.pg_store.execute_read(sql, (user_id, arm), fetch_one=True)
                if result:
                    alpha, beta = result['alpha'], result['beta']
                    logger.info(f"🔥 SQL RECOVERY: {key} = ({alpha:.3f}, {beta:.3f})")
                    # Restore to Redis for fast access
                    self._set_alpha_beta(user_id, arm, alpha, beta)
                    return alpha, beta
            except Exception as e:
                logger.warning(f"🔥 SQL GET failed for {key}: {e}")
        
        # Fallback to memory or prior
        if arm in self.alpha_beta_params:
            return self.alpha_beta_params[arm]
        else:
            # 🔥 DIFFICULTY-AWARE MASTERY-ALIGNED COLD START PRIOR
            if mastery_context and arm in mastery_context:
                mastery = mastery_context[arm]
                difficulty = task_difficulty  # Use actual task difficulty
                
                # Difficulty-aware prior: easy tasks get higher alpha, hard tasks get higher beta
                alpha = 1.0 + mastery * (1.0 - difficulty)  # Easy tasks → higher alpha
                beta = 1.0 + (1.0 - mastery) * difficulty  # Hard tasks → higher beta
                logger.debug(f"🔥 DIFFICULTY-AWARE PRIOR: user={user_id} arm={arm} mastery={mastery:.3f} difficulty={difficulty:.3f} α={alpha:.3f} β={beta:.3f}")
                return alpha, beta
            else:
                return 1.0, 1.0  # Default prior
    
    def _set_alpha_beta(self, user_id: str, arm: str, alpha: float, beta: float):
        """
        Store α/β parameters in Redis, SQL backup, and memory
        
        🔥 PHASE 2D: Thread-safe with lock protecting alpha_beta_params

        Args:
            user_id: User identifier
            arm: Task identifier
            alpha: Alpha parameter
            beta: Beta parameter
        """
        with self._lock:
            # Update memory
            self.alpha_beta_params[arm] = [alpha, beta]
        
        # Update Redis with TTL for forgetting
        key = f"bandit:{user_id}:{arm}"
        if self.redis_client:
            try:
                # 🔥 ADD TTL: 30 days forgetting period
                ttl_seconds = 30 * 24 * 60 * 60  # 30 days
                self.redis_client.setex(key, ttl_seconds, f"{alpha},{beta}")
                logger.debug(f"🔥 REDIS SET: {key} = ({alpha:.3f}, {beta:.3f}) TTL={ttl_seconds}s")
            except Exception as e:
                logger.warning(f"🔥 REDIS SET failed for {key}: {e}")
        
        # Update SQL backup for production resilience
        if self.pg_store:
            try:
                sql = """
                INSERT INTO bandit_state (user_id, arm, alpha, beta, last_updated)
                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id, arm) 
                DO UPDATE SET 
                    alpha = EXCLUDED.alpha,
                    beta = EXCLUDED.beta,
                    last_updated = CURRENT_TIMESTAMP
                """
                # 🔥 FIX: Convert numpy types to native Python types for SQL
                self.pg_store.execute_write(sql, (
                    user_id, 
                    arm, 
                    _convert_numpy(alpha), 
                    _convert_numpy(beta)
                ))
                logger.debug(f"🔥 SQL BACKUP: {key} = ({alpha:.3f}, {beta:.3f})")
            except Exception as e:
                logger.warning(f"🔥 SQL BACKUP failed for {key}: {e}")
    
    def update(self, user_id: str, arm: str, reward: float, context: Dict[str, Any]):
        """
        Update bandit with reward feedback (real Bayesian learning with persistence)
        
        🔥 PHASE 2D: Thread-safe with lock protecting arm_rewards, arm_contexts

        Args:
            user_id: User identifier
            arm: Selected arm (task representation)
            reward: Observed reward
            context: Context features used for selection
        """
        import traceback
        caller = traceback.extract_stack()[-2].filename.split('/')[-1] if traceback.extract_stack() else "unknown"
        logger.warning(f" BANDIT UPDATE from {caller}: user={user_id} arm={arm} reward={reward:.3f}")
        # GET CURRENT STATE (from Redis or memory)
        alpha, beta = self._get_alpha_beta(user_id, arm)
        
        # WEIGHTED BAYESIAN UPDATE (better than binary)
        alpha += reward  # Weighted success
        beta += (1 - reward)  # Weighted failure
        
        # 🔥 PERSIST NEW STATE
        self._set_alpha_beta(user_id, arm, alpha, beta)
        
        with self._lock:
            # Keep logging for debugging
            self.arm_rewards[arm].append(reward)
            self.arm_contexts[arm].append(context)
            
            # Keep only recent history (prevent memory growth)
            if len(self.arm_rewards[arm]) > 100:
                self.arm_rewards[arm] = self.arm_rewards[arm][-50:]
                self.arm_contexts[arm] = self.arm_contexts[arm][-50:]
        
        logger.info(f"🔥 BANDIT LEARNED: user={user_id} arm={arm} reward={reward:.3f} α={alpha:.3f} β={beta:.3f}")
    
    def _sigmoid_normalize_JT(self, J_t: float, k: float = 15.0) -> float:
        """
        🔥 PHASE 4: Sigmoid-based JT normalization for near-equilibrium sensitivity

        Linear normalization wastes resolution near zero where cognition actually lives.
        Sigmoid compression amplifies equilibrium gradients while saturating extremes.

        Governance principle:
        - Near equilibrium (JT ≈ 0): small differences become more expressive
        - Extreme JT: saturate to prevent overreaction to outliers

        Args:
            J_t: Raw objective function value (typically in [-0.2, +0.2])
            k: Sensitivity parameter (higher = steeper transition at zero)

        Returns:
            Normalized JT in [0,1] range with enhanced equilibrium sensitivity
        """
        # Sigmoid: y = 1 / (1 + e^(-kx))
        # This maps JT to [0,1] with enhanced resolution near zero
        normalized_J = 1.0 / (1.0 + np.exp(-k * J_t))

        logger.debug(f"🔥 SIGMOID NORMALIZATION: J_t={J_t:.6f} → {normalized_J:.3f} (k={k})")

        return normalized_J

    def update_with_objective(self, user_id: str, arm: str, J_t: float, context: Dict[str, Any]):
        """
        🔥 JT-ALIGNED REWARD: Update bandit with JT-derived reward
        
        🔥 PHASE 2D: Thread-safe with lock protecting jt_history, arm_rewards, arm_contexts

        Reward formula: R_t = J_t - J_{t-1} + exploration_bonus - regret_penalty
        
        This aligns bandit optimization with JT semantic:
        - Positive delta (J_t > J_{t-1}): reward improvement
        - Negative delta (J_t < J_{t-1}): penalize degradation
        - Exploration bonus: reward information gain from uncertain actions
        - Regret penalty: penalize suboptimal actions relative to best possible
        
        Args:
            user_id: User identifier
            arm: Selected arm (task representation)
            J_t: Per-interaction objective function value
            context: Context features used for selection
        """
        import traceback
        caller = traceback.extract_stack()[-2].filename.split('/')[-1] if traceback.extract_stack() else "unknown"
        logger.info(f"🔥 J_t-ALIGNED UPDATE from {caller}: user={user_id} arm={arm} J_t={J_t:.6f}")
        
        # GET CURRENT STATE (from Redis or memory)
        alpha, beta = self._get_alpha_beta(user_id, arm)
        
        with self._lock:
            # 🔥 TRACK JT HISTORY for delta calculation
            self.jt_history[user_id].append(J_t)
            if len(self.jt_history[user_id]) > self.jt_window_size:
                self.jt_history[user_id].pop(0)
            
            # 🔥 COMPUTE JT DELTA: J_t - J_{t-1}
            J_t_minus_1 = self.jt_history[user_id][-2] if len(self.jt_history[user_id]) >= 2 else 0.0
            jt_delta = J_t - J_t_minus_1
            
            # 🔥 EXPLORATION BONUS: Reward information gain from uncertainty
            uncertainty = context.get("uncertainty", 0.0)
            exploration_bonus = 0.1 * uncertainty  # 10% of uncertainty as exploration bonus
            
            # 🔥 REGRET PENALTY: Penalize suboptimal actions
            # Estimate best possible J_t from recent history
            recent_jts = self.jt_history[user_id]
            best_jt = max(recent_jts) if recent_jts else J_t
            regret_penalty = 0.05 * (best_jt - J_t) if J_t < best_jt else 0.0
            
            # 🔥 JT-ALIGNED REWARD: R_t = J_t - J_{t-1} + exploration_bonus - regret_penalty
            reward = jt_delta + exploration_bonus - regret_penalty
            
            # Normalize reward to [0, 1] range for bandit update
            # JT delta is typically in [-0.2, +0.2], so we shift and scale
            normalized_reward = (reward + 0.3) / 0.6  # Map [-0.3, 0.3] to [0, 1]
            normalized_reward = max(0.0, min(1.0, normalized_reward))  # Clamp to [0, 1]
            
            logger.info(
                f"🔥 JT-ALIGNED REWARD: J_t={J_t:.6f} J_t_minus_1={J_t_minus_1:.6f} "
                f"delta={jt_delta:.6f} exploration={exploration_bonus:.6f} "
                f"regret={regret_penalty:.6f} reward={reward:.6f} normalized={normalized_reward:.3f}"
            )
            
            # 🔥 STABILIZED UPDATE: Reduce learning rate for JT optimization
            learning_rate = 0.3  # Reduced from 1.0 for stability
            alpha += learning_rate * normalized_reward
            beta += learning_rate * (1 - normalized_reward)
        
        # 🔥 PERSIST NEW STATE
        self._set_alpha_beta(user_id, arm, alpha, beta)
        
        with self._lock:
            # Keep logging for debugging
            self.arm_rewards[arm].append(normalized_reward)  # Store JT-aligned reward
            self.arm_contexts[arm].append(context)
            
            # Keep only recent history (prevent memory growth)
            if len(self.arm_rewards[arm]) > 100:
                self.arm_rewards[arm] = self.arm_rewards[arm][-50:]
                self.arm_contexts[arm] = self.arm_contexts[arm][-50:]
        
        logger.info(f"🔥 J_t-OPTIMIZED: user={user_id} arm={arm} J_t={J_t:.6f} normalized={normalized_reward:.3f} α={alpha:.3f} β={beta:.3f}")

    def _adjust_exploration_pressure(self, user_id: str) -> float:
        """
        🔥 JT-AWARE EXPLORATION: Dynamically adjust exploration pressure based on JT volatility

        Governance principle:
        - Stable JT (low volatility) → exploit current knowledge (low exploration)
        - Unstable JT (high volatility) → explore more aggressively (high exploration)

        This makes exploration a governance response to architectural confidence,
        not just heuristic curiosity.

        Args:
            user_id: User identifier

        Returns:
            Adjusted uncertainty_weight multiplier (1.0 = base, >1.0 = more exploration)
        """
        logger.info(f"🔥 JT-AWARE EXPLORATION: Checking user={user_id}, history_size={len(self.jt_history.get(user_id, []))}")

        if user_id not in self.jt_history or len(self.jt_history[user_id]) < 5:
            # Not enough history: use base exploration
            logger.info(f"🔥 JT-AWARE EXPLORATION: user={user_id} has insufficient history (<5), using base exploration")
            return 1.0

        jt_values = self.jt_history[user_id]
        jt_std = np.std(jt_values)
        jt_mean = np.mean(jt_values)

        # Calculate coefficient of variation (normalized volatility)
        # This accounts for magnitude differences
        if abs(jt_mean) < 1e-6:
            cv = 0.0  # Avoid division by zero
        else:
            cv = abs(jt_std / jt_mean)

        # 🔥 GOVERNANCE RULE: Exploration pressure scales with JT instability
        # Low CV (< 0.5) → stable cognition, exploit (0.5x exploration)
        # Medium CV (0.5-2.0) → normal exploration (1.0x exploration)
        # High CV (> 2.0) → unstable cognition, explore (2.0x exploration)
        if cv < 0.5:
            multiplier = 0.5
        elif cv < 2.0:
            multiplier = 1.0
        else:
            multiplier = 2.0

        # Apply the multiplier to the base uncertainty weight
        self.uncertainty_weight = self.base_uncertainty_weight * multiplier

        logger.info(f"🔥 JT-AWARE EXPLORATION: user={user_id} JT_volatility={cv:.3f} exploration_multiplier={multiplier:.1f}")

        return multiplier
    
    def select_arm_contextual_thompson(self, user_id: str, candidates: List[Dict[str, Any]], 
                                  mastery_context: Dict[str, float]) -> Dict[str, Any]:
        """
        Select arm using contextual Thompson sampling with per-user persistence
        
        Args:
            user_id: User identifier
            candidates: List of candidate tasks
            mastery_context: Dict of concept_id -> mastery for contextual guidance
            
        Returns:
            Best task based on contextual Thompson sampling
        """
        best_sample = -1
        best_contextual_score = -1  # Track best contextual score for regret calculation
        best_expected_value = -1  # Track best expected value for true regret
        best_hybrid_score = -1  # Track best hybrid score for decision regret
        
        for task in candidates:
            arm = task["concept_id"]  # 🔥 CONCEPT-LEVEL ARM (better generalization)
            
            # 🔥 GET PER-USER α, β parameters (from Redis or memory) with difficulty-aware mastery-aligned prior
            task_difficulty = task.get("difficulty", 0.5)
            alpha, beta = self._get_alpha_beta(user_id, arm, mastery_context, task_difficulty)
            
            # 🔥 REAL THOMPSON SAMPLING: Sample from Beta posterior
            sample = self.sample_beta(alpha, beta)
            
            # 🔥 CONTEXTUAL BONUS: Add mastery/difficulty guidance
            concept_id = task.get("concept_id", "unknown")
            mastery = mastery_context.get(concept_id, 0.5)
            difficulty = task.get("difficulty", 0.5)
            
            # 🔥 PUBLISHABLE-GRADE CONTEXTUAL SCORING (ZPD-aligned)
            uncertainty = self._calculate_uncertainty(alpha, beta)
            
            # ZPD alignment: prefer tasks near mastery level (Zone of Proximal Development)
            zpd_distance = abs(mastery - difficulty)
            zpd_bonus = math.exp(-zpd_distance**2 / 0.1)  # Gaussian around mastery
            
            # Contextual score: Thompson sample + exploration bonus - ZPD distance penalty
            contextual_score = sample + (0.1 * uncertainty) - (0.2 * zpd_distance) + (0.1 * zpd_bonus)
            
            # 🔥 BOUND CONTEXTUAL SCORE with sigmoid for comparability
            contextual_score = 1.0 / (1.0 + math.exp(-contextual_score))
            
            # 🔥 HYBRID SCORING: Combine Thompson with HCIE policy weight (exploration floor)
            policy_weight = task.get("policy_weight", 1.0)
            final_score = contextual_score * (0.7 + 0.3 * policy_weight)  # Minimum 70% exploration
            
            # 🔥 CALCULATE EXPECTED VALUE FOR TRUE REGRET
            expected_value = alpha / (alpha + beta) if (alpha + beta) > 0 else 0.5
            
            # 🔥 POPULATE ALL METRICS FOR EVERY CANDIDATE (critical for softmax)
            task["thompson_sample"] = sample  # Original Thompson sample
            task["contextual_score"] = contextual_score  # Before policy weighting
            task["hybrid_score"] = final_score  # After policy weighting
            task["policy_weight"] = policy_weight  # HCIE policy influence
            task["policy_effect"] = final_score / contextual_score if contextual_score > 0 else 1.0  # Policy influence ratio
            task["expected_value"] = expected_value  # Expected value for regret
            
            logger.debug(f"🔥 CONTEXTUAL THOMPSON: user={user_id} arm={arm} α={alpha:.3f} β={beta:.3f} sample={sample:.3f} mastery={mastery:.3f} difficulty={difficulty:.3f} zpd_distance={zpd_distance:.3f} zpd_bonus={zpd_bonus:.3f} score={contextual_score:.3f}")
            logger.info(f"🔥 HYBRID DECISION: user={user_id} task={arm} sample={sample:.3f} policy={policy_weight:.3f} final_score={final_score:.3f}")
            
            # 🔥 TRACK BEST SCORES FOR REGRET CALCULATION
            if contextual_score > best_contextual_score:
                best_contextual_score = contextual_score
            if expected_value > best_expected_value:
                best_expected_value = expected_value
            if final_score > best_hybrid_score:
                best_hybrid_score = final_score
            
            if final_score > best_sample:
                best_sample = final_score
                # 🔥 RESEARCH-GRADE LOGGING: Full contextual decision
                logger.info(
                    f"🔥 CONTEXTUAL DECISION: user={user_id} task={arm} "
                    f"sample={sample:.3f} mastery={mastery:.3f} "
                    f"difficulty={difficulty:.3f} zpd={zpd_distance:.3f} "
                    f"zpd_bonus={zpd_bonus:.3f} score={contextual_score:.3f}"
                )
        
        # 🔥 SOFTMAX SELECTION FOR MEANINGFUL DECISION REGRET
        if candidates:
            logger.info(f"🔥 SOFTMAX SELECTION: Processing {len(candidates)} candidates for user={user_id}")
            try:
                # Use softmax selection instead of deterministic argmax
                selected_task, probs = self._softmax_sample(candidates, temperature=0.2)
                logger.info(f"🔥 SOFTMAX SUCCESS: Selected task {selected_task.get('task_id', 'unknown')}")
            except Exception as e:
                logger.error(f"🔥 SOFTMAX ERROR: {e}")
                # Fallback to deterministic selection
                selected_task = max(candidates, key=lambda t: t.get("hybrid_score", 0.0))
                probs = [1.0]
            
            # Calculate uncertainty for the selected task
            selected_alpha, selected_beta = self._get_alpha_beta(user_id, selected_task["concept_id"], mastery_context, selected_task.get("difficulty", 0.5))
            uncertainty = self._calculate_uncertainty(selected_alpha, selected_beta)
            selected_task["exploration_metric"] = uncertainty
            
            # Calculate regrets after selection
            chosen_expected = selected_task["expected_value"]
            chosen_hybrid = selected_task["hybrid_score"]
            
            # Learning regret: Best expected value - Chosen expected value
            learning_regret = max(0.0, best_expected_value - chosen_expected)
            
            # Decision regret: Best hybrid score - Chosen hybrid score (now can be > 0!)
            decision_regret = max(0.0, best_hybrid_score - chosen_hybrid)
            
            selected_task["learning_regret"] = learning_regret
            selected_task["decision_regret"] = decision_regret
            selected_task["regret"] = learning_regret  # Keep backward compatibility
            selected_task["selection_probabilities"] = probs
            
            logger.info(f"🔥 SOFTMAX SELECTED: user={user_id} task={selected_task['task_id']} sample={selected_task['thompson_sample']:.3f} uncertainty={uncertainty:.3f} expected={chosen_expected:.3f} hybrid={chosen_hybrid:.3f} learning_regret={learning_regret:.3f} decision_regret={decision_regret:.3f}")
            
            # 🔥 PERSIST CUMULATIVE REGRET IN REDIS (research-grade)
            if self.redis_client:
                try:
                    # Redis keys for cumulative regret
                    key_lr = f"bandit:regret:lr:{user_id}"
                    key_dr = f"bandit:regret:dr:{user_id}"
                    key_steps = f"bandit:regret:steps:{user_id}"
                    
                    # Increment cumulative regret in Redis
                    self.redis_client.incrbyfloat(key_lr, learning_regret)
                    self.redis_client.incrbyfloat(key_dr, decision_regret)
                    self.redis_client.incrby(key_steps, 1)
                    
                    # Get cumulative values from Redis
                    cumulative_learning = float(self.redis_client.get(key_lr) or 0.0)
                    cumulative_decision = float(self.redis_client.get(key_dr) or 0.0)
                    steps = int(self.redis_client.get(key_steps) or 0)
                    
                    # Also update in-memory for fallback
                    self.cumulative_learning_regret[user_id] = cumulative_learning
                    self.cumulative_decision_regret[user_id] = cumulative_decision
                    self.step_count[user_id] = steps
                    
                    # 🔥 SQL BACKUP: Persist regret to database
                    if self.pg_store:
                        try:
                            sql_lr = """
                            INSERT INTO bandit_regret (user_id, regret_type, cumulative_regret, step_count, last_updated)
                            VALUES (%s, 'learning', %s, %s, CURRENT_TIMESTAMP)
                            ON CONFLICT (user_id, regret_type)
                            DO UPDATE SET
                                cumulative_regret = EXCLUDED.cumulative_regret,
                                step_count = EXCLUDED.step_count,
                                last_updated = CURRENT_TIMESTAMP
                            """
                            sql_dr = """
                            INSERT INTO bandit_regret (user_id, regret_type, cumulative_regret, step_count, last_updated)
                            VALUES (%s, 'decision', %s, %s, CURRENT_TIMESTAMP)
                            ON CONFLICT (user_id, regret_type)
                            DO UPDATE SET
                                cumulative_regret = EXCLUDED.cumulative_regret,
                                step_count = EXCLUDED.step_count,
                                last_updated = CURRENT_TIMESTAMP
                            """
                            # 🔥 FIX: Convert numpy types to native Python types for SQL
                            self.pg_store.execute_write(sql_lr, (
                                user_id, 
                                _convert_numpy(cumulative_learning), 
                                _convert_numpy(steps)
                            ))
                            self.pg_store.execute_write(sql_dr, (
                                user_id, 
                                _convert_numpy(cumulative_decision), 
                                _convert_numpy(steps)
                            ))
                            logger.debug(f"🔥 SQL REGRET BACKUP: {user_id} lr={cumulative_learning:.3f} dr={cumulative_decision:.3f} steps={steps}")
                        except Exception as e:
                            logger.warning(f"🔥 SQL regret backup failed: {e}")
                    
                    # 🔥 STORE CUMULATIVE METRICS IN TASK
                    selected_task["cumulative_learning_regret"] = cumulative_learning
                    selected_task["cumulative_decision_regret"] = cumulative_decision
                    selected_task["steps"] = steps
                    selected_task["avg_learning_regret"] = cumulative_learning / steps if steps > 0 else 0.0
                    selected_task["avg_decision_regret"] = cumulative_decision / steps if steps > 0 else 0.0
                    
                except Exception as e:
                    logger.warning(f"🔥 Redis regret persistence failed: {e}")
                    # Fallback to in-memory
                    self.cumulative_learning_regret[user_id] += learning_regret
                    self.cumulative_decision_regret[user_id] += decision_regret
                    self.step_count[user_id] += 1
                    
                    selected_task["cumulative_learning_regret"] = self.cumulative_learning_regret[user_id]
                    selected_task["cumulative_decision_regret"] = self.cumulative_decision_regret[user_id]
                    selected_task["steps"] = self.step_count[user_id]
                    selected_task["avg_learning_regret"] = self.cumulative_learning_regret[user_id] / self.step_count[user_id]
                    selected_task["avg_decision_regret"] = self.cumulative_decision_regret[user_id] / self.step_count[user_id]
            else:
                # Fallback to in-memory if Redis not available
                self.cumulative_learning_regret[user_id] += learning_regret
                self.cumulative_decision_regret[user_id] += decision_regret
                self.step_count[user_id] += 1
                
                selected_task["cumulative_learning_regret"] = self.cumulative_learning_regret[user_id]
                selected_task["cumulative_decision_regret"] = self.cumulative_decision_regret[user_id]
                selected_task["steps"] = self.step_count[user_id]
                selected_task["avg_learning_regret"] = self.cumulative_learning_regret[user_id] / self.step_count[user_id]
                selected_task["avg_decision_regret"] = self.cumulative_decision_regret[user_id] / self.step_count[user_id]
            
            # 🔥 SAFETY NET: Ensure exploration_metric is always set
            if "exploration_metric" not in selected_task:
                selected_alpha, selected_beta = self._get_alpha_beta(
                    user_id,
                    selected_task["concept_id"],
                    mastery_context,
                    selected_task.get("difficulty", 0.5)
                )
                selected_task["exploration_metric"] = self._calculate_uncertainty(selected_alpha, selected_beta)
                logger.warning(f"🔥 SAFETY NET: Computed exploration_metric for {selected_task.get('task_id', 'unknown')}")
            
            return selected_task
        else:
            return None
    
    def reset_cumulative_regret(self, user_id: str):
        """
        Reset cumulative regret for a user (for testing)
        
        Args:
            user_id: User identifier
        """
        if self.redis_client:
            try:
                # Delete Redis keys
                self.redis_client.delete(f"bandit:regret:lr:{user_id}")
                self.redis_client.delete(f"bandit:regret:dr:{user_id}")
                self.redis_client.delete(f"bandit:regret:steps:{user_id}")
                logger.info(f"🔥 RESET: Cumulative regret reset for user {user_id}")
            except Exception as e:
                logger.warning(f"🔥 RESET failed: {e}")
        
        # Reset SQL backup
        if self.pg_store:
            try:
                sql = """
                DELETE FROM bandit_regret WHERE user_id = %s
                """
                self.pg_store.execute_write(sql, (user_id,))
                logger.info(f"🔥 SQL RESET: Cumulative regret reset for user {user_id}")
            except Exception as e:
                logger.warning(f"🔥 SQL RESET failed: {e}")
        
        # Reset in-memory
        self.cumulative_learning_regret[user_id] = 0.0
        self.cumulative_decision_regret[user_id] = 0.0
        self.step_count[user_id] = 0
    
    def _softmax_sample(self, candidates: List[Dict], temperature: float = 0.2) -> Tuple[Dict, List[float]]:
        """
        Probabilistic selection using softmax for meaningful decision regret
        
        Args:
            candidates: List of candidate tasks
            temperature: Temperature parameter (lower = more greedy, higher = more exploratory)
            
        Returns:
            Selected task and probability distribution
        """
        try:
            # Extract hybrid scores
            scores = np.array([task.get("hybrid_score", 0.0) for task in candidates])
            
            # Stabilize numerically
            scores = scores - np.max(scores)
            
            # Apply softmax
            exp_scores = np.exp(scores / temperature)
            probs = exp_scores / np.sum(exp_scores)
            
            # Probabilistic selection (🔥 FIX F1: seeded RNG stream when provided, else global np.random)
            _rng = self.rng_stream if self.rng_stream is not None else np.random
            idx = _rng.choice(len(candidates), p=probs)
            selected_task = candidates[idx]
            
            return selected_task, probs.tolist()
            
        except Exception as e:
            logger.warning(f"Softmax selection failed: {e}")
            # Fallback to deterministic selection
            return max(candidates, key=lambda t: t.get("hybrid_score", 0.0)), [1.0]
    
    def _calculate_uncertainty(self, alpha: float, beta: float) -> float:
        """
        Calculate uncertainty from Beta distribution
        
        Args:
            alpha: Alpha parameter
            beta: Beta parameter
            
        Returns:
            Uncertainty measure (standard deviation)
        """
        if alpha <= 0 or beta <= 0:
            return 1.0
        
        # Beta distribution variance
        total = alpha + beta
        variance = (alpha * beta) / (total * total * (total + 1))
        
        return math.sqrt(variance)
    
    def select_arm(self,
                   user_id: str,
                   available_nodes: List[str],
                   mastery_params: Dict[str, Tuple[float, float]],
                   representation_params: Dict[str, Tuple[float, float]],
                   difficulty_map: Dict[str, float],
                   context: Dict[str, any] = None) -> Tuple[str, str, float]:
        """
        Select best (node, representation) arm using Thompson sampling

        Returns:
            (best_node, best_representation, score)
        """
        # 🔥 JT-AWARE EXPLORATION: Adjust exploration pressure based on JT volatility
        # This makes exploration a governance response to architectural confidence
        self._adjust_exploration_pressure(user_id)

        best_node = None
        best_representation = None
        best_score = -float('inf')
        
        for node in available_nodes:
            # Get mastery parameters
            alpha, beta = mastery_params.get(node, (1.0, 1.0))
            mastery_sample = self.sample_beta(alpha, beta)
            # Calculate uncertainty with safeguards against negative values
            if (alpha + beta) > 0 and alpha > 0 and beta > 0:
                variance = (alpha * beta) / ((alpha + beta) ** 2 * (alpha + beta + 1))
                uncertainty = math.sqrt(max(0.0, variance))  # Ensure non-negative
            else:
                uncertainty = 0.25
            
            difficulty = difficulty_map.get(node, 0.5)

            # 🔥 JT-NATIVE: Use historical JT instead of heuristic learning_gain
            # This makes exploration governance-native
            if user_id in self.jt_history and len(self.jt_history[user_id]) > 0:
                # Use historical average raw JT for this user (not arm-specific for simplicity)
                # This allows the bandit to learn global JT patterns while maintaining arm-specific alpha/beta
                historical_J = np.mean(self.jt_history[user_id])
                # 🔥 PHASE 4: Use sigmoid normalization for enhanced equilibrium sensitivity
                normalized_J = self._sigmoid_normalize_JT(historical_J, k=15.0)
                learning_gain = normalized_J
            else:
                # No history: use neutral value (allows exploration)
                learning_gain = 0.5

            for representation in self.representations:
                # Get representation parameters
                arm = f"{node}:{representation}"
                rep_alpha, rep_beta = representation_params.get(arm, (1.0, 1.0))
                representation_sample = self.sample_beta(rep_alpha, rep_beta)

                # Calculate Thompson score with JT-native reward
                score = self.calculate_thompson_score(
                    mastery_sample, representation_sample, uncertainty, difficulty, learning_gain
                )
                
                if score > best_score:
                    best_score = score
                    best_node = node
                    best_representation = representation
        
        return best_node, best_representation, best_score
    
    def _calculate_learning_gain(self, alpha: float, beta: float, difficulty: float) -> float:
        """
        Calculate expected learning gain from attempting an item
        """
        mastery = alpha / (alpha + beta) if (alpha + beta) > 0 else 0.5
        
        # Calculate uncertainty with safeguards against negative values
        if (alpha + beta) > 0 and alpha > 0 and beta > 0:
            variance = (alpha * beta) / ((alpha + beta) ** 2 * (alpha + beta + 1))
            uncertainty = math.sqrt(max(0.0, variance))  # Ensure non-negative
        else:
            uncertainty = 0.25
        
        # Learning gain is highest when difficulty is close to mastery
        difficulty_match = 1 - abs(mastery - difficulty)
        
        return 0.1 * difficulty_match * uncertainty
    
    def select_representation(self,
                            user_id: str,
                            concept: str,
                            available_representations: List[str],
                            representation_params: Optional[Dict[str, Tuple[float, float]]] = None) -> str:
        """
        Thompson-sample the best material representation (modality) for a concept.

        Each representation gets a Beta(alpha, beta) success belief from
        ``representation_params`` (keyed by representation name). A representation
        with no recorded outcomes falls back to the uninformative prior (1, 1), so
        unseen modalities are still explored. The representation with the highest
        posterior sample wins — exactly the explore/exploit trade-off that lets a
        learner who does better with, say, video get steered toward video.

        Args:
            user_id: learner identifier (for logging / determinism context)
            concept: concept identifier
            available_representations: representations actually available for this
                concept (e.g. ['text', 'video_question', 'mcq'])
            representation_params: {representation: (alpha, beta)} success priors

        Returns:
            The selected representation (falls back to the first available, then to
            the configured default).
        """
        if not available_representations:
            return self.representations[0] if self.representations else "text"
        params = representation_params or {}
        best_rep: Optional[str] = None
        best_sample = -1.0
        for rep in available_representations:
            alpha, beta = params.get(rep, (1.0, 1.0))
            try:
                sample = self.sample_beta(float(alpha), float(beta))
            except Exception:
                sample = 0.5
            if sample > best_sample:
                best_sample = sample
                best_rep = rep
        return best_rep if best_rep is not None else available_representations[0]
    
    def compute_orchestration_metrics(
        self,
        ranked_candidates: List[Tuple[str, float]],
        selected_concept: str
    ) -> Dict[str, Any]:
        """
        🔥 PHASE 3C: Compute selection metrics for observability

        Args:
            ranked_candidates: Full governance ranking
            selected_concept: The concept that was selected

        Returns:
            Dict with orchestration metrics
        """
        if not ranked_candidates:
            return {"error": "empty_ranking"}

        concept_to_rank = {c: i for i, (c, _) in enumerate(ranked_candidates)}
        concept_to_score = {c: s for c, s in ranked_candidates}

        selected_rank = concept_to_rank.get(selected_concept, -1)
        selected_score = concept_to_score.get(selected_concept, 0.0)

        # Compute selection distribution statistics
        scores = [s for _, s in ranked_candidates]
        score_variance = np.var(scores) if scores else 0.0
        score_entropy = -np.sum([s * np.log(s + 1e-10) for s in scores if s > 0]) if scores else 0.0

        return {
            "selected_rank": selected_rank,
            "selected_score": float(selected_score),
            "ranking_size": len(ranked_candidates),
            "score_variance": float(score_variance),
            "score_entropy": float(score_entropy),
            "top_score": float(max(scores)) if scores else 0.0,
            "score_spread": float(max(scores) - min(scores)) if scores else 0.0,
            "mode": "orchestration_only",
            "authority": "unified_brain"
        }
