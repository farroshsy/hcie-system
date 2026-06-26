/**
 * Admin Settings Screen
 * 
 * Admin interface for managing system settings, configuration, and feature flags.
 */

'use client'

import { useState } from 'react'
import { useConfig } from '@/contexts'

export default function AdminSettingsScreen() {
  const config = useConfig()
  const [settings, setSettings] = useState({
    maintenanceMode: false,
    newRegistrations: true,
    experimentalFeatures: config.features.experimentalFeatures,
    realTimeUpdates: config.features.realTimeUpdates,
    debugMode: config.features.debugMode,
  })

  const handleToggle = (key: keyof typeof settings) => {
    setSettings((prev) => ({ ...prev, [key]: !prev[key] }))
  }

  const handleSave = () => {
    console.log('Saving settings:', settings)
    // In production, this would save to backend
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-6 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">System Settings</h1>
            <p className="text-gray-600 mt-1">Configure system behavior and features</p>
          </div>
          <button onClick={handleSave} className="bg-blue-600 text-white px-6 py-2 rounded-lg font-semibold hover:bg-blue-700 transition">
            Save Changes
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* System Status */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">System Status</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-medium text-gray-700">Maintenance Mode</h3>
                <p className="text-sm text-gray-500">Disable user access for maintenance</p>
              </div>
              <button
                onClick={() => handleToggle('maintenanceMode')}
                className={`w-12 h-6 rounded-full transition ${
                  settings.maintenanceMode ? 'bg-red-600' : 'bg-gray-300'
                }`}
              >
                <div
                  className={`w-5 h-5 bg-white rounded-full transition transform ${
                    settings.maintenanceMode ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-medium text-gray-700">New Registrations</h3>
                <p className="text-sm text-gray-500">Allow new user registrations</p>
              </div>
              <button
                onClick={() => handleToggle('newRegistrations')}
                className={`w-12 h-6 rounded-full transition ${
                  settings.newRegistrations ? 'bg-green-600' : 'bg-gray-300'
                }`}
              >
                <div
                  className={`w-5 h-5 bg-white rounded-full transition transform ${
                    settings.newRegistrations ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          </div>
        </div>

        {/* Feature Flags */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Feature Flags</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-medium text-gray-700">Experimental Features</h3>
                <p className="text-sm text-gray-500">Enable experimental and beta features</p>
              </div>
              <button
                onClick={() => handleToggle('experimentalFeatures')}
                className={`w-12 h-6 rounded-full transition ${
                  settings.experimentalFeatures ? 'bg-blue-600' : 'bg-gray-300'
                }`}
              >
                <div
                  className={`w-5 h-5 bg-white rounded-full transition transform ${
                    settings.experimentalFeatures ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-medium text-gray-700">Real-time Updates</h3>
                <p className="text-sm text-gray-500">Enable WebSocket real-time updates</p>
              </div>
              <button
                onClick={() => handleToggle('realTimeUpdates')}
                className={`w-12 h-6 rounded-full transition ${
                  settings.realTimeUpdates ? 'bg-blue-600' : 'bg-gray-300'
                }`}
              >
                <div
                  className={`w-5 h-5 bg-white rounded-full transition transform ${
                    settings.realTimeUpdates ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-medium text-gray-700">Debug Mode</h3>
                <p className="text-sm text-gray-500">Enable debug logging and diagnostics</p>
              </div>
              <button
                onClick={() => handleToggle('debugMode')}
                className={`w-12 h-6 rounded-full transition ${
                  settings.debugMode ? 'bg-purple-600' : 'bg-gray-300'
                }`}
              >
                <div
                  className={`w-5 h-5 bg-white rounded-full transition transform ${
                    settings.debugMode ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          </div>
        </div>

        {/* API Configuration */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">API Configuration</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">API Base URL</label>
              <input
                type="text"
                defaultValue={config.api.baseUrl}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">WebSocket URL</label>
              <input
                type="text"
                defaultValue={config.websocket.url}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
        </div>

        {/* Cache Configuration */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Cache Configuration</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Cache Duration (seconds)</label>
              <input
                type="number"
                defaultValue={config.cache.defaultDuration / 1000}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
