'use client'

/**
 * KT Prediction Benchmark — HCIE vs knowledge-tracing baselines.
 *
 * DIFFERENT experiment from /dashboard/cohorts (policy comparison). Here we ask:
 * how well does HCIE PREDICT the next answer vs trained KT models (BKT, DKT, SAKT,
 * IRT-1PL, …) on the SAME held-out users of a real dataset? Metric = AUC / accuracy /
 * Brier, not teaching efficacy. HCIE is zero-shot (no training).
 *
 * Data:
 *   GET /v3/frontend/dashboard/cohort-runs?group=dataset  → datasets + latest/best run
 *   GET /v3/frontend/dashboard/kt-benchmark/{run_id}      → per-model AUC/acc/brier
 */

import { useEffect, useState, useCallback } from 'react'
import Link from 'next/link'
import { getBackendUrl } from '@/lib/api/backend-url'
import { useT } from '@/contexts/language_context'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, ReferenceLine,
  LineChart, Line, Legend,
} from 'recharts'
import { CrossDatasetBenchmark } from '@/components/dashboard/CrossDatasetBenchmark'
import { DeployedBeatsBKT } from '@/components/dashboard/DeployedBeatsBKT'
import { Panel, Tag, Callout, SectionTitle, Eyebrow } from '@/lib/ui/primitives'
import { t as ui } from '@/lib/ui/theme'  // aliased: `t` is taken by useT() (translations)
import PageGuide, { TourStep } from '@/components/help/PageGuide'

const BACKEND = getBackendUrl()

const DATASET_ORDER = ['junyi', 'assistments', 'ednet', 'statics', 'csedm']

// Color: HCIE highlighted, baselines neutral, floor models muted.
// Canonical per-model palette now lives in the shared theme (was duplicated per page).
const MODEL_COLOR = ui.modelColor

// Display labels for governance dimensions / dataset meta / model labels are
// built INSIDE the component (below) so the t() translator is in scope.

// The six canonical governance dimensions (order matches ConstitutionalWeights w1..w6).
const GOV_DIMS = ['delta_m', 'transfer_realized', 'transfer_prospective', 'challenge', 'uncertainty', 'zpd'] as const

function getAuthHeaders(): HeadersInit {
  const token = (typeof window !== 'undefined' &&
    (localStorage.getItem('hcie_auth_token') || localStorage.getItem('access_token'))) || ''
  return token ? { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }
               : { 'Content-Type': 'application/json' }
}

// HCIE on the THESIS CANONICAL (Kalman-alone, m_K) — not the legacy 3-learner mastery_before
// that the per-run tables below surface. Shows HCIE leads overall AND the honest per-window
// cold-start picture (deep models lead; Simpson). Source: /kt-benchmark-canonical.
function CanonicalHeadlinePanel({ t }: { t: (key: string, fallback?: string) => string }) {
  const [d, setD] = useState<any>(null)
  useEffect(() => {
    let c = false
    fetch(`${BACKEND}/v3/frontend/dashboard/kt-benchmark-canonical`, { headers: getAuthHeaders() })
      .then(r => r.json()).then(j => { if (!c) setD(j) }).catch(() => { if (!c) setD({ status: 'error' }) })
    return () => { c = true }
  }, [])
  if (!d || d.status !== 'ok' || !d.matched_headline) return null
  const mh = d.matched_headline
  const rows: any[] = mh.rows || []
  const fmt = (x: any) => (typeof x === 'number' ? x.toFixed(4) : '—')
  const cols = [['hcie_lagged_kalman', t('benchmarksBody.colHcieKalman')], ['bkt', 'BKT'], ['dkt', 'DKT'], ['sakt', 'SAKT'], ['gkt', 'GKT']] as const
  const leaderKey = (r: any) => {
    let bk = 'hcie_lagged_kalman', bv = -1
    for (const [k] of cols) { const v = r[k]; if (typeof v === 'number' && v > bv) { bv = v; bk = k } }
    return bk
  }
  return (
    <Panel tone="ok" data-tour="canonical-headline" style={{ marginBottom: ui.space.lg }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: ui.space.sm, flexWrap: 'wrap', marginBottom: ui.space.xs }}>
        <Tag tone="ok">{t('benchmarksBody.thesisCanonicalTag')}</Tag>
        <span style={{ fontSize: ui.font.size.md, fontWeight: ui.font.weight.heavy, color: ui.tone.ok.fg }}>{t('benchmarksBody.hcieKalmanAlone')}</span>
        {mh.leads_overall && <span style={{ fontSize: ui.font.size.sm, color: ui.tone.ok.fg }}>{t('benchmarksBody.leadsAllOverall')}</span>}
      </div>
      <div style={{ fontSize: ui.font.size.sm, color: ui.color.body, margin: `0 0 ${ui.space.sm}px` }}>{mh.note}</div>
      <table style={{ borderCollapse: 'collapse', fontSize: ui.font.size.base, width: '100%', maxWidth: 640, fontVariantNumeric: 'tabular-nums' }}>
        <thead><tr>
          <th style={{ textAlign: 'left', padding: '6px 8px', fontSize: ui.font.size.xs, fontWeight: ui.font.weight.bold, textTransform: 'uppercase', letterSpacing: '0.05em', color: ui.color.muted, borderBottom: `1px solid ${ui.tone.ok.border}` }}>{t('benchmarksBody.thWindow')}</th>
          {cols.map(([k, lbl]) => <th key={k} style={{ textAlign: 'right', padding: '6px 8px', fontSize: ui.font.size.xs, fontWeight: ui.font.weight.bold, textTransform: 'uppercase', letterSpacing: '0.05em', color: k === 'hcie_lagged_kalman' ? ui.tone.ok.fg : ui.color.muted, borderBottom: `1px solid ${ui.tone.ok.border}` }}>{lbl}</th>)}
        </tr></thead>
        <tbody>
          {rows.map((r, i) => { const lk = leaderKey(r); return (
            <tr key={i} style={{ borderTop: `1px solid ${ui.tone.ok.border}` }}>
              <td style={{ padding: '5px 8px', fontWeight: r.window === 'overall' ? ui.font.weight.bold : 400, color: ui.color.heading }}>{r.window}</td>
              {cols.map(([k]) => (
                <td key={k} style={{ textAlign: 'right', padding: '5px 8px',
                     fontWeight: k === lk ? ui.font.weight.heavy : (k === 'hcie_lagged_kalman' ? ui.font.weight.medium : 400),
                     color: k === lk ? ui.tone.ok.fg : (k === 'hcie_lagged_kalman' ? ui.tone.ok.fg : ui.color.body),
                     background: k === 'hcie_lagged_kalman' ? ui.tone.ok.bg : 'transparent' }}>
                  {fmt(r[k])}{k === lk ? ' ◀' : ''}
                </td>
              ))}
            </tr>
          )})}
        </tbody>
      </table>
      <Callout tone="warn" style={{ marginTop: ui.space.md }}>{'⚠'} {d.honesty_note}</Callout>
    </Panel>
  )
}

const STEPS: TourStep[] = [
  {
    selector: '[data-tour="page-intro"]',
    title: { en: 'What this page asks', id: 'Apa yang halaman ini tanya' },
    body: {
      en: 'This page tests how well HCIE predicts a learner\'s next answer versus trained knowledge-tracing baselines. Read this intro first to know what is being compared.',
      id: 'Halaman ini menguji seberapa baik HCIE memprediksi jawaban berikutnya seorang pelajar dibanding baseline knowledge-tracing terlatih. Baca intro ini dulu untuk tahu apa yang dibandingkan.',
    },
  },
  {
    selector: '[data-tour="canonical-headline"]',
    title: { en: 'The headline result', id: 'Hasil utama' },
    body: {
      en: 'The green panel is the main result: HCIE (Kalman-alone) AUC versus BKT, DKT, SAKT and GKT. The row marked overall is the top-line number; ◀ flags the leader in each row.',
      id: 'Panel hijau adalah hasil utama: AUC HCIE (Kalman-alone) versus BKT, DKT, SAKT dan GKT. Baris bertanda overall adalah angka utama; ◀ menandai pemimpin di tiap baris.',
    },
  },
  {
    selector: '[data-tour="regime-toggle"]',
    title: { en: 'Switch comparison worlds', id: 'Ganti dunia perbandingan' },
    body: {
      en: 'Use these tabs to switch between three comparison settings: non-graph, graph (the thesis headline), and cross-dataset. The graph tab is selected by default.',
      id: 'Pakai tab ini untuk berpindah antara tiga setting perbandingan: non-graph, graph (headline tesis), dan cross-dataset. Tab graph dipilih secara default.',
    },
  },
  {
    selector: '[data-tour="dataset-picker"]',
    title: { en: 'Pick a dataset', id: 'Pilih dataset' },
    body: {
      en: 'In the non-graph view, click a dataset card to load its results. You can also toggle between the best and latest run.',
      id: 'Di tampilan non-graph, klik kartu dataset untuk memuat hasilnya. Anda juga bisa beralih antara run terbaik (best) dan terbaru (latest).',
    },
  },
  {
    selector: '[data-tour="coldstart-curve"]',
    title: { en: 'Cold-start curve', id: 'Kurva cold-start' },
    body: {
      en: 'This chart is the core lens: AUC across early windows (first 5, 10, 20 answers) versus all interactions. A flatter HCIE line means it holds up when there is little data.',
      id: 'Grafik ini adalah lensa inti: AUC pada window awal (5, 10, 20 jawaban pertama) versus semua interaksi. Garis HCIE yang lebih datar berarti tetap kuat saat data sedikit (cold-start).',
    },
  },
  {
    selector: '[data-tour="results-table"]',
    title: { en: 'Per-window results', id: 'Hasil per-window' },
    body: {
      en: 'Hover a bar to read its exact value. Switch the metric (AUC, accuracy, Brier) above; HCIE is highlighted so you can compare it against each baseline.',
      id: 'Arahkan kursor ke sebuah bar untuk membaca nilai persisnya. Ganti metrik (AUC, accuracy, Brier) di atas; HCIE disorot agar mudah dibandingkan dengan tiap baseline.',
    },
  },
]

export default function BenchmarksPage() {
  const t = useT()

  // Display labels live inside the component so the t() translator is in scope.
  // Friendly dataset metadata (origin/domain). Keyed by the dataset key the
  // backend derives from cohort_runs.reason. Badges stay VERBATIM (dataset names).
  const DATASET_META: Record<string, { label: string; origin: string; badge: string }> = {
    junyi:       { label: 'Junyi 2015',   origin: t('benchmarksBody.datasetJunyiOrigin'),   badge: 'JUNYI' },
    assistments: { label: 'ASSISTments',  origin: t('benchmarksBody.datasetAssistOrigin'),  badge: 'ASSIST' },
    ednet:       { label: 'EdNet KT1',    origin: t('benchmarksBody.datasetEdnetOrigin'),    badge: 'EDNET' },
    statics:     { label: 'STATICS 2011', origin: t('benchmarksBody.datasetStaticsOrigin'),  badge: 'STATICS' },
    csedm:       { label: 'CSEDM F19',    origin: t('benchmarksBody.datasetCsedmOrigin'),     badge: 'CSEDM' },
  }
  // Model labels: model names stay VERBATIM English; only floor-model words translate.
  const modelLabel = (m: string) => ({
    hcie: 'HCIE', sakt: 'SAKT', dkt: 'DKT', bkt: 'BKT', irt_1pl: 'IRT-1PL',
    gkt: 'GKT', greedy_correct_rate: t('benchmarksBody.modelGreedy'),
    random: t('benchmarksBody.modelRandom'), static_prior: t('benchmarksBody.modelStatic'),
  }[m] ?? m.toUpperCase())
  // Governance-dimension labels (technical terms kept VERBATIM).
  const DIM_LABEL: Record<string, string> = {
    delta_m: t('benchmarksBody.dimDeltaM'), transfer_realized: t('benchmarksBody.dimTransferGraph'),
    transfer_prospective: t('benchmarksBody.dimTransferProspective'), challenge: t('benchmarksBody.dimChallenge'),
    uncertainty: t('benchmarksBody.dimUncertainty'), zpd: t('benchmarksBody.dimZpd'),
  }

  // Regime: non-graph (per-dataset DB evals) vs graph (Phase-2 matched, incl GKT).
  // DEFAULT = 'graph' so the THESIS HEADLINE (matched 10-user AUC: HCIE 0.609 vs
  // BKT 0.612) leads. The nongraph/cross tabs are all-users POOLED AUC (exploratory)
  // and carry a pointer banner back to this tab.
  const [regime, setRegime] = useState<'nongraph' | 'graph' | 'cross'>('graph')
  const [runsByDataset, setRunsByDataset] = useState<Record<string, any[]>>({})
  const [latestByKey, setLatestByKey] = useState<Record<string, string>>({})
  const [bestByKey, setBestByKey] = useState<Record<string, string>>({})
  const [dataset, setDataset] = useState<string>('junyi')
  const [pick, setPick] = useState<'best' | 'latest'>('best')
  const [runId, setRunId] = useState('')
  const [showAllRuns, setShowAllRuns] = useState(false)
  const [bench, setBench] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [metric, setMetric] = useState<'auc' | 'accuracy' | 'brier'>('auc')
  // Graph-regime data (Phase-2 matched comparison)
  const [graphBench, setGraphBench] = useState<any>(null)
  const [graphErr, setGraphErr] = useState<string | null>(null)
  const [graphWindow, setGraphWindow] = useState<'w5' | 'w10' | 'w20' | 'overall'>('overall')
  // ADC per-signal activation — the system's OWN verdict (canonical classifier over the
  // authoritative raw_governance_snapshot), not a hand-authored claim.
  const [adc, setAdc] = useState<any>(null)
  const [adcErr, setAdcErr] = useState<string | null>(null)

  // Load the graph-regime comparison once
  useEffect(() => {
    (async () => {
      try {
        const r = await fetch(`${BACKEND}/v3/frontend/dashboard/graph-baseline`,
          { headers: getAuthHeaders(), signal: AbortSignal.timeout(10000) })
        if (r.ok) { setGraphBench(await r.json()); setGraphErr(null) }
        else setGraphErr(`HTTP ${r.status}`)
      } catch {
        // Don't spin "Loading…" forever — record the failure so the section can say so.
        setGraphErr('could not reach the backend')
      }
    })()
  }, [])

  // Load the ADC per-signal activation profile for the thesis anchor once
  useEffect(() => {
    (async () => {
      try {
        const r = await fetch(`${BACKEND}/v3/frontend/dashboard/adc-activation`,
          { headers: getAuthHeaders(), signal: AbortSignal.timeout(10000) })
        if (r.ok) { setAdc(await r.json()); setAdcErr(null) }
        else setAdcErr(`HTTP ${r.status}`)
      } catch {
        setAdcErr('could not reach the backend')
      }
    })()
  }, [])

  // ── Load the dataset run index (live — not hardcoded) ───────────────────────
  useEffect(() => {
    (async () => {
      try {
        const r = await fetch(`${BACKEND}/v3/frontend/dashboard/cohort-runs?group=dataset`,
          { headers: getAuthHeaders(), signal: AbortSignal.timeout(10000) })
        if (!r.ok) return
        const d = await r.json()
        const grouped: Record<string, any[]> = {}
        for (const run of (d.runs ?? [])) {
          const k = run.dataset || 'other'
          ;(grouped[k] ??= []).push(run)
        }
        setRunsByDataset(grouped)
        setLatestByKey(d.latest_by_key ?? {})
        setBestByKey(d.best_by_key ?? {})
      } catch { /* leave empty */ }
    })()
  }, [])

  // Resolve which run to load when dataset / pick changes
  useEffect(() => {
    const id = pick === 'best' ? bestByKey[dataset] : latestByKey[dataset]
    if (id) setRunId(id)
  }, [dataset, pick, bestByKey, latestByKey])

  // ── Load benchmark for the chosen run ───────────────────────────────────────
  const loadBench = useCallback(async (id: string) => {
    if (!id) return
    setLoading(true)
    try {
      const r = await fetch(`${BACKEND}/v3/frontend/dashboard/kt-benchmark/${id}`,
        { headers: getAuthHeaders(), signal: AbortSignal.timeout(12000) })
      if (r.ok) setBench(await r.json())
    } catch { /* keep previous */ }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { if (runId) loadBench(runId) }, [runId, loadBench])

  const models: any[] = bench?.models ?? []
  // Brier is lower-is-better; auc/accuracy higher-is-better
  const sorted = [...models].sort((a, b) =>
    metric === 'brier' ? (a[metric] ?? 1) - (b[metric] ?? 1)
                       : (b[metric] ?? 0) - (a[metric] ?? 0))
  const chartData = sorted.map(m => ({
    name: modelLabel(m.model_id),
    value: m[metric] ?? 0,
    model_id: m.model_id,
    is_hcie: m.is_hcie,
  }))
  const hcie = models.find(m => m.is_hcie)

  // ── Cold-start window curves (THE hypothesis lens) ──────────────────────────
  const windows: any[] = bench?.windows ?? []
  // Recharts line-chart shape: one row per window-position, a key per model.
  const WINDOW_POSITIONS = [
    { key: 'auc_w5',      x: `${t('benchmarksBody.firstWordCap')} 5` },
    { key: 'auc_w10',     x: `${t('benchmarksBody.firstWordCap')} 10` },
    { key: 'auc_w20',     x: `${t('benchmarksBody.firstWordCap')} 20` },
    { key: 'auc_overall', x: t('benchmarksBody.winAll') },
  ]
  const lineData = WINDOW_POSITIONS.map(pos => {
    const row: any = { x: pos.x }
    for (const m of windows) row[m.model_id] = m[pos.key]
    return row
  })
  // delta readout sorted least-negative (most sparsity-robust) first
  const deltaRows = [...windows].sort((a, b) =>
    (b.cold_start_delta ?? -99) - (a.cold_start_delta ?? -99))
  const validationProvisional = bench?.validation_status === 'provisional'

  // Pooled-vs-matched pointer: the thesis headline (0.609 matched) lives on the
  // Graph-regime tab; the nongraph/cross tabs show all-users POOLED AUC (exploratory).
  const pooledBanner = (
    <Callout tone="warn" style={{ marginBottom: 14 }}
      title={t('benchmarksBody.pooledBannerTitle')}>
      {t('benchmarksBody.pooledBannerA')} <strong>{t('benchmarksBody.pooledBannerNotHeadline')}</strong>.
      {' '}{t('benchmarksBody.pooledBannerB')} <strong>{t('benchmarksBody.pooledBannerCompanion')}</strong> — HCIE 0.609 vs BKT 0.612, DKT 0.589,
      SAKT 0.573, GKT 0.571 {t('benchmarksBody.pooledBannerC')}{' '}
      <button onClick={() => setRegime('graph')} style={{ background: 'none', border: 'none', padding: 0,
        color: ui.tone.ok.fg, fontWeight: ui.font.weight.heavy, cursor: 'pointer', textDecoration: 'underline', fontSize: ui.font.size.sm }}>
        🟢 {t('benchmarksBody.graphRegimeTab')}</button> {t('benchmarksBody.pooledBannerTabSuffix')}
    </Callout>
  )

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: `${ui.space.xl}px ${ui.space.lg}px 64px` }}>

      {/* ── INTENT FIRST — what this page is asking (before any numbers) ──────── */}
      <div data-tour="page-intro" style={{ marginBottom: ui.space.lg }}>
        <Eyebrow color={ui.tone.warn.fg}>{t('benchmarks.eyebrow')}</Eyebrow>
        <h1 style={{ fontSize: ui.font.size.h1, fontWeight: ui.font.weight.heavy, color: ui.color.ink, margin: 0, lineHeight: 1.1 }}>
          {t('benchmarks.title')}
        </h1>
        <div style={{ fontSize: ui.font.size.md, color: ui.color.muted, marginTop: ui.space.sm, maxWidth: 780, lineHeight: 1.5 }}>
          {t('benchmarks.intro')}
        </div>
      </div>

      {/* ── CANONICAL HEADLINE — HCIE on the thesis canonical (Kalman-alone, m_K) ── */}
      <CanonicalHeadlinePanel t={t} />

      {/* ── REGIME TOGGLE — the two comparison worlds ────────────────────────── */}
      <div data-tour="regime-toggle" style={{ display: 'flex', gap: 0, marginBottom: ui.space.lg, border: `1px solid ${ui.color.lineStrong}`,
                    borderRadius: ui.radius.lg, overflow: 'hidden', width: 'fit-content', maxWidth: '100%', flexWrap: 'wrap' }}>
        {([
          ['nongraph', `🟡 ${t('benchmarksBody.regimeNongraphLabel')}`, t('benchmarksBody.regimeNongraphSub')],
          ['graph', `🟢 ${t('benchmarksBody.graphRegimeTab')}`, t('benchmarksBody.regimeGraphSub')],
          ['cross', `🔵 ${t('benchmarksBody.regimeCrossLabel')}`, t('benchmarksBody.regimeCrossSub')],
        ] as const).map(([id, lbl, sub]) => (
          <button key={id} onClick={() => setRegime(id)} style={{
            padding: `${ui.space.sm}px ${ui.space.lg}px`, fontSize: ui.font.size.md, fontWeight: ui.font.weight.bold,
            border: 'none', cursor: 'pointer', textAlign: 'left', transition: 'all 0.15s',
            background: regime === id ? (id === 'graph' ? ui.tone.ok.fg : ui.tone.warn.fg) : ui.color.surface,
            color: regime === id ? ui.color.surface : ui.color.body,
          }}>
            <div>{lbl}</div>
            <div style={{ fontSize: ui.font.size.xs, fontWeight: 400, opacity: 0.85, marginTop: 1 }}>{sub}</div>
          </button>
        ))}
      </div>

      {/* ════ DEPLOYED RUNTIME vs BKT — always-on close-out result ════════════
          Shown above every regime: the deployed runtime (individualized-prior
          cold-start + 2-learner Kalman+Bayesian) now beats BKT per-window, per
          traffic class. Honest labels (synthetic ≤5 inflated / live no-AUC) are
          baked into the component so the win cannot be misread. ════════════ */}
      <DeployedBeatsBKT />

      {/* ════ GRAPH REGIME — Phase-2 matched, HCIE at full prowess ════════════ */}
      {regime === 'graph' && (
        <div>
          <Panel tone="ok" style={{ marginBottom: ui.space.lg }}>
            <Eyebrow color={ui.tone.ok.fg}>🟢 {t('benchmarksBody.graphIntroEyebrow')}</Eyebrow>
            <div style={{ fontSize: ui.font.size.md, color: ui.color.heading, lineHeight: 1.65 }}>
              <strong>{t('benchmarksBody.graphIntroLead')}</strong> {t('benchmarksBody.graphIntroA')} <strong>GKT</strong>,
              {' '}{t('benchmarksBody.graphIntroB')}
              <strong> {t('benchmarksBody.graphIntroZeroShot')}</strong> {t('benchmarksBody.graphIntroC')}
            </div>
          </Panel>

          {graphBench?.status === 'ok' ? (() => {
            const ref = graphBench.models.find((m: any) => m.is_phase1_ref)
            const live = graphBench.models.filter((m: any) => !m.is_phase1_ref)
            const sorted = [...live].sort((a, b) => (b[graphWindow] ?? 0) - (a[graphWindow] ?? 0))
            const hcie = live.find((m: any) => m.is_hcie)
            const colorOf = (m: any) => m.is_hcie ? '#6C3483' : m.is_graph_aware ? '#117A65' : '#2980B9'
            return (
              <>
                {/* Provisional for graph regime */}
                <Callout tone="bad" style={{ marginBottom: ui.space.lg }} title={t('benchmarksBody.provisionalSmallNTitle')}>
                  {graphBench.validation_note} ({graphBench.train_users} {t('benchmarksBody.trainUsers')} / {graphBench.eval_users} {t('benchmarksBody.evalUsers')})
                </Callout>

                {/* HCIE rank headline */}
                <div style={{ display: 'flex', gap: ui.space.md, marginBottom: ui.space.lg, flexWrap: 'wrap' }}>
                  <Panel tone="ok" pad="md" style={{ flex: '1 1 220px' }}>
                    <div style={{ fontSize: ui.font.size.xs, fontWeight: ui.font.weight.bold, color: ui.tone.ok.fg, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      {t('benchmarksBody.hciePhase2OverallRank')}
                    </div>
                    <div style={{ fontSize: ui.font.size.h1, fontWeight: ui.font.weight.heavy, color: ui.tone.ok.fg, marginTop: 2 }}>
                      #{graphBench.hcie_overall_rank}<span style={{ fontSize: ui.font.size.lg, fontWeight: ui.font.weight.bold, color: ui.color.faint }}> {t('benchmarksBody.ofN')} {graphBench.n_models}</span>
                    </div>
                    <div style={{ fontSize: ui.font.size.sm, color: ui.color.body, marginTop: ui.space.xs }}>
                      {t('benchmarksBody.rankCaptionBeatsGkt')}
                    </div>
                  </Panel>
                  {ref && hcie && (
                    <Panel pad="md" style={{ flex: '1 1 220px' }}>
                      <div style={{ fontSize: ui.font.size.xs, fontWeight: ui.font.weight.bold, color: ui.color.muted, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                        {t('benchmarksBody.graphLiftLabel')}
                      </div>
                      <div style={{ fontSize: ui.font.size.h1, fontWeight: ui.font.weight.heavy, color: ui.modelColor.bkt, marginTop: 2 }}>
                        +{(((hcie.w5 ?? 0) - (ref.w5 ?? 0)) * 100).toFixed(1)}
                      </div>
                      <div style={{ fontSize: ui.font.size.sm, color: ui.color.body, marginTop: ui.space.xs }}>
                        {t('benchmarksBody.graphOff')} {(ref.w5 * 100).toFixed(0)}% → {t('benchmarksBody.graphOn')} {(hcie.w5 * 100).toFixed(0)}% — {t('benchmarksBody.theTransferDimension')}
                      </div>
                    </Panel>
                  )}
                </div>

                {/* window toggle */}
                <div style={{ display: 'flex', gap: ui.space.xs, marginBottom: ui.space.md, alignItems: 'center', flexWrap: 'wrap' }}>
                  <span style={{ fontSize: ui.font.size.sm, color: ui.color.muted, fontWeight: ui.font.weight.bold }}>{t('benchmarksBody.windowLabel')}</span>
                  {(['w5','w10','w20','overall'] as const).map(w => (
                    <button key={w} onClick={() => setGraphWindow(w)} style={{
                      padding: `${ui.space.xs}px ${ui.space.md}px`, fontSize: ui.font.size.sm, fontWeight: ui.font.weight.medium, borderRadius: ui.radius.sm, cursor: 'pointer',
                      border: `1px solid ${graphWindow === w ? ui.tone.ok.fg : ui.color.lineStrong}`,
                      background: graphWindow === w ? ui.tone.ok.fg : ui.color.surface, color: graphWindow === w ? ui.color.surface : ui.color.body,
                    }}>{w === 'overall' ? t('benchmarksBody.winAll') : `${t('benchmarksBody.winFirst')} ${w.slice(1)}`}</button>
                  ))}
                </div>

                {/* bar chart */}
                <Panel style={{ marginBottom: ui.space.lg }}>
                  <SectionTitle sub={t('benchmarksBody.graphBarSub')}>
                    AUC {t('benchmarksBody.atWord')} {graphWindow === 'overall' ? t('benchmarksBody.allInteractions') : `${t('benchmarksBody.firstWord')} ${graphWindow.slice(1)}`} — {t('benchmarksBody.graphBarTitleSuffix')}
                  </SectionTitle>
                  {/* legend: the three model classes this regime distinguishes */}
                  <div style={{ display: 'flex', gap: ui.space.lg, flexWrap: 'wrap', marginBottom: ui.space.md }}>
                    {([[t('benchmarksBody.legendHcieZeroShot'), ui.modelColor.hcie], [t('benchmarksBody.legendGraphAware'), ui.tone.ok.fg], [t('benchmarksBody.legendTrainedKt'), ui.modelColor.sakt]] as const).map(([lbl, col]) => (
                      <span key={lbl} style={{ display: 'inline-flex', alignItems: 'center', gap: ui.space.xs, fontSize: ui.font.size.sm, color: ui.color.muted }}>
                        <span style={{ width: 10, height: 10, borderRadius: 2, background: col, display: 'inline-block' }} />{lbl}
                      </span>
                    ))}
                  </div>
                  <ResponsiveContainer width="100%" height={280}>
                    <BarChart data={sorted.map((m: any) => ({ name: m.model.replace(' (graph-aware)',''), value: m[graphWindow], is_hcie: m.is_hcie, is_graph_aware: m.is_graph_aware, model: m.model }))}
                              layout="vertical" margin={{ left: 10, right: 40, top: 0, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke={ui.color.grid} />
                      <XAxis type="number" domain={[0.5, 0.9]} tickFormatter={v => `${(v*100).toFixed(0)}%`}
                        tick={{ fontSize: ui.font.size.xs, fill: ui.color.faint }} axisLine={false} tickLine={false} />
                      <YAxis type="category" dataKey="name" width={90}
                        tick={{ fontSize: ui.font.size.sm, fill: ui.color.body }} axisLine={false} tickLine={false} />
                      <Tooltip cursor={{ fill: ui.color.subtle }}
                        contentStyle={{ borderRadius: ui.radius.md, border: `1px solid ${ui.color.line}`, fontSize: ui.font.size.sm }}
                        formatter={(v: any) => `${(Number(v)*100).toFixed(1)}%`} />
                      <ReferenceLine x={0.5} stroke={ui.tone.bad.fg} strokeDasharray="4 4"
                        label={{ value: t('benchmarksBody.chance'), fontSize: ui.font.size.xs, fill: ui.tone.bad.fg, position: 'top' }} />
                      <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                        {sorted.map((m: any, i: number) => (
                          <Cell key={i} fill={colorOf(m)} opacity={m.is_hcie ? 1 : 0.85} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                  <Callout tone="info" style={{ marginTop: ui.space.md }} title={t('benchmarksBody.honestReadTitle')}>
                    {t('benchmarksBody.honestReadA')} <strong>{t('benchmarksBody.honestReadLeadsOverall')}</strong> AUC
                    (lagged-Kalman 0.6051 vs BKT 0.5963, +0.0088; tie-aware) {t('benchmarksBody.honestReadB')} <strong>{t('benchmarksBody.honestReadSignificant')}</strong>
                    (+0.0088 at n=10 → +0.0125 at n=76, 95% CI [+0.0017, +0.0226]). {t('benchmarksBody.honestReadC')} <strong>GKT</strong> — {t('benchmarksBody.honestReadD')}
                    {' '}{t('benchmarksBody.honestReadE')}
                  </Callout>
                </Panel>

                {/* ════ TRANSFER-ACTIVATION — the graph-regime signature plot ════
                    The ONE comparison unique to this regime: the SAME HCIE runtime
                    with the prerequisite graph dormant (Phase 1) vs injected
                    (Phase 2), across cold-start windows. The vertical gap between
                    the two lines IS the transfer dimension switching on — it exists
                    in no other regime, so no other regime can show this plot. */}
                {ref && hcie && (
                  <Panel style={{ marginBottom: ui.space.lg }}>
                    <SectionTitle sub={<>{t('benchmarksBody.transferActivationSubA')} <em>{t('benchmarksBody.transferActivationSubOnly')}</em> {t('benchmarksBody.transferActivationSubB')}</>}>
                      {t('benchmarksBody.transferActivationTitle')}
                    </SectionTitle>
                    <ResponsiveContainer width="100%" height={280}>
                      <LineChart data={[
                        { x: `${t('benchmarksBody.firstWordCap')} 5`,  dormant: ref.w5,      injected: hcie.w5 },
                        { x: `${t('benchmarksBody.firstWordCap')} 10`, dormant: ref.w10,     injected: hcie.w10 },
                        { x: `${t('benchmarksBody.firstWordCap')} 20`, dormant: ref.w20,     injected: hcie.w20 },
                        { x: t('benchmarksBody.winAll'),      dormant: ref.overall, injected: hcie.overall },
                      ]} margin={{ left: 0, right: 28, top: 8, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke={ui.color.grid} />
                        <XAxis dataKey="x" tick={{ fontSize: ui.font.size.sm, fill: ui.color.body }} axisLine={false} tickLine={false} />
                        <YAxis domain={[0.45, 0.95]} tickFormatter={v => `${(v * 100).toFixed(0)}%`}
                          tick={{ fontSize: ui.font.size.xs, fill: ui.color.faint }} axisLine={false} tickLine={false} />
                        <Tooltip cursor={{ stroke: ui.color.lineStrong }}
                          contentStyle={{ borderRadius: ui.radius.md, border: `1px solid ${ui.color.line}`, fontSize: ui.font.size.sm }}
                          formatter={(v: any, n: any) => [v != null ? `${(Number(v) * 100).toFixed(1)}%` : '—',
                          n === 'injected' ? t('benchmarksBody.graphInjectedPhase2') : t('benchmarksBody.graphDormantPhase1')]} />
                        <ReferenceLine y={0.5} stroke={ui.tone.bad.fg} strokeDasharray="4 4"
                          label={{ value: t('benchmarksBody.chance'), fontSize: ui.font.size.xs, fill: ui.tone.bad.fg, position: 'right' }} />
                        <Line dataKey="dormant" name="dormant" stroke={ui.color.faint} strokeWidth={2}
                          strokeDasharray="5 4" dot={{ r: 3 }} type="monotone" />
                        <Line dataKey="injected" name="injected" stroke={ui.modelColor.hcie} strokeWidth={3.5}
                          dot={{ r: 4 }} type="monotone" />
                        <Legend formatter={(v) => v === 'injected' ? t('benchmarksBody.graphInjectedPhase2') : t('benchmarksBody.graphDormantPhase1')}
                          wrapperStyle={{ fontSize: ui.font.size.xs }} />
                      </LineChart>
                    </ResponsiveContainer>
                    <Callout tone="accent" style={{ marginTop: ui.space.md }} title={t('benchmarksBody.readTitle')}>
                      {t('benchmarksBody.transferReadA')}
                      (≈{(ref.w5 * 100).toFixed(0)}–{(ref.overall * 100).toFixed(0)}%). {t('benchmarksBody.transferReadB')} <strong>+{(((hcie.w5 ?? 0) - (ref.w5 ?? 0)) * 100).toFixed(1)} {t('benchmarksBody.pts')}</strong> ({t('benchmarksBody.firstWordCap')} 5) —
                      {' '}{t('benchmarksBody.transferReadC')}
                    </Callout>
                  </Panel>
                )}

                {/* ════ ADC PER-SIGNAL ACTIVATION — the instrument's OWN verdict ════
                    Reads /adc-activation: the canonical classifier's per-dimension
                    active/dormant over the authoritative raw_governance_snapshot. The
                    system reporting on itself, not a hand-written claim. */}
                {adc?.status === 'ok' && (
                  <Panel style={{ marginBottom: ui.space.lg }}>
                    <SectionTitle sub={
                      <>{t('benchmarksBody.adcSubA')} <code>{adc.input}</code> {t('benchmarksBody.adcSubB')}{' '}
                      <span style={{ fontWeight: ui.font.weight.bold, color: adc.source === 'sealed' ? ui.tone.ok.fg : ui.tone.warn.fg }}>
                        {adc.source === 'sealed' ? `✓ ${t('benchmarksBody.adcFrozenInSeal')}` : `⟳ ${t('benchmarksBody.adcLiveRecompute')}`}
                      </span></>
                    }>
                      {t('benchmarksBody.adcSectionTitle')}
                    </SectionTitle>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: ui.space.sm }}>
                      {GOV_DIMS.map(dim => {
                        const d = adc.per_dimension?.[dim]
                        if (!d) return null
                        const status = d.active ? 'ACTIVE'
                          : (d.has_signal && d.weight_collapsed) ? 'SUPPRESSED' : 'DORMANT'
                        const tn = status === 'ACTIVE' ? 'ok' : status === 'SUPPRESSED' ? 'warn' : 'neutral'
                        const statusLabel = status === 'ACTIVE' ? t('benchmarksBody.statusActive')
                          : status === 'SUPPRESSED' ? t('benchmarksBody.statusSuppressed') : t('benchmarksBody.statusDormant')
                        return (
                          <Panel key={dim} tone={tn} pad="md">
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                              <span style={{ fontSize: ui.font.size.base, fontWeight: ui.font.weight.bold, color: ui.color.heading }}>
                                {DIM_LABEL[dim] ?? dim}
                              </span>
                              <Tag tone={tn}>{statusLabel}</Tag>
                            </div>
                            <div style={{ fontSize: ui.font.size.xs, color: ui.color.muted, marginTop: ui.space.xs }}>
                              {t('benchmarksBody.fires')} {((d.nonzero_fraction ?? 0) * 100).toFixed(0)}% {t('benchmarksBody.ofSteps')} · w̄={(d.weight_mean ?? 0).toFixed(2)}
                            </div>
                          </Panel>
                        )
                      })}
                    </div>
                    <Callout tone="info" title={t('benchmarksBody.readTitle')} style={{ marginTop: ui.space.md }}>
                      {t('benchmarksBody.adcReadA')} {t('benchmarksBody.adcReadActiveHere')}{' '}
                      <strong>{(adc.active_dimensions ?? []).join(', ') || '—'}</strong>; {t('benchmarksBody.adcReadDormant')}{' '}
                      <strong>{(adc.dormant_dimensions ?? []).join(', ') || '—'}</strong> {t('benchmarksBody.adcReadB')}
                    </Callout>
                  </Panel>
                )}
                {adc && adc.status !== 'ok' && (
                  <Callout tone="neutral" style={{ marginBottom: ui.space.lg, borderStyle: 'dashed', color: ui.color.faint }}>
                    {t('benchmarksBody.adcUnavailable')}{adcErr ? ` (${adcErr})` : ''}.
                  </Callout>
                )}

                {/* nav to other experiments */}
                <Link href="/dashboard/data" style={{ textDecoration: 'none' }}>
                  <Panel tone="ok" pad="md" style={{ marginBottom: ui.space.lg, fontSize: ui.font.size.base, color: ui.tone.ok.fg, fontWeight: ui.font.weight.bold }}>
                    🕸 {t('benchmarksBody.navSeeJunyiGraph')}
                  </Panel>
                </Link>
              </>
            )
          })() : (
            <div style={{ textAlign: 'center', padding: ui.space.xxl + ui.space.lg, color: graphErr ? ui.tone.bad.fg : ui.color.faint, fontSize: ui.font.size.md }}>
              {graphBench?.status === 'no_data'
                ? t('benchmarksBody.graphNoData')
                : graphErr
                  ? `⚠ ${t('benchmarksBody.graphLoadError')} (${graphErr}).`
                  : `⟳ ${t('benchmarksBody.graphLoading')}`}
            </div>
          )}
        </div>
      )}

      {/* ════ CROSS-DATASET REGIME — unified matrix + scale sweep ═════════════ */}
      {regime === 'cross' && <div>{pooledBanner}<CrossDatasetBenchmark /></div>}

      {/* ════ NON-GRAPH REGIME (existing content) ═════════════════════════════ */}
      {regime === 'nongraph' && (
      <div>

      {pooledBanner}

      {/* Hypothesis card — the question, stated before the data */}
      <Panel tone="info" style={{ marginBottom: ui.space.lg }}>
        <Eyebrow color={ui.tone.info.fg}>🎯 {t('benchmarksBody.hypothesisEyebrow')}</Eyebrow>
        <div style={{ fontSize: ui.font.size.md, color: ui.color.heading, lineHeight: 1.65 }}>
          {t('benchmarksBody.hypoA')} <strong>{t('benchmarksBody.hypoDataHungry')}</strong> {t('benchmarksBody.hypoB')}
          {' '}<strong>{t('benchmarksBody.hypoColdStart')}</strong> {t('benchmarksBody.hypoC')}
          <strong> {t('benchmarksBody.hypoQuestion')}</strong>
          {' '}{t('benchmarksBody.hypoD')}
        </div>
      </Panel>

      {/* ── VALIDATION-STATUS banner — numbers must not masquerade as findings ── */}
      {validationProvisional && (
        <Callout tone="bad" style={{ marginBottom: ui.space.lg }} title={t('benchmarksBody.provisionalNotValidatedTitle')}>
          {bench?.validation_note ?? t('benchmarksBody.validationDefaultNote')}
          {' '}{t('benchmarksBody.validationA')} <em>{t('benchmarksBody.validationFirstNSlice')}</em> —
          {t('benchmarksBody.validationB')} <strong>{t('benchmarksBody.validationTrainOnFew')}</strong> {t('benchmarksBody.validationC')} <strong>{t('benchmarksBody.validationTool')}</strong>{t('benchmarksBody.validationD')}
          {' '}{t('benchmarksBody.validationMethods')}
        </Callout>
      )}

      <div style={{ fontSize: ui.font.size.base, color: ui.color.muted, marginBottom: ui.space.sm, maxWidth: 760, lineHeight: 1.5 }}>
        {t('benchmarksBody.zeroShotA')} <strong>{t('benchmarksBody.zeroShot')}</strong> {t('benchmarksBody.zeroShotB')}
        {' '}{t('benchmarksBody.zeroShotC')}
        {' '}(<Link href="/dashboard/cohorts" style={{ color: ui.modelColor.hcie, fontWeight: ui.font.weight.medium }}>{t('benchmarksBody.cohortStudyLink')}</Link>).
      </div>

      {/* ── Dataset picker ───────────────────────────────────────────────────── */}
      <Panel data-tour="dataset-picker" style={{ margin: `${ui.space.lg}px 0` }}>
        <SectionTitle>{t('benchmarksBody.chooseDataset')}</SectionTitle>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: ui.space.sm }}>
          {DATASET_ORDER.filter(k => runsByDataset[k]?.length).map(k => {
            const meta = DATASET_META[k]
            const active = dataset === k
            const runCount = runsByDataset[k]?.length ?? 0
            return (
              <button key={k} onClick={() => { setDataset(k); setShowAllRuns(false) }} style={{
                textAlign: 'left', cursor: 'pointer',
                background: active ? ui.tone.warn.bg : ui.color.surface,
                border: `2px solid ${active ? ui.tone.warn.fg : ui.color.line}`,
                borderRadius: ui.radius.lg, padding: `${ui.space.md}px ${ui.space.md}px`, transition: 'all 0.15s',
              }}>
                <Tag tone="warn">{meta.badge}</Tag>
                <div style={{ fontSize: ui.font.size.md, fontWeight: ui.font.weight.heavy, color: ui.color.heading, marginTop: ui.space.xs }}>{meta.label}</div>
                <div style={{ fontSize: ui.font.size.xs, color: ui.color.muted, marginTop: 2 }}>{meta.origin}</div>
                <div style={{ fontSize: ui.font.size.xs, color: ui.color.faint, marginTop: ui.space.xs }}>{runCount} {runCount !== 1 ? t('benchmarksBody.runsPlural') : t('benchmarksBody.runSingular')}</div>
              </button>
            )
          })}
        </div>

        {/* best/latest toggle + see-other-runs */}
        <div style={{ display: 'flex', gap: ui.space.md, alignItems: 'center', marginTop: ui.space.lg, flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', gap: 0, border: `1px solid ${ui.color.lineStrong}`, borderRadius: ui.radius.sm, overflow: 'hidden' }}>
            {(['best','latest'] as const).map(p => (
              <button key={p} onClick={() => setPick(p)} style={{
                padding: `${ui.space.xs}px ${ui.space.md}px`, fontSize: ui.font.size.base, fontWeight: ui.font.weight.medium, border: 'none', cursor: 'pointer',
                background: pick === p ? ui.tone.warn.fg : ui.color.surface, color: pick === p ? ui.color.surface : ui.color.body,
              }}>
                {p === 'best' ? `★ ${t('benchmarksBody.bestRun')}` : `⟳ ${t('benchmarksBody.latestRun')}`}
              </button>
            ))}
          </div>
          <button onClick={() => setShowAllRuns(s => !s)} style={{
            fontSize: ui.font.size.base, color: ui.modelColor.hcie, background: 'none', border: 'none',
            cursor: 'pointer', textDecoration: 'underline' }}>
            {showAllRuns ? t('benchmarksBody.hideOtherRuns') : t('benchmarksBody.seeOtherRuns')}
          </button>
          <span style={{ fontSize: ui.font.size.xs, color: ui.color.faint, fontFamily: 'monospace' }}>
            {runId ? `${runId.slice(0,16)}…` : ''}
          </span>
        </div>

        {/* all-runs expander */}
        {showAllRuns && (
          <div style={{ marginTop: ui.space.sm, display: 'flex', flexDirection: 'column', gap: ui.space.xs }}>
            {(runsByDataset[dataset] ?? []).map(run => (
              <button key={run.run_id} onClick={() => setRunId(run.run_id)} style={{
                textAlign: 'left', cursor: 'pointer', fontSize: ui.font.size.sm,
                background: runId === run.run_id ? ui.tone.accent.bg : ui.color.subtle,
                border: `1px solid ${runId === run.run_id ? ui.modelColor.hcie : ui.color.line}`,
                borderRadius: ui.radius.sm, padding: `${ui.space.xs}px ${ui.space.sm}px`, display: 'flex',
                justifyContent: 'space-between', gap: ui.space.sm }}>
                <span style={{ fontFamily: 'monospace', color: ui.color.body }}>{run.run_id.slice(0,24)}…</span>
                <span style={{ color: ui.color.muted }}>
                  {run.completed}/{run.total} · {run.status}
                  {run.started_at ? ` · ${run.started_at.slice(0,10)}` : ''}
                </span>
              </button>
            ))}
          </div>
        )}
      </Panel>

      {/* ══ HERO: COLD-START CURVE — the hypothesis lens ══════════════════════ */}
      {bench?.status === 'ok' && lineData.length > 0 && windows.length > 0 && (
        <Panel tone="info" data-tour="coldstart-curve" style={{ marginBottom: ui.space.lg, borderWidth: 2 }}>
          <SectionTitle sub={<>{t('benchmarksBody.heroSubA')}
            <strong> {t('benchmarksBody.heroSubDataHungry')}</strong>{t('benchmarksBody.heroSubB')}</>}>
            {t('benchmarksBody.heroTitle')}
          </SectionTitle>
          <ResponsiveContainer width="100%" height={320}>
            <LineChart data={lineData} margin={{ left: 0, right: 24, top: 8, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={ui.color.grid} />
              <XAxis dataKey="x" tick={{ fontSize: ui.font.size.sm, fill: ui.color.body }} axisLine={false} tickLine={false} />
              <YAxis domain={[0.45, 0.8]} tickFormatter={v => `${(v*100).toFixed(0)}%`}
                tick={{ fontSize: ui.font.size.xs, fill: ui.color.faint }} axisLine={false} tickLine={false} />
              <Tooltip cursor={{ stroke: ui.color.lineStrong }}
                contentStyle={{ borderRadius: ui.radius.md, border: `1px solid ${ui.color.line}`, fontSize: ui.font.size.sm }}
                formatter={(v: any, n: any) => [v != null ? `${(Number(v)*100).toFixed(1)}%` : '—', modelLabel(n)]} />
              <ReferenceLine y={0.5} stroke={ui.tone.bad.fg} strokeDasharray="4 4"
                label={{ value: t('benchmarksBody.chance'), fontSize: ui.font.size.xs, fill: ui.tone.bad.fg, position: 'right' }} />
              {windows.map(m => (
                <Line key={m.model_id} dataKey={m.model_id} name={m.model_id}
                  stroke={MODEL_COLOR[m.model_id] ?? ui.color.body}
                  strokeWidth={m.is_hcie ? 3.5 : 1.5}
                  dot={{ r: m.is_hcie ? 4 : 2 }} type="monotone"
                  opacity={m.is_hcie ? 1 : 0.7} connectNulls />
              ))}
              <Legend formatter={(v) => modelLabel(v)} wrapperStyle={{ fontSize: ui.font.size.xs }} />
            </LineChart>
          </ResponsiveContainer>

          {/* Data-starvation delta readout */}
          <div style={{ marginTop: ui.space.lg }}>
            <div style={{ fontSize: ui.font.size.base, fontWeight: ui.font.weight.bold, color: ui.color.heading, marginBottom: ui.space.sm }}>
              {t('benchmarksBody.deltaHeading')}
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: ui.space.xs }}>
              {deltaRows.filter(m => m.cold_start_delta != null).map(m => {
                const d = m.cold_start_delta as number
                const c = MODEL_COLOR[m.model_id] ?? ui.color.body
                // bar scaled: 0 delta = full robust; -0.06 ≈ worst
                const widthPct = Math.max(2, Math.min(100, (1 + d / 0.06) * 100))
                return (
                  <div key={m.model_id} style={{ display: 'flex', alignItems: 'center', gap: ui.space.sm,
                    background: m.is_hcie ? ui.tone.accent.bg : 'transparent',
                    border: `1px solid ${m.is_hcie ? ui.tone.accent.border : 'transparent'}`,
                    borderRadius: ui.radius.sm, padding: `${ui.space.xs}px ${ui.space.sm}px` }}>
                    <span style={{ width: 80, fontSize: ui.font.size.sm, fontWeight: m.is_hcie ? ui.font.weight.heavy : ui.font.weight.medium,
                                   color: m.is_hcie ? ui.modelColor.hcie : ui.color.body }}>{modelLabel(m.model_id)}</span>
                    <div style={{ flex: 1, height: 14, background: ui.color.grid, borderRadius: ui.radius.sm, overflow: 'hidden' }}>
                      <div style={{ height: '100%', width: `${widthPct}%`, background: c,
                                    borderRadius: ui.radius.sm, opacity: m.is_hcie ? 1 : 0.7 }} />
                    </div>
                    <span style={{ width: 56, textAlign: 'right', fontSize: ui.font.size.base, fontWeight: ui.font.weight.bold,
                      fontVariantNumeric: 'tabular-nums',
                      color: d >= -0.02 ? ui.modelColor.bkt : d >= -0.04 ? ui.modelColor.irt_1pl : ui.tone.bad.fg }}>
                      {d > 0 ? '+' : ''}{(d*100).toFixed(1)}
                    </span>
                  </div>
                )
              })}
            </div>
            <Callout tone="info" style={{ marginTop: ui.space.sm }} title={t('benchmarksBody.deltaCalloutTitle')}>
              {t('benchmarksBody.deltaCalloutA')} <em>{t('benchmarksBody.deltaCalloutWithhold')}</em> {t('benchmarksBody.deltaCalloutB')}
            </Callout>
          </div>
        </Panel>
      )}

      {/* ── HCIE headline + metric toggle (secondary: flat overall ranking) ──── */}
      {bench?.status === 'ok' && (
        <div style={{ display: 'flex', gap: ui.space.md, marginBottom: ui.space.lg, flexWrap: 'wrap', alignItems: 'stretch' }}>
          <Panel tone="accent" pad="md" style={{ flex: '1 1 240px' }}>
            <div style={{ fontSize: ui.font.size.xs, fontWeight: ui.font.weight.bold, color: ui.modelColor.hcie, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              {t('benchmarksBody.hcieRankByAuc')}
            </div>
            <div style={{ fontSize: ui.font.size.h1, fontWeight: ui.font.weight.heavy, color: ui.modelColor.hcie, marginTop: 2 }}>
              #{bench.hcie_auc_rank ?? '—'}<span style={{ fontSize: ui.font.size.lg, fontWeight: ui.font.weight.bold, color: ui.color.faint }}> {t('benchmarksBody.ofN')} {bench.n_models}</span>
            </div>
            {hcie && (
              <div style={{ fontSize: ui.font.size.sm, color: ui.color.body, marginTop: ui.space.xs }}>
                AUC {hcie.auc?.toFixed(3)} · {t('benchmarksBody.accAbbr')} {(hcie.accuracy*100)?.toFixed(1)}% · {hcie.n_predictions?.toLocaleString()} {t('benchmarksBody.predsAbbr')}
              </div>
            )}
          </Panel>
          <Panel pad="md" style={{ flex: '2 1 360px', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            <div style={{ fontSize: ui.font.size.sm, fontWeight: ui.font.weight.bold, color: ui.color.muted, marginBottom: ui.space.sm, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              {t('benchmarksBody.metricLabel')}
            </div>
            <div style={{ display: 'flex', gap: ui.space.xs, flexWrap: 'wrap' }}>
              {([['auc','AUC ↑'],['accuracy',`${t('benchmarksBody.metricAccuracy')} ↑`],['brier','Brier ↓']] as const).map(([m,lbl]) => (
                <button key={m} onClick={() => setMetric(m)} style={{
                  padding: `${ui.space.xs}px ${ui.space.md}px`, fontSize: ui.font.size.base, fontWeight: ui.font.weight.medium, borderRadius: ui.radius.sm, cursor: 'pointer',
                  border: `1px solid ${metric === m ? ui.modelColor.hcie : ui.color.lineStrong}`,
                  background: metric === m ? ui.modelColor.hcie : ui.color.surface, color: metric === m ? ui.color.surface : ui.color.body,
                }}>{lbl}</button>
              ))}
            </div>
            <div style={{ fontSize: ui.font.size.xs, color: ui.color.faint, marginTop: ui.space.sm }}>
              {metric === 'brier' ? t('benchmarksBody.metricBrierHint')
                : metric === 'auc' ? t('benchmarksBody.metricAucHint')
                : t('benchmarksBody.metricAccHint')}
            </div>
          </Panel>
        </div>
      )}

      {/* ── Bar chart: model vs metric ───────────────────────────────────────── */}
      {bench?.status === 'ok' && chartData.length > 0 && (
        <Panel data-tour="results-table" style={{ marginBottom: ui.space.lg }}>
          <Eyebrow color={ui.color.faint}>{t('benchmarksBody.secondaryViewEyebrow')}</Eyebrow>
          <SectionTitle sub={<>{t('benchmarksBody.secondarySubA')} {hcie?.n_predictions?.toLocaleString() ?? '—'} {t('benchmarksBody.secondarySubB')}</>}>
            {modelLabel('hcie')} {t('benchmarksBody.vsBaselines')} — {metric.toUpperCase()} ({t('benchmarksBody.allInteractions')})
          </SectionTitle>
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={chartData} layout="vertical" margin={{ left: 10, right: 40, top: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke={ui.color.grid} />
              <XAxis type="number"
                domain={metric === 'brier' ? [0, 'auto'] : [0, 1]}
                tickFormatter={v => metric === 'brier' ? v.toFixed(2) : `${(v*100).toFixed(0)}%`}
                tick={{ fontSize: ui.font.size.xs, fill: ui.color.faint }} axisLine={false} tickLine={false} />
              <YAxis type="category" dataKey="name" width={70}
                tick={{ fontSize: ui.font.size.sm, fill: ui.color.body }} axisLine={false} tickLine={false} />
              <Tooltip cursor={{ fill: ui.color.subtle }}
                contentStyle={{ borderRadius: ui.radius.md, border: `1px solid ${ui.color.line}`, fontSize: ui.font.size.sm }}
                formatter={(v: any) => metric === 'brier' ? Number(v).toFixed(4) : `${(Number(v)*100).toFixed(1)}%`} />
              {metric === 'auc' && <ReferenceLine x={0.5} stroke={ui.tone.bad.fg} strokeDasharray="4 4"
                label={{ value: t('benchmarksBody.chance'), fontSize: ui.font.size.xs, fill: ui.tone.bad.fg, position: 'top' }} />}
              <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                {chartData.map((d, i) => (
                  <Cell key={i} fill={MODEL_COLOR[d.model_id] ?? ui.color.body}
                        opacity={d.is_hcie ? 1 : 0.85} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <Callout tone="info" style={{ marginTop: ui.space.md }} title={t('benchmarksBody.readingThisTitle')}>
            {t('benchmarksBody.readingThisA')} <Link href="/dashboard/cohorts" style={{ color: ui.modelColor.hcie, fontWeight: ui.font.weight.medium }}>{t('benchmarksBody.policyStudyLink')}</Link>.
          </Callout>
        </Panel>
      )}

      {bench?.status === 'no_data' && (
        <Panel style={{ borderStyle: 'dashed', borderColor: ui.color.lineStrong,
                      padding: `${ui.space.xxl + ui.space.lg}px ${ui.space.xxl}px`, textAlign: 'center', color: ui.color.faint }}>
          <div style={{ fontSize: 32, marginBottom: ui.space.sm }}>📭</div>
          <div style={{ fontSize: ui.font.size.md, fontWeight: ui.font.weight.bold, color: ui.color.body }}>{t('benchmarksBody.noKtEvals')}</div>
          <div style={{ fontSize: ui.font.size.base, marginTop: ui.space.xs }}>
            {t('benchmarksBody.noKtEvalsHint')}
          </div>
        </Panel>
      )}
      {loading && !bench && (
        <div style={{ textAlign: 'center', padding: ui.space.xxl + ui.space.lg, color: ui.color.muted, fontSize: ui.font.size.md }}>⟳ {t('benchmarksBody.loadingBenchmark')}</div>
      )}
      </div>
      )}

      {/* Footer nav */}
      <div style={{ display: 'flex', gap: ui.space.sm, marginTop: ui.space.xxl, justifyContent: 'center', flexWrap: 'wrap' }}>
        <Link href="/dashboard/instructor" style={{ fontSize: ui.font.size.md, fontWeight: ui.font.weight.medium, color: ui.color.body,
          textDecoration: 'none', padding: `${ui.space.sm}px ${ui.space.xxl}px`, borderRadius: ui.radius.md,
          border: `1px solid ${ui.color.lineStrong}`, background: ui.color.surface }}>
          ← {t('benchmarksBody.navInstructorDashboard')}
        </Link>
        <Link href="/dashboard/data" style={{ fontSize: ui.font.size.md, fontWeight: ui.font.weight.bold, color: ui.tone.info.fg,
          textDecoration: 'none', padding: `${ui.space.sm}px ${ui.space.xxl}px`, borderRadius: ui.radius.md,
          border: `1px solid ${ui.tone.info.border}`, background: ui.tone.info.bg }}>
          🗂 {t('benchmarksBody.navKnowYourData')} →
        </Link>
        <Link href="/dashboard/cohorts" style={{ fontSize: ui.font.size.md, fontWeight: ui.font.weight.bold, color: ui.tone.accent.fg,
          textDecoration: 'none', padding: `${ui.space.sm}px ${ui.space.xxl}px`, borderRadius: ui.radius.md,
          border: `1px solid ${ui.tone.accent.border}`, background: ui.tone.accent.bg }}>
          ⚗ {t('benchmarksBody.navPolicyComparison')} →
        </Link>
      </div>

      <PageGuide tourId="benchmarks" steps={STEPS} />
    </div>
  )
}
