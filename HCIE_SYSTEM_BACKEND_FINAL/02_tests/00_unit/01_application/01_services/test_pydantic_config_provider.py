"""Unit test for `PydanticSettingsConfigProvider`.

Exercises the typed-accessor surface against a fake Settings object that
mimics the BACKENDV2 `pydantic-settings` `Settings` shape.
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
def fake_settings():
    obj = SimpleNamespace(
        debug=True,
        api_port=8000,
        api_host="0.0.0.0",
        request_timeout=30.0,
        analytics_enabled=False,
        secret_key="dev-key",
        cache_ttl_seconds=3600,
    )
    obj.model_dump = lambda: {
        "debug": obj.debug,
        "api_port": obj.api_port,
        "api_host": obj.api_host,
        "request_timeout": obj.request_timeout,
        "analytics_enabled": obj.analytics_enabled,
        "secret_key": obj.secret_key,
        "cache_ttl_seconds": obj.cache_ttl_seconds,
    }
    return obj


class TestPydanticSettingsConfigProvider:
    def test_get_returns_value(self, cfg_module, fake_settings):
        p = cfg_module.PydanticSettingsConfigProvider(fake_settings)
        assert p.get("api_host") == "0.0.0.0"

    def test_get_returns_default_when_missing(self, cfg_module, fake_settings):
        p = cfg_module.PydanticSettingsConfigProvider(fake_settings)
        assert p.get("nonexistent", "fallback") == "fallback"

    def test_case_insensitive_lookup(self, cfg_module, fake_settings):
        p = cfg_module.PydanticSettingsConfigProvider(fake_settings)
        assert p.get_str("API_HOST") == "0.0.0.0"
        assert p.get_str("Api_Host") == "0.0.0.0"

    def test_typed_accessors(self, cfg_module, fake_settings):
        p = cfg_module.PydanticSettingsConfigProvider(fake_settings)
        assert p.get_int("api_port") == 8000
        assert p.get_float("request_timeout") == 30.0
        assert p.get_bool("debug") is True
        assert p.get_bool("analytics_enabled") is False
        assert p.get_str("secret_key") == "dev-key"

    def test_typed_accessors_fall_back_on_missing(self, cfg_module, fake_settings):
        p = cfg_module.PydanticSettingsConfigProvider(fake_settings)
        assert p.get_int("missing", 42) == 42
        assert p.get_float("missing", 1.5) == 1.5
        assert p.get_bool("missing", True) is True
        assert p.get_str("missing", "fb") == "fb"

    def test_snapshot_uses_model_dump(self, cfg_module, fake_settings):
        p = cfg_module.PydanticSettingsConfigProvider(fake_settings)
        snap = p.snapshot()
        assert snap["api_port"] == 8000
        assert snap["debug"] is True
        # Mutating the snapshot must not affect the provider.
        snap["api_port"] = 0
        assert p.get_int("api_port") == 8000


class TestConfigProviderProtocolConformance:
    def test_runtime_checkable_against_pydantic_adapter(self, cfg_module, fake_settings):
        ports = from_finals("01_source/00_core/00_interfaces/09_config_ports.py")
        p = cfg_module.PydanticSettingsConfigProvider(fake_settings)
        assert isinstance(p, ports.ConfigProviderProtocol)

    def test_runtime_checkable_against_env_overlay(self, cfg_module, fake_settings):
        ports = from_finals("01_source/00_core/00_interfaces/09_config_ports.py")
        base = cfg_module.PydanticSettingsConfigProvider(fake_settings)
        env = cfg_module.EnvOverlayConfigProvider(base, env={})
        assert isinstance(env, ports.ConfigProviderProtocol)
