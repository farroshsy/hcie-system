from pathlib import Path

import yaml

from app.main import app


MANIFEST_PATH = Path("config/endpoint_authority_manifest.yaml")
ALLOWED_STATUSES = {
    "canonical",
    "compatibility",
    "deprecated",
    "debug-only",
    "test-only",
    "admin-only",
    "health",
    "metrics",
    "static-docs",
}


def _route_key(route) -> str:
    methods = sorted(getattr(route, "methods", []) or [])
    methods = [method for method in methods if method not in {"HEAD", "OPTIONS"}]
    method_label = ",".join(methods) if methods else "WS"
    return f"{method_label} {route.path}"


def test_endpoint_authority_manifest_exists():
    assert MANIFEST_PATH.exists()


def test_every_manifest_entry_has_valid_status():
    manifest = yaml.safe_load(MANIFEST_PATH.read_text()) or {}
    routes = manifest.get("routes", {})
    assert routes
    invalid = {
        key: value.get("status")
        for key, value in routes.items()
        if value.get("status") not in ALLOWED_STATUSES
    }
    assert invalid == {}


def test_every_fastapi_route_has_manifest_classification():
    manifest = yaml.safe_load(MANIFEST_PATH.read_text()) or {}
    classified = set(manifest.get("routes", {}).keys())
    active_routes = {
        _route_key(route)
        for route in app.routes
        if hasattr(route, "path") and not route.path.startswith("/openapi")
    }
    missing = sorted(active_routes - classified)
    if missing:
        # Write missing routes to file for debugging
        with open("missing_routes.txt", "w") as f:
            f.write(f"Missing routes from manifest ({len(missing)}):\n")
            for route in missing:
                f.write(f"{route}\n")
        print(f"\nMissing routes from manifest ({len(missing)}): see missing_routes.txt")
    assert missing == []
