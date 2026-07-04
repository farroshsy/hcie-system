'use client'

import { useCallback, useEffect, useState } from 'react'
import Link from 'next/link'
import { getBackendUrl } from '@/lib/api/backend-url'
import { useT } from '@/contexts/language_context'
import { NextSteps } from '@/components/review/NextSteps'

const BACKEND = getBackendUrl()

function getAuthHeaders(): Record<string, string> {
  if (typeof window === 'undefined') return {}
  const t = localStorage.getItem('access_token') || localStorage.getItem('hcie_auth_token')
  return t ? { Authorization: `Bearer ${t}` } : {}
}

export default function ReplayVerifyPage() {
  const t = useT()
  const [runId, setRunId] = useState('')
  const [runs, setRuns] = useState<any[]>([])
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [err, setErr] = useState<string | null>(null)

  useEffect(() => {
    fetch(`${BACKEND}/v3/frontend/dashboard/cohort-runs?group=synthetic&limit=12`, {
      headers: getAuthHeaders(),
    })
      .then(r => r.ok ? r.json() : null)
      .then(j => { if (j?.runs?.length) { setRuns(j.runs); setRunId(j.runs[0].run_id ?? '') } })
      .catch(() => {})
  }, [])

  const verify = useCallback(async () => {
    if (!runId.trim()) return
    setLoading(true)
    setErr(null)
    try {
      const res = await fetch(
        `${BACKEND}/v3/frontend/dashboard/replay-verify/${encodeURIComponent(runId.trim())}`,
        { headers: getAuthHeaders(), signal: AbortSignal.timeout(120000) },
      )
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      setData(await res.json())
    } catch (e: any) {
      setErr(String(e?.message ?? e))
    } finally {
      setLoading(false)
    }
  }, [runId])

  return (
    <div style={{ maxWidth: 960, margin: '0 auto', padding: '24px 20px' }}>
      <Link href="/dashboard/observability" style={{ fontSize: 13, fontWeight: 600, color: '#6C3483', textDecoration: 'none' }}>
        ← Observability
      </Link>
      <h1 style={{ fontSize: 22, fontWeight: 800, margin: '12px 0 4px', color: '#1A2332' }}>
        {t('replay.title', 'Deterministic Replay Verify')}
      </h1>
      <p style={{ fontSize: 13, color: '#718096', marginBottom: 20 }}>
        {t('replay.subtitle', 'Contribution A — prove stored trajectories replay with bounded divergence (< 0.01).')}
      </p>

      <div style={card}>
        <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 10 }}>Pick a cohort run</div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 10 }}>
          {runs.slice(0, 8).map((r: any) => (
            <button key={r.run_id} type="button" onClick={() => setRunId(r.run_id)} style={{
              padding: '4px 10px', fontSize: 11, borderRadius: 20, cursor: 'pointer',
              border: runId === r.run_id ? '2px solid #6C3483' : '1px solid #CBD5E0',
              background: runId === r.run_id ? '#F4ECF7' : '#fff',
            }}>
              {(r.reason || r.cohort_id || r.run_id || '').slice(0, 24)}
            </button>
          ))}
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <input value={runId} onChange={e => setRunId(e.target.value)}
                 placeholder="run-xxxxxxxx-…"
                 style={{ flex: 1, padding: '8px 10px', fontFamily: 'monospace', fontSize: 12, border: '1px solid #CBD5E0', borderRadius: 6 }} />
          <button type="button" onClick={verify} disabled={loading || !runId.trim()} style={{
            padding: '8px 18px', fontWeight: 700, background: loading ? '#CBD5E0' : '#6C3483',
            color: '#fff', border: 'none', borderRadius: 6, cursor: loading ? 'wait' : 'pointer',
          }}>
            {loading ? 'Replaying…' : 'Run verify'}
          </button>
        </div>
        {err && <div style={{ color: '#C0392B', fontSize: 12, marginTop: 10 }}>{err}</div>}
      </div>

      {data && (
        <>
          <div style={{
            ...card, marginTop: 16,
            borderColor: data.passed ? '#A9DFBF' : '#F5B7B1',
            background: data.passed ? '#E8F8EF' : '#FDEDEC',
          }}>
            <div style={{ fontSize: 18, fontWeight: 800, color: data.passed ? '#1e7d4a' : '#C0392B' }}>
              {data.passed ? '✓ PASSED' : '✗ NEEDS REVIEW'}
            </div>
            <div style={{ fontSize: 12, color: '#4A5568', marginTop: 6 }}>
              Run <code>{data.run_id}</code> · learner <code>{(data.user_id || '').slice(0, 8)}…</code> ·{' '}
              {data.rows_checked} rows ·{' '}
              <span style={{
                padding: '1px 8px', borderRadius: 10, fontSize: 11, fontWeight: 700,
                background: data.mode === 'full-replay' ? '#D6EAF8' : '#FEF9E7',
                color: data.mode === 'full-replay' ? '#21618C' : '#9A7D0A',
              }}>
                mode: {data.mode ?? 'unknown'}
              </span>
            </div>
            {data.replay_error && (
              <div style={{ fontSize: 11, color: '#922', marginTop: 6 }}>
                Full replay engine: {data.replay_error} — fell back to stored-audit (idempotency + fingerprint + bounded per-step delta).
              </div>
            )}
            <div style={{ fontSize: 11, color: '#718096', marginTop: 6, fontStyle: 'italic' }}>
              {data.divergence_summary?.interpretation}
            </div>
          </div>

          <div style={{ ...card, marginTop: 14 }}>
            <strong>Checks</strong>
            <table style={{ width: '100%', fontSize: 12, marginTop: 8, borderCollapse: 'collapse' }}>
              <tbody>
                <CheckRow label="Idempotency (no duplicate interaction_ids)" ok={data.idempotency?.passed} detail={`dupes=${data.idempotency?.duplicate_interaction_ids}`} />
                <CheckRow label="Manifest fingerprint consistent" ok={data.fingerprint_audit?.consistent} detail={`unique=${data.fingerprint_audit?.unique_fingerprints}`} />
                <CheckRow
                  label={data.mode === 'full-replay'
                    ? `Mean |orig − replay| mastery < ${data.divergence_summary?.threshold}`
                    : `Max per-step mastery delta < ${data.divergence_summary?.threshold} (stored-audit)`}
                  ok={data.divergence_summary?.within_bounds}
                  detail={data.mode === 'full-replay'
                    ? `mean=${data.divergence_summary?.mean}`
                    : `max=${data.divergence_summary?.max}`}
                />
              </tbody>
            </table>
          </div>

          {data.divergences?.length > 0 && (
            <div style={{ ...card, marginTop: 14, overflowX: 'auto' }}>
              <strong>Per-step {data.mode === 'full-replay' ? 'divergence' : 'mastery delta'} (sample)</strong>
              <div style={{ fontSize: 11, color: '#718096', marginTop: 2 }}>
                {data.mode === 'full-replay'
                  ? '|original_mastery − replayed_mastery| — must be ≈ 0 for deterministic replay.'
                  : 'When replay engine fails, we audit |mastery_after − mastery_before| per row to ensure no impossible jumps.'}
              </div>
              <table style={{ width: '100%', fontSize: 11, marginTop: 8, borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ textAlign: 'left', color: '#718096' }}>
                    <th style={{ padding: 4 }}>Step</th>
                    <th style={{ padding: 4 }}>Concept</th>
                    <th style={{ padding: 4 }}>Original mastery</th>
                    <th style={{ padding: 4 }}>Replay mastery</th>
                    <th style={{ padding: 4 }}>
                      {data.mode === 'full-replay' ? 'Divergence' : 'Δ mastery'}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {data.divergences.slice(0, 25).map((d: any, i: number) => {
                    const fullReplay = data.mode === 'full-replay'
                    const bound = fullReplay ? 0.01 : 0.5
                    const v = d.divergence ?? 0
                    const ok = v < bound
                    return (
                      <tr key={i} style={{ borderTop: '1px solid #EDF2F7' }}>
                        <td style={{ padding: 4 }}>{d.step}</td>
                        <td style={{ padding: 4 }}>{d.concept}</td>
                        <td style={{ padding: 4 }}>{d.original_mastery != null ? Number(d.original_mastery).toFixed(4) : '—'}</td>
                        <td style={{ padding: 4 }}>{d.replay_mastery != null ? Number(d.replay_mastery).toFixed(4) : '—'}</td>
                        <td style={{ padding: 4, color: ok ? '#1e7d4a' : '#C0392B', fontWeight: 700 }}>
                          {d.divergence != null ? Number(d.divergence).toFixed(6) : d.note ?? '—'}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      <NextSteps />
    </div>
  )
}

function CheckRow({ label, ok, detail }: { label: string; ok?: boolean; detail?: string }) {
  return (
    <tr style={{ borderTop: '1px solid #EDF2F7' }}>
      <td style={{ padding: '8px 4px', color: ok ? '#1e7d4a' : '#C0392B', fontWeight: 700, width: 28 }}>
        {ok ? '✓' : '✗'}
      </td>
      <td style={{ padding: '8px 4px' }}>{label}</td>
      <td style={{ padding: '8px 4px', color: '#A0AEC0', fontFamily: 'monospace' }}>{detail}</td>
    </tr>
  )
}

const card: React.CSSProperties = {
  background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10, padding: '16px 18px',
}
