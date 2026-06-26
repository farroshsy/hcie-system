'use client'

/**
 * Ablation Studies — "which design choices matter?"
 *
 * Two studies:
 *  ⑤ R12 graph on/off — attempted control, now withdrawn after sealed
 *     re-derivation showed a confounded, sign-unstable graph-OFF condition.
 *  ④ JT-dimension ablation — drop each of the 6 JT dims, measure JT-signal drop.
 *     ⚠ smoke-scale: mastery-outcome flat; only JT signal moves. Honestly labeled.
 *
 * Data: GET /v3/frontend/dashboard/ablation
 */

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { getBackendUrl } from '@/lib/api/backend-url'
import { useT } from '@/contexts/language_context'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
  LineChart, Line, Legend,
} from 'recharts'

const BACKEND = getBackendUrl()
function getAuthHeaders(): HeadersInit {
  const token = (typeof window !== 'undefined' &&
    (localStorage.getItem('hcie_auth_token') || localStorage.getItem('access_token'))) || ''
  return token ? { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' } : { 'Content-Type': 'application/json' }
}

const DIM_LABEL: Record<string, string> = {
  baseline: 'Baseline (all 6)',
  no_delta_m: '− ΔM (mastery gain)',
  no_transfer_realized: '− Transfer realized',
  no_transfer_prospective: '− Transfer prospective',
  no_challenge: '− Challenge',
  no_uncertainty: '− Uncertainty',
  no_zpd: '− ZPD',
  ablate_all: 'Ablate all',
}

export default function AblationPage() {
  const t = useT()
  const [data, setData] = useState<any>(null)
  const [window, setWindow] = useState<'w5' | 'w10' | 'w20' | 'overall'>('w5')

  useEffect(() => {
    (async () => {
      try {
        const r = await fetch(`${BACKEND}/v3/frontend/dashboard/ablation`,
          { headers: getAuthHeaders(), signal: AbortSignal.timeout(12000) })
        if (r.ok) setData(await r.json())
      } catch { /* empty */ }
    })()
  }, [])

  const r12 = data?.r12
  const jt = (data?.jt_dimensions ?? []).filter((d: any) => !d.is_baseline)
  const jtSorted = [...jt].sort((a, b) => (b.jt_drop_vs_baseline ?? 0) - (a.jt_drop_vs_baseline ?? 0))

  // R12 line data
  const r12Line = r12 ? [
    { x: 'First 5', on: r12.graph_on_auc?.w5, off: r12.graph_off_auc?.w5 },
    { x: 'First 10', on: r12.graph_on_auc?.w10, off: r12.graph_off_auc?.w10 },
    { x: 'First 20', on: r12.graph_on_auc?.w20, off: r12.graph_off_auc?.w20 },
    { x: 'All', on: r12.graph_on_auc?.overall, off: r12.graph_off_auc?.overall },
  ] : []

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: '24px 20px' }}>

      {/* Intent */}
      <div style={{ marginBottom: 12 }}>
        <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.1em',
                      color: '#C0392B', textTransform: 'uppercase', marginBottom: 4 }}>
          {t('ablation.eyebrow')}
        </div>
        <h1 style={{ fontSize: 22, fontWeight: 800, color: '#1A2332', margin: 0 }}>
          {t('ablation.title')}
        </h1>
        <div style={{ fontSize: 12, color: '#718096', marginTop: 4, maxWidth: 760, lineHeight: 1.5 }}>
          {t('ablation.intro')}
        </div>
      </div>

      {/* ══ ⑤ R12 GRAPH ON/OFF — withdrawn attempted control ════════════════ */}
      {r12 && (
        <div style={{ background: '#fff', border: '2px solid #F5B7B1', borderRadius: 12,
                      padding: '18px 20px', marginBottom: 16 }}>
          <div style={{ fontSize: 14, fontWeight: 800, color: '#C0392B', marginBottom: 2 }}>
            ⑤ R12 graph on/off — withdrawn attempted control
          </div>
          <div style={{ fontSize: 12, color: '#4A5568', lineHeight: 1.6, marginBottom: 14 }}>
            R12 replayed the same 10 held-out users with graph injection disabled, but re-derivation showed
            the graph-OFF condition is not an independent control. The live graph-OFF runtime path drifted
            enough to flip the delta&apos;s sign, so no R12 ΔAUC is citable. The causal topology claim rests
            on the ability-matched shuffled-DAG control.
          </div>

          <div style={{ display: 'flex', gap: 12, marginBottom: 14, flexWrap: 'wrap' }}>
            <Stat label="R12 ΔAUC" value="withdrawn" color="#C0392B" big />
            <Stat label="Causal topology lift" value="+0.053" color="#117A65" />
            <Stat label="Matched interactions" value={(r12.n_matched?.overall ?? 0).toLocaleString()} color="#2980B9" />
          </div>

          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={r12Line} margin={{ left: 0, right: 20, top: 8, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
              <XAxis dataKey="x" tick={{ fontSize: 11, fill: '#4A5568' }} axisLine={false} tickLine={false} />
              <YAxis domain={[0.55, 0.8]} tickFormatter={v => `${(v*100).toFixed(0)}%`}
                tick={{ fontSize: 10, fill: '#A0AEC0' }} axisLine={false} tickLine={false} />
              <Tooltip formatter={(v: any, n: any) => [`${(Number(v)*100).toFixed(1)}%`, n === 'on' ? 'Graph ON' : 'Graph OFF']} />
              <Legend formatter={(v) => v === 'on' ? 'Graph ON (Phase-2)' : 'Graph OFF (R12)'} wrapperStyle={{ fontSize: 11 }} />
              <Line dataKey="on" stroke="#117A65" strokeWidth={3} dot={{ r: 4 }} type="monotone" />
              <Line dataKey="off" stroke="#C0392B" strokeWidth={2} strokeDasharray="5 4" dot={{ r: 3 }} type="monotone" />
            </LineChart>
          </ResponsiveContainer>
          <div style={{ marginTop: 10, fontSize: 11, color: '#718096', lineHeight: 1.6,
                        background: '#F8F9FF', border: '1px solid #C3CFE2', borderRadius: 8, padding: '10px 12px' }}>
            <strong>Withdrawn:</strong> the plotted R12 values are retained only as an attempted-control audit trail.
            They no longer support a graph-presence causal magnitude. Use the shuffled-DAG control for the sealed
            causal topology effect (+0.053, p&lt;0.01).
          </div>
        </div>
      )}

      {/* ══ ④ JT-DIMENSION ABLATION — smoke-scale, JT-signal contribution ═════ */}
      {data?.jt_dimensions?.length > 0 && (
        <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 12,
                      padding: '18px 20px', marginBottom: 16 }}>
          <div style={{ fontSize: 14, fontWeight: 800, color: '#1A2332', marginBottom: 2 }}>
            ④ JT 6-dimension ablation — contribution to the JT signal
          </div>
          {/* honest smoke caveat */}
          <div style={{ background: '#FDEDEC', border: '1px solid #F5B7B1', borderRadius: 8,
                        padding: '10px 14px', margin: '8px 0 14px' }}>
            <span style={{ fontSize: 11, fontWeight: 800, color: '#C0392B' }}>⚠ SMOKE-SCALE</span>
            <span style={{ fontSize: 11, color: '#922B21', marginLeft: 8 }}>{data.jt_caveat}</span>
          </div>

          <div style={{ fontSize: 12, color: '#4A5568', marginBottom: 12, lineHeight: 1.5 }}>
            Each bar = how much the average JT value <strong>drops</strong> when that dimension is removed.
            Bigger drop = more load-bearing.
          </div>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={jtSorted.map((d: any) => ({ name: DIM_LABEL[d.condition] ?? d.condition, value: d.jt_drop_vs_baseline, cond: d.condition }))}
                      layout="vertical" margin={{ left: 30, right: 30, top: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#F1F5F9" />
              <XAxis type="number" tickFormatter={v => v.toFixed(3)} tick={{ fontSize: 10, fill: '#A0AEC0' }} axisLine={false} tickLine={false} />
              <YAxis type="category" dataKey="name" width={150} tick={{ fontSize: 10, fill: '#4A5568' }} axisLine={false} tickLine={false} />
              <Tooltip formatter={(v: any) => [`−${Number(v).toFixed(4)} JT`, 'drop']} />
              <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                {jtSorted.map((d: any, i: number) => (
                  <Cell key={i} fill={d.condition === 'ablate_all' ? '#C0392B'
                    : (d.jt_drop_vs_baseline ?? 0) < 0.005 ? '#CBD5E0' : '#8E44AD'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <div style={{ marginTop: 10, fontSize: 11, color: '#718096', lineHeight: 1.6,
                        background: '#F8F9FF', border: '1px solid #C3CFE2', borderRadius: 8, padding: '10px 12px' }}>
            <strong>Reads consistent with the audit:</strong> removing <em>transfer_prospective</em> barely
            moves JT (≈0 drop) — confirming it's the <strong>dormant 6th dimension</strong> (hardcoded 0 on the
            recorded path). Uncertainty, challenge, and ΔM carry the most signal. Grey bars = negligible
            contribution. A results-grade version (mastery outcome, full N) is part of the sealed re-run.
          </div>
        </div>
      )}

      {/* nav */}
      <div style={{ display: 'flex', gap: 10, marginTop: 8, justifyContent: 'center', flexWrap: 'wrap' }}>
        <Link href="/dashboard/instructor" style={{ fontSize: 13, fontWeight: 600, color: '#4A5568',
          textDecoration: 'none', padding: '10px 24px', borderRadius: 8, border: '1px solid #CBD5E0', background: '#fff' }}>
          ← Instructor Dashboard
        </Link>
        <Link href="/dashboard/benchmarks" style={{ fontSize: 13, fontWeight: 700, color: '#9A7D0A',
          textDecoration: 'none', padding: '10px 24px', borderRadius: 8, border: '1px solid #F9E79F', background: '#FEF9E7' }}>
          📊 KT Benchmark →
        </Link>
      </div>
    </div>
  )
}

function Stat({ label, value, color, big }: { label: string; value: any; color: string; big?: boolean }) {
  return (
    <div style={{ background: `${color}0D`, border: `1px solid ${color}40`, borderRadius: 8,
                  padding: big ? '14px 20px' : '10px 14px', minWidth: big ? 160 : 120 }}>
      <div style={{ fontSize: 9, fontWeight: 700, color: '#718096', textTransform: 'uppercase' }}>{label}</div>
      <div style={{ fontSize: big ? 28 : 18, fontWeight: 800, color }}>{value}</div>
    </div>
  )
}
