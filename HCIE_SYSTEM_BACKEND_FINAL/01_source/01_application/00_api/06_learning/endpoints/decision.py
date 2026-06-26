"""
Decision API - Real-time Learning Policy Decisions
Provides next best action recommendations using bandit policy
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
import logging
import json
import uuid
from datetime import datetime
from contextlib import contextmanager

from storage.postgres_store.interaction_store import PostgresInteractionStore
# Phase 14c quarantined `learning_loop_engine_v2`; this router still references
# the class for type hints. Provide a typed no-op stub if the real symbol is gone
# so the rest of `app.main` can boot. Endpoints that actually USE the engine
# will fail with 503 at call time (which is correct — there is no V2 engine).
try:
    from core.learning.learning_loop_engine_v2 import LearningLoopEngineV2 as LearningLoopEngine
except ImportError:
    class LearningLoopEngine:  # type: ignore[no-redef]
        """Stub for the Phase 14c-quarantined V2 engine. Any instance use raises."""

        def __init__(self, *args, **kwargs):
            raise RuntimeError(
                "LearningLoopEngineV2 was quarantined in Phase 14c. "
                "Use the FINAL /v3/its/* spine via UnifiedBrainRuntimeService."
            )
from core.learning.state_compatibility import StateCompatibility
from core.learning.state_projection import StateProjection
from core.bandit.bandit import ContextualBandit
from core.bandit.transfer_aware_bandit import TransferAwareBandit
from app.api.dependencies.learning import get_task_service, get_learning_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/decision", tags=["decision"])


@contextmanager
def get_db_connection(db_store: PostgresInteractionStore):
    """Context manager for safe connection handling."""
    conn = None
    try:
        conn = db_store._get_connection()
        yield conn
    finally:
        if conn is not None:
            conn.close()


def get_db_store():
    """Dependency injection for database store - FAST PATH"""
    return PostgresInteractionStore()


@router.get("/next-action/{user_id}", response_model=Dict[str, Any])
async def get_next_action(
    user_id: str,
    concept: Optional[str] = None,
    difficulty_preference: Optional[float] = None,
    db_store: PostgresInteractionStore = Depends(get_db_store),
    task_service = Depends(get_task_service)  # 🔥 RUNTIME CONVERGENCE: Primary path uses UnifiedBrain via TaskService
) -> Dict[str, Any]:
    """
    Get next recommended action for user using bandit policy
    """
    logger.info(f"🔍 get_next_action called for user: {user_id}")
    
    try:
        # � RUNTIME CONVERGENCE: Use UnifiedBrain for state inference via TaskService
        # TaskService internally uses UnifiedBrain for governance
        inferred_state = task_service.get_user_state(user_id) if hasattr(task_service, 'get_user_state') else {}
        learner_insights = inferred_state.get("learner_inference", {})
        ensemble_mastery = learner_insights.get("ensemble_mastery", {})
        ensemble_uncertainty = learner_insights.get("ensemble_uncertainty", {})
        
        logger.info(f"🧠 LEARNER-INFORMED DECISION: user={user_id} concept={concept}")
        logger.info(f"  ensemble_mastery: {ensemble_mastery}")
        logger.info(f"  ensemble_uncertainty: {ensemble_uncertainty}")
        
        # Use context manager for safe connection handling
        with get_db_connection(db_store) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT mastery FROM user_state 
                WHERE user_id = %s
            """, (user_id,))
            
            result = cursor.fetchone()
            cursor.close()
            
            if not result:
                # Cold start - initialize with learner-informed priors
                state = inferred_state
                logger.info(f"❄️ Cold start with learner inference for user {user_id}")
                
                cursor = conn.cursor()
                state_json = json.dumps(state)
                cursor.execute("""
                    INSERT INTO user_state (user_id, mastery)
                    VALUES (%s, %s)
                """, (user_id, state_json))
                conn.commit()  # ✅ Proper commit
                cursor.close()
            else:
                mastery_data = result[0]
                state = json.loads(mastery_data) if isinstance(mastery_data, str) else mastery_data
                logger.info(f"🧠 Loaded existing state for user {user_id}")
            
            # Decision event
            decision_event = {
                "event_id": str(uuid.uuid4()),
                "user_id": user_id,
                "event_type": "task_requested",
                "concept": concept or "global",
                "difficulty_preference": difficulty_preference,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            try:
                # 🔥 TASK SERVICE FIRST: Use TaskService directly as primary service
                logger.info("🔥 USING TASK SERVICE AS PRIMARY SERVICE")
                
                # Generate task using TaskService with K-12 concepts
                task_result = task_service.generate_task(
                    user_id=user_id,
                    concept_filter=[concept] if concept else None  # Pass K-12 concepts as list
                )
                
                # Extract task details
                selected_task = task_result.get("task_id", "basic_task")
                concept_mastery = task_result.get("mastery", 0.5)
                learner_inference = task_result.get("learner_inference", {})
                used_learner_priors = learner_inference.get("used_learner_priors", False)
                
                logger.info(" SHADOW MODE DECISION SUCCESS")
                logger.info(f"  task: {selected_task}")
                logger.info(f"  mastery: {concept_mastery}")
                
                if selected_task:
                    next_task = selected_task
                    logger.info(f" TASK SERVICE TASK SELECTED: {next_task}")
                    logger.info(f"  mastery: {concept_mastery}")
                    
                    # 🔥 INTEGRATION: Return complete learning-aware response
                    response = {
                        "user_id": user_id,
                        "recommended_task": next_task,
                        "concept": task_result.get("concept_id", concept),  # Use actual concept from task
                        "mastery": concept_mastery,
                        "confidence": task_result.get("confidence", 0.5),
                        "reasoning": {
                            "strategy": "task_service_primary",
                            "learner_informed": used_learner_priors,
                            "ensemble_mastery": learner_inference.get("ensemble_mastery", {}),
                            "transfer_potential": learner_inference.get("transfer_potential", {})
                        },
                        "bandit_integration": True,
                        "decision_source": "task_service",
                        "metadata": {
                            "timestamp": datetime.utcnow().isoformat(),
                            "concept": task_result.get("concept_id", concept),
                            "cold_start": not task_result,
                            "learner_inference": learner_inference
                        },
                        
                        # 🔥 INTEGRATION: Include learning state information
                        "learning_state": {
                            "mastery": concept_mastery,
                            "confidence": task_result.get("confidence", 0.5),
                            "uncertainty": 1.0 - task_result.get("confidence", 0.5),
                            "policy_mode": task_result.get("policy_mode", "hcie"),
                            "transfer_potential": learner_inference.get("transfer_potential", {})
                        }
                    }
                    
                    # Add learning_result if available from TaskService
                    if "learning_result" in task_result:
                        response["learning_result"] = task_result["learning_result"]
                    
                    return response
                else:
                    # 🔥 RUNTIME CONVERGENCE: No legacy fallback - TaskService is canonical
                    # If TaskService fails, surface the error rather than bypassing with legacy engine
                    logger.error("❌ TaskService task generation failed: no task returned")
                    raise HTTPException(status_code=500, detail="Task generation failed - canonical governance path unavailable")
                        
            except Exception as e:
                logger.error(f"❌ Error in unified decision process: {e}")
                raise HTTPException(status_code=500, detail=f"Decision generation failed: {str(e)}")
            # conn automatically closed by context manager
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error in get_next_action: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/feedback")
async def submit_feedback(
    feedback: Dict[str, Any],
    db_store: PostgresInteractionStore = Depends(get_db_store)
) -> Dict[str, Any]:
    """
    Submit user feedback on recommended action (PRODUCTION SCHEMA v1.1)
    """
    # 🔥 ENHANCED: Use comprehensive production schema v1.1
    try:
        from core.schema.production_schema import create_production_event, validate_production_schema
        
        # Extract interaction data with validation
        outcome = feedback["outcome"]
        if not isinstance(outcome, dict):
            raise ValueError("outcome must be a dictionary")
        
        # Auto-calculate reward from correctness if not provided
        reward = outcome.get("reward")
        if reward is None and "correct" in outcome:
            reward = 1.0 if outcome["correct"] else 0.0
        
        # Create production event using factory function
        production_event = create_production_event(
            event_type="decision_feedback",
            user_id=feedback["user_id"],
            concept=feedback["action_taken"],
            interaction=outcome,
            task_id=feedback.get("task_id"),
            reward=reward,
            session_id=feedback.get("session_id"),
            difficulty=outcome.get("difficulty"),
            source_service="feedback-api"
        )
        
        # Validate the complete event
        validated_data = validate_production_schema(production_event.to_dict())
        
        # Check for validation errors
        if "_validation_error" in validated_data:
            raise HTTPException(
                status_code=400, 
                detail={
                    "error": "Schema validation failed",
                    "validation_error": validated_data["_validation_error"],
                    "details": validated_data
                }
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400, 
            detail=f"Production schema validation failed: {str(e)}"
        )
    
    with get_db_connection(db_store) as conn:
        cursor = conn.cursor()
        
        try:
            event_id = feedback.get("event_id", str(uuid.uuid4()))
            
            # 🔥 FIXED: Use production schema for Kafka
            feedback_event = validated_data  # Already has all required fields
            
            cursor.execute("""
                INSERT INTO outbox_event_envelopes 
                (event_id, event_type, topic, version, timestamp, envelope, correlation_id, causation_id, source_service, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                feedback_event["event_id"],
                feedback_event["event_type"],
                "user-interactions",
                1,
                feedback_event["timestamp"],
                json.dumps({
                    "topic": "user-interactions",
                    "payload": feedback_event,
                    "version": 1,
                    "event_id": feedback_event["event_id"],
                    "metadata": {
                        "source_service": "feedback-api",
                        "partition_key": feedback_event["user_id"]
                    },
                    "timestamp": feedback_event["timestamp"],
                    "event_type": feedback_event["event_type"]
                }),
                None,
                None,
                "feedback-api",
                "pending",
                datetime.utcnow()
            ))
            
            conn.commit()  # ✅ Proper commit
            cursor.close()
            
            logger.info(f"✅ Feedback queued for user {feedback['user_id']}: {feedback_event['event_id']}")
            
            return {
                "status": "queued",
                "event_id": feedback_event["event_id"],
                "message": "Feedback queued for async processing",
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "topic": "user-interactions"
                }
            }
            
        except Exception as e:
            conn.rollback()  # ✅ Proper rollback
            cursor.close()
            logger.error(f"❌ Failed to queue feedback: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to queue feedback: {str(e)}")
        # conn automatically closed by context manager


@router.get("/policy-state/{user_id}")
async def get_policy_state(
    user_id: str,
    db_store: PostgresInteractionStore = Depends(get_db_store)
) -> Dict[str, Any]:
    """
    Get current bandit policy state for user
    """
    with get_db_connection(db_store) as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT mastery FROM user_state 
            WHERE user_id = %s
        """, (user_id,))
        
        result = cursor.fetchone()
        cursor.close()
        
        if not result:
            raise HTTPException(status_code=404, detail="User not found")
        
        mastery_data = result[0]
        state = json.loads(mastery_data) if isinstance(mastery_data, str) else mastery_data
        bandit_state = state.get("bandit", {})
        counts = bandit_state.get("counts", {})
        total_actions = sum(counts.values()) if counts else 0
        
        return {
            "user_id": user_id,
            "bandit_state": bandit_state,
            "mastery_state": state.get("mastery", {}),
            "policy_metrics": {
                "total_actions": total_actions,
                "exploration_rate": 0.2,
                "action_distribution": {
                    action: count / total_actions
                    for action, count in counts.items()
                } if total_actions > 0 else {}
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    # conn automatically closed by context manager


@router.post("/initialize/{user_id}")
async def initialize_user(
    user_id: str,
    prior_knowledge: Optional[Dict[str, float]] = None,
    cohort: Optional[str] = None,
    db_store: PostgresInteractionStore = Depends(get_db_store),
    task_service = Depends(get_task_service)  # 🔥 RUNTIME CONVERGENCE: Use canonical TaskService
) -> Dict[str, Any]:
    """
    Initialize user with Bayesian priors or cohort-based warm start
    """
    with get_db_connection(db_store) as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 1 FROM user_state 
            WHERE user_id = %s
        """, (user_id,))
        
        if cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=409, detail="User already initialized")
        
        # 🔥 RUNTIME CONVERGENCE: Use TaskService for initialization (uses UnifiedBrain governance)
        # Fallback to default if TaskService doesn't have initialization method
        if hasattr(task_service, 'initialize_user'):
            initial_state = task_service.initialize_user(user_id, prior_knowledge)
        else:
            # Legacy fallback
            initial_state = {"mastery": prior_knowledge if prior_knowledge else {}, "bandit": {}}
        
        if prior_knowledge:
            mastery = initial_state.get("mastery", {})
            mastery.update(prior_knowledge)
            initial_state["mastery"] = mastery
        
        if cohort:
            logger.info(f"👥 Initializing user {user_id} from cohort {cohort}")
        
        state_json = json.dumps(initial_state)
        cursor.execute("""
            INSERT INTO user_state (user_id, mastery)
            VALUES (%s, %s)
        """, (user_id, state_json))
        
        conn.commit()  # ✅ Proper commit
        cursor.close()
        
        logger.info(f"🎯 User {user_id} initialized successfully")
        
        return {
            "user_id": user_id,
            "status": "initialized",
            "initial_mastery": initial_state.get("mastery", {}),
            "initial_bandit": initial_state.get("bandit", {}),
            "initialization_method": "bayesian_priors" if prior_knowledge else "default",
            "cohort": cohort,
            "timestamp": datetime.utcnow().isoformat()
        }
    # conn automatically closed by context manager


@router.get("/transfer-aware/{user_id}", response_model=Dict[str, Any])
async def get_transfer_aware_recommendation(
    user_id: str,
    db_store: PostgresInteractionStore = Depends(get_db_store),
    task_service = Depends(get_task_service)  # 🔥 RUNTIME CONVERGENCE: Use canonical TaskService
) -> Dict[str, Any]:
    """
    Get transfer-aware recommendation for next concept to learn
    
    Combines multi-armed bandit with DAG transfer learning to provide
    intelligent recommendations that consider transfer opportunities.
    """
    logger.info(f"🔥 Transfer-aware recommendation requested for user: {user_id}")
    
    try:
        # 🔥 RUNTIME CONVERGENCE: Use UnifiedBrain's bandit instead of direct creation
        # Initialize transfer-aware bandit with canonical bandit from UnifiedBrain
        if hasattr(task_service, 'unified_brain') and hasattr(task_service.unified_brain, 'bandit'):
            bandit = task_service.unified_brain.bandit
        else:
            # Fallback to direct creation if UnifiedBrain unavailable
            logger.warning("UnifiedBrain bandit not available, using fallback")
            bandit = ContextualBandit()
        
        transfer_aware_bandit = TransferAwareBandit(
            bandit=bandit,
            pg_store=db_store
        )
        
        # Get current mastery state for all concepts
        with get_db_connection(db_store) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT concept, state_data FROM learning_state
                WHERE user_id = %s
                ORDER BY updated_at DESC
            """, (user_id,))
            
            results = cursor.fetchall()
            cursor.close()
            
            if not results:
                return {
                    "user_id": user_id,
                    "recommended_concept": None,
                    "reason": "no_mastery_data",
                    "message": "No mastery data found for user"
                }
            
            # Extract mastery data from all concepts
            mastery_data = {}
            for concept, state_data in results:
                if isinstance(state_data, dict):
                    # Mastery is stored as a direct float in state_data
                    mastery = state_data.get("mastery", 0.0)
                    if isinstance(mastery, (int, float)):
                        mastery_data[concept] = float(mastery)
            
            if not mastery_data:
                return {
                    "user_id": user_id,
                    "recommended_concept": None,
                    "reason": "no_concept_mastery",
                    "message": "No concept mastery data found"
                }
            
            # Get transfer-aware recommendation
            recommendation = transfer_aware_bandit.get_transfer_aware_recommendation(
                user_id=user_id,
                mastery_data=mastery_data,
                context={"mode": "transfer_aware"}
            )
            
            logger.info(f"🔥 Transfer-aware recommendation: {recommendation}")
            
            return {
                "user_id": user_id,
                **recommendation,
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        logger.error(f"❌ Transfer-aware recommendation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Transfer-aware recommendation failed: {str(e)}")