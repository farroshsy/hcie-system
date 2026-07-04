from fastapi import APIRouter
from app.api.v3.experiment_control_plane import (
    get_all_experiment_configs,
    get_experiment_config,
    create_experiment_run,
)
import uuid
import time

router = APIRouter(prefix="/research/experiments", tags=["experiments"])

# In-memory run state storage
_experiment_runs = {}


def _capability_manifest_fingerprint():
    try:
        from core.learning.unified_brain import get_latest_capability_manifest

        manifest = get_latest_capability_manifest()
        return manifest.get("fingerprint") if manifest else None
    except Exception:
        return None


@router.get("")
async def list_experiments():
    """List all experiment configurations"""
    configs = get_all_experiment_configs()
    return {"configs": configs}


@router.get("/{config_id}")
async def get_experiment(config_id: str):
    """Get specific experiment configuration"""
    config = get_experiment_config(config_id)
    return {"config": config}


@router.post("")
async def create_experiment(config_id: str):
    """Create new experiment run"""
    from app.api.v3.experiment_control_plane import get_experiment_config
    config = get_experiment_config(config_id)
    run = create_experiment_run(config)

    # Store run state
    run_id = str(uuid.uuid4())
    _experiment_runs[run_id] = {
        "run_id": run_id,
        "config_id": config_id,
        "status": "running",
        "created_at": time.time(),
        "updated_at": time.time(),
        "config": config,
        "capability_manifest_fingerprint": _capability_manifest_fingerprint(),
    }

    return {"run": _experiment_runs[run_id]}


@router.get("/runs/{run_id}")
async def get_experiment_run(run_id: str):
    """Get specific experiment run status"""
    if run_id not in _experiment_runs:
        return {"error": "Run not found", "run_id": run_id}
    return _experiment_runs[run_id]


@router.post("/runs/{run_id}/stop")
async def stop_experiment_run(run_id: str):
    """Stop an experiment run"""
    if run_id not in _experiment_runs:
        return {"error": "Run not found", "run_id": run_id}

    _experiment_runs[run_id]["status"] = "stopped"
    _experiment_runs[run_id]["updated_at"] = time.time()
    return _experiment_runs[run_id]
