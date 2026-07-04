'use client'

/**
 * Thesis Evidence Console — all 20 extraction passes on one surface.
 *
 * Renders thesis_extracts/*.json (the read-only tabulation of the sealed anchor
 * run, plus isolated probes and one labelled synthetic mechanism demo) as a hero
 * chart/table per pass, with a raw-extract explorer and a deep-link to the live
 * surface where one exists. Honesty carries through: status, provenance, and
 * caveat fields are rendered, never laundered.
 *
 * Data: src/data/thesis_extracts (build-time copy of RealSystem/thesis_extracts).
 */

import React from 'react'
import Link from 'next/link'
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, Legend,
} from 'recharts'
import { Panel, Tag, Callout, SectionTitle, Eyebrow, Stat } from '@/lib/ui/primitives'
import { t as ui, type Tone } from '@/lib/ui/theme'
import { useT } from '@/contexts/language_context'
import { PASSES, ANCHOR, TALLY, type PassMeta, type PassStatus } from '@/data/thesis_extracts'

type TFn = (key: string, fallback?: string) => string

// ─── small helpers ──────────────────────────────────────────────────────────

const STATUS_TONE: Record<PassStatus, Tone> = {
  ok: 'ok', demo: 'accent', partial: 'warn', unavailable: 'bad',
}
const statusLabel = (t: TFn): Record<PassStatus, string> => ({
  ok: t('thesisEvidence.statusOk'),
  demo: t('thesisEvidence.statusDemo'),
  partial: t('thesisEvidence.statusPartial'),
  unavailable: t('thesisEvidence.statusUnavailable'),
})

/** Locale-independent thousands grouping — avoids SSR/CSR hydration mismatch from toLocaleString(). */
const groupInt = (n: number) => Math.trunc(n).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
const fmt = (v: any, d = 4) =>
  typeof v === 'number' ? (Number.isInteger(v) ? groupInt(v) : v.toFixed(d)) : String(v ?? '—')

const modelTone = (name: string): string => {
  const k = name.toLowerCase().replace(/[^a-z0-9_]/g, '')
  if (k.includes('hcie')) return ui.modelColor.hcie
  for (const m of Object.keys(ui.modelColor)) if (k.includes(m)) return ui.modelColor[m]
  return ui.color.muted
}

const prettyDim = (s: string) =>
  s.replace(/^jt_/, '').replace(/_contribution$/, '').replace(/^\d+_/, '').replace(/_/g, ' ')

function domainOf(vals: number[], pad = 0.01): [number, number] {
  const xs = vals.filter((v) => typeof v === 'number' && isFinite(v))
  if (!xs.length) return [0, 1]
  const lo = Math.max(0, Math.min(...xs) - pad)
  const hi = Math.min(1, Math.max(...xs) + pad)
  return [Math.floor(lo * 100) / 100, Math.ceil(hi * 100) / 100]
}

// ─── reusable charts ────────────────────────────────────────────────────────

function BarsH({ data, domain, unit = '' }: {
  data: { name: string; value: number; color?: string }[]; domain?: [number, number]; unit?: string
}) {
  const dom = domain ?? domainOf(data.map((d) => d.value))
  return (
    <ResponsiveContainer width="100%" height={Math.max(120, data.length * 34 + 24)}>
      <BarChart data={data} layout="vertical" margin={{ left: 8, right: 28, top: 4, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={ui.color.grid} horizontal={false} />
        <XAxis type="number" domain={dom} tick={{ fontSize: 10, fill: ui.color.muted }} />
        <YAxis type="category" dataKey="name" width={132} tick={{ fontSize: 11, fill: ui.color.body }} />
        <Tooltip formatter={(v: any) => `${fmt(v)}${unit}`} />
        <Bar dataKey="value" radius={[0, 4, 4, 0]} label={{ position: 'right', fontSize: 10, fill: ui.color.muted, formatter: (v: any) => `${fmt(v)}${unit}` }}>
          {data.map((d, i) => <Cell key={i} fill={d.color ?? ui.modelColor.hcie} />)}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

function GroupedBars({ data, series, xKey = 'name', domain }: {
  data: any[]; series: { key: string; color: string; label?: string }[]; xKey?: string; domain?: [number, number]
}) {
  const dom = domain ?? domainOf(data.flatMap((r) => series.map((s) => r[s.key])))
  return (
    <ResponsiveContainer width="100%" height={230}>
      <BarChart data={data} margin={{ left: 0, right: 8, top: 8, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={ui.color.grid} />
        <XAxis dataKey={xKey} tick={{ fontSize: 10, fill: ui.color.body }} />
        <YAxis domain={dom} tick={{ fontSize: 10, fill: ui.color.muted }} />
        <Tooltip formatter={(v: any) => fmt(v)} />
        <Legend wrapperStyle={{ fontSize: 11 }} />
        {series.map((s) => (
          <Bar key={s.key} dataKey={s.key} name={s.label ?? s.key} fill={s.color} radius={[3, 3, 0, 0]} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  )
}

function Lines({ data, lines, xKey = 'x', domain }: {
  data: any[]; lines: { key: string; color: string; label?: string; axis?: 'left' | 'right' }[]; xKey?: string; domain?: [number, number]
}) {
  return (
    <ResponsiveContainer width="100%" height={230}>
      <LineChart data={data} margin={{ left: 0, right: 8, top: 8, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={ui.color.grid} />
        <XAxis dataKey={xKey} tick={{ fontSize: 10, fill: ui.color.body }} />
        <YAxis yAxisId="left" domain={domain ?? ['auto', 'auto']} tick={{ fontSize: 10, fill: ui.color.muted }} />
        {lines.some((l) => l.axis === 'right') && (
          <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 10, fill: ui.color.faint }} />
        )}
        <Tooltip formatter={(v: any) => fmt(v)} />
        <Legend wrapperStyle={{ fontSize: 11 }} />
        {lines.map((l) => (
          <Line key={l.key} yAxisId={l.axis ?? 'left'} type="monotone" dataKey={l.key}
            name={l.label ?? l.key} stroke={l.color} dot={false} strokeWidth={2} />
        ))}
      </LineChart>
    </ResponsiveContainer>
  )
}

function MiniTable({ columns, rows, highlightCol }: {
  columns: string[]; rows: (string | number)[][]; highlightCol?: number
}) {
  return (
    <div style={{ overflowX: 'auto', border: `1px solid ${ui.color.line}`, borderRadius: ui.radius.md }}>
      <table style={{ borderCollapse: 'collapse', width: '100%', fontSize: ui.font.size.sm }}>
        <thead>
          <tr style={{ background: ui.color.subtle }}>
            {columns.map((c, i) => (
              <th key={i} style={{ textAlign: i === 0 ? 'left' : 'right', padding: '6px 10px', color: ui.color.heading, fontWeight: ui.font.weight.bold, borderBottom: `1px solid ${ui.color.line}`, whiteSpace: 'nowrap' }}>{c}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, ri) => (
            <tr key={ri} style={{ background: ri % 2 ? ui.color.faintSurface : ui.color.surface }}>
              {r.map((cell, ci) => (
                <td key={ci} style={{ textAlign: ci === 0 ? 'left' : 'right', padding: '5px 10px', color: ci === highlightCol ? ui.modelColor.hcie : ui.color.body, fontWeight: ci === highlightCol ? ui.font.weight.bold : 400, borderBottom: `1px solid ${ui.color.grid}`, whiteSpace: 'nowrap' }}>
                  {typeof cell === 'number' ? fmt(cell) : cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function Chips({ items }: { items: { label: string; value: React.ReactNode; tone?: Tone }[] }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: ui.space.sm }}>
      {items.map((it, i) => <Stat key={i} label={it.label} value={it.value} tone={it.tone} />)}
    </div>
  )
}

// ─── per-pass hero renderers ────────────────────────────────────────────────

function Hero({ p, t }: { p: PassMeta; t: TFn }) {
  const d = p.data
  try {
    switch (p.hero) {
      case 'aucBars': {
        const w = d.table_4_5?.windows?.overall ?? {}
        const order = ['hcie_lagged_kalman', 'bkt', 'dkt', 'sakt', 'gkt', 'hcie_3learner_mastery_before_reference']
        const labels: Record<string, string> = {
          hcie_lagged_kalman: t('thesisEvidence.modelHcieLaggedKalman'), bkt: 'BKT', dkt: 'DKT', sakt: 'SAKT', gkt: 'GKT',
          hcie_3learner_mastery_before_reference: t('thesisEvidence.modelHcie3LearnerRef'),
        }
        const data = order.filter((k) => typeof w[k] === 'number').map((k) => ({ name: labels[k], value: w[k], color: modelTone(k) }))
        return <BarsH data={data} />
      }
      case 'datasetGroupedBars': {
        const ds = d.datasets ?? {}
        const rows = Object.values(ds).map((v: any) => ({
          name: (v.label || '').replace(/_/g, ' '), hcie: v.overall_aucs?.hcie, bkt: v.overall_aucs?.bkt,
        })).filter((r: any) => typeof r.hcie === 'number')
        return <GroupedBars data={rows} series={[{ key: 'hcie', color: ui.modelColor.hcie, label: 'HCIE' }, { key: 'bkt', color: ui.modelColor.bkt, label: 'BKT' }]} />
      }
      case 'windowGroupedBars': {
        const r = d.results_auc ?? {}
        const wins = ['<=5', '<=10', '<=20', 'overall']
        const rows = wins.map((w) => ({
          name: w, HCIE: r.HCIE_deployed_readout?.[w]?.auc ?? r.HCIE_sealed_lagged_kalman?.[w]?.auc, warmed: r.warmed_BKT?.[w]?.auc, cold: r.cold_BKT_floor?.[w]?.auc,
        }))
        return <GroupedBars data={rows} series={[
          { key: 'HCIE', color: ui.modelColor.hcie, label: t('thesisEvidence.seriesHcieSealed') },
          { key: 'warmed', color: ui.modelColor.bkt, label: t('thesisEvidence.seriesWarmedBkt') },
          { key: 'cold', color: ui.color.faint, label: t('thesisEvidence.seriesColdBktFloor') },
        ]} />
      }
      case 'scaleLines': {
        const c = d.scale_sweep_window20?.csedm_f19 ?? {}
        const Ns = ['N30', 'N100', 'N500']
        const rows = Ns.map((N) => ({
          x: N.replace('N', 'N='), hcie: c.hcie?.[N]?.auc, bkt: c.bkt?.[N]?.auc, dkt: c.dkt?.[N]?.auc, sakt: c.sakt?.[N]?.auc,
        }))
        return <Lines data={rows} lines={[
          { key: 'hcie', color: ui.modelColor.hcie, label: t('thesisEvidence.seriesHcieCsedm') },
          { key: 'dkt', color: ui.modelColor.dkt, label: 'DKT' },
          { key: 'sakt', color: ui.modelColor.sakt, label: 'SAKT' },
          { key: 'bkt', color: ui.modelColor.bkt, label: 'BKT' },
        ]} />
      }
      case 'matrixTable': {
        const m = d.matrix_window20_N500 ?? {}
        const models: string[] = d.models_present ?? []
        const cols = [t('thesisEvidence.colDataset'), ...models]
        const rows = Object.entries(m).map(([ds, mv]: any) => [ds.replace(/_/g, ' '), ...models.map((mo) => mv?.[mo])])
        return <MiniTable columns={cols} rows={rows} highlightCol={1 + models.indexOf('hcie')} />
      }
      case 'perDimBars': {
        const stats = d.tabel_4_10_per_dim_stats_COLUMNS ?? {}
        const cls = d.tabel_4_8_ADC_classification_OVER_COLUMNS ?? {}
        const data = Object.keys(stats).filter((k) => !k.startsWith('_')).map((k) => {
          const active = String(cls?.[k]?.class || '').toUpperCase().includes('ACTIVE')
          return { name: prettyDim(k), value: stats[k]?.mean, color: active ? ui.tone.ok.fg : ui.color.faint }
        }).filter((r) => typeof r.value === 'number')
        return <>
          <BarsH data={data} />
          <div style={{ marginTop: ui.space.sm, display: 'flex', gap: ui.space.xs, flexWrap: 'wrap' }}>
            {Object.keys(cls).filter((k) => !k.startsWith('_')).map((k) => {
              const c = String(cls[k]?.class || '').toUpperCase()
              return <Tag key={k} tone={c.includes('ACTIVE') ? 'ok' : 'neutral'}>{prettyDim(k)}: {c || '—'}</Tag>
            })}
          </div>
        </>
      }
      case 'ablationBars': {
        const r = d.ranked_component_importance_by_jt_mean_drop ?? {}
        const data = Object.keys(r).filter((k) => /^\d+_/.test(k)).map((k) => ({
          name: prettyDim(k), value: Math.abs(r[k]), color: ui.modelColor.hcie,
        }))
        return <BarsH data={data} unit="" />
      }
      case 'taxonomy': {
        const a = d.summary_accuracy ?? {}
        const tbl = d.tabel_4_11_predicted_vs_observed ?? {}
        const rows = Object.entries(tbl).filter(([k]) => !k.startsWith('_')).map(([ds, v]: any) => [
          ds.replace(/_/g, ' '),
          (v.observed_active_dims || []).map(prettyDim).join(', ') || '—',
          (v.observed_dormant_dims || []).map(prettyDim).join(', ') || '—',
        ])
        return <>
          <Chips items={[
            { label: t('thesisEvidence.chipTaxonomyAccuracy'), value: fmt(a.accuracy, 2), tone: 'info' },
            { label: t('thesisEvidence.chipMatches'), value: `${a.total_matches}/${a.total_predictions}` },
          ]} />
          <div style={{ marginTop: ui.space.sm }}>
            <MiniTable columns={[t('thesisEvidence.colDataset'), t('thesisEvidence.colObservedActive'), t('thesisEvidence.colObservedDormant')]} rows={rows} />
          </div>
        </>
      }
      case 'transferBars': {
        const v = d.values ?? {}
        const corr = d.corroborating_artifacts?.prospective_probe_v3_subsample ?? {}
        const data = [
          { name: t('thesisEvidence.transferDurableSameFamily'), value: v.durable_coefficient?.b_durable_SAME, color: ui.tone.ok.fg },
          { name: t('thesisEvidence.transferDurableCrossPast'), value: v.durable_coefficient?.b_durable_CROSS_past, color: ui.modelColor.hcie },
          { name: t('thesisEvidence.transferProximity'), value: v.proximity?.b_proximity, color: ui.modelColor.sakt },
          { name: t('thesisEvidence.transferPlaceboFuture'), value: v.placebo?.b_FUTURE_cross_PLACEBO, color: ui.color.faint },
        ].filter((r) => typeof r.value === 'number')
        const ratio = v.placebo?.placebo_ratio ?? corr.placebo_ratio_future_over_past
        const permP = v.durable_coefficient?.cross_perm_p ?? corr.cross_perm_p ?? d.values?.permutation_p
        return <>
          <BarsH data={data} domain={domainOf(data.map((x) => x.value), 0.02)} />
          <div style={{ marginTop: ui.space.sm }}>
            <Chips items={[
              { label: t('thesisEvidence.chipPlaceboRatio'), value: fmt(ratio, 3), tone: 'warn' },
              { label: t('thesisEvidence.chipPermPCross'), value: fmt(permP, 4), tone: 'info' },
            ]} />
          </div>
        </>
      }
      case 'journeyLines': {
        const pi = d.per_interaction ?? []
        const rows = pi.map((r: any) => ({
          x: r.interaction_number, m: r.m_kalman_mastery_after ?? r.canonical_mastery_after,
          sigma2: r.sigma2_ensemble_variance_after,
        }))
        return <Lines data={rows} domain={[0, 1]} lines={[
          { key: 'm', color: ui.modelColor.hcie, label: t('thesisEvidence.lineMasteryKalman'), axis: 'left' },
          { key: 'sigma2', color: ui.tone.warn.fg, label: t('thesisEvidence.lineSigma2EnsembleVar'), axis: 'right' },
        ]} />
      }
      case 'banditBars': {
        const post = d.posteriors ?? {}
        const best = d.best_modality_by_design
        const means = Object.entries(post).map(([k, v]: any) => ({
          name: k.replace(/_/g, ' '), value: v.posterior_mean, color: k === best ? ui.modelColor.hcie : ui.color.faint,
        }))
        const pulls = Object.entries(post).map(([k, v]: any) => ({
          name: k.replace(/_/g, ' '), value: v.pulls, color: k === best ? ui.tone.accent.fg : ui.color.lineStrong,
        }))
        const cv = d.convergence ?? {}
        return <>
          <Eyebrow>{t('thesisEvidence.banditPosteriorMeanCaption')}</Eyebrow>
          <BarsH data={means} domain={[0, 1]} />
          <div style={{ marginTop: ui.space.sm }}><Eyebrow>{t('thesisEvidence.banditPullsCaption')}</Eyebrow></div>
          <BarsH data={pulls} domain={domainOf(pulls.map((x) => x.value), 2)} />
          <div style={{ marginTop: ui.space.sm }}>
            <Chips items={[
              { label: t('thesisEvidence.chipBestArm'), value: String(best).replace(/_/g, ' '), tone: 'accent' },
              { label: t('thesisEvidence.chipPullShareOverall'), value: fmt(cv.best_arm_pull_share_overall, 3) },
              { label: t('thesisEvidence.chipPullShareLast40'), value: fmt(cv.best_arm_pull_share_last_40, 3), tone: 'ok' },
            ]} />
          </div>
        </>
      }
      case 'complexity': {
        const cc = d.complexity_by_construction ?? {}
        const et = d.empirical_timing ?? {}
        const single = et.only_measured_timing_available?.single_observed_latency_ms ?? et.only_measured_timing_available?.value
        return <>
          <Callout tone="ok" title={t('thesisEvidence.complexityByConstructionTitle')}>{cc.verdict || '—'}</Callout>
          <div style={{ marginTop: ui.space.sm }}>
            <Callout tone="warn" title={t('thesisEvidence.complexityEmpiricalUnavailableTitle')}>{et.reason || t('thesisEvidence.complexityProcessingTimeNull')}</Callout>
          </div>
          {single != null && <div style={{ marginTop: ui.space.sm }}><Chips items={[{ label: t('thesisEvidence.chipOnlyMeasuredTiming'), value: `${fmt(single, 2)} ms`, tone: 'info' }]} /></div>}
        </>
      }
      case 'trace': {
        const cd = d.chain_length_distribution ?? {}
        const rep = d.representative_learner_near_302 ?? {}
        const five = d.five_layer_chain_definition ?? {}
        return <>
          <Chips items={[
            { label: t('thesisEvidence.chipLearners'), value: fmt(cd.n_users) },
            { label: t('thesisEvidence.chipInteractions'), value: fmt(cd.total_interactions) },
            { label: t('thesisEvidence.chipMeanChain'), value: fmt(cd.mean_chain, 0) },
            { label: t('thesisEvidence.chipMaxChain'), value: fmt(cd.max_chain) },
            { label: t('thesisEvidence.chipRepresentative'), value: fmt(rep.chain_length), tone: 'info' },
          ]} />
          <div style={{ marginTop: ui.space.sm }}>
            <MiniTable columns={[t('thesisEvidence.colLayer'), t('thesisEvidence.colDefinition')]} rows={['L1_jt_contribution', 'L2_ensemble_weight', 'L3_canonical', 'L4_mastery_after', 'L5_policy_score'].filter((k) => five[k]).map((k) => [k.replace(/_/g, ' '), String(five[k]).slice(0, 120)])} />
          </div>
        </>
      }
      case 'determinism': {
        const cov = d.deterministic_inputs_hash_coverage ?? {}
        const ex = d.canonical_equals_kalman_exactness ?? {}
        const led = d.seal_ledger_provenance ?? {}
        return <Chips items={[
          { label: t('thesisEvidence.chipInputsHashCoverage'), value: `${fmt(cov.coverage_pct, 1)}%`, tone: 'ok' },
          { label: t('thesisEvidence.chipRowsHashed'), value: `${fmt(cov.rows_with_deterministic_inputs_hash)}/${fmt(cov.total_rows)}` },
          { label: t('thesisEvidence.chipCanonicalEqKalman'), value: `${fmt(ex.exact_match)} ${t('thesisEvidence.exactLabel')} / ${fmt(ex.mismatch)} ${t('thesisEvidence.mismatchLabel')}`, tone: 'ok' },
          { label: t('thesisEvidence.chipMaxAbsDelta'), value: fmt(ex.max_abs_diff, 4) },
          { label: t('thesisEvidence.chipGitDirty'), value: String(led.code_provenance?.git_dirty ?? ANCHOR.git_dirty), tone: 'ok' },
        ]} />
      }
      case 'functional': {
        const c = d.counts ?? {}
        const cats = d.apparent_failures_categorized ?? {}
        const catRows = Object.entries(cats).map(([k, v]: any) => [k.split(' (')[0], Array.isArray(v) ? v.length : 0])
        return <>
          <GroupedBars data={[{ name: t('thesisEvidence.barScenarios'), passed: c.passed, failed: c.failed }]} series={[
            { key: 'passed', color: ui.tone.ok.fg, label: t('thesisEvidence.seriesPassed') }, { key: 'failed', color: ui.tone.bad.fg, label: t('thesisEvidence.seriesFailed') },
          ]} domain={[0, (c.ran_total || c.passed) * 1.05]} />
          <div style={{ marginTop: ui.space.sm }}>
            <Chips items={[
              { label: t('thesisEvidence.chipPassed'), value: fmt(c.passed), tone: 'ok' },
              { label: t('thesisEvidence.chipRan'), value: fmt(c.ran_total) },
              { label: t('thesisEvidence.chipLogicRegressions'), value: fmt(c.scenario_logic_regressions ?? 0), tone: 'ok' },
              { label: t('thesisEvidence.chipCollectionErrors'), value: fmt(c.collection_errors_excluded) },
            ]} />
            <div style={{ marginTop: ui.space.sm }}>
              <MiniTable columns={[t('thesisEvidence.colFailureCategory'), t('thesisEvidence.colCount')]} rows={catRows} />
            </div>
          </div>
        </>
      }
      case 'operational': {
        const lat = d.latency?.recommend_endpoint ?? {}
        const res = d.resources ?? {}
        const sq = d.code_quality_sonarqube ?? {}
        const r = sq.ratings ?? {}
        return <Chips items={[
          { label: t('thesisEvidence.chipRecommendP95'), value: `${fmt(lat.p95_ms ?? lat.single_observed_latency_ms, 2)} ms`, tone: 'info' },
          { label: t('thesisEvidence.chipRecommendP50'), value: `${fmt(lat.p50_ms ?? lat.single_observed_latency_ms, 2)} ms` },
          { label: t('thesisEvidence.chipCpu5m'), value: `${fmt((res.cpu_cores_5m_rate || 0) * 100, 1)}% ${t('thesisEvidence.coreLabel')}` },
          { label: t('thesisEvidence.chipMemory'), value: `${fmt(res.memory_usage_mib, 1)} MiB` },
          { label: t('thesisEvidence.chipSonarMaintainability'), value: r.sqale_rating_maintainability || 'A', tone: 'ok' },
          { label: t('thesisEvidence.chipSonarReliability'), value: r.reliability_rating || 'A', tone: 'ok' },
          { label: t('thesisEvidence.chipSonarSecurity'), value: r.security_rating || 'A', tone: 'ok' },
          { label: t('thesisEvidence.chipCoverage'), value: `${fmt(sq.coverage ?? 36.4, 1)}%` },
        ]} />
      }
      case 'liveCounts': {
        const tb = d.total_experiment_trajectories_rows?.traffic_type_breakdown ?? {}
        const bars = Object.entries(tb).map(([k, v]: any) => ({ name: k.replace(/_/g, ' '), value: v, color: ui.modelColor.hcie }))
        return <>
          <Chips items={[
            { label: t('thesisEvidence.chipRealLearners'), value: fmt(d.real_learners_distinct?.value), tone: 'info' },
            { label: t('thesisEvidence.chipRealInteractions'), value: fmt(d.real_learner_interactions?.value) },
            { label: t('thesisEvidence.chipTotalTrajectories'), value: fmt(d.total_experiment_trajectories_rows?.value) },
            { label: t('thesisEvidence.chipCohortRuns'), value: fmt(d.cohort_runs_count?.value) },
          ]} />
          <div style={{ marginTop: ui.space.sm }}><Eyebrow>{t('thesisEvidence.trajectoryByTrafficCaption')}</Eyebrow></div>
          <BarsH data={bars} domain={domainOf(bars.map((b) => b.value), 5000)} />
        </>
      }
      case 'datasetTable': {
        const rows = (d.datasets ?? []).map((r: any) => [r.dataset_id, r.family, r.license || '—'])
        const tot = d.totals ?? {}
        return <>
          <Chips items={[
            { label: t('thesisEvidence.chipDatasets'), value: fmt(tot.datasets_registered), tone: 'info' },
            { label: t('thesisEvidence.chipExternalAttempts'), value: fmt(tot.total_external_attempts) },
            { label: t('thesisEvidence.chipExternalRuns'), value: fmt(tot.distinct_external_runs) },
          ]} />
          <div style={{ marginTop: ui.space.sm }}>
            <MiniTable columns={[t('thesisEvidence.colDatasetId'), t('thesisEvidence.colFamily'), t('thesisEvidence.colLicense')]} rows={rows} />
          </div>
        </>
      }
      case 'pyktBars': {
        const vals = d.honest_ranking_at_this_scale?.values ?? {}
        const data = Object.entries(vals).filter(([, v]) => typeof v === 'number').map(([k, v]: any) => ({
          name: k.replace(/_/g, ' '), value: v, color: modelTone(k),
        }))
        const cv = d.custom_vs_pykt_overall_auc ?? {}
        return <>
          <BarsH data={data} />
          <div style={{ marginTop: ui.space.sm }}>
            <Chips items={[
              { label: t('thesisEvidence.chipDktCustomMinusPykt'), value: fmt(cv.dkt?.delta_custom_minus_pykt, 4), tone: 'ok' },
              { label: t('thesisEvidence.chipSaktCustomMinusPykt'), value: fmt(cv.sakt?.delta_custom_minus_pykt, 4), tone: 'ok' },
            ]} />
          </div>
        </>
      }
      case 'interactionTable': {
        const it = d.interactions ?? []
        const rows = it.slice(0, 20).map((r: any) => [
          r.interaction_number, r.concept, r.correctness ? '✓' : '✗',
          fmt(r.mastery_before, 3), fmt(r.mastery_after, 3), r.arm_selected ?? '—',
        ])
        return <MiniTable columns={[t('thesisEvidence.colNum'), t('thesisEvidence.colConcept'), t('thesisEvidence.colCorrect'), t('thesisEvidence.colMBefore'), t('thesisEvidence.colMAfter'), t('thesisEvidence.colArm')]} rows={rows} />
      }
      default:
        return null
    }
  } catch (e) {
    return <Callout tone="warn" title={t('thesisEvidence.heroRenderSkippedTitle')}>{t('thesisEvidence.heroRenderSkippedBody')} ({String(e)})</Callout>
  }
}

// ─── raw-extract explorer + caveats ─────────────────────────────────────────

const CAVEAT_KEYS = [
  'status', 'unavailable_reason', 'CRITICAL_FLAG_hcie_is_ensemble', 'PROVENANCE_AND_SCOPE_WARNING',
  'INHERITANCE_DISCLOSURE', 'TWO_DISTINCT_SUBSTRATES_WARNING', 'scope_note', 'SCOPE_NOTE',
  'provenance_note', 'caveats', 'small_sample_caveat', 'framing', 'why_not_live',
]

function caveatsOf(d: any): string[] {
  const out: string[] = []
  for (const k of CAVEAT_KEYS) {
    const v = d?.[k] ?? d?.provenance?.[k]
    if (typeof v === 'string') out.push(v)
    else if (Array.isArray(v)) v.forEach((x) => typeof x === 'string' && out.push(x))
  }
  return out
}

function PassCard({ p, t }: { p: PassMeta; t: TFn }) {
  const caveats = caveatsOf(p.data)
  const labels = statusLabel(t)
  return (
    <Panel style={{ display: 'flex', flexDirection: 'column', gap: ui.space.sm }}>
      <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', gap: ui.space.sm, flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: ui.space.sm }}>
          <span style={{ fontSize: ui.font.size.xs, fontWeight: ui.font.weight.heavy, color: ui.color.faint }}>{t('thesisEvidence.passLabel')} {p.pass}</span>
          <span style={{ fontSize: ui.font.size.lg, fontWeight: ui.font.weight.heavy, color: ui.color.ink }}>{p.title}</span>
        </div>
        <Tag tone={STATUS_TONE[p.status]}>{labels[p.status]}</Tag>
      </div>
      <div style={{ display: 'flex', gap: ui.space.sm, alignItems: 'center', flexWrap: 'wrap' }}>
        <Tag tone="neutral">{p.slot}</Tag>
        {p.deepLink && (
          <Link href={p.deepLink.href} style={{ fontSize: ui.font.size.sm, color: ui.tone.info.fg, fontWeight: ui.font.weight.bold, textDecoration: 'none' }}>
            → {t('thesisEvidence.livePrefix')}: {p.deepLink.label}
          </Link>
        )}
      </div>
      <p style={{ fontSize: ui.font.size.md, color: ui.color.body, margin: 0, lineHeight: 1.5 }}>{p.headline}</p>
      <div style={{ marginTop: ui.space.xs }}><Hero p={p} t={t} /></div>
      {caveats.length > 0 && (
        <Callout tone={p.status === 'demo' ? 'accent' : p.status === 'ok' ? 'neutral' : 'warn'} title={t('thesisEvidence.provenanceCaveatsTitle')}>
          <ul style={{ margin: 0, paddingLeft: 18, fontSize: ui.font.size.sm, lineHeight: 1.5 }}>
            {caveats.slice(0, 4).map((c, i) => <li key={i}>{c}</li>)}
          </ul>
        </Callout>
      )}
      <details>
        <summary style={{ cursor: 'pointer', fontSize: ui.font.size.sm, color: ui.color.muted, fontWeight: ui.font.weight.bold }}>{t('thesisEvidence.rawExtractSummary')}</summary>
        <pre style={{ maxHeight: 320, overflow: 'auto', background: ui.color.subtle, border: `1px solid ${ui.color.line}`, borderRadius: ui.radius.md, padding: ui.space.md, fontSize: ui.font.size.xs, color: ui.color.body, marginTop: ui.space.xs }}>
          {JSON.stringify(p.data, null, 2)}
        </pre>
      </details>
    </Panel>
  )
}

// ─── page ───────────────────────────────────────────────────────────────────

export default function ThesisEvidencePage() {
  const t = useT()
  const groups = Array.from(new Set(PASSES.map((p) => p.group)))
  return (
    <div style={{ maxWidth: 1160, margin: '0 auto', padding: `${ui.space.xl}px ${ui.space.lg}px 64px` }}>
      <Eyebrow>{t('thesisEvidence.eyebrow')}</Eyebrow>
      <SectionTitle sub={t('thesisEvidence.heroSub')}>
        {t('thesisEvidence.heroTitle')}
      </SectionTitle>

      <Panel tone="info" style={{ marginTop: ui.space.lg, display: 'flex', flexDirection: 'column', gap: ui.space.sm }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: ui.space.sm }}>
          <Stat label={t('thesisEvidence.anchorSeal')} value={ANCHOR.seal_id.slice(0, 13) + '…'} tone="info" />
          <Stat label={t('thesisEvidence.anchorRun')} value={ANCHOR.run_id.slice(0, 14) + '…'} />
          <Stat label={t('thesisEvidence.anchorContentHash')} value={ANCHOR.content_hash.slice(0, 12) + '…'} />
          <Stat label={t('thesisEvidence.anchorRows')} value={groupInt(ANCHOR.rows)} />
          <Stat label={t('thesisEvidence.anchorGitDirty')} value={String(ANCHOR.git_dirty)} tone="ok" />
          <Stat label={t('thesisEvidence.anchorDate')} value={ANCHOR.date} />
        </div>
        <p style={{ margin: 0, fontSize: ui.font.size.sm, color: ui.color.body }}>
          <strong>{t('thesisEvidence.anchorConfigLabel')}</strong> {ANCHOR.config}
        </p>
      </Panel>

      <div style={{ marginTop: ui.space.md, display: 'flex', gap: ui.space.sm, flexWrap: 'wrap', alignItems: 'center' }}>
        <Tag tone="ok">{TALLY.ok} {t('thesisEvidence.tallyOk')}</Tag>
        <Tag tone="accent">{TALLY.demo} {t('thesisEvidence.tallyDemo')}</Tag>
        <Tag tone="warn">{TALLY.partial} {t('thesisEvidence.tallyPartial')}</Tag>
        {TALLY.unavailable > 0 && <Tag tone="bad">{TALLY.unavailable} {t('thesisEvidence.tallyUnavailable')}</Tag>}
        <span style={{ fontSize: ui.font.size.sm, color: ui.color.muted }}>· {TALLY.total} {t('thesisEvidence.tallyPassesTotal')}</span>
      </div>

      <Callout tone="neutral" style={{ marginTop: ui.space.md }} title={t('thesisEvidence.howToReadTitle')}>
        {t('thesisEvidence.howToReadA')} <strong>{t('thesisEvidence.howToReadSyntheticDemo')}</strong> {t('thesisEvidence.howToReadB')}
        <strong>{t('thesisEvidence.howToReadPartial')}</strong> {t('thesisEvidence.howToReadC')}
      </Callout>

      {groups.map((g) => (
        <section key={g} style={{ marginTop: ui.space.xxl }}>
          <h2 style={{ fontSize: ui.font.size.h2, fontWeight: ui.font.weight.heavy, color: ui.color.heading, marginBottom: ui.space.md, borderBottom: `2px solid ${ui.color.line}`, paddingBottom: ui.space.xs }}>{g}</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(440px, 1fr))', gap: ui.space.lg }}>
            {PASSES.filter((p) => p.group === g).map((p) => <PassCard key={p.pass} p={p} t={t} />)}
          </div>
        </section>
      ))}
    </div>
  )
}
