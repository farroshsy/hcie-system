'use client'

import { useEffect, useMemo, useState } from 'react'
import { useT } from '@/contexts/language_context'
import { t as ui } from '@/lib/ui/theme'

type GEdge = { source: string; target: string; weight: number; source_label: string; target_label: string }
type GNode = { id: string; label: string; out_degree: number; in_degree: number }
type GResp = {
  status: string
  nodes: GNode[]
  edges: GEdge[]
  total_edges?: number
  shown_edges?: number
  graph_method?: string
}

const W = 720
const H = 660
const CX = 330
const CY = 320
const R = 262

/**
 * Live node-link plot of the prerequisite concept graph (default: the sealed
 * Junyi dataset graph from `external_concept_graph`). This is the actual DAG the
 * HCIE transfer mechanism — and the shuffled-DAG causal test on this page —
 * runs on, fetched live from /v3/frontend/dashboard/concept-graph. Hover a node
 * to trace its transfer links; node radius encodes connectivity (degree).
 */
export default function ConceptGraph({ backendUrl, dataset = 'junyi_2015_graph' }: { backendUrl: string; dataset?: string }) {
  const t = useT()
  const [resp, setResp] = useState<GResp | null>(null)
  const [failed, setFailed] = useState(false)
  const [hover, setHover] = useState<string | null>(null)

  useEffect(() => {
    let alive = true
    fetch(`${backendUrl}/v3/frontend/dashboard/concept-graph/${dataset}?limit=400`)
      .then(r => (r.ok ? r.json() : Promise.reject(r.status)))
      .then(d => { if (alive) setResp(d) })
      .catch(() => { if (alive) setFailed(true) })
    return () => { alive = false }
  }, [backendUrl, dataset])

  const G = useMemo(() => {
    if (!resp || resp.status !== 'ok' || !resp.nodes?.length) return null
    // The endpoint returns the top-weighted edges and can include duplicates;
    // collapse to one edge per ordered pair (keep the strongest weight).
    const seen = new Map<string, GEdge>()
    for (const e of resp.edges || []) {
      if (!e.source || !e.target || e.source === e.target) continue
      const k = `${e.source}>${e.target}`
      const prev = seen.get(k)
      if (!prev || e.weight > prev.weight) seen.set(k, e)
    }
    const edges = Array.from(seen.values())
    const deg = new Map<string, number>()
    const nbr = new Map<string, Set<string>>()
    for (const e of edges) {
      deg.set(e.source, (deg.get(e.source) || 0) + 1)
      deg.set(e.target, (deg.get(e.target) || 0) + 1)
      if (!nbr.has(e.source)) nbr.set(e.source, new Set())
      if (!nbr.has(e.target)) nbr.set(e.target, new Set())
      nbr.get(e.source)!.add(e.target)
      nbr.get(e.target)!.add(e.source)
    }
    const nodes = resp.nodes.slice().sort((a, b) => (deg.get(b.id) || 0) - (deg.get(a.id) || 0))
    const N = nodes.length
    const pos = new Map<string, { x: number; y: number; right: boolean }>()
    nodes.forEach((n, i) => {
      const ang = (i / N) * Math.PI * 2 - Math.PI / 2
      pos.set(n.id, { x: CX + R * Math.cos(ang), y: CY + R * Math.sin(ang), right: Math.cos(ang) >= -0.01 })
    })
    const maxDeg = Math.max(1, ...Array.from(deg.values()))
    const hubs = new Set(nodes.slice(0, 10).map(n => n.id))
    return { edges, nodes, pos, deg, nbr, maxDeg, hubs, N }
  }, [resp])

  if (failed) return null

  const lbl = (s: string) => (s.length > 20 ? s.slice(0, 19) + '…' : s)

  return (
    <div style={{ border: `1px solid ${ui.color.line}`, borderRadius: ui.radius.lg, background: ui.color.surface, padding: ui.space.lg, marginBottom: ui.space.xl }}>
      <div style={{ fontSize: ui.font.size.xs, fontWeight: ui.font.weight.bold, letterSpacing: '0.06em', textTransform: 'uppercase', color: ui.tone.info.fg }}>
        {t('conceptGraph.eyebrow', 'Live prerequisite graph')}
      </div>
      <div style={{ fontSize: ui.font.size.xl, fontWeight: ui.font.weight.heavy, color: ui.color.heading, marginTop: 4 }}>
        {t('conceptGraph.title', 'The concept DAG the transfer mechanism runs on')}
      </div>
      <div style={{ fontSize: ui.font.size.sm, color: ui.color.muted, marginTop: 4, maxWidth: 720, lineHeight: 1.5 }}>
        {t('conceptGraph.sub', 'Live from the sealed Junyi dataset graph. Hover a concept to trace its transfer links; node size is its connectivity. This is exactly the structure the shuffled-DAG test below randomizes.')}
      </div>

      {!G ? (
        <div style={{ padding: '48px 0', textAlign: 'center', color: ui.color.faint, fontSize: ui.font.size.sm }}>
          {t('conceptGraph.loading', 'Loading graph…')}
        </div>
      ) : (
        <div style={{ display: 'flex', gap: ui.space.lg, flexWrap: 'wrap', marginTop: ui.space.md, alignItems: 'flex-start' }}>
          <svg viewBox={`0 0 ${W} ${H}`} role="img"
               aria-label={t('conceptGraph.title', 'Concept transfer graph')}
               style={{ width: '100%', maxWidth: 560, height: 'auto', flex: '1 1 420px' }}>
            {G.edges.map((e, i) => {
              const a = G.pos.get(e.source); const b = G.pos.get(e.target)
              if (!a || !b) return null
              const active = hover != null && (e.source === hover || e.target === hover)
              const op = hover == null ? 0.10 : active ? 0.7 : 0.03
              return (
                <line key={i} x1={a.x} y1={a.y} x2={b.x} y2={b.y}
                      stroke={active ? ui.tone.info.fg : ui.color.lineStrong}
                      strokeWidth={active ? 1.4 : 0.8} opacity={op} />
              )
            })}
            {G.nodes.map(n => {
              const p = G.pos.get(n.id)
              if (!p) return null
              const d = G.deg.get(n.id) || 0
              const r = 3 + 7 * (d / G.maxDeg)
              const isHover = hover === n.id
              const isNbr = hover != null && (G.nbr.get(hover)?.has(n.id) ?? false)
              const dim = hover != null && !isHover && !isNbr
              const fill = isHover ? ui.tone.accent.fg : isNbr ? ui.tone.ok.fg : ui.tone.info.fg
              const showLabel = G.hubs.has(n.id) || isHover || isNbr
              return (
                <g key={n.id} opacity={dim ? 0.18 : 1} style={{ cursor: 'pointer' }}
                   onMouseEnter={() => setHover(n.id)} onMouseLeave={() => setHover(null)}>
                  <circle cx={p.x} cy={p.y} r={r} fill={fill} stroke={ui.color.surface} strokeWidth={0.8} />
                  {showLabel && (
                    <text x={p.right ? p.x + r + 4 : p.x - r - 4} y={p.y + 3}
                          textAnchor={p.right ? 'start' : 'end'} fontSize={10}
                          fill={isHover ? ui.color.ink : ui.color.muted}
                          fontWeight={isHover ? 600 : 400}>{lbl(n.label)}</text>
                  )}
                </g>
              )
            })}
          </svg>

          <aside style={{ flex: '1 1 240px', minWidth: 220, fontSize: ui.font.size.sm, color: ui.color.body }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: ui.space.sm, marginBottom: ui.space.md }}>
              <Stat label={t('conceptGraph.statNodes', 'concepts')} value={String(G.N)} />
              <Stat label={t('conceptGraph.statEdges', 'unique links')} value={String(G.edges.length)} />
              <Stat label={t('conceptGraph.statTotal', 'total edges')} value={(resp?.total_edges ?? 0).toLocaleString()} />
              <Stat label={t('conceptGraph.statMethod', 'graph method')} value={resp?.graph_method ?? '—'} />
            </div>
            <div style={{ fontSize: ui.font.size.xs, fontWeight: ui.font.weight.bold, textTransform: 'uppercase', letterSpacing: '0.05em', color: ui.color.muted, marginBottom: 6 }}>
              {t('conceptGraph.hubs', 'Most-connected concepts')}
            </div>
            {G.nodes.slice(0, 6).map(n => (
              <div key={n.id} onMouseEnter={() => setHover(n.id)} onMouseLeave={() => setHover(null)}
                   style={{ display: 'flex', justifyContent: 'space-between', padding: '3px 6px', borderRadius: ui.radius.sm, cursor: 'pointer', background: hover === n.id ? ui.tone.info.bg : 'transparent' }}>
                <span style={{ color: ui.color.ink }}>{lbl(n.label)}</span>
                <span style={{ color: ui.color.muted, fontVariantNumeric: 'tabular-nums' }}>{G.deg.get(n.id) || 0}</span>
              </div>
            ))}
            <div style={{ marginTop: ui.space.md, fontSize: ui.font.size.xs, color: ui.color.faint, lineHeight: 1.5 }}>
              {t('conceptGraph.hint', 'Hover any node to highlight its transfer links. Blue = concept, green = its neighbours, purple = focused.')}
            </div>
          </aside>
        </div>
      )}
    </div>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div style={{ fontSize: ui.font.size.lg, fontWeight: ui.font.weight.heavy, color: ui.tone.info.fg, fontVariantNumeric: 'tabular-nums' }}>{value}</div>
      <div style={{ fontSize: ui.font.size.xs, color: ui.color.muted }}>{label}</div>
    </div>
  )
}
