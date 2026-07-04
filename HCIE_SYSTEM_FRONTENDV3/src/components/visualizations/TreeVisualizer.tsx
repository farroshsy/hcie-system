/**
 * TreeVisualizer
 *
 * Interactive tree visualization with node highlighting.
 * Shows binary or general tree structure with parent-child relationships.
 */

'use client'

import { useState } from 'react'

export interface TreeNode {
  id: string
  value: number | string
  left?: TreeNode
  right?: TreeNode
  children?: TreeNode[]
}

export interface TreeVisualizerProps {
  root: TreeNode | null
  highlightedNodes?: string[]
  className?: string
  nodeSize?: 'sm' | 'md' | 'lg'
  showValues?: boolean
}

export function TreeVisualizer({
  root,
  highlightedNodes = [],
  className = '',
  nodeSize = 'md',
  showValues = true,
}: TreeVisualizerProps) {
  const nodeSizes = {
    sm: 'w-10 h-10 text-xs',
    md: 'w-14 h-14 text-sm',
    lg: 'w-18 h-18 text-base',
  }

  const isHighlighted = (nodeId: string) => highlightedNodes.includes(nodeId)

  const renderNode = (node: TreeNode, level: number = 0) => {
    if (!node) return null

    const isNodeHighlighted = isHighlighted(node.id)

    return (
      <div key={node.id} className="flex flex-col items-center">
        <div
          className={`${nodeSizes[nodeSize]} flex items-center justify-center rounded-full border-4 transition-all duration-300 ${
            isNodeHighlighted
              ? 'bg-green-500 border-green-600 text-white'
              : 'bg-white border-gray-400 text-gray-900'
          }`}
        >
          {showValues && <span className="font-mono font-bold">{node.value}</span>}
        </div>

        {(node.left || node.right || node.children) && (
          <div className="flex gap-4 mt-2">
            {node.left && (
              <div className="flex flex-col items-center">
                <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19V5M12 5l-7 7M12 5l7 7" />
                </svg>
                {renderNode(node.left, level + 1)}
              </div>
            )}
            {node.right && (
              <div className="flex flex-col items-center">
                <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19V5M12 5l-7 7M12 5l7 7" />
                </svg>
                {renderNode(node.right, level + 1)}
              </div>
            )}
            {node.children && node.children.map((child, index) => (
              <div key={child.id} className="flex flex-col items-center">
                <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19V5M12 5l-7 7M12 5l7 7" />
                </svg>
                {renderNode(child, level + 1)}
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className={`flex items-center justify-center p-8 ${className}`}>
      {root ? renderNode(root) : <div className="text-gray-500">Empty tree</div>}
    </div>
  )
}
