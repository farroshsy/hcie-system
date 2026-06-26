/**
 * Experiments Management Screen
 * 
 * Admin interface for managing experiments, viewing experiment status, and configuring experiment parameters.
 */

'use client'

import { useEffect, useState } from 'react'
import { useServices } from '@/contexts'

interface Experiment {
  id: string
  name: string
  description: string
  status: 'running' | 'completed' | 'paused' | 'scheduled'
  startDate: string
  endDate?: string
  participants: number
  conditions: string[]
}

export default function ExperimentsScreen() {
  const services = useServices()
  const [experiments, setExperiments] = useState<Experiment[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    loadExperiments()
  }, [])

  const loadExperiments = async () => {
    try {
      setIsLoading(true)
      // In production, this would call the experiment service
      const exps: Experiment[] = [
        {
          id: 'exp_001',
          name: 'HCIE vs Random Policy',
          description: 'Compare HCIE adaptive policy against random baseline',
          status: 'running',
          startDate: '2026-05-01',
          participants: 150,
          conditions: ['HCIE', 'Random'],
        },
        {
          id: 'exp_002',
          name: 'DAG Constraint Impact',
          description: 'Evaluate impact of DAG constraints on learning outcomes',
          status: 'running',
          startDate: '2026-05-05',
          participants: 200,
          conditions: ['With DAG', 'Without DAG'],
        },
        {
          id: 'exp_003',
          name: 'Epsilon-Greedy Sweep',
          description: 'Sweep epsilon values to find optimal exploration rate',
          status: 'completed',
          startDate: '2026-04-15',
          endDate: '2026-04-30',
          participants: 300,
          conditions: ['ε=0.1', 'ε=0.2', 'ε=0.3', 'ε=0.4'],
        },
      ]
      setExperiments(exps)
    } catch (error) {
      console.error('Failed to load experiments:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const getStatusColor = (status: Experiment['status']) => {
    switch (status) {
      case 'running':
        return 'bg-green-100 text-green-800'
      case 'completed':
        return 'bg-blue-100 text-blue-800'
      case 'paused':
        return 'bg-yellow-100 text-yellow-800'
      case 'scheduled':
        return 'bg-gray-100 text-gray-800'
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-gray-600">Loading experiments...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-6 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Experiments</h1>
            <p className="text-gray-600 mt-1">Manage and monitor experiments</p>
          </div>
          <button className="bg-blue-600 text-white px-6 py-2 rounded-lg font-semibold hover:bg-blue-700 transition">
            Create Experiment
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Experiments List */}
        <div className="space-y-6">
          {experiments.map((exp) => (
            <div key={exp.id} className="bg-white rounded-lg shadow p-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-xl font-bold text-gray-900">{exp.name}</h3>
                  <p className="text-gray-600 mt-1">{exp.description}</p>
                </div>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(exp.status)}`}>
                  {exp.status}
                </span>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <div>
                  <p className="text-sm text-gray-500">Participants</p>
                  <p className="text-lg font-semibold text-gray-900">{exp.participants}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Start Date</p>
                  <p className="text-lg font-semibold text-gray-900">{exp.startDate}</p>
                </div>
                {exp.endDate && (
                  <div>
                    <p className="text-sm text-gray-500">End Date</p>
                    <p className="text-lg font-semibold text-gray-900">{exp.endDate}</p>
                  </div>
                )}
                <div>
                  <p className="text-sm text-gray-500">Conditions</p>
                  <p className="text-lg font-semibold text-gray-900">{exp.conditions.length}</p>
                </div>
              </div>

              <div className="flex gap-2">
                <button className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition">
                  View Details
                </button>
                {exp.status === 'running' && (
                  <button className="bg-yellow-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-yellow-700 transition">
                    Pause
                  </button>
                )}
                {exp.status === 'paused' && (
                  <button className="bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-green-700 transition">
                    Resume
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  )
}
