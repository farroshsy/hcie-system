import inspect


def test_experiment_endpoints_exist():
    """Verify experiment control plane endpoints are defined"""
    from app.api.v3.experiments import router
    # Verify router exists
    assert router is not None
    # Verify router has routes
    assert len(router.routes) > 0
