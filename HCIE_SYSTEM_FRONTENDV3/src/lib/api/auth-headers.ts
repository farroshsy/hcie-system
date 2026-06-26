/**
 * Single source of truth for the client-side auth header.
 *
 * Token precedence is fixed here so every dashboard page agrees: the app
 * persists the access token under `hcie_auth_token` (auth_context.persistAccessToken)
 * and mirrors it to `access_token` for backwards-compat. Reading them in a
 * consistent order avoids the class of bug where a page reads only one key and
 * silently makes unauthenticated requests (e.g. the old learner-journey page).
 *
 * NOTE: tokens currently live in localStorage (XSS-readable). Migrating to an
 * httpOnly cookie issued by the backend is tracked separately — it is a
 * backend-coupled change and must not be done piecemeal on the client.
 */

const TOKEN_KEYS = ['hcie_auth_token', 'access_token'] as const

/** Return the stored access token, or '' on the server / when logged out. */
export function getAccessToken(): string {
  if (typeof window === 'undefined') return ''
  for (const k of TOKEN_KEYS) {
    const v = localStorage.getItem(k)
    if (v) return v
  }
  return ''
}

/**
 * Auth headers for fetch(). Pass `json: false` for GETs that don't need a
 * Content-Type (avoids triggering needless CORS preflights on simple requests).
 */
export function authHeaders(opts: { json?: boolean } = {}): Record<string, string> {
  const { json = true } = opts
  const token = getAccessToken()
  const headers: Record<string, string> = {}
  if (json) headers['Content-Type'] = 'application/json'
  if (token) headers.Authorization = `Bearer ${token}`
  return headers
}
