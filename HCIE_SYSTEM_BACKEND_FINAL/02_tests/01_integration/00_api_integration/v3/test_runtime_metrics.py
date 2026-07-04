import inspect


def test_runtime_metrics_endpoints_exist():
    """Verify runtime metrics endpoints are defined"""
    from app.api.v3.runtime.lifecycle import router
    # Verify router exists
    assert router is not None
    # Verify router has metrics endpoints
    routes = [route.path for route in router.routes]
    # Metrics endpoint should exist
    assert "/runtime/lifecycle/metrics" in routes


def test_runtime_metrics_returns_prometheus_format():
    """Verify runtime metrics endpoint returns Prometheus format"""
    from prometheus_client import CONTENT_TYPE_LATEST
    from app.api.v3.runtime.lifecycle import runtime_metrics
    import asyncio
    # Call the endpoint (async function)
    response = asyncio.run(runtime_metrics())
    # Verify it returns Response object with correct content type
    assert response.media_type == CONTENT_TYPE_LATEST
