/**
 * Dashboard Mapper Implementation
 * 
 * Implements the IDashboardMapper protocol for mapping dashboard data between different representations.
 * This mapper handles conversion between API responses and domain models.
 */

import type {
  IDashboardMapper,
  SystemOverview,
  UserDashboardData,
  AnalyticsData,
  AnalyticsQueryParams,
} from '../interfaces'

/**
 * Dashboard Mapper Implementation
 */
export class DashboardMapper implements IDashboardMapper {
  /**
   * Map API response to system overview
   */
  apiToSystemOverview(apiResponse: unknown): SystemOverview {
    const response = apiResponse as Record<string, unknown>
    
    return {
      total_users: (response.total_users as number) || 0,
      active_users: (response.active_users as number) || 0,
      total_experiments: (response.total_experiments as number) || 0,
      running_experiments: (response.running_experiments as number) || 0,
      system_health: (response.system_health as 'healthy' | 'degraded' | 'unhealthy') || 'healthy',
      last_updated: response.last_updated as string || new Date().toISOString(),
    }
  }

  /**
   * Map API response to user dashboard data
   */
  apiToUserDashboard(apiResponse: unknown): UserDashboardData {
    const response = apiResponse as Record<string, unknown>
    
    return {
      user: response.user as {
        id: string
        username: string
        email: string
        role: 'user' | 'student' | 'researcher' | 'admin'
        permissions: string[]
        created_at: string
      },
      learning_state: response.learning_state as {
        user_id: string
        mastery: Record<string, number>
        current_task: unknown | null
        recommendations: unknown[]
        projection: unknown
        last_updated: string
      },
      recent_activity: (response.recent_activity as Array<{
        id: string
        type: 'task_completed' | 'login' | 'achievement' | 'experiment'
        description: string
        timestamp: string
        metadata?: Record<string, unknown>
      }>) || [],
      achievements: (response.achievements as Array<{
        id: string
        title: string
        description: string
        icon?: string
        unlocked: boolean
        unlocked_at?: string
      }>) || [],
    }
  }

  /**
   * Map API response to analytics data
   */
  apiToAnalytics(apiResponse: unknown): AnalyticsData {
    const response = apiResponse as Record<string, unknown>
    
    return {
      learning_curves: (response.learning_curves as Array<{
        concept: string
        data: Array<{ timestamp: string; mastery: number }>
        current_mastery: number
        target_mastery: number
      }>) || [],
      engagement_metrics: response.engagement_metrics as {
        total_sessions: number
        avg_session_duration: number
        tasks_completed: number
        accuracy: number
        avg_time_on_task: number
      } || {
        total_sessions: 0,
        avg_session_duration: 0,
        tasks_completed: 0,
        accuracy: 0,
        avg_time_on_task: 0,
      },
      performance_metrics: response.performance_metrics as {
        overall_accuracy: number
        avg_response_time: number
        completion_rate: number
        retention_rate: number
        learning_gain: number
      } || {
        overall_accuracy: 0,
        avg_response_time: 0,
        completion_rate: 0,
        retention_rate: 0,
        learning_gain: 0,
      },
      time_range: response.time_range as {
        start: string
        end: string
        granularity: 'hour' | 'day' | 'week'
      } || {
        start: new Date().toISOString(),
        end: new Date().toISOString(),
        granularity: 'day',
      },
    }
  }

  /**
   * Map analytics query parameters to API request format
   */
  analyticsParamsToApi(params: AnalyticsQueryParams): Record<string, unknown> {
    return {
      start_date: params.start_date,
      end_date: params.end_date,
      granularity: params.granularity,
      user_id: params.user_id,
      concepts: params.concepts,
    }
  }

  /**
   * Map widget configuration to API request format
   */
  widgetsToApi(widgets: Array<{
    id: string
    type: 'metric' | 'chart' | 'table' | 'list'
    title: string
    position: { x: number; y: number; w: number; h: number }
    config: Record<string, unknown>
    visible: boolean
  }>): Record<string, unknown> {
    return {
      widgets: widgets.map(widget => ({
        id: widget.id,
        type: widget.type,
        title: widget.title,
        position: widget.position,
        config: widget.config,
        visible: widget.visible,
      })),
    }
  }
}
