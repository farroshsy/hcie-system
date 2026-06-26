"""Sanity tests for `ConfigProviderProtocol`.

These tests exist alongside `check_protocols.py` -- the static AST check
verifies *structural* conformance; this file verifies that the protocol
is `runtime_checkable` and that every method it declares is implemented
by both application adapters.
"""

from __future__ import annotations

import pytest

from finals_loader import from_finals


@pytest.fixture(scope="module")
def ports():
    return from_finals("01_source/00_core/00_interfaces/09_config_ports.py")


@pytest.fixture(scope="module")
def cfg_module():
    return from_finals(
        "01_source/01_application/07_infrastructure/00_di/config_factory.py"
    )


PROTOCOL_METHODS = {"get", "get_int", "get_float", "get_bool", "get_str", "snapshot"}


class TestConfigProtocolSurface:
    def test_protocol_class_exists(self, ports):
        assert hasattr(ports, "ConfigProviderProtocol")

    def test_protocol_is_runtime_checkable(self, ports):
        # If the protocol is not runtime_checkable, isinstance() will raise.
        class _Stub:
            def get(self, k, d=None): return d
            def get_int(self, k, d=0): return d
            def get_float(self, k, d=0.0): return d
            def get_bool(self, k, d=False): return d
            def get_str(self, k, d=""): return d
            def snapshot(self): return {}

        assert isinstance(_Stub(), ports.ConfigProviderProtocol)

    def test_pydantic_adapter_has_protocol_methods(self, cfg_module):
        impl = cfg_module.PydanticSettingsConfigProvider(object())
        for m in PROTOCOL_METHODS:
            assert hasattr(impl, m), f"missing method: {m}"

    def test_env_overlay_has_protocol_methods(self, cfg_module):
        from types import SimpleNamespace
        base = SimpleNamespace(
            get=lambda k, d=None: d, get_int=lambda k, d=0: d,
            get_float=lambda k, d=0.0: d, get_bool=lambda k, d=False: d,
            get_str=lambda k, d="": d, snapshot=lambda: {},
        )
        impl = cfg_module.EnvOverlayConfigProvider(base, env={})
        for m in PROTOCOL_METHODS:
            assert hasattr(impl, m), f"missing method: {m}"
