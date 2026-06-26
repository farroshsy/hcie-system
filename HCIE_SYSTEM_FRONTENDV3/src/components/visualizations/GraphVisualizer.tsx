/**
 * GraphVisualizer
 *
 * Interactive graph visualization with node and edge highlighting.
 * Shows directed/undirected graphs with visual feedback for operations.
 */

'use client'

import { useState } from 'react'

export interface GraphNode {
  id: string
  label: string
  x?: number
  y?: number
}

export interface GraphEdge {
  from: string
  to: string
  weight?: number
  directed?: boolean
}

export interface GraphVisualizerProps {
  nodes: GraphNode[]
  edges: GraphEdge[]
  highlightedNodes?: string[]
  highlightedEdges?: { from: string; to: string }[]
  className?: string
  nodeSize?: 'sm' | 'md' | 'lg'
  showWeights?: boolean
  directed?: boolean
}

export function GraphVisualizer({
  nodes,
  edges,
  highlightedNodes = [],
  highlightedEdges = [],
  className = '',
  nodeSize = 'md',
  showWeights = true,
  directed = false,
}: GraphVisualizerProps) {
  const nodeSizes = {
    sm: 'w-10 h-10 text-sm',
    md: 'w-14 h-14 text-base',
    lg: 'w-18 h-18 text-lg',
  }

  const isNodeHighlighted = (nodeId: string) => highlightedNodes.includes(nodeId)
  const isEdgeHighlighted = (from: string, to: string) =>
    highlightedEdges.some((edge) => edge.from === from && edge.to === to)

  const getEdgeColor = (from: string, to: string) => {
    if (isEdgeHighlighted(from, to)) return 'stroke-green-500'
    return 'stroke-gray-400'
  }

  return (
    <div className={`relative w-full h-96 ${className}`}>
      <svg className="w-full h-full" viewBox="0 0 400 300">
        {edges.map((edge, index) => {
          const fromNode = nodes.find((n) => n.id === edge.from)
          const toNode = nodes.find((n) => n.id === edge.to)

          if (!fromNode || !toNode) return null

          const fromX = fromNode.x ?? (index % 4) * 100 + 50
          const fromY = fromNode.y ?? Math.floor(index / 4) * 100 + 50
          const toX = toNode.x ?? ((index + 1) % 4) * 100 + 50
          const toY = toNode.y ?? Math.floor((index + 1) / 4) * 100 + 50

          const midX = (fromX + toX) / 2
          const midY = (fromY + toY) / 2

          return (
            <g key={`${edge.from}-${edge.to}`}>
              <line
                x1={fromX}
                y1={fromY}
                x2={toX}
                y2={toY}
                strokeWidth={2}
                className={getEdgeColor(edge.from, edge.to)}
              />
              {directed && (
                <polygon
                  points={`${toX},${toY} ${toX - 8},${toY - 5} ${toX - 8},${toY + 5}`}
                  fill="currentColor"
                  className={getEdgeColor(edge.from, edge.to)}
                />
              )}
              {showWeights && edge.weight !== undefined && (
                <>
                  <rect x={midX - 15} y={midY - 10} width={30} height={20} fill="white" />
                  <text
                    x={midX}
                    y={midY + 5}
                    textAnchor="middle"
                    className="text-xs font-mono fill-gray-700"
                  >
                    {edge.weight}
                  </text>
                </>
              )}
            </g>
          )
        })}

        {nodes.map((node, index) => {
          const x = node.x ?? (index % 4) * 100 + 50
          const y = node.y ?? Math.floor(index / 4) * 100 + 50

          return (
            <g key={node.id}>
              <circle
                cx={x}
                cy={y}
                r={nodeSize === 'sm' ? 20 : nodeSize === 'md' ? 28 : 36}
                className={`${
                  isNodeHighlighted(node.id) ? 'fill-green-500' : 'fill-white'
                } stroke-gray-400 stroke-2`}
              />
              <text
                x={x}
                y={y + 5}
                textAnchor="middle"
                className={`font-mono font-bold ${
                  isNodeHighlighted(node.id) ? 'fill-white' : 'fill-gray-900'
                } ${nodeSize === 'sm' ? 'text-xs' : nodeSize === 'md' ? 'text-sm' : 'text-base'}`}
              >
                {node.label}
              </text>
            </g>
          )
        })}
      </svg>
    </div>
  )
}
