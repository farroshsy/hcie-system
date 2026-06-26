'use client'

export const dynamic = 'force-dynamic'

import { useSystemStatus } from '@/hooks/useWebSocket'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api-client'
import { Activity, Server, Database, Cpu, HardDrive, Network, Wifi, AlertCircle, CheckCircle } from 'lucide-react'
import { useT } from '@/contexts/language_context'

export default function SystemStatusPage() {
  const t = useT()
  const { isConnected, systemHealth, activeUsers, processingRate } = useSystemStatus()

  // System-wide stats via REST (real: 430k+ interactions, 4k+ users, avg_correct etc.)
  const { data: sysStats } = useQuery({
    queryKey: ['system-stats-rest'],
    queryFn: async () => {
      const token = typeof window !== 'undefined'
        ? (localStorage.getItem('hcie_auth_token') || localStorage.getItem('access_token') || '')
        : ''
      const r = await fetch('/v3/frontend/dashboard/system-stats',
        { headers: token ? { Authorization: `Bearer ${token}` } : {},
          signal: AbortSignal.timeout(8000) })
      if (!r.ok) return null
      return r.json()
    },
    refetchInterval: 30000,
  })

  // Get V3 health status
  const { data: healthStatus } = useQuery({
    queryKey: ['health'],
    queryFn: () => apiClient.healthCheck(),
    refetchInterval: 5000,
  })

  // Get detailed health
  const { data: detailedHealthData } = useQuery({
    queryKey: ['health-detailed'],
    queryFn: () => apiClient.get('/health/detailed'),
    refetchInterval: 10000,
  })

  const detailedHealth = detailedHealthData?.data

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'text-green-600 bg-green-50'
      case 'degraded':
        return 'text-yellow-600 bg-yellow-50'
      case 'unhealthy':
        return 'text-red-600 bg-red-50'
      default:
        return 'text-gray-600 bg-gray-50'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="w-5 h-5" />
      case 'degraded':
      case 'unhealthy':
        return <AlertCircle className="w-5 h-5" />
      default:
        return <Activity className="w-5 h-5" />
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{t('systemStatus.eyebrow')}</h1>
              <p className="text-gray-600 mt-1">{t('systemStatus.title')}</p>
            </div>
            <div className={`flex items-center gap-2 px-4 py-2 rounded-full ${getStatusColor(systemHealth)}`}>
              {getStatusIcon(systemHealth)}
              <span className="font-medium capitalize">{systemHealth}</span>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8 space-y-6">
        {/* WebSocket Connection Status */}
        <div className={`rounded-lg shadow p-6 ${isConnected ? 'bg-green-50 border-2 border-green-200' : 'bg-red-50 border-2 border-red-200'}`}>
          <div className="flex items-center gap-4">
            <div className={`text-4xl ${isConnected ? 'text-green-600' : 'text-red-600'}`}>
              {isConnected ? <Wifi className="w-10 h-10" /> : <AlertCircle className="w-10 h-10" />}
            </div>
            <div>
              <h2 className={`text-2xl font-bold ${isConnected ? 'text-green-800' : 'text-red-800'}`}>
                WebSocket {isConnected ? 'Connected' : 'Disconnected'}
              </h2>
              <p className={isConnected ? 'text-green-700' : 'text-red-700'}>
                Real-time updates {isConnected ? 'enabled' : 'unavailable'}
              </p>
            </div>
          </div>
        </div>

        {/* System Stats — REST (real data) */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center gap-2 mb-2">
              <Server className="w-5 h-5 text-blue-600" />
              <span className="text-sm font-medium text-gray-700">Total Interactions</span>
            </div>
            <p className="text-3xl font-bold text-gray-900">
              {sysStats?.interactions?.total?.toLocaleString() ?? '—'}
            </p>
            <p className="text-sm text-gray-500 mt-1">All-time · REST polled</p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center gap-2 mb-2">
              <Database className="w-5 h-5 text-green-600" />
              <span className="text-sm font-medium text-gray-700">Unique Learners</span>
            </div>
            <p className="text-3xl font-bold text-gray-900">
              {sysStats?.interactions?.unique_users?.toLocaleString() ?? '—'}
            </p>
            <p className="text-sm text-gray-500 mt-1">Distinct user IDs</p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center gap-2 mb-2">
              <Activity className="w-5 h-5 text-purple-600" />
              <span className="text-sm font-medium text-gray-700">Avg Correct Rate</span>
            </div>
            <p className="text-3xl font-bold text-gray-900">
              {sysStats?.interactions?.avg_correct != null
                ? `${(sysStats.interactions.avg_correct * 100).toFixed(1)}%`
                : '—'}
            </p>
            <p className="text-sm text-gray-500 mt-1">Across all learners</p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center gap-2 mb-2">
              <Database className="w-5 h-5 text-orange-600" />
              <span className="text-sm font-medium text-gray-700">Health Status</span>
            </div>
            <p className="text-3xl font-bold text-gray-900 capitalize">{healthStatus?.status || 'Unknown'}</p>
            <p className="text-sm text-gray-500 mt-1">V3 Health API</p>
          </div>
        </div>

        {/* WS metrics — honest label */}
        {!isConnected && (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-sm text-gray-500">
            <strong>Active Users</strong> and <strong>Processing Rate</strong> require a live WebSocket connection
            (not wired end-to-end). Real-time interaction count is above.
          </div>
        )}

        {/* Detailed Health */}
        {detailedHealth && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Detailed Health</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {detailedHealth.services && Object.entries(detailedHealth.services).map(([service, data]: [string, any]) => (
                <div key={service} className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-medium text-gray-700 capitalize">{service}</h3>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(data.status)}`}>
                      {data.status}
                    </span>
                  </div>
                  <p className="text-sm text-gray-500">Latency: {data.latency}ms</p>
                  {data.uptime && <p className="text-sm text-gray-500">Uptime: {data.uptime}</p>}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* System Resources */}
        {detailedHealth?.resources && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center gap-2 mb-4">
                <Cpu className="w-5 h-5 text-blue-600" />
                <h2 className="text-xl font-bold text-gray-900">CPU Usage</h2>
              </div>
              <div className="flex items-center justify-between mb-2">
                <div className="w-full bg-gray-200 rounded-full h-4 mr-4">
                  <div
                    className="h-4 rounded-full bg-blue-600 transition-all"
                    style={{ width: `${detailedHealth.resources.cpu_usage || 0}%` }}
                  />
                </div>
                <span className="text-lg font-semibold text-gray-900">{detailedHealth.resources.cpu_usage || 0}%</span>
              </div>
              <p className="text-sm text-gray-500">{detailedHealth.resources.cpu_cores || 0} cores</p>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center gap-2 mb-4">
                <Database className="w-5 h-5 text-green-600" />
                <h2 className="text-xl font-bold text-gray-900">Memory Usage</h2>
              </div>
              <div className="flex items-center justify-between mb-2">
                <div className="w-full bg-gray-200 rounded-full h-4 mr-4">
                  <div
                    className="h-4 rounded-full bg-green-600 transition-all"
                    style={{ width: `${detailedHealth.resources.memory_usage || 0}%` }}
                  />
                </div>
                <span className="text-lg font-semibold text-gray-900">{detailedHealth.resources.memory_usage || 0}%</span>
              </div>
              <p className="text-sm text-gray-500">
                {detailedHealth.resources.memory_used?.toFixed(1) || 0}GB / {detailedHealth.resources.memory_total || 0}GB
              </p>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center gap-2 mb-4">
                <HardDrive className="w-5 h-5 text-purple-600" />
                <h2 className="text-xl font-bold text-gray-900">Disk Usage</h2>
              </div>
              <div className="flex items-center justify-between mb-2">
                <div className="w-full bg-gray-200 rounded-full h-4 mr-4">
                  <div
                    className="h-4 rounded-full bg-purple-600 transition-all"
                    style={{ width: `${detailedHealth.resources.disk_usage || 0}%` }}
                  />
                </div>
                <span className="text-lg font-semibold text-gray-900">{detailedHealth.resources.disk_usage || 0}%</span>
              </div>
              <p className="text-sm text-gray-500">
                {detailedHealth.resources.disk_used || 0}GB / {detailedHealth.resources.disk_total || 0}GB
              </p>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center gap-2 mb-4">
                <Network className="w-5 h-5 text-orange-600" />
                <h2 className="text-xl font-bold text-gray-900">Network</h2>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-500">Incoming</span>
                  <span className="text-sm font-medium text-gray-900">
                    {((detailedHealth.resources.network_incoming || 0) / (1024 * 1024)).toFixed(1)} MB/s
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-500">Outgoing</span>
                  <span className="text-sm font-medium text-gray-900">
                    {((detailedHealth.resources.network_outgoing || 0) / (1024 * 1024)).toFixed(1)} MB/s
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
