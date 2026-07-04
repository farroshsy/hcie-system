'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { mockConcepts } from '@/data/mockLearningData'
import type { ExportData, LearningSession, AnalyticsData } from '@/types/learning'
import { DemoDataBadge } from '@/components/DemoDataBadge'

export function DataExport() {
  const [isExporting, setIsExporting] = useState(false)
  const [lastExport, setLastExport] = useState<string | null>(null)

  const generateExportData = (): ExportData => {
    const mockSessions: LearningSession[] = [
      {
        id: 'session-001',
        conceptId: 'k2_algorithms',
        taskId: 'k2_algorithms_text_v1',
        method: 'text',
        startTime: new Date(Date.now() - 86400000),
        endTime: new Date(Date.now() - 86400000 + 300000),
        completed: true,
        score: 0.9,
        answers: { 'ex-001': 'A recipe' },
        timeSpent: 300
      },
      {
        id: 'session-002',
        conceptId: 'k2_algorithms',
        taskId: 'k2_algorithms_code_v1',
        method: 'code',
        startTime: new Date(Date.now() - 172800000),
        endTime: new Date(Date.now() - 172800000 + 600000),
        completed: true,
        score: 0.85,
        answers: {},
        timeSpent: 600
      }
    ]

    const mockAnalytics: AnalyticsData = {
      engagement_metrics: {
        totalSessions: 45,
        tasksCompleted: 32,
        accuracy: 0.78,
        avgSessionDuration: 1800,
        avgTimeOnTask: 45,
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
        { concept: 'k5_algorithms', current_mastery: 0.45, target_mastery: 0.8 }
      ]
    }

    return {
      userId: 'user-001',
      exportDate: new Date().toISOString(),
      concepts: mockConcepts,
      sessions: mockSessions,
      analytics: mockAnalytics
    }
  }

  const exportToCSV = () => {
    setIsExporting(true)
    try {
      const data = generateExportData()
      
      // Flatten concepts for CSV
      const csvRows = [
        ['Export Date', data.exportDate],
        ['User ID', data.userId],
        [],
        ['Engagement Metrics'],
        ['Total Sessions', data.analytics.engagement_metrics.totalSessions],
        ['Tasks Completed', data.analytics.engagement_metrics.tasksCompleted],
        ['Accuracy', data.analytics.engagement_metrics.accuracy],
        ['Avg Session Duration (s)', data.analytics.engagement_metrics.avgSessionDuration],
        ['Avg Time on Task (s)', data.analytics.engagement_metrics.avgTimeOnTask],
        ['Retention Rate', data.analytics.engagement_metrics.retentionRate],
        [],
        ['Concept Mastery'],
        ...data.concepts.map(c => [
          c.id,
          c.masteryLevel,
          c.masteryProbability,
          c.confidenceInterval.lower,
          c.confidenceInterval.upper,
          c.banditScore || 'N/A',
          c.recommended ? 'Yes' : 'No'
        ]),
        [],
        ['Sessions'],
        ...data.sessions.map(s => [
          s.id,
          s.conceptId,
          s.taskId,
          s.method,
          s.startTime.toISOString(),
          s.endTime?.toISOString() || 'N/A',
          s.completed,
          s.score || 'N/A',
          s.timeSpent
        ])
      ]

      const csvContent = csvRows.map(row => row.join(',')).join('\n')
      const blob = new Blob([csvContent], { type: 'text/csv' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `learning_data_${new Date().toISOString().split('T')[0]}.csv`
      link.click()
      URL.revokeObjectURL(url)
      
      setLastExport(new Date().toISOString())
    } catch (error) {
      console.error('Export failed:', error)
    } finally {
      setIsExporting(false)
    }
  }

  const exportToJSON = async () => {
    setIsExporting(true)
    try {
      const data = generateExportData()
      
      // Backend API fetch - ready for integration
      // const response = await fetch('/api/analytics/export', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({ format: 'json', dateRange: '30d' })
      // })
      // const blob = await response.blob()
      
      const jsonContent = JSON.stringify(data, null, 2)
      const blob = new Blob([jsonContent], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `learning_data_${new Date().toISOString().split('T')[0]}.json`
      link.click()
      URL.revokeObjectURL(url)
      
      setLastExport(new Date().toISOString())
    } catch (error) {
      console.error('Export failed:', error)
    } finally {
      setIsExporting(false)
    }
  }

  return (
    <Card>
      <div style={{ padding: '12px 12px 0' }}>
        <DemoDataBadge what="exported data is synthetic — not your data" />
      </div>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Data Export <span className="text-sm font-normal text-amber-600">(Illustrative Demo)</span></span>
          {lastExport && (
            <Badge variant="outline">
              Last: {new Date(lastExport).toLocaleTimeString()}
            </Badge>
          )}
        </CardTitle>
        <CardDescription>
          Exports a SAMPLE dataset to demonstrate the export format — not your real learning history.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <p className="text-sm font-medium">Export Format</p>
          <p className="text-sm text-gray-600">
            Choose your preferred format. Both produce a SAMPLE export (illustrative concepts/sessions/
            analytics) to demonstrate structure — this research deployment has no per-user export endpoint.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 border rounded-lg">
            <div className="font-medium mb-2">CSV Format</div>
            <p className="text-sm text-gray-600 mb-4">
              Spreadsheet-compatible format with flattened data structure
            </p>
            <Button
              onClick={exportToCSV}
              disabled={isExporting}
              className="w-full"
            >
              {isExporting ? 'Exporting...' : 'Export CSV'}
            </Button>
          </div>

          <div className="p-4 border rounded-lg">
            <div className="font-medium mb-2">JSON Format</div>
            <p className="text-sm text-gray-600 mb-4">
              Full structured data with nested objects and arrays
            </p>
            <Button
              onClick={exportToJSON}
              disabled={isExporting}
              className="w-full"
              variant="outline"
            >
              {isExporting ? 'Exporting...' : 'Export JSON'}
            </Button>
          </div>
        </div>

        <div className="space-y-2">
          <p className="text-sm font-medium">Data Included</p>
          <div className="text-sm text-gray-600 space-y-1">
            <div>• Concept mastery and knowledge tracing data</div>
            <div>• Learning sessions with task completion</div>
            <div>• Engagement metrics (sessions, accuracy, time)</div>
            <div>• Performance metrics (response time, completion rate)</div>
            <div>• Learning curves and progress over time</div>
            <div>• Spaced repetition schedules</div>
            <div>• IRT-calibrated difficulty parameters</div>
          </div>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
          <p className="text-sm text-blue-800">
            <strong>Research Ready:</strong> Exported data includes all adaptive ITS metrics needed
            for educational research, including knowledge tracing probabilities, confidence intervals,
            and bandit selection scores.
          </p>
        </div>
      </CardContent>
    </Card>
  )
}
