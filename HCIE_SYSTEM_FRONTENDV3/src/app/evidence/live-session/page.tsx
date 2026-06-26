'use client'

/**
 * /evidence/live-session — defense demonstration page.
 *
 * Renders the canonical per-interaction evidence table for a learner:
 *   User · Task · Answer · Correct · Mastery Before · Mastery After · ΔM ·
 *   T_realized · Transfer Fired · Policy · Timestamp
 *
 * Data source:
 *   GET /v3/frontend/dashboard/session-trace/{user_id}
 *
 * That endpoint joins experiment_trajectories + outbox envelopes and returns
 * the full interaction trace including JT 6D decomposition, ensemble
 * before/after, and transfer state. This page renders the table form for
 * easy demonstration:
 *   "Here is interaction #25. Here is the transfer event. Here is the mastery
 *    update. Here is where it appears in instructor analytics."
 */

import { useEffect, useState, useCallback } from 'react'
import { useAuth } from '@/contexts/auth_context'
import Link from 'next/link'
import { useSearchParams } from 'next/navigation'
import { getBackendUrl } from '@/lib/api/backend-url'
import { getAuthHeaders } from '@/lib/auth-headers'
import { useT } from '@/contexts/language_context'

// ─── Types ────────────────────────────────────────────────────────────────────

interface JTComponents {
  delta_m: number | null
  transfer: number | null
  challenge: number | null
  uncertainty: number | null
  zpd: number | null
}

interface InteractionTrace {
  event_id: string | null
  interaction_id: string | null
  interaction_number: number | null
  concept_id: string | null
  timestamp: string | null
  policy: string | null
  arm_selected: string | null
  difficulty: number | null
  correct: boolean | null
  response_time: number | null
  mastery_before: number | null
  mastery_after: number | null
  mastery_delta: number | null
  jt_value: number | null
  jt_components: JTComponents
  ensemble: any
  transfer: {
    amount: number | null
    efficiency: number | null
    fired: boolean
  }
  zpd: {
    target: number | null
    alignment_error: number | null
    score: number | null
  }
}

interface SessionSummary {
  total_interactions: number
  correct_count: number
  incorrect_count: number
  accuracy: number
  cumulative_mastery_gain: number
  transfer_events: number
  cold_start_accuracy: number
  avg_response_time: number
  unique_concepts: number
  first_timestamp: string | null
  latest_timestamp: string | null
}

interface SessionTraceResponse {
  status: 'ok' | 'no_data'
  user_id: string
  trace: InteractionTrace[]
  count: number
  session_summary?: SessionSummary
  authority: string
  fallback_reason?: string
  reason?: string
}

// ─── Constants ─────────────────────────────────────────────────────────────────

const BACKEND = getBackendUrl()
const POLL_MS = 4000
const TRANSFER_THRESHOLD = 0.08

// ─── Helpers ──────────────────────────────────────────────────────────────────

function pct(v: number | null | undefined, dec = 1): string {
  if (v == null) return '—'
  return `${(Number(v) * 100).toFixed(dec)}%`
}

function fmt(v: number | null | undefined, dec = 3): string {
  if (v == null) return '—'
  return Number(v).toFixed(dec)
}

function shortConcept(c: string | null): string {
  if (!c) return '—'
  return c.replace(/^k(\d+)_/, 'K$1·').replace(/_/g, ' ')
}

function shortEvent(id: string | null): string {
  if (!id) return '—'
  return id.length > 18 ? id.slice(0, 14) + '…' : id
}

function timeStr(iso: string | null): string {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString('en-GB', {
      hour12: false,
      year: '2-digit', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit', second: '2-digit',
    })
  } catch { return iso }
}

// ─── Sub-components ────────────────────────────────────────────────────────────

function StatTile({ label, value, color, sub }: {
  label: string
  value: string | number
  color: string
  sub?: string
}) {
  return (
    <div style={{
      background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10,
      padding: '14px 18px', flex: 1, minWidth: 140,
    }}>
      <div style={{ fontSize: 10, color: '#718096', fontWeight: 700,
                     textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 }}>
        {label}
      </div>
      <div style={{ fontSize: 22, fontWeight: 800, color, fontVariantNumeric: 'tabular-nums' }}>
        {value}
      </div>
      {sub && (
        <div style={{ fontSize: 10, color: '#A0AEC0', marginTop: 2 }}>{sub}</div>
      )}
    </div>
  )
}

function MasteryArrow({ before, after, delta }: {
  before: number | null
  after: number | null
  delta: number | null
}) {
  if (before == null && after == null) return <span style={{ color: '#A0AEC0' }}>—</span>
  const positive = (delta ?? 0) >= 0
  return (
    <span style={{ fontVariantNumeric: 'tabular-nums', fontSize: 12 }}>
      <span style={{ color: '#718096' }}>{pct(before, 1)}</span>
      <span style={{ margin: '0 5px', color: positive ? '#27AE60' : '#C0392B' }}>→</span>
      <span style={{ fontWeight: 700, color: positive ? '#27AE60' : '#C0392B' }}>{pct(after, 1)}</span>
      {delta != null && (
        <span style={{ marginLeft: 6, fontSize: 10,
                       color: positive ? '#27AE60' : '#C0392B', fontWeight: 600 }}>
          ({positive ? '+' : ''}{pct(delta, 2)})
        </span>
      )}
    </span>
  )
}

function CorrectChip({ value }: { value: boolean | null }) {
  if (value === true) return (
    <span style={{ fontSize: 10, fontWeight: 700, color: '#1E8449',
                   background: '#D5F5E3', borderRadius: 4, padding: '2px 8px' }}>
      ✓ correct
    </span>
  )
  if (value === false) return (
    <span style={{ fontSize: 10, fontWeight: 700, color: '#C0392B',
                   background: '#FADBD8', borderRadius: 4, padding: '2px 8px' }}>
      ✗ incorrect
    </span>
  )
  return <span style={{ fontSize: 10, color: '#A0AEC0' }}>unknown</span>
}

function TransferChip({ amount, fired }: { amount: number | null; fired: boolean }) {
  if (!fired) return (
    <span style={{ fontSize: 11, color: '#A0AEC0', fontVariantNumeric: 'tabular-nums' }}>
      {pct(amount ?? 0, 1)}
    </span>
  )
  return (
    <span style={{ fontSize: 11, fontWeight: 700, color: '#C0392B',
                   background: '#FADBD8', borderRadius: 4, padding: '2px 8px' }}>
      ⚡ {pct(amount, 1)}
    </span>
  )
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function LiveSessionEvidencePage() {
  const t = useT()
  const { user, isLoading: authLoading } = useAuth()
  const params = useSearchParams()
  const queryUserId = params?.get('user_id') ?? null

  const [data, setData] = useState<SessionTraceResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [tickCount, setTickCount] = useState(0)
  const [expanded, setExpanded] = useState<number | null>(null)

  const activeUserId = queryUserId ?? user?.id ?? null

  const fetchTrace = useCallback(async () => {
    if (!BACKEND || !activeUserId) {
      setData(null)
      setLoading(false)
      return
    }
    try {
      const resp = await fetch(
        `${BACKEND}/v3/frontend/dashboard/session-trace/${activeUserId}?limit=100`,
        { headers: getAuthHeaders(), signal: AbortSignal.timeout(15000) }
      )
      if (!resp.ok) {
        setData(null)
        return
      }
      const json: SessionTraceResponse = await resp.json()
      setData(json)
    } catch {
      // keep prior data on transient error
    } finally {
      setLoading(false)
      setTickCount(c => c + 1)
    }
  }, [activeUserId])

  useEffect(() => {
    if (authLoading) return
    fetchTrace()
  }, [authLoading, fetchTrace])

  useEffect(() => {
    if (!autoRefresh || authLoading) return
    const t = setInterval(fetchTrace, POLL_MS)
    return () => clearInterval(t)
  }, [autoRefresh, fetchTrace, authLoading])

  if (authLoading) {
    return <div style={{ padding: 40, textAlign: 'center', color: '#718096' }}>Loading…</div>
  }

  if (!activeUserId) {
    return (
      <div style={{ maxWidth: 720, margin: '40px auto', padding: '0 20px' }}>
        <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 12,
                       padding: '32px 28px', textAlign: 'center' }}>
          <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.1em',
                         color: '#1A5276', textTransform: 'uppercase', marginBottom: 8 }}>
            {t('evidence.liveSession')}
          </div>
          <h1 style={{ fontSize: 20, fontWeight: 800, margin: '0 0 8px' }}>
            {t('common.noData')}
          </h1>
          <div style={{ fontSize: 13, color: '#4A5568', lineHeight: 1.6, marginBottom: 16 }}>
            {t('evidence.title')}
          </div>
          <Link href="/learn" style={{
            display: 'inline-block', padding: '10px 24px',
            background: '#1A5276', color: '#fff', borderRadius: 8,
            textDecoration: 'none', fontWeight: 700,
          }}>
            {t('home.ctaLearner')} →
          </Link>
        </div>
      </div>
    )
  }

  const summary = data?.session_summary
  const trace = data?.trace ?? []
  const isFallback = !!data?.fallback_reason

  return (
    <div style={{ maxWidth: 1280, margin: '0 auto', padding: '24px 20px' }}>

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between',
                     alignItems: 'flex-start', marginBottom: 20 }}>
        <div>
          <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.1em',
                         color: '#922B21', textTransform: 'uppercase', marginBottom: 4 }}>
            {t('evidence.liveSession')}
          </div>
          <h1 style={{ fontSize: 22, fontWeight: 800, color: '#1A2332', margin: 0 }}>
            {t('evidence.title')}
          </h1>
          <div style={{ fontSize: 12, color: '#718096', marginTop: 2 }}>
            user_id: <code style={{ background: '#EDF2F7', padding: '1px 6px',
                                     borderRadius: 3 }}>{activeUserId}</code>
            {data?.authority && (
              <span style={{ marginLeft: 12, fontSize: 11, color: '#A0AEC0' }}>
                authority: {data.authority}
              </span>
            )}
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <span style={{ fontSize: 10, color: '#718096',
                          background: '#EDF2F7', borderRadius: 4, padding: '3px 8px' }}>
            tick #{tickCount} · {POLL_MS / 1000}s
          </span>
          <button onClick={() => setAutoRefresh(v => !v)} style={{
            fontSize: 12, fontWeight: 700,
            color: autoRefresh ? '#C0392B' : '#27AE60',
            background: autoRefresh ? '#FDEDEC' : '#D5F5E3',
            border: `1px solid ${autoRefresh ? '#F5B7B1' : '#A9DFBF'}`,
            borderRadius: 6, padding: '5px 12px', cursor: 'pointer',
          }}>
            {autoRefresh ? '⏸ Pause' : '▶ Live'}
          </button>
          <button onClick={fetchTrace} style={{
            fontSize: 12, color: '#4A5568', background: '#EDF2F7',
            border: '1px solid #CBD5E0', borderRadius: 6,
            padding: '5px 12px', cursor: 'pointer',
          }}>
            ↻ Refresh
          </button>
        </div>
      </div>

      {/* Fallback notice */}
      {isFallback && (
        <div style={{ background: '#FEF9E7', border: '1px solid #F9E79F',
                       borderRadius: 8, padding: '10px 14px', marginBottom: 16,
                       fontSize: 11, color: '#7D6008' }}>
          <strong>Fallback active:</strong> {data?.fallback_reason}.
          Data is synthesized from outbox event envelopes — the canonical
          CognitionUpdated events have all the JT decomposition that the
          trajectory recorder will eventually project to experiment_trajectories.
        </div>
      )}

      {/* Session summary tiles */}
      {summary && (
        <div style={{ display: 'flex', gap: 12, marginBottom: 24, flexWrap: 'wrap' }}>
          <StatTile label="Interactions" value={summary.total_interactions}
                    color="#2980B9" sub={`${summary.unique_concepts} concepts`} />
          <StatTile label="Accuracy"
                    value={`${(summary.accuracy * 100).toFixed(0)}%`}
                    color="#27AE60"
                    sub={`${summary.correct_count} / ${summary.total_interactions}`} />
          <StatTile label="Mastery gain"
                    value={`${summary.cumulative_mastery_gain >= 0 ? '+' : ''}${(summary.cumulative_mastery_gain * 100).toFixed(2)}%`}
                    color={summary.cumulative_mastery_gain >= 0 ? '#27AE60' : '#C0392B'}
                    sub="cumulative ΔM" />
          <StatTile label="Transfer events"
                    value={summary.transfer_events}
                    color="#C0392B"
                    sub={`T > ${TRANSFER_THRESHOLD}`} />
          <StatTile label="Cold-start"
                    value={`${(summary.cold_start_accuracy * 100).toFixed(0)}%`}
                    color="#8E44AD"
                    sub="first 5 attempts" />
          <StatTile label="Avg response"
                    value={summary.avg_response_time > 0 ? `${summary.avg_response_time.toFixed(1)}s` : '—'}
                    color="#E67E22" sub="per attempt" />
        </div>
      )}

      {/* Empty state */}
      {!loading && trace.length === 0 && (
        <div style={{ background: '#fff', border: '1px dashed #CBD5E0',
                       borderRadius: 12, padding: '40px 20px', textAlign: 'center' }}>
          <div style={{ fontSize: 36, marginBottom: 12, opacity: 0.4 }}>📭</div>
          <div style={{ fontSize: 14, fontWeight: 700, color: '#4A5568', marginBottom: 4 }}>
            No interactions yet for this user
          </div>
          <div style={{ fontSize: 12, color: '#718096', maxWidth: 480,
                         margin: '0 auto 16px', lineHeight: 1.5 }}>
            {data?.reason ?? 'Once the learner attempts a few tasks in /learn, every interaction will appear here with full JT 6D attribution.'}
          </div>
          <Link href="/learn" style={{
            display: 'inline-block', padding: '10px 24px',
            background: '#1A5276', color: '#fff', borderRadius: 8,
            textDecoration: 'none', fontWeight: 700, fontSize: 13,
          }}>
            Start a session →
          </Link>
        </div>
      )}

      {/* Evidence table */}
      {trace.length > 0 && (
        <div style={{ background: '#fff', border: '1px solid #E2E8F0',
                       borderRadius: 12, overflow: 'hidden' }}>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse',
                            fontSize: 12, fontVariantNumeric: 'tabular-nums' }}>
              <thead>
                <tr style={{ background: '#F7FAFC', borderBottom: '2px solid #E2E8F0' }}>
                  {[
                    { l: '#', w: 36 },
                    { l: 'Timestamp', w: 130 },
                    { l: 'Event ID', w: 140 },
                    { l: 'Concept', w: 140 },
                    { l: 'Policy', w: 70 },
                    { l: 'Correct', w: 80 },
                    { l: 'Mastery', w: 200 },
                    { l: 'JT', w: 60 },
                    { l: 'ΔM', w: 70 },
                    { l: 'T_realized', w: 90 },
                    { l: 'Challenge', w: 70 },
                    { l: 'Uncert', w: 60 },
                    { l: 'ZPD', w: 60 },
                    { l: '', w: 24 },
                  ].map((h, i) => (
                    <th key={i} style={{
                      padding: '10px 8px', textAlign: 'left',
                      fontWeight: 700, fontSize: 10, color: '#718096',
                      textTransform: 'uppercase', letterSpacing: '0.04em',
                      minWidth: h.w, position: i === 0 ? 'sticky' : undefined,
                      left: i === 0 ? 0 : undefined,
                    }}>{h.l}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {trace.map((t, idx) => {
                  const isExpanded = expanded === idx
                  return (
                    <>
                      <tr key={`${t.event_id}-${idx}`}
                          onClick={() => setExpanded(isExpanded ? null : idx)}
                          style={{
                            borderBottom: '1px solid #F1F5F9',
                            cursor: 'pointer',
                            background: isExpanded ? '#F0F9FF'
                                       : t.transfer.fired ? '#FFF5F5'
                                       : 'transparent',
                          }}>
                        <td style={{ padding: '10px 8px', fontWeight: 700,
                                     color: '#4A5568' }}>
                          {t.interaction_number ?? idx + 1}
                        </td>
                        <td style={{ padding: '10px 8px', fontFamily: 'monospace',
                                     color: '#4A5568', fontSize: 11 }}>
                          {timeStr(t.timestamp)}
                        </td>
                        <td style={{ padding: '10px 8px', fontFamily: 'monospace',
                                     color: '#718096', fontSize: 10 }}>
                          {shortEvent(t.event_id)}
                        </td>
                        <td style={{ padding: '10px 8px', color: '#1A2332', fontWeight: 600 }}>
                          {shortConcept(t.concept_id)}
                        </td>
                        <td style={{ padding: '10px 8px', color: '#4A5568',
                                     textTransform: 'uppercase', fontSize: 10 }}>
                          {t.policy ?? '—'}
                        </td>
                        <td style={{ padding: '10px 8px' }}>
                          <CorrectChip value={t.correct} />
                        </td>
                        <td style={{ padding: '10px 8px' }}>
                          <MasteryArrow before={t.mastery_before}
                                        after={t.mastery_after}
                                        delta={t.mastery_delta} />
                        </td>
                        <td style={{ padding: '10px 8px', color: '#1A5276',
                                     fontWeight: 600 }}>
                          {pct(t.jt_value, 0)}
                        </td>
                        <td style={{ padding: '10px 8px', color: '#2980B9' }}>
                          {pct(t.jt_components.delta_m, 1)}
                        </td>
                        <td style={{ padding: '10px 8px' }}>
                          <TransferChip amount={t.jt_components.transfer ?? t.transfer.amount}
                                        fired={t.transfer.fired} />
                        </td>
                        <td style={{ padding: '10px 8px', color: '#8E44AD' }}>
                          {pct(t.jt_components.challenge, 1)}
                        </td>
                        <td style={{ padding: '10px 8px', color: '#D35400' }}>
                          {pct(t.jt_components.uncertainty, 1)}
                        </td>
                        <td style={{ padding: '10px 8px', color: '#27AE60' }}>
                          {pct(t.jt_components.zpd, 1)}
                        </td>
                        <td style={{ padding: '10px 8px', color: '#A0AEC0',
                                     fontSize: 14, textAlign: 'center' }}>
                          {isExpanded ? '▾' : '▸'}
                        </td>
                      </tr>
                      {isExpanded && (
                        <tr style={{ background: '#0D1117', color: '#E6EDF3' }}>
                          <td colSpan={14} style={{ padding: '14px 18px',
                                                     fontFamily: 'monospace', fontSize: 11 }}>
                            <div style={{ display: 'grid',
                                           gridTemplateColumns: '1fr 1fr',
                                           gap: '12px 24px' }}>
                              <div>
                                <div style={{ color: '#F0883E', fontWeight: 700, marginBottom: 4 }}>
                                  Ensemble (after this interaction)
                                </div>
                                <div>
                                  Bayesian: α=<span style={{ color: '#79C0FF' }}>
                                    {fmt(t.ensemble?.bayesian_after?.alpha, 2)}
                                  </span> β=<span style={{ color: '#79C0FF' }}>
                                    {fmt(t.ensemble?.bayesian_after?.beta, 2)}
                                  </span>
                                </div>
                                <div>
                                  Kalman: μ=<span style={{ color: '#79C0FF' }}>
                                    {pct(t.ensemble?.kalman_after?.mastery, 1)}
                                  </span> σ²=<span style={{ color: '#79C0FF' }}>
                                    {fmt(t.ensemble?.kalman_after?.covariance, 4)}
                                  </span>
                                </div>
                                <div>
                                  Lyapunov: μ=<span style={{ color: '#79C0FF' }}>
                                    {pct(t.ensemble?.lyapunov_after, 1)}
                                  </span>
                                </div>
                                {t.ensemble?.normalized_weights && (
                                  <div style={{ marginTop: 4 }}>
                                    Weights: B={pct(t.ensemble.normalized_weights.bayesian, 0)} /
                                    K={pct(t.ensemble.normalized_weights.kalman, 0)} /
                                    L={pct(t.ensemble.normalized_weights.lyapunov, 0)}
                                  </div>
                                )}
                              </div>
                              <div>
                                <div style={{ color: '#F0883E', fontWeight: 700, marginBottom: 4 }}>
                                  ZPD &amp; transfer
                                </div>
                                <div>
                                  ZPD target=<span style={{ color: '#79C0FF' }}>{pct(t.zpd.target, 0)}</span>
                                  {' '}score=<span style={{ color: '#79C0FF' }}>{pct(t.zpd.score, 0)}</span>
                                  {' '}err=<span style={{ color: '#79C0FF' }}>{fmt(t.zpd.alignment_error, 3)}</span>
                                </div>
                                <div>
                                  Transfer: amount=<span style={{ color: t.transfer.fired ? '#F85149' : '#79C0FF' }}>
                                    {pct(t.transfer.amount, 2)}
                                  </span>
                                  {t.transfer.fired && (
                                    <span style={{ color: '#F85149', fontWeight: 700, marginLeft: 6 }}>
                                      ⚡ FIRED
                                    </span>
                                  )}
                                </div>
                                <div>
                                  Difficulty: <span style={{ color: '#79C0FF' }}>{pct(t.difficulty, 0)}</span>
                                  {' '}arm: <span style={{ color: '#79C0FF' }}>{t.arm_selected ?? '—'}</span>
                                </div>
                                <div style={{ marginTop: 4, color: '#8B949E', fontSize: 10 }}>
                                  event_id={t.event_id}
                                </div>
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Demo legend */}
      <div style={{ marginTop: 20, fontSize: 11, color: '#718096', lineHeight: 1.6 }}>
        <strong>Reading the table:</strong>{' '}
        Each row is one closed-loop iteration captured directly from{' '}
        <code>experiment_trajectories</code> (or via the{' '}
        <code>outbox_event_envelopes</code> fallback when consumers are lagging).
        Click any row to expand the ensemble (Bayesian/Kalman/Lyapunov before+after) and ZPD/transfer details.
        Rows highlighted in <span style={{ background: '#FFF5F5', padding: '0 4px' }}>red</span>{' '}
        fired a transfer event (T_realized &gt; {TRANSFER_THRESHOLD}).
      </div>

      {/* Footer nav */}
      <div style={{ display: 'flex', gap: 10, marginTop: 24, justifyContent: 'center' }}>
        <Link href="/learn" style={{
          fontSize: 13, fontWeight: 700, color: '#fff', background: '#1A5276',
          textDecoration: 'none', padding: '10px 24px', borderRadius: 8,
        }}>
          ← Continue learning
        </Link>
        <Link href="/dashboard/learner" style={{
          fontSize: 13, fontWeight: 600, color: '#4A5568',
          textDecoration: 'none', padding: '10px 24px', borderRadius: 8,
          border: '1px solid #CBD5E0', background: '#fff',
        }}>
          Learner Dashboard
        </Link>
        <Link href="/dashboard/instructor" style={{
          fontSize: 13, fontWeight: 600, color: '#4A5568',
          textDecoration: 'none', padding: '10px 24px', borderRadius: 8,
          border: '1px solid #CBD5E0', background: '#fff',
        }}>
          Instructor View
        </Link>
        <Link href="/dashboard/governance" style={{
          fontSize: 13, fontWeight: 600, color: '#4A5568',
          textDecoration: 'none', padding: '10px 24px', borderRadius: 8,
          border: '1px solid #CBD5E0', background: '#fff',
        }}>
          Governance Monitor
        </Link>
      </div>
    </div>
  )
}
