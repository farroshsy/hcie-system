'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useT } from '@/contexts/language_context'

export default function BackendConnectionPage() {
  const t = useT()
  const [status, setStatus] = useState<'loading' | 'connected' | 'error'>('loading')
  const [apiUrl, setApiUrl] = useState('')
  const [error, setError] = useState('')
  const [testResult, setTestResult] = useState('')

  useEffect(() => {
    const configUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8011'
    setApiUrl(configUrl)
    
    testConnection()
  }, [])

  const testConnection = async () => {
    setStatus('loading')
    setTestResult('')
    setError('')

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8011'}/api/system/health`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (response.ok) {
        setStatus('connected')
        const data = await response.json()
        setTestResult(JSON.stringify(data, null, 2))
      } else {
        setStatus('error')
        setError(`HTTP ${response.status}: ${response.statusText}`)
      }
    } catch (err) {
      setStatus('error')
      setError(err instanceof Error ? err.message : 'Unknown error')
    }
  }

  const statusColor = {
    loading: 'text-yellow-500',
    connected: 'text-green-500',
    error: 'text-red-500',
  }[status]

  const statusText = {
    loading: 'Testing connection...',
    connected: 'Connected',
    error: 'Connection failed',
  }[status]

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold">{t('backendConnection.eyebrow')}</h1>
        <p className="text-gray-600">{t('backendConnection.title')}</p>
      </div>

      {/* Connection Status */}
      <Card>
        <CardHeader>
          <CardTitle>Connection Status</CardTitle>
          <CardDescription>Current backend API connectivity</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-500">API Endpoint</div>
              <div className="font-mono text-lg">{apiUrl}</div>
            </div>
            <div className={`text-2xl font-bold ${statusColor}`}>
              {statusText}
            </div>
          </div>

          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="text-sm font-medium text-red-800">Error Details</div>
              <div className="text-sm text-red-600 mt-1 font-mono">{error}</div>
            </div>
          )}

          <button
            onClick={testConnection}
            disabled={status === 'loading'}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {status === 'loading' ? 'Testing...' : 'Test Connection'}
          </button>
        </CardContent>
      </Card>

      {/* Configuration */}
      <Card>
        <CardHeader>
          <CardTitle>Configuration</CardTitle>
          <CardDescription>Environment variables and settings</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <div className="text-sm text-gray-500">NEXT_PUBLIC_API_URL</div>
            <div className="font-mono p-2 bg-gray-100 rounded">{process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}</div>
          </div>

          <div className="space-y-2">
            <div className="text-sm text-gray-500">NEXT_PUBLIC_WS_URL</div>
            <div className="font-mono p-2 bg-gray-100 rounded">{process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'}</div>
          </div>

          <div className="space-y-2">
            <div className="text-sm text-gray-500">Environment</div>
            <div className="font-mono p-2 bg-gray-100 rounded">{process.env.NODE_ENV || 'development'}</div>
          </div>
        </CardContent>
      </Card>

      {/* Test Result */}
      {testResult && (
        <Card>
          <CardHeader>
            <CardTitle>Health Check Response</CardTitle>
            <CardDescription>Raw response from backend health endpoint</CardDescription>
          </CardHeader>
          <CardContent>
            <pre className="p-4 bg-gray-900 text-green-400 rounded-lg overflow-auto text-sm">
              {testResult}
            </pre>
          </CardContent>
        </Card>
      )}

      {/* Troubleshooting */}
      <Card>
        <CardHeader>
          <CardTitle>Troubleshooting</CardTitle>
          <CardDescription>Common issues and solutions</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <div className="font-medium">Backend not running</div>
            <div className="text-sm text-gray-600">
              Start your backend services using docker-compose or the backend startup script
            </div>
          </div>

          <div className="space-y-2">
            <div className="font-medium">Wrong API URL</div>
            <div className="text-sm text-gray-600">
              Check NEXT_PUBLIC_API_URL in .env.local matches your backend endpoint
            </div>
          </div>

          <div className="space-y-2">
            <div className="font-medium">CORS issues</div>
            <div className="text-sm text-gray-600">
              Ensure backend allows requests from frontend origin
            </div>
          </div>

          <div className="space-y-2">
            <div className="font-medium">Firewall/Network</div>
            <div className="text-sm text-gray-600">
              Check firewall rules allow connections to backend port
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
