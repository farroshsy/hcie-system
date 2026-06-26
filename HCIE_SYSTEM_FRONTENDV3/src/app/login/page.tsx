'use client'

import { useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { useAuth } from '@/contexts/auth_context'
import { useT } from '@/contexts/language_context'
import { roleOf, homeFor } from '@/lib/auth/roles'
import { Activity } from 'lucide-react'

export const dynamic = 'force-dynamic'

// Pull a human message out of whatever shape the error arrives in.
function readableError(err: any, t: (k: string, fb?: string) => string): string {
  // auth_service throws plain Error('Login failed'); the API body is
  // {error:{message:"Invalid credentials"}}. Cover both + network failures.
  const msg = err?.message ?? ''
  if (/invalid cred/i.test(msg) || err?.status === 401) return t('auth.errInvalidCreds')
  if (/failed to fetch|networkerror|timeout|aborted/i.test(msg)) return t('auth.errNetwork')
  if (/login failed/i.test(msg)) return t('auth.errInvalidCreds')
  return msg || t('auth.errNetwork')
}

export default function LoginPage() {
  const t = useT()
  const router = useRouter()
  const searchParams = useSearchParams()
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // If middleware bounced us here because a session expired, say so.
  const cameFrom = searchParams.get('from')
  const sessionExpired = !!cameFrom

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      await login({ email, password })
      // Cookie + token persistence now happens inside auth_context.login().
      // Land each role on its home (student→/learn, researcher→/dashboard, admin→/infrastructure).
      let dest = cameFrom
      if (!dest) {
        try {
          const snap = JSON.parse(localStorage.getItem('hcie_user_snapshot') || 'null')
          dest = homeFor(roleOf(snap))
        } catch { dest = '/dashboard' }
      }
      router.push(dest)
    } catch (err: any) {
      setError(readableError(err, t))
    } finally {
      setLoading(false)
    }
  }

  const inputCls = 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white rounded-lg shadow-lg p-8">
        <div className="text-center mb-6">
          <div className="flex justify-center mb-4">
            <Activity className="w-12 h-12 text-blue-600" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">{t('auth.loginTitle')}</h1>
          <p className="text-gray-600 mt-2">{t('home.tagline')}</p>
        </div>

        {sessionExpired && (
          <div className="bg-amber-50 border border-amber-200 rounded-md p-3 text-amber-800 text-sm mb-4">
            {t('auth.errInvalidCreds')}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm font-medium mb-1">{t('auth.email')}</label>
            <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)}
              className={inputCls} placeholder="you@example.com" required autoComplete="email" />
          </div>
          <div>
            <label htmlFor="password" className="block text-sm font-medium mb-1">{t('auth.password')}</label>
            <input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)}
              className={inputCls} required autoComplete="current-password" />
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-3 text-red-800 text-sm">
              {error}
            </div>
          )}

          <button type="submit" disabled={loading}
            className="w-full bg-blue-600 text-white py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed">
            {loading ? `${t('common.loading')}` : t('auth.submitLogin')}
          </button>
        </form>

        <div className="mt-6 pt-4 border-t border-gray-100 text-center text-sm text-gray-500">
          {t('auth.noAccount')}{' '}
          <Link href="/register" className="text-blue-600 font-medium hover:underline">{t('auth.submitRegister')}</Link>
        </div>
      </div>
    </div>
  )
}
