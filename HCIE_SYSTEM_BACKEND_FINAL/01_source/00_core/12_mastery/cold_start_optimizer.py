"""
Cold Start Optimizer - Personalized initial mastery estimation
"""

import logging
from typing import Dict, Any, Optional
import random

logger = logging.getLogger(__name__)

class ColdStartOptimizer:
    """Provides personalized cold-start mastery instead of generic 0.3"""
    
    # Concept difficulty profiles (based on cognitive complexity)
    CONCEPT_DIFFICULTY = {
        "k2_algorithms": 0.2,           # Simple concepts
        "k2_computing_systems_devices": 0.15,
        "ct_problem_identification": 0.25,
        
        "k5_algorithms": 0.4,           # Medium concepts  
        "k5_computing_systems_devices": 0.35,
        "ct_algorithms": 0.45,
        
        "k8_algorithms": 0.6,           # Advanced concepts
        "k8_computing_systems_devices": 0.55,
    }
    
    # User cohort profiles (simplified)
    COHORT_PROFILES = {
        "beginner": {"base_mastery": 0.25, "variance": 0.1},
        "intermediate": {"base_mastery": 0.4, "variance": 0.15},
        "advanced": {"base_mastery": 0.6, "variance": 0.1}
    }
    
    @staticmethod
    def get_personalized_mastery(user_id: str, concept: str, user_profile: Optional[Dict[str, Any]] = None) -> float:
        """
        Get personalized cold-start mastery for user/concept
        """
        try:
            # Get concept difficulty
            concept_difficulty = ColdStartOptimizer.CONCEPT_DIFFICULTY.get(concept, 0.3)
            
            # Determine user cohort (simplified - in production use real user data)
            if user_profile:
                cohort = user_profile.get("cohort", "beginner")
            else:
                # Simple heuristic based on user_id hash for demo
                user_hash = hash(user_id) % 3
                cohort_names = ["beginner", "intermediate", "advanced"]
                cohort = cohort_names[user_hash]
            
            cohort_profile = ColdStartOptimizer.COHORT_PROFILES.get(cohort, ColdStartOptimizer.COHORT_PROFILES["beginner"])
            
            # Calculate personalized mastery
            base_mastery = cohort_profile["base_mastery"]
            
            # Adjust based on concept difficulty
            if concept_difficulty > 0.5:  # Hard concepts
                mastery = max(0.1, base_mastery - 0.1)
            elif concept_difficulty < 0.3:  # Easy concepts  
                mastery = min(0.8, base_mastery + 0.1)
            else:  # Medium concepts
                mastery = base_mastery
            
            # Add small random variation for personalization
            variance = cohort_profile["variance"]
            personalization = random.gauss(0, variance)
            mastery = max(0.05, min(0.9, mastery + personalization))
            
            logger.debug(f"Cold start mastery for {user_id}/{concept}: {mastery:.3f} (cohort: {cohort})")
            
            return round(mastery, 3)
            
        except Exception as e:
            logger.error(f"❌ Error calculating cold start mastery: {e}")
            return 0.3  # Safe fallback
    
    @staticmethod
    def get_user_cohort(user_id: str, user_profile: Optional[Dict[str, Any]] = None) -> str:
        """
        Determine user cohort for cold start optimization
        """
        if user_profile and "cohort" in user_profile:
            return user_profile["cohort"]
        
        # Simple heuristic for demo (production: use assessment data, demographics, etc.)
        user_hash = hash(user_id) % 3
        cohort_names = ["beginner", "intermediate", "advanced"]
        return cohort_names[user_hash]
