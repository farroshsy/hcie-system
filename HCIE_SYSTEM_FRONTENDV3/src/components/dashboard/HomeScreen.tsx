/**
 * Dashboard Home — "What to do next"
 *
 * Single purpose: surface the learner's real state + one clear CTA.
 * Data: /v3/frontend/dashboard/session-trace (real session stats)
 *       /v3/learner/recommend (next task hint)
 * No mock data, no WS dependency, no fake numbers.
 */

'use client'

import { useEffect, useState, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts'
import { useT } from '@/contexts/language_context'
import { getBackendUrl } from '@/lib/api/backend-url'

interface SessionStats {
  total_interactions: number
  cumulative_mastery_gain: number
  accuracy: number | null
  unique_concepts: number
  transfer_events: number
}

interface NextTask {
  task_id: string
  concept_id: string
  policy_type: string
  cold_start: boolean
}

export default function HomeScreen() {
  const t = useT()
  const { user } = useAuth()
  const router = useRouter()
  const [stats, setStats] = useState<SessionStats | null>(null)
  const [next, setNext] = useState<NextTask | null>(null)
  const [loading, setLoading] = useState(true)
  const hasFetched = useRef(false)

  useEffect(() => {
    if (!user || hasFetched.current) return
    hasFetched.current = true
    fetchData()
  }, [user])

  const fetchData = async () => {
    const token = localStorage.getItem('hcie_auth_token') || localStorage.getItem('access_token') || ''
    const headers: HeadersInit = token ? { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' } : { 'Content-Type': 'application/json' }
    const base = getBackendUrl()
    const uid = user?.id

    await Promise.allSettled([
      // Session stats from trajectory_records
      (async () => {
        if (!uid) return
        const r = await fetch(`${base}/v3/frontend/dashboard/session-trace/${uid}?limit=500`, { headers, signal: AbortSignal.timeout(5000) })
        if (!r.ok) return
        const d = await r.json()
        const s = d.session_summary ?? {}
        setStats({
          total_interactions: Number(s.total_interactions ?? 0),
          cumulative_mastery_gain: Number(s.cumulative_mastery_gain ?? 0),
          accuracy: s.accuracy != null ? Number(s.accuracy) : null,
          unique_concepts: Number(s.unique_concepts ?? 0),
          transfer_events: Number(s.transfer_events ?? 0),
        })
      })(),
      // Next task recommendation
      (async () => {
        const r = await fetch(`${base}/v3/learner/recommend`, { method: 'POST', headers, body: JSON.stringify({ concept_filter: null }), signal: AbortSignal.timeout(5000) })
        if (!r.ok) return
        const d = await r.json()
        if (d.task_id) {
          setNext({
            task_id: d.task_id,
            concept_id: d.concept_id ?? '',
            policy_type: d.selection_metrics?.policy_type ?? 'default',
            cold_start: d.cold_start?.active ?? false,
          })
        }
      })(),
    ])
    setLoading(false)
  }

  const conceptLabel = (id: string) =>
    id.replace(/_/g, ' ').replace(/^(k\d+)\s/, (_, g) => g.toUpperCase() + ' — ')

  return (
    <div className="max-w-3xl mx-auto px-4 py-10">

      {/* Greeting */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">
          {(() => {
            // Greeting name: only show a clean, name-like token. A raw handle / email-local
            // (e.g. "anyvalid", "user_12") reads like a bug, so fall back to no name.
            const raw = (user?.username || '').split('_')[0].split('@')[0]
            const nameLike = /^[A-Za-z][A-Za-z'’-]{1,}$/.test(raw) && !/\d/.test(raw)
            const name = nameLike ? ', ' + raw.charAt(0).toUpperCase() + raw.slice(1) : ''
            if (loading) return t('common.loading')
            return (stats && stats.total_interactions > 0 ? t('home.enterDashboard') : t('home.ctaLearner')) + name
          })()}
        </h1>
        {!loading && stats && stats.total_interactions > 0 && (
          <p className="text-gray-500 mt-1">
            {stats.total_interactions} {t('common.attempts')} · {stats.unique_concepts} {t('common.concepts')} · {
              stats.accuracy != null ? `${Math.round(stats.accuracy * 100)}% ${t('common.accuracy').toLowerCase()}` : ''
            }
          </p>
        )}
      </div>

      {/* Guided-review banner — points reviewers at the guided evidence path */}
      <a href="/review/start-here"
         className="block mb-6 rounded-xl border border-blue-200 bg-blue-50 px-5 py-4 hover:bg-blue-100 transition no-underline">
        <div className="flex items-center justify-between gap-3">
          <span className="text-sm font-medium text-blue-900">🔍 {t('home.guidedBanner')}</span>
          <span className="text-sm font-bold text-blue-700 whitespace-nowrap">{t('home.guidedBannerCta')} →</span>
        </div>
      </a>

      {/* Primary CTA */}
      <button
        onClick={() => router.push('/learn')}
        className="w-full bg-blue-600 hover:bg-blue-700 text-white text-lg font-semibold py-5 rounded-xl shadow-md transition mb-6"
      >
        🎓 {t('home.ctaLearner')}
      </button>

      {/* Next task hint */}
      {!loading && next && (
        <div className="bg-white border border-gray-200 rounded-xl p-5 mb-6 shadow-sm">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">{t('common.next')}</p>
          <p className="text-base font-semibold text-gray-800">{conceptLabel(next.concept_id)}</p>
          <p className="text-sm text-gray-500 mt-0.5">
            {next.cold_start ? t('coldStart.title') : `${t('common.policy')}: ${next.policy_type}`}
          </p>
        </div>
      )}

      {/* Stats row */}
      {!loading && stats && stats.total_interactions > 0 && (
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="bg-white border border-gray-200 rounded-xl p-4 text-center shadow-sm">
            <p className="text-2xl font-bold text-blue-600">{stats.total_interactions}</p>
            <p className="text-xs text-gray-500 mt-1">{t('common.attempts')}</p>
          </div>
          <div className="bg-white border border-gray-200 rounded-xl p-4 text-center shadow-sm">
            <p className="text-2xl font-bold text-green-600">
              {stats.cumulative_mastery_gain > 0
                ? `+${(stats.cumulative_mastery_gain * 100).toFixed(1)}%`
                : '—'}
            </p>
            <p className="text-xs text-gray-500 mt-1">{t('common.mastery')}</p>
          </div>
          <div className="bg-white border border-gray-200 rounded-xl p-4 text-center shadow-sm">
            <p className="text-2xl font-bold text-purple-600">
              {stats.accuracy != null ? `${Math.round(stats.accuracy * 100)}%` : '—'}
            </p>
            <p className="text-xs text-gray-500 mt-1">{t('common.accuracy')}</p>
          </div>
        </div>
      )}

      {/* Secondary links */}
      <div className="flex gap-3">
        <button
          onClick={() => router.push('/dashboard/learner')}
          className="flex-1 bg-white border border-gray-200 hover:border-blue-300 text-gray-700 text-sm font-medium py-3 rounded-xl shadow-sm transition"
        >
          📊 {t('nav.myProgress')}
        </button>
        <a
          href="/review"
          className="flex-1 bg-white border border-gray-200 hover:border-gray-300 text-gray-500 text-sm font-medium py-3 rounded-xl shadow-sm transition text-center"
          target="_blank"
          rel="noopener noreferrer"
        >
          📄 {t('nav.review')}
        </a>
      </div>
    </div>
  )
}
