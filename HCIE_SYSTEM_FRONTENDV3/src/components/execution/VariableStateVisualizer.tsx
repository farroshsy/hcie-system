/**
 * Variable State Visualizer
 *
 * Real-time visualization of variable states during code execution.
 * Shows variable changes with highlighting and history.
 */

'use client'

import { useState } from 'react'
import { ExecutionState } from './CodeExecutionEngine'

export interface VariableStateVisualizerProps {
  executionState: ExecutionState | null
  className?: string
  showHistory?: boolean
}

export function VariableStateVisualizer({
  executionState,
  className = '',
  showHistory = true,
}: VariableStateVisualizerProps) {
  const [expandedVars, setExpandedVars] = useState<Set<string>>(new Set())

  const toggleVar = (varName: string) => {
    const newExpanded = new Set(expandedVars)
    if (newExpanded.has(varName)) {
      newExpanded.delete(varName)
    } else {
      newExpanded.add(varName)
    }
    setExpandedVars(newExpanded)
  }

  const formatValue = (value: any): string => {
    if (value === null) return 'null'
    if (value === undefined) return 'undefined'
    if (typeof value === 'object') {
      try {
        return JSON.stringify(value, null, 2)
      } catch {
        return String(value)
      }
    }
    return String(value)
  }

  const getValueType = (value: any): string => {
    if (value === null) return 'null'
    if (Array.isArray(value)) return 'array'
    return typeof value
  }

  if (!executionState) {
    return (
      <div className={`bg-gray-50 rounded-lg p-4 ${className}`}>
        <div className="text-gray-500 text-sm">No execution state available</div>
      </div>
    )
  }

  return (
    <div className={`bg-white rounded-lg shadow-lg border border-gray-200 ${className}`}>
      <div className="bg-gray-800 text-white px-4 py-2 rounded-t-lg flex items-center justify-between">
        <span className="font-semibold">Variable State</span>
        <span className="text-sm text-gray-300">Line {executionState.line}</span>
      </div>

      <div className="p-4 space-y-3">
        {Object.entries(executionState.variables).length === 0 ? (
          <div className="text-gray-500 text-sm">No variables in scope</div>
        ) : (
          Object.entries(executionState.variables).map(([name, value]) => (
            <div
              key={name}
              className="border border-gray-200 rounded-lg overflow-hidden"
            >
              <div
                className="bg-gray-50 px-3 py-2 flex items-center justify-between cursor-pointer hover:bg-gray-100 transition"
                onClick={() => toggleVar(name)}
              >
                <div className="flex items-center gap-2">
                  <span className="font-mono font-semibold text-blue-600">{name}</span>
                  <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded">
                    {getValueType(value)}
                  </span>
                </div>
                <span className="text-gray-400">
                  {expandedVars.has(name) ? '▼' : '▶'}
                </span>
              </div>
              {expandedVars.has(name) && (
                <div className="bg-white p-3">
                  <pre className="text-sm font-mono bg-gray-50 p-2 rounded overflow-x-auto">
                    {formatValue(value)}
                  </pre>
                </div>
              )}
            </div>
          ))
        )}

        {executionState.description && (
          <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="text-sm text-blue-900">
              <span className="font-semibold">Description:</span> {executionState.description}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
