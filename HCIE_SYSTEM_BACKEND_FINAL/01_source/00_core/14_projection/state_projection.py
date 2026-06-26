"""
State Projection Layer - Clean API Boundary
Transforms rich internal state to simple external API responses
"""

import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class StateProjection:
    """
    Projects rich internal learning state to clean API responses
    Maintains internal complexity while exposing external simplicity
    """
    
    @staticmethod
    def to_api_response(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert internal state to API response
        Hides internal complexity, exposes only what client needs
        """
        if not state:
            return {"mastery": 0.5, "concepts_tracked": 0}
        
        mastery_data = state.get("mastery", {})
        
        # Extract only what API should expose
        response = {
            "mastery": mastery_data.get("global", 0.5),
            "concepts_tracked": len(mastery_data.get("concepts", {})),
            "last_updated": state.get("meta", {}).get("last_event")
        }
        
        # Optional: Add confidence indicator
        concepts = mastery_data.get("concepts", {})
        if concepts:
            # Simple confidence based on number of concepts and consistency
            avg_concept_mastery = sum(concepts.values()) / len(concepts)
            variance = sum((x - avg_concept_mastery) ** 2 for x in concepts.values()) / len(concepts)
            confidence = max(0.0, min(1.0, 1.0 - variance))  # Lower variance = higher confidence
            response["confidence"] = round(confidence, 3)
        else:
            response["confidence"] = 0.5  # Default confidence
        
        return response
    
    @staticmethod
    def to_debug_response(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert internal state to debug response
        Exposes internal structure for debugging/monitoring
        """
        if not state:
            return {"error": "No state found"}
        
        return {
            "full_state": state,
            "state_summary": {
                "version": state.get("meta", {}).get("version", "unknown"),
                "concepts_count": len(state.get("mastery", {}).get("concepts", {})),
                "global_mastery": state.get("mastery", {}).get("global", 0.0),
                "transfer_active": state.get("transfer", {}).get("applied", False),
                "bandit_concepts": len(state.get("bandit", {}).get("concept_counts", {}))
            }
        }
    
    @staticmethod
    def to_learning_analytics(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert internal state to learning analytics
        Provides insights about learning progress
        """
        if not state:
            return {"error": "No state found"}
        
        mastery = state.get("mastery", {})
        concepts = mastery.get("concepts", {})
        bandit = state.get("bandit", {})
        transfer = state.get("transfer", {})
        
        # Concept mastery analysis
        concept_analysis = {}
        if concepts:
            mastery_values = list(concepts.values())
            concept_analysis = {
                "total_concepts": len(concepts),
                "average_mastery": sum(mastery_values) / len(mastery_values),
                "highest_mastery": max(mastery_values),
                "lowest_mastery": min(mastery_values),
                "mastered_concepts": len([x for x in mastery_values if x >= 0.8]),
                "struggling_concepts": len([x for x in mastery_values if x < 0.3])
            }
        
        # Transfer learning analysis
        transfer_analysis = {
            "transfer_applied": transfer.get("applied", False),
            "total_transfer_bonus": transfer.get("bonus", 0.0),
            "transfer_history_size": len(transfer.get("transfer_history", [])),
            "last_transfer_concept": transfer.get("last_concept")
        }
        
        # Bandit analysis
        bandit_analysis = {
            "total_interactions": sum(bandit.get("counts", {}).values()),
            "concept_interactions": sum(bandit.get("concept_counts", {}).values()),
            "unique_concepts_seen": len(bandit.get("concept_counts", {})),
            "exploration_history_size": len(bandit.get("exploration_history", []))
        }
        
        return {
            "user_id": state.get("meta", {}).get("user_id", "unknown"),
            "global_mastery": mastery.get("global", 0.0),
            "concept_analysis": concept_analysis,
            "transfer_analysis": transfer_analysis,
            "bandit_analysis": bandit_analysis,
            "learning_velocity": StateProjection._calculate_learning_velocity(state),
            "recommendations": StateProjection._generate_recommendations(state)
        }
    
    @staticmethod
    def _calculate_learning_velocity(state: Dict[str, Any]) -> float:
        """Calculate learning velocity based on recent progress"""
        transfer_history = state.get("transfer", {}).get("transfer_history", [])
        
        if len(transfer_history) < 2:
            return 0.0
        
        # Get last 10 transfer events
        recent_events = transfer_history[-10:]
        if len(recent_events) < 2:
            return 0.0
        
        # Calculate velocity based on transfer bonuses
        total_bonus = sum(event.get("bonus", 0.0) for event in recent_events)
        time_span = recent_events[-1].get("timestamp", 0) - recent_events[0].get("timestamp", 0)
        
        if time_span <= 0:
            return 0.0
        
        return total_bonus / time_span
    
    @staticmethod
    def _generate_recommendations(state: Dict[str, Any]) -> List[str]:
        """Generate learning recommendations based on state"""
        recommendations = []
        
        concepts = state.get("mastery", {}).get("concepts", {})
        transfer = state.get("transfer", {})
        bandit = state.get("bandit", {})
        
        # Concept-based recommendations
        if concepts:
            low_mastery_concepts = [c for c, m in concepts.items() if m < 0.3]
            if low_mastery_concepts:
                recommendations.append(f"Focus on: {', '.join(low_mastery_concepts[:2])}")
            
            high_mastery_concepts = [c for c, m in concepts.items() if m >= 0.8]
            if high_mastery_concepts:
                recommendations.append(f"Advanced topics ready: {', '.join(high_mastery_concepts[:2])}")
        
        # Transfer-based recommendations
        if not transfer.get("applied", False):
            recommendations.append("Build foundational concepts for transfer learning")
        
        # Bandit-based recommendations
        concept_counts = bandit.get("concept_counts", {})
        if concept_counts:
            most_practiced = max(concept_counts.items(), key=lambda x: x[1])[0]
            recommendations.append(f"Most practiced: {most_practiced}")
        
        return recommendations[:3]  # Top 3 recommendations
    
    @staticmethod
    def validate_state_structure(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate state structure for correctness
        Returns validation results
        """
        errors = []
        warnings = []
        
        # Check required top-level keys
        required_keys = ["meta", "mastery", "bandit", "transfer"]
        for key in required_keys:
            if key not in state:
                errors.append(f"Missing required key: {key}")
        
        # Check mastery structure
        mastery = state.get("mastery", {})
        if "global" not in mastery:
            errors.append("Missing global mastery")
        if "concepts" not in mastery:
            warnings.append("Missing concepts structure")
        elif not isinstance(mastery["concepts"], dict):
            errors.append("Concepts must be a dictionary")
        
        # Check bandit structure
        bandit = state.get("bandit", {})
        required_bandit_keys = ["counts", "values"]
        for key in required_bandit_keys:
            if key not in bandit:
                errors.append(f"Missing bandit key: {key}")
        
        # Check transfer structure
        transfer = state.get("transfer", {})
        required_transfer_keys = ["applied", "bonus"]
        for key in required_transfer_keys:
            if key not in transfer:
                errors.append(f"Missing transfer key: {key}")
        
        # Validate data types
        if mastery.get("global", 0) < 0 or mastery.get("global", 0) > 1:
            errors.append("Global mastery must be between 0 and 1")
        
        concepts = mastery.get("concepts", {})
        for concept, value in concepts.items():
            if not isinstance(value, (int, float)) or value < 0 or value > 1:
                errors.append(f"Concept {concept} mastery must be between 0 and 1")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "state_version": state.get("meta", {}).get("version", "unknown")
        }

# Usage examples
def example_usage():
    """Example of how to use state projection"""
    
    # Rich internal state
    internal_state = {
        "meta": {"version": 2, "last_event": "abc123"},
        "mastery": {
            "global": 0.82,
            "concepts": {
                "ct_algorithm": 0.9,
                "ct_abstraction": 0.6
            }
        },
        "bandit": {
            "counts": {"easy": 5, "hard": 3},
            "concept_counts": {"ct_algorithm": 4, "ct_abstraction": 2}
        },
        "transfer": {
            "applied": True,
            "bonus": 0.1,
            "transfer_history": [...]
        }
    }
    
    # API response (simple)
    api_response = StateProjection.to_api_response(internal_state)
    # Returns: {"mastery": 0.82, "concepts_tracked": 2, "confidence": 0.85}
    
    # Debug response (detailed)
    debug_response = StateProjection.to_debug_response(internal_state)
    # Returns full internal state for debugging
    
    # Analytics response (insights)
    analytics_response = StateProjection.to_learning_analytics(internal_state)
    # Returns learning analytics and recommendations
