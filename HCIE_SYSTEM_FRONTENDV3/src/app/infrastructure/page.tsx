'use client'

/**
 * Infrastructure & Auditability — the event-sourced substrate, made visible.
 *
 * Top: live pipeline flow (submission → outbox → Kafka → projection → trajectory)
 *      with polled counts. "The system is alive and auditable."
 * Below: determinism / run-sealing proof. "Pin me to the rows behind any number."
 *
 * Data:
 *   GET /v3/frontend/dashboard/pipeline-stats   (polled every 5s)
 *   GET /v3/frontend/dashboard/sealed-runs
 */

import { useEffect, useState, useRef, useCallback } from 'react'
import Link from 'next/link'
import { getBackendUrl } from '@/lib/api/backend-url'
import { useT } from '@/contexts/language_context'

const BACKEND = getBackendUrl()

function getAuthHeaders(): HeadersInit {
  const token = (typeof window !== 'undefined' &&
    (localStorage.getItem('hcie_auth_token') || localStorage.getItem('access_token'))) || ''
  return token ? { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }
               : { 'Content-Type': 'application/json' }
}

const fmt = (n: number | undefined) => (n ?? 0).toLocaleString()

export default function InfrastructurePage() {
  const t = useT()
  const [stats, setStats] = useState<any>(null)
  const [seals, setSeals] = useState<any[]>([])
  const [lastUpdate, setLastUpdate] = useState<string>('')
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const loadStats = useCallback(async () => {
    try {
      const r = await fetch(`${BACKEND}/v3/frontend/dashboard/pipeline-stats`,
        { headers: getAuthHeaders(), signal: AbortSignal.timeout(10000) })
      if (r.ok) {
        setStats(await r.json())
        setLastUpdate(new Date().toLocaleTimeString())
      }
    } catch { /* keep */ }
  }, [])

  useEffect(() => {
    loadStats()
    pollRef.current = setInterval(loadStats, 5000)
    ;(async () => {
      try {
        const r = await fetch(`${BACKEND}/v3/frontend/dashboard/sealed-runs`,
          { headers: getAuthHeaders(), signal: AbortSignal.timeout(10000) })
        if (r.ok) { const d = await r.json(); setSeals(d.sealed_runs ?? []) }
      } catch { /* empty */ }
    })()
    return () => { if (pollRef.current) clearInterval(pollRef.current) }
  }, [loadStats])

  const s = stats?.stages
  const failed = s?.outbox?.failed ?? 0

  // Pipeline stages for the flow diagram
  const STAGES = [
    { key: 'submit', icon: '✍️', label: 'Submission', sub: 'learner attempt', value: null,
      color: '#2980B9', desc: 'A learner answers — the only write that starts the chain.' },
    { key: 'outbox', icon: '📤', label: 'Transactional Outbox', sub: `${fmt(s?.outbox?.total)} events`,
      value: s?.outbox?.total, color: '#117A65',
      desc: 'Event written in the SAME DB transaction as the state change — no dual-write race. The auditable trail.' },
    { key: 'kafka', icon: '⚡', label: 'Kafka (Redpanda)', sub: 'event stream', value: null,
      color: '#E67E22', desc: 'Outbox relay publishes to topics (.mastery, .submissions, cognition_updated…). Consumers subscribe.' },
    { key: 'projection', icon: '🗂', label: 'Projections', sub: `${fmt(s?.projection?.read_models)} read-models`,
      value: s?.projection?.read_models, color: '#8E44AD',
      desc: 'Consumers fold events into read models (learner_projections) — CQRS read side, rebuildable from the log.' },
    { key: 'trajectory', icon: '📈', label: 'Trajectory', sub: `${fmt(s?.trajectory?.rows_estimated)} rows`,
      value: s?.trajectory?.rows_estimated, color: '#C0392B',
      desc: 'Governance trajectory (experiment_trajectories) — every interaction with its full JT attribution, replayable.' },
  ]

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: '24px 20px' }}>

      {/* Header */}
      <div style={{ marginBottom: 12 }}>
        <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.1em',
                      color: '#117A65', textTransform: 'uppercase', marginBottom: 4 }}>
          {t('infrastructure.eyebrow')}
        </div>
        <h1 style={{ fontSize: 22, fontWeight: 800, color: '#1A2332', margin: 0 }}>
          {t('infrastructure.title')}
        </h1>
        <div style={{ fontSize: 12, color: '#718096', marginTop: 4, maxWidth: 760, lineHeight: 1.5 }}>
          {t('infrastructure.intro')}
          {lastUpdate && <span style={{ color: '#A0AEC0' }}> · {lastUpdate}</span>}
        </div>
      </div>

      {/* ══ LIVE PIPELINE FLOW ════════════════════════════════════════════════ */}
      <div style={{ background: '#fff', border: '2px solid #A2D9CE', borderRadius: 12,
                    padding: '20px', marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div style={{ fontSize: 14, fontWeight: 800, color: '#1A2332' }}>
            Live event pipeline
          </div>
          <span style={{ fontSize: 10, fontWeight: 700, color: '#1E8449', background: '#D5F5E3',
                         borderRadius: 10, padding: '3px 10px' }}>
            ● polling every 5s
          </span>
        </div>

        {/* Flow row */}
        <div style={{ display: 'flex', alignItems: 'stretch', gap: 4, overflowX: 'auto', paddingBottom: 6 }}>
          {STAGES.map((st, i) => (
            <div key={st.key} style={{ display: 'flex', alignItems: 'center', gap: 4, flex: 1, minWidth: 150 }}>
              <div style={{ flex: 1, background: `${st.color}0D`, border: `1px solid ${st.color}40`,
                            borderTop: `3px solid ${st.color}`, borderRadius: 10, padding: '12px 10px',
                            minHeight: 130, display: 'flex', flexDirection: 'column' }}>
                <div style={{ fontSize: 22, marginBottom: 4 }}>{st.icon}</div>
                <div style={{ fontSize: 12, fontWeight: 800, color: st.color }}>{st.label}</div>
                <div style={{ fontSize: 16, fontWeight: 800, color: '#1A2332', margin: '4px 0',
                              fontVariantNumeric: 'tabular-nums' }}>
                  {st.value != null ? fmt(st.value) : <span style={{ fontSize: 11, color: '#A0AEC0' }}>{st.sub}</span>}
                </div>
                {st.value != null && <div style={{ fontSize: 9, color: '#718096' }}>{st.sub.replace(/^[\d,]+ /, '')}</div>}
                <div style={{ fontSize: 9.5, color: '#718096', marginTop: 6, lineHeight: 1.4 }}>{st.desc}</div>
              </div>
              {i < STAGES.length - 1 && (
                <div style={{ fontSize: 20, color: '#A2D9CE', fontWeight: 800 }}>→</div>
              )}
            </div>
          ))}
        </div>

        {/* Outbox health + DLQ */}
        <div style={{ display: 'flex', gap: 12, marginTop: 14, flexWrap: 'wrap' }}>
          <HealthChip label="Published" value={fmt(s?.outbox?.published)} good />
          <HealthChip label="Failed (DLQ)" value={fmt(failed)} good={failed === 0} warn={failed > 0} />
          <HealthChip label="Delivery rate"
            value={s?.outbox?.total ? `${((s.outbox.published / s.outbox.total) * 100).toFixed(3)}%` : '—'} good />
        </div>
      </div>

      {/* Event-type taxonomy */}
      {stats?.event_types?.length > 0 && (
        <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10,
                      padding: '16px 20px', marginBottom: 16 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: '#2C3E50', marginBottom: 2 }}>
            What flows through — event taxonomy
          </div>
          <div style={{ fontSize: 11, color: '#718096', marginBottom: 12 }}>
            Every domain change is a typed event. These are the real types in the outbox.
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
            {(() => {
              const max = Math.max(...stats.event_types.map((e: any) => e.count))
              return stats.event_types.map((e: any) => (
                <div key={e.type} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span style={{ width: 200, fontSize: 11, fontWeight: 600, color: '#2C3E50',
                                 fontFamily: 'monospace' }}>{e.type}</span>
                  <div style={{ flex: 1, height: 16, background: '#EDF2F7', borderRadius: 3, overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: `${(e.count / max) * 100}%`,
                                  background: '#117A65', borderRadius: 3 }} />
                  </div>
                  <span style={{ width: 80, textAlign: 'right', fontSize: 11, fontWeight: 700,
                                 color: '#4A5568', fontVariantNumeric: 'tabular-nums' }}>{fmt(e.count)}</span>
                </div>
              ))
            })()}
          </div>
        </div>
      )}

      {/* ══ DETERMINISM / SEALING PROOF ═══════════════════════════════════════ */}
      <div style={{ background: 'linear-gradient(135deg, #EBF5FB, #F4ECF7)',
                    border: '1px solid #C3CFE2', borderRadius: 12, padding: '18px 20px', marginBottom: 16 }}>
        <div style={{ fontSize: 14, fontWeight: 800, color: '#1A2332', marginBottom: 2 }}>
          🔒 Determinism & provenance — "pin me to the rows behind this number"
        </div>
        <div style={{ fontSize: 12, color: '#4A5568', lineHeight: 1.6, marginBottom: 14 }}>
          Because the system is event-sourced, a run can be <strong>sealed</strong>: its exact row count
          and a content hash are frozen. Anyone can re-derive the hash from the live rows and confirm a
          cited figure reproduces. Post-seal writes are rejected (the run is immutable). This is the
          difference between "trust me" and "here's the sealed artifact."
        </div>

        {seals.length === 0 && (
          <div style={{ fontSize: 12, color: '#A0AEC0' }}>No sealed runs yet.</div>
        )}
        {seals.map(seal => {
          const fs = seal.frozen_stats || {}
          return (
            <div key={seal.seal_id} style={{ background: '#fff', border: '1px solid #D2B4DE',
                                             borderRadius: 10, padding: '14px 16px', marginBottom: 10 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                            flexWrap: 'wrap', gap: 8, marginBottom: 10 }}>
                <span style={{ fontSize: 12, fontWeight: 800, color: '#6C3483', fontFamily: 'monospace' }}>
                  {seal.seal_id}
                </span>
                <span style={{ fontSize: 10, fontWeight: 700, color: '#1E8449', background: '#D5F5E3',
                               borderRadius: 4, padding: '2px 8px' }}>✓ SEALED · immutable</span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 10 }}>
                <Field label="Run ID" value={seal.run_id} mono />
                <Field label="Sealed rows (N)" value={fmt(seal.row_count)} />
                <Field label="Content hash" value={seal.content_hash?.slice(0, 20) + '…'} mono />
                <Field label="Sealed at" value={seal.sealed_at?.slice(0, 10)} />
                {fs.mean != null && <Field label="frozen mean" value={Number(fs.mean).toFixed(5)} />}
                {fs.signal_ratio != null && <Field label="signal_ratio" value={Number(fs.signal_ratio).toFixed(4)} />}
                {fs.adc_class && <Field label="ADC verdict" value={String(fs.adc_class)} />}
              </div>
            </div>
          )
        })}

        <div style={{ fontSize: 11, color: '#718096', lineHeight: 1.6, marginTop: 4 }}>
          ⚠ Only <strong>{seals.length}</strong> run is sealed (the thesis anchor). The validated re-run
          campaign will seal each new experiment so every cited number has an anchor — that's the
          provenance discipline the whole frontend is being built to make visible.
        </div>
      </div>

      {/* Why event-sourcing (the rationale) */}
      <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10,
                    padding: '16px 20px', marginBottom: 16 }}>
        <div style={{ fontSize: 13, fontWeight: 700, color: '#2C3E50', marginBottom: 10 }}>
          Why event-sourcing (not REST CRUD)?
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 12 }}>
          {[
            ['Auditable', 'Every change is an immutable event. Nothing is overwritten — the full history is the source of truth.'],
            ['Reproducible', 'Read models are a fold over the log. Rebuild them, replay them, get the same answer (determinism).'],
            ['Provable', 'Seal a run → content hash. "Pin me to the rows" is answerable, not a hand-wave.'],
            ['Decoupled', 'Outbox + Kafka means the write path never blocks on the read side; consumers scale independently.'],
          ].map(([t, d]) => (
            <div key={t} style={{ background: '#F8F9FF', border: '1px solid #C3CFE2', borderRadius: 8, padding: '10px 14px' }}>
              <div style={{ fontSize: 12, fontWeight: 800, color: '#1A5276', marginBottom: 4 }}>{t}</div>
              <div style={{ fontSize: 11, color: '#4A5568', lineHeight: 1.5 }}>{d}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Footer nav */}
      <div style={{ display: 'flex', gap: 10, marginTop: 24, justifyContent: 'center', flexWrap: 'wrap' }}>
        <Link href="/dashboard/instructor" style={{ fontSize: 13, fontWeight: 600, color: '#4A5568',
          textDecoration: 'none', padding: '10px 24px', borderRadius: 8,
          border: '1px solid #CBD5E0', background: '#fff' }}>
          ← Instructor Dashboard
        </Link>
        <Link href="/dashboard/governance" style={{ fontSize: 13, fontWeight: 700, color: '#fff',
          textDecoration: 'none', padding: '10px 24px', borderRadius: 8, background: '#117A65' }}>
          ⚡ Live Governance Monitor →
        </Link>
      </div>
    </div>
  )
}

function HealthChip({ label, value, good, warn }: { label: string; value: string; good?: boolean; warn?: boolean }) {
  const c = warn ? '#C0392B' : good ? '#1E8449' : '#718096'
  const bg = warn ? '#FDEDEC' : good ? '#D5F5E3' : '#F7FAFC'
  return (
    <div style={{ background: bg, border: `1px solid ${c}40`, borderRadius: 8, padding: '8px 14px' }}>
      <div style={{ fontSize: 9, fontWeight: 700, color: '#718096', textTransform: 'uppercase' }}>{label}</div>
      <div style={{ fontSize: 16, fontWeight: 800, color: c, fontVariantNumeric: 'tabular-nums' }}>{value}</div>
    </div>
  )
}

function Field({ label, value, mono }: { label: string; value: any; mono?: boolean }) {
  return (
    <div>
      <div style={{ fontSize: 9, fontWeight: 700, color: '#A0AEC0', textTransform: 'uppercase' }}>{label}</div>
      <div style={{ fontSize: 12, fontWeight: 700, color: '#2C3E50',
                    fontFamily: mono ? 'monospace' : 'inherit',
                    wordBreak: 'break-all', lineHeight: 1.3 }}>{value}</div>
    </div>
  )
}
