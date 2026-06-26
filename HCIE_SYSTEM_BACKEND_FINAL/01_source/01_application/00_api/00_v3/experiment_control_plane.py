from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List
from enum import Enum


class ExperimentStatus(str, Enum):
    INITIALIZED = "initialized"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ExperimentConfig:
    config_id: str
    version: str
    enabled: bool
    parameters: Dict[str, Any]
    description: str = ""
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ExperimentRun:
    run_id: str
    config_id: str
    status: ExperimentStatus
    start_time: datetime
    end_time: datetime = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    results: Dict[str, Any] = field(default_factory=dict)
    error_message: str = ""


# Predefined experiment configurations (V1 skeleton)
_EXPERIMENT_CONFIGS: Dict[str, ExperimentConfig] = {
    "epsilon_sweep_v1": ExperimentConfig(
        config_id="epsilon_sweep_v1",
        version="1.0",
        enabled=True,
        parameters={
            "epsilon_values": [0.0, 0.1, 0.2, 0.3, 0.4, 0.5],
            "num_users": 1000,
            "num_interactions": 10000,
        },
        description="Epsilon-greedy parameter sweep",
        tags=["bandit", "exploration"],
    ),
    "jt_weight_ablation_v1": ExperimentConfig(
        config_id="jt_weight_ablation_v1",
        version="1.0",
        enabled=True,
        parameters={
            "weight_configs": [
                {"mastery_gain": 1.0, "transfer": 0.0},
                {"mastery_gain": 0.7, "transfer": 0.3},
                {"mastery_gain": 0.5, "transfer": 0.5},
            ],
            "num_users": 500,
            "num_interactions": 5000,
        },
        description="JT governance weight ablation",
        tags=["governance", "ablation"],
    ),
}


def get_all_experiment_configs() -> List[ExperimentConfig]:
    """Get all available experiment configurations."""
    return list(_EXPERIMENT_CONFIGS.values())


def get_experiment_config(config_id: str) -> ExperimentConfig:
    """Get a specific experiment configuration by ID."""
    if config_id not in _EXPERIMENT_CONFIGS:
        raise ValueError(f"Experiment config not found: {config_id}")
    return _EXPERIMENT_CONFIGS[config_id]


def create_experiment_run(config: ExperimentConfig) -> ExperimentRun:
    """Create a new experiment run from a configuration."""
    run_id = f"run_{config.config_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    return ExperimentRun(
        run_id=run_id,
        config_id=config.config_id,
        status=ExperimentStatus.INITIALIZED,
        start_time=datetime.utcnow(),
        parameters=config.parameters.copy(),
    )
