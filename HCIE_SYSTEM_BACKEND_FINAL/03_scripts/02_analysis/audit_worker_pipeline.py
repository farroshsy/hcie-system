#!/usr/bin/env python3
"""FINAL-owned worker-pipeline audit entrypoint for cutover.

The audited implementation lives in `research_validation/scripts` and
validates the live event-sourced path through API, outbox, consumers, and
Postgres materialization. This wrapper keeps that logic unchanged while
making the FINAL tree own the operator command and report destination.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from types import ModuleType


HERE = Path(__file__).resolve()
FINAL_ROOT = HERE.parents[2]
REAL_SYSTEM_ROOT = FINAL_ROOT.parent
AUDIT_IMPL = REAL_SYSTEM_ROOT / "research_validation" / "scripts" / "audit_worker_pipeline.py"
DEFAULT_OUTPUT = FINAL_ROOT / "09_research" / "00_results" / "07_cutover" / "worker_pipeline"
DEFAULT_API = "http://localhost:8011"
DEFAULT_POSTGRES_CONTAINER = "hcie-final-postgres"


def _load_audit_impl() -> ModuleType:
    if not AUDIT_IMPL.exists():
        raise FileNotFoundError(f"worker-pipeline audit implementation not found: {AUDIT_IMPL}")

    spec = importlib.util.spec_from_file_location("_hcie_worker_pipeline_audit", AUDIT_IMPL)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load audit implementation from {AUDIT_IMPL}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser(description="FINAL worker-pipeline cutover audit")
    parser.add_argument("--api-url", default=DEFAULT_API, help="FINAL API base URL")
    parser.add_argument(
        "--postgres-container",
        default=DEFAULT_POSTGRES_CONTAINER,
        help="Docker Postgres container for pipeline verification",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="Output directory for audit reports",
    )
    args = parser.parse_args()

    audit = _load_audit_impl()
    output_dir = Path(args.output)
    return int(
        audit.run_audit(
            args.api_url,
            output_dir,
            postgres_container=args.postgres_container,
        )
    )


if __name__ == "__main__":
    sys.exit(main())
