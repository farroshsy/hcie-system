'use client'

/**
 * Cohort Study — standalone page (trial extraction from the instructor tab).
 *
 * Three upgrades over the old in-tab version:
 *   1. Label-based policy/run picker — click a labeled card, no UUID typing.
 *   2. Live elapsed timer — started_at → now (or → completed_at) + ETA from progress.
 *   3. Resume indicator — badge when a run was restarted mid-flight.
 *
 * Data: GET /v3/frontend/dashboard/cohort-run/{run_id}/comparison
 *       (same endpoint the instructor Cohort Study tab uses — single source of truth)
 * Launch (researcher/admin only): POST /v3/experiments/cohorts/{id}/launch
 */

import { useEffect, useState, useRef, useCallback } from 'react'
import { useAuth } from '@/contexts/auth_context'
import { useT } from '@/contexts/language_context'
import Link from 'next/link'
import { getBackendUrl } from '@/lib/api/backend-url'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'
import { conceptLabel } from '@/lib/catalog/k12-catalog'

const BACKEND = getBackendUrl()

// ── Known labeled runs (entry points without typing a UUID) ──────────────────
// Grouped into Synthetic (policy-comparison sweeps) and Real-Dataset Replay
// (real student KT logs replayed through HCIE). Run IDs are the best
// completed run per source (most interactions) as of 2026-06-01.
type RunGroup = 'synthetic' | 'dataset'

// Runs are now loaded LIVE from /cohort-runs?group=synthetic (no hardcoded IDs).
// A run that the backend can't classify still shows; reason/cohort_id label it.
// Dataset-replay runs live in /dashboard/benchmarks (different experiment).

const POLICY_COLOR: Record<string, string> = {
  hcie: '#1A5276', random: '#C0392B', mastery_greedy: '#1E8449',
  static: '#E67E22', zpd_aligned: '#8E44AD', thompson: '#2980B9',
  uncertainty_reduction: '#16A085', epsilon_greedy: '#27AE60',
  bandit: '#784212', ucb: '#7F8C8D',
}

function getAuthHeaders(): HeadersInit {
  const token = (typeof window !== 'undefined' &&
    (localStorage.getItem('hcie_auth_token') || localStorage.getItem('access_token'))) || ''
  return token ? { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }
               : { 'Content-Type': 'application/json' }
}

// ── Elapsed-time formatting ───────────────────────────────────────────────────
function fmtDuration(ms: number): string {
  if (ms < 0 || !isFinite(ms)) return '—'
  const s = Math.floor(ms / 1000)
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  const sec = s % 60
  if (h > 0) return `${h}h ${m}m ${sec}s`
  if (m > 0) return `${m}m ${sec}s`
  return `${sec}s`
}

export default function CohortStudyPage() {
  const { user, isAuthenticated, isLoading: authLoading } = useAuth()
  const t = useT()
  const role = String((user as any)?.role || '')
  const canLaunch = ['researcher', 'admin'].includes(role)

  const [runId, setRunId] = useState('')
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [polling, setPolling] = useState(false)
  // Live cohort comparison — real human learners as a virtual cohort,
  // grouped against the most recent synthetic policy runs.
  const [liveCohort, setLiveCohort] = useState<any>(null)
  const [liveLoading, setLiveLoading] = useState(false)
  const [liveErr, setLiveErr] = useState<string | null>(null)
  const [liveSince, setLiveSince] = useState<string>('')
  const [liveUntil, setLiveUntil] = useState<string>('')
  const [regretData, setRegretData] = useState<any>(null)
  // Live synthetic-run index (replaces hardcoded KNOWN_RUNS)
  const [syntheticRuns, setSyntheticRuns] = useState<any[]>([])
  // Tick state to re-render the live timer every second
  const [, setTick] = useState(0)
  const tickRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Launcher state (researcher/admin)
  const [cohorts, setCohorts] = useState<Array<{cohort_id: string, name: string}>>([])
  const [selectedCohort, setSelectedCohort] = useState('')
  const [launching, setLaunching] = useState(false)
  const [launchError, setLaunchError] = useState<string | null>(null)

  // Curve metric switcher — surfaces the full curve payload (was only
  // showing avg_mastery; backend already returns accuracy + avg_delta_m + avg_jt).
  type CurveMetric = 'avg_mastery' | 'accuracy' | 'avg_delta_m' | 'avg_jt'
  const [curveMetric, setCurveMetric] = useState<CurveMetric>('avg_mastery')

  // Leaderboard sort
  type LeaderKey = 'avg_final_mastery' | 'peak_mastery' | 'overall_accuracy' | 'avg_jt'
  const [leaderSort, setLeaderSort] = useState<LeaderKey>('avg_final_mastery')

  // Per-policy chart visibility — lets the user A/B specific policies on the curve.
  // Stored as a Set of HIDDEN policy names so the default (empty set) shows everything.
  const [hiddenPolicies, setHiddenPolicies] = useState<Set<string>>(new Set())

  // When a new run is selected, reset visibility so we don't carry "hidden" flags
  // from a previous run whose policy mix may differ.
  useEffect(() => { setHiddenPolicies(new Set()) }, [runId])

  // ── Load a run's comparison data ────────────────────────────────────────────
  const loadRun = useCallback(async (id: string) => {
    if (!id.trim()) return
    setLoading(true)
    try {
      const res = await fetch(
        `${BACKEND}/v3/frontend/dashboard/cohort-run/${id.trim()}/comparison`,
        { headers: getAuthHeaders(), signal: AbortSignal.timeout(12000) }
      )
      if (res.ok) {
        const d = await res.json()
        setData(d)
        setPolling(d.status === 'running')
      }
    } catch { /* keep previous */ }
    finally { setLoading(false) }
  }, [])

  useEffect(() => {
    if (runId && isAuthenticated && !authLoading) loadRun(runId)
  }, [runId, isAuthenticated, authLoading, loadRun])

  // Load the live synthetic-run index (no hardcoded run IDs)
  useEffect(() => {
    (async () => {
      try {
        const r = await fetch(`${BACKEND}/v3/frontend/dashboard/cohort-runs?group=synthetic`,
          { headers: getAuthHeaders(), signal: AbortSignal.timeout(10000) })
        if (!r.ok) return
        const d = await r.json()
        // newest-first, completed runs surfaced; keep all but sort by completed desc
        const runs = (d.runs ?? []).sort((a: any, b: any) => (b.completed ?? 0) - (a.completed ?? 0))
        setSyntheticRuns(runs)
        // auto-select the richest completed run as the default view
        if (!runId && runs.length) {
          const best = runs.find((x: any) => x.status?.startsWith('completed')) ?? runs[0]
          if (best) setRunId(best.run_id)
        }
      } catch { /* empty */ }
    })()
  }, [])

  // Poll while running
  useEffect(() => {
    if (!polling || !runId) return
    const t = setInterval(() => loadRun(runId), 4000)
    return () => clearInterval(t)
  }, [polling, runId, loadRun])

  // ── Live-cohort fetch (real learners vs synthetic policies) ─────────────────
  const loadLiveCohort = useCallback(async (since?: string, until?: string) => {
    setLiveLoading(true); setLiveErr(null)
    try {
      const qs = new URLSearchParams()
      if (since) qs.set('since', since)
      if (until) qs.set('until', until)
      const res = await fetch(
        `${BACKEND}/v3/frontend/dashboard/live-cohort-comparison?${qs.toString()}`,
        { headers: getAuthHeaders(), signal: AbortSignal.timeout(15000) },
      )
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      setLiveCohort(await res.json())
    } catch (e: any) {
      setLiveErr(String(e?.message ?? e))
    } finally {
      setLiveLoading(false)
    }
  }, [])

  useEffect(() => { loadLiveCohort() }, [loadLiveCohort])

  useEffect(() => {
    if (!runId?.trim()) { setRegretData(null); return }
    fetch(`${BACKEND}/v3/frontend/dashboard/cohort-regret/${encodeURIComponent(runId.trim())}`, {
      headers: getAuthHeaders(), signal: AbortSignal.timeout(15000),
    })
      .then(r => r.ok ? r.json() : null)
      .then(j => setRegretData(j))
      .catch(() => setRegretData(null))
  }, [runId])

  // Live 1s tick for the elapsed timer (only while running)
  useEffect(() => {
    if (data?.status === 'running') {
      tickRef.current = setInterval(() => setTick(t => t + 1), 1000)
      return () => { if (tickRef.current) clearInterval(tickRef.current) }
    }
  }, [data?.status])

  // ── Launcher ────────────────────────────────────────────────────────────────
  const loadCohorts = useCallback(async () => {
    try {
      const res = await fetch(`${BACKEND}/v3/experiments/cohorts`,
        { headers: getAuthHeaders(), signal: AbortSignal.timeout(10000) })
      if (res.ok) {
        const d = await res.json()
        setCohorts(d.cohorts || [])
      }
    } catch { /* empty */ }
  }, [])

  useEffect(() => {
    if (canLaunch && isAuthenticated && !authLoading) loadCohorts()
  }, [canLaunch, isAuthenticated, authLoading, loadCohorts])

  const launch = useCallback(async () => {
    if (!selectedCohort) return
    setLaunching(true); setLaunchError(null)
    try {
      const res = await fetch(`${BACKEND}/v3/experiments/cohorts/${selectedCohort}/launch`,
        { method: 'POST', headers: getAuthHeaders(),
          body: JSON.stringify({ reason: 'launch from cohort study page' }),
          signal: AbortSignal.timeout(15000) })
      if (!res.ok) { setLaunchError(`launch failed: ${res.status}`); return }
      const d = await res.json()
      if (d.run_id) { setRunId(d.run_id); setPolling(true) }
      else setLaunchError('no run_id returned')
    } catch (e: any) { setLaunchError(e?.message || 'network error') }
    finally { setLaunching(false) }
  }, [selectedCohort])

  // ── Derived timer values ──────────────────────────────────────────────────
  const startedAt = data?.started_at ? new Date(data.started_at).getTime() : null
  const completedAt = data?.completed_at ? new Date(data.completed_at).getTime() : null
  const isRunning = data?.status === 'running'
  // Use a fixed "now" only when running; when done use completed_at
  const nowMs = Date.now()
  const elapsedMs = startedAt != null
    ? (completedAt ?? nowMs) - startedAt
    : null
  const completed = data?.progress?.completed ?? 0
  const total = data?.progress?.total ?? 0
  const errors = data?.progress?.errors ?? 0
  const pctDone = total > 0 ? (completed / total) : 0
  // ETA: elapsed / pctDone gives projected total; remaining = projected − elapsed
  const etaMs = (isRunning && pctDone > 0 && elapsedMs != null)
    ? (elapsedMs / pctDone) - elapsedMs
    : null
  const resumed = Boolean(data?.resumed)

  const statusColor = data?.status === 'completed' ? '#27AE60'
    : data?.status === 'completed_with_errors' ? '#1E8449'
    : data?.status === 'running' ? '#E67E22'
    : data?.status === 'failed' || data?.status === 'cancelled' ? '#C0392B' : '#718096'

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: '24px 20px' }}>

      {/* ── INTENT FIRST ─────────────────────────────────────────────────────── */}
      <div style={{ marginBottom: 8 }}>
        <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.1em',
                      color: '#6C3483', textTransform: 'uppercase', marginBottom: 4 }}>
          {t('cohorts.eyebrow')}
        </div>
        <h1 style={{ fontSize: 22, fontWeight: 800, color: '#1A2332', margin: 0 }}>
          {t('cohorts.title')}
        </h1>
      </div>

      {/* Hypothesis card */}
      <div style={{ background: 'linear-gradient(135deg, #F4ECF7, #EBF5FB)',
                    border: '1px solid #D2B4DE', borderRadius: 10,
                    padding: '16px 20px', marginBottom: 14 }}>
        <div style={{ fontSize: 12, fontWeight: 800, color: '#6C3483', marginBottom: 6,
                      textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          {t('cohorts.hypothesisHeader')}
        </div>
        <div style={{ fontSize: 13, color: '#2C3E50', lineHeight: 1.65 }}>
          This is <strong>teaching efficacy</strong> — does a policy raise mastery faster — on
          <strong> IRT-driven synthetic learners</strong>, NOT next-answer prediction on real data
          (that's the <Link href="/dashboard/benchmarks" style={{ color: '#9A7D0A' }}>KT Benchmark</Link>).
          Synthetic learners let us compare all 10 policies under controlled, repeatable conditions.
          {!canLaunch && <span style={{ color: '#718096' }}> Launching new runs requires researcher/admin role.</span>}
        </div>
      </div>

      {/* ── Live Real-Learner cohort vs synthetic policies ─────────────────────── */}
      <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10,
                    padding: '18px 20px', marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'baseline', flexWrap: 'wrap', gap: 12,
                      justifyContent: 'space-between', marginBottom: 6 }}>
          <div>
            <div style={{ fontSize: 13, fontWeight: 800, color: '#1e7d4a' }}>
              Live real learners vs synthetic policies
            </div>
            <div style={{ fontSize: 11.5, color: '#718096', marginTop: 2 }}>
              Every <code>live::</code> attempt grouped as one cohort, compared against the latest synthetic policy runs.
              Same projection, same chart shape — directly comparable.
            </div>
          </div>
          <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
            <label style={{ fontSize: 11, color: '#444' }}>
              Since
              <input type="date" value={liveSince}
                     onChange={e => setLiveSince(e.target.value)}
                     style={{ marginLeft: 4, padding: '3px 6px', border: '1px solid #CBD5E0',
                              borderRadius: 4, fontSize: 12 }} />
            </label>
            <label style={{ fontSize: 11, color: '#444' }}>
              Until
              <input type="date" value={liveUntil}
                     onChange={e => setLiveUntil(e.target.value)}
                     style={{ marginLeft: 4, padding: '3px 6px', border: '1px solid #CBD5E0',
                              borderRadius: 4, fontSize: 12 }} />
            </label>
            <button onClick={() => loadLiveCohort(liveSince || undefined, liveUntil || undefined)}
                    disabled={liveLoading}
                    style={{ padding: '4px 10px', fontSize: 12, fontWeight: 700,
                             background: liveLoading ? '#CBD5E0' : '#1e7d4a', color: '#fff',
                             border: 'none', borderRadius: 4, cursor: liveLoading ? 'wait' : 'pointer' }}>
              {liveLoading ? '…' : 'Apply'}
            </button>
          </div>
        </div>

        {liveErr && (
          <div style={{ fontSize: 11.5, color: '#922', background: '#fff4f4',
                        padding: 8, borderRadius: 4, marginTop: 8 }}>
            {liveErr}
          </div>
        )}

        {liveCohort?.cohorts?.live?.summary && (
          <div style={{ display: 'grid', gap: 10,
                        gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', marginTop: 10 }}>
            <Kpi label="Real learners" value={String(liveCohort.cohorts.live.summary.n_learners)} />
            <Kpi label="Attempts" value={String(liveCohort.cohorts.live.summary.n_attempts)} />
            <Kpi label="Avg mastery" value={(liveCohort.cohorts.live.summary.final_mastery * 100).toFixed(1) + '%'} />
            <Kpi label="Accuracy" value={(liveCohort.cohorts.live.summary.accuracy * 100).toFixed(0) + '%'} />
            <Kpi label="Avg JT" value={liveCohort.cohorts.live.summary.avg_jt.toFixed(3)} />
          </div>
        )}

        {liveCohort?.cohorts?.live?.curve?.length > 0 && (
          <div style={{ height: 220, marginTop: 12 }}>
            <ResponsiveContainer>
              <LineChart>
                <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
                <XAxis type="number" dataKey="step" allowDuplicatedCategory={false}
                       domain={['dataMin', 'dataMax']}
                       label={{ value: 'interaction #', position: 'insideBottomRight', offset: -5, fontSize: 10 }} />
                <YAxis domain={[0, 1]} tickFormatter={(v) => (v * 100).toFixed(0) + '%'} />
                <Tooltip formatter={(v: any) => v != null ? (Number(v) * 100).toFixed(1) + '%' : '—'} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                {/* Live cohort */}
                <Line type="monotone" data={liveCohort.cohorts.live.curve} dataKey="avg_mastery"
                      name="live (real learners)" stroke="#1e7d4a" strokeWidth={3}
                      dot={false} isAnimationActive={false} />
                {/* Synthetic policies overlay */}
                {Object.entries(liveCohort.cohorts.synthetic as Record<string, any[]>).slice(0, 4).map(([label, curve], i) => {
                  const colors = ['#6C3483', '#E67E22', '#1A5276', '#C0392B']
                  return (
                    <Line key={label} type="monotone" data={curve} dataKey="avg_mastery"
                          name={label} stroke={colors[i % colors.length]} strokeDasharray="4 2"
                          dot={false} isAnimationActive={false} />
                  )
                })}
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {liveCohort?.cohorts?.live?.summary?.n_attempts === 0 && (
          <div style={{ fontSize: 12, color: '#718096', marginTop: 10 }}>
            No live attempts in the selected window. Have a learner complete a few tasks on{' '}
            <Link href="/learn" style={{ color: '#1e7d4a' }}>/learn</Link>, or autopilot one from{' '}
            <Link href="/dashboard/instructor" style={{ color: '#1e7d4a' }}>the Cohort tab</Link>.
          </div>
        )}
      </div>

      {/* ── PROVISIONAL banner ─────────────────────────────────────────────────── */}
      <div style={{ background: '#FDEDEC', border: '1px solid #F5B7B1', borderRadius: 10,
                    padding: '14px 18px', marginBottom: 16 }}>
        <div style={{ fontSize: 12, fontWeight: 800, color: '#C0392B', marginBottom: 4 }}>
          {t('cohorts.provisional')}
        </div>
        <div style={{ fontSize: 11.5, color: '#922B21', lineHeight: 1.6 }}>
          {t('cohorts.provisionalBody')}
        </div>
      </div>

      {/* ── Step 1: Pick a run (label-based, no UUID typing) ──────────────────── */}
      <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10,
                    padding: '18px 20px', marginBottom: 16 }}>
        <div style={{ fontSize: 13, fontWeight: 700, color: '#2C3E50', marginBottom: 4 }}>
          {t('cohorts.pickRun')}
        </div>
        <div style={{ fontSize: 11, color: '#718096', marginBottom: 14 }}>
          {t('cohorts.pickRunHint')}
        </div>

        {syntheticRuns.length === 0 && (
          <div style={{ fontSize: 12, color: '#A0AEC0', padding: '12px 0' }}>
            Loading synthetic runs… (none found means no policy sweeps in the DB yet)
          </div>
        )}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: 10 }}>
          {syntheticRuns.slice(0, 12).map((r: any) => {
            const active = runId === r.run_id
            const done = String(r.status ?? '').startsWith('completed')
            return (
              <button key={r.run_id} onClick={() => setRunId(r.run_id)} style={{
                textAlign: 'left', cursor: 'pointer',
                background: active ? '#F4ECF7' : '#fff',
                border: `2px solid ${active ? '#6C3483' : '#E2E8F0'}`,
                borderRadius: 10, padding: '12px 14px', transition: 'all 0.15s',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                  <span style={{ background: '#EBF5FB', color: '#1A5276', borderRadius: 3,
                                 padding: '1px 5px', fontSize: 9, fontWeight: 700 }}>synthetic</span>
                  <span style={{ background: done ? '#D5F5E3' : '#FEF9E7',
                                 color: done ? '#1E8449' : '#9A7D0A', borderRadius: 3,
                                 padding: '1px 5px', fontSize: 9, fontWeight: 700 }}>{r.status}</span>
                </div>
                <div style={{ fontSize: 12, fontWeight: 800, color: '#2C3E50', fontFamily: 'monospace' }}>
                  {r.run_id.slice(0, 18)}…
                </div>
                <div style={{ fontSize: 10, color: '#718096', marginTop: 3, lineHeight: 1.4 }}>
                  {r.completed?.toLocaleString() ?? 0}/{r.total?.toLocaleString() ?? '?'} steps
                  {r.reason ? ` · ${r.reason.slice(0, 40)}` : ''}
                  {r.started_at ? ` · ${r.started_at.slice(0, 10)}` : ''}
                </div>
              </button>
            )
          })}
        </div>
      </div>

      {/* Cross-link to the other experiment (KT prediction benchmark) */}
      <Link href="/dashboard/benchmarks" style={{ textDecoration: 'none' }}>
        <div style={{ background: 'linear-gradient(135deg, #FEF9E7, #FDF2E9)',
                      border: '1px solid #F9E79F', borderRadius: 10,
                      padding: '12px 18px', marginBottom: 16, display: 'flex',
                      alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer' }}>
          <div>
            <div style={{ fontSize: 12, fontWeight: 800, color: '#9A7D0A' }}>
              Looking for the real datasets (Junyi · ASSISTments · EdNet · STATICS · CSEDM)?
            </div>
            <div style={{ fontSize: 11, color: '#7D6008', marginTop: 2 }}>
              Those are a different experiment — KT prediction (HCIE vs BKT/DKT/SAKT). →
            </div>
          </div>
          <span style={{ fontSize: 13, fontWeight: 700, color: '#9A7D0A',
                         background: '#fff', border: '1px solid #F9E79F',
                         borderRadius: 6, padding: '6px 14px', whiteSpace: 'nowrap' }}>
            Open KT Benchmark →
          </span>
        </div>
      </Link>

      {/* ── Launcher (researcher/admin) ──────────────────────────────────────── */}
      {canLaunch && (
        <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10,
                      padding: '18px 20px', marginBottom: 16 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: '#2C3E50', marginBottom: 10 }}>
            {t('cohorts.launchTitle')}
          </div>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
            <select value={selectedCohort} onChange={e => setSelectedCohort(e.target.value)}
              style={{ flex: '1 1 260px', minWidth: 240, padding: '8px 12px', fontSize: 13,
                       border: '1px solid #CBD5E0', borderRadius: 6, background: '#fff' }}>
              <option value="">— select cohort spec —</option>
              {cohorts.map(c => (
                <option key={c.cohort_id} value={c.cohort_id}>{c.name} ({c.cohort_id.slice(0,8)}…)</option>
              ))}
            </select>
            <button onClick={launch} disabled={launching || !selectedCohort}
              style={{ padding: '8px 20px', fontSize: 13, fontWeight: 700,
                       background: launching || !selectedCohort ? '#CBD5E0' : '#27AE60',
                       color: '#fff', border: 'none', borderRadius: 6,
                       cursor: launching || !selectedCohort ? 'default' : 'pointer' }}>
              {launching ? t('cohorts.launchQueueing') : t('cohorts.launchButton')}
            </button>
          </div>
          {launchError && <div style={{ marginTop: 8, fontSize: 12, color: '#C0392B' }}>⚠ {launchError}</div>}
          {cohorts.length === 0 && (
            <div style={{ marginTop: 8, fontSize: 11, color: '#718096' }}>
              No cohort specs found. Create one via POST /v3/experiments/cohorts.
            </div>
          )}
        </div>
      )}

      {/* ── Step 2: Run status + LIVE TIMER + resume indicator ───────────────── */}
      {data && (
        <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10,
                      padding: '18px 20px', marginBottom: 16 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                        marginBottom: 14, flexWrap: 'wrap', gap: 10 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <span style={{ width: 10, height: 10, borderRadius: '50%', background: statusColor,
                             boxShadow: isRunning ? `0 0 0 4px ${statusColor}33` : 'none' }} />
              <span style={{ fontSize: 14, fontWeight: 800, color: statusColor, textTransform: 'capitalize' }}>
                {data.status ?? 'unknown'}
              </span>
              {resumed && (
                <span style={{ fontSize: 10, fontWeight: 700, color: '#7D6008',
                               background: '#FEF9E7', border: '1px solid #F9E79F',
                               borderRadius: 4, padding: '2px 8px' }}>
                  ⟳ Resumed mid-flight
                </span>
              )}
              {isRunning && (
                <span style={{ fontSize: 10, color: '#E67E22', fontWeight: 700 }}>
                  ● polling every 4s
                </span>
              )}
            </div>
            <div style={{ fontSize: 11, color: '#A0AEC0', fontFamily: 'monospace' }}>
              {runId.slice(0, 16)}…
            </div>
          </div>

          {/* TIMER ROW */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
                        gap: 12, marginBottom: 14 }}>
            <div style={{ background: '#F8F9FF', border: '1px solid #C3CFE2', borderRadius: 8, padding: '10px 14px' }}>
              <div style={{ fontSize: 9, fontWeight: 700, color: '#718096', textTransform: 'uppercase' }}>
                {isRunning ? 'Elapsed (live)' : 'Total runtime'}
              </div>
              <div style={{ fontSize: 20, fontWeight: 800, color: '#1A5276', fontVariantNumeric: 'tabular-nums' }}>
                {elapsedMs != null ? fmtDuration(elapsedMs) : '—'}
              </div>
            </div>
            {isRunning && (
              <div style={{ background: '#FEF9E7', border: '1px solid #F9E79F', borderRadius: 8, padding: '10px 14px' }}>
                <div style={{ fontSize: 9, fontWeight: 700, color: '#718096', textTransform: 'uppercase' }}>
                  ETA remaining
                </div>
                <div style={{ fontSize: 20, fontWeight: 800, color: '#9A7D0A', fontVariantNumeric: 'tabular-nums' }}>
                  {etaMs != null ? fmtDuration(etaMs) : '…'}
                </div>
              </div>
            )}
            <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 8, padding: '10px 14px' }}>
              <div style={{ fontSize: 9, fontWeight: 700, color: '#718096', textTransform: 'uppercase' }}>Steps</div>
              <div style={{ fontSize: 20, fontWeight: 800, color: '#2C3E50', fontVariantNumeric: 'tabular-nums' }}>
                {completed}<span style={{ fontSize: 13, color: '#A0AEC0' }}> / {total || '?'}</span>
              </div>
            </div>
            {errors > 0 && (
              <div style={{ background: '#FDEDEC', border: '1px solid #F5B7B1', borderRadius: 8, padding: '10px 14px' }}>
                <div style={{ fontSize: 9, fontWeight: 700, color: '#718096', textTransform: 'uppercase' }}>Errors</div>
                <div style={{ fontSize: 20, fontWeight: 800, color: '#C0392B' }}>{errors}</div>
              </div>
            )}
          </div>

          {/* Progress bar */}
          <div style={{ background: '#EDF2F7', borderRadius: 4, height: 8, overflow: 'hidden' }}>
            <div style={{ height: '100%', borderRadius: 4, transition: 'width 0.4s',
                          background: data.status === 'completed' ? '#27AE60' : '#6C3483',
                          width: `${Math.min(100, pctDone * 100)}%` }} />
          </div>
          <div style={{ marginTop: 6, fontSize: 11, color: '#A0AEC0' }}>
            Policies: {(data.policies ?? []).join(', ') || '—'}
          </div>
        </div>
      )}

      {/* ── Cumulative bandit regret (Contribution B) ─────────────────────────── */}
      {regretData?.policies && Object.keys(regretData.policies).length > 0 && (
        <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10,
                      padding: '18px 20px', marginBottom: 16 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: '#2C3E50', marginBottom: 4 }}>
            Cumulative bandit regret
          </div>
          <div style={{ fontSize: 11, color: '#718096', marginBottom: 12 }}>
            Contribution B — lower is better. Uses candidate_arm_scores when available.
          </div>
          <div style={{ height: 260 }}>
            <ResponsiveContainer>
              <LineChart>
                <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
                <XAxis type="number" dataKey="step" domain={['dataMin', 'dataMax']} />
                <YAxis />
                <Tooltip />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                {Object.entries(regretData.policies as Record<string, any[]>).map(([policy, curve]) => (
                  <Line key={policy} type="monotone" data={curve} dataKey="cumulative" name={policy}
                        stroke={POLICY_COLOR[policy] ?? '#718096'} dot={false} isAnimationActive={false} />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
          {regretData.summary && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10, marginTop: 10, fontSize: 11 }}>
              {Object.entries(regretData.summary as Record<string, any>).map(([p, s]) => (
                <span key={p} style={{ background: '#F7FAFC', padding: '4px 8px', borderRadius: 4, border: '1px solid #E2E8F0' }}>
                  <strong style={{ color: POLICY_COLOR[p] ?? '#333' }}>{p}</strong>: final regret {Number(s.final_cumulative_regret).toFixed(4)}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── Policy leaderboard (rich, sortable) ──────────────────────────────── */}
      {data?.summary && Object.keys(data.summary).length > 0 && (() => {
        // Derive avg ΔM per policy by averaging the per-step deltas in the curve.
        // Backend already returns avg_delta_m per (policy, step); collapse it here.
        const deltaByPolicy: Record<string, number> = {}
        for (const [policy, pts] of Object.entries(data.curves ?? {}) as [string, any[]][]) {
          if (!pts?.length) continue
          const sum = pts.reduce((a, p) => a + (p.avg_delta_m ?? 0), 0)
          deltaByPolicy[policy] = sum / pts.length
        }
        const rows = Object.entries(data.summary as Record<string, any>)
          .map(([policy, s]) => ({ policy, s, avg_delta_m: deltaByPolicy[policy] ?? 0 }))
          .sort((a, b) => {
            const ka = leaderSort === 'avg_jt' ? -(a.s[leaderSort] ?? 0) : (a.s[leaderSort] ?? 0)
            const kb = leaderSort === 'avg_jt' ? -(b.s[leaderSort] ?? 0) : (b.s[leaderSort] ?? 0)
            return kb - ka
          })
        const SortHead = ({ id, label, hint }: { id: LeaderKey, label: string, hint?: string }) => (
          <th onClick={() => setLeaderSort(id)} style={{
            textAlign: 'right', padding: '8px 10px', cursor: 'pointer',
            color: leaderSort === id ? '#6C3483' : '#4A5568',
            fontWeight: 700, fontSize: 11, whiteSpace: 'nowrap',
            borderBottom: '2px solid #E2E8F0', userSelect: 'none',
          }} title={hint}>
            {label} {leaderSort === id && <span style={{ fontSize: 9 }}>▼</span>}
          </th>
        )
        return (
          <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10,
                        padding: '18px 20px', marginBottom: 16, overflowX: 'auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
                          marginBottom: 12, gap: 12, flexWrap: 'wrap' }}>
              <div>
                <div style={{ fontSize: 13, fontWeight: 700, color: '#2C3E50' }}>
                  {t('cohorts.leaderboard')} ({rows.length})
                </div>
                <div style={{ fontSize: 11, color: '#718096', marginTop: 2 }}>
                  {t('cohorts.leaderboardHint')}
                </div>
              </div>
              <div style={{ fontSize: 10, color: '#A0AEC0' }}>
                Total interactions: {rows.reduce((a, r) => a + (r.s.total_interactions ?? 0), 0).toLocaleString()}
              </div>
            </div>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
              <thead>
                <tr>
                  <th style={{ textAlign: 'left', padding: '8px 10px', color: '#4A5568',
                               fontSize: 11, fontWeight: 700, borderBottom: '2px solid #E2E8F0' }}>
                    Rank · Policy
                  </th>
                  <SortHead id="avg_final_mastery" label="Final M" hint="Average final mastery across learners" />
                  <SortHead id="peak_mastery"     label="Peak M"  hint="Max mastery achieved by any learner" />
                  <th style={{ textAlign: 'right', padding: '8px 10px', color: '#4A5568',
                               fontSize: 11, fontWeight: 700, borderBottom: '2px solid #E2E8F0' }}
                      title="Average per-step mastery gain (averaged across all steps in the curve)">
                    ΔM / step
                  </th>
                  <SortHead id="overall_accuracy" label="Accuracy" hint="Fraction correct across all interactions" />
                  <SortHead id="avg_jt"           label="Avg JT"   hint="Mean Justification-Triple value (lower = better calibration)" />
                  <th style={{ textAlign: 'right', padding: '8px 10px', color: '#4A5568',
                               fontSize: 11, fontWeight: 700, borderBottom: '2px solid #E2E8F0' }}>
                    Learners
                  </th>
                  <th style={{ textAlign: 'right', padding: '8px 10px', color: '#4A5568',
                               fontSize: 11, fontWeight: 700, borderBottom: '2px solid #E2E8F0' }}>
                    Interactions
                  </th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row, idx) => {
                  const c = POLICY_COLOR[row.policy] ?? '#4A5568'
                  const isHcie = row.policy === 'hcie'
                  return (
                    <tr key={row.policy} style={{
                      background: isHcie ? '#F4ECF710' : (idx % 2 === 0 ? '#fff' : '#F8F9FB'),
                      borderLeft: isHcie ? `3px solid ${c}` : '3px solid transparent',
                    }}>
                      <td style={{ padding: '10px', whiteSpace: 'nowrap' }}>
                        <span style={{ fontSize: 10, fontWeight: 700, color: '#fff', background: c,
                                       borderRadius: 10, padding: '2px 8px', marginRight: 8 }}>
                          #{idx + 1}
                        </span>
                        <span style={{ fontSize: 12, fontWeight: 800, color: c }}>{row.policy}</span>
                      </td>
                      <td style={{ textAlign: 'right', padding: '10px', fontVariantNumeric: 'tabular-nums', fontWeight: 700, color: c }}>
                        {((row.s.avg_final_mastery ?? 0) * 100).toFixed(1)}%
                      </td>
                      <td style={{ textAlign: 'right', padding: '10px', fontVariantNumeric: 'tabular-nums', color: '#4A5568' }}>
                        {((row.s.peak_mastery ?? 0) * 100).toFixed(1)}%
                      </td>
                      <td style={{ textAlign: 'right', padding: '10px', fontVariantNumeric: 'tabular-nums',
                                   color: row.avg_delta_m >= 0 ? '#1E8449' : '#C0392B', fontWeight: 600 }}>
                        {row.avg_delta_m >= 0 ? '+' : ''}{(row.avg_delta_m * 100).toFixed(2)}%
                      </td>
                      <td style={{ textAlign: 'right', padding: '10px', fontVariantNumeric: 'tabular-nums', color: '#4A5568' }}>
                        {((row.s.overall_accuracy ?? 0) * 100).toFixed(1)}%
                      </td>
                      <td style={{ textAlign: 'right', padding: '10px', fontVariantNumeric: 'tabular-nums', color: '#4A5568' }}>
                        {(row.s.avg_jt ?? 0).toFixed(2)}
                      </td>
                      <td style={{ textAlign: 'right', padding: '10px', fontVariantNumeric: 'tabular-nums', color: '#718096' }}>
                        {row.s.total_learners?.toLocaleString() ?? '—'}
                      </td>
                      <td style={{ textAlign: 'right', padding: '10px', fontVariantNumeric: 'tabular-nums', color: '#718096' }}>
                        {row.s.total_interactions?.toLocaleString() ?? '—'}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )
      })()}

      {/* ── Per-step curve — metric switchable ───────────────────────────────── */}
      {data?.curves && Object.keys(data.curves).length > 0 && (() => {
        const METRICS: Array<{ id: CurveMetric, label: string, hint: string, fmt: (v: number) => string, domain?: [number, number] }> = [
          { id: 'avg_mastery',  label: 'Mastery',    hint: 'Mean mastery across learners at each step',          fmt: v => `${(v*100).toFixed(0)}%`, domain: [0, 1] },
          { id: 'accuracy',     label: 'Accuracy',   hint: 'Fraction of correct responses at each step',          fmt: v => `${(v*100).toFixed(0)}%`, domain: [0, 1] },
          { id: 'avg_delta_m',  label: 'ΔM / step',  hint: 'Per-step mastery gain (>0 = learning, <0 = forgetting)', fmt: v => `${(v*100).toFixed(1)}%` },
          { id: 'avg_jt',       label: 'Avg JT',     hint: 'Justification-Triple value at each step',             fmt: v => v.toFixed(2) },
        ]
        const active = METRICS.find(m => m.id === curveMetric) ?? METRICS[0]
        // Order chips by leaderboard rank so the top-performing policy is first.
        const policyNames = Object.entries(data.summary as Record<string, any> ?? {})
          .sort(([,a],[,b]) => (b.avg_final_mastery ?? 0) - (a.avg_final_mastery ?? 0))
          .map(([p]) => p)
          .filter(p => Array.isArray(data.curves?.[p]) && data.curves[p].length > 0)
        const togglePolicy = (p: string) => {
          setHiddenPolicies(prev => {
            const next = new Set(prev)
            if (next.has(p)) next.delete(p); else next.add(p)
            return next
          })
        }
        const showAll = () => setHiddenPolicies(new Set())
        const showOnlyHcie = () => setHiddenPolicies(new Set(policyNames.filter(p => p !== 'hcie')))
        const allHidden = hiddenPolicies.size >= policyNames.length
        return (
          <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10,
                        padding: '18px 20px', marginBottom: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end',
                          marginBottom: 14, gap: 12, flexWrap: 'wrap' }}>
              <div>
                <div style={{ fontSize: 13, fontWeight: 700, color: '#2C3E50' }}>
                  {t('cohorts.trajectoryTitle')} · {active.label}
                </div>
                <div style={{ fontSize: 11, color: '#718096', marginTop: 2 }}>
                  {active.hint}
                </div>
              </div>
              <div style={{ display: 'flex', gap: 4, background: '#F8F9FB', border: '1px solid #E2E8F0',
                            borderRadius: 6, padding: 3 }}>
                {METRICS.map(m => (
                  <button key={m.id} onClick={() => setCurveMetric(m.id)} style={{
                    padding: '5px 10px', fontSize: 11, fontWeight: 700, cursor: 'pointer',
                    border: 'none', borderRadius: 4,
                    background: curveMetric === m.id ? '#6C3483' : 'transparent',
                    color: curveMetric === m.id ? '#fff' : '#4A5568',
                  }}>
                    {m.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Policy show/hide chip row — A/B any subset by clicking. */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap',
                          marginBottom: 12, padding: '8px 10px', background: '#F8F9FB',
                          border: '1px solid #E2E8F0', borderRadius: 6 }}>
              <span style={{ fontSize: 10, fontWeight: 700, color: '#718096',
                             textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                {t('common.compare')}
              </span>
              {policyNames.map(policy => {
                const c = POLICY_COLOR[policy] ?? '#4A5568'
                const visible = !hiddenPolicies.has(policy)
                return (
                  <button key={policy} onClick={() => togglePolicy(policy)}
                          title={visible ? `Hide ${policy}` : `Show ${policy}`}
                          style={{
                    display: 'inline-flex', alignItems: 'center', gap: 6,
                    padding: '3px 8px', fontSize: 11, fontWeight: 700,
                    cursor: 'pointer', borderRadius: 4,
                    border: `1px solid ${visible ? c : '#CBD5E0'}`,
                    background: visible ? `${c}15` : '#fff',
                    color: visible ? c : '#A0AEC0',
                    textDecoration: visible ? 'none' : 'line-through',
                    transition: 'all 0.12s',
                  }}>
                    <span style={{ width: 8, height: 8, borderRadius: 2,
                                   background: visible ? c : '#CBD5E0',
                                   border: visible ? 'none' : '1px solid #CBD5E0' }} />
                    {policy}
                  </button>
                )
              })}
              <span style={{ flex: 1 }} />
              <button onClick={showAll} disabled={hiddenPolicies.size === 0} style={{
                padding: '3px 10px', fontSize: 10, fontWeight: 700,
                cursor: hiddenPolicies.size === 0 ? 'default' : 'pointer',
                borderRadius: 4, border: '1px solid #CBD5E0',
                background: '#fff', color: hiddenPolicies.size === 0 ? '#CBD5E0' : '#4A5568',
              }}>{t('common.all')}</button>
              <button onClick={showOnlyHcie} style={{
                padding: '3px 10px', fontSize: 10, fontWeight: 700,
                cursor: 'pointer', borderRadius: 4,
                border: '1px solid #6C3483', background: '#F4ECF7', color: '#6C3483',
              }}>{t('common.hcieOnly')}</button>
            </div>

            {allHidden ? (
              <div style={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center',
                            color: '#A0AEC0', fontSize: 12, border: '1px dashed #E2E8F0', borderRadius: 6 }}>
                {t('cohorts.allHidden')}
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart margin={{ left: 0, right: 20, top: 8, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                  <XAxis dataKey="step" type="number" tick={{ fontSize: 10, fill: '#A0AEC0' }}
                         axisLine={false} tickLine={false} />
                  <YAxis domain={active.domain ?? ['auto', 'auto']}
                         tickFormatter={active.fmt}
                         tick={{ fontSize: 10, fill: '#A0AEC0' }} axisLine={false} tickLine={false} />
                  <Tooltip formatter={(v:any,n:any) => [active.fmt(Number(v)), n]}
                           labelFormatter={l => `Step ${l}`} contentStyle={{ fontSize: 11, borderRadius: 6 }} />
                  <Legend wrapperStyle={{ fontSize: 10, paddingTop: 4 }} iconType="line" />
                  {Object.entries(data.curves as Record<string, any[]>)
                    .filter(([policy]) => !hiddenPolicies.has(policy))
                    .map(([policy, pts]) => (
                      <Line key={policy} data={pts} dataKey={curveMetric} name={policy}
                            stroke={POLICY_COLOR[policy] ?? '#4A5568'}
                            strokeWidth={policy === 'hcie' ? 2.5 : 1.5} dot={false} type="monotone" />
                    ))}
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        )
      })()}

      {/* ── Cold-start by archetype (steps 1–5) ──────────────────────────────── */}
      {data?.cold_start && Object.keys(data.cold_start).length > 0 && (() => {
        // Collect every archetype that appears in any policy's cold-start payload.
        const archSet = new Set<string>()
        for (const m of Object.values(data.cold_start as Record<string, any>)) {
          for (const a of Object.keys(m)) archSet.add(a)
        }
        const archetypes = Array.from(archSet).sort((a, b) => a.localeCompare(b))
        // Heatmap cell color — interpolate light → policy color by mastery
        const heatColor = (base: string, m: number) => {
          const pct = Math.max(0, Math.min(1, m))
          const alpha = Math.round((0.10 + pct * 0.55) * 255).toString(16).padStart(2, '0')
          return `${base}${alpha}`
        }
        // Sort policies by best archetype-average so HCIE-vs-baselines reads top-down
        const policyEntries = Object.entries(data.cold_start as Record<string, any>)
          .map(([p, m]) => {
            const vals = archetypes.map(a => (m[a]?.avg_mastery ?? 0))
            const mean = vals.reduce((s, v) => s + v, 0) / Math.max(1, vals.length)
            return { policy: p, m, mean }
          })
          .sort((a, b) => b.mean - a.mean)
        return (
          <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10,
                        padding: '18px 20px', marginBottom: 16, overflowX: 'auto' }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: '#2C3E50' }}>
              {t('cohorts.coldStartTitle')}
            </div>
            <div style={{ fontSize: 11, color: '#718096', marginTop: 2, marginBottom: 12 }}>
              {t('cohorts.coldStartSub')}
            </div>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
              <thead>
                <tr>
                  <th style={{ textAlign: 'left', padding: '8px 10px', borderBottom: '2px solid #E2E8F0',
                               fontSize: 11, fontWeight: 700, color: '#4A5568' }}>Policy</th>
                  {archetypes.map(a => (
                    <th key={a} style={{ textAlign: 'center', padding: '8px 10px',
                                         borderBottom: '2px solid #E2E8F0',
                                         fontSize: 11, fontWeight: 700, color: '#4A5568',
                                         textTransform: 'capitalize' }}>
                      {a}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {policyEntries.map(({ policy, m }) => {
                  const base = POLICY_COLOR[policy] ?? '#4A5568'
                  return (
                    <tr key={policy}>
                      <td style={{ padding: '8px 10px', whiteSpace: 'nowrap', borderBottom: '1px solid #F1F5F9' }}>
                        <span style={{ display: 'inline-block', width: 10, height: 10, borderRadius: 2,
                                       background: base, marginRight: 8, verticalAlign: 'middle' }} />
                        <span style={{ fontSize: 12, fontWeight: 700, color: base }}>{policy}</span>
                      </td>
                      {archetypes.map(a => {
                        const cell = m[a]
                        if (!cell) {
                          return <td key={a} style={{ padding: '8px 10px', textAlign: 'center',
                                                      color: '#CBD5E0', borderBottom: '1px solid #F1F5F9' }}>—</td>
                        }
                        return (
                          <td key={a} style={{ padding: '8px 10px', textAlign: 'center',
                                               borderBottom: '1px solid #F1F5F9',
                                               background: heatColor(base, cell.avg_mastery ?? 0) }}>
                            <div style={{ fontSize: 13, fontWeight: 800, color: '#1A2332',
                                          fontVariantNumeric: 'tabular-nums' }}>
                              {((cell.avg_mastery ?? 0) * 100).toFixed(1)}%
                            </div>
                            <div style={{ fontSize: 9, color: '#4A5568', marginTop: 1 }}>
                              acc {((cell.accuracy ?? 0) * 100).toFixed(0)}% · n={cell.n_learners ?? 0}
                            </div>
                          </td>
                        )
                      })}
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )
      })()}

      {/* ── Concept routing per policy ───────────────────────────────────────── */}
      {data?.concept_distribution && Object.keys(data.concept_distribution).length > 0 && (() => {
        const dist = data.concept_distribution as Record<string, Array<{
          concept: string, n: number, accuracy: number, avg_mastery: number, avg_delta_m: number,
        }>>
        // Order policies the same way as the leaderboard (final mastery desc) for visual continuity.
        const policyOrder = Object.entries(data.summary as Record<string, any>)
          .sort(([,a],[,b]) => (b.avg_final_mastery ?? 0) - (a.avg_final_mastery ?? 0))
          .map(([p]) => p)
          .filter(p => dist[p])
        return (
          <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10,
                        padding: '18px 20px', marginBottom: 16 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: '#2C3E50' }}>
              {t('cohorts.conceptRoutingTitle')}
            </div>
            <div style={{ fontSize: 11, color: '#718096', marginTop: 2, marginBottom: 14 }}>
              {t('cohorts.conceptRoutingSub')}
            </div>
            <div style={{ display: 'grid',
                          gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 12 }}>
              {policyOrder.map(policy => {
                const rows = (dist[policy] ?? []).slice(0, 6)
                if (!rows.length) return null
                const maxN = Math.max(...rows.map(r => r.n), 1)
                const base = POLICY_COLOR[policy] ?? '#4A5568'
                return (
                  <div key={policy} style={{ border: `1px solid ${base}33`,
                                             borderTop: `3px solid ${base}`, borderRadius: 8,
                                             padding: '10px 12px', background: `${base}05` }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between',
                                  alignItems: 'baseline', marginBottom: 8 }}>
                      <span style={{ fontSize: 11, fontWeight: 800, textTransform: 'uppercase',
                                     color: base }}>{policy}</span>
                      <span style={{ fontSize: 10, color: '#A0AEC0' }}>
                        {(dist[policy] ?? []).length} concepts
                      </span>
                    </div>
                    {rows.map(r => {
                      const w = Math.round((r.n / maxN) * 100)
                      const dm = r.avg_delta_m ?? 0
                      return (
                        <div key={r.concept} style={{ marginBottom: 6 }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between',
                                        fontSize: 11, color: '#2C3E50', marginBottom: 2 }}>
                            <span style={{ fontWeight: 600, maxWidth: '60%',
                                           overflow: 'hidden', textOverflow: 'ellipsis',
                                           whiteSpace: 'nowrap' }}
                                  title={conceptLabel(r.concept)}>
                              {conceptLabel(r.concept)}
                            </span>
                            <span style={{ fontVariantNumeric: 'tabular-nums', color: '#718096',
                                           fontSize: 10 }}>
                              {r.n.toLocaleString()} · acc {((r.accuracy ?? 0)*100).toFixed(0)}%
                              · <span style={{ color: dm >= 0 ? '#1E8449' : '#C0392B', fontWeight: 700 }}>
                                  {dm >= 0 ? '+' : ''}{(dm*100).toFixed(1)}%
                                </span>
                            </span>
                          </div>
                          <div style={{ background: '#F1F5F9', borderRadius: 3, height: 6 }}>
                            <div style={{ width: `${w}%`, height: '100%', borderRadius: 3,
                                          background: base, opacity: 0.7 }} />
                          </div>
                        </div>
                      )
                    })}
                  </div>
                )
              })}
            </div>
          </div>
        )
      })()}

      {/* Empty state */}
      {!data && !loading && (
        <div style={{ background: '#fff', border: '1px dashed #CBD5E0', borderRadius: 12,
                      padding: '48px 28px', textAlign: 'center', color: '#A0AEC0' }}>
          <div style={{ fontSize: 36, marginBottom: 12 }}>⚗</div>
          <div style={{ fontSize: 14, fontWeight: 700, color: '#4A5568' }}>No run selected</div>
          <div style={{ fontSize: 12, marginTop: 4 }}>Pick a labeled run above to load its comparison.</div>
        </div>
      )}
      {loading && !data && (
        <div style={{ textAlign: 'center', padding: 40, color: '#718096' }}>⟳ Loading run…</div>
      )}

      {/* Footer nav */}
      <div style={{ display: 'flex', gap: 10, marginTop: 24, justifyContent: 'center' }}>
        <Link href="/dashboard/instructor" style={{ fontSize: 13, fontWeight: 600, color: '#4A5568',
          textDecoration: 'none', padding: '10px 24px', borderRadius: 8,
          border: '1px solid #CBD5E0', background: '#fff' }}>
          {t('cohorts.backToInstructor')}
        </Link>
      </div>
    </div>
  )
}

function Kpi({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ background: '#F8FAF9', border: '1px solid #E2E8F0', borderRadius: 6, padding: 10 }}>
      <div style={{ fontSize: 10, color: '#718096', textTransform: 'uppercase', letterSpacing: 0.5 }}>
        {label}
      </div>
      <div style={{ fontSize: 18, fontWeight: 800, color: '#1e7d4a', marginTop: 4 }}>
        {value}
      </div>
    </div>
  )
}
