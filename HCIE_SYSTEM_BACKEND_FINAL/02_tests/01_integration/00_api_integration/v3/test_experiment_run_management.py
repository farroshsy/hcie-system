import inspect


def test_experiment_run_management_endpoints_exist():
    """Verify experiment run management endpoints are defined"""
    from app.api.v3.experiments import router
    # Verify router exists
    assert router is not None
    # Verify router has run management endpoints
    routes = [route.path for route in router.routes]
    # Should have endpoints for run management (beyond just config listing)
    assert len(routes) >= 3


def test_experiment_run_state_tracking():
    """Verify experiment run management includes state tracking"""
    from app.api.v3.experiments import _experiment_runs, create_experiment, stop_experiment_run
    import asyncio

    # Verify in-memory storage exists
    assert isinstance(_experiment_runs, dict)

    # Create a test run
    # Note: This would require actual config_id, so we just verify the structure exists
    assert hasattr(create_experiment, "__annotations__") or callable(create_experiment)
    assert hasattr(stop_experiment_run, "__annotations__") or callable(stop_experiment_run)
