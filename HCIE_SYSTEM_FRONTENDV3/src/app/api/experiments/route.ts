/**
 * Experiments API Route
 * 
 * Server-side API endpoint for experiment management.
 * Uses Next.js App Router API routes for server-side data processing.
 */

import { NextRequest, NextResponse } from 'next/server'
import { blockInProd } from '@/lib/api/dev-only-guard'

export async function GET(request: NextRequest) {
  const blocked = blockInProd()
  if (blocked) return blocked
  try {
    const searchParams = request.nextUrl.searchParams
    const action = searchParams.get('action')
    const experimentId = searchParams.get('experimentId')

    switch (action) {
      case 'list':
        return NextResponse.json([
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
        ])
      case 'detail':
        if (!experimentId) {
          return NextResponse.json({ error: 'experimentId is required' }, { status: 400 })
        }
        return NextResponse.json({
          id: experimentId,
          name: 'HCIE vs Random Policy',
          description: 'Compare HCIE adaptive policy against random baseline',
          status: 'running',
          startDate: '2026-05-01',
          participants: 150,
          conditions: ['HCIE', 'Random'],
          results: {
            hcie: { average_mastery: 0.82, completion_rate: 0.78 },
            random: { average_mastery: 0.65, completion_rate: 0.70 },
          },
        })
      default:
        return NextResponse.json({ error: 'Invalid action' }, { status: 400 })
    }
  } catch (error) {
    console.error('Experiments API error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

export async function POST(request: NextRequest) {
  const blocked = blockInProd()
  if (blocked) return blocked
  try {
    const body = await request.json()
    const { name, description, conditions, startDate } = body

    if (!name || !conditions) {
      return NextResponse.json({ error: 'Missing required fields' }, { status: 400 })
    }

    // In production, this would create a new experiment
    return NextResponse.json({
      id: `exp_${Date.now()}`,
      name,
      description: description || '',
      status: 'scheduled',
      startDate: startDate || new Date().toISOString(),
      participants: 0,
      conditions,
    })
  } catch (error) {
    console.error('Experiments API error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
