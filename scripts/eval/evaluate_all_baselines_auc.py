"""Unified cold-start AUC evaluation: BKT, DKT, SAKT, GKT vs HCIE Phase 1 & Phase 2.

METRIC REALITY (see research_validation/deliverables/SYSTEM_DATA_METRIC_MAP.md — read before claiming
what's tracked). This script now emits AUC + accuracy + Brier + log-loss per window (via _metrics()),
all from the same (y_true, y_score) arrays — AUC computation unchanged so it reproduces sealed values.
NOT computed here: regret (candidate_arm_scores logged as []; bandit_regret table empty → future work)
and learning-gain (derive separately from experiment_trajectories.mastery_delta, ~0,034/interaction).


Evaluation protocol (fully matched):
  - All models evaluated on the SAME held-out user list from the Phase 2 run.
  - Baselines (BKT/DKT/SAKT/GKT): predict→observe loop using experiment_trajectories sequences.
  - HCIE Phase 2: mastery_before as prediction, correctness as ground truth, from
    experiment_trajectories — same users, same cold-start windows.
  - HCIE Phase 1: evaluated on equivalent held-out positions from the Phase 1 run
    (separate population; shown as causal-delta reference, not a direct baseline comparison).

Outputs:
  reports/baseline_comparison/comparison_table.{json,md}

Usage::

    python -X utf8 research_validation/scripts/evaluate_all_baselines_auc.py \\
        --phase2-run-id run-94a3b8ba-015b-4d84-b288-004fe60bc282 \\
        --phase1-run-id run-217532ca-39e6-4859-a41f-88ed53e904a2 \\
        --train-users 17 --eval-users 10
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from baselines.bkt import BKTBaseline  # type: ignore
from baselines.dkt import DKTBaseline  # type: ignore
from baselines.sakt import SAKTBaseline  # type: ignore
from baselines.gkt_pykt import GKTBaseline  # type: ignore
from baselines.artifacts import default_artifact_root  # type: ignore

DATASET_ID = "junyi_2015_graph"
COLD_START_WINDOWS = [5, 10, 20]


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def _psql(container: str, sql: str) -> str:
    proc = subprocess.run(
        ["docker", "exec", container, "psql", "-U", "hcie_user", "-d", "hcie",
         "-t", "-A", "-c", sql],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return proc.stdout.strip()


def _query_all_users(run_id: str, container: str) -> List[str]:
    raw = _psql(container, f"""
        SELECT user_id FROM experiment_trajectories
        WHERE experiment_run_id = '{run_id}'
        GROUP BY user_id ORDER BY MIN(interaction_number)
    """)
    return [l.strip() for l in raw.splitlines() if l.strip()]


def _eval_half(user_id: str) -> int:
    """Deterministic 50/50 user split — identical to probe_hcie_vs_deepmodels.half().

    eval = half 1 (held-out); train/prior = half 0 (the cold-start population-prior
    snapshot). Using this split makes the matched eval LEAK-FREE: the held-out users
    are never in the md5%2==0 half that built the prior, and pass01 shares pass02's split.

    Hash the STABLE canonical id = user_id minus the per-run 'run-XXXX::' prefix, so the
    split is identical across re-seals and matches the snapshot + probe_hcie_vs_deepmodels.half().
    """
    return int(hashlib.md5(user_id.rsplit("::", 1)[-1].encode()).hexdigest(), 16) % 2


def _query_sequences(
    run_id: str,
    container: str,
    user_list: List[str],
) -> Dict[str, List[Tuple[str, bool, int]]]:
    uid_list = ", ".join(f"'{u}'" for u in user_list)
    raw = _psql(container, f"""
        SELECT user_id, concept, correctness, interaction_number
        FROM experiment_trajectories
        WHERE experiment_run_id = '{run_id}'
          AND user_id IN ({uid_list})
          AND concept IS NOT NULL AND correctness IS NOT NULL
        ORDER BY user_id, interaction_number
    """)
    seqs: Dict[str, List[Tuple[str, bool, int]]] = defaultdict(list)
    for line in raw.splitlines():
        parts = line.strip().split("|")
        if len(parts) < 4:
            continue
        uid, concept, correct_raw, inter_n = parts[0], parts[1], parts[2], parts[3]
        correct = correct_raw.strip().lower() in ("t", "true", "1")
        try:
            n = int(inter_n)
        except ValueError:
            n = 0
        seqs[uid].append((concept, correct, n))
    for uid in seqs:
        seqs[uid].sort(key=lambda x: x[2])
    return dict(seqs)


def _query_hcie_trajectories(
    run_id: str,
    container: str,
    user_list: List[str],
) -> Dict[str, List[Tuple[float, bool, int]]]:
    """Query mastery_before (prediction) and correctness for specified users.

    Returns per-user list of (mastery_before, correct, interaction_number).
    mastery_before is HCIE's prediction signal — ensemble mastery estimate
    before the interaction, used as P(correct) proxy.
    """
    uid_list = ", ".join(f"'{u}'" for u in user_list)
    raw = _psql(container, f"""
        SELECT user_id, mastery_before, correctness, interaction_number
        FROM experiment_trajectories
        WHERE experiment_run_id = '{run_id}'
          AND user_id IN ({uid_list})
          AND mastery_before IS NOT NULL
          AND correctness IS NOT NULL
        ORDER BY user_id, interaction_number
    """)
    seqs: Dict[str, List[Tuple[float, bool, int]]] = defaultdict(list)
    for line in raw.splitlines():
        parts = line.strip().split("|")
        if len(parts) < 4:
            continue
        uid, mastery_raw, correct_raw, inter_n = parts[0], parts[1], parts[2], parts[3]
        try:
            mastery = float(mastery_raw)
        except (ValueError, TypeError):
            continue
        correct = correct_raw.strip().lower() in ("t", "true", "1")
        try:
            n = int(inter_n)
        except ValueError:
            n = 0
        seqs[uid].append((mastery, correct, n))
    for uid in seqs:
        seqs[uid].sort(key=lambda x: x[2])
    return dict(seqs)


def _evaluate_hcie(
    trajectories: Dict[str, List[Tuple[float, bool, int]]],
) -> Dict[str, Any]:
    """Evaluate HCIE using mastery_before as prediction, matching baseline protocol.

    Uses same cold-start windows and AUC computation as _evaluate().
    """
    yt_w: Dict[int, List[int]] = {w: [] for w in COLD_START_WINDOWS}
    ys_w: Dict[int, List[float]] = {w: [] for w in COLD_START_WINDOWS}
    yt_all: List[int] = []
    ys_all: List[float] = []

    for uid, seq in trajectories.items():
        for idx, (mastery, correct, _) in enumerate(seq):
            for w in COLD_START_WINDOWS:
                if idx < w:
                    yt_w[w].append(int(correct))
                    ys_w[w].append(mastery)
            yt_all.append(int(correct))
            ys_all.append(mastery)

    results: Dict[str, Any] = {}
    for w in COLD_START_WINDOWS:
        results[f"window_{w}"] = _metrics(yt_w[w], ys_w[w], w)
    results["overall"] = _metrics(yt_all, ys_all, -1)
    return results


def _query_hcie_aucs_all_users(run_id: str, container: str) -> Dict[int, Optional[float]]:
    """Query pre-computed HCIE AUC over all run users (reference only, not for primary table)."""
    raw = _psql(container, f"""
        SELECT cold_start_window, auc FROM kt_prediction_evaluations
        WHERE experiment_run_id = '{run_id}' AND model_id = 'hcie'
        ORDER BY cold_start_window
    """)
    out: Dict[int, Optional[float]] = {}
    for line in raw.splitlines():
        parts = line.strip().split("|")
        if len(parts) >= 2:
            try:
                w = int(parts[0]) if parts[0] else -1
                out[w] = float(parts[1]) if parts[1] else None
            except ValueError:
                pass
    return out


# ---------------------------------------------------------------------------
# AUC computation
# ---------------------------------------------------------------------------

def _auc(y_true: List[int], y_score: List[float]) -> Optional[float]:
    """Rank-AUC with averaged-rank tie handling (sklearn.roc_auc_score-equivalent).

    Tied scores receive the AVERAGE rank, so coincidentally-equal predictions get
    fractional (0.5) pair credit instead of the optimistic full credit. This is the
    standard convention and matches probe_hcie_vs_deepmodels.py's ``auc()`` — one
    tie-handling convention across every eval script (see Rekomendasi A).
    """
    n = len(y_true)
    if n == 0:
        return None
    pos = sum(y_true)
    neg = n - pos
    if pos == 0 or neg == 0:
        return None
    order = sorted(range(n), key=lambda i: y_score[i])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and y_score[order[j + 1]] == y_score[order[i]]:
            j += 1
        avg_rank = (i + j) / 2.0 + 1.0
        for kk in range(i, j + 1):
            ranks[order[kk]] = avg_rank
        i = j + 1
    return (sum(ranks[k] for k in range(n) if y_true[k] == 1) - pos * (pos + 1) / 2.0) / (pos * neg)


def _brier(y_true: List[int], y_score: List[float]) -> Optional[float]:
    if not y_true:
        return None
    return sum((s - t) ** 2 for t, s in zip(y_true, y_score)) / len(y_true)


def _accuracy(y_true: List[int], y_score: List[float], thr: float = 0.5) -> Optional[float]:
    if not y_true:
        return None
    return sum(1 for t, s in zip(y_true, y_score) if (s >= thr) == bool(t)) / len(y_true)


def _logloss(y_true: List[int], y_score: List[float], eps: float = 1e-12) -> Optional[float]:
    import math
    if not y_true:
        return None
    tot = 0.0
    for t, s in zip(y_true, y_score):
        s = min(1.0 - eps, max(eps, s))
        tot += -(t * math.log(s) + (1 - t) * math.log(1.0 - s))
    return tot / len(y_true)


def _metrics(y_true: List[int], y_score: List[float], window: int) -> Dict[str, Any]:
    """AUC (unchanged) + Brier + accuracy + log-loss from the SAME arrays."""
    return {
        "window": window,
        "n": len(y_true),
        "auc": _auc(y_true, y_score),
        "brier": _brier(y_true, y_score),
        "accuracy": _accuracy(y_true, y_score),
        "log_loss": _logloss(y_true, y_score),
    }


# ---------------------------------------------------------------------------
# Generic evaluate loop
# ---------------------------------------------------------------------------

def _evaluate(
    model,
    sequences: Dict[str, List[Tuple[str, bool, int]]],
) -> Dict[str, Any]:
    yt_w: Dict[int, List[int]] = {w: [] for w in COLD_START_WINDOWS}
    ys_w: Dict[int, List[float]] = {w: [] for w in COLD_START_WINDOWS}
    yt_all: List[int] = []
    ys_all: List[float] = []

    for uid, seq in sequences.items():
        for idx, (concept, correct, _) in enumerate(seq):
            prob = model.predict(uid, concept, idx)
            model.observe(uid, concept, idx, correct)
            for w in COLD_START_WINDOWS:
                if idx < w:
                    yt_w[w].append(int(correct))
                    ys_w[w].append(prob)
            yt_all.append(int(correct))
            ys_all.append(prob)

    results: Dict[str, Any] = {}
    for w in COLD_START_WINDOWS:
        results[f"window_{w}"] = _metrics(yt_w[w], ys_w[w], w)
    results["overall"] = _metrics(yt_all, ys_all, -1)
    return results


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------

def _fmt(v: Optional[float]) -> str:
    return f"{v:.4f}" if v is not None else "—"


def _render_md(
    primary_rows: List[Dict],
    phase1_ref: Dict,
    phase1_all_users: Dict[int, Optional[float]],
    phase2_all_users: Dict[int, Optional[float]],
    generated_at: str,
    phase1_run: str,
    phase2_run: str,
    n_train: int,
    n_eval: int,
) -> str:
    lines = [
        "# Baseline Comparison: Cold-Start AUC on Junyi 2015 (Matched Evaluation)",
        "",
        f"*Generated: {generated_at}*",
        "",
        "## Evaluation Protocol",
        "",
        f"- Dataset: `junyi_2015_graph` (837 concepts, 1,052 DAG edges)",
        f"- Phase 2 run: `{phase2_run[:20]}…` (graph injected)",
        f"- Train split: first {n_train} users by Phase 2 run ordering (used for DKT/SAKT/GKT training)",
        f"- Eval split: next {n_eval} held-out users (same for ALL models)",
        f"- HCIE Phase 2 prediction: `mastery_before` from `experiment_trajectories` for the same {n_eval} eval users",
        f"- All models evaluated at cold-start windows ≤5, ≤10, ≤20, and overall",
        "",
        "## Table 1 — Primary Comparison (Matched: same held-out users, same windows)",
        "",
        "| Model | ≤5 AUC | ≤10 AUC | ≤20 AUC | Overall AUC | Notes |",
        "|-------|--------|---------|---------|-------------|-------|",
    ]
    for r in primary_rows:
        note = r.get("note", "")
        lines.append(
            f"| {r['model']} | {_fmt(r.get('w5'))} | {_fmt(r.get('w10'))} | "
            f"{_fmt(r.get('w20'))} | {_fmt(r.get('overall'))} | {note} |"
        )
    lines += [
        "",
        "## Table 2 — HCIE Causal Delta (Phase 1 → Phase 2, reference only)",
        "",
        "Phase 1 and Phase 2 run different user populations; this table shows the",
        "within-system effect of graph injection, not a direct cross-model comparison.",
        "",
        "| Config | ≤5 AUC | ≤10 AUC | ≤20 AUC | Overall AUC | Population |",
        "|--------|--------|---------|---------|-------------|------------|",
        f"| HCIE Phase 1 (no graph) | {_fmt(phase1_ref.get('w5'))} | {_fmt(phase1_ref.get('w10'))} | "
        f"{_fmt(phase1_ref.get('w20'))} | {_fmt(phase1_ref.get('overall'))} | held-out users from Phase 1 run |",
        f"| HCIE Phase 2 (graph injected) | {_fmt(phase2_all_users.get(5))} | {_fmt(phase2_all_users.get(10))} | "
        f"{_fmt(phase2_all_users.get(20))} | {_fmt(phase2_all_users.get(-1))} | all Phase 2 users (pre-computed) |",
    ]

    # Compute deltas if available
    p1_w5, p2_w5 = phase1_ref.get("w5"), phase2_all_users.get(5)
    p1_ov, p2_ov = phase1_ref.get("overall"), phase2_all_users.get(-1)
    if p1_w5 is not None and p2_w5 is not None:
        lines += [
            "",
            f"*Graph injection effect: ≤5 Δ={p2_w5 - p1_w5:+.4f}, "
            f"overall Δ={p2_ov - p1_ov:+.4f}*" if (p1_ov is not None and p2_ov is not None) else "",
        ]

    lines += [
        "",
        "## Model Notes",
        "",
        "- **BKT**: Corbett & Anderson (1995); Yudelson 2013 cold-start priors; no training required",
        "- **DKT**: Piech et al. (2015) LSTM; trained 15 epochs on first 17 Phase 2 users",
        "- **SAKT**: Pandey & Karypis (2019) transformer; trained 15 epochs on same 17 users",
        f"- **GKT**: Zhang et al. (2020) via pyKT; trained 15 epochs on same 17 users with Junyi DAG",
        "- **HCIE Phase 2**: zero-shot mastery tracking; `mastery_before` used as P(correct) proxy",
        "  — same {n_eval} held-out users, same cold-start windows as baselines",
        "- **HCIE Phase 1**: evaluated on equivalent held-out positions from Phase 1 run",
        "  (different user population — causal reference only)",
        "- Graph-DKT / HELP-DKT: not available (pyKT not installed in evaluation environment)",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase2-run-id", default="run-94a3b8ba-015b-4d84-b288-004fe60bc282")
    parser.add_argument("--phase1-run-id", default="run-217532ca-39e6-4859-a41f-88ed53e904a2")
    parser.add_argument("--train-users", type=int, default=17)
    parser.add_argument("--eval-users", type=int, default=10)
    parser.add_argument("--postgres-container", default="hcie-final-postgres")
    parser.add_argument("--artifact-dir", type=Path, default=None)
    parser.add_argument(
        "--output-dir", type=Path,
        default=HERE.parent / "reports" / "baseline_comparison",
    )
    args = parser.parse_args()

    generated_at = datetime.now(timezone.utc).isoformat()
    root = args.artifact_dir or default_artifact_root()

    # --- Define train/eval split from Phase 2 run ---
    print("[eval] querying held-out users from Phase 2 run…")
    all_users_p2 = _query_all_users(args.phase2_run_id, args.postgres_container)
    # LEAK-FREE md5 split (Option A): held-out eval = md5(user)%2==1, disjoint from the
    # md5%2==0 train half that builds the cold-start population-prior snapshot. Matches
    # probe_hcie_vs_deepmodels so pass01 and pass02 share one prior. Cohort = first N.
    eval_half_p2 = [u for u in all_users_p2 if _eval_half(u) == 1]
    eval_users = eval_half_p2[: args.eval_users]
    print(f"[eval] total={len(all_users_p2)}, eval-half(md5%2==1)={len(eval_half_p2)}, eval={len(eval_users)}")

    # --- Query interaction sequences for baselines (concept+correctness) ---
    sequences = _query_sequences(args.phase2_run_id, args.postgres_container, eval_users)
    total = sum(len(v) for v in sequences.values())
    print(f"[eval] eval sequences: {len(sequences)} users, {total} attempts")

    # --- Query HCIE trajectories (mastery_before+correctness) for the same eval users ---
    print("[eval] querying HCIE Phase 2 trajectories for eval users…")
    hcie_p2_traj = _query_hcie_trajectories(args.phase2_run_id, args.postgres_container, eval_users)
    hcie_p2_n = sum(len(v) for v in hcie_p2_traj.values())
    print(f"[eval] HCIE Phase 2 trajectories: {len(hcie_p2_traj)} users, {hcie_p2_n} attempts with mastery_before")

    # --- Phase 1: equivalent held-out users (causal-delta reference) ---
    print("[eval] querying HCIE Phase 1 held-out users…")
    all_users_p1 = _query_all_users(args.phase1_run_id, args.postgres_container)
    eval_users_p1 = [u for u in all_users_p1 if _eval_half(u) == 1][: args.eval_users]
    hcie_p1_traj = _query_hcie_trajectories(args.phase1_run_id, args.postgres_container, eval_users_p1)
    print(f"[eval] HCIE Phase 1 trajectories: {len(hcie_p1_traj)} users "
          f"(positions {args.train_users}–{args.train_users + len(eval_users_p1)} of Phase 1 run)")

    # --- Pre-computed all-user AUC (sanity check / reporting) ---
    print("[eval] querying pre-computed all-user AUC (reference only)…")
    hcie_p1_all = _query_hcie_aucs_all_users(args.phase1_run_id, args.postgres_container)
    hcie_p2_all = _query_hcie_aucs_all_users(args.phase2_run_id, args.postgres_container)

    # --- Evaluate baselines on same eval users ---
    model_results: Dict[str, Dict[str, Any]] = {}

    print("[eval] evaluating BKT…")
    model_results["bkt"] = _evaluate(BKTBaseline(), sequences)

    print("[eval] evaluating DKT…")
    try:
        model_results["dkt"] = _evaluate(DKTBaseline(dataset_id=DATASET_ID, artifact_dir=str(root)), sequences)
    except FileNotFoundError as e:
        print(f"[eval] DKT checkpoint missing: {e}", file=sys.stderr)
        model_results["dkt"] = {"error": str(e)}

    print("[eval] evaluating SAKT…")
    try:
        model_results["sakt"] = _evaluate(SAKTBaseline(dataset_id=DATASET_ID, artifact_dir=str(root)), sequences)
    except FileNotFoundError as e:
        print(f"[eval] SAKT checkpoint missing: {e}", file=sys.stderr)
        model_results["sakt"] = {"error": str(e)}

    print("[eval] evaluating GKT…")
    try:
        model_results["gkt"] = _evaluate(GKTBaseline(dataset_id=DATASET_ID, artifact_dir=str(root)), sequences)
    except Exception as e:
        print(f"[eval] GKT error: {e}", file=sys.stderr)
        model_results["gkt"] = {"error": str(e)}

    # --- Evaluate HCIE on same eval users (matched protocol) ---
    print("[eval] evaluating HCIE Phase 2 (matched eval users, mastery_before)…")
    model_results["hcie_p2_matched"] = _evaluate_hcie(hcie_p2_traj)

    print("[eval] evaluating HCIE Phase 1 (reference, equivalent positions from P1 run)…")
    model_results["hcie_p1_ref"] = _evaluate_hcie(hcie_p1_traj)

    # --- Print summary ---
    print(f"\n{'='*70}")
    print("TABLE 1 — PRIMARY COMPARISON (matched: same held-out users, same windows)")
    print(f"{'='*70}")
    print(f"{'Model':<20} {'≤5':>8} {'≤10':>8} {'≤20':>8} {'Overall':>10}")
    print(f"{'-'*60}")

    def _print_row(label: str, res: Dict) -> None:
        if "error" in res:
            print(f"  {label:<18} ERROR: {res['error'][:40]}")
            return
        w5 = res.get("window_5", {}).get("auc")
        w10 = res.get("window_10", {}).get("auc")
        w20 = res.get("window_20", {}).get("auc")
        ov = res.get("overall", {}).get("auc")
        print(f"  {label:<18} {_fmt(w5):>8} {_fmt(w10):>8} {_fmt(w20):>8} {_fmt(ov):>10}")

    for mid, label in [("bkt", "bkt"), ("dkt", "dkt"), ("sakt", "sakt"), ("gkt", "gkt")]:
        _print_row(label, model_results[mid])
    _print_row("HCIE-P2 (matched)", model_results["hcie_p2_matched"])
    print(f"\n{'='*70}")
    print("TABLE 2 — HCIE CAUSAL DELTA (reference; different user populations)")
    print(f"{'='*70}")
    _print_row("HCIE-P1 (ref)", model_results["hcie_p1_ref"])
    _print_row("HCIE-P2 (ref, all)", {
        "window_5": {"auc": hcie_p2_all.get(5)},
        "window_10": {"auc": hcie_p2_all.get(10)},
        "window_20": {"auc": hcie_p2_all.get(20)},
        "overall": {"auc": hcie_p2_all.get(-1)},
    })
    print(f"{'='*70}\n")

    # --- Build rows for MD rendering ---
    def _row(mid: str, res: Dict, label: str, note: str = "") -> Dict:
        if "error" in res:
            return {"model": label, "note": f"ERROR: {res['error'][:40]}",
                    "w5": None, "w10": None, "w20": None, "overall": None}
        return {
            "model": label,
            "note": note,
            "w5": res.get("window_5", {}).get("auc"),
            "w10": res.get("window_10", {}).get("auc"),
            "w20": res.get("window_20", {}).get("auc"),
            "overall": res.get("overall", {}).get("auc"),
            "n_overall": res.get("overall", {}).get("n"),
        }

    primary_rows = [
        _row("bkt",  model_results["bkt"],  "BKT",              "trained on 17 Phase 2 users (Corbett & Anderson 1995)"),
        _row("dkt",  model_results["dkt"],  "DKT",              "trained on 17 Phase 2 users (Piech et al. 2015)"),
        _row("sakt", model_results["sakt"], "SAKT",             "trained on 17 Phase 2 users (Pandey & Karypis 2019)"),
        _row("gkt",  model_results["gkt"],  "GKT (graph-aware)","trained on 17 Phase 2 users + Junyi DAG (Zhang et al. 2020)"),
        _row("hcie_p2_matched", model_results["hcie_p2_matched"], "HCIE Phase 2",
             "zero-shot; mastery_before as P(correct); same 10 eval users"),
    ]

    p1_ref = _row("hcie_p1_ref", model_results["hcie_p1_ref"], "HCIE Phase 1")

    # --- Save ---
    args.output_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "generated_at": generated_at,
        "phase2_run_id": args.phase2_run_id,
        "phase1_run_id": args.phase1_run_id,
        "train_users": args.train_users,
        "eval_users": len(eval_users),
        "eval_user_list": eval_users,
        "eval_users_p1": eval_users_p1,
        "split_method": (
            "LEAK-FREE md5(user_id)%2: eval = held-out half 1; train/prior = half 0 "
            "(the cold-start population-prior snapshot). Identical split to "
            "probe_hcie_vs_deepmodels so pass01 and pass02 share one prior; held-out "
            "users are never in the prior. n=10/40/76 cohorts are the first N of half 1."
        ),
        "protocol_note": (
            "Matched evaluation: BKT/DKT/SAKT/GKT and HCIE Phase 2 all evaluated on "
            "the same held-out user list (md5%2==1), same cold-start windows, same AUC computation. "
            "HCIE Phase 2 uses mastery_before as prediction signal. "
            "HCIE Phase 1 is the md5%2==1 held-out of the Phase 1 run "
            "(different user population; causal-delta reference only)."
        ),
        "model_results": model_results,
        "hcie_p2_all_users_auc": hcie_p2_all,
        "hcie_p1_all_users_auc": hcie_p1_all,
        "primary_rows": primary_rows,
        "phase1_ref_row": p1_ref,
    }
    (args.output_dir / "comparison_table.json").write_text(
        json.dumps(report, indent=2, default=str), encoding="utf-8"
    )
    md = _render_md(
        primary_rows=primary_rows,
        phase1_ref=p1_ref,
        phase1_all_users=hcie_p1_all,
        phase2_all_users=hcie_p2_all,
        generated_at=generated_at,
        phase1_run=args.phase1_run_id,
        phase2_run=args.phase2_run_id,
        n_train=args.train_users,
        n_eval=len(eval_users),
    )
    (args.output_dir / "comparison_table.md").write_text(md, encoding="utf-8")
    print(f"[eval] wrote {args.output_dir / 'comparison_table.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
