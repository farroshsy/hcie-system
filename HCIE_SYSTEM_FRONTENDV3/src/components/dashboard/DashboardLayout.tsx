/**
 * Dashboard Layout
 *
 * Thin layout: renders the nav + the page content passed as children.
 * Routing is handled by Next.js App Router, not a useState switch.
 */

'use client'

import { Navigation } from './Navigation'

export function DashboardLayout({ children }: { children?: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      {children}
    </div>
  )
}
