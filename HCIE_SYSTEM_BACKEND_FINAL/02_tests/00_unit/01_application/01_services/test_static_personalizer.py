"""Unit test for the `StaticColdStartPersonalizer` adapter.

The adapter performs a deferred import of
`core.mastery.cold_start_optimizer.ColdStartOptimizer`
so we can substitute a stub via `sys.modules` without booting the
BACKENDV2 app stack.

Phase 14e audit slice relocated cold_start_optimizer from
`app.services.user_profiling.*` to `core.mastery.*` (prior estimation is
core math, not a service). The stub install paths follow the new home.
"""

from __future__ import annotations

import sys
import types

import pytest

from finals_loader import from_finals


@pytest.fixture
def personalizer_module():
    return from_finals(
        "01_source/01_application/07_infrastructure/00_di/personalizer.py"
    )


def _install_stub_cold_start(returns: float = 0.42) -> dict:
    """Install a stub `ColdStartOptimizer` in sys.modules.

    Returns the captured calls list so assertions can verify the adapter
    forwarded arguments correctly.
    """
    captured: dict = {"calls": []}

    class _StubColdStartOptimizer:
        @staticmethod
        def get_personalized_mastery(user_id, concept, user_profile=None):
            captured["calls"].append((user_id, concept, user_profile))
            return returns

    core_pkg = types.ModuleType("core")
    mastery_pkg = types.ModuleType("core.mastery")
    cold_start = types.ModuleType("core.mastery.cold_start_optimizer")
    cold_start.ColdStartOptimizer = _StubColdStartOptimizer

    sys.modules["core"] = core_pkg
    sys.modules["core.mastery"] = mastery_pkg
    sys.modules["core.mastery.cold_start_optimizer"] = cold_start
    return captured


@pytest.fixture
def captured_calls():
    snapshot = {k: sys.modules.get(k) for k in [
        "core",
        "core.mastery",
        "core.mastery.cold_start_optimizer",
    ]}
    captured = _install_stub_cold_start(returns=0.42)
    yield captured
    for k, v in snapshot.items():
        if v is None:
            sys.modules.pop(k, None)
        else:
            sys.modules[k] = v


class TestStaticColdStartPersonalizer:
    def test_build_returns_instance(self, personalizer_module):
        p = personalizer_module.build_personalizer()
        assert isinstance(p, personalizer_module.StaticColdStartPersonalizer)

    def test_forwards_arguments(self, personalizer_module, captured_calls):
        p = personalizer_module.build_personalizer()
        value = p.get_personalized_mastery("user-1", "concept-A", user_profile={"x": 1})
        assert value == 0.42
        assert captured_calls["calls"] == [("user-1", "concept-A", {"x": 1})]

    def test_user_profile_defaults_to_none(self, personalizer_module, captured_calls):
        p = personalizer_module.build_personalizer()
        p.get_personalized_mastery("user-2", "concept-B")
        assert captured_calls["calls"][-1] == ("user-2", "concept-B", None)
