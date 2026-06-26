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

**Caption (ID):** *Gambar 4.x. Kontrol kausal shuffled-DAG: transfer durable lintas-keluarga teramati 0,0992
dibanding plasebo (masa-depan→masa-lalu) 0,0405 (residu 0,0587), p-permutasi 0,0099 atas 100 pengacakan (rerata
null −0,0144). Confound proximity (0,132) dan same-family (0,117) **lebih besar** dari efek lintas-keluarga —
sehingga efek nyata tetapi tidak murni kausal. Sampel 1/10.*

**Caption (EN):** Shuffled-DAG causal control — observed cross-family durable transfer 0.0992 vs future→past
placebo 0.0405 (residual 0.0587), permutation p = 0.0099 over 100 shuffles (null −0.0144). Proximity (0.132) and
same-family (0.117) confounds are **larger** — the effect is real but not cleanly causal. 1/10 sample.

**What it shows / why it matters.** This is the figure that **earns the honesty caveat** in README / REPRODUCIBILITY
§5 ("transfer = a placebo-corrected residual … correlational/topological, **not** causal"). It plots the observed
cross-family durable effect against a future→past placebo and a 100-shuffle permutation null, and — crucially —
shows the proximity / same-family confounds are *larger* than the cross-family effect. Use it to support, not
overclaim, the transfer result. **Provenance:** `tier5_topology_mag.json` — seal `51b8b51a`, run `13b43797`; fields
`b_durable_CROSS_past` (0.0992), `b_FUTURE_cross_PLACEBO` (0.0405), `b_durable_SAME` (0.117), `b_proximity` (0.132),
`cross_perm_p` (0.0099), `perm_K` (100), `null_mean` (−0.0144), `n_rows` (200,418), `n_users` (23,450); `mode` = 1/10 sample.

> Note: F4's residual (0.0587) is the **shuffled-DAG control run on a 1/10 sample** and corroborates — but is not
> identical to — the anchor's headline transfer residual **+0.053** (full run, README §Provenance). Report each with
> its own provenance; do not equate them.
