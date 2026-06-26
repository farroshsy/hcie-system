"""
State Compatibility Layer - Schema Evolution & Migration
Handles backward compatibility between state versions
"""

import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class StateCompatibility:
    """
    Ensures state schema compatibility across versions
    Handles migration from V1 to V2 format
    """
    
    @staticmethod
    def ensure_compatibility(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure state has all required fields for V2 engine
        Migrates V1 format to V2 format
        """
        if not state:
            return StateCompatibility._get_default_v2_state()
        
        # Ensure top-level structure
        if "meta" not in state:
            state["meta"] = {}
        if "mastery" not in state:
            state["mastery"] = {}
        if "bandit" not in state:
            state["bandit"] = {}
        if "transfer" not in state:
            state["transfer"] = {}
        
        # Migrate mastery structure
        state = StateCompatibility._migrate_mastery(state)
        
        # Migrate bandit structure  
        state = StateCompatibility._migrate_bandit(state)
        
        # Migrate transfer structure
        state = StateCompatibility._migrate_transfer(state)
        
        # Migrate meta structure
        state = StateCompatibility._migrate_meta(state)
        
        # Log migration if needed
        if state["meta"].get("version", 1) < 2:
            logger.info(f"🔄 Migrated state from V{state['meta'].get('version', 1)} to V2")
            state["meta"]["version"] = 2
            state["meta"]["migration_timestamp"] = json.dumps({"migrated": True})
        
        return state
    
    @staticmethod
    def _migrate_mastery(state: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate mastery structure to V2 format"""
        mastery = state["mastery"]
        
        # Ensure concepts dictionary exists
        if "concepts" not in mastery:
            mastery["concepts"] = {}
        
        # If only global mastery exists, migrate it to concepts
        if "global" in mastery and not mastery["concepts"]:
            global_mastery = mastery["global"]
            mastery["concepts"]["global"] = global_mastery
            logger.info(f"📊 Migrated global mastery {global_mastery} to concepts")
        
        # Ensure global mastery exists
        if "global" not in mastery:
            mastery["global"] = 0.5
        
        return state
    
    @staticmethod
    def _migrate_bandit(state: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate bandit structure to V2 format"""
        bandit = state["bandit"]
        
        # Ensure basic bandit structure
        if "counts" not in bandit:
            bandit["counts"] = {"easy": 0, "hard": 0}
        if "values" not in bandit:
            bandit["values"] = {"easy": 0.5, "hard": 0.5}
        
        # Ensure concept-aware bandit structure
        if "concept_counts" not in bandit:
            bandit["concept_counts"] = {}
        if "concept_values" not in bandit:
            bandit["concept_values"] = {}
        if "exploration_history" not in bandit:
            bandit["exploration_history"] = []
        
        # Migrate old format if needed
        if "prior_type" not in bandit:
            bandit["prior_type"] = "uniform"
        
        return state
    
    @staticmethod
    def _migrate_transfer(state: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate transfer structure to V2 format"""
        transfer = state["transfer"]
        
        # Ensure basic transfer structure
        if "applied" not in transfer:
            transfer["applied"] = False
        if "bonus" not in transfer:
            transfer["bonus"] = 0.0
        if "last_concept" not in transfer:
            transfer["last_concept"] = None
        
        # Ensure history fields exist
        if "transfer_history" not in transfer:
            # Try to migrate from bonus_history
            if "bonus_history" in transfer and transfer["bonus_history"]:
                transfer["transfer_history"] = transfer["bonus_history"].copy()
                logger.info(f"🔄 Migrated {len(transfer['bonus_history'])} bonus records to transfer_history")
            else:
                transfer["transfer_history"] = []
        
        if "bonus_history" not in transfer:
            # Try to migrate from transfer_history
            if "transfer_history" in transfer and transfer["transfer_history"]:
                transfer["bonus_history"] = transfer["transfer_history"].copy()
                logger.info(f"🔄 Migrated {len(transfer['transfer_history'])} transfer records to bonus_history")
            else:
                transfer["bonus_history"] = []
        
        # Ensure applied concepts tracking
        if "applied_concepts" not in transfer:
            transfer["applied_concepts"] = []
        
        return state
    
    @staticmethod
    def _migrate_meta(state: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate meta structure to V2 format"""
        meta = state["meta"]
        
        # Ensure version tracking
        if "version" not in meta:
            meta["version"] = 1  # Will be updated to 2 in main function
        
        # Ensure basic fields
        if "cold_start" not in meta:
            meta["cold_start"] = True
        if "initialization" not in meta:
            meta["initialization"] = "migrated"
        if "last_event" not in meta:
            meta["last_event"] = None
        if "last_concept" not in meta:
            meta["last_concept"] = None
        
        return state
    
    @staticmethod
    def _get_default_v2_state() -> Dict[str, Any]:
        """Get default V2 state structure"""
        return {
            "meta": {
                "version": 2,
                "cold_start": True,
                "initialization": "default",
                "last_event": None,
                "last_concept": None
            },
            "mastery": {
                "global": 0.5,
                "concepts": {}
            },
            "bandit": {
                "counts": {"easy": 0, "hard": 0},
                "values": {"easy": 0.5, "hard": 0.5},
                "concept_counts": {},
                "concept_values": {},
                "exploration_history": [],
                "prior_type": "uniform"
            },
            "transfer": {
                "applied": False,
                "bonus": 0.0,
                "last_concept": None,
                "transfer_history": [],
                "bonus_history": [],
                "applied_concepts": []
            }
        }
    
    @staticmethod
    def validate_state_structure(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate state structure and return validation results
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
        required_bandit_keys = ["counts", "values", "concept_counts", "concept_values"]
        for key in required_bandit_keys:
            if key not in bandit:
                errors.append(f"Missing bandit key: {key}")
        
        # Check transfer structure
        transfer = state.get("transfer", {})
        required_transfer_keys = ["applied", "bonus", "transfer_history", "bonus_history"]
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
            "version": state.get("meta", {}).get("version", "unknown")
        }

# Factory function for easy usage
def create_state_compatibility():
    """Create state compatibility manager"""
    return StateCompatibility()
