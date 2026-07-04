/**
 * Dashboard Layout
 *
 * Layout for dashboard pages with consistent navigation and structure.
 * Uses Next.js App Router layout conventions.
 */

import { DashboardLayout as NavLayout } from '@/components/dashboard'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <NavLayout>
      {children}
    </NavLayout>
  )
}
