/**
 * SortingVisualizer
 *
 * Interactive sorting algorithm visualization with animation controls.
 * Shows sorting steps with comparisons, swaps, and sorted elements.
 */

'use client'

import { useState, useEffect } from 'react'

export interface SortingVisualizerProps {
  array: number[]
  step: number
  comparisons: [number, number][]
  swaps: [number, number][]
  sortedIndices: number[]
  className?: string
  speed?: number
  totalSteps?: number
  onStepChange?: (step: number) => void
  isPlaying?: boolean
  onPlayPause?: () => void
}

export function SortingVisualizer({
  array,
  step,
  comparisons,
  swaps,
  sortedIndices,
  className = '',
  speed = 500,
  totalSteps,
  onStepChange,
  isPlaying = false,
  onPlayPause,
}: SortingVisualizerProps) {
  const max = Math.max(...array, 0)
  const stepsCount = totalSteps || comparisons.length

  const getBarColor = (index: number) => {
    if (sortedIndices.includes(index)) return 'bg-green-500'
    if (swaps[step]?.includes(index)) return 'bg-red-500'
    if (comparisons[step]?.includes(index)) return 'bg-yellow-500'
    return 'bg-blue-500'
  }

  const handleStepForward = () => {
    if (onStepChange && step < stepsCount - 1) {
      onStepChange(step + 1)
    }
  }

  const handleStepBackward = () => {
    if (onStepChange && step > 0) {
      onStepChange(step - 1)
    }
  }

  const handleReset = () => {
    if (onStepChange) {
      onStepChange(0)
    }
  }

  return (
    <div className={`flex flex-col gap-6 ${className}`}>
      <div className="flex items-end justify-center gap-2 h-80 bg-gray-50 rounded-xl p-4 border-2 border-gray-200">
        {array.map((value, index) => {
          const height = max > 0 ? `${(value / max) * 100}%` : '0%'

          return (
            <div
              key={index}
              className={`flex flex-col items-center`}
            >
              <div
                className={`${getBarColor(index)} rounded-t transition-all duration-300 ease-in-out shadow-md`}
                style={{
                  height,
                  width: '50px',
                  minHeight: '20px',
                }}
              />
              <div className="text-sm mt-2 font-mono font-bold text-gray-700">{value}</div>
            </div>
          )
        })}
      </div>

      <div className="flex items-center justify-center gap-3 flex-wrap">
        <button
          onClick={handleReset}
          className="px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-800 text-sm font-semibold shadow-md transition"
        >
          Reset
        </button>
        <button
          onClick={handleStepBackward}
          disabled={step === 0}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-semibold shadow-md transition disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          ← Step Back
        </button>
        <button
          onClick={onPlayPause}
          className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm font-semibold shadow-md transition"
        >
          {isPlaying ? '⏸ Pause' : '▶ Play'}
        </button>
        <button
          onClick={handleStepForward}
          disabled={step >= stepsCount - 1}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-semibold shadow-md transition disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          Step Forward →
        </button>
        <div className="text-sm font-semibold text-gray-700 bg-white px-4 py-2 rounded-lg border-2 border-gray-200">
          Step: {step} / {stepsCount - 1}
        </div>
      </div>
    </div>
  )
}
