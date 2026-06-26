"""Pytest wrapper around `tools/migrate/check_protocols.py`.

Re-runs the static structural check at test time so CI flags any
protocol-implementation drift the moment a regression lands.
"""

from __future__ import annotations

import pytest as _pt_skip
_pt_skip.skip(
    "tools/migrate/check_*.py linters were removed in 398cbeb8 (one-off migration tooling); these target retired code.",
    allow_module_level=True,
)


import sys
from pathlib import Path

import pytest


_THIS = Path(__file__).resolve()
FINAL_ROOT = _THIS.parents[3]
TOOLS_MIGRATE = FINAL_ROOT / "tools" / "migrate"


@pytest.fixture(scope="module", autouse=True)
def _ensure_tools_on_path():
    p = str(TOOLS_MIGRATE)
    if p not in sys.path:
        sys.path.insert(0, p)
    yield


def test_check_protocols_passes():
    import importlib

    check_protocols = importlib.import_module("check_protocols")
    rc = check_protocols.main([])
    assert rc == 0, "check_protocols.main() returned non-zero -- see captured stdout"


def test_check_di_passes():
    import importlib

    check_di = importlib.import_module("check_di")
    rc = check_di.main([])
    assert rc == 0, "check_di.main() returned non-zero -- see captured stdout"


def test_check_layers_strict_passes():
    import importlib

    check_layers = importlib.import_module("check_layers")
    rc = check_layers.main(["--strict"])
    assert rc == 0, "check_layers --strict returned non-zero"


def test_check_shim_static_passes():
    """Static check on the generated `hcie/` shim package.

    Runtime smoke (`--exec`) is intentionally NOT run here because the
    BACKENDV2 import-time side effects (Prometheus default-registry
    double-registration, etc.) make it unsafe inside pytest. The static
    check is sufficient to catch shim drift.
    """
    import importlib

    check_shim = importlib.import_module("check_shim")
    rc = check_shim.main([])
    assert rc == 0, "check_shim returned non-zero -- see captured stdout"


def test_check_retirement_runs_to_completion():
    """Phase 8 retirement-readiness check.

    The verdict is informational, not a gate -- the test only requires
    that the tool runs to completion against the live inventory. The
    operator decides what to do with NOT_READY / PARTIAL / READY.
    """
    import importlib

    check_retirement = importlib.import_module("check_retirement")
    rc = check_retirement.main(["--quiet"])
    assert rc in (0, 1, 2), f"unexpected exit code {rc}"
