"""Runtime projection for booting the numbered FINAL tree.

Python imports this module automatically when this directory is on
`PYTHONPATH`. It registers legacy package names used by the carried-over
application body (`app`, `core.learning`, `storage`, `messaging`, etc.)
against the numbered FINAL layout without copying source files.

NAVIGATION: this mapping is invisible to grep / IDE "go to definition". The static
clean-name -> physical-dir lookup is `import_map.json` in this directory (generated
from PACKAGE_ROOTS below by `gen_import_map.py`; re-run it after changing PACKAGE_ROOTS).
Rationale + trade-off: 00_documentation/09_adr/ARCHITECTURE_DECISIONS.md (ADR-1).
"""

from __future__ import annotations

import importlib.abc
import importlib.util
import re
import sys
from pathlib import Path
from types import ModuleType
from typing import Dict, Iterable, List, Optional


_NUMERIC_PREFIX = re.compile(r"^\d+_")
_PROJECTION_ROOT = Path(__file__).resolve().parent
_FINAL_ROOT = _PROJECTION_ROOT.parents[1]


def _p(*parts: str) -> Path:
    return _FINAL_ROOT.joinpath(*parts)


PACKAGE_ROOTS: Dict[str, List[Path]] = {
    "app": [_PROJECTION_ROOT / "app", _p("01_source", "01_application")],
    "app.api": [_PROJECTION_ROOT / "app" / "api", _p("01_source", "01_application", "00_api")],
    "app.services": [_p("01_source", "01_application", "01_services")],
    "app.domains": [_p("01_source", "01_application", "02_domains")],
    "app.repositories": [_p("01_source", "01_application", "03_repositories")],
    "app.workers": [_p("01_source", "01_application", "04_workers")],
    "app.middleware": [_p("01_source", "01_application", "05_middleware")],
    "app.models": [_p("01_source", "01_application", "06_models")],
    "app.infrastructure": [_p("01_source", "01_application", "07_infrastructure")],
    # Phase 14e correction: `app.infrastructure.di.*` must resolve to BOTH
    # `00_di/` (canonical Container, container_access, factories) and `di/`
    # (legacy `dependency_injection.py`, `get_container.py` bridge). Previously
    # the same lookups went via the now-deleted `hcie/` shim, which mapped to
    # `00_di/`. This mapping replaces that path without reintroducing `hcie/`.
    "app.infrastructure.di": [
        _p("01_source", "01_application", "07_infrastructure", "00_di"),
        _p("01_source", "01_application", "07_infrastructure", "di"),
    ],
    "app.infrastructure.monitoring": [_p("01_source", "02_infrastructure", "03_monitoring")],
    "app.telemetry": [_PROJECTION_ROOT / "app" / "telemetry", _p("01_source", "01_application", "08_telemetry")],
    "app.runtime": [_p("01_source", "01_application", "09_runtime")],
    "app.utils": [_p("01_source", "01_application", "10_utils")],
    "config": [_PROJECTION_ROOT / "config", _p("04_config", "00_schemas")],
    "storage": [_p("01_source", "02_infrastructure", "01_storage")],
    "messaging": [_p("01_source", "02_infrastructure", "00_messaging")],
    "infrastructure": [_p("01_source", "02_infrastructure")],
    "infrastructure.experiment": [_p("01_source", "02_infrastructure", "02_experiment")],
    "core": [_PROJECTION_ROOT / "core", _p("01_source", "00_core")],
    "core.learning": [
        _p("01_source", "00_core", "03_ensemble"),
        _p("01_source", "00_core", "09_validation"),
        _p("01_source", "00_core", "04_learners"),
        _p("01_source", "00_core", "06_transfer"),
        _p("01_source", "00_core", "08_research"),
        _p("01_source", "00_core", "01_governance"),
        _p("01_source", "00_core", "02_state"),
        _p("01_source", "00_core", "13_reward"),  # was 06_reward (absent); real reward code is 13_reward
        _p("01_source", "00_core", "10_curriculum"),
        _p("01_source", "00_core", "14_projection"),
    ],
    "core.bandit": [_p("01_source", "00_core", "07_bandit")],
    "core.reward": [_p("01_source", "00_core", "13_reward")],  # 3 live importers (from core.reward.reward)
    "core.determinism": [_p("01_source", "00_core", "11_determinism")],
    # Back-compat alias: the determinism/replay analysis modules (semantic_drift,
    # longitudinal_reconstruction, counterfactual_replay, deterministic_replay_engine)
    # were authored under the old `core.replay` name and still import each other that
    # way internally. The dir is now 11_determinism. This alias keeps both the source
    # modules and their tests importable without editing the (replay-path-adjacent)
    # source. Pure name aliasing — behaviour-preserving, does not touch any seal number.
    "core.replay": [_p("01_source", "00_core", "11_determinism")],
    "core.mapping": [_p("01_source", "00_core", "10_curriculum")],
    "core.projection": [_p("01_source", "00_core", "14_projection")],
    "core.session": [_p("01_source", "00_core", "18_session")],
    "core.ownership": [_p("01_source", "00_core", "02_state")],
    "core.telemetry": [_p("01_source", "01_application", "08_telemetry")],
    # Clean-name for the messaging schema package (schema_validator, validate_learning_event).
    # Live code does `from schema.schema_validator import ...` (previously only inside try/except);
    # this maps it to the real numbered dir so the import resolves first-class. Pure aliasing.
    "schema": [_p("01_source", "02_infrastructure", "00_messaging", "02_schema")],
}


def _canonical(name: str) -> str:
    return _NUMERIC_PREFIX.sub("", name)


def _iter_dirs(package: str) -> Iterable[Path]:
    for path in PACKAGE_ROOTS.get(package, []):
        if path.is_dir():
            yield path


class _SyntheticPackageLoader(importlib.abc.Loader):
    def create_module(self, spec):
        return ModuleType(spec.name)

    def exec_module(self, module) -> None:
        paths = [str(path) for path in _iter_dirs(module.__name__)]
        module.__path__ = paths
        module.__package__ = module.__name__


class _ProjectionFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname: str, path=None, target=None):
        if fullname in PACKAGE_ROOTS:
            init = self._find_init(fullname)
            if init is not None:
                return importlib.util.spec_from_file_location(
                    fullname,
                    init,
                    submodule_search_locations=[str(path) for path in _iter_dirs(fullname)],
                )
            spec = importlib.util.spec_from_loader(fullname, _SyntheticPackageLoader(), is_package=True)
            if spec is not None:
                spec.submodule_search_locations = [str(path) for path in _iter_dirs(fullname)]
            return spec

        parent, _, leaf = fullname.rpartition(".")
        if not parent:
            return None

        for root in _iter_dirs(parent):
            package_dir = self._find_child_package(root, leaf)
            if package_dir is not None:
                init = package_dir / "__init__.py"
                if init.exists():
                    return importlib.util.spec_from_file_location(
                        fullname,
                        init,
                        submodule_search_locations=[str(package_dir)],
                    )

            module_file = self._find_child_module(root, leaf)
            if module_file is not None:
                return importlib.util.spec_from_file_location(fullname, module_file)

        return None

    def _find_init(self, fullname: str) -> Optional[Path]:
        for root in _iter_dirs(fullname):
            init = root / "__init__.py"
            if init.exists():
                return init
        return None

    def _find_child_package(self, root: Path, leaf: str) -> Optional[Path]:
        exact = root / leaf
        if exact.is_dir():
            return exact
        for child in root.iterdir():
            if child.is_dir() and _canonical(child.name) == leaf:
                return child
        return None

    def _find_child_module(self, root: Path, leaf: str) -> Optional[Path]:
        exact = root / f"{leaf}.py"
        if exact.is_file():
            return exact
        for child in root.iterdir():
            if child.is_file() and child.suffix == ".py" and _canonical(child.stem) == leaf:
                return child
        return None


if not any(isinstance(finder, _ProjectionFinder) for finder in sys.meta_path):
    sys.meta_path.insert(0, _ProjectionFinder())

final_root = str(_FINAL_ROOT)
if final_root not in sys.path:
    sys.path.insert(0, final_root)
