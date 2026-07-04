'use client'

/**
 * /experiments → redirect to the new Cohort Study page.
 * The old standalone experiments CRUD was a redundant duplicate of the
 * cohort-run tooling. Single source of truth is now /dashboard/cohorts.
 */

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useT } from '@/contexts/language_context'

export default function ExperimentsPage() {
  const t = useT()
  const router = useRouter()
  useEffect(() => { router.replace('/dashboard/cohorts') }, [router])
  return (
    <div className="flex items-center justify-center min-h-screen">
      <p className="text-gray-400 text-sm">{t('common.loading')} → {t('nav.cohortStudy')}</p>
    </div>
  )
}
