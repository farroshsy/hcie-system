'use client'

import { useEffect, useState } from 'react'
import ProvenanceBadge, { type ProvenanceSource } from '@/components/review/ProvenanceBadge'
import ProvisionalBanner from '@/components/review/ProvisionalBanner'
import { NextSteps } from '@/components/review/NextSteps'
import { getBackendUrl } from '@/lib/api/backend-url'
import { useT } from '@/contexts/language_context'
import { Panel, Callout, Eyebrow } from '@/lib/ui/primitives'
import { t as ui } from '@/lib/ui/theme'  // aliased: `t` is taken by useT() (translations)

type JTAttr = {
  zpd: number
  delta_m: number
  challenge: number
  uncertainty: number
  transfer_realized: number
  transfer_prospective: number
}

type Interaction = {
  interaction_number: number
  concept: string
  mastery_before: number | null
  mastery_after: number
  correct: boolean
  jt_value: number
  jt_transfer_contribution: number
  jt_delta_m_contribution: number
  jt_challenge_contribution: number
  jt_uncertainty_contribution: number
  jt_zpd_contribution: number
  transfer_amount_raw: number
  transfer_amounts_json: Record<string, number>
  jt_attribution: JTAttr
  event_id: string
}

type TraceData = {
  generated_at?: string
  run_id?: string
  user_short?: string
  n_interactions: number
  n_transfer_active: number
  dag_edges_division4?: Array<{ source: string; target: string; weight: number }>
  trace: Interaction[]
}

const TRANSFER_THRESHOLD = 0.08

function isTransferActive(ix: Interaction) {
  return ix.jt_transfer_contribution > TRANSFER_THRESHOLD
}

function shortConcept(c: string) {
  return c.replace(/^ext_junyi_graph_/, '').replace(/_/g, ' ')
}

function Bar({ value, max, color }: { value: number; max: number; color: string }) {
  const pct = max > 0 ? Math.min(100, (value / max) * 100) : 0
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
      <div style={{ flex: 1, height: 6, background: ui.color.line, borderRadius: 3, overflow: 'hidden' }}>
        <div style={{ width: `${pct}%`, height: '100%', background: color, borderRadius: 3,
                      transition: 'width 0.3s' }} />
      </div>
      <span style={{ fontSize: ui.font.size.xs, color: ui.color.body, minWidth: 36, textAlign: 'right',
                     fontVariantNumeric: 'tabular-nums' }}>
        {(value * 100).toFixed(1)}%
      </span>
    </div>
  )
}

export default function TracePage() {
  const t = useT()
  const [data, setData] = useState<TraceData | null>(null)
  const [selected, setSelected] = useState<number>(25)
  const [dataSource, setDataSource] = useState<ProvenanceSource>('loading')

  useEffect(() => {
    // P4-3: prefer the live /v3/review/trace endpoint (recompute from the DB);
    // fall back to the sealed static export when the backend is unreachable.
    const BACKEND = getBackendUrl()
    const tryLive = BACKEND
      ? fetch(`${BACKEND}/v3/review/trace`, { signal: AbortSignal.timeout(4000) })
          .then(r => r.ok ? r.json() : Promise.reject(r.status))
      : Promise.reject('no backend configured')

    tryLive
      .then(d => { setData(d); setDataSource('live_db') })
      .catch(() =>
        fetch('/data/adc/governance_trace.json')
          .then(r => r.json())
          .then(d => { setData(d); setDataSource('frozen') })
      )
  }, [])

  const trace = data?.trace ?? []
  const sel = trace.find(ix => ix.interaction_number === selected)

  const maxTransfer = Math.max(...trace.map(ix => ix.jt_transfer_contribution), 0.001)

  return (
    <div style={{ padding: '32px 40px', maxWidth: 1100 }}>
      <div style={{ marginBottom: ui.space.xxl }}>
        <Eyebrow color="#6A1E55">{t('traceReview.eyebrow')}</Eyebrow>
        <h1 style={{ fontSize: ui.font.size.h2, fontWeight: ui.font.weight.heavy, color: ui.color.ink, marginBottom: ui.space.sm }}>
          {t('traceReview.heroTitle')} ex_junyi_graph_135350
        </h1>
        <p style={{ fontSize: ui.font.size.md, color: ui.color.body, lineHeight: 1.6, maxWidth: 700 }}>
          {trace.length} {t('traceReview.heroIntroA')}{' '}
          <strong>3.3% → 25.6%</strong> {t('traceReview.heroIntroB')}
        </p>
        <Callout tone="warn" style={{ lineHeight: 1.5, maxWidth: 700, marginTop: ui.space.sm }}>
          <strong>{t('traceReview.calloutTitle')}</strong> {t('traceReview.calloutBodyA')}{' '}
          {trace.filter(i => i.jt_transfer_contribution > 0.03).length}/{trace.length} {t('traceReview.calloutBodyB')}{' '}
          {trace.filter(i => i.jt_transfer_contribution > TRANSFER_THRESHOLD).length}/{trace.length} {t('traceReview.calloutBodyC')}{' '}
          {TRANSFER_THRESHOLD} {t('traceReview.calloutBodyD')}
        </Callout>
      </div>

      <ProvisionalBanner
        tone="partial"
        headline={t('traceReview.bannerHeadline')}
        body={<>{t('traceReview.bannerBody')}</>}
        flipsAfter={[
          t('traceReview.bannerFlip1'),
          t('traceReview.bannerFlip2'),
        ]}
      />

      <ProvenanceBadge
        source={dataSource}
        generatedAt={data?.generated_at}
        runId={data?.run_id}
        n={data?.n_interactions ?? (trace.length || null)}
      />

      <div style={{ display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
                    gap: 24 }}>
        {/* Grid */}
        <div>
          <div style={{ display: 'flex', gap: ui.space.md, marginBottom: ui.space.lg, fontSize: ui.font.size.sm, color: ui.color.muted }}>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
              <span style={{ width: 12, height: 12, borderRadius: 2, background: '#2ECC71', display: 'inline-block' }} />
              {t('traceReview.legendActive')}
            </span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
              <span style={{ width: 12, height: 12, borderRadius: 2, background: ui.color.line, display: 'inline-block' }} />
              {t('traceReview.legendStructuralZero')}
            </span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
              <span style={{ width: 12, height: 12, borderRadius: 2, background: '#1A5276', display: 'inline-block' }} />
              {t('traceReview.legendSelected')}
            </span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(10, 1fr)', gap: 3 }}>
            {trace.map(ix => {
              const active = isTransferActive(ix)
              const isSelected = ix.interaction_number === selected
              const is25 = ix.interaction_number === 25
              const intensity = Math.min(1, ix.jt_transfer_contribution / 0.25)
              const green = Math.round(46 + intensity * 159)
              const bgColor = isSelected
                ? '#1A5276'
                : active
                  ? `rgb(${Math.round(46 * (1 - intensity))}, ${green}, ${Math.round(113 * (1 - intensity))})`
                  : '#E8ECF0'
              return (
                <button key={ix.interaction_number} onClick={() => setSelected(ix.interaction_number)}
                  title={`#${ix.interaction_number}: ${shortConcept(ix.concept)}`}
                  style={{
                    aspectRatio: '1', border: is25 ? '2px solid #C0392B' : isSelected ? '2px solid #1A5276' : '1px solid #D1D8E0',
                    borderRadius: 4, background: bgColor, cursor: 'pointer',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 8, color: isSelected || active ? '#FFFFFF' : '#718096',
                    fontWeight: is25 ? 700 : 400,
                    transition: 'transform 0.1s',
                    position: 'relative',
                  }}>
                  {ix.interaction_number}
                  {is25 && (
                    <span style={{
                      position: 'absolute', top: -8, right: -4, fontSize: 8,
                      background: '#C0392B', color: '#FFF', borderRadius: 4,
                      padding: '0 3px', fontWeight: 700, lineHeight: 1.5,
                    }}>8×</span>
                  )}
                </button>
              )
            })}
          </div>
          {trace.length === 0 && (
            <div style={{ color: ui.color.muted, fontSize: ui.font.size.lg, padding: ui.space.xl }}>{t('traceReview.loading')}</div>
          )}

          {/* Mastery timeline mini-chart */}
          {trace.length > 0 && (
            <div style={{ marginTop: ui.space.xl }}>
              <div style={{ fontSize: ui.font.size.sm, fontWeight: ui.font.weight.medium, color: ui.color.body, marginBottom: ui.space.xs }}>
                {t('traceReview.masteryTrajectory')}
              </div>
              <svg width="100%" height={60} style={{ overflow: 'visible' }}>
                {trace.map((ix, i) => {
                  const x = (i / (trace.length - 1)) * 100
                  const y = ix.mastery_after != null ? (1 - ix.mastery_after) * 50 + 5 : 30
                  return (
                    <circle key={ix.interaction_number}
                      cx={`${x}%`} cy={y} r={ix.interaction_number === 25 ? 4 : 2}
                      fill={ix.interaction_number === selected ? '#1A5276'
                             : isTransferActive(ix) ? '#2ECC71' : '#CBD5E0'}
                      stroke={ix.interaction_number === 25 ? '#C0392B' : 'none'}
                      strokeWidth={2}
                    />
                  )
                })}
              </svg>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: ui.font.size.xs, color: ui.color.faint }}>
                <span>{t('traceReview.axisInteraction1')}</span>
                <span>100</span>
              </div>
            </div>
          )}
        </div>

        {/* Detail panel */}
        <Panel style={{ padding: ui.space.xl, alignSelf: 'start', position: 'sticky', top: 24 }}>
          {sel ? (
            <>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: ui.space.md }}>
                <div>
                  <div style={{ fontSize: ui.font.size.sm, color: ui.color.muted, fontWeight: ui.font.weight.medium, marginBottom: 2 }}>
                    {t('traceReview.interactionLabel')} #{sel.interaction_number}
                    {sel.interaction_number === 25 && (
                      <span style={{ marginLeft: 6, fontSize: ui.font.size.xs, background: '#FADBD8', color: '#C0392B',
                                     fontWeight: ui.font.weight.bold, padding: '1px 6px', borderRadius: ui.radius.sm }}>
                        {t('traceReview.activationEvent')}
                      </span>
                    )}
                  </div>
                  <div style={{ fontSize: ui.font.size.lg, fontWeight: ui.font.weight.bold, color: ui.color.ink }}>
                    {shortConcept(sel.concept)}
                  </div>
                </div>
                <span style={{ fontSize: ui.font.size.lg }}>{sel.correct ? '✓' : '✗'}</span>
              </div>

              <div style={{ display: 'grid',
                            gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
                            gap: 8, marginBottom: 14 }}>
                {[
                  [t('traceReview.metricMasteryBefore'), sel.mastery_before != null ? sel.mastery_before.toFixed(3) : '—'],
                  [t('traceReview.metricMasteryAfter'), sel.mastery_after.toFixed(3)],
                  [t('traceReview.metricJtValue'), sel.jt_value.toFixed(4)],
                  [t('traceReview.metricTransferRaw'), sel.transfer_amount_raw.toFixed(4)],
                ].map(([k, v]) => (
                  <div key={k} style={{ background: '#F7FAFC', borderRadius: ui.radius.sm, padding: '6px 10px' }}>
                    <div style={{ fontSize: ui.font.size.xs, color: ui.color.muted }}>{k}</div>
                    <div style={{ fontSize: ui.font.size.md, fontWeight: ui.font.weight.bold, color: '#2D3748', fontVariantNumeric: 'tabular-nums' }}>{v}</div>
                  </div>
                ))}
              </div>

              <div style={{ fontSize: ui.font.size.sm, fontWeight: ui.font.weight.bold, color: ui.color.body, marginBottom: ui.space.sm }}>
                {t('traceReview.jtBreakdownTitle')}
              </div>
              {([
                [t('traceReview.attrTransferRealized'), sel.jt_attribution?.transfer_realized ?? 0, '#C0392B'],
                [t('traceReview.attrDeltaMastery'), sel.jt_attribution?.delta_m ?? 0, '#2980B9'],
                [t('traceReview.attrChallenge'), sel.jt_attribution?.challenge ?? 0, '#8E44AD'],
                [t('traceReview.attrUncertainty'), sel.jt_attribution?.uncertainty ?? 0, '#D35400'],
                ['ZPD', sel.jt_attribution?.zpd ?? 0, '#27AE60'],
                [t('traceReview.attrTransferProspective'), sel.jt_attribution?.transfer_prospective ?? 0, '#7F8C8D'],
              ] as [string, number, string][]).map(([k, v, color]) => (
                <div key={k} style={{ marginBottom: 5 }}>
                  <div style={{ fontSize: ui.font.size.xs, color: ui.color.muted, marginBottom: 2 }}>{k}</div>
                  <Bar value={v} max={0.25} color={color} />
                </div>
              ))}

              {Object.keys(sel.transfer_amounts_json ?? {}).filter(k => k !== 'total_transfer').length > 0 && (
                <>
                  <div style={{ fontSize: ui.font.size.sm, fontWeight: ui.font.weight.bold, color: ui.color.body, marginTop: ui.space.md, marginBottom: ui.space.xs }}>
                    {t('traceReview.transferTargets')}
                  </div>
                  {Object.entries(sel.transfer_amounts_json ?? {})
                    .filter(([k]) => k !== 'total_transfer')
                    .map(([k, v]) => (
                      <div key={k} style={{ display: 'flex', justifyContent: 'space-between',
                                            fontSize: ui.font.size.sm, color: ui.color.body, marginBottom: 3 }}>
                        <span>{shortConcept(k)}</span>
                        <span style={{ fontVariantNumeric: 'tabular-nums', color: '#C0392B', fontWeight: ui.font.weight.medium }}>
                          {(v as number).toFixed(4)}
                        </span>
                      </div>
                    ))
                  }
                </>
              )}
            </>
          ) : (
            <div style={{ color: ui.color.muted, fontSize: ui.font.size.md }}>{t('traceReview.clickToInspect')}</div>
          )}
        </Panel>
      </div>

      <NextSteps />
    </div>
  )
}
