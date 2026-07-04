/**
 * Concept Detail Screen
 * 
 * Detailed view of a specific learning concept with mastery progress, related tasks, and learning history.
 */

'use client'

import { useEffect, useState } from 'react'
import { useAuth } from '@/contexts'
import { useServices } from '@/contexts'
import { useParams } from 'next/navigation'

interface ConceptData {
  concept: string
  mastery: number
  totalTasks: number
  completedTasks: number
  accuracy: number
  avgResponseTime: number
  relatedConcepts: string[]
  recentTasks: Array<{
    taskId: string
    completed: boolean
    correct: boolean
    timestamp: string
  }>
}

export default function ConceptDetailScreen() {
  const params = useParams()
  const conceptId = params.concept as string
  const { user } = useAuth()
  const services = useServices()
  const [conceptData, setConceptData] = useState<ConceptData | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    if (user && conceptId) {
      loadConceptData()
    }
  }, [user, conceptId])

  const loadConceptData = async () => {
    try {
      setIsLoading(true)
      // In production, this would call the learning service
      const data: ConceptData = {
        concept: conceptId,
        mastery: 0.75,
        totalTasks: 50,
        completedTasks: 38,
        accuracy: 0.82,
        avgResponseTime: 4500,
        relatedConcepts: ['Algebra', 'Geometry', 'Calculus'],
        recentTasks: [
          { taskId: 'task_001', completed: true, correct: true, timestamp: '2026-05-20T10:00:00Z' },
          { taskId: 'task_002', completed: true, correct: false, timestamp: '2026-05-20T10:05:00Z' },
          { taskId: 'task_003', completed: true, correct: true, timestamp: '2026-05-20T10:10:00Z' },
        ],
      }
      setConceptData(data)
    } catch (error) {
      console.error('Failed to load concept data:', error)
    } finally {
      setIsLoading(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-gray-600">Loading concept details...</div>
      </div>
    )
  }

  if (!conceptData) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-gray-600">Concept not found</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-gray-900">{conceptData.concept}</h1>
          <p className="text-gray-600 mt-1">Concept details and learning progress</p>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Mastery Overview */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Mastery Overview</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <p className="text-sm text-gray-500">Mastery Level</p>
              <p className="text-4xl font-bold text-blue-600 mt-2">
                {Math.round(conceptData.mastery * 100)}%
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Tasks Completed</p>
              <p className="text-4xl font-bold text-green-600 mt-2">
                {conceptData.completedTasks} / {conceptData.totalTasks}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Accuracy</p>
              <p className="text-4xl font-bold text-purple-600 mt-2">
                {Math.round(conceptData.accuracy * 100)}%
              </p>
            </div>
          </div>
          <div className="mt-6">
            <div className="flex justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">Progress</span>
              <span className="text-sm font-medium text-gray-700">
                {Math.round((conceptData.completedTasks / conceptData.totalTasks) * 100)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className="h-3 rounded-full bg-blue-600 transition-all"
                style={{ width: `${(conceptData.completedTasks / conceptData.totalTasks) * 100}%` }}
              />
            </div>
          </div>
        </div>

        {/* Related Concepts */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Related Concepts</h2>
          <div className="flex flex-wrap gap-2">
            {conceptData.relatedConcepts.map((concept) => (
              <button
                key={concept}
                className="px-4 py-2 bg-blue-100 text-blue-800 rounded-lg hover:bg-blue-200 transition"
              >
                {concept}
              </button>
            ))}
          </div>
        </div>

        {/* Recent Tasks */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Recent Tasks</h2>
          <div className="space-y-3">
            {conceptData.recentTasks.map((task) => (
              <div key={task.taskId} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div>
                  <p className="font-medium text-gray-900">{task.taskId}</p>
                  <p className="text-sm text-gray-500">{new Date(task.timestamp).toLocaleString()}</p>
                </div>
                <div className="flex items-center gap-4">
                  {task.correct ? (
                    <span className="text-green-600 font-medium">Correct ✓</span>
                  ) : (
                    <span className="text-red-600 font-medium">Incorrect ✗</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  )
}
