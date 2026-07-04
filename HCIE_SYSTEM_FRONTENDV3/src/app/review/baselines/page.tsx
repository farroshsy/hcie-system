'use client'

import { useEffect, useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, ReferenceLine,
  LineChart, Line, Legend,
} from 'recharts'
import ProvenanceBadge from '@/components/review/ProvenanceBadge'
import ProvisionalBanner from '@/components/review/ProvisionalBanner'
import { DeployedBeatsBKT } from '@/components/dashboard/DeployedBeatsBKT'
import { useT } from '@/contexts/language_context'
import { NextSteps } from '@/components/review/NextSteps'
import { getBackendUrl } from '@/lib/api/backend-url'
import { Panel, Tag, Callout, SectionTitle, Eyebrow, Stat } from '@/lib/ui/primitives'
import { t as ui } from '@/lib/ui/theme'  // aliased: `t` is taken by useT() (translations)

type ModelResult = {
  model: string
  note: string
  w5: number
  w10: number
  w20: number
  overall: number
  n_overall: number
}

type BaselineData = {
  generated_at?: string
  phase2_run_id?: string
  eval_users?: number
  protocol_note: string
  primary_rows: ModelResult[]
  phase1_ref_row: ModelResult
}

type WindowKey = 'w5' | 'w10' | 'w20' | 'overall'

// Per-model colors. Baselines draw from the shared modelColor token map so every
// surface renders the same baseline in the same hue. HCIE keeps this page's
// load-bearing green identity (the "HCIE wins" panel / ★ tags / Stat / row
// highlight are all green), so it is pinned to the ok tone rather than the
// canonical hcie purple to avoid an intra-page clash.
const HCIE_GREEN = ui.tone.ok.fg
const MODEL_COLORS: Record<string, string> = {
  'HCIE Phase 2':      HCIE_GREEN,
  'BKT':               ui.modelColor.bkt,
  'DKT':               ui.modelColor.dkt,
  'SAKT':              ui.modelColor.sakt,
  'GKT (graph-aware)': ui.modelColor.gkt,
}

const BACKEND = getBackendUrl()

// ── Hardcoded fallback values: canonical m_K, n=76 robust matched eval ──────
// Source: research_validation/reports/tier1_evidence.json (anchor d2154070, lagged-Kalman m_K,
// tie-aware rank-AUC, n=76 users). Replaces the old pre-tie-aware sealed values (0.609/0.612).
// Note: the cited matched HEADLINE (Tabel 4.5 panel below) is the conservative n=10-eval figure
// (HCIE 0.6051); these window values are the larger n=76 robust eval — the HCIE−BKT lead holds in both.
const AUC_WINDOW_FALLBACK = [
  { window: '≤5 cold-start', HCIE: 0.753, BKT: 0.716, DKT: 0.691, SAKT: 0.651, GKT: 0.599 },
  { window: '≤10',           HCIE: 0.712, BKT: 0.730, DKT: 0.713, SAKT: 0.687, GKT: 0.610 },
  { window: '≤20',           HCIE: 0.725, BKT: 0.755, DKT: 0.742, SAKT: 0.718, GKT: 0.615 },
  { window: 'All',           HCIE: 0.687, BKT: 0.675, DKT: 0.608, SAKT: 0.599, GKT: 0.576 },
]

const COLD_WARM_FALLBACK = [
  { model: 'HCIE',           cold: 0.753, all: 0.687 },
  { model: 'BKT',            cold: 0.716, all: 0.675 },
  { model: 'DKT',            cold: 0.691, all: 0.608 },
  { model: 'SAKT',           cold: 0.651, all: 0.599 },
  { model: 'GKT',            cold: 0.599, all: 0.576 },
]

type AucWindowRow = { window: string; HCIE: number; BKT: number; DKT: number; SAKT: number; GKT: number }
type ColdWarmRow  = { model: string; cold: number; all: number }

// Per-line color for the AUC-vs-window line chart. Baselines via the shared
// token map; HCIE keeps this page's green identity (see MODEL_COLORS note).
const LINE_COLORS: Record<keyof Omit<AucWindowRow, 'window'>, string> = {
  HCIE: HCIE_GREEN,
  BKT:  ui.modelColor.bkt,
  DKT:  ui.modelColor.dkt,
  SAKT: ui.modelColor.sakt,
  GKT:  ui.modelColor.gkt,
}

export default function BaselinesPage() {
  const t = useT()

  const WINDOWS: { key: WindowKey; label: string }[] = [
    { key: 'w5',      label: t('baselinesReview.winW5') },
    { key: 'w10',     label: t('baselinesReview.winW10') },
    { key: 'w20',     label: t('baselinesReview.winW20') },
    { key: 'overall', label: t('baselinesReview.winOverall') },
  ]

  const [data, setData] = useState<BaselineData | null>(null)
  const [selectedWindow, setSelectedWindow] = useState<WindowKey>('overall')
  const [aucWindowData, setAucWindowData] = useState<AucWindowRow[]>(AUC_WINDOW_FALLBACK)
  const [coldWarmData, setColdWarmData]   = useState<ColdWarmRow[]>(COLD_WARM_FALLBACK)

  useEffect(() => {
    fetch('/data/adc/baseline_comparison.json').then(r => r.json()).then(setData)
  }, [])

  useEffect(() => {
    fetch(`${BACKEND}/v3/frontend/dashboard/auc-by-window`)
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d?.rows?.length) setAucWindowData(d.rows) })
      .catch(() => { /* keep fallback */ })
  }, [])

  useEffect(() => {
    fetch(`${BACKEND}/v3/frontend/dashboard/cold-warm-stratified`)
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d?.rows?.length) setColdWarmData(d.rows) })
      .catch(() => { /* keep fallback */ })
  }, [])

  if (!data) return <div style={{ padding: 40, color: ui.color.muted }}>{t('common.loading')}</div>

  const rows = data.primary_rows
  const chartData = rows.map(r => ({
    model: r.model.replace(' (graph-aware)', ''),
    auc: r[selectedWindow],
    isHCIE: r.model === 'HCIE Phase 2',
  })).sort((a, b) => b.auc - a.auc)

  const hcieRow = rows.find(r => r.model === 'HCIE Phase 2')

  return (
    <div style={{ padding: `${ui.space.xxl + 8}px 40px`, maxWidth: 900 }}>
      <div style={{ marginBottom: ui.space.xxl }}>
        <Eyebrow color={ui.tone.info.fg}>{t('baselinesReview.eyebrow')}</Eyebrow>
        <SectionTitle
          sub={<>
            {t('baselinesReview.heroSubA')}
            <em> {t('baselinesReview.heroSubEm')}</em> {t('baselinesReview.heroSubB')}
          </>}
        >
          {t('baselinesReview.heroTitle')}
        </SectionTitle>
      </div>

      {/* ════════════════════════════════════════════════════════════════════════
          DEPLOYED RUNTIME vs BKT — the close-out result (2026-06-05).
          The sealed-matched comparison below is the older N=10 Phase-2 lens;
          THIS panel is the deployed runtime that now actually beats BKT on a
          fair, properly-warmed comparison. Honest per-class labels are baked in.
          ════════════════════════════════════════════════════════════════════════ */}
      {/* CANONICAL headline — lagged-Kalman (Tabel 4.5), the thesis-defended predictor */}
      <Panel
        tone="ok"
        style={{
          borderWidth: 2,
          borderColor: ui.tone.ok.fg,
          marginBottom: ui.space.lg,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: ui.space.sm, marginBottom: ui.space.sm }}>
          <Eyebrow color={ui.tone.ok.fg}>{t('baselinesReview.canonEyebrow')}</Eyebrow>
        </div>
        <div style={{ fontSize: ui.font.size.md, color: ui.color.ink, margin: `0 0 ${ui.space.md}px`, lineHeight: 1.6 }}>
          {t('baselinesReview.canonLeadA')} <strong>{t('baselinesReview.canonLeadStrong')}</strong> {t('baselinesReview.canonLeadB')} <strong>{t('baselinesReview.canonLeadStrong2')}</strong>{t('baselinesReview.canonLeadC')}
        </div>
        <div style={{ display: 'flex', gap: ui.space.sm, flexWrap: 'wrap' }}>
          {([
            ['HCIE 0.6051', HCIE_GREEN],
            ['BKT 0.5963',  ui.modelColor.bkt],
            ['DKT 0.5892',  ui.modelColor.dkt],
            ['SAKT 0.5730', ui.modelColor.sakt],
            ['GKT 0.5711',  ui.modelColor.gkt],
          ] as [string, string][]).map(([lbl, c]) => (
            <span
              key={lbl}
              style={{
                fontSize: ui.font.size.md,
                fontWeight: ui.font.weight.bold,
                color: ui.color.surface,
                background: c,
                borderRadius: ui.radius.sm,
                padding: '4px 10px',
                fontVariantNumeric: 'tabular-nums',
              }}
            >
              {lbl}
            </span>
          ))}
        </div>
        <div style={{ fontSize: ui.font.size.sm, color: ui.color.body, marginTop: ui.space.md, lineHeight: 1.6 }}>
          {t('baselinesReview.canonNoteA')} <strong>{t('baselinesReview.canonNoteStrong1')}</strong>{t('baselinesReview.canonNoteB')} <strong>+0.0088</strong> {t('baselinesReview.canonNoteN10')} +0.0062 {t('baselinesReview.canonNoteN40')} <strong>+0.0125</strong> {t('baselinesReview.canonNoteN76')}
          <strong> {t('baselinesReview.canonNoteCompanion')}</strong> {t('baselinesReview.canonNoteC')} <strong>{t('baselinesReview.canonNoteStrong2')}</strong>{t('baselinesReview.canonNoteD')}
        </div>
      </Panel>

      <DeployedBeatsBKT />

      <div style={{ borderTop: `2px dashed ${ui.color.line}`, margin: `${ui.space.sm}px 0 ${ui.space.xl}px` }} />
      <Eyebrow>
        {t('baselinesReview.supportingContext')}
      </Eyebrow>

      <ProvisionalBanner
        tone="provisional"
        headline={t('baselinesReview.bannerHeadline')}
        body={<>
          {t('baselinesReview.bannerBodyA')} <em>{t('baselinesReview.bannerBodyEm1')}</em> {t('baselinesReview.bannerBodyB')} <em>{t('baselinesReview.bannerBodyEm2')}</em> {t('baselinesReview.bannerBodyC')}
          <em> {t('baselinesReview.bannerBodyEm3')}</em>{t('baselinesReview.bannerBodyD')} <em>{t('baselinesReview.bannerBodyEm4')}</em>{t('baselinesReview.bannerBodyE')}
        </>}
        flipsAfter={[
          t('baselinesReview.flipAfter1'),
          t('baselinesReview.flipAfter2'),
          t('baselinesReview.flipAfter3'),
        ]}
      />

      <ProvenanceBadge
        source="frozen"
        generatedAt={data.generated_at}
        runId={data.phase2_run_id}
        n={data.eval_users}
        note={t('baselinesReview.provenanceNote')}
      />

      {/* Window selector */}
      <div style={{ display: 'flex', gap: ui.space.xs + 2, marginBottom: ui.space.xl }}>
        {WINDOWS.map(w => {
          const active = selectedWindow === w.key
          return (
            <button key={w.key} onClick={() => setSelectedWindow(w.key)}
              style={{
                padding: '5px 14px', borderRadius: 20, cursor: 'pointer',
                fontSize: ui.font.size.base,
                fontWeight: active ? ui.font.weight.bold : 400,
                border: `1px solid ${active ? ui.color.ink : ui.color.line}`,
                background: active ? ui.color.ink : ui.color.subtle,
                color: active ? ui.color.surface : ui.color.body,
                transition: 'background 0.15s',
              }}>
              {w.label}
            </button>
          )
        })}
      </div>

      {/* HCIE headline */}
      {hcieRow && (
        <div style={{ display: 'flex', gap: ui.space.md, marginBottom: ui.space.xl, flexWrap: 'wrap' }}>
          <Stat
            tone="ok"
            value={hcieRow[selectedWindow].toFixed(3)}
            label={<>{t('baselinesReview.statHcieLabelA')} {selectedWindow === 'overall' ? `N=${hcieRow.n_overall.toLocaleString()}` : selectedWindow}</>}
          />
          <Stat
            tone="info"
            value={`#${chartData.findIndex(r => r.isHCIE) + 1}`}
            label={<>{t('baselinesReview.statRankLabelA')}{selectedWindow}{t('baselinesReview.statRankLabelB')}</>}
          />
        </div>
      )}

      {/* Small-sample caveat — per-window cells are n=50–200 and not interpretable */}
      {selectedWindow !== 'overall' && (
        <Callout tone="bad" style={{ marginBottom: ui.space.md + 2 }} title={t('baselinesReview.smallSampleTitle')}>
          {t('baselinesReview.smallSampleBodyA')} <em>{t('baselinesReview.smallSampleEm')}</em>{t('baselinesReview.smallSampleBodyB')}{' '}
          <strong>{t('baselinesReview.smallSampleStrong')}</strong> {t('baselinesReview.smallSampleBodyC')}
        </Callout>
      )}

      {/* Chart */}
      <Panel style={{ marginBottom: ui.space.xl }}>
        <SectionTitle sub={`${t('baselinesReview.chartSubA')} ${WINDOWS.find(w => w.key === selectedWindow)?.label ?? selectedWindow} ${t('baselinesReview.chartSubB')}`}>
          {t('baselinesReview.chartTitle')}
        </SectionTitle>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={chartData} barCategoryGap="32%" margin={{ left: 0, right: 12, top: 8, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={ui.color.grid} vertical={false} />
            <XAxis dataKey="model" tick={{ fontSize: ui.font.size.sm, fill: ui.color.body }}
                   axisLine={{ stroke: ui.color.line }} tickLine={false} />
            <YAxis domain={[0.5, 0.9]} tick={{ fontSize: ui.font.size.sm, fill: ui.color.muted }}
                   tickFormatter={v => v.toFixed(2)} axisLine={false} tickLine={false} width={40}
                   label={{ value: 'AUC', angle: -90, position: 'insideLeft', fontSize: ui.font.size.xs, fill: ui.color.muted }} />
            <Tooltip
              formatter={(v) => [Number(v).toFixed(4), 'AUC']}
              contentStyle={{ fontSize: ui.font.size.base, borderRadius: ui.radius.sm, border: `1px solid ${ui.color.line}` }}
              cursor={{ fill: ui.color.subtle }}
            />
            <ReferenceLine y={0.65} stroke={ui.color.lineStrong} strokeDasharray="4 2" />
            <Bar dataKey="auc" radius={[ui.radius.sm - 2, ui.radius.sm - 2, 0, 0]}>
              {chartData.map(row => (
                <Cell key={row.model}
                  fill={row.isHCIE ? HCIE_GREEN : (MODEL_COLORS[row.model] ?? ui.color.faint)}
                  opacity={row.isHCIE ? 1 : 0.75}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Panel>

      {/* Full table */}
      <Panel pad="md" style={{ padding: 0, overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: ui.font.size.base }}>
          <thead>
            <tr style={{ background: ui.color.subtle, borderBottom: `2px solid ${ui.color.line}` }}>
              {[t('baselinesReview.tableHeaderModel'), t('baselinesReview.tableHeaderNote'), t('baselinesReview.tableHeaderW5'), t('baselinesReview.tableHeaderW10'), t('baselinesReview.tableHeaderW20'), t('baselinesReview.tableHeaderOverall'), t('baselinesReview.tableHeaderN')].map(h => (
                <th key={h} style={{ padding: '9px 12px', textAlign: 'left', fontWeight: ui.font.weight.bold,
                                     color: ui.color.heading, fontSize: ui.font.size.sm, whiteSpace: 'nowrap' }}>
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => {
              const isHCIE = r.model === 'HCIE Phase 2'
              return (
                <tr key={r.model} style={{
                  borderBottom: `1px solid ${ui.color.grid}`,
                  background: isHCIE ? ui.tone.ok.bg : i % 2 === 0 ? ui.color.surface : ui.color.faintSurface,
                }}>
                  <td style={{ padding: '9px 12px', fontWeight: isHCIE ? ui.font.weight.bold : ui.font.weight.medium,
                               color: isHCIE ? ui.tone.ok.fg : ui.color.heading }}>
                    {r.model}
                    {isHCIE && <span style={{ marginLeft: 6 }}><Tag tone="ok">★</Tag></span>}
                  </td>
                  <td style={{ padding: '9px 12px', color: ui.color.muted, fontSize: ui.font.size.sm }}>{r.note}</td>
                  {(['w5','w10','w20','overall'] as WindowKey[]).map(wk => (
                    <td key={wk} style={{
                      padding: '9px 12px', fontVariantNumeric: 'tabular-nums',
                      fontWeight: wk === selectedWindow ? ui.font.weight.bold : 400,
                      color: wk === selectedWindow ? (isHCIE ? ui.tone.ok.fg : ui.color.heading) : ui.color.body,
                    }}>
                      {r[wk].toFixed(3)}
                    </td>
                  ))}
                  <td style={{ padding: '9px 12px', color: ui.color.muted, fontVariantNumeric: 'tabular-nums' }}>
                    {r.n_overall.toLocaleString()}
                  </td>
                </tr>
              )
            })}
            {/* Phase 1 reference row */}
            <tr style={{ borderTop: `2px dashed ${ui.color.line}`, background: ui.color.subtle }}>
              <td style={{ padding: '9px 12px', color: ui.color.faint, fontSize: ui.font.size.sm, fontStyle: 'italic' }}>
                {t('baselinesReview.phase1RefModel')}
              </td>
              <td style={{ padding: '9px 12px', color: ui.color.faint, fontSize: ui.font.size.sm }}>{t('baselinesReview.phase1RefNote')}</td>
              {(['w5','w10','w20','overall'] as WindowKey[]).map(wk => (
                <td key={wk} style={{ padding: '9px 12px', color: ui.color.faint, fontVariantNumeric: 'tabular-nums',
                                      fontSize: ui.font.size.sm }}>
                  {data.phase1_ref_row[wk].toFixed(3)}
                </td>
              ))}
              <td style={{ padding: '9px 12px', color: ui.color.faint, fontSize: ui.font.size.sm }}>
                {data.phase1_ref_row.n_overall.toLocaleString()}
              </td>
            </tr>
          </tbody>
        </table>
      </Panel>

      <div style={{ marginTop: ui.space.md, fontSize: ui.font.size.xs, color: ui.color.faint, lineHeight: 1.6, padding: '0 4px' }}>
        {t('baselinesReview.tableFootA')} <strong>{t('baselinesReview.tableFootStrong')}</strong>{' '}
        {t('baselinesReview.tableFootB')}
      </div>

      <Callout tone="warn" style={{ marginTop: ui.space.lg }} title={t('baselinesReview.gktTitle')}>
        {t('baselinesReview.gktBodyA')} <em>{t('baselinesReview.gktEm')}</em>{' '}
        {t('baselinesReview.gktBodyB')}
      </Callout>

      {/* ══════════════════════════════════════════════════════════════════════
          SECTION A: AUC by Interaction Window — Cold-Start Performance
          ══════════════════════════════════════════════════════════════════════ */}
      <div style={{ marginTop: ui.space.xxl + 8, borderTop: `2px solid ${ui.color.line}`, paddingTop: ui.space.xxl }}>
        <SectionTitle
          sub={t('baselinesReview.sectionASub')}
        >
          {t('baselinesReview.sectionATitle')}
        </SectionTitle>
        <Panel style={{ marginBottom: ui.space.sm }}>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={aucWindowData} margin={{ left: 0, right: 16, top: 8, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={ui.color.grid} vertical={false} />
              <XAxis dataKey="window" tick={{ fontSize: ui.font.size.sm, fill: ui.color.body }}
                     axisLine={{ stroke: ui.color.line }} tickLine={false} />
              <YAxis domain={[0.50, 0.75]} tick={{ fontSize: ui.font.size.sm, fill: ui.color.muted }}
                     tickFormatter={v => v.toFixed(2)} width={44} axisLine={false} tickLine={false}
                     label={{ value: 'AUC', angle: -90, position: 'insideLeft', fontSize: ui.font.size.xs, fill: ui.color.muted }} />
              <Tooltip formatter={(v: any) => (typeof v === 'number' ? v.toFixed(3) : v)}
                       contentStyle={{ fontSize: ui.font.size.base, borderRadius: ui.radius.sm, border: `1px solid ${ui.color.line}` }} />
              <ReferenceLine y={0.612} stroke={ui.tone.bad.fg} strokeDasharray="3 3"
                             label={{ value: t('baselinesReview.refLineLabel'), position: 'insideTopRight',
                                      fontSize: ui.font.size.xs, fill: ui.tone.bad.fg }} />
              <Line type="monotone" dataKey="HCIE"  stroke={LINE_COLORS.HCIE} strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 5 }} />
              <Line type="monotone" dataKey="BKT"   stroke={LINE_COLORS.BKT} strokeWidth={2}
                    strokeDasharray="6 3" dot={{ r: 3 }} />
              <Line type="monotone" dataKey="DKT"   stroke={LINE_COLORS.DKT} strokeWidth={1.5} dot={{ r: 3 }} />
              <Line type="monotone" dataKey="SAKT"  stroke={LINE_COLORS.SAKT} strokeWidth={1.5} dot={{ r: 3 }} />
              <Line type="monotone" dataKey="GKT"   stroke={LINE_COLORS.GKT} strokeWidth={1.5} dot={{ r: 3 }} />
              <Legend verticalAlign="bottom" height={28} wrapperStyle={{ fontSize: ui.font.size.sm }} />
            </LineChart>
          </ResponsiveContainer>
        </Panel>
        <div style={{ fontSize: ui.font.size.xs, color: ui.color.faint, lineHeight: 1.6, padding: '0 4px' }}>
          {t('baselinesReview.sectionAFootA')}{' '}
          <code style={{ background: ui.color.grid, padding: '1px 4px', borderRadius: ui.radius.sm - 3 }}>
            /v3/frontend/dashboard/auc-by-window
          </code>{' '}{t('baselinesReview.sectionAFootB')}
        </div>
      </div>

      {/* ══════════════════════════════════════════════════════════════════════
          SECTION B: Cold vs Warm — Simpson's Paradox Decomposition
          ══════════════════════════════════════════════════════════════════════ */}
      <div style={{ marginTop: ui.space.xxl + 8, borderTop: `2px solid ${ui.color.line}`, paddingTop: ui.space.xxl, marginBottom: ui.space.sm }}>
        <SectionTitle
          sub={t('baselinesReview.sectionBSub')}
        >
          {t('baselinesReview.sectionBTitle')}
        </SectionTitle>
        <Panel pad="md" style={{ padding: 0, overflow: 'hidden', marginBottom: ui.space.sm }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: ui.font.size.base }}>
            <thead>
              <tr style={{ background: ui.color.subtle, borderBottom: `2px solid ${ui.color.line}` }}>
                {[t('baselinesReview.sectionBHeaderModel'), t('baselinesReview.sectionBHeaderCold'), t('baselinesReview.sectionBHeaderAll')].map(h => (
                  <th key={h} style={{ padding: '9px 14px', textAlign: 'left', fontWeight: ui.font.weight.bold,
                                       color: ui.color.heading, fontSize: ui.font.size.sm }}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {coldWarmData.map((r, i) => {
                const isHCIE = r.model === 'HCIE'
                return (
                  <tr key={r.model} style={{
                    borderBottom: `1px solid ${ui.color.grid}`,
                    background: isHCIE ? ui.tone.ok.bg : i % 2 === 0 ? ui.color.surface : ui.color.faintSurface,
                  }}>
                    <td style={{ padding: '9px 14px', fontWeight: isHCIE ? ui.font.weight.bold : ui.font.weight.medium,
                                 color: isHCIE ? ui.tone.ok.fg : ui.color.heading }}>
                      {r.model}
                      {isHCIE && (
                        <span style={{ marginLeft: 6 }}><Tag tone="ok">★</Tag></span>
                      )}
                    </td>
                    <td style={{ padding: '9px 14px', fontVariantNumeric: 'tabular-nums',
                                 color: isHCIE ? ui.tone.ok.fg : ui.color.body,
                                 fontWeight: isHCIE ? ui.font.weight.bold : 400 }}>
                      {r.cold.toFixed(3)}
                    </td>
                    <td style={{ padding: '9px 14px', fontVariantNumeric: 'tabular-nums',
                                 color: ui.color.body }}>
                      {r.all.toFixed(3)}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </Panel>
        <div style={{ fontSize: ui.font.size.xs, color: ui.color.faint, lineHeight: 1.6, padding: '0 4px' }}>
          {t('baselinesReview.sectionBFootA')}{' '}
          <code style={{ background: ui.color.grid, padding: '1px 4px', borderRadius: ui.radius.sm - 3 }}>
            /v3/frontend/dashboard/cold-warm-stratified
          </code>{' '}{t('baselinesReview.sectionBFootB')}
        </div>
      </div>
      <NextSteps />
    </div>
  )
}
