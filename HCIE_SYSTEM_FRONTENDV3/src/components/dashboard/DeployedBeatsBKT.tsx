'use client'

/**
 * HCIE (DEPLOYED runtime) vs BKT — per window, by traffic class.
 *
 * This is the "frontend as evidence" close-out: the deployed runtime
 * (individualized-prior cold-start + 2-learner Kalman+Bayesian, Lyapunov cut)
 * now beats BKT. Sourced from the sealed validation report
 *   research_validation/reports/MAKE_IT_REAL_2026-06-05.md
 * via the frozen static artifact /data/adc/deployed_beats_bkt.json — cited,
 * NOT re-derived in the browser.
 *
 * Honesty is load-bearing here: the synthetic cold-start ≤5 margin (+0.45) is
 * INFLATED (BKT degenerate at the first per-skill attempt) and the live class
 * has NO per-window AUC (no BKT comparator). Both are surfaced with explicit
 * labels so a viewer cannot mistake them for a clean win.
 */

import { useEffect, useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, Legend,
} from 'recharts'

type WindowRow = {
  window: string
  label: string
  n: number
  bkt: number | null
  hcie: number | null
  delta: number | null
  winner: string
  inflated?: boolean
  win_note?: string
  /** v2: all model AUCs on matched intersection (HCIE, BKT, DKT, …) */
  models?: Record<string, number | null>
  standings?: Record<string, string>
  bkt_standing?: string | null
  bkt_delta?: number | null
  simpson_artifact?: boolean | null
}
type MechRow = { signal: string; value: string; ok: boolean }
type ClassRow = {
  key: string
  label: string
  status: string
  status_label: string
  tone: 'credible' | 'mixed' | 'caveat' | 'mechanism'
  run_id: string
  n_users: number | null
  n_events: number
  base_rate: number | null
  avg_attempts_per_skill: number | null
  caveat: string
  note: string
  windows: WindowRow[]
  mechanism?: MechRow[]
  /** v2: which baselines were scored on this cohort */
  models_present?: string[]
  v2_note?: string
}
// ── multi-baseline block (BKT + DKT + SAKT + IRT-1PL, per dataset, per window) ──
type MBWindow = {
  window: string
  label: string
  n: number
  models: Record<string, number | null>        // { HCIE, BKT, DKT, SAKT, IRT-1PL }
  standings: Record<string, string>             // model → BEATS|competitive|below
  bkt_delta: number | null
  bkt_standing: string | null
  simpson_artifact: boolean | null
  decomp: {
    n_warm: number; n_cold: number
    hcie_warm: number | null; bkt_warm: number | null
    hcie_cold: number | null; bkt_cold: number | null
  }
}
type MBDataset = {
  key: string
  label: string
  run_id: string
  base_rate: number
  balanced: boolean
  n_matched: number
  n_coldstart: number
  models_present: string[]
  windows: MBWindow[]
}
type MultiBaseline = {
  title: string
  predictor_note: string
  bar_note: string
  simpson_note: string
  gkt_note: string
  datasets: MBDataset[]
}
type Payload = {
  title: string
  generated_at: string
  source_report: string
  deployed_config: string
  predictor_note: string
  headline_class: string
  headline_text: string
  classes: ClassRow[]
  footnote: string
  multi_baseline?: MultiBaseline
  v2_note?: string
  v1_artifact?: string
  artifact_version?: 'v1' | 'v2'
}

// tone → border / accent colors for the per-class status banner.
const TONE: Record<string, { bg: string; border: string; fg: string; chip: string }> = {
  credible:  { bg: '#D5F5E3', border: '#1E8449', fg: '#196F3D', chip: '#1E8449' },
  mixed:     { bg: '#FEF9E7', border: '#D4AC0D', fg: '#7D6608', chip: '#B7950B' },
  caveat:    { bg: '#FDEDEC', border: '#E74C3C', fg: '#922B21', chip: '#C0392B' },
  mechanism: { bg: '#EBF5FB', border: '#3498DB', fg: '#1A5276', chip: '#2980B9' },
}

const BKT_COLOR = '#2980B9'
const HCIE_COLOR = '#6C3483'

// per-model colors for the multi-baseline grouped bars
const MB_COLORS: Record<string, string> = {
  HCIE: '#1E8449', BKT: '#2980B9', DKT: '#8E44AD', SAKT: '#D35400', 'IRT-1PL': '#7F8C8D',
}
// standing → small badge style
const STANDING_BADGE: Record<string, { bg: string; fg: string; txt: string }> = {
  BEATS:       { bg: '#D5F5E3', fg: '#196F3D', txt: 'beats' },
  competitive: { bg: '#FEF9E7', fg: '#7D6608', txt: '~comp' },
  below:       { bg: '#FDEDEC', fg: '#922B21', txt: 'below' },
  'n/a':       { bg: '#F1F5F9', fg: '#94A3B8', txt: 'n/a' },
}

/**
 * Multi-baseline panel: deployed HCIE vs ALL recorded baselines (BKT, DKT, SAKT,
 * IRT-1PL) per dataset, per window — the honest extension of the BKT-only story.
 * The user's rule is baked into the labels: beating BKT is the mandatory FLOOR
 * (held on all 4 datasets); competing with / beating the deep models (DKT) is the
 * bar (met on CSEDM + EdNet). Pooled BKT losses on high-base-rate corpora are
 * shown with the Simpson's-paradox decomposition so they cannot be misread as a
 * true loss. GKT is recorded only on tiny matched-eval runs → not shown per-window.
 */
function MultiBaselinePanel({ mb }: { mb: MultiBaseline }) {
  return (
    <div data-testid="multi-baseline" style={{ marginTop: 22 }}>
      <div style={{ background: 'linear-gradient(135deg,#EBF5FB,#F4ECF7)', border: '2px solid #6C3483',
                    borderRadius: 12, padding: '16px 20px', marginBottom: 14 }}>
        <div style={{ fontSize: 11, fontWeight: 800, color: '#5B2C6F', letterSpacing: '0.06em',
                      textTransform: 'uppercase', marginBottom: 6 }}>
          ★ Deployed HCIE vs ALL baselines — BKT · DKT · SAKT · IRT-1PL, per dataset, per window
        </div>
        <div style={{ fontSize: 12.5, color: '#1A2332', lineHeight: 1.6, fontWeight: 600 }}>
          {mb.bar_note}
        </div>
        <div style={{ fontSize: 10.5, color: '#4A5568', marginTop: 8, lineHeight: 1.55 }}>
          {mb.predictor_note}
        </div>
      </div>

      {mb.datasets.map(ds => {
        const order = ds.models_present // HCIE first, then baselines
        const chartRows = ds.windows.map(w => {
          const row: Record<string, number | string | null> = { label: w.label }
          for (const m of order) row[m] = w.models[m]
          return row
        })
        const anySimpson = ds.windows.some(w => w.simpson_artifact)
        return (
          <div key={ds.key} data-testid={`mb-dataset-${ds.key}`}
               style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 12,
                        padding: '16px 18px', marginBottom: 14 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
                          flexWrap: 'wrap', gap: 8, marginBottom: 8 }}>
              <div style={{ fontSize: 14, fontWeight: 800, color: '#1A2332' }}>
                {ds.label}
                <span style={{ marginLeft: 8, fontSize: 10, fontWeight: 700,
                               background: ds.balanced ? '#D5F5E3' : '#FEF9E7',
                               color: ds.balanced ? '#196F3D' : '#7D6608',
                               borderRadius: 4, padding: '2px 7px' }}>
                  base rate {ds.base_rate.toFixed(2)} · {ds.balanced ? 'balanced' : 'high'}
                </span>
              </div>
              <div style={{ fontSize: 10.5, color: '#718096', fontFamily: 'monospace' }}>
                {ds.n_matched.toLocaleString()} matched · {ds.n_coldstart.toLocaleString()} cold-start
              </div>
            </div>

            {/* grouped bars: HCIE vs each baseline per window */}
            <ResponsiveContainer width="100%" height={230}>
              <BarChart data={chartRows} barCategoryGap="22%" margin={{ left: 0, right: 16, top: 4, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#EDF2F7" />
                <XAxis dataKey="label" tick={{ fontSize: 10, fill: '#4A5568' }} axisLine={false} tickLine={false} />
                <YAxis domain={[0.4, 0.8]} tickFormatter={v => v.toFixed(1)}
                       tick={{ fontSize: 10, fill: '#A0AEC0' }} axisLine={false} tickLine={false} />
                <Tooltip formatter={(v: any, n: any) => [v == null ? 'n/a' : Number(v).toFixed(4), n]}
                         contentStyle={{ fontSize: 11, borderRadius: 6 }} />
                <Legend wrapperStyle={{ fontSize: 10.5 }} />
                {order.map(m => (
                  <Bar key={m} dataKey={m} fill={MB_COLORS[m] ?? '#94A3B8'}
                       radius={[2, 2, 0, 0]} opacity={m === 'HCIE' ? 1 : 0.8} />
                ))}
              </BarChart>
            </ResponsiveContainer>

            {/* standing table: HCIE vs each baseline + Simpson note */}
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 10.5, marginTop: 10 }}>
              <thead>
                <tr style={{ background: '#F7FAFC', borderBottom: '2px solid #E2E8F0' }}>
                  {['Window', 'n', ...order, 'HCIE vs BKT'].map(h => (
                    <th key={h} style={{ padding: '5px 8px', textAlign: h === 'Window' ? 'left' : 'right',
                                         fontWeight: 700, color: '#2D3748', fontSize: 10 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {ds.windows.map(w => (
                  <tr key={w.window} style={{ borderBottom: '1px solid #EDF2F7' }}>
                    <td style={{ padding: '5px 8px', fontWeight: 600, color: '#2D3748' }}>{w.label}</td>
                    <td style={{ padding: '5px 8px', textAlign: 'right', color: '#718096',
                                 fontVariantNumeric: 'tabular-nums' }}>{w.n.toLocaleString()}</td>
                    {order.map(m => {
                      const v = w.models[m]
                      const lead = order.every(o => (w.models[o] ?? -1) <= (v ?? -1))
                      return (
                        <td key={m} style={{ padding: '5px 8px', textAlign: 'right',
                                             fontVariantNumeric: 'tabular-nums',
                                             fontWeight: m === 'HCIE' ? 800 : (lead ? 700 : 400),
                                             color: m === 'HCIE' ? '#1E8449' : (lead ? '#1A2332' : '#4A5568') }}>
                          {v == null ? 'n/a' : v.toFixed(4)}
                        </td>
                      )
                    })}
                    <td style={{ padding: '5px 8px', textAlign: 'right' }}>
                      {(() => {
                        const st = w.bkt_standing ?? 'n/a'
                        const badge = STANDING_BADGE[st] ?? STANDING_BADGE['n/a']
                        const simp = w.simpson_artifact
                        return (
                          <span style={{ display: 'inline-flex', gap: 4, alignItems: 'center' }}>
                            <span style={{ background: simp ? '#FEF9E7' : badge.bg,
                                           color: simp ? '#7D6608' : badge.fg,
                                           borderRadius: 4, padding: '1px 6px', fontWeight: 700,
                                           fontSize: 9.5, whiteSpace: 'nowrap' }}>
                              {w.bkt_delta != null ? `${w.bkt_delta > 0 ? '+' : ''}${w.bkt_delta.toFixed(3)}` : 'n/a'}
                              {simp ? ' Simpson' : ` ${badge.txt}`}
                            </span>
                          </span>
                        )
                      })()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* Simpson decomposition (only when a pooled BKT loss is an artifact) */}
            {anySimpson && (
              <div style={{ fontSize: 10, color: '#7D6608', lineHeight: 1.55, marginTop: 8,
                            background: '#FFFCF2', border: '1px dashed #D4AC0D', borderRadius: 6, padding: '8px 12px' }}>
                <strong>⚠ Pooled-BKT below = Simpson's-paradox artifact, not a true loss.</strong>{' '}
                HCIE wins BOTH sub-populations separately. Overall window:{' '}
                {(() => {
                  const o = ds.windows.find(w => w.window === 'overall')
                  if (!o) return null
                  const d = o.decomp
                  return (
                    <>warm (n={d.n_warm.toLocaleString()}) HCIE {d.hcie_warm?.toFixed(3)} vs BKT {d.bkt_warm?.toFixed(3)};{' '}
                    cold (n={d.n_cold.toLocaleString()}) HCIE {d.hcie_cold?.toFixed(3)} vs BKT {d.bkt_cold?.toFixed(3)}.</>
                  )
                })()}{' '}
                {mb.simpson_note}
              </div>
            )}
            <div style={{ fontSize: 9.5, color: '#A0AEC0', fontFamily: 'monospace', marginTop: 6 }}>
              run {ds.run_id}
            </div>
          </div>
        )
      })}

      <div style={{ fontSize: 10, color: '#A0AEC0', lineHeight: 1.55, padding: '0 4px' }}>
        {mb.gkt_note}
      </div>
    </div>
  )
}

export function DeployedBeatsBKT() {
  const [data, setData] = useState<Payload | null>(null)
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    const load = async () => {
      try {
        const v2 = await fetch('/data/adc/deployed_beats_bkt_v2.json', { signal: AbortSignal.timeout(12000) })
        if (v2.ok) {
          const payload = await v2.json()
          setData({ ...payload, artifact_version: 'v2' })
          return
        }
        const v1 = await fetch('/data/adc/deployed_beats_bkt.json', { signal: AbortSignal.timeout(12000) })
        if (v1.ok) {
          setData({ ...(await v1.json()), artifact_version: 'v1' })
          return
        }
        setFailed(true)
      } catch {
        setFailed(true)
      }
    }
    load()
  }, [])

  if (failed) {
    return (
      <div style={{ background: '#fff', border: '1px dashed #CBD5E0', borderRadius: 10,
                    padding: '24px', textAlign: 'center', color: '#A0AEC0', fontSize: 12 }}>
        Deployed beats-BKT artifact not found (/data/adc/deployed_beats_bkt.json).
      </div>
    )
  }
  if (!data) {
    return <div style={{ padding: 24, color: '#718096', fontSize: 12 }}>⟳ Loading deployed beats-BKT…</div>
  }

  return (
    <div data-testid="deployed-beats-bkt" style={{ marginBottom: 18 }}>
      {/* ── Section header + headline ─────────────────────────────────────────── */}
      <div style={{ background: 'linear-gradient(135deg, #D5F5E3, #F4ECF7)',
                    border: '2px solid #1E8449', borderRadius: 12, padding: '16px 20px', marginBottom: 14 }}>
        <div style={{ fontSize: 11, fontWeight: 800, color: '#196F3D', letterSpacing: '0.06em',
                      textTransform: 'uppercase', marginBottom: 6 }}>
          ★ Deployed runtime vs BKT — the live system now wins
        </div>
        <div style={{ fontSize: 13.5, color: '#1A2332', lineHeight: 1.6, fontWeight: 600 }}>
          {data.headline_text}
        </div>
        <div style={{ fontSize: 11, color: '#4A5568', marginTop: 8, lineHeight: 1.55 }}>
          <strong>Deployed config:</strong> {data.deployed_config}.{' '}
          {data.artifact_version === 'v2' ? (
            <>Showing <strong>v2 cohorts</strong> (deep baselines on ASSISTments + Junyi); paper-cited v1 in <code style={{ fontSize: 10 }}>{data.v1_artifact ?? 'deployed_beats_bkt.json'}</code>.</>
          ) : (
            <>Cited from <code style={{ fontSize: 10 }}>{data.source_report}</code> — not re-derived in the browser.</>
          )}
        </div>
      </div>

      {/* ── Per-class panels ──────────────────────────────────────────────────── */}
      {data.classes.map(cls => {
        const tone = TONE[cls.tone] ?? TONE.mechanism
        const isLive = cls.tone === 'mechanism'
        const hasDeep = Boolean(cls.models_present?.length && cls.windows.some(w => w.models))
        const modelOrder = hasDeep
          ? (cls.models_present ?? ['HCIE', 'BKT'])
          : ['HCIE', 'BKT']
        // chart rows: all models per window when v2 deep baselines present
        const chartRows = cls.windows.map(w => {
          if (hasDeep && w.models) {
            const row: Record<string, number | string | boolean | null | undefined> = {
              label: w.label, inflated: w.inflated, delta: w.delta,
            }
            for (const m of modelOrder) row[m] = w.models[m] ?? null
            return row
          }
          return {
            label: w.label, BKT: w.bkt, HCIE: w.hcie, inflated: w.inflated, delta: w.delta,
          }
        })
        return (
          <div key={cls.key} data-testid={`beats-bkt-class-${cls.key}`}
               style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 12,
                        padding: '16px 18px', marginBottom: 14 }}>
            {/* class title + status banner */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
                          flexWrap: 'wrap', gap: 8, marginBottom: 8 }}>
              <div style={{ fontSize: 14, fontWeight: 800, color: '#1A2332' }}>{cls.label}</div>
              <div style={{ fontSize: 10.5, color: '#718096', fontFamily: 'monospace' }}>
                {cls.n_events.toLocaleString()} events
                {cls.n_users != null ? ` · ${cls.n_users} users` : ''}
                {cls.avg_attempts_per_skill != null ? ` · ${cls.avg_attempts_per_skill} attempts/skill` : ''}
              </div>
            </div>

            {/* THE honest status label — always visible */}
            <div style={{ background: tone.bg, border: `1px solid ${tone.border}`, borderRadius: 8,
                          padding: '8px 12px', marginBottom: 12, display: 'flex', gap: 8, alignItems: 'center',
                          flexWrap: 'wrap' }}>
              <span style={{ background: tone.chip, color: '#fff', borderRadius: 4, padding: '2px 8px',
                             fontSize: 10, fontWeight: 800, whiteSpace: 'nowrap' }}>
                {cls.status.toUpperCase()}
              </span>
              <span style={{ fontSize: 11.5, fontWeight: 700, color: tone.fg }}>{cls.status_label}</span>
            </div>

            {/* caveat (if any) — the explicit "don't misread this" note */}
            {cls.caveat && (
              <div style={{ fontSize: 11, color: tone.fg, lineHeight: 1.55, marginBottom: 12,
                            background: '#FCFCFD', border: `1px dashed ${tone.border}`, borderRadius: 6,
                            padding: '8px 12px' }}>
                <strong>⚠ Read honestly:</strong> {cls.caveat}
              </div>
            )}

            {/* ── live class: mechanism status table (NO fake AUC) ── */}
            {isLive ? (
              <div style={{ border: '1px solid #EDF2F7', borderRadius: 8, overflow: 'hidden' }}>
                {(cls.mechanism ?? []).map((m, i) => (
                  <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                                        gap: 10, padding: '8px 12px',
                                        background: i % 2 === 0 ? '#fff' : '#F9FAFB',
                                        borderTop: i === 0 ? 'none' : '1px solid #F1F5F9' }}>
                    <span style={{ fontSize: 11.5, color: '#2D3748' }}>
                      <span style={{ marginRight: 8, color: m.ok ? '#1E8449' : '#C0392B', fontWeight: 800 }}>
                        {m.ok ? '✓' : '○'}
                      </span>
                      {m.signal}
                    </span>
                    <span style={{ fontSize: 11, fontWeight: 700, fontFamily: 'monospace',
                                   color: m.ok ? '#196F3D' : '#922B21' }}>
                      {m.value}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <>
                {/* ── dataset/synthetic/junyi: per-window bars (BKT+HCIE or all baselines) ── */}
                <ResponsiveContainer width="100%" height={hasDeep ? 250 : 220}>
                  <BarChart data={chartRows} barCategoryGap={hasDeep ? '18%' : '28%'}
                            margin={{ left: 0, right: 16, top: 4, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#EDF2F7" />
                    <XAxis dataKey="label" tick={{ fontSize: 10.5, fill: '#4A5568' }} axisLine={false} tickLine={false} />
                    <YAxis domain={[0, 1]} tickFormatter={v => v.toFixed(1)}
                           tick={{ fontSize: 10, fill: '#A0AEC0' }} axisLine={false} tickLine={false} />
                    <Tooltip formatter={(v: any, n: any) => [v == null ? 'n/a' : Number(v).toFixed(4), n]}
                             contentStyle={{ fontSize: 11, borderRadius: 6 }} />
                    <Legend wrapperStyle={{ fontSize: 11 }} />
                    {hasDeep ? (
                      modelOrder.map(m => (
                        <Bar key={m} dataKey={m} fill={MB_COLORS[m] ?? '#94A3B8'}
                             radius={[2, 2, 0, 0]} opacity={m === 'HCIE' ? 1 : 0.8} />
                      ))
                    ) : (
                      <>
                        <Bar dataKey="BKT" fill={BKT_COLOR} radius={[3, 3, 0, 0]} opacity={0.75} />
                        <Bar dataKey="HCIE" radius={[3, 3, 0, 0]}>
                          {chartRows.map((r, i) => (
                            <Cell key={i} fill={HCIE_COLOR} opacity={r.inflated ? 0.45 : 1}
                                  stroke={r.inflated ? '#C0392B' : 'none'} strokeWidth={r.inflated ? 1.5 : 0}
                                  strokeDasharray={r.inflated ? '3 2' : '0'} />
                          ))}
                        </Bar>
                      </>
                    )}
                  </BarChart>
                </ResponsiveContainer>

                {/* per-window table */}
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11, marginTop: 10 }}>
                  <thead>
                    <tr style={{ background: '#F7FAFC', borderBottom: '2px solid #E2E8F0' }}>
                      {(hasDeep
                        ? ['Window', 'n', ...modelOrder, 'HCIE vs BKT', '']
                        : ['Window', 'n', 'BKT', 'HCIE', 'HCIE − BKT', '']
                      ).map(h => (
                        <th key={h} style={{ padding: '6px 10px', textAlign: h === 'Window' || h === '' ? 'left' : 'right',
                                             fontWeight: 700, color: '#2D3748', fontSize: 10.5 }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {cls.windows.map(w => (
                      <tr key={w.window} style={{ borderBottom: '1px solid #EDF2F7' }}>
                        <td style={{ padding: '6px 10px', fontWeight: 600, color: '#2D3748' }}>{w.label}</td>
                        <td style={{ padding: '6px 10px', textAlign: 'right', color: '#718096',
                                     fontVariantNumeric: 'tabular-nums' }}>{w.n.toLocaleString()}</td>
                        {hasDeep && w.models ? (
                          <>
                            {modelOrder.map(m => {
                              const v = w.models![m]
                              return (
                                <td key={m} style={{ padding: '6px 10px', textAlign: 'right',
                                                     fontVariantNumeric: 'tabular-nums',
                                                     fontWeight: m === 'HCIE' ? 800 : 400,
                                                     color: m === 'HCIE' ? '#1E8449' : '#4A5568' }}>
                                  {v == null ? 'n/a' : v.toFixed(4)}
                                </td>
                              )
                            })}
                            <td style={{ padding: '6px 10px', textAlign: 'right' }}>
                              {w.bkt_delta != null ? (
                                <span style={{
                                  background: w.simpson_artifact ? '#FEF9E7' : (STANDING_BADGE[w.bkt_standing ?? 'n/a']?.bg ?? '#F1F5F9'),
                                  color: w.simpson_artifact ? '#7D6608' : (STANDING_BADGE[w.bkt_standing ?? 'n/a']?.fg ?? '#4A5568'),
                                  borderRadius: 4, padding: '1px 6px', fontWeight: 700, fontSize: 9.5,
                                }}>
                                  {w.bkt_delta > 0 ? '+' : ''}{w.bkt_delta.toFixed(3)}
                                  {w.simpson_artifact ? ' Simpson' : ''}
                                </span>
                              ) : 'n/a'}
                            </td>
                          </>
                        ) : (
                          <>
                            <td style={{ padding: '6px 10px', textAlign: 'right', color: '#2980B9',
                                         fontVariantNumeric: 'tabular-nums' }}>{w.bkt?.toFixed(4) ?? 'n/a'}</td>
                            <td style={{ padding: '6px 10px', textAlign: 'right', fontWeight: 700, color: '#6C3483',
                                         fontVariantNumeric: 'tabular-nums' }}>{w.hcie?.toFixed(4) ?? 'n/a'}</td>
                            <td style={{ padding: '6px 10px', textAlign: 'right', fontWeight: 800,
                                         fontVariantNumeric: 'tabular-nums',
                                         color: (w.delta ?? 0) > 0 ? '#1E8449' : '#C0392B' }}>
                              {w.delta != null ? `${w.delta > 0 ? '+' : ''}${w.delta.toFixed(4)}` : 'n/a'}
                            </td>
                          </>
                        )}
                        <td style={{ padding: '6px 10px', fontSize: 10, color: '#922B21' }}>
                          {w.inflated && (
                            <span style={{ background: '#FDEDEC', border: '1px solid #F5B7B1', borderRadius: 4,
                                           padding: '1px 6px', fontWeight: 700, whiteSpace: 'nowrap' }}>
                              ⚠ inflated{w.win_note ? ` — ${w.win_note}` : ''}
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </>
            )}

            {cls.note && (
              <div style={{ fontSize: 10.5, color: '#718096', lineHeight: 1.55, marginTop: 10 }}>
                {cls.note}
              </div>
            )}
            <div style={{ fontSize: 9.5, color: '#A0AEC0', fontFamily: 'monospace', marginTop: 6 }}>
              run {cls.run_id}
            </div>
          </div>
        )
      })}

      {/* ── Multi-baseline extension: HCIE vs BKT/DKT/SAKT/IRT per dataset per window ── */}
      {data.multi_baseline && <MultiBaselinePanel mb={data.multi_baseline} />}

      <div style={{ fontSize: 10, color: '#A0AEC0', lineHeight: 1.55, padding: '0 4px' }}>
        {data.footnote}
      </div>
    </div>
  )
}

export default DeployedBeatsBKT
