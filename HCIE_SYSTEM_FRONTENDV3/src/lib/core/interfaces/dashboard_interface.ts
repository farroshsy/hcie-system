/**
 * Dashboard Interface Protocol
 * 
 * Defines the contract for dashboard-related operations in the HCIE system.
 * This protocol ensures type safety and provides clear contracts for
 * system overview, user-specific data, and analytics.
 */

// ============================================================================
// Domain Types
// ============================================================================

/**
 * Represents system overview metrics
 */
export interface SystemOverview {
  /** Total number of users */
  total_users: number
  /** Number of currently active users */
  active_users: number
  /** Total number of experiments */
  total_experiments: number
  /** Number of currently running experiments */
  running_experiments: number
  /** System health status */
  system_health: 'healthy' | 'degraded' | 'unhealthy'
  /** Last updated timestamp */
  last_updated: string
}

/**
 * Represents user-specific dashboard data
 */
export interface UserDashboardData {
  /** User information */
  user: User
  /** Learning state */
  learning_state: LearningState
  /** Recent activity */
  recent_activity: Activity[]
  /** Achievements */
  achievements: Achievement[]
}

/**
 * Represents an activity event
 */
export interface Activity {
  /** Activity ID */
  id: string
  /** Activity type */
  type: 'task_completed' | 'login' | 'achievement' | 'experiment'
  /** Activity description */
  description: string
  /** Activity timestamp */
  timestamp: string
  /** Activity metadata */
  metadata?: Record<string, unknown>
}

/**
 * Represents an achievement
 */
export interface Achievement {
  /** Achievement ID */
  id: string
  /** Achievement title */
  title: string
  /** Achievement description */
  description: string
  /** Achievement icon */
  icon?: string
  /** Whether achievement is unlocked */
  unlocked: boolean
  /** Unlocked timestamp (if unlocked) */
  unlocked_at?: string
}

/**
 * Represents analytics data
 */
export interface AnalyticsData {
  /** Learning curves data */
  learning_curves: LearningCurve[]
  /** Engagement metrics */
  engagement_metrics: EngagementMetrics
  /** Performance metrics */
  performance_metrics: PerformanceMetrics
  /** Time range for analytics */
  time_range: {
    start: string
    end: string
    granularity: 'hour' | 'day' | 'week'
  }
}

/**
 * Represents a learning curve data point
 */
export interface LearningCurve {
  /** Concept identifier */
  concept: string
  /** Data points (timestamp, mastery) */
  data: Array<{
    timestamp: string
    mastery: number
  }>
  /** Current mastery level */
  current_mastery: number
  /** Target mastery level */
  target_mastery: number
}

/**
 * Represents engagement metrics
 */
export interface EngagementMetrics {
  /** Total sessions */
  total_sessions: number
  /** Average session duration (seconds) */
  avg_session_duration: number
  /** Tasks completed */
  tasks_completed: number
  /** Accuracy rate (0-1) */
  accuracy: number
  /** Time on task (average) */
  avg_time_on_task: number
}

/**
 * Represents performance metrics
 */
export interface PerformanceMetrics {
  /** Overall accuracy (0-1) */
  overall_accuracy: number
  /** Average response time (milliseconds) */
  avg_response_time: number
  /** Completion rate (0-1) */
  completion_rate: number
  /** Retention rate (0-1) */
  retention_rate: number
  /** Learning gain (0-1) */
  learning_gain: number
}

/**
 * Represents a dashboard widget configuration
 */
export interface DashboardWidget {
  /** Widget ID */
  id: string
  /** Widget type */
  type: 'metric' | 'chart' | 'table' | 'list'
  /** Widget title */
  title: string
  /** Widget position */
  position: { x: number; y: number; w: number; h: number }
  /** Widget configuration */
  config: Record<string, unknown>
  /** Whether widget is visible */
  visible: boolean
}

/**
 * User type (simplified)
 */
export interface User {
  id: string
  username: string
  email: string
  role: 'user' | 'student' | 'researcher' | 'admin'
  permissions: string[]
  created_at: string
}

/**
 * Learning state type (simplified)
 */
export interface LearningState {
  user_id: string
  mastery: Record<string, number>
  current_task: unknown | null
  recommendations: unknown[]
  projection: unknown
  last_updated: string
}

// ============================================================================
// Service Protocol
// ============================================================================

/**
 * Dashboard Service Protocol
 * 
 * Defines the contract for dashboard-related operations.
 * All implementations must adhere to this protocol.
 */
export interface IDashboardService {
  /**
   * Get system overview metrics
   * @returns Promise resolving to system overview
   * @throws Error if API request fails
   */
  getSystemOverview(): Promise<SystemOverview>

  /**
   * Get user-specific dashboard data
   * @param userId - User identifier
   * @returns Promise resolving to user dashboard data
   * @throws Error if user not found or API request fails
   */
  getUserDashboard(userId: string): Promise<UserDashboardData>

  /**
   * Get analytics data
   * @param params - Analytics query parameters
   * @returns Promise resolving to analytics data
   * @throws Error if API request fails
   */
  getAnalytics(params: AnalyticsQueryParams): Promise<AnalyticsData>

  /**
   * Get learning curves for a user
   * @param userId - User identifier
   * @param concepts - List of concepts to fetch (empty for all)
   * @param timeRange - Time range for data
   * @returns Promise resolving to learning curves
   * @throws Error if API request fails
   */
  getLearningCurves(
    userId: string,
    concepts?: string[],
    timeRange?: { start: string; end: string }
  ): Promise<LearningCurve[]>

  /**
   * Get recent activity for a user
   * @param userId - User identifier
   * @param limit - Number of activities to fetch (default: 10)
   * @returns Promise resolving to recent activities
   * @throws Error if API request fails
   */
  getRecentActivity(userId: string, limit?: number): Promise<Activity[]>

  /**
   * Get achievements for a user
   * @param userId - User identifier
   * @returns Promise resolving to achievements
   * @throws Error if API request fails
   */
  getAchievements(userId: string): Promise<Achievement[]>

  /**
   * Get dashboard widget configuration
   * @param userId - User identifier
   * @returns Promise resolving to widget configuration
   * @throws Error if API request fails
   */
  getWidgetConfig(userId: string): Promise<DashboardWidget[]>

  /**
   * Save dashboard widget configuration
   * @param userId - User identifier
   * @param widgets - Widget configuration
   * @returns Promise resolving when saved
   * @throws Error if save fails or API request fails
   */
  saveWidgetConfig(userId: string, widgets: DashboardWidget[]): Promise<void>
}

/**
 * Analytics query parameters
 */
export interface AnalyticsQueryParams {
  /** Start date (ISO string) */
  start_date: string
  /** End date (ISO string) */
  end_date: string
  /** Granularity of data */
  granularity: 'hour' | 'day' | 'week'
  /** User ID (optional, for user-specific analytics) */
  user_id?: string
  /** Concepts to filter (optional) */
  concepts?: string[]
}

// ============================================================================
// Validator Protocol
// ============================================================================

/**
 * Dashboard Validator Protocol
 * 
 * Defines the contract for validating dashboard-related data.
 */
export interface IDashboardValidator {
  /**
   * Validate analytics query parameters
   * @param params - Parameters to validate
   * @returns Whether the parameters are valid
   */
  validateAnalyticsParams(params: unknown): params is AnalyticsQueryParams

  /**
   * Validate dashboard widget
   * @param widget - Widget to validate
   * @returns Whether the widget is valid
   */
  validateWidget(widget: unknown): widget is DashboardWidget

  /**
   * Validate system overview
   * @param overview - Overview to validate
   * @returns Whether the overview is valid
   */
  validateSystemOverview(overview: unknown): overview is SystemOverview

  /**
   * Validate user dashboard data
   * @param data - Data to validate
   * @returns Whether the data is valid
   */
  validateUserDashboard(data: unknown): data is UserDashboardData
}

// ============================================================================
// Mapper Protocol
// ============================================================================

/**
 * Dashboard Mapper Protocol
 * 
 * Defines the contract for mapping dashboard data between different representations.
 */
export interface IDashboardMapper {
  /**
   * Map API response to system overview
   * @param apiResponse - Raw API response
   * @returns Mapped system overview
   */
  apiToSystemOverview(apiResponse: unknown): SystemOverview

  /**
   * Map API response to user dashboard data
   * @param apiResponse - Raw API response
   * @returns Mapped user dashboard data
   */
  apiToUserDashboard(apiResponse: unknown): UserDashboardData

  /**
   * Map API response to analytics data
   * @param apiResponse - Raw API response
   * @returns Mapped analytics data
   */
  apiToAnalytics(apiResponse: unknown): AnalyticsData

  /**
   * Map analytics query parameters to API request format
   * @param params - Query parameters
   * @returns API request format
   */
  analyticsParamsToApi(params: AnalyticsQueryParams): Record<string, unknown>

  /**
   * Map widget configuration to API request format
   * @param widgets - Widget configuration
   * @returns API request format
   */
  widgetsToApi(widgets: DashboardWidget[]): Record<string, unknown>
}

// ============================================================================
// Factory Protocol
// ============================================================================

/**
 * Dashboard Service Factory Protocol
 * 
 * Defines the contract for creating dashboard service instances.
 */
export interface IDashboardServiceFactory {
  /**
   * Create a dashboard service instance
   * @param config - Service configuration
   * @returns Dashboard service instance
   */
  create(config: DashboardServiceConfig): IDashboardService

  /**
   * Create a dashboard validator instance
   * @returns Dashboard validator instance
   */
  createValidator(): IDashboardValidator

  /**
   * Create a dashboard mapper instance
   * @returns Dashboard mapper instance
   */
  createMapper(): IDashboardMapper
}

/**
 * Dashboard service configuration
 */
export interface DashboardServiceConfig {
  /** API base URL */
  apiUrl: string
  /** Authentication token */
  authToken: string
  /** Cache duration in milliseconds */
  cacheDuration?: number
  /** Enable real-time updates */
  enableRealtime?: boolean
  /** WebSocket URL for real-time updates */
  wsUrl?: string
  /** Enable debug logging */
  debug?: boolean
}
