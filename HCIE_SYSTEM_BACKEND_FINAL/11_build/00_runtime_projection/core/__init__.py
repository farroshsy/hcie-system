"""Synthetic legacy `core` package for FINAL runtime projection."""

from __future__ import annotations

from pathlib import Path

_FINAL_ROOT = Path(__file__).resolve().parents[3]
__path__ = [
    str(Path(__file__).resolve().parent),
    str(_FINAL_ROOT / "01_source" / "00_core"),
]
