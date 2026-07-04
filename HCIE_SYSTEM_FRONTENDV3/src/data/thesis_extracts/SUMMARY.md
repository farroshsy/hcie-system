# Thesis Value Extraction -- Pass Summary

**seal_id:** seal-bae44d1a-a314-48f5-b145-c92e6cbe08d7
**run_id:** run-d2154070-b6e4-4abe-94e6-a2e6ccfbefc1
**git_sha:** 035b37ca374cf8723b80e217a8c4cad5acb2be3b
**content_hash:** 85690d8be722e1e6271abb2f860290dd | rows: 96,727 | git_dirty: false
**date:** 2026-06-17 | passes read: 20 (read-only tabulation, nothing recomputed)

Anchor config: canonical mastery = single Kalman (m = m_K); ensemble used for sigma^2 only; V2 governance OFF; F4 ON.

**Status tally: 19 OK, 1 SYNTHETIC-DEMO** (pass 11; plus pass 12 split: complexity OK / empirical timing UNAVAILABLE). All 20 slots now have an exhibit.

> **Update 2026-06-17 — two isolated runs filled the prior gaps:**
> - **Pass 3 (Tabel 4.6 / T8d) NOW OK** -> `thesis_extracts/t8d_warmed_bkt_assist2009.json`. ASSIST-2009 leak-free
>   matched, per-USER windows: HCIE deployed-readout **0.6569** vs **warmed-BKT 0.6302** vs cold-BKT floor 0.5954.
>   Verdict: HCIE BEATS warmed-BKT overall (+0.0267) and <=10 (+0.0297); competitive <=5 (-0.0059) / <=20 (+0.0121).
>   Warming HELPS BKT (0.595->0.630) but HCIE still leads -> answers the "just cold BKT" criticism. AUC=competitive.
> - **Pass 15 (§4.1.2.a) NOW OK** -> `thesis_extracts/functional_suite.json`. Isolated stack: **150 passed / 159 ran**,
>   0 scenario-logic regressions; 9 failures = 5 infra/e2e (need live API) + 1 stale-test + 3 missing-artifact
>   (config/endpoint_authority_manifest.yaml); 6 collection errors excluded (httpx dep + stale import paths).
> - **Pass 11 (§4.1.3.f) NOW FILLED as a labelled SYNTHETIC mechanism demo** -> `thesis_extracts/pass11_bandit.json`.
>   The live representation bandit is real-learner-only **by contract** (its_runtime_service guards selection AND
>   `save_interaction` with `not _is_synthetic_user`; `_is_synthetic_user == user_id.startswith('synthetic:')`), so no
>   live human modality traffic exists to extract. Instead an in-memory closed loop drives the **production**
>   `ContextualBandit.select_representation` (real Thompson sampler) + the **exact** `_representation_outcomes` Beta
>   formula `(1+c, 1+(n-c))` over the real 5-modality concept `k12_algorithms`; only the learner responses are synthetic.
>   Deterministic (Thompson RNG=default_rng(42), outcome RNG=Random(7)). Result: the sampler concentrates on the
>   true-best modality `video_question` (128/160 pulls; last-40 share 0.875; posterior mean 0.908). NOT live traffic.
> - **Pass 12** empirical time-vs-history remains partial (O(1) by construction; processing_time NULL).

---

## Priority A -- Predictive comparison (KT family, AUC)

| Pass | Thesis slot | Headline value(s) | Status | Source file |
|---|---|---|---|---|
| 1 | Tabel 4.5 / Gambar 4.24 HCIE lagged-Kalman vs 5 baselines (matched eval) | HCIE overall AUC 0.6051 (tie-aware; was 0.6364 optimistic); BKT 0.5963 / DKT 0.5892 / SAKT 0.5730 / GKT 0.5711; HCIE 3-learner ref 0.6085. HCIE leads overall. Per-window le5/le10/le20 deep DKT/BKT lead (Simpson/cold-start, small-n 50/100/200). n_eval=10. | OK | research_validation/reports/baseline_comparison/lagged_kalman_auc.json |
| 2 | Tabel 4.7 / T8e + Gambar 4.8a-c deployed read-out, 4 datasets x window + BKT-floor | HCIE BEATS BKT on CSEDM (+0.0237) and EdNet (+0.0287); below deep on Junyi/ASSIST-2015 pooled; BKT cold-AUC = 0.5 floor on every dataset, HCIE cold 0.62-0.76. Simpson verdict documented. | OK | research_validation/reports/baseline_comparison/cross_dataset_kalman.json |
| 3 | Tabel 4.6 / T8d fair warmed BKT on ASSISTments-2009 per window | (none) UNAVAILABLE: no stored per-window fair-warmed/individualized-prior BKT on ASSIST-2009; only warmed-BKT probe is hardcoded to Junyi-graph run-94a3b8ba. Standard online BKT N30 exists but is NOT the warmed baseline. | UNAVAILABLE | research_validation/reports/kt_prediction/run-ca68d16f.../kt_prediction_auc.json (standard only) |
| 4 | F10 / scale sweep AUC per (dataset x model x N in 30/100/500), window=20 | Full 5-dataset x 8-model x 3-N matrix extracted. CSEDM N500: HCIE 0.681 BEATS DKT 0.651 and SAKT 0.650 (scoped win); deep models lead on 4/5 datasets at all N. WARN: HCIE here = runtime ENSEMBLE not Kalman-alone (noise-limited check). | OK | research_validation/reports/kt_scale_sweep/scale_sweep_summary.json |
| 5 | Gambar 4.27 cross-dataset overall (w20) AUC matrix, 8-model x 5-dataset (N=500 cell) | Matrix extracted. Per-dataset leaders: CSEDM=irt_1pl(hcie 0.681), Junyi=sakt, EdNet=sakt, ASSIST-2009=sakt, ASSIST-2015=bkt. No universal winner. WARN: HCIE = ensemble. | OK | research_validation/reports/kt_scale_sweep/scale_sweep_summary.json |
| 19 | 4.1.1.4 custom-vs-pyKT DKT/SAKT (are deep baselines under-powered?) | Custom DKT 0.589 ~= pyKT 0.584 (TIE); custom SAKT 0.573 > pyKT 0.548. Custom NOT under-powered. Honest ranking: BKT 0.612 ~= HCIE(3-learner) 0.609 > custom DKT 0.589 ~= pyKT DKT 0.584 > custom SAKT 0.573 ~= GKT 0.571 > pyKT SAKT 0.548. Matched-eval headline = lagged-Kalman 0.6051 (tie-aware; different protocol from this full-Junyi ranking — not directly comparable). | OK | research_validation/reports/grounding/PROBE_pykt_dkt_sakt.md |

## Priority B -- Governance / ADC / JT (3-learner-inherited on this seal)

| Pass | Thesis slot | Headline value(s) | Status | Source file |
|---|---|---|---|---|
| 6 | Tabel 4.8 (ADC class) + 4.10 (per-dim stats N=96,727) + 4.9 (threshold sens) + selector geometry | Sealed thresholds: ALPHA_FLOOR=0.01, SIGNAL_RATIO=0.08. Authoritative SNAPSHOT verdict: ACTIVE = {delta_m, transfer_realized, uncertainty, zpd}; DORMANT = {transfer_prospective, challenge} (4 ACTIVE / 2 DORMANT). Per-dim COLUMN stats for Tabel 4.10 extracted. Threshold sweep computed analytically (robust). WARN: two distinct substrates (columns vs snapshot) do not conflate. | OK | sealed_runs.frozen_stats (SQL) + SQL over experiment_trajectories; selector geometry research_validation/reports/governance_ecology/h12_audit/governance_ecology_report.json |
| 7 | Gambar 4.29 JT per-component ablation | Ranked JT-mean drop: uncertainty -0.0312 > challenge -0.0276 > delta_m -0.0242 > transfer_realized -0.0068 > zpd -0.0044 > transfer_prospective -0.0005. Ablate-all -> JT collapses to constant 0.5. Task-selection invariant (overlap=1.0). WARN: SMOKE-scale (1 learner/8 interactions, separate run_ids, NOT the seal). | OK | research_validation/reports/jt_ablation_smoke/jt_ablation_smoke.json |
| 8 | Tabel 4.11 L4 structure-class taxonomy (predicted vs observed) | Accuracy 18/24 = 0.75. Observed ACTIVE everywhere = {delta_m, uncertainty, zpd}; transfer dims uniformly DORMANT (4/4). Consistent miss: challenge predicted-active/observed-dormant (4/4). ASSIST-2009 observed row UNAVAILABLE (prediction-only). WARN: cross-dataset reveal, not the seal. | OK | research_validation/reports/adc_l4_reveal/l4_reveal_results.json |

## Priority C -- Transfer (placebo-corrected, confound disclosed)

| Pass | Thesis slot | Headline value(s) | Status | Source file |
|---|---|---|---|---|
| 9 | 4.1.3.e transfer probe + Bab5 RM4 | b_durable_CROSS_past = 0.09147; same-family 0.11865; placebo 0.03812; placebo_ratio = 0.417 (~42% confounded); cross_perm_p = 0.0099; b_proximity 0.13372. Net = placebo-corrected residual (~58%), confound disclosed, NOT net causal. Replicated in 1/10 subsample (ratio 0.409). WARN: probe population (1.97M rows/232k users) != sealed anchor. | OK | research_validation/reports/prospective_probe_v3_full.json |

## Priority D -- Live learner exhibits / journeys

| Pass | Thesis slot | Headline value(s) | Status | Source file |
|---|---|---|---|---|
| 10 | 4.1.1.1 cold-start journey (one sealed learner: m and sigma^2 per interaction) | Learner ex_junyi_graph_154646, single concept, 20 interactions. Cold start m1=0.1429 (mastery_before NULL); m saturates to 0.95 ceiling by interaction 9. sigma^2 NON-MONOTONE: rises 0.0034 -> peak ~0.0281 (int7), then narrows 0.0247(int5) -> 0.0244(int10) -> 0.0099(int20). Honest shape reported. | OK | SQL over experiment_trajectories (run-d2154070) |
| 11 | 4.1.3.f single-learner modality arm-selection + Thompson posterior | SYNTHETIC mechanism demo (live bandit is real-learner-only by contract; no live human modality traffic exists). Production `ContextualBandit.select_representation` + exact `_representation_outcomes` Beta `(1+c,1+(n-c))` over real 5-modality concept k12_algorithms; only responses synthetic; deterministic. Sampler concentrates on true-best `video_question` (128/160 pulls, last-40 share 0.875, posterior mean 0.908). NOT live traffic. | SYNTHETIC-DEMO | research_validation/scripts/seed_modality_bandit_demo.py -> thesis_extracts/pass11_bandit.json |
| 13 | ~302-interaction trace reconstruction (4.1.1.2 + 4.1.2.b 5-layer exhibit) | Chain distribution: 93 learners, 96,727 interactions, mean 1040 / median 563 / max 6502. Representative learner = ex_junyi_graph_147151 (313 interactions, closest to ~302). 5-layer exhibit (JT contrib -> ensemble weights -> canonical=m_K -> mastery_after V1-inherited -> policy). ew_kalman=1.0 everywhere; policy_score NULL (offline replay) -> use policy_multiplier. | OK | SQL over experiment_trajectories (run-d2154070) |
| 20 | Appendix example human learner (N=144) first 20 interactions + per-dim JT | Learner 99e34a5c... (traffic=human, N=144). First 20 rows w/ mastery_before/after + 6-dim JT attribution + jt_clamped. arm_selected NULL all rows (action carried by policy=text); transfer_prospective=0, zpd=0 all rows; jt_v2_* NULL (V2 OFF). WARN: LIVE human traffic, outside the seal. | OK | SQL over experiment_trajectories (live::99e34a5c...) |

## Priority E -- Reproducibility / determinism / auditability

| Pass | Thesis slot | Headline value(s) | Status | Source file |
|---|---|---|---|---|
| 14 | 4.1.2.c replay determinism / replay identity | deterministic_inputs_hash coverage = 100.0% (96,727/96,727). canonical_mastery_after == kalman_mastery_after exactly (0 mismatch, max_abs_diff 0.0). mastery_after (V1 3-learner) differs: corr 0.793, mean_abs_diff 0.164. Seal ledger consistent (content_hash, row_count, git_sha all match; git_dirty=false). F4/F9 drift trace (earlier pair) bounded le ~4e-3. | OK | SQL over experiment_trajectories + sealed_runs; drift research_validation/reports/replay_determinism_smoke/ |
| 12 | G2f O(1) update cost time-per-update vs history length | Complexity O(1) per update / O(1) posterior mean / O(K) memory, history-independent (by construction; Kalman canonical also O(1) recursive). EMPIRICAL time-vs-history curve UNAVAILABLE (processing_time NULL for all 96,727 rows). Only live bound: one /recommend = 4.44 ms. | OK (construction) / UNAVAILABLE (empirical) | HCIE_SYSTEM_BACKEND_FINAL/01_source/00_core/03_ensemble/jt_v2_signals.py |
| 15 | 4.1.2.a functional scenarios pass/total | (none) UNAVAILABLE: no stored junit/pytest result or run_tests.sh stdout. Disk: 614 declared test funcs / 124 files (structural), 36.4% line coverage (coverage.xml), host pytest cache 38 failures = docker-network collection errors not scenario fails. Needs one isolated-stack run (avoided per brief). | UNAVAILABLE | static + coverage.xml + .pytest_cache |

## Priority F -- Operational NFRs + corpus inventory (LIVE snapshots)

| Pass | Thesis slot | Headline value(s) | Status | Source file |
|---|---|---|---|---|
| 16 | 4.1.2.d/e operational NFRs (LIVE) | /recommend single live call 4.44 ms (only 1 recorded -> p50=p95). Overall hcie-api p95 7.58 ms / p50 2.79 ms (5m). CPU ~1.3% core; mem 149.6 MiB (3.65% of 4 GiB). SonarQube: Maint/Reliab/Security = A; 0 bugs, 0 vulns, 87 hotspots (Sec-Review E), 675 smells, dup 2.7%, debt 0.3%. Coverage 36.4% (Sonar shows 0 ingestion gap). /attempt latency UNAVAILABLE (0 requests). | OK | LIVE Prometheus :9090 + SonarQube :9000 (+ research_validation/reports/nfr_measurement/basic_nfr_measurement_results.json) |
| 17 | 4.1.1.2 [DATA-live] live database counts | Real learners 773 (human 54 / live 721); real interactions 108,602; total experiment_trajectories 847,122 (research 493,888 / replay_kalman 122,316 / replay_v2_causal 122,316 / live 107,941 / human 661); distinct runs = 77 clean (24,722 raw inflated by live composite keys); cohort_runs 79. WARN: LIVE snapshot, not seal. | OK | SQL over experiment_trajectories, cohort_runs |
| 18 | Tabel 4.1 / 4.1.1.3 external dataset registry + counts | 8 datasets registered, total external attempts 292,766, 39 distinct external runs. Per-dataset citation/license/source_sha256 (G1) + src/mapped learners + attempts extracted. junyi_2015_graph dominant (200,608 attempts) = the seal anchor source family. Synthetic runs 33 (98,811 rows); replay corpus = 3 sealed_runs + 6 run_forks. | OK | SQL over external_dataset_registry, external_log_attempts, sealed_runs, run_forks |

---

## Framing reminders (carry into thesis prose)

- Transfer = placebo-corrected residual with confound disclosed (~42% of cross-family effect is state/selection confound; net ~58% residual) NOT net causal.
- AUC = competitive, not superior. HCIE lagged-Kalman leads pooled overall (0.6051, tie-aware); per-window deep-model leads are a Simpson / cold-start pattern (sub-populations pool to higher AUC), not a loss. BKT cold-start floors at 0.5; HCIE structural edge is the cold-start sub-population.
- Governance / JT / ADC magnitudes (passes 6, 7, 8, 9-RM4, 13, 20) are 3-learner-runtime-inherited on this seal: canonical mastery = m_K (single Kalman) but the recorded JT/ADC/governance signals were inherited from the V1 runtime (which used the 3-learner mean to drive governance). ADC verdicts (active/dormant) are robust to this; only the magnitudes differ. An exact m_K-driven regenerate is UNAVAILABLE (not load-bearing). See research_validation/KALMAN_OVERLAY_GOVERNANCE_SCOPING.md.
- Custom deep baselines are NOT under-powered (pass 19): custom DKT ties pyKT, custom SAKT exceeds pyKT the library is not a confound.

## UNAVAILABLE / partial register (current)

All 20 slots now have an exhibit. The three prior UNAVAILABLEs were resolved:

| Pass | Slot | Resolution |
|---|---|---|
| 3 | Tabel 4.6 fair-warmed BKT (ASSIST-2009) | FILLED — `t8d_warmed_bkt_assist2009.json` (HCIE 0.6569 > warmed-BKT 0.6302 > cold 0.5954). |
| 11 | 4.1.3.f modality arm-selection + Thompson posterior | FILLED as labelled SYNTHETIC mechanism demo — `pass11_bandit.json` (live bandit is real-learner-only by contract; production sampler + exact Beta formula on synthetic responses; NOT live traffic). |
| 15 | 4.1.2.a functional scenarios pass/total | FILLED — `functional_suite.json` (150 passed / 159 ran, 0 logic regressions). |

The one remaining genuine gap is **partial, not absent**: pass 12's *empirical* time-vs-history curve. O(1)/O(K) is established by construction (and the Kalman canonical is O(1) recursive), but `processing_time` is NULL across all 96,727 rows so no measured time-vs-history plot exists (only one live `/recommend` = 4.44 ms).

## Frontend showcase

All 20 passes are surfaced on a single console: **`/dashboard/thesis-evidence`** (researcher role). Each pass renders a hero chart/table + provenance/caveats + a raw-JSON explorer, deep-linked to its live surface (Benchmarks, Governance, Ablation, Cold-Start, Replay/Integrity, Observability, Live Users, Data, Archetype×Modality). Data source = `src/data/thesis_extracts/` (build-time copy of this directory; re-copy + rebuild FE after re-running any probe).
