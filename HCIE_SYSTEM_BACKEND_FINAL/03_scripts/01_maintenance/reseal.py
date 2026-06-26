#!/usr/bin/env python3
"""Operator CLI for sealing/re-sealing an experiment run.

`run_sealing.seal_run` is the single most-repeated critical op in this repo (every "re-seal the
anchor" task), but it is only reachable over HTTP today (POST /cohorts/{id}/runs/{run_id}/seal).
This thin CLI exposes the SAME proven, idempotent function as the operator command the reseal
runbook otherwise lacks — it adds no sealing logic of its own.

Idempotent: re-sealing a run returns the existing manifest unchanged (per seal_run's contract).

Usage (in-container, stack up):
    docker compose -f .../docker-compose.final.yml exec api \
        python /app/03_scripts/01_maintenance/reseal.py <run_id> --note "Kalman re-seal"
Or via the Makefile:
    make reseal RUN=<run_id> NOTE="..."
"""
from __future__ import annotations

import argparse
import json
import sys


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Seal (or re-seal) an experiment run via the proven seal_run().")
    ap.add_argument("run_id", help="experiment_run_id to seal, e.g. run-d2154070-...")
    ap.add_argument("--sealed-by", default="cli", help="attribution stored on the seal (default: cli)")
    ap.add_argument("--note", default=None, help="free-text note stored on the seal")
    ap.add_argument("--dataset-id", default=None, help="optional dataset id to record on the seal")
    args = ap.parse_args(argv)

    # Clean module names are resolved by the runtime projection (11_build/00_runtime_projection),
    # which is active inside the api container where this script is meant to run.
    try:
        from storage.postgres_store.interaction_store import PostgresInteractionStore
        from app.api.v3.experiments.run_sealing import seal_run
    except Exception as exc:  # pragma: no cover - import wiring is environment-specific
        print(f"ERROR: could not import sealing deps ({exc}).\n"
              f"Run this inside the api container so the module resolver + DB are available.",
              file=sys.stderr)
        return 2

    store = PostgresInteractionStore()
    manifest = seal_run(store, args.run_id, sealed_by=args.sealed_by,
                        note=args.note, dataset_id=args.dataset_id)

    if not manifest:
        print(f"ERROR: seal_run returned nothing for {args.run_id} "
              f"(does the run have trajectories?)", file=sys.stderr)
        return 1

    seal_id = manifest.get("seal_id", "?")
    n = manifest.get("as_of_row_count", "?")
    chash = (manifest.get("content_hash") or "")[:12]
    frozen = manifest.get("frozen_stats")
    if isinstance(frozen, str):
        try:
            frozen = json.loads(frozen)
        except Exception:
            frozen = {}
    adc = (frozen or {}).get("adc_class", "?")

    print(f"✅ sealed: {seal_id}")
    print(f"   run_id       : {args.run_id}")
    print(f"   rows         : {n}")
    print(f"   content_hash : {chash}…")
    print(f"   adc_class    : {adc}")
    print(f"   (idempotent — re-running returns this same manifest)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
