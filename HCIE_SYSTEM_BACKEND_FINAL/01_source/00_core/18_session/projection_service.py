"""
Projection Service - Frontend-Safe Learner Projection

This service transforms internal cognitive state into human pedagogical state:
- Internal cognition → Pedagogical abstraction → Frontend-safe rendering

Key Design Principles:
- NEVER expose JT, ensemble weights, uncertainty internals, governance metrics
- Frontend exposes "human pedagogical state" only
- Language-independent cognition with localized presentation
- Simplified mastery representation (0-100 scale)
"""

import logging
from typing import Dict, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

from core.session.models import (
    LearnerProjection
)
from core.curriculum.concept_registry import (
    ConceptRegistry,
    get_registry
)
from core.session.models import generate_learner_projection


class ProjectionService:
    """
    Service for generating frontend-safe learner projections.
    
    This transforms internal cognitive state into human pedagogical state
    that is safe to expose to frontend learners.
    
    CRITICAL: This is the ONLY place where internal cognition (JT, ensemble, etc.)
    is transformed into human pedagogical state. Frontend should NEVER receive
    governance internals directly.
    """
    
    def __init__(self, concept_registry: Optional[ConceptRegistry] = None, cognitive_store=None, cache_store=None):
        """
        Initialize projection service.
        
        Args:
            concept_registry: Concept registry instance (DEPRECATED: kept for compatibility only)
            cognitive_store: Database store for cognitive state (B3.4: async support)
            cache_store: Cache store for projections (B3.4: async support)
        
        NOTE: concept_registry is DEPRECATED and will be removed in deterministic refactor.
        ProjectionService must derive projections ONLY from canonical event payload.
        """
        self.concept_registry = concept_registry  # DEPRECATED: will be removed
        self.cognitive_store = cognitive_store
        self.cache_store = cache_store
    
    def generate_projection(
        self,
        user_id: str,
        internal_mastery: Dict[str, float],  # Internal 0-1 scale from cognition
        current_concept_id: str,
        recent_performance: Dict[str, float],
        achievements: list,
        language: str = "en"
    ) -> LearnerProjection:
        """
        Generate frontend-safe learner projection from internal cognitive state.
        
        DEPRECATED: This method uses concept_registry (replay poison).
        Use generate_projection_async() instead (deterministic pure).
        
        Args:
            user_id: User identifier
            internal_mastery: Dict of concept_id -> internal mastery (0-1 scale)
            current_concept_id: Current concept identifier
            recent_performance: Dict with recent performance metrics
            achievements: List of achievement IDs
            language: Language for localized content (en or id)
        
        Returns:
            LearnerProjection with human pedagogical state
        """
        # Use the helper function from models.py
        projection = generate_learner_projection(
            user_id=user_id,
            concept_mastery=internal_mastery,
            current_concept_id=current_concept_id,
            concept_registry=self.concept_registry,
            language=language
        )
        
        # Add recent performance
        projection.recent_accuracy = recent_performance.get("accuracy", 0.0)
        projection.recent_task_count = recent_performance.get("attempts", 0)
        
        # Add achievements
        projection.achievements = achievements
        
        # Calculate streak from recent performance
        if recent_performance.get("current_streak"):
            projection.current_streak = recent_performance["current_streak"]
        if recent_performance.get("best_streak"):
            projection.best_streak = recent_performance["best_streak"]
        
        # Calculate total tasks completed
        projection.total_tasks_completed = sum(
            int(m * 10) for m in internal_mastery.values()
        )  # Rough estimate: mastery * 10 tasks per concept
        
        # DEPRECATED: Generate recommendation based on mastery (uses registry)
        self._generate_recommendation(projection, internal_mastery, language)
        
        return projection
    
    def generate_projection_async(
        self,
        user_id: str,
        concept_id: str,
        cognitive_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        B3.4: Generate projection from cognitive state (async pattern)
        
        DETERMINISTIC PURE: Derives projections ONLY from canonical event payload.
        No registry lookups, no graph dependencies, no mutable runtime state.
        
        Args:
            user_id: User identifier
            concept_id: Concept identifier
            cognitive_state: Dict with mastery, uncertainty, zpd_score, etc.
        
        Returns:
            Dict with projection data (serializable for events)
        """
        # Extract canonical cognitive state from event payload
        mastery = cognitive_state.get("mastery", 0.0)
        uncertainty = cognitive_state.get("uncertainty", 0.0)
        zpd_score = cognitive_state.get("zpd_score", 0.0)
        
        # DETERMINISTIC: Calculate projected mastery (0-100 scale for frontend)
        projected_mastery = mastery * 100
        
        # DETERMINISTIC: Calculate projected difficulty based on mastery and ZPD only
        # No registry lookups - pure mathematical transform
        base_difficulty = 0.5  # Default difficulty (no registry dependency)
        mastery_adjustment = mastery * 0.3  # Up to 0.3 increase from mastery
        zpd_adjustment = zpd_score * 0.2  # Up to 0.2 increase from ZPD
        projected_difficulty = max(0.0, min(1.0, base_difficulty + mastery_adjustment + zpd_adjustment))
        
        # DETERMINISTIC: ZPD alignment is direct from cognitive state
        zpd_alignment = zpd_score
        
        # DETERMINISTIC: No concept recommendations from registry traversal
        # Recommendations should come from ProjectionStore (event-driven), not runtime graph
        recommended_concepts = []  # Empty until ProjectionStore is implemented
        
        return {
            "projected_mastery": projected_mastery,
            "projected_difficulty": projected_difficulty,
            "recommended_concepts": recommended_concepts,
            "zpd_alignment": zpd_alignment,
            "concept_id": concept_id,
            "concept_name": concept_id,  # Use concept_id directly (no registry lookup)
            "uncertainty": uncertainty
        }
    
    def _calculate_projected_difficulty(
        self,
        mastery: float,
        zpd_score: float,
        base_difficulty: float
    ) -> float:
        """
        Calculate projected difficulty based on mastery and ZPD.
        
        DEPRECATED: This method is no longer used in generate_projection_async().
        Logic is now inlined as deterministic pure transform.
        
        Higher mastery + higher ZPD alignment = higher difficulty recommended
        """
        # Base adjustment from mastery
        mastery_adjustment = mastery * 0.3  # Up to 0.3 increase from mastery
        
        # ZPD adjustment
        zpd_adjustment = zpd_score * 0.2  # Up to 0.2 increase from ZPD
        
        # Calculate projected difficulty (clamped 0-1)
        projected = base_difficulty + mastery_adjustment + zpd_adjustment
        return max(0.0, min(1.0, projected))
    
    def _generate_recommended_concepts(
        self,
        user_id: str,
        current_concept_id: str,
        mastery: float,
        zpd_score: float
    ) -> list:
        """
        Generate recommended concepts based on current state.
        
        DEPRECATED: This method uses concept_registry.get_all_concepts() (replay poison).
        No longer used in generate_projection_async().
        Recommendations should come from ProjectionStore (event-driven).
        
        Returns concepts within ZPD range.
        """
        # Get all concepts from registry
        all_concepts = self.concept_registry.get_all_concepts()
        
        # Filter concepts within ZPD range
        recommended = []
        for concept in all_concepts:
            concept_id = concept["id"]
            
            # Skip current concept
            if concept_id == current_concept_id:
                continue
            
            # Calculate ZPD alignment for this concept
            concept_difficulty = concept.get("difficulty", 0.5)
            zpd_lower = mastery - 0.2  # ZPD lower bound
            zpd_upper = mastery + 0.2  # ZPD upper bound
            
            # Check if within ZPD
            if zpd_lower <= concept_difficulty <= zpd_upper:
                recommended.append({
                    "concept_id": concept_id,
                    "concept_name": concept.get("name", concept_id),
                    "difficulty": concept_difficulty,
                    "zpd_alignment": 1.0 - abs(concept_difficulty - mastery) / 0.2
                })
        
        # Sort by ZPD alignment and return top 5
        recommended.sort(key=lambda x: x["zpd_alignment"], reverse=True)
        return recommended[:5]
    
    def _generate_recommendation(
        self,
        projection: LearnerProjection,
        internal_mastery: Dict[str, float],
        language: str
    ):
        """
        Generate recommended next step based on mastery state.
        
        DEPRECATED: This method uses concept_registry lookups (replay poison).
        No longer used in generate_projection_async().
        
        Args:
            projection: Learner projection to update
            internal_mastery: Internal mastery state
            language: Language for recommendations
        """
        current_concept = projection.current_concept_id
        current_mastery = internal_mastery.get(current_concept, 0.0)
        
        # Get concept details
        concept = self.concept_registry.get_concept(current_concept)
        if not concept:
            return
        
        # If current concept is mastered, recommend next concept
        if current_mastery >= concept.mastery_threshold:
            if concept.supports:
                next_concept = concept.supports[0]
                next_mastery = internal_mastery.get(next_concept, 0.0)
                
                if next_mastery < concept.mastery_threshold:
                    projection.recommended_concept_id = next_concept
                    if language == "en":
                        projection.recommended_reason_en = f"You've mastered {concept.canonical_name}. Let's try {self.concept_registry.get_concept(next_concept).canonical_name if self.concept_registry.get_concept(next_concept) else next_concept}!"
                        projection.recommended_reason_id = f"Anda telah menguasai {concept.canonical_name}. Mari coba {self.concept_registry.get_concept(next_concept).canonical_name if self.concept_registry.get_concept(next_concept) else next_concept}!"
                    else:
                        projection.recommended_reason_id = f"Anda telah menguasai {concept.canonical_name}. Mari coba {self.concept_registry.get_concept(next_concept).canonical_name if self.concept_registry.get_concept(next_concept) else next_concept}!"
                        projection.recommended_reason_en = f"You've mastered {concept.canonical_name}. Let's try {self.concept_registry.get_concept(next_concept).canonical_name if self.concept_registry.get_concept(next_concept) else next_concept}!"
        
        # If current concept needs more practice
        elif current_mastery < 0.5:
            projection.recommended_concept_id = current_concept
            if language == "en":
                projection.recommended_reason_en = f"Keep practicing {concept.canonical_name} to build your foundation."
                projection.recommended_reason_id = f"Tetap berlatih {concept.canonical_name} untuk memperkuat dasar Anda."
            else:
                projection.recommended_reason_id = f"Tetap berlatih {concept.canonical_name} untuk memperkuat dasar Anda."
                projection.recommended_reason_en = f"Keep practicing {concept.canonical_name} to build your foundation."
    
    def update_projection_with_attempt(
        self,
        projection: LearnerProjection,
        concept_id: str,
        correct: bool,
        new_mastery: float
    ):
        """
        Update projection after a task attempt.
        
        Args:
            projection: Learner projection to update
            concept_id: Concept identifier
            correct: Whether the attempt was correct
            new_mastery: New mastery value for the concept
        """
        # Update mastery (convert to 0-100 scale)
        projection.concept_mastery[concept_id] = int(new_mastery * 100)
        
        # Update recent performance
        projection.recent_task_count += 1
        if correct:
            projection.current_streak += 1
            if projection.current_streak > projection.best_streak:
                projection.best_streak = projection.current_streak
        else:
            projection.current_streak = 0
        
        # Update progress indicators
        mastered = sum(1 for m in projection.concept_mastery.values() if m >= 70)
        in_progress = sum(1 for m in projection.concept_mastery.values() if 30 <= m < 70)
        projection.concepts_mastered = mastered
        projection.concepts_in_progress = in_progress
        
        # Update total tasks completed
        projection.total_tasks_completed += 1
        
        # Regenerate recommendation
        internal_mastery = {k: v / 100.0 for k, v in projection.concept_mastery.items()}
        self._generate_recommendation(projection, internal_mastery, "en")
        
        projection.updated_at = datetime.utcnow()
    
    def add_achievement(
        self,
        projection: LearnerProjection,
        achievement_id: str
    ):
        """
        Add an achievement to the projection.
        
        Args:
            projection: Learner projection to update
            achievement_id: Achievement identifier
        """
        if achievement_id not in projection.achievements:
            projection.achievements.append(achievement_id)
            projection.updated_at = datetime.utcnow()
