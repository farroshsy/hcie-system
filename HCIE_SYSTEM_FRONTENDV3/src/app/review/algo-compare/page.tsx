'use client'

import { useState, useEffect } from 'react'
import { Panel, Eyebrow } from '@/lib/ui/primitives'
import { t as tk } from '@/lib/ui/theme'  // design tokens (renamed: useT() owns `t`)
import { useT } from '@/contexts/language_context'
import { NextSteps } from '@/components/review/NextSteps'

// ── palette ────────────────────────────────────────────────────────────────────
const ACCENT  = tk.tone.info.fg     // #1565C0
const AL      = '#E3F2FD'          // light-blue tint (code/table highlight)
const NEUTRAL = tk.color.body       // #4A5568
const GREEN   = '#1E8449'          // success / "HCIE advantage" green (semantic)
const WARN    = '#B7791F'
const DARK    = '#0F172A'

// ── code block ────────────────────────────────────────────────────────────────
function Code({ children }: { children: string }) {
  const lines = children.split('\n')
  return (
    <pre style={{
      margin: 0, padding: '12px 16px',
      background: DARK, borderRadius: 6,
      fontSize: 11, lineHeight: 1.65,
      overflowX: 'auto',
      fontFamily: '"Fira Code","Cascadia Code",Consolas,monospace',
      whiteSpace: 'pre',
    }}>
      {lines.map((line, i) => {
        const isComment  = line.trim().startsWith('//')
        const isHeader   = line.trim().startsWith('##')
        const isKeyword  = /^(state|update|predict|train|complexity|space|strength|weakness)\s/.test(line.trim().toLowerCase())
        const color = isComment  ? '#4ADE80'
                    : isHeader   ? '#FACC15'
                    : isKeyword  ? '#93C5FD'
                    : '#E2E8F0'
        return <span key={i} style={{ color, display: 'block' }}>{line}</span>
      })}
    </pre>
  )
}

// ── section header ─────────────────────────────────────────────────────────────
function SectionHead({ title, sub }: { title: string; sub?: string }) {
  return (
    <div style={{ marginBottom: tk.space.lg, borderBottom: `2px solid ${AL}`, paddingBottom: tk.space.sm }}>
      <div style={{ fontSize: tk.font.size.sm, fontWeight: tk.font.weight.bold, letterSpacing: '0.1em',
                    color: NEUTRAL, textTransform: 'uppercase', marginBottom: 3 }}>{sub}</div>
      <div style={{ fontSize: tk.font.size.xl, fontWeight: tk.font.weight.heavy, color: tk.color.ink }}>{title}</div>
    </div>
  )
}

// ── Algoritma 3.5 animated stepper ─────────────────────────────────────────────
// Lines are VERBATIM Algoritma 3.5 (naskah §3.3.2 = deck slide 37/81). Kalman
// numbers in the demo state = Tabel 3.13 naskah (seed m=0,5 P=0,25; y=1).
// Thompson sample and J_t values are labelled illustrative.
type StepState = {
  mK: string; P: string; ac: string; repr: string
  cstar: string; astar: string; jt: string; y: string; log: string
}
const S0: StepState = {
  mK: '—', P: '—', ac: '—', repr: '—',
  cstar: '—', astar: '—', jt: '—', y: '—', log: '0 events',
}
type AlgStep = {
  no?: string; text: string; phase: 0 | 1 | 2
  expl?: string; state?: Partial<StepState>; changed?: (keyof StepState)[]
}
const ALG35: AlgStep[] = [
  { text: '// Cold-start: seed state tiap konsep', phase: 0 },
  { no: '1', text: 'for c in C:  state(u,c) ← (m ← p̄(c) [def 0,3], σ² ← σ₀² [def 0,5])', phase: 0,
    expl: 'Every concept gets an explicit prior BEFORE any interaction — a prediction exists from step 0. That is the cold-start property. Demo values = the thesis worked example (Tabel 3.13): seed m=0,5, P=0,25.',
    state: { mK: '0,5000', P: '0,25000' }, changed: ['mK', 'P'] },
  { no: '2', text: '             repr_posterior(u,c) ← prior lemah', phase: 0,
    expl: 'The modality bandit starts from a weak Beta(1,1) prior — no assumption about which representation (text/code/video/…) works for this learner.',
    state: { repr: 'Beta(1,1)' }, changed: ['repr'] },
  { text: '// --- REKOMENDASI (per permintaan) ---', phase: 1 },
  { no: '3', text: 'C_avail ← unlocked_concepts(u, C, dag, τ)      // gerbang prasyarat', phase: 1,
    expl: 'The prerequisite DAG gates the action space: only concepts whose prerequisites reach mastery τ are candidates. Structure constrains, it does not select.' },
  { no: '4', text: 'if C_avail = ∅:  C_avail ← foundation_concepts(C)', phase: 1,
    expl: 'Safety fallback: a brand-new (or struggling) learner always has the foundation concepts available — the loop can never dead-end.' },
  { no: '5', text: 'for c in C_avail:', phase: 1 },
  { no: '6', text: '    (m, σ²) ← read_posterior(u, c)', phase: 1,
    expl: 'Read the explicit state for each candidate. This is the ONLY input selection needs — no embeddings, no history scan (O(1) per candidate).' },
  { no: '7', text: '    n ← 1/σ²;  α_c ← m·n;  β_c ← (1−m)·n     // ketidakpastian → kekuatan prior', phase: 1,
    expl: 'Uncertainty becomes prior strength: low σ² → concentrated Beta (exploit); high σ² → flat Beta (explore). Here: n = 1/0,25 = 4 → α_c = 2, β_c = 2.',
    state: { ac: 'α=2, β=2' }, changed: ['ac'] },
  { no: '8', text: 'c* ← bandit.select_arm({Beta(α_c, β_c)}, context=π)   // Thompson: pilih konsep', phase: 1,
    expl: 'THE SELECTOR: Thompson sampling over the per-concept Beta posteriors (detailed in Algoritma 3.6: contextual score, exploration floor 0,7+0,3·ρ, softmax τ=0,2). The bandit selects — J_t does not.',
    state: { cstar: 'c₁ "loops" (sampel ilustratif)' }, changed: ['cstar'] },
  { no: '9', text: 'if c* invalid or c* ∉ C_avail:  c* ← fallback_concept(C_avail)', phase: 1,
    expl: 'Guard: the choice must respect the gate from line 3.' },
  { no: '10', text: '(task, a*) ← pick_task(u, c*)                 // bandit representasi: pilih modalitas', phase: 1,
    expl: 'Second bandit: pick the representation (text · code · Parsons · MCQ · video · interactive) from its own Beta posteriors.',
    state: { astar: 'a* = video (ilustratif)' }, changed: ['astar'] },
  { no: '11', text: 'J_t(u,c*) ← σ(Σ wᵢ·Nᵢ) atas 6 dimensi          // pandangan tata kelola (ADC)', phase: 1,
    expl: 'J_t is computed AFTER selection as the auditable governance VIEW (6 dimensions, zero-guard normalisation — Algoritma 3.7). It is recorded for ADC; it does not pick the concept.',
    state: { jt: '0,42 (ilustratif)' }, changed: ['jt'] },
  { no: '12', text: 'emit RecommendationGenerated(u, c*, a*, J_t)  // event-sourcing', phase: 1,
    expl: 'The decision + its rationale become an immutable event (outbox → Kafka). This is what makes every decision replayable.',
    state: { log: '1 event' }, changed: ['log'] },
  { no: '13', text: 'serve (c*, a*)', phase: 1,
    expl: 'The learner sees the task. Total decision cost so far: O(K) with constant windows — measured p95 ≈ 24 ms.' },
  { text: '// --- PEMBARUAN (saat hasil diamati) ---', phase: 2 },
  { no: '14', text: 'observe y ∈ {0,1} dan sinyal (waktu respons, dst.)', phase: 2,
    expl: 'The learner answers. Demo: y = 1 (correct), matching Tabel 3.13 interaction 1.',
    state: { y: 'y = 1 (benar)' }, changed: ['y'] },
  { no: '15', text: '(m, σ²) ← kalman_update(m, σ², y)             // Algoritma 3.1, O(1)', phase: 2,
    expl: 'Kalman update (Q=0,01, R=0,1): P̄ = 0,25+0,01; gain K = 0,7222; m: 0,5000 → 0,8611; P: 0,25 → 0,07222. Exact Tabel 3.13 values — 5 scalar ops, O(1).',
    state: { mK: '0,8611  (K=0,7222)', P: '0,07222' }, changed: ['mK', 'P'] },
  { no: '16', text: 'repr_posterior(u, a*) ← beta_update(·, y)     // menutup lingkar bandit modalitas', phase: 2,
    expl: 'The modality bandit learns: success with "video" → Beta(1,1) → Beta(2,1). Next time, video is slightly more likely for this learner.',
    state: { repr: 'Beta(2,1)' }, changed: ['repr'] },
  { no: '17', text: 'propagate_transfer(u, c*, dag)                // bukti → konsep turunan', phase: 2,
    expl: 'Positive evidence nudges DIRECT dependents only, capped at 0,5·|ΔM| — no recursive cascade, cost O(deg(c)).' },
  { no: '18', text: 'append_event(u, state sebelum/sesudah, aksi, sinyal)   // keterlacakan (audit)', phase: 2,
    expl: 'Before/after state is appended immutably. Replay of this log is bit-identical at the decision layer — the reproducibility claim.',
    state: { log: '2 events' }, changed: ['log'] },
  { no: '19', text: 'return (c*, a*), m', phase: 2,
    expl: 'One full cycle done. The loop repeats from line 3 on the next request — state persists, nothing is retrained.' },
]
const PHASE_META = [
  { label: 'Cold-start seed', color: '#1565C0' },
  { label: 'Rekomendasi (baris 3–13)', color: '#1E8449' },
  { label: 'Pembaruan (baris 14–19)', color: '#B7791F' },
]
const STATE_ROWS: { key: keyof StepState; label: string }[] = [
  { key: 'mK', label: 'm_K (kanonik)' },
  { key: 'P', label: 'P (varians Kalman)' },
  { key: 'ac', label: 'α_c, β_c (prior seleksi ← m,σ²)' },
  { key: 'cstar', label: 'c* (konsep terpilih — bandit)' },
  { key: 'astar', label: 'a* (modalitas)' },
  { key: 'jt', label: 'J_t (pandangan ADC)' },
  { key: 'repr', label: 'repr_posterior(a*)' },
  { key: 'y', label: 'y (hasil)' },
  { key: 'log', label: 'event log (imutabel)' },
]

function Alg35Stepper() {
  const [idx, setIdx] = useState(0)
  const [playing, setPlaying] = useState(false)

  useEffect(() => {
    if (!playing) return
    const h = setInterval(() => {
      setIdx(i => {
        if (i >= ALG35.length - 1) { setPlaying(false); return i }
        return i + 1
      })
    }, 1600)
    return () => clearInterval(h)
  }, [playing])

  // fold state up to current index
  const st: StepState = { ...S0 }
  for (let i = 0; i <= idx; i++) Object.assign(st, ALG35[i].state)
  const cur = ALG35[idx]
  const changed = new Set(cur.changed ?? [])
  const phase = cur.phase

  const btn = (label: string, onClick: () => void, disabled = false, primary = false) => (
    <button onClick={onClick} disabled={disabled}
      style={{ padding: '5px 12px', borderRadius: 5, fontSize: 12, fontWeight: 700, cursor: disabled ? 'default' : 'pointer',
               border: `1px solid ${primary ? ACCENT : '#CBD5E0'}`, background: primary ? ACCENT : '#fff',
               color: primary ? '#fff' : NEUTRAL, opacity: disabled ? 0.4 : 1 }}>{label}</button>
  )

  return (
    <div style={{ border: `1px solid ${AL}`, borderRadius: 8, padding: 16, marginBottom: 20, background: '#FAFBFC' }}>
      {/* phase chips */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', marginBottom: 12 }}>
        {PHASE_META.map((p, i) => (
          <span key={p.label} style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
            <span style={{ padding: '4px 12px', borderRadius: 999, fontSize: 11, fontWeight: 700,
                           background: phase === i ? p.color : '#EDF2F7', color: phase === i ? '#fff' : '#718096',
                           transition: 'background 300ms, color 300ms' }}>{p.label}</span>
            {i < 2 && <span style={{ color: '#A0AEC0' }}>→</span>}
          </span>
        ))}
        <span style={{ marginLeft: 'auto', fontSize: 11, color: NEUTRAL, fontFamily: 'monospace' }}>
          {idx + 1} / {ALG35.length}
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(380px, 3fr) minmax(260px, 2fr)', gap: 14 }}>
        {/* code pane */}
        <pre style={{ margin: 0, padding: '10px 12px', background: DARK, borderRadius: 6, fontSize: 11,
                      lineHeight: 1.8, overflowX: 'auto', fontFamily: '"Fira Code","Cascadia Code",Consolas,monospace' }}>
          {ALG35.map((l, i) => {
            const active = i === idx
            const done = i < idx
            const isComment = l.text.trim().startsWith('//')
            return (
              <div key={i} onClick={() => { setPlaying(false); setIdx(i) }}
                style={{ display: 'flex', gap: 8, cursor: 'pointer', borderRadius: 3,
                         padding: '0 6px', transition: 'background 250ms, opacity 250ms, transform 250ms',
                         background: active ? PHASE_META[l.phase].color + '55' : 'transparent',
                         borderLeft: active ? `3px solid ${PHASE_META[l.phase].color}` : '3px solid transparent',
                         transform: active ? 'translateX(2px)' : 'none',
                         opacity: active ? 1 : done ? 0.85 : 0.38 }}>
                <span style={{ color: '#64748B', width: 18, textAlign: 'right', flexShrink: 0 }}>{l.no ?? ''}</span>
                <span style={{ color: isComment ? '#4ADE80' : active ? '#FFFFFF' : '#E2E8F0', whiteSpace: 'pre' }}>{l.text}</span>
              </div>
            )
          })}
        </pre>

        {/* explanation + live state */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div style={{ background: '#fff', border: `1px solid #E2E8F0`, borderLeft: `4px solid ${PHASE_META[phase].color}`,
                        borderRadius: 6, padding: '10px 12px', fontSize: 12.5, color: tk.color.ink, lineHeight: 1.55, minHeight: 88 }}>
            {cur.expl ?? (cur.text.includes('REKOMENDASI') ? 'The synchronous decision path begins — this is what runs when the learner asks for the next task.'
              : cur.text.includes('PEMBARUAN') ? 'The asynchronous learning path begins — the outcome flows back into every estimator.'
              : 'Seeding phase: explicit priors give the system a defined prediction before any data exists.')}
          </div>
          <table style={{ borderCollapse: 'collapse', fontSize: 11.5, background: '#fff', border: '1px solid #E2E8F0', borderRadius: 6, overflow: 'hidden' }}>
            <tbody>
              {STATE_ROWS.map(r => {
                const hot = changed.has(r.key)
                return (
                  <tr key={r.key} style={{ borderBottom: '1px solid #EDF2F7' }}>
                    <td style={{ padding: '4px 10px', color: NEUTRAL, whiteSpace: 'nowrap' }}>{r.label}</td>
                    <td key={`${r.key}-${st[r.key]}`}
                        style={{ padding: '4px 10px', fontFamily: 'monospace', fontWeight: hot ? 800 : 500,
                                 color: hot ? PHASE_META[phase].color : tk.color.ink,
                                 background: hot ? PHASE_META[phase].color + '18' : 'transparent',
                                 transition: 'background 400ms, color 400ms' }}>{st[r.key]}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {btn('⏮ Reset', () => { setPlaying(false); setIdx(0) }, idx === 0)}
            {btn('◀', () => { setPlaying(false); setIdx(i => Math.max(0, i - 1)) }, idx === 0)}
            {btn('▶', () => { setPlaying(false); setIdx(i => Math.min(ALG35.length - 1, i + 1)) }, idx === ALG35.length - 1)}
            {btn(playing ? '⏸ Pause' : '⏵ Auto-play', () => setPlaying(p => !p), idx === ALG35.length - 1 && !playing, true)}
          </div>
          <div style={{ fontSize: 10.5, color: '#94A3B8', lineHeight: 1.5 }}>
            Baris = verbatim Algoritma 3.5 naskah (≡ slide 37/81). Angka Kalman = Tabel 3.13 (benih 0,5 / 0,25; y=1).
            Sampel Thompson &amp; J_t berlabel ilustratif. Klik baris mana pun untuk melompat.
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Algoritma 3.1–3.7: verbatim thesis listings ────────────────────────────────
// Text is VERBATIM from the naskah (§3). `ground` = where it runs / where its
// evidence lives, so a reviewer can jump from listing → running system.
const THESIS_ALGS: { id: string; title: string; ground: string; code: string }[] = [
  { id: '3.1', title: 'Pembaruan filter Kalman skalar',
    ground: 'Runs in: kalman_learner.py (deployed path) · animated in the stepper above · deck slide 76/78 · exact worked values: Tabel 3.13',
    code: `Input : mastery m, variance P, response y ∈ {0,1}
Const : Q = 0,01 ;  R = 0,1
1   m_pred ← m
2   P_pred ← P + Q
3   K      ← P_pred / (P_pred + R)
4   m      ← m_pred + K · (y − m_pred)
5   P      ← (1 − K) · P_pred
6   return clip(m, 0,05, 0,95)` },
  { id: '3.2', title: 'Protokol evaluasi tercocok (pra-upaya, lintas-model)',
    ground: 'Runs in: evaluate_all_baselines_auc.py + dump_matched_eval_perrow.py · produces Tabel 4.8 (AUC 0,6051) · results on /review/baselines · re-verify ≈ 2 s (Section 6)',
    code: `Input : model, U_heldout, windows = {≤5, ≤10, ≤20, all}
1   records ← [ ]
2   for each u ∈ U_heldout do
3       seq ← interaction_sequence(u)
4       for (t, (c, y)) in enumerate(seq) do
5           p̂ ← model.predict(u, c, t)        // PREDICT before observe → leak-free
6           records.append( (t, p̂, y) )
7           model.observe(u, c, y)
8   for each W ∈ windows do
9       S ← { (p̂, y) ∈ records : t ≤ W }
10      compute AUC, ACC, Brier, log-loss on S
11  return metrics` },
  { id: '3.3', title: 'Klasifikasi observabilitas dimensi (ADC)',
    ground: 'Runs in: adaptive_dimension_controller.py · produces Tabel 4.11 (6-dim verdicts, N=96.727) · live view /dashboard/governance · deck slide 36',
    code: `Input : contributions c_i over a run
Const : α_floor = 0,01 ;  signal_ratio = 0,08
1   μ ← mean(c_i)
2   ρ ← std(c_i) / |μ|
3   if μ ≤ α_floor then return STRUCTURAL_ZERO
4   if ρ < signal_ratio then return OBSERVATION_BIAS
5   return ACTIVE
// live sealer simplifies to binary {AKTIF, DORMAN}` },
  { id: '3.4', title: 'Kontrol shuffled-DAG (uji-null permutasi)',
    ground: 'Runs in: probe_prospective_transfer_v3.py (K=1000, seed 20260531) → p < 0,001 · interactive sandbox /review/methods §H · deck slide 13',
    code: `Input : observed_signal, dag, n_perm
1   b_obs ← estimate_transfer_effect(observed_signal, dag)
2   null ← [ ]
3   repeat n_perm times
4       dag_shuf ← shuffle_dag(dag)          // degree-preserving
5       null.append( estimate_transfer_effect(observed_signal, dag_shuf) )
6   p ← fraction( |null| ≥ |b_obs| )
7   return (b_obs, p)` },
  { id: '3.5', title: 'Lingkar adaptif HCIE ujung-ke-ujung',
    ground: 'Runs in: task_service (recommend) + unified_brain.process_event (update) · ANIMATED step-by-step at the top of this section · deck slides 37/81 · live scrub /review/run-it-yourself',
    code: ALG35.map(l => (l.no ? `${l.no.padStart(2)}  ${l.text}` : l.text)).join('\n') },
  { id: '3.6', title: 'Seleksi konsep: bandit Thompson kontekstual',
    ground: 'Runs in: bandit.py:510-602 (select_arm_contextual_thompson) · THE selector (Alg 3.5 line 8) · interactive bandit demo /review/methods · deck slide 82',
    code: `Input  : C_avail, posterior (m_c, σ²_c) tiap konsep, kesulitan d_c, bobot kebijakan ρ (0..1, def 1)
Output : konsep terpilih c*
1   for c in C_avail:
2       (α_c, β_c) ← posterior_ke_beta(m_c, σ²_c, d_c)      // prior selaras-penguasaan
3       s_c   ← sample Beta(α_c, β_c)                       // Thompson
4       u_c   ← ketidakpastian(α_c, β_c)                    // dorongan eksplorasi
5       zpd_c ← exp(−(m_c − d_c)² / 0,1)                    // keselarasan ZPD
6       g_c   ← σ( s_c + 0,1·u_c − 0,2·|m_c − d_c| + 0,1·zpd_c )   // skor kontekstual
7       h_c   ← g_c · (0,7 + 0,3·ρ)                         // modulasi bertepi (lantai eksplorasi 70%)
8   c* ← softmax_sample({h_c}, τ = 0,2)                     // seleksi stokastik
9   return c*` },
  { id: '3.7', title: 'Komputasi J_t dan pelapisan observabilitas (ADC)',
    ground: 'Runs in: governance_engine.py:820-862 (6-dim weighted sum) · the VIEW at Alg 3.5 line 11 — recorded for ADC, does not select · decomposition /review/trace',
    code: `Input  : state s_t = (m, σ², z), konteks c_t, bobot konstitusional w (Σ wᵢ = 1), lantai α_floor = 0,01
Output : J_t, kontribusi per-dimensi {c_i}, verdikt ADC {v_i}
1   comp ← [Δm, transfer_terealisasi, transfer_prospektif, tantangan, ketidakpastian, ZPD]
2   for i in 1..6:
3       N_i ← normalisasi_pengaman_nol(comp_i)   // nol-sejati → 0, bukan lantai
4       c_i ← w_i · N_i                          // kontribusi dimensi
5   J_t ← σ( Σ_i c_i )                           // skor tata kelola tersintesis
6   for i in 1..6:                               // lapisan observabilitas (ADC)
7       v_i ← AKTIF bila mean(c_i) > α_floor, selain itu DORMAN
8   emit GovernanceSnapshot(J_t, {c_i}, {v_i})   // dicatat, tidak memilih konsep
9   return J_t, {c_i}, {v_i}` },
]

function ThesisAlgBrowser() {
  const [tab, setTab] = useState('3.5')
  const alg = THESIS_ALGS.find(a => a.id === tab)!
  return (
    <div>
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 12 }}>
        {THESIS_ALGS.map(a => (
          <button key={a.id} onClick={() => setTab(a.id)}
            style={{ padding: '6px 14px', borderRadius: 6, fontSize: 12, fontWeight: 700, cursor: 'pointer',
                     border: `1px solid ${tab === a.id ? ACCENT : '#CBD5E0'}`,
                     background: tab === a.id ? ACCENT : '#fff', color: tab === a.id ? '#fff' : NEUTRAL,
                     transition: 'background 200ms, color 200ms' }}>
            Alg {a.id}
          </button>
        ))}
      </div>
      <div style={{ fontSize: 14, fontWeight: 800, color: tk.color.ink, marginBottom: 4 }}>
        Algoritma {alg.id} — {alg.title}
      </div>
      <div style={{ fontSize: 11.5, color: NEUTRAL, marginBottom: 8, lineHeight: 1.5 }}>{alg.ground}</div>
      <Code>{alg.code}</Code>
    </div>
  )
}

// ── model tab bar ──────────────────────────────────────────────────────────────
const MODELS = ['BKT', 'DKT', 'SAKT', 'GKT', 'HCIE'] as const
type Model = typeof MODELS[number]

// Static visual metadata (color + terse technical tag). Human-readable model
// names live in the dictionary and are resolved inside the component via t().
const MODEL_VISUAL: Record<Model, { color: string; tag: string }> = {
  BKT:  { color: '#6B7280', tag: 'HMM · 2-state' },
  DKT:  { color: '#7C3AED', tag: 'LSTM · offline' },
  SAKT: { color: '#0891B2', tag: 'Transformer · offline' },
  GKT:  { color: '#059669', tag: 'GNN · offline' },
  HCIE: { color: ACCENT,    tag: 'KF+Bayes · online' },
}

// ── content blocks per model (PSEUDOCODE — code, not translated) ────────────────

const MASTERY_UPDATE: Record<Model, string> = {
  BKT: `## BKT — Mastery Update (Hidden Markov Model)
// State: P(K_t) ∈ [0,1]  — scalar probability "concept is learned"
// Parameters per concept (fit offline via EM):
//   p_L0  = P(already known at t=0)
//   p_T   = P(transition: unlearned → learned after attempt)
//   p_G   = P(correct | unlearned)   ← guess rate
//   p_S   = P(incorrect | learned)   ← slip rate

// Step 1 — Bayes update on observed response r ∈ {0,1}:
if r == 1:  // correct
    P(K_t | r) = P(K_{t-1}) * (1 - p_S)
                 / [P(K_{t-1})*(1-p_S) + (1-P(K_{t-1}))*p_G]
else:       // incorrect
    P(K_t | r) = P(K_{t-1}) * p_S
                 / [P(K_{t-1})*p_S   + (1-P(K_{t-1}))*(1-p_G)]

// Step 2 — Learning transition:
P(K_{t+1}) = P(K_t | r) + (1 - P(K_t | r)) * p_T

// complexity: O(1) per step
// space:      O(4) per concept  (4 scalar params, no per-learner memory)
// weakness:   binary latent state; no concept graph; EM offline only`,

  DKT: `## DKT — Mastery Update (LSTM Hidden State)
// State: h_t ∈ R^d  — continuous vector, NOT interpretable as mastery
// Input embedding: x_t = [one_hot(q_t) || one_hot(r_t)] ∈ R^{2|K|}
//   or learned embedding E[q_t + |K|*r_t] ∈ R^d

// LSTM cell update (4 gates, all O(d²)):
f_t = σ(W_f · [h_{t-1}, x_t] + b_f)   // forget: what to erase from c
i_t = σ(W_i · [h_{t-1}, x_t] + b_i)   // input:  what new info to write
g_t = tanh(W_g · [h_{t-1}, x_t] + b_g) // candidate cell values
o_t = σ(W_o · [h_{t-1}, x_t] + b_o)   // output: what to expose as h

c_t = f_t ⊙ c_{t-1} + i_t ⊙ g_t       // cell state (long memory)
h_t = o_t ⊙ tanh(c_t)                  // hidden state (short memory)

// Prediction for any concept k at time t+1:
ŷ_{t+1,k} = σ(W_out[k] · h_t + b_out[k])

// Training: offline, teacher forcing, Adam, BCE loss
// complexity: O(d²) per step,  O(N·T·d²) total training
// space:      O(d²) weights (frozen after training) + O(d) per active session
// weakness:   h_t is black-box; no per-learner online update; cold-start = zero state`,

  SAKT: `## SAKT — Mastery Update (Self-Attention over History)
// State: last M interaction embeddings  (M=100 typical, sliding window)
// Embedding: e_t = E_q[q_t] + E_r[r_t]  ∈ R^d  (position-encoded)

// Query = target concept embedding q_{t+1} ∈ R^d
// Keys  = K = E_q[q_{1..t}] · W_K        ∈ R^{t×d}
// Values= V = E_r[r_{1..t}] · W_V        ∈ R^{t×d}

// Scaled dot-product attention (causal — lower-tri mask):
A = softmax( (Q · K^T) / √d )           // R^{1×t}  attention weights
ctx = A · V                              // R^{1×d}  attended context

// Feed-forward prediction:
ŷ_{t+1} = σ(FFN(ctx + Q))              // residual + 2-layer MLP

// complexity: O(M²·d) per prediction  (attention over M steps)
// space:      O(M·d) KV cache per active session
// weakness:   fixed M window; forgets history > M; no concept graph; offline`,

  GKT: `## GKT — Mastery Update (Graph Neural Network over Concept Graph)
// State: node embeddings H ∈ R^{|K|×d}  (one per concept, global — not per learner)
// Graph: prerequisite graph G = (V, E)   (same for all learners)

// GNN message passing (L=2 typical layers):
for layer l in 1..L:
    for concept k in V:
        m_k = Σ_{j ∈ N(k)} W_msg · h_j^{l-1}   // aggregate neighbors O(deg·d)
        h_k^l = GRU(h_k^{l-1}, [m_k, x_t])      // update with interaction

// Prediction for concept k:
ŷ_{t,k} = σ(W_out · h_k^L)

// complexity: O(L · |E| · d) per forward pass
// space:      O(|K|·d) node states  (shared, not per-learner)
// strength:   explicitly models concept prerequisites
// weakness:   global node states (not personalised per learner);
//             all concept embeddings updated on every step — expensive;
//             offline training required`,

  HCIE: `## HCIE — Mastery Update (Online Kalman Filter + Bayesian)

// ── KALMAN FILTER per (learner i, concept k) ─────────────────────────
// State: (μ_ik, σ²_ik)  — ability mean + variance
// No offline training needed; updates on every attempt

// Predict step (prior):
μ̄_t  = μ_{t-1}              // no drift model in V1
σ̄²_t = σ²_{t-1} + Q        // process noise Q = 0.01 (hyperparameter)

// Update step (posterior):
K_t  = σ̄²_t / (σ̄²_t + R)  // Kalman gain; R = obs noise ≈ 0.1
μ_t  = μ̄_t + K_t · (r_t - μ̄_t)   // weighted move toward obs
σ²_t = (1 - K_t) · σ̄²_t           // variance shrinks with each obs

// complexity: O(1) — 5 scalar ops per attempt
// space:      O(2) per (learner, concept) pair

// ── BAYESIAN BETA POSTERIOR per (learner i, concept k) ────────────────
// State: (α_ik, β_ik)  — Beta distribution over mastery prob
// Init: α=1, β=1  (uniform prior)

α_t = α_{t-1} + r_t          // add 1 on correct
β_t = β_{t-1} + (1 - r_t)   // add 1 on incorrect
E[p_mastery] = α / (α + β)   // posterior mean
Var[p_mastery] = α·β / ((α+β)²·(α+β+1))  // epistemic uncertainty

// complexity: O(1) — 2 scalar increments
// space:      O(2) per (learner, concept) pair

// ── ENSEMBLE (Exponentiated Gradient) ─────────────────────────────────
// 2 learners V2 (Kalman + Bayesian); initialised w = [0.5, 0.5]
ŷ_t = w_Kalman · μ_t + w_Bayes · E[p_mastery]
loss_l = (ŷ_l - r_t)²                    // per-learner squared loss
w_l ← w_l · exp(-η · loss_l)  then /= Σ  // EG update, η=0.1

// ── JT SCORE (recommendation, not prediction) ─────────────────────────
// KEY DIFFERENCE: HCIE doesn't just predict — it scores next concepts
JT(i,k) = Σ_d weight_d · signal_d(i,k)
// signals drive which concept to serve NEXT (policy, not estimator)`,
}

const COMPLEXITY_TABLE = [
  { model: 'BKT',  update: 'O(1)',         train: 'O(N·T) EM',         space: 'O(4·|K|)',      online: '✗', graph: '✗', interp: '✓' },
  { model: 'DKT',  update: 'O(d²)',        train: 'O(N·T·d²)',         space: 'O(d²)',         online: '✗', graph: '✗', interp: '✗' },
  { model: 'SAKT', update: 'O(M²·d)',      train: 'O(N·T·M²·d)',      space: 'O(M·d)/session',online: '✗', graph: '✗', interp: '~' },
  { model: 'GKT',  update: 'O(L·|E|·d)',  train: 'O(N·T·L·|E|·d)',   space: 'O(|K|·d)',      online: '✗', graph: '✓', interp: '~' },
  { model: 'HCIE', update: 'O(indeg(k))',  train: 'none (online)',      space: 'O(2·|learners|·|K|)', online: '✓', graph: '✓', interp: '✓' },
]

// ── main page ──────────────────────────────────────────────────────────────────

export default function AlgoComparePage() {
  const t = useT()
  const [activeModel, setActiveModel] = useState<Model>('HCIE')

  // Human-readable model names (resolved per language).
  const MODEL_FULL: Record<Model, string> = {
    BKT:  t('algoCompare.modelFullBkt'),
    DKT:  t('algoCompare.modelFullDkt'),
    SAKT: t('algoCompare.modelFullSakt'),
    GKT:  t('algoCompare.modelFullGkt'),
    HCIE: t('algoCompare.modelFullHcie'),
  }

  // Design decisions (prose) — resolved per language.
  const DESIGN_DECISIONS = [
    {
      title:   t('algoCompare.decision1Title'),
      desc:    t('algoCompare.decision1Desc'),
      verdict: t('algoCompare.decision1Verdict'),
    },
    {
      title:   t('algoCompare.decision2Title'),
      desc:    t('algoCompare.decision2Desc'),
      verdict: t('algoCompare.decision2Verdict'),
    },
    {
      title:   t('algoCompare.decision3Title'),
      desc:    t('algoCompare.decision3Desc'),
      verdict: t('algoCompare.decision3Verdict'),
    },
    {
      title:   t('algoCompare.decision4Title'),
      desc:    t('algoCompare.decision4Desc'),
      verdict: t('algoCompare.decision4Verdict'),
    },
    {
      title:   t('algoCompare.decision5Title'),
      desc:    t('algoCompare.decision5Desc'),
      verdict: t('algoCompare.decision5Verdict'),
    },
  ]

  const TABLE_HEADERS = [
    t('algoCompare.colModel'),
    t('algoCompare.colPerStepUpdate'),
    t('algoCompare.colTrainingCost'),
    t('algoCompare.colSpace'),
    t('algoCompare.colOnline'),
    t('algoCompare.colGraph'),
    t('algoCompare.colInterpretable'),
  ]

  return (
    <div style={{ padding: '32px 40px', maxWidth: 1040, fontFamily: 'Inter,system-ui,sans-serif' }}>

      {/* Header */}
      <div style={{ marginBottom: tk.space.xxl }}>
        <Eyebrow color={NEUTRAL}>{t('algoCompare.eyebrow')}</Eyebrow>
        <h1 style={{ fontSize: tk.font.size.h2, fontWeight: tk.font.weight.heavy, color: tk.color.ink, marginBottom: tk.space.sm }}>
          {t('algoCompare.title')}
        </h1>
        <p style={{ fontSize: tk.font.size.md, color: NEUTRAL, lineHeight: 1.7, maxWidth: 720 }}>
          {t('algoCompare.introA')}{' '}
          <em>{t('algoCompare.introEm')}</em>{t('algoCompare.introB')}
        </p>
      </div>

      {/* ── Section 1: Mastery update ── */}
      <section style={{ marginBottom: 40 }}>
        <SectionHead title={t('algoCompare.sec1Title')} sub={t('algoCompare.sec1Sub')} />

        {/* Model tabs */}
        <div style={{ display: 'flex', gap: tk.space.xs, flexWrap: 'wrap', marginBottom: tk.space.lg }}>
          {MODELS.map(m => {
            const meta = MODEL_VISUAL[m]
            const active = m === activeModel
            return (
              <button key={m} onClick={() => setActiveModel(m)} style={{
                padding: '6px 14px', borderRadius: 20, fontSize: tk.font.size.base, fontWeight: tk.font.weight.bold,
                border: `2px solid ${active ? meta.color : tk.color.line}`,
                background: active ? meta.color : tk.color.surface,
                color: active ? '#fff' : NEUTRAL,
                cursor: 'pointer', transition: 'all 0.15s',
              }}>
                {m}
                <span style={{ marginLeft: 6, fontWeight: 400, fontSize: tk.font.size.xs,
                               opacity: 0.8, display: active ? 'inline' : 'none' }}>
                  {meta.tag}
                </span>
              </button>
            )
          })}
        </div>

        {/* Model info bar */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: tk.space.sm, marginBottom: tk.space.sm,
          padding: '8px 14px', background: AL, borderRadius: tk.radius.sm,
        }}>
          <span style={{ fontWeight: tk.font.weight.bold, fontSize: tk.font.size.md, color: MODEL_VISUAL[activeModel].color }}>
            {activeModel}
          </span>
          <span style={{ fontSize: tk.font.size.base, color: NEUTRAL }}>
            {MODEL_FULL[activeModel]}
          </span>
          <span style={{
            marginLeft: 'auto', fontSize: tk.font.size.xs, fontWeight: tk.font.weight.bold,
            color: MODEL_VISUAL[activeModel].color, letterSpacing: '0.06em',
          }}>
            {MODEL_VISUAL[activeModel].tag}
          </span>
        </div>

        <Code>{MASTERY_UPDATE[activeModel]}</Code>
      </section>

      {/* ── Section 2: Complexity table ── */}
      <section style={{ marginBottom: 40 }}>
        <SectionHead title={t('algoCompare.sec2Title')} sub={t('algoCompare.sec2Sub')} />
        <div style={{ overflowX: 'auto' }}>
          <table style={{ borderCollapse: 'collapse', fontSize: tk.font.size.base, width: '100%' }}>
            <thead>
              <tr style={{ background: tk.color.grid }}>
                {TABLE_HEADERS.map(h => (
                  <th key={h} style={{
                    padding: '8px 12px', color: NEUTRAL, fontWeight: tk.font.weight.bold,
                    textAlign: 'left', borderBottom: `2px solid ${tk.color.lineStrong}`, whiteSpace: 'nowrap',
                  }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {COMPLEXITY_TABLE.map((row, i) => {
                const isHcie = row.model === 'HCIE'
                return (
                  <tr key={row.model} style={{
                    background: isHcie ? AL : i % 2 === 0 ? tk.color.surface : '#F8FAFC',
                    fontWeight: isHcie ? tk.font.weight.bold : 400,
                  }}>
                    <td style={{ padding: '7px 12px', borderBottom: `1px solid ${tk.color.grid}`,
                                 color: MODEL_VISUAL[row.model as Model].color, fontWeight: tk.font.weight.bold }}>
                      {row.model}
                    </td>
                    <td style={{ padding: '7px 12px', borderBottom: `1px solid ${tk.color.grid}`,
                                 fontFamily: 'Consolas,monospace', color: tk.color.ink }}>
                      {row.update}
                    </td>
                    <td style={{ padding: '7px 12px', borderBottom: `1px solid ${tk.color.grid}`,
                                 fontFamily: 'Consolas,monospace', color: tk.color.ink }}>
                      {row.train}
                    </td>
                    <td style={{ padding: '7px 12px', borderBottom: `1px solid ${tk.color.grid}`,
                                 fontFamily: 'Consolas,monospace', color: tk.color.ink, fontSize: tk.font.size.sm }}>
                      {row.space}
                    </td>
                    {[row.online, row.graph, row.interp].map((v, j) => (
                      <td key={j} style={{ padding: '7px 12px', borderBottom: `1px solid ${tk.color.grid}`,
                                           textAlign: 'center', fontSize: tk.font.size.lg,
                                           color: v === '✓' ? GREEN : v === '✗' ? '#C0392B' : WARN }}>
                        {v}
                      </td>
                    ))}
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
        <div style={{ marginTop: tk.space.sm, fontSize: tk.font.size.sm, color: NEUTRAL }}>
          {t('algoCompare.sec2Legend')}
        </div>
      </section>

      {/* ── Section 3: Key design decisions ── */}
      <section style={{ marginBottom: 40 }}>
        <SectionHead title={t('algoCompare.sec3Title')} sub={t('algoCompare.sec3Sub')} />
        <div style={{ display: 'flex', flexDirection: 'column', gap: tk.space.lg }}>
          {DESIGN_DECISIONS.map((d, i) => (
            <Panel key={i} style={{ padding: 0, overflow: 'hidden', borderRadius: tk.radius.md }}>
              <div style={{ padding: '10px 16px', background: '#F8FAFC',
                            borderBottom: `1px solid ${tk.color.line}`,
                            display: 'flex', alignItems: 'center', gap: tk.space.sm }}>
                <span style={{ fontSize: tk.font.size.sm, fontWeight: tk.font.weight.heavy, color: ACCENT,
                               background: AL, borderRadius: tk.radius.lg, padding: '1px 8px' }}>
                  {i + 1}
                </span>
                <span style={{ fontWeight: tk.font.weight.bold, fontSize: tk.font.size.lg, color: tk.color.ink }}>{d.title}</span>
              </div>
              <div style={{ padding: '12px 16px' }}>
                <p style={{ fontSize: tk.font.size.base, color: NEUTRAL, lineHeight: 1.7, margin: '0 0 8px' }}>
                  {d.desc}
                </p>
                <div style={{
                  fontSize: tk.font.size.sm, fontWeight: tk.font.weight.bold, color: GREEN,
                  background: '#EAFAF1', borderRadius: tk.radius.sm, padding: '4px 10px',
                  display: 'inline-block',
                }}>
                  → {d.verdict}
                </div>
              </div>
            </Panel>
          ))}
        </div>
      </section>

      {/* ── Section 4: HCIE full pipeline ── */}
      <section style={{ marginBottom: 40 }}>
        <SectionHead title={t('algoCompare.sec4Title')} sub={t('algoCompare.sec4Sub')} />
        <Alg35Stepper />
        <Code>{`## Full loop: learner i attempts concept k, response r ∈ {0,1}

// ─── 1. RECEIVE EVENT ─────────────────────────────────────────────────
event = {learner_id: i, concept_id: k, correct: r, timestamp: t}

// ─── 2. KALMAN UPDATE  O(1) ───────────────────────────────────────────
state_ik = kf_store[i][k]          // (μ, σ²) loaded from DB / cache
K_t      = state_ik.var / (state_ik.var + R)
state_ik.mean += K_t * (r - state_ik.mean)
state_ik.var  *= (1 - K_t)

// ─── 3. BAYESIAN UPDATE  O(1) ─────────────────────────────────────────
beta_ik = beta_store[i][k]         // (α, β)
beta_ik.alpha += r
beta_ik.beta  += (1 - r)

// ─── 4. ENSEMBLE PREDICTION  O(learners=2) ────────────────────────────
p_kalman = state_ik.mean
p_bayes  = beta_ik.alpha / (beta_ik.alpha + beta_ik.beta)
p_hat    = w_kalman * p_kalman + w_bayes * p_bayes
// EG weight update omitted for brevity

// ─── 5. NEXT-CONCEPT SELECTION — Thompson bandit  O(|C_avail|) ────────
// Called when system needs to pick NEXT concept for learner i
C_avail = prerequisite_gate(i, concept_graph, τ)     // DAG constrains
for candidate k' in C_avail:
    α,β   = beta_prior_from(μ_ik', σ²_ik')           // uncertainty → prior strength
    score = thompson_contextual(α, β, zpd, ρ)        // Algoritma 3.6
next_concept = softmax_sample(scores, τ=0.2)         // the BANDIT selects
J_t = jt_compute(i, next_concept)                    // 6-dim governance VIEW → ADC
                                                     // (recorded, does NOT select)

// ─── 6. PERSIST ───────────────────────────────────────────────────────
// experiment_trajectories: jt_delta_m_contribution, jt_challenge_contribution, ...
// outbox_events → Kafka → projection-consumer → learner_projections
// ADC reads trajectory columns post-hoc for governance audit

// ─── TOTAL PER-EVENT COST ─────────────────────────────────────────────
// Steps 1-4:  O(1)
// Step 5:     O(|C_avail|) selection + O(deg(c)) J_t view ← only on
//             recommendation request; skipped on pure prediction queries
// No batch job needed, no model reload, works from first interaction`}</Code>
      </section>

      {/* ── Section 5: What the numbers mean ── */}
      <section>
        <SectionHead title={t('algoCompare.sec5Title')} sub={t('algoCompare.sec5Sub')} />
        <Code>{`## AUC comparison (matched eval, sealed run — Tabel 4.8, tie-aware rank-AUC)
// AUC = P(model ranks a correct attempt above an incorrect attempt)
// = area under ROC curve

// HCIE AUC=0.6051  — headline (canonical lagged m_K, single Kalman)
// BKT  AUC=0.5963  — best classical baseline; EM-tuned per concept
// DKT  AUC=0.5892  — underperforms on Junyi (small dataset; LSTM overfit risk)
// SAKT AUC=0.5730  — attention needs longer sequences than Junyi provides
// GKT  AUC=0.5711  — global node states hurt per-learner personalisation here
// (the rejected 2-learner deployed readout — HCIE 0.609 vs BKT 0.612 —
//  is disclosed on /review/baselines; it is NOT the headline)

// COLD-START delta (≤5 attempts, pooled Junyi):
//   HCIE - BKT = +0.037   HCIE leads in the sparse-data regime
//   (reported as a lead, not significance — the CI crosses 0 at n=10)
//   Mechanism: KF uncertainty + ZPD → explore before exploiting
//              BKT needs several attempts before EM estimate converges
//   As history grows (≤20, all): delta shrinks — BKT catches up
//   This is the expected tradeoff: online priors help cold, EM helps warm

// KEY CAVEAT: HCIE is solving a HARDER problem than DKT/SAKT/GKT
//   Those models are pure predictors evaluated at test time.
//   HCIE runs the full policy loop (recommend → observe → update) at eval time.
//   It's closer to regret minimisation than AUC maximisation.`}</Code>
      </section>

      {/* ── Section 6: measured cost & runtime ── */}
      <section>
        <SectionHead title={t('algoCompare.sec6Title')} sub={t('algoCompare.sec6Sub')} />
        <Code>{`## Live decision path (deployed gateway, measured with k6)
// p95 ≈ 24 ms per decision @ 40 req/s per IP — CPU only, no GPU, no batch queue
// per interaction: O(K) scalar ops (constant rolling windows: 10/100/100/20)

## Regenerating the thesis evidence (measured wall-clock)
// 1) verify Tabel 4.8 from the sealed per-row CSV (10,500 rows × 5 models):
//      sklearn roc_auc_score → 0.6051 / 0.5963 / 0.5892 / 0.5730 / 0.5711
//      wall-clock ≈ 2 s            (re-measured 2026-07-04 — exact reproduction)
// 2) full 5-model re-score from the DB (dump_matched_eval_perrow.py):
//      > 10 min                    (DKT/SAKT torch inference on CPU dominates)
// 3) full sealed-run replay through the live runtime (API + outbox + consumers):
//      ≈ 7.7 events/s + ~90 s startup   (measured 2026-06-25)
//      → anchor N=96,727 ≈ 3.5 h wall-clock

## Training cost
// HCIE: none — no offline training, no embeddings, 0 GPU-hours
// DKT / SAKT / GKT: require offline training per dataset before any prediction
//   (that asymmetry is the Pareto argument: competitive AUC at ~zero setup cost)`}</Code>
      </section>

      {/* ── Section 7: all seven thesis algorithms, verbatim ── */}
      <section>
        <SectionHead title={t('algoCompare.sec7Title')} sub={t('algoCompare.sec7Sub')} />
        <ThesisAlgBrowser />
      </section>

      <NextSteps />
    </div>
  )
}
