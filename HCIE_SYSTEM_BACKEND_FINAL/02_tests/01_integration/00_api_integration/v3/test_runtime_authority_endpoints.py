import inspect


def test_runtime_authority_endpoints_exist():
    """Verify runtime authority endpoints are defined"""
    from app.api.v3.runtime.authority import router
    # Verify router exists
    assert router is not None
    # Verify router has the authority endpoints
    routes = [route.path for route in router.routes]
    assert "/runtime/authority/state/{api_name}" in routes
    assert "/runtime/authority/all" in routes
