/**
 * Learning API Route
 * 
 * Server-side API endpoint for learning-related data fetching.
 * Uses Next.js App Router API routes for server-side data processing.
 */

import { NextRequest, NextResponse } from 'next/server'
import { blockInProd } from '@/lib/api/dev-only-guard'

export const dynamic = 'force-dynamic'

export async function GET(request: NextRequest) {
  const blocked = blockInProd()
  if (blocked) return blocked
  try {
    const searchParams = request.nextUrl.searchParams
    const userId = searchParams.get('userId')
    const action = searchParams.get('action')

    if (!userId) {
      return NextResponse.json({ error: 'userId is required' }, { status: 400 })
    }

    // In production, this would call the backend services
    // For now, returning mock data
    switch (action) {
      case 'state':
        return NextResponse.json({
          user_id: userId,
          mastery: { algebra: 0.75, geometry: 0.68, calculus: 0.45 },
          tasks_completed: 38,
          streak: 7,
          last_updated: new Date().toISOString(),
        })
      case 'next-task':
        return NextResponse.json({
          task_id: 'task_001',
          concept: 'Algebra',
          difficulty: 0.6,
          content: 'Solve for x: 2x + 5 = 15',
          options: ['x = 5', 'x = 10', 'x = 7', 'x = 3'],
        })
      case 'recommendations':
        return NextResponse.json([
          { task_id: 'task_002', concept: 'Geometry', confidence: 0.85, reason: 'Based on your progress' },
          { task_id: 'task_003', concept: 'Algebra', confidence: 0.78, reason: 'Reinforce learning' },
        ])
      default:
        return NextResponse.json({ error: 'Invalid action' }, { status: 400 })
    }
  } catch (error) {
    console.error('Learning API error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

export async function POST(request: NextRequest) {
  const blocked = blockInProd()
  if (blocked) return blocked
  try {
    const body = await request.json()
    const { userId, taskId, answer, responseTime } = body

    if (!userId || !taskId || !answer) {
      return NextResponse.json({ error: 'Missing required fields' }, { status: 400 })
    }

    // In production, this would call the backend learning service
    // For now, returning mock result
    const isCorrect = answer === 'x = 5' // Mock validation

    return NextResponse.json({
      correct: isCorrect,
      points_earned: isCorrect ? 10 : 0,
      feedback: isCorrect ? 'Great job!' : 'Try again',
      new_mastery: isCorrect ? 0.78 : 0.72,
    })
  } catch (error) {
    console.error('Learning API error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
