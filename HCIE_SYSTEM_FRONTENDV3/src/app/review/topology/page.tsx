'use client'

import { useEffect, useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, LabelList, ReferenceLine,
} from 'recharts'
import ProvenanceBadge from '@/components/review/ProvenanceBadge'
import ProvisionalBanner from '@/components/review/ProvisionalBanner'
import { useT } from '@/contexts/language_context'
import { getBackendUrl } from '@/lib/api/backend-url'
import { Panel, Tag, Callout, SectionTitle, Eyebrow } from '@/lib/ui/primitives'
import { t as ui } from '@/lib/ui/theme'  // aliased: `t` is taken by useT() (translations)

type Dataset = {
  dataset_id: string
  display_name: string
  topology_class: string
  concept_structure: string
  adc_prediction: string
  prediction_rationale: string
  citation: string
  phase: string
  run_id: string
  n: number
  mean: number
  std: number
  signal_ratio: number
  nonzero_count: number
  observed_class: string
  adc_match: boolean
  hcie_auc?: number
}

type TaxonomyData = {
  generated_at: string
  sealed_thresholds: { alpha_floor: number; signal_ratio_threshold: number }
  datasets: Dataset[]
}

const CLASS_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  explicit_dag:      { bg: '#EBF5FB', text: '#1565C0', border: '#AED6F1' },
  flat_skill_tag:    { bg: '#FDFEFE', text: '#5D6D7E', border: '#D5DBDB' },
  null_graph:        { bg: '#FDEDEC', text: '#C0392B', border: '#FADBD8' },
  transition_only:   { bg: '#FEF9E7', text: '#7D6008', border: '#F9E79F' },
  bipartite_qmatrix: { bg: '#F5EEF8', text: '#7D3C98', border: '#D2B4DE' },
}

const ALL_CLASSES = Object.keys(CLASS_COLORS)

function TopologyBadge({ cls }: { cls: string }) {
  const c = CLASS_COLORS[cls] ?? { bg: ui.color.subtle, text: ui.color.body, border: ui.color.lineStrong }
  return (
    <span style={{
      display: 'inline-block', padding: '2px 8px', borderRadius: ui.radius.sm,
      background: c.bg, color: c.text, border: `1px solid ${c.border}`,
      fontSize: ui.font.size.sm, fontWeight: ui.font.weight.bold, whiteSpace: 'nowrap',
    }}>
      {cls.replace(/_/g, ' ')}
    </span>
  )
}

const BACKEND_URL = getBackendUrl()

// ── Hardcoded fallback values from sealed run ──────────────────────────────
type CausalStats = {
  past: number
  shuffled: number
  placebo: number
  causal: number
  n: number
}
const CAUSAL_FALLBACK: CausalStats = {
  past: 0.091,
  shuffled: 0.000,
  placebo: 0.038,
  causal: 0.053,
  n: 1976020,
}

export default function TopologyPage() {
  const t = useT()
  const [data, setData] = useState<TaxonomyData | null>(null)
  const [filter, setFilter] = useState<string>('all')
  const [causalStats, setCausalStats] = useState<CausalStats>(CAUSAL_FALLBACK)

  useEffect(() => {
    fetch('/data/adc/topology_taxonomy.json').then(r => r.json()).then(setData)
  }, [])

  useEffect(() => {
    fetch(`${BACKEND_URL}/v3/frontend/dashboard/topology-comparison`)
      .then(r => r.ok ? r.json() : null)
      .then(d => {
        // API shape: { status, data: { b_durable_CROSS_past, shuffled_dag_estimate,
        // b_FUTURE_cross_PLACEBO, causal_estimate, n_rows } } — map to the local shape.
        const c = d?.data
        if (c?.b_durable_CROSS_past != null) setCausalStats({
          past: c.b_durable_CROSS_past,
          shuffled: c.shuffled_dag_estimate,
          placebo: c.b_FUTURE_cross_PLACEBO,
          causal: c.causal_estimate,
          n: c.n_rows,
        })
      })
      .catch(() => { /* keep fallback */ })
  }, [])

  const datasets = data?.datasets.filter(d =>
    filter === 'all' ? true : d.topology_class === filter
  ) ?? []

  // Decomposition bars — fills track the three condition cards above (ok/warn/accent)
  // plus the placebo-corrected residual (info). Same data binding as the stat cards.
  const DECOMP_BARS = [
    { label: t('topologyReview.barCrossPast'), value: causalStats.past,     color: ui.tone.ok.fg },
    { label: t('topologyReview.barShuffled'),  value: causalStats.shuffled, color: ui.tone.warn.fg },
    { label: t('topologyReview.barPlacebo'),   value: causalStats.placebo,  color: ui.tone.accent.fg },
    { label: t('topologyReview.barResidual'),  value: causalStats.causal,   color: ui.tone.info.fg },
  ]

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: `${ui.space.xl}px ${ui.space.lg}px 64px` }}>
      <Eyebrow color={ui.tone.info.fg}>{t('topologyReview.eyebrow')}</Eyebrow>
      <SectionTitle
        sub={<>
          {t('topologyReview.heroSubA')}{' '}
          <strong>{t('topologyReview.heroSubB')}</strong>{' '}
          {t('topologyReview.heroSubC')}
        </>}
      >
        {t('topologyReview.heroTitle')}
      </SectionTitle>
      <div style={{ marginTop: ui.space.lg }} />

      <ProvisionalBanner
        tone="partial"
        headline={t('topologyReview.bannerHeadline')}
        body={<>
          {t('topologyReview.bannerBodyA')} <em>{t('topologyReview.bannerBodyPresence')}</em>{t('topologyReview.bannerBodyB')} <em>{t('topologyReview.bannerBodyCorrectness')}</em> {t('topologyReview.bannerBodyC')} <em>{t('topologyReview.bannerBodyMeans')}</em> {t('topologyReview.bannerBodyD')}
        </>}
        flipsAfter={[
          t('topologyReview.bannerFlip1'),
          t('topologyReview.bannerFlip2'),
        ]}
      />

      <ProvenanceBadge
        source={data ? 'frozen' : 'loading'}
        generatedAt={data?.generated_at}
        n={data?.datasets?.reduce((sum, d) => sum + (d.n || 0), 0) ?? null}
        note={t('topologyReview.provenanceNote')}
      />

      {/* Sealed thresholds */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: ui.space.md, marginBottom: ui.space.xl }}>
        {([
          ['alphaFloor', 'α_floor', '0.01', t('topologyReview.thresholdAlphaFloorDesc'), 'info'],
          ['signalRatio', t('topologyReview.thresholdSignalRatioLabel'), '0.08', t('topologyReview.thresholdSignalRatioDesc'), 'info'],
          ['classMatch', t('topologyReview.thresholdConsistentLabel'), '8 / 8', t('topologyReview.thresholdConsistentDesc'), 'ok'],
        ] as const).map(([k, label, v, desc, tn]) => (
          <Panel key={k} pad="md" tone={tn}>
            <div style={{ fontSize: ui.font.size.h2, fontWeight: ui.font.weight.heavy, color: ui.tone[tn].fg, fontVariantNumeric: 'tabular-nums' }}>{v}</div>
            <div style={{ fontSize: ui.font.size.sm, fontWeight: ui.font.weight.bold, color: ui.color.heading, marginTop: 2 }}>{label}</div>
            <div style={{ fontSize: ui.font.size.xs, color: ui.color.muted, marginTop: 2 }}>{desc}</div>
          </Panel>
        ))}
      </div>

      {/* Filter */}
      <div style={{ display: 'flex', gap: ui.space.sm, marginBottom: ui.space.xl, flexWrap: 'wrap' }}>
        {['all', ...ALL_CLASSES].map(cls => (
          <button key={cls} onClick={() => setFilter(cls)}
            style={{
              padding: `${ui.space.xs}px ${ui.space.md}px`, borderRadius: ui.radius.xl, cursor: 'pointer',
              fontSize: ui.font.size.base, fontWeight: filter === cls ? ui.font.weight.bold : 400,
              background: filter === cls ? ui.tone.info.fg : ui.color.surface,
              color: filter === cls ? ui.color.surface : ui.color.body,
              border: `1px solid ${filter === cls ? ui.tone.info.fg : ui.color.line}`,
              transition: 'background 0.15s, border-color 0.15s',
            }}>
            {cls === 'all' ? t('topologyReview.filterAll') : cls.replace(/_/g, ' ')}
          </button>
        ))}
      </div>

      {/* Table */}
      {!data ? (
        <div style={{ color: ui.color.muted, fontSize: ui.font.size.lg }}>{t('topologyReview.loading')}</div>
      ) : (
        <Panel style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', minWidth: 860, borderCollapse: 'collapse', fontSize: ui.font.size.base }}>
            <thead>
              <tr style={{ background: ui.color.subtle, borderBottom: `2px solid ${ui.color.lineStrong}` }}>
                {[
                  t('topologyReview.thDataset'),
                  t('topologyReview.thTopologyClass'),
                  t('topologyReview.thConceptStructure'),
                  t('topologyReview.thAdcPrediction'),
                  t('topologyReview.thObserved'),
                  t('topologyReview.thMatch'),
                  t('topologyReview.thN'),
                  t('topologyReview.thMeanTr'),
                  t('topologyReview.thHcieAuc'),
                ].map((h, hi) => (
                  <th key={h} style={{ padding: `${ui.space.sm}px ${ui.space.md}px`,
                                       textAlign: hi >= 6 ? 'right' : 'left',
                                       fontWeight: ui.font.weight.bold,
                                       color: ui.color.heading, fontSize: ui.font.size.sm, whiteSpace: 'nowrap' }}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {datasets.map((d, i) => (
                <tr key={d.dataset_id} style={{
                  borderBottom: `1px solid ${ui.color.line}`,
                  background: i % 2 === 0 ? ui.color.surface : ui.color.faintSurface,
                }}>
                  <td style={{ padding: `${ui.space.sm}px ${ui.space.md}px`, fontWeight: ui.font.weight.medium, color: ui.color.heading }}>
                    {d.display_name}
                  </td>
                  <td style={{ padding: `${ui.space.sm}px ${ui.space.md}px` }}>
                    <TopologyBadge cls={d.topology_class} />
                  </td>
                  <td style={{ padding: `${ui.space.sm}px ${ui.space.md}px`, color: ui.color.body, maxWidth: 220 }}>
                    {d.concept_structure}
                  </td>
                  <td style={{ padding: `${ui.space.sm}px ${ui.space.md}px` }}>
                    <Tag tone={d.adc_prediction === 'ACTIVE' ? 'ok' : 'neutral'}>{d.adc_prediction}</Tag>
                  </td>
                  <td style={{ padding: `${ui.space.sm}px ${ui.space.md}px` }}>
                    <Tag tone={d.observed_class === 'ACTIVE' ? 'ok' : 'neutral'}>{d.observed_class}</Tag>
                  </td>
                  <td style={{ padding: `${ui.space.sm}px ${ui.space.md}px`, textAlign: 'center' }}>
                    <span style={{ fontSize: ui.font.size.lg, fontWeight: ui.font.weight.bold,
                                   color: d.adc_match ? ui.tone.ok.fg : ui.tone.bad.fg }}>{d.adc_match ? '✓' : '✗'}</span>
                  </td>
                  <td style={{ padding: `${ui.space.sm}px ${ui.space.md}px`, color: ui.color.body, textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
                    {d.n.toLocaleString()}
                  </td>
                  <td style={{ padding: `${ui.space.sm}px ${ui.space.md}px`, textAlign: 'right', fontVariantNumeric: 'tabular-nums',
                               color: d.observed_class === 'ACTIVE' ? ui.tone.ok.fg : ui.color.body,
                               fontWeight: d.observed_class === 'ACTIVE' ? ui.font.weight.bold : 400 }}>
                    {d.mean.toFixed(4)}
                  </td>
                  <td style={{ padding: `${ui.space.sm}px ${ui.space.md}px`, textAlign: 'right', fontVariantNumeric: 'tabular-nums',
                               color: d.hcie_auc != null ? ui.modelColor.hcie : ui.color.faint,
                               fontWeight: d.hcie_auc != null ? ui.font.weight.bold : 400 }}>
                    {d.hcie_auc != null ? d.hcie_auc.toFixed(3) : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>
        </Panel>
      )}

      {/* Key insight */}
      <Callout tone="warn" style={{ marginTop: ui.space.xl, lineHeight: 1.6 }} title={t('topologyReview.keyInsightTitle')}>
        {t('topologyReview.keyInsightBodyA')} <em>{t('topologyReview.keyInsightBodyEm')}</em>{t('topologyReview.keyInsightBodyB')}
      </Callout>

      {/* ══════════════════════════════════════════════════════════════════════
          SHUFFLED-DAG CAUSAL ANALYSIS
          ══════════════════════════════════════════════════════════════════════ */}
      <div style={{ marginTop: ui.space.xxl, borderTop: `2px solid ${ui.color.line}`, paddingTop: ui.space.xxl }}>

        {/* Heading */}
        <SectionTitle
          sub={<>{t('topologyReview.causalSectionSub')}</>}
        >
          {t('topologyReview.causalSectionTitle')}
        </SectionTitle>

        {/* Three-column stat panel */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: ui.space.lg, margin: `${ui.space.lg}px 0 ${ui.space.xl}px` }}>
          {([
            {
              label: t('topologyReview.statObservedLabel'),
              value: `b = +${causalStats.past.toFixed(3)}`,
              sublabel: t('topologyReview.statObservedSub'),
              tone: 'ok' as const,
            },
            {
              label: t('topologyReview.statShuffledLabel'),
              value: `b ≈ ${causalStats.shuffled === 0 ? '0' : causalStats.shuffled.toFixed(3)} (p < 0.01)`,
              sublabel: t('topologyReview.statShuffledSub'),
              tone: 'warn' as const,
            },
            {
              label: t('topologyReview.statPlaceboLabel'),
              value: `b = +${causalStats.placebo.toFixed(3)}`,
              sublabel: t('topologyReview.statPlaceboSub'),
              tone: 'accent' as const,
            },
          ]).map(col => (
            <Panel key={col.label} tone={col.tone}>
              <div style={{ fontSize: ui.font.size.sm, fontWeight: ui.font.weight.bold, color: ui.tone[col.tone].fg, textTransform: 'uppercase',
                             letterSpacing: '0.05em', marginBottom: ui.space.xs }}>
                {col.label}
              </div>
              <div style={{ fontSize: ui.font.size.h2, fontWeight: ui.font.weight.heavy, color: ui.tone[col.tone].fg,
                             fontVariantNumeric: 'tabular-nums', marginBottom: ui.space.xs }}>
                {col.value}
              </div>
              <div style={{ fontSize: ui.font.size.sm, color: ui.color.body }}>{col.sublabel}</div>
            </Panel>
          ))}
        </div>

        {/* Placebo-corrected residual panel — NOT clean causal (mandatory framing) */}
        <Callout tone="warn" style={{ borderWidth: 2, borderRadius: ui.radius.lg, padding: `${ui.space.lg}px ${ui.space.xl}px`, marginBottom: ui.space.xl }}>
          <div style={{ fontSize: ui.font.size.md, fontWeight: ui.font.weight.heavy, color: ui.tone.warn.fg, marginBottom: ui.space.sm }}>
            {t('topologyReview.residualTitle')}
          </div>
          <div style={{ fontSize: ui.font.size.md, color: ui.color.ink, lineHeight: 1.8 }}>
            {t('topologyReview.residualEqDurable')} ({causalStats.past.toFixed(3)}) − {t('topologyReview.residualEqPlacebo')} ({causalStats.placebo.toFixed(3)}) ={' '}
            <strong style={{ fontSize: ui.font.size.lg, color: ui.tone.warn.fg }}>+{causalStats.causal.toFixed(3)}</strong>{' '}
            {t('topologyReview.residualEqLabel')}
          </div>
          <div style={{ marginTop: ui.space.sm, display: 'flex', gap: ui.space.lg, flexWrap: 'wrap', fontSize: ui.font.size.base, color: ui.color.body }}>
            <span><strong>{t('topologyReview.residualRatioStrong')}</strong> {t('topologyReview.residualRatioRest')}</span>
            <span><strong>{t('topologyReview.residualPermStrong')}</strong> {t('topologyReview.residualPermRest')}</span>
          </div>
          <div style={{ marginTop: ui.space.sm, fontSize: ui.font.size.base, color: ui.color.body, lineHeight: 1.7 }}>
            {t('topologyReview.residualNoteA')} <strong>{t('topologyReview.residualNoteStrong')}</strong>{t('topologyReview.residualNoteB')}
          </div>
        </Callout>

        {/* Bar chart */}
        <Panel style={{ marginBottom: ui.space.lg }}>
          <SectionTitle sub="Coefficient b per condition, on a common axis — the residual (right) is what survives both the shuffled-edge and time-placebo controls.">
            Decomposition — coefficient b
          </SectionTitle>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart
              data={DECOMP_BARS}
              barCategoryGap="32%"
              margin={{ left: 12, right: 16, top: 24, bottom: 28 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke={ui.color.grid} vertical={false} />
              <XAxis
                dataKey="label"
                tick={{ fontSize: ui.font.size.xs, fill: ui.color.muted }}
                tickLine={false}
                axisLine={{ stroke: ui.color.lineStrong }}
                interval={0}
              />
              <YAxis
                domain={[0, 0.12]}
                tick={{ fontSize: ui.font.size.xs, fill: ui.color.muted }}
                tickFormatter={v => v.toFixed(3)}
                tickLine={false}
                axisLine={{ stroke: ui.color.lineStrong }}
                width={52}
                label={{ value: 'coefficient b', angle: -90, position: 'insideLeft',
                         style: { fontSize: ui.font.size.xs, fill: ui.color.muted, textAnchor: 'middle' } }}
              />
              <Tooltip
                cursor={{ fill: ui.color.grid }}
                formatter={(v: any) => [typeof v === 'number' ? v.toFixed(4) : Number(v).toFixed(4), 'coefficient b']}
                contentStyle={{
                  fontSize: ui.font.size.sm, borderRadius: ui.radius.md,
                  border: `1px solid ${ui.color.line}`, color: ui.color.heading,
                }}
              />
              <ReferenceLine
                y={causalStats.causal}
                stroke={ui.tone.warn.fg}
                strokeDasharray="4 3"
                label={{ value: `residual +${causalStats.causal.toFixed(3)}`, position: 'right',
                         fill: ui.tone.warn.fg, fontSize: ui.font.size.xs, fontWeight: ui.font.weight.bold }}
              />
              <Bar dataKey="value" radius={[ui.radius.sm, ui.radius.sm, 0, 0]} maxBarSize={88}>
                <LabelList
                  dataKey="value"
                  position="top"
                  formatter={(v: any) => Number(v).toFixed(3)}
                  style={{ fontSize: ui.font.size.xs, fontWeight: ui.font.weight.bold, fill: ui.color.heading }}
                />
                {DECOMP_BARS.map(row => (
                  <Cell key={row.label} fill={row.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Panel>

        {/* Footer / sourcing */}
        <div style={{ fontSize: ui.font.size.sm, color: ui.color.muted, lineHeight: 1.7 }}>
          <div>
            N = {causalStats.n.toLocaleString()} first-encounters · sealed 2026-06-03 ·
            p &lt; 0.01 (permutation test) · Source: prospective_probe_v3_full.json
          </div>
          <Callout tone="neutral" style={{ marginTop: ui.space.xs, padding: '8px 12px', fontSize: ui.font.size.sm }}>
            <strong>R12 ablation note:</strong> R12 ablation was attempted but withdrawn (confounded —
            cross-run state accumulation, sign-flip in multi-seed). Shuffled-DAG is the primary
            causal evidence.
          </Callout>
        </div>
      </div>
    </div>
  )
}
