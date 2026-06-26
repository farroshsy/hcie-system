'use client'

/**
 * Figure Atlas — every thesis/journal figure with a live "Fetch Data" button.
 *
 * Each card maps to one figure reference in THESIS_V2.md / JOURNAL_V2.md.
 * Clicking "Get Data" hits /v3/frontend/figures/{id} and renders the response
 * inline as a table, bar summary, or key-value list.
 *
 * The manifest is fetched once from /v3/frontend/figures/manifest so this page
 * always reflects the current backend registry.
 */

import { useEffect, useState, useCallback } from 'react'
import { getBackendUrl } from '@/lib/api/backend-url'
import { useT } from '@/contexts/language_context'
import { NextSteps } from '@/components/review/NextSteps'

const BACKEND = getBackendUrl()

function authHeaders(): HeadersInit {
  const tok =
    typeof window !== 'undefined' &&
    (localStorage.getItem('hcie_auth_token') || localStorage.getItem('access_token'))
  return tok
    ? { Authorization: `Bearer ${tok}`, 'Content-Type': 'application/json' }
    : { 'Content-Type': 'application/json' }
}

// ── colour palette ─────────────────────────────────────────────────────────────
const ACCENT = '#1565C0'
const ACCENT_LIGHT = '#E3F2FD'
const WITHDRAWN = '#C0392B'
const WITHDRAWN_LIGHT = '#FDEDEC'
const GREEN = '#1E8449'
const GREEN_LIGHT = '#EAFAF1'
const NEUTRAL = '#4A5568'

// ── tiny components ────────────────────────────────────────────────────────────

function Badge({ label, color, bg }: { label: string; color: string; bg: string }) {
  return (
    <span style={{
      display: 'inline-block', padding: '1px 7px', borderRadius: 10,
      fontSize: 10, fontWeight: 700, letterSpacing: '0.06em',
      color, background: bg, textTransform: 'uppercase',
    }}>
      {label}
    </span>
  )
}

function Spinner() {
  return (
    <span style={{
      display: 'inline-block', width: 14, height: 14, border: `2px solid ${ACCENT}`,
      borderTopColor: 'transparent', borderRadius: '50%',
      animation: 'spin 0.7s linear infinite',
    }} />
  )
}

// ── render helpers ─────────────────────────────────────────────────────────────

function renderKeyValue(data: Record<string, unknown>, depth = 0): React.ReactNode {
  if (data === null || data === undefined) return <span style={{ color: '#999' }}>—</span>
  if (typeof data !== 'object') {
    const s = String(data)
    const isNum = /^-?\d+\.?\d*$/.test(s)
    return (
      <span style={{ fontVariantNumeric: 'tabular-nums', color: isNum ? '#1565C0' : '#1A2332' }}>
        {s}
      </span>
    )
  }
  if (Array.isArray(data)) {
    return (
      <div style={{ paddingLeft: depth > 0 ? 12 : 0 }}>
        {(data as unknown[]).map((item, i) => (
          <div key={i} style={{ marginBottom: 2 }}>
            {typeof item === 'object' && item !== null
              ? renderKeyValue(item as Record<string, unknown>, depth + 1)
              : <span style={{ color: '#1A2332' }}>{String(item)}</span>}
          </div>
        ))}
      </div>
    )
  }
  return (
    <table style={{ borderCollapse: 'collapse', width: '100%', fontSize: 12 }}>
      <tbody>
        {Object.entries(data).map(([k, v]) => {
          if (k === 'status' || k === 'semantic_version' || k === 'authority') return null
          if (typeof v === 'object' && v !== null && !Array.isArray(v)) {
            return (
              <tr key={k}>
                <td style={{ fontWeight: 600, color: NEUTRAL, verticalAlign: 'top',
                              padding: '3px 10px 3px 0', whiteSpace: 'nowrap', width: '30%' }}>
                  {k}
                </td>
                <td style={{ padding: '3px 0', color: '#1A2332' }}>
                  {renderKeyValue(v as Record<string, unknown>, depth + 1)}
                </td>
              </tr>
            )
          }
          return (
            <tr key={k}>
              <td style={{ fontWeight: 600, color: NEUTRAL, verticalAlign: 'top',
                            padding: '3px 10px 3px 0', whiteSpace: 'nowrap', width: '30%' }}>
                {k}
              </td>
              <td style={{ padding: '3px 0' }}>{renderKeyValue({ _: v }['_'] as any)}</td>
            </tr>
          )
        })}
      </tbody>
    </table>
  )
}

function renderTable(rows: Record<string, unknown>[], t: (k: string, f?: string) => string) {
  if (!rows || rows.length === 0) return <span style={{ color: '#999', fontSize: 12 }}>{t('figures.noRows')}</span>
  const keys = Object.keys(rows[0])
  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ borderCollapse: 'collapse', fontSize: 12, width: '100%' }}>
        <thead>
          <tr>
            {keys.map(k => (
              <th key={k} style={{
                padding: '4px 10px', background: '#F1F5F9',
                color: NEUTRAL, fontWeight: 700, textAlign: 'left',
                borderBottom: '1px solid #CBD5E0', whiteSpace: 'nowrap',
              }}>{k}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} style={{ background: i % 2 === 0 ? '#fff' : '#F8FAFC' }}>
              {keys.map(k => {
                const v = row[k]
                const s = v === null || v === undefined ? '—' : String(v)
                const isNum = /^-?\d+\.?\d*$/.test(s) && s !== '—'
                const isPos = isNum && parseFloat(s) > 0
                const isNeg = isNum && parseFloat(s) < 0
                return (
                  <td key={k} style={{
                    padding: '4px 10px', borderBottom: '1px solid #EDF2F7',
                    color: isPos ? GREEN : isNeg ? WITHDRAWN : '#1A2332',
                    fontVariantNumeric: 'tabular-nums',
                  }}>{s}</td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function renderBars(contributions: { dimension: string; mean: number | null }[]) {
  const max = Math.max(...contributions.map(c => c.mean ?? 0))
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      {contributions.map(c => (
        <div key={c.dimension} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ width: 220, fontSize: 11, color: NEUTRAL, flexShrink: 0, textAlign: 'right' }}>
            {c.dimension}
          </span>
          <div style={{ flex: 1, background: '#E2E8F0', borderRadius: 3, height: 14, position: 'relative' }}>
            <div style={{
              width: `${max > 0 ? ((c.mean ?? 0) / max) * 100 : 0}%`,
              background: c.mean === 0 ? '#CBD5E0' : ACCENT,
              borderRadius: 3, height: '100%',
            }} />
          </div>
          <span style={{ width: 56, fontSize: 11, color: '#1A2332', fontVariantNumeric: 'tabular-nums' }}>
            {c.mean !== null && c.mean !== undefined ? c.mean.toFixed(4) : '—'}
          </span>
        </div>
      ))}
    </div>
  )
}

function renderData(fig: FigEntry, data: Record<string, unknown>, t: (k: string, f?: string) => string) {
  const render = fig.render
  if (render === 'bars') {
    const contribs = (data.contributions as any[]) || []
    if (contribs.length > 0) return renderBars(contribs)
    // ensemble weights as bars
    const sealed = data.sealed_run as Record<string, unknown> | undefined
    if (sealed) {
      const bars = [
        { dimension: 'Bayesian', mean: sealed.weight_bayesian_mean as number },
        { dimension: 'Kalman',   mean: sealed.weight_kalman_mean as number },
        { dimension: 'Bounded-stability (cut)', mean: sealed.weight_lyapunov_mean as number },
      ]
      return (
        <div>
          {renderBars(bars)}
          <div style={{ marginTop: 8, fontSize: 11, color: NEUTRAL }}>
            {t('figures.deployed2learnerLyapunov')} {(data.deployed_2learner as any)?.lyapunov ?? 0}
          </div>
        </div>
      )
    }
  }
  if (render === 'table') {
    // Try common row keys
    const rows = (data.rows as any[]) || (data.arms as any[]) || (data.combined as any[])
    if (rows && rows.length > 0) {
      return (
        <div>
          {renderTable(rows, t)}
          {!!data.headline && (
            <div style={{ marginTop: 8, fontSize: 11, color: GREEN, fontWeight: 600 }}>
              ✓ {data.headline as string}
            </div>
          )}
          {!!data.caveat && (
            <div style={{ marginTop: 4, fontSize: 11, color: NEUTRAL }}>
              ⚠ {data.caveat as string}
            </div>
          )}
          {!!data.note && (
            <div style={{ marginTop: 4, fontSize: 11, color: NEUTRAL }}>
              {data.note as string}
            </div>
          )}
        </div>
      )
    }
    // datasets structure
    if (data.datasets) {
      const datasets = data.datasets as any[]
      return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {datasets.map((ds: any) => (
            <div key={ds.dataset}>
              <div style={{ fontWeight: 700, fontSize: 12, color: '#1A2332', marginBottom: 4 }}>
                {ds.label}
                <span style={{ marginLeft: 8, fontSize: 11, color: NEUTRAL }}>
                  {ds.pooled_verdict}
                </span>
              </div>
              {renderTable(ds.windows || [], t)}
            </div>
          ))}
          {!!data.headline && (
            <div style={{ fontSize: 11, color: GREEN, fontWeight: 600 }}>✓ {data.headline as string}</div>
          )}
        </div>
      )
    }
  }
  // key-value / summary / fallback
  const omit = new Set(['status', 'semantic_version'])
  const filtered = Object.fromEntries(Object.entries(data).filter(([k]) => !omit.has(k)))
  return renderKeyValue(filtered as Record<string, unknown>)
}

// ── CP algorithm notes (static, one per figure) ───────────────────────────────

const ALGO_NOTES: Record<string, string> = {
  'fig02-jt-decomposition': `// Joint Trajectory Score — complexity varies per dimension
// Input: (learner i, concept k, response r ∈ {0,1})
JT(i,k) = Σ_d  weight_d * signal_d(i,k)

// 6 dimensions in V1 (sealed N=96,727):
signal_1 = ΔM(i,k)          // O(1) — Kalman scalar update: P_t, K_t, mean_t in state
signal_2 = T_realized(i,k)  // O(indegree(k)) — Σ_{p ∈ prereqs(k)} mastery(i,p)
                             //   adjacency list walk; O(1) per prereq lookup in dict
signal_3 = Challenge(k)      // O(1) — concept-level constant, no per-event compute
signal_4 = Uncertainty(i,k)  // O(1) — KF variance P_t already in state
signal_5 = ZPD(i,k)          // O(1) — scalar distance: |ability(i) - difficulty(k)|
signal_6 = T_prospective(k)  // O(1) — hardcoded 0.0 in V1 (5 formulations failed)

// Overall per-event: O(indegree(k))
//   Junyi concept graph: mean indegree ≈ 2–4, max ≈ 12 → effectively constant
//   NOT O(1) in theory; O(1) in practice for sparse educational KGs
// Normaliser: α_floor = max(0.01, std(JT_t) / mean(JT_t))
// Bounded: JT_norm = sigmoid(JT / α_floor)`,

  'fig03-ensemble-weights': `// Online Ensemble — Exponentiated Gradient (EG) update
// 3 learners V1: Bayesian β-posterior, Kalman KF, BoundedStability (≈Bayesian, r=0.92)
// 2 learners V2 plan: drop BoundedStability (redundant — cuts synergy)

// Per learner l ∈ {Bayes, Kalman, Lyap}:
//   p_l(t) = learner_l.predict(state_t)
//   loss_l(t) = (p_l(t) - outcome_t)^2
//   w_l(t+1) = w_l(t) * exp(-η * loss_l(t))  then renormalise

// Ensemble output: p̂(t) = Σ_l w_l(t) * p_l(t)
// Sealed CV on weights: 0.03–0.06  → near-uniform (weights barely move)
// Best single predictor: Kalman (r=0.3322 vs ensemble r=0.3113)`,

  'table1-sealed-matched': `// Sealed Matched-Dataset AUC benchmark
// Dataset: Junyi Phase-2, N=96,727, run_id=run-94a3b8ba (sealed)
// Metric: AUC = P(score_correct > score_incorrect)  [ROC integral]

// For each model M ∈ {HCIE, BKT, DKT, SAKT, GKT}:
//   predictions = M.predict(X_test)           // X = interaction history
//   AUC_M = roc_auc_score(y_test, predictions)

// BKT: 2-state HMM  P(K_t | K_{t-1}) via EM (learn/forget/guess/slip)
// DKT: LSTM over embedding(concept), trained offline
// SAKT: self-attention KT (transformer encoder, 1-layer)
// GKT: GNN over concept graph + interaction history
// HCIE: online KF+Bayesian ensemble, no offline training`,

  'table2-deployed-beats-bkt': `// Cold-Start Window Sweep — O(N log N) sort + sliding window
// Dataset: ASSISTments-2009 (4,729 events), run_id=run-e49d92e6

// For window W ∈ {5, 10, 20, all}:
//   S_W = {(learner i, concept k) : n_attempts(i,k) ≤ W}
//   AUC_BKT[W]  = roc_auc_score(y[S_W], BKT.predict(S_W))
//   AUC_HCIE[W] = roc_auc_score(y[S_W], HCIE.predict(S_W))
//   delta[W]    = AUC_HCIE[W] - AUC_BKT[W]

// Hypothesis: HCIE > BKT for small W (Uncertainty + ZPD drive exploration
//   before BKT EM converges on sparse data)`,

  'table3-all-baselines': `// All-Baselines Decomposition — HCIE vs deep-sequence models
// Two datasets:
//   Junyi Phase-2:   N=96,727 sealed (run-94a3b8ba)
//   ASSISTments-09:  N=4,729  sealed (run-e49d92e6)

// Models ranked by AUC descending per dataset
// Deep models (DKT/SAKT/GKT) trained offline, evaluated on held-out split
// HCIE fully online — no offline training phase
// Simpson's paradox check: per-concept AUC vs pooled AUC (see §4.14)`,

  'fig04-causal-probe': `// Prospective Causal Probe — within-learner difference-in-differences
// Question: does traversing prerequisite edge (A → B) causally improve P(correct on B)?

// Treatment: learner touched concept A before attempting B
//   b_durable = E[correct_B | crossed_edge_AB]  (cross-past estimate)
// Placebo:  learner will touch concept A *after* attempting B (time reversal)
//   b_placebo = E[correct_B | will_cross_edge_AB_future]

// Causal effect = b_durable - b_placebo
//   removes selection bias: both groups same learner trajectory,
//   placebo cancels learner-ability confound

// Permutation null (K=100): shuffle DAG labels, recompute effect
//   p_value = #{null_k >= observed_effect} / K
// Result: b_durable=0.099, b_placebo=0.041, p=0.0099`,

  'fig10-scale-sweep': `// Scale Sweep — AUC vs cohort size N
// For N ∈ {100, 500, 1000, 2000, 5000, max_users}:
//   sample N learners uniformly from sealed run
//   compute AUC(HCIE, sample_N)

// Expected: AUC improves with N (Bayesian priors sharpen, KF converges faster)
// Implementation: single pass over experiment_trajectories sorted by user_id
// Complexity: O(N log N) per sweep point (sort + AUC)`,

  'stat-live-cohort': `// Live system counters — no ML, pure DB aggregation
// experiment_trajectories WHERE run_id LIKE 'live::%'
//   n_rows  = total trajectory steps recorded
//   n_users = COUNT DISTINCT user_id

// interactions WHERE policy_mode = 'hcie'
//   total, text_only, non_text (modality split)

// learner_projections
//   n_total, n_synthetic (WHERE synthetic=true OR traffic_type='synthetic')

// live:: run_id pattern: 'live::run-<uuid>::ex_<dataset>_<user_id>'`,

  'fig-modality-mab': `// Thompson Sampling bandit — O(K) sample per request, K=4 arms
// Arms: {text, mcq, video, audio}
// State per (learner, concept, arm): Beta(α, β) posterior

// On each recommendation request:
//   for arm a ∈ {text, mcq, video, audio}:
//     θ_a ~ Beta(α_a, β_a)          // sample from posterior
//   serve arm* = argmax_a θ_a

// On feedback (attempt result r ∈ {0,1}):
//   α_{arm*} += r                   // success count
//   β_{arm*} += (1 - r)             // failure count

// Convergence: TS achieves O(√(K·T·log T)) Bayes regret
// Guard: real learners only (no synthetic traffic in bandit loop)`,

  'fig-archetype-modality': `// Learner Archetype — VARK clustering + behavioural features
// Input: onboarding quiz responses → vark_scores {V, A, R, K} ∈ [0,1]^4
//   + behav_scores {session_length, revisit_rate, streak}
//   + motiv_scores {goal_type, self_report_difficulty}

// Archetype assignment: argmax component in vark_scores (with tie-breaking)
// Stored in: user_archetype_profile.vark_scores (JSON blob)

// Independence design: archetype is a COVARIATE for the MAB,
//   NOT a bandit arm selector — prevents confounding modality reward signal
// Cross-tab: archetype × modality win-rate (this figure)`,

  'table-cascade': `// Grounding Cascade — topological test suite, 46 steps
// DAG: tier1 → tier2 → tier2_5 → tier4 → tier5
// Each node: runs a Python script, emits {status, findings[], open_decisions[]}

// Status codes:
//   PASS   — evidence gate met, decision locked
//   DEFER  — gate unmeasured, decision logged in jt_design_decisions.json
//   WARN   — gate met with disclosure (reported in manuscript Methods)
//   FAIL   — gate not met, blocks downstream (0 currently)

// Decision-aware reframing: WARN→PASS when finding is already
//   disclosed in manuscript AND decision_ref cites the design decision
// Result: 42 PASS + 4 DEFER + 0 FAIL (sealed 2026-06-04)`,
}

function AlgoNote({ figId, t }: { figId: string; t: (k: string, f?: string) => string }) {
  const note = ALGO_NOTES[figId]
  if (!note) return null
  return (
    <details style={{ marginTop: 8 }}>
      <summary style={{
        fontSize: 11, fontWeight: 700, color: '#64748B', cursor: 'pointer',
        userSelect: 'none', letterSpacing: '0.04em',
        listStyle: 'none', display: 'flex', alignItems: 'center', gap: 5,
      }}>
        <span style={{ fontSize: 10 }}>▶</span> {t('figures.algorithmCpView')}
      </summary>
      <pre style={{
        marginTop: 8, padding: '10px 14px',
        background: '#0F172A', color: '#94A3B8',
        borderRadius: 6, fontSize: 11, lineHeight: 1.6,
        overflowX: 'auto', fontFamily: '"Fira Code", "Cascadia Code", Consolas, monospace',
        whiteSpace: 'pre',
      }}>
        {note.split('\n').map((line, i) => {
          const isComment = line.trim().startsWith('//')
          const isKeyword = /^(signal_\d|JT|weight_|alpha_|beta_|b_|p_|AUC|delta|n_)/.test(line.trim())
          return (
            <span key={i} style={{
              color: isComment ? '#4ADE80' : isKeyword ? '#93C5FD' : '#E2E8F0',
              display: 'block',
            }}>
              {line}
            </span>
          )
        })}
      </pre>
    </details>
  )
}

// ── types ──────────────────────────────────────────────────────────────────────

interface FigEntry {
  id: string
  label: string
  section: string
  title: string
  description: string
  endpoint: string
  source: string
  render: string
  external_page?: string
}

interface CardState {
  loading: boolean
  data: Record<string, unknown> | null
  error: string | null
}

// ── main component ─────────────────────────────────────────────────────────────

export default function FigureAtlas() {
  const t = useT()
  const [figures, setFigures] = useState<FigEntry[]>([])
  const [anchor, setAnchor] = useState('')
  const [cards, setCards] = useState<Record<string, CardState>>({})
  const [manifestLoading, setManifestLoading] = useState(true)
  const [manifestError, setManifestError] = useState('')

  useEffect(() => {
    ;(async () => {
      try {
        const r = await fetch(`${BACKEND}/v3/frontend/figures/manifest`, { headers: authHeaders() })
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        const j = await r.json()
        setFigures(j.figures || [])
        setAnchor(j.anchor || '')
      } catch (e: unknown) {
        setManifestError(e instanceof Error ? e.message : String(e))
      } finally {
        setManifestLoading(false)
      }
    })()
  }, [])

  const fetchFigure = useCallback(async (fig: FigEntry) => {
    setCards(prev => ({ ...prev, [fig.id]: { loading: true, data: null, error: null } }))
    try {
      const url = `${BACKEND}${fig.endpoint.startsWith('/v3') ? '' : ''}${fig.endpoint}`
      const r = await fetch(url, { headers: authHeaders() })
      if (!r.ok) throw new Error(`HTTP ${r.status} — ${await r.text().then(t => t.slice(0, 120))}`)
      const j = await r.json()
      setCards(prev => ({ ...prev, [fig.id]: { loading: false, data: j, error: null } }))
    } catch (e: unknown) {
      setCards(prev => ({
        ...prev,
        [fig.id]: { loading: false, data: null, error: e instanceof Error ? e.message : String(e) },
      }))
    }
  }, [])

  const isWithdrawn = (fig: FigEntry) => fig.title.includes('WITHDRAWN')
  const isExternal = (fig: FigEntry) => fig.render === 'external'

  return (
    <div style={{ padding: '32px 40px', maxWidth: 1000, fontFamily: 'Inter, system-ui, sans-serif' }}>
      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.1em',
                      color: NEUTRAL, textTransform: 'uppercase', marginBottom: 6 }}>
          {t('figures.eyebrow')}
        </div>
        <h1 style={{ fontSize: 22, fontWeight: 800, color: '#1A2332', marginBottom: 8 }}>
          {t('figures.heroTitle')}
        </h1>
        <p style={{ fontSize: 13, color: NEUTRAL, lineHeight: 1.6, maxWidth: 680, marginBottom: 12 }}>
          {t('figures.intro')}
        </p>
        {anchor && (
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 6,
            background: ACCENT_LIGHT, borderRadius: 8, padding: '4px 12px',
            fontSize: 11, color: ACCENT, fontWeight: 600,
          }}>
            ◈ {anchor}
          </div>
        )}
      </div>

      {/* Manifest loading state */}
      {manifestLoading && (
        <div style={{ color: NEUTRAL, fontSize: 13, display: 'flex', alignItems: 'center', gap: 8 }}>
          <Spinner /> {t('figures.loadingRegistry')}
        </div>
      )}
      {manifestError && (
        <div style={{ color: WITHDRAWN, fontSize: 12, background: WITHDRAWN_LIGHT,
                      padding: '8px 12px', borderRadius: 6, marginBottom: 16 }}>
          ✗ {t('figures.registryError')} {manifestError}
        </div>
      )}

      {/* Figure cards */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        {figures.map(fig => {
          const card = cards[fig.id]
          const withdrawn = isWithdrawn(fig)
          const external = isExternal(fig)
          const borderColor = withdrawn ? WITHDRAWN : external ? '#D4A500' : ACCENT
          const headerBg = withdrawn ? WITHDRAWN_LIGHT : external ? '#FFFBEB' : ACCENT_LIGHT

          return (
            <div key={fig.id} style={{
              border: `1px solid ${borderColor}`,
              borderRadius: 10, overflow: 'hidden',
              boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
            }}>
              {/* Card header */}
              <div style={{
                background: headerBg, padding: '12px 16px',
                display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12,
              }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', marginBottom: 4 }}>
                    <span style={{ fontWeight: 800, fontSize: 12, color: borderColor }}>
                      {fig.label}
                    </span>
                    <Badge label={fig.section} color={NEUTRAL} bg="#E2E8F0" />
                    {withdrawn && <Badge label={t('figures.badgeWithdrawn')} color={WITHDRAWN} bg={WITHDRAWN_LIGHT} />}
                    {external && <Badge label={t('figures.badgeSeeDashboard')} color="#D4A500" bg="#FFFBEB" />}
                  </div>
                  <div style={{ fontWeight: 700, fontSize: 14, color: '#1A2332', marginBottom: 4 }}>
                    {fig.title}
                  </div>
                  <div style={{ fontSize: 12, color: NEUTRAL, lineHeight: 1.5 }}>
                    {fig.description}
                  </div>
                  <AlgoNote figId={fig.id} t={t} />
                  <div style={{ marginTop: 6, fontSize: 10, color: '#94A3B8' }}>
                    {t('figures.sourceLabel')} {fig.source}
                  </div>
                </div>

                {/* Action button */}
                <div style={{ flexShrink: 0, display: 'flex', flexDirection: 'column', gap: 6, alignItems: 'flex-end' }}>
                  {external ? (
                    <a
                      href={fig.external_page}
                      style={{
                        padding: '6px 14px', borderRadius: 6, fontSize: 12, fontWeight: 700,
                        background: '#D4A500', color: '#fff', textDecoration: 'none',
                        display: 'inline-block',
                      }}
                    >
                      {t('figures.openPage')}
                    </a>
                  ) : (
                    <button
                      onClick={() => fetchFigure(fig)}
                      disabled={card?.loading}
                      style={{
                        padding: '6px 14px', borderRadius: 6, fontSize: 12, fontWeight: 700,
                        background: card?.loading ? '#CBD5E0' : withdrawn ? WITHDRAWN : ACCENT,
                        color: '#fff', border: 'none', cursor: card?.loading ? 'default' : 'pointer',
                        display: 'flex', alignItems: 'center', gap: 6,
                        transition: 'background 0.15s',
                      }}
                    >
                      {card?.loading ? <><Spinner /> {t('figures.fetching')}</> : `⟳ ${t('figures.getData')}`}
                    </button>
                  )}
                  {card?.data && (
                    <button
                      onClick={() => setCards(prev => ({ ...prev, [fig.id]: { ...prev[fig.id], data: null } }))}
                      style={{ fontSize: 10, color: '#94A3B8', background: 'none', border: 'none',
                                cursor: 'pointer', textDecoration: 'underline' }}
                    >
                      {t('figures.collapse')}
                    </button>
                  )}
                </div>
              </div>

              {/* Data panel */}
              {card?.error && (
                <div style={{ padding: '10px 16px', background: WITHDRAWN_LIGHT,
                              fontSize: 12, color: WITHDRAWN }}>
                  ✗ {card.error}
                </div>
              )}
              {card?.data && (
                <div style={{ padding: '14px 16px', background: '#fff', borderTop: `1px solid ${borderColor}` }}>
                  {renderData(fig, card.data, t)}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Footer */}
      {figures.length > 0 && (
        <div style={{ marginTop: 28, padding: '12px 16px', background: '#F1F5F9',
                      borderRadius: 8, fontSize: 11, color: NEUTRAL }}>
          <div style={{ fontWeight: 700, marginBottom: 4 }}>{t('figures.endpointPattern')}</div>
          <code style={{ fontSize: 10, color: '#1A2332' }}>
            GET {BACKEND}/v3/frontend/figures/&#123;id&#125;
          </code>
          <div style={{ marginTop: 4 }}>
            {t('figures.sealedJsons')} <code>/app/research_validation/reports/grounding/tier5_*.json</code>
            {' · '}{t('figures.liveDb')} <code>experiment_trajectories, interactions, user_archetype_profile</code>
          </div>
        </div>
      )}

      {/* CSS for the spinner */}
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>

      <NextSteps />
    </div>
  )
}
