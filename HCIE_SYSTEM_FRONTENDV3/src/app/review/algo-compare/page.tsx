'use client'

import { useState } from 'react'
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

// ─── 5. JT SCORE — recommendation signal  O(indeg(k_next)) ───────────
// Called when system needs to pick NEXT concept for learner i
for candidate k' in concept_graph.successors(k) + unexplored:
    jt_scores[k'] = jt_compute(i, k')   // 6-signal decomposition
next_concept = argmax(jt_scores)        // highest utility concept

// ─── 6. PERSIST ───────────────────────────────────────────────────────
// experiment_trajectories: jt_delta_m_contribution, jt_challenge_contribution, ...
// outbox_events → Kafka → projection-consumer → learner_projections
// ADC reads trajectory columns post-hoc for governance audit

// ─── TOTAL PER-EVENT COST ─────────────────────────────────────────────
// Steps 1-4:  O(1)
// Step 5:     O(|successors(k)| * indeg(k'))  ← only on recommendation request
//             skipped on pure prediction queries
// No batch job needed, no model reload, works from first interaction`}</Code>
      </section>

      {/* ── Section 5: What the numbers mean ── */}
      <section>
        <SectionHead title={t('algoCompare.sec5Title')} sub={t('algoCompare.sec5Sub')} />
        <Code>{`## AUC comparison (Table 1, sealed N=96,727 Junyi Phase-2)
// AUC = P(model ranks a correct attempt above an incorrect attempt)
// = area under ROC curve

// BKT  AUC=0.6118  — best simple baseline; EM-tuned per concept
// HCIE AUC=0.6090  — NOT the headline (online, no per-concept EM tuning)
// DKT  AUC=0.5892  — underperforms on Junyi (small dataset; LSTM overfit risk)
// SAKT AUC=0.5730  — attention needs longer sequences than Junyi provides
// GKT  AUC=0.5711  — global node states hurt per-learner personalisation here

// COLD-START delta (Table 2, ≤5 attempts):
//   HCIE - BKT = +0.037   HCIE wins in sparse-data regime
//   Mechanism: KF uncertainty + ZPD → explore before exploiting
//              BKT needs several attempts before EM estimate converges
//   As history grows (≤20, all): delta shrinks — BKT catches up
//   This is the expected tradeoff: online priors help cold, EM helps warm

// KEY CAVEAT: HCIE is solving a HARDER problem than DKT/SAKT/GKT
//   Those models are pure predictors evaluated at test time.
//   HCIE runs the full policy loop (recommend → observe → update) at eval time.
//   It's closer to regret minimisation than AUC maximisation.`}</Code>
      </section>

      <NextSteps />
    </div>
  )
}
