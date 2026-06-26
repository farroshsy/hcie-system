"""
Task service layer — transitional adapter over Phase 14e ItsRuntimeService.

New production ingress should call ``/v3/its/*`` via ``hcie.entrypoints.api``.
This module keeps legacy response shapes for V2 callers while delegating
recommend/attempt paths to the DI-built ITS spine when available.
"""

import json
import logging
import os
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

from config.env import settings

from app.telemetry import get_submission_counter, get_transfer_events_counter, get_mastery_updates_counter, get_latency_histogram

# Import factory for pluggable learners
from core.learning.learner_factory import LearnerFactory

# Import models for learner initialization
from core.mastery.mastery_model import MasteryModel
from core.learning.transfer_learning_engine import TransferLearningEngine
from core.learning.unified_brain import UnifiedLearningBrain
from core.bandit.bandit import ContextualBandit
from core.policy.policy import PolicyEngine
from core.reward.reward import RewardCalculator
from core.learning.learner_factory import LearnerFactory
from storage.redis_store.redis_store import RedisFeatureStore, create_redis_feature_store
from storage.postgres_store.interaction_store import PostgresInteractionStore, get_postgres_interaction_store

from app.models.requests import TaskSubmission
from app.models.responses import TaskSubmissionResponse

logger = logging.getLogger(__name__)

class TaskService:
    """Stateless service layer for task operations with dual-mode support (CT/EdNet)"""
    
    def __init__(self):
        """Initialize TaskService with all required components"""
        self._its_runtime_cached = None
        # Initialize storage
        self.redis_store = create_redis_feature_store(settings.redis_host)
        self.postgres_store = get_postgres_interaction_store()
        
        self.reward_calculator = RewardCalculator()
        
        # ✅ THEN: initialize dependencies
        self.mastery_model = MasteryModel()
        self.transfer_engine = TransferLearningEngine(
            transfer_decay_rate=0.01,
            min_transfer_threshold=0.0005,
            max_transfer_boost=0.6
        )
        
        # 🔥 PRODUCTION: Initialize Outbox pattern for atomic event publishing
        event_bus = None
        outbox = None
        try:
            # Create event bus first (needed by outbox)
            from app.infrastructure.messaging.event_bus import KafkaEventBus
            from app.infrastructure.kafka.kafka_factory import KafkaFactory, DefaultKafkaProducerFactory
            
            kafka_factory = KafkaFactory(settings, producer_factory=DefaultKafkaProducerFactory())
            kafka_producer = kafka_factory.create_producer()
            event_bus = KafkaEventBus(kafka_producer)
            logger.info("🔥 Event bus created for Outbox pattern")
            
            # Create outbox pattern for atomic publishing
            from app.infrastructure.outbox.outbox_pattern import OutboxPattern
            outbox = OutboxPattern(
                db_store=self.postgres_store,
                event_bus=event_bus
            )
            logger.info("🔥 Outbox pattern initialized for atomic event publishing")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to initialize Outbox pattern for UnifiedLearningBrain: {e}")

        # 🔥 TRAJECTORY: Initialize trajectory recorder for automatic capture
        trajectory_recorder = None
        try:
            if getattr(settings, "enable_trajectory_recording", False):
                from infrastructure.experiment.trajectory_recorder import TrajectoryRecorder
                from storage.postgres_store.interaction_store import PostgresInteractionStore
                postgres_store = PostgresInteractionStore()
                trajectory_recorder = TrajectoryRecorder(postgres_store)
                logger.info("🔥 Trajectory recorder initialized in TaskService")
        except Exception as e:
            logger.warning(f"⚠️ Failed to initialize trajectory recorder in TaskService: {e}")

        # 🔥 PRODUCTION-FIRST: Inject Outbox to UnifiedBrain
        # Slice 0a removed `system_mode` (was hardcoded JT in practice).
        self.unified_brain = UnifiedLearningBrain(
            event_bus=event_bus,  # Fallback for dev mode
            outbox=outbox,        # Production mode
            trajectory_recorder=trajectory_recorder  # 🔥 TRAJECTORY: Automatic capture
        )
        logger.info("🔥 UnifiedLearningBrain initialized in TaskService with Outbox integration")
        
        # 🔥 FIX: Load real database dependencies
        try:
            from storage.postgres_store.interaction_store import PostgresInteractionStore
            store = PostgresInteractionStore()
            dependencies = store.get_concept_dependencies()
            
            if dependencies:
                self.transfer_engine.load_concept_dependencies(dependencies)
                logger.info(f"🔥 TASK SERVICE: Loaded {len(dependencies)} database dependencies")
            else:
                logger.warning("⚠️ TASK SERVICE: No dependencies found in database")
        except Exception as e:
            logger.error(f"❌ TASK SERVICE: Failed to load dependencies: {e}")
        
        # ✅ FINALLY: initialize learner factory with StateAdapter
        self.learner_factory = LearnerFactory(
            redis_store=self.redis_store,
            transfer_engine=self.transfer_engine,
            mastery_model=self.mastery_model
        )
        
        # 🔥 CLOSED LOOP: Initialize contextual bandit
        self.bandit = ContextualBandit(
            uncertainty_weight=0.1,
            learning_gain_weight=0.05,
            representations=["text", "code", "multiple_choice", "video", "interactive"]
        )
        
    def _degraded_task_response(
        self,
        user_id: str,
        policy_mode: str,
        reason: str,
    ) -> Dict[str, Any]:
        # Degraded selection response. Per final_intent section 7 ban list this
        # path emits no synthetic mastery or fabricated selection metrics; the
        # caller observes the divergence through policy_type and reason.
        return {
            "user_id": user_id,
            "task_id": None,
            "concept_id": None,
            "representation": None,
            "difficulty": None,
            "question_text": None,
            "choices": [],
            "policy_mode": policy_mode,
            "timestamp": datetime.utcnow().timestamp(),
            "selection_metrics": {
                "policy_type": "degraded",
                "reason": reason,
                "candidates_count": 0,
            },
        }

    def _its_runtime(self):
        """Lazy Phase 14e façade (Container-built)."""
        if getattr(self, "_its_runtime_cached", None) is not None:
            return self._its_runtime_cached
        self._its_runtime_cached = None
        if os.getenv("HCIE_USE_ITS_ADAPTER", "1") != "1":
            return None
        try:
            from app.infrastructure.di.get_container import get_container

            self._its_runtime_cached = get_container().its_runtime_service()
        except Exception as exc:
            logger.debug("ITS runtime adapter unavailable: %s", exc)
        return self._its_runtime_cached

    def _generate_task_via_its(
        self,
        user_id: str,
        policy_mode: str,
        concept_filter: Optional[List[str]],
    ) -> Optional[Dict[str, Any]]:
        its = self._its_runtime()
        if its is None:
            return None
        from app.runtime.its_runtime_service import RuntimeDegraded

        try:
            view = its.recommend(
                user_id,
                policy_mode=policy_mode,
                concept_filter=concept_filter,
            )
        except RuntimeDegraded as exc:
            return self._degraded_task_response(
                user_id=user_id,
                policy_mode=policy_mode,
                reason=exc.reason,
            )
        return {
            "user_id": view.user_id,
            "task_id": view.task_id,
            "concept_id": view.concept_id,
            "representation": view.representation,
            "difficulty": view.difficulty,
            "question_text": view.question_text,
            "choices": view.choices,
            "policy_mode": view.policy_mode,
            "timestamp": datetime.utcnow().timestamp(),
            "selection_metrics": view.selection_metrics,
        }

    def _process_submission_via_its(self, submission: TaskSubmission) -> Optional[Dict[str, Any]]:
        its = self._its_runtime()
        if its is None:
            return None
        result = its.submit_attempt(
            submission.user_id,
            task_id=submission.task_id,
            concept_id=submission.node_id,
            answer=submission.answer,
            response_time=getattr(submission, "response_time", 10.0),
        )
        return {
            "user_id": result.user_id,
            "event_id": result.event_id,
            "concept_id": result.concept_id,
            "correct": result.correct,
            "mastery": result.mastery,
            "processing_mode": "its_runtime",
            "payload": result.payload,
        }

    def _build_bandit_context(self, user_id: str, concept_id: str, representation: str) -> Dict[str, float]:
        """Build context for contextual bandit decision"""
        try:
            # Get learner for mastery state
            learner = self.learner_factory.get("lyapunov")
            mastery_state = learner.get_state(user_id, concept_id)
            
            # Handle different mastery state formats
            if isinstance(mastery_state, tuple):
                mastery = mastery_state[0]
            elif isinstance(mastery_state, dict):
                mastery = mastery_state.get("mastery", 0.3)
            else:
                mastery = float(mastery_state) if mastery_state else 0.3
                
            return {
                "mastery": mastery,
                "representation": 1.0 if representation in ["text", "multiple_choice"] else 0.5,
                "difficulty": 0.5,  # TODO: get from task data
                "uncertainty": 1.0 - mastery,
                "learning_gain": 0.0  # Unknown before action
            }
        except Exception as e:
            logger.warning(f"Failed to build bandit context: {e}")
            return {
                "mastery": 0.3,
                "representation": 1.0,
                "difficulty": 0.5,
                "uncertainty": 0.7,
                "learning_gain": 0.0
            }
    
    def _get_candidate_tasks(self, user_id: str, difficulty_range: Optional[tuple[float, float]] = None, 
                             concept_filter: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """🔥 Get REAL candidate tasks from database for bandit selection"""
        candidates = []
        
        try:
            logger.error(f"🔥 DEBUG: Starting candidate pool for {user_id}")
            
            # 🔥 K-12 CONCEPTS ONLY: Query K-12 concepts directly
            if concept_filter:
                # Query K-12 concepts directly (new system)
                available_concepts = concept_filter  # Use K-12 concept IDs directly
                logger.info(f"🔥 Using K-12 concepts directly: {available_concepts}")
                
                # Get MULTIPLE UNIQUE tasks from K-12 concepts for proper bandit selection
                candidates = []
                tasks_per_concept = 3  # Get 3 tasks per concept for variety
                
                for concept_id in available_concepts:
                    # Get ALL tasks for this concept, then sample unique ones
                    query = """
                        SELECT id, concept_id, difficulty, task_type, content, solution, hints, metadata,
                               media_url, media_type, transcript
                        FROM tasks 
                        WHERE concept_id = %s AND concept_type = 'k12'
                        ORDER BY RANDOM()
                    """
                    
                    try:
                        all_tasks = self.postgres_store.execute_read(query, (concept_id,))
                        if all_tasks and len(all_tasks) > 0:
                            # Take unique tasks (limit to tasks_per_concept)
                            concept_tasks = []
                            seen_task_ids = set()
                            
                            for row in all_tasks:
                                if row["id"] not in seen_task_ids:
                                    concept_tasks.append({
                                        "task_id": row["id"],
                                        "concept_id": row["concept_id"],
                                        "difficulty": float(row["difficulty"]),
                                        "representation": row["task_type"] if row.get("task_type") else "text",
                                        "task_type": row.get("task_type"),
                                        "content": row.get("content") or {},
                                        "media_url": row.get("media_url"),
                                        "media_type": row.get("media_type"),
                                        "transcript": row.get("transcript"),
                                    })
                                    seen_task_ids.add(row["id"])
                                
                                if len(concept_tasks) >= tasks_per_concept:
                                    break
                            
                            candidates.extend(concept_tasks)
                            logger.info(f"🔥 K-12 CONCEPT {concept_id}: {len(concept_tasks)} unique tasks found")
                        else:
                            logger.error(f"❌ No K-12 tasks found for {concept_id}")
                    except Exception as e:
                        logger.error(f"❌ Failed to get tasks for {concept_id}: {e}")
                
                if candidates:
                    logger.info(f"🔥 TOTAL CANDIDATES: {len(candidates)} tasks for bandit selection")
                    return candidates
                else:
                    # If no K-12 tasks found, fallback to basic_task
                    logger.error(f"❌ No K-12 tasks found for any concept in {available_concepts}")
                    return [{"task_id": "basic_task", "concept_id": None}]
            else:
                # No concept filter - use K-12 concepts by default
                default_concepts = ["k2_algorithms", "k5_algorithms", "k8_algorithms"]
                candidates = []
                tasks_per_concept = 3
                
                for concept_id in default_concepts:
                    concept_tasks = []
                    for attempt in range(tasks_per_concept):
                        task = self.get_random_task_for_concept(concept_id)
                        if task:
                            concept_tasks.append(task)
                    
                    if concept_tasks:
                        candidates.extend(concept_tasks)
                        logger.info(f"🔥 DEFAULT CONCEPT {concept_id}: {len(concept_tasks)} tasks found")
                
                if candidates:
                    logger.info(f"🔥 DEFAULT TOTAL CANDIDATES: {len(candidates)} tasks")
                    return candidates
                else:
                    logger.error("❌ No default K-12 tasks found")
                    return [{"task_id": "basic_task", "concept_id": None}]
                    
        except Exception as e:
            logger.error(f"❌ Task generation failed: {e}")
            return {"task_id": "basic_task", "concept_id": None}
    
    def _optimize_with_unified_brain(self, candidates: List[Dict], user_id: str) -> Dict[str, Any]:
        """
        🔥 UNIFIED BRAIN: Use UnifiedLearningBrain for advanced task selection
        
        Args:
            candidates: List of candidate tasks
            user_id: User identifier
            
        Returns:
            Optimized task selection with unified brain insights
        """
        try:
            logger.info(f"🔥 UNIFIED BRAIN OPTIMIZATION: {len(candidates)} candidates for {user_id}")
            
            # Get objective function value for current state
            current_J = self.unified_brain.get_objective_function()
            logger.info(f"🔥 Current objective function J: {current_J:.6f}")
            
            # Use unified brain to optimize for best action
            candidate_actions = [task.get("concept_id", "unknown") for task in candidates]
            best_concept = self.unified_brain.optimize_for_objective(candidate_actions)
            
            # Find the task with the best concept
            best_task = None
            for task in candidates:
                if task.get("concept_id") == best_concept:
                    best_task = task
                    break
            
            if best_task:
                # Get mastery context using unified brain
                mastery_context = self._get_mastery_context(user_id, candidates)
                
                # Add unified brain insights to the task
                best_task["unified_brain_optimized"] = True
                best_task["objective_function_J"] = current_J
                best_task["selected_concept"] = best_concept
                best_task["mastery_context"] = mastery_context
                
                logger.info(f"🔥 UNIFIED BRAIN SELECTED: {best_concept} (J: {current_J:.6f})")
                return best_task
            else:
                logger.warning(f"🔥 UNIFIED BRAIN: No task found for concept {best_concept}")
                return candidates[0] if candidates else None
                
        except Exception as e:
            logger.error(f"❌ Unified brain optimization failed: {e}")
            # Fallback to first candidate
            return candidates[0] if candidates else None
    
    def _apply_concept_level_filter(self, candidates: List[Dict], user_id: str, max_level_distance: int = 1) -> List[Dict]:
        """
        Filter candidates by cognitive level proximity to user's current level
        
        Args:
            candidates: List of candidate tasks
            user_id: User identifier
            max_level_distance: Maximum allowed cognitive level difference
            
        Returns:
            Filtered list of tasks at appropriate cognitive level
        """
        try:
            # Get user's current cognitive level from mastery
            user_level = self._estimate_user_cognitive_level(user_id)
            
            # Get concept levels from database
            concept_levels = self._get_concept_levels()
            
            filtered = []
            for task in candidates:
                concept_id = task.get("concept_id", "")
                concept_level = concept_levels.get(concept_id, 2)  # Default to intermediate
                
                level_distance = abs(concept_level - user_level)
                
                if level_distance <= max_level_distance:
                    filtered.append(task)
                    logger.debug(f"🔥 LEVEL FILTER: {concept_id} level={concept_level} user_level={user_level} distance={level_distance} ✓")
                else:
                    logger.debug(f"🔥 LEVEL FILTER: {concept_id} level={concept_level} user_level={user_level} distance={level_distance} ✗ (too advanced/basic)")
            
            # Fallback: don't kill exploration
            if len(filtered) >= 2:
                logger.info(f"🔥 LEVEL FILTERED: {len(filtered)}/{len(candidates)} tasks at appropriate cognitive level")
                return filtered
            else:
                logger.warning(f"🔥 LEVEL FILTER: Only {len(filtered)} tasks at level, using all {len(candidates)} candidates")
                return candidates
                
        except Exception as e:
            logger.warning(f"Concept level filtering failed: {e}")
            return candidates
    
    def _estimate_user_cognitive_level(self, user_id: str) -> int:
        """
        Estimate user's cognitive level based on mastery patterns
        
        Args:
            user_id: User identifier
            
        Returns:
            Estimated cognitive level (1=basic, 2=intermediate, 3=advanced)
        """
        try:
            # Get mastery directly from learners to avoid circular dependency
            mastery_values = []
            for learner_type in ["lyapunov", "bayesian", "kalman"]:
                try:
                    # Get mastery for K-12 CS Framework concepts
                    k12_concepts = ["k2_algorithms", "k5_algorithms", "k8_algorithms", "k12_algorithms",
                                   "k2_data_collection", "k5_data_collection", "k8_data_collection", "k12_data_collection",
                                   "k2_networks_communication", "k5_networks_communication", "k8_networks_communication"]
                    
                    for concept_id in k12_concepts:
                        try:
                            state = self.learner_factory.state_adapter.get(learner_type, user_id, concept_id)
                            if state and hasattr(state, 'mastery'):
                                mastery_values.append(float(state.mastery))
                                break  # Use first learner that has data
                        except:
                            continue
                            
                    if mastery_values:
                        break  # Got some mastery data
                except:
                    continue
            
            if not mastery_values:
                return 2  # Default to intermediate
            
            # Calculate average mastery
            avg_mastery = sum(mastery_values) / len(mastery_values)
            
            # Map mastery to cognitive level
            if avg_mastery < 0.4:
                return 1  # Basic
            elif avg_mastery < 0.7:
                return 2  # Intermediate
            else:
                return 3  # Advanced
                
        except Exception as e:
            logger.warning(f"Failed to estimate cognitive level for {user_id}: {e}")
            return 2  # Default to intermediate
    
    def _get_concept_levels(self) -> Dict[str, int]:
        """
        Get cognitive levels for all concepts from database
        
        Returns:
            Dict of concept_id -> cognitive_level (1-3)
        """
        # Sources cognitive_level from canonical K-12 schema seeded by
        # alembic 009_seed_k12_concepts. CT path retired in Phase 14c.
        try:
            rows = self.postgres_store.execute_read(
                "SELECT id, cognitive_level FROM k12_concepts"
            )
            concept_levels: Dict[str, int] = {}
            for row in rows or []:
                level_raw = row.get("cognitive_level")
                try:
                    level = int(level_raw) if level_raw is not None else 2
                except (TypeError, ValueError):
                    level = 2
                if level not in (1, 2, 3, 4):
                    level = 2
                concept_levels[row["id"]] = level
            return concept_levels
        except Exception as e:
            logger.warning(f"Failed to get k12 concept levels: {e}")
            return {}
    
    def _get_mastery_context(self, user_id: str, candidates: List[Dict] = None) -> Dict[str, float]:
        """
        Get current mastery levels using UnifiedLearningBrain
        
        Args:
            user_id: User identifier
            candidates: List of candidate tasks to extract concepts from
            
        Returns:
            Dict of concept_id -> mastery level
        """
        try:
            #  UNIFIED BRAIN: Extract concepts from actual candidates
            mastery_context = {}
            
            # Get unique concepts from candidates
            target_concepts = set()
            if candidates:
                for task in candidates:
                    concept_id = task.get("concept_id", "")
                    if concept_id:  # Include all concepts (K-12 and CT)
                        target_concepts.add(concept_id)
            
            logger.info(f" UNIFIED BRAIN TARGET CONCEPTS: {target_concepts}")
            
            #  USE UNIFIED BRAIN for mastery inference
            for concept_id in target_concepts:
                try:
                    # Use UnifiedLearningBrain for READ mode inference
                    learning_result = self.unified_brain.process_event(
                        user_id=user_id,
                        concept=concept_id,
                        interaction=None,
                        mode="read"  # Inference mode
                    )
                    
                    # Extract mastery from unified brain result
                    mastery = learning_result.mastery if hasattr(learning_result, 'mastery') else 0.3
                    mastery_context[concept_id] = mastery
                    
                    logger.info(f" UNIFIED BRAIN MASTERY: {user_id}/{concept_id} = {mastery:.3f}")
                    
                except Exception as e:
                    logger.warning(f" Unified brain mastery failed for {concept_id}: {e}")
                    # Fallback to default mastery
                    mastery_context[concept_id] = 0.3
            
            return mastery_context
            
        except Exception as e:
            logger.error(f" Unified brain mastery context failed: {e}")
            return {}  # Empty context -> default priors
    
    def _apply_zpd_filter(self, candidates: List[Dict], mastery_context: Dict[str, float], max_distance: float = 0.4) -> List[Dict]:
        """
        Filter candidates to stay within Zone of Proximal Development
        
        Args:
            candidates: List of candidate tasks
            mastery_context: Dict of concept_id -> mastery level
            max_distance: Maximum allowed |mastery - difficulty| distance
            
        Returns:
            Filtered list of tasks within ZPD
        """
        filtered = []
        
        for task in candidates:
            concept = task.get("concept_id", "")
            difficulty = task.get("difficulty", 0.5)
            mastery = mastery_context.get(concept, 0.3)  # Default to novice mastery
            
            distance = abs(mastery - difficulty)
            
            if distance <= max_distance:
                filtered.append(task)
                logger.debug(f"🔥 ZPD FILTER: {concept} mastery={mastery:.3f} difficulty={difficulty:.3f} distance={distance:.3f} ✓")
            else:
                logger.debug(f"🔥 ZPD FILTER: {concept} mastery={mastery:.3f} difficulty={difficulty:.3f} distance={distance:.3f} ✗ (too hard/easy)")
        
        # Fallback: don't kill exploration - ensure we have at least 2 candidates
        if len(filtered) >= 2:
            logger.info(f"🔥 ZPD FILTERED: {len(filtered)}/{len(candidates)} tasks within optimal learning zone")
            return filtered
        else:
            logger.warning(f"🔥 ZPD FILTER: Only {len(filtered)} tasks in zone, using all {len(candidates)} candidates")
            return candidates
    
    def _apply_hcie_policy_filter(self, user_id: str, candidates: List[Dict], policy_mode: str) -> List[Dict]:
        """
        Apply HCIE policy constraints to candidate pool
        
        Args:
            user_id: User identifier
            candidates: List of candidate tasks
            policy_mode: Policy mode ("hcie", "dag", "random")
            
        Returns:
            HCIE-filtered candidate pool
        """
        try:
            if policy_mode == "random":
                logger.info("🔥 HCIE POLICY: Random mode - no filtering applied")
                return candidates
            
            elif policy_mode == "dag":
                # DAG-based progression: enforce prerequisites
                candidates = self._filter_by_prerequisites(user_id, candidates)
                logger.info(f"🔥 HCIE POLICY: DAG mode - {len(candidates)} candidates after prerequisite filtering")
                return candidates
            
            elif policy_mode == "hcie":
                # HCIE mode: focus on weak mastery areas
                candidates = self._filter_by_mastery_weakness(user_id, candidates)
                logger.info(f"🔥 HCIE POLICY: HCIE mode - {len(candidates)} candidates after weakness filtering")
                return candidates
            
            else:
                # Default: no HCIE filtering
                logger.warning(f"🔥 HCIE POLICY: Unknown mode '{policy_mode}', using all candidates")
                return candidates
                
        except Exception as e:
            logger.error(f"HCIE policy filtering failed: {e}")
            return candidates
    
    def _filter_by_prerequisites(self, user_id: str, candidates: List[Dict]) -> List[Dict]:
        """
        Filter candidates based on DAG prerequisites
        
        Args:
            user_id: User identifier
            candidates: List of candidate tasks
            
        Returns:
            Candidates with satisfied prerequisites
        """
        try:
            # Get user's mastered concepts
            mastered_concepts = self._get_mastered_concepts(user_id)
            
            filtered = []
            for task in candidates:
                concept_id = task.get("concept_id", "")
                
                # Get prerequisites for this concept
                prerequisites = self._get_concept_prerequisites(concept_id)
                
                # Check if all prerequisites are mastered (mastery > 0.6)
                prereq_satisfied = True
                for prereq in prerequisites:
                    if mastered_concepts.get(prereq, 0.0) < 0.6:
                        prereq_satisfied = False
                        break
                
                if prereq_satisfied:
                    filtered.append(task)
                    logger.debug(f"🔥 DAG FILTER: {concept_id} prerequisites satisfied ✓")
                else:
                    logger.debug(f"🔥 DAG FILTER: {concept_id} prerequisites not met ✗")
            
            return filtered
            
        except Exception as e:
            logger.warning(f"DAG prerequisite filtering failed: {e}")
            return candidates
    
    def _filter_by_mastery_weakness(self, user_id: str, candidates: List[Dict]) -> List[Dict]:
        """
        Filter candidates to focus on weak mastery areas (HCIE policy)
        
        Args:
            user_id: User identifier
            candidates: List of candidate tasks
            
        Returns:
            Candidates focusing on weak areas
        """
        try:
            mastery_context = self._get_mastery_context(user_id, candidates)
            
            # HCIE rule: focus on concepts with mastery < 0.7
            filtered = []
            for task in candidates:
                concept_id = task.get("concept_id", "")
                mastery = mastery_context.get(concept_id, 0.3)
                
                if mastery < 0.7:
                    filtered.append(task)
                    logger.debug(f"🔥 HCIE FILTER: {concept_id} mastery={mastery:.3f} (weak area) ✓")
                else:
                    logger.debug(f"🔥 HCIE FILTER: {concept_id} mastery={mastery:.3f} (already strong) ✗")
            
            # Ensure we have candidates for exploration
            if len(filtered) >= 2:
                return filtered
            else:
                logger.warning(f"🔥 HCIE FILTER: Only {len(filtered)} weak areas, using all {len(candidates)} candidates")
                return candidates
                
        except Exception as e:
            logger.warning(f"HCIE mastery weakness filtering failed: {e}")
            return candidates
    
    def _get_mastered_concepts(self, user_id: str) -> Dict[str, float]:
        """
        Get user's current mastery levels
        
        Args:
            user_id: User identifier
            
        Returns:
            Dict of concept_id -> mastery level
        """
        try:
            mastery_context = self._get_mastery_context(user_id)
            return mastery_context
        except Exception as e:
            logger.warning(f"Failed to get mastered concepts: {e}")
            return {}
    
    def get_random_task_for_concept(self, concept_id: str) -> Dict[str, Any]:
        """Fetch a random task for a given concept from K-12 tasks table"""
        query = """
            SELECT id, concept_id, difficulty, task_type, content, solution, hints, metadata
            FROM tasks 
            WHERE concept_id = %s AND concept_type = 'k12'
            ORDER BY RANDOM() 
            LIMIT 1
        """
        
        try:
            result = self.postgres_store.execute_read(query, (concept_id,))
            if result and len(result) > 0:
                row = result[0]
                if row:
                    return {
                        "task_id": row["id"],
                        "concept_id": row["concept_id"],
                        "difficulty": float(row["difficulty"]),
                        "representation": row["task_type"] if row.get("task_type") else "text"
                    }
        except Exception as e:
            logger.error(f"❌ K-12 task query failed: {e}")
        
        # No CT fallback - we only support K-12 concepts now
        raise ValueError(f"K-12 task {concept_id} not found")

    def _get_concept_prerequisites(self, concept_id: str) -> List[str]:
        """
        Get prerequisites for a concept
        
        Args:
            concept_id: Concept identifier
            
        Returns:
            List of prerequisite concept IDs
        """
        # Prerequisite edges live in concept_dependencies (canonical K-12
        # DAG seeder). CT path retired in Phase 14c.
        try:
            rows = self.postgres_store.execute_read(
                """
                SELECT source_concept AS prerequisite
                FROM concept_dependencies
                WHERE target_concept = %s
                  AND dependency_type = 'prerequisite'
                ORDER BY source_concept
                """,
                (concept_id,),
            )
            return [r["prerequisite"] for r in rows or [] if r.get("prerequisite")]
        except Exception as e:
            logger.warning(f"Failed to get prerequisites for {concept_id}: {e}")
            return []
    
    def _compute_hcie_weight(self, user_id: str, task: Dict, mastery_context: Dict[str, float]) -> float:
        """
        Soft HCIE policy weight instead of hard filtering
        Returns value in [0, 1]
        """
        try:
            import math
            
            concept = task.get("concept_id", "")
            difficulty = task.get("difficulty", 0.5)
            mastery = mastery_context.get(concept, 0.3)
            
            # 🔥 1. Weakness targeting (HCIE core)
            weakness_weight = 1.0 - mastery  # lower mastery = higher weight
            
            # 🔥 2. ZPD alignment (soft preference)
            zpd_distance = abs(mastery - difficulty)
            zpd_weight = math.exp(-zpd_distance**2 / 0.1)
            
            # 🔥 3. Cognitive level alignment
            user_level = self._estimate_user_cognitive_level(user_id)
            concept_levels = self._get_concept_levels()
            concept_level = concept_levels.get(concept, 2)
            
            level_distance = abs(concept_level - user_level)
            level_weight = math.exp(-level_distance)
            
            # 🔥 FINAL POLICY WEIGHT (tunable)
            policy_weight = (
                0.5 * weakness_weight +
                0.3 * zpd_weight +
                0.2 * level_weight
            )
            
            return max(0.05, min(1.0, policy_weight))  # avoid zeroing out exploration
            
        except Exception as e:
            logger.warning(f"HCIE weight failed for {task.get('concept_id', 'unknown')}: {e}")
            return 0.5
    
    def generate_task(self, user_id: str, policy_mode: str = "hcie",
                     difficulty_range: Optional[tuple[float, float]] = None,
                     concept_filter: Optional[List[str]] = None) -> Dict[str, Any]:
        """Generate task — delegates to ItsRuntimeService when the Phase 14e spine is available."""
        adapted = self._generate_task_via_its(user_id, policy_mode, concept_filter)
        if adapted is not None:
            return adapted
        try:
            # 1. Get REAL candidate tasks from database (not just one from engine)
            candidates = self._get_candidate_tasks(user_id, difficulty_range, concept_filter)
            
            # Handle multiple candidates (REAL THOMPSON SAMPLING)
            if isinstance(candidates, list) and len(candidates) > 1:
                # 🔥 REAL PERSISTENT CONTEXTUAL THOMPSON SAMPLING SELECTION
                mastery_context = self._get_mastery_context(user_id, candidates)
                
                # 🔥 STEP 0: Apply HCIE policy weighting (soft probabilistic guidance)
                for task in candidates:
                    task["policy_weight"] = self._compute_hcie_weight(user_id, task, mastery_context)
                
                # 🔥 NEW: CONCEPT LEVEL FILTER - Keep tasks at appropriate cognitive level
                candidates = self._apply_concept_level_filter(candidates, user_id)
                
                # 🔥 NEW: ZPD FILTER - Keep tasks in optimal learning zone
                candidates = self._apply_zpd_filter(candidates, mastery_context)
                
                # 🔥 UNIFIED BRAIN: Use unified brain for advanced optimization
                unified_optimized_task = self._optimize_with_unified_brain(candidates, user_id)
                
                if unified_optimized_task and unified_optimized_task.get("unified_brain_optimized"):
                    best_task = unified_optimized_task
                    logger.info(f"🔥 USING UNIFIED BRAIN OPTIMIZED TASK: {best_task.get('task_id')}")
                else:
                    # Fallback to regular bandit selection
                    best_task = self.bandit.select_arm_contextual_thompson(user_id, candidates, mastery_context)
                best_score = best_task.get("hybrid_score", 0.0) if best_task else 0.0
                exploration_metric = best_task.get("exploration_metric") if best_task else None
                
                if exploration_metric is None:
                    logger.warning("🔥 Missing exploration_metric, recomputing fallback")
                    # Use default alpha and beta for uncertainty calculation
                    alpha, beta = 1.0, 1.0
                    exploration_metric = self.bandit._calculate_uncertainty(alpha, beta)
                
                if best_task:
                    best_task["bandit_score"] = best_score
                    logger.info(f"🔥 BANDIT SELECTED: task={best_task.get('task_id')} score={best_score:.3f} from {len(candidates)} candidates")
                    
                    # 🔥 FIX API CONTRACT: Return complete response schema
                    return {
                        "user_id": user_id,
                        "task_id": best_task["task_id"],
                        "concept_id": best_task["concept_id"],
                        "representation": best_task.get("representation", "text"),
                        "difficulty": best_task.get("difficulty", 0.5),
                        "question_text": best_task.get("question_text"),
                        "choices": best_task.get("choices", []),
                        
                        # 🔥 REQUIRED FOR API + KAFKA
                        "policy_mode": policy_mode,
                        "timestamp": datetime.utcnow().timestamp(),
                        
                        # 🔥 RESEARCH-GRADE REGRET METRICS (important for publication)
                        "selection_metrics": {
                            "bandit_score": best_task.get("contextual_score", 0.0),  # Before policy weighting
                            "policy_weight": best_task.get("policy_weight", 1.0),  # HCIE influence
                            "policy_effect": best_task.get("policy_effect", 1.0),  # Policy influence ratio
                            "hybrid_score": best_score,  # After policy weighting
                            "thompson_sample": best_task.get("thompson_sample", 0.0),  # Original sample
                            "expected_value": best_task.get("expected_value", 0.0),  # Expected value for learning regret
                            "learning_regret": best_task.get("learning_regret", 0.0),  # Learning tradeoff regret
                            "decision_regret": best_task.get("decision_regret", 0.0),  # Policy inefficiency regret
                            "regret": best_task.get("regret", 0.0),  # Backward compatibility (learning regret)
                            "cumulative_learning_regret": best_task.get("cumulative_learning_regret", 0.0),  # Total learning regret
                            "cumulative_decision_regret": best_task.get("cumulative_decision_regret", 0.0),  # Total decision regret
                            "steps": best_task.get("steps", 0),  # Number of interactions
                            "avg_learning_regret": best_task.get("avg_learning_regret", 0.0),  # Average learning regret
                            "avg_decision_regret": best_task.get("avg_decision_regret", 0.0),  # Average decision regret
                            "candidates_count": len(candidates),
                            "exploration": exploration_metric,  # 🔥 REAL UNCERTAINTY
                            "policy_type": "hybrid_bandit",
                            "persistence": "redis" if self.bandit.redis_client else "memory"
                        }
                    }
                else:
                    # Fallback to first candidate
                    return candidates[0]
            
            # Handle single task case (fallback)
            elif isinstance(candidates, list) and len(candidates) == 1:
                task = candidates[0]
                context = self._build_bandit_context(
                    user_id,
                    task.get("concept_id", "unknown"),
                    task.get("representation", "text")
                )
                score = self.bandit.calculate_thompson_score(
                    mastery_sample=context["mastery"],
                    representation_sample=context["representation"],
                    uncertainty=context["uncertainty"],
                    difficulty=context["difficulty"],
                    learning_gain=context["learning_gain"]
                )
                task["bandit_score"] = score
                
                # Candidates already come from the K-12 tasks table
                # (concept_type='k12'); no CT translation needed post Phase 14c.
                final_concept_id = task["concept_id"]
                
                # 🔥 FIX API CONTRACT: Return complete response schema
                return {
                    "user_id": user_id,
                    "task_id": task["task_id"],
                    "concept_id": final_concept_id,
                    "representation": task.get("representation", "text"),
                    "difficulty": task.get("difficulty", 0.5),
                    "question_text": task.get("question_text"),
                    "choices": task.get("choices", []),
                    
                    # 🔥 REQUIRED FOR API + KAFKA
                    "policy_mode": policy_mode,
                    "timestamp": datetime.utcnow().timestamp(),
                    
                    # 🔥 HYBRID BANDIT METRICS
                    "selection_metrics": {
                        "bandit_score": score,  # contextual_score
                        "policy_weight": 1.0,  # No policy influence
                        "policy_effect": 1.0,  # No policy effect
                        "hybrid_score": score,  # Same as contextual for single task
                        "thompson_sample": score,  # Same as contextual for single task
                        "expected_value": score,  # Same as contextual for single task
                        "learning_regret": 0.0,  # No learning regret with single task
                        "decision_regret": 0.0,  # No decision regret with single task
                        "regret": 0.0,  # Backward compatibility
                        "candidates_count": 1,
                        "exploration": 0.0,
                        "policy_type": "hybrid_bandit"
                    }
                }
            
            # Unexpected candidate shape -> degraded response (no synthetic cognition)
            else:
                logger.warning(f"Unexpected candidates format: {type(candidates)}")
                return self._degraded_task_response(
                    user_id=user_id,
                    policy_mode=policy_mode,
                    reason="unexpected_candidates_format",
                )

        except Exception as e:
            logger.error(f"Bandit task generation failed for {user_id}: {e}")
            return self._degraded_task_response(
                user_id=user_id,
                policy_mode=policy_mode,
                reason="bandit_selection_failed",
            )
    
    def process_submission(self, submission: TaskSubmission) -> Dict[str, Any]:
        """Process submission — delegates mutation to ItsRuntimeService spine when available."""
        adapted = self._process_submission_via_its(submission)
        if adapted is not None:
            return adapted
        logger.warning("🔥 TASK SERVICE LEARNING CALLED - API is doing learning updates!")
        start_time = time.time()
        try:
            # 1. Fetch the actual task to get the correct answer
            task = self.postgres_store.get_task_by_id(submission.task_id)
            if not task:
                # SAFE FALLBACK: Handle missing task gracefully
                logger.warning(f"Task {submission.task_id} not found, using fallback processing")
                return self._process_fallback_submission(submission)
            
            # 2. Evaluate correctness with probabilistic behavior
            user_answer = str(submission.answer).strip().lower()
            correct_answer = str(task["correct_answer"]).strip().lower()
            
            # 🔥 FIXED: Get current mastery from UnifiedBrain canonical state, not learners
            # This ensures temporal consistency - we read the same state that will be written to
            learner_mode = getattr(submission, 'learner_mode', 'lyapunov')
            
            # Read current mastery from canonical state (before update)
            try:
                current_mastery_result = self.unified_brain.process_event(
                    user_id=submission.user_id,
                    concept=submission.node_id,
                    interaction={"timestamp": datetime.utcnow().isoformat()},
                    mode="read"
                )
                current_mastery = current_mastery_result.mastery
                logger.info(f"🔥 CANONICAL READ BEFORE: {submission.node_id} = {current_mastery:.6f}")
            except Exception as e:
                logger.warning(f"🔥 Canonical read failed, using default: {e}")
                current_mastery = 0.3
            
            # Handle different answer formats
            deterministic_correct = False
            if user_answer == correct_answer:
                deterministic_correct = True
            elif user_answer in correct_answer or correct_answer in user_answer:
                deterministic_correct = True
            
            # Check for force_correct research control
            force_correct = getattr(submission, 'force_correct', None)
            
            # Add probabilistic correctness based on mastery
            import random
            correctness_probability = 0.5  # Default value
            if force_correct is not None:
                # Research control: override correctness
                is_correct = force_correct
                logger.info(f"🔥 FORCE CORRECT: mastery={current_mastery:.3f}, forced_correct={is_correct}")
            elif deterministic_correct:
                # High mastery students are more likely to get deterministic correct answers right
                correctness_probability = 0.7 + 0.3 * current_mastery  # 0.7 to 1.0
                is_correct = random.random() < correctness_probability
            else:
                # Low mastery students might still get some partial credit
                correctness_probability = 0.2 * current_mastery  # 0.0 to 0.2
                is_correct = random.random() < correctness_probability
                
            logger.info(f"🎲 PROBABILISTIC CORRECTNESS: mastery={current_mastery:.3f}, prob={correctness_probability:.3f}, correct={is_correct}")
            
            # 3. Get mode (defaults to 'hcie' if not provided)
            mode = getattr(submission, 'mode', 'hcie')
            
            # 4. Get beta from submission (learner_mode already set above)
            beta_from_submission = getattr(submission, 'beta', 0.5)
            logger.info(f"🚀 TASK SERVICE BETA: {beta_from_submission}")
            
            interaction_data = {
                "concept_id": submission.node_id,
                "representation": submission.representation,
                "correct": is_correct,
                "response_time": submission.response_time,
                "difficulty": task.get("difficulty", 0.5),
                "policy_mode": mode,
                "beta": beta_from_submission,
                "learner_mode": learner_mode,  # Pass learner mode to engine
                "force_correct": getattr(submission, 'force_correct', None),  # Research control
                "prior_mastery": getattr(submission, 'prior_mastery', None)  # Cold start control
            }
            
            logger.info(f"🚀 TASK SERVICE INTERACTION: learner={learner_mode}, beta={interaction_data['beta']}")
            
            # 5. 🔥 UNIFIED BRAIN: Use UnifiedLearningBrain for real mastery updates
            try:
                # Create UnifiedLearningBrain interaction data
                unified_interaction = {
                    "task_id": submission.task_id,
                    "user_id": submission.user_id,
                    "concept_id": submission.node_id,
                    "correctness": 1.0 if is_correct else 0.0,
                    "response_time": submission.response_time,
                    "difficulty": task.get("difficulty", 0.5),
                    "timestamp": datetime.utcnow().isoformat(),
                    "attempts": 1,
                    "hints_used": getattr(submission, 'hints_used', 0),
                    "frustration": 0.8 if not is_correct else 0.2,
                    "engagement": 0.9 if is_correct else 0.6,
                    "learner_mode": learner_mode
                }
                
                # 🔥 REAL LEARNING UPDATE: Use ONLY UnifiedLearningBrain in WRITE mode
                unified_result = self.unified_brain.process_event(
                    user_id=submission.user_id,
                    concept=submission.node_id,
                    interaction=unified_interaction,
                    mode="write"  # 🎯 THIS ACTUALLY UPDATES MASTERY
                )
                
                logger.info(f"🔥 UNIFIED BRAIN UPDATE: {submission.node_id} → mastery: {unified_result.mastery:.6f}")
                
                # 🔥 CLOSED LOOP: Calculate real reward using UnifiedLearningBrain mastery
                # current_mastery is already read from canonical state above
                updated_mastery = unified_result.mastery
                logger.info(f"🔥 MASTERY DELTA: {current_mastery:.6f} → {updated_mastery:.6f} ({updated_mastery - current_mastery:+.6f})")
                
                reward = self.reward_calculator.compute_reward(
                    correct=is_correct,
                    time_taken=submission.response_time,
                    difficulty=task.get("difficulty", 0.5),
                    learning_progress=updated_mastery - current_mastery
                )
                
                # 🔥 FIXED: Initialize result in success path (was only in exception handler)
                result = {
                    "success": True,
                    "user_id": submission.user_id,
                    "node_id": submission.node_id,
                    "concept_id": submission.node_id,
                    "task_id": submission.task_id,
                    "is_correct": is_correct,
                    "mastery_before": current_mastery,
                    "mastery_after": updated_mastery,
                    "mastery_change": updated_mastery - current_mastery,
                    "transferred_mastery": sum(getattr(unified_result, 'transfer_amounts', {}).values()),
                    "total_mastery": updated_mastery,
                    "direct_mastery": updated_mastery - sum(getattr(unified_result, 'transfer_amounts', {}).values()),
                    "prior_mastery": current_mastery,
                    "transfer_sources": list(getattr(unified_result, 'transfer_amounts', {}).keys()),
                    "transfer_enabled": bool(getattr(unified_result, 'transfer_amounts', {})),
                    "transfers_applied": getattr(unified_result, 'transfer_amounts', {}),
                    "transferred_mastery_change": sum(getattr(unified_result, 'transfer_amounts', {}).values()),
                    "learning_metrics": {
                        "transfer_events": len(getattr(unified_result, 'transfer_amounts', {})),
                        "total_transferred_mastery": sum(getattr(unified_result, 'transfer_amounts', {}).values()),
                        "transfer_efficiency": getattr(unified_result, 'transfer_efficiency', 0.0),
                        "confidence": getattr(unified_result, 'confidence', 0.5),
                        "raw_transfer": 0.0,
                        "decayed_transfer": 0.0,
                        "transfer_memory": 0.0
                    },
                    "transfer_effect": sum(getattr(unified_result, 'transfer_amounts', {}).values()),
                    "timestamp": datetime.utcnow().isoformat(),
                    "mode": "unified_brain",
                    "processing_time_ms": (time.time() - start_time) * 1000,
                    "correct_answer": task["correct_answer"],
                    "explanation": task.get("explanation", "Good job!"),
                    "learner": "unified_brain"
                }
                
            except Exception as unified_error:
                logger.error(f"Unified brain processing failed: {unified_error}")
                # Fallback to basic processing
                current_mastery = 0.3
                updated_mastery = 0.3
                reward = 0.5
                
                # Format result to match expected API response
                result = {
                    "success": True,
                    "user_id": submission.user_id,
                    "node_id": submission.node_id,
                    "concept_id": submission.node_id,
                    "task_id": submission.task_id,
                    "is_correct": is_correct,
                    "mastery_before": current_mastery,
                    "mastery_after": updated_mastery,
                    "mastery_change": updated_mastery - current_mastery,
                    "transferred_mastery": 0.0,
                    "total_mastery": updated_mastery,
                    "direct_mastery": updated_mastery,
                    "prior_mastery": current_mastery,
                    "transfer_sources": [],
                    "transfer_enabled": False,
                    "transfers_applied": {},
                    "transferred_mastery_change": 0.0,
                    "learning_metrics": {
                        "transfer_events": 0,
                        "total_transferred_mastery": 0.0,
                        "transfer_efficiency": 0.0,
                        "confidence": 0.5,
                        "raw_transfer": 0.0,
                        "decayed_transfer": 0.0,
                        "transfer_memory": 0.0
                    },
                    "transfer_effect": 0.0,
                    "timestamp": datetime.utcnow().isoformat(),
                    "mode": "fallback",
                    "processing_time_ms": 0,
                    "correct_answer": task["correct_answer"],
                    "explanation": task.get("explanation", "Good job!"),
                    "learner": "fallback"
                }
                
                # 🔥 LEARNING-ALIGNED REWARD: Add mastery gain signal
                mastery_before = current_mastery
                mastery_after = updated_mastery
                mastery_gain = max(0.0, mastery_after - mastery_before)
                learning_aligned_reward = reward + 0.3 * mastery_gain
                
                # 🔥 CLOSED LOOP: Update bandit with learning-aligned reward feedback (persistent per-user)
                logger.info("🔥 BANDIT UPDATE TRIGGERED")
                try:
                    self.bandit.update(
                        user_id=submission.user_id,
                        arm=submission.node_id,  # 🔥 CONCEPT-LEVEL ARM (better generalization)
                        reward=learning_aligned_reward,
                        context={
                            "user_id": submission.user_id,
                            "concept_id": task["concept_id"],
                            "difficulty": task.get("difficulty", 0.5),
                            "mastery_before": mastery_before,
                            "mastery_after": mastery_after,
                            "correct": is_correct
                        }
                    )
                    logger.info(f"🔥 BANDIT UPDATED: user={submission.user_id} task={submission.task_id} base_reward={reward:.3f} mastery_gain={mastery_gain:.3f} aligned_reward={learning_aligned_reward:.3f}")
                except Exception as bandit_error:
                    logger.warning(f"Bandit update failed: {bandit_error}")
                    # Don't fail the request for bandit issues
                
                logger.info(f"Learner processing successful for {submission.user_id}")
            
            # 7. Update mastery projection table
            try:
                self._update_user_mastery_projection(submission.user_id, submission.node_id, unified_result)
                logger.info(f"Mastery projection updated for {submission.user_id}: {submission.node_id}")
            except Exception as projection_error:
                logger.error(f"Mastery projection update failed: {projection_error}")
            
            # 8. Persist transfer events
            try:
                self._persist_transfer_events(submission.user_id, unified_result)
                logger.info(f"Transfer events persisted for {submission.user_id}")
                
                # Record transfer metrics for alerting
                transfer_amounts = getattr(unified_result, 'transfer_amounts', {})
                for source_concept, transfer_amount in transfer_amounts.items():
                    if source_concept != 'total':
                        get_transfer_events_counter().add(1, {
                            "source_concept": source_concept,
                            "target_concept": submission.node_id,
                            "transfer_amount": transfer_amount
                        })
            except Exception as transfer_error:
                logger.error(f"Transfer events persistence failed: {transfer_error}")
                # Don't fail the request for transfer issues
            
            # 9. Record learning metrics
            get_mastery_updates_counter().add(1, {
                "user_id": submission.user_id,
                "concept_id": submission.node_id,
                "mastery_after": str(unified_result.mastery)
            })
            
            # Record latency metric
            get_latency_histogram().record(time.time() - start_time)
            
            # 6. Add feedback for the UI
            result.update({
                "correct": is_correct,
                "correct_answer": task["correct_answer"],
                "explanation": task.get("explanation", "Good job!") if is_correct else task.get("hint", "Try again!"),
                "task_id": submission.task_id,
                "node_id": submission.node_id,
                
                # 🔥 INTEGRATION: Include LearningResult for API consistency
                "learning_result": {
                    "mastery": unified_result.mastery,
                    "uncertainty": unified_result.uncertainty,
                    "confidence": unified_result.confidence,
                    "lyapunov_mastery": unified_result.lyapunov_mastery,
                    "bayesian_alpha": unified_result.bayesian_alpha,
                    "bayesian_beta": unified_result.bayesian_beta,
                    "kalman_mastery": unified_result.kalman_mastery,
                    "kalman_covariance": unified_result.kalman_covariance,
                    "ensemble_weights": unified_result.ensemble_weights,
                    "ensemble_variance": unified_result.ensemble_variance,
                    "policy": unified_result.policy,
                    "policy_multiplier": unified_result.policy_multiplier,
                    "transfer_amounts": unified_result.transfer_amounts,
                    "transfer_efficiency": unified_result.transfer_efficiency,
                    "zpd_target": unified_result.zpd_target,
                    "zpd_alignment_error": unified_result.zpd_alignment_error,
                    "zpd_score": unified_result.zpd_score,
                    "J_value": getattr(unified_result, 'J_value', None),
                    "processing_mode": unified_result.processing_mode
                }
            })
            
            return result
            
        except Exception as e:
            # SAFE FALLBACK: Never let learning crash the system
            logger.error(f"Submission processing failed: {e}")
            return self._process_fallback_submission(submission, error=str(e))
    
    def _process_fallback_submission(self, submission: TaskSubmission, error: str = None) -> Dict[str, Any]:
        """
        Safe fallback processing when main submission fails
        Never crashes the system, always returns a valid response
        """
        try:
            # Basic correctness evaluation for fallback
            user_answer = str(submission.answer).strip()
            
            # Simple numeric evaluation for fallback tasks
            try:
                answer_num = float(user_answer)
                # Assume 70+ is correct for fallback tasks
                is_correct = answer_num >= 70.0
            except ValueError:
                # For non-numeric answers, assume correct (lenient fallback)
                is_correct = len(user_answer) > 0
            
            # Create minimal valid response
            fallback_response = {
                "status": "partial_success",
                "message": "Learning processed with fallback (analytics may be limited)",
                "correct": is_correct,
                "correct_answer": "70",  # Simple fallback answer
                "explanation": "Good job!" if is_correct else "Keep practicing!",
                "task_id": submission.task_id,
                "node_id": submission.node_id,
                "user_id": submission.user_id,
                "response_time": submission.response_time,
                "mastery_update": {
                    "concept_id": submission.node_id,
                    "old_mastery": 0.5,
                    "new_mastery": 0.55 if is_correct else 0.45,
                    "improvement": 0.05 if is_correct else -0.05
                },
                "reward": 1.0 if is_correct else 0.1,
                "policy_mode": getattr(submission, 'mode', 'hcie'),
                "fallback_used": True,
                # Add confidence and exclusion data for API validation
                "confidence": 0.65 if is_correct else 0.35,
                "mapping_confidence": 0.65 if is_correct else 0.35,
                "excluded": False,
                "data_source": "ednet_transformed",
                # Debug logging for learning variability
                "debug": {
                    "base_learning_rate": 0.05,
                    "effective_rate": 0.05,
                    "confidence_used": 0.65 if is_correct else 0.35,
                    "mastery_before": 0.5,
                    "mastery_after": 0.55 if is_correct else 0.45
                }
            }
            
            if error:
                fallback_response["processing_error"] = error
                logger.warning(f"Used fallback processing due to: {error}")
                logger.error(f"Full error details: {type(error).__name__}: {error}")
            
            return fallback_response
            
        except Exception as fallback_error:
            # ULTIMATE FALLBACK: Return the most basic valid response
            logger.error(f"Even fallback processing failed: {fallback_error}")
            return {
                "status": "basic_success",
                "message": "Answer recorded (minimal processing)",
                "correct": True,  # Assume correct to avoid negative UX
                "explanation": "Answer recorded successfully!",
                "task_id": submission.task_id,
                "node_id": submission.node_id,
                "user_id": submission.user_id,
                "fallback_used": True,
                "processing_error": str(fallback_error)
            }
    
    def get_task_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get task history for user
        
        Args:
            user_id: User identifier
            limit: Maximum number of tasks to return
            
        Returns:
            List of task interactions
        """
        try:
            if not self.redis_store.redis_available:
                return []
            
            # Get interaction history from Redis
            history_key = f"history:{user_id}"
            history_data = self.redis_store.redis_client.lrange(history_key, 0, limit - 1)
            
            history = []
            for item in history_data:
                try:
                    import json
                    interaction = json.loads(item)
                    history.append({
                        "task_id": interaction.get("task_id"),
                        "concept_id": interaction.get("concept_id"),
                        "correct": interaction.get("correct"),
                        "timestamp": interaction.get("timestamp"),
                        "response_time": interaction.get("response_time")
                    })
                except Exception as e:
                    logger.warning(f"Error parsing history item: {e}")
                    continue
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting task history for {user_id}: {e}")
            return []
    
    def get_user_mastery_summary(self, user_id: str, mode: Optional[str] = None) -> Dict[str, Any]:
        """
        Get user mastery summary with dual-mode support
        
        Args:
            user_id: User identifier
            mode: Override mode ("ct", "ednet", or "hcie")
            
        Returns:
            User mastery summary
        """
        try:
            effective_mode = mode or "hcie"  # Default fallback, no self.mode
            
            if self.redis_store.redis_available:
                # Get mastery using unified Bayesian model
                mastery = self.redis_store.get_user_mastery(user_id)
                return {
                    "mode": effective_mode,
                    "mastery": mastery,
                    "average_mastery": sum(mastery.values()) / len(mastery) if mastery else 0.3,
                    "total_concepts": len(mastery),
                    "mastered_concepts": len([k for k, v in mastery.items() if v >= 0.8])
                }
            else:
                return {"mode": effective_mode, "error": "Redis not available"}
        except Exception as e:
            logger.error(f"Error getting mastery summary for {user_id}: {e}")
            return {"mode": effective_mode, "error": str(e)}
    
    def get_system_stats(self) -> Dict[str, Any]:
        """
        Get system statistics
        
        Returns:
            System statistics
        """
        try:
            stats = {
                # 05_engines bucket retired; concept counts surface from a
                # canonical concept registry once TaskService DI migration lands.
                "total_concepts": 0,
                "policy_mode": "dynamic",
                "redis_available": self.redis_store.redis_available
            }
            
            # Add Redis stats if available
            if self.redis_store.redis_available:
                try:
                    info = self.redis_store.redis_client.info()
                    stats["redis"] = {
                        "connected_clients": info.get("connected_clients"),
                        "used_memory": info.get("used_memory"),
                        "total_commands": info.get("total_commands_processed")
                    }
                except Exception as e:
                    logger.warning(f"Error getting Redis stats: {e}")
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            return {"error": str(e)}
    
    def _get_concept_name(self, concept_id: str) -> str:
        """Get human-readable concept name"""
        concept_names = {
            "ct_problem_identification": "Problem Identification",
            "ct_pattern_recognition": "Pattern Recognition", 
            "ct_abstraction": "Abstraction",
            "ct_decomposition": "Decomposition",
            "ct_algorithm_tracing": "Algorithm Tracing",
            "ct_algorithm_design": "Algorithm Design",
            "ct_optimization": "Optimization",
            "ct_system_thinking": "System Thinking",
            "ct_debugging": "Debugging",
            "ct_generalization": "Generalization",
            "ct_edge_cases": "Edge Cases"
        }
        return concept_names.get(concept_id, concept_id)
    
    def _get_concept_category(self, concept_id: str) -> str:
        """Get concept category"""
        categories = {
            "ct_problem_identification": "Problem Solving",
            "ct_pattern_recognition": "Pattern Recognition",
            "ct_abstraction": "Abstraction",
            "ct_decomposition": "Problem Decomposition",
            "ct_algorithm_tracing": "Algorithm Understanding",
            "ct_algorithm_design": "Algorithm Creation",
            "ct_optimization": "Performance Optimization",
            "ct_system_thinking": "Systems Integration",
            "ct_debugging": "Troubleshooting",
            "ct_generalization": "Pattern Generalization",
            "ct_edge_cases": "Boundary Testing"
        }
        return categories.get(concept_id, "Unknown")
    
    def _get_concept_level(self, concept_id: str) -> int:
        """Get cognitive level for concept"""
        levels = {
            "ct_problem_identification": 1,
            "ct_pattern_recognition": 1,
            "ct_abstraction": 2,
            "ct_decomposition": 2,
            "ct_algorithm_tracing": 2,
            "ct_algorithm_design": 3,
            "ct_optimization": 3,
            "ct_system_thinking": 4,
            "ct_debugging": 3,
            "ct_generalization": 4,
            "ct_edge_cases": 4
        }
        return levels.get(concept_id, 2)
    
    def _get_grade_level(self, concept_id: str) -> str:
        """Get grade level for concept"""
        levels = {
            "ct_problem_identification": "elementary",
            "ct_pattern_recognition": "elementary",
            "ct_abstraction": "middle_school",
            "ct_decomposition": "middle_school",
            "ct_algorithm_tracing": "middle_school",
            "ct_algorithm_design": "high_school",
            "ct_optimization": "high_school",
            "ct_system_thinking": "high_school",
            "ct_debugging": "high_school",
            "ct_generalization": "high_school",
            "ct_edge_cases": "high_school"
        }
        return levels.get(concept_id, "middle_school")
    
    def _get_subject_area(self, concept_id: str) -> str:
        """Get subject area for concept"""
        subjects = {
            "ct_problem_identification": "computer_science",
            "ct_pattern_recognition": "mathematics",
            "ct_abstraction": "computer_science",
            "ct_decomposition": "computer_science",
            "ct_algorithm_tracing": "computer_science",
            "ct_algorithm_design": "computer_science",
            "ct_optimization": "computer_science",
            "ct_system_thinking": "interdisciplinary",
            "ct_debugging": "computer_science",
            "ct_generalization": "mathematics",
            "ct_edge_cases": "computer_science"
        }
        return subjects.get(concept_id, "general")
    
    def _generate_ct_feedback(self, submission, mastery_before: float, mastery_after: float) -> str:
        """
        Generate contextual feedback for CT answer
        
        Args:
            submission: Answer submission
            mastery_before: Mastery before interaction
            mastery_after: Mastery after interaction
            
        Returns:
            str: Feedback message
        """
        if submission.correct_answer == submission.answer:
            return f"Excellent! You've mastered this {self._get_concept_name(submission.node_id)} concept. Your mastery improved from {mastery_before:.3f} to {mastery_after:.3f}."
        else:
            improvement = mastery_after - mastery_before
            if improvement > 0:
                return f"Good attempt! You're making progress in {self._get_concept_category(submission.node_id)}. Your mastery improved by {improvement:.3f}. Keep practicing!"
            else:
                return f"Not quite right. Review the {self._get_concept_category(submission.node_id)} concepts and try again. Your mastery is currently at {mastery_after:.3f}."
    
    def _update_user_mastery_projection(self, user_id: str, concept_id: str, learner_result) -> None:
        """
        Update the user mastery with transfer projection table
        
        Args:
            user_id: User identifier
            concept_id: Concept identifier  
            learner_result: Result from learner processing (LearningResult dataclass)
        """
        try:
            # 🔥 FIXED: LearningResult is a dataclass, not a dict - use attribute access
            total_mastery = getattr(learner_result, 'mastery', 0.3)
            transferred_mastery = sum(getattr(learner_result, 'transfer_amounts', {}).values())
            
            # Calculate direct mastery as total minus transferred
            direct_mastery = total_mastery - transferred_mastery
            
            # Prepare transfer sources as JSON
            transfer_sources = json.dumps(list(getattr(learner_result, 'transfer_amounts', {}).keys()))
            
            # 🔥 FIXED: Convert string user_id to UUID for database compatibility
            import uuid
            try:
                # Try to parse as UUID, generate if needed
                if isinstance(user_id, str) and user_id.startswith('integrity_test_user'):
                    # For test users, generate consistent UUID
                    user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, user_id)
                elif isinstance(user_id, str):
                    # Try to parse existing UUID string
                    user_uuid = uuid.UUID(user_id)
                else:
                    # Already a UUID object
                    user_uuid = user_id
                    
                logger.info(f"🔥 UUID CONVERSION: {user_id} → {user_uuid}")
            except Exception as uuid_error:
                logger.warning(f"🔥 UUID conversion failed, generating new: {uuid_error}")
                user_uuid = uuid.uuid4()
            
            # Upsert to user_mastery_with_transfer table
            query = """
                INSERT INTO user_mastery_with_transfer 
                (user_id, concept_name, direct_mastery, transferred_mastery, total_mastery, transfer_sources, last_updated)
                VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id, concept_name) 
                DO UPDATE SET 
                    direct_mastery = EXCLUDED.direct_mastery,
                    transferred_mastery = EXCLUDED.transferred_mastery,
                    total_mastery = EXCLUDED.total_mastery,
                    transfer_sources = EXCLUDED.transfer_sources,
                    last_updated = EXCLUDED.last_updated
            """
            
            self.postgres_store.execute_write(query, (
                user_uuid,
                concept_id,
                direct_mastery,
                transferred_mastery,
                total_mastery,
                transfer_sources
            ))
            
            logger.info(f"✅ Mastery projection updated: {user_id}/{concept_id}")
            
        except Exception as e:
            logger.error(f"Failed to update mastery projection for {user_id}/{concept_id}: {e}")
            raise

    def _persist_transfer_events(self, user_id: str, learner_result) -> None:
        """
        Persist transfer learning events to database
        
        Args:
            user_id: User identifier
            learner_result: Result from learner processing (LearningResult dataclass)
        """
        # 🔥 FIXED: LearningResult is a dataclass, not a dict - use attribute access
        events = getattr(learner_result, 'transfer_events', [])
        
        for event in events:
            try:
                # Use proper store method for database access
                query = """
                    INSERT INTO transfer_learning_events (
                        user_id,
                        source_concept,
                        target_concept,
                        transfer_amount,
                        transfer_type,
                        original_mastery_change,
                        transferred_mastery_change,
                        confidence_score,
                        timestamp
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """
                
                self.postgres_store.execute_write(query, (
                    event.user_id,
                    event.source_concept,
                    event.target_concepts[0] if event.target_concepts else None,
                    event.transfer_amounts.get(event.target_concepts[0], 0.0) if event.target_concepts else 0.0,
                    "direct",
                    event.original_mastery_change,
                    event.transferred_mastery_change,
                    event.confidence_score,
                    event.timestamp_datetime or datetime.now()
                ))
                logger.info(f"Transfer event persisted: {event.source_concept} → {event.target_concepts[0] if event.target_concepts else 'None'}")
                
            except Exception as e:
                logger.error(f"Failed to persist transfer event: {e}")
                # Continue with other events
                continue

    # REMOVED: switch_mode function is incompatible with stateless design
    # Mode switching should be handled per-request, not via shared state mutation
