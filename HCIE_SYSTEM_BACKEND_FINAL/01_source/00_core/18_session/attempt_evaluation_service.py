"""
Attempt Evaluation Service - Correctness and Misconception Detection

This service evaluates task attempts:
- Correctness assessment
- Misconception detection
- Cognitive operation identification
- Research metadata preservation

Key Design Principles:
- Evaluation modes: binary, partial, rubric
- Misconception targeting for remediation
- Cognitive operation tracking
- Research-grade diagnostics
"""

from typing import Optional, Dict, Any
from enum import Enum

from core.session.models import (
    TaskAttempt,
    TaskOutcome
)
from core.curriculum.concept_registry import (
    ConceptRegistry,
    LearningTask,
    get_registry
)


class EvaluationMode(Enum):
    """Evaluation modes for task attempts"""
    BINARY = "binary"  # Correct/Incorrect only
    PARTIAL = "partial"  # Partial credit possible
    RUBRIC = "rubric"  # Multi-criteria rubric evaluation


class AttemptEvaluationService:
    """
    Service for evaluating task attempts.
    
    This provides correctness assessment and misconception detection
    for pedagogical adaptation.
    """
    
    def __init__(self, concept_registry: Optional[ConceptRegistry] = None):
        """
        Initialize attempt evaluation service.
        
        Args:
            concept_registry: Concept registry instance (uses global if None)
        """
        self.concept_registry = concept_registry or get_registry()
    
    def evaluate_attempt(
        self,
        attempt: TaskAttempt,
        task: LearningTask
    ) -> Dict[str, Any]:
        """
        Evaluate a task attempt.
        
        Args:
            attempt: Task attempt to evaluate
            task: Learning task definition
        
        Returns:
            Evaluation result with:
            - outcome: TaskOutcome
            - score: 0-1 scale
            - misconception_triggered: Optional misconception
            - cognitive_operation: Optional cognitive operation
            - feedback: Human-readable feedback
        """
        # Determine evaluation mode
        evaluation_mode = EvaluationMode(task.evaluation_mode)
        
        if evaluation_mode == EvaluationMode.BINARY:
            return self._evaluate_binary(attempt, task)
        elif evaluation_mode == EvaluationMode.PARTIAL:
            return self._evaluate_partial(attempt, task)
        elif evaluation_mode == EvaluationMode.RUBRIC:
            return self._evaluate_rubric(attempt, task)
        else:
            return self._evaluate_binary(attempt, task)
    
    def _evaluate_binary(
        self,
        attempt: TaskAttempt,
        task: LearningTask
    ) -> Dict[str, Any]:
        """
        Binary evaluation (correct/incorrect only).
        
        Args:
            attempt: Task attempt
            task: Learning task
        
        Returns:
            Evaluation result
        """
        is_correct = self._check_correctness(attempt.learner_response, task.expected_answer)
        
        outcome = TaskOutcome.CORRECT if is_correct else TaskOutcome.INCORRECT
        score = 1.0 if is_correct else 0.0
        
        # Detect misconception if incorrect
        misconception = None
        if not is_correct and task.misconception_target:
            misconception = self._detect_misconception(
                attempt.learner_response,
                task.expected_answer,
                task.misconception_target
            )
        
        return {
            "outcome": outcome,
            "score": score,
            "misconception_triggered": misconception,
            "cognitive_operation": self._infer_cognitive_operation(task),
            "feedback": self._generate_feedback(outcome, misconception, task)
        }
    
    def _evaluate_partial(
        self,
        attempt: TaskAttempt,
        task: LearningTask
    ) -> Dict[str, Any]:
        """
        Partial credit evaluation.
        
        Args:
            attempt: Task attempt
            task: Learning task
        
        Returns:
            Evaluation result
        """
        # Calculate partial score based on similarity
        similarity = self._calculate_similarity(attempt.learner_response, task.expected_answer)
        
        if similarity >= 0.8:
            outcome = TaskOutcome.CORRECT
            score = 1.0
        elif similarity >= 0.5:
            outcome = TaskOutcome.PARTIAL
            score = similarity
        else:
            outcome = TaskOutcome.INCORRECT
            score = similarity
        
        # Detect misconception
        misconception = None
        if similarity < 0.8 and task.misconception_target:
            misconception = self._detect_misconception(
                attempt.learner_response,
                task.expected_answer,
                task.misconception_target
            )
        
        return {
            "outcome": outcome,
            "score": score,
            "misconception_triggered": misconception,
            "cognitive_operation": self._infer_cognitive_operation(task),
            "feedback": self._generate_feedback(outcome, misconception, task)
        }
    
    def _evaluate_rubric(
        self,
        attempt: TaskAttempt,
        task: LearningTask
    ) -> Dict[str, Any]:
        """
        Rubric-based evaluation (placeholder for multi-criteria).
        
        Args:
            attempt: Task attempt
            task: Learning task
        
        Returns:
            Evaluation result
        """
        # For now, fall back to partial evaluation
        # TODO: Implement multi-criteria rubric evaluation
        return self._evaluate_partial(attempt, task)
    
    def _check_correctness(self, learner_response: str, expected_answer: str) -> bool:
        """
        Check if learner response matches expected answer.
        
        Args:
            learner_response: Learner's response
            expected_answer: Expected answer
        
        Returns:
            True if correct, False otherwise
        """
        # Normalize for comparison
        learner_normalized = learner_response.strip().lower()
        expected_normalized = expected_answer.strip().lower()
        
        return learner_normalized == expected_normalized
    
    def _calculate_similarity(self, learner_response: str, expected_answer: str) -> float:
        """
        Calculate similarity between learner response and expected answer.
        
        Args:
            learner_response: Learner's response
            expected_answer: Expected answer
        
        Returns:
            Similarity score (0-1 scale)
        """
        # Simple word overlap similarity
        learner_words = set(learner_response.lower().split())
        expected_words = set(expected_answer.lower().split())
        
        if not expected_words:
            return 0.0
        
        intersection = learner_words & expected_words
        union = learner_words | expected_words
        
        return len(intersection) / len(union) if union else 0.0
    
    def _detect_misconception(
        self,
        learner_response: str,
        expected_answer: str,
        misconception_target: str
    ) -> Optional[str]:
        """
        Detect if a specific misconception was triggered.
        
        Args:
            learner_response: Learner's response
            expected_answer: Expected answer
            misconception_target: Target misconception to detect
        
        Returns:
            Misconception ID if triggered, None otherwise
        """
        # Placeholder: In production, this would use more sophisticated
        # misconception detection based on response patterns
        # For now, return the misconception_target if incorrect
        
        if not self._check_correctness(learner_response, expected_answer):
            return misconception_target
        
        return None
    
    def _infer_cognitive_operation(self, task: LearningTask) -> Optional[str]:
        """
        Infer the cognitive operation required by the task.
        
        Args:
            task: Learning task
        
        Returns:
            Cognitive operation name
        """
        # Get concept to determine cognitive operations
        concept = self.concept_registry.get_concept(task.concept_id)
        if concept and concept.cognitive_operations:
            # Return first cognitive operation (simplified)
            return concept.cognitive_operations[0].value if concept.cognitive_operations else None
        
        return None
    
    def _generate_feedback(
        self,
        outcome: TaskOutcome,
        misconception: Optional[str],
        task: LearningTask
    ) -> str:
        """
        Generate human-readable feedback for the attempt.
        
        Args:
            outcome: Task outcome
            misconception: Triggered misconception (if any)
            task: Learning task
        
        Returns:
            Human-readable feedback
        """
        if outcome == TaskOutcome.CORRECT:
            return task.explanation or "Correct! Well done."
        elif outcome == TaskOutcome.PARTIAL:
            return task.explanation or "Partially correct. Review the explanation."
        else:
            if misconception:
                return f"Incorrect. You may have a misunderstanding about {misconception}. {task.explanation}"
            return task.explanation or "Incorrect. Review the explanation."
    
    def update_attempt_with_evaluation(
        self,
        attempt: TaskAttempt,
        evaluation: Dict[str, Any]
    ) -> TaskAttempt:
        """
        Update attempt with evaluation results.
        
        Args:
            attempt: Task attempt to update
            evaluation: Evaluation result
        
        Returns:
            Updated TaskAttempt
        """
        attempt.outcome = evaluation["outcome"]
        attempt.misconception_triggered = evaluation.get("misconception_triggered")
        attempt.cognitive_operation = evaluation.get("cognitive_operation")
        
        return attempt
