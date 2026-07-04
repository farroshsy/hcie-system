'use client'

import { useCallback, useEffect, useState } from 'react'
import { useLanguage } from '@/contexts/language_context'
import { t as ui } from '@/lib/ui/theme'

/** Bilingual string. */
export type Bi = { en: string; id: string }

/**
 * One walkthrough step. `selector` targets an element on the current page
 * (use a stable `[data-tour="..."]` attribute). If the element is missing the
 * step still shows, centered — so a tour never breaks if a page changes.
 */
export type TourStep = { selector: string; title: Bi; body: Bi }

const seenKey = (id: string) => `hcie_tour_seen_${id}`

const COPY = {
  tour: { en: 'Guide', id: 'Pandu' },
  newHere: { en: 'New here? Take a 60-second tour of this page.', id: 'Baru di sini? Ikuti tur 60 detik halaman ini.' },
  start: { en: 'Start tour', id: 'Mulai tur' },
  later: { en: 'Maybe later', id: 'Nanti saja' },
  skip: { en: 'Skip', id: 'Lewati' },
  back: { en: 'Back', id: 'Kembali' },
  next: { en: 'Next', id: 'Lanjut' },
  done: { en: 'Done', id: 'Selesai' },
}

/**
 * Self-contained guided walkthrough for a single page. Renders a floating
 * "Guide" button (bottom-right), a first-visit prompt, and a spotlight + tooltip
 * tour. No external dependency. Drop one per page:
 *   <PageGuide tourId="benchmarks" steps={STEPS} />
 */
export default function PageGuide({ steps, tourId }: { steps: TourStep[]; tourId: string }) {
  const { language } = useLanguage()
  const L = (b: Bi) => (language === 'id' ? b.id : b.en)

  const [active, setActive] = useState(false)
  const [idx, setIdx] = useState(0)
  const [rect, setRect] = useState<DOMRect | null>(null)
  const [prompt, setPrompt] = useState(false)

  useEffect(() => {
    if (typeof window === 'undefined') return
    try { if (!localStorage.getItem(seenKey(tourId))) setPrompt(true) } catch { /* ignore */ }
  }, [tourId])

  const markSeen = useCallback(() => {
    try { localStorage.setItem(seenKey(tourId), '1') } catch { /* ignore */ }
  }, [tourId])

  const locate = useCallback((i: number) => {
    const step = steps[i]
    if (!step) return
    const el = typeof document !== 'undefined'
      ? (document.querySelector(step.selector) as HTMLElement | null)
      : null
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' })
      window.setTimeout(() => setRect(el.getBoundingClientRect()), 320)
    } else {
      setRect(null)
    }
  }, [steps])

  const start = useCallback(() => { setPrompt(false); setActive(true); setIdx(0); locate(0) }, [locate])
  const close = useCallback(() => { setActive(false); markSeen() }, [markSeen])
  const go = useCallback((i: number) => { setIdx(i); locate(i) }, [locate])

  useEffect(() => {
    if (!active) return
    const reloc = () => locate(idx)
    window.addEventListener('resize', reloc)
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') close()
      else if (e.key === 'ArrowRight') { if (idx < steps.length - 1) go(idx + 1); else close() }
      else if (e.key === 'ArrowLeft' && idx > 0) go(idx - 1)
    }
    window.addEventListener('keydown', onKey)
    return () => { window.removeEventListener('resize', reloc); window.removeEventListener('keydown', onKey) }
  }, [active, idx, steps.length, locate, go, close])

  if (!steps.length) return null
  const step = steps[idx]
  const last = idx === steps.length - 1

  const card: React.CSSProperties = {
    background: ui.color.surface, border: `1px solid ${ui.color.line}`,
    borderRadius: ui.radius.lg, boxShadow: '0 8px 28px rgba(15,23,42,0.18)', padding: ui.space.md,
  }

  // Tooltip placement: below the target if there's room, else above, else centered.
  let tip: React.CSSProperties
  if (rect) {
    const vw = window.innerWidth, vh = window.innerHeight
    const left = Math.min(Math.max(rect.left, 12), Math.max(12, vw - 332))
    tip = rect.bottom < vh * 0.62
      ? { top: rect.bottom + 14, left }
      : { bottom: vh - rect.top + 14, left }
  } else {
    tip = { top: '50%', left: '50%', transform: 'translate(-50%, -50%)' }
  }

  return (
    <>
      <button onClick={start} aria-label={L(COPY.tour)} style={{
        position: 'fixed', right: 20, bottom: 20, zIndex: 9000, display: 'flex', alignItems: 'center', gap: 6,
        padding: '8px 14px', borderRadius: ui.radius.xl, cursor: 'pointer',
        background: ui.tone.info.fg, color: ui.color.surface, border: 'none',
        fontSize: ui.font.size.sm, fontWeight: ui.font.weight.bold, boxShadow: '0 4px 14px rgba(21,101,192,0.35)',
      }}>
        <span aria-hidden style={{ fontSize: ui.font.size.md }}>?</span> {L(COPY.tour)}
      </button>

      {prompt && !active && (
        <div style={{ position: 'fixed', right: 20, bottom: 70, zIndex: 9000, maxWidth: 280, ...card }}>
          <div style={{ fontSize: ui.font.size.sm, color: ui.color.body, lineHeight: 1.5, marginBottom: ui.space.sm }}>
            {L(COPY.newHere)}
          </div>
          <div style={{ display: 'flex', gap: ui.space.sm, justifyContent: 'flex-end' }}>
            <button onClick={() => { setPrompt(false); markSeen() }} style={btn('ghost')}>{L(COPY.later)}</button>
            <button onClick={start} style={btn('primary')}>{L(COPY.start)}</button>
          </div>
        </div>
      )}

      {active && (
        <div style={{ position: 'fixed', inset: 0, zIndex: 9500 }}>
          <div onClick={close} style={{ position: 'fixed', inset: 0, cursor: 'default' }} />
          {rect ? (
            <div style={{
              position: 'fixed', top: rect.top - 6, left: rect.left - 6,
              width: rect.width + 12, height: rect.height + 12, borderRadius: ui.radius.md,
              boxShadow: '0 0 0 9999px rgba(15,23,42,0.55)', border: `2px solid ${ui.tone.info.fg}`,
              pointerEvents: 'none', transition: 'all 0.25s ease',
            }} />
          ) : (
            <div style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,0.55)', pointerEvents: 'none' }} />
          )}

          <div style={{ position: 'fixed', maxWidth: 320, zIndex: 9600, ...card, ...tip }}>
            <div style={{ fontSize: ui.font.size.xs, fontWeight: ui.font.weight.bold, letterSpacing: '0.05em', textTransform: 'uppercase', color: ui.tone.info.fg }}>
              {idx + 1} / {steps.length}
            </div>
            <div style={{ fontSize: ui.font.size.md, fontWeight: ui.font.weight.heavy, color: ui.color.heading, margin: '4px 0 6px' }}>
              {L(step.title)}
            </div>
            <div style={{ fontSize: ui.font.size.sm, color: ui.color.body, lineHeight: 1.55, marginBottom: ui.space.md }}>
              {L(step.body)}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: ui.space.sm }}>
              <button onClick={close} style={btn('ghost')}>{L(COPY.skip)}</button>
              <div style={{ display: 'flex', gap: ui.space.sm }}>
                {idx > 0 && <button onClick={() => go(idx - 1)} style={btn('ghost')}>{L(COPY.back)}</button>}
                <button onClick={() => (last ? close() : go(idx + 1))} style={btn('primary')}>
                  {last ? L(COPY.done) : L(COPY.next)}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )

  function btn(kind: 'primary' | 'ghost'): React.CSSProperties {
    return {
      padding: '6px 14px', borderRadius: ui.radius.md, cursor: 'pointer', fontSize: ui.font.size.sm,
      fontWeight: ui.font.weight.bold,
      background: kind === 'primary' ? ui.tone.info.fg : ui.color.surface,
      color: kind === 'primary' ? ui.color.surface : ui.color.body,
      border: `1px solid ${kind === 'primary' ? ui.tone.info.fg : ui.color.line}`,
    }
  }
}
