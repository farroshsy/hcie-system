"""Legacy `config.env` adapter backed by FINAL settings schemas."""

from __future__ import annotations

import importlib.util
from pathlib import Path


_FINAL_ROOT = Path(__file__).resolve().parents[3]
_SETTINGS_FILE = _FINAL_ROOT / "04_config" / "00_schemas" / "settings.py"


def _load_settings():
    spec = importlib.util.spec_from_file_location("_hcie_final_settings", _SETTINGS_FILE)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load FINAL settings from {_SETTINGS_FILE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Settings()


settings = _load_settings()


def load_settings():
    return settings


def is_production_environment() -> bool:
    return str(getattr(settings, "environment", "")).lower() == "production"


def is_docker_environment() -> bool:
    return bool(getattr(settings, "docker_env", False)) or str(getattr(settings, "environment", "")).lower() == "docker"
