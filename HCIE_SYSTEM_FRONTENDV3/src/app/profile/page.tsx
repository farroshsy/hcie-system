'use client'

/**
 * Profile page — real auth identity plus live learner progress.
 */

import { useEffect, useState } from 'react'
import { useAuth } from '@/contexts'
import { useT } from '@/contexts/language_context'
import { getBackendUrl } from '@/lib/api/backend-url'
import { conceptLabel } from '@/lib/catalog/k12-catalog'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

type LearnerProgress = {
  user_id: string
  concepts: Record<string, number>
  semantic_version: string
}

function authHeaders(): HeadersInit {
  const token = typeof window !== 'undefined'
    ? (localStorage.getItem('hcie_auth_token') || localStorage.getItem('access_token'))
    : null
  return token
    ? { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }
    : { 'Content-Type': 'application/json' }
}

function masteryColor(value: number) {
  if (value >= 0.7) return 'text-green-700 bg-green-50 border-green-200'
  if (value >= 0.4) return 'text-amber-700 bg-amber-50 border-amber-200'
  return 'text-red-700 bg-red-50 border-red-200'
}

export default function ProfilePage() {
  const t = useT()
  const { user, isLoading, logout } = useAuth()
  const router = useRouter()
  const [progress, setProgress] = useState<LearnerProgress | null>(null)
  const [progressError, setProgressError] = useState<string | null>(null)

  useEffect(() => {
    if (isLoading || !user) return

    let cancelled = false
    fetch(`${getBackendUrl()}/v3/learner/progress`, {
      headers: authHeaders(),
      signal: AbortSignal.timeout(6000),
    })
      .then(async response => {
        if (!response.ok) throw new Error(`Progress unavailable (${response.status})`)
        return response.json()
      })
      .then(data => {
        if (!cancelled) {
          setProgress(data)
          setProgressError(null)
        }
      })
      .catch(error => {
        if (!cancelled) setProgressError(error instanceof Error ? error.message : 'Progress unavailable')
      })

    return () => { cancelled = true }
  }, [isLoading, user])

  const handleLogout = async () => {
    await logout()
    router.push('/login')
  }

  if (isLoading) {
    return (
      <div className="max-w-xl mx-auto px-4 py-10">
        <p className="text-sm text-gray-500">{t('common.loading')}</p>
      </div>
    )
  }

  if (!user) {
    return (
      <div className="max-w-xl mx-auto px-4 py-10">
        <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
          <h1 className="text-lg font-bold text-gray-900 mb-2">{t('auth.loginEyebrow')}</h1>
          <p className="text-sm text-gray-500 mb-4">{t('auth.loginTitle')}</p>
          <Link href="/login" className="inline-flex bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition">
            {t('auth.submitLogin')}
          </Link>
        </div>
      </div>
    )
  }

  const initials = (user.email ?? user.username ?? '?').slice(0, 1).toUpperCase()
  const displayName = user.username ?? user.email?.split('@')[0] ?? 'Learner'
  const conceptEntries = Object.entries(progress?.concepts ?? {})
    .filter(([concept]) => concept && concept !== 'unknown')
    .sort((a, b) => Number(b[1]) - Number(a[1]))
  const mastered = conceptEntries.filter(([, value]) => Number(value) >= 0.7).length
  const avgMastery = conceptEntries.length
    ? conceptEntries.reduce((sum, [, value]) => sum + Number(value), 0) / conceptEntries.length
    : 0

  return (
    <div className="max-w-3xl mx-auto px-4 py-10">
      {/* Avatar + name */}
      <div className="flex items-center gap-4 mb-8">
        <div className="w-16 h-16 rounded-full bg-blue-600 flex items-center justify-center text-white text-2xl font-bold">
          {initials}
        </div>
        <div>
          <h1 className="text-xl font-bold text-gray-900">{displayName}</h1>
          <p className="text-sm text-gray-500">{user.email}</p>
          <span className="inline-block mt-1 px-2 py-0.5 text-xs font-semibold bg-blue-100 text-blue-700 rounded">
            {user.role ?? 'student'}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-8">
        <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
          <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">{t('common.concepts')}</p>
          <p className="text-2xl font-bold text-blue-700">{conceptEntries.length}</p>
        </div>
        <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
          <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">{t('instructor.bottlenecks.strongestTitle')}</p>
          <p className="text-2xl font-bold text-green-700">{mastered}</p>
        </div>
        <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
          <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">{t('common.mastery')}</p>
          <p className="text-2xl font-bold text-gray-900">{(avgMastery * 100).toFixed(0)}%</p>
        </div>
      </div>

      {/* Details */}
      <div className="bg-white border border-gray-200 rounded-xl divide-y divide-gray-100 mb-8 shadow-sm">
        <div className="px-5 py-4">
          <p className="text-xs text-gray-400 uppercase tracking-wide mb-0.5">{t('profile.email')}</p>
          <p className="text-sm text-gray-800">{user.email}</p>
        </div>
        <div className="px-5 py-4">
          <p className="text-xs text-gray-400 uppercase tracking-wide mb-0.5">{t('profile.account')}</p>
          <p className="text-sm text-green-600 font-medium">●</p>
        </div>
        <div className="px-5 py-4">
          <p className="text-xs text-gray-400 uppercase tracking-wide mb-0.5">{t('profile.role')}</p>
          <div className="flex gap-1.5 flex-wrap mt-1">
            {(user.permissions ?? ['read:learning', 'write:learning']).map((p: string) => (
              <span key={p} className="px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded">
                {p}
              </span>
            ))}
          </div>
        </div>
        <div className="px-5 py-4">
          <p className="text-xs text-gray-400 uppercase tracking-wide mb-0.5">{t('profile.authIdentity')}</p>
          <p className="text-xs text-gray-400 font-mono">{user.id}</p>
        </div>
      </div>

      <div className="bg-white border border-gray-200 rounded-xl p-5 mb-8 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <p className="text-xs text-gray-400 uppercase tracking-wide mb-0.5">{t('profile.learnerState')}</p>
            <h2 className="text-base font-semibold text-gray-900">{t('learner.mastery')}</h2>
          </div>
          <Link href="/learn/concepts" className="text-sm text-blue-700 hover:text-blue-800 font-medium">
            {t('nav.conceptMap')}
          </Link>
        </div>

        {progressError && (
          <div className="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-lg p-3">
            {progressError}
          </div>
        )}

        {!progressError && conceptEntries.length === 0 && (
          <div className="text-sm text-gray-500 bg-gray-50 border border-gray-200 rounded-lg p-4">
            {t('profile.noState')}
          </div>
        )}

        {conceptEntries.length > 0 && (
          <div className="space-y-2">
            {conceptEntries.slice(0, 8).map(([concept, value]) => (
              <div key={concept} className="flex items-center gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex justify-between text-xs mb-1">
                    <span className="font-medium text-gray-700 truncate">{conceptLabel(concept)}</span>
                    <span className="text-gray-500">{(Number(value) * 100).toFixed(0)}%</span>
                  </div>
                  <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div className="h-full bg-blue-600 rounded-full" style={{ width: `${Math.max(0, Math.min(1, Number(value))) * 100}%` }} />
                  </div>
                </div>
                <Link
                  href={`/learn?concept=${encodeURIComponent(concept)}`}
                  className={`shrink-0 text-xs font-semibold border rounded-md px-2 py-1 ${masteryColor(Number(value))}`}
                >
                  {t('nav.learn')}
                </Link>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex gap-3">
        <button
          onClick={() => router.push('/progress')}
          className="flex-1 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium py-3 rounded-xl transition"
        >
          {t('nav.progress')}
        </button>
        <button
          onClick={() => router.push('/learn')}
          className="flex-1 bg-white border border-blue-200 hover:border-blue-400 text-blue-700 text-sm font-medium py-3 rounded-xl transition"
        >
          {t('nav.learn')}
        </button>
        <button
          onClick={handleLogout}
          className="flex-1 bg-white border border-gray-200 hover:border-red-300 hover:text-red-600 text-gray-600 text-sm font-medium py-3 rounded-xl transition"
        >
          {t('profile.signOut')}
        </button>
      </div>
    </div>
  )
}
