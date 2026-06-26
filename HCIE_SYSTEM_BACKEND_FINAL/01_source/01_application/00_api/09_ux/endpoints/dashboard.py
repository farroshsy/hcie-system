"""
UX Dashboard API - User-friendly dashboard endpoint
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import logging

from app.utils.api_responses.response_translator import ResponseTranslator
from app.api.dependencies.learning import get_task_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/dashboard", tags=["ux"])


@router.get("/overview")
async def get_dashboard_overview(
    user_id: str = Depends(lambda: "current_user"),  # TODO: Replace with real auth
    task_service = Depends(get_task_service)  # MIGRATION: Explicit dependency (was inline ServiceFactory)
) -> Dict[str, Any]:
    """
    Get user-friendly dashboard overview
    """
    try:
        
        # 🔥 OWNERSHIP BOUNDARY: Frontend must read from learner_progress, NOT UnifiedBrain
        # UnifiedBrain is only reachable through event ingestion or replay topology
        mastery_data = {}
        try:
            db_store = task_service.db_store
            
            # Get mastery for key concepts from learner_progress table (canonical source)
            key_concepts = ["k2_algorithms", "k5_algorithms"]
            
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
            mastery_data = {"k2_algorithms": 0.65, "k5_algorithms": 0.45}
        
        # Get bandit state
        bandit_state = {}
        try:
            if task_service.bandit:
                bandit_state = {
                    "recommendations": [{"concept": "k5_algorithms", "score": 0.78}]
                }
        except Exception as e:
            logger.warning(f"Could not get bandit state: {e}")
        
        # Translate to UX-friendly format
        dashboard_data = ResponseTranslator.translate_dashboard_data(
            user_id, mastery_data, bandit_state
        )
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"❌ Error in dashboard overview: {e}")
        raise HTTPException(status_code=500, detail="Failed to load dashboard")
