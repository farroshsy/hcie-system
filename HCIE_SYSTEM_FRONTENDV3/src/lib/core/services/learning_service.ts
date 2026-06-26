/**
 * Learning Service Implementation
 * 
 * Implements the ILearningService protocol for learning-related operations.
 * This service handles learning state, recommendations, task submissions, and progress tracking.
 */

import type {
  ILearningService,
  LearningServiceConfig,
  LearningState,
  Recommendation,
  Task,
  TaskSubmission,
  SubmissionResult,
  Progress,
} from '../interfaces'
import { getV3ApiUrl } from '@/lib/api/backend-url'

/**
 * Learning Service Implementation
 */
export class LearningService implements ILearningService {
  private apiUrl: string
  private authToken: string
  private cacheDuration: number
  private debug: boolean
  private cache: Map<string, { data: unknown; timestamp: number }>

  constructor(config: LearningServiceConfig) {
    this.apiUrl = config.apiUrl
    this.authToken = config.authToken
    this.cacheDuration = config.cacheDuration || 30 * 1000 // 30 seconds — keeps dashboard fresh after attempts
    this.debug = config.debug || false
    this.cache = new Map()
  }

  private getToken(): string {
    if (this.authToken) return this.authToken
    if (typeof window === 'undefined') return ''
    return localStorage.getItem('hcie_auth_token') || localStorage.getItem('access_token') || ''
  }

  /**
   * Fetch the current learning state for a user.
   * Calls GET /v3/learner/progress (JWT-identified) and maps to LearningState shape.
   */
  async getLearningState(userId: string): Promise<LearningState> {
    const cacheKey = `learning-state-${userId}`
    const cached = this.getFromCache(cacheKey)

    if (cached) {
      this.log('Cache hit for learning state:', userId)
      return cached as LearningState
    }

    this.log('Fetching learning state for user:', userId)

    try {
      const base = getV3ApiUrl()
      const token = this.getToken()
      const response = await fetch(`${base}/learner/progress`, {
        headers: {
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`Failed to fetch learning state: ${response.statusText}`)
      }

      const raw = await response.json()
      // Backend returns {user_id, concepts: {concept_id: mastery}, semantic_version}
      const rawConcepts: Record<string, number> = raw.concepts ?? {}
      const mastery: Record<string, number> = Object.fromEntries(
        Object.entries(rawConcepts).filter(([k]) => k !== 'unknown' && k !== '')
      )

      // Fetch attempt count from session-trace endpoint for accurate tasks_completed
      let tasksCompleted = Object.values(mastery).filter(v => v > 0).length
      try {
        const traceBase = getV3ApiUrl()
        const traceRes = await fetch(`${traceBase}/frontend/dashboard/session-trace/${userId}?limit=500`, {
          headers: { ...(this.getToken() ? { 'Authorization': `Bearer ${this.getToken()}` } : {}) },
        })
        if (traceRes.ok) {
          const traceData = await traceRes.json()
          const totalInteractions = traceData.session_summary?.total_interactions
          if (typeof totalInteractions === 'number' && totalInteractions > 0) {
            tasksCompleted = totalInteractions
          }
        }
      } catch { /* use concept-count fallback */ }

      const state: LearningState = {
        user_id: raw.user_id ?? userId,
        mastery,
        current_task: null,
        recommendations: [],
        projection: { mastery: {}, ensemble_weights: {}, governance_metrics: {} as any, timestamp: new Date().toISOString() },
        last_updated: new Date().toISOString(),
        tasks_completed: tasksCompleted,
        streak: 0,
      }
      this.setCache(cacheKey, state)

      return state
    } catch (error) {
      this.log('Error fetching learning state:', error)
      throw new Error(`Unable to fetch learning state: ${error instanceof Error ? error.message : String(error)}`)
    }
  }

  /**
   * Fetch task recommendations for a user.
   * Calls GET /v3/runtime/recommendation/state/{userId} and normalises to Recommendation[].
   */
  async getRecommendations(userId: string, count: number = 5): Promise<Recommendation[]> {
    const cacheKey = `recommendations-${userId}-${count}`
    const cached = this.getFromCache(cacheKey)

    if (cached) {
      this.log('Cache hit for recommendations:', userId)
      return cached as Recommendation[]
    }

    this.log('Fetching recommendations for user:', userId, 'count:', count)

    try {
      const base = getV3ApiUrl()
      const response = await fetch(`${base}/runtime/recommendation/state/${userId}`, {
        headers: { 'Content-Type': 'application/json' },
      })

      if (!response.ok) {
        this.log('Recommendation endpoint unavailable:', response.status)
        return []
      }

      const data = await response.json()
      const concept = data.recommended_concept ?? ''
      // Don't surface a recommendation if the engine hasn't converged yet
      if (!concept || concept === 'unknown') return []
      const recs: Recommendation[] = [{
        task_id: concept,
        reason: data.reasoning_summary ?? 'Recommended by adaptive engine',
        confidence: data.confidence_score ?? 0.5,
        expected_mastery: data.estimated_success_probability ?? 0.5,
        policy: 'hcie',
      }]
      this.setCache(cacheKey, recs)

      return recs
    } catch (error) {
      this.log('Error fetching recommendations:', error)
      return []
    }
  }

  /**
   * Submit a task answer
   */
  async submitAnswer(submission: TaskSubmission): Promise<SubmissionResult> {
    this.log('Submitting answer for task:', submission.task_id)
    
    try {
      const response = await fetch(`${this.apiUrl}/learning/submit`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.getToken()}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(submission),
      })

      if (!response.ok) {
        throw new Error(`Failed to submit answer: ${response.statusText}`)
      }

      const data = await response.json()
      
      // Invalidate related cache entries
      this.invalidateCache(`learning-state-${submission.user_id}`)
      this.invalidateCache(`recommendations-${submission.user_id}`)
      
      return data as SubmissionResult
    } catch (error) {
      this.log('Error submitting answer:', error)
      throw new Error(`Unable to submit answer: ${error instanceof Error ? error.message : String(error)}`)
    }
  }

  /**
   * Fetch learning progress for a user
   */
  async getProgress(userId: string): Promise<Progress> {
    const cacheKey = `progress-${userId}`
    const cached = this.getFromCache(cacheKey)
    
    if (cached) {
      this.log('Cache hit for progress:', userId)
      return cached as Progress
    }

    this.log('Fetching progress for user:', userId)
    
    try {
      const response = await fetch(`${this.apiUrl}/learning/progress/${userId}`, {
        headers: {
          'Authorization': `Bearer ${this.getToken()}`,
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`Failed to fetch progress: ${response.statusText}`)
      }

      const data = await response.json()
      this.setCache(cacheKey, data)
      
      return data as Progress
    } catch (error) {
      this.log('Error fetching progress:', error)
      throw new Error(`Unable to fetch progress: ${error instanceof Error ? error.message : String(error)}`)
    }
  }

  /**
   * Fetch the next recommended task for a user
   */
  async getNextTask(userId: string): Promise<{ task: Task; reason: string; confidence: number }> {
    const cacheKey = `next-task-${userId}`
    const cached = this.getFromCache(cacheKey)
    
    if (cached) {
      this.log('Cache hit for next task:', userId)
      return cached as { task: Task; reason: string; confidence: number }
    }

    this.log('Fetching next task for user:', userId)
    
    try {
      const response = await fetch(`${this.apiUrl}/learning/next-task/${userId}`, {
        headers: {
          'Authorization': `Bearer ${this.getToken()}`,
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`Failed to fetch next task: ${response.statusText}`)
      }

      const data = await response.json()
      this.setCache(cacheKey, data)
      
      return data as { task: Task; reason: string; confidence: number }
    } catch (error) {
      this.log('Error fetching next task:', error)
      throw new Error(`Unable to fetch next task: ${error instanceof Error ? error.message : String(error)}`)
    }
  }

  /**
   * Reset learning state for a user (admin only)
   */
  async resetLearningState(userId: string): Promise<void> {
    this.log('Resetting learning state for user:', userId)
    
    try {
      const response = await fetch(`${this.apiUrl}/learning/reset/${userId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.getToken()}`,
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`Failed to reset learning state: ${response.statusText}`)
      }

      // Invalidate related cache entries
      this.invalidateCache(`learning-state-${userId}`)
      this.invalidateCache(`recommendations-${userId}`)
      this.invalidateCache(`progress-${userId}`)
    } catch (error) {
      this.log('Error resetting learning state:', error)
      throw new Error(`Unable to reset learning state: ${error instanceof Error ? error.message : String(error)}`)
    }
  }

  /**
   * Get data from cache if not expired
   */
  private getFromCache(key: string): unknown | null {
    const cached = this.cache.get(key)
    if (!cached) return null
    
    const now = Date.now()
    if (now - cached.timestamp > this.cacheDuration) {
      this.cache.delete(key)
      return null
    }
    
    return cached.data
  }

  /**
   * Set data in cache
   */
  private setCache(key: string, data: unknown): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
    })
  }

  /**
   * Invalidate cache entry
   */
  private invalidateCache(key: string): void {
    this.cache.delete(key)
  }

  /**
   * Clear all cache
   */
  clearCache(): void {
    this.cache.clear()
  }

  /**
   * Debug logging
   */
  private log(...args: unknown[]): void {
    if (this.debug) {
      console.log('[LearningService]', ...args)
    }
  }
}
