"""
Experiments Management API - Create and manage learning experiments
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import uuid

logger = logging.getLogger(__name__)
router = APIRouter()

# Import PHASE 1-6 experiments
try:
    from experiments.phase1_experiment_2a_stochastic_cognition_divergence import Experiment2A, Experiment2AConfig
    from experiments.phase2_experiment_1a_cold_start_baselines import Experiment1A, Experiment1AConfig
    from experiments.phase2_experiment_1b_early_learning_curves import Experiment1B, Experiment1BConfig
    from experiments.phase2_cold_start_real import ColdStartRealExperiment, ColdStartRealConfig
    from experiments.phase3_ablation_1_signal_necessity import Ablation1, Ablation1Config
    from experiments.phase3_ablation_2_ensemble_contribution import Ablation2, Ablation2Config
    from experiments.phase4_experiment_3a_bandit_regret_analysis import Experiment3A, Experiment3AConfig
    from experiments.phase4_experiment_4a_jt_aware_policy_selection import Experiment4A, Experiment4AConfig
    from experiments.phase4_experiment_4b_jt_correlation_testing import Experiment4B, Experiment4BConfig
    from experiments.phase5_experiment_5_ensemble_convergence import Experiment5, Experiment5Config
    from experiments.phase5_experiment_6_learning_gain_dynamics import Experiment6, Experiment6Config
    from experiments.phase6_generalization import Generalization, GeneralizationConfig
    EXPERIMENTS_AVAILABLE = True
except ImportError:
    logger.warning("PHASE 1-6 experiments not available - mock experiments not loaded")
    EXPERIMENTS_AVAILABLE = False


def convert_numpy_types(obj):
    """Convert numpy types to Python types for JSON serialization"""
    import numpy as np
    if isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, (np.bool_, np.integer, np.floating)):
        return obj.item()
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj

class ExperimentConfig(BaseModel):
    name: str
    description: Optional[str] = None
    groups: List[str]  # e.g., ["hcie", "random", "hybrid"]
    user_count: int
    duration_days: Optional[int] = 7
    metrics: List[str] = ["reward", "regret", "mastery_gain"]
    auto_start: bool = False

# In-memory experiment storage (in production, use Redis/DB)
active_experiments: Dict[str, Dict] = {}

@router.post("/")
async def create_experiment(config: ExperimentConfig) -> Dict[str, Any]:
    """Create a new learning experiment"""
    try:
        experiment_id = str(uuid.uuid4())
        
        experiment = {
            "id": experiment_id,
            "name": config.name,
            "description": config.description,
            "groups": config.groups,
            "user_count": config.user_count,
            "duration_days": config.duration_days,
            "metrics": config.metrics,
            "status": "created",
            "created_at": datetime.utcnow().isoformat(),
            "started_at": None,
            "completed_at": None,
            "results": {}
        }
        
        active_experiments[experiment_id] = experiment
        
        logger.info(f"🧪 Created experiment: {config.name} ({experiment_id})")
        
        return {
            "experiment_id": experiment_id,
            "status": "created",
            "config": experiment
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to create experiment: {e}")
        raise HTTPException(status_code=500, detail="Failed to create experiment")

@router.get("/")
async def list_experiments() -> Dict[str, Any]:
    """List all experiments"""
    return {
        "experiments": list(active_experiments.values()),
        "total": len(active_experiments)
    }

@router.get("/{experiment_id}")
async def get_experiment(experiment_id: str) -> Dict[str, Any]:
    """Get experiment details"""
    if experiment_id not in active_experiments:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    return active_experiments[experiment_id]

@router.post("/{experiment_id}/start")
async def start_experiment(experiment_id: str) -> Dict[str, Any]:
    """Start an experiment"""
    if experiment_id not in active_experiments:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    experiment = active_experiments[experiment_id]
    
    if experiment["status"] == "running":
        raise HTTPException(status_code=400, detail="Experiment already running")
    
    if experiment["status"] == "completed":
        raise HTTPException(status_code=400, detail="Experiment already completed")
    
    experiment["status"] = "running"
    experiment["started_at"] = datetime.utcnow().isoformat()
    
    logger.info(f"🚀 Started experiment: {experiment['name']} ({experiment_id})")
    
    return {
        "experiment_id": experiment_id,
        "status": "running",
        "started_at": experiment["started_at"]
    }

@router.post("/{experiment_id}/stop")
async def stop_experiment(experiment_id: str) -> Dict[str, Any]:
    """Stop an experiment"""
    if experiment_id not in active_experiments:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    experiment = active_experiments[experiment_id]
    
    if experiment["status"] != "running":
        raise HTTPException(status_code=400, detail="Experiment not running")
    
    experiment["status"] = "stopped"
    experiment["completed_at"] = datetime.utcnow().isoformat()
    
    logger.info(f"⏹️ Stopped experiment: {experiment['name']} ({experiment_id})")
    
    return {
        "experiment_id": experiment_id,
        "status": "stopped",
        "completed_at": experiment["completed_at"]
    }

@router.delete("/{experiment_id}")
async def delete_experiment(experiment_id: str) -> Dict[str, Any]:
    """Delete an experiment"""
    if experiment_id not in active_experiments:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    experiment_name = active_experiments[experiment_id]["name"]
    del active_experiments[experiment_id]
    
    logger.info(f"🗑️ Deleted experiment: {experiment_name} ({experiment_id})")
    
    return {
        "experiment_id": experiment_id,
        "status": "deleted"
    }


# =============================================================================
# PHASE 1-6 EXPERIMENT ENDPOINTS - Real Runtime Integration
# =============================================================================

@router.post("/phase1/2a/launch")
async def launch_phase1_experiment_2a(
    num_runs: int = 5,
    num_learners: int = 20,
    num_concepts: int = 30,
    num_interactions: int = 100,
    seed: int = 42,
    learner_archetype: str = "novice"
) -> Dict[str, Any]:
    """
    Launch PHASE 1 Experiment 2A: Stochastic Cognition Divergence
    
    Verifies deterministic replay integrity, bounded stochasticity, projection_hash consistency.
    Supports Contribution A (System Design CORE).
    """
    if not EXPERIMENTS_AVAILABLE:
        raise HTTPException(status_code=503, detail="PHASE 1-6 experiments not available")
    
    try:
        config = Experiment2AConfig(
            num_runs=num_runs,
            num_learners=num_learners,
            num_concepts=num_concepts,
            num_interactions=num_interactions,
            seed=seed,
            learner_archetype=learner_archetype
        )
        
        experiment = Experiment2A(config)
        results = experiment.run()
        
        return {
            "status": "success",
            "message": "PHASE 1 Experiment 2A launched successfully",
            "experiment_id": results.experiment_id,
            "success": results.success,
            "results": convert_numpy_types(results.__dict__)
        }
    except Exception as e:
        logger.error(f"Failed to launch PHASE 1 Experiment 2A: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to launch experiment: {str(e)}")


@router.post("/phase2/1a/launch")
async def launch_phase2_experiment_1a(
    num_runs: int = 5,
    num_learners: int = 20,
    num_concepts: int = 30,
    num_interactions: int = 100,
    seed: int = 42,
    learner_archetype: str = "novice"
) -> Dict[str, Any]:
    """
    Launch PHASE 2 Experiment 1A: Cold-Start with Strong Baselines
    
    Baselines: Random, Static, Heuristic mastery-only.
    Metrics: Learning gain, Time-to-mastery, Regret, Accuracy.
    Supports Contribution C (VALIDATION).
    """
    if not EXPERIMENTS_AVAILABLE:
        raise HTTPException(status_code=503, detail="PHASE 1-6 experiments not available")
    
    try:
        config = Experiment1AConfig(
            num_runs=num_runs,
            num_learners=num_learners,
            num_concepts=num_concepts,
            num_interactions=num_interactions,
            seed=seed,
            learner_archetype=learner_archetype
        )
        
        experiment = Experiment1A(config)
        results = experiment.run()
        
        return {
            "status": "success",
            "message": "PHASE 2 Experiment 1A launched successfully",
            "experiment_id": results.experiment_id,
            "success": results.success,
            "results": convert_numpy_types(results.__dict__)
        }
    except Exception as e:
        logger.error(f"Failed to launch PHASE 2 Experiment 1A: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to launch experiment: {str(e)}")


@router.post("/phase2/cold_start_real/launch")
async def launch_phase2_cold_start_real(
    num_learners: int = 20,
    num_concepts: int = 30,
    num_interactions: int = 20,
    seed: int = 42,
    cold_start_alpha: float = 1.0,
    cold_start_beta: float = 2.33,
    learner_archetype: str = "novice",
    run_baselines: bool = False,
    use_bandit_selection: bool = True,
    enable_transfer_learning: bool = True
) -> Dict[str, Any]:
    """
    Launch Modern Cold Start Real System Experiment
    
    Uses full architecture (UnifiedBrain, TrajectoryRecorder, Ownership enforcement).
    Initializes learners with cold-start parameters (low confidence alpha/beta).
    Tests full signal hierarchy under cold-start conditions (first 5-20 interactions).
    
    Supports Contribution A (System Design CORE) - validates architecture under cold-start.
    
    Baselines: If run_baselines=True, also runs Random, Static, and Heuristic mastery-only baselines for comparison.
    
    Options:
    - use_bandit_selection: Enable/disable Thompson sampling bandit for task selection
    - enable_transfer_learning: Enable/disable K-12 concept DAG transfer learning
    """
    if not EXPERIMENTS_AVAILABLE:
        raise HTTPException(status_code=503, detail="PHASE 1-6 experiments not available")
    
    try:
        config = ColdStartRealConfig(
            num_learners=num_learners,
            num_concepts=num_concepts,
            num_interactions=num_interactions,
            seed=seed,
            cold_start_alpha=cold_start_alpha,
            cold_start_beta=cold_start_beta,
            learner_archetype=learner_archetype,
            run_baselines=run_baselines,
            use_bandit_selection=use_bandit_selection,
            enable_transfer_learning=enable_transfer_learning
        )
        
        # 🔥 DETERMINISM CHECK: Log config parameters before experiment creation
        print(f"🔥 API DETERMINISM CHECK: num_learners={num_learners}, num_interactions={num_interactions}, seed={seed}, learner_archetype={learner_archetype}")
        
        experiment = ColdStartRealExperiment(config)
        results = experiment.run()
        
        return {
            "status": "success",
            "message": "PHASE 2 Cold Start Real experiment launched successfully",
            "experiment_id": results.experiment_id,
            "experiment_run_id": experiment.experiment_run_id,
            "run_namespace": experiment._run_namespace,
            "config_snapshot": experiment._config_snapshot,
            "success": results.success,
            "results": convert_numpy_types(results.__dict__)
        }
    except Exception as e:
        logger.error(f"Failed to launch PHASE 2 Cold Start Real: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to launch experiment: {str(e)}")


@router.post("/phase2/1b/launch")
async def launch_phase2_experiment_1b(
    num_runs: int = 5,
    num_learners: int = 20,
    num_concepts: int = 30,
    num_interactions: int = 100,
    seed: int = 42,
    learner_archetype: str = "novice"
) -> Dict[str, Any]:
    """
    Launch PHASE 2 Experiment 1B: Early Learning Curves
    
    Performance over 5, 10, 20 interactions.
    Metrics: Learning slope, Time-to-threshold, Regret reduction.
    Supports Contribution C (VALIDATION).
    """
    if not EXPERIMENTS_AVAILABLE:
        raise HTTPException(status_code=503, detail="PHASE 1-6 experiments not available")
    
    try:
        config = Experiment1BConfig(
            num_runs=num_runs,
            num_learners=num_learners,
            num_concepts=num_concepts,
            num_interactions=num_interactions,
            seed=seed,
            learner_archetype=learner_archetype
        )
        
        experiment = Experiment1B(config)
        results = experiment.run()
        
        return {
            "status": "success",
            "message": "PHASE 2 Experiment 1B launched successfully",
            "experiment_id": results.experiment_id,
            "success": results.success,
            "results": convert_numpy_types(results.__dict__)
        }
    except Exception as e:
        logger.error(f"Failed to launch PHASE 2 Experiment 1B: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to launch experiment: {str(e)}")


@router.post("/phase3/ablation1/launch")
async def launch_phase3_ablation1(
    num_runs: int = 5,
    num_learners: int = 20,
    num_concepts: int = 30,
    num_interactions: int = 100,
    seed: int = 42,
    learner_archetype: str = "novice"
) -> Dict[str, Any]:
    """
    Launch PHASE 3 Ablation 1: Signal Necessity
    
    Remove uncertainty, ZPD, JT, Lyapunov, Bayesian, Kalman one at a time.
    Metrics: Learning gain drop, stability degradation.
    Supports Contribution A (System Design CORE).
    """
    if not EXPERIMENTS_AVAILABLE:
        raise HTTPException(status_code=503, detail="PHASE 1-6 experiments not available")
    
    try:
        config = Ablation1Config(
            num_runs=num_runs,
            num_learners=num_learners,
            num_concepts=num_concepts,
            num_interactions=num_interactions,
            seed=seed,
            learner_archetype=learner_archetype
        )
        
        experiment = Ablation1(config)
        results = experiment.run()
        
        return {
            "status": "success",
            "message": "PHASE 3 Ablation 1 launched successfully",
            "experiment_id": results.experiment_id,
            "success": results.success,
            "results": convert_numpy_types(results.__dict__)
        }
    except Exception as e:
        logger.error(f"Failed to launch PHASE 3 Ablation 1: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to launch experiment: {str(e)}")


@router.post("/phase3/ablation2/launch")
async def launch_phase3_ablation2(
    num_runs: int = 5,
    num_learners: int = 20,
    num_concepts: int = 30,
    num_interactions: int = 100,
    seed: int = 42,
    learner_archetype: str = "novice"
) -> Dict[str, Any]:
    """
    Launch PHASE 3 Ablation 2: Ensemble Contribution
    
    Remove Lyapunov-only, Bayesian-only, Kalman-only vs full ensemble.
    Metrics: Robustness, uncertainty calibration, performance drop.
    Supports Contribution A (System Design CORE).
    """
    if not EXPERIMENTS_AVAILABLE:
        raise HTTPException(status_code=503, detail="PHASE 1-6 experiments not available")
    
    try:
        config = Ablation2Config(
            num_runs=num_runs,
            num_learners=num_learners,
            num_concepts=num_concepts,
            num_interactions=num_interactions,
            seed=seed,
            learner_archetype=learner_archetype
        )
        
        experiment = Ablation2(config)
        results = experiment.run()
        
        return {
            "status": "success",
            "message": "PHASE 3 Ablation 2 launched successfully",
            "experiment_id": results.experiment_id,
            "success": results.success,
            "results": convert_numpy_types(results.__dict__)
        }
    except Exception as e:
        logger.error(f"Failed to launch PHASE 3 Ablation 2: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to launch experiment: {str(e)}")


@router.post("/phase4/3a/launch")
async def launch_phase4_experiment_3a(
    num_runs: int = 5,
    num_learners: int = 20,
    num_concepts: int = 30,
    num_interactions: int = 200,
    seed: int = 42,
    learner_archetype: str = "novice"
) -> Dict[str, Any]:
    """
    Launch PHASE 4 Experiment 3A: Bandit Regret Analysis - Full System Integration
    
    Full UnifiedBrain integration via CohortRunner for end-to-end experiment execution.
    """
    import json
    print("🔥🔥🔥 PHASE 4 Experiment 3A endpoint called - FULL SYSTEM INTEGRATION")
    logger.info("🔥 PHASE 4 Experiment 3A: Attempting full UnifiedBrain integration")
    
    try:
        # Full system integration using CohortRunner + UnifiedBrain
        logger.info("🔥 Importing CohortRunner and dependencies")
        from infrastructure.experiment.cohort_runner import CohortRunner
        from infrastructure.experiment.trajectory_recorder import TrajectoryRecorder
        from infrastructure.experiment.interaction_scheduler import InteractionScheduler
        from core.learning.unified_brain import UnifiedLearningBrain
        from storage.postgres_store.interaction_store import PostgresInteractionStore
        import numpy as np
        
        # Create DB adapter to bridge PostgresInteractionStore to CohortRunner interface
        class PostgresAdapter:
            def __init__(self, store):
                self.store = store
            
            def insert(self, table: str, data: Dict[str, Any]) -> str:
                """Insert record and return ID"""
                columns = list(data.keys())
                values = list(data.values())
                placeholders = ', '.join(['%s'] * len(values))
                columns_str = ', '.join(columns)
                
                # Convert datetime objects to strings, dicts to JSON, and numpy types to Python types
                import datetime
                import json
                for i, v in enumerate(values):
                    if isinstance(v, datetime.datetime):
                        values[i] = v.isoformat()
                    elif isinstance(v, dict):
                        values[i] = json.dumps(v)
                    elif hasattr(v, '__module__') and v.__module__ == 'numpy':
                        # Convert numpy types to Python types
                        if hasattr(v, 'item'):
                            values[i] = v.item()
                        else:
                            values[i] = float(v)
                
                query = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders}) RETURNING id"
                logger.info(f"Inserting into {table}: {query[:100]}...")
                result = self.store.execute_write(query, tuple(values), fetch_one=True)
                logger.info(f"Insert result: {result}")
                
                if not result or 'id' not in result:
                    raise Exception(f"Failed to insert into {table}: insert returned no ID")
                
                return str(result['id'])
            
            def query(self, table: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
                """Query records with filters"""
                if not filters:
                    query = f"SELECT * FROM {table}"
                    result = self.store.execute_read(query)
                else:
                    where_clauses = [f"{k} = %s" for k in filters.keys()]
                    where_str = ' AND '.join(where_clauses)
                    query = f"SELECT * FROM {table} WHERE {where_str}"
                    result = self.store.execute_read(query, tuple(filters.values()))
                return result if result else []
            
            def update(self, table: str, filters: Dict[str, Any], updates: Dict[str, Any]):
                """Update records"""
                set_clauses = [f"{k} = %s" for k in updates.keys()]
                set_str = ', '.join(set_clauses)
                where_clauses = [f"{k} = %s" for k in filters.keys()]
                where_str = ' AND '.join(where_clauses)
                
                query = f"UPDATE {table} SET {set_str} WHERE {where_str}"
                params = tuple(list(updates.values()) + list(filters.values()))
                self.store.execute_write(query, params)
        
        # Initialize components with correct database configuration for Docker
        import os
        from config.env import settings
        
        # Set DATABASE_URL for PostgresInteractionStore (must be set before initialization)
        db_host = os.getenv("POSTGRES_HOST", "postgres")
        db_port = os.getenv("POSTGRES_PORT", "5432")
        db_name = os.getenv("POSTGRES_DB", "hcie")
        db_user = os.getenv("POSTGRES_USER", "hcie_user")
        db_password = os.getenv("POSTGRES_PASSWORD", "hcie_password")
        
        # Override settings.database_url before initializing PostgresInteractionStore
        original_db_url = settings.database_url
        settings.database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        
        # Also set DATABASE_URL environment variable as backup
        os.environ["DATABASE_URL"] = settings.database_url
        
        db_store = PostgresInteractionStore()
        
        # Restore original database_url
        settings.database_url = original_db_url
        
        # Test database connection
        logger.info(f"🔥 Testing database connection to {db_host}:{db_port}...")
        try:
            test_result = db_store.execute_read("SELECT 1")
            logger.info(f"🔥 Database connection successful: {test_result}")
        except Exception as e:
            logger.error(f"🔥 Database connection failed: {e}")
            raise
        
        db_client = PostgresAdapter(db_store)
        trajectory_recorder = TrajectoryRecorder(db_client)
        unified_brain = UnifiedLearningBrain(trajectory_recorder=trajectory_recorder)
        cohort_runner = CohortRunner(unified_brain, trajectory_recorder, db_client)
        
        # Generate experiment_id and experiment_run_id
        experiment_id = str(uuid.uuid4())
        experiment_run_id = str(uuid.uuid4())
        
        # Create concepts list
        concepts = [
            "computing_systems", "networks", "data", "algorithms", "impacts",
            "inclusive_culture", "collaboration", "problem_recognition",
            "abstractions", "creation", "testing", "communication"
        ]
        
        # Initialize interaction scheduler with concepts
        interaction_scheduler = InteractionScheduler(concepts=concepts)
        
        # Create experiment record first (required for foreign key constraint)
        logger.info(f"🔥 Creating experiment record with ID: {experiment_id}")
        try:
            # Get default tenant ID
            tenant_query = "SELECT id FROM tenants WHERE name = 'default' LIMIT 1"
            tenant_result = db_store.execute_read(tenant_query, fetch_one=True)
            if not tenant_result:
                raise Exception("Default tenant not found")
            tenant_id = tenant_result["id"]
            
            experiment_data = {
                "id": experiment_id,
                "tenant_id": tenant_id,  # Use existing tenant
                "name": f"PHASE4_3A_Bandit_Regret_Analysis_{seed}",
                "groups": [],
                "status": "created"
            }
            db_client.insert("experiments", experiment_data)
            logger.info(f"🔥 Experiment record created with ID: {experiment_id}")
        except Exception as e:
            logger.error(f"🔥 Failed to create experiment record: {e}")
            raise
        
        # Create experiment run in DB
        logger.info(f"🔥 Creating experiment run with ID: {experiment_run_id}")
        try:
            run_id = cohort_runner.create_experiment_run(
                experiment_id=experiment_id,
                run_name=f"PHASE4_3A_{seed}",
                policy="hcie",
                learner_archetype=learner_archetype,
                num_learners=num_learners,
                num_concepts=num_concepts,
                num_interactions=num_interactions,
                config={"seed": seed}
            )
            logger.info(f"🔥 Experiment run created with ID: {run_id}")
        except Exception as e:
            logger.error(f"🔥 Failed to create experiment run: {e}")
            raise
        
        # Generate simulated user IDs
        user_ids = [f"exp_user_{i}" for i in range(num_learners)]
        
        # Mark users as simulated in user_state table
        for user_id in user_ids:
            try:
                # Check if user exists
                existing = db_store.execute_read(
                    "SELECT user_id FROM user_state WHERE user_id = %s",
                    (user_id,),
                    fetch_one=True
                )
                if existing:
                    db_store.execute_write(
                        "UPDATE user_state SET user_type = 'simulated' WHERE user_id = %s",
                        (user_id,)
                    )
                else:
                    db_store.execute_write(
                        "INSERT INTO user_state (user_id, user_type, mastery) VALUES (%s, 'simulated', '{}')",
                        (user_id,)
                    )
            except Exception as e:
                logger.warning(f"Failed to mark {user_id} as simulated: {e}")
        
        # Assign users to cohort
        cohort_runner.assign_cohorts(run_id, user_ids, cohort_name="default")
        
        # Execute run (this calls UnifiedBrain.process_event() directly)
        logger.info(f"🔥 Executing CohortRunner for {num_learners} learners, {num_interactions} interactions each")
        metrics = cohort_runner.execute_run(run_id, interaction_scheduler)
        
        # Query trajectory_records for results
        trajectories = db_store.execute_read(
            "SELECT * FROM trajectory_records WHERE experiment_run_id = %s",
            (run_id,)
        )
        
        # Compute basic metrics from trajectories
        total_correct = sum(1 for t in trajectories if t.get("correctness") is True)
        total_interactions = len(trajectories)
        avg_mastery = np.mean([t.get("mastery_after", 0) for t in trajectories]) if trajectories else 0
        
        response_data = {
            "status": "success",
            "message": "PHASE 4 Experiment 3A launched successfully with full UnifiedBrain integration",
            "experiment_run_id": run_id,
            "success": True,
            "mode": "full_unified_brain",
            "num_learners": num_learners,
            "num_concepts": num_concepts,
            "num_interactions": num_interactions,
            "total_trajectories": total_interactions,
            "total_correct": total_correct,
            "accuracy": float(total_correct / total_interactions) if total_interactions > 0 else 0.0,
            "final_avg_mastery": float(avg_mastery),
            "execution_metrics": {
                "total_interactions": metrics.get("total_interactions", 0),
                "num_learners": metrics.get("num_learners", 0)
            }
        }
        
        logger.info(f"🔥 Full system integration completed: {total_interactions} trajectories recorded")
        
        return response_data
        
    except Exception as e:
        logger.error(f"Failed to launch full system experiment: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to launch experiment: {str(e)}")


@router.post("/phase4/4a/launch")
async def launch_phase4_experiment_4a(
    num_runs: int = 5,
    num_learners: int = 20,
    num_concepts: int = 30,
    num_interactions: int = 100,
    seed: int = 42,
    learner_archetype: str = "novice"
) -> Dict[str, Any]:
    """
    Launch PHASE 4 Experiment 4A: JT-Aware Policy Selection with Baselines
    
    Baselines: Greedy mastery, Uncertainty reduction, ZPD-only, Random.
    Metrics: JT trajectory, learning outcomes.
    Supports Contribution B (SUPPORTING).
    """
    if not EXPERIMENTS_AVAILABLE:
        raise HTTPException(status_code=503, detail="PHASE 1-6 experiments not available")
    
    try:
        config = Experiment4AConfig(
            num_runs=num_runs,
            num_learners=num_learners,
            num_concepts=num_concepts,
            num_interactions=num_interactions,
            seed=seed,
            learner_archetype=learner_archetype
        )
        
        experiment = Experiment4A(config)
        results = experiment.run()
        
        return {
            "status": "success",
            "message": "PHASE 4 Experiment 4A launched successfully",
            "experiment_id": results.experiment_id,
            "success": results.success,
            "results": convert_numpy_types(results.__dict__)
        }
    except Exception as e:
        logger.error(f"Failed to launch PHASE 4 Experiment 4A: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to launch experiment: {str(e)}")


@router.post("/phase4/4b/launch")
async def launch_phase4_experiment_4b(
    num_runs: int = 5,
    num_learners: int = 20,
    num_concepts: int = 30,
    num_interactions: int = 100,
    seed: int = 42,
    learner_archetype: str = "novice"
) -> Dict[str, Any]:
    """
    Launch PHASE 4 Experiment 4B: JT Correlation Testing
    
    Does JT correlate with learning outcomes? Counterfactual analysis.
    Supports Contribution B (SUPPORTING).
    """
    if not EXPERIMENTS_AVAILABLE:
        raise HTTPException(status_code=503, detail="PHASE 1-6 experiments not available")
    
    try:
        config = Experiment4BConfig(
            num_runs=num_runs,
            num_learners=num_learners,
            num_concepts=num_concepts,
            num_interactions=num_interactions,
            seed=seed,
            learner_archetype=learner_archetype
        )
        
        experiment = Experiment4B(config)
        results = experiment.run()
        
        return {
            "status": "success",
            "message": "PHASE 4 Experiment 4B launched successfully",
            "experiment_id": results.experiment_id,
            "success": results.success,
            "results": convert_numpy_types(results.__dict__)
        }
    except Exception as e:
        logger.error(f"Failed to launch PHASE 4 Experiment 4B: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to launch experiment: {str(e)}")


@router.post("/phase5/5/launch")
async def launch_phase5_experiment_5(
    num_runs: int = 5,
    num_learners: int = 20,
    num_concepts: int = 30,
    num_interactions: int = 100,
    seed: int = 42,
    learner_archetype: str = "novice"
) -> Dict[str, Any]:
    """
    Launch PHASE 5 Experiment 5: Ensemble Convergence
    
    Ensemble agreement over time, multi-learner vs single learners.
    Metrics: Convergence rate, agreement metrics.
    Supports Contribution A (System Design CORE).
    """
    if not EXPERIMENTS_AVAILABLE:
        raise HTTPException(status_code=503, detail="PHASE 1-6 experiments not available")
    
    try:
        config = Experiment5Config(
            num_runs=num_runs,
            num_learners=num_learners,
            num_concepts=num_concepts,
            num_interactions=num_interactions,
            seed=seed,
            learner_archetype=learner_archetype
        )
        
        experiment = Experiment5(config)
        results = experiment.run()
        
        return {
            "status": "success",
            "message": "PHASE 5 Experiment 5 launched successfully",
            "experiment_id": results.experiment_id,
            "success": results.success,
            "results": convert_numpy_types(results.__dict__)
        }
    except Exception as e:
        logger.error(f"Failed to launch PHASE 5 Experiment 5: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to launch experiment: {str(e)}")


@router.post("/phase5/6/launch")
async def launch_phase5_experiment_6(
    num_runs: int = 5,
    num_learners: int = 20,
    num_concepts: int = 30,
    num_interactions: int = 100,
    seed: int = 42,
    learner_archetype: str = "novice"
) -> Dict[str, Any]:
    """
    Launch PHASE 5 Experiment 6: Learning Gain Dynamics with JT Evolution
    
    JT trajectory, learner contributions, mastery delta, uncertainty reduction.
    Metrics: Longitudinal stability.
    Supports Contribution B (SUPPORTING).
    """
    if not EXPERIMENTS_AVAILABLE:
        raise HTTPException(status_code=503, detail="PHASE 1-6 experiments not available")
    
    try:
        config = Experiment6Config(
            num_runs=num_runs,
            num_learners=num_learners,
            num_concepts=num_concepts,
            num_interactions=num_interactions,
            seed=seed,
            learner_archetype=learner_archetype
        )
        
        experiment = Experiment6(config)
        results = experiment.run()
        
        return {
            "status": "success",
            "message": "PHASE 5 Experiment 6 launched successfully",
            "experiment_id": results.experiment_id,
            "success": results.success,
            "results": convert_numpy_types(results.__dict__)
        }
    except Exception as e:
        logger.error(f"Failed to launch PHASE 5 Experiment 6: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to launch experiment: {str(e)}")


@router.post("/phase6/generalization/launch")
async def launch_phase6_generalization(
    num_runs: int = 3,
    num_learners: int = 10,
    num_concepts: int = 20,
    num_interactions: int = 100,
    seed: int = 42,
    learner_archetype: str = "novice"
) -> Dict[str, Any]:
    """
    Launch PHASE 6 Generalization Test
    
    Different learners, difficulty distributions, domains, cross-concept transfer.
    Metrics: Generalization score, performance consistency, transfer effectiveness.
    Supports Contribution C (VALIDATION).
    """
    if not EXPERIMENTS_AVAILABLE:
        raise HTTPException(status_code=503, detail="PHASE 1-6 experiments not available")
    
    try:
        config = GeneralizationConfig(
            num_runs=num_runs,
            num_learners=num_learners,
            num_concepts=num_concepts,
            num_interactions=num_interactions,
            seed=seed,
            learner_archetype=learner_archetype
        )
        
        experiment = Generalization(config)
        results = experiment.run()
        
        return {
            "status": "success",
            "message": "PHASE 6 Generalization Test launched successfully",
            "experiment_id": results.experiment_id,
            "success": results.success,
            "results": convert_numpy_types(results.__dict__)
        }
    except Exception as e:
        logger.error(f"Failed to launch PHASE 6 Generalization: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to launch experiment: {str(e)}")


# =============================================================================
# EVALUATION ENGINE API ENDPOINTS
# =============================================================================

class EvaluationRequest(BaseModel):
    """Request model for experiment evaluation"""
    experiment_run_id: str
    evaluation_windows: List[int] = [5, 10, 20]
    metrics: List[str] = ["learning_gain", "regret", "stability"]
    statistical_method: str = "frequentist"
    confidence_level: float = 0.95


class ComparisonRequest(BaseModel):
    """Request model for comparing two experiment runs"""
    experiment_run_id_1: str
    experiment_run_id_2: str
    metric: str = "learning_gain"
    evaluation_window: int = 20
    statistical_method: str = "frequentist"
    confidence_level: float = 0.95


@router.post("/evaluate")
async def evaluate_experiment_run(request: EvaluationRequest) -> Dict[str, Any]:
    """
    Evaluate an experiment run with specified metrics and windows
    
    POST /experiments/evaluate
    
    Request:
    {
      "experiment_run_id": "exp_001",
      "evaluation_windows": [5, 10, 20],
      "metrics": ["learning_gain", "regret", "stability"],
      "statistical_method": "frequentist|bayesian",
      "confidence_level": 0.95
    }
    """
    try:
        # Import Evaluation Engine
        from infrastructure.experiment.evaluation_engine import EvaluationEngine
        from storage.postgres_store.interaction_store import PostgresInteractionStore
        
        # Initialize database client
        import os
        os.environ["DATABASE_URL"] = "postgresql://hcie_user:hcie_password@postgres:5432/hcie"
        db_store = PostgresInteractionStore()
        
        # Initialize Evaluation Engine
        evaluation_engine = EvaluationEngine(db_store)
        
        # Evaluate experiment run
        results = evaluation_engine.evaluate_experiment_run(
            experiment_run_id=request.experiment_run_id,
            evaluation_windows=request.evaluation_windows,
            metrics=request.metrics,
            statistical_method=request.statistical_method,
            confidence_level=request.confidence_level
        )
        
        # Convert numpy types for JSON serialization
        results = convert_numpy_types(results)
        
        logger.info(f"Evaluation complete for experiment run {request.experiment_run_id}")
        
        return {
            "status": "success",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Failed to evaluate experiment run: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to evaluate experiment run: {str(e)}")


@router.post("/compare")
async def compare_experiment_runs(request: ComparisonRequest) -> Dict[str, Any]:
    """
    Compare two experiment runs with statistical testing
    
    POST /experiments/compare
    
    Request:
    {
      "experiment_run_id_1": "exp_001",
      "experiment_run_id_2": "exp_002",
      "metric": "learning_gain",
      "evaluation_window": 20,
      "statistical_method": "frequentist|bayesian",
      "confidence_level": 0.95
    }
    """
    try:
        # Import Evaluation Engine
        from infrastructure.experiment.evaluation_engine import EvaluationEngine
        from storage.postgres_store.interaction_store import PostgresInteractionStore
        
        # Initialize database client
        import os
        os.environ["DATABASE_URL"] = "postgresql://hcie_user:hcie_password@postgres:5432/hcie"
        db_store = PostgresInteractionStore()
        
        # Initialize Evaluation Engine
        evaluation_engine = EvaluationEngine(db_store)
        
        # Compare experiment runs
        comparison = evaluation_engine.compare_experiment_runs(
            experiment_run_id_1=request.experiment_run_id_1,
            experiment_run_id_2=request.experiment_run_id_2,
            metric=request.metric,
            evaluation_window=request.evaluation_window,
            statistical_method=request.statistical_method,
            confidence_level=request.confidence_level
        )
        
        # Convert numpy types for JSON serialization
        comparison = convert_numpy_types(comparison)
        
        logger.info(f"Comparison complete for experiment runs {request.experiment_run_id_1} and {request.experiment_run_id_2}")
        
        return {
            "status": "success",
            "comparison": comparison
        }
        
    except Exception as e:
        logger.error(f"Failed to compare experiment runs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to compare experiment runs: {str(e)}")


# =============================================================================
# CONTRIBUTION C EVALUATION API ENDPOINT
# =============================================================================

class ContributionCConfig(BaseModel):
    """Configuration for Contribution C evaluation"""
    mode: str = "single-condition"  # gates-only, single-condition, baselines-only, ablations-only, practical, full
    policies: Optional[str] = None  # Comma-separated policies
    ablations: Optional[str] = None  # Comma-separated ablations
    archetype: str = "novice"  # Learner archetype
    archetypes: Optional[str] = None  # Comma-separated archetypes
    seed: int = 42  # Single seed
    seeds: Optional[str] = None  # Comma-separated seeds
    interactions: int = 20  # Interactions per learner
    learners: int = 5  # Learners per condition
    concepts: int = 10  # Number of concepts
    cold_start_alpha: float = 1.0  # Cold start alpha
    cold_start_beta: float = 2.33  # Cold start beta
    skip_drift_audit: bool = False  # Skip Gate 3
    output_dir: Optional[str] = None  # Output directory override


@router.post("/contribution_c/launch")
async def launch_contribution_c_evaluation(config: ContributionCConfig) -> Dict[str, Any]:
    """
    Launch Contribution C Evaluation via API
    
    Contribution C is the validation contribution that demonstrates HCIE outperforms
    strong baselines across multiple conditions, archetypes, and seeds.
    
    POST /experiments/contribution_c/launch
    
    Modes:
    - gates-only: Run gates 1-4 only, no conditions (fast validation)
    - single-condition: Run one condition (e.g., hcie)
    - baselines-only: Run all 9 baseline policies
    - ablations-only: Run all 7 ablation conditions
    - practical: Practical matrix (policies × critical ablations × novice × 3 seeds)
    - full: Full matrix (all policies × ablations × archetypes × seeds - large execution)
    
    Request:
    {
      "mode": "single-condition",
      "policies": "hcie",
      "ablations": null,
      "archetype": "novice",
      "archetypes": null,
      "seed": 42,
      "seeds": null,
      "interactions": 20,
      "learners": 5,
      "concepts": 10,
      "cold_start_alpha": 1.0,
      "cold_start_beta": 2.33,
      "skip_drift_audit": false,
      "output_dir": null
    }
    """
    try:
        # Import contribution_c_evaluation components
        from experiments.contribution_c_evaluation import (
            EvaluationConfig,
            UnifiedEvaluationRunner,
            ArtifactExporter,
            ALL_POLICIES,
            ALL_ABLATIONS,
            ARCHETYPE_MAP,
            GateFailure,
            RuntimeTopology,
            SemanticAudit,
            ConditionEquivalenceContract
        )
        from core.learning.learner_archetypes import ArchetypeType
        
        # Build EvaluationConfig from request
        seeds = [int(s.strip()) for s in config.seeds.split(",")] if config.seeds else [config.seed]
        archetypes = [a.strip() for a in config.archetypes.split(",")] if config.archetypes else [config.archetype]
        
        # Determine policies and ablations based on mode
        policies = []
        ablations = []
        
        if config.mode == "gates-only":
            policies = []
            ablations = []
        elif config.mode == "single-condition":
            policies = config.policies.split(",") if config.policies else ["hcie"]
            ablations = []
        elif config.mode == "baselines-only":
            policies = ALL_POLICIES
            ablations = []
        elif config.mode == "ablations-only":
            policies = ["hcie"]
            ablations = ALL_ABLATIONS
        elif config.mode == "practical":
            policies = ALL_POLICIES
            ablations = ["no_jt", "no_transfer", "no_zpd"]
            archetypes = ["novice"]
            seeds = [42, 123, 999]
        elif config.mode == "full":
            policies = ALL_POLICIES
            ablations = ALL_ABLATIONS
            archetypes = ["novice", "unstable", "transfer_heavy"]
            seeds = [42, 123, 999, 456, 789]
        else:
            raise HTTPException(status_code=400, detail=f"Invalid mode: {config.mode}")
        
        # Override with explicit policies/ablations if provided
        if config.policies:
            policies = [p.strip() for p in config.policies.split(",")]
        if config.ablations:
            ablations = [a.strip() for a in config.ablations.split(",")]
        
        # Build EvaluationConfig
        eval_config = EvaluationConfig(
            policies=policies,
            ablations=ablations,
            archetypes=archetypes,
            seeds=seeds,
            num_interactions=config.interactions,
            num_learners=config.learners,
            num_concepts=config.concepts,
            cold_start_alpha=config.cold_start_alpha,
            cold_start_beta=config.cold_start_beta,
            output_dir=config.output_dir or "",
            skip_drift_audit=config.skip_drift_audit
        )
        
        logger.info(f"🚀 Contribution C Evaluation — {eval_config.run_id}")
        logger.info(f"   mode={config.mode}  policies={policies}  ablations={ablations}")
        logger.info(f"   archetypes={archetypes}  seeds={seeds}")
        logger.info(f"   interactions={config.interactions}  learners={config.learners}")
        logger.info(f"   output_dir={eval_config.output_dir}")
        
        # Run gates-only mode
        if config.mode == "gates-only":
            try:
                g1 = RuntimeTopology()
                r1 = g1.verify()
                logger.info(f"Gate 1 PASSED: topology_hash={r1.topology_snapshot_hash[:16]}…")
                
                g2 = SemanticAudit()
                g2.verify()
                logger.info("Gate 2 PASSED: SemanticAudit")
                
                if not config.skip_drift_audit:
                    logger.info("Gate 3: DeterminismDriftAudit requires run_condition_fn — skipped in gates-only mode")
                else:
                    logger.info("Gate 3 skipped (skip_drift_audit=True)")
                
                g4 = ConditionEquivalenceContract()
                g4.verify()
                logger.info("Gate 4 PASSED: ConditionEquivalenceContract")
                
                logger.info("✅ Gates 1-2+4 PASSED (Gate 3 requires condition runner)")
                
                return {
                    "status": "success",
                    "message": "Contribution C gates evaluation completed successfully",
                    "run_id": eval_config.run_id,
                    "mode": config.mode,
                    "gate_results": {
                        "gate1_topology": "PASSED",
                        "gate2_semantic": "PASSED",
                        "gate3_drift": "SKIPPED",
                        "gate4_equivalence": "PASSED"
                    }
                }
            except GateFailure as gf:
                logger.error(f"❌ Gate failure: {gf}")
                raise HTTPException(status_code=500, detail=f"Gate failure: {str(gf)}")
        
        # Run full evaluation
        runner = UnifiedEvaluationRunner(eval_config)
        er = runner.run()
        
        if er.quarantine_triggered:
            logger.error(f"❌ Evidence quarantined: {er.quarantine_reason}")
            raise HTTPException(status_code=500, detail=f"Evidence quarantined: {er.quarantine_reason}")
        
        # Export artifacts
        exporter = ArtifactExporter(er)
        exporter.export_all()
        
        # Get legitimacy contract results
        legitimacy = None
        if er.legitimacy:
            legitimacy = {
                "evidence_tier": er.legitimacy.evidence_tier,
                "publishable": er.legitimacy.publishable,
                "validation_score": er.legitimacy.validation_score
            }
        
        logger.info(f"✅ Contribution C evaluation completed: {eval_config.run_id}")
        
        return {
            "status": "success",
            "message": "Contribution C evaluation completed successfully",
            "run_id": eval_config.run_id,
            "mode": config.mode,
            "config": {
                "policies": policies,
                "ablations": ablations,
                "archetypes": archetypes,
                "seeds": seeds,
                "interactions": config.interactions,
                "learners": config.learners,
                "concepts": config.concepts
            },
            "output_dir": eval_config.output_dir,
            "legitimacy": legitimacy,
            "artifact_count": len(er.artifacts) if hasattr(er, 'artifacts') else 0
        }
        
    except ImportError as e:
        logger.error(f"Contribution C evaluation not available: {e}")
        raise HTTPException(status_code=503, detail="Contribution C evaluation components not available")
    except Exception as e:
        logger.error(f"Failed to launch Contribution C evaluation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to launch evaluation: {str(e)}")

