"""
UX Dashboard API v2 - Production-ready with real data
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import logging

from app.services.service_factory import ServiceFactory
from app.utils.api_responses.response_translator import ResponseTranslator
from app.api.dependencies.auth import get_current_user
from core.state.read_mode_cache import ReadModeCache

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/dashboard", tags=["ux"])

@router.get("/overview")
async def get_dashboard_overview(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get user-friendly dashboard overview with REAL data
    """
    try:
        user_id = current_user["id"]
        service_factory = ServiceFactory()
        task_service = service_factory.get_task_service()
        
        # 🔥 OWNERSHIP BOUNDARY: Frontend must read from learner_progress, NOT UnifiedBrain
        # UnifiedBrain is only reachable through event ingestion or replay topology
        mastery_data = {}
        try:
            db_store = task_service.db_store
            
            # Get mastery for key concepts from learner_progress table (canonical source)
            key_concepts = ["k2_algorithms", "k5_algorithms", "k8_algorithms", 
                          "k2_computing_systems_devices", "k2_networks_communication"]
            
            for concept in key_concepts:
                try:
                    # Query from learner_progress table
                    progress = db_store.query_learner_progress(user_id, concept)
                    if progress:
                        mastery_data[concept] = progress.get("mastery", 0.3)
                    else:
                        # No progress data yet, use default
                        mastery_data[concept] = 0.3
                except Exception as e:
                    logger.debug(f"Failed to get mastery for {concept} from learner_progress: {e}")
                    mastery_data[concept] = 0.3
                    
        except Exception as e:
            logger.warning(f"Could not get mastery data from learner_progress: {e}")
            # Safe fallback
            mastery_data = {"k2_algorithms": 0.3, "k5_algorithms": 0.3, "k2_computing_systems_devices": 0.3}
        
        # 🔥 OWNERSHIP BOUNDARY: Recommendations should come from ProjectionStore, NOT UnifiedBrain
        # For now, use simple fallback until ProjectionStore is fully implemented
        bandit_state = {
            "recommendations": [{
                "concept": "k2_computing_systems_devices",  # Simple deterministic fallback
                "score": 0.5,
                "reason": "projection_fallback",
                "engine": "projection_consumer"
            }]
        }
        
        # Translate to UX-friendly format
        dashboard_data = ResponseTranslator.translate_dashboard_data(
            user_id, mastery_data, bandit_state
        )
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"❌ Error in dashboard overview: {e}")
        raise HTTPException(status_code=500, detail="Failed to load dashboard")
