'use client'

import { useState, useEffect, useRef, type ReactNode } from 'react'
import { useT } from '@/contexts/language_context'
import { INTERACTIVE_GAMES } from './interactive-games'
import { getBackendUrl } from '@/lib/api/backend-url'
import { getAuthHeaders } from '@/lib/auth-headers'

// ─── Modality-engagement beacon (additive observability) ──────────────────────
// Fire-and-forget POST recording WHICH modality a learner opened for a concept,
// so the reviewer's Modality Effectiveness Lab can study modality → learning.
// Observational ONLY — it never feeds the MAB or the sealed evaluation, and it
// never changes any existing behavior here. Guarded so we beacon at most once
// per material per browser session.
const beaconedMaterials = new Set<string>()

function beaconMaterialView(mat: LearningMaterial, msSpent: number) {
  if (beaconedMaterials.has(mat.id)) return
  beaconedMaterials.add(mat.id)
  try {
    fetch(`${getBackendUrl()}/v3/learner/material-view`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
      body: JSON.stringify({
        concept_id: mat.concept_id,
        modality: mat.modality,
        grade_band: mat.grade_band ?? null,
        ms_spent: msSpent,
      }),
    }).catch(() => {})
  } catch {
    // fail silently — analytics must never break the /learn flow
  }
}

export interface LearningMaterial {
  id: string
  concept_id: string
  language: string
  modality: string
  archetype_tags: string[]
  title: string
  body?: string | null
  media_url?: string | null
  transcript?: string | null
  estimated_minutes: number
  difficulty: number
  /** Archetype personalization (set by the backend): match to the learner's
   * self-reported profile, and whether this is the single best-fit material. */
  match_score?: number
  best_fit?: boolean
  /** Concept grade-band (K-2/K-5/K-8/K-12), when the caller has it. Used only
   * by the observability beacon; optional and never required for rendering. */
  grade_band?: string | null
}

interface Props {
  materials: LearningMaterial[]
  loading: boolean
  onStartPractice: () => void
}

// ─── Read-state (localStorage) ────────────────────────────────────────────────

const READ_KEY = 'hcie_material_read'

function getReadMap(): Record<string, boolean> {
  if (typeof window === 'undefined') return {}
  try { return JSON.parse(localStorage.getItem(READ_KEY) || '{}') } catch { return {} }
}

function persistRead(id: string) {
  const m = getReadMap()
  m[id] = true
  try { localStorage.setItem(READ_KEY, JSON.stringify(m)) } catch { /* quota — non-fatal */ }
  return m
}

// ─── Text-to-speech (real audio modality without media files) ─────────────────

function stripForSpeech(s: string) {
  return s
    .replace(/```[\s\S]*?```/g, ' ')
    .replace(/^::: ?\w+$/gm, ' ')
    .replace(/^:::$/gm, ' ')
    .replace(/^#{2,3} /gm, '')
    .replace(/\*\*(.+?)\*\*/g, '$1')
    .replace(/\*(.+?)\*/g, '$1')
    .replace(/^\| .*$/gm, ' ')
    .replace(/^[-•] /gm, '')
}

function ListenButton({ text, language }: { text: string; language: string }) {
  const t = useT()
  const [speaking, setSpeaking] = useState(false)
  const [supported, setSupported] = useState(true)

  useEffect(() => {
    setSupported(typeof window !== 'undefined' && 'speechSynthesis' in window)
    return () => { try { window.speechSynthesis?.cancel() } catch { /* noop */ } }
  }, [])
  // Switching material stops any running narration.
  useEffect(() => {
    try { window.speechSynthesis?.cancel() } catch { /* noop */ }
    setSpeaking(false)
  }, [text])

  if (!supported) return null

  const toggle = () => {
    const synth = window.speechSynthesis
    if (speaking) { synth.cancel(); setSpeaking(false); return }
    const u = new SpeechSynthesisUtterance(stripForSpeech(text))
    const lang = language === 'id' ? 'id-ID' : 'en-US'
    u.lang = lang
    const voice = synth.getVoices().find(v => v.lang?.startsWith(language === 'id' ? 'id' : 'en'))
    if (voice) u.voice = voice
    u.rate = 0.98
    u.onend = () => setSpeaking(false)
    u.onerror = () => setSpeaking(false)
    synth.speak(u)
    setSpeaking(true)
  }

  return (
    <button type="button" onClick={toggle} style={{
      display: 'inline-flex', alignItems: 'center', gap: 6, padding: '7px 14px',
      borderRadius: 8, cursor: 'pointer', fontSize: 12, fontWeight: 700,
      border: `1px solid ${speaking ? '#C0392B' : '#2980B9'}`,
      background: speaking ? '#FDF0EE' : '#EBF5FB', color: speaking ? '#C0392B' : '#2980B9',
    }}>
      {speaking ? '■ ' + t('learn.material.stopListen', 'Stop') : '▶ ' + t('learn.material.listen', 'Listen')}
    </button>
  )
}

// ─── Callout / check-yourself blocks ─────────────────────────────────────────

const CALLOUT_META: Record<string, { icon: string; label: string; bg: string; border: string; fg: string }> = {
  tip:           { icon: '💡', label: 'Tip',            bg: '#EBF8F2', border: '#B7E0D7', fg: '#1B5E55' },
  warn:          { icon: '⚠️', label: 'Careful',        bg: '#FEF9E7', border: '#F5E3A2', fg: '#8A6D0B' },
  misconception: { icon: '🔄', label: 'Misconception',  bg: '#FDF0EE', border: '#F0C2BB', fg: '#A93226' },
}

function CheckBlock({ pairs, checkLabel, showLabel, hideLabel }: {
  pairs: { q: string; a: string }[]
  checkLabel: string
  showLabel: string
  hideLabel: string
}) {
  const [open, setOpen] = useState<Record<number, boolean>>({})
  return (
    <div style={{ background: '#F4F0FA', border: '1px solid #D6CCEC', borderRadius: 10,
                  padding: '12px 14px', margin: '12px 0' }}>
      <div style={{ fontSize: 11, fontWeight: 800, color: '#5B4B8A', textTransform: 'uppercase',
                    letterSpacing: '0.06em', marginBottom: 8 }}>
        ✓ {checkLabel}
      </div>
      {pairs.map((p, i) => (
        <div key={i} style={{ marginBottom: i < pairs.length - 1 ? 10 : 0 }}>
          <div style={{ fontSize: 13, color: '#2D3748', fontWeight: 600, lineHeight: 1.5 }}>{p.q}</div>
          {open[i] ? (
            <div style={{ fontSize: 13, color: '#1B5E55', background: '#EBF8F2',
                          border: '1px solid #B7E0D7', borderRadius: 6, padding: '7px 10px',
                          marginTop: 6, lineHeight: 1.55 }}>
              {p.a}
              <button type="button" onClick={() => setOpen(o => ({ ...o, [i]: false }))}
                style={{ marginLeft: 8, border: 'none', background: 'none', color: '#718096',
                         fontSize: 11, cursor: 'pointer' }}>
                {hideLabel}
              </button>
            </div>
          ) : (
            <button type="button" onClick={() => setOpen(o => ({ ...o, [i]: true }))}
              style={{ marginTop: 5, padding: '4px 10px', borderRadius: 6, cursor: 'pointer',
                       border: '1px solid #B4A7D6', background: '#fff', color: '#5B4B8A',
                       fontSize: 11, fontWeight: 700 }}>
              {showLabel}
            </button>
          )}
        </div>
      ))}
    </div>
  )
}

// ─── Markdown-ish renderer ────────────────────────────────────────────────────
// Supports: ## / ### headings, **bold**, *italic*, "- " and "1. " lists, code
// fences, "| a | b |" tables, and ::: check|tip|warn|misconception blocks.

function renderBody(body: string, labels: { check: string; show: string; hide: string }) {
  const lines = body.split('\n')
  const elements: ReactNode[] = []
  let i = 0
  while (i < lines.length) {
    const line = lines[i]
    const callout = line.match(/^::: ?(check|tip|warn|misconception)\s*$/)
    if (callout) {
      const kind = callout[1]
      const inner: string[] = []
      i++
      while (i < lines.length && !/^:::\s*$/.test(lines[i])) {
        inner.push(lines[i])
        i++
      }
      if (kind === 'check') {
        const pairs: { q: string; a: string }[] = []
        let q: string | null = null
        for (const l of inner) {
          if (l.startsWith('Q: ')) q = l.slice(3)
          else if (l.startsWith('A: ') && q) { pairs.push({ q, a: l.slice(3) }); q = null }
        }
        elements.push(<CheckBlock key={`chk-${i}`} pairs={pairs}
          checkLabel={labels.check} showLabel={labels.show} hideLabel={labels.hide} />)
      } else {
        const m = CALLOUT_META[kind]
        elements.push(
          <div key={`co-${i}`} style={{ background: m.bg, border: `1px solid ${m.border}`,
                                        borderRadius: 10, padding: '10px 14px', margin: '12px 0' }}>
            <div style={{ fontSize: 11, fontWeight: 800, color: m.fg, marginBottom: 4 }}>
              {m.icon} {m.label}
            </div>
            {inner.filter(l => l.trim()).map((l, li) => (
              <p key={li} style={{ fontSize: 13, color: m.fg, lineHeight: 1.6, margin: '3px 0' }}
                 dangerouslySetInnerHTML={{ __html: l
                   .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
                   .replace(/\*(.+?)\*/g, '<em>$1</em>') }} />
            ))}
          </div>
        )
      }
    } else if (line.startsWith('### ')) {
      elements.push(<h4 key={i} style={{ fontSize: 14, fontWeight: 700, margin: '16px 0 6px', color: '#2D3748' }}>{line.slice(4)}</h4>)
    } else if (line.startsWith('## ')) {
      elements.push(<h3 key={i} style={{ fontSize: 15, fontWeight: 700, margin: '18px 0 8px', color: '#1A2332' }}>{line.slice(3)}</h3>)
    } else if (line.startsWith('```')) {
      const codeLines: string[] = []
      i++
      while (i < lines.length && !lines[i].startsWith('```')) {
        codeLines.push(lines[i])
        i++
      }
      elements.push(
        <pre key={`code-${i}`} style={{
          background: '#1A2332', color: '#E2E8F0', padding: '12px 14px',
          borderRadius: 8, fontSize: 12, overflowX: 'auto', lineHeight: 1.5, margin: '8px 0',
        }}>{codeLines.join('\n')}</pre>
      )
    } else if (line.startsWith('| ')) {
      const tableLines: string[] = [line]
      i++
      while (i < lines.length && lines[i].startsWith('|')) {
        tableLines.push(lines[i])
        i++
      }
      i--
      const rows = tableLines.filter(l => !l.includes('---'))
      elements.push(
        <table key={`tbl-${i}`} style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12, margin: '10px 0' }}>
          <tbody>
            {rows.map((r, ri) => {
              const cells = r.split('|').filter(Boolean).map(c => c.trim())
              const Tag = ri === 0 ? 'th' : 'td'
              return (
                <tr key={ri} style={{ borderBottom: '1px solid #E2E8F0' }}>
                  {cells.map((c, ci) => (
                    <Tag key={ci} style={{ padding: '6px 10px', textAlign: 'left', fontWeight: ri === 0 ? 700 : 400 }}>{c}</Tag>
                  ))}
                </tr>
              )
            })}
          </tbody>
        </table>
      )
    } else if (/^\d+\.\s/.test(line)) {
      elements.push(<div key={i} style={{ fontSize: 13, color: '#4A5568', margin: '4px 0 4px 16px', lineHeight: 1.6 }}
        dangerouslySetInnerHTML={{ __html: line
          .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
          .replace(/\*(.+?)\*/g, '<em>$1</em>') }} />)
    } else if (line.startsWith('- ')) {
      elements.push(<div key={i} style={{ fontSize: 13, color: '#4A5568', margin: '3px 0 3px 12px', lineHeight: 1.6 }}
        dangerouslySetInnerHTML={{ __html: '• ' + line.slice(2)
          .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
          .replace(/\*(.+?)\*/g, '<em>$1</em>') }} />)
    } else if (line.startsWith('@interactive')) {
      // marker consumed by MaterialPane — not user-visible text
    } else if (line.trim() === '') {
      elements.push(<div key={i} style={{ height: 8 }} />)
    } else {
      const html = line
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
      elements.push(
        <p key={i} style={{ fontSize: 13, color: '#4A5568', lineHeight: 1.7, margin: '6px 0' }}
           dangerouslySetInnerHTML={{ __html: html }} />
      )
    }
    i++
  }
  return elements
}

// ─── Video placeholder (media in production — poster is honest about it) ─────

function VideoPlaceholder({ language, title }: { language: string; title: string }) {
  const [tapped, setTapped] = useState(false)
  const id = language === 'id'
  return (
    <div onClick={() => setTapped(true)} style={{
      marginBottom: 16, borderRadius: 10, aspectRatio: '16/9', cursor: 'pointer',
      background: 'linear-gradient(135deg, #1A2332, #2C3E50)', display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center', gap: 10, color: '#fff', position: 'relative',
    }}>
      <div style={{ width: 64, height: 64, borderRadius: 32, background: 'rgba(255,255,255,0.15)',
                    border: '2px solid rgba(255,255,255,0.5)', display: 'flex', alignItems: 'center',
                    justifyContent: 'center', fontSize: 26 }}>▶</div>
      <div style={{ fontSize: 13, fontWeight: 700, opacity: 0.9, padding: '0 24px', textAlign: 'center' }}>{title}</div>
      <div style={{ fontSize: 11, opacity: 0.7 }}>
        {tapped
          ? (id ? '🎬 Video pembelajaran sedang diproduksi — segera hadir' : '🎬 Learning video in production — coming soon')
          : (id ? 'Placeholder video · ketuk untuk info' : 'Video placeholder · tap for info')}
      </div>
    </div>
  )
}

// ─── Sequence helpers ─────────────────────────────────────────────────────────

const MODALITY_ICON: Record<string, string> = {
  reading: '📖', video: '▶', audio: '♪', diagram: '🗺', interactive: '⬡', example: '💡',
}

// Pedagogic ramp: easiest reading first, deepest last; diagrams/audio in between
// by their difficulty. (The backend's best-fit ordering still decides which
// single material is ✨-badged; the SEQUENCE is a study path, so it stays stable.)
function sequenced(materials: LearningMaterial[]) {
  return [...materials].sort((a, b) => a.difficulty - b.difficulty || a.id.localeCompare(b.id))
}

export function MaterialPane({ materials, loading, onStartPractice }: Props) {
  const t = useT()
  const seq = sequenced(materials)
  const [idx, setIdx] = useState(0)
  const [readMap, setReadMap] = useState<Record<string, boolean>>({})
  const matKey = seq.map(m => m.id).join(',')
  const readTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => { setIdx(0) }, [matKey])
  useEffect(() => { setReadMap(getReadMap()) }, [])

  const mat = seq[Math.min(idx, seq.length - 1)]

  // A material counts as "read" after it has been open for a few seconds —
  // enough to rule out accidental chip taps, cheap enough to never nag.
  useEffect(() => {
    if (!mat) return
    if (readTimer.current) clearTimeout(readTimer.current)
    const openedAt = Date.now()
    readTimer.current = setTimeout(() => {
      setReadMap(persistRead(mat.id))
      // Additive observability: record the modality this learner engaged with.
      // Fire-and-forget, once per material per session; never blocks read-state.
      beaconMaterialView(mat, Date.now() - openedAt)
    }, 4000)
    return () => { if (readTimer.current) clearTimeout(readTimer.current) }
  }, [mat?.id])

  if (loading) {
    return (
      <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 12, padding: 48, textAlign: 'center', color: '#718096' }}>
        <div style={{ fontSize: 28, marginBottom: 12 }}>📖</div>
        {t('learn.material.loading', 'Loading learning materials…')}
      </div>
    )
  }

  if (seq.length === 0) {
    return (
      <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 12, padding: 32, textAlign: 'center' }}>
        <div style={{ fontSize: 32, marginBottom: 12 }}>📭</div>
        <p style={{ fontSize: 13, color: '#718096', marginBottom: 16 }}>
          {t('learn.material.none', 'No learning materials for this concept yet. Jump straight to practice!')}
        </p>
        <button type="button" onClick={onStartPractice}
          style={{ padding: '10px 20px', borderRadius: 8, border: 'none', background: '#2980B9', color: '#fff', fontSize: 13, fontWeight: 700, cursor: 'pointer' }}>
          {t('learn.material.startPractice', 'Start practice →')}
        </button>
      </div>
    )
  }

  const readCount = seq.filter(m => readMap[m.id]).length
  const isLast = idx >= seq.length - 1
  const speechText = mat.transcript || mat.body || ''

  return (
    <div style={{ display: 'grid', gap: 16 }}>
      {/* Study-path chips: numbered sequence, read-state ticks, progress */}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
        <span style={{ fontSize: 11, color: '#718096' }}>{t('learn.material.path', 'Study path')}:</span>
        {seq.map((m, i) => (
          <button key={m.id} type="button" onClick={() => setIdx(i)} style={{
            display: 'flex', alignItems: 'center', gap: 6, padding: '5px 11px', borderRadius: 8, cursor: 'pointer', fontSize: 12, fontWeight: 600,
            border: `1px solid ${i === idx ? '#2980B9' : readMap[m.id] ? '#27AE60' : '#CBD5E0'}`,
            background: i === idx ? '#2980B9' : '#fff',
            color: i === idx ? '#fff' : readMap[m.id] ? '#1B5E55' : '#4A5568',
          }}>
            <span style={{ opacity: 0.75 }}>{i + 1}.</span>
            <span>{MODALITY_ICON[m.modality] ?? '📄'}</span>
            <span style={{ textTransform: 'capitalize' }}>{m.modality}</span>
            {readMap[m.id] && i !== idx && <span>✓</span>}
            {m.best_fit && <span title="Best fit for your learning style">✨</span>}
          </button>
        ))}
        <span style={{ fontSize: 11, color: '#A0AEC0', marginLeft: 'auto', fontVariantNumeric: 'tabular-nums' }}>
          {readCount}/{seq.length} {t('learn.material.read', 'read')}
        </span>
      </div>

      <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 12, padding: 24, boxShadow: '0 1px 4px rgba(0,0,0,0.06)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
          <span style={{ fontSize: 20 }}>{MODALITY_ICON[mat.modality] ?? '📄'}</span>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 10, color: '#A0AEC0', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
              {t('learn.material.label', 'Learning material')} · {mat.modality} · ~{mat.estimated_minutes} min
              {mat.best_fit && <span style={{ marginLeft: 8, color: '#6C3483', fontWeight: 700 }}>✨ matches your style</span>}
            </div>
            <h2 style={{ fontSize: 18, fontWeight: 800, color: '#1A2332', margin: 0 }}>{mat.title}</h2>
          </div>
          {/* Narrated playback: real for audio, available for every material */}
          {speechText && (mat.modality === 'audio' || mat.modality === 'reading') && (
            <ListenButton text={speechText} language={mat.language} />
          )}
        </div>

        {/* Video placeholder — honest "in production" poster when no media yet. */}
        {!mat.media_url && mat.modality === 'video' && (
          <VideoPlaceholder language={mat.language} title={mat.title} />
        )}

        {/* Interactive activity — body carries an `@interactive <key>` marker. */}
        {mat.modality === 'interactive' && (() => {
          const key = mat.body?.match(/^@interactive (\w+)/m)?.[1]
          const Game = key ? INTERACTIVE_GAMES[key] : undefined
          return Game ? (
            <div style={{ marginBottom: 16 }}>
              <Game language={mat.language} onDone={onStartPractice} />
            </div>
          ) : null
        })()}

        {mat.media_url && mat.modality === 'video' && (
          <div style={{ marginBottom: 16, borderRadius: 8, overflow: 'hidden', aspectRatio: '16/9', background: '#000' }}>
            <iframe src={mat.media_url} style={{ width: '100%', height: '100%', border: 'none' }} allowFullScreen title={mat.title} />
          </div>
        )}
        {mat.media_url && mat.modality === 'audio' && (
          <audio controls src={mat.media_url} style={{ width: '100%', marginBottom: 16 }} />
        )}

        {/* Audio without a media file = narration script + TTS playback. Show the
            script as readable paragraphs rather than a collapsed transcript. */}
        {mat.modality === 'audio' && !mat.media_url && mat.transcript ? (
          <div style={{ borderTop: '1px solid #EDF2F7', paddingTop: 16 }}>
            {mat.transcript.split(/\n{2,}|\n/).filter(p => p.trim()).map((p, pi) => (
              <p key={pi} style={{ fontSize: 13.5, color: '#4A5568', lineHeight: 1.8, margin: '8px 0' }}>{p}</p>
            ))}
          </div>
        ) : (
          <>
            {mat.body && (
              <div style={{ borderTop: '1px solid #EDF2F7', paddingTop: 16 }}>
                {renderBody(mat.body, {
                  check: t('learn.material.checkYourself', 'Check yourself'),
                  show: t('learn.material.showAnswer', 'Show answer'),
                  hide: t('learn.material.hideAnswer', 'hide'),
                })}
              </div>
            )}
            {mat.transcript && (
              <details style={{ marginTop: 16, fontSize: 12, color: '#718096' }}>
                <summary style={{ cursor: 'pointer', fontWeight: 600 }}>{t('learn.material.transcript', 'Transcript')}</summary>
                <p style={{ marginTop: 8, lineHeight: 1.6 }}>{mat.transcript}</p>
              </details>
            )}
          </>
        )}
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
        <div style={{ fontSize: 12, color: '#718096' }}>
          {isLast
            ? t('learn.material.pathDone', 'End of the study path — time to practice.')
            : `${t('learn.material.upNext', 'Up next')}: ${MODALITY_ICON[seq[idx + 1].modality] ?? '📄'} ${seq[idx + 1].title}`}
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          {!isLast && (
            <button type="button" onClick={() => setIdx(i => Math.min(i + 1, seq.length - 1))}
              style={{ padding: '12px 20px', borderRadius: 8, border: '1px solid #2980B9', background: '#fff',
                       color: '#2980B9', fontSize: 14, fontWeight: 700, cursor: 'pointer' }}>
              {t('learn.material.next', 'Next material →')}
            </button>
          )}
          <button type="button" onClick={onStartPractice}
            style={{ padding: '12px 24px', borderRadius: 8, border: 'none', background: '#27AE60', color: '#fff',
                     fontSize: 14, fontWeight: 700, cursor: 'pointer', boxShadow: '0 2px 8px rgba(39,174,96,0.3)' }}>
            {t('learn.material.donePractice', 'Done — try a question →')}
          </button>
        </div>
      </div>
    </div>
  )
}
