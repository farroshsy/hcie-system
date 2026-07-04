"""Load numbered-FINAL modules into Python without renaming anything.

The FINAL tree organises code under directories like
`01_source/00_core/02_state/interaction_keys.py`. Python's `import`
syntax rejects identifiers starting with a digit, so a plain
`from 00_core.02_state.interaction_keys import ...` is a SyntaxError.

This loader uses `importlib.util.spec_from_file_location` to register
the file as a module under any name we choose. It is the substrate for
Phase 4 contract tests; it will be superseded by the Phase 6 `hcie/`
shim package once that lands.

Public surface:

    from finals_loader import from_finals
    mod = from_finals("01_source/00_core/02_state/interaction_keys.py")
    mod.interaction_is_correct({"score": 0.9})
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Dict, Optional

_FINAL_ROOT = Path(__file__).resolve().parents[2]
_LOADED: Dict[str, ModuleType] = {}


def _module_name_for(rel_path: str) -> str:
    safe = rel_path.replace("/", ".").replace("\\", ".").replace(".py", "")
    return f"finals.{safe}"


def from_finals(rel_path: str, *, module_name: Optional[str] = None) -> ModuleType:
    """Return the module at `<FINAL_ROOT>/<rel_path>`.

    The same `rel_path` always returns the same module instance (cached
    in `sys.modules`).
    """
    abs_path = (_FINAL_ROOT / rel_path).resolve()
    if not abs_path.is_file():
        raise FileNotFoundError(f"finals_loader: no such file: {abs_path}")

    name = module_name or _module_name_for(rel_path)
    if name in _LOADED:
        return _LOADED[name]
    if name in sys.modules:
        return sys.modules[name]

    spec = importlib.util.spec_from_file_location(name, abs_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"finals_loader: cannot build spec for {abs_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    _LOADED[name] = module
    return module


def final_root() -> Path:
    return _FINAL_ROOT
