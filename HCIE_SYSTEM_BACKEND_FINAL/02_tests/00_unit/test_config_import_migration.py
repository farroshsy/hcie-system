"""Phase 7 config-import cleanup guard.

The `hcie/` shim makes canonical application imports possible, so migrated
FINAL code should no longer import the old BACKENDV2 global
`config.settings.settings` object directly. The composition root may still
import `config.env.load_settings()` as its backwards-compatible adapter.
"""

from __future__ import annotations

import ast
from pathlib import Path


FINAL_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = FINAL_ROOT / "01_source"


def test_no_direct_config_settings_imports_in_final_source() -> None:
    offenders = []

    for path in SOURCE_ROOT.rglob("*.py"):
        if any(part in {"_legacy", "__pycache__"} for part in path.parts):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "config.settings":
                offenders.append(path.relative_to(FINAL_ROOT).as_posix())
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "config.settings":
                        offenders.append(path.relative_to(FINAL_ROOT).as_posix())

    assert offenders == []
