"""
Response Translator - Converts backend LearningResult to UX-friendly responses
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class ResponseTranslator:
    """Translates raw backend results into user-friendly responses"""
    
    @staticmethod
    def translate_learning_result(result: Dict[str, Any]) -> Dict[str, Any]:
        """Convert LearningResult into UX-friendly response"""
        try:
            mastery = result.get('mastery', 0.0)
            mastery_delta = result.get('mastery_delta', 0.0)
            J_value = result.get('J_value', 0.0)
            transfer_amounts = result.get('transfer_amounts', {})
            
            # Generate human-friendly feedback
            feedback = ResponseTranslator._generate_feedback(mastery, mastery_delta, J_value)
            
            # Calculate progress percentage
            progress_percentage = min(95.0, mastery * 100)  # Cap at 95%
            
            # Determine next recommendation
            next_recommendation = ResponseTranslator._get_next_recommendation(result)
            
            return {
                "correct": result.get('correct', False),
                "feedback": feedback,
                "progress": {
                    "message": ResponseTranslator._mastery_to_message(mastery),
                    "percentage": progress_percentage,
                    "delta": mastery_delta,
                    "level": ResponseTranslator._mastery_to_level(mastery)
                },
                "next_recommendation": next_recommendation,
                "learning_insights": {
                    "transfer_applied": len(transfer_amounts.get('sources', [])) > 0,
                    "transfer_concepts": list(transfer_amounts.get('sources', [])),
                    "efficiency_score": min(1.0, J_value) if J_value else 0.0
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error translating learning result: {e}")
            return ResponseTranslator._fallback_response()
    
    @staticmethod
    def _generate_feedback(mastery: float, mastery_delta: float, J_value: float) -> str:
        """Generate contextual feedback based on learning performance"""
        
        # Correctness-based feedback
        if mastery_delta > 0.05:
            base_feedback = "Excellent! You're really getting this."
        elif mastery_delta > 0.02:
            base_feedback = "Good job! You're making progress."
        elif mastery_delta > 0:
            base_feedback = "Nice work! Keep practicing."
        else:
            base_feedback = "Let's try that again. Learning takes practice."
        
        # Efficiency-based modifier
        if J_value and J_value > 0.7:
            efficiency_note = " You're learning very efficiently!"
        elif J_value and J_value > 0.5:
            efficiency_note = " Your learning pace is solid."
        elif J_value and J_value < 0.3:
            efficiency_note = " Take your time to understand the concepts."
        else:
            efficiency_note = ""
        
        return base_feedback + efficiency_note
    
    @staticmethod
    def _mastery_to_message(mastery: float) -> str:
        """Convert mastery level to encouraging message"""
        if mastery >= 0.8:
            return "You've mastered this concept! Great work!"
        elif mastery >= 0.6:
            return "You're doing well with this concept."
        elif mastery >= 0.4:
            return "You're making good progress."
        elif mastery >= 0.2:
            return "You're starting to get the hang of this."
        else:
            return "You're just getting started. Keep going!"
    
    @staticmethod
    def _mastery_to_level(mastery: float) -> str:
        """Convert mastery to skill level"""
        if mastery >= 0.8:
            return "advanced"
        elif mastery >= 0.6:
            return "intermediate"
        elif mastery >= 0.4:
            return "beginner"
        else:
            return "novice"
    
    @staticmethod
    def _get_next_recommendation(result: Dict[str, Any]) -> str:
        """Get next recommended concept based on bandit/transfer learning"""
        transfer_amounts = result.get('transfer_amounts', {})
        
        # If transfer learning suggests next concepts
        if transfer_amounts.get('sources'):
            sources = transfer_amounts['sources']
            if sources and len(sources) > 0:
                # Return the first transferred concept as recommendation
                return sources[0]
        
        # Fallback to current concept with progression hint
        current_concept = result.get('concept', 'k2_algorithms')
        if 'k2_' in current_concept:
            return current_concept.replace('k2_', 'k5_')
        elif 'k5_' in current_concept:
            return current_concept.replace('k5_', 'k8_')
        else:
            return current_concept
    
    @staticmethod
    def translate_dashboard_data(user_id: str, mastery_data: Dict[str, float], 
                                bandit_state: Dict[str, Any]) -> Dict[str, Any]:
        """Convert raw dashboard data into UX-friendly format"""
        try:
            # Calculate overall progress
            total_concepts = len(mastery_data)
            mastered_concepts = sum(1 for m in mastery_data.values() if m >= 0.8)
            progress_percentage = (mastered_concepts / total_concepts * 100) if total_concepts > 0 else 0
            
            # Determine current level
            avg_mastery = sum(mastery_data.values()) / total_concepts if total_concepts > 0 else 0
            level = ResponseTranslator._mastery_to_level(avg_mastery)
            
            # Get next concept from bandit
            next_concept = "k2_algorithms"  # Default fallback
            if bandit_state and 'recommendations' in bandit_state:
                recommendations = bandit_state['recommendations']
                if recommendations:
                    next_concept = recommendations[0].get('concept', 'k2_algorithms')
            
            return {
                "user_id": user_id,
                "progress": round(progress_percentage, 1),
                "level": level,
                "streak": 5,  # TODO: Calculate from interaction history
                "next_concept": next_concept,
                "message": ResponseTranslator._mastery_to_message(avg_mastery),
                "stats": {
                    "concepts_mastered": mastered_concepts,
                    "total_concepts": total_concepts,
                    "average_mastery": round(avg_mastery, 3)
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error translating dashboard data: {e}")
            return ResponseTranslator._fallback_dashboard(user_id)
    
    @staticmethod
    def _fallback_response() -> Dict[str, Any]:
        """Safe fallback response for translation errors"""
        return {
            "correct": False,
            "feedback": "Great effort! Learning is a journey.",
            "progress": {
                "message": "You're making progress!",
                "percentage": 50.0,
                "delta": 0.0,
                "level": "beginner"
            },
            "next_recommendation": "k2_algorithms",
            "learning_insights": {
                "transfer_applied": False,
                "transfer_concepts": [],
                "efficiency_score": 0.5
            }
        }
    
    @staticmethod
    def _fallback_dashboard(user_id: str) -> Dict[str, Any]:
        """Safe fallback dashboard for translation errors"""
        return {
            "user_id": user_id,
            "progress": 25.0,
            "level": "beginner",
            "streak": 1,
            "next_concept": "k2_algorithms",
            "message": "You're just getting started. Keep going!",
            "stats": {
                "concepts_mastered": 0,
                "total_concepts": 1,
                "average_mastery": 0.3
            }
        }
