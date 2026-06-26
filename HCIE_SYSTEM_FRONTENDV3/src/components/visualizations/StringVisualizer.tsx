/**
 * StringVisualizer
 *
 * Interactive string visualization with character highlighting.
 * Shows string manipulation operations with visual feedback.
 */

'use client'

import { useState } from 'react'

export interface StringVisualizerProps {
  text: string
  highlightedIndices?: number[]
  comparedIndices?: number[]
  className?: string
  charSize?: 'sm' | 'md' | 'lg'
  showIndex?: boolean
  highlightColor?: string
  compareColor?: string
}

export function StringVisualizer({
  text,
  highlightedIndices = [],
  comparedIndices = [],
  className = '',
  charSize = 'md',
  showIndex = true,
  highlightColor = 'bg-green-500',
  compareColor = 'bg-yellow-500',
}: StringVisualizerProps) {
  const charSizes = {
    sm: 'w-8 h-8 text-sm',
    md: 'w-10 h-10 text-base',
    lg: 'w-12 h-12 text-lg',
  }

  const isHighlighted = (index: number) => highlightedIndices.includes(index)
  const isCompared = (index: number) => comparedIndices.includes(index)

  return (
    <div className={`flex flex-col items-center gap-4 ${className}`}>
      {showIndex && (
        <div className="flex gap-1">
          {text.split('').map((_, index) => (
            <div key={index} className="w-10 text-center text-xs text-gray-400">
              {index}
            </div>
          ))}
        </div>
      )}

      <div className="flex gap-1">
        {text.split('').map((char, index) => {
          const isCharHighlighted = isHighlighted(index)
          const isCharCompared = isCompared(index)

          return (
            <div key={index} className="flex flex-col items-center">
              {showIndex && (
                <div className="text-xs text-gray-400 mb-1">{index}</div>
              )}
              <div
                className={`${charSizes[charSize]} flex items-center justify-center rounded border-2 transition-all duration-300 ${
                  isCharHighlighted
                    ? `${highlightColor} border-green-600 text-white`
                    : isCharCompared
                    ? `${compareColor} border-yellow-600 text-gray-900`
                    : 'bg-white border-gray-300 text-gray-900'
                }`}
              >
                <span className="font-mono font-bold">{char}</span>
              </div>
            </div>
          )
        })}
      </div>

      <div className="text-xs text-gray-500">
        Length: {text.length} characters
      </div>
    </div>
  )
}
