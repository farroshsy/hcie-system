from app.runtime.composition import RuntimeRole, build_api_runtime
from app.main import app
from config.env import settings


def test_build_api_runtime_returns_correct_role():
    runtime = build_api_runtime(settings)
    assert runtime.unified_brain_runtime.role == RuntimeRole.API


def test_api_startup_code_includes_composition_root():
    # Verify the startup code wires the composition root. The legacy
    # @app.on_event('startup') `startup_event` was migrated to the FastAPI
    # `lifespan` context manager (main.py) — inspect that instead.
    import inspect
    from app.main import lifespan

    # @asynccontextmanager wraps the function; unwrap to read the real body.
    target = getattr(lifespan, "__wrapped__", lifespan)
    source = inspect.getsource(target)
    assert "build_api_runtime" in source
    assert "app.state.runtime" in source
