/**
 * Admin Home Screen
 * 
 * Main admin dashboard with system overview, quick stats, and navigation to admin features.
 */

'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts'
import { useServices } from '@/contexts'
import { useSystemStatus } from '@/hooks/useWebSocket'
import { Activity, Users, Beaker, BarChart3, RefreshCw, Snowflake } from 'lucide-react'

interface SystemStats {
  totalUsers: number
  activeUsers: number
  totalExperiments: number
  activeExperiments: number
  averageMastery: number
  learningEventsToday: number
}

export default function AdminHomeScreen() {
  const { user } = useAuth()
  const services = useServices()
  const router = useRouter()
  const [stats, setStats] = useState<SystemStats | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Real-time system status via WebSocket
  const { isConnected, systemHealth, activeUsers, processingRate } = useSystemStatus()

  useEffect(() => {
    if (user && user.role === 'admin') {
      loadSystemStats()
    }
  }, [user])

  const loadSystemStats = async () => {
    try {
      setIsLoading(true)
      // In production, this would call the dashboard service
      const systemStats = await services.dashboard.getSystemOverview()
      setStats({
        totalUsers: systemStats.total_users || 0,
        activeUsers: systemStats.active_users || 0,
        totalExperiments: systemStats.total_experiments || 0,
        activeExperiments: systemStats.running_experiments || 0,
        averageMastery: 0.75, // Placeholder - would come from analytics
        learningEventsToday: 0, // Placeholder - would come from analytics
      })
    } catch (error) {
      console.error('Failed to load system stats:', error)
    } finally {
      setIsLoading(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-gray-600">Loading admin dashboard...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
          <p className="text-gray-600 mt-1">System overview and management</p>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Real-time System Status */}
        <div className={`rounded-lg shadow p-6 mb-8 ${isConnected ? 'bg-green-50 border-2 border-green-200' : 'bg-gray-50 border-2 border-gray-200'}`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className={`text-3xl ${isConnected ? 'text-green-600' : 'text-gray-400'}`}>
                <Activity className="w-8 h-8" />
              </div>
              <div>
                <h3 className={`text-lg font-bold ${isConnected ? 'text-green-800' : 'text-gray-700'}`}>
                  System {isConnected ? 'Online' : 'Offline'}
                </h3>
                <p className={isConnected ? 'text-green-700' : 'text-gray-500'}>
                  {activeUsers} active users • {processingRate.toFixed(1)} req/s
                </p>
              </div>
            </div>
            <div className={`px-4 py-2 rounded-full text-sm font-medium ${
              systemHealth === 'healthy' ? 'bg-green-100 text-green-800' :
              systemHealth === 'degraded' ? 'bg-yellow-100 text-yellow-800' :
              'bg-red-100 text-red-800'
            }`}>
              {systemHealth || 'Unknown'}
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-700">Total Users</h3>
            <p className="text-4xl font-bold text-blue-600 mt-2">{stats?.totalUsers || 0}</p>
            <p className="text-sm text-gray-500 mt-1">Registered learners</p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-700">Active Users</h3>
            <p className="text-4xl font-bold text-green-600 mt-2">{stats?.activeUsers || 0}</p>
            <p className="text-sm text-gray-500 mt-1">Currently learning</p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-700">Average Mastery</h3>
            <p className="text-4xl font-bold text-purple-600 mt-2">
              {stats ? Math.round(stats.averageMastery * 100) : 0}%
            </p>
            <p className="text-sm text-gray-500 mt-1">Across all concepts</p>
          </div>
        </div>

        {/* Experiment Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-700">Total Experiments</h3>
            <p className="text-4xl font-bold text-orange-600 mt-2">{stats?.totalExperiments || 0}</p>
            <p className="text-sm text-gray-500 mt-1">All time</p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-700">Active Experiments</h3>
            <p className="text-4xl font-bold text-teal-600 mt-2">{stats?.activeExperiments || 0}</p>
            <p className="text-sm text-gray-500 mt-1">Currently running</p>
          </div>
        </div>

        {/* Learning Activity */}
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <h3 className="text-lg font-semibold text-gray-700 mb-4">Learning Activity Today</h3>
          <p className="text-4xl font-bold text-indigo-600">{stats?.learningEventsToday || 0}</p>
          <p className="text-sm text-gray-500 mt-1">Task submissions</p>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
          <button
            onClick={() => router.push('/dashboard/cohorts')}
            className="bg-blue-600 text-white px-6 py-4 rounded-lg font-semibold hover:bg-blue-700 transition text-left"
          >
            <div className="flex items-center gap-2 text-2xl mb-2">
              <Beaker />
            </div>
            <div>Experiments</div>
          </button>
          <button
            onClick={() => router.push('/replay')}
            className="bg-green-600 text-white px-6 py-4 rounded-lg font-semibold hover:bg-green-700 transition text-left"
          >
            <div className="flex items-center gap-2 text-2xl mb-2">
              <RefreshCw />
            </div>
            <div>Replay</div>
          </button>
          <button
            onClick={() => router.push('/cold-start')}
            className="bg-cyan-600 text-white px-6 py-4 rounded-lg font-semibold hover:bg-cyan-700 transition text-left"
          >
            <div className="flex items-center gap-2 text-2xl mb-2">
              <Snowflake />
            </div>
            <div>Cold Start</div>
          </button>
          <button
            onClick={() => router.push('/research')}
            className="bg-purple-600 text-white px-6 py-4 rounded-lg font-semibold hover:bg-purple-700 transition text-left"
          >
            <div className="flex items-center gap-2 text-2xl mb-2">
              <BarChart3 />
            </div>
            <div>Research</div>
          </button>
          <button
            onClick={() => router.push('/system-status')}
            className="bg-orange-600 text-white px-6 py-4 rounded-lg font-semibold hover:bg-orange-700 transition text-left"
          >
            <div className="flex items-center gap-2 text-2xl mb-2">
              <Activity />
            </div>
            <div>System Status</div>
          </button>
        </div>
      </main>
    </div>
  )
}
