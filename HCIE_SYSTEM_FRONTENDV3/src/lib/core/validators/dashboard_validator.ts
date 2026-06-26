/**
 * Dashboard Validator Implementation
 * 
 * Implements the IDashboardValidator protocol for validating dashboard-related data.
 * This validator uses Zod schemas for runtime type checking and validation.
 */

import { z } from 'zod'
import type {
  IDashboardValidator,
  AnalyticsQueryParams,
  DashboardWidget,
  SystemOverview,
  UserDashboardData,
} from '../interfaces'

/**
 * Zod schemas for dashboard-related data
 */
const AnalyticsQueryParamsSchema = z.object({
  start_date: z.string(),
  end_date: z.string(),
  granularity: z.enum(['hour', 'day', 'week']),
  user_id: z.string().optional(),
  concepts: z.array(z.string()).optional(),
})

const DashboardWidgetSchema = z.object({
  id: z.string(),
  type: z.enum(['metric', 'chart', 'table', 'list']),
  title: z.string(),
  position: z.object({
    x: z.number(),
    y: z.number(),
    w: z.number(),
    h: z.number(),
  }),
  config: z.record(z.string(), z.unknown()),
  visible: z.boolean(),
})

const SystemOverviewSchema = z.object({
  total_users: z.number().min(0),
  active_users: z.number().min(0),
  total_experiments: z.number().min(0),
  running_experiments: z.number().min(0),
  system_health: z.enum(['healthy', 'degraded', 'unhealthy']),
  last_updated: z.string(),
})

const UserDashboardDataSchema = z.object({
  user: z.object({
    id: z.string(),
    username: z.string(),
    email: z.string(),
    role: z.enum(['user', 'admin']),
    permissions: z.array(z.string()),
    created_at: z.string(),
  }),
  learning_state: z.any(),
  recent_activity: z.array(z.object({
    id: z.string(),
    type: z.string(),
    description: z.string(),
    timestamp: z.string(),
    metadata: z.record(z.string(), z.unknown()).optional(),
  })),
  achievements: z.array(z.object({
    id: z.string(),
    title: z.string(),
    description: z.string(),
    icon: z.string().optional(),
    unlocked: z.boolean(),
    unlocked_at: z.string().optional(),
  })),
}) as z.ZodType<UserDashboardData>

/**
 * Dashboard Validator Implementation
 */
export class DashboardValidator implements IDashboardValidator {
  /**
   * Validate analytics query parameters
   */
  validateAnalyticsParams(params: unknown): params is AnalyticsQueryParams {
    return AnalyticsQueryParamsSchema.safeParse(params).success
  }

  /**
   * Validate dashboard widget
   */
  validateWidget(widget: unknown): widget is DashboardWidget {
    return DashboardWidgetSchema.safeParse(widget).success
  }

  /**
   * Validate system overview
   */
  validateSystemOverview(overview: unknown): overview is SystemOverview {
    return SystemOverviewSchema.safeParse(overview).success
  }

  /**
   * Validate user dashboard data
   */
  validateUserDashboard(data: unknown): data is UserDashboardData {
    const result = UserDashboardDataSchema.safeParse(data)
    if (result.success) {
      return true
    }
    // Fallback: check if it has the required structure
    return typeof data === 'object' && data !== null && 'user' in data && 'learning_state' in data
  }

  /**
   * Validate and parse analytics params (throws on error)
   */
  parseAnalyticsParams(params: unknown): AnalyticsQueryParams {
    return AnalyticsQueryParamsSchema.parse(params)
  }

  /**
   * Validate and parse widget (throws on error)
   */
  parseWidget(widget: unknown): DashboardWidget {
    return DashboardWidgetSchema.parse(widget)
  }

  /**
   * Validate and parse system overview (throws on error)
   */
  parseSystemOverview(overview: unknown): SystemOverview {
    return SystemOverviewSchema.parse(overview)
  }

  /**
   * Validate and parse user dashboard data (throws on error)
   */
  parseUserDashboard(data: unknown): UserDashboardData {
    return UserDashboardDataSchema.parse(data)
  }
}
