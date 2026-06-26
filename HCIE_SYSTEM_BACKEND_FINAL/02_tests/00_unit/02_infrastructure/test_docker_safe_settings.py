from app.infrastructure.v3.v3_client import resolve_v3_base_url
from config.env import settings


def test_docker_safe_url_resolution():
    """Verify Docker-safe URL resolution works with settings"""
    url = resolve_v3_base_url(settings)
    assert url is not None
    assert url.startswith("http://")


def test_settings_has_docker_env_flag():
    """Verify settings has docker_env flag for Docker detection"""
    assert hasattr(settings, "docker_env") or hasattr(settings, "DOCKER_ENV")
