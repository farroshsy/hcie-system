/**
 * System Status API Route
 * 
 * Server-side API endpoint for system health and status monitoring.
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

    switch (action) {
      case 'health':
        // In production, this would check actual system health
        return NextResponse.json({
          status: 'healthy',
          timestamp: new Date().toISOString(),
          services: {
            api: { status: 'healthy', latency: 45 },
            database: { status: 'healthy', latency: 12 },
            cache: { status: 'healthy', latency: 5 },
            websocket: { status: 'healthy', connections: 45 },
          },
          metrics: {
            uptime: '15d 4h 32m',
            requests_per_minute: 120,
            error_rate: 0.001,
          },
        })
      case 'metrics':
        // In production, this would return actual system metrics
        return NextResponse.json({
          cpu: { usage: 45, cores: 8 },
          memory: { used: 4.2, total: 16, percentage: 26 },
          disk: { used: 120, total: 500, percentage: 24 },
          network: {
            incoming: 1024 * 1024 * 10, // 10 MB/s
            outgoing: 1024 * 1024 * 5, // 5 MB/s
          },
        })
      default:
        return NextResponse.json({ error: 'Invalid action' }, { status: 400 })
    }
  } catch (error) {
    console.error('System API error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
