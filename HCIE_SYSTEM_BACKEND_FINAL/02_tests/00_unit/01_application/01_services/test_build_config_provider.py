"""Unit test for `build_config_provider()`.

Two cases:

1. Explicit `settings=` arg → builds a pydantic adapter wrapped in the env
   overlay.
2. No args + BACKENDV2 not importable → falls back to a pure-env provider
   (no exception raised at boot).
"""

from __future__ import annotations

import sys
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
    s = SimpleNamespace(api_port=7777, debug=False)
    s.model_dump = lambda: {"api_port": s.api_port, "debug": s.debug}
    return s


def _purge_config_modules() -> dict:
    """Remove BACKENDV2 `config` modules from sys.modules so the factory's
    fallback path is exercised. Returns the snapshot so the fixture can
    restore them afterwards.
    """
    keys = [k for k in sys.modules if k == "config" or k.startswith("config.")]
    snapshot = {k: sys.modules.pop(k) for k in keys}
    return snapshot


class TestBuildConfigProvider:
    def test_explicit_settings_arg(self, cfg_module, fake_settings):
        p = cfg_module.build_config_provider(settings=fake_settings)
        # The overlay returns the base value when no env override is set
        # for the key (we don't manipulate os.environ here).
        if "API_PORT" not in __import__("os").environ:
            assert p.get_int("api_port") == 7777

    def test_fallback_when_backendv2_unavailable(self, cfg_module, monkeypatch):
        snapshot = _purge_config_modules()
        try:
            # Block the config import path
            import builtins

            real_import = builtins.__import__

            def _no_config(name, *a, **k):
                if name == "config.env" or name.startswith("config."):
                    raise ImportError("config blocked for test")
                return real_import(name, *a, **k)

            monkeypatch.setattr(builtins, "__import__", _no_config)

            p = cfg_module.build_config_provider()
            # Pure-env provider: known env vars are reachable through the
            # protocol; absent keys return the default.
            assert p.get_str("absolutely_does_not_exist", "fb") == "fb"
        finally:
            for k, v in snapshot.items():
                sys.modules[k] = v
