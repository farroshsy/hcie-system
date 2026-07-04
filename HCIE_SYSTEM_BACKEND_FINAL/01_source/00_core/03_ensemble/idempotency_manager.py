"""Bridge module — re-exports the CANONICAL IdempotencyManager.

NOT a stub. It loads the real 510-line implementation from
``core/09_validation/idempotency_manager.py`` and re-exports its ``IdempotencyManager`` so that
ensemble-relative imports (``from .idempotency_manager import IdempotencyManager`` in
``unified_brain.py``) resolve to the *same* canonical class used everywhere else
(``core.validation.idempotency_manager``). There is no shadowing: this delegates, it does not
reimplement.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_SOURCE = Path(__file__).resolve().parent.parent / "09_validation" / "idempotency_manager.py"
_spec = importlib.util.spec_from_file_location("_hcie_ensemble_idempotency", _SOURCE)
if _spec is None or _spec.loader is None:
    raise ImportError(f"unable to load idempotency manager from {_SOURCE}")

_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

IdempotencyManager = _module.IdempotencyManager

__all__ = ["IdempotencyManager"]
