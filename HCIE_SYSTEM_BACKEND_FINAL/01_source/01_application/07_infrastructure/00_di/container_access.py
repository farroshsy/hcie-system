"""Process-wide access to the Phase 14 ``00_di`` composition root."""

from __future__ import annotations

import os
import threading
from typing import Optional

from .container import Container

_CONTAINER: Optional[Container] = None
_LOCK = threading.RLock()


def get_container() -> Container:
    """Return the process-local Container singleton.

    Tests may inject a container via ``HCIE_CONTAINER_OVERRIDE=reset`` or by
    calling ``set_container`` directly.
    """
    global _CONTAINER
    with _LOCK:
        if os.environ.get("HCIE_CONTAINER_OVERRIDE") == "reset":
            _CONTAINER = None
            os.environ.pop("HCIE_CONTAINER_OVERRIDE", None)
        if _CONTAINER is None:
            _CONTAINER = Container()
        return _CONTAINER


def set_container(container: Optional[Container]) -> None:
    """Replace or clear the global container (tests)."""
    global _CONTAINER
    with _LOCK:
        _CONTAINER = container
