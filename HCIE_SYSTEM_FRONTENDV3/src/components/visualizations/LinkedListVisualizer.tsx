/**
 * LinkedListVisualizer
 *
 * Interactive linked list visualization with node highlighting.
 * Shows linked list structure with pointers and operations.
 */

'use client'

import { useState } from 'react'

export interface ListNode {
  id: string
  value: number | string
  next: string | null
}

export interface LinkedListVisualizerProps {
  nodes: ListNode[]
  highlightedNodes?: string[]
  highlightedPointers?: string[]
  className?: string
  nodeSize?: 'sm' | 'md' | 'lg'
  showPointers?: boolean
}

export function LinkedListVisualizer({
  nodes,
  highlightedNodes = [],
  highlightedPointers = [],
  className = '',
  nodeSize = 'md',
  showPointers = true,
}: LinkedListVisualizerProps) {
  const nodeSizes = {
    sm: 'w-12 h-12 text-sm',
    md: 'w-16 h-16 text-base',
    lg: 'w-20 h-20 text-lg',
  }

  const arrowSizes = {
    sm: 'w-8',
    md: 'w-12',
    lg: 'w-16',
  }

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      {nodes.map((node, index) => {
        const isHighlighted = highlightedNodes.includes(node.id)
        const isPointerHighlighted = highlightedPointers.includes(node.id)

        return (
          <div key={node.id} className="flex items-center">
            <div
              className={`${nodeSizes[nodeSize]} flex items-center justify-center rounded-full border-4 transition-all duration-300 ${
                isHighlighted
                  ? 'bg-green-500 border-green-600 text-white'
                  : 'bg-white border-gray-400 text-gray-900'
              }`}
            >
              <span className="font-mono font-bold">{node.value}</span>
            </div>

            {showPointers && node.next && (
              <div
                className={`${arrowSizes[nodeSize]} flex items-center justify-center ${
                  isPointerHighlighted ? 'text-green-500' : 'text-gray-400'
                }`}
              >
                <svg
                  className="w-full h-8"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M17 8l4 4m0 0l-4 4m4-4H3"
                  />
                </svg>
              </div>
            )}

            {showPointers && !node.next && (
              <div className={`${arrowSizes[nodeSize]} flex items-center justify-center text-gray-400`}>
                <svg
                  className="w-full h-8"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
