import inspect


def test_runtime_service_discovery_endpoints_exist():
    """Verify runtime service discovery endpoints are defined"""
    from app.api.v3.runtime.authority import router
    # Verify router exists
    assert router is not None
    # Verify router has service discovery endpoints
    routes = [route.path for route in router.routes]
    # Should have endpoints for service discovery
    assert len(routes) >= 2


def test_runtime_service_discovery_includes_health():
    """Verify runtime service discovery includes health status"""
    from app.api.v3.runtime.authority import get_runtime_services
    import asyncio

    # Call the endpoint (async function)
    response = asyncio.run(get_runtime_services())
    # Verify it returns health information
    assert "services" in response
    assert "total_count" in response
    assert "healthy_count" in response
    # Verify each service has health status
    for service in response["services"]:
        assert "name" in service
        assert "status" in service
        assert "last_checked" in service
