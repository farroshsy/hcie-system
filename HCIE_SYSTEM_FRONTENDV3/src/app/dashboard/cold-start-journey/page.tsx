'use client'

/**
 * Cold-Start Learning Journey
 *
 * Traces a real learner's cold-start progression with full JT 6D governance
 * decomposition per interaction. Data from:
 *   GET /v3/frontend/dashboard/cold-start-users?limit=30
 *   GET /v3/frontend/dashboard/cold-start-journey?user_id=X&run_id=Y&limit=50
 *
 * Falls back to sealed-run reference panel when backend is unreachable.
 */

import React, { useState, useEffect, useCallback } from 'react'
import {
  LineChart, Line, BarChart, Bar, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  ReferenceLine, Legend,
} from 'recharts'
import { getBackendUrl } from '@/lib/api/backend-url'
import ProvenanceBadge from '@/components/review/ProvenanceBadge'
import Link from 'next/link'
import { Panel, Tag, Callout, SectionTitle, Eyebrow, Stat } from '@/lib/ui/primitives'
import { t as ui, type Tone } from '@/lib/ui/theme'
import { useT } from '@/contexts/language_context'

// ─── Types ────────────────────────────────────────────────────────────────────

type UserEntry = {
  user_id: string
  n_interactions: number
  run_id?: string | null
}

type InteractionPoint = {
  interaction_number: number
  concept?: string | null
  correctness?: boolean | number | null
  mastery_before: number
  mastery_after: number
  kalman_mastery_after?: number | null
  bayesian_mastery_after?: number | null
  // JT 6D
  jt_challenge_contribution?: number | null
  jt_uncertainty_contribution?: number | null
  jt_delta_m_contribution?: number | null
  jt_zpd_contribution?: number | null
  jt_transfer_contribution?: number | null
  jt_transfer_prospective_contribution?: number | null
  jt_value?: number | null
  // ensemble weights
  ensemble_weight_kalman?: number | null
  ensemble_weight_bayesian?: number | null
  ensemble_weight_lyapunov?: number | null
}

type JourneyData = {
  status?: string
  user_id?: string
  run_id?: string | null
  n_interactions?: number
  window_auc?: {
    hcie?: Record<string, number>
    bkt?: Record<string, number>
  }
  interactions?: InteractionPoint[]
  error?: string
}

type UsersData = {
  status?: string
  users?: UserEntry[]
  error?: string
}

// ─── Constants ────────────────────────────────────────────────────────────────

const JT_COLORS: Record<string, string> = {
  challenge:   ui.modelColor.sakt,
  uncertainty: ui.modelColor.hcie,
  delta_m:     ui.modelColor.bkt,
  zpd:         ui.modelColor.irt_1pl,
  transfer:    ui.tone.bad.fg,
  prospective: ui.color.faint,
}

const JT_DIMS = ['challenge', 'uncertainty', 'delta_m', 'zpd', 'transfer', 'prospective'] as const
type JTDim = typeof JT_DIMS[number]

// Series colors for the hero mastery chart (distinct per model output).
const MASTERY_COLORS = {
  ensemble: ui.tone.info.fg,   // HCIE Ensemble (hero line)
  kalman:   ui.modelColor.bkt, // Kalman component
  bayesian: ui.modelColor.irt_1pl, // Bayesian component
}

// Sealed run reference (canonical Kalman re-seal — Tabel 4.5 · seal-bae44d1a · run-d2154070)
const SEALED = {
  n: 96727,
  seal: 'bae44d1a',
  hcie_auc: 0.6051,
  bkt_auc:  0.5963,
  dkt_auc:  0.5892,
  date:     '2026-06-17',
  jt_means: {
    challenge:   { mean: 0.158, signal_ratio: 1.64, status: 'ACTIVE' },
    uncertainty: { mean: 0.119, signal_ratio: 1.22, status: 'ACTIVE' },
    delta_m:     { mean: 0.083, signal_ratio: 0.97, status: 'ACTIVE' },
    zpd:         { mean: 0.044, signal_ratio: 0.71, status: 'ACTIVE' },
    transfer:    { mean: 0.015, signal_ratio: 0.38, status: 'near-threshold' },
    prospective: { mean: 0.000, signal_ratio: 0.00, status: 'structural_zero' },
  },
  kalman_corr:  0.3322,
  bayesian_corr: 0.9204,
}

// ─── Sub-components ───────────────────────────────────────────────────────────

const ADC_TONE: Record<string, Tone> = {
  ACTIVE:           'ok',
  'near-threshold': 'warn',
  structural_zero:  'bad',
}

function adcBadge(status: string) {
  return <Tag tone={ADC_TONE[status] ?? 'neutral'}>{status}</Tag>
}

// Custom tooltip for mastery chart.
// `t` is threaded in so the module-level component can resolve translations.
function MasteryTooltip({ active, payload, t }: any) {
  if (!active || !payload?.length) return null
  const d = payload[0]?.payload as InteractionPoint | undefined
  if (!d) return null
  return (
    <div style={{ background: ui.color.ink, color: ui.color.subtle, padding: '10px 14px',
                  borderRadius: ui.radius.md, fontSize: ui.font.size.sm, lineHeight: 1.6, minWidth: 180 }}>
      <div style={{ fontWeight: ui.font.weight.bold, marginBottom: 4 }}>{t('coldStartJourney.tooltipInteraction')} #{d.interaction_number}</div>
      {d.concept && <div style={{ color: ui.color.faint }}>{d.concept}</div>}
      <div style={{ marginTop: 4 }}>
        <span style={{ color: d.correctness ? ui.tone.ok.fg : ui.tone.bad.fg, fontWeight: ui.font.weight.bold }}>
          {d.correctness ? t('coldStartJourney.correct') : t('coldStartJourney.incorrect')}
        </span>
      </div>
      {payload.map((p: any) => (
        <div key={p.name} style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
          <span style={{ color: p.color }}>{p.name}</span>
          <span>{typeof p.value === 'number' ? p.value.toFixed(3) : '—'}</span>
        </div>
      ))}
      {d.jt_value != null && (
        <div style={{ marginTop: 4, borderTop: `1px solid ${ui.color.body}`, paddingTop: 4, color: ui.color.faint }}>
          {t('coldStartJourney.tooltipJtTotal')}: {d.jt_value.toFixed(3)}
        </div>
      )}
    </div>
  )
}

// ─── Fallback panel ───────────────────────────────────────────────────────────

function FallbackPanel({ t }: { t: (key: string, fallback?: string) => string }) {
  return (
    <div>
      <Callout tone="warn" style={{ marginBottom: ui.space.lg }}
        title={t('coldStartJourney.fallbackTitle')}>
        {t('coldStartJourney.fallbackBodyA')}
        {' '}<code style={{ background: ui.tone.warn.bg }}>/v3/frontend/dashboard/cold-start-journey</code>{' '}
        {t('coldStartJourney.fallbackBodyB')}
      </Callout>

      <Panel style={{ marginBottom: ui.space.lg }}>
        <SectionTitle>{t('coldStartJourney.sealedRunReference')} — N=96,727</SectionTitle>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: ui.space.md, marginBottom: ui.space.lg }}>
          {[
            { label: t('coldStartJourney.statHcieAucAll'), value: SEALED.hcie_auc.toFixed(3), tone: 'ok' as Tone },
            { label: t('coldStartJourney.statBktAucAll'),  value: SEALED.bkt_auc.toFixed(3),  tone: 'info' as Tone },
            { label: t('coldStartJourney.statDktAucAll'),  value: SEALED.dkt_auc.toFixed(3),  tone: 'accent' as Tone },
            { label: t('coldStartJourney.statSealId'),     value: SEALED.seal,                tone: 'neutral' as Tone },
          ].map(c => (
            <Stat key={c.label} label={c.label} value={c.value} tone={c.tone} />
          ))}
        </div>

        <SectionTitle>{t('coldStartJourney.adcSixDStatusSealed')}</SectionTitle>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: ui.space.sm }}>
          {JT_DIMS.map(dim => {
            const info = SEALED.jt_means[dim]
            return (
              <Panel key={dim} pad="md" tone="neutral">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: ui.space.xs }}>
                  <span style={{ fontSize: ui.font.size.base, fontWeight: ui.font.weight.bold, color: JT_COLORS[dim] }}>{dim}</span>
                  {adcBadge(info.status)}
                </div>
                <div style={{ fontSize: ui.font.size.sm, color: ui.color.body }}>
                  mean={info.mean.toFixed(3)} · signal_ratio={info.signal_ratio.toFixed(2)}
                </div>
              </Panel>
            )
          })}
        </div>
      </Panel>

      <ProvenanceBadge
        source="frozen"
        generatedAt="2026-06-05T00:00:00Z"
        runId={SEALED.seal}
        n={SEALED.n}
        note={`${t('coldStartJourney.provSealedRun')} · matched-eval cold-start AUC: HCIE ${SEALED.hcie_auc} (leads) · BKT ${SEALED.bkt_auc} · DKT ${SEALED.dkt_auc}`}
      />
    </div>
  )
}

// ─── Main page ────────────────────────────────────────────────────────────────

export default function ColdStartJourneyPage() {
  const t = useT()
  const BACKEND = getBackendUrl()

  const [users, setUsers]           = useState<UserEntry[]>([])
  const [selectedUser, setSelectedUser] = useState<string>('')
  const [runId, setRunId]           = useState<string>('')
  const [journey, setJourney]       = useState<JourneyData | null>(null)
  const [loadingUsers, setLoadingUsers] = useState(true)
  const [loadingJourney, setLoadingJourney] = useState(false)
  const [error, setError]           = useState<string | null>(null)
  const [noData, setNoData]         = useState(false)

  // ── Fetch user list on mount ──
  useEffect(() => {
    setLoadingUsers(true)
    fetch(`${BACKEND}/v3/frontend/dashboard/cold-start-users?limit=30`,
      { signal: AbortSignal.timeout(12000) })
      .then(r => r.ok ? r.json() : Promise.reject(r.status))
      .then((data: UsersData) => {
        const list = data.users ?? []
        setUsers(list)
        if (list.length > 0) setSelectedUser(list[0].user_id)
      })
      .catch(() => {
        setUsers([])
        setNoData(true)
      })
      .finally(() => setLoadingUsers(false))
  }, [BACKEND])

  // ── Auto-load journey when user changes ──
  const loadJourney = useCallback((userId: string, rid: string) => {
    if (!userId) return
    setLoadingJourney(true)
    setError(null)
    setNoData(false)
    const params = new URLSearchParams({ user_id: userId, limit: '50' })
    if (rid) params.set('run_id', rid)
    fetch(`${BACKEND}/v3/frontend/dashboard/cold-start-journey?${params}`,
      { signal: AbortSignal.timeout(15000) })
      .then(r => r.ok ? r.json() : Promise.reject(r.status))
      .then((data: JourneyData) => {
        if (!data.interactions || data.interactions.length === 0) {
          setNoData(true)
          setJourney(null)
        } else {
          setJourney(data)
        }
      })
      .catch(() => {
        setNoData(true)
        setJourney(null)
      })
      .finally(() => setLoadingJourney(false))
  }, [BACKEND])

  useEffect(() => {
    if (selectedUser) loadJourney(selectedUser, runId)
  }, [selectedUser]) // eslint-disable-line react-hooks/exhaustive-deps

  // ── Derived data ──
  const interactions: InteractionPoint[] = journey?.interactions ?? []

  const masteryData = interactions.map(pt => ({
    ...pt,
    'HCIE Ensemble': pt.mastery_after,
    'Kalman':        pt.kalman_mastery_after ?? null,
    'Bayesian':      pt.bayesian_mastery_after ?? null,
  }))

  const jtData = interactions.map(pt => ({
    interaction_number: pt.interaction_number,
    challenge:   Math.max(0, pt.jt_challenge_contribution   ?? 0),
    uncertainty: Math.max(0, pt.jt_uncertainty_contribution ?? 0),
    delta_m:     Math.max(0, pt.jt_delta_m_contribution     ?? 0),
    zpd:         Math.max(0, pt.jt_zpd_contribution         ?? 0),
    transfer:    Math.max(0, pt.jt_transfer_contribution    ?? 0),
    prospective: Math.max(0, pt.jt_transfer_prospective_contribution ?? 0),
  }))

  const ensembleData = interactions.map(pt => {
    const wk = pt.ensemble_weight_kalman   ?? 0
    const wb = pt.ensemble_weight_bayesian ?? 0
    const wl = pt.ensemble_weight_lyapunov ?? 0
    const total = wk + wb + wl || 1
    return {
      interaction_number: pt.interaction_number,
      Kalman:   (wk / total) * 100,
      Bayesian: (wb / total) * 100,
      Lyapunov: (wl / total) * 100,
    }
  })

  const auc = journey?.window_auc
  const bktAll = auc?.bkt?.['all'] ?? SEALED.bkt_auc
  const hcieAll = auc?.hcie?.['all']
  const hcie5   = auc?.hcie?.['5']
  const hcie10  = auc?.hcie?.['10']
  const hcieDeltaAll = hcieAll != null ? hcieAll - bktAll : null

  // ─────────────────────────────────────────────────────────────────────────────

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: `${ui.space.xl}px ${ui.space.lg}px 64px` }}>

      {/* ── Header ── */}
      <Eyebrow color={ui.tone.info.fg}>{t('coldStartJourney.eyebrow')}</Eyebrow>
      <SectionTitle sub={t('coldStartJourney.heroSub')}>
        {t('coldStartJourney.heroTitle')}
      </SectionTitle>

      <Callout tone="warn" style={{ marginTop: ui.space.md, maxWidth: 800 }}>
        ⚠ <strong>{t('coldStartJourney.snapshotWarnTitle')}</strong> — {t('coldStartJourney.snapshotWarnBodyA')}
        {' '}(m₁≈0.143 → 0.95 {t('coldStartJourney.snapshotWarnCeiling')} 9; σ² {t('coldStartJourney.snapshotWarnNarrows')} 0.0099 {t('coldStartJourney.snapshotWarnByInt')} 20){' '}
        {t('coldStartJourney.snapshotWarnBodyB')} §4.1.1.1 / <code>/review/baselines</code> (S5).
      </Callout>

      {/* ── Section 1: Learner Selector ── */}
      <Panel style={{ marginTop: ui.space.lg, display: 'flex', alignItems: 'flex-end', gap: ui.space.md, flexWrap: 'wrap' }}>
        <div>
          <div style={{ fontSize: ui.font.size.xs, fontWeight: ui.font.weight.bold, textTransform: 'uppercase', letterSpacing: '0.07em', color: ui.color.muted, marginBottom: ui.space.xs }}>{t('coldStartJourney.labelUser')}</div>
          {loadingUsers ? (
            <div style={{ fontSize: ui.font.size.sm, color: ui.color.muted }}>{t('coldStartJourney.loadingUsers')}</div>
          ) : users.length === 0 ? (
            <div style={{ fontSize: ui.font.size.sm, color: ui.color.muted }}>{t('coldStartJourney.noColdStartUsers')}</div>
          ) : (
            <select
              value={selectedUser}
              onChange={e => setSelectedUser(e.target.value)}
              style={{ fontSize: ui.font.size.base, padding: '6px 10px', borderRadius: ui.radius.sm,
                       border: `1px solid ${ui.color.lineStrong}`, background: ui.color.surface,
                       color: ui.color.heading, cursor: 'pointer', minWidth: 260 }}
            >
              {users.map(u => (
                <option key={u.user_id} value={u.user_id}>
                  {u.user_id.length > 20 ? u.user_id.slice(0, 20) + '…' : u.user_id}
                  {' '}({u.n_interactions} {t('coldStartJourney.interactions')})
                </option>
              ))}
            </select>
          )}
        </div>

        <div>
          <div style={{ fontSize: ui.font.size.xs, fontWeight: ui.font.weight.bold, textTransform: 'uppercase', letterSpacing: '0.07em', color: ui.color.muted, marginBottom: ui.space.xs }}>{t('coldStartJourney.labelRunId')}</div>
          <input
            type="text"
            value={runId}
            onChange={e => setRunId(e.target.value)}
            placeholder={`${t('coldStartJourney.egPrefix')} fbf78cd9`}
            style={{ fontSize: ui.font.size.base, padding: '6px 10px', borderRadius: ui.radius.sm,
                     border: `1px solid ${ui.color.lineStrong}`, background: ui.color.surface,
                     color: ui.color.heading, minWidth: 200 }}
          />
        </div>

        <button
          style={{ fontSize: ui.font.size.base, fontWeight: ui.font.weight.bold, padding: '7px 18px',
                   borderRadius: ui.radius.sm, border: 'none', background: ui.tone.info.fg,
                   color: ui.color.surface, cursor: 'pointer' }}
          onClick={() => loadJourney(selectedUser, runId)}
          disabled={loadingJourney || !selectedUser}
        >
          {loadingJourney ? t('coldStartJourney.loadingShort') : t('coldStartJourney.loadJourney')}
        </button>
      </Panel>

      {/* ── Error / no-data fallback ── */}
      {noData && !loadingJourney && <div style={{ marginTop: ui.space.lg }}><FallbackPanel t={t} /></div>}

      {/* ── Journey content ── */}
      {journey && interactions.length > 0 && (
        <>
          {/* ── Section 2: Stat Cards ── */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: ui.space.md, marginTop: ui.space.lg }}>
            <Stat
              label={`${t('coldStartJourney.statTotalInteractions')} · ${t('coldStartJourney.statUser')} ${(journey.user_id ?? selectedUser).slice(0, 14)}…`}
              value={journey.n_interactions ?? interactions.length}
              tone="info"
            />
            <Stat
              label={`AUC ≤5 cold-start · ${hcie5 != null && bktAll ? `${((hcie5 - bktAll) >= 0 ? '+' : '')}${(hcie5 - bktAll).toFixed(3)} ${t('coldStartJourney.vsBkt')}` : t('coldStartJourney.bktRef') + ': ' + SEALED.bkt_auc.toFixed(3)}`}
              value={hcie5 != null ? hcie5.toFixed(3) : '—'}
              tone="ok"
            />
            <Stat
              label={`AUC ≤10${hcie10 != null && bktAll ? ` · ${((hcie10 - bktAll) >= 0 ? '+' : '')}${(hcie10 - bktAll).toFixed(3)} ${t('coldStartJourney.vsBkt')}` : ''}`}
              value={hcie10 != null ? hcie10.toFixed(3) : '—'}
              tone="ok"
            />
            <Stat
              label={`AUC (ALL) · BKT: ${bktAll.toFixed(3)}${hcieDeltaAll != null ? ` · ${t('coldStartJourney.delta')} ${(hcieDeltaAll >= 0 ? '+' : '') + hcieDeltaAll.toFixed(3)}` : ''}`}
              value={hcieAll != null ? hcieAll.toFixed(3) : '—'}
              tone={hcieDeltaAll != null && hcieDeltaAll >= 0 ? 'ok' : 'warn'}
            />
          </div>

          {/* ── Section 3: Mastery Curve (HERO) ── */}
          <Panel style={{ marginTop: ui.space.lg }}>
            <SectionTitle sub={t('coldStartJourney.masterySub')}>
              {t('coldStartJourney.masteryTitle')}
            </SectionTitle>
            <ResponsiveContainer width="100%" height={380}>
              <LineChart data={masteryData} margin={{ top: 12, right: 24, bottom: 18, left: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={ui.color.grid} vertical={false} />
                <XAxis
                  dataKey="interaction_number"
                  tick={{ fontSize: ui.font.size.sm, fill: ui.color.muted }}
                  stroke={ui.color.lineStrong}
                  tickLine={false}
                  label={{ value: t('coldStartJourney.axisInteractionNum'), position: 'insideBottom', offset: -10, fontSize: ui.font.size.sm, fill: ui.color.muted }}
                />
                <YAxis
                  domain={[0, 1]}
                  ticks={[0, 0.25, 0.5, 0.75, 1]}
                  tick={{ fontSize: ui.font.size.sm, fill: ui.color.muted }}
                  stroke={ui.color.lineStrong}
                  tickLine={false}
                  tickFormatter={v => v.toFixed(2)}
                  label={{ value: t('coldStartJourney.axisMastery'), angle: -90, position: 'insideLeft', offset: 18, fontSize: ui.font.size.sm, fill: ui.color.muted }}
                />
                <Tooltip content={(props: any) => <MasteryTooltip {...props} t={t} />} cursor={{ stroke: ui.color.lineStrong, strokeDasharray: '3 3' }} />
                <Legend wrapperStyle={{ fontSize: ui.font.size.sm, paddingTop: 12 }} iconType="plainline" />
                <ReferenceLine
                  y={0.5}
                  stroke={ui.color.muted}
                  strokeDasharray="5 3"
                  label={{ value: t('coldStartJourney.thresholdLabel'), fill: ui.color.faint, fontSize: ui.font.size.xs, position: 'right' }}
                />
                <Line
                  type="monotone"
                  dataKey="HCIE Ensemble"
                  stroke={MASTERY_COLORS.ensemble}
                  strokeWidth={3}
                  dot={(props: any) => {
                    const d = props.payload as InteractionPoint
                    return (
                      <circle
                        key={`dot-${d.interaction_number}`}
                        cx={props.cx}
                        cy={props.cy}
                        r={4}
                        fill={d.correctness ? ui.tone.ok.fg : ui.tone.bad.fg}
                        stroke={ui.color.surface}
                        strokeWidth={1.5}
                      />
                    )
                  }}
                  activeDot={{ r: 6 }}
                  isAnimationActive={false}
                />
                <Line
                  type="monotone"
                  dataKey="Kalman"
                  stroke={MASTERY_COLORS.kalman}
                  strokeWidth={1.5}
                  strokeDasharray="4 2"
                  dot={false}
                  connectNulls
                  isAnimationActive={false}
                />
                <Line
                  type="monotone"
                  dataKey="Bayesian"
                  stroke={MASTERY_COLORS.bayesian}
                  strokeWidth={1.5}
                  strokeDasharray="2 4"
                  dot={false}
                  connectNulls
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </Panel>

          {/* ── Section 4: JT 6D Attribution ── */}
          <Panel style={{ marginTop: ui.space.lg }}>
            <SectionTitle sub={t('coldStartJourney.jtSub')}>
              {t('coldStartJourney.jtTitle')}
            </SectionTitle>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={jtData} margin={{ top: 8, right: 24, bottom: 18, left: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={ui.color.grid} vertical={false} />
                <XAxis
                  dataKey="interaction_number"
                  tick={{ fontSize: ui.font.size.sm, fill: ui.color.muted }}
                  stroke={ui.color.lineStrong}
                  tickLine={false}
                  label={{ value: t('coldStartJourney.axisInteractionNum'), position: 'insideBottom', offset: -10, fontSize: ui.font.size.sm, fill: ui.color.muted }}
                />
                <YAxis
                  tick={{ fontSize: ui.font.size.sm, fill: ui.color.muted }}
                  stroke={ui.color.lineStrong}
                  tickLine={false}
                  tickFormatter={v => v.toFixed(2)}
                  label={{ value: t('coldStartJourney.axisJtScore'), angle: -90, position: 'insideLeft', offset: 18, fontSize: ui.font.size.sm, fill: ui.color.muted }}
                />
                <Tooltip
                  cursor={{ fill: ui.color.grid }}
                  contentStyle={{ fontSize: ui.font.size.sm, borderRadius: ui.radius.md, border: `1px solid ${ui.color.line}` }}
                  formatter={(v: any, name: any) => [Number(v).toFixed(4), name]}
                />
                <Legend wrapperStyle={{ fontSize: ui.font.size.sm, paddingTop: 10 }} />
                {JT_DIMS.map((dim, i) => (
                  <Bar
                    key={dim}
                    dataKey={dim}
                    stackId="jt"
                    fill={JT_COLORS[dim]}
                    radius={i === JT_DIMS.length - 1 ? [3, 3, 0, 0] : undefined}
                    isAnimationActive={false}
                  />
                ))}
              </BarChart>
            </ResponsiveContainer>

            {/* Dimension legend */}
            <div style={{ display: 'flex', gap: ui.space.md, flexWrap: 'wrap', marginTop: ui.space.md }}>
              {JT_DIMS.map(dim => (
                <div key={dim} style={{ display: 'flex', alignItems: 'center', gap: ui.space.xs, fontSize: ui.font.size.sm }}>
                  <div style={{ width: 12, height: 12, borderRadius: 2, background: JT_COLORS[dim] }} />
                  <span style={{ color: ui.color.body, fontWeight: ui.font.weight.medium }}>{dim}</span>
                </div>
              ))}
            </div>

            <Callout tone="info" style={{ marginTop: ui.space.md }}>
              {t('coldStartJourney.jtCalloutA')}{' '}
              (challenge=0.158, uncertainty=0.119, delta_m=0.083).{' '}
              {t('coldStartJourney.jtCalloutB')}
            </Callout>
          </Panel>

          {/* ── Section 5: Ensemble Weight Evolution ── */}
          {ensembleData.some(d => d.Kalman > 0 || d.Bayesian > 0) && (
            <Panel style={{ marginTop: ui.space.lg }}>
              <SectionTitle sub={t('coldStartJourney.ensembleSub')}>
                {t('coldStartJourney.ensembleTitle')}
              </SectionTitle>
              <ResponsiveContainer width="100%" height={220}>
                <AreaChart data={ensembleData} margin={{ top: 8, right: 24, bottom: 18, left: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={ui.color.grid} vertical={false} />
                  <XAxis
                    dataKey="interaction_number"
                    tick={{ fontSize: ui.font.size.sm, fill: ui.color.muted }}
                    stroke={ui.color.lineStrong}
                    tickLine={false}
                    label={{ value: t('coldStartJourney.axisInteractionNum'), position: 'insideBottom', offset: -10, fontSize: ui.font.size.sm, fill: ui.color.muted }}
                  />
                  <YAxis
                    tick={{ fontSize: ui.font.size.sm, fill: ui.color.muted }}
                    stroke={ui.color.lineStrong}
                    tickLine={false}
                    tickFormatter={v => `${v.toFixed(0)}%`}
                    domain={[0, 100]}
                  />
                  <Tooltip
                    cursor={{ stroke: ui.color.lineStrong, strokeDasharray: '3 3' }}
                    contentStyle={{ fontSize: ui.font.size.sm, borderRadius: ui.radius.md, border: `1px solid ${ui.color.line}` }}
                    formatter={(v: any, name: any) => [`${Number(v).toFixed(1)}%`, name]}
                  />
                  <Legend wrapperStyle={{ fontSize: ui.font.size.sm, paddingTop: 10 }} />
                  <Area type="monotone" dataKey="Kalman"   stackId="w" stroke={MASTERY_COLORS.ensemble} fill={`${MASTERY_COLORS.ensemble}33`} isAnimationActive={false} />
                  <Area type="monotone" dataKey="Bayesian" stackId="w" stroke={MASTERY_COLORS.bayesian} fill={`${MASTERY_COLORS.bayesian}33`} isAnimationActive={false} />
                  <Area type="monotone" dataKey="Lyapunov" stackId="w" stroke={ui.color.faint} fill={`${ui.color.faint}22`} isAnimationActive={false} />
                </AreaChart>
              </ResponsiveContainer>
              <Callout tone="neutral" style={{ marginTop: ui.space.md }}>
                {t('coldStartJourney.ensembleCalloutA')} (HCIE_FUSION_CUT_LYAPUNOV=1).
                {' '}Kalman r={SEALED.kalman_corr} {t('coldStartJourney.ensembleCalloutBestPredictor')}; Bayesian corr={SEALED.bayesian_corr} {t('coldStartJourney.ensembleCalloutWith')}
                {' '}BoundedStability ({t('coldStartJourney.ensembleCalloutRedundancy')}). {t('coldStartJourney.ensembleSub')}
              </Callout>
            </Panel>
          )}

          {/* ── Section 6: ADC Status ── */}
          <Panel style={{ marginTop: ui.space.lg }}>
            <SectionTitle>{t('coldStartJourney.adcStatusTitle')}</SectionTitle>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(230px, 1fr))', gap: ui.space.sm }}>
              {JT_DIMS.map(dim => {
                const info = SEALED.jt_means[dim]
                return (
                  <Panel key={dim} pad="md" tone="neutral">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: ui.space.sm }}>
                      <span style={{ fontSize: ui.font.size.md, fontWeight: ui.font.weight.bold, color: JT_COLORS[dim] }}>{dim}</span>
                      {adcBadge(info.status)}
                    </div>
                    <div style={{ fontSize: ui.font.size.sm, color: ui.color.body, lineHeight: 1.7 }}>
                      <div>mean = <strong>{info.mean.toFixed(3)}</strong></div>
                      <div>signal_ratio = <strong>{info.signal_ratio.toFixed(2)}</strong></div>
                    </div>
                  </Panel>
                )
              })}
            </div>
            <Callout tone="info" style={{ marginTop: ui.space.md }}>
              {t('coldStartJourney.adcCalloutA')}
              {' '}(floor artifact confirmed by shuffled-DAG control, p=5e-5, +0.020).
              {' '}{t('coldStartJourney.adcCalloutB')} (mean=0.015).
            </Callout>
          </Panel>

          {/* ── Section 7: Provenance Footer ── */}
          <div style={{ marginTop: ui.space.lg }}>
            <ProvenanceBadge
              source={journey?.run_id ? 'live_db' : 'frozen'}
              generatedAt={new Date().toISOString()}
              runId={journey?.run_id ?? SEALED.seal}
              n={journey?.n_interactions ?? interactions.length}
              note={`${t('coldStartJourney.provSealedRun')} N=${SEALED.n.toLocaleString()} · seal-${SEALED.seal} · AUC HCIE ${SEALED.hcie_auc} BKT ${SEALED.bkt_auc} DKT ${SEALED.dkt_auc} · ${t('coldStartJourney.provDeployed2Learner')} (Kalman+Bayesian) ${SEALED.date}`}
            />
          </div>
          <div style={{ fontSize: ui.font.size.xs, color: ui.color.faint, marginTop: ui.space.xs, marginBottom: ui.space.lg }}>
            {t('coldStartJourney.sourceLabel')}: experiment_trajectories {t('coldStartJourney.via')} GET /v3/frontend/dashboard/cold-start-journey
          </div>
        </>
      )}

      {/* ── Loading state ── */}
      {loadingJourney && (
        <Panel style={{ marginTop: ui.space.lg, textAlign: 'center', padding: 40, color: ui.color.muted, fontSize: ui.font.size.md }}>
          {t('coldStartJourney.loadingJourneyData')}
        </Panel>
      )}

      {/* ── Footer nav ── */}
      <div style={{ display: 'flex', gap: ui.space.md, marginTop: ui.space.xxl, justifyContent: 'center', flexWrap: 'wrap' }}>
        <Link href="/dashboard" style={{ fontSize: ui.font.size.md, fontWeight: ui.font.weight.medium, color: ui.color.body,
          textDecoration: 'none', padding: '10px 24px', borderRadius: ui.radius.md,
          border: `1px solid ${ui.color.lineStrong}`, background: ui.color.surface }}>
          ← {t('coldStartJourney.navDashboard')}
        </Link>
        <Link href="/dashboard/learner-journey" style={{ fontSize: ui.font.size.md, fontWeight: ui.font.weight.bold, color: ui.tone.info.fg,
          textDecoration: 'none', padding: '10px 24px', borderRadius: ui.radius.md,
          border: `1px solid ${ui.tone.info.border}`, background: ui.tone.info.bg }}>
          {t('coldStartJourney.navLearnerJourney')} →
        </Link>
        <Link href="/review" style={{ fontSize: ui.font.size.md, fontWeight: ui.font.weight.bold, color: ui.tone.accent.fg,
          textDecoration: 'none', padding: '10px 24px', borderRadius: ui.radius.md,
          border: `1px solid ${ui.tone.accent.border}`, background: ui.tone.accent.bg }}>
          {t('coldStartJourney.navReviewPortal')} →
        </Link>
      </div>
    </div>
  )
}
