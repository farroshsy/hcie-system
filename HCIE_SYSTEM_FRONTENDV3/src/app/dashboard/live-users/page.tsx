'use client'

/**
 * Live-user experiment surface.
 *
 * Visualizes the registered HUMAN learners that hit /v3/learner/* through the
 * ITS — the small but real signal that mirrors the science the rest of the
 * dashboard layer presents on synthetic + dataset-import users.
 *
 * Data (all live, no fabrication):
 *   GET /v3/frontend/dashboard/system-stats?traffic_type=human    aggregate
 *   GET /v3/frontend/dashboard/learner-cohort                     per-user (filter human)
 *   GET /v3/frontend/dashboard/challenge-distribution?traffic_type=human  difficulty
 *
 * PROVISIONAL: N is small (demo cohort) until the live-user run-type seals.
 */

import { useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import { getBackendUrl } from '@/lib/api/backend-url'
import { useT } from '@/contexts/language_context'

const BACKEND = getBackendUrl()

type SystemStats = {
  status?: string
  // `interactions.*` is whole-table (NOT filtered by traffic_type — verified
  // against backend dashboard.py: only the trajectories block honors the
  // traffic filter). Use trajectories.* for human-only counts.
  interactions?: {
    total?: number
    unique_users?: number
    unique_concepts?: number
    avg_correct?: number
    first_interaction?: string | null
    last_interaction?: string | null
  }
  trajectories?: { total?: number; users_with_trajectories?: number }
  active_sessions?: number
}

type Learner = {
  user_id: string
  short_id?: string
  learner_type?: string
  dataset?: string
  n_interactions: number
  avg_mastery: number
  accuracy: number
  concepts_visited: number
  first_mastery?: number
  last_mastery?: number
  improvement?: number
  traffic_type: string
  last_seen?: string | null
}

type CohortResponse = {
  status?: string
  learners?: Learner[]
  total?: number
}

type DifficultyResponse = {
  status?: string
  distribution?: Array<{ label: string; count: number; avg_correct: number; range: string }>
}

function authHeaders(): HeadersInit {
  const token = typeof window !== 'undefined'
    ? (localStorage.getItem('hcie_auth_token') || localStorage.getItem('access_token'))
    : null
  return token
    ? { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }
    : { 'Content-Type': 'application/json' }
}

function fmtDateTime(s?: string | null): string {
  if (!s) return '—'
  try {
    const d = new Date(s.replace(' ', 'T') + (s.endsWith('Z') ? '' : 'Z'))
    if (isNaN(d.getTime())) return s
    return d.toISOString().slice(0, 16).replace('T', ' ') + ' UTC'
  } catch {
    return s
  }
}

function masteryColor(v: number): string {
  if (v >= 0.7) return '#1E8449'
  if (v >= 0.45) return '#E67E22'
  return '#C0392B'
}

export default function LiveUsersPage() {
  const t = useT()
  const [stats, setStats] = useState<SystemStats | null>(null)
  const [cohort, setCohort] = useState<Learner[] | null>(null)
  const [difficulty, setDifficulty] = useState<DifficultyResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    Promise.allSettled([
      fetch(`${BACKEND}/v3/frontend/dashboard/system-stats?traffic_type=human`,
        { headers: authHeaders(), signal: AbortSignal.timeout(12000) }).then(r => r.ok ? r.json() : null),
      fetch(`${BACKEND}/v3/frontend/dashboard/learner-cohort?limit=100`,
        { headers: authHeaders(), signal: AbortSignal.timeout(12000) }).then(r => r.ok ? r.json() : null),
      fetch(`${BACKEND}/v3/frontend/dashboard/challenge-distribution?traffic_type=human`,
        { headers: authHeaders(), signal: AbortSignal.timeout(8000) }).then(r => r.ok ? r.json() : null),
    ]).then(results => {
      if (cancelled) return
      const [statsRes, cohortRes, diffRes] = results
      if (statsRes.status === 'fulfilled' && statsRes.value) setStats(statsRes.value as SystemStats)
      if (cohortRes.status === 'fulfilled' && cohortRes.value) {
        const c = cohortRes.value as CohortResponse
        const humans = (c.learners ?? []).filter(l => l.traffic_type === 'human')
        setCohort(humans)
      }
      if (diffRes.status === 'fulfilled' && diffRes.value) setDifficulty(diffRes.value as DifficultyResponse)
      const anyOk = results.some(r => r.status === 'fulfilled' && r.value)
      if (!anyOk) setError('Live-user endpoints unreachable. Make sure you are signed in.')
      setLoading(false)
    })
    return () => { cancelled = true }
  }, [])

  const sorted = useMemo(() => {
    if (!cohort) return []
    return [...cohort].sort((a, b) => (b.n_interactions ?? 0) - (a.n_interactions ?? 0))
  }, [cohort])

  // Human-only counts come from trajectories.* (traffic-filtered server-side);
  // interactions.* is the global whole-table aggregate (NOT human-only) so we
  // do not surface it here — it would lie about cohort size.
  const humanAttempts = stats?.trajectories?.total ?? 0
  const humanLearners = stats?.trajectories?.users_with_trajectories ?? sorted.length
  const activeSessions = stats?.active_sessions ?? 0
  const cohortAvgMastery = sorted.length
    ? sorted.reduce((s, l) => s + (l.avg_mastery || 0), 0) / sorted.length
    : 0
  const cohortAvgAccuracy = sorted.length
    ? sorted.reduce((s, l) => s + (l.accuracy || 0), 0) / sorted.length
    : 0
  const cohortConcepts = sorted.reduce(
    (max, l) => Math.max(max, l.concepts_visited || 0), 0,
  )

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: '24px 20px' }}>

      {/* Header / intent */}
      <div style={{ marginBottom: 12 }}>
        <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.1em',
                      color: '#117A65', textTransform: 'uppercase', marginBottom: 4 }}>
          {t('liveUsers.title')}
        </div>
        <h1 style={{ fontSize: 22, fontWeight: 800, color: '#1A2332', margin: 0 }}>
          {t('liveUsers.headline', 'Real humans on the live ITS — does the science replicate on registered learners?')}
        </h1>
        <p style={{ fontSize: 13, color: '#4A5568', marginTop: 6, maxWidth: 760, lineHeight: 1.55 }}>
          {t('liveUsers.intro', 'The benchmark and policy studies use dataset-import / synthetic learners. This page is the small but real-traffic mirror: every row below is a registered human who ran the live recommend → attempt → mastery loop. The point is checking that the same authority chain works on real users.')}
        </p>
      </div>

      {/* PROVISIONAL — small-N until live-user run-type seals */}
      <div style={{ background: '#FDEDEC', border: '1px solid #F5B7B1', borderRadius: 10,
                    padding: '12px 16px', marginBottom: 16 }}>
        <div style={{ fontSize: 10, fontWeight: 800, color: '#C0392B', textTransform: 'uppercase',
                      letterSpacing: '0.06em', marginBottom: 4 }}>
          ⚠ Provisional · small-N demo cohort
        </div>
        <div style={{ fontSize: 12, color: '#922B21', lineHeight: 1.5 }}>
          The Option-2 sealed re-run includes a dedicated <strong>live-user</strong> run type.
          Until it seals, this page shows whoever has hit the ITS so far (demo accounts +
          you). Treat the trends as a sanity check on the pipeline, not as a result.
        </div>
      </div>

      {error && (
        <div style={{ background: '#FEF9E7', border: '1px solid #F9E79F', borderRadius: 8,
                      padding: '10px 14px', marginBottom: 16, fontSize: 12, color: '#7D6008' }}>
          {error}
        </div>
      )}

      {/* KPI strip — all counts are human-traffic only (server-filtered) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
                    gap: 10, marginBottom: 20 }}>
        <Stat label={t('liveUsers.kpiLiveLearners')} value={humanLearners} color="#117A65"
              hint={loading ? t('common.loading') : `${sorted.length} surfaced below · traffic=human`} />
        <Stat label={t('liveUsers.kpiHumanAttempts')} value={humanAttempts.toLocaleString()} color="#1A5276"
              hint="experiment_trajectories · traffic=human" />
        <Stat label="Active (last 5 min)" value={activeSessions} color="#9A7D0A"
              hint="experiment_trajectories — global, not human-only" />
        <Stat label="Max concepts / learner" value={cohortConcepts} color="#6C3483"
              hint="largest per-learner concept set in cohort" />
        <Stat label="Cohort avg mastery" value={`${(cohortAvgMastery * 100).toFixed(0)}%`}
              color={masteryColor(cohortAvgMastery)} hint="per-learner avg, then averaged" />
        <Stat label="Cohort avg accuracy" value={`${(cohortAvgAccuracy * 100).toFixed(0)}%`}
              color="#4A235A" hint="per-learner attempt accuracy" />
      </div>

      {/* Difficulty distribution */}
      {difficulty?.distribution && difficulty.distribution.length > 0 && (
        <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10,
                      padding: '16px 20px', marginBottom: 16 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: '#2C3E50', marginBottom: 2 }}>
            Difficulty distribution — human attempts
          </div>
          <div style={{ fontSize: 11, color: '#718096', marginBottom: 12 }}>
            ⚠ Most human Kafka rows lack a difficulty value, so this is sparse — included for shape, not as a primary signal.
          </div>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            {difficulty.distribution.map(b => (
              <div key={b.label} style={{ flex: '1 1 130px', background: '#F8FAFC',
                                          border: '1px solid #E2E8F0', borderRadius: 8, padding: '10px 12px' }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: '#1A5276' }}>{b.label}</div>
                <div style={{ fontSize: 10, color: '#718096' }}>{b.range}</div>
                <div style={{ fontSize: 18, fontWeight: 800, color: '#2C3E50', marginTop: 4 }}>{b.count}</div>
                <div style={{ fontSize: 10, color: '#4A5568' }}>
                  acc {(b.avg_correct * 100).toFixed(0)}%
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Learner table */}
      <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10,
                    padding: '16px 20px', marginBottom: 16, overflowX: 'auto' }}>
        <div style={{ fontSize: 13, fontWeight: 700, color: '#2C3E50', marginBottom: 2 }}>
          Live learners — ordered by attempt count
        </div>
        <div style={{ fontSize: 11, color: '#718096', marginBottom: 12 }}>
          One row per registered human · click <em>Profile →</em> to open their dashboard trace.
          {loading && ' · loading…'}
        </div>
        {sorted.length === 0 && !loading && (
          <div style={{ fontSize: 12, color: '#A0AEC0', padding: '12px 0' }}>
            No human-traffic learners found yet. Register a demo account from <Link href="/register"
            style={{ color: '#1A5276' }}>/register</Link> or hit the live ITS at <Link href="/learn"
            style={{ color: '#1A5276' }}>/learn</Link>.
          </div>
        )}
        {sorted.length > 0 && (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #E2E8F0' }}>
                {['Learner', 'Attempts', 'Concepts', 'Accuracy', 'Avg mastery', 'Improvement', 'Last seen', ''].map(h => (
                  <th key={h} style={{ padding: '6px 10px', textAlign: h === 'Learner' || h === '' ? 'left' : 'right',
                                       color: '#718096', fontWeight: 700, fontSize: 11 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sorted.map(l => {
                const imp = l.improvement ?? ((l.last_mastery ?? 0) - (l.first_mastery ?? 0))
                const impColor = imp > 0.02 ? '#1E8449' : imp < -0.02 ? '#C0392B' : '#718096'
                return (
                  <tr key={l.user_id} style={{ borderBottom: '1px solid #F7FAFC' }}>
                    <td style={{ padding: '8px 10px', fontFamily: 'monospace', color: '#1A2332' }}>
                      {l.short_id ?? l.user_id.slice(0, 12)}
                      <div style={{ fontSize: 10, color: '#A0AEC0', fontWeight: 400 }}>
                        {l.learner_type ?? 'human'}
                      </div>
                    </td>
                    <td style={{ padding: '8px 10px', textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
                      {l.n_interactions}
                    </td>
                    <td style={{ padding: '8px 10px', textAlign: 'right' }}>{l.concepts_visited}</td>
                    <td style={{ padding: '8px 10px', textAlign: 'right',
                                 color: l.accuracy >= 0.7 ? '#1E8449' : l.accuracy >= 0.4 ? '#E67E22' : '#C0392B' }}>
                      {(l.accuracy * 100).toFixed(0)}%
                    </td>
                    <td style={{ padding: '8px 10px', textAlign: 'right',
                                 color: masteryColor(l.avg_mastery), fontWeight: 700 }}>
                      {(l.avg_mastery * 100).toFixed(0)}%
                    </td>
                    <td style={{ padding: '8px 10px', textAlign: 'right', color: impColor,
                                 fontVariantNumeric: 'tabular-nums' }}>
                      {imp >= 0 ? '+' : ''}{(imp * 100).toFixed(1)}pp
                    </td>
                    <td style={{ padding: '8px 10px', textAlign: 'right', color: '#718096', fontSize: 11 }}>
                      {fmtDateTime(l.last_seen)}
                    </td>
                    <td style={{ padding: '8px 10px' }}>
                      <Link href={`/dashboard/learner?user_id=${encodeURIComponent(l.user_id)}`}
                            style={{ fontSize: 11, fontWeight: 700, color: '#1A5276', textDecoration: 'none' }}>
                        Profile →
                      </Link>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* Footer nav */}
      <div style={{ display: 'flex', gap: 10, marginTop: 24, justifyContent: 'center', flexWrap: 'wrap' }}>
        <Link href="/dashboard" style={{ fontSize: 13, fontWeight: 600, color: '#4A5568',
          textDecoration: 'none', padding: '10px 24px', borderRadius: 8,
          border: '1px solid #CBD5E0', background: '#fff' }}>
          ← Dashboard
        </Link>
        <Link href="/dashboard/cohorts" style={{ fontSize: 13, fontWeight: 700, color: '#6C3483',
          textDecoration: 'none', padding: '10px 24px', borderRadius: 8,
          border: '1px solid #D2B4DE', background: '#F5EEF8' }}>
          ⚗ Cohort Study (synthetic) →
        </Link>
        <Link href="/dashboard/instructor" style={{ fontSize: 13, fontWeight: 700, color: '#1A5276',
          textDecoration: 'none', padding: '10px 24px', borderRadius: 8,
          border: '1px solid #AED6F1', background: '#EBF5FB' }}>
          🏫 Instructor Dashboard →
        </Link>
      </div>
    </div>
  )
}

function Stat({ label, value, color, hint }: { label: string; value: any; color: string; hint?: string }) {
  return (
    <div style={{ background: `${color}0D`, border: `1px solid ${color}40`, borderRadius: 8,
                  padding: '10px 14px' }}>
      <div style={{ fontSize: 9, fontWeight: 700, color: '#718096', textTransform: 'uppercase',
                    letterSpacing: '0.06em' }}>
        {label}
      </div>
      <div style={{ fontSize: 20, fontWeight: 800, color }}>{value}</div>
      {hint && <div style={{ fontSize: 10, color: '#A0AEC0', marginTop: 2 }}>{hint}</div>}
    </div>
  )
}
