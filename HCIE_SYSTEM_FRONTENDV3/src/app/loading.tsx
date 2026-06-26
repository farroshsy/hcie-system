/**
 * Loading Page
 * 
 * Global loading state for the application.
 * Uses Next.js App Router loading.tsx convention.
 */

export default function Loading() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p className="text-gray-600">Loading...</p>
      </div>
    </div>
  )
}
