"""
Method-grounding cascade API — progress board + dataset audit + step re-run triggers.

Reports are read from research_validation/reports/grounding/ (and linked paths in STEPS_REGISTRY.json).
Scripts are invoked via subprocess from the API container when POST /method-grounding/run/{step_id} is called.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/frontend/dashboard", tags=["v3-method-grounding"])

# Bulk rerun job state — only one batch at a time, persisted to disk so the
# frontend can poll across API restarts and the user can audit past runs.
_JOB_LOCK = threading.Lock()
_ACTIVE_JOB_ID: Optional[str] = None
_PER_STEP_TIMEOUT_S = int(os.environ.get("HCIE_GROUNDING_RERUN_TIMEOUT", "1800"))
# Steps that read host-side dataset files / write large derived artifacts.
# These are still allowed in the bulk runner, but the frontend warns the user
# they may fail when the API runs in a container without the data mount.
_HOST_FS_STEPS = {"tier0-reingest"}

# Resolve RealSystem root from backend layout (baked image: /app/...)
def _real_system_root() -> Path:
    """Find the workspace root that contains the grounding registry.

    Order: explicit env, container mount at /app/research_validation, host parents,
    then the host RealSystem layout. The Docker mount is the production path.
    """
    env = os.environ.get("HCIE_GROUNDING_ROOT")
    if env and (Path(env) / "research_validation" / "grounding" / "STEPS_REGISTRY.json").is_file():
        return Path(env)
    container = Path("/app")
    if (container / "research_validation" / "grounding" / "STEPS_REGISTRY.json").is_file():
        return container
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "research_validation" / "grounding" / "STEPS_REGISTRY.json").is_file():
            return parent
        if (parent / "HCIE_SYSTEM_BACKEND_FINAL").is_dir() and (parent / "research_validation").is_dir():
            return parent
    return container if container.exists() else here.parents[6]


def _grounding_root() -> Path:
    return _real_system_root() / "research_validation" / "grounding"


def _reports_dir() -> Path:
    return _real_system_root() / "research_validation" / "reports" / "grounding"


def _registry() -> Dict[str, Any]:
    path = _grounding_root() / "STEPS_REGISTRY.json"
    if not path.is_file():
        return {"version": "0", "tiers": []}
    return json.loads(path.read_text(encoding="utf-8"))


def _report_path(step: Dict[str, Any]) -> Optional[Path]:
    rel = step.get("report")
    if not rel:
        return None
    if str(rel).startswith("../"):
        return (_grounding_root() / rel).resolve()
    return _reports_dir() / rel


def _read_report(step: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    path = _report_path(step)
    if not path or not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("read report %s: %s", path, exc)
        return None


def _status(rep: Optional[Dict[str, Any]]) -> str:
    if not rep:
        return "pending"
    s = rep.get("status")
    # "deferred"/"disclosed" are decision-aware TERMINAL statuses (a limitation
    # adjudicated by a locked decision in jt_design_decisions.json) — they must be
    # recognized BEFORE the passed-bool fallback, otherwise a deferred report that
    # also carries passed=False is mis-mapped to "fail". See _cascade_status.py.
    if s in ("pass", "fail", "warn", "unknown", "deferred", "disclosed"):
        return s
    if rep.get("passed") is True:
        return "pass"
    if rep.get("passed") is False:
        return "fail"
    return "unknown"


def _store():
    from storage.postgres_store.interaction_store import PostgresInteractionStore
    return PostgresInteractionStore()


def _safe_read(query: str, params: tuple = (), default=None, fetch_one: bool = False):
    try:
        rows = _store().execute_read(query, params, fetch_one=fetch_one)
        if rows is None:
            return default if default is not None else ({} if fetch_one else [])
        return rows
    except Exception as exc:
        logger.warning("grounding query failed: %s", exc)
        return default if default is not None else []


_HEADLINE_KEYS = (
    "reason",
    "kalman_baseline_target", "best_predictor", "redundant_pairs",
    "corr_next_correct", "winner", "decision",
    "hcie_matched_overall_auc", "causal_magnitude",
    "markers_remaining", "files_updated",
    "anchor", "child_run_id", "supersede_lineage",
    "dimensions", "predictors",
)


def _headline(rep: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not rep:
        return {}
    return {k: rep[k] for k in _HEADLINE_KEYS if k in rep}


@router.get("/method-grounding")
async def method_grounding_progress() -> Dict[str, Any]:
    """Full Tier 0-5 progress board with last report metadata per step."""
    tiers_out: List[Dict[str, Any]] = []
    total = passed = pending = failed = warns = deferred = 0
    for tier in _registry().get("tiers", []):
        steps_out = []
        for step in tier.get("steps", []):
            rep = _read_report(step)
            st = _status(rep)
            total += 1
            if st == "pass":
                passed += 1
            elif st == "pending":
                pending += 1
            elif st == "fail":
                failed += 1
            elif st == "warn":
                warns += 1
            elif st in ("deferred", "disclosed"):
                deferred += 1
            rp = _report_path(step)
            steps_out.append({
                "id": step["id"],
                "title": step.get("title"),
                "script": step.get("script"),
                "report_path": str(rp) if rp else None,
                "report_filename": rp.name if rp else None,
                "status": st,
                "finished_at": rep.get("finished_at") if rep else None,
                "phase2_run_id": rep.get("phase2_run_id") if rep else None,
                "seal_id": rep.get("seal_id") if rep else None,
                "input_hash": rep.get("input_hash") if rep else None,
                "headline": _headline(rep),
                "type": step.get("type", "script"),
            })
        tiers_out.append({
            "id": tier["id"],
            "title": tier["title"],
            "steps": steps_out,
        })
    return {
        "status": "ok",
        "summary": {
            "total_steps": total,
            "passed": passed,
            "pending": pending,
            "warn": warns,
            "failed": failed,
            "deferred": deferred,
            "completion_pct": round(100.0 * (passed + deferred) / total, 1) if total else 0,
        },
        "anchor": {
            "phase2_run_id": "run-94a3b8ba-015b-4d84-b288-004fe60bc282",
            "seal_id": "seal-fbf78cd9-ce2a-4a26-81b1-f7b93f7ae00f",
        },
        "tiers": tiers_out,
        "registry_version": _registry().get("version"),
        "semantic_version": "2.0",
    }


@router.get("/method-grounding/report/{step_id}")
async def method_grounding_report(step_id: str) -> Dict[str, Any]:
    """Full JSON report for a single step (for the evidence panel drawer)."""
    step = None
    for tier in _registry().get("tiers", []):
        for s in tier.get("steps", []):
            if s["id"] == step_id:
                step = s
                break
        if step:
            break
    if not step:
        raise HTTPException(404, detail=f"unknown step_id: {step_id}")
    rp = _report_path(step)
    rep = _read_report(step)
    return {
        "status": "ok" if rep else "missing",
        "step_id": step_id,
        "title": step.get("title"),
        "script": step.get("script"),
        "report_path": str(rp) if rp else None,
        "report": rep,
        "semantic_version": "1.0",
    }


@router.get("/method-grounding/evidence")
async def method_grounding_evidence() -> Dict[str, Any]:
    """Aggregated evidence panels (signal table, synergy, lineage, marker count)."""
    rd = _reports_dir()

    def load(name: str) -> Optional[Dict[str, Any]]:
        p = rd / name
        if not p.is_file():
            return None
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return None

    synergy = load("tier2_synergy_matrix.json")
    predictive = load("tier2_predictive_validity.json")
    selection = load("tier2_selection_ablation.json")
    lit = load("tier2_literature_packets.json")
    math_audit = load("tier2_signal_math_audit.json")
    enkf = load("tier3_enkf_trial.json")
    ensemble_dec = load("tier3_ensemble_decision.json")
    decisions = load("tier0_dataset_decisions.json")
    intent = load("tier1_intent_decisions.json")
    papers = load("tier5_papers.json")
    seal_state = load("tier4_seal.json")
    fork_state = load("tier4_supersede.json")
    topology = load("tier5_topology_mag.json")
    r12 = load("tier5_r12.json")
    baselines = load("tier5_baselines.json")
    dataset_decisions = decisions.get("decisions") if decisions else {}

    return {
        "status": "ok",
        "anchor": {
            "phase2_run_id": "run-94a3b8ba-015b-4d84-b288-004fe60bc282",
            "seal_id": "seal-fbf78cd9-ce2a-4a26-81b1-f7b93f7ae00f",
            "lineage": fork_state.get("supersede_lineage") if fork_state else None,
            "anchor_rows": (seal_state or {}).get("anchor_rows"),
        },
        "signal_truth_table": {
            "math_audit": math_audit,
            "literature_packets": lit,
            "predictive_validity": predictive,
            "selection_impact": selection,
            "intent_decisions": intent,
        },
        "synergy_matrix": synergy,
        "ensemble_decision": ensemble_dec,
        "enkf_trial": enkf,
        "topology_magnitude": topology,
        "r12_ablation": r12,
        "matched_baselines": baselines,
        "dataset_decisions": dataset_decisions,
        "papers": papers,
        "semantic_version": "1.0",
    }


@router.get("/dataset-audit/{dataset_id}")
async def dataset_audit(dataset_id: str) -> Dict[str, Any]:
    """Contamination / lineage audit for one external dataset (Tier 0 evidence)."""
    profile = _safe_read(
        """
        SELECT dataset_id,
               count(*) AS rows,
               count(DISTINCT user_id) AS users,
               count(DISTINCT concept_id) AS concepts,
               avg(correct::int) AS correct_rate,
               min(raw_timestamp) AS first_ts,
               max(raw_timestamp) AS last_ts
        FROM external_log_attempts
        WHERE dataset_id = %s
        GROUP BY dataset_id
        """,
        (dataset_id,),
        fetch_one=True,
    ) or {}

    edges = _safe_read(
        """
        SELECT count(*) AS edges,
               count(DISTINCT source_concept_id) AS sources,
               count(DISTINCT target_concept_id) AS targets
        FROM external_concept_graph
        WHERE dataset_id = %s
        """,
        (dataset_id,),
        fetch_one=True,
    ) or {}

    dup_user_concept = _safe_read(
        """
        SELECT count(*) - count(DISTINCT (user_id, concept_id, raw_timestamp)) AS dup_triples
        FROM external_log_attempts WHERE dataset_id = %s
        """,
        (dataset_id,),
        fetch_one=True,
    ) or {}

    # Load tier0 reports if present
    lineage_rep = None
    dups_rep = None
    lin_path = _reports_dir() / "tier0_lineage_audit.json"
    dup_path = _reports_dir() / "tier0_dups_edges.json"
    if lin_path.is_file():
        lineage_rep = json.loads(lin_path.read_text(encoding="utf-8"))
    if dup_path.is_file():
        dups_rep = json.loads(dup_path.read_text(encoding="utf-8"))

    ds_lineage = None
    if lineage_rep:
        for row in lineage_rep.get("lineage_per_dataset", []):
            if row.get("dataset_id") == dataset_id:
                ds_lineage = row
                break

    decision_path = _reports_dir() / "tier0_dataset_decisions.json"
    decision = None
    if decision_path.is_file():
        dec_all = json.loads(decision_path.read_text(encoding="utf-8"))
        decision = (dec_all.get("decisions") or {}).get(dataset_id)

    dup_triples = int(dup_user_concept.get("dup_triples") or 0)
    flags: List[str] = []
    if dup_triples > 0:
        flags.append(f"duplicate_user_concept_timestamp={dup_triples}")
    if int(edges.get("edges") or 0) == 0 and dataset_id.startswith("junyi"):
        flags.append("no_graph_edges_for_junyi_variant")
    if decision:
        flags.append(f"decision={decision}")

    return {
        "status": "ok",
        "dataset_id": dataset_id,
        "profile": profile,
        "graph": edges,
        "contamination_flags": flags,
        "lineage": ds_lineage,
        "tier0_reports": {
            "lineage_audit": str(lin_path) if lin_path.is_file() else None,
            "dups_edges": str(dup_path) if dup_path.is_file() else None,
        },
        "decision": decision,
        "semantic_version": "1.0",
    }


@router.post("/method-grounding/run/{step_id}")
async def run_grounding_step(step_id: str) -> Dict[str, Any]:
    """Re-run a grounding script step (host must have python + docker)."""
    reg_steps = []
    for tier in _registry().get("tiers", []):
        for step in tier.get("steps", []):
            reg_steps.append(step)
    step = next((s for s in reg_steps if s["id"] == step_id), None)
    if not step:
        raise HTTPException(404, detail=f"unknown step_id: {step_id}")
    script = step.get("script")
    if not script:
        raise HTTPException(400, detail=f"step {step_id} is not script-runnable")
    root = _real_system_root()
    script_path = _grounding_root() / script
    if not script_path.is_file():
        # tier5 may point to ../scripts/
        script_path = (_grounding_root() / script).resolve()
    if not script_path.is_file():
        raise HTTPException(404, detail=f"script not found: {script}")
    try:
        proc = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=600,
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(504, detail="step timed out after 600s")
    rep = _read_report(step)
    return {
        "status": "ok" if proc.returncode == 0 else "error",
        "step_id": step_id,
        "exit_code": proc.returncode,
        "stdout_tail": (proc.stdout or "")[-4000:],
        "stderr_tail": (proc.stderr or "")[-2000:],
        "report_status": _status(rep),
        "finished_at": rep.get("finished_at") if rep else None,
    }


# ── Bulk re-run ───────────────────────────────────────────────────────────────
# The bulk runner powers the frontend "Rerun cascade" tray. It accepts either an
# explicit list of step_ids or a coarse scope (all / tier0 / tier1 / …) plus an
# optional status filter, then runs each script subprocess sequentially in a
# background thread. Job state is persisted to a JSON file so the UI can poll
# across page reloads and we keep a minimal audit trail of who reran what.

def _jobs_dir() -> Path:
    p = _real_system_root() / "research_validation" / "reports" / "grounding" / "_rerun_jobs"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _job_path(job_id: str) -> Path:
    return _jobs_dir() / f"{job_id}.json"


def _write_job(job_id: str, state: Dict[str, Any]) -> None:
    p = _job_path(job_id)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")
    tmp.replace(p)


def _read_job(job_id: str) -> Optional[Dict[str, Any]]:
    p = _job_path(job_id)
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def _flatten_registry() -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for tier in _registry().get("tiers", []):
        for step in tier.get("steps", []):
            out.append({"tier_id": tier["id"], **step})
    return out


def _resolve_step_ids(payload: Dict[str, Any]) -> List[str]:
    """Map a batch request payload to an ordered list of runnable step_ids.

    Order follows the registry definition (tier0 → tier5). Steps without a
    script (manual decision rows) are dropped. We never run the same id twice
    in one batch.
    """
    all_steps = _flatten_registry()
    explicit = list(payload.get("step_ids") or [])
    scope = payload.get("scope")
    status_filter = payload.get("status_filter") or []

    if explicit:
        wanted = set(explicit)
        ordered = [s for s in all_steps if s["id"] in wanted]
    elif scope == "all" or not scope:
        ordered = list(all_steps)
    elif scope.startswith("tier"):
        ordered = [s for s in all_steps if s["tier_id"] == scope]
    else:
        ordered = []

    if status_filter:
        wanted_status = {str(s).lower() for s in status_filter}
        kept: List[Dict[str, Any]] = []
        for s in ordered:
            if _status(_read_report(s)) in wanted_status:
                kept.append(s)
        ordered = kept

    seen: set = set()
    runnable: List[str] = []
    for s in ordered:
        if not s.get("script"):
            continue
        if s["id"] in seen:
            continue
        seen.add(s["id"])
        runnable.append(s["id"])
    return runnable


def _run_batch_in_thread(job_id: str, step_ids: List[str], stop_on_fail: bool) -> None:
    """Run each step's script sequentially, updating the job file after each."""
    global _ACTIVE_JOB_ID
    state = _read_job(job_id) or {}
    state.update({
        "state": "running",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "current_index": 0,
        "current_step_id": step_ids[0] if step_ids else None,
    })
    state.setdefault("results", [])
    _write_job(job_id, state)

    reg_steps = _flatten_registry()
    by_id = {s["id"]: s for s in reg_steps}
    root = _real_system_root()
    final_state = "done"

    for idx, sid in enumerate(step_ids):
        state["current_index"] = idx
        state["current_step_id"] = sid
        _write_job(job_id, state)

        step = by_id.get(sid)
        if not step or not step.get("script"):
            state["results"].append({
                "step_id": sid,
                "status": "skipped",
                "reason": "no script registered",
            })
            _write_job(job_id, state)
            continue

        script_path = (_grounding_root() / step["script"]).resolve()
        if not script_path.is_file():
            state["results"].append({
                "step_id": sid,
                "status": "missing",
                "reason": f"script not found: {step['script']}",
            })
            _write_job(job_id, state)
            if stop_on_fail:
                final_state = "stopped"
                break
            continue

        t0 = time.time()
        entry: Dict[str, Any] = {"step_id": sid, "started_at": datetime.now(timezone.utc).isoformat()}
        try:
            proc = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=str(root),
                capture_output=True,
                text=True,
                timeout=_PER_STEP_TIMEOUT_S,
            )
            elapsed = time.time() - t0
            rep = _read_report(step)
            entry.update({
                "status": "done" if proc.returncode == 0 else "failed",
                "exit_code": proc.returncode,
                "elapsed_s": round(elapsed, 1),
                "report_status": _status(rep),
                "report_finished_at": rep.get("finished_at") if rep else None,
                "stderr_tail": (proc.stderr or "")[-1500:] or None,
            })
        except subprocess.TimeoutExpired:
            entry.update({
                "status": "timeout",
                "elapsed_s": round(time.time() - t0, 1),
                "reason": f"per-step timeout {_PER_STEP_TIMEOUT_S}s exceeded",
            })
        except Exception as exc:
            entry.update({
                "status": "exception",
                "elapsed_s": round(time.time() - t0, 1),
                "error": repr(exc),
            })

        state["results"].append(entry)
        _write_job(job_id, state)

        if entry["status"] != "done" and stop_on_fail:
            final_state = "stopped"
            break

    state["state"] = final_state
    state["finished_at"] = datetime.now(timezone.utc).isoformat()
    state["current_step_id"] = None
    summary = {"done": 0, "failed": 0, "skipped": 0, "timeout": 0, "exception": 0, "missing": 0}
    for r in state.get("results", []):
        s = r.get("status")
        if s in summary:
            summary[s] += 1
    state["summary"] = summary
    _write_job(job_id, state)

    with _JOB_LOCK:
        if _ACTIVE_JOB_ID == job_id:
            _ACTIVE_JOB_ID = None


@router.post("/method-grounding/rerun-batch")
async def rerun_batch(payload: Dict[str, Any] = Body(default={})) -> Dict[str, Any]:
    """Kick off a sequential rerun of multiple grounding steps.

    Body shape (all fields optional, but at least one selector required):
      step_ids:      explicit ordered list of step_ids
      scope:         "all" | "tier0" | "tier1" | "tier2" | "tier2_5" | "tier3" | "tier4" | "tier5"
      status_filter: ["pending", "fail", "warn", "pass"] — narrows the selection
      stop_on_fail:  bool, default false (continue across failures)

    Returns: { job_id, step_ids, stop_on_fail }
    Poll status with GET /method-grounding/rerun-batch/{job_id}.
    """
    global _ACTIVE_JOB_ID
    payload = payload or {}
    step_ids = _resolve_step_ids(payload)
    if not step_ids:
        raise HTTPException(400, detail="no runnable steps matched the request (manual rows are skipped)")
    stop_on_fail = bool(payload.get("stop_on_fail", False))
    note = payload.get("note")

    with _JOB_LOCK:
        if _ACTIVE_JOB_ID:
            raise HTTPException(
                409,
                detail=f"another rerun batch is in progress: {_ACTIVE_JOB_ID}",
            )
        job_id = f"rerun-{uuid.uuid4().hex[:12]}"
        _ACTIVE_JOB_ID = job_id

    state = {
        "job_id": job_id,
        "step_ids": step_ids,
        "stop_on_fail": stop_on_fail,
        "note": note,
        "state": "queued",
        "queued_at": datetime.now(timezone.utc).isoformat(),
        "current_index": -1,
        "current_step_id": None,
        "results": [],
        "host_fs_steps": [s for s in step_ids if s in _HOST_FS_STEPS],
    }
    _write_job(job_id, state)

    thread = threading.Thread(
        target=_run_batch_in_thread,
        args=(job_id, step_ids, stop_on_fail),
        daemon=True,
        name=f"grounding-rerun-{job_id}",
    )
    thread.start()

    return {
        "job_id": job_id,
        "step_ids": step_ids,
        "stop_on_fail": stop_on_fail,
        "host_fs_steps": state["host_fs_steps"],
        "per_step_timeout_s": _PER_STEP_TIMEOUT_S,
    }


@router.get("/method-grounding/rerun-batch/{job_id}")
async def rerun_batch_status(job_id: str) -> Dict[str, Any]:
    state = _read_job(job_id)
    if not state:
        raise HTTPException(404, detail=f"unknown job_id: {job_id}")
    state = dict(state)
    state["progress"] = {
        "completed": len(state.get("results", [])),
        "total": len(state.get("step_ids", [])),
    }
    state["is_active"] = state.get("job_id") == _ACTIVE_JOB_ID
    return state


@router.get("/method-grounding/rerun-batch")
async def rerun_batch_list() -> Dict[str, Any]:
    """List recent batch jobs (newest first, capped) plus the active id."""
    jobs_dir = _jobs_dir()
    if not jobs_dir.is_dir():
        return {"active": _ACTIVE_JOB_ID, "jobs": []}
    files = sorted(
        (p for p in jobs_dir.glob("rerun-*.json")),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    out: List[Dict[str, Any]] = []
    for p in files[:30]:
        try:
            j = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        results = j.get("results", []) or []
        summary = j.get("summary") or {"done": sum(1 for r in results if r.get("status") == "done")}
        out.append({
            "job_id": j.get("job_id"),
            "state": j.get("state"),
            "queued_at": j.get("queued_at"),
            "started_at": j.get("started_at"),
            "finished_at": j.get("finished_at"),
            "step_count": len(j.get("step_ids", [])),
            "completed": len(results),
            "current_step_id": j.get("current_step_id"),
            "stop_on_fail": j.get("stop_on_fail"),
            "summary": summary,
            "note": j.get("note"),
        })
    return {"active": _ACTIVE_JOB_ID, "jobs": out, "host_fs_steps": sorted(_HOST_FS_STEPS)}


# ────────────────────────────────────────────────────────────────────────────
# Anchor ledger — single source of truth for the cascade's phase2_run_id +
# seal_id. Lives in research_validation/grounding/ANCHOR.json so a Tier 2.5
# continuation run can promote a child run id without anyone editing Python
# constants. _runner.py reads `active` at import time.
# ────────────────────────────────────────────────────────────────────────────


def _anchor_path() -> Path:
    return _grounding_root() / "ANCHOR.json"


def _read_anchor() -> Dict[str, Any]:
    p = _anchor_path()
    if not p.is_file():
        return {"version": 1, "active": {}, "history": [], "candidates": []}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"version": 1, "active": {}, "history": [], "candidates": []}


def _write_anchor(data: Dict[str, Any]) -> None:
    p = _anchor_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")


@router.get("/method-grounding/anchor")
async def anchor_get() -> Dict[str, Any]:
    """Return the current cascade anchor + any continuation-run candidates."""
    data = _read_anchor()
    return {
        "active": data.get("active") or {},
        "candidates": data.get("candidates") or [],
        "history": data.get("history") or [],
        "anchor_path": str(_anchor_path()),
    }


@router.post("/method-grounding/anchor/promote")
async def anchor_promote(payload: Dict[str, Any] = Body(default={})) -> Dict[str, Any]:
    """Promote a candidate continuation run to the active anchor.

    Body:
        {
            "phase2_run_id": "run-...",         # required
            "seal_id":       "seal-..." | null,  # optional; defaults to "<run_id>-unsealed"
            "label":         "..."               # optional
        }

    The previous `active` is pushed onto `history`. The candidate (matched by
    `phase2_run_id`) is removed from `candidates`. The cascade picks up the new
    anchor on the next process import (frontend rerun-batch will fork fresh
    Python subprocesses, so they see the change immediately).
    """
    new_run = str(payload.get("phase2_run_id") or "").strip()
    if not new_run:
        raise HTTPException(status_code=400, detail="phase2_run_id is required")
    new_seal = payload.get("seal_id")
    label = payload.get("label")

    data = _read_anchor()
    candidates = list(data.get("candidates") or [])
    cand = next((c for c in candidates if str(c.get("phase2_run_id")) == new_run), None)

    prev_active = dict(data.get("active") or {})
    if prev_active:
        history = list(data.get("history") or [])
        history.append({**prev_active, "demoted_at": datetime.now(timezone.utc).isoformat()})
        data["history"] = history

    new_active = {
        "phase2_run_id": new_run,
        "seal_id": str(new_seal) if new_seal else f"{new_run}-unsealed",
        "label": str(label) if label else (cand or {}).get("label") or new_run,
        "v2_active": bool((cand or {}).get("v2_active", True)),
        "promoted_at": datetime.now(timezone.utc).isoformat(),
    }
    data["active"] = new_active
    data["candidates"] = [c for c in candidates if str(c.get("phase2_run_id")) != new_run]
    _write_anchor(data)

    return {
        "status": "ok",
        "active": new_active,
        "previous_active": prev_active,
        "candidates_remaining": len(data["candidates"]),
        "next": (
            "Open the Rerun cascade tray with scope=all to re-validate every "
            "tier against the new anchor."
        ),
    }
