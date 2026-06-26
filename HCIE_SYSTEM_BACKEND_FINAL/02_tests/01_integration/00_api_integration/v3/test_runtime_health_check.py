import inspect


def test_runtime_health_check_endpoints_exist():
    """Verify runtime health check endpoints are defined"""
    from app.api.v3.runtime.lifecycle import router
    # Verify router exists
    assert router is not None
    # Verify router has health check endpoints
    routes = [route.path for route in router.routes]
    assert "/runtime/lifecycle/health" in routes


def test_runtime_health_check_includes_dependency_checks():
    """Verify runtime health check includes dependency checks"""
    from app.api.v3.runtime.lifecycle import runtime_health_check
    import asyncio
    # Call the endpoint (async function)
    response = asyncio.run(runtime_health_check())
    # Verify it returns a dict with checks
    assert isinstance(response, dict)
    assert "status" in response
    assert "checks" in response
    assert "postgres" in response["checks"]
    assert "redis" in response["checks"]
    assert "runtime" in response["checks"]
