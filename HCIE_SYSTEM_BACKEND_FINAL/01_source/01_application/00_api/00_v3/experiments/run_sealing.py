"""Stage 0 run sealing (reject + assisted-handoff mode).

A sealed run is an immutable, reproducible anchor for any cited figure:
- ``seal_run()`` freezes a manifest (row count + content hash + frozen stats).
- post-seal writes (replay/resume) are **rejected** — sealed means sealed. To
  keep collecting data, ``mint_continuation()`` creates a fresh run linked to the
  sealed parent and the caller re-issues the write against it. The redirect is
  **explicit** (the caller is told the new run_id), never silent — so a cited
  run_id always points at exactly one immutable row set, with no chain to walk.

Cite the ``seal_id`` (not the bare run_id) — it points at the frozen manifest.
Lineage of continuations lives in ``run_forks`` (parent_run_id -> child_run_id).

Additive module: imported by the seal endpoint + the replay/cohort write guards
in cohorts.py / service/router.py. Requires tables ``sealed_runs`` + ``run_forks``.
"""
from __future__ import annotations

import json
import os
import uuid
from typing import Any, Dict, List, Mapping, Optional

# ADC thresholds (kept in sync with the classifier; see phase2 provenance notes).
ALPHA_FLOOR = 0.01            # mean threshold — the load-bearing ACTIVE/DORMANT separator
SIGNAL_RATIO_THRESHOLD = 0.08  # signal_ratio = std/mean


class RunSealedError(Exception):
    """A write targeted a sealed run. Carries the seal + the continuation run_id
    the caller should write to instead (assisted handoff)."""

    def __init__(self, run_id: str, seal_id: str, continue_with: str):
        self.run_id = run_id
        self.seal_id = seal_id
        self.continue_with = continue_with
        super().__init__(
            f"run {run_id} is sealed ({seal_id}); writes are rejected — "
            f"continue with {continue_with}"
        )


def is_sealed(store, run_id: str) -> bool:
    return _seal_id(store, run_id) is not None


def _seal_id(store, run_id: str) -> Optional[str]:
    row = store.execute_read(
        "SELECT seal_id FROM sealed_runs WHERE experiment_run_id = %s", (run_id,), fetch_one=True
    )
    return row["seal_id"] if row else None


def _f(row: Mapping[str, Any], key: str) -> float:
    """Float-coerce a possibly-NULL aggregate cell (NULL/0 -> 0.0)."""
    return float(row.get(key) or 0.0)


def _activation_profile(store, run_id: str) -> Optional[Dict[str, Any]]:
    """Per-signal ADC verdict from raw_governance_snapshot via the ONE canonical
    classifier (``classify_dimension``) — the same rule the offline L4 profiler uses.
    Replaces the legacy single-metric std/mean verdict (which read the downstream
    ``jt_transfer_contribution`` and so reported a dimension active even where the raw
    substrate was null).

    ONE table scan computes mean/std/min/max/nonzero-fraction + mean weight for ALL six
    dimensions (was 6 separate scans -> ~17s on the 96k-row anchor; this is a single pass).
    Read-only/additive; returns None on failure so sealing never breaks. The endpoint caches
    the result; the sealer calls it once at seal time.
    """
    try:
        from core.learning.adaptive_dimension_controller import (  # lazy: numpy-heavy
            GOVERNANCE_DIMENSIONS, DIMENSION_TO_WEIGHT_KEY, DimensionSignal, classify_dimension,
        )
    except Exception:
        return None
    eps = 1e-6
    # One SELECT, one scan: per-dimension stats as <dim>_mean/_std/_lo/_hi/_nz/_w. dim/wkey are
    # fixed module constants (GOVERNANCE_DIMENSIONS / WEIGHT_KEYS), never user input — safe to inline.
    cols: List[str] = ["COUNT(*) AS n"]
    for dim in GOVERNANCE_DIMENSIONS:
        v = f"(raw_governance_snapshot->>'{dim}')::float"
        w = f"(weights_snapshot->>'{DIMENSION_TO_WEIGHT_KEY[dim]}')::float"
        cols += [
            f"COALESCE(AVG({v}),0) AS {dim}_mean",
            f"COALESCE(STDDEV_POP({v}),0) AS {dim}_std",
            f"COALESCE(MIN({v}),0) AS {dim}_lo",
            f"COALESCE(MAX({v}),0) AS {dim}_hi",
            f"COALESCE(AVG(CASE WHEN {v} IS NOT NULL AND ABS({v}) > {eps} THEN 1.0 ELSE 0.0 END),0) AS {dim}_nz",
            f"COALESCE(AVG({w}),0) AS {dim}_w",
        ]
    row = store.execute_read(
        f"SELECT {', '.join(cols)} FROM experiment_trajectories WHERE experiment_run_id = %s",
        (run_id,), fetch_one=True,
    ) or {}
    n = int(row.get("n") or 0)
    per_dim: Dict[str, Any] = {}
    buckets: Dict[str, List[str]] = {
        "active_dimensions": [], "dormant_dimensions": [], "suppressed_dimensions": []
    }
    for dim in GOVERNANCE_DIMENSIONS:
        mean, std = _f(row, f"{dim}_mean"), _f(row, f"{dim}_std")
        lo, hi, nz, wmean = _f(row, f"{dim}_lo"), _f(row, f"{dim}_hi"), _f(row, f"{dim}_nz"), _f(row, f"{dim}_w")
        sig = DimensionSignal(
            dimension=dim, n_observations=n, mean=mean, std=std, min=lo, max=hi,
            dynamic_range=hi - lo, nonzero_fraction=nz,
            coefficient_of_variation=(std / abs(mean)) if abs(mean) > 1e-9 else float("nan"),
            weight_mean=wmean, weight_min=wmean, weight_max=wmean, weight_collapsed=wmean < 0.05,
        )
        verdict = classify_dimension(sig)
        per_dim[dim] = {
            "active": verdict.active, "has_signal": verdict.has_signal,
            "weight_collapsed": verdict.weight_collapsed, "rationale": verdict.rationale,
            "mean": round(mean, 6), "std": round(std, 6),
            "nonzero_fraction": round(nz, 4), "weight_mean": round(wmean, 4),
        }
        bucket = ("active_dimensions" if verdict.active
                  else "dormant_dimensions" if not verdict.has_signal
                  else "suppressed_dimensions")
        buckets[bucket].append(dim)
    return {
        "schema": "adc-perdim-1.0",
        "source": "raw_governance_snapshot",
        "classifier": "adaptive_dimension_controller.classify_dimension",
        "per_dimension": per_dim,
        **buckets,
    }


def _code_provenance() -> Dict[str, Any]:
    """Pipeline/code version baked into the image at build time (G7). The seal's content_hash
    freezes the ROWS; this freezes the CODE that produced them, so a consumer can detect a seal
    that is stale vs the current HEAD (git_sha != HEAD). Values come from build-time env stamped
    by Dockerfile.cutover; 'unknown' when the image predates the stamp."""
    return {
        "git_sha": os.environ.get("HCIE_GIT_SHA", "unknown"),
        "git_dirty": os.environ.get("HCIE_GIT_DIRTY", "unknown"),
        "build_time": os.environ.get("HCIE_BUILD_TIME", "unknown"),
        "note": "code/pipeline version that generated this run; compare git_sha to HEAD to detect a stale-vs-code seal",
    }


def _compute_manifest(store, run_id: str) -> Dict[str, Any]:
    """Raw aggregates + deterministic content hash over the run's trajectory rows."""
    agg = store.execute_read(
        """
        SELECT COUNT(*)                              AS n,
               AVG(jt_transfer_contribution)         AS mean,
               STDDEV_POP(jt_transfer_contribution)  AS std,
               md5(string_agg(interaction_id::text, ',' ORDER BY interaction_id)) AS content_hash
        FROM experiment_trajectories
        WHERE experiment_run_id = %s
        """,
        (run_id,),
        fetch_one=True,
    ) or {}
    n = int(agg.get("n") or 0)
    mean = float(agg.get("mean") or 0.0)
    std = float(agg.get("std") or 0.0)
    ratio = (std / mean) if mean else 0.0  # std/mean, NOT mean/std
    adc_class = "ACTIVE" if (mean > ALPHA_FLOOR and ratio >= SIGNAL_RATIO_THRESHOLD) else "DORMANT"
    frozen_stats: Dict[str, Any] = {
        # Legacy single-metric verdict (kept for back-compat with existing consumers).
        # NOTE: reads the downstream jt_transfer_contribution; the per-signal
        # activation_profile below is the AUTHORITATIVE verdict (raw snapshot).
        "n": n,
        "mean": mean,
        "std": std,
        "signal_ratio": ratio,
        "adc_class": adc_class,
        "metric": "jt_transfer_contribution",
        "thresholds": {"alpha_floor": ALPHA_FLOOR, "signal_ratio": SIGNAL_RATIO_THRESHOLD},
    }
    activation_profile = _activation_profile(store, run_id)
    if activation_profile is not None:
        frozen_stats["activation_profile"] = activation_profile
    frozen_stats["code_provenance"] = _code_provenance()  # G7: stamp git-sha/build into the seal
    return {
        "as_of_row_count": n,
        "content_hash": agg.get("content_hash") or "",
        "frozen_stats": frozen_stats,
    }


def seal_run(
    store,
    run_id: str,
    *,
    sealed_by: str = "api",
    note: Optional[str] = None,
    dataset_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Freeze a run. Idempotent: re-sealing returns the existing manifest unchanged."""
    existing = store.execute_read(
        "SELECT * FROM sealed_runs WHERE experiment_run_id = %s", (run_id,), fetch_one=True
    )
    if existing:
        return existing
    m = _compute_manifest(store, run_id)
    seal_id = f"seal-{uuid.uuid4()}"
    store.execute_write(
        """
        INSERT INTO sealed_runs (seal_id, experiment_run_id, as_of_row_count, content_hash,
                                 frozen_stats, dataset_id, sealed_by, note)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (experiment_run_id) DO NOTHING
        """,
        (seal_id, run_id, m["as_of_row_count"], m["content_hash"],
         json.dumps(m["frozen_stats"]), dataset_id, sealed_by, note),
    )
    return store.execute_read(
        "SELECT * FROM sealed_runs WHERE experiment_run_id = %s", (run_id,), fetch_one=True
    )


def mint_continuation(store, parent_run_id: str) -> str:
    """Create (or reuse) the active continuation run for a sealed parent.

    Idempotent under concurrency: the partial unique index
    ``ux_run_forks_active_parent`` guarantees at most one ACTIVE child per parent,
    so repeated calls return the same continuation run_id. Clones the parent's
    ``cohort_runs`` config row (if present) so stats/export work on the child.
    """
    row = store.execute_read(
        "SELECT child_run_id FROM run_forks WHERE parent_run_id = %s AND active",
        (parent_run_id,), fetch_one=True,
    )
    if row:
        return row["child_run_id"]

    child = f"run-{uuid.uuid4()}"
    # Clone parent cohort_runs config so the continuation is a first-class run
    # (queryable via stats.csv / trajectories.csv). No-op if parent has no row.
    store.execute_write(
        """
        INSERT INTO cohort_runs (run_id, cohort_id, status, reason,
                                 capability_manifest_fingerprint, seed_set,
                                 synthetic_user_prefix, progress)
        SELECT %s, cohort_id, 'continuation',
               'continuation of sealed ' || %s,
               capability_manifest_fingerprint, seed_set,
               synthetic_user_prefix, '{}'::jsonb
        FROM cohort_runs WHERE run_id = %s
        ON CONFLICT (run_id) DO NOTHING
        """,
        (child, parent_run_id, parent_run_id),
    )
    store.execute_write(
        """
        INSERT INTO run_forks (parent_run_id, child_run_id, active)
        VALUES (%s, %s, TRUE)
        ON CONFLICT (parent_run_id) WHERE active DO NOTHING
        """,
        (parent_run_id, child),
    )
    # Re-read: under a concurrent race the ON CONFLICT may have been a no-op and
    # another caller's child is the winner — always return the active one.
    row = store.execute_read(
        "SELECT child_run_id FROM run_forks WHERE parent_run_id = %s AND active",
        (parent_run_id,), fetch_one=True,
    )
    return row["child_run_id"] if row else child


def assert_writable(store, run_id: str) -> None:
    """Reject writes to a sealed run. Raises ``RunSealedError`` carrying the
    continuation run_id (assisted handoff). No-op for normal (unsealed) runs."""
    seal_id = _seal_id(store, run_id)
    if seal_id is not None:
        raise RunSealedError(run_id, seal_id, mint_continuation(store, run_id))
