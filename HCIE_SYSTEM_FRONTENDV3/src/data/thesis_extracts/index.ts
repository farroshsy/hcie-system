/**
 * Thesis-evidence extracts — static bundle for the /dashboard/thesis-evidence console.
 *
 * These JSON files are the read-only tabulation of the sealed anchor run
 * (seal-bae44d1a / run-d2154070, content_hash 85690d8b…, 96,727 rows, git_dirty=false)
 * plus a handful of isolated probes and one labelled synthetic mechanism demo (pass 11).
 *
 * SOURCE OF TRUTH = RealSystem/thesis_extracts/*.json. This directory is a build-time
 * COPY (the frontend ships as a baked standalone image, so the data must live in-tree).
 * After re-running any probe, re-copy the changed file here and rebuild the FE.
 *
 * Honesty carries through verbatim: every file keeps its own status / provenance /
 * caveat fields; the page renders them, it does not launder them.
 */

import pass01 from './pass01_matched_eval.json'
import pass02 from './pass02_deployed_readout.json'
import pass03 from './pass03_t8d_sealed_assist2009.json' // pass 3 fill (SEALED T8d — seal-8530c026, run-a7e35992)
import pass04 from './pass04_scale_sweep.json'
import pass05 from './pass05_cross_dataset_matrix.json'
import pass06 from './pass06_governance_ecology.json'
import pass07 from './pass07_jt_ablation.json'
import pass08 from './pass08_l4_taxonomy.json'
import pass09 from './pass09_transfer.json'
import pass10 from './pass10_coldstart_journey.json'
import pass11 from './pass11_bandit.json'
import pass12 from './pass12_update_cost.json'
import pass13 from './pass13_trace_reconstruction.json'
import pass14 from './pass14_replay_determinism.json'
import pass15 from './functional_suite.json' // pass 15 fill (functional suite)
import pass16 from './pass16_operational.json'
import pass17 from './pass17_live_db_counts.json'
import pass18 from './pass18_dataset_registry.json'
import pass19 from './pass19_custom_vs_pykt.json'
import pass20 from './pass20_example_20interactions.json'

export type Json = any

/** Status as rendered on a card. */
export type PassStatus = 'ok' | 'demo' | 'partial' | 'unavailable'

export interface DeepLink {
  label: string
  href: string
}

export interface PassMeta {
  pass: number
  /** A–F priority group, matching thesis_extracts/SUMMARY.md. */
  group: string
  title: string
  /** thesis slot this fills (Tabel/Gambar/§). */
  slot: string
  status: PassStatus
  /** one-line headline carried from SUMMARY.md. */
  headline: string
  /** existing live/deep surface this snapshot links out to, if any. */
  deepLink?: DeepLink
  /** the raw extract JSON. */
  data: Json
  /** which kind of hero visual to draw (handled in the page). */
  hero:
    | 'aucBars'
    | 'datasetGroupedBars'
    | 'windowGroupedBars'
    | 'scaleLines'
    | 'matrixTable'
    | 'perDimBars'
    | 'ablationBars'
    | 'taxonomy'
    | 'transferBars'
    | 'journeyLines'
    | 'banditBars'
    | 'complexity'
    | 'trace'
    | 'determinism'
    | 'functional'
    | 'operational'
    | 'liveCounts'
    | 'datasetTable'
    | 'pyktBars'
    | 'interactionTable'
}

export const ANCHOR = {
  seal_id: 'seal-bae44d1a-a314-48f5-b145-c92e6cbe08d7',
  run_id: 'run-d2154070-b6e4-4abe-94e6-a2e6ccfbefc1',
  git_sha: '035b37ca374cf8723b80e217a8c4cad5acb2be3b',
  content_hash: '85690d8be722e1e6271abb2f860290dd',
  rows: 96727,
  git_dirty: false,
  date: '2026-06-17',
  config:
    'canonical mastery = single Kalman (m = m_K); ensemble used for σ² only; V2 governance OFF; F4 ON.',
}

/** Ordered exactly as SUMMARY.md (priority A → F), not by pass number. */
export const PASSES: PassMeta[] = [
  // ── A · predictive comparison (KT family, AUC) ──
  {
    pass: 1, group: 'A · Predictive (KT family, AUC)', hero: 'aucBars',
    title: 'Matched eval — HCIE lagged-Kalman vs 5 baselines',
    slot: 'Tabel 4.5 / Gambar 4.24', status: 'ok',
    headline: 'HCIE overall AUC 0.6051 leads all (BKT 0.5963 / DKT 0.5892 / SAKT 0.5730 / GKT 0.5711; tie-aware); lead +0.0088(n10)→+0.0062(n40)→+0.0125(n76), positive at all power & significant at n=76 (CI [+0.0017,+0.0226]) [pass07b]; per-window deep/BKT leads = Simpson/cold-start.',
    deepLink: { label: 'Benchmarks', href: '/dashboard/benchmarks' }, data: pass01,
  },
  {
    pass: 2, group: 'A · Predictive (KT family, AUC)', hero: 'datasetGroupedBars',
    title: 'Deployed read-out per dataset × window (+ BKT floor)',
    slot: 'Tabel 4.7 / T8e + Gambar 4.8a–c', status: 'ok',
    headline: 'HCIE beats BKT on CSEDM (+0.0237) and EdNet (+0.0287); BKT cold-AUC floors at 0.5 on every dataset, HCIE cold 0.62–0.76.',
    deepLink: { label: 'Benchmarks', href: '/dashboard/benchmarks' }, data: pass02,
  },
  {
    pass: 3, group: 'A · Predictive (KT family, AUC)', hero: 'windowGroupedBars',
    title: 'SEALED warmed-BKT vs HCIE — ASSISTments-2009 (T8d)',
    slot: 'Tabel 4.6 / T8d', status: 'ok',
    headline: 'SEALED run (seal-8530c026 / run-a7e35992): HCIE 0.6331 > warmed-BKT 0.6096 (+0.0235 overall); HCIE wins ≤10/≤20, competitive ≤5; cold-BKT floor 0.6214. A sealed comparison now, not a deployed read-out.',
    deepLink: { label: 'Benchmarks', href: '/dashboard/benchmarks' }, data: pass03,
  },
  {
    pass: 4, group: 'A · Predictive (KT family, AUC)', hero: 'scaleLines',
    title: 'Scale sweep — AUC per (dataset × model × N)',
    slot: 'Gambar F10 (window=20)', status: 'partial',
    headline: 'CSEDM N500: HCIE 0.681 beats DKT 0.651 / SAKT 0.650 (scoped win); deep models lead on 4/5 datasets at all N. NOTE: HCIE here = runtime ensemble (noise-limited check).',
    deepLink: { label: 'Benchmarks', href: '/dashboard/benchmarks' }, data: pass04,
  },
  {
    pass: 5, group: 'A · Predictive (KT family, AUC)', hero: 'matrixTable',
    title: 'Cross-dataset overall AUC matrix (8 model × 5 dataset)',
    slot: 'Gambar 4.27 (w20, N=500)', status: 'partial',
    headline: 'No universal winner. Per-dataset leaders: CSEDM=irt_1pl(HCIE 0.681), Junyi/EdNet/ASSIST-2009=sakt, ASSIST-2015=bkt. NOTE: HCIE = ensemble.',
    deepLink: { label: 'Benchmarks', href: '/dashboard/benchmarks' }, data: pass05,
  },
  {
    pass: 19, group: 'A · Predictive (KT family, AUC)', hero: 'pyktBars',
    title: 'Custom vs pyKT DKT/SAKT — are deep baselines under-powered?',
    slot: '§4.1.1.4', status: 'ok',
    headline: 'Custom DKT 0.589 ≈ pyKT 0.584 (tie); custom SAKT 0.573 > pyKT 0.548. Custom NOT under-powered — the library is not a confound.',
    data: pass19,
  },
  // ── B · governance / ADC / JT ──
  {
    pass: 6, group: 'B · Governance / ADC / JT', hero: 'perDimBars',
    title: 'Governance ecology — per-dimension stats + ADC class',
    slot: 'Tabel 4.8 / 4.9 / 4.10 (N=96,727)', status: 'ok',
    headline: 'Sealed thresholds α_floor=0.01, signal_ratio=0.08. ACTIVE = {δm, transfer_realized, uncertainty, zpd}; DORMANT = {transfer_prospective, challenge}.',
    deepLink: { label: 'Governance', href: '/dashboard/governance' }, data: pass06,
  },
  {
    pass: 7, group: 'B · Governance / ADC / JT', hero: 'ablationBars',
    title: 'JT per-component ablation',
    slot: 'Gambar 4.29', status: 'partial',
    headline: 'Ranked JT-mean drop: uncertainty −0.0312 > challenge −0.0276 > δm −0.0242 > transfer_realized −0.0068 > zpd −0.0044 > transfer_prospective −0.0005. NOTE: smoke-scale, not the seal.',
    deepLink: { label: 'Ablation', href: '/dashboard/ablation' }, data: pass07,
  },
  {
    pass: 8, group: 'B · Governance / ADC / JT', hero: 'taxonomy',
    title: 'L4 structure-class taxonomy (predicted vs observed)',
    slot: 'Tabel 4.11', status: 'partial',
    headline: 'Accuracy 18/24 = 0.75. Consistent miss: challenge predicted-active / observed-dormant (4/4). NOTE: cross-dataset reveal, not the seal.',
    deepLink: { label: 'Governance', href: '/dashboard/governance' }, data: pass08,
  },
  // ── C · transfer ──
  {
    pass: 9, group: 'C · Transfer (placebo-corrected)', hero: 'transferBars',
    title: 'Transfer probe — durable / placebo / proximity',
    slot: '§4.1.3.e + Bab 5 RM4', status: 'ok',
    headline: 'b_durable_cross 0.0915; same-family 0.1187; placebo 0.0381; placebo_ratio 0.417 (~42% confounded); perm-p 0.0099. Net = placebo-corrected residual (~58%), NOT net causal.',
    data: pass09,
  },
  // ── D · live learner exhibits / journeys ──
  {
    pass: 10, group: 'D · Learner exhibits / journeys', hero: 'journeyLines',
    title: 'Cold-start journey (one sealed learner: m & σ²)',
    slot: '§4.1.1.1', status: 'ok',
    headline: 'Learner ex_junyi_graph_154646: cold-start m₁=0.143, saturates to 0.95 ceiling by interaction 9; σ² non-monotone — rises to ~0.028 (int 7) then narrows to 0.0099 (int 20).',
    deepLink: { label: 'Cold-Start Journey', href: '/dashboard/cold-start-journey' }, data: pass10,
  },
  {
    pass: 11, group: 'D · Learner exhibits / journeys', hero: 'banditBars',
    title: 'Representation (modality) bandit — arm log + posteriors',
    slot: '§4.1.3.f', status: 'demo',
    headline: 'SYNTHETIC mechanism demo (live bandit is real-learner-only by contract). Production Thompson sampler converges on the true-best modality video_question: 128/160 pulls, last-40 share 0.875.',
    deepLink: { label: 'Archetype × Modality', href: '/dashboard/archetype-modality' }, data: pass11,
  },
  {
    pass: 13, group: 'D · Learner exhibits / journeys', hero: 'trace',
    title: 'Decision-chain trace reconstruction (5-layer)',
    slot: '§4.1.1.2 + §4.1.2.b', status: 'ok',
    headline: '93 learners / 96,727 interactions (mean 1040, max 6502). Representative learner ex_junyi_graph_147151 (313 interactions ≈ 302). 5 layers: JT → ensemble weight → canonical=m_K → mastery → policy.',
    deepLink: { label: 'Replay / Integrity', href: '/dashboard/replay-verify' }, data: pass13,
  },
  {
    pass: 20, group: 'D · Learner exhibits / journeys', hero: 'interactionTable',
    title: 'Appendix exhibit — real learner first 20 interactions',
    slot: 'Lampiran (N=144)', status: 'ok',
    headline: 'Learner 99e34a5c… (traffic=human, N=144): first 20 rows with mastery before/after + 6-dim JT attribution. NOTE: live human traffic, outside the seal.',
    deepLink: { label: 'Learner Journey', href: '/dashboard/learner-journey' }, data: pass20,
  },
  // ── E · reproducibility / determinism ──
  {
    pass: 14, group: 'E · Reproducibility / determinism', hero: 'determinism',
    title: 'Replay determinism / replay identity',
    slot: '§4.1.2.c', status: 'ok',
    headline: 'deterministic_inputs_hash coverage 100% (96,727/96,727). canonical_mastery_after == kalman_mastery_after exactly (0 mismatch, max|Δ|=0.0). Seal ledger consistent; git_dirty=false.',
    deepLink: { label: 'Replay / Integrity', href: '/dashboard/replay-verify' }, data: pass14,
  },
  {
    pass: 12, group: 'E · Reproducibility / determinism', hero: 'complexity',
    title: 'O(1) update-cost (G2f)',
    slot: 'G2f', status: 'partial',
    headline: 'Complexity O(1) per update / O(K) memory, history-independent by construction (Kalman canonical also O(1) recursive). EMPIRICAL time-vs-history curve UNAVAILABLE (processing_time NULL).',
    data: pass12,
  },
  {
    pass: 15, group: 'E · Reproducibility / determinism', hero: 'functional',
    title: 'Functional / behavioral scenario suite',
    slot: '§4.1.2.a', status: 'ok',
    headline: '398 passed / 28 skipped / 0 failed (full functional suite, isolated stack, host source, 2026-06-21). 00_unit alone = 208/23/0. Post test-honesty remediation: print-theater removed, sealing + correctness tests added.',
    data: pass15,
  },
  // ── F · operational NFRs + corpus (LIVE snapshots) ──
  {
    pass: 16, group: 'F · Operational NFRs + corpus (LIVE)', hero: 'operational',
    title: 'Operational NFRs (LIVE) + SonarQube',
    slot: '§4.1.2.d / §4.1.2.e', status: 'ok',
    headline: '/recommend 4.44 ms; api p95 7.58 / p50 2.79 ms; CPU ~1.3% core, mem 149.6 MiB. SonarQube Maint/Reliab/Security = A; 0 bugs/0 vulns, 675 smells, dup 2.7%, coverage 36.4%.',
    deepLink: { label: 'Observability', href: '/dashboard/observability' }, data: pass16,
  },
  {
    pass: 17, group: 'F · Operational NFRs + corpus (LIVE)', hero: 'liveCounts',
    title: 'Live database counts',
    slot: '§4.1.1.2 [DATA-live]', status: 'ok',
    headline: 'Real learners 773 (human 54 / live 721); real interactions 108,602; total trajectories 847,122; distinct clean runs 77; cohort_runs 79. NOTE: live snapshot, not seal.',
    deepLink: { label: 'Live Users', href: '/dashboard/live-users' }, data: pass17,
  },
  {
    pass: 18, group: 'F · Operational NFRs + corpus (LIVE)', hero: 'datasetTable',
    title: 'External dataset registry + corpus inventory',
    slot: 'Tabel 4.1 / §4.1.1.3', status: 'ok',
    headline: '8 datasets registered, 292,766 external attempts, 39 distinct external runs. junyi_2015_graph dominant (200,608) = the seal anchor source family. Replay corpus = 3 sealed_runs + 6 run_forks.',
    deepLink: { label: 'Data', href: '/dashboard/data' }, data: pass18,
  },
]

export const TALLY = {
  total: PASSES.length,
  ok: PASSES.filter((p) => p.status === 'ok').length,
  demo: PASSES.filter((p) => p.status === 'demo').length,
  partial: PASSES.filter((p) => p.status === 'partial').length,
  unavailable: PASSES.filter((p) => p.status === 'unavailable').length,
}
