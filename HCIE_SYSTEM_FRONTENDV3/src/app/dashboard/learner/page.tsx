'use client'

import { useEffect, useState, useCallback } from 'react'
import { useAuth } from '@/contexts/auth_context'
import Link from 'next/link'
import { useSearchParams, useRouter } from 'next/navigation'
import { getBackendUrl } from '@/lib/api/backend-url'
import { getAuthHeaders } from '@/lib/auth-headers'
import { useT } from '@/contexts/language_context'
import {
  K12_CONCEPTS, K12_EDGES,
  buildDemoMasteryMap, buildDemoTrajectory, conceptLabel,
} from '@/lib/catalog/k12-catalog'
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, PieChart, Pie, Cell, ReferenceLine,
} from 'recharts'
import { LearnerSelector } from '@/components/learners/LearnerSelector'

// ─── Types ────────────────────────────────────────────────────────────────────

interface ConceptMastery {
  concept: string
  label: string
  mastery: number
}

interface JTPoint {
  step: number
  jt: number
  delta_m?: number
  transfer?: number
}

interface TransferEvent {
  step: number
  concept: string
  amount: number
}

interface EnsembleWeight {
  name: string
  value: number
  color: string
}

interface AttributionEvent {
  step: number
  concept_id: string
  delta_m: number
  transfer_realized: number
  challenge: number
  uncertainty: number
  zpd: number
  transfer_prospective: number
  jt_value: number
  correct: boolean
}

interface DashboardData {
  userId: string
  concepts: ConceptMastery[]
  jtTrajectory: JTPoint[]
  transferEvents: TransferEvent[]
  ensembleWeights: EnsembleWeight[]
  attributionEvents: AttributionEvent[]
  totalTasks: number
  avgMastery: number
  totalTransfer: number
  isMock: boolean
  /** True when backend returned empty trajectory — show "complete attempts to populate" state. */
  isEmpty: boolean
  /** True when backend is unreachable / not authenticated. */
  isOffline: boolean
}

// ─── Constants ─────────────────────────────────────────────────────────────────

const BACKEND = getBackendUrl()
const TRANSFER_THRESHOLD = 0.08

const ENSEMBLE_COLORS = {
  bayesian:  '#2980B9',
  kalman:    '#8E44AD',
  lyapunov:  '#27AE60',
  ensemble:  '#E67E22',
}

// ─── Mock data generator (uses canonical K-12 catalog) ───────────────────────

function buildMockData(userId: string): DashboardData {
  // Use catalog-based mastery map (K-2 mostly mastered, K-5 in progress, K-8 just started)
  const masteryMap = buildDemoMasteryMap()

  const concepts: ConceptMastery[] = K12_CONCEPTS.map(c => ({
    concept: c.id,
    label: c.label,
    mastery: masteryMap[c.id] ?? 0,
  })).sort((a, b) => b.mastery - a.mastery)

  // JT trajectory from catalog helper
  const trajRaw = buildDemoTrajectory(30)
  const jtTrajectory: JTPoint[] = trajRaw.map(r => ({
    step: r.step,
    jt: r.jt,
    delta_m: r.delta_m,
    transfer: r.transfer_realized,
  }))

  // Transfer events where transfer_realized > threshold
  const transferEvents: TransferEvent[] = trajRaw
    .filter(r => r.transfer_realized > TRANSFER_THRESHOLD)
    .map(r => ({
      step: r.step,
      concept: r.conceptId,
      amount: r.transfer_realized,
    }))

  const ensembleWeights: EnsembleWeight[] = [
    { name: 'Bayesian BKT', value: 0.42, color: ENSEMBLE_COLORS.bayesian },
    { name: 'Kalman Filter', value: 0.31, color: ENSEMBLE_COLORS.kalman },
    { name: 'Bounded-stability (cut)', value: 0.27, color: ENSEMBLE_COLORS.lyapunov },
  ]

  const attributionEvents: AttributionEvent[] = trajRaw.slice(0, 25).map(r => ({
    step: r.step,
    concept_id: r.conceptId,
    delta_m: r.delta_m,
    transfer_realized: r.transfer_realized,
    challenge: 0.15 + Math.random() * 0.1,
    uncertainty: 0.08 + Math.random() * 0.08,
    zpd: 0.05 + Math.random() * 0.05,
    transfer_prospective: 0.02 + Math.random() * 0.04,
    jt_value: r.jt,
    correct: r.correct,
  }))

  const avgMastery = concepts.reduce((s, c) => s + c.mastery, 0) / concepts.length

  return {
    userId,
    concepts,
    jtTrajectory,
    transferEvents,
    ensembleWeights,
    attributionEvents,
    totalTasks: 30,
    avgMastery,
    totalTransfer: transferEvents.length,
    isMock: true,
    isEmpty: false,
    isOffline: true,
  }
}

/** Empty-state data — backend reachable but no learner history yet. */
function buildEmptyData(userId: string): DashboardData {
  return {
    userId,
    concepts: [],
    jtTrajectory: [],
    transferEvents: [],
    ensembleWeights: [],
    attributionEvents: [],
    totalTasks: 0,
    avgMastery: 0,
    totalTransfer: 0,
    isMock: false,
    isEmpty: true,
    isOffline: false,
  }
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function shortLabel(s: string) {
  const full = conceptLabel(s)
  // conceptLabel returns the id unchanged when the concept is unknown → pretty-print it
  const display = full === s
    ? s.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
    : full
  return display.substring(0, 20)
}

function masteryColor(v: number) {
  return v >= 0.7 ? '#27AE60' : v >= 0.45 ? '#E67E22' : '#C0392B'
}

function pct(v: number) { return `${(v * 100).toFixed(1)}%` }

// ─── Custom Tooltip ───────────────────────────────────────────────────────────

function JTTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null
  const d = payload[0]?.payload
  return (
    <div style={{ background: '#1A2332', color: '#fff', padding: '8px 12px',
                  borderRadius: 6, fontSize: 11 }}>
      <div style={{ fontWeight: 700, marginBottom: 4 }}>Task {label}</div>
      <div>JT Score: <strong>{(d.jt * 100).toFixed(1)}%</strong></div>
      {d.delta_m != null && <div>ΔM: <strong>+{(d.delta_m * 100).toFixed(2)}%</strong></div>}
      {d.transfer != null && d.transfer > TRANSFER_THRESHOLD && (
        <div style={{ color: '#E74C3C' }}>⚡ Transfer: {(d.transfer * 100).toFixed(1)}%</div>
      )}
    </div>
  )
}

function MasteryTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null
  const v = payload[0]?.value as number
  return (
    <div style={{ background: '#1A2332', color: '#fff', padding: '8px 12px',
                  borderRadius: 6, fontSize: 11 }}>
      <div style={{ fontWeight: 700, marginBottom: 2 }}>{label}</div>
      <div>Mastery: <strong style={{ color: masteryColor(v) }}>{pct(v)}</strong></div>
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

// ─── Main Page ────────────────────────────────────────────────────────────────

// Modality fit — the representation bandit's live Beta(α,β) belief per modality for
// THIS learner (from /v3/research/learner/{id}/representation-arms → interactions).
// Self-contained + quiet: renders nothing when the learner has no modality history.
const MODALITY_COLOR: Record<string, string> = {
  text: '#2980B9', mcq: '#8E44AD', video_question: '#C0392B', audio_listen: '#16A085', code: '#D35400',
}
function ModalityFitPanel({ userId, isMock }: { userId: string; isMock: boolean }) {
  const [arms, setArms] = useState<any[] | null>(null)
  useEffect(() => {
    if (!userId || isMock) { setArms([]); return }
    setArms(null)
    const token = typeof window !== 'undefined'
      ? (localStorage.getItem('hcie_auth_token') || localStorage.getItem('access_token') || '') : ''
    fetch(`${BACKEND}/v3/research/learner/${encodeURIComponent(userId)}/representation-arms`,
      { headers: token ? { Authorization: `Bearer ${token}` } : {}, signal: AbortSignal.timeout(7000) })
      .then(r => (r.ok ? r.json() : null))
      .then(d => setArms(d && d.status === 'ok' && Array.isArray(d.arms) ? d.arms : []))
      .catch(() => setArms([]))
  }, [userId, isMock])

  if (arms !== null && arms.length === 0) return null // quiet when no modality history
  const best = arms && arms.length
    ? arms.reduce((a, b) => (b.est_success_rate > (a?.est_success_rate ?? -1) ? b : a))
    : null
  return (
    <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10, padding: 16, marginBottom: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 4 }}>
        <div style={{ fontSize: 13, fontWeight: 800, color: '#1A2332' }}>Modality fit — why this format</div>
        <Link href="/review/methods" style={{ fontSize: 11, color: '#16A085', textDecoration: 'none', fontWeight: 700 }}>open the bandit sandbox →</Link>
      </div>
      <div style={{ fontSize: 11.5, color: '#718096', marginBottom: 12, lineHeight: 1.5 }}>
        The representation bandit&apos;s live Beta(α,β) belief per modality for this learner, from their real attempts.
        {best && <> Best so far: <b style={{ color: MODALITY_COLOR[best.representation] ?? '#1A2332' }}>{best.representation}</b> ({(best.est_success_rate * 100).toFixed(0)}% est).</>}
      </div>
      {arms === null ? (
        <div style={{ fontSize: 12, color: '#A0AEC0' }}>⟳ loading…</div>
      ) : (
        <div style={{ display: 'grid', gap: 8 }}>
          {arms.slice().sort((a, b) => b.est_success_rate - a.est_success_rate).map((a) => (
            <div key={a.representation} style={{ display: 'grid', gridTemplateColumns: '130px 1fr 150px', gap: 10, alignItems: 'center' }}>
              <span style={{ fontSize: 12, fontWeight: 700, color: MODALITY_COLOR[a.representation] ?? '#4A5568' }}>{a.representation}</span>
              <span style={{ height: 8, background: '#F1F5F9', borderRadius: 4, overflow: 'hidden' }}>
                <span style={{ display: 'block', width: `${Math.min(100, a.est_success_rate * 100)}%`, height: '100%', background: MODALITY_COLOR[a.representation] ?? '#94A3B8' }} />
              </span>
              <span style={{ fontSize: 11, fontFamily: 'ui-monospace, monospace', color: '#5A6776' }}>
                {(a.est_success_rate * 100).toFixed(0)}% · Beta({Number(a.alpha).toFixed(0)},{Number(a.beta).toFixed(0)}) · {a.attempts}×
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default function LearnerDashboardPage() {
  const t = useT()
  const { user, isAuthenticated, isLoading: authLoading } = useAuth()
  const searchParams = useSearchParams()
  // Allow instructor view to pass a specific learner user_id via ?user_id=...
  const queryUserId = searchParams?.get('user_id') ?? null
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'mastery' | 'trajectory' | 'attribution'>('mastery')
  const router = useRouter()
  const [showPicker, setShowPicker] = useState(false)

  const loadDashboard = useCallback(async (silent = false) => {
    if (!silent) setLoading(true)

    // queryUserId allows instructor view to deep-link to a specific learner
    const userId = queryUserId ?? user?.id ?? 'mock-user-1'

    // Backend unreachable or unauthenticated → offline mode (mock badge shown)
    // (When viewing a specific learner via queryUserId, allow even if !isAuthenticated in mock)
    if (!BACKEND || (!isAuthenticated && !queryUserId)) {
      await new Promise(r => setTimeout(r, 200))
      setData(buildMockData(userId))
      setLoading(false)
      return
    }

    try {
      const headers = getAuthHeaders()

      // Phase 14h: trajectory endpoint returns enriched per-row fields
      // (jt_value, jt_delta_m, jt_transfer, jt_challenge, jt_uncertainty,
      //  jt_zpd, mastery_before, mastery_after, transfer_amount, correctness, ...).
      // We can derive everything from this single call; ensemble-weights & jt-attribution
      // are supplementary aggregates.
      const [progRes, trajRes, weightsRes, attrRes] = await Promise.allSettled([
        fetch(`${BACKEND}/v3/learner/progress`, { headers, signal: AbortSignal.timeout(5000) }),
        fetch(`${BACKEND}/v3/research/learner/${userId}/governance/trajectory?limit=500`,
              { headers, signal: AbortSignal.timeout(6000) }),
        fetch(`${BACKEND}/v3/research/learner/${userId}/governance/ensemble-weights?limit=200`,
              { headers, signal: AbortSignal.timeout(5000) }),
        fetch(`${BACKEND}/v3/research/learner/${userId}/jt-attribution?limit=500`,
              { headers, signal: AbortSignal.timeout(5000) }),
      ])

      // ── Progress → concept mastery map (real) ──────────────────────────────
      let concepts: ConceptMastery[] = []
      if (progRes.status === 'fulfilled' && progRes.value.ok) {
        const pd = await progRes.value.json()
        const raw: Record<string, number> = pd.concepts ?? {}
        concepts = Object.entries(raw)
          .filter(([concept]) => concept !== 'unknown' && concept !== '')
          .map(([concept, mastery]) => ({
            concept,
            label: shortLabel(concept),
            mastery: Number(mastery),
          }))
          .sort((a, b) => b.mastery - a.mastery)
          .slice(0, 36)
      }

      // ── Trajectory → JT, transfer events, per-step attribution (real) ──────
      // Real shape: {trajectory: [{interaction_number, concept, jt_value, jt_delta_m, ...}]}
      let jtTrajectory: JTPoint[] = []
      let transferEvents: TransferEvent[] = []
      let attributionEvents: AttributionEvent[] = []
      if (trajRes.status === 'fulfilled' && trajRes.value.ok) {
        const td = await trajRes.value.json()
        const rows: any[] = td.trajectory ?? []
        // Per-concept mastery from THIS learner's own trajectory — works for any
        // class (real / synthetic / dataset). /v3/learner/progress only carries the
        // logged-in user's own state, so a viewed learner needs its trajectory.
        const tm: Record<string, number> = {}
        for (const r of rows) {
          if (r.concept != null && r.concept !== 'unknown' && r.mastery_after != null) tm[String(r.concept)] = Number(r.mastery_after)
        }
        const trajConcepts: ConceptMastery[] = Object.entries(tm)
          .map(([concept, mastery]) => ({ concept, label: shortLabel(concept), mastery }))
          .sort((a, b) => b.mastery - a.mastery)
          .slice(0, 36)
        if (trajConcepts.length) concepts = trajConcepts
        jtTrajectory = rows.map((r, i) => ({
          step: r.interaction_number ?? i + 1,
          jt: Number(r.jt_value ?? 0),
          delta_m: r.mastery_delta != null ? Number(r.mastery_delta) : undefined,
          transfer: r.transfer_amount != null ? Number(r.transfer_amount) : undefined,
        }))
        transferEvents = rows
          .filter(r => Number(r.transfer_amount ?? 0) > TRANSFER_THRESHOLD)
          .map(r => ({
            step: r.interaction_number ?? 0,
            concept: r.concept ?? '',
            amount: Number(r.transfer_amount),
          }))
        attributionEvents = rows.slice(-50).map((r, i) => ({
          step: r.interaction_number ?? i + 1,
          concept_id: r.concept ?? '',
          delta_m: Number(r.jt_delta_m ?? 0),
          transfer_realized: Number(r.jt_transfer ?? r.transfer_amount ?? 0),
          challenge: Number(r.jt_challenge ?? 0),
          uncertainty: Number(r.jt_uncertainty ?? 0),
          zpd: Number(r.jt_zpd ?? 0),
          transfer_prospective: 0,
          jt_value: Number(r.jt_value ?? 0),
          correct: Boolean(r.correctness),
        }))
      }

      // ── Ensemble weights (real, latest series entry) ───────────────────────
      // Real shape: {series: [{ensemble_weights: {bayesian, kalman, lyapunov}, ...}]}
      let ensembleWeights: EnsembleWeight[] = []
      if (weightsRes.status === 'fulfilled' && weightsRes.value.ok) {
        const wd = await weightsRes.value.json()
        const series: any[] = wd.series ?? []
        const latest = series[series.length - 1] ?? {}
        const nwv = latest.normalized_weight_vector
        const ew = (nwv && Object.keys(nwv).length > 0) ? nwv : (latest.ensemble_weights ?? {})
        const hasReal = ew.bayesian != null || ew.kalman != null || ew.lyapunov != null
        if (hasReal) {
          ensembleWeights = [
            { name: 'Bayesian BKT', value: Number(ew.bayesian ?? 0), color: ENSEMBLE_COLORS.bayesian },
            { name: 'Kalman Filter', value: Number(ew.kalman ?? 0), color: ENSEMBLE_COLORS.kalman },
            { name: 'Bounded-stability (cut)', value: Number(ew.lyapunov ?? 0), color: ENSEMBLE_COLORS.lyapunov },
          ]
        }
      }

      // ── If trajectory was empty, fall back to aggregate JT attribution shares ─
      // Real shape: {components: {delta_m: {share, ...}, transfer: {...}, ...}, summary}
      if (attributionEvents.length === 0 && attrRes.status === 'fulfilled' && attrRes.value.ok) {
        const ad = await attrRes.value.json()
        const comp = ad.components ?? {}
        const sum = ad.summary ?? {}
        if (comp.delta_m || comp.transfer || comp.challenge) {
          attributionEvents = [{
            step: 1,
            concept_id: 'aggregate',
            delta_m: Number(comp.delta_m?.share ?? 0),
            transfer_realized: Number(comp.transfer?.share ?? 0),
            challenge: Number(comp.challenge?.share ?? 0),
            uncertainty: Number(comp.uncertainty?.share ?? 0),
            zpd: Number(comp.zpd?.share ?? 0),
            transfer_prospective: 0,
            jt_value: Number(sum.jt_mean ?? 0),
            correct: true,
          }]
        }
      }

      // ── Empty-state detection — show "no data" instead of mock fallback ────
      // If learner has no progress and no trajectory, the system has no history yet.
      const hasAnyData =
        concepts.length > 0 ||
        jtTrajectory.length > 0 ||
        ensembleWeights.length > 0 ||
        attributionEvents.length > 0
      if (!hasAnyData) {
        setData(buildEmptyData(userId))
        return
      }

      const avgMastery = concepts.length
        ? concepts.reduce((s, c) => s + c.mastery, 0) / concepts.length
        : 0

      setData({
        userId,
        concepts,
        jtTrajectory,
        transferEvents,
        ensembleWeights,
        attributionEvents,
        totalTasks: jtTrajectory.length,
        avgMastery,
        totalTransfer: transferEvents.length,
        isMock: false,
        isEmpty: false,
        isOffline: false,
      })
    } catch {
      // Network error → mock (offline) badge so user sees it isn't real
      setData(buildMockData(userId))
    } finally {
      setLoading(false)
    }
  }, [user, isAuthenticated, queryUserId])

  useEffect(() => {
    if (authLoading) return
    loadDashboard()
    // Live-feel: silently refresh every 5s (HTTP polling — no WebSocket needed).
    const id = setInterval(() => loadDashboard(true), 5000)
    return () => clearInterval(id)
  }, [authLoading, loadDashboard, queryUserId])

  // ─── Render ───────────────────────────────────────────────────────────────

  if (loading || authLoading) {
    return (
      <div style={{ maxWidth: 1100, margin: '0 auto', padding: '40px 20px', textAlign: 'center',
                    color: '#718096' }}>
        <div style={{ fontSize: 36, marginBottom: 12 }}>⟳</div>
        <div>Loading your learning dashboard…</div>
      </div>
    )
  }

  if (!data) return null

  // ── Empty state: backend is live but learner has no recorded interactions yet ─
  if (data.isEmpty) {
    return (
      <div style={{ maxWidth: 700, margin: '0 auto', padding: '40px 20px' }}>
        <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 12,
                      padding: '36px 32px', textAlign: 'center' }}>
          <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.1em',
                        color: '#1A5276', textTransform: 'uppercase', marginBottom: 8 }}>
            Learner Dashboard
          </div>
          <div style={{ fontSize: 48, marginBottom: 12 }}>📊</div>
          <h2 style={{ fontSize: 20, fontWeight: 800, color: '#1A2332', margin: 0, marginBottom: 8 }}>
            No learning history yet
          </h2>
          <div style={{ fontSize: 13, color: '#4A5568', lineHeight: 1.6, marginBottom: 20 }}>
            <strong>User ID:</strong>{' '}
            <code style={{ background: '#EDF2F7', padding: '1px 5px', borderRadius: 3 }}>
              {data.userId}
            </code>
            <br />
            The backend is connected but no interactions have been recorded for this account yet.
            <br />
            Complete a few attempts in <strong>/learn</strong> to populate:
            <ul style={{ textAlign: 'left', maxWidth: 480, margin: '12px auto 0',
                         color: '#4A5568', lineHeight: 1.8 }}>
              <li><code>interactions</code> — per-attempt log</li>
              <li><code>learning_state</code> — per-concept mastery</li>
              <li><code>trajectory_records</code> — full JT/ensemble/transfer snapshot</li>
              <li><code>experiment_trajectories</code> — phase-A research-grade attribution</li>
            </ul>
          </div>
          <div style={{ display: 'flex', gap: 10, justifyContent: 'center' }}>
            <Link href="/learn" style={{
              fontSize: 13, fontWeight: 700, color: '#fff', background: '#1A5276',
              textDecoration: 'none', padding: '10px 24px', borderRadius: 8,
            }}>
              Start a Session →
            </Link>
            <button onClick={() => loadDashboard()} style={{
              fontSize: 13, fontWeight: 600, color: '#4A5568',
              padding: '10px 24px', borderRadius: 8,
              border: '1px solid #CBD5E0', background: '#fff', cursor: 'pointer',
            }}>
              ↻ Reload
            </button>
          </div>
        </div>
      </div>
    )
  }

  const topConcept = data.concepts[0]
  const bottomConcept = data.concepts[data.concepts.length - 1]
  const TABS = [
    { id: 'mastery', label: 'Mastery Map' },
    { id: 'trajectory', label: 'JT Trajectory' },
    { id: 'attribution', label: 'Attribution Log' },
  ] as const

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: '24px 20px' }}>

      {/* ── Mock-data banner ───────────────────────────────────────────────── */}
      {/* When the backend is unreachable / unauthenticated, buildMockData() supplies
          fabricated mastery/challenge/uncertainty/ZPD numbers. Surface that loudly so
          these illustrative figures are never mistaken for real measurements. */}
      {data.isMock && (
        <div role="alert" style={{
          background: '#FEF9E7', border: '1px solid #F9E79F', borderLeft: '5px solid #D4AC0D',
          borderRadius: 8, padding: '14px 18px', marginBottom: 20,
        }}>
          <div style={{ fontSize: 13, fontWeight: 800, color: '#7D6008', marginBottom: 4 }}>
            ⚠ {t('mockNotice.title')}
          </div>
          <div style={{ fontSize: 12, color: '#7D6008', lineHeight: 1.5 }}>
            {t('mockNotice.body')}
          </div>
        </div>
      )}

      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start',
                    marginBottom: 20 }}>
        <div>
          <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.1em',
                        color: '#1A5276', textTransform: 'uppercase', marginBottom: 4 }}>
            {t('learner.eyebrow')}
          </div>
          <h1 style={{ fontSize: 22, fontWeight: 800, color: '#1A2332', margin: 0 }}>
            {user?.username ?? t('common.learners')} — {t('learner.title')}
          </h1>
          <div style={{ fontSize: 12, color: '#718096', marginTop: 2 }}>
            User ID: <code style={{ background: '#EDF2F7', padding: '1px 5px', borderRadius: 3 }}>
              {data.userId}
            </code>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          {data.isMock && (
            <span style={{ fontSize: 10, fontWeight: 700, color: '#7D6008',
                           background: '#FEF9E7', border: '1px solid #F9E79F',
                           borderRadius: 4, padding: '3px 8px' }}>
              ○ Mock data
            </span>
          )}
          {!data.isMock && (
            <span style={{ fontSize: 10, fontWeight: 700, color: '#1E8449',
                           background: '#D5F5E3', border: '1px solid #A9DFBF',
                           borderRadius: 4, padding: '3px 8px' }}>
              ● Live backend
            </span>
          )}
          <button onClick={() => setShowPicker(o => !o)} style={{
            fontSize: 12, fontWeight: 700, color: '#fff', background: '#1A5276',
            border: 'none', borderRadius: 6, padding: '5px 12px', cursor: 'pointer',
          }}>
            ⇄ Switch learner
          </button>
          <button onClick={() => loadDashboard()} style={{
            fontSize: 12, color: '#4A5568', background: '#EDF2F7',
            border: '1px solid #CBD5E0', borderRadius: 6,
            padding: '5px 12px', cursor: 'pointer',
          }}>
            ↻ Refresh
          </button>
          <Link href="/learn" style={{
            fontSize: 12, color: '#fff', background: '#1A5276',
            textDecoration: 'none', padding: '5px 12px',
            border: '1px solid #1A5276', borderRadius: 6, fontWeight: 700,
          }}>
            ← Back to Learn
          </Link>
        </div>
      </div>

      {showPicker && (
        <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10, padding: 14, marginBottom: 20 }}>
          <LearnerSelector compact selectedId={queryUserId ?? undefined}
            onSelect={l => { setShowPicker(false); router.push(`/dashboard/learner?user_id=${encodeURIComponent(l.user_id)}`) }} />
        </div>
      )}

      <ModalityFitPanel userId={data.userId} isMock={data.isMock} />

      {/* ── Stat strip ─────────────────────────────────────────────────────── */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 24 }}>
        <StatCard
          label="Tasks Completed"
          value={data.totalTasks}
          sub="interactions recorded"
          color="#2980B9"
        />
        <StatCard
          label="Avg Mastery"
          value={pct(data.avgMastery)}
          sub="across all concepts"
          color={masteryColor(data.avgMastery)}
        />
        <StatCard
          label="Transfer Events"
          value={data.totalTransfer}
          sub="cross-concept activations"
          color="#C0392B"
        />
        <StatCard
          label="Concepts Tracked"
          value={data.concepts.length}
          sub="in knowledge graph"
          color="#8E44AD"
        />
      </div>

      {/* ── Concept highlights ─────────────────────────────────────────────── */}
      {data.concepts.length > 0 && (
        <div style={{ display: 'grid',
                      gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
                      gap: 12, marginBottom: 24 }}>
          <div style={{ background: '#D5F5E3', border: '1px solid #A9DFBF', borderRadius: 10,
                        padding: '12px 16px' }}>
            <div style={{ fontSize: 10, color: '#1E8449', fontWeight: 700,
                          textTransform: 'uppercase', marginBottom: 4 }}>
              Strongest Concept
            </div>
            <div style={{ fontSize: 15, fontWeight: 800, color: '#1E8449' }}>
              {topConcept.label}
            </div>
            <div style={{ fontSize: 22, fontWeight: 800, color: '#1E8449',
                          fontVariantNumeric: 'tabular-nums' }}>
              {pct(topConcept.mastery)}
            </div>
          </div>
          <div style={{ background: '#FDEDEC', border: '1px solid #F5B7B1', borderRadius: 10,
                        padding: '12px 16px' }}>
            <div style={{ fontSize: 10, color: '#C0392B', fontWeight: 700,
                          textTransform: 'uppercase', marginBottom: 4 }}>
              Needs Attention
            </div>
            <div style={{ fontSize: 15, fontWeight: 800, color: '#C0392B' }}>
              {bottomConcept.label}
            </div>
            <div style={{ fontSize: 22, fontWeight: 800, color: '#C0392B',
                          fontVariantNumeric: 'tabular-nums' }}>
              {pct(bottomConcept.mastery)}
            </div>
          </div>
        </div>
      )}

      {/* ── Tabs ───────────────────────────────────────────────────────────── */}
      <div style={{ display: 'flex', gap: 2, marginBottom: 16, borderBottom: '2px solid #E2E8F0' }}>
        {TABS.map(t => (
          <button key={t.id} onClick={() => setActiveTab(t.id)} style={{
            padding: '8px 18px', fontSize: 13, fontWeight: 600,
            background: 'none', border: 'none', cursor: 'pointer',
            color: activeTab === t.id ? '#1A5276' : '#718096',
            borderBottom: activeTab === t.id ? '2px solid #1A5276' : '2px solid transparent',
            marginBottom: -2,
          }}>
            {t.label}
          </button>
        ))}
      </div>

      {/* ── Tab: Mastery Map ───────────────────────────────────────────────── */}
      {activeTab === 'mastery' && (
        <div style={{ display: 'grid',
                      gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
                      gap: 20 }}>
          {/* Bar chart */}
          <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10,
                        padding: '18px 20px' }}>
            <SectionHeader
              title="Per-Concept Mastery"
              sub="Sorted by mastery level — JT + Bayesian ensemble estimate"
            />
            <ResponsiveContainer width="100%" height={Math.max(200, data.concepts.length * 28)}>
              <BarChart
                data={data.concepts}
                layout="vertical"
                margin={{ left: 8, right: 40, top: 0, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#F1F5F9" />
                <XAxis
                  type="number"
                  domain={[0, 1]}
                  tickFormatter={v => `${(v * 100).toFixed(0)}%`}
                  tick={{ fontSize: 10, fill: '#A0AEC0' }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  type="category"
                  dataKey="label"
                  width={110}
                  tick={{ fontSize: 11, fill: '#4A5568' }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip content={<MasteryTooltip />} />
                <ReferenceLine x={0.7} stroke="#27AE60" strokeDasharray="4 4" strokeWidth={1.5} />
                <Bar dataKey="mastery" radius={[0, 4, 4, 0]}>
                  {data.concepts.map((entry) => (
                    <Cell key={entry.concept} fill={masteryColor(entry.mastery)} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <div style={{ display: 'flex', gap: 16, marginTop: 10, fontSize: 10, color: '#718096' }}>
              <span>
                <span style={{ color: '#27AE60', fontWeight: 700 }}>●</span> Mastered (≥70%)
              </span>
              <span>
                <span style={{ color: '#E67E22', fontWeight: 700 }}>●</span> Developing (45–70%)
              </span>
              <span>
                <span style={{ color: '#C0392B', fontWeight: 700 }}>●</span> Needs work (&lt;45%)
              </span>
              <span style={{ marginLeft: 'auto' }}>
                <span style={{ color: '#27AE60', fontWeight: 700 }}>– –</span> Mastery threshold
              </span>
            </div>
          </div>

          {/* Ensemble weights */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10,
                          padding: '18px 20px' }}>
              <SectionHeader
                title="Ensemble Weights"
                sub="Current MAB weighting of mastery estimators"
              />
              <ResponsiveContainer width="100%" height={160}>
                <PieChart>
                  <Pie
                    data={data.ensembleWeights}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={65}
                    innerRadius={38}
                    paddingAngle={3}
                  >
                    {data.ensembleWeights.map((e, i) => (
                      <Cell key={i} fill={e.color} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(v: any) => `${(Number(v) * 100).toFixed(1)}%`} />
                </PieChart>
              </ResponsiveContainer>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {data.ensembleWeights.map(w => (
                  <div key={w.name} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div style={{ width: 10, height: 10, borderRadius: 2, background: w.color,
                                  flexShrink: 0 }} />
                    <div style={{ flex: 1, fontSize: 11, color: '#4A5568' }}>{w.name}</div>
                    <div style={{ fontSize: 12, fontWeight: 700, color: w.color,
                                  fontVariantNumeric: 'tabular-nums' }}>
                      {pct(w.value)}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Transfer events summary */}
            <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10,
                          padding: '18px 20px' }}>
              <SectionHeader
                title="Transfer Events"
                sub={`${data.transferEvents.length} cross-concept activations`}
              />
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6, maxHeight: 160,
                            overflowY: 'auto' }}>
                {data.transferEvents.length === 0 ? (
                  <div style={{ fontSize: 12, color: '#A0AEC0', textAlign: 'center',
                                padding: '20px 0' }}>
                    No transfer events yet.<br />Keep learning to activate edges!
                  </div>
                ) : data.transferEvents.map((t, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8,
                                        fontSize: 11 }}>
                    <span style={{ color: '#C0392B', fontWeight: 700, fontSize: 12 }}>⚡</span>
                    <span style={{ flex: 1, color: '#4A5568' }}>
                      Task #{t.step} — {shortLabel(t.concept)}
                    </span>
                    <span style={{ fontWeight: 700, color: '#C0392B',
                                   fontVariantNumeric: 'tabular-nums' }}>
                      +{pct(t.amount)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── Tab: JT Trajectory ─────────────────────────────────────────────── */}
      {activeTab === 'trajectory' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10,
                        padding: '18px 20px' }}>
            <SectionHeader
              title="Joint Transfer (JT) Score — Learning Trajectory"
              sub="Composite governance objective over time. ⚡ marks transfer activation events."
            />
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={data.jtTrajectory}
                         margin={{ left: 0, right: 16, top: 8, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                <XAxis
                  dataKey="step"
                  tick={{ fontSize: 10, fill: '#A0AEC0' }}
                  axisLine={false} tickLine={false}
                  label={{ value: 'Task #', position: 'insideBottom', offset: -4,
                           fontSize: 10, fill: '#A0AEC0' }}
                />
                <YAxis
                  domain={[0, 1]}
                  tickFormatter={v => `${(v * 100).toFixed(0)}%`}
                  tick={{ fontSize: 10, fill: '#A0AEC0' }}
                  axisLine={false} tickLine={false}
                  width={42}
                />
                <Tooltip content={<JTTooltip />} />
                <ReferenceLine y={0.5} stroke="#CBD5E0" strokeDasharray="4 4" strokeWidth={1} />
                <Line
                  type="monotone"
                  dataKey="jt"
                  stroke="#1A5276"
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4, fill: '#1A5276' }}
                />
                <Line
                  type="monotone"
                  dataKey="delta_m"
                  stroke="#27AE60"
                  strokeWidth={1.5}
                  strokeDasharray="4 2"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
            <div style={{ display: 'flex', gap: 20, marginTop: 10, fontSize: 10, color: '#718096' }}>
              <span><span style={{ color: '#1A5276', fontWeight: 700 }}>—</span> JT Score</span>
              <span><span style={{ color: '#27AE60', fontWeight: 700 }}>- -</span> ΔM (Mastery Delta)</span>
              <span><span style={{ color: '#CBD5E0', fontWeight: 700 }}>– –</span> JT = 0.5 reference</span>
            </div>
          </div>

          {/* Ensemble weights over time */}
          <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10,
                        padding: '18px 20px' }}>
            <SectionHeader
              title="Current Ensemble State"
              sub="How the MAB weights the three mastery estimators"
            />
            <div style={{ display: 'grid',
                          gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
                          gap: 12 }}>
              {data.ensembleWeights.map(w => (
                <div key={w.name} style={{ border: `2px solid ${w.color}40`,
                                           borderRadius: 10, padding: '14px 16px',
                                           background: `${w.color}08` }}>
                  <div style={{ fontSize: 11, color: w.color, fontWeight: 700, marginBottom: 6 }}>
                    {w.name}
                  </div>
                  <div style={{ fontSize: 26, fontWeight: 800, color: w.color,
                                fontVariantNumeric: 'tabular-nums' }}>
                    {pct(w.value)}
                  </div>
                  <div style={{ marginTop: 8, height: 6, background: '#E2E8F0', borderRadius: 3 }}>
                    <div style={{ height: '100%', width: `${w.value * 100}%`,
                                  background: w.color, borderRadius: 3,
                                  transition: 'width 0.4s' }} />
                  </div>
                  <div style={{ fontSize: 10, color: '#718096', marginTop: 6 }}>
                    {w.name === 'Bayesian BKT' && 'Item-response model, calibrated per concept'}
                    {w.name === 'Kalman Filter' && 'Continuous state estimation with noise model'}
                    {w.name === 'Bounded-stability (cut)' && 'Ex-Lyapunov heuristic, removed from fusion (weight 0)'}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ── Tab: Attribution Log ───────────────────────────────────────────── */}
      {activeTab === 'attribution' && (
        <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10,
                      padding: '18px 20px' }}>
          <SectionHeader
            title="JT Attribution Log"
            sub="Per-task decomposition of the 6D governance signal. Each row is one task attempt."
          />
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11 }}>
              <thead>
                <tr style={{ borderBottom: '2px solid #E2E8F0' }}>
                  {['#', 'Concept', 'Result', 'JT Score', 'ΔM', 'T_realized', 'Challenge',
                    'Uncertainty', 'ZPD'].map(h => (
                    <th key={h} style={{ padding: '6px 10px', textAlign: h === '#' ? 'center' : 'left',
                                         color: '#718096', fontWeight: 700, whiteSpace: 'nowrap' }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.attributionEvents.map((e, i) => (
                  <tr key={i} style={{
                    borderBottom: '1px solid #F7FAFC',
                    background: i % 2 === 0 ? '#fff' : '#FAFAFA',
                  }}>
                    <td style={{ padding: '6px 10px', textAlign: 'center',
                                  color: '#A0AEC0', fontVariantNumeric: 'tabular-nums' }}>
                      {e.step}
                    </td>
                    <td style={{ padding: '6px 10px', color: '#4A5568', maxWidth: 120,
                                  overflow: 'hidden', textOverflow: 'ellipsis',
                                  whiteSpace: 'nowrap' }}>
                      {shortLabel(e.concept_id)}
                    </td>
                    <td style={{ padding: '6px 10px' }}>
                      <span style={{
                        fontSize: 10, fontWeight: 700,
                        color: e.correct ? '#1E8449' : '#C0392B',
                        background: e.correct ? '#D5F5E3' : '#FDEDEC',
                        borderRadius: 4, padding: '2px 6px',
                      }}>
                        {e.correct ? '✓' : '✗'}
                      </span>
                    </td>
                    <td style={{ padding: '6px 10px', fontWeight: 700,
                                  color: '#1A5276', fontVariantNumeric: 'tabular-nums' }}>
                      {(e.jt_value * 100).toFixed(1)}%
                    </td>
                    <td style={{ padding: '6px 10px', color: e.delta_m >= 0 ? '#27AE60' : '#C0392B',
                                  fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>
                      {e.delta_m >= 0 ? '+' : ''}{(e.delta_m * 100).toFixed(2)}%
                    </td>
                    <td style={{ padding: '6px 10px', fontVariantNumeric: 'tabular-nums' }}>
                      {e.transfer_realized > TRANSFER_THRESHOLD ? (
                        <span style={{ color: '#C0392B', fontWeight: 700 }}>
                          ⚡ {(e.transfer_realized * 100).toFixed(1)}%
                        </span>
                      ) : (
                        <span style={{ color: '#A0AEC0' }}>
                          {(e.transfer_realized * 100).toFixed(1)}%
                        </span>
                      )}
                    </td>
                    {[e.challenge, e.uncertainty, e.zpd].map((v, j) => (
                      <td key={j} style={{ padding: '6px 10px', color: '#4A5568',
                                            fontVariantNumeric: 'tabular-nums' }}>
                        {(v * 100).toFixed(1)}%
                      </td>
                    ))}
                  </tr>
                ))}
                {data.attributionEvents.length === 0 && (
                  <tr>
                    <td colSpan={9} style={{ padding: '24px', textAlign: 'center',
                                             color: '#A0AEC0', fontSize: 12 }}>
                      No attribution events recorded yet. Complete tasks in the Learn section.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── Footer nav ─────────────────────────────────────────────────────── */}
      <div style={{ display: 'flex', gap: 10, marginTop: 24, justifyContent: 'center' }}>
        <Link href="/learn" style={{
          fontSize: 13, fontWeight: 700, color: '#fff', background: '#1A5276',
          textDecoration: 'none', padding: '10px 24px', borderRadius: 8,
        }}>
          ← Continue Learning
        </Link>
        <Link href="/dashboard/instructor" style={{
          fontSize: 13, fontWeight: 600, color: '#4A5568',
          textDecoration: 'none', padding: '10px 24px', borderRadius: 8,
          border: '1px solid #CBD5E0', background: '#fff',
        }}>
          Instructor View →
        </Link>
        <Link href="/dashboard/governance" style={{
          fontSize: 13, fontWeight: 600, color: '#4A5568',
          textDecoration: 'none', padding: '10px 24px', borderRadius: 8,
          border: '1px solid #CBD5E0', background: '#fff',
        }}>
          Governance Monitor →
        </Link>
      </div>
    </div>
  )
}
