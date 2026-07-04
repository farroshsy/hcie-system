/**
 * Authentication Context Provider
 * 
 * Manages authentication state and provides auth utilities to the application.
 * Handles login, logout, token management, and user session.
 */

'use client'

import { createContext, useContext, useState, useEffect, type ReactNode } from 'react'
import { useServices } from './service_context'
import { getConfig } from '@/config'
import { getBackendUrl } from '@/lib/api/backend-url'
import type { User, AuthResponse, LoginCredentials, RegistrationData } from '@/lib/core'

// The cookie is the SERVER-SIDE middleware gate; it must outlive the 1h access
// token, or the middleware hard-bounces to /login before client-side refresh can
// run. We give it the REFRESH token's lifetime (7 days) so the middleware lets
// the request through, and client-side loadUser() renews the access token as
// needed. This is the real session-persistence fix.
const COOKIE_MAX_AGE_SEC = 7 * 24 * 3600  // match refresh-token (7d)
function persistAccessToken(token: string, _expiresInSec = 3600) {
  if (typeof window === 'undefined' || !token) return
  localStorage.setItem('hcie_auth_token', token)
  localStorage.setItem('access_token', token)
  document.cookie = `hcie_auth_token=${token}; path=/; max-age=${COOKIE_MAX_AGE_SEC}; SameSite=Lax`
}

// Try to mint a fresh access token from the stored refresh token. Returns the
// new token or null. This is what keeps sessions alive past the 1h access-token
// expiry — the API exposes /v3/auth/refresh taking {refresh_token} in the body.
async function tryRefreshAccessToken(): Promise<string | null> {
  if (typeof window === 'undefined') return null
  const refresh = localStorage.getItem('hcie_refresh_token')
  if (!refresh) return null
  try {
    const r = await fetch(`${getBackendUrl()}/v3/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refresh }),
      signal: AbortSignal.timeout(6000),
    })
    if (!r.ok) return null
    const d = await r.json()
    if (d.access_token) {
      persistAccessToken(d.access_token, d.expires_in ?? 3600)
      if (d.refresh_token) localStorage.setItem('hcie_refresh_token', d.refresh_token)
      return d.access_token
    }
  } catch { /* fall through */ }
  return null
}

function clearAuthStorage() {
  if (typeof window === 'undefined') return
  for (const k of ['hcie_auth_token', 'access_token', 'hcie_token', 'hcie_refresh_token', 'hcie_user_snapshot', 'hcie_user']) {
    localStorage.removeItem(k)
  }
  document.cookie = 'hcie_auth_token=; path=/; max-age=0'
}

/**
 * Auth context interface
 */
interface AuthContextValue {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (credentials: LoginCredentials) => Promise<void>
  register: (data: RegistrationData) => Promise<void>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
}

/**
 * Auth context
 */
const AuthContext = createContext<AuthContextValue | null>(null)

/**
 * Auth context provider props
 */
interface AuthProviderProps {
  children: ReactNode
}

/**
 * Auth context provider component
 */
export function AuthProvider({ children }: AuthProviderProps) {
  const services = useServices()
  const config = getConfig()
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Load user on mount
  useEffect(() => {
    loadUser()
  }, [])

  const loadUser = async () => {
    try {
      const token = localStorage.getItem('hcie_auth_token') || localStorage.getItem(config.auth.tokenStorageKey)
      if (!token) { setIsLoading(false); return }

      // Re-sync the middleware cookie from the stored token on every load — the
      // cookie expires independently (and was the source of the "logged in but
      // bounced to /login" half-dead state). If we still hold a token, restore it.
      persistAccessToken(token, 3600)

      try {
        const userData = await services.auth.getProfile()
        setUser(userData)
      } catch {
        // Access token likely expired → try the refresh token before giving up.
        const fresh = await tryRefreshAccessToken()
        if (fresh) {
          try {
            const userData = await services.auth.getProfile()
            setUser(userData)
            setIsLoading(false)
            return
          } catch { /* refresh worked but profile still failed — fall to snapshot */ }
        }
        // Fall back to the stored snapshot so a transient backend blip doesn't log out.
        const stored = localStorage.getItem('hcie_user_snapshot')
        if (stored) {
          try { setUser(JSON.parse(stored)) }
          catch { clearAuthStorage() }
        } else {
          // No snapshot and refresh failed → session is genuinely dead. Clear the
          // half-dead state so the login page is consistent (cookie + storage agree).
          clearAuthStorage()
        }
      }
    } finally {
      setIsLoading(false)
    }
  }

  const login = async (credentials: LoginCredentials) => {
    const response: AuthResponse = await services.auth.login(credentials)
    // Normalise: API returns user_id, frontend expects id
    const user = response.user as any
    if (user && user.user_id && !user.id) {
      user.id = user.user_id
      user.username = user.username || user.email?.split('@')[0] || user.user_id
    }
    setUser(user)
    // Persist access token (+ cookie sync) and the REFRESH token so the session
    // can self-renew past the 1h access-token expiry. This is the core session fix.
    if (response.access_token) persistAccessToken(response.access_token, response.expires_in ?? 3600)
    if ((response as any).refresh_token) localStorage.setItem('hcie_refresh_token', (response as any).refresh_token)
    localStorage.setItem('hcie_user_snapshot', JSON.stringify(user))
  }

  const register = async (data: RegistrationData) => {
    const response: AuthResponse = await services.auth.register(data)
    setUser(response.user)
  }

  const logout = async () => {
    const refreshToken = localStorage.getItem(config.auth.refreshTokenStorageKey)
    if (refreshToken) {
      try { await services.auth.logout(refreshToken) } catch { /* ignore */ }
    }
    localStorage.removeItem('hcie_user_snapshot')
    // Clear middleware auth cookie
    document.cookie = 'hcie_auth_token=; path=/; max-age=0'
    setUser(null)
  }

  const refreshUser = async () => {
    const userData = await services.auth.getProfile()
    setUser(userData)
  }

  const value: AuthContextValue = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    register,
    logout,
    refreshUser,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

/**
 * Hook to use auth context
 */
export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
