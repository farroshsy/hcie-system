'use client'

/**
 * Interactive showcase activities — 5 traditional-Javanese-game experiences,
 * each teaching one CS concept and ending in the SAME practice loop the thesis
 * evaluates (completion → onDone() → practice tab → /v3/learner/attempt →
 * trajectory → live-session). Observability rides the existing pipeline —
 * no new event tables, no purposeless data.
 *
 * Sound: Web Audio synthesis only (gamelan slendro tones, feedback cues) —
 * zero media files, works in any browser and in the Expo WebView.
 *
 * Registry key = marker in learning_materials.body: `@interactive <key>`.
 */

import { useState, type ComponentType } from 'react'

// ─── Shared audio (lazy singleton; requires first user gesture) ───────────────

let _ctx: AudioContext | null = null
function ctx(): AudioContext | null {
  if (typeof window === 'undefined') return null
  try {
    if (!_ctx) _ctx = new (window.AudioContext || (window as any).webkitAudioContext)()
    if (_ctx.state === 'suspended') _ctx.resume()
    return _ctx
  } catch { return null }
}

/** Gamelan-ish strike: base sine + detuned partial, fast decay. */
function strike(freq: number, dur = 0.7, gain = 0.25) {
  const c = ctx(); if (!c) return
  const t = c.currentTime
  const g = c.createGain()
  g.gain.setValueAtTime(gain, t)
  g.gain.exponentialRampToValueAtTime(0.001, t + dur)
  g.connect(c.destination)
  for (const [mult, amt] of [[1, 1], [2.76, 0.35], [5.4, 0.12]] as const) {
    const o = c.createOscillator()
    o.type = 'sine'
    o.frequency.value = freq * mult
    const og = c.createGain(); og.gain.value = amt
    o.connect(og); og.connect(g)
    o.start(t); o.stop(t + dur)
  }
}

// Slendro-approx pentatonic (barang, gulu, dhada, lima, nem)
export const SLENDRO = [270, 305, 342, 392, 436]

function cueSuccess() { [0, 1, 2, 4].forEach((n, i) => setTimeout(() => strike(SLENDRO[n], 0.5, 0.2), i * 110)) }
function cueFail() { strike(120, 0.4, 0.3); setTimeout(() => strike(95, 0.5, 0.3), 130) }
function cueTap() { strike(SLENDRO[2], 0.15, 0.08) }

// ─── Shared UI bits ───────────────────────────────────────────────────────────

const C = {
  ink: '#1A2332', body: '#4A5568', muted: '#718096', line: '#E2E8F0',
  blue: '#2980B9', green: '#27AE60', red: '#C0392B', amber: '#B7791F',
  gold: '#B8860B', wood: '#6B4226', woodDark: '#4A2E1A',
}

function GameShell({ title, objective, steps, children, stats }: {
  title: string; objective: string; steps?: string
  children: React.ReactNode
  stats: { attempts: number; mistakes: number; done: boolean }
}) {
  return (
    <div style={{ border: `1px solid ${C.line}`, borderRadius: 12, overflow: 'hidden', background: '#fff' }}>
      <div style={{ padding: '12px 16px', background: '#F7FAFC', borderBottom: `1px solid ${C.line}` }}>
        <div style={{ fontSize: 15, fontWeight: 800, color: C.ink }}>{title}</div>
        <div style={{ fontSize: 12, color: C.body, marginTop: 2 }}>🎯 {objective}</div>
        {steps && <div style={{ fontSize: 11, color: C.muted, marginTop: 2 }}>{steps}</div>}
      </div>
      <div style={{ padding: 16 }}>{children}</div>
      <div style={{ padding: '8px 16px', borderTop: `1px solid ${C.line}`, display: 'flex', gap: 16,
                    fontSize: 11, color: C.muted }}>
        <span>▶ {stats.attempts}</span>
        <span style={{ color: stats.mistakes ? C.red : C.muted }}>✗ {stats.mistakes}</span>
        {stats.done && <span style={{ color: C.green, fontWeight: 700 }}>✓ selesai</span>}
      </div>
    </div>
  )
}

function DoneCard({ language, mistakes, onDone }: { language: string; mistakes: number; onDone: () => void }) {
  const id = language === 'id'
  return (
    <div style={{ textAlign: 'center', padding: 18, background: '#EBF8F2', border: '1px solid #B7E0D7',
                  borderRadius: 10, marginTop: 12 }}>
      <div style={{ fontSize: 26 }}>🎉</div>
      <div style={{ fontSize: 14, fontWeight: 800, color: '#1B5E55', margin: '4px 0' }}>
        {id ? 'Berhasil!' : 'You did it!'}
      </div>
      <div style={{ fontSize: 12, color: '#1B5E55', marginBottom: 10 }}>
        {id ? `Kesalahan: ${mistakes} — sekarang buktikan pemahamanmu di soal latihan.`
            : `Mistakes: ${mistakes} — now prove it on a practice question.`}
      </div>
      <button type="button" onClick={onDone} style={{ padding: '10px 22px', borderRadius: 8, border: 'none',
        background: C.green, color: '#fff', fontSize: 13, fontWeight: 700, cursor: 'pointer' }}>
        {id ? 'Lanjut latihan →' : 'Try a question →'}
      </button>
    </div>
  )
}

export interface GameProps { language: string; onDone: () => void }

// ─── 1. GAMELAN — susun urutan nada = algoritma (k2/k5_algorithms) ───────────

const NOTE_COLORS = ['#C0392B', '#B7791F', '#27AE60', '#2980B9', '#6C3483']
const NOTE_NAMES = ['ji', 'ro', 'lu', 'ma', 'nem']

export function GamelanGame({ language, onDone }: GameProps) {
  const id = language === 'id'
  const ROUNDS = [[0, 2, 4], [4, 2, 1, 0], [0, 1, 2, 4, 3]]
  const [round, setRound] = useState(0)
  const [seq, setSeq] = useState<number[]>([])
  const [attempts, setAttempts] = useState(0)
  const [mistakes, setMistakes] = useState(0)
  const [playing, setPlaying] = useState(false)
  const [done, setDone] = useState(false)
  const target = ROUNDS[round]

  const playSeq = (s: number[], after?: () => void) => {
    setPlaying(true)
    s.forEach((n, i) => setTimeout(() => strike(SLENDRO[n]), i * 450))
    setTimeout(() => { setPlaying(false); after?.() }, s.length * 450 + 200)
  }

  const check = () => {
    setAttempts(a => a + 1)
    playSeq(seq, () => {
      if (seq.join() === target.join()) {
        cueSuccess()
        if (round + 1 >= ROUNDS.length) setDone(true)
        else { setRound(r => r + 1); setSeq([]) }
      } else { cueFail(); setMistakes(m => m + 1); setSeq([]) }
    })
  }

  return (
    <GameShell
      title={id ? '🎶 Gamelan — Rakit Melodinya' : '🎶 Gamelan — Build the Melody'}
      objective={id ? 'Algoritma = urutan langkah yang tepat. Susun balok nada persis seperti target, lalu mainkan.'
                    : 'An algorithm = exact ordered steps. Arrange the note blocks to match the target, then play.'}
      steps={id ? `Ronde ${round + 1}/3 · dengar target, susun, mainkan` : `Round ${round + 1}/3 · listen, arrange, play`}
      stats={{ attempts, mistakes, done }}>
      {/* Target sequence (colored blocks, Blockly-flavored) */}
      <div style={{ display: 'flex', gap: 6, alignItems: 'center', marginBottom: 10, flexWrap: 'wrap' }}>
        <span style={{ fontSize: 11, color: C.muted }}>{id ? 'Target:' : 'Target:'}</span>
        {target.map((n, i) => (
          <span key={i} style={{ width: 34, height: 26, borderRadius: 6, background: NOTE_COLORS[n],
            color: '#fff', fontSize: 11, fontWeight: 800, display: 'inline-flex', alignItems: 'center',
            justifyContent: 'center' }}>{NOTE_NAMES[n]}</span>
        ))}
        <button type="button" disabled={playing} onClick={() => playSeq(target)}
          style={{ marginLeft: 6, padding: '4px 10px', borderRadius: 6, border: `1px solid ${C.blue}`,
                   background: '#fff', color: C.blue, fontSize: 11, fontWeight: 700, cursor: 'pointer' }}>
          ▶ {id ? 'dengar' : 'listen'}
        </button>
      </div>
      {/* Player sequence */}
      <div style={{ minHeight: 34, display: 'flex', gap: 6, alignItems: 'center', padding: 6,
                    background: '#F7FAFC', border: `1px dashed ${C.line}`, borderRadius: 8, marginBottom: 12 }}>
        {seq.length === 0 && <span style={{ fontSize: 11, color: C.muted }}>
          {id ? 'susunanmu muncul di sini…' : 'your sequence appears here…'}</span>}
        {seq.map((n, i) => (
          <span key={i} onClick={() => setSeq(s => s.filter((_, j) => j !== i))}
            style={{ width: 34, height: 26, borderRadius: 6, background: NOTE_COLORS[n], color: '#fff',
                     fontSize: 11, fontWeight: 800, display: 'inline-flex', alignItems: 'center',
                     justifyContent: 'center', cursor: 'pointer' }} title={id ? 'ketuk untuk hapus' : 'tap to remove'}>
            {NOTE_NAMES[n]}</span>
        ))}
      </div>
      {/* Saron keys */}
      <div style={{ display: 'flex', gap: 8, justifyContent: 'center', marginBottom: 12 }}>
        {SLENDRO.map((f, n) => (
          <button key={n} type="button" disabled={done}
            onClick={() => { strike(f); if (seq.length < target.length) setSeq(s => [...s, n]) }}
            style={{ flex: 1, maxWidth: 76, height: 84, borderRadius: '8px 8px 14px 14px',
                     border: `2px solid ${C.woodDark}`, cursor: 'pointer',
                     background: `linear-gradient(${C.gold}, #8a6508)`, boxShadow: '0 3px 0 #4A2E1A' }}>
            <span style={{ display: 'block', fontSize: 13, fontWeight: 800, color: '#fff' }}>{NOTE_NAMES[n]}</span>
            <span style={{ display: 'block', width: 18, height: 18, borderRadius: 9, background: NOTE_COLORS[n],
                           margin: '6px auto 0' }} />
          </button>
        ))}
      </div>
      {!done && (
        <button type="button" disabled={seq.length !== target.length || playing} onClick={check}
          style={{ width: '100%', padding: 12, borderRadius: 8, border: 'none', fontSize: 13, fontWeight: 800,
                   cursor: seq.length === target.length ? 'pointer' : 'not-allowed',
                   background: seq.length === target.length ? C.green : C.line,
                   color: seq.length === target.length ? '#fff' : C.muted }}>
          ▶ {id ? 'Mainkan susunanku' : 'Play my sequence'}
        </button>
      )}
      {done && <DoneCard language={language} mistakes={mistakes} onDone={onDone} />}
    </GameShell>
  )
}

// ─── 2. CONGKLAK — lubang = variabel menyimpan nilai (k2/k5_variables) ────────

export function CongklakGame({ language, onDone }: GameProps) {
  const id = language === 'id'
  type Round = { start: number[]; op: string; opEn: string; apply: (h: number[]) => number[]; ask: number }
  const ROUNDS: Round[] = [
    { start: [4, 2, 5], op: 'Tambahkan 3 biji ke lubang B', opEn: 'Add 3 seeds to hole B',
      apply: h => [h[0], h[1] + 3, h[2]], ask: 1 },
    { start: [6, 3, 2], op: 'Pindahkan 2 biji dari A ke C', opEn: 'Move 2 seeds from A to C',
      apply: h => [h[0] - 2, h[1], h[2] + 2], ask: 2 },
    { start: [5, 4, 3], op: 'Kosongkan B, sebar 2 ke A dan 2 ke C', opEn: 'Empty B, deal 2 to A and 2 to C',
      apply: h => [h[0] + 2, 0, h[2] + 2], ask: 1 },
  ]
  const [round, setRound] = useState(0)
  const [holes, setHoles] = useState(ROUNDS[0].start)
  const [applied, setApplied] = useState(false)
  const [attempts, setAttempts] = useState(0)
  const [mistakes, setMistakes] = useState(0)
  const [done, setDone] = useState(false)
  const r = ROUNDS[round]
  const answer = r.apply(r.start)[r.ask]
  const options = [answer, answer + 2, Math.max(0, answer - 2)].sort(() => 0.5 - ((round * 7 + 3) % 10) / 10)

  const pick = (v: number) => {
    setAttempts(a => a + 1)
    if (v === answer) {
      cueSuccess(); setApplied(true); setHoles(r.apply(r.start))
      setTimeout(() => {
        if (round + 1 >= ROUNDS.length) setDone(true)
        else { const nr = round + 1; setRound(nr); setHoles(ROUNDS[nr].start); setApplied(false) }
      }, 1200)
    } else { cueFail(); setMistakes(m => m + 1) }
  }

  const label = ['A', 'B', 'C']
  return (
    <GameShell
      title={id ? '🥥 Congklak — Lubang Penyimpan Nilai' : '🥥 Congklak — Holes that Store Values'}
      objective={id ? 'Variabel = tempat menyimpan nilai yang bisa berubah. Setiap lubang congklak adalah variabel.'
                    : 'A variable = a named place storing a changeable value. Each congklak hole is a variable.'}
      steps={id ? `Ronde ${round + 1}/3` : `Round ${round + 1}/3`}
      stats={{ attempts, mistakes, done }}>
      <div style={{ display: 'flex', gap: 12, justifyContent: 'center', padding: '14px 8px',
                    background: `linear-gradient(${C.wood}, ${C.woodDark})`, borderRadius: 40, marginBottom: 12 }}>
        {holes.map((n, i) => (
          <div key={i} style={{ textAlign: 'center' }}>
            <div style={{ width: 76, height: 76, borderRadius: 38, background: '#2E1B0F',
                          boxShadow: 'inset 0 4px 10px rgba(0,0,0,0.7)', display: 'flex', flexWrap: 'wrap',
                          alignItems: 'center', justifyContent: 'center', gap: 2, padding: 10 }}>
              {Array.from({ length: Math.min(n, 12) }).map((_, s) => (
                <span key={s} style={{ width: 9, height: 9, borderRadius: 5,
                  background: ['#E8D8B0', '#D9C08A', '#C9A96B'][s % 3] }} />
              ))}
            </div>
            <div style={{ fontSize: 12, fontWeight: 800, color: '#F0E4C8', marginTop: 4 }}>
              {label[i]} = {n}
            </div>
          </div>
        ))}
      </div>
      <div style={{ fontSize: 13, color: C.ink, fontWeight: 600, textAlign: 'center', marginBottom: 10 }}>
        {id ? r.op : r.opEn}.&nbsp;
        {id ? <>Setelah itu, <code>{label[r.ask]}</code> berisi berapa?</>
            : <>Afterwards, what does <code>{label[r.ask]}</code> hold?</>}
      </div>
      {!done && !applied && (
        <div style={{ display: 'flex', gap: 8, justifyContent: 'center' }}>
          {options.map(v => (
            <button key={v} type="button" onClick={() => { cueTap(); pick(v) }}
              style={{ padding: '10px 22px', borderRadius: 8, border: `2px solid ${C.blue}`,
                       background: '#fff', color: C.blue, fontSize: 15, fontWeight: 800, cursor: 'pointer' }}>
              {v}
            </button>
          ))}
        </div>
      )}
      {applied && !done && (
        <div style={{ textAlign: 'center', fontSize: 12, color: C.green, fontWeight: 700 }}>
          ✓ {id ? 'Benar — lihat isi lubang berubah' : 'Correct — watch the hole update'}
        </div>
      )}
      {done && <DoneCard language={language} mistakes={mistakes} onDone={onDone} />}
    </GameShell>
  )
}

// ─── 3. GOBAK SODOR — percabangan JIKA/MAKA (k5/k8_control) ──────────────────

export function GobakSodorGame({ language, onDone }: GameProps) {
  const id = language === 'id'
  // Guard column per row (0..2); player must pick a DIFFERENT column via the rule.
  const GUARDS = [1, 0, 2, 1]
  const [row, setRow] = useState(0)
  const [pos, setPos] = useState(1)
  const [attempts, setAttempts] = useState(0)
  const [mistakes, setMistakes] = useState(0)
  const [done, setDone] = useState(false)
  const cols = [id ? 'kiri' : 'left', id ? 'tengah' : 'middle', id ? 'kanan' : 'right']

  const move = (col: number) => {
    setAttempts(a => a + 1); cueTap()
    if (col === GUARDS[row]) {
      cueFail(); setMistakes(m => m + 1)
    } else {
      setPos(col)
      if (row + 1 >= GUARDS.length) { cueSuccess(); setDone(true) }
      else setRow(r => r + 1)
    }
  }

  return (
    <GameShell
      title={id ? '🏃 Gobak Sodor — Lolos dengan JIKA/MAKA' : '🏃 Gobak Sodor — Escape with IF/THEN'}
      objective={id ? 'Percabangan: JIKA penjaga di satu jalur, MAKA lari lewat jalur lain. Satu aturan per baris.'
                    : 'Conditionals: IF the guard blocks a lane, THEN run through another. One rule per row.'}
      steps={id ? `Baris ${Math.min(row + 1, GUARDS.length)}/${GUARDS.length}` : `Row ${Math.min(row + 1, GUARDS.length)}/${GUARDS.length}`}
      stats={{ attempts, mistakes, done }}>
      <div style={{ display: 'grid', gap: 6, marginBottom: 12 }}>
        {GUARDS.map((g, ri) => (
          <div key={ri} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 6,
                                 opacity: ri < row ? 0.45 : 1 }}>
            {cols.map((_, ci) => (
              <div key={ci} style={{ height: 44, borderRadius: 8, display: 'flex', alignItems: 'center',
                justifyContent: 'center', fontSize: 20,
                background: ri === row ? '#FEF9E7' : '#F7FAFC',
                border: `2px solid ${ri === row ? C.amber : C.line}` }}>
                {g === ci ? '🧍' : ''}
                {ri === row - 1 && ci === pos ? '👟' : ''}
              </div>
            ))}
          </div>
        ))}
        <div style={{ textAlign: 'center', fontSize: 11, color: C.green, fontWeight: 700 }}>
          {id ? '⬇ garis finis' : '⬇ finish line'}
        </div>
      </div>
      {!done && (
        <div>
          <div style={{ fontSize: 12.5, color: C.ink, fontWeight: 600, textAlign: 'center', marginBottom: 8 }}>
            {id ? <>Penjaga di <b>{cols[GUARDS[row]]}</b>. Lengkapi: JIKA penjaga di {cols[GUARDS[row]]} MAKA lari lewat…</>
                : <>Guard is <b>{cols[GUARDS[row]]}</b>. Complete: IF guard at {cols[GUARDS[row]]} THEN run through…</>}
          </div>
          <div style={{ display: 'flex', gap: 8, justifyContent: 'center' }}>
            {cols.map((c, ci) => (
              <button key={ci} type="button" onClick={() => move(ci)}
                style={{ padding: '10px 18px', borderRadius: 8, border: `2px solid ${C.blue}`,
                         background: '#fff', color: C.blue, fontSize: 13, fontWeight: 800, cursor: 'pointer' }}>
                {c}
              </button>
            ))}
          </div>
        </div>
      )}
      {done && <DoneCard language={language} mistakes={mistakes} onDone={onDone} />}
    </GameShell>
  )
}

// ─── 4. ENGKLEK — perulangan ULANGI×N (k2_control / loops) ────────────────────

export function EngklekGame({ language, onDone }: GameProps) {
  const id = language === 'id'
  // Course: single, single, double, single, double, single = pattern [1,2] × 3 after start? Keep: target loop [lompat-1, lompat-2] × 3
  const COURSE = [1, 2, 1, 2, 1, 2] // hop sizes
  const [blocks, setBlocks] = useState<number[]>([])
  const [repeat, setRepeat] = useState(2)
  const [running, setRunning] = useState(false)
  const [hopIdx, setHopIdx] = useState(-1)
  const [attempts, setAttempts] = useState(0)
  const [mistakes, setMistakes] = useState(0)
  const [done, setDone] = useState(false)
  const squares = COURSE.reduce((s, h) => s + h, 0) // 9 cells

  const run = () => {
    setAttempts(a => a + 1); setRunning(true); setHopIdx(-1)
    const plan: number[] = []
    for (let r = 0; r < repeat; r++) plan.push(...blocks)
    const ok = plan.join() === COURSE.join()
    plan.slice(0, Math.min(plan.length, COURSE.length)).forEach((_, i) =>
      setTimeout(() => { setHopIdx(i); strike(SLENDRO[i % 5], 0.2, 0.12) }, i * 380))
    setTimeout(() => {
      setRunning(false)
      if (ok) { cueSuccess(); setDone(true) }
      else { cueFail(); setMistakes(m => m + 1); setHopIdx(-1) }
    }, Math.min(plan.length, COURSE.length) * 380 + 250)
  }

  // cells covered after each hop for token position
  let acc = 0
  const hopEnds = COURSE.map(h => (acc += h))

  return (
    <GameShell
      title={id ? '🦶 Engklek — ULANGI Pola Lompatan' : '🦶 Engklek — REPEAT the Hop Pattern'}
      objective={id ? 'Perulangan: pola [lompat-1, lompat-2] tidak ditulis 3 kali — ditulis sekali lalu DIULANG ×3.'
                    : 'Loops: the pattern [hop-1, hop-2] is not written 3 times — written once, REPEATED ×3.'}
      steps={id ? 'Susun blok, atur ulangan, jalankan' : 'Build blocks, set repeats, run'}
      stats={{ attempts, mistakes, done }}>
      {/* Course */}
      <div style={{ display: 'flex', gap: 4, justifyContent: 'center', marginBottom: 14, flexWrap: 'wrap' }}>
        {Array.from({ length: squares }).map((_, i) => {
          const reached = hopIdx >= 0 && i < (hopEnds[Math.min(hopIdx, hopEnds.length - 1)] ?? 0)
          return (
            <div key={i} style={{ width: 34, height: 42, borderRadius: 6, display: 'flex', alignItems: 'center',
              justifyContent: 'center', fontSize: 15, fontWeight: 800,
              background: reached ? '#EBF8F2' : '#F7FAFC',
              border: `2px solid ${reached ? C.green : C.line}`, color: C.muted }}>
              {hopIdx >= 0 && hopEnds[hopIdx] === i + 1 ? '🦶' : i + 1}
            </div>
          )
        })}
      </div>
      {/* Program: ULANGI n × [blocks] */}
      <div style={{ background: '#F4F0FA', border: '1px solid #D6CCEC', borderRadius: 10, padding: 12, marginBottom: 12 }}>
        <div style={{ fontSize: 11, fontWeight: 800, color: '#5B4B8A', marginBottom: 8 }}>
          {id ? 'PROGRAM-MU' : 'YOUR PROGRAM'}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          <span style={{ fontSize: 12, fontWeight: 800, color: '#5B4B8A' }}>{id ? 'ULANGI' : 'REPEAT'}</span>
          {[2, 3, 4].map(n => (
            <button key={n} type="button" onClick={() => { cueTap(); setRepeat(n) }}
              style={{ width: 34, height: 30, borderRadius: 6, fontWeight: 800, cursor: 'pointer',
                       border: `2px solid ${repeat === n ? '#5B4B8A' : C.line}`,
                       background: repeat === n ? '#5B4B8A' : '#fff', color: repeat === n ? '#fff' : C.body }}>
              {n}×
            </button>
          ))}
          <span style={{ fontSize: 14, color: '#5B4B8A' }}>[</span>
          {blocks.map((b, i) => (
            <span key={i} onClick={() => setBlocks(s => s.filter((_, j) => j !== i))}
              style={{ padding: '5px 10px', borderRadius: 6, background: b === 1 ? C.blue : C.amber, color: '#fff',
                       fontSize: 11, fontWeight: 800, cursor: 'pointer' }}>
              {id ? `lompat-${b}` : `hop-${b}`}</span>
          ))}
          {blocks.length === 0 && <span style={{ fontSize: 11, color: C.muted }}>{id ? 'kosong' : 'empty'}</span>}
          <span style={{ fontSize: 14, color: '#5B4B8A' }}>]</span>
        </div>
        <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
          {[1, 2].map(b => (
            <button key={b} type="button" disabled={blocks.length >= 3}
              onClick={() => { cueTap(); setBlocks(s => [...s, b]) }}
              style={{ padding: '7px 12px', borderRadius: 6, border: `1px dashed ${b === 1 ? C.blue : C.amber}`,
                       background: '#fff', color: b === 1 ? C.blue : C.amber, fontSize: 11, fontWeight: 800,
                       cursor: 'pointer' }}>
              + {id ? `lompat-${b}` : `hop-${b}`} ({b === 1 ? (id ? '1 kotak' : '1 square') : (id ? '2 kotak' : '2 squares')})
            </button>
          ))}
        </div>
      </div>
      {!done && (
        <button type="button" disabled={blocks.length === 0 || running} onClick={run}
          style={{ width: '100%', padding: 12, borderRadius: 8, border: 'none', fontSize: 13, fontWeight: 800,
                   background: blocks.length && !running ? C.green : C.line,
                   color: blocks.length && !running ? '#fff' : C.muted,
                   cursor: blocks.length && !running ? 'pointer' : 'not-allowed' }}>
          ▶ {id ? 'Jalankan program' : 'Run program'}
        </button>
      )}
      {done && <DoneCard language={language} mistakes={mistakes} onDone={onDone} />}
    </GameShell>
  )
}

// ─── 5. BATIK CAP — modul motif dipakai ulang (k5/k8_modularity) ──────────────

const MOTIFS = ['◆', '❋', '☾'] as const

export function BatikGame({ language, onDone }: GameProps) {
  const id = language === 'id'
  // Round: target module (2×2 of motif indices), canvas repeats it 4×.
  const ROUNDS = [
    [0, 1, 1, 0],
    [2, 0, 0, 1],
  ]
  const [round, setRound] = useState(0)
  const [cell, setCell] = useState<(number | null)[]>([null, null, null, null])
  const [brush, setBrush] = useState(0)
  const [stamped, setStamped] = useState(false)
  const [attempts, setAttempts] = useState(0)
  const [mistakes, setMistakes] = useState(0)
  const [done, setDone] = useState(false)
  const target = ROUNDS[round]

  const stamp = () => {
    setAttempts(a => a + 1)
    if (cell.join() === target.join()) {
      cueSuccess(); setStamped(true)
      setTimeout(() => {
        if (round + 1 >= ROUNDS.length) setDone(true)
        else { setRound(r => r + 1); setCell([null, null, null, null]); setStamped(false) }
      }, 1600)
    } else { cueFail(); setMistakes(m => m + 1) }
  }

  const Module = ({ cells, size = 26, faded = false }: { cells: (number | null)[]; size?: number; faded?: boolean }) => (
    <div style={{ display: 'grid', gridTemplateColumns: `repeat(2, ${size}px)`, gap: 2, opacity: faded ? 0.9 : 1 }}>
      {cells.map((m, i) => (
        <div key={i} style={{ width: size, height: size, borderRadius: 4, background: '#3B2415',
          color: '#E8C56A', display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: size * 0.55, border: '1px solid #5A3A22' }}>
          {m != null ? MOTIFS[m] : ''}
        </div>
      ))}
    </div>
  )

  return (
    <GameShell
      title={id ? '🖼 Batik Cap — Satu Modul, Dipakai Berulang' : '🖼 Batik Stamp — One Module, Reused'}
      objective={id ? 'Modularitas: rancang SATU modul motif, lalu "panggil" modul itu berulang untuk mengisi kain.'
                    : 'Modularity: design ONE motif module, then "call" it repeatedly to fill the cloth.'}
      steps={id ? `Ronde ${round + 1}/2 · samakan modulmu dengan target` : `Round ${round + 1}/2 · match your module to the target`}
      stats={{ attempts, mistakes, done }}>
      <div style={{ display: 'flex', gap: 20, justifyContent: 'center', alignItems: 'flex-start',
                    flexWrap: 'wrap', marginBottom: 12 }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 11, color: C.muted, marginBottom: 4 }}>{id ? 'Modul target' : 'Target module'}</div>
          <Module cells={target} />
        </div>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 11, color: C.muted, marginBottom: 4 }}>
            {id ? 'Modulmu (ketuk sel untuk mengecap)' : 'Your module (tap a cell to stamp)'}
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 40px)', gap: 3 }}>
            {cell.map((m, i) => (
              <button key={i} type="button" onClick={() => { cueTap(); setCell(c => c.map((v, j) => j === i ? brush : v)) }}
                style={{ width: 40, height: 40, borderRadius: 5, background: '#3B2415', color: '#E8C56A',
                         fontSize: 20, border: `2px solid ${m != null ? '#B8860B' : '#5A3A22'}`, cursor: 'pointer' }}>
                {m != null ? MOTIFS[m] : '·'}
              </button>
            ))}
          </div>
          <div style={{ display: 'flex', gap: 6, justifyContent: 'center', marginTop: 8 }}>
            {MOTIFS.map((mo, i) => (
              <button key={i} type="button" onClick={() => { cueTap(); setBrush(i) }}
                style={{ width: 34, height: 34, borderRadius: 6, fontSize: 16, cursor: 'pointer',
                         border: `2px solid ${brush === i ? C.gold : C.line}`,
                         background: brush === i ? '#FEF6E0' : '#fff' }}>
                {mo}
              </button>
            ))}
          </div>
        </div>
      </div>
      {/* Cloth: module called ×4 */}
      <div style={{ textAlign: 'center', marginBottom: 12 }}>
        <div style={{ fontSize: 11, color: C.muted, marginBottom: 4 }}>
          {id ? 'Kain — modul dipanggil 4×' : 'Cloth — module called 4×'}
        </div>
        <div style={{ display: 'inline-flex', gap: 4, padding: 8, background: '#2E1B0F', borderRadius: 8 }}>
          {Array.from({ length: 4 }).map((_, k) => (
            <Module key={k} cells={stamped ? cell : [null, null, null, null]} size={18} faded />
          ))}
        </div>
      </div>
      {!done && (
        <button type="button" disabled={cell.some(c => c == null)} onClick={stamp}
          style={{ width: '100%', padding: 12, borderRadius: 8, border: 'none', fontSize: 13, fontWeight: 800,
                   background: cell.every(c => c != null) ? C.green : C.line,
                   color: cell.every(c => c != null) ? '#fff' : C.muted,
                   cursor: cell.every(c => c != null) ? 'pointer' : 'not-allowed' }}>
          🖐 {id ? 'Cap ke kain (panggil modul ×4)' : 'Stamp the cloth (call module ×4)'}
        </button>
      )}
      {done && <DoneCard language={language} mistakes={mistakes} onDone={onDone} />}
    </GameShell>
  )
}

// ─── 6. EXECUTION TRACE — input → proses → output (k5_control / k2_algorithms) ─
// "Coding feel, not syntax": watch a tiny program READ input, step through in
// plain language, update its memory boxes, and produce output. Concept: find the
// biggest number — a loop + compare + store. Zero real-language syntax.

export function ExecutionTraceGame({ language, onDone }: GameProps) {
  const id = language === 'id'
  const INPUT = [3, 7, 2, 9, 5] // fixed, deterministic

  // Plain-language "program" — one step per animation tick, bilingual.
  const PROGRAM = [
    { id: 'AMBIL', text: id ? 'AMBIL angka pertama → simpan sebagai "terbesar"' : 'TAKE the first number → store it as "biggest"' },
    { id: 'AMBIL_BERIKUT', text: id ? 'AMBIL angka berikutnya dari daftar' : 'TAKE the next number from the list' },
    { id: 'BANDINGKAN', text: id ? 'BANDINGKAN: apakah angka ini > "terbesar"?' : 'COMPARE: is this number > "biggest"?' },
    { id: 'SIMPAN', text: id ? 'JIKA ya, SIMPAN angka ini sebagai "terbesar"' : 'IF yes, STORE this number as "biggest"' },
    { id: 'ULANGI', text: id ? 'ULANGI sampai daftar habis' : 'REPEAT until the list is empty' },
    { id: 'KELUARKAN', text: id ? 'KELUARKAN "terbesar" sebagai hasil' : 'OUTPUT "biggest" as the result' },
  ]

  // Build the frame-by-frame trace once (deterministic).
  type Frame = { step: number; idx: number; biggest: number; cur: number | null; updated: boolean; note: string }
  const frames: Frame[] = []
  let biggest = INPUT[0]
  frames.push({ step: 0, idx: 0, biggest, cur: INPUT[0], updated: true,
    note: id ? `terbesar = ${INPUT[0]} (angka pertama)` : `biggest = ${INPUT[0]} (first number)` })
  for (let i = 1; i < INPUT.length; i++) {
    const cur = INPUT[i]
    frames.push({ step: 1, idx: i, biggest, cur, updated: false,
      note: id ? `ambil angka: ${cur}` : `take number: ${cur}` })
    const bigger = cur > biggest
    frames.push({ step: 2, idx: i, biggest, cur, updated: false,
      note: id ? `${cur} > ${biggest}? ${bigger ? 'YA' : 'TIDAK'}` : `${cur} > ${biggest}? ${bigger ? 'YES' : 'NO'}` })
    if (bigger) {
      biggest = cur
      frames.push({ step: 3, idx: i, biggest, cur, updated: true,
        note: id ? `simpan: terbesar = ${cur}` : `store: biggest = ${cur}` })
    } else {
      frames.push({ step: 3, idx: i, biggest, cur, updated: false,
        note: id ? 'tidak diubah' : 'no change' })
    }
    frames.push({ step: 4, idx: i, biggest, cur: null, updated: false,
      note: id ? 'ulangi…' : 'repeat…' })
  }
  frames.push({ step: 5, idx: INPUT.length - 1, biggest, cur: null, updated: true,
    note: id ? `HASIL = ${biggest}` : `RESULT = ${biggest}` })

  const [fi, setFi] = useState(-1) // -1 = not started
  const [running, setRunning] = useState(false)
  const [attempts, setAttempts] = useState(0)
  const [done, setDone] = useState(false)
  const frame = fi >= 0 ? frames[fi] : null

  const run = () => {
    if (running) return
    setAttempts(a => a + 1); setRunning(true); setFi(-1)
    frames.forEach((f, i) => setTimeout(() => {
      setFi(i)
      if (f.updated) strike(SLENDRO[Math.min(i, 4)], 0.2, 0.12); else cueTap()
    }, i * 700))
    setTimeout(() => { setRunning(false); cueSuccess(); setDone(true) }, frames.length * 700 + 200)
  }

  const activeStep = frame ? frame.step : -1
  return (
    <GameShell
      title={id ? '⚙️ Jejak Program — Cari Angka Terbesar' : '⚙️ Execution Trace — Find the Biggest Number'}
      objective={id ? 'Komputer MEMBACA masukan, MEMPROSES langkah demi langkah, lalu memberi keluaran. Tekan ▶ dan amati.'
                    : 'A computer READS input, PROCESSES it step by step, then gives output. Press ▶ and watch.'}
      steps={id ? 'masukan → proses → keluaran (tanpa sintaks)' : 'input → process → output (no syntax)'}
      stats={{ attempts, mistakes: 0, done }}>
      {/* Input row */}
      <div style={{ marginBottom: 12 }}>
        <div style={{ fontSize: 11, fontWeight: 800, color: C.blue, marginBottom: 6 }}>
          {id ? 'MASUKAN — daftar angka' : 'INPUT — list of numbers'}
        </div>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          {INPUT.map((n, i) => {
            const isCur = frame != null && frame.idx === i && frame.step >= 1 && frame.step <= 4
            const isRead = frame != null && i <= frame.idx
            return (
              <span key={i} style={{ width: 40, height: 40, borderRadius: 8, display: 'inline-flex',
                alignItems: 'center', justifyContent: 'center', fontSize: 16, fontWeight: 800,
                background: isCur ? '#FEF9E7' : isRead ? '#EBF8F2' : '#F7FAFC',
                border: `2px solid ${isCur ? C.amber : isRead ? C.green : C.line}`,
                color: isCur ? C.amber : C.ink, transition: 'all .15s' }}>
                {n}
              </span>
            )
          })}
        </div>
      </div>

      {/* Program steps — highlight the active one */}
      <div style={{ background: '#F4F0FA', border: '1px solid #D6CCEC', borderRadius: 10, padding: 12, marginBottom: 12 }}>
        <div style={{ fontSize: 11, fontWeight: 800, color: '#5B4B8A', marginBottom: 8 }}>
          {id ? 'PROGRAM — langkah demi langkah' : 'PROGRAM — step by step'}
        </div>
        {PROGRAM.map((p, i) => {
          const active = i === activeStep
          return (
            <div key={p.id} style={{ display: 'flex', gap: 8, alignItems: 'center', padding: '5px 8px',
              borderRadius: 6, marginBottom: 3, transition: 'all .15s',
              background: active ? '#5B4B8A' : 'transparent' }}>
              <span style={{ width: 20, height: 20, borderRadius: 10, flexShrink: 0, fontSize: 11, fontWeight: 800,
                display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                background: active ? '#fff' : '#D6CCEC', color: '#5B4B8A' }}>{i + 1}</span>
              <span style={{ fontSize: 12, fontWeight: active ? 700 : 500,
                color: active ? '#fff' : C.body }}>{p.text}</span>
            </div>
          )
        })}
      </div>

      {/* Memory boxes — what the computer is holding right now */}
      <div style={{ marginBottom: 12 }}>
        <div style={{ fontSize: 11, fontWeight: 800, color: C.muted, marginBottom: 6 }}>
          {id ? 'MEMORI — kotak yang berubah' : 'MEMORY — boxes that change'}
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <div style={{ flex: 1, textAlign: 'center', padding: '10px 6px', borderRadius: 8,
            background: frame?.updated ? '#EBF8F2' : '#F7FAFC',
            border: `2px solid ${frame?.updated ? C.green : C.line}`, transition: 'all .15s' }}>
            <div style={{ fontSize: 10, color: C.muted, fontWeight: 700 }}>{id ? 'terbesar' : 'biggest'}</div>
            <div style={{ fontSize: 22, fontWeight: 800, color: C.ink }}>{frame ? frame.biggest : '—'}</div>
          </div>
          <div style={{ flex: 1, textAlign: 'center', padding: '10px 6px', borderRadius: 8,
            background: '#F7FAFC', border: `2px solid ${C.line}` }}>
            <div style={{ fontSize: 10, color: C.muted, fontWeight: 700 }}>{id ? 'sedang dilihat' : 'looking at'}</div>
            <div style={{ fontSize: 22, fontWeight: 800, color: C.blue }}>{frame && frame.cur != null ? frame.cur : '—'}</div>
          </div>
        </div>
        <div style={{ fontSize: 11.5, color: C.body, textAlign: 'center', marginTop: 8, minHeight: 16 }}>
          {frame ? frame.note : (id ? 'tekan ▶ untuk mulai' : 'press ▶ to start')}
        </div>
      </div>

      {/* Output */}
      <div style={{ textAlign: 'center', marginBottom: 12 }}>
        <div style={{ fontSize: 11, fontWeight: 800, color: C.green, marginBottom: 4 }}>
          {id ? 'KELUARAN' : 'OUTPUT'}
        </div>
        <div style={{ display: 'inline-flex', minWidth: 60, height: 44, alignItems: 'center', justifyContent: 'center',
          padding: '0 16px', borderRadius: 8, fontSize: 22, fontWeight: 800,
          background: done ? '#EBF8F2' : '#F7FAFC',
          border: `2px solid ${done ? C.green : C.line}`, color: done ? C.green : C.muted }}>
          {done ? biggest : '?'}
        </div>
      </div>

      {!done && (
        <button type="button" disabled={running} onClick={run}
          style={{ width: '100%', padding: 12, borderRadius: 8, border: 'none', fontSize: 13, fontWeight: 800,
            background: running ? C.line : C.green, color: running ? C.muted : '#fff',
            cursor: running ? 'not-allowed' : 'pointer' }}>
          ▶ {running ? (id ? 'menjalankan…' : 'running…') : (id ? 'Jalankan program' : 'Run the program')}
        </button>
      )}
      {done && <DoneCard language={language} mistakes={0} onDone={onDone} />}
    </GameShell>
  )
}

// ─── 7. SORT RACE — dua cara, satu tugas (k8_algorithms / k5_algorithms) ──────
// Visualgo-flavored: two sorting methods race on the SAME fixed bars, animating
// swaps/highlights and counting comparisons. Shows "one way does less work".

export function SortRaceGame({ language, onDone }: GameProps) {
  const id = language === 'id'
  const SEED = [5, 2, 8, 1, 6, 3, 7, 4] // fixed heights → deterministic per mount
  const MAXV = 8

  // Precompute animation frames for a method. A frame = { arr, a, b, sorted, done }.
  type SFrame = { arr: number[]; a: number; b: number; sortedFrom: number; comparisons: number }
  function traceBubble(): SFrame[] {
    const arr = [...SEED]; const out: SFrame[] = []; let comp = 0
    let sortedFrom = arr.length
    for (let i = 0; i < arr.length - 1; i++) {
      for (let j = 0; j < arr.length - 1 - i; j++) {
        comp++
        out.push({ arr: [...arr], a: j, b: j + 1, sortedFrom, comparisons: comp })
        if (arr[j] > arr[j + 1]) { const t = arr[j]; arr[j] = arr[j + 1]; arr[j + 1] = t }
      }
      sortedFrom = arr.length - 1 - i
    }
    out.push({ arr: [...arr], a: -1, b: -1, sortedFrom: 0, comparisons: comp })
    return out
  }
  function traceSelection(): SFrame[] {
    const arr = [...SEED]; const out: SFrame[] = []; let comp = 0
    for (let i = 0; i < arr.length - 1; i++) {
      let min = i
      for (let j = i + 1; j < arr.length; j++) {
        comp++
        out.push({ arr: [...arr], a: min, b: j, sortedFrom: i, comparisons: comp })
        if (arr[j] < arr[min]) min = j
      }
      if (min !== i) { const t = arr[i]; arr[i] = arr[min]; arr[min] = t }
    }
    out.push({ arr: [...arr], a: -1, b: -1, sortedFrom: 0, comparisons: comp })
    return out
  }
  const TRACES: Record<0 | 1, SFrame[]> = { 0: traceBubble(), 1: traceSelection() }
  const NAMES = [id ? 'Cara 1 · Gelembung' : 'Way 1 · Bubble', id ? 'Cara 2 · Seleksi' : 'Way 2 · Selection']
  const TOTAL = [TRACES[0][TRACES[0].length - 1].comparisons, TRACES[1][TRACES[1].length - 1].comparisons]

  const [mode, setMode] = useState<0 | 1>(0)
  const [fi, setFi] = useState(0)
  const [running, setRunning] = useState(false)
  const [ranBoth, setRanBoth] = useState<[boolean, boolean]>([false, false])
  const [attempts, setAttempts] = useState(0)
  const [done, setDone] = useState(false)

  const frames = TRACES[mode]
  const frame = frames[Math.min(fi, frames.length - 1)]
  const finished = fi >= frames.length - 1

  const run = () => {
    if (running) return
    setAttempts(a => a + 1); setRunning(true); setFi(0)
    frames.forEach((_, i) => setTimeout(() => {
      setFi(i)
      if (i < frames.length - 1) cueTap()
    }, i * 300))
    setTimeout(() => {
      setRunning(false)
      cueSuccess()
      setRanBoth(prev => {
        const next: [boolean, boolean] = [...prev] as [boolean, boolean]
        next[mode] = true
        if (next[0] && next[1]) setDone(true)
        return next
      })
    }, frames.length * 300 + 200)
  }

  return (
    <GameShell
      title={id ? '📊 Adu Urut — Dua Cara, Satu Tugas' : '📊 Sort Race — Two Ways, One Task'}
      objective={id ? 'Tugas sama: urutkan batang dari pendek ke tinggi. Dua cara — satu bekerja lebih sedikit. Jalankan keduanya.'
                    : 'Same task: sort the bars short→tall. Two ways — one does less work. Run both and compare.'}
      steps={id ? 'jalankan Cara 1 & Cara 2, bandingkan jumlah perbandingan' : 'run Way 1 & Way 2, compare the comparison counts'}
      stats={{ attempts, mistakes: 0, done }}>
      {/* Mode toggle */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
        {[0, 1].map(m => (
          <button key={m} type="button" disabled={running} onClick={() => { setMode(m as 0 | 1); setFi(0) }}
            style={{ flex: 1, padding: '10px 8px', borderRadius: 8, fontSize: 12.5, fontWeight: 800, cursor: running ? 'not-allowed' : 'pointer',
              border: `2px solid ${mode === m ? C.blue : C.line}`,
              background: mode === m ? '#EAF2F8' : '#fff', color: mode === m ? C.blue : C.muted }}>
            {NAMES[m]}{ranBoth[m] ? ' ✓' : ''}
          </button>
        ))}
      </div>

      {/* Bars */}
      <div style={{ display: 'flex', gap: 6, alignItems: 'flex-end', height: 140, padding: '0 4px 8px',
        background: '#F7FAFC', border: `1px solid ${C.line}`, borderRadius: 10, marginBottom: 12 }}>
        {frame.arr.map((v, i) => {
          const isCompared = i === frame.a || i === frame.b
          const isSorted = finished || i >= frame.sortedFrom
          const bg = isCompared ? C.amber : isSorted ? C.green : C.blue
          return (
            <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center',
              justifyContent: 'flex-end' }}>
              <div style={{ width: '100%', height: `${(v / MAXV) * 100}%`, background: bg,
                borderRadius: '4px 4px 0 0', transition: 'height .18s, background .12s',
                display: 'flex', alignItems: 'flex-start', justifyContent: 'center' }}>
                <span style={{ fontSize: 11, fontWeight: 800, color: '#fff', paddingTop: 2 }}>{v}</span>
              </div>
            </div>
          )
        })}
      </div>

      {/* Live counters */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 12 }}>
        {[0, 1].map(m => (
          <div key={m} style={{ flex: 1, textAlign: 'center', padding: '8px 6px', borderRadius: 8,
            background: mode === m ? '#EAF2F8' : '#F7FAFC',
            border: `2px solid ${mode === m ? C.blue : C.line}` }}>
            <div style={{ fontSize: 10, color: C.muted, fontWeight: 700 }}>{NAMES[m]}</div>
            <div style={{ fontSize: 20, fontWeight: 800, color: C.ink }}>
              {mode === m ? frame.comparisons : (ranBoth[m] ? TOTAL[m] : '—')}
            </div>
            <div style={{ fontSize: 9.5, color: C.muted }}>{id ? 'perbandingan' : 'comparisons'}</div>
          </div>
        ))}
      </div>

      {done ? (
        <>
          <div style={{ textAlign: 'center', fontSize: 12.5, color: C.ink, fontWeight: 700, marginBottom: 4 }}>
            {TOTAL[0] === TOTAL[1]
              ? (id ? 'Seri — keduanya butuh perbandingan yang sama.' : 'Tie — both needed the same comparisons.')
              : (id ? `${NAMES[TOTAL[0] < TOTAL[1] ? 0 : 1]} menang: ${Math.min(TOTAL[0], TOTAL[1])} vs ${Math.max(TOTAL[0], TOTAL[1])} perbandingan — kerja lebih sedikit untuk tugas yang sama.`
                    : `${NAMES[TOTAL[0] < TOTAL[1] ? 0 : 1]} wins: ${Math.min(TOTAL[0], TOTAL[1])} vs ${Math.max(TOTAL[0], TOTAL[1])} comparisons — less work for the same task.`)}
          </div>
          <DoneCard language={language} mistakes={0} onDone={onDone} />
        </>
      ) : (
        <button type="button" disabled={running} onClick={run}
          style={{ width: '100%', padding: 12, borderRadius: 8, border: 'none', fontSize: 13, fontWeight: 800,
            background: running ? C.line : C.green, color: running ? C.muted : '#fff',
            cursor: running ? 'not-allowed' : 'pointer' }}>
          ▶ {running ? (id ? 'mengurutkan…' : 'sorting…')
                     : (ranBoth[mode] ? (id ? `Jalankan lagi (${NAMES[mode]})` : `Run again (${NAMES[mode]})`)
                                      : (id ? `Jalankan ${NAMES[mode]}` : `Run ${NAMES[mode]}`))}
        </button>
      )}
    </GameShell>
  )
}

// ─── Registry ─────────────────────────────────────────────────────────────────

export const INTERACTIVE_GAMES: Record<string, ComponentType<GameProps>> = {
  gamelan: GamelanGame,
  congklak: CongklakGame,
  gobak_sodor: GobakSodorGame,
  engklek: EngklekGame,
  batik: BatikGame,
  execution_trace: ExecutionTraceGame,
  sort_race: SortRaceGame,
}
