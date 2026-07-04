/**
 * Dashboard API Route
 * 
 * Server-side API endpoint for dashboard-related data fetching.
 * Uses Next.js App Router API routes for server-side data processing.
 */

import { NextRequest, NextResponse } from 'next/server'
import { blockInProd } from '@/lib/api/dev-only-guard'

export async function GET(request: NextRequest) {
  const blocked = blockInProd()
  if (blocked) return blocked
  try {
    const searchParams = request.nextUrl.searchParams
    const userId = searchParams.get('userId')
    const action = searchParams.get('action')

    // In production, this would call the backend dashboard service
    switch (action) {
      case 'system-overview':
        return NextResponse.json({
          total_users: 150,
          active_users: 45,
          total_experiments: 10,
          running_experiments: 3,
          system_health: 'healthy',
          last_updated: new Date().toISOString(),
        })
      case 'user-dashboard':
        if (!userId) {
          return NextResponse.json({ error: 'userId is required' }, { status: 400 })
        }
        return NextResponse.json({
          user: {
            id: userId,
            username: 'student1',
            email: 'student1@example.com',
            role: 'user',
            permissions: ['read:learning', 'write:progress'],
            created_at: '2026-01-15T10:00:00Z',
          },
          learning_state: {
            user_id: userId,
            mastery: { algebra: 0.75, geometry: 0.68, calculus: 0.45 },
            current_task: null,
            recommendations: [],
            projection: null,
            last_updated: new Date().toISOString(),
          },
          recent_activity: [
            {
              id: 'act_001',
              type: 'task_completed',
              description: 'Completed algebra task',
              timestamp: new Date().toISOString(),
            },
          ],
          achievements: [
            {
              id: 'ach_001',
              title: 'First Steps',
              description: 'Complete your first task',
              icon: '🎯',
              unlocked: true,
              unlocked_at: '2026-01-16T10:00:00Z',
            },
          ],
        })
      case 'analytics':
        const startDate = searchParams.get('startDate')
        const endDate = searchParams.get('endDate')
        return NextResponse.json({
          learning_curves: [
            {
              concept: 'algebra',
              data: [
                { timestamp: startDate || '2026-04-01', mastery: 0.5 },
                { timestamp: endDate || new Date().toISOString(), mastery: 0.75 },
              ],
              current_mastery: 0.75,
              target_mastery: 0.9,
            },
          ],
          engagement_metrics: {
            total_sessions: 50,
            avg_session_duration: 1800,
            tasks_completed: 38,
            accuracy: 0.82,
            avg_time_on_task: 45,
          },
          performance_metrics: {
            overall_accuracy: 0.82,
            avg_response_time: 4500,
            completion_rate: 0.76,
            retention_rate: 0.85,
            learning_gain: 0.25,
          },
          time_range: {
            start: startDate || '2026-04-01',
            end: endDate || new Date().toISOString(),
            granularity: 'day',
          },
        })
      default:
        return NextResponse.json({ error: 'Invalid action' }, { status: 400 })
    }
  } catch (error) {
    console.error('Dashboard API error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
