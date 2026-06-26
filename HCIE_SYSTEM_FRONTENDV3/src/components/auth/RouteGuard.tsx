'use client'

/**
 * RouteGuard — one central place that enforces the route→role table from
 * `@/lib/auth/roles`. Mounted once inside <Providers> so every route passes
 * through it. It only redirects AUTHENTICATED users who lack the required role
 * (a student wandering into /dashboard/audit goes back to /learn). Logged-out
 * users are left to each page's own auth handling (many demo pages render on
 * open endpoints / fall back to mock), since roles here are a UX layer, not a
 * security boundary.
 */

import { useEffect } from 'react'
import { usePathname, useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/auth_context'
import { roleOf, requiredRoleFor, canAccessRoute, homeFor } from '@/lib/auth/roles'

export function RouteGuard({ children }: { children: React.ReactNode }) {
  const pathname = usePathname() || '/'
  const router = useRouter()
  const { user, isAuthenticated, isLoading } = useAuth()

  useEffect(() => {
    if (isLoading) return
    const req = requiredRoleFor(pathname)
    if (req === null) return        // public route
    if (!isAuthenticated) return    // let the page handle its own auth/mock
    const role = roleOf(user as { role?: string | null; email?: string | null } | null)
    if (!canAccessRoute(pathname, role)) {
      router.replace(homeFor(role))
    }
  }, [pathname, isAuthenticated, isLoading, user, router])

  return <>{children}</>
}
