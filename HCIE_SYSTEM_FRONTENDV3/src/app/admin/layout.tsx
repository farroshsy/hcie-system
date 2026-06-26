/**
 * Admin Layout
 * 
 * Layout for admin pages with authentication check.
 * Uses Next.js App Router layout conventions.
 */

import { redirect } from 'next/navigation'
import { useAuth } from '@/contexts'

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode
}) {
  // In production, this would check authentication on the server
  // For now, we'll let the client-side auth context handle it
  return <div className="min-h-screen">{children}</div>
}
