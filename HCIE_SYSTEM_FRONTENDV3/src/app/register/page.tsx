'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useAuth } from '@/contexts/auth_context'
import { useT } from '@/contexts/language_context'
import { getBackendUrl } from '@/lib/api/backend-url'
import { Activity } from 'lucide-react'

export const dynamic = 'force-dynamic'

function readableError(err: any, t: (k: string, fb?: string) => string): string {
  const msg = err?.message ?? ''
  if (/already|exist|duplicate|409/i.test(msg) || err?.status === 409) return t('auth.errInvalidCreds')
  if (/failed to fetch|networkerror|timeout|aborted/i.test(msg)) return t('auth.errNetwork')
  return msg || t('auth.errNetwork')
}

export default function RegisterPage() {
  const t = useT()
  const router = useRouter()
  const { login } = useAuth()
  const ROLES = [
    { id: 'student',    label: t('auth.roleStudent'),    desc: t('learn.intro') },
    { id: 'researcher', label: t('auth.roleResearcher'), desc: t('research.eyebrow') },
  ]
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [role, setRole] = useState('student')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const pwOk = password.length >= 8
  const emailOk = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
  const canSubmit = emailOk && pwOk && displayName.trim().length > 0 && !loading

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!canSubmit) return
    setLoading(true); setError('')
    try {
      // Register, then immediately log in so the session (cookie + refresh) is set
      // up by the same path as a normal login.
      const r = await fetch(`${getBackendUrl()}/v3/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, role, display_name: displayName }),
        signal: AbortSignal.timeout(10000),
      })
      if (!r.ok) {
        const body = await r.json().catch(() => null)
        throw Object.assign(new Error(body?.error?.message || 'Registration failed'), { status: r.status })
      }
      await login({ email, password })
      router.push('/dashboard')
    } catch (err: any) {
      setError(readableError(err, t))
    } finally {
      setLoading(false)
    }
  }

  const tryDemo = async () => {
    setLoading(true); setError('')
    try {
      // Mint a throwaway demo student so a visitor can explore without thinking.
      const stamp = Math.floor(Math.random() * 1e9)
      const demoEmail = `demo_${stamp}@hcie.test`
      const r = await fetch(`${getBackendUrl()}/v3/auth/register`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: demoEmail, password: 'demo123456', role: 'student', display_name: 'Demo Learner' }),
        signal: AbortSignal.timeout(10000),
      })
      if (!r.ok) throw new Error('Could not create a demo account')
      await login({ email: demoEmail, password: 'demo123456' })
      router.push('/dashboard')
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
          <div className="flex justify-center mb-4"><Activity className="w-12 h-12 text-blue-600" /></div>
          <h1 className="text-2xl font-bold text-gray-900">{t('auth.registerTitle')}</h1>
          <p className="text-gray-600 mt-2">{t('auth.registerEyebrow')}</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">{t('auth.email')}</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
              className={inputCls} placeholder="you@example.com" required autoComplete="email" />
            <p className={`text-xs mt-1 ${email && !emailOk ? 'text-red-500' : 'text-gray-400'}`}>
              {email && !emailOk ? t('auth.errMissingFields') : ''}
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">{t('auth.password')}</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
              className={inputCls} required autoComplete="new-password" />
            <p className={`text-xs mt-1 ${password && !pwOk ? 'text-red-500' : 'text-gray-400'}`}>
              {password && !pwOk ? t('auth.errMissingFields') : ''}
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">{t('auth.username')}</label>
            <input type="text" value={displayName} onChange={(e) => setDisplayName(e.target.value)}
              className={inputCls} required />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">{t('auth.role')}</label>
            <div className="space-y-2">
              {ROLES.map(r => (
                <label key={r.id} className={`flex items-start gap-3 p-3 rounded-md border cursor-pointer transition ${
                  role === r.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'}`}>
                  <input type="radio" name="role" value={r.id} checked={role === r.id}
                    onChange={() => setRole(r.id)} className="mt-1" />
                  <div>
                    <div className="text-sm font-semibold text-gray-800">{r.label}</div>
                    <div className="text-xs text-gray-500">{r.desc}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-3 text-red-800 text-sm">{error}</div>
          )}

          <button type="submit" disabled={!canSubmit}
            className="w-full bg-blue-600 text-white py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed">
            {loading ? t('common.loading') : t('auth.submitRegister')}
          </button>
        </form>

        <div className="mt-4 text-center">
          <button onClick={tryDemo} disabled={loading}
            className="text-sm text-gray-500 hover:text-blue-600 hover:underline disabled:opacity-50">
            {t('home.ctaLearner')} →
          </button>
        </div>

        <div className="mt-6 pt-4 border-t border-gray-100 text-center text-sm text-gray-500">
          {t('auth.haveAccount')}{' '}
          <Link href="/login" className="text-blue-600 font-medium hover:underline">{t('auth.submitLogin')}</Link>
        </div>
      </div>
    </div>
  )
}
