/**
 * Cartesian-Style Interactive Visualizer
 *
 * Complete Cartesian-style visualization system combining:
 * - Code execution engine
 * - Real-time variable state visualization
 * - Playback controls
 * - Custom input support
 * - Complexity analysis
 * - Code flow animation with line highlighting
 */

'use client'

import { useState, useEffect } from 'react'
import {
  CodeExecutionEngine,
  AlgorithmTemplates,
  type ExecutionResult,
} from './CodeExecutionEngine'
import { VariableStateVisualizer } from './VariableStateVisualizer'
import { PlaybackController } from './PlaybackController'

export interface CartesianVisualizerProps {
  initialCode?: string
  algorithm?: keyof typeof AlgorithmTemplates
  className?: string
}

export function CartesianVisualizer({
  initialCode,
  algorithm,
  className = '',
}: CartesianVisualizerProps) {
  const [code, setCode] = useState(initialCode || AlgorithmTemplates[algorithm || 'bubbleSort'])
  const [executionResult, setExecutionResult] = useState<ExecutionResult | null>(null)
  const [currentStep, setCurrentStep] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [speed, setSpeed] = useState(500)
  const [showCode, setShowCode] = useState(true)
  const [showVariables, setShowVariables] = useState(true)

  const engine = new CodeExecutionEngine()

  // Execute code when it changes
  useEffect(() => {
    const result = engine.execute(code)
    setExecutionResult(result)
    setCurrentStep(0)
    setIsPlaying(false)
  }, [code])

  // Auto-play animation
  useEffect(() => {
    if (isPlaying && executionResult && currentStep < executionResult.steps.length - 1) {
      const timer = setTimeout(() => setCurrentStep(currentStep + 1), speed)
      return () => clearTimeout(timer)
    } else if (isPlaying) {
      setIsPlaying(false)
    }
  }, [isPlaying, currentStep, executionResult, speed])

  const handleCodeChange = (newCode: string) => {
    setCode(newCode)
  }

  const handleAlgorithmSelect = (alg: keyof typeof AlgorithmTemplates) => {
    setCode(AlgorithmTemplates[alg])
  }

  const getCurrentExecutionState = () => {
    if (!executionResult || executionResult.steps.length === 0) return null
    return executionResult.steps[currentStep] || executionResult.steps[0]
  }

  const getComplexityAnalysis = () => {
    if (code.includes('for') && code.includes('for')) {
      return {
        time: 'O(n²)',
        space: 'O(1)',
        description: 'Nested loops indicate quadratic time complexity',
      }
    } else if (code.includes('for') || code.includes('while')) {
      return {
        time: 'O(n)',
        space: 'O(1)',
        description: 'Single loop indicates linear time complexity',
      }
    } else if (code.includes('sort')) {
      return {
        time: 'O(n log n)',
        space: 'O(n)',
        description: 'Sorting algorithms typically have logarithmic time complexity',
      }
    }
    return {
      time: 'O(1)',
      space: 'O(1)',
      description: 'Constant time and space complexity',
    }
  }

  const complexity = getComplexityAnalysis()
  const currentExecution = getCurrentExecutionState()
  const lines = code.split('\n')

  return (
    <div className={`flex flex-col gap-4 ${className}`}>
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-t-lg p-4">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold">Interactive Code Visualizer</h2>
          <div className="flex gap-2">
            {Object.keys(AlgorithmTemplates).map((alg) => (
              <button
                key={alg}
                onClick={() => handleAlgorithmSelect(alg as keyof typeof AlgorithmTemplates)}
                className="px-3 py-1 bg-white/20 hover:bg-white/30 rounded text-sm transition"
              >
                {alg}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Code Flow Visualization */}
        {showCode && (
          <div className="bg-gray-900 rounded-lg overflow-hidden shadow-lg">
            <div className="bg-gray-800 px-4 py-2 flex items-center justify-between">
              <span className="text-white font-semibold">Code Flow</span>
              <button
                onClick={() => setShowCode(!showCode)}
                className="text-gray-400 hover:text-white text-sm"
              >
                {showCode ? 'Hide' : 'Show'}
              </button>
            </div>
            <div className="p-4 overflow-x-auto">
              <pre className="font-mono text-sm">
                {lines.map((line, index) => {
                  const lineNum = index + 1
                  const isCurrentLine = currentExecution?.line === lineNum
                  const isExecuted = executionResult?.steps.some(
                    (step) => step.line === lineNum && executionResult.steps.indexOf(step) <= currentStep
                  )

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
        )}

        {/* Variable State */}
        {showVariables && (
          <VariableStateVisualizer
            executionState={currentExecution}
            className="h-fit"
          />
        )}
      </div>

      {/* Description */}
      {currentExecution?.description && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm text-blue-900">{currentExecution.description}</p>
        </div>
      )}

      {/* Playback Controls */}
      {executionResult && (
        <PlaybackController
          totalSteps={executionResult.steps.length}
          currentStep={currentStep}
          onStepChange={setCurrentStep}
          isPlaying={isPlaying}
          onPlayPause={() => setIsPlaying(!isPlaying)}
          speed={speed}
          onSpeedChange={setSpeed}
        />
      )}

      {/* Complexity Analysis */}
      <div className="bg-white rounded-lg shadow-lg border border-gray-200 p-4">
        <h3 className="font-bold text-gray-800 mb-3">Complexity Analysis</h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <span className="text-sm text-gray-600">Time Complexity:</span>
            <span className="ml-2 font-mono font-semibold text-blue-600">{complexity.time}</span>
          </div>
          <div>
            <span className="text-sm text-gray-600">Space Complexity:</span>
            <span className="ml-2 font-mono font-semibold text-purple-600">{complexity.space}</span>
          </div>
        </div>
        <p className="text-sm text-gray-600 mt-2">{complexity.description}</p>
      </div>

      {/* Execution Summary */}
      {executionResult && (
        <div className="bg-white rounded-lg shadow-lg border border-gray-200 p-4">
          <h3 className="font-bold text-gray-800 mb-3">Execution Summary</h3>
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <span className="text-gray-600">Total Steps:</span>
              <span className="ml-2 font-semibold">{executionResult.steps.length}</span>
            </div>
            <div>
              <span className="text-gray-600">Variables:</span>
              <span className="ml-2 font-semibold">
                {Object.keys(executionResult.finalState).length}
              </span>
            </div>
            <div>
              <span className="text-gray-600">Status:</span>
              <span className={`ml-2 font-semibold ${executionResult.error ? 'text-red-600' : 'text-green-600'}`}>
                {executionResult.error ? 'Error' : 'Success'}
              </span>
            </div>
          </div>
          {executionResult.error && (
            <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
              {executionResult.error}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
