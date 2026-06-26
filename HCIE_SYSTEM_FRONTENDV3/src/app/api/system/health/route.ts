/**
 * System Health Check Route
 * 
 * Simple health check endpoint for monitoring and load balancers.
 * Returns minimal health status for quick checks.
 */

import { NextResponse } from 'next/server'

export async function GET() {
  try {
    // In production, this would check actual system health
    return NextResponse.json({
      status: 'healthy',
      timestamp: new Date().toISOString(),
    })
  } catch (error) {
    return NextResponse.json({ status: 'unhealthy', error: 'Health check failed' }, { status: 503 })
  }
}
