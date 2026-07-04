#!/usr/bin/env python3
"""Lagged-Kalman HCIE AUC on the matched eval — re-baseline the headline to the ACTUAL canonical.

evaluate_all_baselines_auc.py scores HCIE from `mastery_before` (the 3-learner ensemble pre-update
synthesis) — the estimator the thesis REJECTS. The thesis canonical is Kalman alone (m_K). This probe
re-scores HCIE with the **lagged-Kalman** predictor (P(correct at t) = kalman_mastery_after[t-1]) on the
SAME eval users + windows + rank-AUC as the matched comparison, so the headline number reflects the
canonical the thesis actually defends.

Faithful-proxy note: the brain's per-learner Kalman *mastery_before* is NOT persisted (only the ensemble
mastery_before + per-learner *_after). The lagged posterior (kalman_mastery_after of the previous
interaction) is the faithful pre-update proxy for what the Kalman learner carried into step t. The first
interaction has no predecessor -> it uses the run's cold-start mastery_before[0] (learner-agnostic prior).

Reads comparison_table.json for the eval set + baseline AUCs; queries kalman_mastery_after via docker psql.
Read-only. Writes reports/baseline_comparison/lagged_kalman_auc.json + prints the table.
"""

import json
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parents[1]  # research_validation/
COMPARISON = REPO / "reports" / "baseline_comparison" / "comparison_table.json"
OUT = REPO / "reports" / "baseline_comparison" / "lagged_kalman_auc.json"
WINDOWS = [5, 10, 20]
CONTAINER = "hcie-final-postgres"


def _psql(sql: str) -> str:
    proc = subprocess.run(
        ["docker", "exec", CONTAINER, "psql", "-U", "hcie_user", "-d", "hcie", "-t", "-A", "-c", sql],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout or "psql failed")
    return proc.stdout.strip()


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


def _query(run_id: str, eval_users: List[str]) -> Dict[str, List[Tuple[float, float, int, int]]]:
    """Per-user [(kalman_after, mastery_before, correct, interaction_number)] ordered."""
    uid_list = ", ".join("'" + u.replace("'", "") + "'" for u in eval_users)
    raw = _psql(
        f"""
        SELECT user_id, kalman_mastery_after, mastery_before, correctness, interaction_number
        FROM experiment_trajectories
        WHERE experiment_run_id = '{run_id}'
          AND user_id IN ({uid_list})
          AND kalman_mastery_after IS NOT NULL
          AND correctness IS NOT NULL
        ORDER BY user_id, interaction_number
        """
    )
    seqs: Dict[str, List[Tuple[float, float, int, int]]] = defaultdict(list)
    for line in raw.splitlines():
        parts = line.strip().split("|")
        if len(parts) < 5:
            continue
        uid, kal_raw, mb_raw, corr_raw, inter = parts[:5]
        try:
            kal = float(kal_raw)
            mb = float(mb_raw) if mb_raw not in ("", None) else kal
            n = int(inter)
        except (ValueError, TypeError):
            continue
        correct = 1 if corr_raw.strip().lower() in ("t", "true", "1") else 0
        seqs[uid].append((kal, mb, correct, n))
    for uid in seqs:
        seqs[uid].sort(key=lambda x: x[3])
    return dict(seqs)


def _evaluate_lagged_kalman(seqs: Dict[str, List[Tuple[float, float, int, int]]]) -> Dict[str, Dict]:
    yt_w: Dict[int, List[int]] = {w: [] for w in WINDOWS}
    ys_w: Dict[int, List[float]] = {w: [] for w in WINDOWS}
    yt_all: List[int] = []
    ys_all: List[float] = []
    for _uid, seq in seqs.items():
        for idx, (kal, mb, correct, _n) in enumerate(seq):
            # Lagged-Kalman: prediction at t = Kalman posterior after t-1; t=0 -> cold-start prior.
            pred = mb if idx == 0 else seq[idx - 1][0]
            for w in WINDOWS:
                if idx < w:
                    yt_w[w].append(correct)
                    ys_w[w].append(pred)
            yt_all.append(correct)
            ys_all.append(pred)
    out: Dict[str, Dict] = {}
    for w in WINDOWS:
        out[f"window_{w}"] = {"n": len(yt_w[w]), "auc": _auc(yt_w[w], ys_w[w])}
    out["overall"] = {"n": len(yt_all), "auc": _auc(yt_all, ys_all)}
    return out


def main() -> int:
    import sys
    # Task 7b: optionally point at a powered companion's comparison_table.json (+ out path)
    comp_path = Path(sys.argv[1]) if len(sys.argv) > 1 else COMPARISON
    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else OUT
    comp = json.loads(comp_path.read_text(encoding="utf-8"))
    run_id = comp["phase2_run_id"]
    eval_users = comp["eval_user_list"]
    mr = comp.get("model_results", {})

    seqs = _query(run_id, eval_users)
    lagged = _evaluate_lagged_kalman(seqs)

    def auc(model: str, key: str) -> Optional[float]:
        return ((mr.get(model) or {}).get(key) or {}).get("auc")

    hcie_3l_overall = auc("hcie_p2_matched", "overall")
    lk_overall = lagged["overall"]["auc"]
    regressed = (lk_overall is not None and hcie_3l_overall is not None and lk_overall < hcie_3l_overall)

    payload = {
        "predictor": "lagged-Kalman (P(correct at t) = kalman_mastery_after[t-1]; t=0 -> cold-start prior)",
        "faithful_proxy_note": ("per-learner Kalman mastery_before is NOT persisted; the lagged posterior is "
                                "the faithful pre-update proxy for the Kalman canonical (m_K)"),
        "phase2_run_id": run_id,
        "n_eval_users": len(eval_users),
        "windows": {
            "overall": {
                "lagged_kalman": lk_overall,
                "hcie_3learner_mastery_before": hcie_3l_overall,
                "bkt": auc("bkt", "overall"), "dkt": auc("dkt", "overall"),
                "sakt": auc("sakt", "overall"), "gkt": auc("gkt", "overall"),
            },
        },
        "delta_vs_3learner_overall": (round(lk_overall - hcie_3l_overall, 4)
                                      if (lk_overall is not None and hcie_3l_overall is not None) else None),
        "regressed_vs_3learner": regressed,
    }
    for w in WINDOWS:
        payload["windows"][f"<= {w}"] = {
            "lagged_kalman": lagged[f"window_{w}"]["auc"],
            "hcie_3learner_mastery_before": auc("hcie_p2_matched", f"window_{w}"),
            "bkt": auc("bkt", f"window_{w}"), "dkt": auc("dkt", f"window_{w}"),
            "sakt": auc("sakt", f"window_{w}"), "gkt": auc("gkt", f"window_{w}"),
        }

    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {out_path}")
    print(f"\nLagged-Kalman HCIE vs baselines (matched eval, N_users={len(eval_users)}, run={run_id[:14]}):")
    print(f"{'window':>8} | {'LK-HCIE':>8} | {'3L-HCIE':>8} | {'BKT':>7} | {'DKT':>7} | {'SAKT':>7} | {'GKT':>7}")
    for label in ["overall", "<= 5", "<= 10", "<= 20"]:
        r = payload["windows"][label]
        def f(x): return f"{x:.4f}" if isinstance(x, (int, float)) else "  -  "
        print(f"{label:>8} | {f(r['lagged_kalman']):>8} | {f(r['hcie_3learner_mastery_before']):>8} | "
              f"{f(r['bkt']):>7} | {f(r['dkt']):>7} | {f(r['sakt']):>7} | {f(r['gkt']):>7}")
    print(f"\noverall delta (LK - 3L) = {payload['delta_vs_3learner_overall']}; "
          f"regressed_vs_3learner = {regressed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
