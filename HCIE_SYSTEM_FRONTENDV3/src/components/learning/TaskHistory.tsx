/**
 * Task History Screen
 * 
 * Displays user's task submission history with filters, pagination, and detailed results.
 */

'use client'

import { useEffect, useState } from 'react'
import { useAuth } from '@/contexts'
import { useServices } from '@/contexts'

interface TaskHistoryItem {
  taskId: string
  concept: string
  completed: boolean
  correct: boolean
  responseTime: number
  timestamp: string
  difficulty: number
}

export default function TaskHistoryScreen() {
  const { user } = useAuth()
  const services = useServices()
  const [tasks, setTasks] = useState<TaskHistoryItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [filter, setFilter] = useState<'all' | 'correct' | 'incorrect'>('all')

  useEffect(() => {
    if (user) {
      loadTaskHistory()
    }
  }, [user])

  const loadTaskHistory = async () => {
    if (!user?.id) return
    try {
      setIsLoading(true)
      const token = typeof window !== 'undefined'
        ? (localStorage.getItem('hcie_auth_token') || localStorage.getItem('access_token') || '')
        : ''
      const headers: HeadersInit = token ? { Authorization: `Bearer ${token}` } : {}
      const r = await fetch(
        `/v3/frontend/dashboard/session-trace/${user.id}?limit=500`,
        { headers, signal: AbortSignal.timeout(8000) }
      )
      if (!r.ok) throw new Error(`${r.status}`)
      const d = await r.json()
      // Map session_trace trace rows → TaskHistoryItem
      // endpoint returns {trace: [...], count, session_summary} — NOT 'interactions'
      const interactions: any[] = d.trace ?? []
      const history: TaskHistoryItem[] = interactions.map((ix: any) => ({
        taskId:       ix.interaction_id ?? ix.task_id ?? ix.event_id ?? 'unknown',
        concept:      ix.concept_id ?? ix.concept ?? 'unknown',
        completed:    true,
        correct:      Boolean(ix.correct ?? ix.correctness),
        // response_time in seconds (may be null for synthetic); convert to ms
        responseTime: ix.response_time != null ? Math.round(Number(ix.response_time) * 1000) : 0,
        timestamp:    (ix.timestamp ?? new Date().toISOString()).replace(' ', 'T'),
        difficulty:   Number(ix.difficulty ?? 0.5),
      }))
      setTasks(history)
    } catch (error) {
      console.error('Failed to load task history:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const filteredTasks = tasks.filter((task) => {
    if (filter === 'all') return true
    if (filter === 'correct') return task.correct
    if (filter === 'incorrect') return !task.correct
    return true
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-gray-600">Loading task history...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-gray-900">Task History</h1>
          <p className="text-gray-600 mt-1">View your task submission history</p>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Filters */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="flex gap-4">
            <button
              onClick={() => setFilter('all')}
              className={`px-4 py-2 rounded-lg font-medium transition ${
                filter === 'all' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              All Tasks
            </button>
            <button
              onClick={() => setFilter('correct')}
              className={`px-4 py-2 rounded-lg font-medium transition ${
                filter === 'correct' ? 'bg-green-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Correct
            </button>
            <button
              onClick={() => setFilter('incorrect')}
              className={`px-4 py-2 rounded-lg font-medium transition ${
                filter === 'incorrect' ? 'bg-red-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Incorrect
            </button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-sm text-gray-500">Total Tasks</p>
            <p className="text-3xl font-bold text-blue-600 mt-2">{tasks.length}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-sm text-gray-500">Correct</p>
            <p className="text-3xl font-bold text-green-600 mt-2">
              {tasks.filter((t) => t.correct).length}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-sm text-gray-500">Accuracy</p>
            <p className="text-3xl font-bold text-purple-600 mt-2">
              {tasks.length > 0 ? Math.round((tasks.filter((t) => t.correct).length / tasks.length) * 100) : 0}%
            </p>
          </div>
        </div>

        {/* Task List */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Task ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Concept
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Result
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Difficulty
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Response Time
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {filteredTasks.map((task) => (
                <tr key={task.taskId}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {task.taskId}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{task.concept}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {task.correct ? (
                      <span className="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                        Correct
                      </span>
                    ) : (
                      <span className="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-100 text-red-800">
                        Incorrect
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {Math.round(task.difficulty * 100)}%
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {Math.round(task.responseTime / 1000)}s
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(task.timestamp).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  )
}
