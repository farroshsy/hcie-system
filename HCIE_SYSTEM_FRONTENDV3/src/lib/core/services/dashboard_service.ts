/**
 * Dashboard Service Implementation
 * 
 * Implements the IDashboardService protocol for dashboard-related operations.
 * This service handles system overview, user-specific data, and analytics.
 */

import type {
  IDashboardService,
  DashboardServiceConfig,
  SystemOverview,
  UserDashboardData,
  AnalyticsData,
  LearningCurve,
  Activity,
  Achievement,
  DashboardWidget,
  AnalyticsQueryParams,
} from '../interfaces'

/**
 * Dashboard Service Implementation
 */
export class DashboardService implements IDashboardService {
  private apiUrl: string
  private authToken: string
  private cacheDuration: number
  private enableRealtime: boolean
  private wsUrl: string | undefined
  private debug: boolean
  private cache: Map<string, { data: unknown; timestamp: number }>

  constructor(config: DashboardServiceConfig) {
    this.apiUrl = config.apiUrl
    this.authToken = config.authToken
    this.cacheDuration = config.cacheDuration || 5 * 60 * 1000 // 5 minutes default
    this.enableRealtime = config.enableRealtime || false
    this.wsUrl = config.wsUrl
    this.debug = config.debug || false
    this.cache = new Map()
  }

  /**
   * Get system overview metrics
   */
  async getSystemOverview(): Promise<SystemOverview> {
    const cacheKey = 'system-overview'
    const cached = this.getFromCache(cacheKey)
    
    if (cached) {
      this.log('Cache hit for system overview')
      return cached as SystemOverview
    }

    this.log('Fetching system overview')
    
    try {
      const response = await fetch(`${this.apiUrl}/dashboard/system-overview`, {
        headers: {
          'Authorization': `Bearer ${this.authToken}`,
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`Failed to fetch system overview: ${response.statusText}`)
      }

      const data = await response.json()
      this.setCache(cacheKey, data)
      
      return data as SystemOverview
    } catch (error) {
      this.log('Error fetching system overview:', error)
      throw new Error(`Unable to fetch system overview: ${error instanceof Error ? error.message : String(error)}`)
    }
  }

  /**
   * Get user-specific dashboard data
   */
  async getUserDashboard(userId: string): Promise<UserDashboardData> {
    const cacheKey = `user-dashboard-${userId}`
    const cached = this.getFromCache(cacheKey)
    
    if (cached) {
      this.log('Cache hit for user dashboard:', userId)
      return cached as UserDashboardData
    }

    this.log('Fetching user dashboard for user:', userId)
    
    try {
      const response = await fetch(`${this.apiUrl}/dashboard/user/${userId}`, {
        headers: {
          'Authorization': `Bearer ${this.authToken}`,
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`Failed to fetch user dashboard: ${response.statusText}`)
      }

      const data = await response.json()
      this.setCache(cacheKey, data)
      
      return data as UserDashboardData
    } catch (error) {
      this.log('Error fetching user dashboard:', error)
      throw new Error(`Unable to fetch user dashboard: ${error instanceof Error ? error.message : String(error)}`)
    }
  }

  /**
   * Get analytics data
   */
  async getAnalytics(params: AnalyticsQueryParams): Promise<AnalyticsData> {
    const cacheKey = `analytics-${params.start_date}-${params.end_date}-${params.granularity}-${params.user_id || 'system'}`
    const cached = this.getFromCache(cacheKey)
    
    if (cached) {
      this.log('Cache hit for analytics')
      return cached as AnalyticsData
    }

    this.log('Fetching analytics with params:', params)
    
    try {
      const queryParams = new URLSearchParams({
        start_date: params.start_date,
        end_date: params.end_date,
        granularity: params.granularity,
      })
      
      if (params.user_id) {
        queryParams.append('user_id', params.user_id)
      }
      
      if (params.concepts && params.concepts.length > 0) {
        queryParams.append('concepts', params.concepts.join(','))
      }

      const response = await fetch(`${this.apiUrl}/dashboard/analytics?${queryParams.toString()}`, {
        headers: {
          'Authorization': `Bearer ${this.authToken}`,
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`Failed to fetch analytics: ${response.statusText}`)
      }

      const data = await response.json()
      this.setCache(cacheKey, data)
      
      return data as AnalyticsData
    } catch (error) {
      this.log('Error fetching analytics:', error)
      throw new Error(`Unable to fetch analytics: ${error instanceof Error ? error.message : String(error)}`)
    }
  }

  /**
   * Get learning curves for a user
   */
  async getLearningCurves(
    userId: string,
    concepts?: string[],
    timeRange?: { start: string; end: string }
  ): Promise<LearningCurve[]> {
    const cacheKey = `learning-curves-${userId}-${concepts?.join(',') || 'all'}-${timeRange?.start || 'all'}`
    const cached = this.getFromCache(cacheKey)
    
    if (cached) {
      this.log('Cache hit for learning curves:', userId)
      return cached as LearningCurve[]
    }

    this.log('Fetching learning curves for user:', userId)
    
    try {
      const queryParams = new URLSearchParams()
      
      if (concepts && concepts.length > 0) {
        queryParams.append('concepts', concepts.join(','))
      }
      
      if (timeRange) {
        queryParams.append('start', timeRange.start)
        queryParams.append('end', timeRange.end)
      }

      const response = await fetch(`${this.apiUrl}/dashboard/learning-curves/${userId}?${queryParams.toString()}`, {
        headers: {
          'Authorization': `Bearer ${this.authToken}`,
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`Failed to fetch learning curves: ${response.statusText}`)
      }

      const data = await response.json()
      this.setCache(cacheKey, data)
      
      return data as LearningCurve[]
    } catch (error) {
      this.log('Error fetching learning curves:', error)
      throw new Error(`Unable to fetch learning curves: ${error instanceof Error ? error.message : String(error)}`)
    }
  }

  /**
   * Get recent activity for a user
   */
  async getRecentActivity(userId: string, limit: number = 10): Promise<Activity[]> {
    const cacheKey = `recent-activity-${userId}-${limit}`
    const cached = this.getFromCache(cacheKey)
    
    if (cached) {
      this.log('Cache hit for recent activity:', userId)
      return cached as Activity[]
    }

    this.log('Fetching recent activity for user:', userId, 'limit:', limit)
    
    try {
      const response = await fetch(`${this.apiUrl}/dashboard/activity/${userId}?limit=${limit}`, {
        headers: {
          'Authorization': `Bearer ${this.authToken}`,
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`Failed to fetch recent activity: ${response.statusText}`)
      }

      const data = await response.json()
      this.setCache(cacheKey, data)
      
      return data as Activity[]
    } catch (error) {
      this.log('Error fetching recent activity:', error)
      throw new Error(`Unable to fetch recent activity: ${error instanceof Error ? error.message : String(error)}`)
    }
  }

  /**
   * Get achievements for a user
   */
  async getAchievements(userId: string): Promise<Achievement[]> {
    const cacheKey = `achievements-${userId}`
    const cached = this.getFromCache(cacheKey)
    
    if (cached) {
      this.log('Cache hit for achievements:', userId)
      return cached as Achievement[]
    }

    this.log('Fetching achievements for user:', userId)
    
    try {
      const response = await fetch(`${this.apiUrl}/dashboard/achievements/${userId}`, {
        headers: {
          'Authorization': `Bearer ${this.authToken}`,
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`Failed to fetch achievements: ${response.statusText}`)
      }

      const data = await response.json()
      this.setCache(cacheKey, data)
      
      return data as Achievement[]
    } catch (error) {
      this.log('Error fetching achievements:', error)
      throw new Error(`Unable to fetch achievements: ${error instanceof Error ? error.message : String(error)}`)
    }
  }

  /**
   * Get dashboard widget configuration
   */
  async getWidgetConfig(userId: string): Promise<DashboardWidget[]> {
    const cacheKey = `widget-config-${userId}`
    const cached = this.getFromCache(cacheKey)
    
    if (cached) {
      this.log('Cache hit for widget config:', userId)
      return cached as DashboardWidget[]
    }

    this.log('Fetching widget config for user:', userId)
    
    try {
      const response = await fetch(`${this.apiUrl}/dashboard/widgets/${userId}`, {
        headers: {
          'Authorization': `Bearer ${this.authToken}`,
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`Failed to fetch widget config: ${response.statusText}`)
      }

      const data = await response.json()
      this.setCache(cacheKey, data)
      
      return data as DashboardWidget[]
    } catch (error) {
      this.log('Error fetching widget config:', error)
      throw new Error(`Unable to fetch widget config: ${error instanceof Error ? error.message : String(error)}`)
    }
  }

  /**
   * Save dashboard widget configuration
   */
  async saveWidgetConfig(userId: string, widgets: DashboardWidget[]): Promise<void> {
    this.log('Saving widget config for user:', userId)
    
    try {
      const response = await fetch(`${this.apiUrl}/dashboard/widgets/${userId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.authToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ widgets }),
      })

      if (!response.ok) {
        throw new Error(`Failed to save widget config: ${response.statusText}`)
      }

      // Invalidate cache
      this.invalidateCache(`widget-config-${userId}`)
    } catch (error) {
      this.log('Error saving widget config:', error)
      throw new Error(`Unable to save widget config: ${error instanceof Error ? error.message : String(error)}`)
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
      console.log('[DashboardService]', ...args)
    }
  }
}
