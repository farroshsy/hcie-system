'use client'

/**
 * RealConceptMap — the REAL structure layer for /concepts. Concepts, mastery and
 * prerequisite edges come from the live backend, for any of the 3 learner classes:
 *   • cohort concepts + avg mastery + prereq-edge count → /v3/frontend/dashboard/cohort-concepts?catalog=
 *   • a picked learner's per-concept mastery            → /v3/research/learner/{id}/governance/trajectory
 * No fabrication — pick a learner and see their real mastery overlaid on the real
 * concept set. The authored task content on /concepts is kept separately as a
 * clearly-labelled "try a task" sandbox.
 */
import { useState, useEffect, useMemo } from 'react'
import Link from 'next/link'
import { LearnerSelector, LearnerRow, learnerClassOf, CLASS_META } from './LearnerSelector'

const CATALOGS = ['k12', 'junyi', 'assistments', 'statics', 'ednet', 'csedm']

interface CohortConcept {
  concept_id: string
  catalog: string
  avg_mastery: number
  student_count: number
  fail_rate: number
  total_attempts: number
  transfer_incoming: number
}

function authHeaders(): HeadersInit {
  const token = typeof window !== 'undefined'
    ? (localStorage.getItem('hcie_auth_token') || localStorage.getItem('access_token') || '') : ''
  return token ? { Authorization: `Bearer ${token}` } : {}
}

function shortConcept(id: string) {
  return id.replace(/^ext_/, '').replace(/^junyi_graph_/, '').replace(/^junyi_/, '')
    .replace(/_/g, ' ').slice(0, 48)
}

export function RealConceptMap() {
  const [catalog, setCatalog] = useState('k12')
  const [concepts, setConcepts] = useState<CohortConcept[] | null>(null)
  const [learner, setLearner] = useState<LearnerRow | null>(null)
  const [learnerMastery, setLearnerMastery] = useState<Record<string, number>>({})
  const [pickerOpen, setPickerOpen] = useState(false)
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    setConcepts(null)
    fetch(`/v3/frontend/dashboard/cohort-concepts?catalog=${catalog}&limit=60`,
      { headers: authHeaders(), signal: AbortSignal.timeout(9000) })
      .then(r => (r.ok ? r.json() : null))
      .then(d => setConcepts(d && d.status === 'ok' && Array.isArray(d.concepts) ? d.concepts : []))
      .catch(() => setConcepts([]))
  }, [catalog, reloadKey])

  useEffect(() => {
    if (!learner) { setLearnerMastery({}); return }
    fetch(`/v3/research/learner/${encodeURIComponent(learner.user_id)}/governance/trajectory?limit=500`,
      { headers: authHeaders(), signal: AbortSignal.timeout(9000) })
      .then(r => (r.ok ? r.json() : null))
      .then(d => {
        const m: Record<string, number> = {}
        for (const row of (d?.trajectory ?? [])) {
          if (row.concept != null && row.mastery_after != null) m[String(row.concept)] = Number(row.mastery_after)
        }
        setLearnerMastery(m)
      })
      .catch(() => setLearnerMastery({}))
  }, [learner])

  const cls = learner ? CLASS_META[learnerClassOf(learner.learner_type)] : null
  const cohortById = useMemo(() => {
    const m: Record<string, CohortConcept> = {}
    for (const c of (concepts ?? [])) m[c.concept_id] = c
    return m
  }, [concepts])
  const hasLearnerData = learner != null && Object.keys(learnerMastery).length > 0
  // When a learner is picked, drive the rows from THEIR visited concepts + real
  // mastery (cohort avg looked up where available). Otherwise show the cohort's
  // top concepts for the catalog.
  const displayRows = useMemo(() => {
    if (hasLearnerData) {
      return Object.entries(learnerMastery)
        .map(([id, lm]) => ({ concept_id: id, learnerM: lm as number | undefined, c: cohortById[id] as CohortConcept | undefined }))
        .sort((a, b) => (b.learnerM ?? 0) - (a.learnerM ?? 0))
    }
    return (concepts ?? []).slice()
      .sort((a, b) => (b.avg_mastery ?? 0) - (a.avg_mastery ?? 0))
      .map(c => ({ concept_id: c.concept_id, learnerM: undefined as number | undefined, c: c as CohortConcept | undefined }))
  }, [concepts, hasLearnerData, learnerMastery, cohortById])

  return (
    <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 12, padding: 18, marginBottom: 20 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 10, marginBottom: 10 }}>
        <div>
          <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', color: '#1A5276', textTransform: 'uppercase' }}>● Live · real concepts</div>
          <div style={{ fontSize: 14, color: '#5A6776', marginTop: 2 }}>
            Real concept set + mastery from the backend. Pick a learner to overlay their actual per-concept mastery.
          </div>
        </div>
        <button onClick={() => setPickerOpen(o => !o)} style={{
          fontSize: 13, fontWeight: 700, color: '#fff', background: '#1A5276', border: 'none',
          borderRadius: 8, padding: '8px 14px', cursor: 'pointer', whiteSpace: 'nowrap',
        }}>{learner ? `↻ ${learner.short_id}` : '+ Pick a learner'}</button>
      </div>

      {/* learner picker (collapsible) */}
      {pickerOpen && (
        <div style={{ border: '1px solid #E2E8F0', borderRadius: 10, padding: 12, marginBottom: 12, background: '#F8FAFC' }}>
          <LearnerSelector compact selectedId={learner?.user_id}
            onSelect={l => { setLearner(l); setPickerOpen(false); if (CATALOGS.includes(l.dataset)) setCatalog(l.dataset) }} />
        </div>
      )}

      {/* selected learner banner */}
      {learner && cls && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap',
                      background: cls.bg, border: `1px solid ${cls.border}`, borderRadius: 8, padding: '8px 12px', marginBottom: 12 }}>
          <span style={{ fontSize: 9, fontWeight: 800, color: '#fff', background: cls.color, borderRadius: 4, padding: '2px 6px' }}>{cls.label}</span>
          <code style={{ fontSize: 12, color: '#1A2332' }}>{learner.short_id}</code>
          <span style={{ fontSize: 12, color: '#5A6776' }}>· {learner.n_interactions} interactions · overlaying this learner's real mastery</span>
          <Link href={`/dashboard/learner?user_id=${encodeURIComponent(learner.user_id)}`}
            style={{ marginLeft: 'auto', fontSize: 12, fontWeight: 700, color: cls.color, textDecoration: 'none' }}>
            full pipeline →
          </Link>
        </div>
      )}

      {/* catalog tabs */}
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 12 }}>
        {CATALOGS.map(c => (
          <button key={c} onClick={() => setCatalog(c)} style={{
            padding: '4px 11px', fontSize: 12, fontWeight: 600, borderRadius: 7, cursor: 'pointer',
            border: `1px solid ${catalog === c ? '#1A5276' : '#CBD5E0'}`,
            background: catalog === c ? '#1A5276' : '#fff', color: catalog === c ? '#fff' : '#4A5568',
          }}>{c}</button>
        ))}
      </div>

      {/* concept rows */}
      {concepts === null ? (
        <div style={{ padding: 16, color: '#A0AEC0', fontSize: 13 }}>⟳ Loading real concepts…</div>
      ) : displayRows.length === 0 ? (
        <div style={{ padding: 16, color: '#A0AEC0', fontSize: 13 }}>
          No concepts loaded for the <b>{catalog}</b> catalog.{' '}
          <button onClick={() => setReloadKey(k => k + 1)} style={{ color: '#1A5276', textDecoration: 'underline', background: 'none', border: 'none', cursor: 'pointer', fontSize: 13 }}>↻ retry</button>
        </div>
      ) : (
        <div style={{ display: 'grid', gap: 7 }}>
          {hasLearnerData && (
            <div style={{ fontSize: 11, color: cls?.color ?? '#1A5276' }}>Showing the <b>{displayRows.length}</b> concepts this learner actually visited, by their real mastery.</div>
          )}
          {displayRows.map(row => {
            const c = row.c
            const lm = row.learnerM
            return (
              <div key={row.concept_id} style={{ display: 'grid', gridTemplateColumns: '1.6fr 1fr 130px', gap: 10, alignItems: 'center',
                                               padding: '7px 12px', border: '1px solid #F1F5F9', borderRadius: 8 }}>
                <div>
                  <div style={{ fontSize: 12.5, color: '#1A2332', fontWeight: 600 }}>{shortConcept(row.concept_id)}</div>
                  <div style={{ fontSize: 10.5, color: '#94A3B8' }}>
                    {c
                      ? <>{c.student_count} learners · {c.transfer_incoming} prereq edge{c.transfer_incoming === 1 ? '' : 's'}{c.fail_rate > 0 ? ` · ${(c.fail_rate * 100).toFixed(0)}% fail` : ''}</>
                      : 'visited by this learner'}
                  </div>
                </div>
                {/* cohort mastery */}
                <div>
                  <div style={{ fontSize: 9.5, color: '#A0AEC0', marginBottom: 2 }}>cohort avg</div>
                  {c ? (
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <span style={{ flex: 1, height: 6, background: '#F1F5F9', borderRadius: 3, overflow: 'hidden' }}>
                        <span style={{ display: 'block', width: `${Math.min(100, (c.avg_mastery ?? 0) * 100)}%`, height: '100%', background: '#94A3B8' }} />
                      </span>
                      <span style={{ fontSize: 11, fontFamily: 'ui-monospace, monospace', color: '#718096' }}>{((c.avg_mastery ?? 0) * 100).toFixed(0)}%</span>
                    </div>
                  ) : <span style={{ fontSize: 10.5, color: '#CBD5E1' }}>—</span>}
                </div>
                {/* selected learner mastery */}
                <div>
                  <div style={{ fontSize: 9.5, color: '#A0AEC0', marginBottom: 2 }}>{learner ? 'this learner' : '—'}</div>
                  {learner ? (
                    lm != null ? (
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <span style={{ flex: 1, height: 6, background: '#F1F5F9', borderRadius: 3, overflow: 'hidden' }}>
                          <span style={{ display: 'block', width: `${Math.min(100, lm * 100)}%`, height: '100%', background: cls?.color ?? '#1E8449' }} />
                        </span>
                        <span style={{ fontSize: 11, fontFamily: 'ui-monospace, monospace', color: cls?.color ?? '#1E8449', fontWeight: 700 }}>{(lm * 100).toFixed(0)}%</span>
                      </div>
                    ) : <span style={{ fontSize: 10.5, color: '#CBD5E1' }}>not visited</span>
                  ) : <span style={{ fontSize: 10.5, color: '#CBD5E1' }}>pick a learner</span>}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
