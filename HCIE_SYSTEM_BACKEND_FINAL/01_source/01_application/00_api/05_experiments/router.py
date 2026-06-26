"""
Experiments API Router - Research experiment management
"""

from fastapi import APIRouter
from .endpoints import experiments, results

router = APIRouter(prefix="/experiments", tags=["experiments"])

# Mount experiment endpoints
router.include_router(experiments.router)
router.include_router(results.router)

# =============================================================================
# PHASE 1-6 EXPERIMENT ENDPOINTS - Real Runtime Integration
# NOTE: Experiment endpoints are now in app/api/experiments/endpoints/experiments.py
# This router includes the endpoints router for those definitions.
# =============================================================================

try:
    from experiments.phase1_experiment_2a_stochastic_cognition_divergence import Experiment2A, Experiment2AConfig
    from experiments.phase2_experiment_1a_cold_start_baselines import Experiment1A, Experiment1AConfig
    from experiments.phase2_experiment_1b_early_learning_curves import Experiment1B, Experiment1BConfig
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
    EXPERIMENTS_AVAILABLE = False

import numpy as np

def convert_numpy_types(obj):
    """Convert numpy types to Python types for JSON serialization"""
    if isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_types(item) for item in obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (bool, int, float, str)):
        return obj
    elif obj is None:
        return None
    elif hasattr(obj, '__dict__'):
        # Handle objects with __dict__ attribute
        return convert_numpy_types(obj.__dict__)
    else:
        # Try to convert any other type to string
        try:
            return str(obj)
        except:
            return None

if EXPERIMENTS_AVAILABLE:
    @router.post("/phase1/2a/launch")
    async def launch_phase1_experiment_2a(
        num_runs: int = 5,
        num_learners: int = 20,
        num_concepts: int = 30,
        num_interactions: int = 100,
        seed: int = 42,
        learner_archetype: str = "novice"
    ):
        """Launch PHASE 1 Experiment 2A: Stochastic Cognition Divergence"""
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

    # NOTE: PHASE 4 Experiment 3A endpoint is now in app/api/experiments/endpoints/experiments.py
    # This router includes the endpoints router which provides the correct implementation
