/**
 * Analytics Screen
 * 
 * Admin analytics dashboard with charts, metrics, and data visualization.
 */

'use client'

import { useEffect, useState } from 'react'
import { useServices } from '@/contexts'
import type { AnalyticsData } from '@/lib/core'

export default function AnalyticsScreen() {
  const services = useServices()
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    loadAnalytics()
  }, [])

  const loadAnalytics = async () => {
    try {
      setIsLoading(true)
      const params = {
        start_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
        end_date: new Date().toISOString(),
        granularity: 'day' as const,
      }
      const data = await services.dashboard.getAnalytics(params)
      setAnalytics(data)
    } catch (error) {
      console.error('Failed to load analytics:', error)
    } finally {
      setIsLoading(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-gray-600">Loading analytics...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
          <p className="text-gray-600 mt-1">System performance and learning analytics</p>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Engagement Metrics */}
        {analytics && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-700">Total Sessions</h3>
              <p className="text-4xl font-bold text-blue-600 mt-2">
                {analytics.engagement_metrics.total_sessions}
              </p>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-700">Tasks Completed</h3>
              <p className="text-4xl font-bold text-green-600 mt-2">
                {analytics.engagement_metrics.tasks_completed}
              </p>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-700">Accuracy Rate</h3>
              <p className="text-4xl font-bold text-purple-600 mt-2">
                {Math.round(analytics.engagement_metrics.accuracy * 100)}%
              </p>
            </div>
          </div>
        )}

        {/* Performance Metrics */}
        {analytics && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-700 mb-4">Performance Metrics</h3>
              <div className="space-y-4">
                <div>
                  <p className="text-sm text-gray-500">Overall Accuracy</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {Math.round(analytics.performance_metrics.overall_accuracy * 100)}%
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Avg Response Time</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {Math.round(analytics.performance_metrics.avg_response_time)}ms
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Completion Rate</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {Math.round(analytics.performance_metrics.completion_rate * 100)}%
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Learning Gain</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {Math.round(analytics.performance_metrics.learning_gain * 100)}%
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-700 mb-4">Engagement Metrics</h3>
              <div className="space-y-4">
                <div>
                  <p className="text-sm text-gray-500">Avg Session Duration</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {Math.round(analytics.engagement_metrics.avg_session_duration / 60)}m
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Avg Time on Task</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {Math.round(analytics.engagement_metrics.avg_time_on_task)}s
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Retention Rate</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {Math.round(analytics.performance_metrics.retention_rate * 100)}%
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Learning Curves */}
        {analytics && analytics.learning_curves.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-700 mb-4">Learning Curves</h3>
            <div className="space-y-4">
              {analytics.learning_curves.map((curve) => (
                <div key={curve.concept}>
                  <div className="flex justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700">{curve.concept}</span>
                    <span className="text-sm font-medium text-gray-700">
                      Current: {Math.round(curve.current_mastery * 100)}% | Target:{' '}
                      {Math.round(curve.target_mastery * 100)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="h-2 rounded-full bg-blue-600"
                      style={{ width: `${curve.current_mastery * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
