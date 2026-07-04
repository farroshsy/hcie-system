const DEFAULT_BACKEND_URL = 'http://localhost:8011'

export function normalizeBackendUrl(value?: string | null): string {
  const raw = (value || DEFAULT_BACKEND_URL).trim()
  return raw.replace(/\/+$/, '').replace(/\/v3$/i, '')
}

export function getBackendUrl(): string {
  // Browser: call the SAME ORIGIN the page was served from. This is URL-agnostic —
  // it works identically at http://localhost and through any tunnel/proxy
  // (e.g. https://xxx.trycloudflare.com), because the gateway serves the frontend
  // AND routes /v3 and /api to the API on that same host. No baked-in host, no
  // mixed-content (https page → https API), no localhost-resolves-to-client bug.
  if (typeof window !== 'undefined' && window.location?.origin) {
    return normalizeBackendUrl(window.location.origin)
  }
  // Server-side render / build: use the configured internal URL.
  return normalizeBackendUrl(
    process.env.NEXT_PUBLIC_BACKEND_URL ||
      process.env.NEXT_PUBLIC_API_URL ||
      DEFAULT_BACKEND_URL,
  )
}

/**
 * Same-origin WebSocket base URL. In the browser, derives ws/wss + host from the
 * current page origin (so it is secure under an HTTPS tunnel). Falls back to the
 * configured env only during SSR/build.
 */
export function getWsUrl(path = ''): string {
  const suffix = path && !path.startsWith('/') ? `/${path}` : path
  if (typeof window !== 'undefined' && window.location?.host) {
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${proto}//${window.location.host}${suffix}`
  }
  const env = (process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8011').replace(/\/+$/, '')
  return `${env}${suffix}`
}

export function buildApiUrl(baseUrl: string | undefined | null, path: string): string {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  return `${normalizeBackendUrl(baseUrl)}${normalizedPath}`
}

export function getV3ApiUrl(): string {
  return `${getBackendUrl()}/v3`
}
