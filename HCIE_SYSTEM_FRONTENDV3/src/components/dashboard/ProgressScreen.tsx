/**
 * Progress Screen
 *
 * Displays detailed learning progress including mastery levels, completed tasks,
 * and learning analytics.
 */

'use client'

import { useEffect, useState } from 'react'
import { useAuth } from '@/contexts'
import { useServices } from '@/contexts'
import { useLearningProgress } from '@/hooks/useWebSocket'
import type { LearningState, Progress } from '@/lib/core'
import { Activity, TrendingUp, Target } from 'lucide-react'

export default function ProgressScreen() {
  const { user } = useAuth()
  const services = useServices()
  const [learningState, setLearningState] = useState<LearningState | null>(null)
  const [progress, setProgress] = useState<Progress | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Real-time learning progress via WebSocket
  const { masteryUpdates, banditScores, notifications } = useLearningProgress()

  useEffect(() => {
    if (user) {
      loadProgressData()
    }
  }, [user])

  const loadProgressData = async () => {
    try {
      setIsLoading(true)
      const [state, prog] = await Promise.all([
        services.learning.getLearningState(user!.id),
        services.learning.getProgress(user!.id),
      ])
      setLearningState(state)
      setProgress(prog)
    } catch (error) {
      console.error('Failed to load progress data:', error)
    } finally {
      setIsLoading(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-gray-600">Loading progress...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Real-time Progress */}
        {(Object.keys(masteryUpdates).length > 0 || Object.keys(banditScores).length > 0) && (
          <div className="bg-white rounded-lg shadow p-6 mb-8">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <Activity className="w-5 h-5 text-blue-600" />
              Real-time Progress Updates
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.keys(masteryUpdates).length > 0 && (
                <div className="bg-blue-50 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <TrendingUp className="w-4 h-4 text-blue-600" />
                    <span className="text-sm font-medium text-gray-700">Recent Mastery Updates</span>
                  </div>
                  <div className="space-y-1">
                    {Object.entries(masteryUpdates).slice(0, 5).map(([concept, value]) => (
                      <div key={concept} className="flex justify-between text-sm">
                        <span className="text-gray-600">{concept}</span>
                        <span className="font-medium text-gray-900">{(value * 100).toFixed(1)}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {Object.keys(banditScores).length > 0 && (
                <div className="bg-green-50 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Target className="w-4 h-4 text-green-600" />
                    <span className="text-sm font-medium text-gray-700">Policy Scores</span>
                  </div>
                  <div className="space-y-1">
                    {Object.entries(banditScores).slice(0, 5).map(([policy, score]) => (
                      <div key={policy} className="flex justify-between text-sm">
                        <span className="text-gray-600">{policy}</span>
                        <span className="font-medium text-gray-900">{score.toFixed(3)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
            {notifications.length > 0 && (
              <div className="mt-4 space-y-2">
                {notifications.slice(0, 3).map((notification, index) => (
                  <div key={index} className="text-sm text-gray-600 bg-gray-50 rounded px-3 py-2">
                    {notification}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Overview Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-600">Tasks Completed</h3>
            <p className="text-3xl font-bold text-blue-600 mt-2">
              {progress?.completed_tasks || 0} / {progress?.total_tasks || 0}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-600">Overall Accuracy</h3>
            <p className="text-3xl font-bold text-green-600 mt-2">
              {Math.round((progress?.accuracy || 0) * 100)}%
            </p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-600">Time Spent</h3>
            <p className="text-3xl font-bold text-purple-600 mt-2">
              {Math.round((progress?.time_spent || 0) / 60)}m
            </p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-600">Current Streak</h3>
            <p className="text-3xl font-bold text-orange-600 mt-2">
              {progress?.streak || 0}
            </p>
          </div>
        </div>

        {/* Mastery by Concept */}
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Mastery by Concept</h2>
          {learningState && Object.keys(learningState.mastery).length > 0 ? (
            <div className="space-y-4">
              {Object.entries(learningState.mastery).map(([concept, mastery]) => (
                <div key={concept}>
                  <div className="flex justify-between mb-1">
                    <span className="text-sm font-medium text-gray-700">{concept}</span>
                    <span className="text-sm font-medium text-gray-700">
                      {Math.round(mastery * 100)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full transition-all ${
                        mastery > 0.8 ? 'bg-green-500' : mastery > 0.5 ? 'bg-yellow-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${mastery * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-600">No mastery data available</p>
          )}
        </div>

        {/* Mastered Concepts */}
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Mastered Concepts</h2>
          {progress && progress.concepts_mastered.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {progress.concepts_mastered.map((concept) => (
                <span
                  key={concept}
                  className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium"
                >
                  {concept}
                </span>
              ))}
            </div>
          ) : (
            <p className="text-gray-600">No concepts mastered yet</p>
          )}
        </div>

        {/* Learning Projection */}
        {learningState && learningState.projection && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Learning Projection</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="text-sm font-medium text-gray-600 mb-2">Governance Metrics</h3>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-700">Volatility</span>
                    <span className="text-sm font-medium text-gray-900">
                      {Math.round(learningState.projection.governance_metrics.volatility * 100)}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-700">Stability</span>
                    <span className="text-sm font-medium text-gray-900">
                      {Math.round(learningState.projection.governance_metrics.stability * 100)}%
                    </span>
                  </div>
                </div>
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-600 mb-2">Ensemble Weights</h3>
                <div className="space-y-2">
                  {Object.entries(learningState.projection.ensemble_weights).map(([learner, weight]) => (
                    <div key={learner} className="flex justify-between">
                      <span className="text-sm text-gray-700">{learner}</span>
                      <span className="text-sm font-medium text-gray-900">
                        {Math.round(weight * 100)}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
