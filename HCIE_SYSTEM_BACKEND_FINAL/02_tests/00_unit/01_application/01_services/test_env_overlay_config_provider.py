"""Unit test for `EnvOverlayConfigProvider`.

Verifies that env vars beat the base provider, that case-insensitive
lookup works, and that snapshot merging gives precedence to the overlay.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from finals_loader import from_finals


@pytest.fixture(scope="module")
def cfg_module():
    return from_finals(
        "01_source/01_application/07_infrastructure/00_di/config_factory.py"
    )


@pytest.fixture
def base_provider(cfg_module):
    settings = SimpleNamespace(api_port=8000, debug=False, log_level="INFO")
    settings.model_dump = lambda: {
        "api_port": settings.api_port,
        "debug": settings.debug,
        "log_level": settings.log_level,
    }
    return cfg_module.PydanticSettingsConfigProvider(settings)


class TestEnvOverlayConfigProvider:
    def test_env_overrides_base(self, cfg_module, base_provider):
        env = {"API_PORT": "9000"}
        p = cfg_module.EnvOverlayConfigProvider(base_provider, env=env)
        assert p.get_int("api_port") == 9000

    def test_base_used_when_env_absent(self, cfg_module, base_provider):
        p = cfg_module.EnvOverlayConfigProvider(base_provider, env={})
        assert p.get_int("api_port") == 8000

    def test_bool_overlay_truthy_strings(self, cfg_module, base_provider):
        for v in ("1", "true", "TRUE", "yes", "on", "y", "t"):
            p = cfg_module.EnvOverlayConfigProvider(base_provider, env={"DEBUG": v})
            assert p.get_bool("debug") is True

    def test_bool_overlay_falsy_strings(self, cfg_module, base_provider):
        for v in ("0", "false", "no", "off"):
            p = cfg_module.EnvOverlayConfigProvider(base_provider, env={"DEBUG": v})
            assert p.get_bool("debug") is False

    def test_overlay_falls_through_to_base_on_unknown_value(
        self, cfg_module, base_provider
    ):
        p = cfg_module.EnvOverlayConfigProvider(base_provider, env={"DEBUG": "?"})
        assert p.get_bool("debug", default=True) is True  # coercion default wins

    def test_get_str_returns_env_verbatim(self, cfg_module, base_provider):
        env = {"LOG_LEVEL": "DEBUG"}
        p = cfg_module.EnvOverlayConfigProvider(base_provider, env=env)
        assert p.get_str("log_level") == "DEBUG"

    def test_get_falls_back_to_default_when_neither_set(
        self, cfg_module, base_provider
    ):
        p = cfg_module.EnvOverlayConfigProvider(base_provider, env={})
        assert p.get("absent", "fb") == "fb"

    def test_snapshot_merges_with_env_precedence(self, cfg_module, base_provider):
        env = {"API_PORT": "9000", "EXTRA": "x"}
        p = cfg_module.EnvOverlayConfigProvider(base_provider, env=env)
        snap = p.snapshot()
        assert snap["API_PORT"] == "9000"  # overlay wins
        assert snap["EXTRA"] == "x"
        # base keys still present
        assert "log_level" in snap
