"""
Admin API Routes - System monitoring and management
"""

from fastapi import APIRouter
import logging

from app.services import get_service_factory

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/reconstruction/status")
async def get_reconstruction_status():
    """Get detailed reconstruction status and statistics"""
    try:
        factory = get_service_factory()
        
        # Check if TaskService has been initialized
        if 'task_service' not in factory._services:
            return {
                "status": "not_initialized",
                "message": "TaskService not yet initialized - call an endpoint that triggers it",
                "reconstruction": None
            }
        
        task_service = factory._services['task_service']
        
        # Get bandit statistics
        bandit_stats = {}
        if hasattr(task_service, 'bandit') and task_service.bandit:
            bandit = task_service.bandit
            
            # User counts
            total_users = 0
            if hasattr(bandit, 'step_count'):
                total_users = len(bandit.step_count)
            
            # Arm counts
            total_arms = 0
            arm_distribution = {}
            if hasattr(bandit, 'arm_contexts'):
                for user_id, arms in bandit.arm_contexts.items():
                    user_arm_count = len(arms)
                    total_arms += user_arm_count
                    arm_distribution[user_id] = user_arm_count
            
            # Step counts
            total_steps = 0
            step_distribution = {}
            if hasattr(bandit, 'step_count'):
                total_steps = sum(bandit.step_count.values())
                step_distribution = dict(bandit.step_count)
            
            # Alpha/Beta params (sample for first few users)
            alpha_beta_sample = {}
            if hasattr(bandit, 'alpha_beta_params'):
                sample_users = list(bandit.alpha_beta_params.keys())[:5]
                for user_id in sample_users:
                    alpha_beta_sample[user_id] = bandit.alpha_beta_params[user_id]
            
            bandit_stats = {
                "total_users": total_users,
                "total_arms": total_arms,
                "total_steps": total_steps,
                "avg_steps_per_user": total_steps / max(total_users, 1),
                "avg_arms_per_user": total_arms / max(total_users, 1),
                "arm_distribution": arm_distribution,
                "step_distribution": step_distribution,
                "alpha_beta_sample": alpha_beta_sample
            }
        
        # Get learner statistics
        learner_stats = {}
        if hasattr(task_service, 'engine') and task_service.engine and hasattr(task_service.engine, 'learner'):
            learner = task_service.engine.learner
            
            # Mastery data
            total_concepts = 0
            concept_distribution = {}
            if hasattr(learner, 'user_mastery'):
                for user_id, concepts in learner.user_mastery.items():
                    user_concept_count = len(concepts)
                    total_concepts += user_concept_count
                    concept_distribution[user_id] = user_concept_count
            elif hasattr(learner, 'mastery_data'):
                for user_id, concepts in learner.mastery_data.items():
                    user_concept_count = len(concepts)
                    total_concepts += user_concept_count
                    concept_distribution[user_id] = user_concept_count
            
            learner_stats = {
                "total_concepts": total_concepts,
                "avg_concepts_per_user": total_concepts / max(len(concept_distribution), 1),
                "concept_distribution": concept_distribution
            }
        
        return {
            "status": "initialized",
            "message": "TaskService initialized with reconstruction data",
            "bandit": bandit_stats,
            "learner": learner_stats,
            "services_initialized": list(factory._services.keys())
        }
        
    except Exception as e:
        logger.error(f"Error getting reconstruction status: {e}")
        return {
            "status": "error",
            "message": f"Error retrieving status: {str(e)}",
            "reconstruction": None
        }

@router.post("/reconstruction/trigger")
async def trigger_reconstruction():
    """Manually trigger state reconstruction (for debugging)"""
    try:
        factory = get_service_factory()
        
        # Reset TaskService to force reconstruction
        if 'task_service' in factory._services:
            del factory._services['task_service']
            logger.info("🔄 TaskService reset - will trigger fresh reconstruction")
        
        # Force recreation and reconstruction
        task_service = factory.get_task_service()
        
        return {
            "status": "triggered",
            "message": "State reconstruction manually triggered",
            "services_initialized": list(factory._services.keys())
        }
        
    except Exception as e:
        logger.error(f"Error triggering reconstruction: {e}")
        return {
            "status": "error",
            "message": f"Error triggering reconstruction: {str(e)}"
        }

@router.get("/system/health")
async def get_system_health():
    """Get overall system health status"""
    try:
        factory = get_service_factory()
        
        health_status = {
            "service_factory": "healthy",
            "services": {},
            "data_stores": {}
        }
        
        # Check each service
        for service_name, service_instance in factory._services.items():
            try:
                health_status["services"][service_name] = "healthy"
            except Exception as e:
                health_status["services"][service_name] = f"unhealthy: {str(e)}"
        
        # Check TaskService data stores
        if 'task_service' in factory._services:
            task_service = factory._services['task_service']
            
            # Check PostgreSQL store
            postgres_store = factory._find_postgres_store(task_service)
            if postgres_store:
                try:
                    stats = postgres_store.get_interaction_stats()
                    health_status["data_stores"]["postgresql"] = {
                        "status": "healthy",
                        "stats": stats
                    }
                except Exception as e:
                    health_status["data_stores"]["postgresql"] = {
                        "status": "unhealthy",
                        "error": str(e)
                    }
            else:
                health_status["data_stores"]["postgresql"] = {
                    "status": "not_found"
                }
        
        return health_status
        
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        return {
            "service_factory": f"unhealthy: {str(e)}",
            "services": {},
            "data_stores": {}
        }
