"""Phase 8 retirement-readiness guard.

The current FINAL tree is intentionally NOT_READY for cutover because
several application/infrastructure buckets are still mirrored from
BACKENDV2 via sys.path rather than copied. This test asserts the tool
runs to completion against the live inventory, produces both report
files, and returns the verdict the operator should be looking at.

If the verdict ever becomes READY this test simply notices and passes
(via the explicit set of accepted verdicts). The point is to detect
regressions in the tool itself, not to gate the migration.
"""

from __future__ import annotations

import pytest as _pt_skip
_pt_skip.skip(
    "tools/migrate/check_retirement.py was removed in 398cbeb8 (one-off migration tooling); targets retired code.",
    allow_module_level=True,
)


import importlib
import sys
from pathlib import Path

import pytest


FINAL_ROOT = Path(__file__).resolve().parents[2]
TOOLS_MIGRATE = FINAL_ROOT / "tools" / "migrate"


@pytest.fixture(scope="module", autouse=True)
def _ensure_tools_on_path():
    p = str(TOOLS_MIGRATE)
    if p not in sys.path:
        sys.path.insert(0, p)
    yield


def test_check_retirement_runs_and_emits_reports():
    check_retirement = importlib.import_module("check_retirement")
    verdict, buckets, per_top = check_retirement.run(top_n_missing=10)

    assert verdict in {"READY", "PARTIAL", "NOT_READY"}, (
        f"unexpected verdict {verdict!r}"
    )

    # CRITICAL bucket must exist and report a sane percentage.
    crit = buckets["CRITICAL"]
    assert crit.total > 0
    assert 0.0 <= crit.percentage() <= 100.0

    # Report files were written.
    assert check_retirement.REPORT_CSV.exists()
    assert check_retirement.REPORT_MD.exists()
    md_text = check_retirement.REPORT_MD.read_text(encoding="utf-8")
    assert "BACKENDV2 Retirement Readiness" in md_text
    assert verdict in md_text


def test_check_retirement_main_exit_codes():
    check_retirement = importlib.import_module("check_retirement")
    rc = check_retirement.main(["--quiet"])
    assert rc in (0, 1, 2)
