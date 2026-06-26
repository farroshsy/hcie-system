'use client'

/**
 * Self-Audit Controls — "is the instrument honest?"
 *
 *  ⑥ Topology taxonomy: ADC predicts active/dormant per dataset, then checks
 *     itself. 8/8 match → the instrument predicts its own behaviour.
 *  ⑦ Shuffled-DAG null: real DAG ≡ permuted DAG ≠ no DAG → the live signal is
 *     graph-PRESENCE, not topology-CORRECTNESS. The corrected +0.053 finding (full-corpus seal).
 *
 * This is the methods keystone: an instrument rigorous enough to calibrate its
 * own headline.  Data: GET /v3/frontend/dashboard/audit-controls
 */

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { getBackendUrl } from '@/lib/api/backend-url'
import { useT } from '@/contexts/language_context'
import { Panel, Tag, Callout, SectionTitle, Eyebrow } from '@/lib/ui/primitives'
import { t as ui } from '@/lib/ui/theme'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, LabelList } from 'recharts'

const BACKEND = getBackendUrl()
function getAuthHeaders(): HeadersInit {
  const token = (typeof window !== 'undefined' &&
    (localStorage.getItem('hcie_auth_token') || localStorage.getItem('access_token'))) || ''
  return token ? { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' } : { 'Content-Type': 'application/json' }
}

export default function AuditPage() {
  const t = useT()
  const [data, setData] = useState<any>(null)
  useEffect(() => {
    (async () => {
      try {
        const r = await fetch(`${BACKEND}/v3/frontend/dashboard/audit-controls`,
          { headers: getAuthHeaders(), signal: AbortSignal.timeout(12000) })
        if (r.ok) setData(await r.json())
      } catch { /* empty */ }
    })()
  }, [])

  const topo = data?.topology
  const sd = data?.shuffled_dag
  const cf = sd?.corrected_finding

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: `${ui.space.xxl}px ${ui.space.xl}px 64px` }}>

      {/* Intent / framing */}
      <Eyebrow color={ui.tone.accent.fg}>{t('audit.eyebrow')}</Eyebrow>
      <SectionTitle sub={t('audit.intro')}>
        {t('audit.title')}
      </SectionTitle>

      {data?.framing && (
        <Panel
          style={{
            marginTop: ui.space.lg, marginBottom: ui.space.lg,
            background: 'linear-gradient(135deg, #F4ECF7, #EBF5FB)',
            borderColor: ui.tone.accent.border,
          }}
        >
          <div style={{ fontSize: ui.font.size.md, color: ui.color.heading, lineHeight: 1.6 }}>
            🔬 <strong>{data.framing}</strong>
          </div>
        </Panel>
      )}

      {/* ══ ⑥ TOPOLOGY TAXONOMY — ADC self-prediction scoreboard ══════════════ */}
      {topo && (
        <Panel pad="xl" style={{ marginBottom: ui.space.lg }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                        flexWrap: 'wrap', gap: ui.space.sm, marginBottom: ui.space.xs }}>
            <SectionTitle>⑥ Topology taxonomy-consistency — does the transfer signal fire only where the graph is?</SectionTitle>
            <Tag tone="ok" style={{ fontSize: ui.font.size.base }}>
              {topo.n_match}/{topo.n_total} taxonomy-consistent
            </Tag>
          </div>
          <div style={{ fontSize: ui.font.size.base, color: ui.color.body, lineHeight: 1.6, marginBottom: ui.space.lg }}>
            Before measuring, the ADC <strong>classifies each dataset's graph structure</strong> and predicts
            whether the transfer dimension will be ACTIVE or a structural-zero (dormant). Then it checks the
            prediction against what actually happened. A perfect score means the instrument understands the
            conditions under which it fires.
          </div>

          <Callout tone="info" style={{ marginBottom: ui.space.lg }}>
            <strong>Self-prediction proper (L4 · Tabel 4.11): 18 / 24 = 0.75.</strong> The ADC&apos;s preregistered
            per-dimension activation prediction across 4 cross-dataset structure classes (assistments-2015 4/6,
            csedm 5/6, ednet 5/6, junyi 4/6); the 6 misses are challenge over-predicted active on flat topologies
            (4/4) and zpd borderline (2/4). The {topo.n_match}/{topo.n_total} scoreboard below is the coarser
            transfer-dimension <em>taxonomy-consistency</em>, not the self-prediction metric.
          </Callout>

          <div style={{ overflowX: 'auto', border: `1px solid ${ui.color.line}`, borderRadius: ui.radius.md }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: ui.font.size.base }}>
              <thead>
                <tr style={{ background: ui.color.subtle, borderBottom: `2px solid ${ui.color.line}` }}>
                  {['Dataset', 'Topology class', 'ADC predicted', 'Observed', 'Match'].map(h => (
                    <th key={h} style={{ padding: `${ui.space.sm}px ${ui.space.md}px`, textAlign: 'left',
                                         color: ui.color.muted, fontWeight: ui.font.weight.bold, fontSize: ui.font.size.sm,
                                         textTransform: 'uppercase', letterSpacing: '0.04em' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {topo.datasets.map((d: any) => {
                  const active = d.adc_prediction === 'ACTIVE'
                  return (
                    <tr key={d.dataset_id} style={{ borderBottom: `1px solid ${ui.color.grid}`,
                                                    background: active ? ui.tone.ok.bg : ui.color.surface }}>
                      <td style={{ padding: `${ui.space.sm}px ${ui.space.md}px`, fontWeight: ui.font.weight.bold, color: ui.color.ink }}>{d.display_name}</td>
                      <td style={{ padding: `${ui.space.sm}px ${ui.space.md}px`, color: ui.color.muted, fontFamily: 'monospace', fontSize: ui.font.size.sm }}>{d.topology_class}</td>
                      <td style={{ padding: `${ui.space.sm}px ${ui.space.md}px` }}>
                        <Tag tone={active ? 'ok' : 'warn'}>{d.adc_prediction}</Tag>
                      </td>
                      <td style={{ padding: `${ui.space.sm}px ${ui.space.md}px` }}>
                        <Tag tone={d.observed_class === 'ACTIVE' ? 'ok' : 'warn'}>{d.observed_class}</Tag>
                      </td>
                      <td style={{ padding: `${ui.space.sm}px ${ui.space.md}px` }}>
                        {d.adc_match
                          ? <span style={{ color: ui.tone.ok.fg, fontWeight: ui.font.weight.heavy, fontSize: ui.font.size.md }}>✓</span>
                          : <span style={{ color: ui.tone.bad.fg, fontWeight: ui.font.weight.heavy, fontSize: ui.font.size.md }}>✗</span>}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
          <div style={{ marginTop: ui.space.md, fontSize: ui.font.size.sm, color: ui.color.muted, lineHeight: 1.6 }}>
            Only <strong>Junyi Phase-2</strong> (graph injected) is predicted — and observed — ACTIVE. Every
            graph-less dataset is correctly predicted dormant. The ADC knows the difference.
          </div>
        </Panel>
      )}

      {/* ══ ⑦ SHUFFLED-DAG NULL — presence vs correctness ════════════════════ */}
      {sd && (
        <Panel pad="xl" tone="bad" style={{ marginBottom: ui.space.lg, background: ui.color.surface, borderWidth: 2 }}>
          <SectionTitle sub={
            <>
              The decisive control. Compare the real prerequisite graph against a <strong>degree+weight-preserving
              shuffle</strong> (same statistics, scrambled connections) and no graph. If the signal needs correct
              topology, the shuffle should collapse to the no-graph level. If it only needs graph presence, real ≈
              shuffled.
            </>
          }>
            ⑦ Shuffled-DAG control — does the graph need to be <em>correct</em>?
          </SectionTitle>

          {/* Condition comparison — event fraction chart + verdict cards */}
          <div style={{ width: '100%', height: 220, marginBottom: ui.space.md }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={sd.conditions.map((c: any) => ({
                  label: c.label,
                  pct: c.event_fraction * 100,
                  verdict: c.verdict,
                  mean_transfer: c.mean_transfer,
                }))}
                margin={{ top: 24, right: 16, left: 8, bottom: 8 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke={ui.color.grid} vertical={false} />
                <XAxis dataKey="label" tick={{ fontSize: ui.font.size.sm, fill: ui.color.body }}
                       tickLine={false} axisLine={{ stroke: ui.color.lineStrong }} />
                <YAxis unit="%" tick={{ fontSize: ui.font.size.sm, fill: ui.color.muted }}
                       tickLine={false} axisLine={false}
                       label={{ value: 'event fraction', angle: -90, position: 'insideLeft',
                                style: { fontSize: ui.font.size.sm, fill: ui.color.muted, textAnchor: 'middle' } }} />
                <Tooltip
                  cursor={{ fill: ui.color.subtle }}
                  contentStyle={{ fontSize: ui.font.size.sm, borderRadius: ui.radius.md, border: `1px solid ${ui.color.line}` }}
                  formatter={(v: any, _n: any, p: any) => [`${Number(v).toFixed(1)}%  ·  mean transfer ${p?.payload?.mean_transfer?.toFixed(5)}  ·  ${p?.payload?.verdict}`, 'event fraction']}
                />
                <Bar dataKey="pct" radius={[ui.radius.sm, ui.radius.sm, 0, 0]} maxBarSize={120}>
                  {sd.conditions.map((c: any, i: number) => (
                    <Cell key={i} fill={c.verdict === 'ACTIVE' ? ui.tone.ok.fg : ui.tone.bad.fg} />
                  ))}
                  <LabelList dataKey="pct" position="top"
                             formatter={(v: any) => `${Number(v).toFixed(1)}%`}
                             style={{ fontSize: ui.font.size.sm, fontWeight: ui.font.weight.bold, fill: ui.color.heading }} />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: ui.space.md, marginBottom: ui.space.lg }}>
            {sd.conditions.map((c: any) => {
              const isActive = c.verdict === 'ACTIVE'
              return (
                <Panel key={c.label} pad="md" tone={isActive ? 'ok' : 'bad'}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: ui.space.sm, marginBottom: ui.space.sm }}>
                    <span style={{ fontSize: ui.font.size.base, fontWeight: ui.font.weight.heavy, color: ui.color.ink }}>{c.label}</span>
                    <Tag tone={isActive ? 'ok' : 'bad'}>{c.verdict}</Tag>
                  </div>
                  <div style={{ fontSize: ui.font.size.xs, color: ui.color.muted, textTransform: 'uppercase', letterSpacing: '0.04em' }}>event fraction</div>
                  <div style={{ fontSize: ui.font.size.h2, fontWeight: ui.font.weight.heavy, color: ui.color.heading }}>{(c.event_fraction * 100).toFixed(1)}%</div>
                  <div style={{ fontSize: ui.font.size.xs, color: ui.color.muted, marginTop: ui.space.xs }}>mean transfer {c.mean_transfer.toFixed(5)}</div>
                </Panel>
              )
            })}
          </div>

          <Callout tone="warn" title="Result: real ≡ permuted." style={{ marginBottom: ui.space.md }}>
            {sd.real_vs_permuted}. The live transfer signal detects
            graph <strong>presence</strong>, not edge <strong>correctness</strong> — a caution for any graph-KT
            method that claims its DAG matters without this control.
          </Callout>

          {cf && (
            <Panel pad="md" tone="info">
              <Callout tone="warn"
                title="Offline outcome-grounded replication: a small placebo-corrected residual — NOT clean causal">
                <div style={{ display: 'flex', gap: ui.space.lg, flexWrap: 'wrap', margin: `${ui.space.sm}px 0 ${ui.space.md}px` }}>
                  <MiniStat label="real − shuffled" value={`+${cf.real_minus_shuffled}`} color={ui.modelColor.hcie} />
                  <MiniStat label="perm-p" value={cf.p_value} color={ui.tone.ok.fg} />
                  <MiniStat label="placebo-corr. residual" value={`+${cf.durable_component}`} color={ui.modelColor.irt_1pl} />
                </div>
                <div style={{ fontSize: ui.font.size.sm, color: ui.color.body, lineHeight: 1.6 }}>
                  <strong>Placebo-corrected durable residual ≈ +0.053</strong> (durable 0.091 − time-placebo 0.038);
                  placebo ratio ≈ 0.42; perm-p ≈ 0.0099. <strong>NOT net/clean causal.</strong> Illustrative live
                  snapshot — sealed decomposition on <code>/review/topology</code> (S9).
                </div>
              </Callout>
              <div style={{ fontSize: ui.font.size.sm, color: ui.color.body, lineHeight: 1.6, marginTop: ui.space.md }}>{cf.note}</div>
            </Panel>
          )}
        </Panel>
      )}

      {/* nav */}
      <div style={{ display: 'flex', gap: ui.space.md, marginTop: ui.space.sm, justifyContent: 'center', flexWrap: 'wrap' }}>
        <Link href="/dashboard/instructor" style={{ fontSize: ui.font.size.md, fontWeight: ui.font.weight.medium, color: ui.color.body,
          textDecoration: 'none', padding: `${ui.space.sm}px ${ui.space.xxl}px`, borderRadius: ui.radius.md, border: `1px solid ${ui.color.lineStrong}`, background: ui.color.surface }}>
          ← Instructor Dashboard
        </Link>
        <Link href="/dashboard/ablation" style={{ fontSize: ui.font.size.md, fontWeight: ui.font.weight.bold, color: ui.tone.bad.fg,
          textDecoration: 'none', padding: `${ui.space.sm}px ${ui.space.xxl}px`, borderRadius: ui.radius.md, border: `1px solid ${ui.tone.bad.border}`, background: ui.tone.bad.bg }}>
          🔬 Ablation Studies →
        </Link>
        <a href="/review/methods" target="_blank" rel="noopener noreferrer" style={{ fontSize: ui.font.size.md, fontWeight: ui.font.weight.bold, color: ui.tone.info.fg,
          textDecoration: 'none', padding: `${ui.space.sm}px ${ui.space.xxl}px`, borderRadius: ui.radius.md, border: `1px solid ${ui.tone.info.border}`, background: ui.tone.info.bg }}>
          📄 Methods Sandbox (paper) →
        </a>
      </div>
    </div>
  )
}

function MiniStat({ label, value, color }: { label: string; value: any; color: string }) {
  return (
    <div>
      <div style={{ fontSize: ui.font.size.xs, fontWeight: ui.font.weight.bold, color: ui.color.muted, textTransform: 'uppercase', letterSpacing: '0.04em' }}>{label}</div>
      <div style={{ fontSize: ui.font.size.xl, fontWeight: ui.font.weight.heavy, color }}>{value}</div>
    </div>
  )
}
