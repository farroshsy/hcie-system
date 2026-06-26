import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig, AxiosResponse } from 'axios'
import { getBackendUrl } from '@/lib/api/backend-url'

const API_URL = getBackendUrl()

class APIClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: API_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      withCredentials: true, // Include httpOnly cookies
    })

    this.setupInterceptors()
  }

  private setupInterceptors() {
    // Response interceptor - handle token refresh
    this.client.interceptors.response.use(
      (response: AxiosResponse) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true
          try {
            // Try to refresh token using V3 auth API
            const response = await this.client.post('/v3/auth/refresh', {
              refresh_token: this.getRefreshToken(),
            })
            
            // Store new access token in localStorage for API calls
            this.setToken(response.data.access_token)
            
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${response.data.access_token}`
            }
            return this.client(originalRequest)
          } catch (refreshError) {
            // Refresh failed, clear tokens and redirect to login
            this.clearTokens()
            if (typeof window !== 'undefined') {
              window.location.href = '/login'
            }
          }
        }

        return Promise.reject(error)
      }
    )
  }

  private getToken(): string | null {
    if (typeof window === 'undefined') return null
    return localStorage.getItem('access_token')
  }

  private setToken(token: string): void {
    if (typeof window === 'undefined') return
    localStorage.setItem('access_token', token)
  }

  private getRefreshToken(): string | null {
    if (typeof window === 'undefined') return null
    return localStorage.getItem('refresh_token')
  }

  private setRefreshToken(token: string): void {
    if (typeof window === 'undefined') return
    localStorage.setItem('refresh_token', token)
  }

  private clearTokens(): void {
    if (typeof window === 'undefined') return
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  // ============================================================================
  // V3 Auth API
  // ============================================================================

  async register(email: string, password: string, name?: string, role?: string) {
    const response = await this.client.post('/v3/auth/register', {
      email,
      password,
      name,
      role: role || 'student',
    })
    this.setToken(response.data.access_token)
    this.setRefreshToken(response.data.refresh_token)
    return response.data
  }

  async login(email: string, password: string) {
    const response = await this.client.post('/v3/auth/login', {
      email,
      password,
    })
    this.setToken(response.data.access_token)
    this.setRefreshToken(response.data.refresh_token)
    return response.data
  }

  async logout() {
    try {
      await this.client.post('/v3/auth/logout')
    } finally {
      this.clearTokens()
    }
  }

  async getProfile() {
    const response = await this.client.get('/v3/auth/profile')
    return response.data
  }

  async refreshToken(refreshToken: string) {
    const response = await this.client.post('/v3/auth/refresh', {
      refresh_token: refreshToken,
    })
    return response.data
  }

  // ============================================================================
  // V3 Learner API (ITS)
  // ============================================================================

  async recommend(conceptFilter?: string[], deterministic?: boolean, seed?: number, policy?: string) {
    const response = await this.client.post('/v3/learner/recommend', {
      concept_filter: conceptFilter,
      deterministic,
      seed,
      policy,
    })
    return response.data
  }

  async submitAttempt(taskId: string, conceptId: string, answer: any, correct?: boolean, responseTime?: number, eventId?: string, deterministic?: boolean, seed?: number) {
    const response = await this.client.post('/v3/learner/attempt', {
      task_id: taskId,
      concept_id: conceptId,
      answer,
      correct,
      response_time: responseTime,
      event_id: eventId,
      deterministic,
      seed,
    })
    return response.data
  }

  async getProgress() {
    const response = await this.client.get('/v3/learner/progress')
    return response.data
  }

  async getSession() {
    const response = await this.client.get('/v3/learner/session')
    return response.data
  }

  // ============================================================================
  // V3 Frontend Dashboard API
  // ============================================================================

  async getSystemOverview() {
    const response = await this.client.get('/v3/frontend/dashboard/overview')
    return response.data
  }

  async getUserDashboard(userId: string) {
    const response = await this.client.get(`/v3/frontend/dashboard/user/${userId}`)
    return response.data
  }

  async getSystemAnalytics() {
    const response = await this.client.get('/v3/frontend/dashboard/analytics')
    return response.data
  }

  // ============================================================================
  // Legacy V2 API Endpoints (for backward compatibility)
  // ============================================================================

  async getNextTask(userId: string) {
    const response = await this.client.get(`/api/learning/next-task?user_id=${userId}`)
    return response.data
  }

  async submitTask(userId: string, taskId: string, answer: string, responseTime?: number) {
    const response = await this.client.post('/api/learning/submit', {
      user_id: userId,
      task_id: taskId,
      answer,
      response_time: responseTime,
    })
    return response.data
  }

  // V3 Experience endpoints (legacy, will be replaced by learner API)
  async getLearningState(userId: string) {
    const response = await this.client.get(`/v3/experience/user/${userId}/learning-state`)
    return response.data
  }

  async getRecommendation(userId: string, availableConcepts: string[], currentConcept?: string) {
    const response = await this.client.post(`/v3/experience/user/${userId}/recommendation`, {
      available_concepts: availableConcepts,
      current_concept: currentConcept,
    })
    return response.data
  }

  async getSessionContinuity(userId: string) {
    const response = await this.client.get(`/v3/experience/user/${userId}/session-continuity`)
    return response.data
  }

  // ============================================================================
  // Experiment endpoints (admin)
  // ============================================================================

  async createExperiment(config: any) {
    const response = await this.client.post('/experiments/', config)
    return response.data
  }

  async listExperiments() {
    const response = await this.client.get('/experiments/')
    return response.data
  }

  async getExperiments() {
    const response = await this.client.get('/experiments')
    return response.data
  }

  async getExperiment(experimentId: string) {
    const response = await this.client.get(`/experiments/${experimentId}`)
    return response.data
  }

  async startExperiment(experimentId: string) {
    const response = await this.client.post(`/experiments/${experimentId}/start`)
    return response.data
  }

  async stopExperiment(experimentId: string) {
    const response = await this.client.post(`/experiments/${experimentId}/stop`)
    return response.data
  }

  async deleteExperiment(experimentId: string) {
    const response = await this.client.delete(`/experiments/${experimentId}`)
    return response.data
  }

  // ============================================================================
  // Analytics API
  // ============================================================================

  async getConceptPerformance() {
    const response = await this.client.get('/analytics/api/v1/analytics/concept-performance')
    return response.data
  }

  async getUserInsights(userId: string) {
    const response = await this.client.get(`/analytics/api/v1/analytics/insights/${userId}`)
    return response.data
  }

  async getUserInteractions(userId: string) {
    const response = await this.client.get(`/analytics/api/v1/analytics/interactions/${userId}`)
    return response.data
  }

  async getLearningCurves(userId: string) {
    const response = await this.client.get(`/analytics/api/v1/analytics/learning-curves/${userId}`)
    return response.data
  }

  async getResearchData() {
    const response = await this.client.get('/analytics/api/v1/analytics/research-data')
    return response.data
  }

  async getUserSignals(userId: string) {
    const response = await this.client.get(`/analytics/api/v1/analytics/signals/${userId}`)
    return response.data
  }

  async getSystemStats() {
    const response = await this.client.get('/analytics/api/v1/analytics/stats')
    return response.data
  }

  async getUserTrajectory(userId: string) {
    const response = await this.client.get(`/analytics/api/v1/analytics/trajectory/${userId}`)
    return response.data
  }

  async getLearningCurve(userId: string) {
    const response = await this.client.get(`/analytics/learning-curve/${userId}`)
    return response.data
  }

  // ============================================================================
  // Research API
  // ============================================================================

  async exportResearchData(format: 'json' | 'csv') {
    const response = await this.client.get(`/api/research/export/${format}`)
    return response.data
  }

  async getColdStartResults(scenario?: string) {
    const url = scenario 
      ? `/api/research/cold-start-results/${scenario}`
      : '/api/research/cold-start-results'
    const response = await this.client.get(url)
    return response.data
  }

  async getResearchMetrics() {
    const response = await this.client.get('/api/research/metrics')
    return response.data
  }

  // ============================================================================
  // V3 Research / Learner Telemetry API
  // (See FRONTEND_API_COVERAGE_AUDIT.md Group 1 — paper-evidence surface)
  // ============================================================================

  async getResearchGovernanceState(userId: string) {
    const response = await this.client.get(`/v3/research/learner/governance/state`, {
      params: { user_id: userId },
    })
    return response.data
  }

  async getResearchGovernanceTrajectory(userId: string, limit?: number) {
    const response = await this.client.get(`/v3/research/learner/governance/trajectory`, {
      params: { user_id: userId, limit },
    })
    return response.data
  }

  async getResearchEnsembleWeights(userId: string) {
    const response = await this.client.get(`/v3/research/learner/governance/ensemble-weights`, {
      params: { user_id: userId },
    })
    return response.data
  }

  async getResearchAdaptationTrajectory(userId: string, limit?: number) {
    const response = await this.client.get(`/v3/research/learner/adaptation/trajectory`, {
      params: { user_id: userId, limit },
    })
    return response.data
  }

  async getResearchJtAttribution(userId: string) {
    const response = await this.client.get(`/v3/research/learner/jt-attribution`, {
      params: { user_id: userId },
    })
    return response.data
  }

  async getResearchDiscriminability(userId: string) {
    const response = await this.client.get(`/v3/research/learner/discriminability`, {
      params: { user_id: userId },
    })
    return response.data
  }

  async getResearchBanditState(userId: string) {
    const response = await this.client.get(`/v3/research/learner/bandit-state`, {
      params: { user_id: userId },
    })
    return response.data
  }

  async getResearchRanking(userId: string) {
    const response = await this.client.get(`/v3/research/learner/ranking`, {
      params: { user_id: userId },
    })
    return response.data
  }

  async getResearchTrajectoryCsv(userId: string, runId?: string) {
    const response = await this.client.get(`/v3/research/learner/trajectory.csv`, {
      params: { user_id: userId, run_id: runId },
      responseType: 'blob',
    })
    return response.data
  }

  async getResearchAttributionTelemetry(userId: string) {
    const response = await this.client.get(`/v3/research/attribution/telemetry/${userId}`)
    return response.data
  }

  async getResearchPolicyTelemetry(userId: string) {
    const response = await this.client.get(`/v3/research/policy/telemetry/${userId}`)
    return response.data
  }

  async getResearchTransferTelemetry(userId: string) {
    const response = await this.client.get(`/v3/research/transfer/telemetry/${userId}`)
    return response.data
  }

  // ============================================================================
  // V3 Runtime Introspection API (Group 2)
  // ============================================================================

  async getRuntimeGovernanceState() {
    const response = await this.client.get('/v3/runtime/governance/state')
    return response.data
  }

  async getRuntimeGovernanceTrajectory(limit?: number) {
    const response = await this.client.get('/v3/runtime/governance/trajectory', {
      params: { limit },
    })
    return response.data
  }

  async getRuntimeTrajectoryState(userId: string) {
    const response = await this.client.get(`/v3/runtime/trajectory/state/${userId}`)
    return response.data
  }

  async getRuntimeObjectiveState() {
    const response = await this.client.get('/v3/runtime/objective/state')
    return response.data
  }

  async getRuntimeLifecycleHealth() {
    const response = await this.client.get('/v3/runtime/lifecycle/health')
    return response.data
  }

  async getRuntimeLifecycleMetrics() {
    const response = await this.client.get('/v3/runtime/lifecycle/metrics')
    return response.data
  }

  async getRuntimeLifecycleState(userId: string) {
    const response = await this.client.get(`/v3/runtime/lifecycle/state/${userId}`)
    return response.data
  }

  async getRuntimeEventsPropagation() {
    const response = await this.client.get('/v3/runtime/events/propagation')
    return response.data
  }

  async getRuntimeRecommendationState(userId: string) {
    const response = await this.client.get(`/v3/runtime/recommendation/state/${userId}`)
    return response.data
  }

  async postRuntimeRecommendation(payload: Record<string, unknown>) {
    const response = await this.client.post('/v3/runtime/recommendation/recommend', payload)
    return response.data
  }

  async getRuntimeAuthorityServices() {
    const response = await this.client.get('/v3/runtime/authority/services')
    return response.data
  }

  async getRuntimeAuthorityAll() {
    const response = await this.client.get('/v3/runtime/authority/all')
    return response.data
  }

  async getRuntimeAuthorityState(apiName: string) {
    const response = await this.client.get(`/v3/runtime/authority/state/${apiName}`)
    return response.data
  }

  // ============================================================================
  // V3 Runtime Replay + Mutations (Group 4)
  // ============================================================================

  async triggerRuntimeReplay(payload: Record<string, unknown>) {
    const response = await this.client.post('/v3/runtime/replay/trigger', payload)
    return response.data
  }

  async getRuntimeReplayStatus(replayId: string) {
    const response = await this.client.get(`/v3/runtime/replay/status/${replayId}`)
    return response.data
  }

  async postRuntimeMutation(payload: Record<string, unknown>) {
    const response = await this.client.post('/v3/runtime/mutations', payload)
    return response.data
  }

  async getRuntimeMutationStatus(mutationId: string) {
    const response = await this.client.get(`/v3/runtime/mutations/status/${mutationId}`)
    return response.data
  }

  // ============================================================================
  // V3 Admin Ops API (Group 3)
  // ============================================================================

  async getAdminHealthDetail() {
    const response = await this.client.get('/v3/admin/health/detail')
    return response.data
  }

  async getAdminOutboxStatus() {
    const response = await this.client.get('/v3/admin/outbox/status')
    return response.data
  }

  async getAdminKafkaTopics() {
    const response = await this.client.get('/v3/admin/kafka/topics')
    return response.data
  }

  async getAdminProjectionStatus() {
    const response = await this.client.get('/v3/admin/projection/status')
    return response.data
  }

  async postAdminProjectionRebuild(payload?: Record<string, unknown>) {
    const response = await this.client.post('/v3/admin/projection/rebuild', payload ?? {})
    return response.data
  }

  async getAdminRuntimeServices() {
    const response = await this.client.get('/v3/admin/runtime/services')
    return response.data
  }

  async getAdminObservabilityLinks() {
    const response = await this.client.get('/v3/admin/observability/links')
    return response.data
  }

  async postAdminGovernanceResetNormalization(payload?: Record<string, unknown>) {
    const response = await this.client.post('/v3/admin/governance/reset-normalization', payload ?? {})
    return response.data
  }

  async getAdminContainerServices() {
    const response = await this.client.get('/v3/admin/container/services')
    return response.data
  }

  async getAdminRuntimeCapabilities() {
    const response = await this.client.get('/v3/admin/runtime/capabilities')
    return response.data
  }

  // ============================================================================
  // V3 Service Router (Group ingest/replay/projection)
  // ============================================================================

  async ingestEvents(payload: Record<string, unknown>) {
    const response = await this.client.post('/v3/events/ingest', payload)
    return response.data
  }

  async batchReplay(payload: Record<string, unknown>) {
    const response = await this.client.post('/v3/replay/batch', payload)
    return response.data
  }

  async rebuildProjection(payload?: Record<string, unknown>) {
    const response = await this.client.post('/v3/projection/rebuild', payload ?? {})
    return response.data
  }

  // ============================================================================
  // V3 Experience extras (close gaps in Group experience)
  // ============================================================================

  async getExperienceProgress(userId: string) {
    const response = await this.client.get(`/v3/experience/user/${userId}/progress`)
    return response.data
  }

  async submitAdaptiveFeedback(userId: string, payload: Record<string, unknown>) {
    const response = await this.client.post(
      `/v3/experience/user/${userId}/adaptive-feedback`,
      payload,
    )
    return response.data
  }

  // ============================================================================
  // Health check
  // ============================================================================

  async healthCheck() {
    const response = await this.client.get('/health')
    return response.data
  }

  // ============================================================================
  // Generic request methods
  // ============================================================================

  async get(url: string, config?: any) {
    return this.client.get(url, config)
  }

  async post(url: string, data?: any, config?: any) {
    return this.client.post(url, data, config)
  }

  async put(url: string, data?: any, config?: any) {
    return this.client.put(url, data, config)
  }

  async patch(url: string, data?: any, config?: any) {
    return this.client.patch(url, data, config)
  }

  async delete(url: string, config?: any) {
    return this.client.delete(url, config)
  }
}

export const apiClient = new APIClient()
