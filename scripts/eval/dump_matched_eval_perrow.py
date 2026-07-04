#!/usr/bin/env python3
"""Dump the PER-ROW scored matched-eval matrix (run-94a3b8ba) for AUC-CI + calibration figures.

Reuses evaluate_all_baselines_auc.py's exact eval set + baseline scorers (predict->observe loop),
adds the canonical lagged-Kalman HCIE predictor (P(correct,t)=kalman_mastery_after[t-1]; t=0=cold-start
mastery_before), and writes one row per (user, interaction): y_true + each model's predicted prob.

Models: HCIE (lagged-Kalman, canonical), BKT, DKT, SAKT, GKT — the MATCHED-eval set (Tabel 4.8).
(IRT is NOT in the matched eval; it only appears in the cross-dataset matrix.)

Read-only on the DB. Output: CSV + JSON manifest. Run with the stack's Postgres up.
"""
import csv, json, sys
from collections import defaultdict
from pathlib import Path

RV = Path(__file__).resolve().parents[1]          # research_validation/
sys.path.insert(0, str(RV))
import evaluate_all_baselines_auc as E             # reuse its queries + baseline classes

CONTAINER = "hcie-final-postgres"
WINDOWS = [5, 10, 20]
# argv[1] = comparison_table.json (default = the 10-user matched eval); argv[2] = output CSV name
COMP = Path(sys.argv[1]) if len(sys.argv) > 1 else RV / "reports" / "baseline_comparison" / "comparison_table.json"
OUT_DIR = Path(r"C:/Users/Farros/Downloads/thesis_audit")
OUT_CSV_NAME = sys.argv[2] if len(sys.argv) > 2 else "matched_eval_perrow_run-94a3b8ba.csv"


def hcie_lagged_perrow(run_id, eval_users):
    """{(uid, inter_n): p_hcie} via lagged-Kalman, matching probe_lagged_kalman_auc.py."""
    uid_list = ", ".join("'" + u.replace("'", "") + "'" for u in eval_users)
    raw = E._psql(CONTAINER, f"""
        SELECT user_id, kalman_mastery_after, mastery_before, correctness, interaction_number
        FROM experiment_trajectories
        WHERE experiment_run_id = '{run_id}' AND user_id IN ({uid_list})
          AND kalman_mastery_after IS NOT NULL AND correctness IS NOT NULL
        ORDER BY user_id, interaction_number
    """)
    seqs = defaultdict(list)
    for line in raw.splitlines():
        p = line.strip().split("|")
        if len(p) < 5:
            continue
        uid, kal_raw, mb_raw, _corr, inter = p[:5]
        try:
            kal = float(kal_raw); mb = float(mb_raw) if mb_raw not in ("", None) else kal; n = int(inter)
        except (ValueError, TypeError):
            continue
        seqs[uid].append((kal, mb, n))
    for uid in seqs:
        seqs[uid].sort(key=lambda x: x[2])
    out = {}
    for uid, seq in seqs.items():
        for idx, (kal, mb, n) in enumerate(seq):
            out[(uid, n)] = mb if idx == 0 else seq[idx - 1][0]   # lagged-Kalman
    return out


def baseline_perrow(model, sequences):
    """{(uid, inter_n): prob} from the predict->observe loop (same as _evaluate)."""
    out = {}
    for uid, seq in sequences.items():
        for idx, (concept, correct, n) in enumerate(seq):
            prob = model.predict(uid, concept, idx)
            model.observe(uid, concept, idx, correct)
            out[(uid, n)] = prob
    return out


def main():
    comp = json.loads(COMP.read_text(encoding="utf-8"))
    run_id = comp["phase2_run_id"]
    eval_users = comp["eval_user_list"]
    print(f"[dump] run={run_id} eval_users={len(eval_users)}")

    sequences = E._query_sequences(run_id, CONTAINER, eval_users)
    print(f"[dump] sequences: {len(sequences)} users, {sum(len(v) for v in sequences.values())} rows")

    root = str(E.default_artifact_root())
    DS = E.DATASET_ID
    cols = {}                      # model -> {(uid,n): prob}
    avail = {}
    cols["hcie"] = hcie_lagged_perrow(run_id, eval_users); avail["hcie"] = True
    cols["bkt"] = baseline_perrow(E.BKTBaseline(), sequences); avail["bkt"] = True
    for name, ctor in [("dkt", lambda: E.DKTBaseline(dataset_id=DS, artifact_dir=root)),
                       ("sakt", lambda: E.SAKTBaseline(dataset_id=DS, artifact_dir=root)),
                       ("gkt", lambda: E.GKTBaseline(dataset_id=DS, artifact_dir=root))]:
        try:
            cols[name] = baseline_perrow(ctor(), sequences); avail[name] = True
            print(f"[dump] {name}: scored {len(cols[name])} rows")
        except Exception as ex:
            cols[name] = {}; avail[name] = False
            print(f"[dump] {name} UNAVAILABLE: {str(ex)[:80]}", file=sys.stderr)

    # assemble per-row rows from the baseline master sequences (carry concept + position)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = OUT_DIR / OUT_CSV_NAME
    n_rows = 0
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["user_id", "interaction_number", "idx", "concept", "y_true",
                    "p_hcie", "p_bkt", "p_dkt", "p_sakt", "p_gkt",
                    "in_le5", "in_le10", "in_le20"])
        for uid, seq in sequences.items():
            for idx, (concept, correct, n) in enumerate(seq):
                key = (uid, n)
                def g(m): return cols[m].get(key, "")
                w.writerow([uid, n, idx, concept, int(correct),
                            g("hcie"), g("bkt"), g("dkt"), g("sakt"), g("gkt"),
                            int(idx < 5), int(idx < 10), int(idx < 20)])
                n_rows += 1
    manifest = {
        "source_run": run_id,
        "note": "Matched cold-start eval (Tabel 4.8). HCIE=lagged-Kalman canonical (kalman_mastery_after[t-1]; t=0=cold-start mastery_before). Baselines via predict->observe loop. IRT not in matched eval.",
        "n_eval_users": len(eval_users), "n_rows": n_rows,
        "models_available": avail,
        "windows": "in_le5/10/20 = cumulative cold-start windows (idx<w); 'overall' = all rows",
        "y_true": "correctness (1=benar, 0=salah)", "scores": "predicted P(correct) per model in [0,1]",
    }
    (OUT_DIR / "matched_eval_perrow_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[dump] wrote {csv_path} ({n_rows} rows); available={avail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
