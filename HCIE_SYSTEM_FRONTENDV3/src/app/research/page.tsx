'use client'

export const dynamic = 'force-dynamic'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useT } from '@/contexts/language_context'
import { EngagementDashboard } from '@/components/analytics/EngagementDashboard'
import { DataExport } from '@/components/analytics/DataExport'
import { GovernanceTelemetryPanel } from '@/components/research/GovernanceTelemetryPanel'
import { NextSteps } from '@/components/review/NextSteps'
import { BarChart3, TrendingUp, Users, Target, Activity } from 'lucide-react'

// Old hooks hit /analytics/api/v1/* (nonexistent). Replaced with real /v3/frontend/* endpoints.

type UserInsights = {
  learning_velocity?: number
  concept_diversity?: number
  engagement_score?: number
  predicted_performance?: number
}

type LearningCurve = {
  concept: string
  mastery?: number
}

function useRealSystemStats() {
  return useQuery({
    queryKey: ['research-system-stats'],
    queryFn: async () => {
      const token = typeof window !== 'undefined'
        ? (localStorage.getItem('hcie_auth_token') || localStorage.getItem('access_token') || '') : ''
      const r = await fetch('/v3/frontend/dashboard/system-stats',
        { headers: token ? { Authorization: `Bearer ${token}` } : {}, signal: AbortSignal.timeout(8000) })
      if (!r.ok) return null
      return r.json()
    },
    refetchInterval: 60000,
  })
}

function useRealConceptPerformance() {
  return useQuery({
    queryKey: ['research-cohort-concepts'],
    queryFn: async () => {
      const token = typeof window !== 'undefined'
        ? (localStorage.getItem('hcie_auth_token') || localStorage.getItem('access_token') || '') : ''
      const r = await fetch('/v3/frontend/dashboard/cohort-concepts',
        { headers: token ? { Authorization: `Bearer ${token}` } : {}, signal: AbortSignal.timeout(8000) })
      if (!r.ok) return null
      const d = await r.json()
      return d.status === 'ok' ? d.concepts : null
    },
    refetchInterval: 60000,
  })
}

export default function ResearchPage() {
  const t = useT()
  const [selectedUserId, setSelectedUserId] = useState('')

  const { data: rawStats } = useRealSystemStats()
  const { data: conceptsData } = useRealConceptPerformance()

  // Map to the shape the rest of the page already expects
  const systemStats = rawStats ? {
    total_users:         rawStats.interactions?.unique_users ?? 0,
    total_interactions:  rawStats.interactions?.total        ?? 0,
    avg_mastery:         rawStats.interactions?.avg_correct  ?? 0,
    learning_velocity:   0,
  } : null

  const conceptPerformance = Array.isArray(conceptsData) ? conceptsData.map((c: any) => ({
    concept:            c.concept_id,
    total_interactions: c.student_count ?? 0,
    avg_mastery:        c.avg_mastery   ?? 0,
    improvement_rate:   0,
    difficulty_distribution: {},
  })) : null

  const userInsights = null as UserInsights | null
  const learningCurves = null as LearningCurve[] | null

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Live backend badge */}
      <div className="bg-green-50 border-b border-green-200 px-4 py-2 text-center">
        <span className="text-xs font-semibold text-green-700">● Live backend</span>
        <span className="text-xs text-green-600 ml-2">
          System-wide stats from <code className="font-mono text-xs">/v3/frontend/dashboard/system-stats</code>
          · Concept data from <code className="font-mono text-xs">/v3/frontend/dashboard/cohort-concepts</code>
        </span>
      </div>
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-gray-900">{t('research.title')}</h1>
          <p className="text-gray-600 mt-1">{t('research.eyebrow')}</p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8 space-y-6">
        {/* System Stats */}
        {systemStats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <Users className="w-5 h-5 text-blue-600" />
                <span className="text-sm font-medium text-gray-700">Total Users</span>
              </div>
              <p className="text-2xl font-bold text-gray-900">{systemStats.total_users || 0}</p>
            </div>
            <div className="bg-green-50 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <Activity className="w-5 h-5 text-green-600" />
                <span className="text-sm font-medium text-gray-700">Total Interactions</span>
              </div>
              <p className="text-2xl font-bold text-gray-900">{systemStats.total_interactions || 0}</p>
            </div>
            <div className="bg-purple-50 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <Target className="w-5 h-5 text-purple-600" />
                <span className="text-sm font-medium text-gray-700">Avg Mastery</span>
              </div>
              <p className="text-2xl font-bold text-gray-900">
                {((systemStats.avg_mastery || 0) * 100).toFixed(1)}%
              </p>
            </div>
            <div className="bg-orange-50 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="w-5 h-5 text-orange-600" />
                <span className="text-sm font-medium text-gray-700">Learning Velocity</span>
              </div>
              <p className="text-2xl font-bold text-gray-900">
                {(systemStats.learning_velocity || 0).toFixed(3)}
              </p>
            </div>
          </div>
        )}

        {/* User Selector */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">User Analysis</h2>
          <div className="flex gap-4">
            <input
              type="text"
              value={selectedUserId}
              onChange={(e) => setSelectedUserId(e.target.value)}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter user ID for detailed analysis (e.g., user_001)"
            />
          </div>
        </div>

        {/* Concept Performance */}
        {Array.isArray(conceptPerformance) && conceptPerformance.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <BarChart3 className="w-5 h-5" />
              Concept Performance
            </h2>
            <div className="space-y-3">
              {conceptPerformance.map((concept: any, index: number) => (
                <div key={index}>
                  <div className="flex justify-between mb-1">
                    <span className="text-sm font-medium text-gray-700">{concept.concept}</span>
                    <span className="text-sm text-gray-600">
                      {((concept.avg_mastery || 0) * 100).toFixed(1)}% ({concept.total_interactions || 0} interactions)
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="h-2 rounded-full bg-blue-600"
                      style={{ width: `${(concept.avg_mastery || 0) * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* User Insights */}
        {userInsights && selectedUserId && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">User Insights</h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-blue-50 rounded-lg p-4">
                <p className="text-sm text-gray-600">Learning Velocity</p>
                <p className="text-2xl font-bold text-gray-900">{(userInsights.learning_velocity || 0).toFixed(3)}</p>
              </div>
              <div className="bg-green-50 rounded-lg p-4">
                <p className="text-sm text-gray-600">Concept Diversity</p>
                <p className="text-2xl font-bold text-gray-900">{(userInsights.concept_diversity || 0).toFixed(2)}</p>
              </div>
              <div className="bg-purple-50 rounded-lg p-4">
                <p className="text-sm text-gray-600">Engagement Score</p>
                <p className="text-2xl font-bold text-gray-900">{(userInsights.engagement_score || 0).toFixed(2)}</p>
              </div>
              <div className="bg-orange-50 rounded-lg p-4">
                <p className="text-sm text-gray-600">Predicted Performance</p>
                <p className="text-2xl font-bold text-gray-900">
                  {((userInsights.predicted_performance || 0) * 100).toFixed(1)}%
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Learning Curves */}
        {Array.isArray(learningCurves) && learningCurves.length > 0 && selectedUserId && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Learning Curves</h2>
            <div className="h-64 bg-gray-50 rounded-lg p-4 flex items-end gap-1">
              {learningCurves.map((curve: any, index: number) => (
                <div
                  key={index}
                  className="flex-1 bg-green-500 rounded-t"
                  style={{ height: `${(curve.mastery || 0) * 100}%` }}
                  title={`${curve.concept}: ${((curve.mastery || 0) * 100).toFixed(1)}%`}
                />
              ))}
            </div>
          </div>
        )}

        {/* HCIE substrate evidence: live ensemble + JT attribution + ADC verdicts */}
        <GovernanceTelemetryPanel userId={selectedUserId} />

        {/* Existing Components */}
        <EngagementDashboard />
        <DataExport />

        <NextSteps />
      </main>
    </div>
  )
}
