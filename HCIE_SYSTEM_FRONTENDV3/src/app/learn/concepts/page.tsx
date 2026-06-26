'use client'

/**
 * Concept Map — K-12 CS curriculum browser with live mastery overlay.
 *
 * Shows all 36 concepts grouped by grade band. Each card shows the learner's
 * current mastery (from /v3/learner/progress) and links to /learn?concept=X
 * so the ITS filters recommendations to that concept.
 *
 * "Let the system choose" goes to /learn without a filter.
 */

import { useEffect, useState } from 'react'
import { useAuth } from '@/contexts/auth_context'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { getBackendUrl } from '@/lib/api/backend-url'
import { K12_CONCEPTS, conceptLabel } from '@/lib/catalog/k12-catalog'
import { useT } from '@/contexts/language_context'
import { Panel, Tag, Stat, Eyebrow } from '@/lib/ui/primitives'
import { t as ui, type Tone } from '@/lib/ui/theme'

const BACKEND = getBackendUrl()

type GradeBand = 'K-2' | 'K-5' | 'K-8' | 'K-12'

interface ConceptLockState {
  id: string
  locked: boolean
  prerequisites: string[]
  missing_prereqs: string[]
  mastery_threshold: number
}

// Per-band semantic tone + accent color. Tone drives the Panel/Tag tint so each
// band reads as one consistent family; `color` is the accent used for the card
// top-rail and area chip. `label` is preserved verbatim from the curriculum.
const GRADE_META: Record<string, { tone: Tone; color: string; label: string }> = {
  'K-2':  { tone: 'ok',      color: ui.tone.ok.fg,      label: 'K–2 · Foundational' },
  'K-5':  { tone: 'info',    color: ui.tone.info.fg,    label: 'K–5 · Developing' },
  'K-8':  { tone: 'accent',  color: ui.tone.accent.fg,  label: 'K–8 · Intermediate' },
  'K-12': { tone: 'warn',    color: ui.tone.warn.fg,    label: 'K–12 · Advanced' },
}
const GRADE_ORDER: GradeBand[] = ['K-2', 'K-5', 'K-8', 'K-12']

function masteryColor(v: number) {
  return v >= 0.7 ? ui.tone.ok.fg : v >= 0.45 ? ui.tone.warn.fg : ui.tone.bad.fg
}

export default function ConceptMapPage() {
  const t = useT()
  const { user, isAuthenticated, isLoading: authLoading } = useAuth()
  const router = useRouter()
  const [masteryMap, setMasteryMap] = useState<Record<string, number>>({})
  const [lockMap, setLockMap] = useState<Record<string, ConceptLockState>>({})
  const [loadingMastery, setLoadingMastery] = useState(true)

  useEffect(() => {
    if (authLoading) return
    if (!BACKEND || !isAuthenticated) { setLoadingMastery(false); return }
    const token = (typeof window !== 'undefined' &&
      (localStorage.getItem('hcie_auth_token') || localStorage.getItem('access_token'))) || ''
    const headers: HeadersInit = token ? { Authorization: `Bearer ${token}` } : {}
    fetch(`${BACKEND}/v3/learner/progress`, { headers, signal: AbortSignal.timeout(5000) })
      .then(r => r.ok ? r.json() : null)
      .then(d => {
        if (!d) return
        const raw: Record<string, any> = d.concepts ?? {}
        const m: Record<string, number> = {}
        for (const [k, v] of Object.entries(raw)) m[k] = Number(v)
        setMasteryMap(m)
      })
      .catch(() => { /* no mastery data — show as not started */ })
      .finally(() => setLoadingMastery(false))

    if (user?.id) {
      fetch(`${BACKEND}/v3/concepts/${encodeURIComponent(user.id)}/locked`, {
        headers,
        signal: AbortSignal.timeout(5000),
      })
        .then(r => r.ok ? r.json() : null)
        .then(d => {
          if (!d?.concepts) return
          const next: Record<string, ConceptLockState> = {}
          for (const c of d.concepts as ConceptLockState[]) next[c.id] = c
          setLockMap(next)
        })
        .catch(() => { /* lock state is progressive enhancement */ })
    }
  }, [authLoading, isAuthenticated, user?.id])

  // Group by grade band
  const byGrade: Record<string, typeof K12_CONCEPTS> = {}
  for (const c of K12_CONCEPTS) {
    if (!byGrade[c.gradeBand]) byGrade[c.gradeBand] = []
    byGrade[c.gradeBand].push(c)
  }

  const totalConcepts = K12_CONCEPTS.length
  const masteredCount = K12_CONCEPTS.filter(c => (masteryMap[c.id] ?? 0) >= 0.7).length
  const inProgressCount = K12_CONCEPTS.filter(c => {
    const m = masteryMap[c.id] ?? 0
    return m > 0 && m < 0.7
  }).length

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: `${ui.space.xxl}px ${ui.space.xl}px 64px` }}>

      {/* ── Header ──────────────────────────────────────────────────────────── */}
      <div style={{ marginBottom: ui.space.xl }}>
        <Eyebrow color={ui.tone.info.fg}>{t('concepts.eyebrow')}</Eyebrow>
        <h1 style={{ fontSize: ui.font.size.h2, fontWeight: ui.font.weight.heavy, color: ui.color.ink, margin: 0 }}>
          {t('concepts.title')}
        </h1>
        <p style={{ fontSize: ui.font.size.md, color: ui.color.muted, marginTop: ui.space.xs, maxWidth: 640, lineHeight: 1.55 }}>
          {totalConcepts} {t('common.concepts')} — {t('concepts.intro')}
        </p>
      </div>

      {/* ── Progress strip + CTA ─────────────────────────────────────────────── */}
      <div style={{ display: 'flex', gap: ui.space.md, marginBottom: ui.space.xxl, flexWrap: 'wrap', alignItems: 'stretch' }}>
        <div style={{ minWidth: 130 }}>
          <Stat
            label="Mastered"
            value={loadingMastery ? '…' : `${masteredCount}/${totalConcepts}`}
            tone="ok"
          />
        </div>
        <div style={{ minWidth: 130 }}>
          <Stat
            label="In Progress"
            value={loadingMastery ? '…' : inProgressCount}
            tone="warn"
          />
        </div>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: ui.space.sm, alignItems: 'center' }}>
          <button
            onClick={() => router.push('/learn')}
            style={{
              padding: `${ui.space.md}px ${ui.space.xxl}px`, fontSize: ui.font.size.md,
              fontWeight: ui.font.weight.bold, color: ui.color.surface,
              background: ui.tone.info.fg, border: 'none', borderRadius: ui.radius.md,
              cursor: 'pointer',
            }}>
            ✨ Let the system choose →
          </button>
        </div>
      </div>

      {/* ── Grade bands ──────────────────────────────────────────────────────── */}
      {GRADE_ORDER.map(band => {
        const concepts = byGrade[band] ?? []
        const g = GRADE_META[band]
        const gt = ui.tone[g.tone]
        const masteredInBand = concepts.filter(c => (masteryMap[c.id] ?? 0) >= 0.7).length
        return (
          <div key={band} style={{ marginBottom: ui.space.xxl + 4 }}>

            {/* Band header */}
            <div style={{ display: 'flex', alignItems: 'center', gap: ui.space.md, marginBottom: ui.space.md }}>
              <Tag tone={g.tone}>{g.label}</Tag>
              {!loadingMastery && (
                <span style={{ fontSize: ui.font.size.sm, color: ui.color.faint, fontVariantNumeric: 'tabular-nums' }}>
                  {masteredInBand}/{concepts.length} mastered
                </span>
              )}
              {!loadingMastery && masteredInBand === concepts.length && concepts.length > 0 && (
                <span style={{ fontSize: ui.font.size.sm, color: ui.tone.ok.fg, fontWeight: ui.font.weight.bold }}>✓ Complete</span>
              )}
            </div>

            {/* Concept grid */}
            <div style={{ display: 'grid',
                          gridTemplateColumns: 'repeat(auto-fill, minmax(195px, 1fr))', gap: ui.space.md }}>
              {concepts.map(concept => {
                const mastery = masteryMap[concept.id] ?? 0
                const started = mastery > 0
                const mastered = mastery >= 0.7
                const mc = masteryColor(mastery)
                const lock = lockMap[concept.id]
                const locked = !!lock?.locked
                const railColor = locked ? ui.color.lineStrong : (started ? mc : g.color)
                return (
                  <Link
                    key={concept.id}
                    href={`/learn?concept=${encodeURIComponent(concept.id)}`}
                    onClick={e => { if (locked) e.preventDefault() }}
                    style={{ textDecoration: 'none' }}>
                    <Panel
                      pad="md"
                      style={{
                        background: locked ? ui.color.subtle : ui.color.surface,
                        borderColor: locked ? ui.color.lineStrong : (started ? mc + '50' : ui.color.line),
                        borderTop: `3px solid ${railColor}`,
                        cursor: locked ? 'not-allowed' : 'pointer', transition: 'all 0.15s', minHeight: 108,
                        display: 'flex', flexDirection: 'column',
                        opacity: locked ? 0.68 : 1,
                      }}
                      title={locked ? `Locked until: ${lock?.missing_prereqs.join(', ')}` : undefined}
                      onMouseEnter={e => {
                        if (locked) return
                        const el = e.currentTarget as HTMLDivElement
                        el.style.transform = 'translateY(-2px)'
                        el.style.boxShadow = '0 4px 14px rgba(0,0,0,0.08)'
                        el.style.borderColor = g.color
                      }}
                      onMouseLeave={e => {
                        if (locked) return
                        const el = e.currentTarget as HTMLDivElement
                        el.style.transform = 'translateY(0)'
                        el.style.boxShadow = 'none'
                        el.style.borderColor = started ? mc + '50' : ui.color.line
                      }}>

                      {/* Top row: area badge + status dot */}
                      <div style={{ display: 'flex', justifyContent: 'space-between',
                                    alignItems: 'flex-start', marginBottom: ui.space.sm }}>
                        <span style={{ fontSize: ui.font.size.xs, color: locked ? ui.color.body : g.color, fontWeight: ui.font.weight.bold,
                                       background: locked ? ui.color.line : gt.bg, borderRadius: ui.radius.sm, padding: '1px 6px',
                                       lineHeight: 1.4 }}>
                          {concept.conceptArea}
                        </span>
                        {locked && (
                          <span style={{ fontSize: ui.font.size.md, color: ui.color.body, lineHeight: 1 }}>🔒</span>
                        )}
                        {!locked && mastered && (
                          <span style={{ fontSize: ui.font.size.md, color: ui.tone.ok.fg, lineHeight: 1 }}>✓</span>
                        )}
                        {!locked && started && !mastered && (
                          <span style={{ fontSize: ui.font.size.sm, color: ui.tone.warn.fg, lineHeight: 1 }}>●</span>
                        )}
                      </div>

                      {/* Concept name */}
                      <div style={{ fontSize: ui.font.size.md, fontWeight: ui.font.weight.bold, color: locked ? ui.color.body : ui.color.ink,
                                    marginBottom: ui.space.xs, lineHeight: 1.3, flex: 1 }}>
                        {concept.label}
                      </div>

                      {/* Description (trimmed) */}
                      <div style={{ fontSize: ui.font.size.xs, color: ui.color.muted, lineHeight: 1.4, marginBottom: ui.space.sm }}>
                        {locked && lock?.missing_prereqs.length
                          ? `Locked: complete ${lock.missing_prereqs.map(conceptLabel).join(', ')} first`
                          : concept.description.length > 65
                          ? concept.description.slice(0, 65) + '…'
                          : concept.description}
                      </div>

                      {/* Mastery bar or difficulty hint */}
                      {started ? (
                        <div>
                          <div style={{ display: 'flex', justifyContent: 'space-between',
                                        marginBottom: ui.space.xs - 1 }}>
                            <span style={{ fontSize: ui.font.size.xs, color: ui.color.muted }}>Mastery</span>
                            <span style={{ fontSize: ui.font.size.xs, fontWeight: ui.font.weight.bold, color: mc,
                                           fontVariantNumeric: 'tabular-nums' }}>
                              {(mastery * 100).toFixed(0)}%
                            </span>
                          </div>
                          <div style={{ height: 4, background: ui.color.line, borderRadius: 2 }}>
                            <div style={{ height: '100%', width: `${mastery * 100}%`,
                                          background: mc, borderRadius: 2,
                                          transition: 'width 0.4s' }} />
                          </div>
                        </div>
                      ) : (
                        <div style={{ fontSize: ui.font.size.xs, color: ui.color.faint }}>
                          {'★'.repeat(concept.cognitiveLevel)}{'☆'.repeat(4 - concept.cognitiveLevel)}
                          {' · '}Bloom L{concept.cognitiveLevel}
                        </div>
                      )}
                    </Panel>
                  </Link>
                )
              })}
            </div>
          </div>
        )
      })}

      {/* ── Legend ──────────────────────────────────────────────────────────── */}
      <Panel pad="md" tone="neutral" style={{ marginTop: ui.space.sm, marginBottom: ui.space.xxl }}>
        <div style={{ display: 'flex', gap: ui.space.lg, flexWrap: 'wrap',
                      fontSize: ui.font.size.sm, color: ui.color.muted, alignItems: 'center' }}>
          <span><span style={{ color: ui.tone.ok.fg, fontWeight: ui.font.weight.bold }}>✓</span> Mastered (≥70%)</span>
          <span><span style={{ color: ui.tone.warn.fg, fontWeight: ui.font.weight.bold }}>●</span> In progress</span>
          <span><span style={{ color: ui.color.body, fontWeight: ui.font.weight.bold }}>🔒</span> Locked by prerequisite</span>
          <span>☆ Not started · bar shows cognitive depth (Bloom level)</span>
        </div>
      </Panel>

      {/* ── Footer nav ──────────────────────────────────────────────────────── */}
      <div style={{ display: 'flex', gap: ui.space.sm, justifyContent: 'center', flexWrap: 'wrap' }}>
        <Link href="/learn" style={{ fontSize: ui.font.size.md, fontWeight: ui.font.weight.medium, color: ui.color.body,
          textDecoration: 'none', padding: `${ui.space.md}px ${ui.space.xxl}px`, borderRadius: ui.radius.md,
          border: `1px solid ${ui.color.lineStrong}`, background: ui.color.surface }}>
          ← Back to Tutor
        </Link>
        <Link href="/dashboard/learner" style={{ fontSize: ui.font.size.md, fontWeight: ui.font.weight.bold, color: ui.color.surface,
          textDecoration: 'none', padding: `${ui.space.md}px ${ui.space.xxl}px`, borderRadius: ui.radius.md, background: ui.tone.info.fg }}>
          My Progress →
        </Link>
      </div>
    </div>
  )
}
