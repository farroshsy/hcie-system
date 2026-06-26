/**
 * 500 Error Page
 * 
 * Custom error page for the HCIE application.
 * Uses Next.js App Router's error.tsx convention.
 */

'use client'

import { useEffect } from 'react'

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    console.error(error)
  }, [error])

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-6xl font-bold text-gray-900 mb-4">500</h1>
        <p className="text-xl text-gray-600 mb-4">Something went wrong</p>
        <p className="text-gray-500 mb-8">{error.message}</p>
        <button
          onClick={reset}
          className="bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition"
        >
          Try again
        </button>
      </div>
    </div>
  )
}
