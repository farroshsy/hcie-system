"""
Task Selection Service - Concept-Aware Task Retrieval

This service manages task selection based on:
- Current concept context
- Difficulty progression
- Learner mastery
- Task type preferences

Key Design Principles:
- Tasks bind TO concepts (not independent)
- Difficulty progression within concepts
- Concept-aware task retrieval
- Pedagogical task sequencing
"""

from typing import List, Optional
import random

from core.curriculum.concept_registry import (
    ConceptRegistry,
    LearningTask,
    get_registry
)


class TaskSelectionService:
    """
    Service for concept-aware task selection.
    
    This provides pedagogical task sequencing based on:
    - Current concept context
    - Learner mastery
    - Difficulty progression
    - Task type preferences
    """
    
    def __init__(self, concept_registry: Optional[ConceptRegistry] = None):
        """
        Initialize task selection service.
        
        Args:
            concept_registry: Concept registry instance (uses global if None)
        """
        self.concept_registry = concept_registry or get_registry()
    
    def select_task_for_concept(
        self,
        concept_id: str,
        learner_mastery: float = 0.0,
        preferred_task_types: Optional[List[str]] = None,
        exclude_task_ids: Optional[List[str]] = None
    ) -> Optional[LearningTask]:
        """
        Select a task for a specific concept based on learner mastery.
        
        Args:
            concept_id: Concept identifier
            learner_mastery: Learner's mastery of the concept (0-1 scale)
            preferred_task_types: Optional list of preferred task types
            exclude_task_ids: Optional list of task IDs to exclude (already attempted)
        
        Returns:
            Selected LearningTask or None if no tasks available
        """
        concept = self.concept_registry.get_concept(concept_id)
        if concept is None:
            return None
        
        tasks = self.concept_registry.get_tasks_for_concept(concept_id)
        if not tasks:
            return None
        
        # Filter out excluded tasks
        if exclude_task_ids:
            tasks = [t for t in tasks if t.id not in exclude_task_ids]
        
        if not tasks:
            return None
        
        # Filter by preferred task types if specified
        if preferred_task_types:
            filtered_tasks = [t for t in tasks if t.task_type.value in preferred_task_types]
            if filtered_tasks:
                tasks = filtered_tasks
        
        # Select task based on learner mastery
        # Low mastery: easier tasks first
        # High mastery: harder tasks first
        if learner_mastery < 0.3:
            # Beginner: select easiest tasks
            tasks = sorted(tasks, key=lambda t: t.difficulty)
            return tasks[0]
        elif learner_mastery < 0.7:
            # Intermediate: select medium difficulty tasks
            medium_tasks = [t for t in tasks if 0.3 <= t.difficulty <= 0.7]
            if medium_tasks:
                return random.choice(medium_tasks)
            return random.choice(tasks)
        else:
            # Advanced: select harder tasks
            hard_tasks = [t for t in tasks if t.difficulty > 0.5]
            if hard_tasks:
                return random.choice(hard_tasks)
            return random.choice(tasks)
    
    def select_next_task(
        self,
        current_concept_id: str,
        learner_mastery: dict,
        completed_task_ids: List[str]
    ) -> Optional[LearningTask]:
        """
        Select the next task based on current context and learner state.
        
        Args:
            current_concept_id: Current concept identifier
            learner_mastery: Dict of concept_id -> mastery (0-1 scale)
            completed_task_ids: List of already completed task IDs
        
        Returns:
            Selected LearningTask or None if no tasks available
        """
        concept_mastery = learner_mastery.get(current_concept_id, 0.0)
        
        # Try to select a task for current concept
        task = self.select_task_for_concept(
            concept_id=current_concept_id,
            learner_mastery=concept_mastery,
            exclude_task_ids=completed_task_ids
        )
        
        if task is not None:
            return task
        
        # If no tasks available for current concept, try to advance
        concept = self.concept_registry.get_concept(current_concept_id)
        if concept and concept.supports:
            # Try supported concepts
            for supported_concept_id in concept.supports:
                supported_mastery = learner_mastery.get(supported_concept_id, 0.0)
                task = self.select_task_for_concept(
                    concept_id=supported_concept_id,
                    learner_mastery=supported_mastery,
                    exclude_task_ids=completed_task_ids
                )
                if task is not None:
                    return task
        
        return None
    
    def get_tasks_by_difficulty(
        self,
        concept_id: str,
        min_difficulty: float = 0.0,
        max_difficulty: float = 1.0
    ) -> List[LearningTask]:
        """
        Get tasks for a concept within a difficulty range.
        
        Args:
            concept_id: Concept identifier
            min_difficulty: Minimum difficulty (0-1 scale)
            max_difficulty: Maximum difficulty (0-1 scale)
        
        Returns:
            List of tasks within difficulty range
        """
        tasks = self.concept_registry.get_tasks_for_concept(concept_id)
        return [t for t in tasks if min_difficulty <= t.difficulty <= max_difficulty]
    
    def get_tasks_by_type(
        self,
        concept_id: str,
        task_type: str
    ) -> List[LearningTask]:
        """
        Get tasks for a concept of a specific type.
        
        Args:
            concept_id: Concept identifier
            task_type: Task type (mcq, parsons, code_trace, etc.)
        
        Returns:
            List of tasks of the specified type
        """
        tasks = self.concept_registry.get_tasks_for_concept(concept_id)
        return [t for t in tasks if t.task_type.value == task_type]
    
    def get_concept_progress(
        self,
        concept_id: str,
        completed_task_ids: List[str]
    ) -> dict:
        """
        Get progress information for a concept.
        
        Args:
            concept_id: Concept identifier
            completed_task_ids: List of completed task IDs
        
        Returns:
            Dict with progress information
        """
        all_tasks = self.concept_registry.get_tasks_for_concept(concept_id)
        completed = [t for t in all_tasks if t.id in completed_task_ids]
        
        return {
            "total_tasks": len(all_tasks),
            "completed_tasks": len(completed),
            "progress_ratio": len(completed) / len(all_tasks) if all_tasks else 0.0,
            "remaining_tasks": len(all_tasks) - len(completed)
        }
