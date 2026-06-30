# HCIE — Figures (concept graph & causal control)

Four publication-ready figures generated from the **live system source** (no placeholders — every label,
edge, weight, and number traces to a real file). Each is provided as **SVG** (canonical vector — use in
LaTeX / Word / InDesign) and **PNG** (2000 px raster, for slides) under `docs/figures/`.

> Rendering note: the SVGs use **inline literal colours only** (no CSS `<style>`/`class`/`var()`), so they
> render identically in a browser, GitHub, Word, LaTeX, and librsvg. The PNGs were rasterised with a
> DejaVu-Sans fallback; for the exact Segoe/Arial look, export the SVG from a browser.

## Where each figure goes (thesis table of contents)

| Fig. | File | Thesis placement | One-line role |
|------|------|------------------|---------------|
| **3.1** | `F1-curriculum.svg` | **Bab 3** — Perancangan Sistem / model kurikulum | The prerequisite ontology + mastery-gate the learner climbs |
| **3.2** | `F2-framework.svg` | **Bab 3** — model transfer lintas-area | The full K-12 CS dependency graph `/learn` adapts over |
| **3.3** | `F3-algorithms.svg` | **Bab 3** — model transfer (detail, pendamping 3.2) | Node-level zoom of one strand (Algorithms & Programming) |
| **4.x** | `F4-causal.svg` | **Bab 4** — Hasil: validitas & keterbatasan transfer | The shuffled-DAG causal control behind the "not causal" caveat |

Place 3.1–3.3 together where the curriculum/transfer model is introduced; place 4.x in Results next to the
transfer paragraph, because it is the *evidence for the honesty caveat*, not a victory chart.

---

## F1 — Curriculum prerequisite DAG  → Bab 3 (Fig. 3.1)

**Caption (ID, siap-tempel):** *Gambar 3.1. DAG prasyarat kurikulum Intro-Python: delapan konsep tersusun dalam
lima kolom kedalaman-prasyarat, diwarnai menurut tipe (pengetahuan / keterampilan / praktik), dengan 15 sisi
prasyarat berarah dan gerbang penguasaan per-konsep (0,75 → 0,60) yang memicu `409 concept_locked`.*

**Caption (EN):** Curriculum prerequisite DAG — 8 concepts in 5 prerequisite-depth columns, colour-coded by type,
15 directed prerequisite edges, per-concept mastery gate (0.75 → 0.60).

**What it shows / why it matters.** This is the concept ontology a learner actually climbs. An item is only
recommended once its prerequisites clear the per-concept mastery gate (≥ threshold); below it the API returns
`409 concept_locked`. The figure makes the gating mechanism — central to the cold-start story — visible in one
view. **Provenance:** `concept_registry.py` → `initialize_intro_python_curriculum()` (8 concepts, 15 edges).

## F2 — Live K-12 CS-framework DAG  → Bab 3 (Fig. 3.2)

**Caption (ID):** *Gambar 3.2. DAG kerangka K-12 Computer Science yang diadaptasi oleh alur `/learn`: lima area
sebagai swimlane × empat jenjang kelas, ditambah rantai 7-langkah Computational Thinking Practices. Garis padat =
progresi prasyarat dalam-area; garis putus-putus = empat sisi transfer lintas-area dengan bobot nyata
(0,95 / 0,90 / 0,85 / 0,80).*

**Caption (EN):** Live K-12 CS-framework DAG — 5 areas × 4 grade bands + the 7-step practices chain; solid =
within-area prerequisite, dashed = the 4 real cross-area transfer edges with weights.

**What it shows / why it matters.** The big-picture dependency graph the adaptive engine reasons over: how the
five CS areas progress across grade bands and where knowledge transfers *across* areas. The transfer edges
(weighted 0.75–0.95) are precisely the structure the transfer-measurement claim (§5) is computed over.
**Provenance:** `real_dag_dependencies.py` (70 nodes, 55 weighted edges; 4 cross-area transfer edges).

## F3 — Algorithms & Programming strand  → Bab 3 (Fig. 3.3)

**Caption (ID):** *Gambar 3.3. Detail tingkat-simpul strand Algorithms & Programming antar-jenjang (Algorithms,
Variables, Control, Modularity, Program Development), dengan sisi transfer internal berbobot dan tautan ke praktik
Computational Thinking. Memperbesar satu lajur dari Gambar 3.2.*

**Caption (EN):** Algorithms & Programming strand — node-level detail across grade bands with weighted internal
transfer edges and incident practice links (zoom-in companion to Fig. 3.2).

**What it shows / why it matters.** A readable zoom into one strand so the reader sees the node-level granularity
that Fig. 3.2 aggregates. **Provenance:** `real_dag_dependencies.py` (Algorithms & Programming strand).

## F4 — Shuffled-DAG causal control  → Bab 4 (Fig. 4.x)

**Caption (ID):** *Gambar 4.x. Kontrol kausal shuffled-DAG (sampel penuh, K=1000): transfer durable lintas-keluarga
teramati 0,091 dibanding plasebo (masa-depan→masa-lalu) 0,038 (residu +0,053), p-permutasi < 0,001 atas 1000
pengacakan (rerata null −0,014). Confound proximity (0,134) dan same-family (0,119) **lebih besar** dari efek
lintas-keluarga — sehingga efek nyata tetapi tidak murni kausal. Sampel penuh: 1.976.020 baris / 232.440 pembelajar.*

**Caption (EN):** Shuffled-DAG causal control (full sample, K=1000) — observed cross-family durable transfer 0.091 vs
future→past placebo 0.038 (residual +0.053), permutation p < 0.001 over 1000 shuffles (null −0.014). Proximity (0.134)
and same-family (0.119) confounds are **larger** — the effect is real but not cleanly causal. Full sample: 1,976,020 rows.

**What it shows / why it matters.** This is the figure that **earns the honesty caveat** in README / REPRODUCIBILITY
§5 ("transfer = a placebo-corrected residual … correlational/topological, **not** causal") — and it now matches the
thesis headline exactly (**+0.053, p<0.001, K=1000**), so figure and prose agree. It plots the observed cross-family
durable effect against a future→past placebo and a 1000-shuffle permutation null, and — crucially — shows the
proximity / same-family confounds are *larger* than the cross-family effect. Use it to support, not overclaim, the
transfer result. **Provenance:** `prospective_probe_v3_full_K1000.json` (full sample, seed 20260531;
`probe_prospective_transfer_v3.py --full --permutations 1000`); fields `b_durable_CROSS_past` (0.09147),
`b_FUTURE_cross_PLACEBO` (0.03812), `b_durable_SAME` (0.11865), `b_proximity` (0.13372), `cross_perm_p` (0.000999),
`perm_K` (1000), `null_mean` (−0.01376), `n_rows` (1,976,020), `n_users` (232,440); `mode` = full.

> Note: F4 is the **full-sample K=1000** run, so its residual **+0.053** is the same value as the thesis/README headline
> transfer residual — figure and prose agree. (The earlier 1/10-sample probe `tier5_topology_mag.json` gave a
> consistent but distinct 0.059 at K=100/p=0.0099; the full run supersedes it for the figure.)

*All four figure files now use Indonesian labels (decimal commas, no "F#" prefix); the captions above are provided ID + EN for pasting.*

---

# Additional Chapter-4 empirical figures (F5–F8)

Reviewer-requested evidence (learning curve, sensitivity, calibration), all computed on the **canonical sealed
run `run-94a3b8ba` / anchor `d2154070`**, matched cold-start protocol, 10 held-out users. The per-row substrate
(`docs/figures/data/matched_eval_perrow_run-94a3b8ba.csv`) reproduces **Tabel 4.8 exactly** (overall HCIE 0,6051;
≤5 0,8738; ≤10 0,8225). Full rationale + the "could-not-produce" item in [EXTRA_EXPERIMENTS_F5-F8.md](EXTRA_EXPERIMENTS_F5-F8.md).

## F8 — Calibration reliability  → Bab 4 (bagian kalibrasi)
HCIE raw **ECE 0,109 / Brier 0,152** vs BKT **ECE 0,062**; post-hoc **Platt → ECE 0,004**, AUC unchanged (0,6051).
Honest: HCIE's *raw* uncertainty is less calibrated than BKT; Platt closes the gap monotonically.
![Kalibrasi](docs/figures/F8-calibration.png)

## F5 — Per-interaction learning curve  → Bab 4 (dekat Tabel 4.8 / Gambar 4.9)
AUC per interaction-depth bin, 5 models. **Honest reading (Simpson):** on the tiny early windows (n=50–200) the
pre-trained DKT/SAKT score *higher* than HCIE; HCIE's win is on the **long tail (idx 101+ = 91 % of data)** → the
aggregate 0,6051. The claim it supports is *competitive without offline training*, not early dominance.
![Kurva pembelajaran](docs/figures/F5-learning-curve.png)

## F7 — Parameter sensitivity (Q, R)  → Bab 4 robustness / Lampiran
AUC stays in **0,60–0,62 across a 200× Q/R range** → robust, not tuned (supports "Q=0,01/R=0,1 ditetapkan tetap").
**Disclosure:** sweep is on a faithful *re-implementation* (base 0,613, corr 0,96 with deployed m_K), not bit-exact
to 0,6051 — the robustness *shape* is trustworthy, the absolute level is the re-impl's.
![Sensitivitas](docs/figures/F7-sensitivity.png)

## F6 — Component ablation → **deliberately NOT added** (honest)
A leave-one-out AUC ablation could not be produced consistently: Thompson/transfer/uncertainty are not in the
predictive `m_K` path (0 change by design), and a naive −Kalman→Beta re-impl scores ≥ Kalman (0,622 vs 0,613),
which contradicts the "Kalman-alone canonical" choice (that rests on out-of-sample predictive validity r=0,332
> 0,311, not matched AUC). Existing **Gambar 4.15 (ablasi JT)** + the estimator predictive-validity evidence
cover this honestly. Data documenting the finding: `docs/figures/data/F6-ablation.csv`.
