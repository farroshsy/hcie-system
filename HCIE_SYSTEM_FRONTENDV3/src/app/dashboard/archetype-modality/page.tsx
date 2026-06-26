'use client'

/**
 * /dashboard/archetype-modality — RESEARCHER surface.
 *
 * "Does a given archetype actually succeed more on a given modality, per concept?"
 * Reads /v3/frontend/dashboard/archetype-modality-analysis → interactions ⋈
 * user_archetype_profile (real learners only). Archetype is a COVARIATE — it never
 * feeds the representation bandit (the bandit learns per-learner success), so this
 * surface lets you CHECK whether the data-driven modality preference happens to line
 * up with self-reported learning style. It is NOT synthetically seeded: empty until
 * real learners both onboard AND accumulate multi-modal attempts.
 */
import { useEffect, useState, useMemo } from 'react'
import Link from 'next/link'
import { useT } from '@/contexts/language_context'

const VARK = ['visual', 'auditory', 'reading', 'kinesthetic'] as const
const MODALITIES = ['text', 'mcq', 'video_question', 'audio_listen', 'code'] as const
const MOD_LABEL: Record<string, string> = {
  text: 'text', mcq: 'mcq', video_question: 'video', audio_listen: 'audio', code: 'code',
}

interface Bucket {
  concept: string
  representation: string
  dominant_vark: string
  n_interactions: number
  accuracy: number | null
  avg_response_time: number | null
}
interface Meta {
  profiles_count: number
  modality_learners: number
  learners_with_archetype_and_modality: number
  data_source: string
  note: string
}

function authHeaders(): HeadersInit {
  const t = typeof window !== 'undefined'
    ? (localStorage.getItem('hcie_auth_token') || localStorage.getItem('access_token') || '') : ''
  return t ? { Authorization: `Bearer ${t}` } : {}
}
function shortConcept(id: string) {
  return id.replace(/^ext_/, '').replace(/^junyi_graph_/, '').replace(/_/g, ' ')
}
function accColor(a: number) {
  if (a >= 0.75) return '#1E8449'
  if (a >= 0.5) return '#B7950B'
  return '#C0392B'
}

export default function ArchetypeModalityPage() {
  const t = useT()
  const [buckets, setBuckets] = useState<Bucket[] | null>(null)
  const [meta, setMeta] = useState<Meta | null>(null)
  const [err, setErr] = useState<string | null>(null)
  const [reload, setReload] = useState(0)

  const VARK_LABEL: Record<string, string> = {
    visual: t('archetypeModality.varkVisual'),
    auditory: t('archetypeModality.varkAuditory'),
    reading: t('archetypeModality.varkReading'),
    kinesthetic: t('archetypeModality.varkKinesthetic'),
    unknown: t('archetypeModality.varkUnknown'),
  }

  useEffect(() => {
    setBuckets(null); setErr(null)
    fetch(`/v3/frontend/dashboard/archetype-modality-analysis`,
      { headers: authHeaders(), signal: AbortSignal.timeout(9000) })
      .then(r => (r.ok ? r.json() : null))
      .then(d => {
        if (!d || d.status !== 'ok') { setErr(t('archetypeModality.loadError')); setBuckets([]); return }
        setBuckets(Array.isArray(d.buckets) ? d.buckets : [])
        setMeta(d.meta ?? null)
      })
      .catch(() => { setErr(t('archetypeModality.loadError')); setBuckets([]) })
  }, [reload])

  // group by concept → archetype → modality → bucket
  const byConcept = useMemo(() => {
    const m: Record<string, Record<string, Record<string, Bucket>>> = {}
    for (const b of (buckets ?? [])) {
      m[b.concept] = m[b.concept] || {}
      m[b.concept][b.dominant_vark] = m[b.concept][b.dominant_vark] || {}
      m[b.concept][b.dominant_vark][b.representation] = b
    }
    return m
  }, [buckets])

  // which modalities + archetypes actually have data (don't show empty columns/rows)
  const activeMods = useMemo(() => {
    const s = new Set<string>()
    for (const b of (buckets ?? [])) s.add(b.representation)
    return MODALITIES.filter(m => s.has(m))
  }, [buckets])
  const activeVark = useMemo(() => {
    const s = new Set<string>()
    for (const b of (buckets ?? [])) s.add(b.dominant_vark)
    return [...VARK, 'unknown'].filter(v => s.has(v))
  }, [buckets])

  const concepts = Object.keys(byConcept).sort((a, b) => a.localeCompare(b))
  const both = meta?.learners_with_archetype_and_modality ?? 0

  return (
    <div style={{ maxWidth: 1120, margin: '0 auto', padding: '28px 24px 80px', fontFamily: 'Inter, system-ui, sans-serif' }}>
      <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.1em', color: '#6C3483', textTransform: 'uppercase' }}>
        {t('archetypeModality.eyebrow')}
      </div>
      <h1 style={{ fontSize: 26, fontWeight: 800, color: '#1A2332', margin: '6px 0 8px' }}>
        {t('archetypeModality.heroTitle')}
      </h1>
      <p style={{ fontSize: 14, color: '#5A6776', maxWidth: 860, lineHeight: 1.6, margin: '0 0 14px' }}>
        {t('archetypeModality.introA')}{' '}<b>{t('archetypeModality.introTriple')}</b>{t('archetypeModality.introB')}{' '}
        <code>interactions ⋈ user_archetype_profile</code>{t('archetypeModality.introC')}{' '}<b>{t('archetypeModality.introCovariate')}</b>{t('archetypeModality.introD')}
      </p>
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 18, fontSize: 13 }}>
        <Link href="/review/methods" style={{ color: '#16A085', textDecoration: 'none', background: '#F0FAF4', border: '1px solid #B7E0D7', borderRadius: 8, padding: '6px 12px' }}>
          🎰 {t('archetypeModality.linkMabSandbox')}
        </Link>
        <Link href="/dashboard/learner" style={{ color: '#1A5276', textDecoration: 'none', background: '#EBF5FB', border: '1px solid #AED6F1', borderRadius: 8, padding: '6px 12px' }}>
          🧑‍🎓 {t('archetypeModality.linkLearnerFit')}
        </Link>
      </div>

      {/* coverage banner */}
      {meta && (
        <div style={{
          display: 'flex', gap: 18, flexWrap: 'wrap', alignItems: 'center',
          background: both > 0 ? '#F0FAF4' : '#FEF9E7',
          border: `1px solid ${both > 0 ? '#B7E0D7' : '#F9E79F'}`,
          borderRadius: 10, padding: '12px 16px', marginBottom: 18,
        }}>
          <Stat label={t('archetypeModality.statOnboarded')} value={meta.profiles_count} />
          <Stat label={t('archetypeModality.statModalityData')} value={meta.modality_learners} />
          <Stat label={t('archetypeModality.statBoth')} value={both} highlight />
          <div style={{ fontSize: 11.5, color: '#7D6008', maxWidth: 460, lineHeight: 1.45 }}>
            {both === 0
              ? t('archetypeModality.bannerEmpty')
              : `${t('archetypeModality.bannerPrelimA')} ${both} ${t('archetypeModality.bannerPrelimB')}`}
          </div>
        </div>
      )}

      {buckets === null ? (
        <div style={{ padding: 18, color: '#A0AEC0', fontSize: 13 }}>⟳ {t('archetypeModality.loading')}</div>
      ) : err ? (
        <div style={{ padding: 18, color: '#C0392B', fontSize: 13 }}>
          {err}{' '}
          <button onClick={() => setReload(k => k + 1)} style={{ color: '#1A5276', textDecoration: 'underline', background: 'none', border: 'none', cursor: 'pointer', fontSize: 13 }}>↻ {t('archetypeModality.retry')}</button>
        </div>
      ) : concepts.length === 0 ? (
        <div style={{ padding: 28, textAlign: 'center', background: '#fff', border: '1px dashed #CBD5E0', borderRadius: 12, color: '#718096' }}>
          <div style={{ fontSize: 15, fontWeight: 700, color: '#4A5568', marginBottom: 6 }}>{t('archetypeModality.emptyTitle')}</div>
          <div style={{ fontSize: 13, maxWidth: 520, margin: '0 auto', lineHeight: 1.6 }}>
            {t('archetypeModality.emptyBodyA')}{' '}
            <Link href="/learn" style={{ color: '#16A085' }}>/learn</Link>{' '}
            {t('archetypeModality.emptyBodyB')}
          </div>
        </div>
      ) : (
        <div style={{ display: 'grid', gap: 16 }}>
          {concepts.map(concept => {
            const grid = byConcept[concept]
            return (
              <div key={concept} style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 12, padding: 16 }}>
                <div style={{ fontSize: 14, fontWeight: 800, color: '#1A2332', marginBottom: 10 }}>{shortConcept(concept)}</div>
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ borderCollapse: 'collapse', fontSize: 12, minWidth: 380 }}>
                    <thead>
                      <tr>
                        <th style={{ textAlign: 'left', padding: '6px 10px', color: '#718096', fontWeight: 600 }}>{t('archetypeModality.thArchetypeModality')}</th>
                        {activeMods.map(m => (
                          <th key={m} style={{ padding: '6px 12px', color: '#4A5568', fontWeight: 700, textTransform: 'capitalize' }}>{MOD_LABEL[m]}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {activeVark.map(v => (
                        <tr key={v}>
                          <td style={{ padding: '6px 10px', color: '#6C3483', fontWeight: 700, whiteSpace: 'nowrap' }}>{VARK_LABEL[v] ?? v}</td>
                          {activeMods.map(m => {
                            const b = grid[v]?.[m]
                            if (!b || b.accuracy == null) {
                              return <td key={m} style={{ padding: '6px 12px', textAlign: 'center', color: '#CBD5E1' }}>—</td>
                            }
                            return (
                              <td key={m} style={{ padding: '6px 12px', textAlign: 'center' }}>
                                <span style={{ fontWeight: 800, color: accColor(b.accuracy) }}>{(b.accuracy * 100).toFixed(0)}%</span>
                                <span style={{ color: '#A0AEC0', fontSize: 10.5 }}> ({b.n_interactions})</span>
                              </td>
                            )
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div style={{ fontSize: 10.5, color: '#A0AEC0', marginTop: 8 }}>{t('archetypeModality.legend')}</div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

function Stat({ label, value, highlight }: { label: string; value: number; highlight?: boolean }) {
  return (
    <div>
      <div style={{ fontSize: 22, fontWeight: 800, color: highlight ? '#6C3483' : '#1A2332', fontFamily: 'ui-monospace, monospace' }}>{value}</div>
      <div style={{ fontSize: 10.5, color: '#718096', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{label}</div>
    </div>
  )
}
