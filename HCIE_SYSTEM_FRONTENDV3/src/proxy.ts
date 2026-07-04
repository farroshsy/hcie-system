/**
 * Proxy
 * 
 * Next.js proxy for authentication, security, and internationalization.
 * Handles route protection, rate limiting, security headers, and locale routing.
 */

import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// i18n configuration
const locales = ['en', 'id'] as const
const defaultLocale = 'en'

// Simple in-memory rate limiting (for production, use Redis)
const rateLimit = new Map<string, { count: number; resetTime: number }>()
const RATE_LIMIT = 100 // requests per minute
const RATE_LIMIT_WINDOW = 60 * 1000 // 1 minute

// Development mode: higher rate limit or disabled
const isDevelopment = process.env.NODE_ENV === 'development'
const DEV_RATE_LIMIT = 1000 // higher limit for development

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl
  const ip = request.headers.get('x-forwarded-for') || request.headers.get('x-real-ip') || 'unknown'

  // i18n locale detection and routing (disabled for now - needs app restructuring)
  // const pathnameIsMissingLocale = locales.every(
  //   (locale) => !pathname.startsWith(`/${locale}/`) && pathname !== `/${locale}`
  // )

  // // Redirect if there is no locale
  // if (pathnameIsMissingLocale) {
  //   const locale = defaultLocale
  //   return NextResponse.redirect(
  //     new URL(`/${locale}${pathname}`, request.url)
  //   )
  // }

  // Rate limiting
  const now = Date.now()
  const userLimit = rateLimit.get(ip)
  const currentRateLimit = isDevelopment ? DEV_RATE_LIMIT : RATE_LIMIT
  
  if (userLimit) {
    if (now > userLimit.resetTime) {
      // Reset window
      rateLimit.set(ip, { count: 1, resetTime: now + RATE_LIMIT_WINDOW })
    } else if (userLimit.count >= currentRateLimit) {
      return new NextResponse('Too Many Requests', { status: 429 })
    } else {
      userLimit.count++
    }
  } else {
    rateLimit.set(ip, { count: 1, resetTime: now + RATE_LIMIT_WINDOW })
  }

  // Paths that require authentication.
  // Token written to cookie hcie_auth_token by auth_service.ts on login.
  const AUTH_REQUIRED = [
    '/admin', '/dashboard', '/learn', '/learning',
    '/progress', '/profile', '/settings', '/concepts',
    '/tasks', '/replay', '/experiments', '/evidence',
  ]
  const needsAuth = AUTH_REQUIRED.some(p => pathname === p || pathname.startsWith(p + '/'))

  // Block dev-only tools in production
  const DEV_ONLY = ['/dev-bypass', '/backend-connection', '/cold-start']
  if (DEV_ONLY.includes(pathname) && !isDevelopment) {
    return NextResponse.redirect(new URL('/', request.url))
  }

  if (needsAuth) {
    const token = request.cookies.get('hcie_auth_token') ?? request.cookies.get('auth_token')
    const devBypass = request.cookies.get('dev_bypass')
    const isDevBypassEnabled = devBypass?.value === 'true' && isDevelopment

    if (!token && !isDevBypassEnabled) {
      const loginUrl = new URL('/login', request.url)
      loginUrl.searchParams.set('from', pathname)
      return NextResponse.redirect(loginUrl)
    }
  }

  // Add security headers to response
  const response = NextResponse.next()
  response.headers.set('X-Content-Type-Options', 'nosniff')
  response.headers.set('X-Frame-Options', 'DENY')
  response.headers.set('X-XSS-Protection', '1; mode=block')
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin')

  return response
}

export const config = {
  matcher: ['/((?!api|_next|_vercel|.*\\..*).*)']
}
