/**
 * Analytics Hooks for Advanced Dashboard
 * 
 * Provides hooks for:
 * - Concept performance metrics
 * - User insights and learning curves
 * - Research data export
 * - System statistics
 */

import { useQuery, useMutation } from '@tanstack/react-query'
import { apiClient } from '@/lib/api-client'

// Analytics Types
export interface ConceptPerformance {
  concept: string
  total_interactions: number
  avg_mastery: number
  improvement_rate: number
  difficulty_distribution: Record<string, number>
}

export interface UserInsights {
  user_id: string
  learning_velocity: number
  concept_diversity: number
  engagement_score: number
  mastery_trajectory: number[]
  predicted_performance: number
}

export interface LearningCurve {
  concept: string
  timestamp: string
  mastery: number
  interactions: number
}

export interface InteractionHistory {
  event_id: string
  concept: string
  timestamp: string
  correct: boolean
  response_time: number
  mastery_before: number
  mastery_after: number
}

export interface ResearchData {
  user_id: string
  concept: string
  interactions: InteractionHistory[]
  learning_curve: LearningCurve[]
  signals: Record<string, number>
}

export interface SystemStats {
  total_users: number
  total_interactions: number
  avg_mastery: number
  learning_velocity: number
  concept_count: number
}

export interface TrajectoryData {
  user_id: string
  concept: string
  trajectory: number[]
  policy_decisions: string[]
  governance_weights: Record<string, number>
}

export interface SignalData {
  user_id: string
  signal_type: string
  value: number
  timestamp: string
  metadata: Record<string, any>
}

// Analytics Hooks

export function useConceptPerformance() {
  return useQuery({
    queryKey: ['analytics', 'concept-performance'],
    queryFn: () => apiClient.get('/analytics/api/v1/analytics/concept-performance'),
  })
}

export function useUserInsights(userId: string) {
  return useQuery({
    queryKey: ['analytics', 'insights', userId],
    queryFn: () => apiClient.get(`/analytics/api/v1/analytics/insights/${userId}`),
    enabled: !!userId,
  })
}

export function useUserInteractions(userId: string) {
  return useQuery({
    queryKey: ['analytics', 'interactions', userId],
    queryFn: () => apiClient.get(`/analytics/api/v1/analytics/interactions/${userId}`),
    enabled: !!userId,
  })
}

export function useLearningCurves(userId: string) {
  return useQuery({
    queryKey: ['analytics', 'learning-curves', userId],
    queryFn: () => apiClient.get(`/analytics/api/v1/analytics/learning-curves/${userId}`),
    enabled: !!userId,
  })
}

export function useResearchData() {
  return useQuery({
    queryKey: ['analytics', 'research-data'],
    queryFn: () => apiClient.get('/analytics/api/v1/analytics/research-data'),
  })
}

export function useUserSignals(userId: string) {
  return useQuery({
    queryKey: ['analytics', 'signals', userId],
    queryFn: () => apiClient.get(`/analytics/api/v1/analytics/signals/${userId}`),
    enabled: !!userId,
  })
}

export function useSystemStats() {
  return useQuery({
    queryKey: ['analytics', 'stats'],
    queryFn: () => apiClient.get('/analytics/api/v1/analytics/stats'),
  })
}

export function useUserTrajectory(userId: string) {
  return useQuery({
    queryKey: ['analytics', 'trajectory', userId],
    queryFn: () => apiClient.get(`/analytics/api/v1/analytics/trajectory/${userId}`),
    enabled: !!userId,
  })
}

export function useLearningCurve(userId: string) {
  return useQuery({
    queryKey: ['analytics', 'learning-curve', userId],
    queryFn: () => apiClient.get(`/analytics/learning-curve/${userId}`),
    enabled: !!userId,
  })
}

// Research Data Export Hook
export function useExportResearchData() {
  return useMutation({
    mutationFn: async (format: 'json' | 'csv') => {
      const response = await apiClient.get(`/api/research/export/${format}`)
      return response
    },
  })
}

// Cold Start Results Hook
export function useColdStartResults(scenario?: string) {
  return useQuery({
    queryKey: ['research', 'cold-start', scenario],
    queryFn: () => {
      const url = scenario 
        ? `/api/research/cold-start-results/${scenario}`
        : '/api/research/cold-start-results'
      return apiClient.get(url)
    },
  })
}

// Research Metrics Hook
export function useResearchMetrics() {
  return useQuery({
    queryKey: ['research', 'metrics'],
    queryFn: () => apiClient.get('/api/research/metrics'),
  })
}
