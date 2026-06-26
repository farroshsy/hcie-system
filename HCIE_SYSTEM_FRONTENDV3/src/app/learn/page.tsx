'use client'

import { useEffect, useState, useRef, useCallback } from 'react'
import { useSearchParams } from 'next/navigation'
import { useAuth } from '@/contexts/auth_context'
import Link from 'next/link'
import { getBackendUrl } from '@/lib/api/backend-url'
import { getAuthHeaders } from '@/lib/auth-headers'
import { useT, useLanguage } from '@/contexts/language_context'
import { ArchetypeOnboardingModal, hasCompletedOnboarding, buildProfileFromAnswers } from '@/components/learn/ArchetypeOnboardingModal'
import { MaterialPane, type LearningMaterial } from '@/components/learn/MaterialPane'
import { conceptLabel } from '@/lib/catalog/k12-catalog'
import {
  DemoTask, TaskSignal, TaskKind, TASK_KIND_META, STRAND_LABEL, BLOOM_LABEL,
  DEMO_TASK_POOL, pickDemoTask, demoTaskForConcept, kindForModality,
} from '@/lib/catalog/task-types'
import { Panel, Tag, Callout, SectionTitle, Eyebrow, Stat } from '@/lib/ui/primitives'
import { t as ui } from '@/lib/ui/theme'
import { TaskBody } from './TaskBody'
import PageGuide, { TourStep } from '@/components/help/PageGuide'

// ─── Types ────────────────────────────────────────────────────────────────────

type Modality = 'mpq' | 'text' | 'video' | 'audio' | 'interactive' | 'unknown'

interface RecommendResponse {
  task_id: string | null
  concept_id: string | null
  representation: string | null
  difficulty: number | null
  question_text: string | null
  choices: string[]
  governance: Record<string, any>
  cold_start: Record<string, any>
  selection_metrics: Record<string, any>
  semantic_version: string
  media_url?: string | null
  media_type?: 'video' | 'audio' | string | null
  transcript?: string | null
  // Multi-format extension: when present, render via <TaskBody> instead of the
  // legacy MCQ/text inputs. `kind` mirrors content.kind for quick checks.
  kind?: TaskKind
  content?: DemoTask
}

interface AttemptResponse {
  event_id: string
  concept_id: string
  correct: boolean
  mastery: number | null
  payload: {
    mastery?: number
    jt_value?: number
    jt_transfer_contribution?: number
    jt_delta_m_contribution?: number
    jt_challenge_contribution?: number
    jt_uncertainty_contribution?: number
    jt_zpd_contribution?: number
    jt_attribution?: Record<string, number>
    transfer_amounts?: Record<string, number>
    bayesian_alpha?: number
    bayesian_beta?: number
    kalman_mastery?: number
    lyapunov_mastery?: number
    mastery_delta?: number
    zpd_score?: number
    [key: string]: any
  }
}

interface ConceptLockState {
  id: string
  locked: boolean
  prerequisites: string[]
  missing_prereqs: string[]
  mastery_threshold: number
}

interface JTSignals {
  delta_m: number
  transfer_realized: number
  challenge: number
  uncertainty: number
  zpd: number
  transfer_prospective: number
}

// ─── Constants ─────────────────────────────────────────────────────────────────

const BACKEND = getBackendUrl()
const TRANSFER_ACTIVATION_THRESHOLD = 0.08

const MODALITY_META: Record<Modality, { label: string; color: string; icon: string; desc: string }> = {
  mpq:         { label: 'Multiple Choice',  color: '#2980B9', icon: '◉', desc: 'Select the best answer' },
  text:        { label: 'Text Response',    color: '#8E44AD', icon: '✎', desc: 'Type your answer' },
  video:       { label: 'Video + Question', color: '#C0392B', icon: '▶', desc: 'Watch then answer' },
  audio:       { label: 'Audio + Question', color: '#6C3483', icon: '♪', desc: 'Listen then answer' },
  interactive: { label: 'Interactive',      color: '#27AE60', icon: '⬡', desc: 'Hands-on exercise' },
  unknown:     { label: 'Question',         color: '#7F8C8D', icon: '?', desc: 'Answer the question' },
}

const JT_DIMS: { key: keyof JTSignals; label: string; color: string }[] = [
  { key: 'delta_m',           label: 'ΔM Mastery Gain',     color: '#2980B9' },
  { key: 'transfer_realized', label: 'T_realized Transfer',  color: '#C0392B' },
  { key: 'challenge',         label: 'Challenge Fit',        color: '#8E44AD' },
  { key: 'uncertainty',       label: 'Uncertainty Drive',    color: '#D35400' },
  { key: 'zpd',               label: 'ZPD Alignment',        color: '#27AE60' },
  { key: 'transfer_prospective', label: 'T_prospective',     color: '#16A085' },
]

// ─── Demo task adaptation ──────────────────────────────────────────────────────
// Turn a rich DemoTask (any of the 8 formats) into the RecommendResponse the page
// renders. question_text/choices are kept for back-compat (header + legacy render);
// `kind`+`content` drive the multi-format <TaskBody>.
function demoToRecommend(demo: DemoTask): RecommendResponse {
  return {
    task_id: demo.id,
    concept_id: demo.conceptId,
    representation: demo.kind,
    difficulty: demo.difficulty,
    question_text: demo.prompt,
    choices: demo.kind === 'mcq' ? demo.choices : [],
    governance: { cold_start: false, transfer_edges_active: 2 },
    cold_start: { active: false },
    selection_metrics: { policy_selector: 'hcie', confidence: 0.68 },
    semantic_version: '1.0',
    kind: demo.kind,
    content: demo,
  }
}

// Offline/demo loop: cycle the pool so each "next task" is a different FORMAT.
function buildMockTask(seed?: number): RecommendResponse {
  return demoToRecommend(pickDemoTask(seed))
}

function backendTaskToDemoTask(data: RecommendResponse): DemoTask | null {
  const raw = (data.content ?? {}) as Record<string, any>
  const conceptId = data.concept_id ?? raw.conceptId ?? raw.concept_id
  if (!conceptId) return null

  const kind = (data.kind ?? raw.kind ?? kindForModality(data.representation)) as TaskKind
  const choices = (raw.choices ?? data.choices ?? []) as string[]
  const correctAnswer = raw.correct_answer ?? raw.correctAnswer
  const correctIndex = typeof raw.correctIndex === 'number'
    ? raw.correctIndex
    : Math.max(0, choices.findIndex(c => c === correctAnswer))
  const base = {
    id: data.task_id ?? raw.id ?? `${conceptId}-${kind}`,
    conceptId,
    strand: 'any' as const,
    difficulty: Number(data.difficulty ?? raw.difficulty ?? 0.5),
    title: raw.title ?? data.question_text ?? 'Learning task',
    prompt: raw.prompt ?? raw.question ?? data.question_text ?? 'Answer the question.',
  }

  if (kind === 'video_question') {
    const mediaUrl = raw.mediaUrl ?? raw.media_url ?? data.media_url
    if (!mediaUrl || choices.length === 0) return null
    return {
      ...base,
      kind,
      mediaUrl,
      transcript: raw.transcript ?? data.transcript ?? undefined,
      choices,
      correctIndex,
      explanation: raw.explanation,
    } as DemoTask
  }
  if (kind === 'audio_listen') {
    const mediaUrl = raw.mediaUrl ?? raw.media_url ?? data.media_url
    if (!mediaUrl || choices.length === 0) return null
    return {
      ...base,
      kind,
      mediaUrl,
      transcript: raw.transcript ?? data.transcript ?? undefined,
      choices,
      correctIndex,
      explanation: raw.explanation,
    } as DemoTask
  }
  if ((kind === 'mcq' || data.representation === 'multiple_choice') && choices.length > 0) {
    return {
      ...base,
      kind: 'mcq',
      choices,
      correctIndex,
      explanation: raw.explanation,
    } as DemoTask
  }
  return null
}

// Live path: preserve backend content whenever it is rich enough to render.
// Fall back to demo tasks only for legacy/stub responses.
function enrichWithKind(data: RecommendResponse): RecommendResponse {
  const backendTask = backendTaskToDemoTask(data)
  if (backendTask) {
    return {
      ...data,
      kind: backendTask.kind,
      content: backendTask,
      representation: backendTask.kind,
      question_text: data.question_text || backendTask.prompt,
      choices: 'choices' in backendTask ? backendTask.choices : (data.choices ?? []),
    }
  }
  let demo: DemoTask | null = data.concept_id ? demoTaskForConcept(data.concept_id) : null
  if (!demo) {
    const kind = kindForModality(data.representation)
    demo = DEMO_TASK_POOL.find(t => t.kind === kind) ?? DEMO_TASK_POOL[0]
  }
  // Align the format to the recommended concept while preserving the live task_id.
  const content = { ...demo, conceptId: data.concept_id ?? demo.conceptId } as DemoTask
  return {
    ...data,
    kind: content.kind,
    content,
    representation: content.kind,
    question_text: data.question_text || content.prompt,
    choices: content.kind === 'mcq' ? content.choices : (data.choices ?? []),
  }
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function detectModality(rep: string | null): Modality {
  if (!rep) return 'unknown'
  const r = rep.toLowerCase()
  if (r.includes('mpq') || r.includes('multiple') || r.includes('choice')) return 'mpq'
  if (r.includes('video')) return 'video'
  if (r.includes('audio') || r.includes('listen')) return 'audio'
  if (r.includes('interactive') || r.includes('drag') || r.includes('sort')) return 'interactive'
  if (r.includes('text') || r.includes('open') || r.includes('free')) return 'text'
  return 'mpq' // default for unknown representations with choices
}

function shortConcept(c: string) {
  return conceptLabel(c)
}

function safeFloat(v: any): number {
  const f = parseFloat(v)
  return isNaN(f) ? 0 : f
}

function extractJT(payload: AttemptResponse['payload']): JTSignals {
  const attr = payload?.jt_attribution ?? {}
  return {
    delta_m:              safeFloat(attr.delta_m           ?? payload.jt_delta_m_contribution),
    transfer_realized:    safeFloat(attr.transfer_realized ?? payload.jt_transfer_contribution),
    challenge:            safeFloat(attr.challenge         ?? payload.jt_challenge_contribution),
    uncertainty:          safeFloat(attr.uncertainty       ?? payload.jt_uncertainty_contribution),
    zpd:                  safeFloat(attr.zpd               ?? payload.jt_zpd_contribution),
    transfer_prospective: safeFloat(attr.transfer_prospective ?? 0),
  }
}

// ─── Sub-components ────────────────────────────────────────────────────────────

function ModalityBadge({ modality }: { modality: Modality }) {
  const m = MODALITY_META[modality]
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 5,
      background: m.color + '18', color: m.color,
      border: `1px solid ${m.color}40`, borderRadius: 6,
      padding: '3px 10px', fontSize: 12, fontWeight: 700,
    }}>
      <span>{m.icon}</span> {m.label}
    </span>
  )
}

// Badge for a multi-format task: format + Bloom verb + strand fit. Makes the
// "the MAB selects task FORMAT, matched to Bloom level + strand" story visible.
function KindBadge({ kind }: { kind: TaskKind }) {
  const k = TASK_KIND_META[kind]
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
      <span style={{
        display: 'inline-flex', alignItems: 'center', gap: 5,
        background: k.color + '18', color: k.color, border: `1px solid ${k.color}40`,
        borderRadius: 6, padding: '3px 10px', fontSize: 12, fontWeight: 700,
      }}>
        <span>{k.icon}</span> {k.label}
      </span>
      <span title="Bloom level" style={{
        fontSize: 11, fontWeight: 600, color: '#5B4B8A', background: '#F3F0FA',
        border: '1px solid #D6CCEC', borderRadius: 4, padding: '2px 7px',
      }}>
        Bloom {k.bloom} · {BLOOM_LABEL[k.bloom]} · {k.bloomVerb}
      </span>
      {k.strands.filter(s => s !== 'any').map(s => (
        <span key={s} title={STRAND_LABEL[s]} style={{
          fontSize: 11, fontWeight: 600, color: '#1B5E55', background: '#E8F6F3',
          border: '1px solid #B7E0D7', borderRadius: 4, padding: '2px 7px',
        }}>{s}</span>
      ))}
    </span>
  )
}

function DifficultyBar({ value }: { value: number }) {
  const color = value < 0.35 ? ui.tone.ok.fg : value < 0.65 ? ui.modelColor.irt_1pl : ui.tone.bad.fg
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: ui.space.sm }}>
      <div style={{ flex: 1, height: 6, background: ui.color.line, borderRadius: 999, overflow: 'hidden' }}>
        <div style={{ width: `${value * 100}%`, height: '100%', background: color, borderRadius: 999,
                      transition: 'width 0.4s' }} />
      </div>
      <span style={{ fontSize: ui.font.size.sm, color, fontWeight: ui.font.weight.bold, minWidth: 32,
                     fontVariantNumeric: 'tabular-nums' }}>
        {(value * 100).toFixed(0)}%
      </span>
    </div>
  )
}

function JTSignalPanel({ signals, masteryDelta, transferActive }: {
  signals: JTSignals
  masteryDelta: number
  transferActive: boolean
}) {
  const total = Object.values(signals).reduce((s, v) => s + Math.abs(v), 0) || 1
  return (
    <Panel pad="lg">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    gap: ui.space.sm, marginBottom: ui.space.md }}>
        <div style={{ fontSize: ui.font.size.base, fontWeight: ui.font.weight.bold, color: ui.color.body }}>
          Joint Transfer Governance — 6D Attribution
        </div>
        {transferActive && (
          <Tag tone="bad" style={{ letterSpacing: '0.05em' }}>
            ⚡ TRANSFER ACTIVATED
          </Tag>
        )}
      </div>
      {JT_DIMS.map(({ key, label, color }) => {
        const v = Math.abs(signals[key])
        const pct = total > 0 ? (v / total) * 100 : 0
        return (
          <div key={key} style={{ marginBottom: ui.space.sm }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: ui.font.size.sm, marginBottom: 2 }}>
              <span style={{ color: ui.color.body }}>{label}</span>
              <span style={{ color, fontWeight: ui.font.weight.bold, fontVariantNumeric: 'tabular-nums' }}>
                {v.toFixed(4)} ({pct.toFixed(0)}%)
              </span>
            </div>
            <div style={{ height: 5, background: ui.color.line, borderRadius: 999, overflow: 'hidden' }}>
              <div style={{ width: `${pct}%`, height: '100%', background: color, borderRadius: 999,
                            transition: 'width 0.5s ease' }} />
            </div>
          </div>
        )
      })}
      <div style={{ marginTop: ui.space.md, padding: `${ui.space.sm}px ${ui.space.md}px`,
                    background: ui.color.subtle, border: `1px solid ${ui.color.line}`,
                    borderRadius: ui.radius.sm, display: 'flex', gap: ui.space.lg, fontSize: ui.font.size.sm }}>
        <div>
          <span style={{ color: ui.color.muted }}>Mastery Δ </span>
          <span style={{ fontWeight: ui.font.weight.bold, color: masteryDelta >= 0 ? ui.tone.ok.fg : ui.tone.bad.fg,
                         fontVariantNumeric: 'tabular-nums' }}>
            {masteryDelta >= 0 ? '+' : ''}{(masteryDelta * 100).toFixed(2)}%
          </span>
        </div>
        <div>
          <span style={{ color: ui.color.muted }}>T_realized </span>
          <span style={{ fontWeight: ui.font.weight.bold, color: transferActive ? ui.tone.bad.fg : ui.color.muted,
                         fontVariantNumeric: 'tabular-nums' }}>
            {(signals.transfer_realized * 100).toFixed(1)}%
          </span>
        </div>
      </div>
    </Panel>
  )
}

function RecommendationExplanation({ rec, isColdStart }: {
  rec: RecommendResponse
  isColdStart: boolean
}) {
  const confidence = safeFloat(rec.selection_metrics?.confidence ?? rec.selection_metrics?.policy_score ?? 0.5)
  const policy = rec.selection_metrics?.policy_selector ?? 'hcie'
  const confColor = confidence > 0.7 ? ui.tone.ok.fg : confidence > 0.4 ? ui.modelColor.irt_1pl : ui.tone.bad.fg

  return (
    <Panel tone="info" pad="lg" style={{ fontSize: ui.font.size.base }}>
      <div style={{ fontWeight: ui.font.weight.bold, color: ui.color.heading,
                    marginBottom: ui.space.sm, fontSize: ui.font.size.md }}>
        Why this task?
      </div>
      <div style={{ display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                    gap: ui.space.sm, marginBottom: ui.space.md }}>
        <div style={{ background: ui.color.surface, borderRadius: ui.radius.sm,
                      padding: `${ui.space.sm}px ${ui.space.md - 2}px`, border: `1px solid ${ui.color.line}` }}>
          <div style={{ color: ui.color.muted, fontSize: ui.font.size.xs, marginBottom: 2 }}>Policy</div>
          <div style={{ fontWeight: ui.font.weight.bold, color: ui.color.ink,
                        textTransform: 'uppercase', fontSize: ui.font.size.sm, letterSpacing: '0.04em' }}>
            {policy}
          </div>
        </div>
        <div style={{ background: ui.color.surface, borderRadius: ui.radius.sm,
                      padding: `${ui.space.sm}px ${ui.space.md - 2}px`, border: `1px solid ${ui.color.line}` }}>
          <div style={{ color: ui.color.muted, fontSize: ui.font.size.xs, marginBottom: 2 }}>Confidence</div>
          <div style={{ fontWeight: ui.font.weight.bold, color: confColor, fontSize: ui.font.size.md,
                        fontVariantNumeric: 'tabular-nums' }}>
            {(confidence * 100).toFixed(0)}%
          </div>
        </div>
      </div>
      {isColdStart && (
        <Callout tone="warn" style={{ marginBottom: ui.space.sm, fontSize: ui.font.size.sm }}>
          ❄️ Cold start — system is exploring your knowledge profile.
          Early interactions calibrate the ensemble.
        </Callout>
      )}
      <div style={{ color: ui.color.body, lineHeight: 1.6 }}>
        {confidence > 0.7
          ? 'This concept is well-matched to your current mastery level. The governance engine selected it because challenge and ZPD signals align with your learning trajectory.'
          : confidence > 0.4
          ? 'This concept is a productive challenge. The MAB selected this modality and difficulty based on recent performance signals.'
          : 'Exploring a new area. Low prior data means the system is gathering information to calibrate future recommendations.'}
      </div>
      {rec.governance?.transfer_edges_active > 0 && (
        <div style={{ marginTop: ui.space.sm, color: ui.tone.bad.fg, fontWeight: ui.font.weight.medium }}>
          ⚡ {rec.governance.transfer_edges_active} prerequisite edge(s) active — transfer will fire on correct answer.
        </div>
      )}
    </Panel>
  )
}

function MasteryMeter({ before, after, concept }: {
  before: number | null
  after: number | null
  concept: string
}) {
  const b = before ?? 0
  const a = after ?? b
  const delta = a - b
  const deltaColor = delta >= 0 ? ui.tone.ok.fg : ui.tone.bad.fg
  return (
    <Panel pad="lg">
      <div style={{ fontSize: ui.font.size.base, fontWeight: ui.font.weight.bold, color: ui.color.body,
                    marginBottom: ui.space.md }}>
        Mastery — {shortConcept(concept)}
      </div>
      <div style={{ display: 'flex', gap: ui.space.xxl, alignItems: 'center', marginBottom: ui.space.md }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: ui.font.size.xs, color: ui.color.muted, marginBottom: 2 }}>Before</div>
          <div style={{ fontSize: ui.font.size.h2, fontWeight: ui.font.weight.heavy, color: ui.color.body,
                        fontVariantNumeric: 'tabular-nums' }}>
            {(b * 100).toFixed(1)}%
          </div>
        </div>
        <div style={{ fontSize: ui.font.size.xl, color: deltaColor }}>→</div>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: ui.font.size.xs, color: ui.color.muted, marginBottom: 2 }}>After</div>
          <div style={{ fontSize: ui.font.size.h2, fontWeight: ui.font.weight.heavy, color: deltaColor,
                        fontVariantNumeric: 'tabular-nums' }}>
            {(a * 100).toFixed(1)}%
          </div>
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: ui.font.size.sm, color: deltaColor, fontWeight: ui.font.weight.bold,
                        marginBottom: ui.space.xs }}>
            {delta >= 0 ? '▲' : '▼'} {Math.abs(delta * 100).toFixed(2)}%
          </div>
          <div style={{ height: 10, background: ui.color.line, borderRadius: 999, overflow: 'hidden', position: 'relative' }}>
            <div style={{ position: 'absolute', left: 0, top: 0, height: '100%',
                          width: `${b * 100}%`, background: ui.color.lineStrong, borderRadius: 999 }} />
            <div style={{ position: 'absolute', left: 0, top: 0, height: '100%',
                          width: `${a * 100}%`, background: deltaColor,
                          borderRadius: 999, transition: 'width 0.6s ease' }} />
          </div>
        </div>
      </div>
    </Panel>
  )
}

// ─── Guided walkthrough ─────────────────────────────────────────────────────

const STEPS: TourStep[] = [
  {
    selector: '[data-tour="data-source-badge"]',
    title: { en: 'Where the data comes from', id: 'Asal data' },
    body: {
      en: 'This badge tells you whether your answers go to the real tutor (Live backend) or to offline demo data (Mock). Check it before you start — Live means everything you do is recorded.',
      id: 'Badge ini menunjukkan apakah jawabanmu dikirim ke tutor sungguhan (Live backend) atau ke data demo offline (Mock). Cek dulu sebelum mulai — Live berarti semua yang kamu lakukan tercatat.',
    },
  },
  {
    selector: '[data-tour="session-metrics"]',
    title: { en: 'Your session at a glance', id: 'Ringkasan sesi' },
    body: {
      en: 'These cards track how many tasks you finished, how much your mastery grew, and your accuracy this session. They update after every answer.',
      id: 'Kartu ini melacak berapa task yang sudah kamu selesaikan, seberapa besar mastery naik, dan accuracy di sesi ini. Semuanya diperbarui setiap kali kamu menjawab.',
    },
  },
  {
    selector: '[data-tour="learn-tabs"]',
    title: { en: 'Study, then practice', id: 'Belajar lalu latihan' },
    body: {
      en: 'Switch between reading the Material for a concept and doing Practice questions on it. Start with Material if the topic is new to you.',
      id: 'Beralih antara membaca Material sebuah konsep dan mengerjakan soal Practice. Mulai dari Material kalau topiknya masih baru buatmu.',
    },
  },
  {
    selector: '[data-tour="task-area"]',
    title: { en: 'The question to answer', id: 'Soal yang dijawab' },
    body: {
      en: 'This is the task the tutor picked for you. Read the question, then choose or type your answer below and press Submit.',
      id: 'Ini task yang dipilihkan tutor untukmu. Baca soalnya, lalu pilih atau ketik jawaban di bawah dan tekan Submit.',
    },
  },
  {
    selector: '[data-tour="next-actions"]',
    title: { en: 'What to do next', id: 'Langkah berikutnya' },
    body: {
      en: 'After you answer, use "Practice again" to get another task on the same concept, or "Next concept" to move on and start with its study material.',
      id: 'Setelah menjawab, pakai "Practice again" untuk soal lain pada konsep yang sama, atau "Next concept" untuk lanjut ke konsep baru beserta materi belajarnya.',
    },
  },
]

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function LearnPage() {
  const t = useT()
  const { user, isAuthenticated, isLoading: authLoading } = useAuth()
  const searchParams = useSearchParams()
  const urlConcept = searchParams?.get('concept') ?? null
  // conceptFilter is seeded from the ?concept= deep-link but is STATE so the
  // free-recommend flow can adopt the concept it returns (material-first) and the
  // controls can clear it. (Previously this was a derived const, so setConceptFilter
  // calls threw ReferenceError at runtime — silently caught → the mock fallback.)
  const [conceptFilter, setConceptFilter] = useState<string | null>(urlConcept)
  const { language: uiLanguage } = useLanguage()

  type LearnTab = 'material' | 'practice'
  const [activeTab, setActiveTab] = useState<LearnTab>('practice')
  const [materials, setMaterials] = useState<LearningMaterial[]>([])
  const [loadingMaterials, setLoadingMaterials] = useState(false)
  const [showOnboarding, setShowOnboarding] = useState(false)

  const [task, setTask] = useState<RecommendResponse | null>(null)
  const [lockedConcept, setLockedConcept] = useState<ConceptLockState | null>(null)
  const [isMock, setIsMock] = useState(false)
  const [loadingTask, setLoadingTask] = useState(false)
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null)
  const [textAnswer, setTextAnswer] = useState('')
  // Multi-format tasks report their interaction here (answer, client grade, signal).
  const [taskSignal, setTaskSignal] = useState<TaskSignal | null>(null)
  const onSignal = useCallback((s: TaskSignal) => setTaskSignal(s), [])
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState<AttemptResponse | null>(null)
  const [masteryBefore, setMasteryBefore] = useState<number | null>(null)
  // Trajectory-backed session metrics: initialized from /v3/research/learner/{id}/governance/trajectory
  // so the strip reflects ACTUAL stored history, not just this browser session.
  const [sessionCount, setSessionCount] = useState(0)
  const [sessionMasteryGain, setSessionMasteryGain] = useState(0)
  const [transferEvents, setTransferEvents] = useState(0)
  const [accuracy, setAccuracy] = useState<number | null>(null)
  const [avgResponseTime, setAvgResponseTime] = useState<number | null>(null)
  const [uniqueConcepts, setUniqueConcepts] = useState(0)
  const [trajectoryLoaded, setTrajectoryLoaded] = useState(false)
  const startTime = useRef<number>(Date.now())
  // Latest-wins guard: the task-loading effect re-fires on several volatile deps
  // (auth settle, conceptFilter, language). Without this, an earlier invocation
  // (e.g. one that bailed during the brief auth-loading window) could land its
  // setState after a later, successful recommend and wrongly latch the mock badge.
  const loadSeq = useRef(0)

  const modality = detectModality(task?.representation ?? null)

  // ── Auth guard (no redirect — just show login prompt inline) ──────────────
  const needsAuth = !authLoading && !isAuthenticated

  // ── Load trajectory-backed session metrics from backend ────────────────────
  // Pulls real counters from the session-trace endpoint (joins trajectory_records
  // + experiment_trajectories). Falls back silently if backend is offline.
  const loadSessionMetrics = async () => {
    const userId = user?.id
    if (!BACKEND || !userId || !isAuthenticated) {
      setTrajectoryLoaded(true)
      return
    }
    try {
      const resp = await fetch(`${BACKEND}/v3/frontend/dashboard/session-trace/${userId}?limit=200`, {
        headers: getAuthHeaders(),
        signal: AbortSignal.timeout(5000),
      })
      if (!resp.ok) {
        setTrajectoryLoaded(true)
        return
      }
      const data = await resp.json()
      const summary = data.session_summary ?? {}
      setSessionCount(Number(summary.total_interactions ?? 0))
      setSessionMasteryGain(Number(summary.cumulative_mastery_gain ?? 0))
      setTransferEvents(Number(summary.transfer_events ?? 0))
      setAccuracy(summary.accuracy != null ? Number(summary.accuracy) : null)
      setAvgResponseTime(summary.avg_response_time != null ? Number(summary.avg_response_time) : null)
      setUniqueConcepts(Number(summary.unique_concepts ?? 0))
    } catch {
      // Network error — leave counters as 0 (real session starts fresh)
    } finally {
      setTrajectoryLoaded(true)
    }
  }

  // ── Load learning materials for the active concept ───────────────────────
  const loadMaterials = async () => {
    if (!BACKEND || !isAuthenticated || !conceptFilter) {
      setMaterials([])
      return
    }
    setLoadingMaterials(true)
    try {
      const lang = uiLanguage === 'id' ? 'id' : 'en'
      const resp = await fetch(
        `${BACKEND}/v3/learner/material?concept_id=${encodeURIComponent(conceptFilter)}&language=${lang}`,
        { headers: getAuthHeaders(), signal: AbortSignal.timeout(5000) },
      )
      if (resp.ok) {
        setMaterials(await resp.json())
      } else {
        setMaterials([])
      }
    } catch {
      setMaterials([])
    } finally {
      setLoadingMaterials(false)
    }
  }

  const submitArchetypeProfile = async (
    profile: ReturnType<typeof buildProfileFromAnswers>,
  ) => {
    if (!BACKEND || !user?.id) return
    await fetch(`${BACKEND}/v3/learner/archetype-profile/${user.id}`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(profile),
    })
  }

  // ── Load next task ─────────────────────────────────────────────────────────
  const loadTask = async () => {
    const seq = ++loadSeq.current
    setLoadingTask(true)
    setLockedConcept(null)
    setResult(null)
    setSelectedAnswer(null)
    setTextAnswer('')
    setTaskSignal(null)
    startTime.current = Date.now()

    // Genuine offline (no backend configured) → demo mock. This is the only case
    // that should latch the mock badge.
    if (!BACKEND) {
      await new Promise(r => setTimeout(r, 300))
      if (seq !== loadSeq.current) return
      setTask(buildMockTask(Date.now()))
      setIsMock(true)
      setLoadingTask(false)
      return
    }
    // Transient auth-loading window (authLoading, or token present but profile not
    // yet hydrated → isAuthenticated still false). Do NOT latch mock here — bail and
    // let the effect re-run loadTask once auth settles. (RouteGuard sends a genuinely
    // unauthenticated user to /login, so we never sit on /learn unauthenticated.)
    if (authLoading || !isAuthenticated) {
      setLoadingTask(false)
      return
    }

    try {
      if (conceptFilter && user?.id) {
        const lockResp = await fetch(`${BACKEND}/v3/concepts/${encodeURIComponent(user.id)}/locked`, {
          headers: getAuthHeaders(),
          signal: AbortSignal.timeout(5000),
        })
        if (lockResp.ok) {
          const lockData = await lockResp.json()
          const state = (lockData.concepts ?? []).find((c: ConceptLockState) => c.id === conceptFilter)
          if (state?.locked) {
            if (seq !== loadSeq.current) return
            setLockedConcept(state)
            setTask(null)
            setIsMock(false)
            setLoadingTask(false)
            return
          }
        }
      }
      const taskLang = uiLanguage === 'id' ? 'id' : 'en'
      const resp = await fetch(`${BACKEND}/v3/learner/recommend`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          concept_filter: conceptFilter ? [conceptFilter] : null,
          language: [taskLang],
        }),
        signal: AbortSignal.timeout(5000),
      })
      if (!resp.ok) throw new Error(`${resp.status}`)
      const data: RecommendResponse = await resp.json()
      // A newer load superseded this one (deps changed mid-flight) — drop the result
      // so a stale invocation can't clobber the latest state.
      if (seq !== loadSeq.current) return
      // Attach a curriculum-appropriate FORMAT (one of the 8 task kinds) to the
      // live recommendation so the ITS renders more than MCQ. The backend task_id
      // + concept_id are preserved for the attempt + governance pipeline.
      setTask(enrichWithKind(data))
      setIsMock(false)
      // Lead with the concept's material (in the learner's chosen modality) before
      // practice — turns the loop into study → practice instead of task-after-task.
      // Setting conceptFilter + the material tab together avoids a second recommend.
      if (!conceptFilter && data.concept_id) {
        setActiveTab('material')
        setConceptFilter(data.concept_id)
      }
    } catch (e) {
      if (seq !== loadSeq.current) return
      // Real failure (network/abort/non-2xx) → demo mock as a graceful fallback.
      // Logged so a session that silently degraded to mock is debuggable in prod.
      console.warn('[learn] live task load failed → mock fallback:', e)
      setTask(buildMockTask(Date.now()))
      setIsMock(true)
    } finally {
      if (seq === loadSeq.current) setLoadingTask(false)
    }
  }

  // ── Submit answer ─────────────────────────────────────────────────────────
  const submitAnswer = async () => {
    if (!task) return
    setSubmitting(true)

    const answer = taskSignal ? taskSignal.answer : (modality === 'text' ? textAnswer : (selectedAnswer ?? ''))
    const responseTime = (Date.now() - startTime.current) / 1000

    if (isMock) {
      await new Promise(r => setTimeout(r, 600))
      // Rich formats grade themselves client-side; fall back to a coin-flip only
      // for the legacy mock path where no signal correctness is available.
      const correct = taskSignal?.correct ?? (Math.random() > 0.4)
      const mockMasteryBefore = masteryBefore ?? 0.45
      const mockMasteryAfter = mockMasteryBefore + (correct ? 0.03 : -0.01)
      setResult({
        event_id: `mock-${Date.now()}`,
        concept_id: task.concept_id ?? 'mock',
        correct,
        mastery: mockMasteryAfter,
        payload: {
          mastery: mockMasteryAfter,
          mastery_delta: correct ? 0.03 : -0.01,
          jt_value: correct ? 0.72 : 0.31,
          jt_transfer_contribution: correct ? 0.22 : 0.02,
          jt_delta_m_contribution: correct ? 0.45 : 0.18,
          jt_challenge_contribution: correct ? 0.18 : 0.08,
          jt_uncertainty_contribution: 0.10,
          jt_zpd_contribution: 0.05,
          jt_attribution: {
            delta_m: correct ? 0.45 : 0.18,
            transfer_realized: correct ? 0.22 : 0.02,
            challenge: correct ? 0.18 : 0.08,
            uncertainty: 0.10,
            zpd: 0.05,
            transfer_prospective: 0.00,
          },
        },
      })
      setMasteryBefore(mockMasteryAfter)
      setSessionCount(c => c + 1)
      if (correct) setSessionMasteryGain(g => g + 0.03)
      if (correct && 0.22 > TRANSFER_ACTIVATION_THRESHOLD) setTransferEvents(t => t + 1)
      setSubmitting(false)
      return
    }

    if (!task.task_id || !task.concept_id) {
      setSubmitting(false)
      return
    }

    try {
      const isCorrect = taskSignal?.correct ?? (modality === 'mpq'
        ? (answer === task.choices?.[0])  // server evaluates; we send the answer
        : undefined)

      const resp = await fetch(`${BACKEND}/v3/learner/attempt`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          task_id: task.task_id,
          concept_id: task.concept_id,
          answer,
          correct: isCorrect,
          response_time: responseTime,
          signal_detail: taskSignal?.detail ?? {},
        }),
        signal: AbortSignal.timeout(8000),
      })
      if (!resp.ok) throw new Error(`${resp.status}`)
      const data: AttemptResponse = await resp.json()
      setResult(data)
      const jt = extractJT(data.payload)
      // Optimistic local update — the trajectory recorder will eventually persist
      // these to trajectory_records and the next loadSessionMetrics call will reconcile.
      setSessionCount(c => c + 1)
      if (data.correct) setSessionMasteryGain(g => g + safeFloat(data.payload?.mastery_delta))
      if (jt.transfer_realized > TRANSFER_ACTIVATION_THRESHOLD) setTransferEvents(t => t + 1)
      // Pull authoritative numbers from backend after a short delay (lets the
      // trajectory-recorder-consumer commit the row to trajectory_records).
      setTimeout(loadSessionMetrics, 1500)
    } catch {
      // Fallback on submission error
    } finally {
      setSubmitting(false)
    }
  }

  useEffect(() => {
    if (authLoading) return
    if (!isAuthenticated) return
    if (!hasCompletedOnboarding()) {
      setShowOnboarding(true)
    }
  }, [authLoading, isAuthenticated, user?.id])

  // Mirror a deep-link ?concept=X into state. Only when the URL actually names a
  // concept, so the free-recommend adoption (which writes state on a bare /learn) is
  // not reset to null on every render.
  useEffect(() => {
    if (urlConcept) setConceptFilter(urlConcept)
  }, [urlConcept])

  useEffect(() => {
    if (conceptFilter) setActiveTab('material')
  }, [conceptFilter])

  useEffect(() => {
    // Gate on the SETTLED auth state. `isAuthenticated` is a dep so this re-runs the
    // moment auth resolves — without it, a first run during the auth-loading window
    // could leave the page stuck. `activeTab` is intentionally NOT a dep: when a
    // conceptFilter is present we go material-first (load material, skip the task —
    // the practice task loads lazily via switchToPractice), so tab switches must not
    // re-fire a recommend.
    if (authLoading || !isAuthenticated) return
    loadSessionMetrics()
    if (conceptFilter) {
      loadMaterials()
      return
    }
    loadTask()
  }, [authLoading, isAuthenticated, user?.id, conceptFilter, uiLanguage])

  useEffect(() => {
    if (authLoading || !conceptFilter) return
    loadMaterials()
  }, [uiLanguage, conceptFilter])

  const switchToPractice = () => {
    setActiveTab('practice')
    if (!task && !loadingTask) loadTask()
  }

  // ─── Render ───────────────────────────────────────────────────────────────

  const jt = result ? extractJT(result.payload) : null
  const transferActive = jt ? jt.transfer_realized > TRANSFER_ACTIVATION_THRESHOLD : false
  const masteryAfter = result?.mastery ?? result?.payload?.mastery ?? null
  // A multi-format task is submittable once its renderer reports `complete`;
  // legacy MCQ/text keep their original selection/non-empty checks.
  const canSubmit = task?.kind
    ? !!taskSignal?.complete
    : (modality === 'text' ? !!textAnswer.trim() : !!selectedAnswer)

  const navLinkStyle = {
    fontSize: ui.font.size.base, color: ui.tone.info.fg, textDecoration: 'none',
    padding: `${ui.space.xs + 1}px ${ui.space.md}px`, border: `1px solid ${ui.tone.info.border}`,
    borderRadius: ui.radius.sm, fontWeight: ui.font.weight.medium,
  } as const

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', padding: `${ui.space.xxl}px ${ui.space.xl}px 64px` }}>

      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start',
                    gap: ui.space.lg, marginBottom: ui.space.xl }}>
        <div>
          <Eyebrow color={ui.tone.info.fg}>{t('learn.eyebrow')}</Eyebrow>
          <h1 style={{ fontSize: ui.font.size.h2, fontWeight: ui.font.weight.heavy,
                       color: ui.color.ink, margin: 0 }}>
            {t('learn.title')}
          </h1>
        </div>
        <div data-tour="data-source-badge" style={{ display: 'flex', gap: ui.space.sm, alignItems: 'center', flexWrap: 'wrap',
                      justifyContent: 'flex-end' }}>
          {isMock && (
            <Tag tone="warn">○ Mock data (no backend)</Tag>
          )}
          {!isMock && (
            <Tag tone="ok">● Live backend</Tag>
          )}
          <Link href="/learn/concepts" style={navLinkStyle}>
            🗺 Concepts
          </Link>
          <Link href="/dashboard/learner" style={navLinkStyle}>
            Dashboard →
          </Link>
        </div>
      </div>

      {/* Concept-filter banner: shown when ?concept=X is in the URL */}
      {conceptFilter && (
        <Callout tone="info" style={{ marginBottom: ui.space.md, display: 'flex',
                                      alignItems: 'center', gap: ui.space.md }}>
          <span style={{ color: ui.tone.info.fg, fontWeight: ui.font.weight.bold }}>
            Focusing on: <code style={{ background: ui.tone.info.border + '60',
                                        padding: '1px 6px', borderRadius: ui.radius.sm,
                                        fontVariantNumeric: 'tabular-nums' }}>{conceptFilter}</code>
          </span>
          <button onClick={() => { setConceptFilter(null); setTask(null); setResult(null) }}
                  style={{ marginLeft: 'auto', color: ui.color.muted, background: 'none',
                           border: 'none', cursor: 'pointer', textDecoration: 'none',
                           fontSize: ui.font.size.sm }}>
            ✕ clear filter
          </button>
        </Callout>
      )}

      {/* ── Session strip — trajectory-backed when backend live ──────────── */}
      <div data-tour="session-metrics" style={{ marginBottom: ui.space.xl }}>
        <div style={{ display: 'flex', justifyContent: 'space-between',
                       alignItems: 'baseline', gap: ui.space.sm, marginBottom: ui.space.sm }}>
          <div style={{ fontSize: ui.font.size.xs, color: ui.color.faint, fontWeight: ui.font.weight.medium,
                         textTransform: 'uppercase', letterSpacing: '0.06em' }}>
            Session Metrics
          </div>
          {trajectoryLoaded && !isMock && (
            <div style={{ fontSize: ui.font.size.xs, color: ui.tone.ok.fg, fontWeight: ui.font.weight.medium }}>
              ● backed by trajectory_records
            </div>
          )}
          {isMock && (
            <div style={{ fontSize: ui.font.size.xs, color: ui.tone.warn.fg, fontWeight: ui.font.weight.medium }}>○ in-session only</div>
          )}
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: ui.space.md }}>
          {[
            { label: 'Tasks done', value: sessionCount, color: ui.modelColor.sakt,
              sub: uniqueConcepts > 0 ? `${uniqueConcepts} concepts` : undefined },
            { label: 'Mastery gain', value: `${sessionMasteryGain >= 0 ? '+' : ''}${(sessionMasteryGain * 100).toFixed(1)}%`,
              color: sessionMasteryGain >= 0 ? ui.tone.ok.fg : ui.tone.bad.fg },
            { label: 'Transfer events', value: transferEvents, color: ui.tone.bad.fg,
              sub: 'T_realized > 0.08' },
            { label: 'Accuracy', value: accuracy != null ? `${(accuracy * 100).toFixed(0)}%` : '—',
              color: ui.modelColor.gkt,
              sub: avgResponseTime != null ? `avg ${avgResponseTime.toFixed(1)}s` : undefined },
          ].map(({ label, value, color, sub }) => (
            <Panel key={label} pad="md">
              <div style={{ fontSize: ui.font.size.xs, color: ui.color.muted, marginBottom: 2 }}>{label}</div>
              <div style={{ fontSize: ui.font.size.xl, fontWeight: ui.font.weight.heavy, color,
                            fontVariantNumeric: 'tabular-nums' }}>
                {value}
              </div>
              {sub && (
                <div style={{ fontSize: ui.font.size.xs, color: ui.color.faint, marginTop: 1 }}>{sub}</div>
              )}
            </Panel>
          ))}
        </div>
      </div>

      {/* ── Material / Practice tabs (when studying a specific concept) ─── */}
      {conceptFilter && !lockedConcept && (
        <div data-tour="learn-tabs" style={{ display: 'flex', gap: ui.space.xs, marginBottom: ui.space.lg,
                      background: ui.color.subtle, border: `1px solid ${ui.color.line}`,
                      borderRadius: ui.radius.lg, padding: ui.space.xs, width: 'fit-content' }}>
          {(['material', 'practice'] as LearnTab[]).map(tab => (
            <button key={tab} type="button"
              onClick={() => tab === 'practice' ? switchToPractice() : setActiveTab('material')}
              style={{
                padding: `${ui.space.sm}px ${ui.space.lg + 2}px`, borderRadius: ui.radius.md,
                border: 'none', cursor: 'pointer',
                fontSize: ui.font.size.md, fontWeight: ui.font.weight.bold,
                background: activeTab === tab ? ui.color.surface : 'transparent',
                color: activeTab === tab ? ui.tone.info.fg : ui.color.muted,
                boxShadow: activeTab === tab ? '0 1px 4px rgba(0,0,0,0.08)' : 'none',
              }}>
              {tab === 'material'
                ? `📖 ${t('learn.tab.material', 'Material')}`
                : `✎ ${t('learn.tab.practice', 'Practice')}`}
            </button>
          ))}
        </div>
      )}

      {/* ── Main content ───────────────────────────────────────────────────── */}
      {lockedConcept ? (
        <Panel tone="bad" pad="xl" style={{ color: ui.color.ink }}>
          <Eyebrow color={ui.tone.bad.fg}>Concept locked</Eyebrow>
          <h2 style={{ fontSize: ui.font.size.h2, fontWeight: ui.font.weight.heavy,
                       color: ui.color.ink, margin: `0 0 ${ui.space.sm}px` }}>
            Complete prerequisite concepts first
          </h2>
          <p style={{ fontSize: ui.font.size.md, color: ui.color.muted, lineHeight: 1.6, marginBottom: ui.space.md }}>
            <code style={{ background: ui.tone.bad.bg, border: `1px solid ${ui.tone.bad.border}`,
                           padding: '2px 6px', borderRadius: ui.radius.sm }}>
              {lockedConcept.id}
            </code>{' '}
            is locked until your mastery reaches {(lockedConcept.mastery_threshold * 100).toFixed(0)}%
            on its prerequisite concept{lockedConcept.missing_prereqs.length === 1 ? '' : 's'}.
          </p>
          <div style={{ display: 'flex', gap: ui.space.sm, flexWrap: 'wrap', marginBottom: ui.space.lg }}>
            {lockedConcept.missing_prereqs.map(p => (
              <Link key={p} href={`/learn?concept=${encodeURIComponent(p)}`}
                    style={{ textDecoration: 'none', color: ui.tone.info.fg, background: ui.tone.info.bg,
                             border: `1px solid ${ui.tone.info.border}`, borderRadius: 999,
                             padding: `${ui.space.xs + 2}px ${ui.space.md}px`,
                             fontSize: ui.font.size.base, fontWeight: ui.font.weight.bold }}>
                Study {shortConcept(p)}
              </Link>
            ))}
          </div>
          <Link href="/learn/concepts" style={{ color: ui.color.muted, fontSize: ui.font.size.base,
                                                textDecoration: 'none', fontWeight: ui.font.weight.medium }}>
            View concept map →
          </Link>
        </Panel>
      ) : activeTab === 'material' && conceptFilter ? (
        <MaterialPane
          materials={materials}
          loading={loadingMaterials}
          onStartPractice={switchToPractice}
        />
      ) : loadingTask ? (
        <Panel pad="xl" style={{ padding: 48, textAlign: 'center', color: ui.color.muted }}>
          <div style={{ fontSize: 28, marginBottom: ui.space.md }}>⟳</div>
          {t('learn.loadingTask', 'Loading next task…')}
        </Panel>
      ) : task ? (
        <div style={{ display: 'grid', gap: ui.space.lg }}>

          {/* Task card */}
          <Panel data-tour="task-area" pad="xl" style={{ padding: ui.space.xxl, boxShadow: '0 1px 4px rgba(0,0,0,0.06)' }}>
            {/* Task meta */}
            <div style={{ display: 'flex', gap: ui.space.sm, marginBottom: ui.space.lg, flexWrap: 'wrap',
                          alignItems: 'center' }}>
              {task.kind ? <KindBadge kind={task.kind} /> : <ModalityBadge modality={modality} />}
              <span style={{ fontSize: ui.font.size.base, color: ui.color.body, background: ui.color.subtle,
                             border: `1px solid ${ui.color.line}`, borderRadius: ui.radius.sm,
                             padding: '3px 8px', fontWeight: ui.font.weight.medium }}>
                {shortConcept(task.concept_id ?? 'Unknown concept')}
              </span>
              {task.difficulty != null && (
                <div style={{ flex: 1, minWidth: 120, maxWidth: 160 }}>
                  <div style={{ fontSize: ui.font.size.xs, color: ui.color.muted, marginBottom: 2 }}>Difficulty</div>
                  <DifficultyBar value={task.difficulty} />
                </div>
              )}
              {task.cold_start?.active && (
                <Tag tone="warn">❄️ Cold start</Tag>
              )}
            </div>

            {/* Question */}
            <div style={{ fontSize: ui.font.size.lg + 2, fontWeight: ui.font.weight.medium, color: ui.color.ink,
                          lineHeight: 1.6, marginBottom: ui.space.xl }}>
              {task.question_text ?? 'Answer the following question:'}
            </div>

            {/* Answer area */}
            {!result && (
              <>
                {/* Multi-format task body — one of the 8 task kinds */}
                {task.kind && task.content && (
                  <div style={{ marginBottom: ui.space.xl }}>
                    <TaskBody task={task.content} disabled={submitting} onSignal={onSignal} />
                  </div>
                )}
                {/* MPQ choices (legacy / live MCQ without a kind) */}
                {!task.kind && (modality === 'mpq' || task.choices?.length > 0) && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: ui.space.sm, marginBottom: ui.space.xl }}>
                    {(task.choices ?? []).map((choice, i) => (
                      <button key={i} onClick={() => setSelectedAnswer(choice)}
                        style={{
                          textAlign: 'left', padding: `${ui.space.md}px ${ui.space.lg}px`, borderRadius: ui.radius.md,
                          border: `2px solid ${selectedAnswer === choice ? ui.tone.info.fg : ui.color.line}`,
                          background: selectedAnswer === choice ? ui.tone.info.bg : ui.color.surface,
                          cursor: 'pointer', fontSize: ui.font.size.lg - 1, color: ui.color.ink,
                          transition: 'all 0.15s',
                        }}>
                        <span style={{ fontWeight: ui.font.weight.bold, color: ui.color.muted, marginRight: ui.space.md }}>
                          {String.fromCharCode(65 + i)}.
                        </span>
                        {choice}
                      </button>
                    ))}
                  </div>
                )}

                {/* Text input */}
                {!task.kind && modality === 'text' && task.choices?.length === 0 && (
                  <textarea
                    value={textAnswer}
                    onChange={e => setTextAnswer(e.target.value)}
                    placeholder="Type your answer here…"
                    style={{
                      width: '100%', minHeight: 100, padding: ui.space.md,
                      border: `2px solid ${ui.color.line}`, borderRadius: ui.radius.md,
                      fontSize: ui.font.size.lg - 1, color: ui.color.ink, resize: 'vertical',
                      marginBottom: ui.space.lg, boxSizing: 'border-box',
                    }}
                  />
                )}

                <button
                  onClick={submitAnswer}
                  disabled={submitting || !canSubmit}
                  style={{
                    padding: `${ui.space.md}px ${ui.space.xxl + 4}px`, color: ui.color.surface,
                    border: 'none', borderRadius: ui.radius.md, fontSize: ui.font.size.lg - 1,
                    fontWeight: ui.font.weight.bold,
                    transition: 'opacity 0.2s, background 0.2s',
                    ...(submitting || !canSubmit
                      ? { background: ui.color.faint, cursor: 'not-allowed', opacity: 0.7 }
                      : { background: ui.tone.info.fg, cursor: 'pointer', opacity: 1 }),
                  }}>
                  {submitting ? 'Submitting…' : 'Submit Answer'}
                </button>
              </>
            )}

            {/* Result */}
            {result && (
              <Callout tone={result.correct ? 'ok' : 'bad'} style={{ marginBottom: ui.space.lg }}>
                <div style={{ fontSize: ui.font.size.xl, fontWeight: ui.font.weight.heavy,
                              color: result.correct ? ui.tone.ok.fg : ui.tone.bad.fg, marginBottom: ui.space.xs }}>
                  {result.correct ? '✓ Correct!' : '✗ Incorrect'}
                </div>
                <div style={{ fontSize: ui.font.size.md, color: result.correct ? ui.tone.ok.fg : ui.tone.bad.fg }}>
                  {result.correct
                    ? 'Great work. The governance engine updated your mastery estimate.'
                    : 'Not quite. Your mastery estimate has been adjusted for this concept.'}
                </div>
              </Callout>
            )}
          </Panel>

          {/* Two-column bottom panel */}
          {result && jt && (
            <div style={{ display: 'grid',
                          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                          gap: ui.space.lg }}>
              {/* Mastery meter */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: ui.space.md }}>
                <MasteryMeter
                  before={masteryBefore}
                  after={masteryAfter}
                  concept={result.concept_id}
                />
                <RecommendationExplanation
                  rec={task}
                  isColdStart={!!task.cold_start?.active}
                />
              </div>
              {/* JT signals */}
              <JTSignalPanel
                signals={jt}
                masteryDelta={safeFloat(result.payload?.mastery_delta)}
                transferActive={transferActive}
              />
            </div>
          )}

          {/* Recommendation explanation (pre-answer) */}
          {!result && (
            <RecommendationExplanation
              rec={task}
              isColdStart={!!task.cold_start?.active}
            />
          )}

          {/* Next: more practice on this concept, or advance to the next concept
              (which leads with its material in the learner's modality). */}
          {result && (
            <div data-tour="next-actions" style={{ textAlign: 'center', display: 'flex', gap: ui.space.md, justifyContent: 'center', flexWrap: 'wrap' }}>
              <button onClick={loadTask} style={{
                padding: `${ui.space.md}px ${ui.space.xxl}px`, background: ui.color.surface,
                color: ui.tone.info.fg, border: `1px solid ${ui.tone.info.border}`, borderRadius: ui.radius.md,
                fontSize: ui.font.size.lg - 1, fontWeight: ui.font.weight.bold, cursor: 'pointer',
              }}>
                {t('learn.nextTask', 'Practice again →')}
              </button>
              <button onClick={() => { setResult(null); setTask(null); setConceptFilter(null) }} style={{
                padding: `${ui.space.md}px ${ui.space.xxl}px`, background: ui.tone.info.fg,
                color: ui.color.surface, border: 'none', borderRadius: ui.radius.md,
                fontSize: ui.font.size.lg - 1, fontWeight: ui.font.weight.bold, cursor: 'pointer',
              }}>
                {t('learn.nextConcept', 'Next concept (study material) →')}
              </button>
            </div>
          )}
        </div>
      ) : null}

      <ArchetypeOnboardingModal
        open={showOnboarding}
        onComplete={() => setShowOnboarding(false)}
        onSkip={() => setShowOnboarding(false)}
        onSubmit={submitArchetypeProfile}
      />

      <PageGuide tourId="learn" steps={STEPS} />
    </div>
  )
}
