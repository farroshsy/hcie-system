"""
Adaptation Service - Pedagogical Transition Generation

This service generates human-readable adaptation decisions:
- Remediation strategies
- Escalation opportunities
- Prerequisite reviews
- Transfer opportunities
- Milestone achievements

Key Design Principles:
- Pedagogical reasoning (NOT governance internals)
- Human-readable explanations
- Localized feedback
- Concept-aware transitions
"""

from typing import Optional, Dict, Any
from datetime import datetime
import uuid

from core.session.models import (
    AdaptationEvent,
    AdaptationType
)
from core.curriculum.concept_registry import (
    ConceptRegistry,
    get_registry
)
from core.session.models import generate_adaptation_explanation


class AdaptationService:
    """
    Service for generating pedagogical adaptation decisions.
    
    This provides human-readable adaptation transitions based on:
    - Learner performance
    - Concept mastery
    - Curriculum dependencies
    - Pedagogical strategies
    
    CRITICAL: This does NOT expose JT, ensemble weights, uncertainty internals,
    or governance metrics to learners. It provides pedagogical explanations only.
    """
    
    def __init__(self, concept_registry: Optional[ConceptRegistry] = None):
        """
        Initialize adaptation service.
        
        Args:
            concept_registry: Concept registry instance (uses global if None)
        """
        self.concept_registry = concept_registry or get_registry()
    
    def generate_adaptation(
        self,
        session_id: str,
        user_id: str,
        current_concept_id: str,
        learner_mastery: Dict[str, float],
        recent_performance: Dict[str, Any],
        language: str = "en"
    ) -> Optional[AdaptationEvent]:
        """
        Generate an adaptation event based on learner state.
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            current_concept_id: Current concept identifier
            learner_mastery: Dict of concept_id -> mastery (0-1 scale)
            recent_performance: Dict with recent performance metrics
            language: Language for explanations (en or id)
        
        Returns:
            AdaptationEvent or None if no adaptation needed
        """
        current_mastery = learner_mastery.get(current_concept_id, 0.0)
        recent_accuracy = recent_performance.get("accuracy", 0.0)
        recent_attempts = recent_performance.get("attempts", 0)
        
        # Check for milestone achievement
        if current_mastery >= 0.8 and recent_attempts >= 3:
            return self._generate_milestone_achievement(
                session_id, user_id, current_concept_id, language
            )
        
        # Check for remediation need
        if recent_accuracy < 0.3 and recent_attempts >= 2:
            # Check if there are prerequisites to review
            concept = self.concept_registry.get_concept(current_concept_id)
            if concept and concept.prerequisites:
                return self._generate_prerequisite_review(
                    session_id, user_id, current_concept_id,
                    concept.prerequisites[0], language
                )
            else:
                return self._generate_remediation(
                    session_id, user_id, current_concept_id, language
                )
        
        # Check for escalation opportunity
        if current_mastery >= 0.7 and recent_accuracy >= 0.7:
            concept = self.concept_registry.get_concept(current_concept_id)
            if concept and concept.supports:
                return self._generate_escalation(
                    session_id, user_id, current_concept_id,
                    concept.supports[0], language
                )
        
        # Check for transfer opportunity
        if current_mastery >= 0.6:
            concept = self.concept_registry.get_concept(current_concept_id)
            if concept and concept.transfer_edges:
                return self._generate_transfer_opportunity(
                    session_id, user_id, current_concept_id,
                    concept.transfer_edges[0], language
                )
        
        return None
    
    def _generate_milestone_achievement(
        self,
        session_id: str,
        user_id: str,
        concept_id: str,
        language: str
    ) -> AdaptationEvent:
        """
        Generate a milestone achievement adaptation.
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            concept_id: Concept identifier
            language: Language for explanations
        
        Returns:
            AdaptationEvent for milestone achievement
        """
        explanation, reasoning = generate_adaptation_explanation(
            AdaptationType.MILESTONE_ACHIEVED,
            concept_id,
            concept_id,  # Same concept for milestone
            self.concept_registry,
            language
        )
        
        return AdaptationEvent(
            id=str(uuid.uuid4()),
            session_id=session_id,
            user_id=user_id,
            adaptation_type=AdaptationType.MILESTONE_ACHIEVED,
            previous_concept_id=concept_id,
            new_concept_id=concept_id,
            explanation_en=explanation if language == "en" else "",
            explanation_id=explanation if language == "id" else "",
            reasoning_en=reasoning if language == "en" else "",
            reasoning_id=reasoning if language == "id" else "",
            created_at=datetime.utcnow(),
            research_metadata={
                "trigger": "mastery_threshold",
                "mastery": ">=0.8"
            }
        )
    
    def _generate_remediation(
        self,
        session_id: str,
        user_id: str,
        concept_id: str,
        language: str
    ) -> AdaptationEvent:
        """
        Generate a remediation adaptation.
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            concept_id: Concept identifier
            language: Language for explanations
        
        Returns:
            AdaptationEvent for remediation
        """
        explanation, reasoning = generate_adaptation_explanation(
            AdaptationType.REMEDIATION,
            concept_id,
            concept_id,  # Same concept for remediation
            self.concept_registry,
            language
        )
        
        return AdaptationEvent(
            id=str(uuid.uuid4()),
            session_id=session_id,
            user_id=user_id,
            adaptation_type=AdaptationType.REMEDIATION,
            previous_concept_id=concept_id,
            new_concept_id=concept_id,
            explanation_en=explanation if language == "en" else "",
            explanation_id=explanation if language == "id" else "",
            reasoning_en=reasoning if language == "en" else "",
            reasoning_id=reasoning if language == "id" else "",
            created_at=datetime.utcnow(),
            research_metadata={
                "trigger": "low_performance",
                "accuracy": "<0.3"
            }
        )
    
    def _generate_prerequisite_review(
        self,
        session_id: str,
        user_id: str,
        current_concept_id: str,
        prerequisite_concept_id: str,
        language: str
    ) -> AdaptationEvent:
        """
        Generate a prerequisite review adaptation.
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            current_concept_id: Current concept identifier
            prerequisite_concept_id: Prerequisite concept identifier
            language: Language for explanations
        
        Returns:
            AdaptationEvent for prerequisite review
        """
        explanation, reasoning = generate_adaptation_explanation(
            AdaptationType.PREREQUISITE_REVIEW,
            current_concept_id,
            prerequisite_concept_id,
            self.concept_registry,
            language
        )
        
        return AdaptationEvent(
            id=str(uuid.uuid4()),
            session_id=session_id,
            user_id=user_id,
            adaptation_type=AdaptationType.PREREQUISITE_REVIEW,
            previous_concept_id=current_concept_id,
            new_concept_id=prerequisite_concept_id,
            explanation_en=explanation if language == "en" else "",
            explanation_id=explanation if language == "id" else "",
            reasoning_en=reasoning if language == "en" else "",
            reasoning_id=reasoning if language == "id" else "",
            created_at=datetime.utcnow(),
            research_metadata={
                "trigger": "prerequisite_needed",
                "prerequisite": prerequisite_concept_id
            }
        )
    
    def _generate_escalation(
        self,
        session_id: str,
        user_id: str,
        current_concept_id: str,
        new_concept_id: str,
        language: str
    ) -> AdaptationEvent:
        """
        Generate an escalation adaptation.
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            current_concept_id: Current concept identifier
            new_concept_id: New concept identifier
            language: Language for explanations
        
        Returns:
            AdaptationEvent for escalation
        """
        explanation, reasoning = generate_adaptation_explanation(
            AdaptationType.ESCALATION,
            current_concept_id,
            new_concept_id,
            self.concept_registry,
            language
        )
        
        return AdaptationEvent(
            id=str(uuid.uuid4()),
            session_id=session_id,
            user_id=user_id,
            adaptation_type=AdaptationType.ESCALATION,
            previous_concept_id=current_concept_id,
            new_concept_id=new_concept_id,
            explanation_en=explanation if language == "en" else "",
            explanation_id=explanation if language == "id" else "",
            reasoning_en=reasoning if language == "en" else "",
            reasoning_id=reasoning if language == "id" else "",
            created_at=datetime.utcnow(),
            research_metadata={
                "trigger": "mastery_threshold",
                "mastery": ">=0.7"
            }
        )
    
    def _generate_transfer_opportunity(
        self,
        session_id: str,
        user_id: str,
        current_concept_id: str,
        transfer_concept_id: str,
        language: str
    ) -> AdaptationEvent:
        """
        Generate a transfer opportunity adaptation.
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            current_concept_id: Current concept identifier
            transfer_concept_id: Transfer concept identifier
            language: Language for explanations
        
        Returns:
            AdaptationEvent for transfer opportunity
        """
        explanation, reasoning = generate_adaptation_explanation(
            AdaptationType.TRANSFER_OPPORTUNITY,
            current_concept_id,
            transfer_concept_id,
            self.concept_registry,
            language
        )
        
        return AdaptationEvent(
            id=str(uuid.uuid4()),
            session_id=session_id,
            user_id=user_id,
            adaptation_type=AdaptationType.TRANSFER_OPPORTUNITY,
            previous_concept_id=current_concept_id,
            new_concept_id=transfer_concept_id,
            explanation_en=explanation if language == "en" else "",
            explanation_id=explanation if language == "id" else "",
            reasoning_en=reasoning if language == "en" else "",
            reasoning_id=reasoning if language == "id" else "",
            created_at=datetime.utcnow(),
            research_metadata={
                "trigger": "transfer_eligible",
                "mastery": ">=0.6"
            }
        )
    
    def generate_streak_bonus(
        self,
        session_id: str,
        user_id: str,
        streak_count: int,
        language: str = "en"
    ) -> AdaptationEvent:
        """
        Generate a streak bonus adaptation.
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            streak_count: Current streak count
            language: Language for explanations
        
        Returns:
            AdaptationEvent for streak bonus
        """
        explanation, reasoning = generate_adaptation_explanation(
            AdaptationType.STREAK_BONUS,
            "",  # No concept change for streak
            str(streak_count),  # Use streak count as "concept"
            self.concept_registry,
            language
        )
        
        return AdaptationEvent(
            id=str(uuid.uuid4()),
            session_id=session_id,
            user_id=user_id,
            adaptation_type=AdaptationType.STREAK_BONUS,
            explanation_en=explanation if language == "en" else "",
            explanation_id=explanation if language == "id" else "",
            reasoning_en=reasoning if language == "en" else "",
            reasoning_id=reasoning if language == "id" else "",
            created_at=datetime.utcnow(),
            research_metadata={
                "trigger": "streak_achieved",
                "streak_count": str(streak_count)
            }
        )
