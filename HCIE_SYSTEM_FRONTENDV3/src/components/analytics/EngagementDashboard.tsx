'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import type { AnalyticsData } from '@/types/learning'
import { DemoDataBadge } from '@/components/DemoDataBadge'

export function EngagementDashboard() {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [dateRange, setDateRange] = useState<'7d' | '30d' | '90d'>('30d')

  useEffect(() => {
    loadAnalytics()
  }, [dateRange])

  const loadAnalytics = async () => {
    try {
      setIsLoading(true)
      // Backend API fetch - ready for integration
      // const response = await fetch(`/api/analytics?range=${dateRange}`)
      // const data = await response.json()
      // setAnalytics(data)
      
      // Mock data for now
      const mockData: AnalyticsData = {
        engagement_metrics: {
          totalSessions: 45,
          tasksCompleted: 32,
          accuracy: 0.78,
          avgSessionDuration: 1800, // 30 minutes
          avgTimeOnTask: 45, // 45 seconds
          retentionRate: 0.85
        },
        performance_metrics: {
          overallAccuracy: 0.78,
          avgResponseTime: 45,
          completionRate: 0.71,
          learningGain: 0.35,
          retentionRate: 0.85
        },
        learning_curves: [
          { concept: 'k2_algorithms', current_mastery: 0.85, target_mastery: 0.9 },
          { concept: 'k5_algorithms', current_mastery: 0.45, target_mastery: 0.8 },
          { concept: 'k8_variables', current_mastery: 0.0, target_mastery: 0.8 },
          { concept: 'k12_control_structures', current_mastery: 0.0, target_mastery: 0.8 }
        ],
        heatmap_data: {
          timeOfDay: [
            { hour: 8, performance: 0.75 },
            { hour: 9, performance: 0.82 },
            { hour: 10, performance: 0.88 },
            { hour: 11, performance: 0.85 },
            { hour: 12, performance: 0.70 },
            { hour: 13, performance: 0.72 },
            { hour: 14, performance: 0.80 },
            { hour: 15, performance: 0.86 },
            { hour: 16, performance: 0.84 },
            { hour: 17, performance: 0.78 },
            { hour: 18, performance: 0.72 },
            { hour: 19, performance: 0.68 }
          ],
          conceptDifficulty: [
            { concept: 'k2_algorithms', difficulty: 0.2, performance: 0.85 },
            { concept: 'k5_algorithms', difficulty: 0.4, performance: 0.45 },
            { concept: 'k8_variables', difficulty: 0.6, performance: 0.0 },
            { concept: 'k12_control_structures', difficulty: 0.8, performance: 0.0 }
          ]
        }
      }
      setAnalytics(mockData)
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

  if (!analytics) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-gray-600">No analytics data available</div>
      </div>
    )
  }

  const { engagement_metrics, performance_metrics, heatmap_data } = analytics

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 pt-4">
        <DemoDataBadge what="research engagement analytics" />
      </div>
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Student Engagement Analytics <span className="text-base font-normal text-amber-600">(Illustrative Demo)</span></h1>
              <p className="text-gray-600 mt-1">Track learning patterns and performance</p>
            </div>
            <div className="flex gap-2">
              {(['7d', '30d', '90d'] as const).map((range) => (
                <Button
                  key={range}
                  variant={dateRange === range ? 'default' : 'outline'}
                  onClick={() => setDateRange(range)}
                >
                  {range === '7d' ? '7 Days' : range === '30d' ? '30 Days' : '90 Days'}
                </Button>
              ))}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Engagement Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <Card>
            <CardHeader>
              <CardTitle>Total Sessions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-4xl font-bold text-blue-600">{engagement_metrics.totalSessions}</div>
              <p className="text-sm text-gray-600 mt-2">
                Avg duration: {Math.round(engagement_metrics.avgSessionDuration / 60)} minutes
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Tasks Completed</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-4xl font-bold text-green-600">{engagement_metrics.tasksCompleted}</div>
              <p className="text-sm text-gray-600 mt-2">
                Avg time per task: {engagement_metrics.avgTimeOnTask}s
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Accuracy Rate</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-4xl font-bold text-purple-600">
                {Math.round(engagement_metrics.accuracy * 100)}%
              </div>
              <p className="text-sm text-gray-600 mt-2">
                Retention: {Math.round(engagement_metrics.retentionRate * 100)}%
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Performance Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <Card>
            <CardHeader>
              <CardTitle>Performance Overview</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-sm text-gray-500">Overall Accuracy</p>
                <p className="text-2xl font-bold text-gray-900">
                  {Math.round(performance_metrics.overallAccuracy * 100)}%
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Avg Response Time</p>
                <p className="text-2xl font-bold text-gray-900">
                  {Math.round(performance_metrics.avgResponseTime)}s
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Completion Rate</p>
                <p className="text-2xl font-bold text-gray-900">
                  {Math.round(performance_metrics.completionRate * 100)}%
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Learning Gain</p>
                <p className="text-2xl font-bold text-gray-900">
                  {Math.round(performance_metrics.learningGain * 100)}%
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Engagement Trends</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-sm text-gray-500">Avg Session Duration</p>
                <p className="text-2xl font-bold text-gray-900">
                  {Math.round(engagement_metrics.avgSessionDuration / 60)}m
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Avg Time on Task</p>
                <p className="text-2xl font-bold text-gray-900">
                  {Math.round(engagement_metrics.avgTimeOnTask)}s
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Retention Rate</p>
                <p className="text-2xl font-bold text-gray-900">
                  {Math.round(performance_metrics.retentionRate * 100)}%
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Time of Day Heatmap */}
        {heatmap_data && (
          <Card className="mb-8">
            <CardHeader>
              <CardTitle>Performance by Time of Day</CardTitle>
              <CardDescription>Identify optimal learning times</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={heatmap_data.timeOfDay}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="hour" label={{ value: 'Hour', position: 'insideBottom', offset: -5 }} />
                    <YAxis label={{ value: 'Performance', angle: -90, position: 'insideLeft' }} />
                    <Tooltip />
                    <Bar dataKey="performance" fill="#3b82f6" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Concept Difficulty Heatmap */}
        {heatmap_data && (
          <Card>
            <CardHeader>
              <CardTitle>Performance by Concept Difficulty</CardTitle>
              <CardDescription>How performance varies with concept difficulty</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={heatmap_data.conceptDifficulty}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="concept" />
                    <YAxis label={{ value: 'Performance', angle: -90, position: 'insideLeft' }} />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="difficulty" fill="#ef4444" name="Difficulty" />
                    <Bar dataKey="performance" fill="#3b82f6" name="Performance" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        )}
      </main>
    </div>
  )
}
