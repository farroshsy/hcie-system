/**
 * CodeSnippet
 *
 * Interactive code snippet display with syntax highlighting.
 * Shows code with line numbers, highlighting, and execution tracking.
 */

'use client'

import { useState } from 'react'

export interface CodeSnippetProps {
  code: string
  language?: string
  highlightedLines?: number[]
  className?: string
  showLineNumbers?: boolean
  fontSize?: 'sm' | 'md' | 'lg'
}

export function CodeSnippet({
  code,
  language = 'typescript',
  highlightedLines = [],
  className = '',
  showLineNumbers = true,
  fontSize = 'md',
}: CodeSnippetProps) {
  const fontSizes = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base',
  }

  const lines = code.split('\n')

  return (
    <div className={`bg-gray-900 rounded-lg overflow-hidden ${className}`}>
      <div className="bg-gray-800 px-4 py-2 flex items-center justify-between">
        <span className="text-gray-400 text-sm font-mono">{language}</span>
        <div className="flex gap-2">
          <div className="w-3 h-3 rounded-full bg-red-500" />
          <div className="w-3 h-3 rounded-full bg-yellow-500" />
          <div className="w-3 h-3 rounded-full bg-green-500" />
        </div>
      </div>
      <div className="p-4 overflow-x-auto">
        <pre className={`font-mono ${fontSizes[fontSize]}`}>
          {lines.map((line, index) => {
            const isHighlighted = highlightedLines.includes(index + 1)

            return (
              <div
                key={index}
                className={`flex hover:bg-gray-800 transition-colors ${
                  isHighlighted ? 'bg-blue-900/30' : ''
                }`}
              >
                {showLineNumbers && (
                  <span className="text-gray-600 w-8 text-right pr-4 select-none">
                    {index + 1}
                  </span>
                )}
                <code className="text-gray-300 whitespace-pre">{line || ' '}</code>
              </div>
            )
          })}
        </pre>
      </div>
    </div>
  )
}
