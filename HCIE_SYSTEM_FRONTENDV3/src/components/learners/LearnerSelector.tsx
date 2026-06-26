'use client'

/**
 * LearnerSelector — pick a learner across the three real classes and drive the
 * end-to-end views. Backed by GET /v3/frontend/dashboard/learner-cohort (real
 * data from learner_projections + experiment_trajectories). No fabrication: every
 * row is a real learner the pipeline actually processed.
 *
 *   • real        (learner_type 'live')              — live humans on the ITS loop
 *   • synthetic   (learner_type 'synthetic')         — generated, run through the real stack
 *   • dataset     (learner_type 'experiment-replay') — ingested Junyi/ASSISTments/… users
 *
 * Reused full-page on /learners and as an embedded picker on /concepts and
 * /dashboard/learner.
 */
import { useState, useEffect, useMemo } from 'react'

export interface LearnerRow {
  user_id: string
  short_id: string
  learner_type: string
  dataset: string
  n_interactions: number
  avg_mastery: number
  accuracy: number
  avg_jt: number
  concepts_visited: number
  uncertainty: number
  improvement?: number
  last_seen?: string
}

export type LearnerClass = 'real' | 'synthetic' | 'dataset'

export const learnerClassOf = (t: string): LearnerClass =>
  t === 'live' ? 'real' : t === 'synthetic' ? 'synthetic' : 'dataset'

export const CLASS_META: Record<LearnerClass, { label: string; color: string; bg: string; border: string; desc: string }> = {
  real:      { label: 'Real · live',  color: '#1E8449', bg: '#D5F5E3', border: '#A9DFBF', desc: 'Live humans on the ITS loop — drive recommend → attempt' },
  synthetic: { label: 'Synthetic',    color: '#8E44AD', bg: '#F4ECF7', border: '#D7BDE2', desc: 'Generated learners run through the real JT / ensemble / bandit stack' },
  dataset:   { label: 'Dataset',      color: '#1A5276', bg: '#EBF5FB', border: '#AED6F1', desc: 'Ingested Junyi / ASSISTments / STATICS / EdNet users, replayed (read-only)' },
}

const TABS: { key: 'all' | LearnerClass; label: string }[] = [
  { key: 'all', label: 'All' },
  { key: 'real', label: 'Real · live' },
  { key: 'synthetic', label: 'Synthetic' },
  { key: 'dataset', label: 'Dataset' },
]

function fmtPct(v: number | undefined) { return v == null ? '—' : `${(v * 100).toFixed(0)}%` }

export function LearnerSelector({ onSelect, selectedId, compact = false, limit = 120 }: {
  onSelect: (l: LearnerRow) => void
  selectedId?: string
  compact?: boolean
  limit?: number  // endpoint caps this at 100
}) {
  const [rows, setRows] = useState<LearnerRow[] | null>(null)
  const [err, setErr] = useState(false)
  const [tab, setTab] = useState<'all' | LearnerClass>('all')
  const [q, setQ] = useState('')

  useEffect(() => {
    const token = typeof window !== 'undefined'
      ? (localStorage.getItem('hcie_auth_token') || localStorage.getItem('access_token') || '') : ''
    const lim = Math.min(100, Math.max(1, limit))
    fetch(`/v3/frontend/dashboard/learner-cohort?dataset=all&limit=${lim}`,
      { headers: token ? { Authorization: `Bearer ${token}` } : {}, signal: AbortSignal.timeout(9000) })
      .then(async r => {
        if (!r.ok) { setErr(true); setRows([]); return }
        const d = await r.json()
        setRows(d && d.status === 'ok' && Array.isArray(d.learners) ? d.learners : [])
      })
      .catch(() => { setErr(true); setRows([]) })
  }, [limit])

  const counts = useMemo(() => {
    const c: Record<string, number> = { all: 0, real: 0, synthetic: 0, dataset: 0 }
    for (const r of rows ?? []) { c.all++; c[learnerClassOf(r.learner_type)]++ }
    return c
  }, [rows])

  const filtered = useMemo(() => (rows ?? []).filter(r =>
    (tab === 'all' || learnerClassOf(r.learner_type) === tab) &&
    (!q || r.short_id?.toLowerCase().includes(q.toLowerCase()) || r.user_id?.toLowerCase().includes(q.toLowerCase()))
  ), [rows, tab, q])

  if (rows === null) {
    return <div style={{ padding: 20, color: '#A0AEC0', fontSize: 13 }}>⟳ Loading learners from <code>/v3/frontend/dashboard/learner-cohort</code>…</div>
  }

  return (
    <div>
      {/* tabs + search */}
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap', marginBottom: 12 }}>
        {TABS.map(t => {
          const active = tab === t.key
          const meta = t.key === 'all' ? null : CLASS_META[t.key as LearnerClass]
          return (
            <button key={t.key} onClick={() => setTab(t.key)} style={{
              padding: '5px 12px', fontSize: 12, fontWeight: 700, borderRadius: 8, cursor: 'pointer',
              border: `1px solid ${active ? (meta?.color ?? '#1A5276') : '#CBD5E0'}`,
              background: active ? (meta?.color ?? '#1A5276') : '#fff',
              color: active ? '#fff' : '#4A5568',
            }}>
              {t.label} <span style={{ opacity: 0.7 }}>{counts[t.key] ?? 0}</span>
            </button>
          )
        })}
        <input value={q} onChange={e => setQ(e.target.value)} placeholder="search id…"
          style={{ marginLeft: 'auto', padding: '6px 10px', fontSize: 12, border: '1px solid #CBD5E0',
                   borderRadius: 8, width: compact ? 140 : 200, fontFamily: 'ui-monospace, monospace' }} />
      </div>

      {tab !== 'all' && (
        <div style={{ fontSize: 12, color: CLASS_META[tab as LearnerClass].color, marginBottom: 10 }}>
          {CLASS_META[tab as LearnerClass].desc}
        </div>
      )}

      {err && <div style={{ fontSize: 12, color: '#C0392B', marginBottom: 8 }}>⚠ Backend unreachable — the selector is empty (no fabricated learners shown).</div>}
      {!err && filtered.length === 0 && <div style={{ fontSize: 13, color: '#A0AEC0', padding: 16 }}>No learners in this class yet.</div>}

      {/* learner list */}
      <div style={{ display: 'grid', gridTemplateColumns: compact ? '1fr' : 'repeat(auto-fill, minmax(260px, 1fr))', gap: 10,
                    maxHeight: compact ? 320 : undefined, overflowY: compact ? 'auto' : undefined }}>
        {filtered.map(r => {
          const cls = learnerClassOf(r.learner_type)
          const meta = CLASS_META[cls]
          const sel = selectedId && r.user_id === selectedId
          return (
            <button key={r.user_id} onClick={() => onSelect(r)} style={{
              textAlign: 'left', cursor: 'pointer', background: sel ? meta.bg : '#fff',
              border: `1px solid ${sel ? meta.color : '#E2E8F0'}`, borderRadius: 10, padding: '10px 12px',
              boxShadow: sel ? `0 0 0 1px ${meta.color}` : 'none',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                <code style={{ fontSize: 12, fontWeight: 700, color: '#1A2332', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{r.short_id || r.user_id}</code>
                <span style={{ fontSize: 9, fontWeight: 800, color: '#fff', background: meta.color, borderRadius: 4, padding: '2px 6px', whiteSpace: 'nowrap' }}>{meta.label}</span>
              </div>
              <div style={{ fontSize: 10.5, color: '#94A3B8', marginBottom: 6 }}>
                {r.dataset && r.dataset !== 'n/a' ? `${r.dataset} · ` : ''}{r.n_interactions} interactions · {r.concepts_visited} concepts
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{ flex: 1, height: 6, background: '#F1F5F9', borderRadius: 3, overflow: 'hidden' }}>
                  <span style={{ display: 'block', width: `${Math.min(100, (r.avg_mastery ?? 0) * 100)}%`, height: '100%', background: meta.color }} />
                </span>
                <span style={{ fontSize: 11, fontFamily: 'ui-monospace, monospace', color: '#2D3748' }}>{fmtPct(r.avg_mastery)} mastery</span>
              </div>
              <div style={{ fontSize: 10, color: '#A0AEC0', marginTop: 4, fontFamily: 'ui-monospace, monospace' }}>
                acc {fmtPct(r.accuracy)} · JT {(r.avg_jt ?? 0).toFixed(3)}
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}
