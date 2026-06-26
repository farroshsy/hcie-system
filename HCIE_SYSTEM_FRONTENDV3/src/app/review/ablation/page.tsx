'use client'

import { useEffect, useState } from 'react'
import {
  ComposedChart, Bar, Line, Scatter, ErrorBar,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine,
} from 'recharts'
import ProvenanceBadge from '@/components/review/ProvenanceBadge'
import ProvisionalBanner from '@/components/review/ProvisionalBanner'
import { NextSteps } from '@/components/review/NextSteps'
import { useT } from '@/contexts/language_context'

type WinAgg = { mean: number; std: number; min: number; max: number }
type Win = 'w5' | 'w10' | 'w20' | 'overall'

type AblationData = {
  generated_at?: string
  status?: string
  source_run_id: string
  r12_run_id: string
  n_interactions_replayed?: number
  withdrawal_reason?: string
  graph_on_auc: Record<Win, number>
  graph_on_note?: string
  graph_off_runs: { run_id: string; kind: string; w5: number; w10: number; w20: number; overall: number }[]
  graph_off_multiseed_agg: { n_runs: number } & Record<Win, WinAgg>
  delta_multiseed_agg: Record<Win, { mean: number; std: number }>
  delta_snapshot: Record<Win, number>
  shuffled_dag_causal_effect?: number
  shuffled_dag_p?: string
  protocol: string
  interpretation: string
}

export default function AblationPage() {
  const t = useT()
  const [data, setData] = useState<AblationData | null>(null)

  const WINDOWS: { key: Win; label: string }[] = [
    { key: 'w5', label: '≤ 5' },
    { key: 'w10', label: '≤ 10' },
    { key: 'w20', label: '≤ 20' },
    { key: 'overall', label: t('ablationReview.winOverall') },
  ]

  useEffect(() => {
    fetch('/data/adc/r12_ablation.json').then(r => r.json()).then(setData)
  }, [])

  if (!data) return <div style={{ padding: 40, color: '#718096' }}>{t('common.loading')}</div>

  // Tolerate the legacy single-replay shape (graph_off_auc / delta_auc): synthesize the
  // multi-seed fields the chart expects so the page renders gracefully instead of crashing on
  // an undefined graph_off_multiseed_agg['w5']. With legacy data the OFF spread collapses to a
  // single point (std 0, no snapshot scatter); the "magnitude withdrawn" message below still holds.
  const legacy = data as any
  const offAgg = data.graph_off_multiseed_agg ?? {
    n_runs: 1,
    ...Object.fromEntries(WINDOWS.map(w => {
      const v = legacy.graph_off_auc?.[w.key] ?? 0
      return [w.key, { mean: v, std: 0, min: v, max: v }]
    })),
  }
  const offRuns = data.graph_off_runs ?? []
  const deltaSnap: Record<Win, number> = data.delta_snapshot ?? legacy.delta_auc ?? ({} as Record<Win, number>)
  const deltaMs: Record<Win, { mean: number; std: number }> =
    data.delta_multiseed_agg ?? (Object.fromEntries(
      WINDOWS.map(w => [w.key, { mean: legacy.delta_auc?.[w.key] ?? 0, std: 0 }])
    ) as Record<Win, { mean: number; std: number }>)

  // Per-window chart rows: fixed graph-ON reference + graph-OFF multi-seed mean±std + cold snapshot point.
  const chartData = WINDOWS.map(w => {
    const agg = offAgg[w.key]
    return {
      window: w.label,
      on: data.graph_on_auc[w.key],
      offMean: agg.mean,
      offStd: agg.std,
      snapshot: offRuns.find(r => r.kind === 'snapshot')?.[w.key] ?? null,
    }
  })

  return (
    <div style={{ padding: '32px 40px', maxWidth: 900 }}>
      <div style={{ marginBottom: 24 }}>
        <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.1em',
                      color: '#C0392B', textTransform: 'uppercase', marginBottom: 6 }}>
          {t('ablationReview.eyebrow')}
        </div>
        <h1 style={{ fontSize: 22, fontWeight: 800, color: '#1A2332', marginBottom: 8 }}>
          {t('ablationReview.heroTitle')}
        </h1>
        <p style={{ fontSize: 13, color: '#4A5568', lineHeight: 1.6, maxWidth: 720 }}>
          {t('ablationReview.introA')} <em>{t('ablationReview.introInside')}</em> {t('ablationReview.introB')}
        </p>
      </div>

      <ProvisionalBanner
        tone="provisional"
        headline={t('ablationReview.bannerHeadline')}
        body={<>
          {t('ablationReview.bannerBodyA')} +7.6 pp {t('ablationReview.bannerBodyB')} +23.6 pp {t('ablationReview.bannerBodyC')} −20.4 pp{t('ablationReview.bannerBodyD')} +0.053, p&lt;0.01).
        </>}
        flipsAfter={[
          t('ablationReview.flipAfter1'),
          t('ablationReview.flipAfter2'),
        ]}
      />

      <ProvenanceBadge
        source="frozen"
        generatedAt={data.generated_at}
        runId={data.source_run_id}
        n={data.n_interactions_replayed}
      />

      {/* Real-data spread chart */}
      <div style={{ background: '#FFFFFF', border: '1px solid #F5B7B1', borderRadius: 10,
                    padding: '20px 16px', marginTop: 16, marginBottom: 20 }}>
        <div style={{ fontSize: 14, fontWeight: 800, color: '#C0392B', marginBottom: 4, padding: '0 4px' }}>
          {t('ablationReview.chartTitle')}
        </div>
        <div style={{ fontSize: 12, color: '#718096', lineHeight: 1.6, marginBottom: 14, padding: '0 4px' }}>
          {t('ablationReview.chartLegendA')} {offAgg.n_runs} {t('ablationReview.chartLegendB')}
        </div>
        <ResponsiveContainer width="100%" height={340}>
          <ComposedChart data={chartData} margin={{ left: 0, right: 20, top: 8, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#EDF2F7" />
            <XAxis dataKey="window" tick={{ fontSize: 11, fill: '#4A5568' }} />
            <YAxis domain={[0.45, 1.0]} tickFormatter={v => v.toFixed(2)}
                   tick={{ fontSize: 10, fill: '#A0AEC0' }} />
            <Tooltip
              formatter={(value: any, name: any) => {
                const label = name === 'on' ? t('ablationReview.legendOnFixed')
                  : name === 'offMean' ? t('ablationReview.legendOffMean')
                  : name === 'snapshot' ? t('ablationReview.legendOffSnapshot') : name
                return [Number(value).toFixed(4), label]
              }}
              contentStyle={{ fontSize: 12, borderRadius: 6 }}
            />
            <Legend wrapperStyle={{ fontSize: 11 }}
              formatter={(v) => v === 'on' ? t('ablationReview.legendOnFixed')
                : v === 'offMean' ? `${t('ablationReview.legendOffMeanPrefix')} ${offAgg.n_runs} ${t('ablationReview.legendOffMeanSuffix')}`
                : v === 'snapshot' ? t('ablationReview.legendOffSnapshot') : v} />
            <ReferenceLine y={0.7} stroke="#E2E8F0" strokeDasharray="4 2" />
            <Bar dataKey="offMean" fill="#C0392B" fillOpacity={0.55} radius={[4, 4, 0, 0]} barSize={40}>
              <ErrorBar dataKey="offStd" width={6} strokeWidth={2} stroke="#7B241C" direction="y" />
            </Bar>
            <Line dataKey="on" stroke="#1E8449" strokeWidth={3} dot={{ r: 4 }} type="monotone" />
            <Scatter dataKey="snapshot" fill="#2980B9" />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Per-window delta read-out: snapshot vs multi-seed — shows the sign flip */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))',
                    gap: 12, marginBottom: 20 }}>
        {WINDOWS.map(w => {
          const snap = deltaSnap[w.key] ?? 0
          const ms = deltaMs[w.key] ?? { mean: 0, std: 0 }
          const flips = (snap > 0) !== (ms.mean > 0)
          return (
            <div key={w.key} style={{ background: '#FFFFFF', border: '1px solid #E2E8F0',
                                      borderRadius: 8, padding: '12px 14px' }}>
              <div style={{ fontSize: 11, color: '#718096', marginBottom: 6 }}>{w.label} {t('ablationReview.interactions')}</div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12 }}>
                <span style={{ color: '#2980B9' }}>{t('ablationReview.snapshot')}</span>
                <span style={{ fontWeight: 700, color: snap > 0 ? '#1E8449' : '#C0392B' }}>
                  {snap > 0 ? '+' : ''}{(snap * 100).toFixed(1)} pp
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginTop: 4 }}>
                <span style={{ color: '#C0392B' }}>{t('ablationReview.fiveSeedMean')}</span>
                <span style={{ fontWeight: 700, color: ms.mean > 0 ? '#1E8449' : '#C0392B' }}>
                  {ms.mean > 0 ? '+' : ''}{(ms.mean * 100).toFixed(1)} pp
                </span>
              </div>
              {flips && (
                <div style={{ marginTop: 8, fontSize: 10, fontWeight: 700, color: '#C0392B',
                              textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  ⚠ {t('ablationReview.signFlips')}
                </div>
              )}
            </div>
          )
        })}
      </div>

      <div style={{ fontSize: 11, color: '#718096', lineHeight: 1.6,
                    background: '#F8F9FF', border: '1px solid #C3CFE2', borderRadius: 8,
                    padding: '12px 14px', marginBottom: 20 }}>
        <strong>⚠ {t('ablationReview.withdrawnLabel')}:</strong> {t('ablationReview.withdrawnBody')}{' '}
        <strong>+{((data.shuffled_dag_causal_effect ?? 0.053) * 100).toFixed(1)} pp</strong>,
        <strong> p{data.shuffled_dag_p ?? '<0.01'}</strong>.
      </div>

      {/* Protocol note */}
      <div style={{ marginTop: 20, padding: '12px 16px', background: '#F7FAFC',
                    border: '1px solid #E2E8F0', borderRadius: 8, fontSize: 11,
                    color: '#4A5568', lineHeight: 1.6 }}>
        <strong>{t('ablationReview.protocolLabel')}:</strong> {data.protocol}
      </div>

      {/* Run IDs */}
      <div style={{ marginTop: 12, padding: '10px 16px', background: '#1A2332', borderRadius: 8,
                    fontSize: 11, color: '#A0AEC0', fontFamily: 'monospace', lineHeight: 2 }}>
        <div><span style={{ color: '#64B5F6' }}>{t('ablationReview.runIdPhase2')}:</span> {data.source_run_id}</div>
        <div><span style={{ color: '#FC8181' }}>{t('ablationReview.runIdR12')}:</span> {data.r12_run_id}</div>
      </div>

      <NextSteps />
    </div>
  )
}
