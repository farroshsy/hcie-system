/**
 * Global Error Boundary
 *
 * Catches errors in the entire app and displays a fallback UI.
 * This is the error boundary for the root layout.
 */

'use client'

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <html>
      <body>
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <div className="text-center max-w-md px-4">
            <h1 className="text-6xl font-bold text-red-600 mb-4">500</h1>
            <h2 className="text-2xl font-semibold text-gray-900 mb-2">Application Error</h2>
            <p className="text-gray-600 mb-6">
              Something went wrong. The application encountered an unexpected error.
            </p>
            {process.env.NODE_ENV === 'development' && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 text-left">
                <p className="text-sm font-mono text-red-800">{error.message}</p>
              </div>
            )}
            <button
              onClick={reset}
              className="bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition"
            >
              Try again
            </button>
          </div>
        </div>
      </body>
    </html>
  )
}
