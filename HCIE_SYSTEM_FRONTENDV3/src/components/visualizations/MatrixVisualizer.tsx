/**
 * MatrixVisualizer
 *
 * Interactive matrix visualization with highlighting for operations.
 * Shows 2D matrices with cell highlighting for row/column operations.
 */

'use client'

import { useState } from 'react'

export interface MatrixVisualizerProps {
  matrix: number[][]
  highlightedCells?: { row: number; col: number }[]
  highlightedRows?: number[]
  highlightedCols?: number[]
  className?: string
  cellSize?: 'sm' | 'md' | 'lg'
  showIndices?: boolean
}

export function MatrixVisualizer({
  matrix,
  highlightedCells = [],
  highlightedRows = [],
  highlightedCols = [],
  className = '',
  cellSize = 'md',
  showIndices = true,
}: MatrixVisualizerProps) {
  const cellSizes = {
    sm: 'w-8 h-8 text-sm',
    md: 'w-10 h-10 text-base',
    lg: 'w-12 h-12 text-lg',
  }

  const isCellHighlighted = (row: number, col: number) =>
    highlightedCells.some((cell) => cell.row === row && cell.col === col)
  const isRowHighlighted = (row: number) => highlightedRows.includes(row)
  const isColHighlighted = (col: number) => highlightedCols.includes(col)

  return (
    <div className={`flex flex-col items-center gap-2 ${className}`}>
      {showIndices && (
        <div className="flex gap-2 ml-6">
          {matrix[0]?.map((_, col) => (
            <div key={col} className="w-10 text-center text-xs text-gray-400">
              {col}
            </div>
          ))}
        </div>
      )}

      <div className="flex gap-2">
        {showIndices && (
          <div className="flex flex-col gap-2 mr-1">
            {matrix.map((_, row) => (
              <div key={row} className="h-10 flex items-center text-xs text-gray-400">
                {row}
              </div>
            ))}
          </div>
        )}

        <div className="flex flex-col gap-1">
          {matrix.map((row, rowIndex) => (
            <div key={rowIndex} className="flex gap-1">
              {row.map((value, colIndex) => {
                const isHighlighted =
                  isCellHighlighted(rowIndex, colIndex) ||
                  isRowHighlighted(rowIndex) ||
                  isColHighlighted(colIndex)

                return (
                  <div
                    key={colIndex}
                    className={`${cellSizes[cellSize]} flex items-center justify-center rounded border-2 transition-all duration-300 ${
                      isHighlighted
                        ? 'bg-green-500 border-green-600 text-white'
                        : 'bg-white border-gray-300 text-gray-900'
                    }`}
                  >
                    <span className="font-mono font-bold">{value}</span>
                  </div>
                )
              })}
            </div>
          ))}
        </div>
      </div>

      <div className="text-xs text-gray-500">
        {matrix.length} × {matrix[0]?.length || 0}
      </div>
    </div>
  )
}
