/**
 * Visualizations Showcase Page
 *
 * Interactive showcase of all algorithm visualization components.
 */

'use client'

import { useState, useEffect } from 'react'
import { useT } from '@/contexts/language_context'
import {
  ArrayVisualizer,
  BinaryVisualizer,
  MatrixVisualizer,
  LinkedListVisualizer,
  TreeVisualizer,
  GraphVisualizer,
  StringVisualizer,
  SortingVisualizer,
} from '@/components/visualizations'
import {
  CartesianVisualizer,
} from '@/components/execution'

export default function VisualizationsPage() {
  const t = useT()
  const [selectedViz, setSelectedViz] = useState('sorting')
  const [arrayData, setArrayData] = useState('5,2,8,1,9,3,7,4,6')
  const [binaryData, setBinaryData] = useState('11010110')
  const [stringData, setStringData] = useState('HELLO WORLD')
  const [sortStep, setSortStep] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)

  // Sorting animation with actual value changes
  const sortArray = arrayData.split(',').map(Number)
  const [currentArray, setCurrentArray] = useState(sortArray)
  const [sortSteps, setSortSteps] = useState<number[][]>([])
  
  // Pre-calculate all bubble sort steps
  useEffect(() => {
    const arr = [...sortArray]
    const steps: number[][] = [arr.map(x => x)]
    
    for (let i = 0; i < arr.length - 1; i++) {
      for (let j = 0; j < arr.length - i - 1; j++) {
        if (arr[j] > arr[j + 1]) {
          [arr[j], arr[j + 1]] = [arr[j + 1], arr[j]]
          steps.push(arr.map(x => x))
        }
      }
    }
    
    setSortSteps(steps)
    setCurrentArray(steps[0] || sortArray)
    setSortStep(0)
    setIsPlaying(false)
  }, [arrayData])

  // Update current array when step changes
  useEffect(() => {
    if (sortSteps[sortStep]) {
      setCurrentArray(sortSteps[sortStep])
    }
  }, [sortStep, sortSteps])

  useEffect(() => {
    if (isPlaying && sortStep < sortSteps.length - 1) {
      const timer = setTimeout(() => setSortStep(sortStep + 1), 500)
      return () => clearTimeout(timer)
    } else if (isPlaying) {
      setIsPlaying(false)
    }
  }, [isPlaying, sortStep, sortSteps.length])

  const visualizations = [
    { id: 'array', name: 'Array', icon: '📊', color: 'bg-blue-500' },
    { id: 'binary', name: 'Binary', icon: '💻', color: 'bg-purple-500' },
    { id: 'matrix', name: 'Matrix', icon: '🔢', color: 'bg-green-500' },
    { id: 'linkedlist', name: 'Linked List', icon: '🔗', color: 'bg-orange-500' },
    { id: 'tree', name: 'Tree', icon: '🌳', color: 'bg-teal-500' },
    { id: 'graph', name: 'Graph', icon: '🕸️', color: 'bg-pink-500' },
    { id: 'string', name: 'String', icon: '📝', color: 'bg-indigo-500' },
    { id: 'sorting', name: 'Sorting', icon: '📈', color: 'bg-red-500' },
    { id: 'code', name: 'Code Flow', icon: '💻', color: 'bg-violet-600' },
  ]

  const getVizDescription = (id: string) => {
    const descriptions: Record<string, string> = {
      array: 'Visualize array operations with highlighting',
      binary: 'Display binary sequences with bit manipulation',
      matrix: 'Show 2D matrices with cell operations',
      linkedlist: 'Demonstrate linked list structure and pointers',
      tree: 'Visualize binary and general tree structures',
      graph: 'Display directed/undirected graphs with weights',
      string: 'Show string manipulation operations',
      sorting: 'Interactive sorting algorithm visualization',
      code: 'Interactive code visualization with step-by-step execution, variable tracking, and playback controls',
    }
    return descriptions[id] || ''
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-white mb-4 tracking-tight">
            {t('visualizations.eyebrow')}
          </h1>
          <p className="text-xl text-purple-200">
            {t('visualizations.title')}
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Sidebar */}
          <div className="lg:col-span-1">
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl shadow-2xl p-6 border border-white/20">
              <h2 className="text-xl font-bold text-white mb-6">Select Visualization</h2>
              <div className="space-y-3">
                {visualizations.map((viz) => (
                  <button
                    key={viz.id}
                    onClick={() => setSelectedViz(viz.id)}
                    className={`w-full text-left px-4 py-3 rounded-xl transition-all duration-300 transform hover:scale-105 ${
                      selectedViz === viz.id
                        ? `${viz.color} text-white shadow-lg`
                        : 'bg-white/10 text-white hover:bg-white/20'
                    }`}
                  >
                    <span className="mr-3 text-2xl">{viz.icon}</span>
                    <span className="font-semibold">{viz.name}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3">
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl shadow-2xl p-8 border border-white/20">
              <div className="mb-6">
                <h2 className="text-3xl font-bold text-white mb-2">
                  {visualizations.find(v => v.id === selectedViz)?.name} Visualizer
                </h2>
                <p className="text-purple-200">{getVizDescription(selectedViz)}</p>
              </div>

              {selectedViz === 'array' && (
                <div className="space-y-6">
                  <div className="bg-white/10 rounded-xl p-4">
                    <label className="block text-sm font-medium text-white mb-2">Array Data (comma-separated)</label>
                    <input
                      type="text"
                      value={arrayData}
                      onChange={(e) => setArrayData(e.target.value)}
                      className="w-full px-4 py-3 bg-white/90 rounded-lg border-2 border-white/30 text-gray-900 focus:border-blue-500 focus:outline-none transition"
                      placeholder="1,2,3,4,5"
                    />
                  </div>
                  <div className="bg-white rounded-2xl p-8 shadow-xl">
                    <ArrayVisualizer
                      array={arrayData.split(',').map(Number)}
                      highlightedIndices={[0, 2, 4]}
                      comparedIndices={[1, 3]}
                      barColor="bg-blue-500"
                      highlightColor="bg-green-500"
                      compareColor="bg-yellow-500"
                    />
                  </div>
                </div>
              )}

              {selectedViz === 'binary' && (
                <div className="space-y-6">
                  <div className="bg-white/10 rounded-xl p-4">
                    <label className="block text-sm font-medium text-white mb-2">Binary Value</label>
                    <input
                      type="text"
                      value={binaryData}
                      onChange={(e) => setBinaryData(e.target.value)}
                      className="w-full px-4 py-3 bg-white/90 rounded-lg border-2 border-white/30 text-gray-900 focus:border-purple-500 focus:outline-none transition"
                      placeholder="11010110"
                    />
                  </div>
                  <div className="bg-white rounded-2xl p-8 shadow-xl">
                    <BinaryVisualizer
                      binary={binaryData}
                      highlightedBits={[0, 2, 4]}
                      bitSize="lg"
                    />
                  </div>
                </div>
              )}

              {selectedViz === 'matrix' && (
                <div className="bg-white rounded-2xl p-8 shadow-xl">
                  <MatrixVisualizer
                    matrix={[
                      [1, 2, 3],
                      [4, 5, 6],
                      [7, 8, 9],
                    ]}
                    highlightedCells={[{ row: 0, col: 0 }, { row: 1, col: 1 }]}
                    cellSize="lg"
                  />
                </div>
              )}

              {selectedViz === 'linkedlist' && (
                <div className="bg-white rounded-2xl p-8 shadow-xl">
                  <LinkedListVisualizer
                    nodes={[
                      { id: '1', value: 10, next: '2' },
                      { id: '2', value: 20, next: '3' },
                      { id: '3', value: 30, next: '4' },
                      { id: '4', value: 40, next: null },
                    ]}
                    highlightedNodes={['2']}
                    nodeSize="lg"
                  />
                </div>
              )}

              {selectedViz === 'tree' && (
                <div className="space-y-6">
                  <div className="bg-white rounded-2xl p-8 shadow-xl">
                    <TreeVisualizer
                      root={{
                        id: '1',
                        value: 50,
                        left: { id: '2', value: 30, left: { id: '4', value: 20 }, right: { id: '5', value: 40 } },
                        right: { id: '3', value: 70, left: { id: '6', value: 60 }, right: { id: '7', value: 80 } },
                      }}
                      highlightedNodes={['2']}
                      nodeSize="lg"
                    />
                  </div>
                  <div className="bg-white/10 rounded-xl p-4">
                    <h3 className="text-white font-semibold mb-3">Interactive Controls</h3>
                    <div className="flex gap-2 flex-wrap">
                      <button
                        onClick={() => setSelectedViz('tree')}
                        className="px-4 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700 text-sm"
                      >
                        Highlight Left Subtree
                      </button>
                      <button
                        onClick={() => setSelectedViz('tree')}
                        className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm"
                      >
                        Highlight Right Subtree
                      </button>
                      <button
                        onClick={() => setSelectedViz('tree')}
                        className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 text-sm"
                      >
                        Show Traversal Order
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {selectedViz === 'graph' && (
                <div className="space-y-6">
                  <div className="bg-white rounded-2xl p-8 shadow-xl">
                    <GraphVisualizer
                      nodes={[
                        { id: '1', label: 'A' },
                        { id: '2', label: 'B' },
                        { id: '3', label: 'C' },
                        { id: '4', label: 'D' },
                      ]}
                      edges={[
                        { from: '1', to: '2', weight: 5 },
                        { from: '2', to: '3', weight: 3 },
                        { from: '3', to: '4', weight: 7 },
                        { from: '4', to: '1', weight: 2 },
                      ]}
                      highlightedNodes={['1', '3']}
                      directed={true}
                      nodeSize="lg"
                    />
                  </div>
                  <div className="bg-white/10 rounded-xl p-4">
                    <h3 className="text-white font-semibold mb-3">Interactive Controls</h3>
                    <div className="flex gap-2 flex-wrap">
                      <button
                        onClick={() => setSelectedViz('graph')}
                        className="px-4 py-2 bg-pink-600 text-white rounded-lg hover:bg-pink-700 text-sm"
                      >
                        Highlight Path A→C
                      </button>
                      <button
                        onClick={() => setSelectedViz('graph')}
                        className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 text-sm"
                      >
                        Show All Edges
                      </button>
                      <button
                        onClick={() => setSelectedViz('graph')}
                        className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 text-sm"
                      >
                        Toggle Direction
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {selectedViz === 'string' && (
                <div className="space-y-6">
                  <div className="bg-white/10 rounded-xl p-4">
                    <label className="block text-sm font-medium text-white mb-2">String</label>
                    <input
                      type="text"
                      value={stringData}
                      onChange={(e) => setStringData(e.target.value)}
                      className="w-full px-4 py-3 bg-white/90 rounded-lg border-2 border-white/30 text-gray-900 focus:border-indigo-500 focus:outline-none transition"
                      placeholder="HELLO WORLD"
                    />
                  </div>
                  <div className="bg-white rounded-2xl p-8 shadow-xl">
                    <StringVisualizer
                      text={stringData}
                      highlightedIndices={[0, 2, 4]}
                      comparedIndices={[1, 3]}
                      charSize="lg"
                      highlightColor="bg-green-500"
                      compareColor="bg-yellow-500"
                    />
                  </div>
                </div>
              )}

              {selectedViz === 'sorting' && (
                <div className="space-y-6">
                  <div className="bg-white/10 rounded-xl p-4">
                    <label className="block text-sm font-medium text-white mb-2">Array Data (comma-separated)</label>
                    <input
                      type="text"
                      value={arrayData}
                      onChange={(e) => setArrayData(e.target.value)}
                      className="w-full px-4 py-3 bg-white/90 rounded-lg border-2 border-white/30 text-gray-900 focus:border-red-500 focus:outline-none transition"
                      placeholder="5,2,8,1,9,3,7,4,6"
                    />
                  </div>
                  <div className="bg-white rounded-2xl p-8 shadow-xl">
                    <SortingVisualizer
                      array={currentArray}
                      step={sortStep}
                      comparisons={[]}
                      swaps={[]}
                      sortedIndices={[]}
                      totalSteps={sortSteps.length}
                      onStepChange={setSortStep}
                      isPlaying={isPlaying}
                      onPlayPause={() => setIsPlaying(!isPlaying)}
                    />
                  </div>
                </div>
              )}

              {selectedViz === 'code' && (
                <CartesianVisualizer algorithm="bubbleSort" />
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
