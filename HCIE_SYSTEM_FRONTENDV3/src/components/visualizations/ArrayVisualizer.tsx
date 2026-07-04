/**
 * ArrayVisualizer
 *
 * Interactive array visualization with animation support.
 * Shows array elements with highlighting for comparisons, swaps, and operations.
 */

'use client'

import { useState } from 'react'

export interface ArrayVisualizerProps {
  array: number[]
  highlightedIndices?: number[]
  comparedIndices?: number[]
  swappedIndices?: number[]
  className?: string
  maxValue?: number
  barColor?: string
  highlightColor?: string
  compareColor?: string
  swapColor?: string
}

export function ArrayVisualizer({
  array,
  highlightedIndices = [],
  comparedIndices = [],
  swappedIndices = [],
  className = '',
  maxValue,
  barColor = 'bg-blue-500',
  highlightColor = 'bg-green-500',
  compareColor = 'bg-yellow-500',
  swapColor = 'bg-red-500',
}: ArrayVisualizerProps) {
  const max = maxValue || Math.max(...array, 0)

  return (
    <div className={`flex items-end justify-center gap-1 h-64 ${className}`}>
      {array.map((value, index) => {
        const isHighlighted = highlightedIndices.includes(index)
        const isCompared = comparedIndices.includes(index)
        const isSwapped = swappedIndices.includes(index)

        const getColor = () => {
          if (isSwapped) return swapColor
          if (isHighlighted) return highlightColor
          if (isCompared) return compareColor
          return barColor
        }

        const height = max > 0 ? `${(value / max) * 100}%` : '0%'

        return (
          <div
            key={index}
            className={`flex flex-col items-center`}
          >
            <div
              className={`${getColor()} rounded-t transition-all duration-300 ease-in-out`}
              style={{
                height,
                width: '40px',
              }}
            />
            <div className="text-xs mt-2 font-mono">{value}</div>
          </div>
        )
      })}
    </div>
  )
}
