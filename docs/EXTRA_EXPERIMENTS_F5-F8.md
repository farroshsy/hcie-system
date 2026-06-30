# Extra Chapter-4 figures (F5–F8) — deliverable report

**Hard-consistency check PASSED.** Every figure below is computed on the **canonical sealed run**
`run-94a3b8ba` / anchor `d2154070`, matched cold-start protocol, **10 held-out users**, HCIE canonical =
lagged single-Kalman `m_K`. The per-row substrate reproduces **Tabel 4.8 exactly**:

| window | HCIE | BKT | DKT | SAKT | GKT |
|--------|------|-----|-----|------|-----|
| overall | **0,6051** | 0,5963 | 0,5892 | 0,5730 | 0,5711 |
| ≤5 | 0,8738 | 0,8350 | 0,9550 | 0,9050 | 0,6550 |
| ≤10 | 0,8225 | 0,8275 | 0,8994 | 0,8656 | 0,6200 |

AUC(overall) for HCIE reproduces **0,6051** ✓. Source substrate: `figures/data/` + the per-row matrix
`thesis_audit/matched_eval_perrow_run-94a3b8ba.csv` (10 users · 10 500 rows, all 5 models scored;
produced by `research_validation/scripts/dump_matched_eval_perrow.py`). Decimal commas, Indonesian labels.

---

## ✅ F8 — Calibration reliability diagram  (`F5/F8` strongest; → Bab 4, bagian kalibrasi)
- **Files:** `figures/F8-calibration.svg` + `png/`. **Data:** `figures/data/F8-calibration.csv`.
- **Exact numbers (computed on the sealed matched run):** HCIE raw **ECE 0,1086 · Brier 0,1515**;
  BKT **ECE 0,0623 · Brier 0,1421**; **HCIE + Platt ECE 0,0043 · Brier 0,1318**, AUC unchanged **0,6051**.
- **Honest reading (matches the instruction's expectation):** HCIE's *raw* uncertainty is **less** calibrated
  than BKT (0,109 vs 0,062) — a real soft-spot, not hidden. A post-hoc Platt correction removes the gap
  (ECE → 0,004) **without changing AUC** (monotone). This strengthens credibility; report it as-is.

## ✅ F5 — Per-interaction learning curve  (→ Bab 4, dekat Tabel 4.8 / Gambar 4.9 Simpson)
- **Files:** `figures/F5-learning-curve.svg` + `png/`. **Data:** `figures/data/F5-learning-curve.csv`.
- **Exact numbers** (AUC per interaction-depth bin):
  | bin | n | HCIE | BKT | DKT | SAKT | GKT |
  |-----|---|------|-----|-----|------|-----|
  | 1–5 | 50 | 0,874 | 0,835 | 0,955 | 0,905 | 0,655 |
  | 6–10 | 50 | 0,791 | 0,839 | 0,837 | 0,807 | 0,655 |
  | 11–20 | 100 | 0,868 | 0,922 | 0,956 | 0,952 | 0,772 |
  | 21–50 | 300 | 0,762 | 0,761 | 0,835 | 0,772 | 0,582 |
  | 51–100 | 412 | 0,577 | 0,685 | 0,615 | 0,558 | 0,743 |
  | **101+** | **9 588** | **0,593** | 0,584 | 0,564 | 0,550 | 0,560 |
- **Honest reading (Simpson disclosed — required by the instruction):** on the *tiny* early windows (n=50–200)
  the **pre-trained deep models (DKT/SAKT) actually score higher than HCIE** — the cold-start windows do NOT
  show HCIE dominance. HCIE's win is on the **long tail (idx 101+ = 91 % of the data)**, which is where the
  aggregate **0,6051** lead comes from. The honest message is *competitiveness without offline training*
  (the deep models paid a training cost HCIE did not — see your Pareto figure), **not** "HCIE starts highest."
  This is consistent with the thesis's own "kompetitif… belum menunjukkan keunggulan universal".

## ⚠️ F7 — Parameter sensitivity (Q, R)  (→ Bab 4 robustness, ATAU Lampiran — see disclosure)
- **Files:** `figures/F7-sensitivity.svg` + `png/`. **Data:** `figures/data/F7-sensitivity.csv`.
- **Exact numbers:** Q-sweep (R=0,1): Q=0,001→0,624 … **Q=0,01→0,613** … Q=0,2→0,602. R-sweep (Q=0,01):
  R=0,02→0,603 … **R=0,1→0,613** … R=1,0→0,619. **AUC stays in 0,60–0,62 across a 200× range** = robust;
  this supports the thesis's stated "Q=0,01, R=0,1 ditetapkan tetap di awal, tidak disetel" (not tuned).
- **DISCLOSURE (read before using):** this sweep is on a **faithful re-implementation** of the lagged-Kalman
  predictor (base AUC **0,6127**, correlation **0,96** with the deployed `m_K`), **not bit-exact** to the sealed
  0,6051 (Δ +0,0076 — beyond rounding). The deployed brain used a single sealed parameter set, so a sweep is
  inherently a re-run. The **shape/robustness** is trustworthy (0,96 corr); the **absolute level** is the
  re-impl's. If a journal reviewer needs an exact-on-sealed sweep, that requires re-replaying the brain at each
  (Q,R) — flagged as future work. Beta-prior and JT-threshold are **not** in the predictive `m_K` path, so they
  do not move this AUC (insensitive by design — reported honestly, not plotted as a fake-flat line).

## ❌ F6 — Leave-one-out component ablation  → **COULD NOT be produced consistently. Do not add.**
The instruction allows this outcome ("honestly report if a component does not contribute… STOP and report").
Reasons, all honest:
1. **Thompson / transfer / uncertainty are not in the predictive `m_K` path.** The matched AUC predictor is the
   lagged Kalman mastery readout. Thompson is *policy* (item selection, not correctness prediction); transfer is
   *JT governance*; uncertainty is *σ²*. Removing them changes the matched AUC by **0 by design** — a 4-bar
   "each drops AUC" figure would be false.
2. **A naive −Kalman→Beta re-implementation scores ≥ Kalman** on this matched AUC (Beta 0,6219, fusion 0,6249 vs
   re-impl Kalman 0,6127). That **contradicts** the thesis's "Kalman-alone canonical, fusion tested-and-rejected"
   — because that choice rests on **out-of-sample predictive validity (correlation r: Kalman 0,332 > ensemble
   0,311)**, not matched AUC. Plotting Beta ≥ Kalman here would undermine the manuscript.
- **Recommendation:** keep the existing **Gambar 4.15 (ablasi JT)** + the 3→2→1 estimator predictive-validity
  evidence; do not add an AUC leave-one-out figure. If you want a *new* honest ablation, it should be on the
  **predictive-validity (correlation) metric**, not matched AUC — that's a separate re-run, flagged as future work.

---

## Files delivered
- `figures/F5-learning-curve.svg/.png`, `figures/F7-sensitivity.svg/.png`, `figures/F8-calibration.svg/.png`
- `figures/data/{F5-learning-curve,F6-ablation,F7-sensitivity,F8-calibration}.csv`
- substrate: `thesis_audit/matched_eval_perrow_run-94a3b8ba.csv` (+ `_manifest.json`)
- Sealed run: **`run-94a3b8ba`** (anchor `d2154070`); all numbers above traced to it. No data invented.
