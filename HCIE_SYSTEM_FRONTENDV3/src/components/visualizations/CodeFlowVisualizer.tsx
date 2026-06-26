/**
 * CodeFlowVisualizer
 *
 * Interactive code flow visualization with step-by-step execution.
 * Shows code execution flow with variable states and call stack.
 */

'use client'

import { useState } from 'react'

export interface ExecutionStep {
  line: number
  variables?: Record<string, any>
  description?: string
}

export interface CodeFlowVisualizerProps {
  code: string
  steps: ExecutionStep[]
  currentStep: number
  onStepChange: (step: number) => void
  className?: string
  fontSize?: 'sm' | 'md' | 'lg'
}

export function CodeFlowVisualizer({
  code,
  steps,
  currentStep,
  onStepChange,
  className = '',
  fontSize = 'md',
}: CodeFlowVisualizerProps) {
  const fontSizes = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base',
  }

  const lines = code.split('\n')
  const currentExecution = steps[currentStep]

  const handleStepForward = () => {
    if (currentStep < steps.length - 1) {
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

  return (
    <div className={`flex flex-col gap-4 ${className}`}>
      <div className="bg-gray-900 rounded-lg overflow-hidden">
        <div className="bg-gray-800 px-4 py-2 flex items-center justify-between">
          <span className="text-gray-400 text-sm font-mono">Code Flow</span>
          <div className="flex gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500" />
            <div className="w-3 h-3 rounded-full bg-yellow-500" />
            <div className="w-3 h-3 rounded-full bg-green-500" />
          </div>
        </div>
        <div className="p-4 overflow-x-auto">
          <pre className={`font-mono ${fontSizes[fontSize]}`}>
            {lines.map((line, index) => {
              const lineNum = index + 1
              const isCurrentLine = currentExecution?.line === lineNum
              const isExecuted = steps.some((step) => step.line === lineNum && steps.indexOf(step) <= currentStep)

              return (
                <div
                  key={index}
                  className={`flex hover:bg-gray-800 transition-colors ${
                    isCurrentLine ? 'bg-blue-900/50' : ''
                  }`}
                >
                  <span className="text-gray-600 w-8 text-right pr-4 select-none">{lineNum}</span>
                  <code
                    className={`text-gray-300 whitespace-pre ${
                      isExecuted ? 'text-green-400' : ''
                    } ${isCurrentLine ? 'text-white font-bold' : ''}`}
                  >
                    {line || ' '}
                  </code>
                  {isCurrentLine && (
                    <span className="ml-2 text-yellow-400">←</span>
                  )}
                </div>
              )
            })}
          </pre>
        </div>
      </div>

      {/* Variable State Panel */}
      {currentExecution?.variables && (
        <div className="bg-gray-100 rounded-lg p-4">
          <h3 className="text-sm font-semibold mb-2">Variable State</h3>
          <div className="flex flex-wrap gap-2">
            {Object.entries(currentExecution.variables).map(([key, value]) => (
              <div key={key} className="bg-white px-3 py-1 rounded border">
                <span className="font-mono text-sm">
                  <span className="text-blue-600">{key}</span> = {String(value)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Description */}
      {currentExecution?.description && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm text-blue-900">{currentExecution.description}</p>
        </div>
      )}

      {/* Controls */}
      <div className="flex items-center justify-center gap-2">
        <button
          onClick={handleReset}
          className="px-3 py-1 bg-gray-600 text-white rounded hover:bg-gray-700 text-sm"
        >
          Reset
        </button>
        <button
          onClick={handleStepBackward}
          disabled={currentStep === 0}
          className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm disabled:bg-gray-400"
        >
          Step Back
        </button>
        <button
          onClick={handleStepForward}
          disabled={currentStep >= steps.length - 1}
          className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm disabled:bg-gray-400"
        >
          Step Forward
        </button>
        <div className="text-sm text-gray-600 ml-4">
          Step: {currentStep} / {steps.length - 1}
        </div>
      </div>
    </div>
  )
}
