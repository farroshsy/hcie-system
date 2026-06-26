import { NextResponse } from 'next/server'

/**
 * These App Router `/api/*` routes return fabricated/mock data and are NOT used
 * by the deployed app — real data is fetched from the backend
 * (NEXT_PUBLIC_API_URL), and MSW intercepts `/api/*` during local development.
 *
 * They're kept (not deleted) as a convenient local mock surface, but must never
 * serve fake data in production. Call this guard at the top of each handler:
 * in any non-development environment it short-circuits with 404 so the fake
 * payloads cannot masquerade as real responses.
 *
 * Returns a NextResponse to return early, or null to proceed.
 */
export function blockInProd(): NextResponse | null {
  if (process.env.NODE_ENV === 'development') return null
  return NextResponse.json(
    { error: 'Not found' },
    { status: 404 },
  )
}
