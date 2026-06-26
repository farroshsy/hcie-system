#!/usr/bin/env python3
"""Generate import_map.json from sitecustomize.PACKAGE_ROOTS.

The runtime projection (sitecustomize.py) maps clean import names (e.g. ``core.learning``)
onto the numbered FINAL tree (e.g. ``01_source/00_core/03_ensemble``). That is great for
Python at runtime but defeats grep / IDE "go to definition" / static analysis, because the
mapping only exists as an import hook.

This script regenerates a *static* navigation map — clean import name -> the ordered list
of physical directories it resolves to (relative to the backend root) — so humans, IDEs,
and grep can follow imports without executing Python. It is generated FROM PACKAGE_ROOTS
(never hand-maintained) so it cannot silently drift; re-run it whenever the resolver changes.

See 00_documentation/09_adr/ARCHITECTURE_DECISIONS.md (ADR-1).

Usage:  python gen_import_map.py
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND_ROOT = HERE.parents[1]  # .../HCIE_SYSTEM_BACKEND_FINAL


def _load_package_roots() -> dict:
    spec = importlib.util.spec_from_file_location("_proj_sitecustomize", HERE / "sitecustomize.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # one-off process; the meta-path install is harmless here
    return mod.PACKAGE_ROOTS


def main() -> None:
    roots = _load_package_roots()
    out: dict = {
        "_README": (
            "Clean import name -> ordered list of physical dirs it resolves to (relative to "
            "HCIE_SYSTEM_BACKEND_FINAL). GENERATED from sitecustomize.PACKAGE_ROOTS by "
            "gen_import_map.py — do not edit by hand. See 00_documentation/09_adr/ARCHITECTURE_DECISIONS.md (ADR-1)."
        ),
    }
    for name, paths in sorted(roots.items()):
        entries = []
        for p in paths:
            p = Path(p)
            try:
                rel = p.resolve().relative_to(BACKEND_ROOT).as_posix()
            except ValueError:
                rel = p.as_posix()
            entries.append({"path": rel, "exists": p.is_dir()})
        out[name] = entries
    (HERE / "import_map.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"wrote import_map.json: {len(roots)} package roots")


if __name__ == "__main__":
    main()
