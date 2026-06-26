'use client'

import { useEffect, useState } from 'react'
import { getBackendUrl } from '@/lib/api/backend-url'
import { useT } from '@/contexts/language_context'
import { Panel, Eyebrow } from '@/lib/ui/primitives'
import { t as ui } from '@/lib/ui/theme'  // aliased: `t` is taken by useT() (translations)
import { NextSteps } from '@/components/review/NextSteps'

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
  jt_attribution: JTAttr
  transfer_amount_raw: number
  transfer_amounts_json: Record<string, number>
  event_id: string
}

type TraceData = {
  user_short?: string
  user_id?: string
  run_id: string
  n_interactions: number
  dag_edges_division4?: Array<{ source: string; target: string; weight: number }>
  trace: Interaction[]
  source?: 'live_db' | 'static'
}

function shortConcept(c: string) {
  return c.replace(/^ext_junyi_graph_/, '').replace(/_/g, ' ')
}

// Display text (label/desc) is keyed and resolved via t() inside the component;
// id/color stay here because they are not user-facing copy.
const PIPELINE_STAGES = [
  { id: 'event',     labelKey: 'stageEventLabel',      descKey: 'stageEventDesc',      color: '#2980B9' },
  { id: 'dag',       labelKey: 'stageDagLabel',        descKey: 'stageDagDesc',        color: '#8E44AD' },
  { id: 'jt',        labelKey: 'stageJtLabel',         descKey: 'stageJtDesc',         color: '#C0392B' },
  { id: 'mastery',   labelKey: 'stageMasteryLabel',    descKey: 'stageMasteryDesc',    color: '#1E8449' },
  { id: 'projection',labelKey: 'stageProjectionLabel', descKey: 'stageProjectionDesc', color: '#D35400' },
]

function PipelineNode({ stage, active, value, t }: {
  stage: typeof PIPELINE_STAGES[number]
  active: boolean
  value?: string
  t: (key: string, fallback?: string) => string
}) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4, minWidth: 120 }}>
      <div style={{
        width: 44, height: 44, borderRadius: '50%',
        background: active ? stage.color : ui.color.line,
        border: `2px solid ${active ? stage.color : ui.color.lineStrong}`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        transition: 'all 0.3s',
      }}>
        <span style={{ fontSize: ui.font.size.xl, color: active ? '#FFF' : ui.color.faint }}>
          {stage.id === 'event' ? '⚡' : stage.id === 'dag' ? '⬡' : stage.id === 'jt' ? '∑' :
           stage.id === 'mastery' ? '▲' : '◉'}
        </span>
      </div>
      <div style={{ fontSize: ui.font.size.sm, fontWeight: ui.font.weight.bold, color: active ? stage.color : ui.color.faint,
                    textAlign: 'center', lineHeight: 1.3 }}>
        {t(`replayReview.${stage.labelKey}`)}
      </div>
      {value && (
        <div style={{ fontSize: ui.font.size.xs, color: ui.color.body, textAlign: 'center',
                      background: '#F7FAFC', padding: '2px 6px', borderRadius: ui.radius.sm,
                      border: `1px solid ${ui.color.line}`, fontVariantNumeric: 'tabular-nums' }}>
          {value}
        </div>
      )}
      <div style={{ fontSize: ui.font.size.xs, color: ui.color.faint, textAlign: 'center', maxWidth: 110, lineHeight: 1.3 }}>
        {t(`replayReview.${stage.descKey}`)}
      </div>
    </div>
  )
}

function Arrow({ active }: { active: boolean }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', marginTop: -30 }}>
      <div style={{
        width: 32, height: 2,
        background: active ? '#64B5F6' : ui.color.line,
        transition: 'background 0.3s',
      }} />
      <div style={{
        borderLeft: `8px solid ${active ? '#64B5F6' : ui.color.line}`,
        borderTop: '5px solid transparent',
        borderBottom: '5px solid transparent',
        transition: 'border-color 0.3s',
      }} />
    </div>
  )
}

export default function ReplayPage() {
  const t = useT()
  const [data, setData] = useState<TraceData | null>(null)
  const [selectedIx, setSelectedIx] = useState(25)
  const [animStep, setAnimStep] = useState(5)

  const [dataSource, setDataSource] = useState<'live_db' | 'static' | 'loading'>('loading')

  useEffect(() => {
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
          .then(d => { setData(d); setDataSource('static') })
      )
  }, [])

  useEffect(() => {
    setAnimStep(0)
    const timer = setInterval(() => {
      setAnimStep(s => {
        if (s >= PIPELINE_STAGES.length - 1) { clearInterval(timer); return s }
        return s + 1
      })
    }, 400)
    return () => clearInterval(timer)
  }, [selectedIx])

  const trace = data?.trace ?? []
  const ix = trace.find(t => t.interaction_number === selectedIx)

  const stageValues: Record<string, string> = ix ? {
    event: `#${ix.interaction_number} · ${shortConcept(ix.concept)} · ${ix.correct ? t('replayReview.outcomeCorrect') : t('replayReview.outcomeWrong')}`,
    dag: Object.keys(ix.transfer_amounts_json ?? {}).filter(k => k !== 'total_transfer').length > 0
      ? `${Object.keys(ix.transfer_amounts_json).filter(k => k !== 'total_transfer').length} ${t('replayReview.dagEdgesResolved')}`
      : t('replayReview.dagNoEdges'),
    jt: `JT = ${ix.jt_value.toFixed(4)} · T_realized = ${(ix.jt_transfer_contribution * 100).toFixed(1)}%`,
    mastery: `${ix.mastery_before?.toFixed(3) ?? '—'} → ${ix.mastery_after.toFixed(3)}`,
    projection: `mastery_before ${t('replayReview.projectionStored')} = ${ix.mastery_after.toFixed(3)} (${t('replayReview.projectionNextPrior')})`,
  } : {}

  return (
    <div style={{ padding: '32px 40px', maxWidth: 1000 }}>
      <div style={{ marginBottom: ui.space.xxl }}>
        <Eyebrow color="#4A235A">{t('replayReview.eyebrow')}</Eyebrow>
        <h1 style={{ fontSize: ui.font.size.h2, fontWeight: ui.font.weight.heavy, color: ui.color.ink, marginBottom: ui.space.sm }}>
          {t('replayReview.heroTitle')}
        </h1>
        <p style={{ fontSize: ui.font.size.md, color: ui.color.body, lineHeight: 1.6, maxWidth: 700 }}>
          {t('replayReview.intro')}
        </p>
      </div>

      {/* Interaction selector */}
      <div style={{ display: 'flex', alignItems: 'center', gap: ui.space.sm, marginBottom: ui.space.xxl, flexWrap: 'wrap' }}>
        <span style={{ fontSize: ui.font.size.md, fontWeight: ui.font.weight.medium, color: ui.color.body, whiteSpace: 'nowrap' }}>{t('replayReview.interactionLabel')}</span>
        <input type="range" min={1} max={100} value={selectedIx}
          onChange={e => setSelectedIx(Number(e.target.value))}
          aria-label={t('replayReview.interactionSliderAria')}
          style={{ width: 200, accentColor: '#1A5276', flexShrink: 0 }}
        />
        <span style={{ fontSize: ui.font.size.lg, fontWeight: ui.font.weight.bold, color: '#1A5276', minWidth: 28 }}>{selectedIx}</span>
        <div style={{ display: 'flex', gap: ui.space.xs, flexWrap: 'wrap' }}>
          {[1, 25, 30, 50, 100].map(n => (
            <button key={n} onClick={() => setSelectedIx(n)}
              style={{
                padding: '3px 10px', borderRadius: ui.radius.sm, border: 'none', cursor: 'pointer',
                fontSize: ui.font.size.sm, fontWeight: ui.font.weight.medium,
                background: selectedIx === n
                  ? (n === 25 ? '#C0392B' : n === 30 ? '#E67E22' : '#1A5276')
                  : ui.color.line,
                color: selectedIx === n ? '#FFF' : ui.color.body,
              }}>
              {n === 25 ? '25 ★' : n === 30 ? '30 ▼' : n}
            </button>
          ))}
        </div>
        {selectedIx === 25 && (
          <span style={{ fontSize: ui.font.size.sm, fontWeight: ui.font.weight.bold, color: '#C0392B', background: '#FADBD8',
                         padding: '2px 8px', borderRadius: ui.radius.sm, whiteSpace: 'nowrap' }}>
            8× {t('replayReview.badgeActivation')}
          </span>
        )}
        {selectedIx === 30 && (
          <span style={{ fontSize: ui.font.size.sm, fontWeight: ui.font.weight.bold, color: '#E67E22', background: '#FDEBD0',
                         padding: '2px 8px', borderRadius: ui.radius.sm, whiteSpace: 'nowrap' }}>
            {t('replayReview.badgeDeactivation')}
          </span>
        )}
      </div>

      {/* Pipeline visualization */}
      <Panel style={{ padding: '28px 24px', marginBottom: ui.space.xl }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 0, overflowX: 'auto', paddingBottom: 8 }}>
          {PIPELINE_STAGES.map((stage, i) => (
            <div key={stage.id} style={{ display: 'flex', alignItems: 'flex-start' }}>
              <PipelineNode
                stage={stage}
                active={i <= animStep}
                value={i <= animStep ? stageValues[stage.id] : undefined}
                t={t}
              />
              {i < PIPELINE_STAGES.length - 1 && <Arrow active={i < animStep} />}
            </div>
          ))}
        </div>
      </Panel>

      {/* JT Attribution detail */}
      {ix && (
        <div style={{ display: 'grid',
                      gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
                      gap: ui.space.lg }}>
          <Panel style={{ padding: ui.space.lg }}>
            <div style={{ fontSize: ui.font.size.base, fontWeight: ui.font.weight.bold, color: ui.color.body, marginBottom: ui.space.sm }}>
              {t('replayReview.jtPanelTitle')} — Interaction #{ix.interaction_number}
            </div>
            {([
              [t('replayReview.dimTransferRealized'), ix.jt_attribution?.transfer_realized ?? 0, '#C0392B'],
              [t('replayReview.dimDeltaMastery'), ix.jt_attribution?.delta_m ?? 0, '#2980B9'],
              [t('replayReview.dimChallenge'), ix.jt_attribution?.challenge ?? 0, '#8E44AD'],
              [t('replayReview.dimUncertainty'), ix.jt_attribution?.uncertainty ?? 0, '#D35400'],
              ['ZPD', ix.jt_attribution?.zpd ?? 0, '#27AE60'],
            ] as [string, number, string][]).map(([k, v, color]) => {
              const total = Object.values(ix.jt_attribution ?? {}).reduce((s, x) => s + x, 0)
              const pct = total > 0 ? (v / total) * 100 : 0
              return (
                <div key={k} style={{ marginBottom: ui.space.sm }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: ui.font.size.sm, marginBottom: 2 }}>
                    <span style={{ color: ui.color.body }}>{k}</span>
                    <span style={{ color, fontWeight: ui.font.weight.bold, fontVariantNumeric: 'tabular-nums' }}>
                      {v.toFixed(4)} ({pct.toFixed(0)}%)
                    </span>
                  </div>
                  <div style={{ height: 5, background: ui.color.line, borderRadius: 3, overflow: 'hidden' }}>
                    <div style={{ width: `${pct}%`, height: '100%', background: color, borderRadius: 3 }} />
                  </div>
                </div>
              )
            })}
          </Panel>

          <Panel style={{ padding: ui.space.lg }}>
            <div style={{ fontSize: ui.font.size.base, fontWeight: ui.font.weight.bold, color: ui.color.body, marginBottom: ui.space.sm }}>
              {t('replayReview.substratesTitle')}
            </div>
            {Object.entries(ix.transfer_amounts_json ?? {})
              .filter(([k]) => k !== 'total_transfer')
              .length > 0 ? (
                Object.entries(ix.transfer_amounts_json ?? {})
                  .filter(([k]) => k !== 'total_transfer')
                  .sort(([, a], [, b]) => (b as number) - (a as number))
                  .map(([k, v]) => {
                    const total = ix.transfer_amounts_json?.total_transfer ?? 0.01
                    const pct = total > 0 ? Math.min(100, ((v as number) / total) * 100) : 0
                    return (
                      <div key={k} style={{ marginBottom: ui.space.sm }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: ui.font.size.sm, marginBottom: 2 }}>
                          <span style={{ color: ui.color.body }}>{shortConcept(k)}</span>
                          <span style={{ fontWeight: ui.font.weight.bold, color: '#C0392B', fontVariantNumeric: 'tabular-nums' }}>
                            {(v as number).toFixed(4)}
                          </span>
                        </div>
                        <div style={{ height: 5, background: ui.color.line, borderRadius: 3, overflow: 'hidden' }}>
                          <div style={{ width: `${pct}%`, height: '100%', background: '#C0392B', borderRadius: 3 }} />
                        </div>
                      </div>
                    )
                  })
              ) : (
                <div style={{ fontSize: ui.font.size.base, color: ui.color.muted, fontStyle: 'italic' }}>
                  {t('replayReview.substratesEmpty')}
                </div>
              )
            }

            <div style={{ marginTop: ui.space.md, padding: '8px 12px', background: '#F7FAFC',
                          borderRadius: ui.radius.sm, fontSize: ui.font.size.sm }}>
              <div style={{ color: ui.color.body, marginBottom: ui.space.xs }}>{t('replayReview.eventIdLabel')}</div>
              <div style={{ color: ui.color.muted, fontSize: ui.font.size.xs, fontFamily: 'monospace',
                            wordBreak: 'break-all', lineHeight: 1.4 }}>
                {ix.event_id}
              </div>
            </div>
          </Panel>
        </div>
      )}

      <div style={{ marginTop: ui.space.lg, display: 'flex', gap: ui.space.sm, alignItems: 'flex-start' }}>
        <div style={{ padding: '10px 14px', background: '#F7FAFC',
                      border: `1px solid ${ui.color.line}`, borderRadius: ui.radius.md, fontSize: ui.font.size.sm,
                      color: ui.color.body, lineHeight: 1.6, flex: 1 }}>
          <strong>{t('replayReview.noteLabel')}</strong> {t('replayReview.noteBodyA')}{' '}
          <code>NEXT_PUBLIC_BACKEND_URL</code>{t('replayReview.noteBodyB')}
        </div>
        <div style={{
          padding: '6px 12px', borderRadius: ui.radius.sm, fontSize: ui.font.size.sm, fontWeight: ui.font.weight.bold,
          whiteSpace: 'nowrap', alignSelf: 'center',
          background: dataSource === 'live_db' ? '#D5F5E3' : dataSource === 'static' ? '#FEF9E7' : '#F7FAFC',
          color:      dataSource === 'live_db' ? '#1E8449' : dataSource === 'static' ? '#7D6008' : ui.color.muted,
          border: `1px solid ${dataSource === 'live_db' ? '#A9DFBF' : dataSource === 'static' ? '#F9E79F' : ui.color.line}`,
        }}>
          {dataSource === 'live_db' ? `● ${t('replayReview.sourceLiveDb')}` : dataSource === 'static' ? `○ ${t('replayReview.sourceStatic')}` : `○ ${t('replayReview.sourceLoading')}`}
        </div>
      </div>

      <NextSteps />
    </div>
  )
}
