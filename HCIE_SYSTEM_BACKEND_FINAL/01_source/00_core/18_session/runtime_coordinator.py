"""
Runtime Coordinator - Full Interaction Loop Orchestration

This service orchestrates the complete learning interaction loop:
start session → load projection → select task → record attempt → evaluate response → 
update cognition → emit adaptation → persist state → select next task

Key Design Principles:
- Orchestrates full interaction loop
- Maintains session continuity
- Coordinates all session services
- Ensures data consistency
"""

from typing import Optional, Dict, Any, List, Protocol
from datetime import datetime
import uuid

from core.session.models import (
    LearningSession,
    TaskAttempt,
    TaskOutcome,
    AdaptationEvent,
    LearnerProjection
)
from core.session.session_service import SessionService
from core.session.task_selection_service import TaskSelectionService
from core.session.attempt_evaluation_service import AttemptEvaluationService
from core.session.adaptation_service import AdaptationService
from core.session.projection_service import ProjectionService
from core.session.repositories import (
    LearnerProgressRepository,
    TaskAttemptRepository,
    AdaptationEventRepository,
    LearningSessionRepository
)
from core.curriculum.concept_registry import (
    ConceptRegistry,
    LearningTask,
    get_registry
)


class BrainBridgeProtocol(Protocol):
    """Core-facing bridge contract; concrete bridge is wired by application DI."""

    def get_all_mastery(self, user_id: str, concept_ids: list) -> Dict[str, float]:
        ...

    def process_interaction(
        self,
        user_id: str,
        concept_id: str,
        correct: bool,
        response_time: Optional[float] = None,
        trace_context: Any = None,
    ) -> Dict[str, Any]:
        ...


class RuntimeCoordinator:
    """
    Coordinator for the full learning interaction loop.
    
    This orchestrates:
    - Session lifecycle
    - Task selection
    - Attempt evaluation
    - Adaptation generation
    - Projection updates
    - State persistence
    
    This is the true educational loop that bridges semantic curriculum
    with learner interaction.
    """
    
    def __init__(
        self,
        session_service: SessionService,
        task_selection_service: TaskSelectionService,
        attempt_evaluation_service: AttemptEvaluationService,
        adaptation_service: AdaptationService,
        projection_service: ProjectionService,
        learner_progress_repository: Optional[LearnerProgressRepository] = None,
        task_attempt_repository: Optional[TaskAttemptRepository] = None,
        adaptation_event_repository: Optional[AdaptationEventRepository] = None,
        learning_session_repository: Optional[LearningSessionRepository] = None,
        brain_bridge_service: Optional[BrainBridgeProtocol] = None,
        concept_registry: Optional[ConceptRegistry] = None,
        db_store=None,
        event_bus=None
    ):
        """
        Initialize runtime coordinator.
        
        Args:
            session_service: Session lifecycle service
            task_selection_service: Task selection service
            attempt_evaluation_service: Attempt evaluation service
            adaptation_service: Adaptation generation service
            projection_service: Projection service
            learner_progress_repository: Learner progress repository
            task_attempt_repository: Task attempt repository
            adaptation_event_repository: Adaptation event repository
            learning_session_repository: Learning session repository
            brain_bridge_service: Brain bridge service for Unified Brain integration
            concept_registry: Concept registry instance (uses global if None)
            db_store: Database store for outbox pattern (B3.1a)
            event_bus: Event bus for outbox pattern (B3.1a)
        """
        self.session_service = session_service
        self.task_selection_service = task_selection_service
        self.attempt_evaluation_service = attempt_evaluation_service
        self.adaptation_service = adaptation_service
        self.projection_service = projection_service
        self.learner_progress_repository = learner_progress_repository or LearnerProgressRepository()
        self.task_attempt_repository = task_attempt_repository or TaskAttemptRepository()
        self.adaptation_event_repository = adaptation_event_repository or AdaptationEventRepository()
        self.learning_session_repository = learning_session_repository or LearningSessionRepository()
        self.db_store = db_store
        self.event_bus = event_bus
        
        # Application DI must provide the bridge implementation; core only
        # depends on the protocol to preserve strict layering.
        if brain_bridge_service:
            self.brain_bridge_service = brain_bridge_service
        else:
            raise RuntimeError(
                "brain_bridge_service is required for RuntimeCoordinator "
                "(B3.1a outbox-backed cognition is wired in application DI)"
            )
        
        self.concept_registry = concept_registry or get_registry()
    
    def start_learning_session(
        self,
        user_id: str,
        tenant_id: str,
        target_concepts: list,
        initial_concept_id: Optional[str] = None,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Start a new learning session.
        
        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
            target_concepts: List of concept IDs to learn
            initial_concept_id: Optional starting concept
            language: Language for content (en or id)
        
        Returns:
            Dict with session, initial task, and learner projection
        """
        # Start session
        session = self.session_service.start_session(
            user_id=user_id,
            tenant_id=tenant_id,
            target_concepts=target_concepts,
            initial_concept_id=initial_concept_id
        )
        
        # Persist session to learning session repository
        self.learning_session_repository.save(session)
        
        # Get or create learner progress from persistence
        projection = self.learner_progress_repository.get_or_create(user_id)
        
        # Initialize mastery for new target concepts if not present
        for concept_id in target_concepts:
            if concept_id not in projection.concept_mastery:
                projection.concept_mastery[concept_id] = 0
                self.learner_progress_repository.update_mastery(user_id, concept_id, 0.0)
        
        # Get actual mastery from Unified Brain (canonical cognition authority)
        internal_mastery = self.brain_bridge_service.get_all_mastery(user_id, target_concepts)
        
        # Select initial task based on actual mastery from Unified Brain
        task = self.task_selection_service.select_task_for_concept(
            concept_id=session.current_concept_id or target_concepts[0],
            learner_mastery=internal_mastery.get(session.current_concept_id or target_concepts[0], 0.0)
        )
        
        # Get recent performance from persistence
        recent_performance = self.task_attempt_repository.get_recent_performance(user_id)
        
        # Regenerate projection with actual data
        projection = self.projection_service.generate_projection(
            user_id=user_id,
            internal_mastery=internal_mastery,
            current_concept_id=session.current_concept_id or target_concepts[0],
            recent_performance=recent_performance,
            achievements=projection.achievements,
            language=language
        )
        
        # Save projection
        self.learner_progress_repository.save(projection)
        
        return {
            "session": session,
            "task": task,
            "projection": projection
        }
    
    def submit_task_attempt(
        self,
        session_id: str,
        task_id: str,
        learner_response: str,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Submit a task attempt and process the full interaction loop.
        
        Args:
            session_id: Session identifier
            task_id: Task identifier
            learner_response: Learner's response
            language: Language for content (en or id)
        
        Returns:
            Dict with evaluation, adaptation, next task, and updated projection
        """
        # Get session
        session = self.learning_session_repository.get(session_id)
        if session is None:
            raise ValueError(f"Session not found: {session_id}")
        
        # Get task
        task = self.concept_registry.get_concept(task_id)
        if task is None:
            # Try to get from task registry
            task = self.concept_registry.get_concept(task_id)
            if task is None:
                raise ValueError(f"Task not found: {task_id}")
        
        # Create task attempt
        attempt = TaskAttempt(
            id=str(uuid.uuid4()),
            session_id=session_id,
            user_id=session.user_id,
            task_id=task_id,
            concept_id=session.current_concept_id,
            learner_response=learner_response,
            expected_answer="",  # Will be filled by evaluation
            started_at=datetime.utcnow()
        )
        
        # Evaluate attempt
        evaluation = self.attempt_evaluation_service.evaluate_attempt(attempt, task)
        attempt.outcome = evaluation["outcome"]
        attempt.completed_at = datetime.utcnow()
        
        # Persist attempt to repository
        self.task_attempt_repository.save(attempt)
        
        # Update session statistics
        self.session_service.update_session_statistics(
            session_id=session_id,
            task_completed=True,
            correct=(evaluation["outcome"] == TaskOutcome.CORRECT)
        )
        
        # Update session in repository
        self.learning_session_repository.save(session)
        
        # Update mastery based on attempt outcome using Unified Brain (B3.1a: outbox-backed)
        # Unified Brain is the canonical cognition authority
        
        # B3.6: Generate trace context for this interaction
        trace_context = None
        try:
            from core.telemetry.trace_context import create_trace_context, TraceContext
            trace_context = create_trace_context(
                user_id=session.user_id,
                session_id=session_id,
                source="runtime_coordinator",
                component="submit_task_attempt"
            )
        except ImportError:
            trace_context = None
        
        brain_result = self.brain_bridge_service.process_interaction(
            user_id=session.user_id,
            concept_id=session.current_concept_id,
            correct=(evaluation["outcome"] == TaskOutcome.CORRECT),
            response_time=(attempt.completed_at - attempt.started_at).total_seconds() if attempt.completed_at else None,
            trace_context=trace_context
        )
        
        # B3.1a: Outbox-based cognition is async - event emitted, cognition pending
        # NO placeholder mastery values - system acknowledges async processing
        # Current mastery remains unchanged until cognition completes
        # TODO: Implement polling/subscription for cognition results (B3.2)
        current_mastery = self.brain_bridge_service.get_all_mastery(session.user_id, session.target_concepts)
        
        # Get recent performance from persistence
        recent_performance = self.task_attempt_repository.get_recent_performance(session.user_id)
        
        # Generate adaptation (if needed)
        adaptation = self.adaptation_service.generate_adaptation(
            session_id=session_id,
            user_id=session.user_id,
            current_concept_id=session.current_concept_id,
            learner_mastery=current_mastery,
            recent_performance=recent_performance,
            language=language
        )
        
        # Persist adaptation if generated
        if adaptation:
            self.adaptation_event_repository.save(adaptation)
        
        # Apply adaptation if generated
        new_concept_id = session.current_concept_id
        if adaptation and adaptation.new_concept_id:
            new_concept_id = adaptation.new_concept_id
            self.session_service.advance_to_concept(session_id, new_concept_id)
            self.learning_session_repository.save(session)
        
        # Select next task using actual completed task IDs from persistence
        completed_task_ids = self.task_attempt_repository.get_completed_task_ids(session.user_id)
        next_task = self.task_selection_service.select_next_task(
            current_concept_id=new_concept_id,
            learner_mastery=current_mastery,
            completed_task_ids=completed_task_ids
        )
        
        # Update learner projection with actual data
        projection = self.learner_progress_repository.get_or_create(session.user_id)
        self.projection_service.update_projection_with_attempt(
            projection,
            new_concept_id,
            correct=(evaluation["outcome"] == TaskOutcome.CORRECT),
            new_mastery=current_mastery.get(new_concept_id, 0.0)
        )
        
        # Save projection
        self.learner_progress_repository.save(projection)
        
        return {
            "evaluation": evaluation,
            "adaptation": adaptation,
            "next_task": next_task,
            "projection": projection
        }
    
    def get_session_state(
        self,
        session_id: str,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Get current session state.
        
        Args:
            session_id: Session identifier
            language: Language for content (en or id)
        
        Returns:
            Dict with session, current task, and learner projection
        """
        # Get session from persistence
        session = self.learning_session_repository.get(session_id)
        if session is None:
            raise ValueError(f"Session not found: {session_id}")
        
        # Get actual mastery from Unified Brain (canonical cognition authority)
        current_mastery = self.brain_bridge_service.get_all_mastery(session.user_id, session.target_concepts)
        
        # Select current task based on actual mastery from Unified Brain
        task = self.task_selection_service.select_task_for_concept(
            concept_id=session.current_concept_id,
            learner_mastery=current_mastery.get(session.current_concept_id, 0.0)
        )
        
        # Get recent performance from persistence
        recent_performance = self.task_attempt_repository.get_recent_performance(session.user_id)
        
        # Get or create learner projection from persistence
        projection = self.learner_progress_repository.get_or_create(session.user_id)
        
        # Regenerate projection with actual data
        projection = self.projection_service.generate_projection(
            user_id=session.user_id,
            internal_mastery=current_mastery,
            current_concept_id=session.current_concept_id,
            recent_performance=recent_performance,
            achievements=projection.achievements,
            language=language
        )
        
        # Save projection
        self.learner_progress_repository.save(projection)
        
        return {
            "session": session,
            "task": task,
            "projection": projection
        }
    
    def pause_session(self, session_id: str) -> LearningSession:
        """
        Pause a learning session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Updated session
        """
        session = self.session_service.pause_session(session_id)
        self.learning_session_repository.save(session)
        return session
    
    def resume_session(self, session_id: str, language: str = "en") -> Dict[str, Any]:
        """
        Resume a paused learning session.
        
        Args:
            session_id: Session identifier
            language: Language for content (en or id)
        
        Returns:
            Dict with session, current task, and learner projection
        """
        session = self.session_service.resume_session(session_id)
        self.learning_session_repository.save(session)
        return self.get_session_state(session_id, language)
    
    def complete_session(self, session_id: str) -> LearningSession:
        """
        Complete a learning session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Updated session
        """
        session = self.session_service.complete_session(session_id)
        self.learning_session_repository.save(session)
        return session
    
    def resume_session_from_history(
        self,
        user_id: str,
        session_id: str,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Resume a specific session from history.
        
        Args:
            user_id: User identifier
            session_id: Session identifier to resume
            language: Language for content (en or id)
        
        Returns:
            Dict with session, current task, and learner projection
        """
        # Get session from persistence
        session = self.learning_session_repository.get(session_id)
        if session is None:
            raise ValueError(f"Session not found: {session_id}")
        
        # Verify session belongs to user
        if session.user_id != user_id:
            raise ValueError(f"Session {session_id} does not belong to user {user_id}")
        
        # Resume the session
        session = self.session_service.resume_session(session_id)
        self.learning_session_repository.save(session)
        
        # Return session state
        return self.get_session_state(session_id, language)
    
    def get_session_history(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[LearningSession]:
        """
        Get session history for a user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of sessions to return
        
        Returns:
            List of learning sessions
        """
        return self.learning_session_repository.get_by_user(user_id, limit)
    
    def continue_learning_session(
        self,
        user_id: str,
        tenant_id: str,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Continue learning from the most recent active session, or start a new one if none exists.
        
        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
            language: Language for content (en or id)
        
        Returns:
            Dict with session, current task, and learner projection
        """
        # Check for active session
        active_session = self.learning_session_repository.get_active_by_user(user_id)
        
        if active_session:
            # Resume active session
            return self.resume_session_from_history(user_id, active_session.id, language)
        
        # Check for most recent completed session to continue from
        session_history = self.learning_session_repository.get_by_user(user_id, limit=1)
        
        if session_history:
            most_recent = session_history[0]
            # Start new session with same target concepts
            return self.start_learning_session(
                user_id=user_id,
                tenant_id=tenant_id,
                target_concepts=most_recent.target_concepts,
                initial_concept_id=most_recent.current_concept_id,
                language=language
            )
        
        # No session history, start fresh with default concepts
        # Get all available concepts from registry
        all_concepts = self.concept_registry.get_all_concepts()
        target_concepts = [c.id for c in all_concepts[:8]]  # First 8 concepts
        
        return self.start_learning_session(
            user_id=user_id,
            tenant_id=tenant_id,
            target_concepts=target_concepts,
            language=language
        )
    
    def get_learner_journey(
        self,
        user_id: str,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Get complete learner journey across all sessions.
        
        Args:
            user_id: User identifier
            language: Language for content (en or id)
        
        Returns:
            Dict with session history, current projection, and journey statistics
        """
        # Get session history
        session_history = self.learning_session_repository.get_by_user(user_id, limit=50)
        
        # Get current learner projection
        projection = self.learner_progress_repository.get_or_create(user_id)
        
        # Get actual mastery from Unified Brain
        if session_history:
            all_concepts = set()
            for session in session_history:
                all_concepts.update(session.target_concepts)
            internal_mastery = self.brain_bridge_service.get_all_mastery(user_id, list(all_concepts))
        else:
            internal_mastery = {}
        
        # Regenerate projection with actual data
        recent_performance = self.task_attempt_repository.get_recent_performance(user_id)
        projection = self.projection_service.generate_projection(
            user_id=user_id,
            internal_mastery=internal_mastery,
            current_concept_id=projection.current_concept_id,
            recent_performance=recent_performance,
            achievements=projection.achievements,
            language=language
        )
        
        # Calculate journey statistics
        total_sessions = len(session_history)
        total_tasks = sum(s.tasks_completed for s in session_history)
        total_correct = sum(s.correct_count for s in session_history)
        overall_accuracy = total_correct / max(total_tasks, 1)
        
        # Get adaptation history
        adaptation_history = self.adaptation_event_repository.get_by_user(user_id, limit=20)
        
        return {
            "session_history": session_history,
            "projection": projection,
            "statistics": {
                "total_sessions": total_sessions,
                "total_tasks": total_tasks,
                "total_correct": total_correct,
                "overall_accuracy": overall_accuracy,
                "best_streak": projection.best_streak,
                "total_achievements": len(projection.achievements)
            },
            "adaptation_history": adaptation_history
        }
