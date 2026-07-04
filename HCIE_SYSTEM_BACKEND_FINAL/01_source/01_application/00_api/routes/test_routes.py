"""
Test Routes - For B4.1 Frontend Validation

These routes are for testing the frontend WebSocket connection without requiring
the full backend event flow (CognitionUpdated → AdaptationGenerated → ProjectionUpdated).
"""

from fastapi import APIRouter
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/test", tags=["test"])

@router.post("/simulate-projection")
async def simulate_projection_updated():
    """
    Simulate a ProjectionUpdated event for frontend testing
    
    This endpoint broadcasts a test ProjectionUpdated event via WebSocket
    to validate the frontend can receive and render projections correctly.
    """
    try:
        from app.api.websocket.projection_websocket import projection_manager
        
        # Create a test ProjectionUpdated event
        test_event = {
            "event_id": f"test_projection_{int(datetime.utcnow().timestamp())}",
            "event_type": "ProjectionUpdated",
            "user_id": "user_001",
            "concept": "k2_algorithms",
            "timestamp": datetime.utcnow().isoformat(),
            "source": "test_endpoint",
            "result": {
                "mastery": 0.75,
                "uncertainty": 0.1,
                "zpd_score": 0.8,
                "processing_mode": "jt",
                "lyapunov_mastery": 0.73,
                "bayesian_alpha": 5.0,
                "bayesian_beta": 2.0,
                "kalman_mastery": 0.74,
                "kalman_covariance": 0.05
            },
            "projection": {
                "projected_mastery": 75.0,
                "projected_difficulty": 0.8,
                "recommended_concepts": ["k5_algorithms", "k8_algorithms"],
                "zpd_alignment": 0.8,
                "concept_id": "k2_algorithms",
                "concept_name": "k2_algorithms",
                "uncertainty": 0.1
            },
            "adaptation": {
                "adaptation_type": "difficulty_shift",
                "recommendation": {
                    "target_difficulty": 0.8,
                    "reason": "High mastery detected, increasing difficulty"
                },
                "policy_version": "v1.0.0",
                "deterministic_inputs_hash": "test_hash_123"
            },
            "causation_id": "test_cognition_001",
            "correlation_id": "test_trace_001",
            "trace_id": "test_trace_001"
        }
        
        # Broadcast to user_001 (default test user)
        await projection_manager.broadcast_projection_update("user_001", test_event)
        
        logger.info(f"🧪 Simulated ProjectionUpdated event: {test_event['event_id']}")
        
        return {
            "success": True,
            "message": "Simulated ProjectionUpdated event broadcast via WebSocket",
            "event_id": test_event["event_id"],
            "user_id": "user_001"
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to simulate projection: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to simulate ProjectionUpdated event"
        }

@router.post("/simulate-runtime-timeline")
async def simulate_runtime_timeline():
    """
    Simulate a complete runtime event sequence for timeline visualization
    
    This endpoint broadcasts a sequence of events (TaskAttemptSubmitted → CognitionUpdated 
    → AdaptationGenerated → ProjectionUpdated) to validate the frontend timeline visualization.
    
    Sequence:
    1. TaskAttemptSubmitted (blue) - User submits answer
    2. CognitionUpdated (green) - Runtime updates cognition
    3. AdaptationGenerated (purple) - Adaptation engine generates pedagogical transition
    4. ProjectionUpdated (orange) - Projection materialized and streamed
    """
    try:
        from app.api.websocket.projection_websocket import projection_manager
        
        base_timestamp = datetime.utcnow().isoformat()
        base_event_id = f"test_timeline_{int(datetime.utcnow().timestamp())}"
        trace_id = f"trace_{base_event_id}"
        causation_id = f"causation_{base_event_id}"
        
        # Event 1: TaskAttemptSubmitted
        task_event = {
            "event_id": f"{base_event_id}_1",
            "event_type": "TaskAttemptSubmitted",
            "user_id": "user_001",
            "task_id": "task_001",
            "concept": "k2_algorithms",
            "timestamp": base_timestamp,
            "trace_id": trace_id,
            "causation_id": causation_id,
            "correlation_id": trace_id,
            "data": {
                "answer": "binary_search",
                "is_correct": True,
                "response_time_ms": 1250
            }
        }
        
        # Event 2: CognitionUpdated (100ms after TaskAttemptSubmitted)
        import time
        time.sleep(0.1)
        cognition_timestamp = datetime.utcnow().isoformat()
        cognition_event = {
            "event_id": f"{base_event_id}_2",
            "event_type": "CognitionUpdated",
            "user_id": "user_001",
            "concept": "k2_algorithms",
            "timestamp": cognition_timestamp,
            "trace_id": trace_id,
            "causation_id": task_event["event_id"],
            "correlation_id": trace_id,
            "data": {
                "mastery": 0.78,
                "uncertainty": 0.09,
                "zpd_score": 0.82,
                "bayesian_alpha": 5.5,
                "bayesian_beta": 1.8,
                "kalman_mastery": 0.77,
                "kalman_covariance": 0.04
            }
        }
        
        # Event 3: AdaptationGenerated (50ms after CognitionUpdated)
        time.sleep(0.05)
        adaptation_timestamp = datetime.utcnow().isoformat()
        adaptation_event = {
            "event_id": f"{base_event_id}_3",
            "event_type": "AdaptationGenerated",
            "user_id": "user_001",
            "concept": "k2_algorithms",
            "timestamp": adaptation_timestamp,
            "trace_id": trace_id,
            "causation_id": cognition_event["event_id"],
            "correlation_id": trace_id,
            "data": {
                "adaptation_type": "difficulty_shift",
                "recommendation": {
                    "target_difficulty": 0.85,
                    "reason": "High mastery detected, increasing difficulty"
                },
                "policy_version": "v1.0.0",
                "deterministic_inputs_hash": "test_hash_456"
            }
        }
        
        # Event 4: ProjectionUpdated (30ms after AdaptationGenerated)
        time.sleep(0.03)
        projection_timestamp = datetime.utcnow().isoformat()
        projection_event = {
            "event_id": f"{base_event_id}_4",
            "event_type": "ProjectionUpdated",
            "user_id": "user_001",
            "concept": "k2_algorithms",
            "timestamp": projection_timestamp,
            "trace_id": trace_id,
            "causation_id": adaptation_event["event_id"],
            "correlation_id": trace_id,
            "result": {
                "mastery": 0.78,
                "uncertainty": 0.09,
                "zpd_score": 0.82,
                "processing_mode": "jt",
                "lyapunov_mastery": 0.76,
                "bayesian_alpha": 5.5,
                "bayesian_beta": 1.8,
                "kalman_mastery": 0.77,
                "kalman_covariance": 0.04
            },
            "projection": {
                "projected_mastery": 78.0,
                "projected_difficulty": 0.85,
                "recommended_concepts": ["k5_algorithms", "k8_algorithms"],
                "zpd_alignment": 0.82,
                "concept_id": "k2_algorithms",
                "concept_name": "k2_algorithms",
                "uncertainty": 0.09
            },
            "adaptation": {
                "adaptation_type": "difficulty_shift",
                "recommendation": {
                    "target_difficulty": 0.85,
                    "reason": "High mastery detected, increasing difficulty"
                },
                "policy_version": "v1.0.0",
                "deterministic_inputs_hash": "test_hash_456"
            }
        }
        
        # Broadcast all events in sequence
        await projection_manager.broadcast_projection_update("user_001", task_event)
        await projection_manager.broadcast_projection_update("user_001", cognition_event)
        await projection_manager.broadcast_projection_update("user_001", adaptation_event)
        await projection_manager.broadcast_projection_update("user_001", projection_event)
        
        logger.info(f"🧪 Simulated runtime timeline sequence: {base_event_id}")
        
        return {
            "success": True,
            "message": "Simulated complete runtime timeline sequence via WebSocket",
            "sequence_id": base_event_id,
            "events": [
                task_event["event_type"],
                cognition_event["event_type"],
                adaptation_event["event_type"],
                projection_event["event_type"]
            ],
            "user_id": "user_001"
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to simulate runtime timeline: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to simulate runtime timeline sequence"
        }
