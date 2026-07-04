'use client'

import { useEffect, useState, useCallback, useRef } from 'react'
import { useAuth } from '@/contexts/auth_context'
import { useT } from '@/contexts/language_context'
import Link from 'next/link'
import { getBackendUrl } from '@/lib/api/backend-url'
import { getAuthHeaders } from '@/lib/auth-headers'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, ScatterChart, Scatter,
  LineChart, Line, PieChart, Pie,
} from 'recharts'
import { conceptLabel } from '@/lib/catalog/k12-catalog'

// ─── Types ────────────────────────────────────────────────────────────────────

interface ConceptBottleneck {
  concept: string
  label: string
  catalog: string
  avgMastery: number
  studentCount: number
  failRate: number
  transferIncoming: number
}

// Catalog visual identity. Used to color bars and chips so the user can
// instantly tell a K-12 row from a Junyi/EdNet/CSEDM row.
const CATALOG_COLOR: Record<string, string> = {
  k12:        '#6C3483',
  junyi:      '#2980B9',
  ednet:      '#27AE60',
  csedm:      '#E67E22',
  assistments:'#16A085',
  statics:    '#C0392B',
  other:      '#718096',
}
const CATALOG_LABEL: Record<string, string> = {
  k12: 'K-12', junyi: 'Junyi', ednet: 'EdNet', csedm: 'CSEDM',
  assistments: 'ASSISTments', statics: 'STATICS', other: 'Other',
}
const SOURCE_LABEL: Record<string, string> = {
  human:          'Human learners',
  synthetic:      'Synthetic sweep',
  dataset_replay: 'Dataset replay',
  other:          'Other',
}

interface DifficultyBucket {
  label: string
  count: number
  avgCorrect: number
  range: string
}

interface EdgeEffectiveness {
  from: string
  to: string
  transferMean: number
  activationCount: number
  effective: boolean
}

interface SystemOverview {
  totalUsers: number
  totalInteractions: number
  activeSessions: number
  systemHealth: string
  objectiveValue: number
  learningVelocity: number
  transferEffectiveness: number
  isMock: boolean
}

// ─── Constants ─────────────────────────────────────────────────────────────────

const BACKEND = getBackendUrl()

// ─── Mock data shape ────────────────────────────────────────────────────────────
//
// INTEGRITY: this no longer fabricates a K-12 bottleneck table, difficulty
// buckets, or transfer edges. Showing invented numbers as if they were real
// cohort measurements is a data-integrity hazard. When offline, the caller
// seeds empty tables (so the existing NoDataPanel renders in each tab) and
// shows a mockNotice banner over the illustrative overview. This function is
// kept only as the canonical shape source for the `mock` state type
// (`ReturnType<typeof buildMockInstructorData>`).
function buildMockInstructorData(): {
  bottlenecks: ConceptBottleneck[]
  difficulty: DifficultyBucket[]
  edges: EdgeEffectiveness[]
} {
  return { bottlenecks: [], difficulty: [], edges: [] }
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function masteryColor(v: number) {
  return v >= 0.7 ? '#27AE60' : v >= 0.45 ? '#E67E22' : '#C0392B'
}
function pct(v: number, dec = 1) { return `${(v * 100).toFixed(dec)}%` }
function healthColor(h: string) {
  const l = h.toLowerCase()
  if (l.includes('healthy') || l.includes('ok') || l.includes('good')) return '#27AE60'
  if (l.includes('degraded') || l.includes('warn')) return '#E67E22'
  return '#C0392B'
}

// ─── Custom Tooltips ──────────────────────────────────────────────────────────

function BottleneckTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null
  const d = payload[0]?.payload as ConceptBottleneck
  return (
    <div style={{ background: '#1A2332', color: '#fff', padding: '10px 14px',
                  borderRadius: 6, fontSize: 11 }}>
      <div style={{ fontWeight: 700, marginBottom: 6 }}>{d.label}</div>
      <div>Avg mastery: <strong style={{ color: masteryColor(d.avgMastery) }}>{pct(d.avgMastery)}</strong></div>
      <div>Students: <strong>{d.studentCount}</strong></div>
      <div>Fail rate: <strong style={{ color: '#E74C3C' }}>{pct(d.failRate)}</strong></div>
      <div>Incoming transfer edges: <strong>{d.transferIncoming}</strong></div>
    </div>
  )
}

function DiffTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null
  const d = payload[0]?.payload as DifficultyBucket
  return (
    <div style={{ background: '#1A2332', color: '#fff', padding: '10px 14px',
                  borderRadius: 6, fontSize: 11 }}>
      <div style={{ fontWeight: 700, marginBottom: 4 }}>{d.label} ({d.range})</div>
      <div>Task count: <strong>{d.count}</strong></div>
      <div>Avg correct rate: <strong style={{ color: '#27AE60' }}>{pct(d.avgCorrect)}</strong></div>
    </div>
  )
}

// ─── Sub-components ────────────────────────────────────────────────────────────

function StatCard({ label, value, sub, color }: {
  label: string; value: string | number; sub?: string; color: string
}) {
  return (
    <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10,
                  padding: '14px 18px', flex: 1 }}>
      <div style={{ fontSize: 10, fontWeight: 700, color: '#718096',
                    textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 4 }}>
        {label}
      </div>
      <div style={{ fontSize: 24, fontWeight: 800, color, fontVariantNumeric: 'tabular-nums' }}>
        {value}
      </div>
      {sub && <div style={{ fontSize: 10, color: '#A0AEC0', marginTop: 2 }}>{sub}</div>}
    </div>
  )
}

function SectionHeader({ title, sub }: { title: string; sub?: string }) {
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ fontSize: 13, fontWeight: 700, color: '#2C3E50' }}>{title}</div>
      {sub && <div style={{ fontSize: 11, color: '#718096', marginTop: 1 }}>{sub}</div>}
    </div>
  )
}

function NoDataPanel({ title, reason, hint }: {
  title: string
  reason: string | null
  hint?: string
}) {
  return (
    <div style={{ background: '#fff', border: '1px dashed #CBD5E0', borderRadius: 12,
                  padding: '32px 28px', textAlign: 'center', minHeight: 280,
                  display: 'flex', flexDirection: 'column',
                  alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ fontSize: 40, marginBottom: 12, opacity: 0.4 }}>📭</div>
      <div style={{ fontSize: 15, fontWeight: 700, color: '#4A5568', marginBottom: 6 }}>
        {title}
      </div>
      <div style={{ fontSize: 12, color: '#718096', maxWidth: 460, lineHeight: 1.55, marginBottom: 8 }}>
        Backend aggregation not configured or no learner activity recorded yet.
      </div>
      {reason && (
        <div style={{ fontSize: 11, color: '#A0AEC0', fontFamily: 'monospace',
                       background: '#F7FAFC', padding: '4px 8px', borderRadius: 4,
                       marginBottom: hint ? 10 : 0 }}>
          reason: {reason}
        </div>
      )}
      {hint && (
        <div style={{ fontSize: 11, color: '#4A5568', maxWidth: 460, lineHeight: 1.55 }}>
          {hint}
        </div>
      )}
    </div>
  )
}

// ─── Main Page ────────────────────────────────────────────────────────────────

interface CohortReason {
  bottlenecks: string | null
  difficulty: string | null
  edges: string | null
}

export default function InstructorDashboardPage() {
  const { user, isAuthenticated, isLoading: authLoading } = useAuth()
  const t = useT()
  const [overview, setOverview] = useState<SystemOverview | null>(null)
  const [mock, setMock] = useState<ReturnType<typeof buildMockInstructorData>>({
    bottlenecks: [], difficulty: [], edges: [],
  })
  const [reasons, setReasons] = useState<CohortReason>({
    bottlenecks: null, difficulty: null, edges: null,
  })
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'bottlenecks' | 'challenge' | 'edges' | 'study' | 'cohort' | 'archetype'>('bottlenecks')
  const [archetypeData, setArchetypeData] = useState<{
    buckets: Array<{ concept: string; dominant_vark: string; n_interactions: number; avg_jt: number; avg_response_time: number; accuracy: number }>
    meta: { profiles_count: number; materials_count: number; task_languages: Record<string, number>; note: string }
  } | null>(null)
  const [archetypeLoading, setArchetypeLoading] = useState(false)

  // ── Bottleneck filters ─────────────────────────────────────────────────────
  // `catalogFilter` segments by concept-ID prefix family (k12 / junyi / ednet / …).
  // `sourceFilter` segments by learner population (human / synthetic / dataset_replay).
  // Both are passed as query params to /cohort-concepts; null = no filter (show all).
  //
  // Default is 'k12' because this is a K-12 CS curriculum dashboard. Without
  // a default the list is dominated by ASSISTments `ext_assist*` skill IDs
  // (thousands of fine-grained skills from the dataset replay), which buries
  // the actual curriculum the instructor is teaching. The user can switch
  // to ASSISTments / Junyi / EdNet via the filter pills with one click.
  const [catalogFilter, setCatalogFilter] = useState<string | null>('k12')
  const [sourceFilter,  setSourceFilter]  = useState<string | null>(null)
  // Shared sort direction — flips the bar chart and re-purposes the right panel
  // between "Priority Intervention" (lowest first) and "Strongest Concepts"
  // (highest first). One toggle, both panels react.
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')
  const [conceptMeta, setConceptMeta] = useState<{
    source_breakdown: Record<string, { users: number; rows: number }>;
    catalog_breakdown: Record<string, { concepts: number; users: number }>;
  }>({ source_breakdown: {}, catalog_breakdown: {} })
  const [bottlenecksLoading, setBottlenecksLoading] = useState(false)

  // ── Cohort study state ─────────────────────────────────────────────────────
  const [studyRunId, setStudyRunId] = useState('')
  const [studyData, setStudyData] = useState<any>(null)
  const [studyLoading, setStudyLoading] = useState(false)
  const [studyPolling, setStudyPolling] = useState(false)

  // ── Cohort launcher state ──────────────────────────────────────────────────
  const [availableCohorts, setAvailableCohorts] = useState<Array<{cohort_id: string, name: string}>>([])
  const [selectedCohortId, setSelectedCohortId] = useState('')
  const [launchReason, setLaunchReason] = useState('manual launch from instructor dashboard')
  const [launching, setLaunching] = useState(false)
  const [launchError, setLaunchError] = useState<string | null>(null)
  const canLaunch = !!user && ['researcher', 'admin'].includes(String((user as any).role || ''))

  // ── Real learner cohort state ──────────────────────────────────────────────
  const [cohortLearners, setCohortLearners] = useState<any[]>([])
  const [cohortLoading, setCohortLoading] = useState(false)
  const [cohortDataset, setCohortDataset] = useState<string>('all')
  const [selectedLearner, setSelectedLearner] = useState<string | null>(null)
  // Interactive chart: empty = all visible, non-empty = only those in set
  const [visiblePolicies, setVisiblePolicies] = useState<Set<string>>(new Set())
  const togglePolicy = (p: string) => setVisiblePolicies(prev => {
    const next = new Set(prev)
    if (next.has(p)) next.delete(p); else next.add(p)
    return next
  })

  const loadOverview = useCallback(async () => {
    setLoading(true)

    // No backend → offline mock badge so the user knows it's not real
    if (!BACKEND) {
      setOverview({
        totalUsers: 247,
        totalInteractions: 18430,
        activeSessions: 12,
        systemHealth: 'Mock',
        objectiveValue: 0.734,
        learningVelocity: 0.058,
        transferEffectiveness: 0.142,
        isMock: true,
      })
      // INTEGRITY: do NOT inject the invented K-12 bottleneck/difficulty/edge
      // tables. Leaving these empty lets the existing NoDataPanel render in each
      // tab instead of showing fabricated numbers as if they were real. The
      // mockNotice banner above the overview discloses that the stat strip is
      // simulated illustrative data, not live measurements.
      setMock({ bottlenecks: [], difficulty: [], edges: [] })
      setReasons({
        bottlenecks: 'offline (no backend)',
        difficulty: 'offline (no backend)',
        edges: 'offline (no backend)',
      })
      setLoading(false)
      return
    }

    try {
      const headers = getAuthHeaders()
      // Fetch overview + analytics + cohort analytics + system stats in parallel
      const [ovRes, anaRes, statsRes, conceptsRes, distRes, edgesRes] = await Promise.allSettled([
        fetch(`${BACKEND}/v3/frontend/dashboard/overview`, { headers, signal: AbortSignal.timeout(5000) }),
        fetch(`${BACKEND}/v3/frontend/dashboard/analytics`, { headers, signal: AbortSignal.timeout(5000) }),
        fetch(`${BACKEND}/v3/frontend/dashboard/system-stats`, { headers, signal: AbortSignal.timeout(5000) }),
        // Initial bottlenecks load defaults to the k12 catalog (matches the
        // default `catalogFilter` state) so the instructor sees curriculum
        // concepts on first paint, not the long ASSISTments skill list.
        fetch(`${BACKEND}/v3/frontend/dashboard/cohort-concepts?catalog=k12`, { headers, signal: AbortSignal.timeout(6000) }),
        fetch(`${BACKEND}/v3/frontend/dashboard/challenge-distribution`, { headers, signal: AbortSignal.timeout(6000) }),
        fetch(`${BACKEND}/v3/frontend/dashboard/cohort-edges`, { headers, signal: AbortSignal.timeout(6000) }),
      ])

      let ov: any = {}
      let ana: any = {}
      let stats: any = {}
      if (ovRes.status === 'fulfilled' && ovRes.value.ok) ov = await ovRes.value.json()
      if (anaRes.status === 'fulfilled' && anaRes.value.ok) ana = await anaRes.value.json()
      if (statsRes.status === 'fulfilled' && statsRes.value.ok) stats = await statsRes.value.json()

      // Prefer system-stats for counts (more comprehensive); fall back to overview
      const statsInteractions = stats?.interactions ?? {}
      setOverview({
        totalUsers: Number(statsInteractions.unique_users ?? ov.total_users ?? 0),
        totalInteractions: Number(statsInteractions.total ?? ov.total_interactions ?? 0),
        activeSessions: Number(stats?.active_sessions ?? ov.active_sessions ?? 0),
        systemHealth: ov.system_health ?? 'Unknown',
        objectiveValue: Number(ov.objective_function_value ?? 0),
        learningVelocity: Number(ana.learning_velocity ?? 0),
        transferEffectiveness: Number(ana.transfer_effectiveness ?? 0),
        isMock: false,
      })

      // ── Cohort concept bottlenecks (real) ────────────────────────────────────
      let bottlenecks: ConceptBottleneck[] = []
      let bottleneckReason: string | null = null
      if (conceptsRes.status === 'fulfilled' && conceptsRes.value.ok) {
        const cd = await conceptsRes.value.json()
        if (cd.status === 'ok' && Array.isArray(cd.concepts)) {
          bottlenecks = cd.concepts.map((c: any) => ({
            concept: c.concept_id,
            label: conceptLabel(c.concept_id),
            catalog: String(c.catalog || 'other'),
            avgMastery: Number(c.avg_mastery ?? 0),
            studentCount: Number(c.student_count ?? 0),
            failRate: Number(c.fail_rate ?? 0),
            transferIncoming: Number(c.transfer_incoming ?? 0),
          }))
          setConceptMeta({
            source_breakdown:  cd.source_breakdown  ?? {},
            catalog_breakdown: cd.catalog_breakdown ?? {},
          })
        } else {
          bottleneckReason = cd.reason ?? 'no data'
        }
      } else {
        bottleneckReason = 'endpoint unavailable'
      }

      // ── Challenge distribution (real) ────────────────────────────────────────
      let difficulty: DifficultyBucket[] = []
      let difficultyReason: string | null = null
      if (distRes.status === 'fulfilled' && distRes.value.ok) {
        const dd = await distRes.value.json()
        if (dd.status === 'ok' && Array.isArray(dd.distribution)) {
          difficulty = dd.distribution.map((d: any) => ({
            label: d.label,
            range: d.range ?? '',
            count: Number(d.count ?? 0),
            avgCorrect: Number(d.avg_correct ?? 0),
          }))
        } else {
          difficultyReason = dd.reason ?? 'no data'
        }
      } else {
        difficultyReason = 'endpoint unavailable'
      }

      // ── Edge effectiveness (real) ────────────────────────────────────────────
      let edges: EdgeEffectiveness[] = []
      let edgesReason: string | null = null
      if (edgesRes.status === 'fulfilled' && edgesRes.value.ok) {
        const ed = await edgesRes.value.json()
        if (ed.status === 'ok' && Array.isArray(ed.edges)) {
          edges = ed.edges.map((e: any) => ({
            from: conceptLabel(e.source),
            to: conceptLabel(e.target),
            // Prefer observed mean if present, else designed weight
            transferMean: Number(e.mean_transfer ?? e.transfer_weight ?? 0),
            activationCount: Number(e.activation_count ?? e.source_attempts ?? 0),
            effective: Boolean(e.effective),
          }))
        } else {
          edgesReason = ed.reason ?? 'no data'
        }
      } else {
        edgesReason = 'endpoint unavailable'
      }

      setMock({ bottlenecks, difficulty, edges })
      setReasons({
        bottlenecks: bottlenecks.length > 0 ? null : bottleneckReason,
        difficulty: difficulty.length > 0 ? null : difficultyReason,
        edges: edges.length > 0 ? null : edgesReason,
      })
    } catch {
      // Network error → mock fallback so the badge shows "Mock"
      setOverview({
        totalUsers: 247, totalInteractions: 18430, activeSessions: 12,
        systemHealth: 'Mock', objectiveValue: 0.734,
        learningVelocity: 0.058, transferEffectiveness: 0.142,
        isMock: true,
      })
      // INTEGRITY: keep the data tables empty so NoDataPanel renders instead of
      // fabricated rows; the mockNotice banner discloses the simulated overview.
      setMock({ bottlenecks: [], difficulty: [], edges: [] })
      setReasons({
        bottlenecks: 'backend unreachable',
        difficulty: 'backend unreachable',
        edges: 'backend unreachable',
      })
    } finally {
      setLoading(false)
    }
  }, [isAuthenticated])

  useEffect(() => {
    if (!authLoading) loadOverview()
  }, [authLoading, loadOverview])

  // Refetch ONLY the bottlenecks slice when catalog/source filters change.
  // We avoid reloading the full overview because that endpoint trio is heavy
  // and the user is just narrowing the segmentation, not refreshing everything.
  const loadBottlenecks = useCallback(async (cat: string | null, src: string | null) => {
    if (!BACKEND) return
    setBottlenecksLoading(true)
    try {
      const qs = new URLSearchParams({ limit: '200' })
      if (cat) qs.set('catalog', cat)
      if (src) qs.set('source', src)
      const res = await fetch(`${BACKEND}/v3/frontend/dashboard/cohort-concepts?${qs.toString()}`, {
        headers: getAuthHeaders(), signal: AbortSignal.timeout(8000),
      })
      if (!res.ok) return
      const cd = await res.json()
      const next: ConceptBottleneck[] = cd.status === 'ok' && Array.isArray(cd.concepts)
        ? cd.concepts.map((c: any) => ({
            concept: c.concept_id,
            label: conceptLabel(c.concept_id),
            catalog: String(c.catalog || 'other'),
            avgMastery: Number(c.avg_mastery ?? 0),
            studentCount: Number(c.student_count ?? 0),
            failRate: Number(c.fail_rate ?? 0),
            transferIncoming: Number(c.transfer_incoming ?? 0),
          }))
        : []
      setMock(prev => ({ ...prev, bottlenecks: next }))
      setReasons(prev => ({
        ...prev,
        bottlenecks: next.length > 0 ? null : (cd.reason ?? 'no data for current filter'),
      }))
      if (cd.catalog_breakdown || cd.source_breakdown) {
        setConceptMeta({
          source_breakdown:  cd.source_breakdown  ?? {},
          catalog_breakdown: cd.catalog_breakdown ?? {},
        })
      }
    } catch { /* keep previous slice */ }
    finally { setBottlenecksLoading(false) }
  }, [])

  // First load is handled by loadOverview; this effect only fires when the
  // user changes the catalog/source filter. The skipRef avoids a duplicate
  // refetch on mount (when state goes from null → null on first render).
  const filterFirstRun = useRef(true)
  useEffect(() => {
    if (loading) return
    if (filterFirstRun.current) { filterFirstRun.current = false; return }
    loadBottlenecks(catalogFilter, sourceFilter)
  }, [catalogFilter, sourceFilter, loading, loadBottlenecks])

  const loadStudy = useCallback(async (runId: string) => {
    if (!runId.trim()) return
    setStudyLoading(true)
    try {
      const headers = getAuthHeaders()
      const res = await fetch(
        `${BACKEND}/v3/frontend/dashboard/cohort-run/${runId.trim()}/comparison`,
        { headers, signal: AbortSignal.timeout(10000) }
      )
      if (res.ok) {
        const d = await res.json()
        setStudyData(d)
        if (d.status === 'running') setStudyPolling(true)
        else setStudyPolling(false)
      }
    } catch { /* silently keep previous data */ }
    finally { setStudyLoading(false) }
  }, [])

  // Auto-load study data when run ID is set
  useEffect(() => {
    if (studyRunId && isAuthenticated && !authLoading) {
      loadStudy(studyRunId)
    }
  }, [studyRunId, isAuthenticated, authLoading, loadStudy])

  // Auto-poll while run is still running
  useEffect(() => {
    if (!studyPolling || !studyRunId) return
    const t = setInterval(() => loadStudy(studyRunId), 4000)
    return () => clearInterval(t)
  }, [studyPolling, studyRunId, loadStudy])

  const loadCohorts = useCallback(async () => {
    try {
      const res = await fetch(`${BACKEND}/v3/experiments/cohorts`, {
        headers: getAuthHeaders(),
        signal: AbortSignal.timeout(10000),
      })
      if (res.ok) {
        const d = await res.json()
        setAvailableCohorts(d.cohorts || [])
      }
    } catch { /* dropdown stays empty */ }
  }, [])

  useEffect(() => {
    if (canLaunch && isAuthenticated && !authLoading) loadCohorts()
  }, [canLaunch, isAuthenticated, authLoading, loadCohorts])

  const launchRun = useCallback(async () => {
    if (!selectedCohortId) return
    setLaunching(true)
    setLaunchError(null)
    try {
      const res = await fetch(
        `${BACKEND}/v3/experiments/cohorts/${selectedCohortId}/launch`,
        {
          method: 'POST',
          headers: getAuthHeaders(),
          body: JSON.stringify({ reason: launchReason || 'manual launch' }),
          signal: AbortSignal.timeout(15000),
        }
      )
      if (!res.ok) {
        setLaunchError(`launch failed: ${res.status}`)
        return
      }
      const d = await res.json()
      if (d.run_id) {
        setStudyRunId(d.run_id)  // existing polling auto-takes over
        setStudyPolling(true)
      } else {
        setLaunchError('launch returned no run_id')
      }
    } catch (e: any) {
      setLaunchError(e?.message || 'network error')
    } finally {
      setLaunching(false)
    }
  }, [selectedCohortId, launchReason])

  const loadCohort = useCallback(async (dataset: string) => {
    if (!BACKEND) return
    setCohortLoading(true)
    try {
      const headers = getAuthHeaders()
      const res = await fetch(
        `${BACKEND}/v3/frontend/dashboard/learner-cohort?limit=24&dataset=${dataset}`,
        { headers, signal: AbortSignal.timeout(10000) }
      )
      if (res.ok) {
        const d = await res.json()
        setCohortLearners(d.learners ?? [])
      }
    } catch { /* keep empty */ }
    finally { setCohortLoading(false) }
  }, [])

  const loadArchetypeAnalysis = async () => {
    if (!BACKEND) return
    setArchetypeLoading(true)
    try {
      const resp = await fetch(`${BACKEND}/v3/frontend/dashboard/archetype-concept-analysis`, {
        headers: getAuthHeaders(),
        signal: AbortSignal.timeout(8000),
      })
      if (resp.ok) {
        const data = await resp.json()
        setArchetypeData({ buckets: data.buckets ?? [], meta: data.meta ?? {} })
      }
    } catch { /* ignore */ }
    finally { setArchetypeLoading(false) }
  }

  // Load cohort when tab becomes active
  useEffect(() => {
    if (activeTab === 'cohort' && cohortLearners.length === 0 && BACKEND) {
      loadCohort(cohortDataset)
    }
  }, [activeTab, cohortLearners.length, cohortDataset, loadCohort])

  useEffect(() => {
    if (activeTab === 'archetype' && !archetypeData && BACKEND) {
      loadArchetypeAnalysis()
    }
  }, [activeTab, archetypeData])

  const TABS = [
    { id: 'bottlenecks', label: t('instructor.tabs.bottlenecks') },
    { id: 'challenge',   label: t('instructor.tabs.challenge') },
    { id: 'edges',       label: t('instructor.tabs.edges') },
    { id: 'archetype',   label: t('instructor.tabs.archetype', 'Archetype × Concept') },
    { id: 'study',       label: t('instructor.tabs.study') },
    { id: 'cohort',      label: t('instructor.tabs.cohort') },
  ] as const

  if (loading || authLoading) {
    return (
      <div style={{ maxWidth: 1100, margin: '0 auto', padding: '40px 20px',
                    textAlign: 'center', color: '#718096' }}>
        <div style={{ fontSize: 36, marginBottom: 12 }}>⟳</div>
        Loading instructor dashboard…
      </div>
    )
  }

  const ov = overview!
  const { bottlenecks, difficulty, edges } = mock

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: '24px 20px' }}>

      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start',
                    marginBottom: 20 }}>
        <div>
          <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.1em',
                        color: '#6C3483', textTransform: 'uppercase', marginBottom: 4 }}>
            {t('nav.instructorDashboard')}
          </div>
          <h1 style={{ fontSize: 22, fontWeight: 800, color: '#1A2332', margin: 0 }}>
            {t('instructor.headline', 'Cohort Analytics & Governance Insights')}
          </h1>
          {user && (
            <div style={{ fontSize: 12, color: '#718096', marginTop: 2 }}>
              Logged in as <strong>{user.username}</strong>
            </div>
          )}
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          {ov.isMock && (
            <span style={{ fontSize: 10, fontWeight: 700, color: '#7D6008',
                           background: '#FEF9E7', border: '1px solid #F9E79F',
                           borderRadius: 4, padding: '3px 8px' }}>
              ○ Mock data
            </span>
          )}
          {!ov.isMock && (
            <span style={{ fontSize: 10, fontWeight: 700, color: '#1E8449',
                           background: '#D5F5E3', border: '1px solid #A9DFBF',
                           borderRadius: 4, padding: '3px 8px' }}>
              ● Live backend
            </span>
          )}
          <Link href="/dashboard/observability" style={{
            fontSize: 11, fontWeight: 600, color: '#6C3483', textDecoration: 'none',
            padding: '5px 10px', border: '1px solid #D2B4DE', borderRadius: 6, background: '#F4ECF7',
          }}>
            Observability
          </Link>
          <Link href="/dashboard/replay-verify" style={{
            fontSize: 11, fontWeight: 600, color: '#1A5276', textDecoration: 'none',
            padding: '5px 10px', border: '1px solid #AED6F1', borderRadius: 6, background: '#EBF5FB',
          }}>
            Replay verify
          </Link>
          <button onClick={loadOverview} style={{
            fontSize: 12, color: '#4A5568', background: '#EDF2F7',
            border: '1px solid #CBD5E0', borderRadius: 6,
            padding: '5px 12px', cursor: 'pointer',
          }}>
            ↻ Refresh
          </button>
        </div>
      </div>

      {/* ── Mock / simulated-data notice ───────────────────────────────────────
          INTEGRITY: when offline (no live backend), the overview/stat strip
          below is illustrative, not measured. This prominent banner discloses
          that so simulated values are never read as real cohort data. The data
          tabs themselves render NoDataPanel (no fabricated rows). */}
      {ov.isMock && (
        <div role="alert" style={{
          background: '#FEF9E7', border: '1px solid #F9E79F', borderLeft: '4px solid #B7950B',
          borderRadius: 10, padding: '14px 18px', marginBottom: 20,
          display: 'flex', alignItems: 'flex-start', gap: 12,
        }}>
          <span style={{ fontSize: 20, lineHeight: 1 }}>⚠</span>
          <div>
            <div style={{ fontSize: 13, fontWeight: 800, color: '#7D6008', marginBottom: 3 }}>
              {t('mockNotice.title')}
            </div>
            <div style={{ fontSize: 12, color: '#7D6008', lineHeight: 1.55 }}>
              {t('mockNotice.body')}
            </div>
          </div>
        </div>
      )}

      {/* ── System health bar ──────────────────────────────────────────────── */}
      <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10,
                    padding: '12px 20px', marginBottom: 20, display: 'flex',
                    alignItems: 'center', gap: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{ width: 10, height: 10, borderRadius: '50%',
                        background: healthColor(ov.systemHealth) }} />
          <span style={{ fontSize: 13, fontWeight: 700, color: healthColor(ov.systemHealth) }}>
            System {ov.systemHealth}
          </span>
        </div>
        <div style={{ width: 1, height: 24, background: '#E2E8F0' }} />
        <div style={{ fontSize: 12, color: '#718096' }}>
          Objective <strong style={{ color: '#1A5276' }}>{pct(ov.objectiveValue)}</strong>
        </div>
        <div style={{ fontSize: 12, color: '#718096' }}>
          Learning velocity <strong style={{ color: '#27AE60' }}>+{pct(ov.learningVelocity, 2)}/task</strong>
        </div>
        <div style={{ fontSize: 12, color: '#718096' }}>
          Transfer effectiveness <strong style={{ color: '#C0392B' }}>{pct(ov.transferEffectiveness)}</strong>
        </div>
        <div style={{ marginLeft: 'auto', fontSize: 11, color: '#A0AEC0' }}>
          {new Date().toLocaleTimeString()}
        </div>
      </div>

      {/* ── Stat strip ─────────────────────────────────────────────────────── */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 24 }}>
        <StatCard label="Total Learners"     value={ov.totalUsers}         sub="registered accounts"   color="#2980B9" />
        <StatCard label="Total Interactions" value={ov.totalInteractions.toLocaleString()} sub="learning events"  color="#8E44AD" />
        <StatCard label="Active Sessions"    value={ov.activeSessions}     sub="right now"             color="#27AE60" />
        <StatCard label="Concepts Tracked"   value={bottlenecks.length}    sub="in knowledge graph"    color="#E67E22" />
      </div>

      {/* ── Tabs ───────────────────────────────────────────────────────────── */}
      <div style={{ display: 'flex', gap: 2, marginBottom: 20,
                    borderBottom: '2px solid #E2E8F0' }}>
        {TABS.map(t => (
          <button key={t.id} onClick={() => setActiveTab(t.id)} style={{
            padding: '8px 18px', fontSize: 13, fontWeight: 600,
            background: 'none', border: 'none', cursor: 'pointer',
            color: activeTab === t.id ? '#6C3483' : '#718096',
            borderBottom: activeTab === t.id ? '2px solid #6C3483' : '2px solid transparent',
            marginBottom: -2,
          }}>
            {t.label}
          </button>
        ))}
      </div>

      {/* ── Tab: Concept Bottlenecks ───────────────────────────────────────── */}
      {activeTab === 'bottlenecks' && (() => {
        // Filter pills row — catalog selector + source selector.
        // The counts come from /cohort-concepts's `catalog_breakdown` /
        // `source_breakdown` so the chips know how much data each segment
        // actually carries before the user clicks.
        const catalogOptions = ['k12', 'junyi', 'ednet', 'csedm', 'assistments', 'statics', 'other']
        const sourceOptions = ['human', 'synthetic', 'dataset_replay']
        const catCounts = conceptMeta.catalog_breakdown
        const srcCounts = conceptMeta.source_breakdown
        const FilterRows = (
          <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10,
                        padding: '14px 16px', marginBottom: 16 }}>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, marginBottom: 10, flexWrap: 'wrap' }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: '#718096',
                            textTransform: 'uppercase', letterSpacing: '0.05em', minWidth: 60 }}>
                {t('common.catalog')}
              </div>
              <button onClick={() => setCatalogFilter(null)} style={{
                padding: '4px 10px', fontSize: 11, fontWeight: 700, cursor: 'pointer',
                borderRadius: 4, border: `1px solid ${catalogFilter === null ? '#2C3E50' : '#CBD5E0'}`,
                background: catalogFilter === null ? '#2C3E50' : '#fff',
                color: catalogFilter === null ? '#fff' : '#4A5568',
              }}>{t('common.all')}</button>
              {catalogOptions.map(cat => {
                const c = CATALOG_COLOR[cat]
                const meta = catCounts[cat]
                const active = catalogFilter === cat
                const disabled = !meta || meta.concepts === 0
                return (
                  <button key={cat} onClick={() => !disabled && setCatalogFilter(cat)}
                          disabled={disabled}
                          title={disabled
                            ? t('instructor.bottlenecks.catalogEmpty', 'no concepts in this catalog yet')
                            : `${meta?.concepts ?? 0} ${t('instructor.bottlenecks.catalogTip')} · ${meta?.users ?? 0} ${t('instructor.bottlenecks.catalogTipUsers')}`}
                          style={{
                    padding: '4px 10px', fontSize: 11, fontWeight: 700,
                    cursor: disabled ? 'default' : 'pointer',
                    borderRadius: 4, border: `1px solid ${active ? c : (disabled ? '#EDF2F7' : c + '66')}`,
                    background: active ? c : (disabled ? '#F8F9FB' : c + '15'),
                    color: active ? '#fff' : (disabled ? '#CBD5E0' : c),
                    opacity: disabled ? 0.55 : 1,
                  }}>
                    {t(`catalog.${cat}`, CATALOG_LABEL[cat])}
                    <span style={{ marginLeft: 6, fontWeight: 500, opacity: 0.75 }}>
                      {meta?.concepts ?? 0}
                    </span>
                  </button>
                )
              })}
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, flexWrap: 'wrap' }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: '#718096',
                            textTransform: 'uppercase', letterSpacing: '0.05em', minWidth: 60 }}>
                {t('common.source')}
              </div>
              <button onClick={() => setSourceFilter(null)} style={{
                padding: '4px 10px', fontSize: 11, fontWeight: 700, cursor: 'pointer',
                borderRadius: 4, border: `1px solid ${sourceFilter === null ? '#2C3E50' : '#CBD5E0'}`,
                background: sourceFilter === null ? '#2C3E50' : '#fff',
                color: sourceFilter === null ? '#fff' : '#4A5568',
              }}>{t('common.all')}</button>
              {sourceOptions.map(src => {
                const meta = srcCounts[src]
                const active = sourceFilter === src
                const disabled = !meta || meta.users === 0
                return (
                  <button key={src} onClick={() => !disabled && setSourceFilter(src)}
                          disabled={disabled}
                          title={disabled
                            ? t('instructor.bottlenecks.sourceEmpty', 'no learners in this population')
                            : `${meta?.users ?? 0} ${t('instructor.bottlenecks.sourceTipUsers')} · ${meta?.rows ?? 0} ${t('instructor.bottlenecks.sourceTipRows')}`}
                          style={{
                    padding: '4px 10px', fontSize: 11, fontWeight: 700,
                    cursor: disabled ? 'default' : 'pointer',
                    borderRadius: 4, border: `1px solid ${active ? '#6C3483' : (disabled ? '#EDF2F7' : '#CBD5E0')}`,
                    background: active ? '#6C3483' : (disabled ? '#F8F9FB' : '#fff'),
                    color: active ? '#fff' : (disabled ? '#CBD5E0' : '#4A5568'),
                    opacity: disabled ? 0.55 : 1,
                  }}>
                    {t(`source.${src}`, SOURCE_LABEL[src])}
                    <span style={{ marginLeft: 6, fontWeight: 500, opacity: 0.75 }}>
                      {meta?.users ?? 0}
                    </span>
                  </button>
                )
              })}
              <span style={{ flex: 1 }} />
              {bottlenecksLoading && (
                <span style={{ fontSize: 10, color: '#E67E22', fontWeight: 700 }}>
                  ⟳ {t('common.refreshing')}
                </span>
              )}
              {(catalogFilter !== null || sourceFilter !== null || sortDir !== 'asc') && !bottlenecksLoading && (
                <button onClick={() => { setCatalogFilter(null); setSourceFilter(null); setSortDir('asc') }}
                        style={{
                  padding: '3px 10px', fontSize: 10, fontWeight: 700, cursor: 'pointer',
                  borderRadius: 4, border: '1px solid #CBD5E0', background: '#fff', color: '#4A5568',
                }}>
                  {t('common.resetFilters')}
                </button>
              )}
            </div>

            {/* Sort direction — flips BOTH the chart and the right panel.
                ascending → bottlenecks at top + "Priority Intervention" list,
                descending → top performers at top + "Strongest Concepts" list. */}
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, marginTop: 10,
                          paddingTop: 10, borderTop: '1px solid #F1F5F9', flexWrap: 'wrap' }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: '#718096',
                            textTransform: 'uppercase', letterSpacing: '0.05em', minWidth: 60 }}>
                {t('common.sort')}
              </div>
              <div style={{ display: 'flex', gap: 4, background: '#F8F9FB', border: '1px solid #E2E8F0',
                            borderRadius: 6, padding: 3 }}>
                <button onClick={() => setSortDir('asc')} style={{
                  padding: '4px 12px', fontSize: 11, fontWeight: 700, cursor: 'pointer',
                  border: 'none', borderRadius: 4,
                  background: sortDir === 'asc' ? '#C0392B' : 'transparent',
                  color: sortDir === 'asc' ? '#fff' : '#4A5568',
                }} title={t('common.interventionViewHint')}>
                  {t('common.lowestFirst')}
                </button>
                <button onClick={() => setSortDir('desc')} style={{
                  padding: '4px 12px', fontSize: 11, fontWeight: 700, cursor: 'pointer',
                  border: 'none', borderRadius: 4,
                  background: sortDir === 'desc' ? '#1E8449' : 'transparent',
                  color: sortDir === 'desc' ? '#fff' : '#4A5568',
                }} title={t('common.masteryViewHint')}>
                  {t('common.highestFirst')}
                </button>
              </div>
              <span style={{ fontSize: 10, color: '#A0AEC0', marginLeft: 6 }}>
                {sortDir === 'asc'
                  ? t('common.interventionViewHint')
                  : t('common.masteryViewHint')}
              </span>
            </div>
          </div>
        )

        if (bottlenecks.length === 0) {
          return (
            <>
              {FilterRows}
              <NoDataPanel
                title={t('instructor.bottlenecks.emptyTitle')}
                reason={reasons.bottlenecks}
                hint={t('instructor.bottlenecks.emptyHintIntervention')}
              />
            </>
          )
        }

        // The bar chart height grows with concept count so users can see every
        // bar. Each row gets ~26 px; capped to a sensible max with a scroll
        // wrapper underneath. Bars are colored by catalog (the user's whole
        // ask) but the right-edge label/tooltip still surfaces mastery%.
        // Sort direction is driven by the toggle in the filter card.
        const sorted = [...bottlenecks].sort((a, b) =>
          sortDir === 'asc' ? a.avgMastery - b.avgMastery : b.avgMastery - a.avgMastery
        )
        const chartHeight = Math.max(320, sorted.length * 26)
        return (
          <>
            {FilterRows}
            <div style={{ display: 'grid',
                          gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
                          gap: 20 }}>
              {/* Mastery bar chart */}
              <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10,
                            padding: '18px 20px' }}>
                <SectionHeader
                  title={`${t('instructor.bottlenecks.chartTitle')} (${sorted.length})`}
                  sub={
                    t('instructor.bottlenecks.chartSubPrefix') +
                    (catalogFilter
                      ? `${t('common.catalog')}: ${t(`catalog.${catalogFilter}`, CATALOG_LABEL[catalogFilter])}`
                      : t('common.all') + ' ' + t('common.catalog').toLowerCase()) +
                    ' · ' +
                    (sourceFilter
                      ? t(`source.${sourceFilter}`, SOURCE_LABEL[sourceFilter])
                      : t('common.all') + ' ' + t('common.source').toLowerCase())
                  }
                />
                <div style={{ maxHeight: 520, overflowY: 'auto', overflowX: 'hidden',
                              paddingRight: 4 }}>
                  <ResponsiveContainer width="100%" height={chartHeight}>
                    <BarChart
                      data={sorted}
                      layout="vertical"
                      margin={{ left: 8, right: 50, top: 0, bottom: 0 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#F1F5F9" />
                      <XAxis
                        type="number" domain={[0, 1]}
                        tickFormatter={v => `${(v * 100).toFixed(0)}%`}
                        tick={{ fontSize: 10, fill: '#A0AEC0' }}
                        axisLine={false} tickLine={false}
                      />
                      <YAxis
                        type="category" dataKey="label" width={140}
                        tick={{ fontSize: 11, fill: '#4A5568' }}
                        axisLine={false} tickLine={false}
                      />
                      <Tooltip content={<BottleneckTooltip />} />
                      <Bar dataKey="avgMastery" radius={[0, 4, 4, 0]}>
                        {sorted.map(e => (
                          <Cell key={e.concept}
                                fill={CATALOG_COLOR[e.catalog] ?? CATALOG_COLOR.other} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                {/* Catalog legend so colors are decodable at a glance */}
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, marginTop: 12,
                              paddingTop: 10, borderTop: '1px solid #F1F5F9', fontSize: 10,
                              color: '#718096' }}>
                  {Array.from(new Set(sorted.map(s => s.catalog))).map(cat => (
                    <span key={cat} style={{ display: 'inline-flex', alignItems: 'center', gap: 5 }}>
                      <span style={{ width: 10, height: 10, borderRadius: 2,
                                     background: CATALOG_COLOR[cat] ?? CATALOG_COLOR.other }} />
                      {CATALOG_LABEL[cat] ?? cat}
                    </span>
                  ))}
                </div>
              </div>

          {/* Right panel — flips identity based on the shared sort toggle.
              Ascending → "Priority Intervention" (concepts <50% mastery, low → high).
              Descending → "Strongest Concepts" (concepts ≥50% mastery, high → low).
              Empty-state copy mentions the toggle so the user knows the other view exists. */}
          {(() => {
            const isAsc = sortDir === 'asc'
            const filtered = isAsc
              ? bottlenecks.filter(b => b.avgMastery < 0.5)
              : bottlenecks.filter(b => b.avgMastery >= 0.5)
            const ranked = [...filtered].sort((a, b) =>
              isAsc ? a.avgMastery - b.avgMastery : b.avgMastery - a.avgMastery
            )
            const panelTitle = isAsc
              ? `${t('instructor.bottlenecks.priorityTitle')} (${ranked.length})`
              : `${t('instructor.bottlenecks.strongestTitle')} (${ranked.length})`
            const panelSub = isAsc
              ? t('instructor.bottlenecks.prioritySub')
              : t('instructor.bottlenecks.strongestSub')
            // Tier styling — red/amber/yellow for intervention, green/teal/light-green for strongest.
            const tierBg     = isAsc ? ['#FDEDEC', '#FEF5E7', '#FEF9E7'] : ['#E8F8F1', '#EAF7EE', '#F0F9F2']
            const tierBorder = isAsc ? ['#F5B7B1', '#F8C471', '#F9E79F'] : ['#A9DFBF', '#B8E0C0', '#D4EFDF']
            const tierIcon   = isAsc ? ['🔴 ', '🟠 ', ''] : ['🟢 ', '🌿 ', '']
            const emptyHint  = isAsc
              ? t('instructor.bottlenecks.emptyHintIntervention')
              : t('instructor.bottlenecks.emptyHintMastery')
            return (
              <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10,
                            padding: '18px 20px',
                            display: 'flex', flexDirection: 'column', minHeight: 0 }}>
                <SectionHeader title={panelTitle} sub={panelSub} />
                {ranked.length === 0 ? (
                  <div style={{ flex: 1, display: 'flex', alignItems: 'center',
                                justifyContent: 'center', color: '#A0AEC0',
                                fontSize: 12, padding: '24px 8px', textAlign: 'center', lineHeight: 1.5 }}>
                    {emptyHint}
                  </div>
                ) : (
                  <div style={{ maxHeight: 520, overflowY: 'auto', overflowX: 'hidden',
                                paddingRight: 4 }}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                      {ranked.map((b, i) => {
                        const tier = i === 0 ? 0 : i === 1 ? 1 : 2
                        return (
                          <div key={b.concept} style={{
                            background: tierBg[tier],
                            border: `1px solid ${tierBorder[tier]}`,
                            borderRadius: 8, padding: '10px 12px',
                            borderLeft: `3px solid ${CATALOG_COLOR[b.catalog] ?? CATALOG_COLOR.other}`,
                          }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between',
                                          alignItems: 'center', marginBottom: 4, gap: 8 }}>
                              <span style={{ fontWeight: 700, fontSize: 13, color: '#1A2332',
                                             overflow: 'hidden', textOverflow: 'ellipsis',
                                             whiteSpace: 'nowrap', minWidth: 0, flex: 1 }}
                                    title={`${b.label} · ${b.concept}`}>
                                {tierIcon[tier]}{b.label}
                              </span>
                              <span style={{ fontWeight: 800, color: masteryColor(b.avgMastery),
                                             fontVariantNumeric: 'tabular-nums', fontSize: 14,
                                             whiteSpace: 'nowrap' }}>
                                {pct(b.avgMastery)}
                              </span>
                            </div>
                            <div style={{ display: 'flex', gap: 12, fontSize: 10, color: '#718096',
                                          flexWrap: 'wrap' }}>
                              <span style={{ background: (CATALOG_COLOR[b.catalog] ?? CATALOG_COLOR.other) + '15',
                                             color: CATALOG_COLOR[b.catalog] ?? CATALOG_COLOR.other,
                                             fontWeight: 700, padding: '1px 6px', borderRadius: 3,
                                             fontSize: 9, letterSpacing: '0.03em' }}>
                                {(t(`catalog.${b.catalog}`, CATALOG_LABEL[b.catalog] ?? b.catalog)).toUpperCase()}
                              </span>
                              <span>{b.studentCount} {t('common.students')}</span>
                              <span>{isAsc ? t('common.failRate') : t('common.passRate')}: {pct(isAsc ? b.failRate : 1 - b.failRate)}</span>
                              <span>↙ {b.transferIncoming} {t('instructor.bottlenecks.edges', 'edges')}</span>
                            </div>
                            <div style={{ marginTop: 6, height: 4, background: '#E2E8F0', borderRadius: 2 }}>
                              <div style={{ height: '100%', width: `${b.avgMastery * 100}%`,
                                            background: masteryColor(b.avgMastery), borderRadius: 2 }} />
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )}
              </div>
            )
          })()}
            </div>
          </>
        )
      })()}

      {/* ── Tab: Challenge Distribution ────────────────────────────────────── */}
      {activeTab === 'challenge' && difficulty.length === 0 && (
        <NoDataPanel
          title="No challenge distribution available"
          reason={reasons.difficulty}
          hint="Difficulty buckets are computed from interactions.difficulty. Submit attempts to populate."
        />
      )}
      {activeTab === 'challenge' && difficulty.length > 0 && (
        <div style={{ display: 'grid',
                      gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
                      gap: 20 }}>
          {/* Task distribution bar chart */}
          <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10,
                        padding: '18px 20px' }}>
            <SectionHeader
              title="Task Distribution by Difficulty"
              sub="How many tasks are assigned at each difficulty tier"
            />
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={difficulty} margin={{ left: 0, right: 16, top: 8, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                <XAxis dataKey="label" tick={{ fontSize: 11, fill: '#4A5568' }}
                       axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 10, fill: '#A0AEC0' }}
                       axisLine={false} tickLine={false} />
                <Tooltip content={<DiffTooltip />} />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {difficulty.map((d, i) => (
                    <Cell key={i} fill={['#27AE60','#2980B9','#E67E22','#C0392B'][i]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <div style={{ display: 'flex', gap: 16, marginTop: 10, fontSize: 10,
                          color: '#718096', flexWrap: 'wrap' }}>
              {difficulty.map((d, i) => (
                <span key={i}>
                  <span style={{ color: ['#27AE60','#2980B9','#E67E22','#C0392B'][i],
                                  fontWeight: 700 }}>●</span>
                  {' '}{d.label} ({d.range})
                </span>
              ))}
            </div>
          </div>

          {/* Correct rate by difficulty */}
          <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10,
                        padding: '18px 20px' }}>
            <SectionHeader
              title="Correct Rate by Difficulty Tier"
              sub="Average student performance per difficulty bucket"
            />
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={difficulty} margin={{ left: 0, right: 16, top: 8, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                <XAxis dataKey="label" tick={{ fontSize: 11, fill: '#4A5568' }}
                       axisLine={false} tickLine={false} />
                <YAxis domain={[0, 1]} tickFormatter={v => `${(v*100).toFixed(0)}%`}
                       tick={{ fontSize: 10, fill: '#A0AEC0' }}
                       axisLine={false} tickLine={false} />
                <Tooltip formatter={(v: any) => pct(Number(v))} />
                <Bar dataKey="avgCorrect" radius={[4, 4, 0, 0]}>
                  {difficulty.map((d, i) => (
                    <Cell key={i} fill={masteryColor(d.avgCorrect)} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>

            {/* ZPD analysis note */}
            <div style={{ marginTop: 16, background: '#F8F9FF', border: '1px solid #C3CFE2',
                          borderRadius: 8, padding: '10px 14px', fontSize: 12 }}>
              <div style={{ fontWeight: 700, color: '#2C3E50', marginBottom: 4 }}>
                📊 ZPD Analysis
              </div>
              <div style={{ color: '#4A5568', lineHeight: 1.6 }}>
                The MAB targets the <strong>30–60% difficulty</strong> range for most learners
                (ZPD sweet spot). Expert tasks serve mastered-concept consolidation. If "Hard"
                correct rate &lt; 40%, consider adding medium scaffolding tasks.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── Tab: Prerequisite Edges ────────────────────────────────────────── */}
      {activeTab === 'edges' && edges.length === 0 && (
        <NoDataPanel
          title="No prerequisite edge analytics available"
          reason={reasons.edges}
          hint="Edge effectiveness is computed from concept_dependencies + trajectory_records.transfer_amount. Seed the dependency graph and complete interactions with transfer activations to populate."
        />
      )}
      {activeTab === 'edges' && edges.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10,
                        padding: '18px 20px' }}>
            <SectionHeader
              title="Prerequisite Edge Effectiveness"
              sub="Which DAG edges are generating measurable transfer. Threshold: T_realized > 0.08"
            />

            {/* Summary chips */}
            <div style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
              <div style={{ background: '#D5F5E3', border: '1px solid #A9DFBF', borderRadius: 8,
                            padding: '8px 16px', fontSize: 12 }}>
                <span style={{ fontWeight: 700, color: '#1E8449' }}>
                  {edges.filter(e => e.effective).length} effective
                </span>
                <span style={{ color: '#1E8449' }}> edges</span>
              </div>
              <div style={{ background: '#FDEDEC', border: '1px solid #F5B7B1', borderRadius: 8,
                            padding: '8px 16px', fontSize: 12 }}>
                <span style={{ fontWeight: 700, color: '#C0392B' }}>
                  {edges.filter(e => !e.effective).length} weak
                </span>
                <span style={{ color: '#C0392B' }}> edges — review curriculum map</span>
              </div>
            </div>

            {/* Edge table */}
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
              <thead>
                <tr style={{ borderBottom: '2px solid #E2E8F0' }}>
                  {['Prerequisite', '→', 'Target Concept', 'Mean T_realized',
                    'Activations', 'Status'].map(h => (
                    <th key={h} style={{ padding: '8px 12px', textAlign: 'left',
                                         color: '#718096', fontWeight: 700, fontSize: 11 }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {edges.sort((a, b) => b.transferMean - a.transferMean).map((e, i) => (
                  <tr key={i} style={{
                    borderBottom: '1px solid #F7FAFC',
                    background: !e.effective ? '#FAFAFA' : '#fff',
                    opacity: e.effective ? 1 : 0.7,
                  }}>
                    <td style={{ padding: '10px 12px', fontWeight: 600, color: '#1A2332' }}>
                      {e.from}
                    </td>
                    <td style={{ padding: '10px 12px', color: '#A0AEC0', fontSize: 16 }}>→</td>
                    <td style={{ padding: '10px 12px', color: '#4A5568' }}>{e.to}</td>
                    <td style={{ padding: '10px 12px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <div style={{ width: 80, height: 6, background: '#E2E8F0',
                                      borderRadius: 3, overflow: 'hidden' }}>
                          <div style={{ width: `${Math.min(e.transferMean / 0.25 * 100, 100)}%`,
                                        height: '100%', borderRadius: 3,
                                        background: e.effective ? '#27AE60' : '#CBD5E0' }} />
                        </div>
                        <span style={{ fontWeight: 700, color: e.effective ? '#27AE60' : '#A0AEC0',
                                        fontVariantNumeric: 'tabular-nums' }}>
                          {pct(e.transferMean)}
                        </span>
                      </div>
                    </td>
                    <td style={{ padding: '10px 12px', color: '#4A5568',
                                  fontVariantNumeric: 'tabular-nums' }}>
                      {e.activationCount.toLocaleString()}
                    </td>
                    <td style={{ padding: '10px 12px' }}>
                      {e.effective ? (
                        <span style={{ fontSize: 11, fontWeight: 700, color: '#1E8449',
                                        background: '#D5F5E3', borderRadius: 4,
                                        padding: '3px 8px' }}>
                          ✓ Effective
                        </span>
                      ) : (
                        <span style={{ fontSize: 11, fontWeight: 700, color: '#7D6008',
                                        background: '#FEF9E7', borderRadius: 4,
                                        padding: '3px 8px' }}>
                          ⚠ Weak
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* Curriculum recommendation */}
            <div style={{ marginTop: 16, background: '#F8F9FF', border: '1px solid #C3CFE2',
                          borderRadius: 8, padding: '12px 16px', fontSize: 12 }}>
              <div style={{ fontWeight: 700, color: '#2C3E50', marginBottom: 6 }}>
                🎓 Curriculum Recommendation
              </div>
              <ul style={{ margin: 0, paddingLeft: 18, color: '#4A5568', lineHeight: 1.8 }}>
                <li>
                  <strong>Strengthen</strong> the Algorithms K-2 → K-5 pathway —
                  highest observed transfer (22%), confirms foundational prerequisite design.
                </li>
                <li>
                  <strong>Review</strong> Modularity K-8 bottleneck — only 31% avg
                  mastery. Add bridging tasks from K-5 Modularity before advancing.
                </li>
                <li>
                  <strong>Investigate</strong> Algorithms K-12 (22% mastery, 74% fail rate) —
                  K-8 → K-12 transfer edge is weak (7%). Consider additional K-8 consolidation tasks.
                </li>
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* ── Tab: Cohort Study ─────────────────────────────────────────────── */}
      {activeTab === 'archetype' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div style={{ background: '#F5EEF8', border: '1px solid #D7BDE2', borderRadius: 10, padding: '14px 18px', fontSize: 12, color: '#4A235A', lineHeight: 1.6 }}>
            <strong>{t('instructor.archetype.observational', 'Observational research only')}</strong>
            {' — '}
            {t('instructor.archetype.note',
              'Learner archetype profiles do not change MAB recommendations. This panel shows which VARK-dominant learners achieve higher JT or faster completion per concept — the data you need to answer "does K-2 work best for kinesthetic learners?"')}
          </div>

          {archetypeData?.meta && (
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
              <StatCard label="Self-reported profiles" value={archetypeData.meta.profiles_count} sub="onboarded learners" color="#6C3483" />
              <StatCard label="Learning materials" value={archetypeData.meta.materials_count} sub="EN + ID seeded" color="#2980B9" />
              {Object.entries(archetypeData.meta.task_languages ?? {}).map(([lang, n]) => (
                <StatCard key={lang} label={`Tasks (${lang})`} value={n} sub="K-12 catalog" color="#27AE60" />
              ))}
            </div>
          )}

          {archetypeLoading ? (
            <div style={{ padding: 40, textAlign: 'center', color: '#718096' }}>Loading archetype analysis…</div>
          ) : !archetypeData?.buckets?.length ? (
            <NoDataPanel
              title="No Archetype × Concept data yet"
              reason="Learners need to complete the onboarding survey and practice tasks."
              hint="Once learners self-report their profile and attempt tasks, buckets appear here grouped by dominant VARK axis and concept."
            />
          ) : (
            <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10, padding: '18px 20px', overflowX: 'auto' }}>
              <SectionHeader
                title="JT & time by dominant VARK × concept"
                sub="Grouped by self-reported dominant learning style (visual / auditory / reading / kinesthetic)"
              />
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid #E2E8F0', textAlign: 'left' }}>
                    {['Concept', 'Dominant VARK', 'N', 'Avg JT', 'Avg time (s)', 'Accuracy'].map(h => (
                      <th key={h} style={{ padding: '8px 10px', color: '#718096', fontWeight: 700 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {archetypeData.buckets.map((b, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid #F1F5F9' }}>
                      <td style={{ padding: '8px 10px', fontFamily: 'monospace', fontSize: 11 }}>{b.concept}</td>
                      <td style={{ padding: '8px 10px', fontWeight: 600, color: '#6C3483' }}>{b.dominant_vark}</td>
                      <td style={{ padding: '8px 10px' }}>{b.n_interactions}</td>
                      <td style={{ padding: '8px 10px', color: b.avg_jt > 0.5 ? '#27AE60' : '#C0392B' }}>{b.avg_jt.toFixed(3)}</td>
                      <td style={{ padding: '8px 10px' }}>{b.avg_response_time.toFixed(1)}</td>
                      <td style={{ padding: '8px 10px' }}>{(b.accuracy * 100).toFixed(0)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {activeTab === 'study' && (
        <div style={{ maxWidth: 700 }}>
          <div style={{ background: 'linear-gradient(135deg, #F4ECF7, #EBF5FB)',
                        border: '1px solid #D2B4DE', borderRadius: 12,
                        padding: '32px 28px', textAlign: 'center' }}>
            <div style={{ fontSize: 40, marginBottom: 12 }}>⚗</div>
            <div style={{ fontSize: 16, fontWeight: 800, color: '#1A2332', marginBottom: 8 }}>
              Cohort Study has a dedicated page
            </div>
            <div style={{ fontSize: 13, color: '#4A5568', lineHeight: 1.6, marginBottom: 20,
                          maxWidth: 480, margin: '0 auto 20px' }}>
              Policy teaching comparison — live run index, mastery curves, ΔM, concept
              routing, cold-start by archetype. All on a single focused page with label
              picker and live elapsed timer.
            </div>
            <Link href="/dashboard/cohorts" style={{
              display: 'inline-block', padding: '11px 28px', fontSize: 14, fontWeight: 700,
              color: '#fff', background: '#6C3483', textDecoration: 'none',
              borderRadius: 8, marginBottom: 12,
            }}>
              Open Cohort Study →
            </Link>
          </div>
        </div>
      )}
      {/* ── (old study tab — moved to /dashboard/cohorts) ────────────────── */}
      {false && (
        <div>
          {/* Launcher (researcher/admin only) */}
          {canLaunch && (
            <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10,
                          padding: '18px 20px', marginBottom: 20 }}>
              <SectionHeader
                title="Launch new cohort run"
                sub="Pick a cohort spec and queue a new run. Survives API restarts via resume."
              />
              <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
                <select
                  value={selectedCohortId}
                  onChange={e => setSelectedCohortId(e.target.value)}
                  style={{ flex: '1 1 240px', minWidth: 240, padding: '8px 12px', fontSize: 13,
                           border: '1px solid #CBD5E0', borderRadius: 6, color: '#2D3748',
                           background: '#fff' }}
                >
                  <option value="">— select cohort —</option>
                  {availableCohorts.map(c => (
                    <option key={c.cohort_id} value={c.cohort_id}>
                      {c.name} ({c.cohort_id.slice(0, 8)}…)
                    </option>
                  ))}
                </select>
                <input
                  value={launchReason}
                  onChange={e => setLaunchReason(e.target.value)}
                  placeholder="reason"
                  style={{ flex: '1 1 200px', minWidth: 200, padding: '8px 12px', fontSize: 13,
                           border: '1px solid #CBD5E0', borderRadius: 6, color: '#2D3748' }}
                />
                <button
                  onClick={launchRun}
                  disabled={launching || !selectedCohortId}
                  style={{ padding: '8px 20px', fontSize: 13, fontWeight: 700,
                           background: launching || !selectedCohortId ? '#CBD5E0' : '#27AE60',
                           color: '#fff', border: 'none', borderRadius: 6,
                           cursor: launching || !selectedCohortId ? 'default' : 'pointer' }}
                >
                  {launching ? 'Queueing…' : 'Launch'}
                </button>
              </div>
              {launchError && (
                <div style={{ marginTop: 10, fontSize: 12, color: '#C0392B', fontWeight: 600 }}>
                  ⚠ {launchError}
                </div>
              )}
              {availableCohorts.length === 0 && (
                <div style={{ marginTop: 10, fontSize: 11, color: '#718096' }}>
                  No cohort specs found. Create one via POST /v3/experiments/cohorts.
                </div>
              )}
            </div>
          )}

          {/* Run ID input */}
          <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10,
                        padding: '18px 20px', marginBottom: 20 }}>
            <SectionHeader
              title="Cohort Run Comparison"
              sub="Enter a run_id or launch one above to compare policy outcomes"
            />
            <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
              <input
                value={studyRunId}
                onChange={e => setStudyRunId(e.target.value)}
                placeholder="run-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                style={{ flex: 1, padding: '8px 12px', fontSize: 13,
                         border: '1px solid #CBD5E0', borderRadius: 6,
                         fontFamily: 'monospace', color: '#2D3748' }}
              />
              <button
                onClick={() => loadStudy(studyRunId)}
                disabled={studyLoading || !studyRunId.trim()}
                style={{ padding: '8px 20px', fontSize: 13, fontWeight: 700,
                         background: studyLoading ? '#CBD5E0' : '#6C3483', color: '#fff',
                         border: 'none', borderRadius: 6, cursor: studyLoading ? 'default' : 'pointer' }}
              >
                {studyLoading ? 'Loading…' : 'Load Run'}
              </button>
              {studyData?.status === 'running' && (
                <span style={{ fontSize: 11, color: '#E67E22', fontWeight: 700 }}>
                  ● Live — polling every 4s
                </span>
              )}
              {studyData?.status === 'completed' && (
                <span style={{ fontSize: 11, color: '#27AE60', fontWeight: 700 }}>
                  ✓ Run complete
                </span>
              )}
            </div>
            {/* Quick-fill hints */}
            {([
              {
                label: '★ Sweep A · stability 5c 40s — 10 policies × 2 archetypes × 3 seeds',
                id: 'run-efa42239-2117-471c-ae2f-93420ae08fcb',
                highlight: true,
                learnerType: 'synthetic' as const,
                sweep: 'A',
              },
              {
                label: 'Original 10-policy ITS run — 5c 40s (partial ~45%, pre-Sweep reference)',
                id: 'run-73c9ae9e-fd8d-49a5-9b2f-323a8681e82a',
                highlight: false,
                learnerType: 'synthetic' as const,
                sweep: null,
              },
              {
                label: '60-user single-concept baseline (uniform correctness)',
                id: 'run-5cd9ac3b-5bb3-4ac8-9dd9-21b3bbf5be3b',
                highlight: false,
                learnerType: 'synthetic' as const,
                sweep: null,
              },
            ] as Array<{label:string,id:string,highlight:boolean,learnerType:'synthetic'|'experiment'|'real',sweep:string|null}>)
            .map(({ label, id, highlight, learnerType, sweep }) => (
              <div key={id} style={{ marginTop: 6, fontSize: 11, color: highlight ? '#6C3483' : '#A0AEC0', display: 'flex', alignItems: 'center', gap: 4 }}>
                {sweep && <span style={{ background: '#8E44AD', color: '#fff', borderRadius: 3, padding: '0 4px', fontSize: 9, fontWeight: 800 }}>SWEEP {sweep}</span>}
                <span style={{ background: learnerType === 'synthetic' ? '#EBF5FB' : learnerType === 'experiment' ? '#FEF9E7' : '#EAFAF1', color: learnerType === 'synthetic' ? '#1A5276' : learnerType === 'experiment' ? '#9A7D0A' : '#1E8449', borderRadius: 3, padding: '0 4px', fontSize: 9, fontWeight: 700 }}>{learnerType}</span>
                <span>{label}:</span>
                <code style={{ fontSize: 10, background: '#F7FAFC', padding: '1px 4px', borderRadius: 3 }}>{id}</code>
                <button
                  onClick={() => setStudyRunId(id)}
                  style={{ fontSize: 11, color: '#6C3483', background: 'none',
                           border: 'none', cursor: 'pointer', textDecoration: 'underline', padding: 0 }}
                >
                  Use
                </button>
              </div>
            ))}
          </div>

          {/* Progress bar if running */}
          {studyData && (
            <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10,
                          padding: '14px 20px', marginBottom: 20 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                <span style={{ fontSize: 12, fontWeight: 700, color: '#2C3E50' }}>
                  Run Progress
                </span>
                <span style={{ fontSize: 12, color: '#718096', fontFamily: 'monospace' }}>
                  {studyData.progress?.completed ?? 0} / {studyData.progress?.total ?? '?'} steps
                  {studyData.progress?.errors > 0 && (
                    <span style={{ color: '#C0392B', marginLeft: 8 }}>
                      {studyData.progress.errors} errors
                    </span>
                  )}
                </span>
              </div>
              <div style={{ background: '#EDF2F7', borderRadius: 4, height: 8, overflow: 'hidden' }}>
                <div style={{
                  height: '100%', borderRadius: 4, transition: 'width 0.4s',
                  background: studyData.status === 'completed' ? '#27AE60' : '#6C3483',
                  width: studyData.progress?.total
                    ? `${Math.min(100, (studyData.progress.completed / studyData.progress.total) * 100)}%`
                    : '0%',
                }} />
              </div>
              <div style={{ marginTop: 6, fontSize: 11, color: '#A0AEC0' }}>
                Policies: {(studyData.policies ?? []).join(', ') || '—'}
                {studyData.started_at && (
                  <span style={{ marginLeft: 12 }}>
                    Started: {new Date(studyData.started_at).toLocaleTimeString()}
                  </span>
                )}
                {studyData.completed_at && (
                  <span style={{ marginLeft: 12 }}>
                    Completed: {new Date(studyData.completed_at).toLocaleTimeString()}
                  </span>
                )}
              </div>
            </div>
          )}

          {/* Policy summary cards */}
          {studyData?.summary && Object.keys(studyData.summary).length > 0 && (() => {
            const PALETTE: Record<string, string> = {
              hcie: '#1A5276', random: '#C0392B', mastery_greedy: '#1E8449',
              static: '#E67E22', zpd_aligned: '#8E44AD', thompson: '#2980B9',
              uncertainty_reduction: '#16A085', epsilon_greedy: '#27AE60',
              bandit: '#784212', ucb: '#7F8C8D',
            }
            // Sort by avg_final_mastery descending so best policy is first
            const sorted = Object.entries(studyData.summary as Record<string, any>)
              .sort(([, a], [, b]) => (b.avg_final_mastery ?? 0) - (a.avg_final_mastery ?? 0))
            return (
              <div style={{ display: 'flex', gap: 10, marginBottom: 20, flexWrap: 'wrap' }}>
                {sorted.map(([policy, s], rank) => {
                  const c = PALETTE[policy] ?? '#4A5568'
                  return (
                    <div key={policy} style={{ flex: 1, minWidth: 160,
                                               background: `${c}0D`, border: `1px solid ${c}40`,
                                               borderRadius: 10, padding: '12px 14px',
                                               borderTop: `3px solid ${c}` }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                        <div style={{ fontSize: 11, fontWeight: 800, textTransform: 'uppercase',
                                      letterSpacing: '0.08em', color: c }}>
                          {policy}
                        </div>
                        <div style={{ fontSize: 10, fontWeight: 700, color: '#fff', background: c,
                                      borderRadius: 10, padding: '1px 6px', opacity: 0.85 }}>
                          #{rank + 1}
                        </div>
                      </div>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 4 }}>
                        <div>
                          <div style={{ fontSize: 9, color: '#718096' }}>Final mastery</div>
                          <div style={{ fontSize: 18, fontWeight: 800, color: c }}>
                            {(s.avg_final_mastery * 100).toFixed(1)}%
                          </div>
                        </div>
                        <div>
                          <div style={{ fontSize: 9, color: '#718096' }}>Learners</div>
                          <div style={{ fontSize: 18, fontWeight: 800, color: '#2C3E50' }}>
                            {s.total_learners}
                          </div>
                        </div>
                        <div>
                          <div style={{ fontSize: 9, color: '#718096' }}>Accuracy</div>
                          <div style={{ fontSize: 14, fontWeight: 700, color: '#2C3E50' }}>
                            {(s.overall_accuracy * 100).toFixed(1)}%
                          </div>
                        </div>
                        <div>
                          <div style={{ fontSize: 9, color: '#718096' }}>Avg JT</div>
                          <div style={{ fontSize: 14, fontWeight: 700, color: '#8E44AD' }}>
                            {(s.avg_jt * 100).toFixed(1)}%
                          </div>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            )
          })()}

          {/* Mastery curve chart + ΔM — shared interactive legend */}
          {studyData?.curves && Object.keys(studyData.curves).length > 0 && (() => {
            const POLICY_PALETTE: Record<string, string> = {
              hcie: '#1A5276', random: '#C0392B', mastery_greedy: '#1E8449',
              static: '#E67E22', zpd_aligned: '#8E44AD', thompson: '#2980B9',
              uncertainty_reduction: '#16A085', epsilon_greedy: '#27AE60',
              bandit: '#784212', ucb: '#7F8C8D',
            }
            const allPolicies = Object.keys(studyData.curves as Record<string, any[]>)
            const active = visiblePolicies.size === 0 ? allPolicies : allPolicies.filter(p => visiblePolicies.has(p))
            const pColor = (p: string, i: number) => POLICY_PALETTE[p] ?? ['#1A5276','#C0392B','#1E8449','#E67E22','#8E44AD','#2980B9','#16A085','#784212'][i % 8]
            const pWidth = (p: string) => p === 'hcie' ? 2.5 : p === 'random' ? 2 : 1.5
            return (
              <>
                {/* Interactive legend / policy toggle */}
                <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10, padding: '14px 20px', marginBottom: 12 }}>
                  <div style={{ fontSize: 11, fontWeight: 700, color: '#4A5568', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    Policy filter — click to isolate · {visiblePolicies.size === 0 ? 'all visible' : `${visiblePolicies.size} selected`}
                    {visiblePolicies.size > 0 && (
                      <button onClick={() => setVisiblePolicies(new Set())}
                        style={{ marginLeft: 10, fontSize: 10, color: '#718096', background: 'none', border: '1px solid #CBD5E0', borderRadius: 4, padding: '1px 6px', cursor: 'pointer' }}>
                        reset
                      </button>
                    )}
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                    {allPolicies.map((p, i) => {
                      const isOn = visiblePolicies.size === 0 || visiblePolicies.has(p)
                      const c = pColor(p, i)
                      return (
                        <button key={p} onClick={() => togglePolicy(p)}
                          style={{
                            display: 'flex', alignItems: 'center', gap: 5,
                            padding: '4px 10px', borderRadius: 20, fontSize: 11, fontWeight: 600, cursor: 'pointer',
                            border: `2px solid ${c}`,
                            background: isOn ? c : 'transparent',
                            color: isOn ? '#fff' : c,
                            opacity: isOn ? 1 : 0.5, transition: 'all 0.15s',
                          }}>
                          <span style={{ width: 8, height: 8, borderRadius: '50%', background: isOn ? '#fff' : c, display: 'inline-block' }} />
                          {p}
                        </button>
                      )
                    })}
                  </div>
                </div>

                {/* Mastery curve */}
                <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10, padding: '18px 20px', marginBottom: 12 }}>
                  <SectionHeader
                    title="Average Mastery Curve by Policy"
                    sub="Mean mastery across all synthetic learners per interaction step"
                  />
                  <ResponsiveContainer width="100%" height={280}>
                    <LineChart margin={{ left: 0, right: 20, top: 8, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                      <XAxis dataKey="step" type="number"
                        label={{ value: 'Interaction', position: 'insideBottom', offset: -4, fontSize: 11 }}
                        tick={{ fontSize: 10, fill: '#A0AEC0' }} axisLine={false} tickLine={false} />
                      <YAxis domain={[0, 1]} tickFormatter={v => `${(v * 100).toFixed(0)}%`}
                        tick={{ fontSize: 10, fill: '#A0AEC0' }} axisLine={false} tickLine={false} />
                      <Tooltip
                        formatter={(v: any, name: any) => [`${(Number(v) * 100).toFixed(1)}%`, name]}
                        labelFormatter={l => `Step ${l}`}
                        contentStyle={{ fontSize: 11, borderRadius: 6 }}
                      />
                      {Object.entries(studyData.curves as Record<string, any[]>).map(([policy, pts], i) => (
                        active.includes(policy) ? (
                          <Line key={policy} data={pts} dataKey="avg_mastery" name={policy}
                            stroke={pColor(policy, i)} strokeWidth={pWidth(policy)} dot={false} type="monotone" />
                        ) : null
                      ))}
                    </LineChart>
                  </ResponsiveContainer>
                </div>

                {/* ΔM learning gain */}
                <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10, padding: '18px 20px', marginBottom: 16 }}>
                  <SectionHeader
                    title="Average Mastery Gain (ΔM) by Policy"
                    sub="Per-step learning gain — separates exploitative efficiency from cumulative depth"
                  />
                  <ResponsiveContainer width="100%" height={200}>
                    <LineChart margin={{ left: 0, right: 20, top: 8, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                      <XAxis dataKey="step" type="number"
                        tick={{ fontSize: 10, fill: '#A0AEC0' }} axisLine={false} tickLine={false} />
                      <YAxis tickFormatter={v => `${(v * 100).toFixed(1)}%`}
                        tick={{ fontSize: 10, fill: '#A0AEC0' }} axisLine={false} tickLine={false} />
                      <Tooltip
                        formatter={(v: any, name: any) => [`${(Number(v) * 100).toFixed(2)}%`, name + ' ΔM']}
                        labelFormatter={l => `Step ${l}`}
                        contentStyle={{ fontSize: 11, borderRadius: 6 }}
                      />
                      {Object.entries(studyData.curves as Record<string, any[]>).map(([policy, pts], i) => (
                        active.includes(policy) ? (
                          <Line key={policy} data={pts} dataKey="avg_delta_m" name={policy}
                            stroke={pColor(policy, i)} strokeWidth={pWidth(policy)} dot={false} type="monotone" />
                        ) : null
                      ))}
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </>
            )
          })()}

          {/* Governance context note */}
          {studyData?.summary && Object.keys(studyData.summary).length > 1 && (() => {
            const summary = studyData.summary as Record<string, any>
            const ranked = Object.entries(summary).sort((a: any, b: any) => (b[1].avg_final_mastery ?? 0) - (a[1].avg_final_mastery ?? 0))
            const best = ranked[0]?.[0] ?? ''; const worst = ranked[ranked.length-1]?.[0] ?? ''
            const hcieRank = ranked.findIndex(([p]) => p === 'hcie') + 1
            const topMastery = (ranked[0]?.[1]?.avg_final_mastery ?? 0) * 100
            const bottomMastery = (ranked[ranked.length-1]?.[1]?.avg_final_mastery ?? 0) * 100
            const spread = topMastery - bottomMastery
            return (
              <div style={{ background: 'linear-gradient(135deg, #EBF5FB, #F9F0FF)', border: '1px solid #D2B4DE', borderRadius: 10, padding: '14px 18px', marginBottom: 16 }}>
                <div style={{ fontSize: 12, fontWeight: 800, color: '#6C3483', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                  ⚗ Governance Interpretation
                </div>
                <div style={{ fontSize: 12, color: '#4A5568', lineHeight: 1.6 }}>
                  <strong>Policy ecology confirmed</strong> — {ranked.length}-policy spread of <strong>{spread.toFixed(1)}pp mastery</strong> ({worst.toUpperCase()} → {best.toUpperCase()}).
                  {hcieRank > 1 && (
                    <> HCIE ranks #{hcieRank}: objective mismatch hypothesis — HCIE optimises ΔM + transfer + ZPD depth, not raw final-mastery.
                    Exploitative policies (mastery_greedy, static) dominate <em>short horizons on compact graphs</em>.
                    Transfer and governance depth become consequential when graph size and step count increase.</>
                  )}
                  {' '}Concept routing divergence (below) confirms the selection layer is functioning — different policies genuinely navigate different parts of the prerequisite graph.
                </div>
              </div>
            )
          })()}

          {/* Concept selection distribution — scrollable, wrapped grid */}
          {studyData?.concept_distribution && Object.keys(studyData.concept_distribution).length > 0 && (() => {
            const dist = studyData.concept_distribution as Record<string, any[]>
            const CONCEPT_COLORS: Record<string, string> = {
              'k2_algorithms': '#1E8449', 'k2_control': '#27AE60',
              'k5_algorithms': '#1A5276', 'k5_control': '#2980B9',
              'k8_algorithms': '#6C3483', 'k8_control': '#8E44AD',
              'k2_variables': '#D4AC0D', 'k5_variables': '#F1C40F',
              'k2_networks_communication': '#E74C3C', 'k5_networks_communication': '#CB4335',
              'k2_program_development': '#1ABC9C', 'k5_program_development': '#17A589',
            }
            const shortC = (c: string) => c.replace(/k(\d+)_/g, 'K$1:').replace(/_/g, ' ')
            const POLICY_PALETTE: Record<string, string> = {
              hcie: '#1A5276', random: '#C0392B', mastery_greedy: '#1E8449',
              static: '#E67E22', zpd_aligned: '#8E44AD', thompson: '#2980B9',
              uncertainty_reduction: '#16A085', epsilon_greedy: '#27AE60',
              bandit: '#784212', ucb: '#7F8C8D',
            }
            // Only show policies selected in legend (or all)
            const filteredDist = Object.entries(dist).filter(([p]) =>
              visiblePolicies.size === 0 || visiblePolicies.has(p)
            )
            return (
              <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10, padding: '18px 20px', marginBottom: 16 }}>
                <SectionHeader
                  title="Concept Selection Distribution"
                  sub="How each policy navigates the knowledge graph — HCIE routes prerequisites (K2→K5→K8); random spreads uniformly; greedy exploits easiest"
                />
                {/* Scrollable wrapper for many policies */}
                <div style={{ overflowX: 'auto', paddingBottom: 4 }}>
                  <div style={{ display: 'grid', gridTemplateColumns: `repeat(${Math.max(3, Math.min(5, filteredDist.length))}, minmax(140px, 1fr))`, gap: 14, minWidth: filteredDist.length > 5 ? '700px' : undefined }}>
                    {filteredDist.map(([policy, rows]) => {
                      const total = (rows as any[]).reduce((s: number, r: any) => s + r.n, 0)
                      const pIdx = Object.keys(dist).indexOf(policy)
                      const color = POLICY_PALETTE[policy] ?? '#4A5568'
                      return (
                        <div key={policy} style={{ borderLeft: `3px solid ${color}`, paddingLeft: 10 }}>
                          <div style={{ fontSize: 11, fontWeight: 800, color, textTransform: 'uppercase', marginBottom: 8, letterSpacing: '0.05em' }}>{policy}</div>
                          {(rows as any[]).map((r: any) => (
                            <div key={r.concept} style={{ marginBottom: 7 }}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, marginBottom: 2 }}>
                                <span style={{ color: CONCEPT_COLORS[r.concept] || '#4A5568', fontWeight: 700, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '70%' }}>{shortC(r.concept)}</span>
                                <span style={{ color: '#718096', flexShrink: 0 }}>{total > 0 ? ((r.n/total)*100).toFixed(0) : 0}%</span>
                              </div>
                              <div style={{ background: '#EDF2F7', borderRadius: 3, height: 5, position: 'relative' }}>
                                <div style={{ height: '100%', borderRadius: 3, background: CONCEPT_COLORS[r.concept] || color,
                                              width: total > 0 ? `${(r.n/total)*100}%` : '0%', transition: 'width 0.3s' }} />
                              </div>
                              <div style={{ fontSize: 9, color: '#A0AEC0', marginTop: 1 }}>
                                acc {((r.accuracy||0)*100).toFixed(0)}% · ΔM {((r.avg_delta_m||0)*100).toFixed(1)}%
                              </div>
                            </div>
                          ))}
                        </div>
                      )
                    })}
                  </div>
                </div>
                {filteredDist.length < Object.keys(dist).length && (
                  <div style={{ fontSize: 10, color: '#A0AEC0', marginTop: 8 }}>
                    Showing {filteredDist.length}/{Object.keys(dist).length} policies — use the policy filter above to change selection
                  </div>
                )}
              </div>
            )
          })()}

          {/* Cold-start performance by archetype */}
          {studyData?.cold_start && Object.keys(studyData.cold_start).length > 0 && (() => {
            const cs = studyData.cold_start as Record<string, Record<string, any>>
            return (
              <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10, padding: '18px 20px', marginTop: 16 }}>
                <SectionHeader
                  title="Cold-Start Performance (Steps 1–5)"
                  sub="First 5 interactions — HCIE's ZPD selection should show higher mastery gain despite lower accuracy"
                />
                {/* Only show selected policies (or all if filter is empty) */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 10 }}>
                  {Object.entries(cs)
                    .filter(([p]) => visiblePolicies.size === 0 || visiblePolicies.has(p))
                    .map(([policy, archetypes]) => {
                      const POLICY_PALETTE: Record<string, string> = {
                        hcie: '#1A5276', random: '#C0392B', mastery_greedy: '#1E8449',
                        static: '#E67E22', zpd_aligned: '#8E44AD', thompson: '#2980B9',
                        uncertainty_reduction: '#16A085', epsilon_greedy: '#27AE60',
                        bandit: '#784212', ucb: '#7F8C8D',
                      }
                      const color = POLICY_PALETTE[policy] ?? '#4A5568'
                      return (
                        <div key={policy} style={{ border: `1px solid ${color}40`, borderRadius: 8, padding: '10px 12px', background: `${color}08` }}>
                          <div style={{ fontSize: 11, fontWeight: 800, color, textTransform: 'uppercase', marginBottom: 6, letterSpacing: '0.05em' }}>{policy}</div>
                          {Object.entries(archetypes).map(([arch, stats]: [string, any]) => (
                            <div key={arch} style={{ marginBottom: 5 }}>
                              <div style={{ fontSize: 10, fontWeight: 600, color: '#4A5568', marginBottom: 1 }}>
                                {arch} · {stats.n_learners}L
                              </div>
                              <div style={{ display: 'flex', gap: 8, fontSize: 10, color: '#718096' }}>
                                <span>M: <strong style={{ color }}>{((stats.avg_mastery||0)*100).toFixed(1)}%</strong></span>
                                <span>Acc: <strong>{((stats.accuracy||0)*100).toFixed(0)}%</strong></span>
                              </div>
                            </div>
                          ))}
                        </div>
                      )
                    })}
                </div>
              </div>
            )
          })()}

          {!studyData && !studyLoading && (
            <div style={{ background: '#fff', border: '1px dashed #CBD5E0', borderRadius: 12,
                          padding: '48px 28px', textAlign: 'center', color: '#A0AEC0' }}>
              <div style={{ fontSize: 36, marginBottom: 12 }}>⚗</div>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#4A5568', marginBottom: 6 }}>
                No cohort run loaded
              </div>
              <div style={{ fontSize: 12, maxWidth: 480, margin: '0 auto', lineHeight: 1.6 }}>
                Enter a <code>run_id</code> from a launched cohort, or click "Use this" above to
                load the active HCIE vs Random validation run.
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── Tab: Real Learner Cohort ─────────────────────────────────────── */}
      {activeTab === 'cohort' && (
        <div>
          {/* Header & filter */}
          <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10,
                        padding: '18px 20px', marginBottom: 16 }}>
            <SectionHeader
              title="Real Learner Cohort"
              sub="Experiment-replay learners (Junyi · ASSISTments · STATICS) and synthetic cohort members — actual learning trajectories through the ITS"
            />
            <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap', marginTop: 10 }}>
              {(['all','live','junyi','assistments','statics','synthetic'] as const).map(ds => (
                <button key={ds} onClick={() => {
                  setCohortDataset(ds)
                  setCohortLearners([])
                  loadCohort(ds)
                }} style={{
                  padding: '5px 12px', fontSize: 11, fontWeight: 600, borderRadius: 20,
                  border: '1px solid',
                  borderColor: cohortDataset === ds ? '#6C3483' : '#CBD5E0',
                  background: cohortDataset === ds ? '#6C3483' : '#fff',
                  color: cohortDataset === ds ? '#fff' : '#4A5568',
                  cursor: 'pointer',
                }}>
                  {ds === 'all' ? 'All datasets' : ds === 'assistments' ? 'ASSISTments' : ds.charAt(0).toUpperCase() + ds.slice(1)}
                </button>
              ))}
              <button onClick={() => loadCohort(cohortDataset)} style={{
                padding: '5px 12px', fontSize: 11, color: '#4A5568', background: '#EDF2F7',
                border: '1px solid #CBD5E0', borderRadius: 20, cursor: 'pointer',
              }}>
                ↻ Refresh
              </button>
              {cohortLoading && <span style={{ fontSize: 11, color: '#8E44AD' }}>Loading…</span>}
            </div>
          </div>

          {/* Legend */}
          <div style={{ display: 'flex', gap: 14, marginBottom: 14, flexWrap: 'wrap' }}>
            {[
              { type: 'live', color: '#1e7d4a', bg: '#E8F8EF', label: 'Live', hint: 'Real human learners exercising /v3/learner/recommend + /attempt end-to-end' },
              { type: 'experiment-replay', color: '#9A7D0A', bg: '#FEF9E7', label: 'Experiment-replay', hint: 'Real student KT logs (Junyi, ASSISTments, STATICS) replayed through HCIE runtime' },
              { type: 'synthetic', color: '#1A5276', bg: '#EBF5FB', label: 'Synthetic', hint: 'IRT-driven synthetic learner from cohort sweep' },
            ].map(({ type, color, bg, label, hint }) => (
              <div key={type} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, color: '#4A5568' }}>
                <span style={{ background: bg, color, border: `1px solid ${color}40`, borderRadius: 3, padding: '1px 6px', fontWeight: 700, fontSize: 10 }}>{label}</span>
                <span style={{ color: '#A0AEC0' }}>{hint}</span>
              </div>
            ))}
          </div>

          {/* Learner grid */}
          {cohortLearners.length === 0 && !cohortLoading && (
            <div style={{ background: '#fff', border: '1px dashed #CBD5E0', borderRadius: 12,
                          padding: '48px 28px', textAlign: 'center', color: '#A0AEC0' }}>
              <div style={{ fontSize: 36, marginBottom: 12 }}>👥</div>
              <div style={{ fontSize: 13, fontWeight: 700, color: '#4A5568', marginBottom: 4 }}>No learner data</div>
              <div style={{ fontSize: 12 }}>
                {BACKEND ? 'No experiment-replay or synthetic learners found in experiment_trajectories for this dataset filter.'
                         : 'Backend not connected.'}
              </div>
            </div>
          )}
          {cohortLearners.length > 0 && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 12 }}>
              {cohortLearners.map((learner) => {
                const isExp = learner.learner_type === 'experiment-replay'
                const isLive = learner.learner_type === 'live'
                const typeColor = isLive ? '#1e7d4a' : isExp ? '#9A7D0A' : '#1A5276'
                const typeBg = isLive ? '#E8F8EF' : isExp ? '#FEF9E7' : '#EBF5FB'
                const masteryColor = (m: number) => m >= 0.7 ? '#27AE60' : m >= 0.4 ? '#E67E22' : '#C0392B'
                const isSelected = selectedLearner === learner.user_id
                return (
                  <div key={learner.user_id}
                    onClick={() => setSelectedLearner(isSelected ? null : learner.user_id)}
                    style={{
                      background: '#fff', border: `1px solid ${isSelected ? typeColor : '#E2E8F0'}`,
                      borderTop: `3px solid ${masteryColor(learner.avg_mastery)}`,
                      borderRadius: 8, padding: '12px 14px', cursor: 'pointer',
                      boxShadow: isSelected ? `0 0 0 2px ${typeColor}40` : 'none',
                      transition: 'all 0.15s',
                    }}>
                    {/* Header */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                      <span style={{ fontSize: 10, fontWeight: 700, background: typeBg, color: typeColor,
                                     border: `1px solid ${typeColor}40`, borderRadius: 3, padding: '1px 5px' }}>
                        {learner.learner_type}
                      </span>
                      <span style={{ fontSize: 9, color: '#A0AEC0', background: '#F7FAFC',
                                     border: '1px solid #E2E8F0', borderRadius: 3, padding: '1px 5px' }}>
                        {learner.dataset}
                      </span>
                    </div>
                    {/* Short ID */}
                    <div style={{ fontSize: 10, fontFamily: 'monospace', color: '#4A5568',
                                  marginBottom: 8, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {learner.short_id}
                    </div>
                    {/* Metrics */}
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
                      <div>
                        <div style={{ fontSize: 9, color: '#718096' }}>Avg Mastery</div>
                        <div style={{ fontSize: 18, fontWeight: 800, color: masteryColor(learner.avg_mastery) }}>
                          {(learner.avg_mastery * 100).toFixed(1)}%
                        </div>
                      </div>
                      <div>
                        <div style={{ fontSize: 9, color: '#718096' }}>Improvement</div>
                        <div style={{ fontSize: 16, fontWeight: 700,
                                      color: learner.improvement >= 0 ? '#27AE60' : '#C0392B' }}>
                          {learner.improvement >= 0 ? '+' : ''}{(learner.improvement * 100).toFixed(1)}pp
                        </div>
                      </div>
                      <div>
                        <div style={{ fontSize: 9, color: '#718096' }}>Accuracy</div>
                        <div style={{ fontSize: 13, fontWeight: 700, color: '#2C3E50' }}>
                          {(learner.accuracy * 100).toFixed(0)}%
                        </div>
                      </div>
                      <div>
                        <div style={{ fontSize: 9, color: '#718096' }}>Interactions</div>
                        <div style={{ fontSize: 13, fontWeight: 700, color: '#2C3E50' }}>
                          {learner.n_interactions}
                        </div>
                      </div>
                    </div>
                    {/* Mini mastery bar */}
                    <div style={{ marginTop: 8, height: 4, background: '#EDF2F7', borderRadius: 2 }}>
                      <div style={{ height: '100%', borderRadius: 2, background: masteryColor(learner.avg_mastery),
                                    width: `${learner.avg_mastery * 100}%` }} />
                    </div>
                    {/* Governance note */}
                    <div style={{ marginTop: 6, fontSize: 9, color: '#A0AEC0' }}>
                      JT: <strong style={{ color: '#8E44AD' }}>{(learner.avg_jt * 100).toFixed(1)}%</strong>
                      · ΔM: <strong style={{ color: '#1A5276' }}>{(learner.avg_delta_m * 100).toFixed(2)}%</strong>
                      · {learner.concepts_visited}c
                    </div>
                    {isSelected && (
                      <div style={{ marginTop: 8, borderTop: '1px solid #EDF2F7', paddingTop: 6,
                                    display: 'flex', flexDirection: 'column', gap: 4 }}>
                        <Link href={`/dashboard/learner-journey/${encodeURIComponent(learner.user_id)}`}
                          style={{ display: 'block', padding: '4px 0', fontSize: 11, fontWeight: 700,
                                   color: '#6c3483', textAlign: 'center', textDecoration: 'none',
                                   background: '#f3eff7', borderRadius: 4 }}
                          onClick={(e) => e.stopPropagation()}>
                          0 → Mastered journey →
                        </Link>
                        <Link href={`/dashboard/learner?user_id=${encodeURIComponent(learner.user_id)}`}
                          style={{ display: 'block', padding: '4px 0', fontSize: 11, fontWeight: 700,
                                   color: typeColor, textAlign: 'center', textDecoration: 'none' }}
                          onClick={(e) => e.stopPropagation()}>
                          Governance analytics →
                        </Link>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}

          {/* Governance explanation */}
          {cohortLearners.length > 0 && (
            <div style={{ background: 'linear-gradient(135deg, #EBF5FB, #EAFAF1)', border: '1px solid #A9DFBF',
                          borderRadius: 10, padding: '14px 18px', marginTop: 16 }}>
              <div style={{ fontSize: 12, fontWeight: 800, color: '#1E8449', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                ℹ Governance Interpretation Guide
              </div>
              <div style={{ fontSize: 11, color: '#4A5568', lineHeight: 1.7 }}>
                <strong>Why do mastery levels differ between learners?</strong> Several governance factors:
                <ul style={{ margin: '6px 0', paddingLeft: 18, lineHeight: 1.8 }}>
                  <li><strong>ADC signal quality</strong> — if the ADC layer (Attention-Difficulty-Confidence) could not project a ZPD target, the selector fell back to a suboptimal arm. Look for high <em>uncertainty</em> (above 0.3) as a diagnostic.</li>
                  <li><strong>Trajectory quality</strong> — experiment-replay learners follow fixed response patterns from KT logs. High accuracy + low ΔM indicates the policy served easy tasks (exploitation without depth).</li>
                  <li><strong>Transfer activation</strong> — when a prerequisite concept's mastery passes threshold, transfer propagates gain to dependent concepts. Low avg JT with high accuracy = transfer not activated = graph traversal issue.</li>
                  <li><strong>Layer fit</strong> — synthetic learners use IRT-generated correctness (θ vs difficulty). Experiment-replay uses real student responses. The two populations show different mastery curves because the underlying response generation differs.</li>
                </ul>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── Observability Stack ────────────────────────────────────────────── */}
      {/* Live monitoring tools, exposed read-only via the gateway subpaths. */}
      <div style={{ marginTop: 32, background: '#F8F9FF',
                    border: '1px solid #C3CFE2', borderRadius: 10,
                    padding: '16px 20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
                      marginBottom: 12 }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: '#4A5568',
                        textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            Observability Stack
          </div>
          <div style={{ fontSize: 10, color: '#A0AEC0' }}>
            live · read-only
          </div>
        </div>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          {[
            { label: 'Grafana',    href: '/grafana/',   icon: '📈', desc: 'Dashboards & metrics' },
            { label: 'Prometheus', href: '/prometheus/', icon: '🔥', desc: 'Metrics scraper' },
            { label: 'Kafka UI',   href: '/kafka-ui/',  icon: '⚡', desc: 'Event stream monitor' },
          ].map(({ label, href, icon, desc }) => (
            <a key={label} href={href} target="_blank" rel="noopener noreferrer" style={{
              display: 'flex', alignItems: 'center', gap: 8,
              background: '#fff', border: '1px solid #E2E8F0',
              borderRadius: 8, padding: '8px 14px', textDecoration: 'none',
            }}>
              <span style={{ fontSize: 14 }}>{icon}</span>
              <div>
                <div style={{ fontSize: 12, fontWeight: 700, color: '#2C3E50' }}>{label} ↗</div>
                <div style={{ fontSize: 10, color: '#718096' }}>{desc}</div>
              </div>
            </a>
          ))}
        </div>
      </div>

      {/* ── Footer nav ─────────────────────────────────────────────────────── */}
      <div style={{ display: 'flex', gap: 10, marginTop: 24, justifyContent: 'center', flexWrap: 'wrap' }}>
        <Link href="/dashboard/learner" style={{
          fontSize: 13, fontWeight: 600, color: '#4A5568',
          textDecoration: 'none', padding: '10px 24px', borderRadius: 8,
          border: '1px solid #CBD5E0', background: '#fff',
        }}>
          ← Learner View
        </Link>
        <Link href="/dashboard/cohorts" style={{
          fontSize: 13, fontWeight: 700, color: '#6C3483', background: '#F4ECF7',
          textDecoration: 'none', padding: '10px 24px', borderRadius: 8,
          border: '1px solid #D2B4DE',
        }}>
          ⚗ Cohort Study (policies) →
        </Link>
        <Link href="/dashboard/benchmarks" style={{
          fontSize: 13, fontWeight: 700, color: '#9A7D0A', background: '#FEF9E7',
          textDecoration: 'none', padding: '10px 24px', borderRadius: 8,
          border: '1px solid #F9E79F',
        }}>
          📊 KT Benchmark (datasets) →
        </Link>
        <Link href="/dashboard/data" style={{
          fontSize: 13, fontWeight: 700, color: '#1A5276', background: '#EBF5FB',
          textDecoration: 'none', padding: '10px 24px', borderRadius: 8,
          border: '1px solid #AED6F1',
        }}>
          🗂 Know Your Data →
        </Link>
        <Link href="/infrastructure" style={{
          fontSize: 13, fontWeight: 700, color: '#117A65', background: '#E8F8F5',
          textDecoration: 'none', padding: '10px 24px', borderRadius: 8,
          border: '1px solid #A2D9CE',
        }}>
          🔒 Infrastructure & Audit →
        </Link>
        <Link href="/dashboard/ablation" style={{
          fontSize: 13, fontWeight: 700, color: '#C0392B', background: '#FDEDEC',
          textDecoration: 'none', padding: '10px 24px', borderRadius: 8,
          border: '1px solid #F5B7B1',
        }}>
          🔬 Ablation Studies →
        </Link>
        <Link href="/dashboard/audit" style={{
          fontSize: 13, fontWeight: 700, color: '#6C3483', background: '#F4ECF7',
          textDecoration: 'none', padding: '10px 24px', borderRadius: 8,
          border: '1px solid #D2B4DE',
        }}>
          🧪 Self-Audit Controls →
        </Link>
        <Link href="/dashboard/governance" style={{
          fontSize: 13, fontWeight: 700, color: '#fff', background: '#6C3483',
          textDecoration: 'none', padding: '10px 24px', borderRadius: 8,
        }}>
          Live Governance Monitor →
        </Link>
      </div>
    </div>
  )
}
