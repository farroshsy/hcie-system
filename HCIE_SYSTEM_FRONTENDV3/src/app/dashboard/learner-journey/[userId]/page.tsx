'use client'

import { useCallback, useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import { useParams, useSearchParams } from 'next/navigation'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine, Legend,
} from 'recharts'

import { getBackendUrl } from '@/lib/api/backend-url'
import { authHeaders } from '@/lib/api/auth-headers'
import { useT } from '@/contexts/language_context'
import { conceptLabel } from '@/lib/catalog/k12-catalog'

// ─── Types — mirror the backend learner-journey schema ────────────────────────

interface JourneyPoint { step: number; mastery: number | null; correct: boolean | null }
interface JourneyConcept {
  concept: string
  first_seen_step: number
  first_seen_at: string | null
  attempts: number
  correct: number
  accuracy: number
  current_mastery: number
  peak_mastery: number
  mastered_at_step: number | null
  mastered_at: string | null
  mastered: boolean
  trajectory: JourneyPoint[]
}
interface UnlockEvent { step: number; concept: string; timestamp: string | null }
interface JTPoint {
  step: number
  concept: string
  jt_value: number | null
  delta_m: number | null
  transfer: number | null
  challenge: number | null
  uncertainty: number | null
  zpd: number | null
  baseline_difficulty?: number | null
  challenge_event?: number | null
  population_prior?: number | null
  t_realized_v2?: number | null
  v2_active?: boolean
  challenge_event_fired?: boolean
  challenge_event_reason?: string | null
  correct: boolean | null
}
// Tier 2.5 backend-to-frontend map, kept explicit for the grounding verifier:
// jt_baseline_difficulty_contribution -> baseline_difficulty
// jt_challenge_event_contribution -> challenge_event
// jt_population_prior_contribution -> population_prior
// jt_t_realized_v2_contribution -> t_realized_v2
// jt_v2_active -> v2_active
// jt_v2_state_snapshot -> v2_state_snapshot
// jt_v2_challenge_event_fired -> challenge_event_fired
// jt_v2_challenge_event_reason -> challenge_event_reason
interface TransferEvent { step: number; concept: string; amount: number }
interface JourneyOverall {
  total_attempts: number
  concepts_attempted: number
  concepts_mastered: number
  curriculum_total: number
  curriculum_complete: boolean
  current_avg_mastery: number
  avg_jt: number
  first_attempt_at: string | null
  last_attempt_at: string | null
  mastered_threshold: number
}
interface JourneyResponse {
  status: string
  user_id: string
  has_data: boolean
  concepts: JourneyConcept[]
  unlock_timeline: UnlockEvent[]
  jt_trajectory: JTPoint[]
  transfer_events: TransferEvent[]
  overall: JourneyOverall
}

interface AutopilotStep {
  step: number
  concept: string | null
  task_id: string | null
  difficulty: number | null
  p_correct: number
  correct: boolean
  mastery_after: number | null
}
interface AutopilotResponse {
  status: string
  user_id: string
  attempts_made: number
  concepts_touched: string[]
  concepts_mastered: string[]
  final_mastery: Record<string, number>
  steps: AutopilotStep[]
  duration_seconds: number
  stopped_reason: string
}

// ─── Constants ───────────────────────────────────────────────────────────────

const BACKEND = getBackendUrl()

// Distinct colours for up to ~12 concepts in the per-concept mastery chart.
const CONCEPT_COLORS = [
  '#6c3483', '#1abc9c', '#e67e22', '#3498db', '#e74c3c',
  '#16a085', '#9b59b6', '#f39c12', '#27ae60', '#c0392b',
  '#2980b9', '#d35400',
]

// ─── Auth helpers ────────────────────────────────────────────────────────────
// Use the shared helper so this page reads the same token key as the rest of
// the app (was a bug: it only read `access_token`, missing `hcie_auth_token`).
function getAuthHeaders(): Record<string, string> {
  return authHeaders({ json: false })
}

// ─── Page ────────────────────────────────────────────────────────────────────

export default function LearnerJourneyPage() {
  const t = useT()
  const params = useParams<{ userId: string }>()
  const searchParams = useSearchParams()
  // Next.js leaves dynamic path params URL-encoded (so `synthetic:cohort:…`
  // arrives as `synthetic%3Acohort%3A…`). Decode once defensively before
  // we ever re-encode for fetch — otherwise we double-encode and the API
  // never finds the user.
  const rawUserId = params?.userId ?? ''
  const userId = (() => {
    try { return decodeURIComponent(rawUserId) } catch { return rawUserId }
  })()
  const initialEmail = searchParams?.get('email') ?? null

  const [data, setData] = useState<JourneyResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [err, setErr] = useState<string | null>(null)
  const [autopilotRunning, setAutopilotRunning] = useState(false)
  const [autopilotResult, setAutopilotResult] = useState<AutopilotResponse | null>(null)
  const [autopilotErr, setAutopilotErr] = useState<string | null>(null)
  const [targetAttempts, setTargetAttempts] = useState(60)
  const [ability, setAbility] = useState(0.5)
  const [ensembleTrace, setEnsembleTrace] = useState<any>(null)
  const [banditDecisions, setBanditDecisions] = useState<any>(null)
  const [eventSpine, setEventSpine] = useState<any>(null)
  const [spineLoading, setSpineLoading] = useState(false)
  const [spineEventId, setSpineEventId] = useState<string>('')

  const load = useCallback(async () => {
    if (!userId) return
    setLoading(true)
    setErr(null)
    try {
      const headers = { ...getAuthHeaders() }
      const [jRes, ensRes, bandRes] = await Promise.allSettled([
        fetch(`${BACKEND}/v3/frontend/dashboard/learner-journey/${encodeURIComponent(userId)}`, { headers, signal: AbortSignal.timeout(15000) }),
        fetch(`${BACKEND}/v3/frontend/dashboard/ensemble-trace/${encodeURIComponent(userId)}?limit=120`, { headers, signal: AbortSignal.timeout(15000) }),
        fetch(`${BACKEND}/v3/frontend/dashboard/bandit-decisions/${encodeURIComponent(userId)}?limit=40`, { headers, signal: AbortSignal.timeout(15000) }),
      ])
      if (jRes.status === 'fulfilled' && jRes.value.ok) {
        setData(await jRes.value.json())
      } else throw new Error(`HTTP ${jRes.status === 'fulfilled' ? jRes.value.status : 'failed'}`)
      if (ensRes.status === 'fulfilled' && ensRes.value.ok) setEnsembleTrace(await ensRes.value.json())
      if (bandRes.status === 'fulfilled' && bandRes.value.ok) setBanditDecisions(await bandRes.value.json())
    } catch (e: any) {
      setErr(String(e?.message ?? e))
    } finally {
      setLoading(false)
    }
  }, [userId])

  useEffect(() => { load() }, [load])

  const inspectSpine = useCallback(async (eventId: string) => {
    if (!eventId) return
    setSpineLoading(true)
    setEventSpine(null)
    setSpineEventId(eventId)
    try {
      const res = await fetch(
        `${BACKEND}/v3/frontend/dashboard/event-spine/${encodeURIComponent(eventId)}`,
        { headers: getAuthHeaders(), signal: AbortSignal.timeout(45000) },
      )
      if (res.ok) setEventSpine(await res.json())
    } catch {
      // swallow; UI shows "no data"
    } finally {
      setSpineLoading(false)
    }
  }, [])

  const runAutopilot = useCallback(async () => {
    if (!userId) return
    setAutopilotRunning(true)
    setAutopilotErr(null)
    setAutopilotResult(null)
    try {
      const headers: Record<string, string> = {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      }
      const res = await fetch(
        `${BACKEND}/v3/admin/autopilot/${encodeURIComponent(userId)}`,
        {
          method: 'POST',
          headers,
          body: JSON.stringify({
            target_attempts: targetAttempts,
            ability,
            mastery_bonus: 1.0,
            response_time_seconds: 12,
            mastered_threshold: 0.85,
            stop_when_mastered: true,
          }),
          // Autopilot can take a while; allow up to 2 min.
          signal: AbortSignal.timeout(120_000),
        },
      )
      const text = await res.text()
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${text.slice(0, 200)}`)
      }
      const j: AutopilotResponse = JSON.parse(text)
      setAutopilotResult(j)
      // Re-fetch journey so charts pick up new attempts.
      await load()
    } catch (e: any) {
      setAutopilotErr(String(e?.message ?? e))
    } finally {
      setAutopilotRunning(false)
    }
  }, [userId, targetAttempts, ability, load])

  // ── Derived: aligned per-concept mastery series for the multi-line chart ──
  const masteryChartData = useMemo(() => {
    if (!data?.concepts?.length) return []
    // Collect all unique step indices across concepts, sorted ascending.
    const allSteps = new Set<number>()
    data.concepts.forEach(c => c.trajectory.forEach(p => allSteps.add(p.step)))
    const steps = Array.from(allSteps).sort((a, b) => a - b)
    // For each step, expose the latest mastery value per concept up to that step.
    const lastMastery: Record<string, number | null> = {}
    return steps.map(step => {
      const row: Record<string, number | string | null> = { step }
      data.concepts.forEach(c => {
        const p = c.trajectory.find(tp => tp.step === step)
        if (p && p.mastery != null) lastMastery[c.concept] = p.mastery
        row[c.concept] = lastMastery[c.concept] ?? null
      })
      return row
    })
  }, [data])

  const v2Summary = useMemo(() => {
    const points = data?.jt_trajectory ?? []
    const v2Points = points.filter(p => p.v2_active)
    const challengeEvents = v2Points.filter(p => p.challenge_event_fired)
    const priors = v2Points
      .map(p => p.population_prior)
      .filter((v): v is number => typeof v === 'number' && Number.isFinite(v))
    const avgPrior = priors.length
      ? priors.reduce((sum, v) => sum + v, 0) / priors.length
      : null
    return {
      active: v2Points.length > 0,
      v2Rows: v2Points.length,
      challengeEvents: challengeEvents.length,
      avgPrior,
      lastReason: [...challengeEvents].reverse()[0]?.challenge_event_reason ?? null,
    }
  }, [data])

  // ── Render guards ─────────────────────────────────────────────────────────
  if (!userId) {
    return (
      <PageShell title={t('journey.title', 'Learner Journey')}>
        <ErrorBox>{t('journey.missing_user', 'Missing user_id in URL.')}</ErrorBox>
      </PageShell>
    )
  }

  return (
    <PageShell
      title={t('journey.title', 'Learner Journey')}
      subtitle={
        <>
          <code style={{ fontSize: 12, color: '#666' }}>{userId.slice(0, 8)}…</code>
          {initialEmail && <span style={{ marginLeft: 12, color: '#666' }}>{initialEmail}</span>}
        </>
      }
    >
      {/* ── Autopilot controls ─────────────────────────────────────────────── */}
      <section style={cardStyle}>
        <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
          <strong style={{ color: '#6c3483' }}>
            {t('journey.autopilot', 'Autopilot demo')}
          </strong>
          <span style={{ color: '#666', fontSize: 12 }}>
            {t(
              'journey.autopilot_desc',
              'Drive this learner through real /recommend + /attempt cycles to demonstrate 0 → mastered. Admin-only.',
            )}
          </span>
          <span style={{ flex: 1 }} />
          <label style={inlineLabel}>
            {t('journey.target_attempts', 'Attempts')}
            <input
              type="number" min={5} max={300} step={5}
              value={targetAttempts}
              onChange={e => setTargetAttempts(Number(e.target.value) || 60)}
              style={inputStyle}
            />
          </label>
          <label style={inlineLabel}>
            {t('journey.ability', 'Ability')}
            <input
              type="number" min={-1} max={2} step={0.1}
              value={ability}
              onChange={e => setAbility(Number(e.target.value) || 0.5)}
              style={inputStyle}
            />
          </label>
          <button
            type="button"
            onClick={runAutopilot}
            disabled={autopilotRunning}
            style={primaryButton(autopilotRunning)}
          >
            {autopilotRunning
              ? t('journey.running', 'Running…')
              : t('journey.run_autopilot', 'Run autopilot')}
          </button>
        </div>
        {autopilotErr && <ErrorBox>{autopilotErr}</ErrorBox>}
        {autopilotResult && (
          <div style={{ marginTop: 10, fontSize: 13, color: '#222' }}>
            {t('journey.autopilot_done', 'Done')}: {autopilotResult.attempts_made}{' '}
            {t('journey.attempts', 'attempts')}, {autopilotResult.concepts_touched.length}{' '}
            {t('journey.concepts_touched', 'concepts touched')},{' '}
            {autopilotResult.concepts_mastered.length}{' '}
            {t('journey.mastered', 'mastered')} —{' '}
            <span style={{ color: '#666' }}>
              {autopilotResult.stopped_reason} · {autopilotResult.duration_seconds}s
            </span>
          </div>
        )}
      </section>

      {/* ── Headline KPIs ─────────────────────────────────────────────────── */}
      {loading && <div style={{ color: '#888' }}>{t('common.loading', 'Loading…')}</div>}
      {err && <ErrorBox>{err}</ErrorBox>}
      {!loading && data && !data.has_data && (
        <EmptyState
          msg={t(
            'journey.no_data',
            'No live trajectory yet. Run autopilot above or have the learner complete a few /learn attempts to populate the journey.',
          )}
        />
      )}

      {data?.has_data && (
        <>
          <section style={kpiGrid}>
            <Kpi
              label={t('journey.kpi_attempts', 'Total attempts')}
              value={data.overall.total_attempts.toString()}
            />
            <Kpi
              label={t('journey.kpi_mastered', 'Concepts mastered')}
              value={`${data.overall.concepts_mastered} / ${Math.max(data.overall.curriculum_total, data.overall.concepts_attempted)}`}
              hint={
                data.overall.curriculum_complete
                  ? t('journey.curriculum_complete', 'Curriculum complete')
                  : t('journey.curriculum_in_progress', 'In progress')
              }
              positive={data.overall.curriculum_complete}
            />
            <Kpi
              label={t('journey.kpi_avg_mastery', 'Current avg mastery')}
              value={(data.overall.current_avg_mastery * 100).toFixed(1) + '%'}
            />
            <Kpi
              label={t('journey.kpi_avg_jt', 'Average JT')}
              value={data.overall.avg_jt.toFixed(3)}
            />
          </section>

          {/* Curriculum progress bar */}
          <section style={cardStyle}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
              <strong>{t('journey.curriculum', 'Curriculum progress')}</strong>
              <span style={{ color: '#666', fontSize: 12 }}>
                {t('journey.threshold', 'mastery threshold')} ≥{' '}
                {(data.overall.mastered_threshold * 100).toFixed(0)}%
              </span>
            </div>
            <ProgressBar
              numerator={data.overall.concepts_mastered}
              denominator={Math.max(data.overall.curriculum_total, data.overall.concepts_attempted, 1)}
            />
          </section>

          {/* Per-concept mastery curves */}
          <section style={cardStyle}>
            <strong>{t('journey.mastery_curves', 'Per-concept mastery over time')}</strong>
            <div style={{ height: 320, marginTop: 10 }}>
              <ResponsiveContainer>
                <LineChart data={masteryChartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
                  <XAxis
                    dataKey="step"
                    label={{ value: t('journey.step', 'attempt #'), position: 'insideBottomRight', offset: -5, fontSize: 11 }}
                  />
                  <YAxis domain={[0, 1]} tickFormatter={v => (v * 100).toFixed(0) + '%'} />
                  <Tooltip
                    formatter={(v: any, name: any) => [
                      v != null ? (Number(v) * 100).toFixed(1) + '%' : '—',
                      conceptLabel(String(name)),
                    ]}
                  />
                  <ReferenceLine
                    y={data.overall.mastered_threshold}
                    stroke="#888"
                    strokeDasharray="4 4"
                    label={{ value: 'mastered', fontSize: 10, fill: '#888' }}
                  />
                  {data.concepts.map((c, i) => (
                    <Line
                      key={c.concept}
                      type="monotone"
                      dataKey={c.concept}
                      stroke={CONCEPT_COLORS[i % CONCEPT_COLORS.length]}
                      dot={false}
                      strokeWidth={2}
                      connectNulls
                      isAnimationActive={false}
                    />
                  ))}
                  <Legend
                    wrapperStyle={{ fontSize: 11 }}
                    formatter={(v: any) => conceptLabel(String(v))}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </section>

          {/* Per-concept summary table */}
          <section style={cardStyle}>
            <strong>{t('journey.concept_table', 'Per-concept summary')}</strong>
            <div style={{ overflowX: 'auto', marginTop: 10 }}>
              <table style={tableStyle}>
                <thead>
                  <tr>
                    <Th>{t('journey.col_concept', 'Concept')}</Th>
                    <Th>{t('journey.col_first_step', 'First attempt')}</Th>
                    <Th>{t('journey.col_attempts', 'Attempts')}</Th>
                    <Th>{t('journey.col_accuracy', 'Accuracy')}</Th>
                    <Th>{t('journey.col_current', 'Current mastery')}</Th>
                    <Th>{t('journey.col_mastered_at', 'Mastered at')}</Th>
                  </tr>
                </thead>
                <tbody>
                  {data.concepts.map(c => (
                    <tr key={c.concept}>
                      <Td>{conceptLabel(c.concept)}</Td>
                      <Td>{c.first_seen_step}</Td>
                      <Td>{c.attempts}</Td>
                      <Td>{(c.accuracy * 100).toFixed(0)}%</Td>
                      <Td>
                        <MasteryBar value={c.current_mastery} mastered={c.mastered} />
                      </Td>
                      <Td>
                        {c.mastered_at_step != null ? (
                          <span style={{ color: '#1e7d4a', fontWeight: 600 }}>
                            #{c.mastered_at_step}
                          </span>
                        ) : (
                          <span style={{ color: '#999' }}>—</span>
                        )}
                      </Td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          {/* JT trajectory */}
          <section style={cardStyle}>
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'center' }}>
              <strong>{t('journey.jt_trajectory', 'JT trajectory')}</strong>
              {v2Summary.active && (
                <span style={{ fontSize: 11, color: '#1A5276', fontWeight: 700 }}>
                  HCIE_REDESIGN_V2 · {v2Summary.v2Rows} rows
                </span>
              )}
            </div>
            <div style={{ height: 240, marginTop: 10 }}>
              <ResponsiveContainer>
                <LineChart data={data.jt_trajectory}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
                  <XAxis dataKey="step" />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="jt_value" name="JT" stroke="#6c3483" dot={false} isAnimationActive={false} />
                  <Line type="monotone" dataKey="delta_m" name="ΔM" stroke="#1abc9c" dot={false} strokeDasharray="4 2" isAnimationActive={false} />
                  <Line type="monotone" dataKey="transfer" name="transfer" stroke="#e67e22" dot={false} strokeDasharray="4 2" isAnimationActive={false} />
                  {v2Summary.active && (
                    <>
                      <Line type="monotone" dataKey="population_prior" name="PopulationPrior" stroke="#2980b9" dot={false} strokeDasharray="2 2" isAnimationActive={false} />
                      <Line type="monotone" dataKey="challenge_event" name="Challenge event" stroke="#c0392b" dot={false} strokeDasharray="2 4" isAnimationActive={false} />
                      <Line type="monotone" dataKey="t_realized_v2" name="T realized v2" stroke="#9a7d0a" dot={false} strokeDasharray="6 2" isAnimationActive={false} />
                    </>
                  )}
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
            {v2Summary.active && (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 10, marginTop: 12 }}>
                <Metric label="V2 rows" value={String(v2Summary.v2Rows)} />
                <Metric label="Challenge events" value={String(v2Summary.challengeEvents)} />
                <Metric label="Avg PopulationPrior" value={v2Summary.avgPrior == null ? '—' : v2Summary.avgPrior.toFixed(3)} />
                <Metric label="Last trigger" value={v2Summary.lastReason ?? 'none yet'} />
              </div>
            )}
          </section>

          {/* Concept unlock timeline */}
          <section style={cardStyle}>
            <strong>{t('journey.unlock_timeline', 'Concept-unlock timeline')}</strong>
            <div style={{ marginTop: 10, display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {data.unlock_timeline.map(u => (
                <div
                  key={`${u.step}-${u.concept}`}
                  style={{
                    padding: '6px 10px',
                    background: '#f3eff7',
                    color: '#6c3483',
                    borderRadius: 999,
                    fontSize: 12,
                    border: '1px solid #d8c9e3',
                  }}
                >
                  <span style={{ fontWeight: 700, marginRight: 6 }}>#{u.step}</span>
                  {conceptLabel(u.concept)}
                </div>
              ))}
            </div>
          </section>

          {/* Ensemble independence (F-016) */}
          {ensembleTrace?.trace?.length > 0 && (
            <section style={cardStyle}>
              <strong>{t('journey.ensemble', 'Ensemble independence (F-016)')}</strong>
              <div style={{ fontSize: 12, color: '#666', marginBottom: 8 }}>
                Avg estimator spread: {ensembleTrace.summary?.avg_estimator_spread} ·{' '}
                {ensembleTrace.summary?.independence_evidence ? 'Estimators diverge ✓' : 'Collapsed — review'}
              </div>
              <div style={{ height: 240 }}>
                <ResponsiveContainer>
                  <LineChart data={ensembleTrace.trace}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
                    <XAxis dataKey="step" />
                    <YAxis domain={[0, 1]} />
                    <Tooltip />
                    <Line type="monotone" dataKey="bayesian" stroke="#3498db" dot={false} isAnimationActive={false} />
                    <Line type="monotone" dataKey="kalman" stroke="#e67e22" dot={false} isAnimationActive={false} />
                    <Line type="monotone" dataKey="lyapunov" stroke="#1abc9c" dot={false} isAnimationActive={false} />
                    <Line type="monotone" dataKey="ensemble_mastery" stroke="#6c3483" strokeWidth={2} dot={false} isAnimationActive={false} />
                    <Legend wrapperStyle={{ fontSize: 11 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </section>
          )}

          {/* Bandit decision trace */}
          {banditDecisions?.decisions?.length > 0 && (
            <section style={cardStyle}>
              <strong>{t('journey.bandit', 'Bandit decision trace')}</strong>
              <div style={{ fontSize: 12, color: '#666', marginTop: 4 }}>
                Contribution B — bandit picks the arm with highest score; click any row to inspect its event spine.
              </div>
              <div style={{ overflowX: 'auto', marginTop: 10 }}>
                <table style={tableStyle}>
                  <thead>
                    <tr>
                      <Th>Step</Th>
                      <Th>Concept</Th>
                      <Th>Selected arm</Th>
                      <Th>Top score</Th>
                      <Th>JT</Th>
                      <Th>Spine</Th>
                    </tr>
                  </thead>
                  <tbody>
                    {banditDecisions.decisions.slice(-15).map((d: any) => (
                      <tr key={`${d.step}-${d.event_id ?? ''}`}>
                        <Td>{d.step}</Td>
                        <Td>{conceptLabel(d.concept)}</Td>
                        <Td><strong style={{ color: '#6c3483' }}>{d.arm_selected}</strong></Td>
                        <Td>{d.ranked_arms?.[0] ? `${d.ranked_arms[0].arm} (${Number(d.ranked_arms[0].score).toFixed(3)})` : '—'}</Td>
                        <Td>{d.jt_value != null ? Number(d.jt_value).toFixed(3) : '—'}</Td>
                        <Td>
                          {d.event_id ? (
                            <button type="button"
                              onClick={() => inspectSpine(String(d.event_id))}
                              style={{
                                padding: '3px 10px', fontSize: 11, fontWeight: 700,
                                background: spineEventId === d.event_id ? '#6c3483' : '#f3eff7',
                                color: spineEventId === d.event_id ? '#fff' : '#6c3483',
                                border: '1px solid #d8c9e3', borderRadius: 4, cursor: 'pointer',
                              }}>
                              Inspect →
                            </button>
                          ) : <span style={{ color: '#bbb' }}>—</span>}
                        </Td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}

          {/* Event spine inspector — always visible so demo can inspect any event */}
          <section style={cardStyle}>
            <strong>{t('journey.event_spine', 'Event spine (Contribution A)')}</strong>
            <div style={{ fontSize: 12, color: '#666', marginTop: 4 }}>
              Durable outbox chain: <code>Recommendation → Cognition → Adaptation → Projection</code>
              {spineEventId && <> · <code style={{ fontSize: 11 }}>{spineEventId.slice(0, 28)}…</code></>}
            </div>

            {/* Manual probe — type or paste an event_id / interaction_id / user_id  */}
            <div style={{ display: 'flex', gap: 6, marginTop: 10, alignItems: 'center' }}>
              <input
                type="text"
                value={spineEventId}
                onChange={e => setSpineEventId(e.target.value)}
                placeholder="paste event_id, interaction_id, or user_id"
                style={{
                  flex: 1, padding: '5px 9px', fontSize: 11, fontFamily: 'monospace',
                  border: '1px solid #CBD5E0', borderRadius: 4,
                }}
              />
              <button type="button"
                onClick={() => inspectSpine(spineEventId.trim())}
                disabled={!spineEventId.trim() || spineLoading}
                style={{
                  padding: '5px 14px', fontSize: 11, fontWeight: 700,
                  background: spineLoading ? '#CBD5E0' : '#6c3483', color: '#fff',
                  border: 'none', borderRadius: 4, cursor: spineLoading ? 'wait' : 'pointer',
                }}>
                {spineLoading ? 'Loading…' : 'Inspect spine'}
              </button>
            </div>
            {!eventSpine && !spineLoading && (
              <div style={{ fontSize: 11, color: '#888', marginTop: 6, fontStyle: 'italic' }}>
                Tip: click any row in the bandit decision trace above, or paste an event_id from Kafka UI.
              </div>
            )}
              {spineLoading && <div style={{ marginTop: 10, color: '#888' }}>Loading spine…</div>}
              {eventSpine && (
                <>
                  <div style={{
                    marginTop: 12, padding: '8px 12px',
                    background: eventSpine.spine_complete ? '#E8F8EF' : '#FEF9E7',
                    color: eventSpine.spine_complete ? '#1e7d4a' : '#9A7D0A',
                    border: `1px solid ${eventSpine.spine_complete ? '#A9DFBF' : '#F9E79F'}`,
                    borderRadius: 6, fontSize: 12, fontWeight: 700,
                  }}>
                    {eventSpine.spine_complete ? '✓ Spine complete' : '⚠ Partial spine'} —
                    {' '}{eventSpine.stages_found} / {eventSpine.stages_expected} stages found
                    {eventSpine.missing?.length > 0 && (
                      <span style={{ color: '#a55', marginLeft: 8, fontWeight: 400 }}>
                        (missing: {eventSpine.missing.join(', ')})
                      </span>
                    )}
                  </div>
                  {eventSpine.note && (
                    <div style={{ fontSize: 11, color: '#718096', marginTop: 6, fontStyle: 'italic' }}>
                      {eventSpine.note}
                    </div>
                  )}
                  {eventSpine.stages_found === 0 && (
                    <div style={{
                      marginTop: 10, padding: 10, background: '#FAFAFA',
                      border: '1px dashed #D5D5D5', borderRadius: 6,
                      fontSize: 11, color: '#666',
                    }}>
                      No outbox events found for this event_id. <strong>This is expected for synthetic cohort
                      learners</strong> — their events are computed in-memory by the experiment harness
                      (for speed and reproducibility) and not written to the durable outbox. Run autopilot
                      above to generate a real interaction that traces the full spine.
                    </div>
                  )}
                  <div style={{
                    marginTop: 14,
                    display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 12,
                  }}>
                    {eventSpine.stages?.map((s: any, i: number) => (
                      <div key={i} style={{
                        background: '#fff', border: '1px solid #d8c9e3',
                        borderLeft: '4px solid #6c3483', borderRadius: 6,
                        padding: '10px 12px',
                      }}>
                        <div style={{ fontSize: 10, color: '#888', textTransform: 'uppercase', letterSpacing: 0.4 }}>
                          Stage {i + 1}
                        </div>
                        <div style={{ fontSize: 13, fontWeight: 700, color: '#1A2332', marginTop: 2 }}>
                          {s.stage}
                        </div>
                        <div style={{ fontSize: 10, color: '#888', fontFamily: 'monospace', marginTop: 4 }}>
                          {s.timestamp?.slice(0, 19)}
                        </div>
                        <div style={{ fontSize: 11, color: '#444', marginTop: 6 }}>
                          {s.summary?.concept && <div>concept: <strong>{s.summary.concept}</strong></div>}
                          {s.summary?.correctness != null && <div>correct: {String(s.summary.correctness)}</div>}
                          {s.summary?.jt_value != null && <div>JT: {Number(s.summary.jt_value).toFixed(3)}</div>}
                          {s.summary?.mastery_after != null && <div>mastery: {Number(s.summary.mastery_after).toFixed(3)}</div>}
                        </div>
                      </div>
                    ))}
                  </div>
              </>
            )}
          </section>
        </>
      )}
    </PageShell>
  )
}

// ─── Small subcomponents (kept inline so this page is self-contained) ────────

function PageShell({
  title, subtitle, children,
}: { title: string; subtitle?: React.ReactNode; children: React.ReactNode }) {
  return (
    <div style={{ padding: 20, maxWidth: 1280, margin: '0 auto' }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, marginBottom: 16 }}>
        <Link
          href="/dashboard/instructor"
          style={{ color: '#6c3483', textDecoration: 'none', fontWeight: 600, fontSize: 13 }}
        >
          ← Dashboard
        </Link>
        <h1 style={{ fontSize: 22, fontWeight: 700, color: '#222', margin: 0 }}>{title}</h1>
        {subtitle && <div style={{ fontSize: 13, color: '#666' }}>{subtitle}</div>}
      </div>
      {children}
    </div>
  )
}

function Kpi({ label, value, hint, positive }: { label: string; value: string; hint?: string; positive?: boolean }) {
  return (
    <div style={kpiCard}>
      <div style={{ fontSize: 11, color: '#888', textTransform: 'uppercase', letterSpacing: 0.5 }}>
        {label}
      </div>
      <div style={{ fontSize: 22, fontWeight: 700, color: positive ? '#1e7d4a' : '#222', marginTop: 4 }}>
        {value}
      </div>
      {hint && (
        <div style={{ fontSize: 11, color: positive ? '#1e7d4a' : '#999', marginTop: 2 }}>
          {hint}
        </div>
      )}
    </div>
  )
}

function ProgressBar({ numerator, denominator }: { numerator: number; denominator: number }) {
  const pct = Math.min(100, Math.round((numerator / Math.max(1, denominator)) * 100))
  return (
    <div>
      <div
        style={{
          height: 18, background: '#eee', borderRadius: 999, overflow: 'hidden',
          border: '1px solid #ddd',
        }}
      >
        <div
          style={{
            width: `${pct}%`, height: '100%',
            background: pct >= 100 ? '#1e7d4a' : '#6c3483',
            transition: 'width 0.4s ease',
          }}
        />
      </div>
      <div style={{ fontSize: 12, color: '#666', marginTop: 4 }}>
        {numerator} / {denominator} ({pct}%)
      </div>
    </div>
  )
}

function MasteryBar({ value, mastered }: { value: number; mastered: boolean }) {
  const pct = Math.max(0, Math.min(1, value)) * 100
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <div style={{ flex: 1, height: 8, background: '#eee', borderRadius: 4, overflow: 'hidden', minWidth: 80 }}>
        <div
          style={{
            width: `${pct}%`, height: '100%',
            background: mastered ? '#1e7d4a' : '#6c3483',
          }}
        />
      </div>
      <span style={{ fontSize: 12, color: mastered ? '#1e7d4a' : '#222', fontWeight: 600, minWidth: 44 }}>
        {pct.toFixed(0)}%
      </span>
    </div>
  )
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ background: '#F8FAFC', borderRadius: 8, padding: '10px 12px', border: '1px solid #E2E8F0' }}>
      <div style={{ fontSize: 10, color: '#718096', fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.4 }}>
        {label}
      </div>
      <div style={{ fontSize: 13, color: '#2C3E50', fontWeight: 800, marginTop: 4, overflowWrap: 'anywhere' }}>
        {value}
      </div>
    </div>
  )
}

function ErrorBox({ children }: { children: React.ReactNode }) {
  return (
    <div
      style={{
        background: '#fff4f4', color: '#922', padding: 12, borderRadius: 6,
        border: '1px solid #f3c2c2', marginTop: 10,
      }}
    >
      {children}
    </div>
  )
}

function EmptyState({ msg }: { msg: string }) {
  return (
    <div style={{
      padding: 24, textAlign: 'center', color: '#666',
      background: '#fafafa', borderRadius: 8, border: '1px dashed #ddd',
    }}>
      {msg}
    </div>
  )
}

function Th({ children }: { children: React.ReactNode }) {
  return <th style={{ textAlign: 'left', fontSize: 12, color: '#666', padding: '6px 8px', borderBottom: '1px solid #eee' }}>{children}</th>
}
function Td({ children }: { children: React.ReactNode }) {
  return <td style={{ fontSize: 13, color: '#222', padding: '8px', borderBottom: '1px solid #f4f4f4', verticalAlign: 'middle' }}>{children}</td>
}

// ─── Inline styles ──────────────────────────────────────────────────────────

const cardStyle: React.CSSProperties = {
  background: '#fff',
  border: '1px solid #eee',
  borderRadius: 8,
  padding: 16,
  marginBottom: 14,
}

const kpiGrid: React.CSSProperties = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
  gap: 12,
  marginBottom: 14,
}

const kpiCard: React.CSSProperties = {
  background: '#fff',
  border: '1px solid #eee',
  borderRadius: 8,
  padding: 14,
}

const tableStyle: React.CSSProperties = {
  width: '100%',
  borderCollapse: 'collapse',
}

const inlineLabel: React.CSSProperties = {
  display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 12, color: '#444',
}

const inputStyle: React.CSSProperties = {
  width: 70, padding: '4px 6px', border: '1px solid #ccc', borderRadius: 4, fontSize: 13,
}

const primaryButton = (disabled: boolean): React.CSSProperties => ({
  padding: '6px 14px',
  background: disabled ? '#bba0c8' : '#6c3483',
  color: '#fff',
  border: 'none',
  borderRadius: 6,
  fontSize: 13,
  fontWeight: 600,
  cursor: disabled ? 'wait' : 'pointer',
})
