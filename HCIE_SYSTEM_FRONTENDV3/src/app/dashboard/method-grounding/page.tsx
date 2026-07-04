'use client'

/**
 * Method Grounding Hub — Tier 0–5 cascade as an operational evidence board.
 *
 * Reads:
 *   GET  /v3/frontend/dashboard/method-grounding              — progress
 *   GET  /v3/frontend/dashboard/method-grounding/evidence     — panels
 *   GET  /v3/frontend/dashboard/method-grounding/report/{id}  — drawer detail
 *   POST /v3/frontend/dashboard/method-grounding/run/{id}     — re-run a single step
 *   POST /v3/frontend/dashboard/method-grounding/rerun-batch  — bulk re-run cascade
 *   GET  /v3/frontend/dashboard/method-grounding/rerun-batch/{id} — job status
 *   GET  /v3/frontend/dashboard/method-grounding/rerun-batch  — list jobs
 *
 * Every tier step is a re-runnable evidence row: status, last run, artifact,
 * input hash, run+seal anchor, and a re-run trigger. The "Rerun cascade" tray
 * lets the user select multiple steps (or a whole tier / failed steps) and
 * have the backend run them sequentially in a background job, polled live.
 */

import { useCallback, useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import { getBackendUrl } from '@/lib/api/backend-url'
import { useT } from '@/contexts/language_context'

const BACKEND = getBackendUrl()

type Step = {
  id: string
  title: string
  status: string
  script?: string | null
  report_path?: string | null
  report_filename?: string | null
  finished_at?: string | null
  phase2_run_id?: string | null
  seal_id?: string | null
  input_hash?: string | null
  headline?: Record<string, unknown>
  type?: string
}
type Tier = { id: string; title: string; steps: Step[] }
type Anchor = { phase2_run_id?: string; seal_id?: string; lineage?: string; anchor_rows?: number }

type AnchorEntry = {
  phase2_run_id?: string
  seal_id?: string
  label?: string
  v2_active?: boolean
  promoted_at?: string
  demoted_at?: string
  created_at?: string
  summary?: {
    rows?: number
    fired?: number
    challenge_event_nonzero_pct?: number
    population_prior_nonzero_pct?: number
  }
}
type AnchorLedger = {
  active?: AnchorEntry
  candidates?: AnchorEntry[]
  history?: AnchorEntry[]
  anchor_path?: string
}
type Summary = { total_steps: number; passed: number; pending: number; warn: number; failed: number; deferred?: number; completion_pct: number }

type RerunResult = {
  step_id: string
  status: string  // done | failed | timeout | exception | skipped | missing
  exit_code?: number
  elapsed_s?: number
  report_status?: string
  report_finished_at?: string
  reason?: string
  error?: string
  stderr_tail?: string | null
  started_at?: string
}
type RerunJob = {
  job_id: string
  state: 'queued' | 'running' | 'done' | 'stopped' | string
  step_ids: string[]
  current_step_id?: string | null
  current_index: number
  results: RerunResult[]
  progress?: { completed: number; total: number }
  summary?: { done?: number; failed?: number; skipped?: number; timeout?: number; exception?: number; missing?: number }
  finished_at?: string
  started_at?: string
  queued_at?: string
  stop_on_fail?: boolean
  host_fs_steps?: string[]
  is_active?: boolean
  note?: string | null
}
type RerunListEntry = {
  job_id: string
  state: string
  queued_at?: string
  started_at?: string
  finished_at?: string
  step_count: number
  completed: number
  current_step_id?: string | null
  stop_on_fail?: boolean
  summary?: Record<string, number>
  note?: string | null
}

// `labelKey` resolves through t('methodGrounding.<labelKey>') at render time so
// the status pill is bilingual; the colors stay static.
const STATUS_TONE: Record<string, { bg: string; fg: string; labelKey: string }> = {
  pass:    { bg: '#1E8449', fg: '#fff', labelKey: 'statusPass' },
  fail:    { bg: '#C0392B', fg: '#fff', labelKey: 'statusFail' },
  warn:    { bg: '#B9770E', fg: '#fff', labelKey: 'statusWarn' },
  pending: { bg: '#94A3B8', fg: '#fff', labelKey: 'statusPending' },
  unknown: { bg: '#64748B', fg: '#fff', labelKey: 'statusUnknown' },
  deferred:  { bg: '#5B7083', fg: '#fff', labelKey: 'statusDeferred' },
  disclosed: { bg: '#1A5276', fg: '#fff', labelKey: 'statusDisclosed' },
}

// Tier blurbs resolve through t() at render — keyed by tier id.
const TIER_BLURB_KEYS: Record<string, string> = {
  tier0: 'tierBlurb0',
  tier1: 'tierBlurb1',
  tier2: 'tierBlurb2',
  tier3: 'tierBlurb3',
  tier4: 'tierBlurb4',
  tier5: 'tierBlurb5',
}

function authHeaders(): HeadersInit {
  if (typeof window === 'undefined') return {}
  const t = localStorage.getItem('hcie_auth_token') || localStorage.getItem('access_token')
  return t ? { Authorization: `Bearer ${t}` } : {}
}

export default function MethodGroundingPage() {
  const t = useT()
  const [tiers, setTiers] = useState<Tier[]>([])
  const [summary, setSummary] = useState<Summary | null>(null)
  const [anchor, setAnchor] = useState<Anchor>({})
  const [evidence, setEvidence] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState<string | null>(null)
  const [drawer, setDrawer] = useState<{ id: string; report: any | null; loading: boolean } | null>(null)
  const [msg, setMsg] = useState<string | null>(null)
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [activeJob, setActiveJob] = useState<RerunJob | null>(null)
  const [recentJobs, setRecentJobs] = useState<RerunListEntry[]>([])
  const [hostFsSteps, setHostFsSteps] = useState<string[]>([])
  const [stopOnFail, setStopOnFail] = useState(false)
  const [submittingBatch, setSubmittingBatch] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [progress, evi, jobs] = await Promise.all([
        fetch(`${BACKEND}/v3/frontend/dashboard/method-grounding`,
              { headers: authHeaders() }).then(r => r.json()),
        fetch(`${BACKEND}/v3/frontend/dashboard/method-grounding/evidence`,
              { headers: authHeaders() }).then(r => r.json()),
        fetch(`${BACKEND}/v3/frontend/dashboard/method-grounding/rerun-batch`,
              { headers: authHeaders() }).then(r => r.json()).catch(() => ({ jobs: [], host_fs_steps: [] })),
      ])
      setTiers(progress.tiers || [])
      setSummary(progress.summary || null)
      setAnchor({ ...(progress.anchor || {}), ...(evi.anchor || {}) })
      setEvidence(evi)
      setRecentJobs(jobs.jobs || [])
      setHostFsSteps(jobs.host_fs_steps || [])
      // Auto-attach to in-flight job if one is running and we don't already have it tracked.
      if (jobs.active && (!activeJob || activeJob.job_id !== jobs.active)) {
        try {
          const j = await fetch(`${BACKEND}/v3/frontend/dashboard/method-grounding/rerun-batch/${jobs.active}`,
                                { headers: authHeaders() }).then(r => r.json())
          setActiveJob(j)
        } catch { /* swallow */ }
      }
    } catch (e) {
      setMsg(`${t('methodGrounding.msgFailedToLoad')}: ${e}`)
    } finally {
      setLoading(false)
    }
  }, [activeJob, t])

  useEffect(() => { load() }, [])  // eslint-disable-line react-hooks/exhaustive-deps

  // Poll active job every 3 s while it is queued/running.
  useEffect(() => {
    if (!activeJob) return
    if (activeJob.state !== 'queued' && activeJob.state !== 'running') return
    const id = setInterval(async () => {
      try {
        const r = await fetch(`${BACKEND}/v3/frontend/dashboard/method-grounding/rerun-batch/${activeJob.job_id}`,
                              { headers: authHeaders() })
        const data: RerunJob = await r.json()
        setActiveJob(data)
        if (data.state !== 'queued' && data.state !== 'running') {
          clearInterval(id)
          await load()  // refresh tiers + recent-jobs list once batch ends
        }
      } catch { /* keep polling */ }
    }, 3000)
    return () => clearInterval(id)
  }, [activeJob?.job_id, activeJob?.state, load])

  const runStep = async (id: string) => {
    setRunning(id); setMsg(null)
    try {
      const res = await fetch(`${BACKEND}/v3/frontend/dashboard/method-grounding/run/${id}`,
                              { method: 'POST', headers: authHeaders() })
      const data = await res.json()
      setMsg(data.exit_code === 0
        ? `✓ ${id} ${t('methodGrounding.msgReran')} (status ${data.report_status})`
        : `✗ ${id} exit ${data.exit_code}`)
      await load()
    } catch (e) {
      setMsg(String(e))
    } finally {
      setRunning(null)
    }
  }

  const allRunnableIds = useMemo(
    () => tiers.flatMap(t => t.steps.filter(s => !!s.script).map(s => s.id)),
    [tiers],
  )

  const toggleStep = (id: string) => {
    setSelected(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id); else next.add(id)
      return next
    })
  }

  const selectScope = useCallback(
    (mode: 'all' | 'pending' | 'failed' | 'warn' | 'clear' | 'invert' | string) => {
      setSelected(prev => {
        if (mode === 'clear') return new Set()
        if (mode === 'all') return new Set(allRunnableIds)
        if (mode === 'invert') {
          const next = new Set(allRunnableIds)
          prev.forEach(id => next.delete(id))
          return next
        }
        const tierMatch = mode.match(/^tier(\w+)$/)
        if (tierMatch) {
          const tid = `tier${tierMatch[1]}`
          const ids = tiers.find(t => t.id === tid)?.steps.filter(s => !!s.script).map(s => s.id) || []
          return new Set([...prev, ...ids])
        }
        // status filter
        const wanted = mode  // 'pending' | 'failed' | 'warn'
        const statusKey = wanted === 'failed' ? 'fail' : wanted
        const ids = tiers.flatMap(t =>
          t.steps.filter(s => !!s.script && s.status === statusKey).map(s => s.id),
        )
        return new Set(ids)
      })
    },
    [tiers, allRunnableIds],
  )

  const submitBatch = async () => {
    const stepIds = Array.from(selected)
    if (stepIds.length === 0) {
      setMsg(t('methodGrounding.msgSelectAtLeastOne'))
      return
    }
    setSubmittingBatch(true)
    setMsg(null)
    try {
      const res = await fetch(`${BACKEND}/v3/frontend/dashboard/method-grounding/rerun-batch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify({ step_ids: stepIds, stop_on_fail: stopOnFail }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        setMsg(`✗ ${t('methodGrounding.msgBatchRejected')}: ${err.detail || res.statusText}`)
        return
      }
      const data = await res.json()
      const initial: RerunJob = {
        job_id: data.job_id,
        state: 'queued',
        step_ids: data.step_ids,
        current_step_id: null,
        current_index: -1,
        results: [],
        progress: { completed: 0, total: data.step_ids.length },
        host_fs_steps: data.host_fs_steps || [],
        stop_on_fail: data.stop_on_fail,
        is_active: true,
      }
      setActiveJob(initial)
      setSelected(new Set())  // clear so the user can build the next batch
      setMsg(`▶ ${t('methodGrounding.msgBatchQueuedPrefix')} ${data.job_id.slice(-6)} ${t('methodGrounding.msgBatchQueuedSuffix')} — ${data.step_ids.length} ${t('methodGrounding.msgStepsParen')}`)
    } catch (e) {
      setMsg(String(e))
    } finally {
      setSubmittingBatch(false)
    }
  }

  const openDrawer = async (id: string) => {
    setDrawer({ id, report: null, loading: true })
    try {
      const r = await fetch(`${BACKEND}/v3/frontend/dashboard/method-grounding/report/${id}`,
                            { headers: authHeaders() })
      const data = await r.json()
      setDrawer({ id, report: data.report, loading: false })
    } catch {
      setDrawer({ id, report: null, loading: false })
    }
  }

  const batchRunning = !!activeJob && (activeJob.state === 'queued' || activeJob.state === 'running')

  return (
    <div style={{ padding: '24px 32px 80px', maxWidth: 1200, fontFamily: 'Inter, system-ui, sans-serif' }}>
      <Header anchor={anchor} summary={summary} onRefresh={load} loading={loading} />

      {msg && <Toast text={msg} onClose={() => setMsg(null)} />}

      <KpiRow summary={summary} />

      <EvidencePanels evidence={evidence} />

      <AnchorPanel onPromoted={load} />

      <DesignLockPanel />

      <RerunTray
        tiers={tiers}
        selected={selected}
        hostFsSteps={hostFsSteps}
        stopOnFail={stopOnFail}
        setStopOnFail={setStopOnFail}
        onScope={selectScope}
        onLaunch={submitBatch}
        submitting={submittingBatch}
        batchRunning={batchRunning}
        activeJob={activeJob}
        tiersList={tiers}
        recentJobs={recentJobs}
      />

      <h2 style={{ fontSize: 18, fontWeight: 800, color: '#1A2332', margin: '32px 0 12px' }}>
        {t('methodGrounding.tierCardsHeading')}
      </h2>

      <div style={{ display: 'grid', gap: 16 }}>
        {tiers.map(tier => (
          <TierCard
            key={tier.id} tier={tier}
            running={running}
            selected={selected}
            onToggle={toggleStep}
            onRun={runStep}
            onOpen={openDrawer}
            hostFsSteps={hostFsSteps}
            onSelectTier={() => selectScope(tier.id)}
            batchDisabled={batchRunning}
          />
        ))}
      </div>

      {drawer && <Drawer drawer={drawer} onClose={() => setDrawer(null)} onRerun={runStep} running={running} />}
    </div>
  )
}

// ── Header & KPIs ─────────────────────────────────────────────────────────────
function Header({ anchor, summary, onRefresh, loading }:
  { anchor: Anchor; summary: Summary | null; onRefresh: () => void; loading: boolean }) {
  const t = useT()
  return (
    <div style={{ marginBottom: 16 }}>
      <Link href="/dashboard" style={{ fontSize: 13, color: '#1A5276' }}>← {t('methodGrounding.navDashboard')}</Link>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', gap: 24, flexWrap: 'wrap',
                    marginTop: 8 }}>
        <div>
          <h1 style={{ fontSize: 26, fontWeight: 800, color: '#1A2332', margin: '0 0 6px' }}>
            {t('methodGrounding.title')}
          </h1>
          <p style={{ fontSize: 13.5, color: '#5A6776', lineHeight: 1.55, maxWidth: 760, margin: 0 }}>
            {t('methodGrounding.introA')}
            {' '}<code style={{ fontSize: 12 }}>research_validation/reports/grounding/</code>{' '}
            {t('methodGrounding.introB')}
          </p>
          <div style={{ marginTop: 8, display: 'flex', gap: 14, fontSize: 12, color: '#475569', flexWrap: 'wrap' }}>
            <span><b>{t('methodGrounding.labelAnchor')}:</b> <code>{anchor.phase2_run_id || '—'}</code></span>
            <span><b>{t('methodGrounding.labelSeal')}:</b> <code>{anchor.seal_id || '—'}</code></span>
            {anchor.anchor_rows && <span><b>N:</b> {anchor.anchor_rows.toLocaleString()}</span>}
            <Link href="/review/methods" style={{ color: '#1A5276', fontWeight: 600 }}>{t('methodGrounding.linkMethodsSandbox')} →</Link>
            <Link href="/dashboard/data" style={{ color: '#1A5276', fontWeight: 600 }}>{t('methodGrounding.linkKnowYourData')} →</Link>
          </div>
        </div>
        <button onClick={onRefresh} disabled={loading}
          style={{ fontSize: 12, padding: '8px 14px', borderRadius: 6, border: '1px solid #CBD5E1',
                   background: '#fff', color: '#1A2332', cursor: 'pointer', fontWeight: 600 }}>
          {loading ? t('methodGrounding.loading') : t('methodGrounding.refresh')}
        </button>
      </div>
    </div>
  )
}

function Toast({ text, onClose }: { text: string; onClose: () => void }) {
  return (
    <div style={{ marginBottom: 16, padding: '10px 14px', background: '#EBF5FB', border: '1px solid #AED6F1',
                  borderRadius: 8, fontSize: 13, color: '#1A5276', display: 'flex', justifyContent: 'space-between' }}>
      <span>{text}</span>
      <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#1A5276', cursor: 'pointer' }}>✕</button>
    </div>
  )
}

function KpiRow({ summary }: { summary: Summary | null }) {
  const t = useT()
  if (!summary) return null
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 12, marginBottom: 24 }}>
      <Kpi label={t('methodGrounding.kpiSteps')} value={summary.total_steps} />
      <Kpi label={t('methodGrounding.kpiPass')} value={summary.passed} color="#1E8449" />
      <Kpi label={t('methodGrounding.kpiWarn')} value={summary.warn} color="#B9770E" />
      <Kpi label={t('methodGrounding.kpiPending')} value={summary.pending} color="#94A3B8" />
      <Kpi label={t('methodGrounding.kpiFail')} value={summary.failed} color="#C0392B" />
      <Kpi label={t('methodGrounding.kpiDeferred')} value={summary.deferred ?? 0} color="#5B7083" />
      <Kpi label={t('methodGrounding.kpiComplete')} value={`${summary.completion_pct}%`} />
    </div>
  )
}

function Kpi({ label, value, color }: { label: string; value: number | string; color?: string }) {
  return (
    <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 8, padding: '12px 16px' }}>
      <div style={{ fontSize: 10.5, color: '#94A3B8', textTransform: 'uppercase', fontWeight: 700, letterSpacing: '0.05em' }}>{label}</div>
      <div style={{ fontSize: 24, fontWeight: 800, color: color || '#1A2332', marginTop: 2 }}>{value}</div>
    </div>
  )
}

// ── Evidence panels ───────────────────────────────────────────────────────────
function EvidencePanels({ evidence }: { evidence: any }) {
  const t = useT()
  if (!evidence) return null
  return (
    <>
      <h2 style={{ fontSize: 18, fontWeight: 800, color: '#1A2332', margin: '8px 0 12px' }}>
        {t('methodGrounding.evidencePanelsHeading')}
      </h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: 16 }}>
        <SignalTablePanel data={evidence.signal_truth_table} />
        <SynergyHeatmapPanel data={evidence.synergy_matrix} />
        <DatasetDecisionsPanel decisions={evidence.dataset_decisions} />
        <SealLineagePanel anchor={evidence.anchor} papers={evidence.papers} baselines={evidence.matched_baselines} />
        <EnsemblePanel ensemble={evidence.ensemble_decision} enkf={evidence.enkf_trial} />
        <TopologyR12Panel topology={evidence.topology_magnitude} r12={evidence.r12_ablation} />
      </div>
    </>
  )
}

function PanelShell({ title, sub, children }: { title: string; sub?: string; children: React.ReactNode }) {
  return (
    <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10, padding: '14px 16px' }}>
      <div style={{ fontSize: 13, fontWeight: 800, color: '#1A2332', marginBottom: 2 }}>{title}</div>
      {sub && <div style={{ fontSize: 11, color: '#94A3B8', marginBottom: 10 }}>{sub}</div>}
      {children}
    </div>
  )
}

function SignalTablePanel({ data }: { data: any }) {
  const t = useT()
  const predictors: any[] = data?.predictive_validity?.predictors || []
  const selection: any[] = data?.selection_impact?.dimensions || []
  const intent: Record<string, string> = data?.intent_decisions?.signals || {}
  const intentCounts = Object.values(intent).reduce((acc: Record<string, number>, v) => {
    acc[v] = (acc[v] || 0) + 1; return acc
  }, {})
  return (
    <PanelShell title={t('methodGrounding.signalTableTitle')} sub={t('methodGrounding.signalTableSub')}>
      <table style={{ width: '100%', fontSize: 11.5, borderCollapse: 'collapse' }}>
        <thead><tr style={{ color: '#94A3B8', textTransform: 'uppercase', fontSize: 10 }}>
          <th style={{ textAlign: 'left', padding: '4px 6px' }}>{t('methodGrounding.colPredictor')}</th>
          <th style={{ textAlign: 'right', padding: '4px 6px' }}>{t('methodGrounding.colRvsNextCorrect')}</th>
          <th style={{ textAlign: 'right', padding: '4px 6px' }}>n</th>
        </tr></thead>
        <tbody>
          {predictors.slice(0, 6).map((p: any) => (
            <tr key={p.column} style={{ borderTop: '1px solid #F1F5F9' }}>
              <td style={{ padding: '4px 6px', fontFamily: 'monospace', color: '#1A2332' }}>{p.column}</td>
              <td style={{ padding: '4px 6px', textAlign: 'right', fontFamily: 'monospace',
                            color: p.corr_next_correct >= 0.30 ? '#1E8449' : '#B9770E', fontWeight: 700 }}>
                {p.corr_next_correct?.toFixed?.(4) ?? '—'}
              </td>
              <td style={{ padding: '4px 6px', textAlign: 'right', color: '#64748B' }}>
                {(p.pairs as number)?.toLocaleString?.() || '—'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <div style={{ marginTop: 10, fontSize: 11, color: '#475569' }}>
        <b>{t('methodGrounding.selectionImpact')}:</b>{' '}
        {selection.map((d: any, i: number) => (
          <span key={d.dimension} style={{ marginRight: 6 }}>
            {d.dimension}=<span style={{ color: d.selection_impact === 'dead' ? '#C0392B' : '#1E8449', fontWeight: 700 }}>
              {d.selection_impact}
            </span>{i < selection.length - 1 ? ' ·' : ''}
          </span>
        ))}
      </div>
      <div style={{ marginTop: 8, fontSize: 11, color: '#475569' }}>
        <b>{t('methodGrounding.a5IntentCounts')}:</b>{' '}
        {Object.entries(intentCounts).map(([k, v]) => (
          <span key={k} style={{ marginRight: 8 }}>{k}={v}</span>
        ))}
      </div>
    </PanelShell>
  )
}

function SynergyHeatmapPanel({ data }: { data: any }) {
  const t = useT()
  const learners: Record<string, Record<string, number>> = data?.learner_correlations || {}
  const jt: Record<string, Record<string, number>> = data?.jt_correlations || {}
  const redundant: any[] = data?.redundant_pairs || []
  const cell = (v: number | undefined) => {
    if (v == null) return { bg: '#F8FAFC', text: '—' }
    const a = Math.min(1, Math.abs(v))
    const r = v >= 0 ? Math.round(255 - a * 100) : 255
    const g = v >= 0 ? Math.round(255 - a * 60) : Math.round(255 - a * 80)
    const b = v >= 0 ? Math.round(255 - a * 60) : Math.round(255 - a * 100)
    return { bg: `rgb(${r},${g},${b})`, text: v.toFixed(2) }
  }
  const learnerNames = ['Bayesian', 'Kalman', 'BoundedStability']
  const jtNames = ['delta_m', 'T_realized', 'T_prospective', 'Challenge', 'Uncertainty', 'ZPD']
  return (
    <PanelShell title={t('methodGrounding.synergyTitle')} sub={t('methodGrounding.synergySub')}>
      <div style={{ marginBottom: 8, fontSize: 11, color: '#94A3B8' }}>{t('methodGrounding.learners')}</div>
      <table style={{ width: '100%', fontSize: 10, borderCollapse: 'collapse' }}>
        <thead><tr><th></th>{learnerNames.map(n => (
          <th key={n} style={{ padding: 3, fontSize: 10, color: '#64748B', fontWeight: 700 }}>{n.slice(0, 4)}</th>
        ))}</tr></thead>
        <tbody>{learnerNames.map(a => (
          <tr key={a}><td style={{ padding: 3, fontSize: 10, color: '#64748B', fontWeight: 700 }}>{a.slice(0, 4)}</td>
            {learnerNames.map(b => {
              const v = a === b ? 1 : (learners[a]?.[b] ?? learners[b]?.[a])
              const c = cell(v)
              return <td key={b} style={{ padding: 3, textAlign: 'center', background: c.bg, fontFamily: 'monospace', fontSize: 10 }}>{c.text}</td>
            })}
          </tr>
        ))}</tbody>
      </table>
      <div style={{ marginTop: 12, marginBottom: 8, fontSize: 11, color: '#94A3B8' }}>{t('methodGrounding.jtDimensions')}</div>
      <table style={{ width: '100%', fontSize: 10, borderCollapse: 'collapse' }}>
        <thead><tr><th></th>{jtNames.map(n => (
          <th key={n} style={{ padding: 2, fontSize: 9, color: '#64748B', fontWeight: 700 }}>{n.slice(0, 4)}</th>
        ))}</tr></thead>
        <tbody>{jtNames.map(a => (
          <tr key={a}><td style={{ padding: 2, fontSize: 9, color: '#64748B', fontWeight: 700 }}>{a.slice(0, 4)}</td>
            {jtNames.map(b => {
              const v = a === b ? 1 : (jt[a]?.[b] ?? jt[b]?.[a])
              const c = cell(v)
              return <td key={b} style={{ padding: 2, textAlign: 'center', background: c.bg, fontFamily: 'monospace', fontSize: 9 }}>{c.text}</td>
            })}
          </tr>
        ))}</tbody>
      </table>
      {redundant.length > 0 && (
        <div style={{ marginTop: 10, padding: 8, background: '#FFF3E0', borderRadius: 6, fontSize: 11, color: '#9A7D0A' }}>
          ⚠ {t('methodGrounding.redundant')}: {redundant.map((p: any) => `${p.a}↔${p.b} (r=${p.corr})`).join(' · ')}
        </div>
      )}
    </PanelShell>
  )
}

function DatasetDecisionsPanel({ decisions }: { decisions: Record<string, string> }) {
  const t = useT()
  const entries = Object.entries(decisions || {})
  return (
    <PanelShell title={t('methodGrounding.datasetDecisionsTitle')} sub={t('methodGrounding.datasetDecisionsSub')}>
      <table style={{ width: '100%', fontSize: 11.5, borderCollapse: 'collapse' }}>
        <tbody>{entries.map(([k, v]) => (
          <tr key={k} style={{ borderTop: '1px solid #F1F5F9' }}>
            <td style={{ padding: '4px 6px', fontFamily: 'monospace', color: '#1A2332' }}>{k}</td>
            <td style={{ padding: '4px 6px', textAlign: 'right' }}>
              <span style={{ fontSize: 10, fontWeight: 700, padding: '2px 8px', borderRadius: 4, color: '#fff',
                             background: v === 'EXCLUDE' ? '#C0392B' : v === 'REPROCESS' ? '#9A7D0A' : '#1A5276' }}>{v}</span>
            </td>
          </tr>
        ))}</tbody>
      </table>
      {entries.length === 0 && <div style={{ fontSize: 11, color: '#94A3B8' }}>{t('methodGrounding.noDecisionsLogged')}</div>}
    </PanelShell>
  )
}

function SealLineagePanel({ anchor, papers, baselines }: { anchor: any; papers: any; baselines: any }) {
  const t = useT()
  const remaining = papers?.markers_remaining ?? '—'
  const filesUpdated = papers?.files_updated?.length ?? 0
  const auc = baselines?.hcie_matched_overall_auc
  return (
    <PanelShell title={t('methodGrounding.sealLineageTitle')} sub={t('methodGrounding.sealLineageSub')}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, fontSize: 11.5 }}>
        <div><b>{t('methodGrounding.labelRun')}</b><div style={{ fontFamily: 'monospace', color: '#1A5276' }}>{anchor?.phase2_run_id?.slice(0, 22) || '—'}…</div></div>
        <div><b>{t('methodGrounding.labelSeal')}</b><div style={{ fontFamily: 'monospace', color: '#1A5276' }}>{anchor?.seal_id?.slice(0, 22) || '—'}…</div></div>
        <div><b>{t('methodGrounding.labelNRows')}</b><div style={{ fontFamily: 'monospace', color: '#1A2332' }}>{anchor?.anchor_rows?.toLocaleString() || '—'}</div></div>
        <div><b>{t('methodGrounding.labelHcieMatchedAuc')}</b><div style={{ fontFamily: 'monospace', color: '#1A2332' }}>{auc?.toFixed?.(3) ?? '—'}</div></div>
        <div><b>⚠ {t('methodGrounding.labelMarkersRemaining')}</b><div style={{ color: remaining === 0 ? '#1E8449' : '#B9770E', fontWeight: 700 }}>{remaining}</div></div>
        <div><b>{t('methodGrounding.labelFilesAnchored')}</b><div style={{ color: '#1A2332', fontWeight: 700 }}>{filesUpdated}</div></div>
      </div>
      {anchor?.lineage && (
        <div style={{ marginTop: 8, fontSize: 11, color: '#475569', lineHeight: 1.5 }}>{anchor.lineage}</div>
      )}
    </PanelShell>
  )
}

function EnsemblePanel({ ensemble, enkf }: { ensemble: any; enkf: any }) {
  const t = useT()
  const c = enkf?.corr_next_correct || {}
  return (
    <PanelShell title={t('methodGrounding.ensembleTitle')} sub={t('methodGrounding.ensembleSub')}>
      <div style={{ fontSize: 12, color: '#1A2332', marginBottom: 8 }}>
        <b>{t('methodGrounding.decision')}:</b> {ensemble?.decision || '—'}
      </div>
      <table style={{ width: '100%', fontSize: 11.5, borderCollapse: 'collapse' }}>
        <tbody>
          {(['kalman_alone', 'weighted_sum', 'enkf_inverse_variance'] as const).map(k => (
            <tr key={k} style={{ borderTop: '1px solid #F1F5F9' }}>
              <td style={{ padding: '4px 6px', fontFamily: 'monospace' }}>{k}</td>
              <td style={{ padding: '4px 6px', textAlign: 'right', fontFamily: 'monospace',
                           fontWeight: 700, color: enkf?.winner === k.split('_')[0] ? '#1E8449' : '#1A2332' }}>
                {(c as any)[k]?.toFixed?.(4) ?? '—'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <div style={{ marginTop: 8, fontSize: 11, color: '#475569', lineHeight: 1.5 }}>
        {t('methodGrounding.winner')}: <b style={{ color: '#1A5276' }}>{enkf?.winner || '—'}</b>. {ensemble?.locked_runtime}
      </div>
    </PanelShell>
  )
}

function TopologyR12Panel({ topology, r12 }: { topology: any; r12: any }) {
  const t = useT()
  const r12s = r12?.r12_summary || {}
  const auc_on = r12s?.graph_on_auc?.overall
  const auc_off = r12s?.graph_off_auc?.overall
  const delta = (auc_on != null && auc_off != null) ? (auc_on - auc_off) : null
  return (
    <PanelShell title={t('methodGrounding.topologyR12Title')} sub={t('methodGrounding.topologyR12Sub')}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, fontSize: 11.5 }}>
        <div>
          <div style={{ fontSize: 10.5, color: '#94A3B8', fontWeight: 700, textTransform: 'uppercase' }}>{t('methodGrounding.causalMagnitude')}</div>
          <div style={{ fontSize: 18, fontWeight: 800, color: '#1A2332', fontFamily: 'monospace' }}>
            {topology?.causal_magnitude?.toFixed?.(4) ?? '—'}
          </div>
          <div style={{ fontSize: 10, color: '#94A3B8' }}>{t('methodGrounding.expectedApprox')} {topology?.expected ?? '0.053'}</div>
        </div>
        <div>
          <div style={{ fontSize: 10.5, color: '#94A3B8', fontWeight: 700, textTransform: 'uppercase' }}>R12 ΔAUC</div>
          <div style={{ fontSize: 18, fontWeight: 800, color: '#1A2332', fontFamily: 'monospace' }}>
            {delta != null ? `${delta >= 0 ? '+' : ''}${delta.toFixed(4)}` : '—'}
          </div>
          <div style={{ fontSize: 10, color: '#94A3B8' }}>{t('methodGrounding.graphOn')} {auc_on?.toFixed?.(3) ?? '—'} {t('methodGrounding.vsOff')} {auc_off?.toFixed?.(3) ?? '—'}</div>
        </div>
      </div>
    </PanelShell>
  )
}

// ── Anchor ledger panel ───────────────────────────────────────────────────────
// Shows the active phase2_run_id + seal_id used by every cascade step, plus
// any candidate continuation runs from tier2_5-continuation-run. Promoting a
// candidate moves it into `active` and pushes the previous active onto
// history. After a promote the page reloads so reports read against the new
// anchor.
// ── Run capability fingerprint ────────────────────────────────────────────────
// For any run, surfaces (from experiment_trajectories) which ensemble it actually
// used — flagging the LEGACY 3-learner ensemble incl. BoundedStability (ex-Lyapunov,
// ~0.92 corr with Bayesian) — and whether every step carries a determinism hash, i.e.
// whether the run is replay-verifiable. Answers "is my thesis data still on the old
// ensemble?" directly on each anchor row.
type Fingerprint = {
  status: string
  run_id?: string
  requested?: string
  n_rows?: number
  ensemble?: {
    members: string[]
    mean_learners?: string[]
    learner_count: number
    uses_ex_lyapunov: boolean
    ex_lyapunov_weight_coverage: number
    canonical_disclosed: string
    canonical_label?: string
    sigma2_source?: string
    weight_method?: string
    note: string
  }
  determinism?: {
    deterministic_inputs_hash_coverage: number
    replay_verifiable: boolean
    note: string
  }
  provenance?: {
    n_users: number
    synthetic_pct: number
    traffic_types: string
    source_family: string
    kind: string
    sealed: boolean
    seal_id?: string | null
    sealed_at?: string | null
    parent_run_id?: string | null
    is_thesis_figure_anchor: boolean
  }
}

function fpChip(bg: string, fg: string): React.CSSProperties {
  return { fontSize: 10, fontWeight: 700, padding: '2px 7px', borderRadius: 10, background: bg, color: fg, whiteSpace: 'nowrap' }
}

function RunFingerprint({ runId }: { runId?: string }) {
  const t = useT()
  const [fp, setFp] = useState<Fingerprint | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!runId) return
    let cancelled = false
    setLoading(true)
    fetch(`${BACKEND}/v3/frontend/dashboard/run-fingerprint/${encodeURIComponent(runId)}`,
          { headers: authHeaders() })
      .then(r => r.json())
      .then(j => { if (!cancelled) setFp(j) })
      .catch(() => { if (!cancelled) setFp({ status: 'error' }) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [runId])

  if (!runId) return null
  if (loading && !fp) return <span style={{ fontSize: 10, color: '#94A3B8', fontStyle: 'italic' }}>{t('methodGrounding.fingerprintLoading')}</span>
  if (!fp || fp.status !== 'ok' || !fp.ensemble) {
    return <span style={{ fontSize: 10, color: '#94A3B8', fontStyle: 'italic' }}>{t('methodGrounding.noFingerprint')}</span>
  }
  const ens = fp.ensemble
  const det = fp.determinism
  const prov = fp.provenance
  const exLyap = ens.uses_ex_lyapunov
  const detPct = Math.round((det?.deterministic_inputs_hash_coverage || 0) * 100)
  return (
    <span style={{ display: 'flex', flexDirection: 'column', gap: 4, marginTop: 6 }}>
      {prov && (
        <span style={{ display: 'inline-flex', gap: 7, flexWrap: 'wrap', alignItems: 'center', fontSize: 10.5, color: '#475569' }}>
          <span style={{ fontWeight: 700, color: '#1A2332' }} title={t('methodGrounding.fpKindTitle')}>{prov.kind}</span>
          <span>· {prov.source_family}</span>
          {prov.n_users > 0 && <span>· {prov.n_users.toLocaleString()} {t('methodGrounding.learners')}</span>}
          {prov.synthetic_pct > 0 && <span style={{ color: '#92400E', fontWeight: 600 }}>· {prov.synthetic_pct}% synthetic</span>}
          <span title={prov.sealed ? `seal: ${prov.seal_id || ''} (${prov.sealed_at || ''})` : t('methodGrounding.fpNoSealTitle')}
                style={fpChip(prov.sealed ? '#DBEAFE' : '#FEF3C7', prov.sealed ? '#1E3A8A' : '#92400E')}>
            {prov.sealed ? t('methodGrounding.fpSealed') : t('methodGrounding.fpUnsealed')}
          </span>
          {prov.is_thesis_figure_anchor && (
            <span title={t('methodGrounding.fpThesisFiguresTitle')} style={fpChip('#EDE9FE', '#5B21B6')}>{t('methodGrounding.fpThesisFigures')}</span>
          )}
        </span>
      )}
      <span style={{ display: 'inline-flex', gap: 6, flexWrap: 'wrap', alignItems: 'center' }}>
        <span title={ens.note} style={fpChip(exLyap ? '#FEF3C7' : '#D1FAE5', exLyap ? '#92400E' : '#065F46')}>
          {exLyap ? '⚠ ' : '✓ '}{ens.canonical_label || (exLyap ? t('methodGrounding.fpExLyapunov') : t('methodGrounding.fpClean'))}
        </span>
        <span title={`${t('methodGrounding.fpMeanLearnersTitle')}: ${(ens.mean_learners || ens.members).join(' + ')} · canonical≈${ens.canonical_disclosed}`}
              style={fpChip('#F1F5F9', '#475569')}>
          {t('methodGrounding.fpMean')}: {(ens.mean_learners || ens.members).join(' + ')}
        </span>
        {ens.sigma2_source && (
          <span title={t('methodGrounding.fpSigma2Title')} style={fpChip('#F1F5F9', '#475569')}>
            σ²: {ens.sigma2_source}
          </span>
        )}
        {det && (
          <span title={det.note}
                style={fpChip(det.replay_verifiable ? '#D1FAE5' : '#FEF3C7', det.replay_verifiable ? '#065F46' : '#92400E')}>
            {t('methodGrounding.fpReplay')} {det.replay_verifiable ? '✓' : '~'} {detPct}%
          </span>
        )}
        {fp.n_rows != null && (
          <span style={{ fontSize: 10, color: '#94A3B8' }}>n={fp.n_rows.toLocaleString()}</span>
        )}
      </span>
    </span>
  )
}

function AnchorPanel({ onPromoted }: { onPromoted: () => void | Promise<void> }) {
  const t = useT()
  const [data, setData] = useState<AnchorLedger | null>(null)
  const [loading, setLoading] = useState(true)
  const [busyRunId, setBusyRunId] = useState<string | null>(null)
  const [msg, setMsg] = useState<string | null>(null)
  const [showHistory, setShowHistory] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const r = await fetch(`${BACKEND}/v3/frontend/dashboard/method-grounding/anchor`,
                            { headers: authHeaders() })
      const j: AnchorLedger = await r.json()
      setData(j)
    } catch (e) {
      setMsg(`${t('methodGrounding.msgFailedLoadAnchor')}: ${e}`)
    } finally {
      setLoading(false)
    }
  }, [t])

  useEffect(() => { load() }, [load])

  const promote = async (cand: AnchorEntry) => {
    if (!cand.phase2_run_id) return
    const ok = window.confirm(
      `${t('methodGrounding.confirmPromote')}\n\n` +
      `${cand.label || cand.phase2_run_id}\n\n` +
      t('methodGrounding.confirmPromoteBody')
    )
    if (!ok) return
    setBusyRunId(cand.phase2_run_id)
    setMsg(null)
    try {
      const r = await fetch(`${BACKEND}/v3/frontend/dashboard/method-grounding/anchor/promote`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify({ phase2_run_id: cand.phase2_run_id, label: cand.label }),
      })
      if (!r.ok) {
        const err = await r.json().catch(() => ({}))
        setMsg(`${t('methodGrounding.msgPromoteRejected')}: ${err.detail || r.statusText}`)
        return
      }
      const j = await r.json()
      setMsg(`✓ ${t('methodGrounding.msgPromoted')} ${j.active?.phase2_run_id || cand.phase2_run_id} — ${j.next || ''}`)
      await load()
      await onPromoted()
    } catch (e) {
      setMsg(`${t('methodGrounding.msgPromoteFailed')}: ${e}`)
    } finally {
      setBusyRunId(null)
    }
  }

  const active = data?.active || {}
  const candidates = data?.candidates || []
  const history = data?.history || []

  return (
    <div style={{
      marginTop: 16,
      padding: '16px 18px',
      borderRadius: 12,
      background: '#FFFFFF',
      border: '1px solid #E2E8F0',
      boxShadow: '0 1px 2px rgba(15,23,42,0.04)',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <div style={{ fontSize: 16, fontWeight: 800, color: '#1A2332' }}>
            {t('methodGrounding.cascadeAnchorTitle')}
          </div>
          <div style={{ fontSize: 12, color: '#64748B', marginTop: 2 }}>
            {t('methodGrounding.cascadeAnchorDesc')}
          </div>
          <div style={{ fontSize: 11, color: '#94A3B8', marginTop: 4 }}>
            {t('methodGrounding.cascadeAnchorFpA')} <b>{t('methodGrounding.cascadeAnchorFpBold')}</b>{t('methodGrounding.cascadeAnchorFpB')}
            (<span style={{ color: '#92400E' }}>⚠ 3-learner · ex-Lyapunov</span> = {t('methodGrounding.cascadeAnchorFpC')}
            <span style={{ color: '#065F46' }}> ✓ 2-learner</span> = {t('methodGrounding.cascadeAnchorFpD')}
          </div>
        </div>
        <button
          onClick={load}
          disabled={loading}
          style={{
            padding: '6px 12px', borderRadius: 6, border: '1px solid #CBD5E1',
            background: '#F8FAFC', color: '#1A2332', cursor: loading ? 'wait' : 'pointer',
            fontSize: 12, fontWeight: 600,
          }}
        >{loading ? t('methodGrounding.loading') : t('methodGrounding.refresh')}</button>
      </div>

      {msg && (
        <div style={{
          marginTop: 10, padding: '8px 12px', borderRadius: 8,
          background: msg.startsWith('✓') ? '#ECFDF5' : '#FEF2F2',
          border: `1px solid ${msg.startsWith('✓') ? '#A7F3D0' : '#FECACA'}`,
          color: msg.startsWith('✓') ? '#065F46' : '#7F1D1D',
          fontSize: 12,
        }}>{msg}</div>
      )}

      {/* Active anchor row */}
      <div style={{
        marginTop: 14,
        padding: '12px 14px',
        borderRadius: 8,
        background: active.v2_active ? '#ECFDF5' : '#F8FAFC',
        border: `1px solid ${active.v2_active ? '#A7F3D0' : '#E2E8F0'}`,
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12, flexWrap: 'wrap' }}>
          <div style={{ flex: '1 1 320px', minWidth: 0 }}>
            <div style={{ fontSize: 11, color: '#64748B', textTransform: 'uppercase', letterSpacing: 0.5 }}>{t('methodGrounding.activeAnchor')}</div>
            <div style={{ fontSize: 14, fontWeight: 700, color: '#1A2332', marginTop: 2 }}>
              {active.label || '—'}
            </div>
            <div style={{ display: 'flex', gap: 16, fontSize: 12, color: '#475569', marginTop: 6, flexWrap: 'wrap' }}>
              <code style={{ fontSize: 11, background: '#F1F5F9', padding: '2px 6px', borderRadius: 4 }}>
                {active.phase2_run_id || '—'}
              </code>
              <code style={{ fontSize: 11, background: '#F1F5F9', padding: '2px 6px', borderRadius: 4 }}>
                {active.seal_id || '—'}
              </code>
            </div>
            <RunFingerprint runId={active.phase2_run_id} />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 4 }}>
            <span style={{
              padding: '2px 8px', borderRadius: 12, fontSize: 10, fontWeight: 700,
              background: '#10B981', color: '#fff',
            }}>{t('methodGrounding.badgeActive')}</span>
            <span style={{ fontSize: 10, color: '#64748B' }}>
              {t('methodGrounding.promotedLabel')} {active.promoted_at?.slice(0, 19) || '—'}
            </span>
          </div>
        </div>
      </div>

      {/* Candidates */}
      <div style={{ marginTop: 14 }}>
        <div style={{ fontSize: 12, fontWeight: 700, color: '#1A2332', marginBottom: 6 }}>
          {t('methodGrounding.continuationCandidates')} ({candidates.length})
        </div>
        {candidates.length === 0 ? (
          <div style={{
            padding: '10px 12px', borderRadius: 8, fontSize: 12, color: '#64748B',
            background: '#F8FAFC', border: '1px dashed #CBD5E1',
          }}>
            {t('methodGrounding.noCandidatesA')} <code>tier2_5-continuation-run</code> {t('methodGrounding.noCandidatesB')}
          </div>
        ) : (
          <div style={{ display: 'grid', gap: 8 }}>
            {candidates.map(c => {
              const summary = c.summary || {}
              const busy = busyRunId === c.phase2_run_id
              return (
                <div key={c.phase2_run_id} style={{
                  padding: '10px 12px', borderRadius: 8,
                  background: '#FFFFFF', border: '1px solid #E2E8F0',
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  gap: 12, flexWrap: 'wrap',
                }}>
                  <div style={{ flex: '1 1 360px', minWidth: 0 }}>
                    <div style={{ fontSize: 13, fontWeight: 600, color: '#1A2332' }}>
                      {c.label || c.phase2_run_id}
                    </div>
                    <div style={{ fontSize: 11, color: '#64748B', marginTop: 4, display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                      <code style={{ fontSize: 10, background: '#F1F5F9', padding: '1px 5px', borderRadius: 3 }}>
                        {c.phase2_run_id}
                      </code>
                      {summary.rows != null && <span>{t('methodGrounding.rowsLabel')}: <b>{summary.rows.toLocaleString()}</b></span>}
                      {summary.population_prior_nonzero_pct != null &&
                        <span>PopulationPrior {t('methodGrounding.nonzero')}: <b>{summary.population_prior_nonzero_pct}%</b></span>}
                      {summary.challenge_event_nonzero_pct != null &&
                        <span>Challenge_event {t('methodGrounding.nonzero')}: <b>{summary.challenge_event_nonzero_pct}%</b></span>}
                      {c.created_at && <span>{t('methodGrounding.createdLabel')} {c.created_at.slice(0, 19)}</span>}
                    </div>
                    <RunFingerprint runId={c.phase2_run_id} />
                  </div>
                  <button
                    onClick={() => promote(c)}
                    disabled={busy || !c.phase2_run_id}
                    style={{
                      padding: '8px 14px', borderRadius: 6, border: 'none',
                      background: busy ? '#94A3B8' : '#1A5276', color: '#fff',
                      cursor: busy ? 'wait' : 'pointer', fontSize: 12, fontWeight: 700,
                    }}
                  >{busy ? t('methodGrounding.promoting') : t('methodGrounding.promoteToActive')}</button>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* History (collapsed) */}
      {history.length > 0 && (
        <div style={{ marginTop: 14 }}>
          <button
            onClick={() => setShowHistory(s => !s)}
            style={{
              padding: '4px 10px', borderRadius: 6, border: '1px solid #E2E8F0',
              background: '#F8FAFC', color: '#475569', cursor: 'pointer',
              fontSize: 11, fontWeight: 600,
            }}
          >
            {showHistory ? t('methodGrounding.hide') : t('methodGrounding.show')} {t('methodGrounding.history')} ({history.length})
          </button>
          {showHistory && (
            <div style={{ marginTop: 8, display: 'grid', gap: 6 }}>
              {history.slice().reverse().map((h, i) => (
                <div key={i} style={{
                  padding: '8px 12px', borderRadius: 6, fontSize: 11,
                  background: '#F8FAFC', border: '1px solid #E2E8F0', color: '#475569',
                  display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap',
                }}>
                  <span>{h.label || h.phase2_run_id}</span>
                  <code style={{ fontSize: 10 }}>{h.phase2_run_id}</code>
                  <span>{t('methodGrounding.demotedLabel')} {h.demoted_at?.slice(0, 19) || '—'}</span>
                  <div style={{ flexBasis: '100%' }}><RunFingerprint runId={h.phase2_run_id} /></div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ── Design lock panel ─────────────────────────────────────────────────────────
// At-a-glance evidence surface for tier2_5-jt-design-lock: the 21 closure packets
// (decision · live evidence gate · closure status · literature validation) plus the
// user-locked resolutions. Fetches the step report directly — /report/{id} already
// serves the full hash-pinned payload, so no backend change is needed.
const GATE_TONE: Record<string, { bg: string; fg: string }> = {
  PASS:       { bg: '#D1FAE5', fg: '#065F46' },
  WARN:       { bg: '#FEF3C7', fg: '#92400E' },
  FAIL:       { bg: '#FEE2E2', fg: '#B91C1C' },
  UNMEASURED: { bg: '#E2E8F0', fg: '#475569' },
}
const PSTATUS_TONE: Record<string, { bg: string; fg: string; labelKey: string }> = {
  CLOSED:           { bg: '#1E8449', fg: '#fff', labelKey: 'pstatusClosed' },
  CLOSED_DISCLOSED: { bg: '#1A5276', fg: '#fff', labelKey: 'pstatusClosedDisc' },
  OPEN:             { bg: '#C0392B', fg: '#fff', labelKey: 'pstatusOpen' },
}
const GROUP_LABEL_KEYS: Record<string, string> = {
  A1_jt_dimensions: 'groupA1',
  A2_machinery: 'groupA2',
  A3_ensemble: 'groupA3',
  A4_bandit_misc: 'groupA4',
  A5_cross_cutting: 'groupA5',
}

function DesignLockPanel() {
  const t = useT()
  const [rep, setRep] = useState<any | null>(null)
  const [loading, setLoading] = useState(true)
  const [open, setOpen] = useState<string | null>(null)

  useEffect(() => {
    let alive = true
    ;(async () => {
      try {
        const r = await fetch(`${BACKEND}/v3/frontend/dashboard/method-grounding/report/tier2_5-jt-design-lock`,
                              { headers: authHeaders() })
        const data = await r.json()
        if (alive) setRep(data.report || data)
      } catch { /* swallow */ } finally { if (alive) setLoading(false) }
    })()
    return () => { alive = false }
  }, [])

  if (loading) {
    return (
      <div style={{ marginTop: 16, padding: '16px 18px', borderRadius: 12, background: '#fff',
                    border: '1px solid #E2E8F0', fontSize: 12, color: '#94A3B8' }}>
        {t('methodGrounding.loadingDesignLock')}
      </div>
    )
  }
  if (!rep || !Array.isArray(rep.packets) || rep.packets.length === 0) return null

  const packets: any[] = rep.packets
  const breakdown: Record<string, number> = rep.status_breakdown || {}
  const lit: any = rep.literature_validation || {}
  const resolutions: any[] = rep.resolutions || []
  const openDecisions: any[] = rep.open_decisions || []
  const overallPass = rep.status === 'pass'
  const groupOrder = ['A1_jt_dimensions', 'A2_machinery', 'A3_ensemble', 'A4_bandit_misc', 'A5_cross_cutting']

  return (
    <div style={{ marginTop: 16, padding: '16px 18px', borderRadius: 12, background: '#fff',
                  border: '1px solid #E2E8F0', boxShadow: '0 1px 2px rgba(15,23,42,0.04)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12, flexWrap: 'wrap' }}>
        <div>
          <div style={{ fontSize: 16, fontWeight: 800, color: '#1A2332' }}>
            {t('methodGrounding.designLockTitle')}
          </div>
          <div style={{ fontSize: 12, color: '#64748B', marginTop: 2, maxWidth: 720, lineHeight: 1.5 }}>
            {rep.packet_count} {t('methodGrounding.designLockDesc')}
          </div>
        </div>
        <span style={{ padding: '3px 10px', borderRadius: 12, fontSize: 11, fontWeight: 800,
                       background: overallPass ? '#10B981' : '#B9770E', color: '#fff' }}>
          {overallPass ? t('methodGrounding.lockedPass') : t('methodGrounding.openWarn')}
        </span>
      </div>

      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 12 }}>
        {Object.entries(breakdown).map(([k, v]) => {
          const tone = PSTATUS_TONE[k]
          const bg = tone?.bg ?? '#E2E8F0'
          const fg = tone?.fg ?? '#475569'
          const label = tone ? t('methodGrounding.' + tone.labelKey) : k
          return (
            <span key={k} style={{ fontSize: 11, fontWeight: 700, padding: '3px 9px', borderRadius: 6,
                                   background: bg, color: fg }}>{label}: {v}</span>
          )
        })}
        <span style={{ fontSize: 11, fontWeight: 700, padding: '3px 9px', borderRadius: 6, background: '#EEF2FF', color: '#3730A3' }}>
          {t('methodGrounding.resolvedLabel')}: {rep.resolved_count ?? resolutions.length}
        </span>
        <span style={{ fontSize: 11, fontWeight: 700, padding: '3px 9px', borderRadius: 6, background: '#ECFEFF', color: '#155E75' }}>
          {t('methodGrounding.litCheck')} {lit.artifact_validated_count ?? '—'} · {t('methodGrounding.handCited')} {(lit.hand_cited_pending_artifact || []).length}
        </span>
      </div>

      <div style={{ marginTop: 12, padding: '10px 12px', borderRadius: 8, background: '#F8FAFC', border: '1px solid #E2E8F0' }}>
        <div style={{ fontSize: 11, fontWeight: 800, color: '#1A2332', textTransform: 'uppercase', letterSpacing: 0.4 }}>
          {t('methodGrounding.literatureValidation')}
        </div>
        <div style={{ fontSize: 11.5, color: '#475569', marginTop: 4, lineHeight: 1.5 }}>
          <b>{lit.artifact_validated_count ?? 0}</b> {t('methodGrounding.litValidatedA')} <code>tier2_literature_packets.json</code>.
          {(lit.hand_cited_pending_artifact || []).length > 0 && (
            <> <b style={{ color: '#B9770E' }}>{(lit.hand_cited_pending_artifact || []).join(', ')}</b> {t('methodGrounding.litHandCitedA')} <code>tier2-lit-v2</code>).</>
          )}
        </div>
      </div>

      {resolutions.length > 0 && (
        <div style={{ marginTop: 12 }}>
          <div style={{ fontSize: 11, fontWeight: 800, color: '#1A2332', textTransform: 'uppercase', letterSpacing: 0.4, marginBottom: 6 }}>
            {t('methodGrounding.lockedDecisions')} ({resolutions.length})
          </div>
          <div style={{ display: 'grid', gap: 6 }}>
            {resolutions.map((r: any) => (
              <div key={r.id} style={{ padding: '8px 10px', borderRadius: 6, background: '#F8FAFC', border: '1px solid #E2E8F0' }}>
                <div style={{ fontSize: 12 }}>
                  <code style={{ color: '#1A5276', fontWeight: 700 }}>{r.id}</code>
                  <span style={{ marginLeft: 8, fontSize: 10.5, fontWeight: 800, padding: '1px 7px', borderRadius: 4, background: '#1A5276', color: '#fff' }}>
                    {r.decision}
                  </span>
                </div>
                {r.resolution?.rationale && (
                  <div style={{ fontSize: 11, color: '#64748B', marginTop: 3, lineHeight: 1.45 }}>{r.resolution.rationale}</div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {openDecisions.length > 0 && (
        <div style={{ marginTop: 12, padding: '10px 12px', borderRadius: 8, background: '#FFFBEB', border: '1px solid #FDE68A' }}>
          <div style={{ fontSize: 11, fontWeight: 800, color: '#92400E' }}>⚠ {openDecisions.length} {t('methodGrounding.openDecisions')}</div>
          {openDecisions.map((d: any) => (
            <div key={d.id} style={{ fontSize: 11.5, color: '#78350F', marginTop: 4 }}>
              <code>{d.id}</code> — {d.recommended || ''}
            </div>
          ))}
        </div>
      )}

      <div style={{ marginTop: 14 }}>
        {groupOrder.filter(g => packets.some(p => p.group === g)).map(g => (
          <div key={g} style={{ marginBottom: 10 }}>
            <div style={{ fontSize: 11, fontWeight: 800, color: '#475569', margin: '6px 0 4px' }}>
              {GROUP_LABEL_KEYS[g] ? t('methodGrounding.' + GROUP_LABEL_KEYS[g]) : g}
            </div>
            <div style={{ display: 'grid', gap: 3 }}>
              {packets.filter(p => p.group === g).map(p => {
                const gt = GATE_TONE[p.evidence_gate?.status] || GATE_TONE.UNMEASURED
                const stTone = PSTATUS_TONE[p.status]
                const st = stTone
                  ? { bg: stTone.bg, fg: stTone.fg, label: t('methodGrounding.' + stTone.labelKey) }
                  : { bg: '#E2E8F0', fg: '#475569', label: p.status }
                const isOpen = open === p.id
                return (
                  <div key={p.id} style={{ border: '1px solid #F1F5F9', borderRadius: 6, overflow: 'hidden' }}>
                    <div onClick={() => setOpen(isOpen ? null : p.id)}
                         style={{ display: 'grid', gridTemplateColumns: '1.4fr 1.2fr 70px 100px 28px', gap: 8,
                                  alignItems: 'center', padding: '6px 10px', cursor: 'pointer',
                                  background: isOpen ? '#F8FAFC' : '#fff', fontSize: 11.5 }}>
                      <code style={{ color: '#1A2332', fontWeight: 600 }}>{p.id}</code>
                      <span style={{ fontSize: 10.5, fontWeight: 700, color: '#1A5276' }}>{p.decision}</span>
                      <span style={{ fontSize: 9.5, fontWeight: 800, textAlign: 'center', padding: '2px 4px',
                                     borderRadius: 4, background: gt.bg, color: gt.fg }}>{p.evidence_gate?.status}</span>
                      <span style={{ fontSize: 9.5, fontWeight: 800, textAlign: 'center', padding: '2px 4px',
                                     borderRadius: 4, background: st.bg, color: st.fg }}>{st.label}</span>
                      <span style={{ textAlign: 'center', fontSize: 12,
                                     color: p.literature?.validated_by_artifact ? '#1E8449' : '#B9770E' }}>
                        {p.literature?.validated_by_artifact ? '✓' : '○'}
                      </span>
                    </div>
                    {isOpen && (
                      <div style={{ padding: '8px 12px', background: '#F8FAFC', borderTop: '1px solid #F1F5F9',
                                    fontSize: 11, color: '#475569', lineHeight: 1.5 }}>
                        <div><b>{t('methodGrounding.detailMath')}:</b> {p.math?.formula}</div>
                        {p.math?.code_ref?.source && <div><b>{t('methodGrounding.detailCodeRef')}:</b> <code>{p.math.code_ref.source}</code></div>}
                        <div style={{ marginTop: 3 }}><b>{t('methodGrounding.detailLiterature')}:</b> {p.literature?.artifact_citation || p.literature?.citation}{' '}
                          <span style={{ color: p.literature?.validated_by_artifact ? '#1E8449' : '#B9770E' }}>
                            ({p.literature?.artifact_source})
                          </span>
                        </div>
                        <div style={{ marginTop: 3 }}><b>{t('methodGrounding.detailGate')}:</b> {p.evidence_gate?.report} — {p.evidence_gate?.threshold}</div>
                        <div style={{ marginTop: 3 }}><b>{t('methodGrounding.detailObserved')}:</b>{' '}
                          <code style={{ fontSize: 10 }}>{JSON.stringify(p.evidence_gate?.observed)}</code></div>
                        {Array.isArray(p.infra_delta) && p.infra_delta.length > 0 &&
                          <div style={{ marginTop: 3 }}><b>{t('methodGrounding.detailInfraDelta')}:</b> {p.infra_delta.join(' · ')}</div>}
                        {p.resolution?.rationale &&
                          <div style={{ marginTop: 3, color: '#1A5276' }}><b>{t('methodGrounding.detailResolution')}:</b> {p.resolution.rationale}</div>}
                        {p.note && <div style={{ marginTop: 3, color: '#92400E' }}>⚠ {p.note}</div>}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        ))}
      </div>

      <div style={{ marginTop: 8, fontSize: 10.5, color: '#94A3B8' }}>
        {t('methodGrounding.anchorLower')} <code>{rep.anchor?.phase2_run_id?.slice(0, 18)}…</code> · {t('methodGrounding.designLockFooter')}
      </div>
    </div>
  )
}

// ── Re-run cascade tray ───────────────────────────────────────────────────────
function RerunTray({
  tiers, selected, hostFsSteps, stopOnFail, setStopOnFail, onScope, onLaunch,
  submitting, batchRunning, activeJob, tiersList, recentJobs,
}: {
  tiers: Tier[]
  selected: Set<string>
  hostFsSteps: string[]
  stopOnFail: boolean
  setStopOnFail: (v: boolean) => void
  onScope: (mode: string) => void
  onLaunch: () => void
  submitting: boolean
  batchRunning: boolean
  activeJob: RerunJob | null
  tiersList: Tier[]
  recentJobs: RerunListEntry[]
}) {
  const t = useT()
  const totalRunnable = useMemo(
    () => tiers.flatMap(t => t.steps.filter(s => !!s.script)).length,
    [tiers],
  )
  const selectedHostFs = Array.from(selected).filter(id => hostFsSteps.includes(id))
  return (
    <div style={{
      marginTop: 24, marginBottom: 4, padding: '14px 16px',
      background: 'linear-gradient(180deg, #F0F9FF 0%, #fff 100%)',
      border: '1px solid #BFDBFE', borderRadius: 10,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 16, flexWrap: 'wrap' }}>
        <div>
          <div style={{ fontSize: 14, fontWeight: 800, color: '#1A2332' }}>
            {t('methodGrounding.rerunCascadeTitle')}
          </div>
          <div style={{ fontSize: 11.5, color: '#475569', marginTop: 4, lineHeight: 1.55, maxWidth: 720 }}>
            {t('methodGrounding.rerunCascadeDescA')}{' '}
            <code style={{ fontSize: 11 }}>research_validation/reports/grounding/</code>{t('methodGrounding.rerunCascadeDescB')}
          </div>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 6, minWidth: 220 }}>
          <div style={{ fontSize: 11, color: '#64748B' }}>
            <b style={{ color: '#1A5276' }}>{selected.size}</b> / {totalRunnable} {t('methodGrounding.runnableSelected')}
          </div>
          <label style={{ fontSize: 11, color: '#475569', display: 'flex', alignItems: 'center', gap: 6 }}>
            <input
              type="checkbox"
              checked={stopOnFail}
              onChange={e => setStopOnFail(e.target.checked)}
              disabled={batchRunning}
            />
            {t('methodGrounding.stopOnFirstFailure')}
          </label>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 12 }}>
        <ScopeBtn label={t('methodGrounding.scopeAllRunnable')} onClick={() => onScope('all')} disabled={batchRunning} />
        {tiersList.map(ti => (
          <ScopeBtn key={ti.id} label={ti.title.split(' ').slice(0, 2).join(' ')} onClick={() => onScope(ti.id)} disabled={batchRunning} />
        ))}
        <ScopeBtn label={t('methodGrounding.scopePendingOnly')} tone="warn" onClick={() => onScope('pending')} disabled={batchRunning} />
        <ScopeBtn label={t('methodGrounding.scopeFailedOnly')} tone="danger" onClick={() => onScope('failed')} disabled={batchRunning} />
        <ScopeBtn label={t('methodGrounding.scopeWarnOnly')} tone="warn" onClick={() => onScope('warn')} disabled={batchRunning} />
        <ScopeBtn label={t('methodGrounding.scopeInvert')} onClick={() => onScope('invert')} disabled={batchRunning} />
        <ScopeBtn label={t('methodGrounding.scopeClear')} onClick={() => onScope('clear')} disabled={batchRunning} />
      </div>

      {selectedHostFs.length > 0 && !batchRunning && (
        <div style={{
          marginTop: 12, padding: '8px 12px', fontSize: 11.5, lineHeight: 1.5,
          background: '#FEF9E7', border: '1px solid #FDE68A', borderRadius: 6, color: '#9A7D0A',
        }}>
          ⚠ {selectedHostFs.length} {selectedHostFs.length === 1 ? t('methodGrounding.hostFsStepSingular') : t('methodGrounding.hostFsStepPlural')} {t('methodGrounding.hostFsWarnA')}
          (<code style={{ fontFamily: 'monospace' }}>{selectedHostFs.join(', ')}</code>). {t('methodGrounding.hostFsWarnB')} <code>python research_validation/grounding/scripts/tier0j_dataset_reingest.py</code>.
        </div>
      )}

      <div style={{ marginTop: 14, display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
        <button
          onClick={onLaunch}
          disabled={submitting || batchRunning || selected.size === 0}
          style={{
            fontSize: 13, padding: '8px 18px', borderRadius: 6, border: '1px solid #1A5276',
            background: submitting || batchRunning || selected.size === 0 ? '#94A3B8' : '#1A5276',
            color: '#fff', cursor: submitting || batchRunning || selected.size === 0 ? 'not-allowed' : 'pointer',
            fontWeight: 800,
          }}
        >
          {batchRunning
            ? t('methodGrounding.batchRunning')
            : submitting
            ? t('methodGrounding.queueing')
            : `▶ ${t('methodGrounding.rerunVerb')} ${selected.size || ''} ${selected.size === 1 ? t('methodGrounding.stepSingular') : t('methodGrounding.stepPlural')}`}
        </button>
      </div>

      {activeJob && (
        <ActiveJobPanel job={activeJob} tiers={tiers} />
      )}

      {recentJobs.length > 0 && (
        <details style={{ marginTop: 14 }}>
          <summary style={{ fontSize: 11.5, fontWeight: 700, color: '#475569', cursor: 'pointer' }}>
            {t('methodGrounding.recentBatches')} ({recentJobs.length})
          </summary>
          <table style={{ width: '100%', fontSize: 11, borderCollapse: 'collapse', marginTop: 8 }}>
            <thead>
              <tr style={{ color: '#94A3B8', textTransform: 'uppercase', fontSize: 10 }}>
                <th style={{ textAlign: 'left', padding: '4px 6px' }}>{t('methodGrounding.colJob')}</th>
                <th style={{ textAlign: 'left', padding: '4px 6px' }}>{t('methodGrounding.colState')}</th>
                <th style={{ textAlign: 'right', padding: '4px 6px' }}>{t('methodGrounding.colSteps')}</th>
                <th style={{ textAlign: 'right', padding: '4px 6px' }}>{t('methodGrounding.colDoneFailed')}</th>
                <th style={{ textAlign: 'left', padding: '4px 6px' }}>{t('methodGrounding.colStarted')}</th>
              </tr>
            </thead>
            <tbody>
              {recentJobs.slice(0, 8).map(j => (
                <tr key={j.job_id} style={{ borderTop: '1px solid #F1F5F9' }}>
                  <td style={{ padding: '4px 6px', fontFamily: 'monospace', color: '#1A5276' }}>…{j.job_id.slice(-6)}</td>
                  <td style={{ padding: '4px 6px', fontWeight: 700,
                               color: j.state === 'done' ? '#1E8449' : j.state === 'running' ? '#1A5276' : j.state === 'stopped' ? '#C0392B' : '#64748B' }}>
                    {j.state}
                  </td>
                  <td style={{ padding: '4px 6px', textAlign: 'right', fontFamily: 'monospace' }}>{j.completed}/{j.step_count}</td>
                  <td style={{ padding: '4px 6px', textAlign: 'right', fontFamily: 'monospace' }}>
                    {(j.summary?.done ?? 0)} / {(j.summary?.failed ?? 0) + (j.summary?.timeout ?? 0) + (j.summary?.exception ?? 0)}
                  </td>
                  <td style={{ padding: '4px 6px', color: '#64748B' }}>
                    {j.started_at ? new Date(j.started_at).toLocaleString() : (j.queued_at ? new Date(j.queued_at).toLocaleString() : '—')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </details>
      )}
    </div>
  )
}

function ScopeBtn({ label, onClick, tone, disabled }:
  { label: string; onClick: () => void; tone?: 'warn' | 'danger'; disabled?: boolean }) {
  const palette = tone === 'danger'
    ? { bg: '#FEF2F2', border: '#FCA5A5', fg: '#B91C1C' }
    : tone === 'warn'
    ? { bg: '#FFFBEB', border: '#FCD34D', fg: '#9A7D0A' }
    : { bg: '#fff', border: '#CBD5E1', fg: '#1A5276' }
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      style={{
        fontSize: 11, padding: '5px 11px', borderRadius: 5,
        background: palette.bg, border: `1px solid ${palette.border}`, color: palette.fg,
        cursor: disabled ? 'not-allowed' : 'pointer', fontWeight: 700,
        opacity: disabled ? 0.5 : 1,
      }}
    >
      {label}
    </button>
  )
}

function ActiveJobPanel({ job, tiers }: { job: RerunJob; tiers: Tier[] }) {
  const t = useT()
  const stepTitles = useMemo(() => {
    const m: Record<string, string> = {}
    tiers.forEach(t => t.steps.forEach(s => { m[s.id] = s.title }))
    return m
  }, [tiers])
  const total = job.step_ids.length
  const completed = job.results.length
  const pct = total ? Math.round(100 * completed / total) : 0
  const stateColor = job.state === 'running' || job.state === 'queued' ? '#1A5276'
    : job.state === 'done' ? '#1E8449' : '#C0392B'
  return (
    <div style={{ marginTop: 14, padding: 12, background: '#fff', border: '1px solid #E2E8F0', borderRadius: 8 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
        <div>
          <div style={{ fontSize: 12.5, fontWeight: 800, color: '#1A2332' }}>
            {t('methodGrounding.batchLabel')} <code style={{ color: '#1A5276' }}>…{job.job_id.slice(-8)}</code>
            <span style={{ marginLeft: 10, fontSize: 11, color: stateColor, fontWeight: 700 }}>
              {job.state.toUpperCase()}
            </span>
          </div>
          <div style={{ fontSize: 11, color: '#64748B', marginTop: 2 }}>
            {completed}/{total} {total === 1 ? t('methodGrounding.stepSingular') : t('methodGrounding.stepPlural')} {t('methodGrounding.completeWord')}
            {job.current_step_id && (job.state === 'running' || job.state === 'queued') && (
              <> · {t('methodGrounding.runningWord')} <code>{job.current_step_id}</code></>
            )}
          </div>
        </div>
        {job.summary && (
          <div style={{ fontSize: 11, color: '#475569', display: 'flex', gap: 10 }}>
            {job.summary.done ? <span>✓ {job.summary.done}</span> : null}
            {job.summary.failed ? <span style={{ color: '#C0392B' }}>✗ {job.summary.failed}</span> : null}
            {job.summary.timeout ? <span style={{ color: '#9A7D0A' }}>⏱ {job.summary.timeout}</span> : null}
            {job.summary.exception ? <span style={{ color: '#C0392B' }}>! {job.summary.exception}</span> : null}
            {job.summary.skipped ? <span style={{ color: '#94A3B8' }}>↷ {job.summary.skipped}</span> : null}
          </div>
        )}
      </div>
      <div style={{ marginTop: 10, height: 6, background: '#F1F5F9', borderRadius: 3, overflow: 'hidden' }}>
        <div style={{
          width: `${pct}%`, height: '100%',
          background: job.state === 'done' ? '#1E8449' : job.state === 'stopped' ? '#C0392B' : '#1A5276',
          transition: 'width 0.4s ease',
        }} />
      </div>
      <div style={{ marginTop: 10, display: 'grid', gap: 4 }}>
        {job.step_ids.map((sid, idx) => {
          const r = job.results.find(x => x.step_id === sid)
          const isCurrent = sid === job.current_step_id && (job.state === 'running' || job.state === 'queued')
          const status = r?.status ?? (isCurrent ? 'running' : 'pending')
          const palette = STEP_TONES[status] || STEP_TONES.pending
          return (
            <div key={sid} style={{
              display: 'grid', gridTemplateColumns: '24px 1fr auto auto', gap: 8, alignItems: 'center',
              padding: '4px 8px', fontSize: 11,
              background: isCurrent ? '#F0F9FF' : undefined, borderRadius: 4,
            }}>
              <span style={{ fontFamily: 'monospace', color: '#94A3B8', textAlign: 'right' }}>{idx + 1}.</span>
              <div>
                <code style={{ fontSize: 10.5, color: '#1A5276' }}>{sid}</code>
                <span style={{ marginLeft: 8, color: '#475569' }}>
                  {stepTitles[sid] || ''}
                </span>
                {r?.reason && <span style={{ marginLeft: 6, color: '#9A7D0A' }}>— {r.reason}</span>}
                {r?.error && <span style={{ marginLeft: 6, color: '#C0392B' }}>— {r.error}</span>}
              </div>
              <span style={{ fontSize: 10, color: '#64748B', fontVariantNumeric: 'tabular-nums' }}>
                {r?.elapsed_s != null ? `${r.elapsed_s.toFixed(1)}s` : (isCurrent ? '…' : '')}
              </span>
              <span style={{
                fontSize: 9.5, fontWeight: 800, padding: '2px 6px', borderRadius: 3,
                color: palette.fg, background: palette.bg,
              }}>
                {status.toUpperCase()}
              </span>
            </div>
          )
        })}
      </div>
      {(job.state !== 'queued' && job.state !== 'running') && (
        <div style={{ marginTop: 10, fontSize: 11, color: '#475569' }}>
          {t('methodGrounding.finishedAt')} {job.finished_at ? new Date(job.finished_at).toLocaleString() : '—'}.
          {job.state === 'stopped' && ` ${t('methodGrounding.stoppedEarly')}`}
        </div>
      )}
    </div>
  )
}

const STEP_TONES: Record<string, { bg: string; fg: string }> = {
  done:      { bg: '#D1FAE5', fg: '#065F46' },
  failed:    { bg: '#FEE2E2', fg: '#B91C1C' },
  timeout:   { bg: '#FEF3C7', fg: '#9A7D0A' },
  exception: { bg: '#FEE2E2', fg: '#B91C1C' },
  skipped:   { bg: '#F1F5F9', fg: '#64748B' },
  missing:   { bg: '#F1F5F9', fg: '#64748B' },
  running:   { bg: '#DBEAFE', fg: '#1E40AF' },
  pending:   { bg: '#F8FAFC', fg: '#94A3B8' },
}

// ── Tier card ─────────────────────────────────────────────────────────────────
function TierCard({ tier, running, selected, onToggle, onRun, onOpen, hostFsSteps, onSelectTier, batchDisabled }:
  {
    tier: Tier
    running: string | null
    selected: Set<string>
    onToggle: (id: string) => void
    onRun: (id: string) => void
    onOpen: (id: string) => void
    hostFsSteps: string[]
    onSelectTier: () => void
    batchDisabled: boolean
  }) {
  const t = useT()
  const counts = useMemo(() => tier.steps.reduce((acc, s) => {
    acc[s.status] = (acc[s.status] || 0) + 1; return acc
  }, {} as Record<string, number>), [tier])
  const total = tier.steps.length
  const passed = counts.pass || 0
  const pct = total ? Math.round(100 * passed / total) : 0
  const runnableInTier = tier.steps.filter(s => !!s.script).length
  const selectedInTier = tier.steps.filter(s => selected.has(s.id)).length
  return (
    <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10, overflow: 'hidden' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12,
                    padding: '12px 16px', background: '#F8FAFC', borderBottom: '1px solid #E2E8F0' }}>
        <div>
          <div style={{ fontSize: 14.5, fontWeight: 800, color: '#1A5276' }}>{tier.title}</div>
          <div style={{ fontSize: 11, color: '#64748B', marginTop: 2 }}>{TIER_BLURB_KEYS[tier.id] ? t('methodGrounding.' + TIER_BLURB_KEYS[tier.id]) : ''}</div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <ProgressBar pct={pct} />
          <span style={{ fontSize: 11, fontFamily: 'monospace', color: '#475569' }}>{passed}/{total}</span>
          <button
            onClick={onSelectTier}
            disabled={batchDisabled || runnableInTier === 0}
            title={`${t('methodGrounding.selectTierTitlePrefix')} ${runnableInTier} ${t('methodGrounding.selectTierTitleSuffix')} ${tier.id}`}
            style={{
              fontSize: 10.5, padding: '4px 8px', borderRadius: 5,
              border: '1px solid #CBD5E1', background: '#fff', color: '#1A5276',
              cursor: batchDisabled || runnableInTier === 0 ? 'not-allowed' : 'pointer',
              fontWeight: 700, opacity: batchDisabled || runnableInTier === 0 ? 0.5 : 1,
            }}
          >
            {t('methodGrounding.selectTier')} {selectedInTier > 0 ? `(${selectedInTier}/${runnableInTier})` : ''}
          </button>
        </div>
      </div>
      {tier.steps.map((step, i) => (
        <StepRow
          key={step.id}
          step={step}
          running={running}
          selected={selected.has(step.id)}
          onToggle={onToggle}
          onRun={onRun}
          onOpen={onOpen}
          first={i === 0}
          isHostFs={hostFsSteps.includes(step.id)}
          batchDisabled={batchDisabled}
        />
      ))}
    </div>
  )
}

function ProgressBar({ pct }: { pct: number }) {
  return (
    <div style={{ width: 120, height: 8, background: '#F1F5F9', borderRadius: 4, overflow: 'hidden' }}>
      <div style={{ width: `${pct}%`, height: '100%',
                    background: pct >= 80 ? '#1E8449' : pct >= 50 ? '#B9770E' : '#94A3B8' }} />
    </div>
  )
}

function StepRow({ step, running, selected, onToggle, onRun, onOpen, first, isHostFs, batchDisabled }:
  {
    step: Step
    running: string | null
    selected: boolean
    onToggle: (id: string) => void
    onRun: (id: string) => void
    onOpen: (id: string) => void
    first: boolean
    isHostFs: boolean
    batchDisabled: boolean
  }) {
  const t = useT()
  const tone = STATUS_TONE[step.status] || STATUS_TONE.unknown
  const toneLabel = t('methodGrounding.' + tone.labelKey)
  const finished = step.finished_at ? new Date(step.finished_at).toLocaleString() : '—'
  const checkable = !!step.script
  // Reason explains *why* a step is pass/warn/fail. Backend exposes it under
  // headline.reason (see grounding.py::_HEADLINE_KEYS). Fall back gracefully.
  const reasonRaw = (step.headline && (step.headline as Record<string, unknown>).reason) ?? null
  const reason = typeof reasonRaw === 'string' ? reasonRaw : (reasonRaw ? JSON.stringify(reasonRaw) : '')
  return (
    <div style={{
      display: 'grid', gridTemplateColumns: '20px 24px 1fr 110px 90px auto auto', gap: 12, alignItems: 'center',
      padding: '11px 16px', borderTop: first ? undefined : '1px solid #F1F5F9',
      background: selected ? '#F0F9FF' : undefined,
    }}>
      <input
        type="checkbox"
        checked={selected}
        disabled={!checkable || batchDisabled}
        onChange={() => onToggle(step.id)}
        title={
          !checkable ? t('methodGrounding.checkboxManual')
          : batchDisabled ? t('methodGrounding.checkboxBatchRunning')
          : t('methodGrounding.checkboxAddRemove')
        }
        style={{ cursor: !checkable || batchDisabled ? 'not-allowed' : 'pointer' }}
      />
      <span style={{ fontSize: 10, fontWeight: 800, color: '#fff', background: tone.bg, padding: '3px 5px',
                     borderRadius: 4, textAlign: 'center' }}>{toneLabel[0]}</span>
      <div>
        <div style={{ fontSize: 13, fontWeight: 600, color: '#1A2332' }}>
          {step.title}
          {isHostFs && (
            <span title={t('methodGrounding.hostFsBadgeTitle')}
                  style={{ marginLeft: 8, fontSize: 9.5, fontWeight: 700, padding: '1px 6px', borderRadius: 4,
                            color: '#9A7D0A', background: '#FEF3C7', border: '1px solid #FDE68A' }}>
              HOST-FS
            </span>
          )}
        </div>
        <div style={{ fontSize: 10.5, color: '#94A3B8', fontFamily: 'monospace', display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <span>{step.id}</span>
          {step.report_filename && <span title={t('methodGrounding.reportTitle')}>📄 {step.report_filename}</span>}
          {step.input_hash && <span title={t('methodGrounding.inputHashTitle')}>⌗ {step.input_hash.slice(0, 8)}</span>}
        </div>
        {reason && (
          <div
            title={reason}
            style={{
              fontSize: 11.5,
              color: tone.fg,
              marginTop: 4,
              lineHeight: 1.4,
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
            }}
          >
            {reason}
          </div>
        )}
      </div>
      <div style={{ fontSize: 10.5, color: '#64748B', fontVariantNumeric: 'tabular-nums' }}>{finished}</div>
      <span style={{ fontSize: 10, fontWeight: 800, color: tone.fg, background: tone.bg, padding: '3px 8px',
                     borderRadius: 4, textAlign: 'center' }}>{toneLabel}</span>
      <button onClick={() => onOpen(step.id)} style={{
        fontSize: 11, padding: '5px 10px', borderRadius: 6, border: '1px solid #CBD5E1',
        background: '#fff', color: '#1A2332', cursor: 'pointer', fontWeight: 600 }}>
        {t('methodGrounding.evidenceBtn')}
      </button>
      {step.script ? (
        <button
          disabled={running === step.id || batchDisabled}
          onClick={() => onRun(step.id)}
          title={batchDisabled ? t('methodGrounding.rerunBtnTitleBusy') : t('methodGrounding.rerunBtnTitle')}
          style={{
            fontSize: 11, padding: '5px 10px', borderRadius: 6, border: '1px solid #AED6F1',
            background: '#EBF5FB', color: '#1A5276',
            cursor: running === step.id || batchDisabled ? 'not-allowed' : 'pointer',
            fontWeight: 700, opacity: batchDisabled ? 0.5 : 1,
          }}
        >
          {running === step.id ? t('methodGrounding.runningWord') : t('methodGrounding.rerunBtn')}
        </button>
      ) : (
        <span style={{ fontSize: 10.5, color: '#A0AEC0', fontStyle: 'italic' }}>{step.type || t('methodGrounding.manual')}</span>
      )}
    </div>
  )
}

// ── Drawer ────────────────────────────────────────────────────────────────────
function Drawer({ drawer, onClose, onRerun, running }:
  { drawer: { id: string; report: any | null; loading: boolean }; onClose: () => void;
    onRerun: (id: string) => void; running: string | null }) {
  const t = useT()
  return (
    <>
      <div onClick={onClose} style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,0.40)', zIndex: 50 }} />
      <aside style={{ position: 'fixed', top: 0, right: 0, bottom: 0, width: 'min(560px, 100%)', background: '#fff',
                      boxShadow: '-12px 0 32px rgba(15,23,42,0.18)', zIndex: 51, padding: '20px 24px',
                      overflowY: 'auto', fontFamily: 'Inter, system-ui, sans-serif' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
          <h2 style={{ fontSize: 16, fontWeight: 800, color: '#1A2332', margin: 0 }}>{t('methodGrounding.stepReport')}</h2>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer',
                                             fontSize: 18, color: '#64748B' }}>✕</button>
        </div>
        <div style={{ fontSize: 12, fontFamily: 'monospace', color: '#1A5276', marginBottom: 12 }}>{drawer.id}</div>
        {drawer.loading && <p style={{ color: '#94A3B8', fontSize: 13 }}>{t('methodGrounding.loading')}</p>}
        {!drawer.loading && drawer.report && (
          <>
            <div style={{ display: 'grid', gridTemplateColumns: '110px 1fr', gap: 6, fontSize: 12, marginBottom: 12 }}>
              <span style={{ color: '#94A3B8' }}>{t('methodGrounding.drawerStatus')}</span>
              <b style={{ color: drawer.report.status === 'pass' ? '#1E8449'
                                : drawer.report.status === 'fail' ? '#C0392B' : '#B9770E' }}>
                {drawer.report.status}
              </b>
              <span style={{ color: '#94A3B8' }}>{t('methodGrounding.drawerFinished')}</span>
              <span>{drawer.report.finished_at}</span>
              <span style={{ color: '#94A3B8' }}>{t('methodGrounding.labelRun')}</span>
              <code style={{ fontSize: 10.5, color: '#1A5276' }}>{drawer.report.phase2_run_id}</code>
              <span style={{ color: '#94A3B8' }}>{t('methodGrounding.labelSeal')}</span>
              <code style={{ fontSize: 10.5, color: '#1A5276' }}>{drawer.report.seal_id}</code>
              <span style={{ color: '#94A3B8' }}>{t('methodGrounding.drawerInputHash')}</span>
              <code style={{ fontSize: 10.5 }}>{drawer.report.input_hash || '—'}</code>
              <span style={{ color: '#94A3B8' }}>{t('methodGrounding.drawerHost')}</span>
              <span style={{ fontSize: 11 }}>{drawer.report.host || '—'}</span>
            </div>
            {drawer.report.reason && (
              <div style={{
                background: drawer.report.status === 'pass' ? '#ECFDF5'
                          : drawer.report.status === 'fail' ? '#FEF2F2' : '#FFFBEB',
                border: `1px solid ${
                  drawer.report.status === 'pass' ? '#A7F3D0'
                  : drawer.report.status === 'fail' ? '#FECACA' : '#FDE68A'
                }`,
                color: drawer.report.status === 'pass' ? '#065F46'
                       : drawer.report.status === 'fail' ? '#7F1D1D' : '#78350F',
                borderRadius: 8, padding: '10px 12px', fontSize: 12, lineHeight: 1.5,
                marginBottom: 14,
              }}>
                <div style={{ fontSize: 10, fontWeight: 800, textTransform: 'uppercase',
                              letterSpacing: 0.4, marginBottom: 4, opacity: 0.75 }}>
                  {t('methodGrounding.reasonLabel')}
                </div>
                {String(drawer.report.reason)}
              </div>
            )}
            <button onClick={() => onRerun(drawer.id)} disabled={running === drawer.id} style={{
              fontSize: 12, padding: '7px 14px', borderRadius: 6, border: '1px solid #AED6F1',
              background: '#EBF5FB', color: '#1A5276', cursor: 'pointer', fontWeight: 700, marginBottom: 14 }}>
              {running === drawer.id ? t('methodGrounding.runningWord') : t('methodGrounding.rerunThisStep')}
            </button>
            <div style={{ fontSize: 11, color: '#94A3B8', fontWeight: 700, textTransform: 'uppercase', marginBottom: 4 }}>
              {t('methodGrounding.fullPayload')}
            </div>
            <pre style={{ background: '#0F172A', color: '#E2E8F0', borderRadius: 8, padding: 14, fontSize: 11,
                          lineHeight: 1.5, maxHeight: '60vh', overflow: 'auto' }}>
              {JSON.stringify(drawer.report, null, 2)}
            </pre>
          </>
        )}
        {!drawer.loading && !drawer.report && (
          <p style={{ color: '#B9770E', fontSize: 13 }}>{t('methodGrounding.noReportYet')}</p>
        )}
      </aside>
    </>
  )
}
