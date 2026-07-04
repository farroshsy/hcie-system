'use client'

/**
 * Know Your Data — the substrate the benchmark sits on.
 *
 * Six tabs (Tier 0h+0j evidence panels for publication):
 *  1. Profiles        — all 8 external datasets: counts, density, correct-rate,
 *                       response-time, interactions-per-user histogram, raw rows.
 *  2. Schema          — source CSV columns vs canonical external_log_attempts
 *                       columns vs live Postgres information_schema dump,
 *                       plus per-dataset residency (rows/users/concepts/runs).
 *  3. Junyi Graph     — node-link DAG of the 4,208 prerequisite edges
 *                       (only junyi_2015_graph has one).
 *  4. Graph Build     — graph_method distribution, transfer-weight histogram,
 *                       edge-validity audit notes (Vuong / null-DAG control).
 *  5. Verdict         — Tier-0 audit decision per dataset (DISCLOSE / REPROCESS
 *                       / EXCLUDE) with sealed lineage row counts.
 *  6. Reproducibility — Tier 0j chain of custody: source-file sha256, adapter
 *                       sha256, DB residency, optional replay-stream sha256,
 *                       and a REPRODUCIBLE/DRIFT/STALE verdict. Re-runnable
 *                       via tier0j_dataset_reingest.py.
 *
 * Data:
 *   GET /v3/frontend/dashboard/datasets
 *   GET /v3/frontend/dashboard/datasets/{id}/sample
 *   GET /v3/frontend/dashboard/concept-graph/{id}
 *   GET /v3/frontend/dashboard/dataset-evidence-overview     (Tier 0h)
 *   GET /v3/frontend/dashboard/dataset-evidence/{id}         (Tier 0h)
 *   GET /v3/frontend/dashboard/dataset-reingest-status       (NEW — Tier 0j)
 */

import { useEffect, useState, useCallback, useMemo } from 'react'
import Link from 'next/link'
import { getBackendUrl } from '@/lib/api/backend-url'
import { useT } from '@/contexts/language_context'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from 'recharts'
import ReactFlow, { Background, Controls, MarkerType, type Node, type Edge } from 'reactflow'
import 'reactflow/dist/style.css'

const BACKEND = getBackendUrl()

// Deterministic LCG so the layout is stable across renders.
function makeRng(seed: number) {
  let s = seed >>> 0
  return () => {
    s = (s * 1664525 + 1013904223) >>> 0
    return s / 0xFFFFFFFF
  }
}

// Force-directed layout (Fruchterman–Reingold flavor) — replaces the earlier
// grid-packed layered layout. Cheap velocity-Verlet sim with O(n²) repulsion,
// Hooke spring along edges, and a centering pull. Junyi's shown subgraph is
// ~80 nodes so 300 iterations is ~milliseconds. Deterministic via seeded RNG.
function forceLayout(
  rawNodes: any[],
  rawEdges: any[],
  opts: { width?: number; height?: number; iterations?: number; seed?: number } = {},
): Record<string, { x: number; y: number }> {
  const { width = 900, height = 460, iterations = 300, seed = 1337 } = opts
  const ids = rawNodes.map(n => n.id)
  const idSet = new Set(ids)
  const edges = rawEdges.filter(e => idSet.has(e.source) && idSet.has(e.target))
  const rng = makeRng(seed)
  type P = { x: number; y: number; vx: number; vy: number }
  const pos: Record<string, P> = {}
  ids.forEach(id => {
    pos[id] = {
      x: width / 2 + (rng() - 0.5) * width * 0.7,
      y: height / 2 + (rng() - 0.5) * height * 0.7,
      vx: 0, vy: 0,
    }
  })
  const REPULSION = 4200
  const SPRING_LEN = 130
  const SPRING_K = 0.04
  const CENTER_K = 0.006
  const DAMPING = 0.82
  const MAX_DELTA = 28
  const CUTOFF = 260

  for (let it = 0; it < iterations; it++) {
    // pairwise repulsion
    for (let i = 0; i < ids.length; i++) {
      const a = pos[ids[i]]
      for (let j = i + 1; j < ids.length; j++) {
        const b = pos[ids[j]]
        const dx = a.x - b.x
        const dy = a.y - b.y
        const d2 = dx * dx + dy * dy + 0.01
        const d = Math.sqrt(d2)
        if (d > CUTOFF) continue
        const f = REPULSION / d2
        const fx = (dx / d) * f
        const fy = (dy / d) * f
        a.vx += fx; a.vy += fy
        b.vx -= fx; b.vy -= fy
      }
    }
    // edge springs — weight scales pull
    for (const e of edges) {
      const a = pos[e.source]
      const b = pos[e.target]
      const dx = b.x - a.x
      const dy = b.y - a.y
      const d = Math.sqrt(dx * dx + dy * dy) + 0.01
      const w = Math.max(0.3, Math.min(2.0, (e.weight ?? 1)))
      const f = SPRING_K * (d - SPRING_LEN) * w
      const fx = (dx / d) * f
      const fy = (dy / d) * f
      a.vx += fx; a.vy += fy
      b.vx -= fx; b.vy -= fy
    }
    // centering pull + integrate
    for (const id of ids) {
      const p = pos[id]
      p.vx += (width / 2 - p.x) * CENTER_K
      p.vy += (height / 2 - p.y) * CENTER_K
      p.vx *= DAMPING
      p.vy *= DAMPING
      // clamp per-step delta to keep things stable
      const dx = Math.max(-MAX_DELTA, Math.min(MAX_DELTA, p.vx))
      const dy = Math.max(-MAX_DELTA, Math.min(MAX_DELTA, p.vy))
      p.x += dx
      p.y += dy
    }
  }
  const out: Record<string, { x: number; y: number }> = {}
  for (const id of ids) out[id] = { x: pos[id].x, y: pos[id].y }
  return out
}

function buildReactFlow(rawNodes: any[], rawEdges: any[]): { nodes: Node[]; edges: Edge[] } {
  const idSet = new Set(rawNodes.map(n => n.id))
  const pos = forceLayout(rawNodes, rawEdges)

  const nodes: Node[] = rawNodes.map(n => {
    const totalDeg = (n.in_degree ?? 0) + (n.out_degree ?? 0)
    const isHub = totalDeg >= 4
    return {
      id: n.id,
      position: pos[n.id] ?? { x: 0, y: 0 },
      data: { label: n.label },
      style: {
        background: isHub ? '#117A65' : '#fff',
        color: isHub ? '#fff' : '#2C3E50',
        border: `1px solid ${isHub ? '#0E6655' : '#A2D9CE'}`,
        borderRadius: 8, fontSize: 10, padding: '6px 10px',
        width: 180, textAlign: 'center' as const,
      },
    }
  })

  const edges: Edge[] = rawEdges
    .filter(e => idSet.has(e.source) && idSet.has(e.target))
    .map((e, i) => ({
      id: `e${i}`, source: e.source, target: e.target,
      style: { stroke: '#A2D9CE', strokeWidth: Math.max(0.5, (e.weight ?? 0.4) * 2.5) },
      markerEnd: { type: MarkerType.ArrowClosed, color: '#A2D9CE' },
      animated: false,
    }))

  return { nodes, edges }
}

function getAuthHeaders(): HeadersInit {
  const token = (typeof window !== 'undefined' &&
    (localStorage.getItem('hcie_auth_token') || localStorage.getItem('access_token'))) || ''
  return token ? { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }
               : { 'Content-Type': 'application/json' }
}

const COL_DICT = [
  ['user_id', 'Learner identity (run-scoped)'],
  ['concept_id', 'Skill / knowledge component'],
  ['task_id', 'Specific problem attempted'],
  ['attempt_index', 'Position in the learner sequence'],
  ['correct', 'Was the answer right?'],
  ['response_time', 'Seconds to answer'],
  ['raw_timestamp', 'Original log timestamp'],
  ['source_user_id', 'Provenance: original dataset user'],
  ['source_skill_id', 'Provenance: original dataset skill'],
]

type TabId = 'profiles' | 'schema' | 'graph' | 'graph-build' | 'verdict' | 'reproducibility'

export default function DataPage() {
  const t = useT()
  const [tab, setTab] = useState<TabId>('profiles')
  const [datasets, setDatasets] = useState<any[]>([])
  const [selected, setSelected] = useState<string>('')
  const [sample, setSample] = useState<any>(null)
  const [graph, setGraph] = useState<any>(null)
  const [loadingSample, setLoadingSample] = useState(false)
  const [loadingGraph, setLoadingGraph] = useState(false)
  const [audit, setAudit] = useState<any>(null)
  const [loadingAudit, setLoadingAudit] = useState(false)
  // Tier 0h: dataset evidence panels (schema / verdict / graph build).
  const [evidence, setEvidence] = useState<any>(null)
  const [overview, setOverview] = useState<any>(null)
  const [loadingEvidence, setLoadingEvidence] = useState(false)
  const [loadingOverview, setLoadingOverview] = useState(false)
  // Tier 0j: dataset reproducibility chain of custody.
  const [reingest, setReingest] = useState<any>(null)
  const [loadingReingest, setLoadingReingest] = useState(false)

  useEffect(() => {
    (async () => {
      try {
        const r = await fetch(`${BACKEND}/v3/frontend/dashboard/datasets`,
          { headers: getAuthHeaders(), signal: AbortSignal.timeout(12000) })
        if (!r.ok) return
        const d = await r.json()
        setDatasets(d.datasets ?? [])
        if (d.datasets?.length) setSelected(d.datasets[0].dataset_id)
      } catch { /* empty */ }
    })()
  }, [])

  const loadSample = useCallback(async (id: string) => {
    if (!id) return
    setLoadingSample(true)
    try {
      const r = await fetch(`${BACKEND}/v3/frontend/dashboard/datasets/${id}/sample?limit=25`,
        { headers: getAuthHeaders(), signal: AbortSignal.timeout(12000) })
      if (r.ok) setSample(await r.json())
    } catch { /* keep */ } finally { setLoadingSample(false) }
  }, [])

  const loadGraph = useCallback(async (id: string) => {
    setLoadingGraph(true)
    try {
      const r = await fetch(`${BACKEND}/v3/frontend/dashboard/concept-graph/${id}?limit=300`,
        { headers: getAuthHeaders(), signal: AbortSignal.timeout(14000) })
      if (r.ok) setGraph(await r.json())
    } catch { /* keep */ } finally { setLoadingGraph(false) }
  }, [])

  const loadAudit = useCallback(async (id: string) => {
    if (!id) return
    setLoadingAudit(true)
    try {
      const r = await fetch(`${BACKEND}/v3/frontend/dashboard/dataset-audit/${encodeURIComponent(id)}`,
        { headers: getAuthHeaders(), signal: AbortSignal.timeout(12000) })
      if (r.ok) setAudit(await r.json())
    } catch { setAudit(null) } finally { setLoadingAudit(false) }
  }, [])

  // Tier 0h: per-dataset full evidence packet (Schema + Graph Build tabs).
  const loadEvidence = useCallback(async (id: string) => {
    if (!id) return
    setLoadingEvidence(true)
    try {
      const r = await fetch(`${BACKEND}/v3/frontend/dashboard/dataset-evidence/${encodeURIComponent(id)}`,
        { headers: getAuthHeaders(), signal: AbortSignal.timeout(14000) })
      if (r.ok) setEvidence(await r.json())
    } catch { setEvidence(null) } finally { setLoadingEvidence(false) }
  }, [])

  // Tier 0h: cross-dataset residency + verdict overview (Verdict tab).
  const loadOverview = useCallback(async () => {
    setLoadingOverview(true)
    try {
      const r = await fetch(`${BACKEND}/v3/frontend/dashboard/dataset-evidence-overview`,
        { headers: getAuthHeaders(), signal: AbortSignal.timeout(14000) })
      if (r.ok) setOverview(await r.json())
    } catch { setOverview(null) } finally { setLoadingOverview(false) }
  }, [])

  // Tier 0j: chain-of-custody / reproducibility evidence.
  const loadReingest = useCallback(async () => {
    setLoadingReingest(true)
    try {
      const r = await fetch(`${BACKEND}/v3/frontend/dashboard/dataset-reingest-status`,
        { headers: getAuthHeaders(), signal: AbortSignal.timeout(14000) })
      if (r.ok) setReingest(await r.json())
    } catch { setReingest(null) } finally { setLoadingReingest(false) }
  }, [])

  useEffect(() => { if (selected && tab === 'profiles') { loadSample(selected); loadAudit(selected) } }, [selected, tab, loadSample, loadAudit])
  useEffect(() => { if (selected && (tab === 'schema' || tab === 'graph-build')) loadEvidence(selected) }, [selected, tab, loadEvidence])
  useEffect(() => { if (tab === 'verdict') loadOverview() }, [tab, loadOverview])
  useEffect(() => { if (tab === 'reproducibility') loadReingest() }, [tab, loadReingest])
  // graph tab always uses junyi_2015_graph (the only one with a graph)
  useEffect(() => { if (tab === 'graph') loadGraph('junyi_2015_graph') }, [tab, loadGraph])

  const sel = datasets.find(d => d.dataset_id === selected)
  const pct = (v: number | null) => v != null ? `${(v * 100).toFixed(1)}%` : '—'

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: '24px 20px' }}>

      {/* Header */}
      <div style={{ marginBottom: 12 }}>
        <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.1em',
                      color: '#1A5276', textTransform: 'uppercase', marginBottom: 4 }}>
          {t('data.eyebrow')}
        </div>
        <h1 style={{ fontSize: 22, fontWeight: 800, color: '#1A2332', margin: 0 }}>
          {t('data.title')}
        </h1>
        <div style={{ fontSize: 12, color: '#718096', marginTop: 4, maxWidth: 740, lineHeight: 1.5 }}>
          {t('data.datasetIntro')}{' '}
          <Link href="/dashboard/benchmarks" style={{ color: '#9A7D0A' }}>{t('nav.benchmarks')}</Link>.
        </div>
      </div>

      {/* Tabs — Tier 0h+0j evidence panels for publication */}
      <div style={{ display: 'flex', gap: 2, marginBottom: 18, borderBottom: '2px solid #E2E8F0', flexWrap: 'wrap' }}>
        {([
          ['profiles',         'Dataset Profiles'],
          ['schema',           'Schema & Pipeline'],
          ['graph',            'Junyi Graph'],
          ['graph-build',      'Graph Build'],
          ['verdict',          'Audit Verdict'],
          ['reproducibility',  'Reproducibility'],
        ] as const).map(([id, lbl]) => (
          <button key={id} onClick={() => setTab(id as TabId)} style={{
            padding: '8px 18px', fontSize: 13, fontWeight: 600, background: 'none', border: 'none',
            cursor: 'pointer', color: tab === id ? '#1A5276' : '#718096',
            borderBottom: tab === id ? '2px solid #1A5276' : '2px solid transparent', marginBottom: -2,
          }}>{lbl}</button>
        ))}
      </div>

      {/* ════ TAB: PROFILES ════════════════════════════════════════════════════ */}
      {tab === 'profiles' && (
        <>
          {/* Comparison table */}
          <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10,
                        padding: '16px 20px', marginBottom: 16, overflowX: 'auto' }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: '#2C3E50', marginBottom: 12 }}>
              All datasets at a glance — click a row to inspect
            </div>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
              <thead>
                <tr style={{ borderBottom: '2px solid #E2E8F0' }}>
                  {['Dataset', 'Rows', 'Users', 'Concepts', 'Per user', 'Correct', 'Avg RT', 'Graph'].map(h => (
                    <th key={h} style={{ padding: '6px 10px', textAlign: h === 'Dataset' ? 'left' : 'right',
                                         color: '#718096', fontWeight: 700, fontSize: 11 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {datasets.map(d => {
                  const active = selected === d.dataset_id
                  return (
                    <tr key={d.dataset_id} onClick={() => setSelected(d.dataset_id)} style={{
                      borderBottom: '1px solid #F7FAFC', cursor: 'pointer',
                      background: active ? '#EBF5FB' : '#fff',
                    }}>
                      <td style={{ padding: '8px 10px', fontWeight: 700, color: '#1A2332' }}>
                        {d.label}
                        <div style={{ fontSize: 9, color: '#A0AEC0', fontWeight: 400 }}>{d.origin}</div>
                      </td>
                      <td style={{ padding: '8px 10px', textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>{d.rows.toLocaleString()}</td>
                      <td style={{ padding: '8px 10px', textAlign: 'right' }}>{d.users}</td>
                      <td style={{ padding: '8px 10px', textAlign: 'right', fontWeight: 700,
                                   color: d.concepts < 15 ? '#C0392B' : '#2C3E50' }}>{d.concepts}</td>
                      <td style={{ padding: '8px 10px', textAlign: 'right' }}>{d.interactions_per_user}</td>
                      <td style={{ padding: '8px 10px', textAlign: 'right',
                                   color: (d.correct_rate ?? 0) > 0.85 ? '#E67E22' : (d.correct_rate ?? 0) < 0.4 ? '#C0392B' : '#1E8449' }}>
                        {pct(d.correct_rate)}
                      </td>
                      <td style={{ padding: '8px 10px', textAlign: 'right', color: '#718096' }}>
                        {d.avg_response_time != null ? `${d.avg_response_time.toFixed(0)}s` : '—'}
                      </td>
                      <td style={{ padding: '8px 10px', textAlign: 'right' }}>
                        {d.has_graph
                          ? <span style={{ fontSize: 10, fontWeight: 700, color: '#1E8449', background: '#D5F5E3',
                                           borderRadius: 4, padding: '2px 6px' }}>✓ {d.graph_edges}</span>
                          : <span style={{ color: '#CBD5E0' }}>—</span>}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
            <div style={{ marginTop: 10, fontSize: 11, color: '#718096', lineHeight: 1.5 }}>
              Note the spread: <strong>EdNet has 7 concepts, Junyi-graph has 596</strong>; correct-rate runs
              0.27 (CSEDM, hard) → 0.93 (STATICS, easy). These shapes drive the benchmark differences.
            </div>
          </div>

          {/* Tier 0 contamination audit */}
          {sel && (
            <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10,
                          padding: '16px 20px', marginBottom: 16 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 700, color: '#2C3E50' }}>
                    {sel.label} — contamination audit (Tier 0)
                  </div>
                  <div style={{ fontSize: 11, color: '#718096' }}>
                    Split-leakage, duplicates, edge validity, PyKT parity — from sealed lineage reports
                  </div>
                </div>
                <Link href="/dashboard/method-grounding" style={{ fontSize: 11, color: '#1A5276', fontWeight: 600 }}>
                  Full cascade →
                </Link>
              </div>
              {loadingAudit && <div style={{ fontSize: 11, color: '#A0AEC0' }}>Loading audit…</div>}
              {audit && !loadingAudit && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 10 }}>
                  {[
                    ['Decision', audit.decision || '—', audit.decision === 'EXCLUDE' ? '#C0392B' : audit.decision === 'REPROCESS' ? '#9A7D0A' : '#1A5276'],
                    ['Dup triples', audit.contamination_flags?.find((f: string) => f.startsWith('duplicate'))?.split('=')[1] ?? '0', '#2C3E50'],
                    ['Graph edges', audit.graph?.edges ?? '—', '#2C3E50'],
                    ['Flags', (audit.contamination_flags?.length ?? 0).toString(), audit.contamination_flags?.length ? '#E67E22' : '#1E8449'],
                  ].map(([lbl, val, col]) => (
                    <div key={lbl as string} style={{ background: '#F8FAFC', borderRadius: 8, padding: '10px 12px' }}>
                      <div style={{ fontSize: 10, color: '#A0AEC0', fontWeight: 700, textTransform: 'uppercase' }}>{lbl}</div>
                      <div style={{ fontSize: 14, fontWeight: 800, color: col as string, marginTop: 4 }}>{val}</div>
                    </div>
                  ))}
                </div>
              )}
              {audit?.contamination_flags?.length > 0 && (
                <ul style={{ margin: '12px 0 0', paddingLeft: 18, fontSize: 11, color: '#718096', lineHeight: 1.6 }}>
                  {audit.contamination_flags.map((f: string) => <li key={f}>{f}</li>)}
                </ul>
              )}
              {audit?.lineage && (
                <div style={{ marginTop: 10, fontSize: 11, color: '#4A5568', lineHeight: 1.5 }}>
                  Sealed trajectories: {audit.lineage.sealed_trajectory_rows ?? '—'} ·
                  parity: {audit.lineage.pykt_parity ?? 'see tier0_lineage_audit.json'}
                </div>
              )}
            </div>
          )}

          {/* Selected dataset detail */}
          {sel && (
            <div style={{ display: 'grid',
                          gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
                          gap: 16, marginBottom: 16 }}>
              {/* Interactions-per-user histogram */}
              <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10, padding: '16px 20px' }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: '#2C3E50', marginBottom: 2 }}>
                  {sel.label} — interactions per user
                </div>
                <div style={{ fontSize: 11, color: '#718096', marginBottom: 12 }}>
                  How much history each learner has — the cold-start sparsity picture
                </div>
                {sample?.histogram && (
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={sample.histogram} margin={{ left: 0, right: 10, top: 4, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                      <XAxis dataKey="bucket" tick={{ fontSize: 10, fill: '#4A5568' }} axisLine={false} tickLine={false} />
                      <YAxis tick={{ fontSize: 10, fill: '#A0AEC0' }} axisLine={false} tickLine={false} />
                      <Tooltip formatter={(v: any) => [`${v} users`, '']} />
                      <Bar dataKey="users" radius={[4, 4, 0, 0]} fill="#2980B9" />
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </div>

              {/* Column dictionary */}
              <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10, padding: '16px 20px' }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: '#2C3E50', marginBottom: 12 }}>
                  Columns — what each row records
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {COL_DICT.map(([col, desc]) => (
                    <div key={col} style={{ display: 'flex', gap: 10, fontSize: 11 }}>
                      <code style={{ fontFamily: 'monospace', color: '#1A5276', fontWeight: 700,
                                     minWidth: 120 }}>{col}</code>
                      <span style={{ color: '#718096' }}>{desc}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Raw row sampler */}
          {sel && (
            <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10,
                          padding: '16px 20px', overflowX: 'auto' }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: '#2C3E50', marginBottom: 2 }}>
                {sel.label} — raw interaction rows
              </div>
              <div style={{ fontSize: 11, color: '#718096', marginBottom: 12 }}>
                Actual data, ordered by learner + attempt index {loadingSample && '· loading…'}
              </div>
              {sample?.sample?.length > 0 && (
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11 }}>
                  <thead>
                    <tr style={{ borderBottom: '2px solid #E2E8F0' }}>
                      {['user', 'concept', 'task', '#', 'correct', 'rt(s)', 'timestamp'].map(h => (
                        <th key={h} style={{ padding: '5px 8px', textAlign: 'left', color: '#718096',
                                             fontWeight: 700, fontSize: 10 }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {sample.sample.map((row: any, i: number) => (
                      <tr key={i} style={{ borderBottom: '1px solid #F7FAFC' }}>
                        <td style={{ padding: '5px 8px', fontFamily: 'monospace', color: '#718096' }}>
                          {String(row.user_id ?? '').split('::').pop()?.slice(-14)}
                        </td>
                        <td style={{ padding: '5px 8px', color: '#4A5568' }}>
                          {String(row.concept_id ?? '').replace(/^ext_[^_]+_/, '')}
                        </td>
                        <td style={{ padding: '5px 8px', color: '#A0AEC0', fontFamily: 'monospace' }}>
                          {String(row.task_id ?? '').slice(-12)}
                        </td>
                        <td style={{ padding: '5px 8px', textAlign: 'right' }}>{row.attempt_index}</td>
                        <td style={{ padding: '5px 8px' }}>
                          {row.correct
                            ? <span style={{ color: '#1E8449', fontWeight: 700 }}>✓</span>
                            : <span style={{ color: '#C0392B', fontWeight: 700 }}>✗</span>}
                        </td>
                        <td style={{ padding: '5px 8px', textAlign: 'right', color: '#718096' }}>
                          {row.response_time != null ? row.response_time.toFixed(0) : '—'}
                        </td>
                        <td style={{ padding: '5px 8px', color: '#A0AEC0', fontSize: 10 }}>
                          {row.raw_timestamp?.slice(0, 19) ?? '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}
        </>
      )}

      {/* ════ TAB: SCHEMA & PIPELINE (Tier 0h) ════════════════════════════════ */}
      {tab === 'schema' && (
        <SchemaPipelineTab
          datasets={datasets}
          selected={selected}
          setSelected={setSelected}
          evidence={evidence}
          loading={loadingEvidence}
        />
      )}

      {/* ════ TAB: GRAPH BUILD (Tier 0h, Junyi-only) ══════════════════════════ */}
      {tab === 'graph-build' && (
        <GraphBuildTab
          datasets={datasets}
          selected={selected}
          setSelected={setSelected}
          evidence={evidence}
          loading={loadingEvidence}
        />
      )}

      {/* ════ TAB: AUDIT VERDICT (Tier 0h) ════════════════════════════════════ */}
      {tab === 'verdict' && (
        <VerdictTab overview={overview} loading={loadingOverview} />
      )}

      {/* ════ TAB: REPRODUCIBILITY (Tier 0j) ══════════════════════════════════ */}
      {tab === 'reproducibility' && (
        <ReproducibilityTab reingest={reingest} loading={loadingReingest} />
      )}

      {/* ════ TAB: JUNYI GRAPH ═════════════════════════════════════════════════ */}
      {tab === 'graph' && (
        <div>
          <div style={{ background: 'linear-gradient(135deg, #EBF5FB, #E8F8F5)',
                        border: '1px solid #A2D9CE', borderRadius: 10, padding: '14px 18px', marginBottom: 16 }}>
            <div style={{ fontSize: 12, fontWeight: 800, color: '#117A65', marginBottom: 4 }}>
              🕸 The prerequisite structure that activates HCIE's transfer dimension
            </div>
            <div style={{ fontSize: 12, color: '#2C3E50', lineHeight: 1.6 }}>
              Only <strong>Junyi</strong> has an explicit concept graph. Each edge is a prerequisite link
              <strong> source → target</strong> with a transfer weight (annotation strength). This is why
              Phase-2 Junyi is HCIE's full-prowess setting — on graph-less datasets the transfer dimension
              stays dormant and HCIE leans on ADC instead.
              {graph?.status === 'ok' && (
                <> Showing the <strong>{graph.shown_edges}</strong> strongest of <strong>{graph.total_edges}</strong> edges.</>
              )}
            </div>
          </div>

          {loadingGraph && <div style={{ textAlign: 'center', padding: 40, color: '#718096' }}>⟳ Loading graph…</div>}

          {graph?.status === 'ok' && (
            <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10, padding: '16px 20px' }}>
              <div style={{ display: 'flex', gap: 16, marginBottom: 14, flexWrap: 'wrap' }}>
                <Stat label="Total edges" value={graph.total_edges} color="#117A65" />
                <Stat label="Concepts (nodes shown)" value={graph.nodes.length} color="#2980B9" />
                <Stat label="Method" value={graph.graph_method} color="#8E44AD" />
              </div>

              {/* ── Visual node-link DAG (top edges, force-directed layout) ─── */}
              <ForceDirectedGraph graph={graph} />


              {/* Edge list — strongest prerequisites first */}
              <div style={{ fontSize: 12, fontWeight: 700, color: '#2C3E50', marginBottom: 8 }}>
                Strongest prerequisite edges (by transfer weight)
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4, maxHeight: 460, overflowY: 'auto' }}>
                {graph.edges.slice(0, 60).map((e: any, i: number) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 11,
                                        padding: '5px 8px', borderRadius: 6,
                                        background: i % 2 ? '#F7FAFC' : '#fff' }}>
                    <span style={{ flex: 1, textAlign: 'right', color: '#4A5568', fontWeight: 600 }}>
                      {e.source_label}
                    </span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 4, minWidth: 110 }}>
                      <div style={{ width: 50, height: 5, background: '#EDF2F7', borderRadius: 3, overflow: 'hidden' }}>
                        <div style={{ height: '100%', width: `${e.weight * 100}%`, background: '#117A65', borderRadius: 3 }} />
                      </div>
                      <span style={{ color: '#117A65', fontWeight: 700, fontVariantNumeric: 'tabular-nums',
                                     minWidth: 36 }}>{e.weight.toFixed(2)}</span>
                      <span style={{ color: '#A0AEC0' }}>→</span>
                    </div>
                    <span style={{ flex: 1, color: '#1A2332', fontWeight: 700 }}>{e.target_label}</span>
                  </div>
                ))}
              </div>
              <div style={{ marginTop: 10, fontSize: 11, color: '#718096' }}>
                ⚠ Per the ADC audit, the transfer signal currently responds to graph <em>presence</em>, not
                edge <em>correctness</em> — a shuffled graph scores nearly the same. This edge list is the
                structure; validating which edges carry real transfer is the re-run's job.
              </div>
            </div>
          )}

          {graph?.status === 'no_graph' && (
            <div style={{ textAlign: 'center', padding: 40, color: '#A0AEC0' }}>
              No graph for this dataset.
            </div>
          )}
        </div>
      )}

      {/* Footer nav */}
      <div style={{ display: 'flex', gap: 10, marginTop: 24, justifyContent: 'center', flexWrap: 'wrap' }}>
        <Link href="/dashboard/instructor" style={{ fontSize: 13, fontWeight: 600, color: '#4A5568',
          textDecoration: 'none', padding: '10px 24px', borderRadius: 8,
          border: '1px solid #CBD5E0', background: '#fff' }}>
          ← Instructor Dashboard
        </Link>
        <Link href="/dashboard/benchmarks" style={{ fontSize: 13, fontWeight: 700, color: '#9A7D0A',
          textDecoration: 'none', padding: '10px 24px', borderRadius: 8,
          border: '1px solid #F9E79F', background: '#FEF9E7' }}>
          📊 KT Benchmark →
        </Link>
      </div>
    </div>
  )
}

function ForceDirectedGraph({ graph }: { graph: any }) {
  const topEdges = (graph.edges ?? []).slice(0, 80)
  const { nodes, edges } = useMemo(() => {
    const usedIds = new Set<string>()
    topEdges.forEach((e: any) => { usedIds.add(e.source); usedIds.add(e.target) })
    const usedNodes = (graph.nodes ?? []).filter((n: any) => usedIds.has(n.id))
    return buildReactFlow(usedNodes, topEdges)
  // recompute only when the graph data identity changes
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [graph])
  return (
    <div style={{ marginBottom: 16 }}>
      <div style={{ fontSize: 12, fontWeight: 700, color: '#2C3E50', marginBottom: 2 }}>
        Prerequisite DAG — top {topEdges.length} edges (force-directed)
      </div>
      <div style={{ fontSize: 11, color: '#718096', marginBottom: 8 }}>
        Arrows point prerequisite → dependent. Green = hub concept (degree ≥ 4).
        Layout solved by a small Fruchterman–Reingold sim — same seed each load, so the picture is stable.
        Drag to pan · scroll to zoom.
      </div>
      <div style={{ height: 460, border: '1px solid #E2E8F0', borderRadius: 8,
                    background: '#FAFCFE' }}>
        <ReactFlow nodes={nodes} edges={edges} fitView
                   minZoom={0.1} maxZoom={2} proOptions={{ hideAttribution: true }}>
          <Background color="#E2E8F0" gap={20} />
          <Controls showInteractive={false} />
        </ReactFlow>
      </div>
    </div>
  )
}

function Stat({ label, value, color }: { label: string; value: any; color: string }) {
  return (
    <div style={{ background: `${color}0D`, border: `1px solid ${color}40`, borderRadius: 8,
                  padding: '10px 14px', minWidth: 120 }}>
      <div style={{ fontSize: 9, fontWeight: 700, color: '#718096', textTransform: 'uppercase' }}>{label}</div>
      <div style={{ fontSize: 20, fontWeight: 800, color }}>{value}</div>
    </div>
  )
}

// ─── Tier 0h tab components ────────────────────────────────────────────────

function DatasetSwitcher({ datasets, selected, setSelected }:
  { datasets: any[]; selected: string; setSelected: (id: string) => void }) {
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 14 }}>
      {datasets.map((d: any) => (
        <button key={d.dataset_id} onClick={() => setSelected(d.dataset_id)} style={{
          fontSize: 11, fontWeight: 600, padding: '5px 10px', borderRadius: 6,
          border: selected === d.dataset_id ? '1px solid #1A5276' : '1px solid #E2E8F0',
          background: selected === d.dataset_id ? '#EBF5FB' : '#fff',
          color: selected === d.dataset_id ? '#1A5276' : '#4A5568', cursor: 'pointer',
        }}>{d.label}</button>
      ))}
    </div>
  )
}

function SchemaPipelineTab({ datasets, selected, setSelected, evidence, loading }:
  { datasets: any[]; selected: string; setSelected: (id: string) => void; evidence: any; loading: boolean }) {
  const ev = evidence?.status === 'ok' ? evidence : null
  return (
    <div>
      <div style={{ background: 'linear-gradient(135deg, #FFF8E1, #FFFDE7)',
                    border: '1px solid #F9E79F', borderRadius: 10, padding: '14px 18px', marginBottom: 16 }}>
        <div style={{ fontSize: 12, fontWeight: 800, color: '#9A7D0A', marginBottom: 4 }}>
          From CSV to Postgres — what each adapter actually does
        </div>
        <div style={{ fontSize: 12, color: '#2C3E50', lineHeight: 1.6 }}>
          Each row in <code>external_log_attempts</code> originates as a row in a published research dataset
          (TSV / CSV / log). The adapter applies a fixed transformation: source identifiers get prefixed,
          time becomes seconds, attempt position becomes a row-number. This tab shows the live Postgres
          schema next to the source schema for the selected dataset, so reviewers can verify the adapter
          contract did not lose information.
        </div>
      </div>

      <DatasetSwitcher datasets={datasets} selected={selected} setSelected={setSelected} />

      {loading && <div style={{ fontSize: 12, color: '#A0AEC0', padding: 14 }}>Loading evidence packet…</div>}

      {ev && (
        <>
          <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10,
                        padding: '16px 20px', marginBottom: 16 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: '#2C3E50', marginBottom: 8 }}>
              {ev.registry?.dataset_id} — registry record
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 10, marginBottom: 12 }}>
              {[
                ['Family', ev.registry?.family ?? '—'],
                ['Schema version', ev.registry?.schema_version ?? '—'],
                ['Concept prefix', ev.registry?.concept_prefix ?? '—'],
                ['Task prefix', ev.registry?.task_prefix ?? '—'],
                ['Adapter', ev.registry?.metadata?.adapter_class ?? '—'],
                ['Topology', ev.registry?.metadata?.topology_class ?? '—'],
              ].map(([lbl, val]: any) => (
                <div key={lbl} style={{ background: '#F8FAFC', borderRadius: 8, padding: '8px 12px' }}>
                  <div style={{ fontSize: 9, color: '#A0AEC0', fontWeight: 700, textTransform: 'uppercase' }}>{lbl}</div>
                  <div style={{ fontSize: 12, color: '#1A2332', marginTop: 2, fontFamily: lbl === 'Adapter' ? 'monospace' : 'inherit' }}>{val}</div>
                </div>
              ))}
            </div>
            {ev.registry?.citation && (
              <div style={{ fontSize: 11, color: '#4A5568', lineHeight: 1.6, marginTop: 6 }}>
                <strong>Cite:</strong> {ev.registry.citation}<br />
                <strong>License:</strong> {ev.registry.license}
              </div>
            )}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 16, marginBottom: 16 }}>
            <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10, padding: '16px 20px' }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: '#2C3E50' }}>Source schema (as shipped)</div>
              <div style={{ fontSize: 11, color: '#718096', marginBottom: 8 }}>
                {ev.source_schema?.format} · {ev.source_schema?.granularity}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 11 }}>
                {(ev.source_schema?.source_columns ?? []).map((c: any[]) => (
                  <div key={c[0]} style={{ display: 'flex', gap: 8 }}>
                    <code style={{ color: '#9A7D0A', fontWeight: 700, minWidth: 130 }}>{c[0]}</code>
                    <span style={{ color: '#4A5568' }}>{c[1]}</span>
                  </div>
                ))}
              </div>
              {ev.source_schema?.release_url && (
                <div style={{ marginTop: 8, fontSize: 11 }}>
                  <a href={ev.source_schema.release_url} target="_blank" rel="noopener noreferrer"
                     style={{ color: '#1A5276' }}>release page →</a>
                </div>
              )}
            </div>

            <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10, padding: '16px 20px' }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: '#2C3E50' }}>Postgres columns (live)</div>
              <div style={{ fontSize: 11, color: '#718096', marginBottom: 8 }}>
                <code>external_log_attempts</code> — pulled from <code>information_schema.columns</code>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 11, maxHeight: 220, overflowY: 'auto' }}>
                {(ev.postgres_schema?.external_log_attempts ?? []).map((c: any) => (
                  <div key={c.column} style={{ display: 'flex', gap: 8 }}>
                    <code style={{ color: '#1A5276', fontWeight: 700, minWidth: 150 }}>{c.column}</code>
                    <span style={{ color: '#4A5568', fontFamily: 'monospace' }}>{c.type}</span>
                    {c.nullable && <span style={{ color: '#A0AEC0', fontSize: 10 }}>NULL</span>}
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10, padding: '16px 20px', marginBottom: 16 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: '#2C3E50', marginBottom: 8 }}>
              Adapter transformation (source → canonical)
            </div>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11 }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #E2E8F0' }}>
                  {['Canonical column', 'From source', 'Rule'].map(h => (
                    <th key={h} style={{ padding: '6px 8px', textAlign: 'left', color: '#718096', fontWeight: 700, fontSize: 10 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(ev.canonical_transform ?? []).map((row: any) => (
                  <tr key={row.canonical} style={{ borderBottom: '1px solid #F7FAFC' }}>
                    <td style={{ padding: '5px 8px' }}><code style={{ color: '#1A5276', fontWeight: 700 }}>{row.canonical}</code></td>
                    <td style={{ padding: '5px 8px', color: '#9A7D0A' }}><code>{row.from}</code></td>
                    <td style={{ padding: '5px 8px', color: '#4A5568' }}>{row.rule}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10, padding: '16px 20px' }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: '#2C3E50', marginBottom: 8 }}>
              Postgres residency — where this dataset's rows actually live
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 10, marginBottom: 10 }}>
              <Stat label="Rows" value={ev.residency?.rows?.toLocaleString() ?? '—'} color="#1A5276" />
              <Stat label="Users" value={ev.residency?.users ?? '—'} color="#117A65" />
              <Stat label="Concepts" value={ev.residency?.concepts ?? '—'} color="#8E44AD" />
              <Stat label="Runs" value={ev.residency?.runs ?? '—'} color="#9A7D0A" />
              <Stat label="Graph edges" value={ev.residency?.graph_edges ?? 0} color="#117A65" />
            </div>
            {(ev.residency?.top_runs ?? []).length > 0 && (
              <>
                <div style={{ fontSize: 11, fontWeight: 700, color: '#4A5568', marginTop: 8, marginBottom: 4 }}>
                  Attached experiment runs (rows from this dataset, top 12 by row count)
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 3, fontSize: 11 }}>
                  {ev.residency.top_runs.map((r: any) => (
                    <div key={r.experiment_run_id} style={{ display: 'flex', gap: 10 }}>
                      <code style={{ color: '#4A5568', minWidth: 320 }}>{r.experiment_run_id}</code>
                      <span style={{ color: '#1A5276', fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>
                        {r.rows.toLocaleString()} rows
                      </span>
                    </div>
                  ))}
                </div>
              </>
            )}
            <div style={{ marginTop: 10, fontSize: 11, color: '#718096', lineHeight: 1.5 }}>
              Pipeline: <code>raw CSV</code> → adapter → <code>external_log_attempts</code> → cohort replay → <code>experiment_trajectories</code>.
              Both ends live in the same Postgres instance; the runtime never sees the original CSV.
            </div>
          </div>
        </>
      )}
    </div>
  )
}

function GraphBuildTab({ datasets, selected, setSelected, evidence, loading }:
  { datasets: any[]; selected: string; setSelected: (id: string) => void; evidence: any; loading: boolean }) {
  const ev = evidence?.status === 'ok' ? evidence : null
  const has = ev?.graph?.edges > 0
  return (
    <div>
      <div style={{ background: 'linear-gradient(135deg, #E8F8F5, #EBF5FB)',
                    border: '1px solid #A2D9CE', borderRadius: 10, padding: '14px 18px', marginBottom: 16 }}>
        <div style={{ fontSize: 12, fontWeight: 800, color: '#117A65', marginBottom: 4 }}>
          How the prerequisite DAG was built
        </div>
        <div style={{ fontSize: 12, color: '#2C3E50', lineHeight: 1.6 }}>
          Of the eight datasets, only Junyi 2015 ships explicit prerequisite annotations. We materialise them
          into <code>external_concept_graph</code> at run-setup time (one row per directed edge,
          unique per <code>(experiment_run_id, source, target)</code>). This panel shows the per-method
          edge count, the transfer-weight distribution, and the validity audit notes — useful for the
          Phase-2 comparison where HCIE's transfer dimension activates.
        </div>
      </div>

      <DatasetSwitcher datasets={datasets} selected={selected} setSelected={setSelected} />

      {loading && <div style={{ fontSize: 12, color: '#A0AEC0', padding: 14 }}>Loading evidence packet…</div>}

      {ev && !has && (
        <div style={{ background: '#FEF9E7', border: '1px solid #F9E79F', borderRadius: 8, padding: '12px 16px',
                      fontSize: 12, color: '#9A7D0A', lineHeight: 1.6 }}>
          <strong>{ev.registry?.dataset_id}</strong> ships no prerequisite graph in the published release
          — {ev.source_schema?.graph_source ?? 'flat skill tags only'}. This is why the transfer dimension
          stays dormant on this dataset and HCIE leans on ADC instead. Switch to <code>junyi_2015_graph</code>
          to see a real graph build.
        </div>
      )}

      {ev && has && (
        <>
          <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10, padding: '16px 20px', marginBottom: 16 }}>
            <div style={{ display: 'flex', gap: 16, marginBottom: 14, flexWrap: 'wrap' }}>
              <Stat label="Edges" value={ev.graph.edges.toLocaleString()} color="#117A65" />
              <Stat label="Methods used" value={ev.graph.method_distribution?.length ?? 0} color="#8E44AD" />
              <Stat label="Source dataset" value={ev.registry?.family} color="#1A5276" />
            </div>

            <div style={{ fontSize: 12, fontWeight: 700, color: '#2C3E50', marginBottom: 8 }}>
              Edges by graph_method
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 11, marginBottom: 14 }}>
              {(ev.graph.method_distribution ?? []).map((m: any) => (
                <div key={m.method} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <code style={{ color: '#117A65', fontWeight: 700, minWidth: 220 }}>{m.method}</code>
                  <div style={{ flex: 1, height: 8, background: '#EDF2F7', borderRadius: 3, overflow: 'hidden', maxWidth: 320 }}>
                    <div style={{ height: '100%', background: '#117A65',
                                  width: `${Math.min(100, (m.edges / ev.graph.edges) * 100)}%` }} />
                  </div>
                  <span style={{ color: '#1A2332', fontWeight: 700, fontVariantNumeric: 'tabular-nums', minWidth: 80, textAlign: 'right' }}>
                    {m.edges.toLocaleString()}
                  </span>
                </div>
              ))}
            </div>

            <div style={{ fontSize: 12, fontWeight: 700, color: '#2C3E50', marginBottom: 8 }}>
              Transfer-weight distribution
            </div>
            <ResponsiveContainer width="100%" height={170}>
              <BarChart data={ev.graph.weight_distribution ?? []} margin={{ left: 0, right: 10, top: 4, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                <XAxis dataKey="bucket" tick={{ fontSize: 10, fill: '#4A5568' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 10, fill: '#A0AEC0' }} axisLine={false} tickLine={false} />
                <Tooltip formatter={(v: any) => [`${v} edges`, '']} />
                <Bar dataKey="edges" radius={[4, 4, 0, 0]} fill="#117A65" />
              </BarChart>
            </ResponsiveContainer>

            <div style={{ marginTop: 12, fontSize: 11, color: '#718096', lineHeight: 1.5 }}>
              <strong>Source:</strong> {ev.source_schema?.graph_source ?? '—'}<br />
              <strong>Validity audit:</strong> {ev.graph.validity_note}
            </div>
          </div>

          <div style={{ background: '#FEF9E7', border: '1px solid #F9E79F', borderRadius: 8, padding: '10px 14px',
                        fontSize: 11, color: '#9A7D0A', lineHeight: 1.6 }}>
            ADC's permuted-graph control found that the transfer signal currently responds to graph
            <em> presence</em>, not edge <em>correctness</em>. The Tier 5 re-run validates whether topology
            order matters — this panel shows the structure under audit.
          </div>
        </>
      )}
    </div>
  )
}

function ReproducibilityTab({ reingest, loading }: { reingest: any; loading: boolean }) {
  const datasets = reingest?.datasets ?? []
  const summary = reingest?.summary ?? {}
  const rerun = reingest?.rerun ?? {}

  const verdictColor = (v: string): { fg: string; bg: string } => {
    if (v === 'REPRODUCIBLE') return { fg: '#1E8449', bg: '#D5F5E3' }
    if (v === 'DRIFT')        return { fg: '#9A7D0A', bg: '#FCF3CF' }
    if (v === 'STALE')        return { fg: '#C0392B', bg: '#FADBD8' }
    if (v === 'UNAVAILABLE')  return { fg: '#7F8C8D', bg: '#ECF0F1' }
    return { fg: '#4A5568', bg: '#EDF2F7' }
  }

  const fmtBytes = (n: number | undefined): string => {
    if (n == null) return '—'
    if (n < 1024) return `${n} B`
    if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`
    if (n < 1024 * 1024 * 1024) return `${(n / 1024 / 1024).toFixed(1)} MB`
    return `${(n / 1024 / 1024 / 1024).toFixed(2)} GB`
  }

  return (
    <div>
      <div style={{ background: 'linear-gradient(135deg, #E8F8F5, #FFF8E1)',
                    border: '1px solid #A2D9CE', borderRadius: 10, padding: '14px 18px', marginBottom: 16 }}>
        <div style={{ fontSize: 12, fontWeight: 800, color: '#117A65', marginBottom: 4 }}>
          Tier 0j — chain of custody from source bytes to dashboard numbers
        </div>
        <div style={{ fontSize: 12, color: '#2C3E50', lineHeight: 1.6 }}>
          Every dataset profile shown elsewhere on this page is grounded in three sha256 hashes:
          the <strong>source file</strong> (the published research release), the <strong>adapter
          code</strong> (the transformation logic), and the <strong>canonical attempt stream</strong>
          (what the adapter emits before insertion). The same script can be re-run to detect any
          change to the source CSV, the adapter implementation, or the streaming output —
          deterministic by construction. A reviewer who wants to verify our numbers downloads the
          source, runs <code>tier0j_dataset_reingest.py</code>, and checks the hashes match.
        </div>
      </div>

      {loading && <div style={{ fontSize: 12, color: '#A0AEC0', padding: 14 }}>Loading reproducibility report…</div>}

      {reingest?.status === 'no_report' && (
        <div style={{ background: '#FEF9E7', border: '1px solid #F9E79F', borderRadius: 8, padding: '12px 16px',
                      fontSize: 12, color: '#9A7D0A', lineHeight: 1.6 }}>
          No tier0j report yet. Run <code>python research_validation/grounding/scripts/tier0j_dataset_reingest.py</code> to generate one.
        </div>
      )}

      {datasets.length > 0 && (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 10, marginBottom: 16 }}>
            <Stat label="Reproducible" value={summary.reproducible ?? 0} color="#1E8449" />
            <Stat label="Drift"        value={summary.drift ?? 0}        color="#9A7D0A" />
            <Stat label="Stale"        value={summary.stale ?? 0}        color="#C0392B" />
            <Stat label="Unavailable" value={summary.unavailable ?? 0}  color="#7F8C8D" />
            <Stat label="Elapsed"      value={`${summary.elapsed_s ?? 0}s`} color="#1A5276" />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {datasets.map((d: any) => {
              const c = verdictColor(d.verdict)
              return (
                <div key={d.dataset_id}
                     style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10,
                              padding: '16px 20px' }}>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, flexWrap: 'wrap', marginBottom: 12 }}>
                    <div style={{ fontSize: 14, fontWeight: 800, color: '#1A2332' }}>{d.dataset_id}</div>
                    <div style={{ fontSize: 11, color: '#718096' }}>family <code>{d.family}</code></div>
                    <div style={{ marginLeft: 'auto' }}>
                      <span style={{ fontSize: 10, fontWeight: 800, color: c.fg, background: c.bg,
                                     borderRadius: 4, padding: '3px 10px', letterSpacing: '0.04em' }}>
                        {d.verdict}
                      </span>
                    </div>
                  </div>
                  <div style={{ fontSize: 11, color: '#4A5568', marginBottom: 12, lineHeight: 1.6 }}>
                    {d.reason}
                  </div>
                  {d.source_profile && Object.keys(d.source_profile).length > 0 && (
                    <div style={{ background: '#F8FAFC', border: '1px solid #E2E8F0', borderRadius: 8,
                                  padding: '10px 12px', marginBottom: 12, fontSize: 11, color: '#4A5568',
                                  lineHeight: 1.55 }}>
                      <div style={{ fontWeight: 800, color: '#1A5276', marginBottom: 3 }}>
                        Source scope: {d.source_profile.scope ?? 'documented sample'}
                      </div>
                      <div>{d.source_profile.raw_corpus}</div>
                      {d.source_profile.local_user_files != null && (
                        <div>Local KT1 user CSVs detected: <strong>{d.source_profile.local_user_files.toLocaleString()}</strong>.</div>
                      )}
                      <div>{d.source_profile.canonical_run_policy}</div>
                      <div style={{ marginTop: 3, color: '#718096' }}>{d.source_profile.source_hash_policy}</div>
                    </div>
                  )}

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 14 }}>
                    {/* Source files */}
                    <div>
                      <div style={{ fontSize: 11, fontWeight: 700, color: '#1A5276', textTransform: 'uppercase', marginBottom: 6, letterSpacing: '0.04em' }}>
                        Source files {d.source?.length ? `(${d.source.length})` : ''}
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                        {(d.source ?? []).map((s: any, i: number) => (
                          <div key={i} style={{ fontSize: 11, lineHeight: 1.4 }}>
                            <div style={{ color: '#1A2332', fontFamily: 'monospace', wordBreak: 'break-all' }}>
                              {(s.path ?? '').split('/').pop()}
                            </div>
                            <div style={{ color: '#A0AEC0', fontSize: 10 }}>
                              {fmtBytes(s.size_bytes)} · file sha256 <code style={{ color: '#117A65' }}>{s.sha256_short || s.sha256?.slice(0,12) || '—'}</code>
                            </div>
                          </div>
                        ))}
                        {!d.source_available && (
                          <div style={{ fontSize: 11, color: '#C0392B' }}>source files not on this host</div>
                        )}
                      </div>
                    </div>

                    {/* Adapter */}
                    <div>
                      <div style={{ fontSize: 11, fontWeight: 700, color: '#9A7D0A', textTransform: 'uppercase', marginBottom: 6, letterSpacing: '0.04em' }}>
                        Adapter
                      </div>
                      <div style={{ fontSize: 11, lineHeight: 1.5 }}>
                        <div style={{ color: '#1A2332', fontFamily: 'monospace', wordBreak: 'break-all' }}>
                          {d.adapter?.module ?? '—'}
                        </div>
                        <div style={{ color: '#A0AEC0', fontSize: 10 }}>
                          adapter code sha256 <code style={{ color: '#9A7D0A' }}>{d.adapter?.sha256_short || '—'}</code>
                        </div>
                        <div style={{ color: '#A0AEC0', fontSize: 10 }}>
                          shared KTAttempt contract sha256 <code>{d.adapter?.base_sha256_short || '—'}</code>
                        </div>
                      </div>
                    </div>

                    {/* DB residency */}
                    <div>
                      <div style={{ fontSize: 11, fontWeight: 700, color: '#117A65', textTransform: 'uppercase', marginBottom: 6, letterSpacing: '0.04em' }}>
                        Postgres canonical run
                      </div>
                      <div style={{ fontSize: 11, lineHeight: 1.5 }}>
                        <div style={{ color: '#A0AEC0', fontFamily: 'monospace', fontSize: 10 }}>
                          {d.observed?.experiment_run_id ?? '—'}
                        </div>
                        <div style={{ color: '#1A2332', marginTop: 4 }}>
                          <strong>{(d.observed?.rows ?? 0).toLocaleString()}</strong> rows ·{' '}
                          {d.observed?.users ?? 0} users · {d.observed?.concepts ?? 0} concepts
                        </div>
                        <div style={{ color: '#A0AEC0', fontSize: 10, marginTop: 2 }}>
                          combined source hash <code>{d.observed?.source_sha256_combined || '—'}</code>
                          {' · '}adapter hash <code>{d.observed?.adapter_sha256 || '—'}</code>
                        </div>
                        {d.expected && Object.keys(d.expected).length > 0 && (
                          <div style={{ color: '#A0AEC0', fontSize: 10, marginTop: 2 }}>
                            expected: {(d.expected.rows ?? 0).toLocaleString()} / {d.expected.users ?? 0} / {d.expected.concepts ?? 0}
                            {' · '}
                            {d.expected.rows === d.observed?.rows
                              ? <span style={{ color: '#1E8449' }}>match</span>
                              : <span style={{ color: '#C0392B' }}>diff</span>}
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Replay (when --replay was used, or a cached stream hash exists) */}
                    {(d.replay || d.expected?.stream_sha256 || d.observed?.stream_sha256) && (
                      <div>
                        <div style={{ fontSize: 11, fontWeight: 700, color: '#8E44AD', textTransform: 'uppercase', marginBottom: 6, letterSpacing: '0.04em' }}>
                          Stream replay
                        </div>
                        <div style={{ fontSize: 11, lineHeight: 1.5 }}>
                          {d.replay ? (
                            <>
                              <div style={{ color: '#1A2332' }}>
                                <strong>{(d.replay.rows ?? 0).toLocaleString()}</strong> attempts streamed in {d.replay.elapsed_s ?? 0}s
                              </div>
                              <div style={{ color: '#A0AEC0', fontSize: 10, marginTop: 2 }}>
                                live replay stream sha256 <code style={{ color: '#8E44AD' }}>{d.replay.stream_sha256_short || '—'}</code>
                              </div>
                              <div style={{ color: '#A0AEC0', fontSize: 10 }}>
                                cap: {d.replay.max_users} users × {d.replay.max_attempts_per_user} attempts
                              </div>
                            </>
                          ) : (
                            <div style={{ color: '#718096' }}>
                              Latest Tier-0j run was fast mode, so it did not replay the adapter stream.
                            </div>
                          )}
                          {d.observed?.stream_sha256 && (
                            <div style={{ color: '#A0AEC0', fontSize: 10, marginTop: 2 }}>
                              observed stream hash <code style={{ color: '#8E44AD' }}>{d.observed.stream_sha256}</code>
                            </div>
                          )}
                          {d.expected?.stream_sha256 && (
                            <div style={{ color: '#A0AEC0', fontSize: 10 }}>
                              cached expected stream hash <code style={{ color: '#8E44AD' }}>{d.expected.stream_sha256}</code>
                            </div>
                          )}
                          {d.replay?.error && (
                            <div style={{ color: '#C0392B', fontSize: 10, marginTop: 2 }}>error: {d.replay.error}</div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>

          <div style={{ marginTop: 16, background: '#F8FAFC', border: '1px solid #E2E8F0', borderRadius: 10, padding: '14px 18px' }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: '#2C3E50', marginBottom: 8 }}>Re-run this evidence</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: 11, fontFamily: 'monospace', color: '#4A5568' }}>
              <div><strong style={{ color: '#1A5276' }}>fast:</strong> {rerun.fast || '—'}</div>
              <div><strong style={{ color: '#1A5276' }}>deep:</strong> {rerun.deep || '—'}</div>
              <div><strong style={{ color: '#1A5276' }}>scoped:</strong> {rerun.scoped || '—'}</div>
            </div>
            <div style={{ marginTop: 8, fontSize: 11, color: '#718096', lineHeight: 1.5 }}>
              Sealed under <code>{reingest?.phase2_run_id ?? '—'}</code> · seal{' '}
              <code>{reingest?.seal_id ?? '—'}</code> · input_hash{' '}
              <code>{reingest?.input_hash ?? '—'}</code>{reingest?.finished_at && <> · {String(reingest.finished_at).slice(0,19)}Z</>}
            </div>
          </div>
        </>
      )}
    </div>
  )
}

function VerdictTab({ overview, loading }: { overview: any; loading: boolean }) {
  const datasets = overview?.datasets ?? []
  return (
    <div>
      <div style={{ background: 'linear-gradient(135deg, #FFF8E1, #FEF9E7)',
                    border: '1px solid #F9E79F', borderRadius: 10, padding: '14px 18px', marginBottom: 16 }}>
        <div style={{ fontSize: 12, fontWeight: 800, color: '#9A7D0A', marginBottom: 4 }}>
          Tier 0 — per-dataset audit decision
        </div>
        <div style={{ fontSize: 12, color: '#2C3E50', lineHeight: 1.6 }}>
          For each registered dataset we record one of three verdicts:
          <strong> DISCLOSE</strong> (use as-is, document caveats),
          <strong> REPROCESS</strong> (re-ingest with a corrected adapter),
          <strong> EXCLUDE</strong> (drop from the publication evidence).
          The decision lives in <code>tier0_dataset_decisions.json</code>; the residency counts come live
          from Postgres so a stale verdict can never hide a missing dataset.
        </div>
      </div>

      {loading && <div style={{ fontSize: 12, color: '#A0AEC0', padding: 14 }}>Loading overview…</div>}

      {datasets.length > 0 && (
        <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10, padding: '16px 20px', overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #E2E8F0' }}>
                {['Dataset', 'Family', 'In Postgres', 'Rows', 'Users', 'Concepts', 'Runs', 'Graph edges', 'Verdict'].map(h => (
                  <th key={h} style={{ padding: '6px 10px', textAlign: h === 'Dataset' || h === 'Family' ? 'left' : 'right',
                                       color: '#718096', fontWeight: 700, fontSize: 11 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {datasets.map((d: any) => {
                const verdict = d.tier0?.decision || 'DISCLOSE'
                const verdictColor = verdict === 'EXCLUDE' ? '#C0392B' : verdict === 'REPROCESS' ? '#9A7D0A' : '#1E8449'
                const verdictBg = verdict === 'EXCLUDE' ? '#FADBD8' : verdict === 'REPROCESS' ? '#FCF3CF' : '#D5F5E3'
                return (
                  <tr key={d.dataset_id} style={{ borderBottom: '1px solid #F7FAFC' }}>
                    <td style={{ padding: '8px 10px', fontWeight: 700, color: '#1A2332' }}>
                      {d.dataset_id}
                      {d.citation && (
                        <div style={{ fontSize: 9, color: '#A0AEC0', fontWeight: 400, marginTop: 2, maxWidth: 320 }}>
                          {d.citation}
                        </div>
                      )}
                    </td>
                    <td style={{ padding: '8px 10px', fontSize: 11, color: '#4A5568' }}>{d.family}</td>
                    <td style={{ padding: '8px 10px', textAlign: 'right' }}>
                      {d.in_postgres
                        ? <span style={{ fontSize: 10, fontWeight: 700, color: '#1E8449', background: '#D5F5E3',
                                         borderRadius: 4, padding: '2px 6px' }}>yes</span>
                        : <span style={{ color: '#C0392B' }}>no</span>}
                    </td>
                    <td style={{ padding: '8px 10px', textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
                      {(d.residency?.external_log_attempts_rows ?? 0).toLocaleString()}
                    </td>
                    <td style={{ padding: '8px 10px', textAlign: 'right' }}>
                      {d.residency?.external_log_attempts_users ?? 0}
                    </td>
                    <td style={{ padding: '8px 10px', textAlign: 'right' }}>
                      {d.residency?.external_log_attempts_concepts ?? 0}
                    </td>
                    <td style={{ padding: '8px 10px', textAlign: 'right' }}>
                      {d.residency?.external_log_attempts_runs ?? 0}
                    </td>
                    <td style={{ padding: '8px 10px', textAlign: 'right',
                                 color: (d.residency?.external_concept_graph_edges ?? 0) > 0 ? '#117A65' : '#CBD5E0',
                                 fontWeight: 700 }}>
                      {d.residency?.external_concept_graph_edges ?? 0}
                    </td>
                    <td style={{ padding: '8px 10px', textAlign: 'right' }}>
                      <span style={{ fontSize: 10, fontWeight: 700, color: verdictColor, background: verdictBg,
                                     borderRadius: 4, padding: '3px 8px' }}>{verdict}</span>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
          <div style={{ marginTop: 10, fontSize: 11, color: '#718096', lineHeight: 1.5 }}>
            Source reports: <code>tier0_lineage_audit.json</code> · <code>tier0_dups_edges.json</code> · <code>tier0_dataset_decisions.json</code>.
            Re-run via <code>tier0h_evidence_panel.py</code> to refresh.
          </div>
        </div>
      )}
    </div>
  )
}
