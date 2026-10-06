'use client'

/**
 * ConceptGraph — the K-12 curriculum as the learner actually experiences it:
 * a prerequisite/transfer topology, not a flat card list.
 *
 * Columns = grade bands (K-2 → K-12), rows = concept areas, so a concept's
 * whole progression reads left-to-right. Two edge families:
 *  - catalog `prerequisites`  → solid gray arrows (what LOCKS what)
 *  - concept_dependencies DB  → dashed blue arrows labelled with the
 *    transfer weight (what mastery TRANSFERS where — the thesis mechanism)
 * Node fill encodes live mastery; locked concepts show the padlock and do
 * not navigate. Clicking any unlocked node deep-links to /learn?concept=X.
 */

import { useMemo } from 'react'
import { useRouter } from 'next/navigation'
import ReactFlow, { Background, Controls, MarkerType, type Node, type Edge } from 'reactflow'
import 'reactflow/dist/style.css'
import { K12_CONCEPTS } from '@/lib/catalog/k12-catalog'
import { CONCEPT_EDGES } from '@/lib/catalog/concept-edges'
import { t as ui } from '@/lib/ui/theme'

interface ConceptLockState {
  id: string
  locked: boolean
  prerequisites: string[]
  missing_prereqs: string[]
  mastery_threshold: number
}

interface Props {
  masteryMap: Record<string, number>
  lockMap: Record<string, ConceptLockState>
  height?: number
}

const BAND_X: Record<string, number> = { 'K-2': 0, 'K-5': 300, 'K-8': 600, 'K-12': 900 }
const BAND_COLOR: Record<string, string> = {
  'K-2': ui.tone.ok.fg, 'K-5': ui.tone.info.fg, 'K-8': ui.tone.accent.fg, 'K-12': ui.tone.warn.fg,
}

function masteryColor(v: number) {
  return v >= 0.7 ? ui.tone.ok.fg : v >= 0.45 ? ui.tone.warn.fg : v > 0 ? ui.tone.bad.fg : ui.color.lineStrong
}

export function ConceptGraph({ masteryMap, lockMap, height = 560 }: Props) {
  const router = useRouter()

  const { nodes, edges } = useMemo(() => {
    // Stable row per concept area so band progressions read horizontally.
    const areas = [...new Set(K12_CONCEPTS.map(c => c.conceptArea))]
    const nodes: Node[] = K12_CONCEPTS.map(c => {
      const mastery = masteryMap[c.id] ?? 0
      const locked = !!lockMap[c.id]?.locked
      const mc = masteryColor(mastery)
      return {
        id: c.id,
        position: { x: BAND_X[c.gradeBand] ?? 0, y: areas.indexOf(c.conceptArea) * 92 },
        data: {
          label: (
            <div style={{ textAlign: 'left', lineHeight: 1.25 }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: locked ? ui.color.muted : ui.color.ink }}>
                {locked ? '🔒 ' : mastery >= 0.7 ? '✓ ' : ''}{c.label}
              </div>
              <div style={{ fontSize: 9, color: ui.color.muted, marginTop: 2 }}>
                {c.gradeBand} · {mastery > 0 ? `${(mastery * 100).toFixed(0)}% mastery` : 'not started'}
              </div>
              <div style={{ height: 3, background: ui.color.line, borderRadius: 2, marginTop: 3 }}>
                <div style={{ height: '100%', width: `${mastery * 100}%`, background: mc, borderRadius: 2 }} />
              </div>
            </div>
          ),
        },
        style: {
          width: 190, padding: '8px 10px', borderRadius: 8,
          background: locked ? ui.color.subtle : ui.color.surface,
          border: `1.5px solid ${locked ? ui.color.lineStrong : mastery > 0 ? mc : BAND_COLOR[c.gradeBand]}`,
          opacity: locked ? 0.7 : 1,
          cursor: locked ? 'not-allowed' : 'pointer',
          boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
        },
      }
    })

    const seen = new Set<string>()
    const edges: Edge[] = []
    // Transfer edges from the DB snapshot — the headline mechanism, drawn first.
    for (const e of CONCEPT_EDGES) {
      const key = `${e.source}->${e.target}`
      seen.add(key)
      edges.push({
        id: `t-${key}`, source: e.source, target: e.target,
        label: `⚡ ${e.transferWeight.toFixed(2)}`,
        labelStyle: { fontSize: 9, fill: ui.tone.info.fg, fontWeight: 700 },
        labelBgStyle: { fill: ui.color.surface, fillOpacity: 0.85 },
        style: { stroke: ui.tone.info.fg, strokeWidth: 1 + e.transferWeight * 1.5, strokeDasharray: e.dependencyType === 'prerequisite' ? undefined : '6 4' },
        animated: e.dependencyType === 'prerequisite',
        markerEnd: { type: MarkerType.ArrowClosed, color: ui.tone.info.fg },
      })
    }
    // Catalog prerequisite edges (lock relationships) not already drawn as transfer.
    for (const c of K12_CONCEPTS) {
      for (const p of c.prerequisites) {
        const key = `${p}->${c.id}`
        if (seen.has(key)) continue
        seen.add(key)
        edges.push({
          id: `p-${key}`, source: p, target: c.id,
          style: { stroke: ui.color.lineStrong, strokeWidth: 1.2 },
          markerEnd: { type: MarkerType.ArrowClosed, color: ui.color.lineStrong },
        })
      }
    }
    return { nodes, edges }
  }, [masteryMap, lockMap])

  return (
    <div style={{ height, border: `1px solid ${ui.color.line}`, borderRadius: ui.radius.lg,
                  background: ui.color.surface, overflow: 'hidden' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        fitView
        fitViewOptions={{ padding: 0.12 }}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={false}
        proOptions={{ hideAttribution: true }}
        onNodeClick={(_, node) => {
          if (lockMap[node.id]?.locked) return
          router.push(`/learn?concept=${encodeURIComponent(node.id)}`)
        }}
      >
        <Background gap={18} size={1} />
        <Controls showInteractive={false} />
      </ReactFlow>
      <div style={{ position: 'relative', top: -34, left: 12, display: 'inline-flex', gap: 14,
                    background: ui.color.surface + 'E6', border: `1px solid ${ui.color.line}`,
                    borderRadius: ui.radius.sm, padding: '4px 10px', fontSize: 10, color: ui.color.muted }}>
        <span><span style={{ color: ui.tone.info.fg, fontWeight: 700 }}>⚡ dashed/animated</span> transfer edge (weight)</span>
        <span><span style={{ color: ui.color.lineStrong, fontWeight: 700 }}>→ gray</span> prerequisite (locks)</span>
        <span>🔒 locked · click a node to study it</span>
      </div>
    </div>
  )
}
