/**
 * Shared fetch auth-header builder.
 *
 * Reads the access token from localStorage and returns the request headers. This
 * consolidates the identical copies that were inlined across dashboard pages
 * (instructor, learner, governance), learn, and evidence (see
 * 00_documentation/09_adr/ARCHITECTURE_DECISIONS.md, ADR-3, F3).
 *
 * NOTE: this intentionally does NOT touch token *refresh*. Refresh lives in
 * `src/contexts/auth_context.tsx` (key `hcie_refresh_token`) and must not be merged
 * here — see ADR-3 for why consolidating refresh is unsafe.
 */
export function getAuthHeaders(): HeadersInit {
  const token =
    (typeof window !== 'undefined' &&
      (localStorage.getItem('hcie_auth_token') || localStorage.getItem('access_token'))) ||
    ''
  return token
    ? { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }
    : { 'Content-Type': 'application/json' }
}
