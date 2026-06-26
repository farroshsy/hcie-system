'use client'

import { useState, useEffect, type ReactNode } from 'react'
import { useT } from '@/contexts/language_context'

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
}

interface Props {
  materials: LearningMaterial[]
  loading: boolean
  onStartPractice: () => void
}

/** Minimal markdown-ish renderer: headings, bold, lists, code fences. */
function renderBody(body: string) {
  const lines = body.split('\n')
  const elements: ReactNode[] = []
  let i = 0
  while (i < lines.length) {
    const line = lines[i]
    if (line.startsWith('### ')) {
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
      elements.push(<div key={i} style={{ fontSize: 13, color: '#4A5568', margin: '4px 0 4px 16px', lineHeight: 1.6 }}>{line}</div>)
    } else if (line.startsWith('- ')) {
      elements.push(<div key={i} style={{ fontSize: 13, color: '#4A5568', margin: '3px 0 3px 12px', lineHeight: 1.6 }}>• {line.slice(2)}</div>)
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

const MODALITY_ICON: Record<string, string> = {
  reading: '📖', video: '▶', audio: '♪', diagram: '🗺', interactive: '⬡', example: '💡',
}

export function MaterialPane({ materials, loading, onStartPractice }: Props) {
  const t = useT()
  // Which material is shown. Backend returns them best-archetype-fit first, so
  // index 0 defaults to the learner's preferred format; the chips let them switch.
  const [idx, setIdx] = useState(0)
  const matKey = materials.map(m => m.id).join(',')
  useEffect(() => { setIdx(0) }, [matKey])

  if (loading) {
    return (
      <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 12, padding: 48, textAlign: 'center', color: '#718096' }}>
        <div style={{ fontSize: 28, marginBottom: 12 }}>📖</div>
        {t('learn.material.loading', 'Loading learning materials…')}
      </div>
    )
  }

  if (materials.length === 0) {
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

  const mat = materials[Math.min(idx, materials.length - 1)]

  return (
    <div style={{ display: 'grid', gap: 16 }}>
      {materials.length > 1 && (
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
          <span style={{ fontSize: 11, color: '#718096' }}>{t('learn.material.format', 'Format')}:</span>
          {materials.map((m, i) => (
            <button key={m.id} type="button" onClick={() => setIdx(i)} style={{
              display: 'flex', alignItems: 'center', gap: 6, padding: '5px 11px', borderRadius: 8, cursor: 'pointer', fontSize: 12, fontWeight: 600,
              border: `1px solid ${i === idx ? '#2980B9' : '#CBD5E0'}`, background: i === idx ? '#2980B9' : '#fff', color: i === idx ? '#fff' : '#4A5568',
            }}>
              <span>{MODALITY_ICON[m.modality] ?? '📄'}</span>
              <span style={{ textTransform: 'capitalize' }}>{m.modality}</span>
              {m.best_fit && <span title="Best fit for your learning style">✨</span>}
            </button>
          ))}
        </div>
      )}
      <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 12, padding: 24, boxShadow: '0 1px 4px rgba(0,0,0,0.06)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
          <span style={{ fontSize: 20 }}>{MODALITY_ICON[mat.modality] ?? '📄'}</span>
          <div>
            <div style={{ fontSize: 10, color: '#A0AEC0', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
              {t('learn.material.label', 'Learning material')} · {mat.modality} · ~{mat.estimated_minutes} min
              {mat.best_fit && <span style={{ marginLeft: 8, color: '#6C3483', fontWeight: 700 }}>✨ matches your style</span>}
            </div>
            <h2 style={{ fontSize: 18, fontWeight: 800, color: '#1A2332', margin: 0 }}>{mat.title}</h2>
          </div>
        </div>

        {mat.media_url && mat.modality === 'video' && (
          <div style={{ marginBottom: 16, borderRadius: 8, overflow: 'hidden', aspectRatio: '16/9', background: '#000' }}>
            <iframe src={mat.media_url} style={{ width: '100%', height: '100%', border: 'none' }} allowFullScreen title={mat.title} />
          </div>
        )}
        {mat.media_url && mat.modality === 'audio' && (
          <audio controls src={mat.media_url} style={{ width: '100%', marginBottom: 16 }} />
        )}

        {mat.body && (
          <div style={{ borderTop: '1px solid #EDF2F7', paddingTop: 16 }}>
            {renderBody(mat.body)}
          </div>
        )}

        {mat.transcript && (
          <details style={{ marginTop: 16, fontSize: 12, color: '#718096' }}>
            <summary style={{ cursor: 'pointer', fontWeight: 600 }}>{t('learn.material.transcript', 'Transcript')}</summary>
            <p style={{ marginTop: 8, lineHeight: 1.6 }}>{mat.transcript}</p>
          </details>
        )}
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
        <button type="button" onClick={onStartPractice}
          style={{ padding: '12px 24px', borderRadius: 8, border: 'none', background: '#27AE60', color: '#fff', fontSize: 14, fontWeight: 700, cursor: 'pointer', boxShadow: '0 2px 8px rgba(39,174,96,0.3)' }}>
          {t('learn.material.donePractice', 'Done — try a question →')}
        </button>
      </div>
    </div>
  )
}
