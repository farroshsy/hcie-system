'use client'

import { useCallback, useEffect, useState } from 'react'
import Link from 'next/link'
import { useAuth } from '@/contexts/auth_context'
import { getBackendUrl } from '@/lib/api/backend-url'
import { useT } from '@/contexts/language_context'

const BACKEND = getBackendUrl()

interface ObsTile {
  id: string
  label: string
  url: string
  healthy: boolean
  health_detail: string
}

function getAuthHeaders(): Record<string, string> {
  if (typeof window === 'undefined') return {}
  const t = localStorage.getItem('access_token') || localStorage.getItem('hcie_auth_token')
  return t ? { Authorization: `Bearer ${t}` } : {}
}

export default function ObservabilityHubPage() {
  const t = useT()
  const { user, isAuthenticated, isLoading } = useAuth()
  const role = String((user as any)?.role || '')
  const allowed = ['researcher', 'admin'].includes(role)

  const [tiles, setTiles] = useState<ObsTile[]>([])
  const [loading, setLoading] = useState(true)
  const [healthyCount, setHealthyCount] = useState(0)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch(`${BACKEND}/v3/frontend/dashboard/observability-health`, {
        headers: getAuthHeaders(),
        signal: AbortSignal.timeout(12000),
      })
      if (res.ok) {
        const j = await res.json()
        setTiles(j.tiles ?? [])
        setHealthyCount(j.healthy_count ?? 0)
      }
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { if (isAuthenticated) load() }, [isAuthenticated, load])

  if (isLoading) return <Shell><p>{t('common.loading', 'Loading…')}</p></Shell>
  if (!isAuthenticated || !allowed) {
    return (
      <Shell>
        <div style={warnBox}>
          {t('observability.restricted', 'Researcher or admin role required to view the observability hub.')}
        </div>
      </Shell>
    )
  }

  return (
    <Shell>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 16 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 800, margin: 0, color: '#1A2332' }}>
            {t('observability.title', 'Observability Hub')}
          </h1>
          <p style={{ fontSize: 13, color: '#718096', margin: '6px 0 0' }}>
            {t('observability.subtitle', 'Operational stack for demos and thesis defense — event spine, metrics, logs.')}
          </p>
        </div>
        <button type="button" onClick={load} style={refreshBtn}>
          {loading ? '…' : '↻ Refresh health'}
        </button>
      </div>

      <div style={{ fontSize: 13, color: '#4A5568', marginBottom: 16 }}>
        {healthyCount} / {tiles.length} services healthy
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
        gap: 14,
      }}>
        {tiles.map(tile => (
          <div key={tile.id} style={{
            background: '#fff',
            border: `1px solid ${tile.healthy ? '#A9DFBF' : '#F5B7B1'}`,
            borderTop: `3px solid ${tile.healthy ? '#1e7d4a' : '#C0392B'}`,
            borderRadius: 10,
            padding: '16px 18px',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <strong style={{ fontSize: 15, color: '#2C3E50' }}>{tile.label}</strong>
              <span style={{
                fontSize: 10, fontWeight: 700, padding: '2px 8px', borderRadius: 999,
                background: tile.healthy ? '#E8F8EF' : '#FDEDEC',
                color: tile.healthy ? '#1e7d4a' : '#C0392B',
              }}>
                {tile.healthy ? 'UP' : 'DOWN'}
              </span>
            </div>
            <div style={{ fontSize: 11, color: '#A0AEC0', marginTop: 6, fontFamily: 'monospace' }}>
              {tile.health_detail || '—'}
            </div>
            <a href={tile.url} target="_blank" rel="noopener noreferrer"
               style={{
                 display: 'inline-block', marginTop: 12, padding: '6px 14px',
                 background: '#6C3483', color: '#fff', borderRadius: 6,
                 fontSize: 12, fontWeight: 700, textDecoration: 'none',
               }}>
              Open →
            </a>
          </div>
        ))}
      </div>

      <div style={{ ...card, marginTop: 20 }}>
        <strong style={{ color: '#6C3483' }}>{t('observability.thesis_map', 'Thesis claim → tool')}</strong>
        <ul style={{ fontSize: 13, color: '#4A5568', lineHeight: 1.8, marginTop: 8, paddingLeft: 20 }}>
          <li><strong>Contribution A</strong> (event spine) → Kafka UI + <Link href="/dashboard/replay-verify">Replay Verify</Link></li>
          <li><strong>Contribution B</strong> (bandit regret) → <Link href="/dashboard/cohorts">Cohort Study</Link> regret chart</li>
          <li><strong>Contribution C</strong> (JT governance) → Grafana JT histogram + <Link href="/dashboard/learner-journey/99e34a5c-8b88-45ab-a3e5-257f51402ffe">Learner Journey</Link></li>
          <li><strong>Live debugging</strong> → Dozzle (container logs during autopilot runs)</li>
        </ul>
      </div>
    </Shell>
  )
}

function Shell({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: '24px 20px' }}>
      <Link href="/dashboard/instructor" style={{ fontSize: 13, fontWeight: 600, color: '#6C3483', textDecoration: 'none' }}>
        ← Dashboard
      </Link>
      <div style={{ marginTop: 12 }}>{children}</div>
    </div>
  )
}

const card: React.CSSProperties = {
  background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10, padding: '16px 18px',
}
const warnBox: React.CSSProperties = {
  background: '#FEF9E7', border: '1px solid #F9E79F', borderRadius: 8, padding: 16, color: '#9A7D0A',
}
const refreshBtn: React.CSSProperties = {
  padding: '6px 12px', fontSize: 12, fontWeight: 600, background: '#EDF2F7',
  border: '1px solid #CBD5E0', borderRadius: 6, cursor: 'pointer',
}
