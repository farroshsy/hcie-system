/**
 * Playback Controller
 *
 * Controls for rewind, fast-forward, play, pause, and step-through of code execution.
 * Cartesian-style playback system with timeline visualization.
 */

'use client'

import { useState, useEffect } from 'react'

export interface PlaybackControllerProps {
  totalSteps: number
  currentStep: number
  onStepChange: (step: number) => void
  isPlaying: boolean
  onPlayPause: () => void
  speed?: number
  onSpeedChange?: (speed: number) => void
  className?: string
}

export function PlaybackController({
  totalSteps,
  currentStep,
  onStepChange,
  isPlaying,
  onPlayPause,
  speed = 500,
  onSpeedChange,
  className = '',
}: PlaybackControllerProps) {
  const [localSpeed, setLocalSpeed] = useState(speed)

  useEffect(() => {
    if (onSpeedChange) {
      onSpeedChange(localSpeed)
    }
  }, [localSpeed, onSpeedChange])

  const handlePlayPause = () => {
    onPlayPause()
  }

  const handleStepForward = () => {
    if (currentStep < totalSteps - 1) {
      onStepChange(currentStep + 1)
    }
  }

  const handleStepBackward = () => {
    if (currentStep > 0) {
      onStepChange(currentStep - 1)
    }
  }

  const handleReset = () => {
    onStepChange(0)
  }

  const handleJumpToStart = () => {
    onStepChange(0)
  }

  const handleJumpToEnd = () => {
    onStepChange(totalSteps - 1)
  }

  const handleSpeedIncrease = () => {
    setLocalSpeed(Math.max(100, localSpeed - 100))
  }

  const handleSpeedDecrease = () => {
    setLocalSpeed(Math.min(2000, localSpeed + 100))
  }

  const progressPercent = totalSteps > 0 ? (currentStep / (totalSteps - 1)) * 100 : 0

  return (
    <div className={`bg-white rounded-lg shadow-lg border border-gray-200 ${className}`}>
      {/* Timeline */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center gap-4 mb-2">
          <span className="text-sm font-semibold text-gray-700">Timeline</span>
          <span className="text-sm text-gray-500">
            Step {currentStep} / {totalSteps - 1}
          </span>
        </div>
        <div className="relative h-2 bg-gray-200 rounded-full cursor-pointer">
          <div
            className="absolute h-full bg-blue-500 rounded-full transition-all duration-200"
            style={{ width: `${progressPercent}%` }}
          />
          <div
            className="absolute top-1/2 -translate-y-1/2 w-4 h-4 bg-blue-600 rounded-full shadow cursor-pointer hover:scale-110 transition-transform"
            style={{ left: `${progressPercent}%`, transform: 'translate(-50%, -50%)' }}
            onClick={(e) => {
              const rect = e.currentTarget.parentElement?.getBoundingClientRect()
              if (rect) {
                const clickX = e.clientX - rect.left
                const newPercent = (clickX / rect.width) * 100
                const newStep = Math.floor((newPercent / 100) * (totalSteps - 1))
                onStepChange(Math.max(0, Math.min(totalSteps - 1, newStep)))
              }
            }}
          />
        </div>
      </div>

      {/* Controls */}
      <div className="p-4">
        <div className="flex items-center justify-center gap-2">
          {/* Jump to start */}
          <button
            onClick={handleJumpToStart}
            disabled={currentStep === 0}
            className="p-2 bg-gray-100 hover:bg-gray-200 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition"
            title="Jump to start"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
            </svg>
          </button>

          {/* Step backward */}
          <button
            onClick={handleStepBackward}
            disabled={currentStep === 0}
            className="p-2 bg-gray-100 hover:bg-gray-200 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition"
            title="Step backward"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>

          {/* Rewind */}
          <button
            onClick={() => onStepChange(Math.max(0, currentStep - 10))}
            disabled={currentStep < 10}
            className="p-2 bg-gray-100 hover:bg-gray-200 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition"
            title="Rewind 10 steps"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12.066 11.2a1 1 0 000 1.6l5.334 4A1 1 0 0019 16V8a1 1 0 00-1.6-.8l-5.333 4zM4.066 11.2a1 1 0 000 1.6l5.334 4A1 1 0 0011 16V8a1 1 0 00-1.6-.8l-5.334 4z" />
            </svg>
          </button>

          {/* Play/Pause */}
          <button
            onClick={handlePlayPause}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold transition flex items-center gap-2"
            title={isPlaying ? 'Pause' : 'Play'}
          >
            {isPlaying ? (
              <>
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
                </svg>
                Pause
              </>
            ) : (
              <>
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M8 5v14l11-7z" />
                </svg>
                Play
              </>
            )}
          </button>

          {/* Fast forward */}
          <button
            onClick={() => onStepChange(Math.min(totalSteps - 1, currentStep + 10))}
            disabled={currentStep > totalSteps - 11}
            className="p-2 bg-gray-100 hover:bg-gray-200 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition"
            title="Fast forward 10 steps"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.933 12.8a1 1 0 000-1.6L6.6 7.2A1 1 0 005 8v8a1 1 0 001.6.8l5.333-4zM19.933 12.8a1 1 0 000-1.6l-5.333-4A1 1 0 0013 8v8a1 1 0 001.6.8l5.333-4z" />
            </svg>
          </button>

          {/* Step forward */}
          <button
            onClick={handleStepForward}
            disabled={currentStep >= totalSteps - 1}
            className="p-2 bg-gray-100 hover:bg-gray-200 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition"
            title="Step forward"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>

          {/* Jump to end */}
          <button
            onClick={handleJumpToEnd}
            disabled={currentStep >= totalSteps - 1}
            className="p-2 bg-gray-100 hover:bg-gray-200 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition"
            title="Jump to end"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
            </svg>
          </button>
        </div>

        {/* Speed control */}
        <div className="flex items-center justify-center gap-4 mt-4">
          <span className="text-sm font-semibold text-gray-700">Speed:</span>
          <button
            onClick={handleSpeedIncrease}
            className="px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded text-sm transition"
            title="Increase speed"
          >
            Faster
          </button>
          <span className="text-sm text-gray-600 w-20 text-center">
            {localSpeed}ms
          </span>
          <button
            onClick={handleSpeedDecrease}
            className="px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded text-sm transition"
            title="Decrease speed"
          >
            Slower
          </button>
        </div>
      </div>
    </div>
  )
}
