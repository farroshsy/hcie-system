import { DashboardLayout } from '@/components/dashboard'

export default function LearnLayout({ children }: { children: React.ReactNode }) {
  return (
    <DashboardLayout>
      <div className="min-h-screen bg-slate-50">{children}</div>
    </DashboardLayout>
  )
}
