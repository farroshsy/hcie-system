'use client'

/**
 * TaskBody — renders one DemoTask by kind and reports a TaskSignal upward.
 *
 * Each sub-renderer owns its local interaction state and emits the canonical
 * answer + client-graded correctness + the kind-specific signal (the "Signal"
 * column of the task-type design table). The parent /learn page consumes the
 * signal for submit (answer, correct, complete) and can surface `detail`.
 */

import { useEffect, useMemo, useState } from 'react'
import {
  DemoTask, TaskSignal, TASK_KIND_META,
  McqTask, TraceTask, ParsonsTask, ParsonsBlock, CodeWriteTask,
  BlockProgramTask, CaseStudyTask, DataInterpTask, DiagramLabelTask,
  VideoQuestionTask, AudioListenTask,
} from '@/lib/catalog/task-types'

// ─── shared bits ────────────────────────────────────────────────────────────────
const codeBox: React.CSSProperties = {
  fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace',
  fontSize: 13, lineHeight: 1.6, background: '#1A2332', color: '#E2E8F0',
  borderRadius: 8, padding: '14px 16px', whiteSpace: 'pre', overflowX: 'auto',
}
const btn = (active: boolean, color = '#1A5276'): React.CSSProperties => ({
  textAlign: 'left', padding: '10px 14px', borderRadius: 8,
  border: `2px solid ${active ? color : '#E2E8F0'}`,
  background: active ? '#EBF5FB' : '#fff', cursor: 'pointer',
  fontSize: 14, color: '#1A2332', transition: 'all 0.15s',
})
const miniBtn: React.CSSProperties = {
  border: '1px solid #CBD5E0', background: '#fff', borderRadius: 6,
  width: 28, height: 28, cursor: 'pointer', fontSize: 14, color: '#2D3748',
  display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
}
function arraysEqual(a: string[], b: string[]) {
  return a.length === b.length && a.every((x, i) => x === b[i])
}
function norm(s: string) { return s.replace(/\s+/g, ' ').trim().toLowerCase() }
// Stable, deterministic shuffle (no Math.random — keeps SSR/demo reproducible).
function stableShuffle<T>(items: T[], salt: string, key: (t: T) => string): T[] {
  const h = (s: string) => { let n = 7; for (const c of s) n = (n * 31 + c.charCodeAt(0)) >>> 0; return n }
  return [...items].sort((a, b) => h(salt + key(a)) - h(salt + key(b)))
}

export function TaskBody(
  { task, disabled, onSignal }:
  { task: DemoTask; disabled?: boolean; onSignal: (s: TaskSignal) => void },
) {
  switch (task.kind) {
    case 'mcq':                 return <McqBody t={task} disabled={disabled} onSignal={onSignal} />
    case 'trace':               return <TraceBody t={task} disabled={disabled} onSignal={onSignal} />
    case 'parsons':             return <ParsonsBody t={task} disabled={disabled} onSignal={onSignal} />
    case 'code_write':          return <CodeWriteBody t={task} disabled={disabled} onSignal={onSignal} />
    case 'block_program':       return <BlockProgramBody t={task} disabled={disabled} onSignal={onSignal} />
    case 'case_study':          return <CaseStudyBody t={task} disabled={disabled} onSignal={onSignal} />
    case 'data_interpretation': return <DataInterpBody t={task} disabled={disabled} onSignal={onSignal} />
    case 'diagram_label':       return <DiagramLabelBody t={task} disabled={disabled} onSignal={onSignal} />
    case 'video_question':      return <VideoQuestionBody t={task} disabled={disabled} onSignal={onSignal} />
    case 'audio_listen':        return <AudioListenBody t={task} disabled={disabled} onSignal={onSignal} />
  }
}

// ─── mcq ──────────────────────────────────────────────────────────────────────
function McqBody({ t, disabled, onSignal }: { t: McqTask; disabled?: boolean; onSignal: (s: TaskSignal) => void }) {
  const [sel, setSel] = useState<number | null>(null)
  useEffect(() => {
    onSignal({
      kind: 'mcq', answer: sel != null ? t.choices[sel] : '',
      correct: sel != null ? sel === t.correctIndex : null,
      complete: sel != null, detail: { correct: sel === t.correctIndex },
    })
  }, [sel]) // eslint-disable-line react-hooks/exhaustive-deps
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {t.choices.map((c, i) => (
        <button key={i} disabled={disabled} onClick={() => setSel(i)} style={btn(sel === i)}>
          <span style={{ fontWeight: 700, color: '#718096', marginRight: 10 }}>{String.fromCharCode(65 + i)}.</span>
          {c}
        </button>
      ))}
    </div>
  )
}

function embedUrl(url: string): string {
  try {
    const u = new URL(url)
    if (u.hostname.includes('youtube.com') && u.searchParams.get('v')) {
      return `https://www.youtube.com/embed/${u.searchParams.get('v')}`
    }
    if (u.hostname === 'youtu.be') {
      return `https://www.youtube.com/embed/${u.pathname.replace('/', '')}`
    }
    if (u.hostname.includes('vimeo.com') && !u.hostname.includes('player.')) {
      return `https://player.vimeo.com/video/${u.pathname.replace('/', '')}`
    }
  } catch { /* leave unchanged */ }
  return url
}

function MediaChoices(
  { choices, correctIndex, disabled, color, selected, setSelected }:
  {
    choices: string[]
    correctIndex: number
    disabled?: boolean
    color: string
    selected: number | null
    setSelected: (i: number) => void
  },
) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {choices.map((c, i) => (
        <button key={i} disabled={disabled} onClick={() => setSelected(i)} style={btn(selected === i, color)}>
          <span style={{ fontWeight: 700, color: '#718096', marginRight: 10 }}>{String.fromCharCode(65 + i)}.</span>
          {c}
        </button>
      ))}
      {selected != null && selected === correctIndex && (
        <div style={{ fontSize: 12, color: '#1E8449', fontWeight: 700 }}>Correct choice selected.</div>
      )}
    </div>
  )
}

function Transcript({ text }: { text?: string }) {
  const [show, setShow] = useState(false)
  if (!text) return null
  return (
    <div>
      <button
        type="button"
        onClick={() => setShow(s => !s)}
        style={{ ...miniBtn, width: 'auto', padding: '5px 10px', fontSize: 12 }}
      >
        {show ? 'Hide transcript' : 'Show transcript'}
      </button>
      {show && (
        <div style={{
          marginTop: 8, padding: '10px 12px', borderRadius: 8,
          border: '1px solid #E2E8F0', background: '#F8FAFC',
          color: '#4A5568', fontSize: 13, lineHeight: 1.55,
        }}>
          {text}
        </div>
      )}
    </div>
  )
}

function VideoQuestionBody({ t, disabled, onSignal }: { t: VideoQuestionTask; disabled?: boolean; onSignal: (s: TaskSignal) => void }) {
  const [sel, setSel] = useState<number | null>(null)
  const [progress, setProgress] = useState(0)
  const media = embedUrl(t.mediaUrl)
  const iframe = /youtube\.com\/embed|player\.vimeo\.com/.test(media)
  useEffect(() => {
    onSignal({
      kind: 'video_question',
      answer: sel != null ? t.choices[sel] : '',
      correct: sel != null ? sel === t.correctIndex : null,
      complete: sel != null,
      detail: { correct: sel === t.correctIndex, mediaProgress: progress, mediaType: 'video' },
    })
  }, [sel, progress]) // eslint-disable-line react-hooks/exhaustive-deps
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      <div style={{ overflow: 'hidden', borderRadius: 10, border: '1px solid #E2E8F0', background: '#000' }}>
        {iframe ? (
          <iframe
            title={t.title}
            src={media}
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
            onLoad={() => setProgress(p => Math.max(p, 0.25))}
            style={{ width: '100%', aspectRatio: '16 / 9', border: 0, display: 'block' }}
          />
        ) : (
          <video
            controls
            src={media}
            onTimeUpdate={e => {
              const el = e.currentTarget
              if (el.duration > 0) setProgress(Math.max(progress, el.currentTime / el.duration))
            }}
            style={{ width: '100%', display: 'block' }}
          />
        )}
      </div>
      <Transcript text={t.transcript} />
      <MediaChoices choices={t.choices} correctIndex={t.correctIndex} disabled={disabled}
                    color="#C0392B" selected={sel} setSelected={setSel} />
    </div>
  )
}

function AudioListenBody({ t, disabled, onSignal }: { t: AudioListenTask; disabled?: boolean; onSignal: (s: TaskSignal) => void }) {
  const [sel, setSel] = useState<number | null>(null)
  const [progress, setProgress] = useState(0)
  useEffect(() => {
    onSignal({
      kind: 'audio_listen',
      answer: sel != null ? t.choices[sel] : '',
      correct: sel != null ? sel === t.correctIndex : null,
      complete: sel != null,
      detail: { correct: sel === t.correctIndex, mediaProgress: progress, mediaType: 'audio' },
    })
  }, [sel, progress]) // eslint-disable-line react-hooks/exhaustive-deps
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      <div style={{
        padding: 14, borderRadius: 10, border: '1px solid #D2B4DE',
        background: '#F4ECF7',
      }}>
        <audio
          controls
          src={t.mediaUrl}
          onTimeUpdate={e => {
            const el = e.currentTarget
            if (el.duration > 0) setProgress(Math.max(progress, el.currentTime / el.duration))
          }}
          style={{ width: '100%' }}
        />
      </div>
      <Transcript text={t.transcript} />
      <MediaChoices choices={t.choices} correctIndex={t.correctIndex} disabled={disabled}
                    color="#6C3483" selected={sel} setSelected={setSel} />
    </div>
  )
}

// ─── trace (predict output, count steps viewed) ─────────────────────────────────
function TraceBody({ t, disabled, onSignal }: { t: TraceTask; disabled?: boolean; onSignal: (s: TaskSignal) => void }) {
  const [revealed, setRevealed] = useState(0)
  const [sel, setSel] = useState<number | null>(null)
  const [text, setText] = useState('')
  const pred = t.outputChoices ? (sel != null ? t.outputChoices[sel] : '') : text
  useEffect(() => {
    onSignal({
      kind: 'trace', answer: pred,
      correct: pred ? norm(pred) === norm(t.expectedOutput) : null,
      complete: pred.trim().length > 0,
      detail: { predicted: pred, expected: t.expectedOutput, stepsViewed: revealed },
    })
  }, [pred, revealed]) // eslint-disable-line react-hooks/exhaustive-deps
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      <pre style={codeBox}>{t.code}</pre>
      <div style={{ border: '1px solid #E2E8F0', borderRadius: 8, padding: 12, background: '#F8FAFC' }}>
        <div style={{ fontSize: 11, fontWeight: 700, color: '#718096', textTransform: 'uppercase', marginBottom: 8 }}>
          Step through it ({revealed}/{t.steps.length} revealed)
        </div>
        {t.steps.slice(0, revealed).map((s, i) => (
          <div key={i} style={{ fontFamily: 'ui-monospace, monospace', fontSize: 13, color: '#2D3748', padding: '2px 0' }}>{s}</div>
        ))}
        {revealed < t.steps.length && (
          <button disabled={disabled} onClick={() => setRevealed(r => r + 1)}
            style={{ ...miniBtn, width: 'auto', padding: '4px 12px', marginTop: 8, fontSize: 12 }}>
            Reveal next step
          </button>
        )}
      </div>
      <div>
        <div style={{ fontSize: 13, fontWeight: 700, color: '#2D3748', marginBottom: 8 }}>What does it print?</div>
        {t.outputChoices
          ? <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {t.outputChoices.map((c, i) => (
                <button key={i} disabled={disabled} onClick={() => setSel(i)} style={{ ...btn(sel === i), minWidth: 56, textAlign: 'center' }}>{c}</button>
              ))}
            </div>
          : <input disabled={disabled} value={text} onChange={e => setText(e.target.value)} placeholder="output…"
              style={{ padding: '10px 12px', border: '2px solid #E2E8F0', borderRadius: 8, fontSize: 14, width: 200 }} />}
      </div>
    </div>
  )
}

// ─── parsons (order + indent, drop distractors) ─────────────────────────────────
interface PItem { id: string; text: string; indent: number; isDistractor: boolean }
function ParsonsBody({ t, disabled, onSignal }: { t: ParsonsTask; disabled?: boolean; onSignal: (s: TaskSignal) => void }) {
  const initial = useMemo<PItem[]>(() => {
    const real = t.blocks.map(b => ({ id: b.id, text: b.text, indent: 0, isDistractor: false }))
    const dis = (t.distractors ?? []).map(d => ({ id: d.id, text: d.text, indent: 0, isDistractor: true }))
    return stableShuffle([...real, ...dis], t.id, x => x.id)
  }, [t])
  const [items, setItems] = useState<PItem[]>(initial)
  useEffect(() => { setItems(initial) }, [initial])

  const move = (i: number, d: number) => setItems(prev => {
    const j = i + d; if (j < 0 || j >= prev.length) return prev
    const next = [...prev];[next[i], next[j]] = [next[j], next[i]]; return next
  })
  const indent = (i: number, d: number) => setItems(prev => prev.map((it, k) => k === i ? { ...it, indent: Math.max(0, Math.min(3, it.indent + d)) } : it))
  const remove = (i: number) => setItems(prev => prev.filter((_, k) => k !== i))

  useEffect(() => {
    const kept = items.filter(it => !it.isDistractor)
    const distractorsUsed = items.filter(it => it.isDistractor).length
    const orderOk = arraysEqual(items.map(it => it.id), t.blocks.map(b => b.id))
    const indentOk = items.length === t.blocks.length &&
      items.every((it, k) => t.blocks[k] && it.id === t.blocks[k].id && it.indent === t.blocks[k].indent)
    const correct = distractorsUsed === 0 && orderOk && indentOk
    onSignal({
      kind: 'parsons',
      answer: items.map(it => `${'  '.repeat(it.indent)}${it.text}`).join('\n'),
      correct, complete: items.length > 0,
      detail: { order: items.map(it => it.id), indents: items.map(it => it.indent), distractorsUsed },
    })
  }, [items]) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      {items.map((it, i) => (
        <div key={it.id} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <button disabled={disabled || i === 0} onClick={() => move(i, -1)} style={{ ...miniBtn, height: 18, width: 22 }}>▲</button>
            <button disabled={disabled || i === items.length - 1} onClick={() => move(i, 1)} style={{ ...miniBtn, height: 18, width: 22 }}>▼</button>
          </div>
          <div style={{
            flex: 1, marginLeft: it.indent * 28, fontFamily: 'ui-monospace, monospace', fontSize: 13,
            padding: '10px 12px', borderRadius: 6, color: '#1A2332',
            background: it.isDistractor ? '#FEF5F5' : '#F1F5F9',
            border: `1px solid ${it.isDistractor ? '#F5B7B1' : '#E2E8F0'}`,
          }}>{it.text}</div>
          <button disabled={disabled} title="indent out" onClick={() => indent(i, -1)} style={miniBtn}>⇤</button>
          <button disabled={disabled} title="indent in" onClick={() => indent(i, 1)} style={miniBtn}>⇥</button>
          <button disabled={disabled} title="remove block" onClick={() => remove(i)} style={{ ...miniBtn, color: '#C0392B' }}>✕</button>
        </div>
      ))}
      <div style={{ fontSize: 11, color: '#718096', marginTop: 4 }}>Use ▲▼ to order, ⇤⇥ to indent, ✕ to drop a block that doesn’t belong.</div>
    </div>
  )
}

// ─── code_write (token-heuristic test grader, demo) ─────────────────────────────
function CodeWriteBody({ t, disabled, onSignal }: { t: CodeWriteTask; disabled?: boolean; onSignal: (s: TaskSignal) => void }) {
  const [code, setCode] = useState(t.starter)
  const [results, setResults] = useState<boolean[] | null>(null)
  const run = () => setResults(t.tests.map(test => test.mustInclude.every(tok => norm(code).includes(norm(tok)))))
  useEffect(() => {
    const passed = results ?? []
    onSignal({
      kind: 'code_write', answer: code,
      correct: results ? results.every(Boolean) : null,
      complete: results != null,
      detail: { code, testsPassed: passed },
    })
  }, [code, results]) // eslint-disable-line react-hooks/exhaustive-deps
  // editing invalidates a previous run
  useEffect(() => { setResults(null) }, [code])
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <textarea disabled={disabled} value={code} onChange={e => setCode(e.target.value)} spellCheck={false}
        style={{ ...codeBox, width: '100%', minHeight: 150, resize: 'vertical', boxSizing: 'border-box', whiteSpace: 'pre', tabSize: 4 }} />
      <div>
        <button disabled={disabled} onClick={run}
          style={{ padding: '8px 18px', background: '#2C3E50', color: '#fff', border: 'none', borderRadius: 8, fontSize: 13, fontWeight: 700, cursor: 'pointer' }}>
          Run tests
        </button>
      </div>
      {results && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          {t.tests.map((test, i) => (
            <div key={i} style={{ fontSize: 13, color: results[i] ? '#1E8449' : '#C0392B', display: 'flex', gap: 8 }}>
              <span>{results[i] ? '✓' : '✕'}</span><span>{test.name}</span>
            </div>
          ))}
          <div style={{ fontSize: 12, color: '#718096', marginTop: 4 }}>
            {results.filter(Boolean).length}/{results.length} tests pass
          </div>
        </div>
      )}
    </div>
  )
}

// ─── block_program (build a sequence from a palette) ────────────────────────────
function BlockProgramBody({ t, disabled, onSignal }: { t: BlockProgramTask; disabled?: boolean; onSignal: (s: TaskSignal) => void }) {
  const [seq, setSeq] = useState<string[]>([])
  useEffect(() => {
    const flags = {
      hasLoop: seq.some(b => /repeat|loop|for|while/i.test(b)),
      hasBranch: seq.some(b => /if|else|when/i.test(b)),
      matchesTarget: arraysEqual(seq, t.target),
    }
    onSignal({
      kind: 'block_program', answer: seq.join(' → '),
      correct: seq.length ? arraysEqual(seq, t.target) : null,
      complete: seq.length > 0, detail: { sequence: seq, structureFlags: flags },
    })
  }, [seq]) // eslint-disable-line react-hooks/exhaustive-deps
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      <div style={{ fontSize: 12, color: '#718096' }}>{t.goal}</div>
      <div>
        <div style={{ fontSize: 11, fontWeight: 700, color: '#718096', textTransform: 'uppercase', marginBottom: 6 }}>Blocks</div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {t.palette.map((b, i) => (
            <button key={i} disabled={disabled} onClick={() => setSeq(s => [...s, b])}
              style={{ padding: '8px 14px', background: '#FEF3E7', border: '1px solid #F0B27A', borderRadius: 18, fontSize: 13, color: '#7E5109', cursor: 'pointer' }}>
              + {b}
            </button>
          ))}
        </div>
      </div>
      <div>
        <div style={{ fontSize: 11, fontWeight: 700, color: '#718096', textTransform: 'uppercase', marginBottom: 6 }}>Your program</div>
        {seq.length === 0
          ? <div style={{ fontSize: 13, color: '#A0AEC0', fontStyle: 'italic' }}>Click blocks above to build your program…</div>
          : <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              {seq.map((b, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ fontSize: 12, color: '#A0AEC0', width: 18 }}>{i + 1}</span>
                  <div style={{ flex: 1, padding: '8px 12px', background: '#D35400', color: '#fff', borderRadius: 6, fontSize: 13 }}>{b}</div>
                  <button disabled={disabled} onClick={() => setSeq(s => s.filter((_, k) => k !== i))} style={{ ...miniBtn, color: '#C0392B' }}>✕</button>
                </div>
              ))}
            </div>}
        {seq.length > 0 && (
          <button disabled={disabled} onClick={() => setSeq([])} style={{ ...miniBtn, width: 'auto', padding: '4px 12px', marginTop: 8, fontSize: 12 }}>Clear</button>
        )}
      </div>
    </div>
  )
}

// ─── case_study (decide + justify) ──────────────────────────────────────────────
function CaseStudyBody({ t, disabled, onSignal }: { t: CaseStudyTask; disabled?: boolean; onSignal: (s: TaskSignal) => void }) {
  const [choice, setChoice] = useState<string | null>(null)
  const [reasoning, setReasoning] = useState('')
  useEffect(() => {
    const opt = t.options.find(o => o.id === choice)
    onSignal({
      kind: 'case_study',
      answer: opt ? `${opt.text} — ${reasoning}` : '',
      correct: choice ? choice === t.correctId : null,
      complete: choice != null && reasoning.trim().length > 0,
      detail: { decision: choice, reasoning, sound: opt?.sound ?? null },
    })
  }, [choice, reasoning]) // eslint-disable-line react-hooks/exhaustive-deps
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      <div style={{ background: '#FDF2F2', border: '1px solid #F5B7B1', borderRadius: 8, padding: '12px 14px', fontSize: 14, color: '#2D3748', lineHeight: 1.6 }}>
        {t.scenario}
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {t.options.map(o => (
          <button key={o.id} disabled={disabled} onClick={() => setChoice(o.id)} style={btn(choice === o.id, '#C0392B')}>{o.text}</button>
        ))}
      </div>
      <div>
        <div style={{ fontSize: 13, fontWeight: 700, color: '#2D3748', marginBottom: 6 }}>{t.reasoningPrompt}</div>
        <textarea disabled={disabled} value={reasoning} onChange={e => setReasoning(e.target.value)} placeholder="Your reasoning…"
          style={{ width: '100%', minHeight: 70, padding: 12, border: '2px solid #E2E8F0', borderRadius: 8, fontSize: 14, resize: 'vertical', boxSizing: 'border-box' }} />
      </div>
    </div>
  )
}

// ─── data_interpretation (read a table, answer) ─────────────────────────────────
function DataInterpBody({ t, disabled, onSignal }: { t: DataInterpTask; disabled?: boolean; onSignal: (s: TaskSignal) => void }) {
  const [sel, setSel] = useState<number | null>(null)
  useEffect(() => {
    onSignal({
      kind: 'data_interpretation', answer: sel != null ? t.choices[sel] : '',
      correct: sel != null ? sel === t.correctIndex : null,
      complete: sel != null, detail: { answer: sel != null ? t.choices[sel] : null },
    })
  }, [sel]) // eslint-disable-line react-hooks/exhaustive-deps
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      <div style={{ overflowX: 'auto' }}>
        <table style={{ borderCollapse: 'collapse', width: '100%', fontSize: 13 }}>
          <thead>
            <tr>{t.table.headers.map((h, i) => (
              <th key={i} style={{ textAlign: 'left', padding: '8px 12px', background: '#1F618D', color: '#fff', border: '1px solid #1A5276' }}>{h}</th>
            ))}</tr>
          </thead>
          <tbody>
            {t.table.rows.map((r, ri) => (
              <tr key={ri} style={{ background: ri % 2 ? '#F8FAFC' : '#fff' }}>
                {r.map((c, ci) => (<td key={ci} style={{ padding: '8px 12px', border: '1px solid #E2E8F0', color: '#2D3748' }}>{c}</td>))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {t.choices.map((c, i) => (
          <button key={i} disabled={disabled} onClick={() => setSel(i)} style={btn(sel === i, '#1F618D')}>
            <span style={{ fontWeight: 700, color: '#718096', marginRight: 10 }}>{String.fromCharCode(65 + i)}.</span>{c}
          </button>
        ))}
      </div>
    </div>
  )
}

// ─── diagram_label (assign labels to parts of a topology) ───────────────────────
function DiagramLabelBody({ t, disabled, onSignal }: { t: DiagramLabelTask; disabled?: boolean; onSignal: (s: TaskSignal) => void }) {
  const [labels, setLabels] = useState<Record<string, string>>({})
  useEffect(() => {
    const allFilled = t.slots.every(s => labels[s.id])
    const correct = t.slots.every(s => labels[s.id] === s.answer)
    onSignal({
      kind: 'diagram_label',
      answer: t.slots.map(s => `${s.id}=${labels[s.id] ?? '?'}`).join(', '),
      correct: allFilled ? correct : null, complete: allFilled,
      detail: { labels },
    })
  }, [labels]) // eslint-disable-line react-hooks/exhaustive-deps
  const icon = (i: number) => ['🖥️', '📶', '🌐', '🗄️'][i] ?? '⬡'
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 4, padding: '8px 0' }}>
        {t.slots.map((s, i) => (
          <div key={s.id} style={{ display: 'contents' }}>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8, minWidth: 96 }}>
              <div style={{ fontSize: 30 }}>{icon(i)}</div>
              <select disabled={disabled} value={labels[s.id] ?? ''} onChange={e => setLabels(l => ({ ...l, [s.id]: e.target.value }))}
                style={{
                  padding: '6px 8px', borderRadius: 6, fontSize: 13,
                  border: `2px solid ${labels[s.id] ? (labels[s.id] === s.answer ? '#27AE60' : '#117A65') : '#E2E8F0'}`,
                  color: '#1A2332', background: '#fff',
                }}>
                <option value="">— label —</option>
                {t.bank.map(b => <option key={b} value={b}>{b}</option>)}
              </select>
            </div>
            {i < t.slots.length - 1 && <div style={{ flex: 1, height: 2, background: '#CBD5E0', minWidth: 16 }} />}
          </div>
        ))}
      </div>
      <div style={{ fontSize: 11, color: '#718096' }}>Pick the label for each node along the path from your device to a website’s server.</div>
    </div>
  )
}
