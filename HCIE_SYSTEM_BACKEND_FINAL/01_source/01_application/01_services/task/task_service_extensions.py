"""
TaskService Extensions - Production-ready task validation methods
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class TaskServiceExtensions:
    """Extensions for TaskService to support production UX endpoints"""
    
    def __init__(self, task_service):
        self.task_service = task_service
    
    def get_task_by_id(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task by ID from the canonical K-12 tasks table for answer validation.

        Rewired in Phase 14c: previously queried the retired ct_tasks table.
        Now delegates to PostgresInteractionStore.get_task_by_id which is the
        single owner of the unified tasks schema.
        """
        try:
            task = self.task_service.postgres_store.get_task_by_id(task_id)
            if not task:
                logger.warning(f"Task not found: {task_id}")
                return None

            difficulty = task.get("difficulty")
            try:
                difficulty_f = float(difficulty) if difficulty is not None else 0.5
            except (TypeError, ValueError):
                difficulty_f = 0.5

            return {
                "task_id": task["id"],
                "concept_id": task["concept_id"],
                "question_text": task.get("question_text", ""),
                "choices": (task.get("content") or {}).get("choices", []),
                "correct_answer": task.get("correct_answer", ""),
                "difficulty": difficulty_f,
                "representation": task.get("task_type", "text"),
                "estimated_time": round(3.0 + difficulty_f * 12.0, 1),
            }

        except ValueError:
            logger.warning(f"Task not found: {task_id}")
            return None
        except Exception as e:
            logger.error(f"❌ Error getting task {task_id}: {e}")
            return None
    
    def validate_answer(self, task_id: str, user_answer: str) -> Dict[str, Any]:
        """
        Validate user answer against correct answer
        """
        try:
            task = self.get_task_by_id(task_id)
            if not task:
                return {"valid": False, "error": "Task not found"}
            
            correct_answer = task.get("correct_answer")
            is_correct = str(user_answer).strip().upper() == str(correct_answer).strip().upper()
            
            return {
                "valid": True,
                "correct": is_correct,
                "correct_answer": correct_answer,
                "user_answer": user_answer,
                "task": task
            }
            
        except Exception as e:
            logger.error(f"❌ Error validating answer: {e}")
            return {"valid": False, "error": str(e)}
    
    def get_user_mastery_data(self, user_id: str) -> Dict[str, float]:
        """
        Get real mastery data for user from UnifiedLearningBrain
        """
        try:
            brain = self.task_service.unified_brain
            mastery_data = {}
            
            # Get mastery for key concepts
            key_concepts = ["k2_algorithms", "k5_algorithms", "k8_algorithms", 
                          "k2_computing_systems_devices", "k5_computing_systems_devices"]
            
            for concept in key_concepts:
                try:
                    # Try to get mastery from each learner
                    for learner_name in ["lyapunov", "bayesian", "kalman"]:
                        learner = brain.learner_factory.get_learner(learner_name)
                        state = learner.get_state(user_id, concept)
                        
                        if isinstance(state, dict):
                            mastery = state.get("mastery", 0.3)
                        elif isinstance(state, (int, float)):
                            mastery = state
                        elif isinstance(state, tuple) and len(state) >= 2:
                            # Bayesian (alpha, beta) -> mastery
                            alpha, beta = state[0], state[1]
                            mastery = alpha / (alpha + beta) if (alpha + beta) > 0 else 0.3
                        else:
                            mastery = 0.3
                        
                        mastery_data[concept] = mastery
                        break  # Use first successful learner
                        
                except Exception as e:
                    logger.debug(f"Could not get mastery for {concept}: {e}")
                    mastery_data[concept] = 0.3
            
            return mastery_data
            
        except Exception as e:
            logger.error(f"❌ Error getting user mastery: {e}")
            return {"k2_algorithms": 0.3}  # Fallback
