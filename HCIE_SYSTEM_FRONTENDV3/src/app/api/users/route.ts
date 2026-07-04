/**
 * Users API Route
 * 
 * Server-side API endpoint for user management.
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
    const userId = searchParams.get('userId')

    switch (action) {
      case 'list':
        return NextResponse.json([
          {
            id: 'user_001',
            username: 'student1',
            email: 'student1@example.com',
            role: 'user',
            permissions: ['read:learning', 'write:progress'],
            created_at: '2026-01-15T10:00:00Z',
            is_active: true,
          },
          {
            id: 'user_002',
            username: 'student2',
            email: 'student2@example.com',
            role: 'user',
            permissions: ['read:learning', 'write:progress'],
            created_at: '2026-02-20T14:30:00Z',
            is_active: true,
          },
          {
            id: 'admin_001',
            username: 'admin',
            email: 'admin@example.com',
            role: 'admin',
            permissions: ['read:all', 'write:all', 'manage:users', 'manage:experiments'],
            created_at: '2026-01-01T08:00:00Z',
            is_active: true,
          },
        ])
      case 'detail':
        if (!userId) {
          return NextResponse.json({ error: 'userId is required' }, { status: 400 })
        }
        return NextResponse.json({
          id: userId,
          username: 'student1',
          email: 'student1@example.com',
          role: 'user',
          permissions: ['read:learning', 'write:progress'],
          created_at: '2026-01-15T10:00:00Z',
          is_active: true,
          last_login: new Date().toISOString(),
        })
      default:
        return NextResponse.json({ error: 'Invalid action' }, { status: 400 })
    }
  } catch (error) {
    console.error('Users API error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

export async function POST(request: NextRequest) {
  const blocked = blockInProd()
  if (blocked) return blocked
  try {
    const body = await request.json()
    const { username, email, role, permissions } = body

    if (!username || !email) {
      return NextResponse.json({ error: 'Missing required fields' }, { status: 400 })
    }

    // In production, this would create a new user
    return NextResponse.json({
      id: `user_${Date.now()}`,
      username,
      email,
      role: role || 'user',
      permissions: permissions || ['read:learning'],
      created_at: new Date().toISOString(),
      is_active: true,
    })
  } catch (error) {
    console.error('Users API error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
