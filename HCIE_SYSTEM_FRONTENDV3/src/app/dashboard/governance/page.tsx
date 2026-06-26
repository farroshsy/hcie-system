'use client'

import React, { useEffect, useState, useRef, useCallback } from 'react'
import { useAuth } from '@/contexts/auth_context'
import Link from 'next/link'
import { getBackendUrl } from '@/lib/api/backend-url'
import { getAuthHeaders } from '@/lib/auth-headers'
import { useT } from '@/contexts/language_context'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine,
  BarChart, Bar, Cell,
} from 'recharts'
import { conceptLabel } from '@/lib/catalog/k12-catalog'
import { Panel, Tag, Callout, SectionTitle, Eyebrow } from '@/lib/ui/primitives'
import { t as ui } from '@/lib/ui/theme'
import PageGuide, { TourStep } from '@/components/help/PageGuide'

// ─── Types ────────────────────────────────────────────────────────────────────

type PipelineStage =
  | 'kafka_event'
  | 'dag_lookup'
  | 'jt_attribution'
  | 'mastery_update'
  | 'recommendation'

type StageStatus = 'idle' | 'active' | 'done' | 'error'

interface PipelineState {
  stage: PipelineStage
  status: StageStatus
  latencyMs: number
  detail: string
}

interface GovernanceSnapshot {
  timestamp: string
  jtScore: number
  masteryDelta: number
  transferRealized: number
  kafkaLag: number
  outboxPending: number
  dlqCount: number
  concept: string
  policy: string
  confidence: number
  governanceWeights: Record<string, number>
  ensembleWeights: {
    bayesian: number
    kalman: number
    lyapunov: number
  }
}

interface EventLog {
  id: string
  timestamp: string
  type: string
  concept: string
  mastery: number
  jtScore: number
  transferFired: boolean
}

/**
 * Per-interaction trace row — the canonical evidence for one closed-loop iteration.
 * Sourced from /v3/frontend/dashboard/session-trace/{user_id} which joins
 * trajectory_records (per-interaction snapshot) with experiment_trajectories
 * (phase-A JT decomposition, ensemble weights, attribution scores).
 */
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
  jt_volatility: number | null
  jt_components: {
    delta_m: number | null
    transfer: number | null
    challenge: number | null
    uncertainty: number | null
    zpd: number | null
  }
  jt_unclamped: number | null
  jt_clamped: number | null
  ensemble: {
    bayesian_before: { alpha: number | null; beta: number | null }
    bayesian_after: { alpha: number | null; beta: number | null }
    kalman_before: { mastery: number | null; covariance: number | null }
    kalman_after: { mastery: number | null; covariance: number | null }
    lyapunov_before: number | null
    lyapunov_after: number | null
    weights: Record<string, number> | null
    normalized_weights: Record<string, number> | null
    attribution_scores: Record<string, any> | null
  }
  exploration: {
    pressure: number | null
    cv_window: number | null
    regime: string | null
    uncertainty_weight: number | null
    candidate_scores: Record<string, number> | null
  }
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
  confidence_before: number | null
  confidence_after: number | null
  uncertainty_before: number | null
  uncertainty_after: number | null
  stability_index: number | null
}

// ─── Constants ─────────────────────────────────────────────────────────────────

const BACKEND = getBackendUrl()
const POLL_INTERVAL_MS = 5000
const MAX_HISTORY = 60
const TRANSFER_THRESHOLD = 0.08

const PIPELINE_META: Record<PipelineStage, { label: string; icon: string; desc: string }> = {
  kafka_event:    { label: 'Kafka Event',       icon: '⚡', desc: 'Learner attempt published to topic hcie.learning_events' },
  dag_lookup:     { label: 'DAG Lookup',        icon: '🗺', desc: 'Knowledge graph traversal — prerequisite edge resolution' },
  jt_attribution: { label: 'JT Attribution',   icon: '⚖', desc: '6D decomposition: ΔM · T_realized · challenge · uncertainty · ZPD · T_prospective' },
  mastery_update: { label: 'Mastery Update',   icon: '📈', desc: 'Ensemble write — 2-learner Kalman + Bayesian fusion updated in projection store' },
  recommendation: { label: 'Recommendation',  icon: '🎯', desc: 'MAB selects next concept & modality via JT-informed bandit policy' },
}

const STAGE_ORDER: PipelineStage[] = [
  'kafka_event', 'dag_lookup', 'jt_attribution', 'mastery_update', 'recommendation',
]

// ─── Mock pipeline simulation ─────────────────────────────────────────────────

let mockStep = 0
// Canonical K-12 CS concept IDs — mirrors concept_dependencies table
const mockConcepts = [
  'k5_algorithms',
  'k8_control',
  'k5_modularity',
  'k8_data_collection',
  'k8_variables',
  'k2_algorithms',
  'k5_variables',
  'k8_networks_communication',
]

function buildMockSnapshot(): GovernanceSnapshot {
  mockStep++
  const concept = mockConcepts[mockStep % mockConcepts.length]
  const jt = 0.4 + (mockStep / 100) * 0.3 + (Math.random() - 0.5) * 0.08
  return {
    timestamp: new Date().toISOString(),
    jtScore: Math.max(0, Math.min(1, jt)),
    masteryDelta: (Math.random() - 0.2) * 0.06,
    transferRealized: mockStep % 5 === 0 ? 0.15 + Math.random() * 0.08 : 0.01 + Math.random() * 0.04,
    kafkaLag: Math.floor(Math.random() * 3),
    outboxPending: Math.floor(Math.random() * 5),
    dlqCount: 0,
    concept,
    policy: 'hcie',
    confidence: 0.6 + Math.random() * 0.3,
    governanceWeights: {
      delta_m: 0.35 + Math.random() * 0.1,
      transfer: 0.25 + Math.random() * 0.1,
      challenge: 0.15 + Math.random() * 0.05,
      uncertainty: 0.10 + Math.random() * 0.05,
      zpd: 0.08 + Math.random() * 0.04,
      transfer_prospective: 0.04 + Math.random() * 0.02,
    },
    ensembleWeights: {
      bayesian: 0.38 + (Math.random() - 0.5) * 0.04,
      kalman:   0.32 + (Math.random() - 0.5) * 0.04,
      lyapunov: 0.30 + (Math.random() - 0.5) * 0.04,
    },
  }
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function shortConcept(c: string) {
  const full = conceptLabel(c)
  // Fall back to prettified id if concept is not in catalog
  return full === c
    ? c.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
    : full
}

function pct(v: number, dec = 1) { return `${(v * 100).toFixed(dec)}%` }

function statusColor(s: StageStatus) {
  return { idle: '#CBD5E0', active: '#E67E22', done: '#27AE60', error: '#C0392B' }[s]
}

function timeStr(iso: string) {
  return new Date(iso).toLocaleTimeString('en-US', { hour12: false })
}

// ─── JT Tooltip ──────────────────────────────────────────────────────────────

function JTTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null
  const d = payload[0]?.payload
  return (
    <div style={{ background: '#1A2332', color: '#fff', padding: '8px 12px',
                  borderRadius: 6, fontSize: 11 }}>
      <div style={{ fontWeight: 700, marginBottom: 4 }}>{d?.time}</div>
      {payload.map((p: any) => (
        <div key={p.dataKey}>
          {p.name}: <strong>{(p.value * 100).toFixed(2)}%</strong>
        </div>
      ))}
    </div>
  )
}

// ─── Pipeline Stage component ─────────────────────────────────────────────────

function PipelineStageCard({ stage, status, latencyMs, detail }: PipelineState) {
  const meta = PIPELINE_META[stage]
  const tn = status === 'active' ? ui.tone.warn
    : status === 'done' ? ui.tone.ok
    : status === 'error' ? ui.tone.bad
    : ui.tone.neutral
  const detailFg = status === 'done' ? ui.tone.ok.fg : ui.tone.warn.fg

  return (
    <div style={{
      background: status === 'idle' ? ui.color.subtle : tn.bg,
      border: `1px solid ${tn.border}`,
      borderRadius: ui.radius.lg, padding: `${ui.space.md}px ${ui.space.md + 2}px`, flex: 1,
      transition: 'all 0.3s ease',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: ui.space.sm, marginBottom: ui.space.sm }}>
        <span style={{ fontSize: ui.font.size.xl }}>{meta.icon}</span>
        <div>
          <div style={{ fontSize: ui.font.size.base, fontWeight: ui.font.weight.bold, color: ui.color.ink }}>{meta.label}</div>
          {status === 'active' && (
            <div style={{ fontSize: ui.font.size.xs, color: ui.tone.warn.fg, fontWeight: ui.font.weight.bold }}>● ACTIVE</div>
          )}
          {status === 'done' && (
            <div style={{ fontSize: ui.font.size.xs, color: ui.tone.ok.fg, fontWeight: ui.font.weight.bold }}>✓ {latencyMs}ms</div>
          )}
          {status === 'idle' && (
            <div style={{ fontSize: ui.font.size.xs, color: ui.color.faint }}>waiting</div>
          )}
          {status === 'error' && (
            <div style={{ fontSize: ui.font.size.xs, color: ui.tone.bad.fg, fontWeight: ui.font.weight.bold }}>✗ error</div>
          )}
        </div>
      </div>
      <div style={{ fontSize: ui.font.size.xs, color: ui.color.muted, lineHeight: 1.5 }}>{meta.desc}</div>
      {detail && status !== 'idle' && (
        <div style={{ marginTop: ui.space.sm, fontSize: ui.font.size.xs, fontWeight: ui.font.weight.medium,
                      color: detailFg,
                      fontFamily: 'monospace' }}>
          {detail}
        </div>
      )}
    </div>
  )
}

// ─── Guided walkthrough steps ───────────────────────────────────────────────

const STEPS: TourStep[] = [
  {
    selector: '[data-tour="live-badge"]',
    title: { en: 'Live or mock data', id: 'Data live atau mock' },
    body: {
      en: 'This badge shows whether the panel is reading real backend events or simulated mock data. Green means the live system is feeding it.',
      id: 'Badge ini menunjukkan apakah panel membaca event backend nyata atau data mock simulasi. Hijau berarti sistem live yang memberinya data.',
    },
  },
  {
    selector: '[data-tour="pipeline-strip"]',
    title: { en: 'The 5-stage pipeline', id: 'Pipeline 5 tahap' },
    body: {
      en: 'Each learner attempt flows left to right through these five stages: Kafka, DAG, JT, mastery, recommendation. Watch a card light up as a real event is processed.',
      id: 'Setiap percobaan learner mengalir dari kiri ke kanan melewati lima tahap ini: Kafka, DAG, JT, mastery, recommendation. Perhatikan kartu menyala saat event nyata diproses.',
    },
  },
  {
    selector: '[data-tour="jt-trace-card"]',
    title: { en: 'Latest interaction trace', id: 'Trace interaksi terbaru' },
    body: {
      en: 'This card is the raw evidence for one closed loop iteration, including JT attribution and the mastery-before to mastery-after change. Read it to see exactly what the system computed.',
      id: 'Kartu ini adalah bukti mentah untuk satu iterasi closed-loop, termasuk JT attribution dan perubahan mastery-before ke mastery-after. Baca untuk melihat persis apa yang dihitung sistem.',
    },
  },
  {
    selector: '[data-tour="jt-chart"]',
    title: { en: 'JT score over time', id: 'Skor JT dari waktu ke waktu' },
    body: {
      en: 'This chart plots the JT score across recent governance ticks. Hover any point to see the exact JT, mastery delta, and transfer values for that moment.',
      id: 'Chart ini memplot skor JT di sepanjang governance tick terbaru. Arahkan kursor ke titik mana pun untuk melihat nilai JT, mastery delta, dan transfer pada saat itu.',
    },
  },
  {
    selector: '[data-tour="gov-weights"]',
    title: { en: '6D governance weights', id: 'Bobot governance 6D' },
    body: {
      en: 'The JT score is built from six components. These bars show how much each one contributes right now. Longer bar means a bigger share of the decision.',
      id: 'Skor JT dibentuk dari enam komponen. Bar ini menunjukkan seberapa besar kontribusi masing-masing saat ini. Bar lebih panjang berarti porsi keputusan lebih besar.',
    },
  },
  {
    selector: '[data-tour="ensemble-weights"]',
    title: { en: 'Mastery ensemble weights', id: 'Bobot ensemble mastery' },
    body: {
      en: 'Mastery is estimated by blending several models, mainly Bayesian BKT and a Kalman filter. These cards show each model current weight in the fusion.',
      id: 'Mastery diperkirakan dengan memadukan beberapa model, terutama Bayesian BKT dan Kalman filter. Kartu ini menunjukkan bobot setiap model dalam fusion saat ini.',
    },
  },
]

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function GovernanceMonitorPage() {
  const t = useT()
  const { user, isAuthenticated, isLoading: authLoading } = useAuth()

  const [history, setHistory] = useState<GovernanceSnapshot[]>([])
  const [current, setCurrent] = useState<GovernanceSnapshot | null>(null)
  const [latestTrace, setLatestTrace] = useState<InteractionTrace | null>(null)
  const [traceHistory, setTraceHistory] = useState<InteractionTrace[]>([])
  const [pipeline, setPipeline] = useState<PipelineState[]>(
    STAGE_ORDER.map(s => ({ stage: s, status: 'idle' as StageStatus, latencyMs: 0, detail: '' }))
  )
  const [eventLog, setEventLog] = useState<EventLog[]>([])
  const [isLive, setIsLive] = useState(true)
  const [isMock, setIsMock] = useState(false)
  const [isEmpty, setIsEmpty] = useState(false)
  const [tickCount, setTickCount] = useState(0)
  const [activeUserId, setActiveUserId] = useState<string | null>(null)

  // ── ADC Live Status ───────────────────────────────────────────────────────
  type AdcDimension = {
    name: string
    mean: number
    std: number
    signal_ratio: number
    status: 'ACTIVE' | 'structural_zero'
    description: string
  }
  const ADC_FALLBACK: AdcDimension[] = [
    { name: 'challenge',    mean: 0.158, std: 0.035, signal_ratio: 0.22, status: 'ACTIVE',
      description: 'Difficulty relative to learner ability (IRT-based)' },
    { name: 'uncertainty',  mean: 0.119, std: 0.031, signal_ratio: 0.26, status: 'ACTIVE',
      description: 'Bayesian posterior uncertainty on mastery' },
    { name: 'delta_m',      mean: 0.083, std: 0.036, signal_ratio: 0.43, status: 'ACTIVE',
      description: 'Mastery change per interaction (Kalman delta)' },
    { name: 'zpd',          mean: 0.044, std: 0.019, signal_ratio: 0.43, status: 'ACTIVE',
      description: 'Zone of proximal development alignment score' },
    { name: 'transfer',     mean: 0.015, std: 0.024, signal_ratio: 1.64, status: 'ACTIVE',
      description: 'Cross-concept realized knowledge transfer (near α_floor)' },
    { name: 'prospective',  mean: 0.000, std: 0.000, signal_ratio: 0.00, status: 'structural_zero',
      description: 'Prospective transfer — dormant (no prereq_weights on replay)' },
  ]
  const [adcData, setAdcData] = useState<AdcDimension[]>(ADC_FALLBACK)

  // ── ADC Sensitivity Sweep ─────────────────────────────────────────────────
  type SweepDim = { name: string; mean: number; std: number; signal_ratio: number }
  type SweepRow = { alpha_floor?: number; ratio_threshold?: number; is_default: boolean; results: Record<string, string> }
  type SweepData = {
    dimensions: SweepDim[]
    alpha_floor_sweep: SweepRow[]
    ratio_threshold_sweep: SweepRow[]
    n_rows: number
    sealed_run_id: string
  }
  const [sweepData, setSweepData] = useState<SweepData | null>(null)

  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const pipelineTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  /**
   * Animate the 5-stage pipeline with REAL per-interaction details.
   * Each stage shows actual values from the trace row:
   *   1. Kafka Event   → event_id from trajectory_records
   *   2. DAG Lookup    → concept + difficulty + arm_selected
   *   3. JT Attribution → JT components, transfer fired
   *   4. Mastery Update → mastery_before → mastery_after, ensemble weights
   *   5. Recommendation → policy + confidence + ZPD target
   */
  const animatePipelineFromTrace = useCallback((trace: InteractionTrace, snap: GovernanceSnapshot) => {
    const delays = [0, 80, 180, 320, 480]
    const latencies = [12, 8, 45, 22, 18]

    const eventIdShort = (trace.event_id ?? 'no-id').slice(0, 12)
    const conceptShort = (trace.concept_id ?? '?').slice(0, 24)
    const transferFired = trace.transfer.fired
    const jtT = trace.jt_components.transfer ?? trace.transfer.amount ?? 0
    const mb = trace.mastery_before
    const ma = trace.mastery_after
    const masteryArrow = (mb != null && ma != null)
      ? `${(mb * 100).toFixed(0)}% → ${(ma * 100).toFixed(0)}%`
      : 'no mastery snapshot'

    const details = [
      `event_id=${eventIdShort} interaction=#${trace.interaction_number ?? '?'}`,
      `concept=${conceptShort} difficulty=${trace.difficulty != null ? (trace.difficulty * 100).toFixed(0) + '%' : '?'} arm=${trace.arm_selected ?? '—'}`,
      `JT=${pct(snap.jtScore, 0)} ΔM=${pct(trace.jt_components.delta_m ?? 0, 0)} T=${pct(jtT, 0)}${transferFired ? ' ⚡FIRED' : ''}`,
      `Mastery: ${masteryArrow}  ens(B/K/L)=${pct(snap.ensembleWeights.bayesian, 0)}/${pct(snap.ensembleWeights.kalman, 0)}/${pct(snap.ensembleWeights.lyapunov, 0)}`,
      `policy=${trace.policy ?? snap.policy} conf=${pct(snap.confidence, 0)} ZPD=${pct(trace.zpd.score ?? 0, 0)}`,
    ]

    setPipeline(STAGE_ORDER.map(s => ({ stage: s, status: 'idle', latencyMs: 0, detail: '' })))
    STAGE_ORDER.forEach((stage, i) => {
      setTimeout(() => {
        setPipeline(prev => prev.map((p, pi) =>
          pi === i ? { ...p, status: 'active', detail: details[i] } : p
        ))
        setTimeout(() => {
          setPipeline(prev => prev.map((p, pi) =>
            pi === i ? { ...p, status: 'done', latencyMs: latencies[i] } : p
          ))
        }, 60)
      }, delays[i])
    })
  }, [])

  // Legacy mock animator (used in offline mode)
  const animatePipeline = useCallback((snap: GovernanceSnapshot) => {
    const delays = [0, 80, 180, 320, 480]
    const latencies = [12, 8, 45, 22, 18]
    const details = [
      `topic=hcie.events key=${snap.concept}`,
      `edges=5 prereqs=${snap.concept}→downstream`,
      `JT=${pct(snap.jtScore)} T=${pct(snap.transferRealized)}`,
      `ΔM=${snap.masteryDelta >= 0 ? '+' : ''}${pct(snap.masteryDelta, 2)} ensemble updated`,
      `policy=${snap.policy} conf=${pct(snap.confidence, 0)} modality=mpq`,
    ]
    setPipeline(STAGE_ORDER.map(s => ({ stage: s, status: 'idle', latencyMs: 0, detail: '' })))
    STAGE_ORDER.forEach((stage, i) => {
      setTimeout(() => {
        setPipeline(prev => prev.map((p, pi) =>
          pi === i ? { ...p, status: 'active', detail: details[i] } : p
        ))
        setTimeout(() => {
          setPipeline(prev => prev.map((p, pi) =>
            pi === i ? { ...p, status: 'done', latencyMs: latencies[i] } : p
          ))
        }, 60)
      }, delays[i])
    })
  }, [])

  const fetchSnapshot = useCallback(async () => {
    const userId = user?.id ?? 'mock-user-1'
    const headers = getAuthHeaders()

    // ── Offline mode (no backend) → mock simulation with explicit badge ────
    if (!BACKEND) {
      const snap = buildMockSnapshot()
      setCurrent(snap)
      setHistory(h => [...h.slice(-(MAX_HISTORY - 1)), snap])
      animatePipeline(snap)
      setIsMock(true)
      setIsEmpty(false)
      setActiveUserId(userId)
      addEventLog(snap)
      setTickCount(c => c + 1)
      return
    }

    try {
      // Phase 14h: trace-driven monitoring.
      // session-trace returns the full per-interaction chain joining
      // trajectory_records + experiment_trajectories. We use the latest row.
      const [traceRes, evRes] = await Promise.allSettled([
        fetch(`${BACKEND}/v3/frontend/dashboard/session-trace/${userId}?limit=20`,
              { headers, signal: AbortSignal.timeout(5000) }),
        fetch(`${BACKEND}/v3/runtime/events/propagation`,
              { headers, signal: AbortSignal.timeout(4000) }),
      ])

      let traceData: any = {}
      let evData: any = {}
      if (traceRes.status === 'fulfilled' && traceRes.value.ok) traceData = await traceRes.value.json()
      if (evRes.status === 'fulfilled' && evRes.value.ok) evData = await evRes.value.json()

      const traces: InteractionTrace[] = traceData.trace ?? []
      const latest: InteractionTrace | null = traces[0] ?? null

      // Empty state: backend reachable but no trace yet
      if (!latest) {
        setIsEmpty(true)
        setIsMock(false)
        setActiveUserId(userId)
        setTickCount(c => c + 1)
        return
      }

      setIsEmpty(false)
      setLatestTrace(latest)
      setTraceHistory(traces)
      setActiveUserId(userId)

      // Build snapshot from real trace row
      const ens = latest.ensemble
      // Normalized weights → ensemble proportions (fallback to uniform if absent)
      const norm = latest.ensemble.normalized_weights ?? latest.ensemble.weights ?? {}
      const bayesian = Number(norm.bayesian ?? 0.33)
      const kalman = Number(norm.kalman ?? 0.33)
      const lyapunov = Number(norm.lyapunov ?? 0.34)

      // Governance weights from JT components (real attribution scores)
      const jtComp = latest.jt_components
      const govWeights: Record<string, number> = {
        delta_m: Math.abs(Number(jtComp.delta_m ?? 0)),
        transfer: Math.abs(Number(jtComp.transfer ?? 0)),
        challenge: Math.abs(Number(jtComp.challenge ?? 0)),
        uncertainty: Math.abs(Number(jtComp.uncertainty ?? 0)),
        zpd: Math.abs(Number(jtComp.zpd ?? 0)),
        transfer_prospective: 0,  // not currently captured per-row
      }

      const snap: GovernanceSnapshot = {
        timestamp: latest.timestamp ?? new Date().toISOString(),
        jtScore: Number(latest.jt_value ?? 0),
        masteryDelta: Number(latest.mastery_delta ?? 0),
        transferRealized: Number(latest.transfer.amount ?? 0),
        kafkaLag: Number(evData.kafka_lag ?? 0),
        outboxPending: Number(evData.outbox_state?.pending_events ?? 0),
        dlqCount: Number(evData.dlq_state?.message_count ?? 0),
        concept: latest.concept_id ?? 'unknown',
        policy: latest.policy ?? 'hcie',
        confidence: Number(latest.confidence_after ?? latest.confidence_before ?? 0.5),
        governanceWeights: govWeights,
        ensembleWeights: { bayesian, kalman, lyapunov },
      }

      setCurrent(snap)
      setHistory(h => [...h.slice(-(MAX_HISTORY - 1)), snap])
      animatePipelineFromTrace(latest, snap)
      setIsMock(false)
      addEventLog(snap)
      setTickCount(c => c + 1)
    } catch {
      // Network error → mock fallback (badge shows "Mock")
      const snap = buildMockSnapshot()
      setCurrent(snap)
      setHistory(h => [...h.slice(-(MAX_HISTORY - 1)), snap])
      animatePipeline(snap)
      setIsMock(true)
      setIsEmpty(false)
      addEventLog(snap)
      setTickCount(c => c + 1)
    }
  }, [user, animatePipeline, animatePipelineFromTrace])

  function addEventLog(snap: GovernanceSnapshot) {
    const entry: EventLog = {
      id: `evt-${Date.now()}`,
      timestamp: snap.timestamp,
      type: 'learning_event',
      concept: snap.concept,
      mastery: snap.masteryDelta,
      jtScore: snap.jtScore,
      transferFired: snap.transferRealized > TRANSFER_THRESHOLD,
    }
    setEventLog(log => [entry, ...log].slice(0, 50))
  }

  // Fetch ADC status for the SEALED thesis anchor (once on mount). Pinned to
  // run-94a3b8ba so this panel matches the thesis (challenge ACTIVE 0.158,
  // transfer signal_ratio 1.645) and its own "sealed run N=96,727" label —
  // NOT the latest small live cohort (which reads structural_zero).
  useEffect(() => {
    const headers = getAuthHeaders()
    fetch(`${BACKEND}/v3/frontend/dashboard/adc-live-status?run_id=run-94a3b8ba-015b-4d84-b288-004fe60bc282`, { headers })
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d?.dimensions?.length) setAdcData(d.dimensions) })
      .catch(() => { /* keep fallback */ })
  }, [])

  // Fetch ADC sensitivity sweep (once on mount)
  useEffect(() => {
    const headers = getAuthHeaders()
    fetch(`${BACKEND}/v3/frontend/dashboard/adc-sensitivity-sweep`, { headers })
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d?.status === 'ok') setSweepData(d) })
      .catch(() => { /* keep null — panel hidden if unavailable */ })
  }, [])

  // Start/stop polling
  useEffect(() => {
    if (!authLoading && isLive) {
      fetchSnapshot() // initial
      timerRef.current = setInterval(fetchSnapshot, POLL_INTERVAL_MS)
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [authLoading, isLive, fetchSnapshot])

  // Chart data
  const chartData = history.map(s => ({
    time: timeStr(s.timestamp),
    jt: s.jtScore,
    delta_m: Math.max(0, s.masteryDelta),
    transfer: s.transferRealized,
  }))

  const snap = current

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: `${ui.space.xxl}px ${ui.space.xl}px 64px` }}>

      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start',
                    gap: ui.space.lg, marginBottom: ui.space.xl }}>
        <div>
          <Eyebrow color={ui.tone.bad.fg}>{t('governance.eyebrow')}</Eyebrow>
          <h1 style={{ fontSize: ui.font.size.h1, fontWeight: ui.font.weight.heavy, color: ui.color.ink, margin: 0, lineHeight: 1.15 }}>
            {t('governance.title')}
          </h1>
          <div style={{ fontSize: ui.font.size.md, color: ui.color.muted, marginTop: ui.space.xs, lineHeight: 1.5, maxWidth: 720 }}>
            {t('governance.intro')}
          </div>
        </div>
        <div data-tour="live-badge" style={{ display: 'flex', gap: ui.space.sm, alignItems: 'center', flexShrink: 0 }}>
          {isMock && (
            <Tag tone="warn">○ Mock data</Tag>
          )}
          {!isMock && (
            <Tag tone="ok">● Live backend</Tag>
          )}
          <span style={{ fontSize: ui.font.size.xs, color: ui.color.muted,
                          background: ui.color.subtle, border: `1px solid ${ui.color.line}`,
                          borderRadius: ui.radius.sm, padding: '3px 8px' }}>
            {tickCount} ticks · {POLL_INTERVAL_MS / 1000}s interval
          </span>
          <button
            onClick={() => setIsLive(l => !l)}
            style={{
              fontSize: ui.font.size.base, fontWeight: ui.font.weight.bold,
              color: isLive ? ui.tone.bad.fg : ui.tone.ok.fg,
              background: isLive ? ui.tone.bad.bg : ui.tone.ok.bg,
              border: `1px solid ${isLive ? ui.tone.bad.border : ui.tone.ok.border}`,
              borderRadius: ui.radius.md, padding: '5px 12px', cursor: 'pointer',
            }}
          >
            {isLive ? '⏸ Pause' : '▶ Resume'}
          </button>
        </div>
      </div>

      {/* ── Mock / fallback banner: data is simulated, not real ───────────── */}
      {isMock && (
        <div style={{ marginBottom: ui.space.xl }}>
          <Callout tone="warn">
            <strong>{t('mockNotice.title')}</strong>
            <div style={{ marginTop: ui.space.xs }}>{t('mockNotice.body')}</div>
          </Callout>
        </div>
      )}

      {/* ── Empty state: backend live but no interaction trace yet ────────── */}
      {isEmpty && (
        <div style={{ background: ui.color.surface, border: `1px dashed ${ui.color.lineStrong}`, borderRadius: ui.radius.xl,
                      padding: '36px 28px', marginBottom: ui.space.xl, textAlign: 'center' }}>
          <div style={{ fontSize: 40, marginBottom: ui.space.md, opacity: 0.4 }}>⏳</div>
          <div style={{ fontSize: ui.font.size.lg, fontWeight: ui.font.weight.bold, color: ui.color.body, marginBottom: ui.space.sm }}>
            No interaction trace recorded yet
          </div>
          <div style={{ fontSize: ui.font.size.base, color: ui.color.muted, maxWidth: 520, margin: '0 auto 10px',
                         lineHeight: 1.6 }}>
            Backend is connected for user{' '}
            <code style={{ background: ui.color.subtle, padding: '1px 6px', borderRadius: ui.radius.sm }}>
              {activeUserId}
            </code>{' '}
            but no rows in <code>trajectory_records</code> yet.
            <br />
            The trajectory-recorder-consumer worker writes one row per learning event.
            Complete an attempt in <strong>/learn</strong> to populate the trace.
          </div>
          <div style={{ fontSize: ui.font.size.sm, color: ui.color.faint, fontFamily: 'monospace',
                         display: 'inline-block', background: ui.color.subtle,
                         padding: '4px 10px', borderRadius: ui.radius.sm }}>
            polling /v3/frontend/dashboard/session-trace/{activeUserId} every {POLL_INTERVAL_MS / 1000}s
          </div>
        </div>
      )}

      {/* ── Pipeline visualization ─────────────────────────────────────────── */}
      <Panel data-tour="pipeline-strip" pad="lg" style={{ borderRadius: ui.radius.xl, marginBottom: ui.space.xl }}>
        <div style={{ fontSize: ui.font.size.base, fontWeight: ui.font.weight.bold, color: ui.color.body, marginBottom: ui.space.lg,
                       display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: ui.space.md }}>
          <span>Event Processing Pipeline</span>
          {latestTrace && (
            <span style={{ fontSize: ui.font.size.xs, color: ui.color.faint, fontFamily: 'monospace',
                           fontWeight: 400 }}>
              interaction #{latestTrace.interaction_number} · event_id={(latestTrace.event_id ?? '').slice(0, 16)}
            </span>
          )}
        </div>
        <div style={{ display: 'flex', gap: ui.space.sm, alignItems: 'stretch' }}>
          {pipeline.map((p, i) => (
            <React.Fragment key={p.stage}>
              <PipelineStageCard {...p} />
              {i < pipeline.length - 1 && (
                <div style={{
                  display: 'flex', alignItems: 'center',
                  color: pipeline[i].status === 'done' ? ui.tone.ok.fg : ui.color.lineStrong,
                  fontSize: ui.font.size.xl, flexShrink: 0, transition: 'color 0.3s',
                }}>
                  →
                </div>
              )}
            </React.Fragment>
          ))}
        </div>
      </Panel>

      {/* ── Latest Interaction Trace (canonical evidence card) ─────────────── */}
      {latestTrace && (
        <div data-tour="jt-trace-card" style={{ background: '#0D1117', color: '#E6EDF3', border: '1px solid #1F2937',
                      borderRadius: 12, padding: '18px 22px', marginBottom: 20,
                      fontFamily: 'monospace' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between',
                         alignItems: 'baseline', marginBottom: 14 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: '#7EE787' }}>
              Interaction #{latestTrace.interaction_number}
              {latestTrace.timestamp && (
                <span style={{ fontSize: 10, color: '#8B949E', marginLeft: 10, fontWeight: 400 }}>
                  {new Date(latestTrace.timestamp).toLocaleString()}
                </span>
              )}
            </div>
            <div style={{ fontSize: 10, color: '#8B949E' }}>
              user_id={activeUserId}
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '6px 14px',
                         fontSize: 12, lineHeight: 1.7 }}>
            <span style={{ color: '#F0883E', fontWeight: 700 }}>Kafka Event:</span>
            <span>event_id=<span style={{ color: '#79C0FF' }}>{latestTrace.event_id ?? '(none)'}</span>{'  '}
              interaction_id=<span style={{ color: '#79C0FF' }}>{latestTrace.interaction_id ?? '—'}</span></span>

            <span style={{ color: '#F0883E', fontWeight: 700 }}>DAG Lookup:</span>
            <span>concept=<span style={{ color: '#D2A8FF' }}>{latestTrace.concept_id ?? '?'}</span>
              {'  '}difficulty={latestTrace.difficulty != null ? `${(latestTrace.difficulty * 100).toFixed(0)}%` : '?'}
              {'  '}arm_selected=<span style={{ color: '#79C0FF' }}>{latestTrace.arm_selected ?? '—'}</span></span>

            <span style={{ color: '#F0883E', fontWeight: 700 }}>JT Attribution:</span>
            <span>
              JT=<strong style={{ color: '#7EE787' }}>{(Number(latestTrace.jt_value ?? 0) * 100).toFixed(2)}%</strong>
              {'  '}ΔM={pct(latestTrace.jt_components.delta_m ?? 0, 2)}
              {'  '}T_realized=<strong style={{ color: latestTrace.transfer.fired ? '#F85149' : '#8B949E' }}>
                {pct(latestTrace.transfer.amount ?? 0, 2)}{latestTrace.transfer.fired ? ' ⚡FIRED' : ''}
              </strong>
              {'  '}challenge={pct(latestTrace.jt_components.challenge ?? 0, 2)}
              {'  '}uncertainty={pct(latestTrace.jt_components.uncertainty ?? 0, 2)}
              {'  '}ZPD={pct(latestTrace.jt_components.zpd ?? 0, 2)}
            </span>

            <span style={{ color: '#F0883E', fontWeight: 700 }}>Mastery:</span>
            <span>
              {latestTrace.mastery_before != null && latestTrace.mastery_after != null ? (
                <>
                  <strong style={{ color: '#8B949E' }}>{(latestTrace.mastery_before * 100).toFixed(1)}%</strong>
                  {' → '}
                  <strong style={{ color: (latestTrace.mastery_delta ?? 0) >= 0 ? '#7EE787' : '#F85149' }}>
                    {(latestTrace.mastery_after * 100).toFixed(1)}%
                  </strong>
                  {'  ('}{(latestTrace.mastery_delta ?? 0) >= 0 ? '+' : ''}
                  {((latestTrace.mastery_delta ?? 0) * 100).toFixed(2)}{'%)'}
                </>
              ) : (
                <span style={{ color: '#8B949E' }}>no mastery snapshot</span>
              )}
              {'  '}ens: B={latestTrace.ensemble.bayesian_after.alpha != null
                ? `α=${Number(latestTrace.ensemble.bayesian_after.alpha).toFixed(2)},β=${Number(latestTrace.ensemble.bayesian_after.beta ?? 0).toFixed(2)}`
                : '—'}
              {'  '}K={latestTrace.ensemble.kalman_after.mastery != null
                ? `${(Number(latestTrace.ensemble.kalman_after.mastery) * 100).toFixed(1)}%`
                : '—'}
              {'  '}L={latestTrace.ensemble.lyapunov_after != null
                ? `${(Number(latestTrace.ensemble.lyapunov_after) * 100).toFixed(1)}%`
                : '—'}
            </span>

            <span style={{ color: '#F0883E', fontWeight: 700 }}>Recommendation:</span>
            <span>
              policy=<span style={{ color: '#79C0FF' }}>{latestTrace.policy ?? '—'}</span>
              {'  '}correct=<strong style={{ color: latestTrace.correct === true ? '#7EE787' :
                latestTrace.correct === false ? '#F85149' : '#8B949E' }}>
                {latestTrace.correct === null ? 'unknown' : String(latestTrace.correct)}
              </strong>
              {'  '}response_time={latestTrace.response_time != null
                ? `${latestTrace.response_time.toFixed(2)}s`
                : '—'}
              {'  '}ZPD_target={latestTrace.zpd.target != null
                ? `${(latestTrace.zpd.target * 100).toFixed(0)}%`
                : '—'}
            </span>
          </div>

          {/* Sparkline of recent trace history */}
          {traceHistory.length > 1 && (
            <div style={{ marginTop: 14, paddingTop: 12, borderTop: '1px solid #1F2937',
                           fontSize: 10, color: '#8B949E' }}>
              <span style={{ marginRight: 12 }}>recent {traceHistory.length} interactions:</span>
              {traceHistory.slice(0, 16).reverse().map((t, i) => (
                <span key={`${t.event_id}-${i}`} style={{
                  display: 'inline-block', marginRight: 3,
                  color: t.correct === true ? '#7EE787' : t.correct === false ? '#F85149' : '#8B949E',
                }}>
                  {t.correct === true ? '●' : t.correct === false ? '✗' : '○'}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── Current snapshot ───────────────────────────────────────────────── */}
      {snap && (
        <div style={{ display: 'grid',
                      gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                      gap: ui.space.md, marginBottom: ui.space.xl }}>
          {[
            { label: 'JT Score',     value: pct(snap.jtScore),    color: '#1A5276' },
            { label: 'Mastery Δ',    value: `${snap.masteryDelta >= 0 ? '+' : ''}${pct(snap.masteryDelta, 2)}`, color: snap.masteryDelta >= 0 ? ui.tone.ok.fg : ui.tone.bad.fg },
            { label: 'T_realized',   value: pct(snap.transferRealized), color: snap.transferRealized > TRANSFER_THRESHOLD ? ui.tone.bad.fg : ui.color.muted },
            { label: 'Kafka Lag',    value: `${snap.kafkaLag} msg`, color: snap.kafkaLag > 5 ? ui.tone.warn.fg : ui.tone.ok.fg },
          ].map(({ label, value, color }) => (
            <Panel key={label} pad="md">
              <div style={{ fontSize: ui.font.size.xs, color: ui.color.muted, fontWeight: ui.font.weight.bold,
                             textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: ui.space.xs }}>
                {label}
              </div>
              <div style={{ fontSize: ui.font.size.h2, fontWeight: ui.font.weight.heavy, color,
                             fontVariantNumeric: 'tabular-nums' }}>
                {value}
              </div>
            </Panel>
          ))}
        </div>
      )}

      {/* ── Two-column: live chart + governance weights ─────────────────────── */}
      <div style={{ display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))',
                    gap: ui.space.xl, marginBottom: ui.space.xl }}>

        {/* JT live chart */}
        <Panel data-tour="jt-chart" pad="lg">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start',
                         gap: ui.space.md, marginBottom: ui.space.md }}>
            <SectionTitle sub={`Last ${history.length} governance ticks`}>
              JT Score — Live Trace
            </SectionTitle>
            {snap?.transferRealized != null && snap.transferRealized > TRANSFER_THRESHOLD && (
              <Tag tone="bad">⚡ TRANSFER ACTIVE</Tag>
            )}
          </div>
          {chartData.length === 0 ? (
            <div style={{ height: 220, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
                          gap: ui.space.sm, textAlign: 'center', border: `1px dashed ${ui.color.line}`, borderRadius: ui.radius.md }}>
              <div style={{ fontSize: 26 }} aria-hidden>⏳</div>
              <div style={{ fontSize: ui.font.size.md, color: ui.color.body, fontWeight: ui.font.weight.medium }}>{t('governance.traceWaiting')}</div>
              <div style={{ fontSize: ui.font.size.sm, color: ui.color.muted, maxWidth: 330, lineHeight: 1.5 }}>{t('governance.traceWaitingSub')}</div>
              <div style={{ display: 'flex', gap: ui.space.md, marginTop: ui.space.xs }}>
                <a href="/learn" style={{ fontSize: ui.font.size.sm, color: ui.tone.info.fg, fontWeight: ui.font.weight.bold, textDecoration: 'none' }}>{t('governance.traceWaitingCta')}</a>
                <a href="/review/run-it-yourself" style={{ fontSize: ui.font.size.sm, color: ui.color.muted, fontWeight: ui.font.weight.medium, textDecoration: 'none' }}>{t('governance.traceWaitingReplay')}</a>
              </div>
            </div>
          ) : (
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={chartData} margin={{ left: 0, right: 8, top: 4, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={ui.color.grid} />
              <XAxis dataKey="time" tick={{ fontSize: ui.font.size.xs, fill: ui.color.faint }}
                     axisLine={false} tickLine={false}
                     interval={Math.max(1, Math.floor(chartData.length / 8))} />
              <YAxis domain={[0, 1]} tickFormatter={v => `${(v*100).toFixed(0)}%`}
                     tick={{ fontSize: ui.font.size.xs, fill: ui.color.faint }}
                     axisLine={false} tickLine={false} width={36} />
              <Tooltip content={<JTTooltip />} />
              <ReferenceLine y={0.5} stroke={ui.color.line} strokeDasharray="4 4"
                             label={{ value: '50%', position: 'insideTopLeft', fontSize: ui.font.size.xs, fill: ui.color.faint }} />
              <Line type="monotone" dataKey="jt" name="JT Score"
                    stroke="#1A5276" strokeWidth={2.5} dot={false}
                    activeDot={{ r: 4, fill: '#1A5276' }} />
              <Line type="monotone" dataKey="delta_m" name="ΔM"
                    stroke={ui.tone.ok.fg} strokeWidth={1.5} strokeDasharray="4 2" dot={false} />
              <Line type="monotone" dataKey="transfer" name="T_realized"
                    stroke={ui.tone.bad.fg} strokeWidth={1.5} strokeDasharray="2 3" dot={false} />
            </LineChart>
          </ResponsiveContainer>
          )}
          <div style={{ display: 'flex', gap: ui.space.lg, marginTop: ui.space.sm, fontSize: ui.font.size.xs, color: ui.color.muted }}>
            <span><span style={{ color: '#1A5276', fontWeight: ui.font.weight.bold }}>—</span> JT Score</span>
            <span><span style={{ color: ui.tone.ok.fg, fontWeight: ui.font.weight.bold }}>- -</span> ΔM</span>
            <span><span style={{ color: ui.tone.bad.fg, fontWeight: ui.font.weight.bold }}>···</span> T_realized</span>
          </div>
        </Panel>

        {/* Governance weights + infra */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: ui.space.md }}>
          {/* JT 6D weights */}
          {snap && (
            <Panel data-tour="gov-weights" pad="md">
              <div style={{ fontSize: ui.font.size.base, fontWeight: ui.font.weight.bold, color: ui.color.body, marginBottom: ui.space.md }}>
                6D Governance Weights
              </div>
              {Object.entries(snap.governanceWeights).map(([k, v]) => {
                const colors: Record<string, string> = {
                  delta_m: '#2980B9', transfer: '#C0392B', challenge: '#8E44AD',
                  uncertainty: '#D35400', zpd: '#27AE60', transfer_prospective: '#16A085',
                }
                const labels: Record<string, string> = {
                  delta_m: 'ΔM', transfer: 'T_realized', challenge: 'Challenge',
                  uncertainty: 'Uncertainty', zpd: 'ZPD', transfer_prospective: 'T_prospective',
                }
                const total = Object.values(snap.governanceWeights).reduce((s, x) => s + Math.abs(x), 0) || 1
                const share = Math.abs(v) / total
                return (
                  <div key={k} style={{ marginBottom: ui.space.xs + 1 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between',
                                   fontSize: ui.font.size.xs, marginBottom: 2 }}>
                      <span style={{ color: ui.color.body }}>{labels[k] ?? k}</span>
                      <span style={{ color: colors[k] ?? ui.color.muted, fontWeight: ui.font.weight.bold,
                                      fontVariantNumeric: 'tabular-nums' }}>
                        {(share * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div style={{ height: 4, background: ui.color.line, borderRadius: 2 }}>
                      <div style={{ width: `${share * 100}%`, height: '100%',
                                    background: colors[k] ?? ui.color.lineStrong,
                                    borderRadius: 2, transition: 'width 0.4s' }} />
                    </div>
                  </div>
                )
              })}
            </Panel>
          )}

          {/* Infrastructure health */}
          {snap && (
            <Panel pad="md">
              <div style={{ fontSize: ui.font.size.base, fontWeight: ui.font.weight.bold, color: ui.color.body, marginBottom: ui.space.md }}>
                Infrastructure
              </div>
              {[
                { label: 'Kafka Lag',      value: `${snap.kafkaLag} msg`,    ok: snap.kafkaLag <= 5 },
                { label: 'Outbox Queue',   value: `${snap.outboxPending} pending`, ok: snap.outboxPending < 10 },
                { label: 'DLQ',            value: snap.dlqCount === 0 ? 'Clean' : `${snap.dlqCount} failed`, ok: snap.dlqCount === 0 },
                { label: 'Policy',         value: snap.policy.toUpperCase(), ok: true },
                { label: 'Confidence',     value: pct(snap.confidence),      ok: snap.confidence > 0.5 },
              ].map(({ label, value, ok }) => (
                <div key={label} style={{ display: 'flex', justifyContent: 'space-between',
                                           alignItems: 'center', padding: '5px 0',
                                           borderBottom: `1px solid ${ui.color.subtle}`, fontSize: ui.font.size.sm }}>
                  <span style={{ color: ui.color.muted }}>{label}</span>
                  <span style={{ fontWeight: ui.font.weight.bold, color: ok ? ui.color.ink : ui.tone.warn.fg,
                                  fontVariantNumeric: 'tabular-nums' }}>
                    {ok ? '' : '⚠ '}{value}
                  </span>
                </div>
              ))}
            </Panel>
          )}
        </div>
      </div>

      {/* ── Event log ──────────────────────────────────────────────────────── */}
      <Panel pad="lg" style={{ marginBottom: ui.space.xl }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start',
                       gap: ui.space.md, marginBottom: ui.space.md }}>
          <SectionTitle sub={`Last ${eventLog.length} events — real-time governance pipeline`}>
            Live Event Log
          </SectionTitle>
          <button onClick={() => setEventLog([])} style={{
            fontSize: ui.font.size.sm, color: ui.color.muted, background: 'none',
            border: `1px solid ${ui.color.line}`, borderRadius: ui.radius.sm, padding: '3px 10px',
            cursor: 'pointer', flexShrink: 0,
          }}>
            Clear
          </button>
        </div>
        <div style={{ fontFamily: 'monospace', fontSize: ui.font.size.sm, maxHeight: 240,
                      overflowY: 'auto', background: '#0D1117', borderRadius: ui.radius.md, padding: ui.space.md }}>
          {eventLog.length === 0 ? (
            <div style={{ color: '#4A5568', textAlign: 'center', padding: '20px 0' }}>
              Waiting for events…
            </div>
          ) : eventLog.map(e => (
            <div key={e.id} style={{ marginBottom: 3, display: 'flex', gap: 10 }}>
              <span style={{ color: '#4A5568', flexShrink: 0 }}>{timeStr(e.timestamp)}</span>
              <span style={{ color: '#2ECC71', flexShrink: 0 }}>[{e.type}]</span>
              <span style={{ color: '#85C1E9' }}>{shortConcept(e.concept)}</span>
              <span style={{ color: e.mastery >= 0 ? '#2ECC71' : '#E74C3C' }}>
                ΔM:{e.mastery >= 0 ? '+' : ''}{(e.mastery * 100).toFixed(2)}%
              </span>
              <span style={{ color: '#F39C12' }}>JT:{(e.jtScore * 100).toFixed(1)}%</span>
              {e.transferFired && (
                <span style={{ color: '#E74C3C', fontWeight: 700 }}>⚡ TRANSFER</span>
              )}
            </div>
          ))}
        </div>
      </Panel>

      {/* ── Ensemble weights ───────────────────────────────────────────────── */}
      {snap && (
        <Panel data-tour="ensemble-weights" pad="lg" style={{ marginBottom: ui.space.xl }}>
          <div style={{ fontSize: ui.font.size.md, fontWeight: ui.font.weight.bold, color: ui.color.heading, marginBottom: ui.space.lg }}>
            Mastery Ensemble Weights
            <span style={{ fontSize: ui.font.size.sm, fontWeight: 400, color: ui.color.muted, marginLeft: ui.space.sm }}>
              Current MAB allocation across estimators
            </span>
          </div>
          <div style={{ display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                        gap: ui.space.md }}>
            {Object.entries(snap.ensembleWeights).map(([name, w]) => {
              const colors: Record<string, string> = {
                bayesian: '#2980B9', kalman: '#8E44AD', lyapunov: '#27AE60',
              }
              const labels: Record<string, string> = {
                bayesian: 'Bayesian BKT', kalman: 'Kalman Filter', lyapunov: 'Bounded-stability (cut · w=0)',
              }
              const descs: Record<string, string> = {
                bayesian: 'Item-response theory with calibrated priors',
                kalman: 'Continuous-state estimation, noise-adaptive',
                lyapunov: 'Disclosed ex-Lyapunov heuristic — removed from fusion (weight 0)',
              }
              const c = colors[name] ?? ui.color.lineStrong
              return (
                <div key={name} style={{ border: `1px solid ${c}40`, borderRadius: ui.radius.lg,
                                          padding: `${ui.space.md}px ${ui.space.lg}px`, background: `${c}08` }}>
                  <div style={{ fontSize: ui.font.size.sm, color: c, fontWeight: ui.font.weight.bold, marginBottom: ui.space.xs }}>
                    {labels[name] ?? name}
                  </div>
                  <div style={{ fontSize: ui.font.size.h1, fontWeight: ui.font.weight.heavy, color: c,
                                 fontVariantNumeric: 'tabular-nums', lineHeight: 1.1 }}>
                    {pct(w)}
                  </div>
                  <div style={{ marginTop: ui.space.sm, height: 6, background: ui.color.line, borderRadius: 3 }}>
                    <div style={{ height: '100%', width: `${w * 100}%`, background: c,
                                   borderRadius: 3, transition: 'width 0.4s' }} />
                  </div>
                  <div style={{ fontSize: ui.font.size.xs, color: ui.color.muted, marginTop: ui.space.sm, lineHeight: 1.4 }}>
                    {descs[name]}
                  </div>
                </div>
              )
            })}
          </div>
        </Panel>
      )}

      {/* ══════════════════════════════════════════════════════════════════════
          ADC LIVE STATUS — Dimension Classification
          ══════════════════════════════════════════════════════════════════════ */}
      <Panel pad="xl" style={{ borderRadius: ui.radius.xl, marginBottom: ui.space.xl }}>

        {/* Header bar */}
        <SectionTitle
          sub={
            <>
              Sealed thresholds: α_floor = 0.01 · signal_ratio ≥ 0.08.{' '}
              <strong style={{ color: ui.tone.ok.fg }}>ACTIVE</strong> = dimension carries empirical signal.{' '}
              <strong style={{ color: ui.tone.bad.fg }}>structural_zero</strong> = dormant under current
              interaction ecology.
            </>
          }
        >
          Adaptive Dimension Controller (ADC) — Live Governance Observability
        </SectionTitle>

        {/* Mandatory ADC disclaimer — magnitudes inherited, verdicts robust */}
        <Callout tone="warn" style={{ marginTop: ui.space.sm }}>
          ⚠ <strong>Magnitudes are 3-learner-runtime-inherited</strong> on this Kalman-canonical seal. The
          ACTIVE / structural_zero <strong>verdicts are robust</strong> to threshold sweeps; the magnitude
          values (mean / std / signal_ratio) are <strong>not load-bearing</strong>. Illustrative live snapshot —
          sealed per-dimension stats are in §4.1.3.d (Tabel 4.10).
        </Callout>

        {/* Bar chart — signal_ratio per dimension */}
        <div style={{ marginTop: ui.space.lg, marginBottom: ui.space.sm }}>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={adcData} barCategoryGap="30%"
                      margin={{ left: 0, right: 8, top: 4, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={ui.color.grid} vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: ui.font.size.xs, fill: ui.color.muted }}
                     axisLine={{ stroke: ui.color.line }} tickLine={false} />
              <YAxis domain={[0, 2]} tick={{ fontSize: ui.font.size.xs, fill: ui.color.faint }}
                     tickFormatter={v => v.toFixed(1)}
                     axisLine={false} tickLine={false}
                     label={{ value: 'signal_ratio (σ/μ)', angle: -90, position: 'insideLeft',
                              fontSize: ui.font.size.xs, fill: ui.color.muted, style: { textAnchor: 'middle' } }}
                     width={48} />
              <Tooltip
                cursor={{ fill: ui.color.grid }}
                contentStyle={{ fontSize: ui.font.size.sm, borderRadius: ui.radius.sm,
                                border: `1px solid ${ui.color.line}` }}
                formatter={(val: any, _name: any, props: any) => {
                  const d = props?.payload ?? {}
                  const v = typeof val === 'number' ? val : Number(val)
                  return [
                    `signal_ratio=${v.toFixed(3)} | mean=${(d.mean ?? 0).toFixed(3)} | std=${(d.std ?? 0).toFixed(3)} | ${d.status ?? ''}`,
                    'ADC',
                  ]
                }}
              />
              <ReferenceLine y={0.08} stroke={ui.tone.warn.fg} strokeDasharray="4 2"
                             label={{ value: 'threshold 0.08', position: 'insideTopRight',
                                      fontSize: ui.font.size.xs, fill: ui.tone.warn.fg }} />
              <Bar dataKey="signal_ratio" radius={[4, 4, 0, 0]} maxBarSize={64}>
                {adcData.map((d) => {
                  const color = d.status === 'structural_zero' ? ui.tone.bad.fg
                    : d.signal_ratio < 0.12 ? ui.tone.warn.fg
                    : ui.tone.ok.fg
                  return <Cell key={d.name} fill={color} />
                })}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          {/* chart legend — verdict color key */}
          <div style={{ display: 'flex', gap: ui.space.lg, marginTop: ui.space.sm, flexWrap: 'wrap',
                         fontSize: ui.font.size.xs, color: ui.color.muted }}>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: ui.space.xs }}>
              <span style={{ width: 10, height: 10, borderRadius: 2, background: ui.tone.ok.fg, display: 'inline-block' }} />
              ACTIVE
            </span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: ui.space.xs }}>
              <span style={{ width: 10, height: 10, borderRadius: 2, background: ui.tone.warn.fg, display: 'inline-block' }} />
              near-threshold
            </span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: ui.space.xs }}>
              <span style={{ width: 10, height: 10, borderRadius: 2, background: ui.tone.bad.fg, display: 'inline-block' }} />
              structural_zero
            </span>
          </div>
        </div>

        {/* 6 dimension cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
                      gap: ui.space.md, marginTop: ui.space.lg }}>
          {adcData.map(d => {
            const isActive = d.status === 'ACTIVE'
            const isNearThreshold = isActive && d.signal_ratio < 0.12
            const cardTone = d.status === 'structural_zero' ? ui.tone.bad
              : isNearThreshold ? ui.tone.warn
              : ui.tone.ok
            return (
              <div key={d.name} style={{ border: `1px solid ${cardTone.border}`,
                                         borderRadius: ui.radius.md, padding: `${ui.space.md}px ${ui.space.md}px`,
                                         background: cardTone.bg }}>
                <div style={{ fontSize: ui.font.size.base, fontWeight: ui.font.weight.bold, color: ui.color.ink,
                               textTransform: 'capitalize', marginBottom: ui.space.xs }}>
                  {d.name.replace(/_/g, ' ')}
                </div>
                <div style={{ marginBottom: ui.space.xs + 1, display: 'flex', gap: ui.space.xs, flexWrap: 'wrap' }}>
                  <span style={{
                    fontSize: ui.font.size.xs, fontWeight: ui.font.weight.bold, borderRadius: ui.radius.sm,
                    padding: '2px 6px',
                    background: isActive ? ui.tone.ok.bg : ui.tone.bad.bg,
                    border: `1px solid ${isActive ? ui.tone.ok.border : ui.tone.bad.border}`,
                    color: isActive ? ui.tone.ok.fg : ui.tone.bad.fg,
                  }}>
                    {d.status === 'structural_zero' ? 'structural_zero' : 'ACTIVE'}
                  </span>
                  {isNearThreshold && (
                    <span style={{ fontSize: ui.font.size.xs, fontWeight: ui.font.weight.bold,
                                   background: ui.tone.warn.bg, color: ui.tone.warn.fg,
                                   border: `1px solid ${ui.tone.warn.border}`,
                                   borderRadius: ui.radius.sm, padding: '2px 6px' }}>
                      near-threshold
                    </span>
                  )}
                </div>
                <div style={{ fontSize: ui.font.size.xs, color: ui.color.body, fontVariantNumeric: 'tabular-nums',
                               marginBottom: ui.space.xs - 1 }}>
                  mean: {d.mean.toFixed(3)} | signal_ratio: {d.signal_ratio.toFixed(2)}
                </div>
                <div style={{ fontSize: ui.font.size.xs, color: ui.color.muted, lineHeight: 1.4 }}>
                  {d.description}
                </div>
              </div>
            )
          })}
        </div>

        {/* Disclosure note */}
        <Callout tone="neutral" title="Structural dormancy disclosure:" style={{ marginTop: ui.space.lg }}>
          challenge_event: 0% active on Junyi corpus (no is_assessment=True records).
          t_realized_v2: 0% active in continuation (prereq_weights=None on replay).
          These are structural dormancy — not failures. The 6 V1 dimensions above are measured
          from sealed run (N=96,727, run-94a3b8ba).
        </Callout>
      </Panel>

      {/* ══════════════════════════════════════════════════════════════════════
          ADC SENSITIVITY SWEEP — Threshold Robustness Analysis
          ══════════════════════════════════════════════════════════════════════ */}
      <Panel pad="xl" style={{ borderRadius: ui.radius.xl, marginBottom: ui.space.xl }}>
        <SectionTitle
          sub={
            <>
              How does the ACTIVE/structural_zero classification change as we vary{' '}
              <code>α_floor</code> and <code>signal_ratio_threshold</code>?
              Verified against sealed run-94a3b8ba (N={sweepData?.n_rows?.toLocaleString() ?? '96,727'}).
              Green = ACTIVE · Red = structural_zero · Blue row = current default.
            </>
          }
        >
          ADC Sensitivity Sweep — Threshold Robustness (R6 Closed)
        </SectionTitle>

        {/* Dim stats table */}
        <div style={{ fontSize: ui.font.size.sm, fontWeight: ui.font.weight.bold, color: ui.color.heading, marginBottom: ui.space.sm }}>
          Dimension Statistics (μ, σ, σ/μ — sealed run)
        </div>
        <div style={{ overflowX: 'auto', marginBottom: ui.space.lg }}>
          <table style={{ borderCollapse: 'collapse', fontSize: ui.font.size.sm, width: '100%' }}>
            <thead>
              <tr style={{ background: ui.color.subtle }}>
                {['Dimension', 'μ (mean)', 'σ (std)', 'σ/μ (ratio)', 'Status'].map(h => (
                  <th key={h} style={{ padding: '6px 10px', textAlign: 'center',
                                        border: `1px solid ${ui.color.lineStrong}`, fontWeight: ui.font.weight.bold,
                                        color: ui.color.heading }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {(sweepData?.dimensions ?? ADC_FALLBACK.map(d => ({
                name: d.name, mean: d.mean, std: d.std, signal_ratio: d.signal_ratio
              }))).map(d => {
                const isActive = d.mean > 0.01 && d.signal_ratio >= 0.08
                return (
                  <tr key={d.name} style={{ background: isActive ? ui.tone.ok.bg : ui.tone.bad.bg }}>
                    <td style={{ padding: '5px 10px', border: `1px solid ${ui.color.line}`,
                                  fontWeight: ui.font.weight.medium, color: ui.color.ink }}>{d.name}</td>
                    <td style={{ padding: '5px 10px', border: `1px solid ${ui.color.line}`,
                                  textAlign: 'center', fontVariantNumeric: 'tabular-nums', color: ui.color.body }}>
                      {d.mean.toFixed(4)}
                    </td>
                    <td style={{ padding: '5px 10px', border: `1px solid ${ui.color.line}`,
                                  textAlign: 'center', fontVariantNumeric: 'tabular-nums', color: ui.color.body }}>
                      {d.std.toFixed(4)}
                    </td>
                    <td style={{ padding: '5px 10px', border: `1px solid ${ui.color.line}`,
                                  textAlign: 'center', fontVariantNumeric: 'tabular-nums', color: ui.color.body }}>
                      {d.signal_ratio.toFixed(3)}
                    </td>
                    <td style={{ padding: '5px 10px', border: `1px solid ${ui.color.line}`,
                                  textAlign: 'center', fontWeight: ui.font.weight.bold,
                                  color: isActive ? ui.tone.ok.fg : ui.tone.bad.fg }}>
                      {isActive ? 'ACTIVE' : 'structural_zero'}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>

        {/* Two sweep tables side by side */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: ui.space.lg }}>
          {/* Alpha floor sweep */}
          <div>
            <div style={{ fontSize: ui.font.size.sm, fontWeight: ui.font.weight.bold, color: ui.color.heading, marginBottom: ui.space.sm }}>
              Sweep 1: α_floor ∈ {'{0.005, 0.01, 0.02, 0.05}'} (ratio_threshold=0.08 fixed)
            </div>
            <table style={{ borderCollapse: 'collapse', fontSize: ui.font.size.xs, width: '100%' }}>
              <thead>
                <tr style={{ background: ui.color.subtle }}>
                  <th style={{ padding: '5px 8px', border: `1px solid ${ui.color.lineStrong}`,
                                fontWeight: ui.font.weight.bold, color: ui.color.heading,
                                whiteSpace: 'nowrap' }}>α_floor</th>
                  {['challenge','uncertainty','delta_m','zpd','transfer','prospective'].map(d => (
                    <th key={d} style={{ padding: '5px 6px', border: `1px solid ${ui.color.lineStrong}`,
                                          fontWeight: ui.font.weight.bold, color: ui.color.heading,
                                          fontSize: ui.font.size.xs }}>
                      {d.replace('_',' ')}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(sweepData?.alpha_floor_sweep ?? [
                  { alpha_floor: 0.005, is_default: false, results: { challenge:'ACTIVE', uncertainty:'ACTIVE', delta_m:'ACTIVE', zpd:'ACTIVE', transfer:'ACTIVE', prospective:'structural_zero' } },
                  { alpha_floor: 0.01,  is_default: true,  results: { challenge:'ACTIVE', uncertainty:'ACTIVE', delta_m:'ACTIVE', zpd:'ACTIVE', transfer:'ACTIVE', prospective:'structural_zero' } },
                  { alpha_floor: 0.02,  is_default: false, results: { challenge:'ACTIVE', uncertainty:'ACTIVE', delta_m:'ACTIVE', zpd:'ACTIVE', transfer:'structural_zero', prospective:'structural_zero' } },
                  { alpha_floor: 0.05,  is_default: false, results: { challenge:'ACTIVE', uncertainty:'ACTIVE', delta_m:'ACTIVE', zpd:'structural_zero', transfer:'structural_zero', prospective:'structural_zero' } },
                ]).map(row => (
                  <tr key={row.alpha_floor}
                      style={{ background: row.is_default ? ui.tone.info.bg : ui.color.surface }}>
                    <td style={{ padding: '5px 8px', border: `1px solid ${ui.color.line}`,
                                  fontWeight: row.is_default ? ui.font.weight.bold : 400, color: ui.color.ink,
                                  whiteSpace: 'nowrap' }}>
                      {row.alpha_floor}{row.is_default ? ' ★' : ''}
                    </td>
                    {['challenge','uncertainty','delta_m','zpd','transfer','prospective'].map(d => {
                      const v = row.results[d]
                      const isA = v === 'ACTIVE'
                      return (
                        <td key={d} style={{ padding: '4px 6px', border: `1px solid ${ui.color.line}`,
                                              textAlign: 'center', fontSize: ui.font.size.xs, fontWeight: ui.font.weight.bold,
                                              background: isA ? ui.tone.ok.bg : ui.tone.bad.bg,
                                              color: isA ? ui.tone.ok.fg : ui.tone.bad.fg }}>
                          {isA ? 'A' : 'sz'}
                        </td>
                      )
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Ratio threshold sweep */}
          <div>
            <div style={{ fontSize: ui.font.size.sm, fontWeight: ui.font.weight.bold, color: ui.color.heading, marginBottom: ui.space.sm }}>
              Sweep 2: ratio_threshold ∈ {'{0.05, 0.08, 0.10, 0.15}'} (α_floor=0.01 fixed)
            </div>
            <table style={{ borderCollapse: 'collapse', fontSize: ui.font.size.xs, width: '100%' }}>
              <thead>
                <tr style={{ background: ui.color.subtle }}>
                  <th style={{ padding: '5px 8px', border: `1px solid ${ui.color.lineStrong}`,
                                fontWeight: ui.font.weight.bold, color: ui.color.heading,
                                whiteSpace: 'nowrap' }}>σ/μ thresh</th>
                  {['challenge','uncertainty','delta_m','zpd','transfer','prospective'].map(d => (
                    <th key={d} style={{ padding: '5px 6px', border: `1px solid ${ui.color.lineStrong}`,
                                          fontWeight: ui.font.weight.bold, color: ui.color.heading,
                                          fontSize: ui.font.size.xs }}>
                      {d.replace('_',' ')}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(sweepData?.ratio_threshold_sweep ?? [
                  { ratio_threshold: 0.05, is_default: false, results: { challenge:'ACTIVE', uncertainty:'ACTIVE', delta_m:'ACTIVE', zpd:'ACTIVE', transfer:'ACTIVE', prospective:'structural_zero' } },
                  { ratio_threshold: 0.08, is_default: true,  results: { challenge:'ACTIVE', uncertainty:'ACTIVE', delta_m:'ACTIVE', zpd:'ACTIVE', transfer:'ACTIVE', prospective:'structural_zero' } },
                  { ratio_threshold: 0.10, is_default: false, results: { challenge:'ACTIVE', uncertainty:'ACTIVE', delta_m:'ACTIVE', zpd:'ACTIVE', transfer:'ACTIVE', prospective:'structural_zero' } },
                  { ratio_threshold: 0.15, is_default: false, results: { challenge:'ACTIVE', uncertainty:'ACTIVE', delta_m:'ACTIVE', zpd:'ACTIVE', transfer:'ACTIVE', prospective:'structural_zero' } },
                ]).map(row => (
                  <tr key={row.ratio_threshold}
                      style={{ background: row.is_default ? ui.tone.info.bg : ui.color.surface }}>
                    <td style={{ padding: '5px 8px', border: `1px solid ${ui.color.line}`,
                                  fontWeight: row.is_default ? ui.font.weight.bold : 400, color: ui.color.ink,
                                  whiteSpace: 'nowrap' }}>
                      {row.ratio_threshold}{row.is_default ? ' ★' : ''}
                    </td>
                    {['challenge','uncertainty','delta_m','zpd','transfer','prospective'].map(d => {
                      const v = row.results[d]
                      const isA = v === 'ACTIVE'
                      return (
                        <td key={d} style={{ padding: '4px 6px', border: `1px solid ${ui.color.line}`,
                                              textAlign: 'center', fontSize: ui.font.size.xs, fontWeight: ui.font.weight.bold,
                                              background: isA ? ui.tone.ok.bg : ui.tone.bad.bg,
                                              color: isA ? ui.tone.ok.fg : ui.tone.bad.fg }}>
                          {isA ? 'A' : 'sz'}
                        </td>
                      )
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Key finding */}
        <Callout tone="ok" title="Key finding:" style={{ marginTop: ui.space.lg }}>
          3 core dims (challenge, uncertainty, delta_m) are ACTIVE at all tested threshold combos —
          classification is threshold-agnostic.
          Transfer becomes structural_zero at α_floor ≥ 0.02 (μ=0.015 borderline).
          ZPD becomes structural_zero only at α_floor = 0.05 (μ=0.044).
          Prospective always structural_zero (μ=0, σ=0).
          ★ = current default. Source: run-94a3b8ba, N=96,727. <strong>R6 CLOSED.</strong>
        </Callout>
      </Panel>

      {/* ── Footer nav ─────────────────────────────────────────────────────── */}
      <div style={{ display: 'flex', gap: ui.space.md, justifyContent: 'center', flexWrap: 'wrap' }}>
        <Link href="/learn" style={{
          fontSize: ui.font.size.md, fontWeight: ui.font.weight.bold, color: '#fff', background: '#1A5276',
          textDecoration: 'none', padding: '10px 24px', borderRadius: ui.radius.md,
        }}>
          ← Back to Learn
        </Link>
        <Link href="/dashboard/learner" style={{
          fontSize: ui.font.size.md, fontWeight: ui.font.weight.medium, color: ui.color.body,
          textDecoration: 'none', padding: '10px 24px', borderRadius: ui.radius.md,
          border: `1px solid ${ui.color.lineStrong}`, background: ui.color.surface,
        }}>
          Learner Dashboard →
        </Link>
        <Link href="/dashboard/instructor" style={{
          fontSize: ui.font.size.md, fontWeight: ui.font.weight.medium, color: ui.color.body,
          textDecoration: 'none', padding: '10px 24px', borderRadius: ui.radius.md,
          border: `1px solid ${ui.color.lineStrong}`, background: ui.color.surface,
        }}>
          Instructor View →
        </Link>
        <a href="http://localhost:3000" target="_blank" rel="noopener noreferrer" style={{
          fontSize: ui.font.size.md, fontWeight: ui.font.weight.medium, color: ui.color.body,
          textDecoration: 'none', padding: '10px 24px', borderRadius: ui.radius.md,
          border: `1px solid ${ui.color.lineStrong}`, background: ui.color.surface,
        }}>
          Grafana ↗
        </a>
        <a href="http://localhost:9090" target="_blank" rel="noopener noreferrer" style={{
          fontSize: ui.font.size.md, fontWeight: ui.font.weight.medium, color: ui.color.body,
          textDecoration: 'none', padding: '10px 24px', borderRadius: ui.radius.md,
          border: `1px solid ${ui.color.lineStrong}`, background: ui.color.surface,
        }}>
          Prometheus ↗
        </a>
      </div>

      <PageGuide tourId="governance" steps={STEPS} />
    </div>
  )
}
