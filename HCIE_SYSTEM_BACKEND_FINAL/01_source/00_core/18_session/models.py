"""
Session Runtime Models - Bridge between Semantic Curriculum and Learner Interaction

This layer provides canonical runtime entities for persistent interaction orchestration.

Key Design Principles:
- Backend: cognition engine, governance runtime, adaptation controller
- Frontend: educational renderer, interaction orchestrator
- NEVER expose JT, ensemble weights, uncertainty internals, governance metrics to learners
- Frontend exposes "human pedagogical state" only
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum


class SessionStatus(Enum):
    """Status of a learning session"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class AdaptationType(Enum):
    """Human-readable adaptation types (NOT governance internals)"""
    REMEDIATION = "remediation"
    ESCALATION = "escalation"
    PREREQUISITE_REVIEW = "prerequisite_review"
    TRANSFER_OPPORTUNITY = "transfer_opportunity"
    MILESTONE_ACHIEVED = "milestone_achieved"
    STREAK_BONUS = "streak_bonus"


class TaskOutcome(Enum):
    """Outcome of a task attempt"""
    CORRECT = "correct"
    INCORRECT = "incorrect"
    PARTIAL = "partial"
    SKIPPED = "skipped"


@dataclass
class LearningSession:
    """
    Continuous interaction session for a learner.
    
    This provides session-level continuity across multiple task attempts.
    """
    id: str
    user_id: str
    tenant_id: str
    
    # Session metadata
    status: SessionStatus = SessionStatus.ACTIVE
    started_at: datetime = field(default_factory=datetime.utcnow)
    paused_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    abandoned_at: Optional[datetime] = None
    
    # Curriculum context
    current_concept_id: Optional[str] = None
    target_concepts: List[str] = field(default_factory=list)
    
    # Session statistics
    tasks_completed: int = 0
    tasks_attempted: int = 0
    correct_count: int = 0
    current_streak: int = 0
    best_streak: int = 0
    
    # Research metadata
    research_metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class TaskAttempt:
    """
    Observable interaction trace for a single task attempt.
    
    This provides replayability and debugging clarity for each interaction.
    """
    id: str
    session_id: str
    user_id: str
    task_id: str
    concept_id: str
    
    # Attempt metadata
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    outcome: Optional[TaskOutcome] = None
    
    # Interaction data
    learner_response: str = ""
    expected_answer: str = ""
    hints_used: int = 0
    time_spent_seconds: int = 0
    
    # Cognitive diagnostics (for research, NOT exposed to learners)
    misconception_triggered: Optional[str] = None
    cognitive_operation: Optional[str] = None
    
    # Research metadata
    research_metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class AdaptationEvent:
    """
    Human-readable behavioral shift explanation.
    
    This explains WHY the system made an adaptation decision.
    Frontend-safe: no JT, ensemble weights, or governance internals.
    """
    id: str
    session_id: str
    user_id: str
    
    # Adaptation type (human-readable)
    adaptation_type: AdaptationType
    
    # What changed
    previous_concept_id: Optional[str] = None
    new_concept_id: Optional[str] = None
    previous_task_id: Optional[str] = None
    new_task_id: Optional[str] = None
    
    # Human-readable explanation (localized)
    explanation_en: str = ""
    explanation_id: str = ""
    
    # Pedagogical reasoning (human-readable, NOT governance internals)
    reasoning_en: str = ""
    reasoning_id: str = ""
    
    # When this occurred
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    # Research metadata (for tracing adaptation decisions)
    research_metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class LearnerProjection:
    """
    Frontend-safe learner state projection.
    
    This is the ONLY learner state exposed to frontend.
    Contains human pedagogical state, NOT JT/ensemble internals.
    """
    user_id: str
    
    # Current learning context
    current_concept_id: Optional[str] = None
    current_concept_name_en: str = ""
    current_concept_name_id: str = ""
    
    # Progress indicators (human-readable)
    concepts_mastered: int = 0
    concepts_in_progress: int = 0
    total_concepts: int = 0
    
    # Mastery by concept (human-readable 0-100 scale)
    concept_mastery: Dict[str, int] = field(default_factory=dict)
    # e.g., {"sequence": 85, "variables": 60, "conditionals": 30}
    
    # Recent performance (human-readable)
    recent_accuracy: float = 0.0  # 0-1 scale
    recent_task_count: int = 0
    
    # Streak and engagement
    current_streak: int = 0
    best_streak: int = 0
    total_tasks_completed: int = 0
    
    # Recommended next steps (human-readable)
    recommended_concept_id: Optional[str] = None
    recommended_reason_en: str = ""
    recommended_reason_id: str = ""
    
    # Achievements (human-readable)
    achievements: List[str] = field(default_factory=list)
    # e.g., ["first_sequence_complete", "loops_master"]
    
    # Last updated
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SessionState:
    """
    Current runtime projection of a session.
    
    This provides the immediate state needed for task selection and rendering.
    """
    session_id: str
    user_id: str
    
    # Current task context
    current_task_id: Optional[str] = None
    current_concept_id: Optional[str] = None
    
    # Interaction state
    awaiting_response: bool = False
    response_pending_since: Optional[datetime] = None
    
    # Adaptation state
    last_adaptation_event_id: Optional[str] = None
    adaptation_pending: bool = False
    
    # Session-level metrics (for research, NOT exposed to learners)
    session_jt_history: List[float] = field(default_factory=list)
    session_uncertainty_history: List[float] = field(default_factory=list)
    
    # Last updated
    updated_at: datetime = field(default_factory=datetime.utcnow)


# === Human Pedagogical State Helpers ===

def generate_learner_projection(
    user_id: str,
    concept_mastery: Dict[str, float],  # Internal 0-1 scale
    current_concept_id: str,
    concept_registry,
    language: str = "en"
) -> LearnerProjection:
    """
    Generate frontend-safe learner projection from internal cognitive state.
    
    This is the ONLY place where internal cognition (JT, ensemble, etc.)
    is transformed into human pedagogical state.
    """
    projection = LearnerProjection(user_id=user_id)
    
    # Map internal concept mastery to human-readable 0-100 scale
    for concept_id, internal_mastery in concept_mastery.items():
        projection.concept_mastery[concept_id] = int(internal_mastery * 100)
    
    # Set current concept with localized names
    concept = concept_registry.get_concept(current_concept_id)
    if concept:
        projection.current_concept_id = current_concept_id
        projection.current_concept_name_en = concept.translations.get("en", {}).get("title", "")
        projection.current_concept_name_id = concept.translations.get("id", {}).get("title", "")
    
    # Calculate progress indicators
    mastered = sum(1 for m in concept_mastery.values() if m >= 0.7)
    in_progress = sum(1 for m in concept_mastery.values() if 0.3 <= m < 0.7)
    projection.concepts_mastered = mastered
    projection.concepts_in_progress = in_progress
    projection.total_concepts = len(concept_mastery)
    
    return projection


def generate_adaptation_explanation(
    adaptation_type: AdaptationType,
    previous_concept_id: str,
    new_concept_id: str,
    concept_registry,
    language: str = "en"
) -> tuple[str, str]:
    """
    Generate human-readable adaptation explanation.
    
    Returns: (explanation, reasoning) in the specified language
    """
    prev_concept = concept_registry.get_concept(previous_concept_id)
    new_concept = concept_registry.get_concept(new_concept_id)
    
    prev_name_en = prev_concept.translations.get("en", {}).get("title", previous_concept_id) if prev_concept else previous_concept_id
    new_name_en = new_concept.translations.get("en", {}).get("title", new_concept_id) if new_concept else new_concept_id
    
    prev_name_id = prev_concept.translations.get("id", {}).get("title", previous_concept_id) if prev_concept else previous_concept_id
    new_name_id = new_concept.translations.get("id", {}).get("title", new_concept_id) if new_concept else new_concept_id
    
    if adaptation_type == AdaptationType.REMEDIATION:
        explanation_en = f"Let's review {prev_name_en} to strengthen your foundation."
        explanation_id = f"Mari tinjau ulang {prev_name_id} untuk memperkuat dasar Anda."
        reasoning_en = f"You need more practice with {prev_name_en} before moving to {new_name_en}."
        reasoning_id = f"Anda perlu lebih banyak latihan dengan {prev_name_id} sebelum melanjutkan ke {new_name_id}."
    elif adaptation_type == AdaptationType.ESCALATION:
        explanation_en = f"You're ready to advance to {new_name_en}!"
        explanation_id = f"Anda siap untuk maju ke {new_name_id}!"
        reasoning_en = f"You've shown strong mastery of {prev_name_en}."
        reasoning_id = f"Anda telah menunjukkan penguasaan yang kuat atas {prev_name_id}."
    elif adaptation_type == AdaptationType.PREREQUISITE_REVIEW:
        explanation_en = f"Let's review {prev_name_en}, which is needed for {new_name_en}."
        explanation_id = f"Mari tinjau ulang {prev_name_id}, yang diperlukan untuk {new_name_id}."
        reasoning_en = f"{new_name_en} requires understanding of {prev_name_en} first."
        reasoning_id = f"{new_name_id} memerlukan pemahaman tentang {prev_name_id} terlebih dahulu."
    elif adaptation_type == AdaptationType.TRANSFER_OPPORTUNITY:
        explanation_en = f"Your skills in {prev_name_en} will help with {new_name_en}!"
        explanation_id = f"Keterampilan Anda dalam {prev_name_id} akan membantu dengan {new_name_id}!"
        reasoning_en = "These concepts share similar cognitive patterns."
        reasoning_id = "Konsep-konsep ini berbagi pola kognitif yang serupa."
    elif adaptation_type == AdaptationType.MILESTONE_ACHIEVED:
        explanation_en = f"Congratulations! You've mastered {prev_name_en}!"
        explanation_id = f"Selamat! Anda telah menguasai {prev_name_id}!"
        reasoning_en = "You've demonstrated consistent mastery through multiple tasks."
        reasoning_id = "Anda telah menunjukkan penguasaan yang konsisten melalui beberapa tugas."
    elif adaptation_type == AdaptationType.STREAK_BONUS:
        explanation_en = f"Great job! You're on a {new_name_en} streak!"
        explanation_id = f"Kerja bagus! Anda sedang dalam streak {new_name_id}!"
        reasoning_en = "Consistent correct answers show strong understanding."
        reasoning_id = "Jawaban benar yang konsisten menunjukkan pemahaman yang kuat."
    else:
        explanation_en = f"Moving to {new_name_en}."
        explanation_id = f"Berpindah ke {new_name_id}."
        reasoning_en = "Continuing your learning journey."
        reasoning_id = "Melanjutkan perjalanan belajar Anda."
    
    if language == "id":
        return explanation_id, reasoning_id
    return explanation_en, reasoning_en
