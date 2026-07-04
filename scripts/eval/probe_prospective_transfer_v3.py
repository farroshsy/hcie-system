#!/usr/bin/env python3
"""Estimator-v3: same-family vs cross-family split (see TRANSFER_PROSPECTIVE_SPEC.md).

v2 found the durable topology effect holds at ~0.14 even with within-learner FE + state controls —
far above the paper's +0.020. The paper's own caveat names the likely cause: the signal is "carried by
a minority of strong, same-skill-family prerequisites; a typical individual edge is indistinguishable
from a shuffled one." This script tests that directly by splitting the DURABLE effect into:

  - durable_SAME  = mastered a same-skill-family prerequisite  (e.g. multiplication_2 -> multiplication_3;
                    near-tautological — shared name-stem OR same topic)
  - durable_CROSS = mastered a genuinely different-concept prerequisite  (the interesting transfer)

If b_durable_CROSS ~ +0.02  -> the paper's number is validated AND explained (it was the cross-family effect).
If b_durable_CROSS also large -> a bigger, riskier finding; the +0.020 understated it.
Either way, b_durable_CROSS (with its permutation p) is the committed, reproducible C magnitude that
supersedes the paper's lost +0.020.

Offline + read-only on the three Junyi CSVs. No live code, no DB. Builds on v2's controls.

Usage:  python probe_prospective_transfer_v3.py --rate 4 --permutations 1000 --out v3.json
"""
from __future__ import annotations

import argparse
import bisect
import csv
import hashlib
import json
import math
import re
import sys
from collections import defaultdict, deque
from pathlib import Path

import numpy as np

DEFAULT_DATA = Path(r"D:\Code\cld-main\cld-main\ProjectHCIE\RealSystem\junyi")
LOG_FILE = "junyi_ProblemLog_original.csv"
EX_FILE = "junyi_Exercise_table.csv"
SESSION_GAP_US = 1800 * 1_000_000
RECENT_WINDOW = 10
_STEM = re.compile(r"[_\s]*\d+$")


def stem(name: str) -> str:
    return _STEM.sub("", name)


def load_dag(data: Path):
    prereq, universe, topic = {}, set(), {}
    with (data / EX_FILE).open(encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            name = (row.get("name") or "").strip()
            if not name:
                continue
            universe.add(name)
            topic[name] = (row.get("topic") or "").strip()
            pres = [p.strip() for p in (row.get("prerequisites") or "").split(",") if p.strip()]
            if pres:
                prereq[name] = pres
    uni = sorted(universe)
    cstem = {c: stem(c) for c in uni}
    return prereq, uni, topic, cstem


def same_family(c, p, topic, cstem) -> bool:
    if cstem.get(c) and cstem.get(c) == cstem.get(p):
        return True
    tc = topic.get(c)
    return bool(tc) and tc == topic.get(p)


def _sampled(uid, rate):
    if rate <= 1:
        return True
    return (int(hashlib.md5(uid.encode()).hexdigest(), 16) % rate) == 0


def stream_user_events(data, rate, row_limit):
    users = defaultdict(list)
    seen = kept = 0
    with (data / LOG_FILE).open(encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            seen += 1
            if row_limit and seen > row_limit:
                break
            uid = (row.get("user_id") or "").strip()
            if not uid or not _sampled(uid, rate):
                continue
            ex = (row.get("exercise") or "").strip()
            traw = (row.get("time_done") or "").strip()
            if not ex or not traw:
                continue
            try:
                t = int(traw)
            except ValueError:
                continue
            correct = (row.get("correct") or "").strip().lower() in ("true", "t", "1")
            users[uid].append((t, ex, correct))
            kept += 1
            if seen % 4_000_000 == 0:
                print(f"  ...scanned {seen:,}, kept {kept:,}", file=sys.stderr)
    print(f"  scanned {seen:,}, kept {kept:,} from {len(users):,} users", file=sys.stderr)
    return users


def build(users, prereq, topic, cstem):
    rows = []
    correct_times = {}
    for uid, evs in users.items():
        evs.sort()
        ct = defaultdict(list)
        seen = set()
        exp = 0
        recent = deque(maxlen=RECENT_WINDOW)
        for (t, ex, c) in evs:
            if ex not in seen:
                seen.add(ex)
                if ex in prereq:
                    dur_same = dur_cross = prox = 0.0
                    for p in prereq[ex]:
                        times = ct.get(p)
                        if not times or times[0] >= t:
                            continue
                        is_prox = times[-1] >= t - SESSION_GAP_US
                        if is_prox:
                            prox = 1.0
                        else:  # durable
                            if same_family(ex, p, topic, cstem):
                                dur_same = 1.0
                            else:
                                dur_cross = 1.0
                    rr = (sum(recent) / len(recent)) if recent else 0.5
                    rows.append({"uid": uid, "C": ex, "T": t, "y": 1.0 if c else 0.0,
                                 "exp": math.log1p(exp), "recent": rr, "prox": prox,
                                 "dur_same": dur_same, "dur_cross": dur_cross})
            exp += 1
            recent.append(1 if c else 0)
            if c:
                ct[ex].append(t)
        correct_times[uid] = ct
    return rows, correct_times


def shuffle_dag(prereq, universe, rng):
    return {c: [universe[rng.randrange(len(universe))] for _ in pres] for c, pres in prereq.items()}


def treat_split(rows, ct_by_user, dag, topic, cstem):
    """(durable_same, durable_cross) arrays under an arbitrary DAG."""
    ds = np.zeros(len(rows)); dc = np.zeros(len(rows))
    for i, r in enumerate(rows):
        ct = ct_by_user[r["uid"]]; T = r["C"], r["T"]
        C, t = T
        s = x = 0.0
        for p in dag.get(C, ()):
            times = ct.get(p)
            if not times or times[0] >= t:
                continue
            j = bisect.bisect_left(times, t)
            is_prox = j > 0 and times[j - 1] >= t - SESSION_GAP_US
            if is_prox:
                continue
            if same_family(C, p, topic, cstem):
                s = 1.0
            else:
                x = 1.0
        ds[i] = s; dc[i] = x
    return ds, dc


def treat_future_cross(rows, ct_by_user, prereq, topic, cstem):
    """PLACEBO: mastered a cross-family prereq for the FIRST time at/after C — causally impossible
    to have helped C. If this predicts C-success like the past-mastery term, the effect is learner
    state/selection (good learners eventually master prereqs), NOT causal transfer."""
    fc = np.zeros(len(rows))
    for i, r in enumerate(rows):
        ct = ct_by_user[r["uid"]]; C, t = r["C"], r["T"]
        for p in prereq.get(C, ()):
            if same_family(C, p, topic, cstem):
                continue
            times = ct.get(p)
            if times and times[0] >= t:   # first correct on this cross prereq is AT/AFTER C
                fc[i] = 1.0
                break
    return fc


def within_demean(v, codes, ng):
    s = np.bincount(codes, weights=v, minlength=ng)
    cnt = np.bincount(codes, minlength=ng).astype(float)
    return v - (s / np.maximum(cnt, 1.0))[codes]


def fit_within(y, cols, codes, ng):
    yd = within_demean(y, codes, ng)
    Xd = np.column_stack([within_demean(c, codes, ng) for c in cols])
    beta, *_ = np.linalg.lstsq(Xd, yd, rcond=None)
    return beta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path, default=DEFAULT_DATA)
    ap.add_argument("--rate", type=int, default=4)
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--permutations", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=20260531)
    ap.add_argument("--row-limit", type=int, default=None)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    rate = 1 if args.full else args.rate
    import random
    rng = random.Random(args.seed)

    print("[1/4] DAG + topic", file=sys.stderr)
    prereq, universe, topic, cstem = load_dag(args.data_dir)
    print(f"[2/4] stream (rate=1/{rate})", file=sys.stderr)
    users = stream_user_events(args.data_dir, rate, args.row_limit)
    print("[3/4] build features (family split)", file=sys.stderr)
    rows, ct_by_user = build(users, prereq, topic, cstem)
    if len(rows) < 500:
        print(f"ABORT: only {len(rows)} rows.", file=sys.stderr); sys.exit(2)

    y = np.array([r["y"] for r in rows])
    exp = np.array([r["exp"] for r in rows])
    recent = np.array([r["recent"] for r in rows])
    prox = np.array([r["prox"] for r in rows])
    dur_same = np.array([r["dur_same"] for r in rows])
    dur_cross = np.array([r["dur_cross"] for r in rows])
    uids = sorted({r["uid"] for r in rows})
    code = {u: i for i, u in enumerate(uids)}          # build the index ONCE (was rebuilt per-row = O(rows*users))
    codes = np.array([code[r["uid"]] for r in rows])
    ng = len(uids)

    future_cross = treat_future_cross(rows, ct_by_user, prereq, topic, cstem)
    # observed: y ~ durable_cross + FUTURE_cross(placebo) + durable_same + proximity + exp + recent
    b = fit_within(y, [dur_cross, future_cross, dur_same, prox, exp, recent], codes, ng)
    b_cross, b_future, b_same, b_prox = b[0], b[1], b[2], b[3]

    print(f"[4/4] permutation null on durable_CROSS (K={args.permutations})", file=sys.stderr)
    null = np.empty(args.permutations)
    for k in range(args.permutations):
        ds, dc = treat_split(rows, ct_by_user, shuffle_dag(prereq, universe, rng), topic, cstem)
        null[k] = fit_within(y, [dc, future_cross, ds, prox, exp, recent], codes, ng)[0]
        if (k + 1) % 200 == 0:
            print(f"  perm {k+1}/{args.permutations}", file=sys.stderr)
    p_cross = (1 + int(np.sum(null >= b_cross))) / (args.permutations + 1)

    n_cross = int((dur_cross > 0).sum()); n_same = int((dur_same > 0).sum())
    result = {
        "spec": "estimator-v3 same-family vs cross-family (within-learner FE + state controls)",
        "mode": "full" if args.full else f"1/{rate} sample", "n_rows": len(rows), "n_users": ng,
        "b_durable_CROSS_past": round(float(b_cross), 5),
        "b_FUTURE_cross_PLACEBO": round(float(b_future), 5),
        "placebo_ratio_future_over_past": round(float(b_future / b_cross), 3) if b_cross else None,
        "placebo_verdict": ("CAUSAL (future placebo ~0)" if abs(b_future) < 0.4 * abs(b_cross) else "STATE/SELECTION CONFOUND (future ~ past)"),
        "b_durable_SAME": round(float(b_same), 5),
        "b_proximity": round(float(b_prox), 5),
        "cross_perm_p": p_cross, "perm_K": args.permutations,
        "null_mean": round(float(null.mean()), 5), "null_sd": round(float(null.std()), 5),
        "n_rows_with_cross_durable": n_cross, "n_rows_with_same_durable": n_same,
        "family_def": "same = shared name-stem OR same topic; cross = otherwise",
        "interpretation": "if b_durable_CROSS ~ 0.02 -> validates+explains paper +0.020; if large -> bigger finding",
        "paper_target_cross": 0.007, "seed": args.seed,
    }
    print("\n" + json.dumps(result, indent=2))
    if args.out:
        args.out.write_text(json.dumps(result, indent=2))
        print(f"\nwrote {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
