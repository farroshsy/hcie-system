/**
 * BinaryVisualizer
 *
 * Interactive binary sequence visualization.
 * Shows binary representation with bit highlighting and operations.
 */

'use client'

import { useState } from 'react'

export interface BinaryVisualizerProps {
  binary: string
  highlightedBits?: number[]
  className?: string
  bitSize?: 'sm' | 'md' | 'lg'
  showIndex?: boolean
  showDecimal?: boolean
}

export function BinaryVisualizer({
  binary,
  highlightedBits = [],
  className = '',
  bitSize = 'md',
  showIndex = true,
  showDecimal = true,
}: BinaryVisualizerProps) {
  const decimalValue = parseInt(binary, 2)

  const bitSizes = {
    sm: 'w-8 h-8 text-sm',
    md: 'w-10 h-10 text-base',
    lg: 'w-12 h-12 text-lg',
  }

  return (
    <div className={`flex flex-col items-center gap-4 ${className}`}>
      {showDecimal && (
        <div className="text-sm text-gray-600">
          Decimal: <span className="font-mono font-bold">{decimalValue}</span>
        </div>
      )}

      <div className="flex gap-2">
        {binary.split('').map((bit, index) => {
          const isHighlighted = highlightedBits.includes(index)

          return (
            <div key={index} className="flex flex-col items-center">
              {showIndex && (
                <div className="text-xs text-gray-400 mb-1">{index}</div>
              )}
              <div
                className={`${bitSizes[bitSize]} flex items-center justify-center rounded border-2 transition-all duration-300 ${
                  isHighlighted
                    ? 'bg-green-500 border-green-600 text-white'
                    : 'bg-gray-100 border-gray-300 text-gray-900'
                }`}
              >
                <span className="font-mono font-bold">{bit}</span>
              </div>
            </div>
          )
        })}
      </div>

      {showDecimal && (
        <div className="text-xs text-gray-500">
          {binary.length} bits
        </div>
      )}
    </div>
  )
}
