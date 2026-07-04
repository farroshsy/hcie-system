const backendUrl = (process.env.NEXT_PUBLIC_BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8011')
  .replace(/\/+$/, '')
  .replace(/\/v3$/i, '')

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  // Skip TS/ESLint *inside the Docker build* — the full type-check pass during
  // `next build` OOMs Docker Desktop's BuildKit on this machine. Type safety is
  // instead enforced out-of-band via `npm run type-check` (tsc --noEmit), which
  // is currently green (0 errors) and should be wired into CI as a gate before
  // deploy. Do NOT rely on the Docker build to catch type/lint errors.
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  experimental: {
    serverActions: {
      bodySizeLimit: '2mb',
    },
  },
  env: {
    NEXT_PUBLIC_API_URL: backendUrl,
    NEXT_PUBLIC_BACKEND_URL: backendUrl,
    NEXT_PUBLIC_WS_URL: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8011',
    NEXT_PUBLIC_SENTRY_DSN: process.env.NEXT_PUBLIC_SENTRY_DSN || '',
  },
  // Dev-only same-origin proxy. In the browser getBackendUrl() returns
  // window.location.origin, so the page calls <dev-origin>/v3/* . Under `next dev`
  // there is no gateway in front, so forward /v3/* to the backend API. Gated to
  // development: in production the gateway serves frontend+API same-origin and
  // routes /v3 to the API directly, so this never runs and prod is unchanged.
  // Only /v3/* is proxied — /api/* stays local (native route: app/api/health).
  async rewrites() {
    if (process.env.NODE_ENV === 'production') return []
    return [
      { source: '/v3/:path*', destination: `${backendUrl}/v3/:path*` },
    ]
  },
  // Security headers for production
  async headers() {
    const cspHeader = `
      default-src 'self';
      script-src 'self' 'unsafe-eval' 'unsafe-inline' https://cdn.jsdelivr.net https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/;
      style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net;
      img-src 'self' data: https: blob:;
      font-src 'self' data: https://cdn.jsdelivr.net;
      object-src 'none';
      base-uri 'self';
      form-action 'self';
      frame-ancestors 'none';
      upgrade-insecure-requests;
      connect-src 'self' ${backendUrl} ${process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8011'};
    `
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on'
          },
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=63072000; includeSubDomains; preload'
          },
          {
            key: 'X-Frame-Options',
            value: 'SAMEORIGIN'
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff'
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block'
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin'
          },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(), geolocation=()'
          },
          {
            key: 'Content-Security-Policy',
            value: cspHeader.replace(/\s{2,}/g, ' ').trim()
          }
        ]
      }
    ]
  }
}

module.exports = nextConfig
