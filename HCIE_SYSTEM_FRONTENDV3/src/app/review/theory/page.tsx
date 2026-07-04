'use client'

import { useState } from 'react'
import { useT } from '@/contexts/language_context'
import { NextSteps } from '@/components/review/NextSteps'

// ── palette ────────────────────────────────────────────────────────────────────
const C = {
  bg:      '#F8FAFC',
  card:    '#FFFFFF',
  border:  '#E2E8F0',
  accent:  '#1565C0',
  accentL: '#E3F2FD',
  green:   '#1E8449',
  greenL:  '#EAFAF1',
  warn:    '#B7791F',
  warnL:   '#FFFBEB',
  red:     '#C0392B',
  redL:    '#FDEDEC',
  neutral: '#4A5568',
  dark:    '#1A2332',
  muted:   '#94A3B8',
  purple:  '#6D28D9',
  purpleL: '#EDE9FE',
  teal:    '#0891B2',
  tealL:   '#ECFEFF',
  orange:  '#C05621',
  orangeL: '#FFFAF0',
}

type GroundingStatus = 'PASS' | 'DISCLOSE' | 'FAIL' | 'N/A'

// ── helpers ────────────────────────────────────────────────────────────────────

function Tag({ label, color, bg }: { label: string; color: string; bg: string }) {
  return (
    <span style={{
      display: 'inline-block', padding: '2px 8px', borderRadius: 10,
      fontSize: 10, fontWeight: 700, letterSpacing: '0.06em',
      color, background: bg, textTransform: 'uppercase' as const, whiteSpace: 'nowrap' as const,
    }}>{label}</span>
  )
}

function GroundingBadge({ status }: { status: GroundingStatus }) {
  const map: Record<GroundingStatus, { color: string; bg: string }> = {
    PASS:     { color: C.green,  bg: C.greenL },
    DISCLOSE: { color: C.warn,   bg: C.warnL  },
    FAIL:     { color: C.red,    bg: C.redL   },
    'N/A':    { color: C.muted,  bg: '#F1F5F9' },
  }
  const s = map[status]
  return <Tag label={status} color={s.color} bg={s.bg} />
}

function Mono({ children }: { children: React.ReactNode }) {
  return (
    <code style={{
      fontFamily: '"Fira Code",Consolas,monospace',
      fontSize: 11, background: '#F1F5F9', padding: '1px 5px', borderRadius: 3,
      color: C.accent,
    }}>{children}</code>
  )
}

function SectionHead({ n, title, sub }: { n: string; title: string; sub?: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 14, margin: '40px 0 20px' }}>
      <div style={{
        width: 40, height: 40, borderRadius: 10, background: C.accent, color: '#fff',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontWeight: 800, fontSize: 15, flexShrink: 0,
      }}>{n}</div>
      <div>
        {sub && <div style={{ fontSize: 10, fontWeight: 700, color: C.muted,
                               letterSpacing: '0.1em', textTransform: 'uppercase' as const,
                               marginBottom: 2 }}>{sub}</div>}
        <div style={{ fontSize: 18, fontWeight: 800, color: C.dark }}>{title}</div>
      </div>
    </div>
  )
}

// ── Framework card ─────────────────────────────────────────────────────────────

interface Framework {
  id: string
  name: string
  short: string
  category: string
  citation: string
  theorem: string
  hcieRole: string
  component: string
  grounding: GroundingStatus
  groundingNote: string
  formula?: string
  cpNote: string
}

function FrameworkCard({ fw }: { fw: Framework }) {
  const t = useT()
  const [open, setOpen] = useState(false)

  const catColor: Record<string, string> = {
    'Math/Stats':   C.accent,
    'ML/Online':    C.purple,
    'Control':      C.teal,
    'Pedagogy':     C.orange,
    'Architecture': C.green,
    'Baseline':     C.neutral,
  }
  const color = catColor[fw.category] || C.neutral

  return (
    <div style={{
      border: `1.5px solid ${C.border}`, borderRadius: 10, overflow: 'hidden',
      marginBottom: 12, boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
    }}>
      {/* Header */}
      <div style={{
        background: '#F8FAFC', padding: '12px 16px',
        display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12,
      }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' as const, marginBottom: 4 }}>
            <span style={{
              fontSize: 10, fontWeight: 800, color, background: `${color}18`,
              borderRadius: 6, padding: '2px 8px', letterSpacing: '0.06em',
              textTransform: 'uppercase' as const,
            }}>{fw.category}</span>
            <GroundingBadge status={fw.grounding} />
          </div>
          <div style={{ fontWeight: 800, fontSize: 14, color: C.dark, marginBottom: 2 }}>{fw.name}</div>
          <div style={{ fontSize: 11, color: C.muted }}>{fw.citation}</div>
        </div>
        <button onClick={() => setOpen(v => !v)} style={{
          fontSize: 11, color: C.accent, background: 'none', border: `1px solid ${C.accent}`,
          borderRadius: 6, padding: '3px 10px', cursor: 'pointer', fontWeight: 600, flexShrink: 0,
        }}>{open ? '▲' : '▼'}</button>
      </div>

      {/* Always visible: theorem + role */}
      <div style={{ padding: '12px 16px', borderTop: `1px solid ${C.border}` }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
          <div>
            <div style={{ fontSize: 10, fontWeight: 700, color: C.muted, letterSpacing: '0.08em',
                           textTransform: 'uppercase' as const, marginBottom: 4 }}>{t('theory.cardClaimsLabel')}</div>
            <div style={{ fontSize: 12, color: C.dark, lineHeight: 1.65 }}>{fw.theorem}</div>
          </div>
          <div>
            <div style={{ fontSize: 10, fontWeight: 700, color: C.muted, letterSpacing: '0.08em',
                           textTransform: 'uppercase' as const, marginBottom: 4 }}>{t('theory.cardUsesLabel')}</div>
            <div style={{ fontSize: 12, color: C.dark, lineHeight: 1.65 }}>
              {fw.hcieRole}
              {fw.component && (
                <div style={{ marginTop: 4 }}>
                  <span style={{ fontSize: 10, color: C.muted }}>{t('theory.cardComponentLabel')} </span>
                  <Mono>{fw.component}</Mono>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Grounding note */}
        <div style={{
          marginTop: 10, padding: '6px 12px', borderRadius: 6, fontSize: 11, lineHeight: 1.6,
          background: fw.grounding === 'PASS' ? C.greenL : fw.grounding === 'DISCLOSE' ? C.warnL : '#F1F5F9',
          color: fw.grounding === 'PASS' ? C.green : fw.grounding === 'DISCLOSE' ? C.warn : C.neutral,
        }}>
          <strong>{t('theory.tier2AuditLabel')} </strong>{fw.groundingNote}
        </div>

        {/* Expandable: formula + CP note */}
        {open && (
          <div style={{ marginTop: 12 }}>
            {fw.formula && (
              <div style={{ marginBottom: 10 }}>
                <div style={{ fontSize: 10, fontWeight: 700, color: C.muted, letterSpacing: '0.08em',
                               textTransform: 'uppercase' as const, marginBottom: 6 }}>{t('theory.coreFormulaLabel')}</div>
                <pre style={{
                  margin: 0, padding: '10px 14px',
                  background: '#0F172A', color: '#E2E8F0',
                  borderRadius: 6, fontSize: 11, lineHeight: 1.65,
                  overflowX: 'auto',
                  fontFamily: '"Fira Code","Cascadia Code",Consolas,monospace',
                }}>{fw.formula}</pre>
              </div>
            )}
            <div style={{ fontSize: 10, fontWeight: 700, color: C.muted, letterSpacing: '0.08em',
                           textTransform: 'uppercase' as const, marginBottom: 6 }}>{t('theory.cpNotesLabel')}</div>
            <pre style={{
              margin: 0, padding: '10px 14px',
              background: '#0F172A',
              borderRadius: 6, fontSize: 11, lineHeight: 1.65,
              overflowX: 'auto',
              fontFamily: '"Fira Code","Cascadia Code",Consolas,monospace',
              whiteSpace: 'pre',
            }}>
              {fw.cpNote.split('\n').map((line, i) => (
                <span key={i} style={{
                  color: line.trim().startsWith('//') ? '#4ADE80' : '#E2E8F0',
                  display: 'block',
                }}>{line}</span>
              ))}
            </pre>
          </div>
        )}
      </div>
    </div>
  )
}

// ── Main ───────────────────────────────────────────────────────────────────────

export default function TheoryPage() {
  const t = useT()
  const [filter, setFilter] = useState<string>('All')

  // ── Framework data (display text resolved via t() at render) ──────────────────
  const FRAMEWORKS: Framework[] = [
    {
      id: 'kalman',
      name: 'Kalman Filter (Scalar)',
      short: 'KF',
      category: 'Math/Stats',
      citation: 'Kalman (1960). "A New Approach to Linear Filtering and Prediction Problems." Welch & Bishop (2006) for scalar formulation.',
      theorem: t('theory.kalmanTheorem'),
      hcieRole: t('theory.kalmanRole'),
      component: 'kalman_learner.py',
      grounding: 'PASS',
      groundingNote: t('theory.kalmanGrounding'),
      formula: `// Predict step
μ̄_t  = μ_{t-1}                // no dynamics model (constant velocity = 0)
σ̄²_t = σ²_{t-1} + Q          // add process noise Q=0.01

// Update step  (r_t ∈ {0,1} = outcome)
K_t  = σ̄²_t / (σ̄²_t + R)    // Kalman gain; R=0.1 obs noise
μ_t  = μ̄_t + K_t * (r_t - μ̄_t)
σ²_t = (1 - K_t) * σ̄²_t      // posterior variance shrinks

// Uncertainty signal fed to JT:
JT_uncertainty = σ²_t         // exploration pull`,
      cpNote: `// Why KF beats naive EMA for mastery tracking:
// EMA:  μ_t = α*r_t + (1-α)*μ_{t-1}  — α is fixed, ignores confidence
// KF:   α ≡ K_t = σ̄²/(σ̄²+R)  — α is ADAPTIVE based on current uncertainty
//   Early: σ² is large → K large → move fast toward observations
//   Late:  σ² is small → K small → stable, resist noise
// Also: σ² gives free uncertainty estimate → drives JT exploration
// Space: O(2) per (learner, concept) pair  — no embedding, no history`},

    {
      id: 'bayesian',
      name: 'Bayesian Beta-Bernoulli (Conjugate Pair)',
      short: 'Bayes',
      category: 'Math/Stats',
      citation: 'Corbett & Anderson (1995). "Knowledge Tracing: Modeling the Acquisition of Procedural Knowledge." J. of User Modeling and User-Adapted Interaction.',
      theorem: t('theory.bayesianTheorem'),
      hcieRole: t('theory.bayesianRole'),
      component: 'bayesian_learner.py',
      grounding: 'PASS',
      groundingNote: t('theory.bayesianGrounding'),
      formula: `// Init from population prior (Yudelson et al. 2013):
α_0 = population_correct + 1
β_0 = population_incorrect + 1

// Update on each attempt:
α_t = α_{t-1} + r_t          // correct count
β_t = β_{t-1} + (1 - r_t)   // incorrect count

// Mastery estimate:
E[p] = α_t / (α_t + β_t)

// Uncertainty (credible interval half-width):
Var[p] = α*β / ((α+β)² * (α+β+1))
95% CI ≈ E[p] ± 1.96 * sqrt(Var[p])`,
      cpNote: `// Why conjugate prior matters for cold-start:
// Non-conjugate: need MCMC or VI → too slow for per-interaction update
// Beta-Bernoulli conjugate: posterior is closed-form → O(1) update
//   "Bayesian surprise": posterior mean moves by K_Bayes = 1/(α+β+1) per obs
//   This is equivalent to a KF with obs noise R = α*β/(α+β)^2
//   (the two learners are NOT identical — Kalman uses fixed R, Bayes adapts)
// Individualized prior (Yudelson et al. 2013):
//   Instead of α=1,β=1 (uniform), use population base rates per concept
//   Faster convergence at cold-start — less regression to 0.5`},

    {
      id: 'thompson',
      name: 'Thompson Sampling (Bayesian MAB)',
      short: 'TS',
      category: 'ML/Online',
      citation: 'Thompson (1933). "On the Likelihood that One Unknown Probability Exceeds Another." Agrawal & Goyal (2012). "Analysis of Thompson Sampling for the Multi-armed Bandit Problem." Lattimore & Szepesvári (2020). "Bandit Algorithms."',
      theorem: t('theory.thompsonTheorem'),
      hcieRole: t('theory.thompsonRole'),
      component: 'bandit.py',
      grounding: 'PASS',
      groundingNote: t('theory.thompsonGrounding'),
      formula: `// Per (learner i, concept k, arm a):
// Arms: {text, mcq, video, audio, code}

// Selection:
for a in arms:
    θ_a ~ Beta(α_{i,k,a}, β_{i,k,a})   // sample from posterior
serve arm* = argmax_a θ_a               // O(K) samples, K=5

// Feedback update:
α_{arm*} += r_t          // reward = 1 if learner succeeded
β_{arm*} += (1 - r_t)

// Regret bound: E[Regret_T] = O(√(K·T·log T))
// vs UCB1: same asymptotic, but TS has better empirical constants`,
      cpNote: `// TS vs ε-greedy vs UCB1 in CP terms:
// ε-greedy: with prob ε, random arm; else argmax mean
//   Problem: ε is fixed — too much or too little exploration
// UCB1: arm = argmax[ mean_a + sqrt(2 log t / n_a) ]
//   Problem: deterministic — adversary can predict it; worse empirical constants
// Thompson Sampling: sample θ_a ~ posterior, take argmax
//   Exploration is IMPLICIT: high-uncertainty arm has high-variance Beta → often sampled
//   Exploitation is IMPLICIT: high-mean arm has peaked Beta → usually wins argmax
//   No parameter to tune — the posterior IS the exploration schedule
// Implementation note: all 5 arm-samples are independent Beta draws
//   Total cost: O(5) random variates per recommendation request`},

    {
      id: 'irt',
      name: 'Item Response Theory — 1PL (Rasch Model)',
      short: 'IRT',
      category: 'Math/Stats',
      citation: 'Rasch (1960). "Probabilistic Models for Some Intelligence and Attainment Tests." Embretson & Reise (2000). "Item Response Theory for Psychologists."',
      theorem: t('theory.irtTheorem'),
      hcieRole: t('theory.irtRole'),
      component: 'unified_brain.py (Challenge signal)',
      grounding: 'DISCLOSE',
      groundingNote: t('theory.irtGrounding'),
      formula: `// IRT 1PL (Rasch) — what it SHOULD be:
P(correct | θ_i, b_k) = σ(θ_i - b_k)
  θ_i = learner i ability  (estimated via EM or IRT fit)
  b_k = item k difficulty  (estimated from response matrix)

// V1 ACTUAL implementation (disclosed approximation):
challenge_k = 1 - (latency_k / max_latency)   // inverted latency proxy
// This is NOT item difficulty in the IRT sense — latency correlates with
// difficulty but is confounded by item format, learner familiarity, UI lag

// V2 plan: fit Rasch b_k from response matrix per dataset
//   then use |θ_i - b_k| as ZPD distance, σ(θ_i - b_k) as probability`,
      cpNote: `// Why IRT matters for the JT score:
// If difficulty b_k is wrong, the ZPD signal is also wrong:
//   ZPD(i,k) = 1 - |ability(i) - difficulty(k)| / range
//   If difficulty(k) = latency_proxy instead of IRT b_k:
//     → ZPD misranks concepts → JT recommends wrong next concept
// The inverted-latency proxy still CORRELATES with true difficulty
//   but adds noise + bias (easy/hard format confound)
// Tier 2 audit: FAIL on pure math faithfulness, but DISCLOSED_BY_DECISION
//   the paper reports this explicitly; the limitation is not hidden`},

    {
      id: 'zpd',
      name: 'Zone of Proximal Development (ZPD)',
      short: 'ZPD',
      category: 'Pedagogy',
      citation: 'Vygotsky (1978). "Mind in Society: The Development of Higher Psychological Processes." Harvard University Press.',
      theorem: t('theory.zpdTheorem'),
      hcieRole: t('theory.zpdRole'),
      component: 'unified_brain.py (JT signal 5)',
      grounding: 'DISCLOSE',
      groundingNote: t('theory.zpdGrounding'),
      formula: `// HCIE ZPD implementation:
ZPD(i,k) = 1 - |ability_i - difficulty_k| / ability_range

// ability_i   = KF mean μ_{ik}  (normalized 0-1)
// difficulty_k = Challenge proxy (inverted latency — see IRT card)
// ability_range = max ability - min ability observed

// Problem: difficulty_k is near-constant (latency proxy has low variance)
//   → |ability_i - difficulty_k| ≈ constant → ZPD ≈ constant
//   → signal saturates at ~0.97 → weak discriminator in JT ranking

// Fix in V2: use IRT b_k for difficulty → more variance → ZPD discriminates`,
      cpNote: `// ZPD in CP terms = a "difficulty matching" score
// It's essentially the INVERSE of a distance metric:
//   d(ability, difficulty) = |θ_i - b_k|
//   ZPD = 1 - d / range  ∈ [0,1]
// Maximizing ZPD = recommending concepts where d → 0
//   i.e., ability ≈ difficulty → "just right" difficulty
// Saturation bug: if b_k has low variance (all items ~same difficulty proxy),
//   then all concepts score ≈ same → ZPD provides no ranking signal
//   → JT score is effectively 5-dimensional, not 6
// This is why the ADC classifies ZPD as "near structural_zero" on Junyi`},

    {
      id: 'lyapunov',
      name: 'Lyapunov Stability (BoundedStability heuristic)',
      short: 'Lyap',
      category: 'Control',
      citation: 'Lyapunov (1892). "The General Problem of the Stability of Motion." Referenced as stability motivation; not a formal Lyapunov theorem in the implementation.',
      theorem: t('theory.lyapunovTheorem'),
      hcieRole: t('theory.lyapunovRole'),
      component: 'lyapunov_learner.py (V1 only; weight=0 in V2)',
      grounding: 'DISCLOSE',
      groundingNote: t('theory.lyapunovGrounding'),
      formula: `// BoundedStability update (V1 — NOT a Lyapunov function):
δ = r_t - μ_{t-1}               // prediction error
μ_t = μ_{t-1} + η * clip(δ, -Δ, +Δ)  // bounded step

// Formal Lyapunov would require:
//   V(μ) > 0 for μ ≠ μ*
//   dV/dt = ∇V · f(μ) ≤ 0  (decreasing energy)
// The clip() constraint provides BOUNDED steps but not V(x) guarantee
// Hence: DISCLOSE — name is a misnomer; stability is heuristic only`,
      cpNote: `// Why it's redundant and cut:
// Bayesian E[p] = α/(α+β) — also bounded to [0,1], also resists outliers
//   (prior acts as a natural regularizer; large α+β → small updates)
// BoundedStability = essentially another mean-tracking rule with clipping
//   → outputs near-identical to Bayesian on stable sequences
//   → synergy correlation r=0.92  → ensemble gets NO additional signal
//   → removing it simplifies the ensemble without AUC loss
// Decision: V2 ensemble = Kalman + Bayesian only (2-learner)
//   Kalman brings uncertainty (KF variance); Bayesian brings conjugate posteriors
//   These are mathematically distinct — not redundant`},

    {
      id: 'eg-ensemble',
      name: 'Exponentiated Gradient Ensemble (EG)',
      short: 'EG',
      category: 'ML/Online',
      citation: 'Kivinen & Warmuth (1997). "Exponentiated Gradient versus Gradient Descent for Linear Predictors." Littlestone & Warmuth (1994). "The Weighted Majority Algorithm."',
      theorem: t('theory.egTheorem'),
      hcieRole: t('theory.egRole'),
      component: 'unified_brain.py (ensemble fusion)',
      grounding: 'DISCLOSE',
      groundingNote: t('theory.egGrounding'),
      formula: `// EG weight update:
ŷ_t = Σ_l w_l · p_l(t)          // ensemble prediction
loss_l = (p_l(t) - r_t)²         // per-learner squared loss

w_l(t+1) = w_l(t) · exp(-η · loss_l)
w ← w / Σ w                      // renormalize to simplex

// Regret bound (Kivinen & Warmuth 1997):
// Σ_t (ŷ_t - r_t)² ≤ Σ_t (p_{best,t} - r_t)² + (log L) / η

// V1 empirical: η too small or losses too similar → weights frozen near 0.5`,
      cpNote: `// When EG works vs when it doesn't:
// Works well: learners have DIVERSE errors — one good at cold-start, one at warm
//   Then EG discovers which to trust for which regime
// Fails: learners make CORRELATED errors (r=0.92 Bayesian/Lyapunov)
//   Then all losses ≈ equal → all weight updates ≈ equal → near-uniform forever
// V1 sealed evidence:
//   w_Bayesian ≈ 0.33, w_Kalman ≈ 0.33, w_Lyapunov ≈ 0.33  (all three similar)
//   CV = 0.03–0.06 → barely deviated from uniform init
// V2 fix: drop Lyapunov, use only Kalman+Bayesian (more diverse error patterns)
//   + use per-concept weight tracking instead of global weights`},

    {
      id: 'dag-transfer',
      name: 'Prerequisite DAG Transfer (T_realized)',
      short: 'DAG',
      category: 'Math/Stats',
      citation: 'Barnes (2005). "The Q-matrix Method." Pavlik et al. (2009). "Performance Factors Analysis." Chen et al. (2018). "Prerequisite-Driven Deep Knowledge Tracing."',
      theorem: t('theory.dagTheorem'),
      hcieRole: t('theory.dagRole'),
      component: 'unified_brain.py (JT signal 2)',
      grounding: 'DISCLOSE',
      groundingNote: t('theory.dagGrounding'),
      formula: `// T_realized (V1 — graph-presence transfer):
T_realized(i,k) = Σ_{p ∈ predecessors(k)} mastery(i,p)
                / |predecessors(k)|        // normalized

// Causal proof (shuffled-DAG control):
//   b_treatment  = E[correct_k | crossed real edge A→B]     = 0.099
//   b_placebo    = E[correct_k | will cross edge A→B later] = 0.041
//   causal_delta = b_treatment - b_placebo                  ≈ +0.053

// Decomposition:
//   ~2/3 = curriculum proximity (same-session sequencing)
//   ~1/3 = durable causal component (survives time-placebo)`,
      cpNote: `// Shuffled-DAG control — the key methodological contribution:
// Problem: "graph improves AUC" could be caused by:
//   (a) Correct topology (edges point to real prerequisites)
//   (b) Graph presence alone (any DAG, even random, adds structure)
//   (c) Learner selection (motivated learners do more prerequisite traversal)
//
// HCIE's control design:
//   null_graph = shuffle_edges(G, preserve_degree_sequence=True)
//     → same |V|, |E|, degree distribution — but WRONG topology
//   if null_graph effect ≈ 0: (b) ruled out
//   time_placebo:
//     treatment  = "learner crossed edge BEFORE target attempt"
//     placebo    = "learner will cross edge AFTER target attempt"
//     if placebo < treatment: (c) partially ruled out
//
// Result: null≈0, placebo removes 42% → ~58% is durable causal
// This control is absent from GKT/GIKT papers — they show AUC improvement
//   but don't separate (a) from (b) from (c)`},

    {
      id: 'adc',
      name: 'Adaptive Dimension Controller (ADC) — Governance Instrument',
      short: 'ADC',
      category: 'Math/Stats',
      citation: 'Novel contribution of this thesis. Sealed threshold design inspired by preregistered hypothesis testing conventions (Simmons et al. 2011; Nosek et al. 2018). Signal-ratio threshold analogous to coefficient of variation tests in psychometrics.',
      theorem: t('theory.adcTheorem'),
      hcieRole: t('theory.adcRole'),
      component: 'adaptive_dimension_controller.py (post-hoc only)',
      grounding: 'PASS',
      groundingNote: t('theory.adcGrounding'),
      formula: `// ADC classification algorithm:
α_floor = 0.01                // sealed pre-registered
ratio_threshold = 0.08        // sealed pre-registered

for d in {ΔM, T_realized, Challenge, Uncertainty, ZPD, T_prospective}:
    μ_d   = mean(jt_{d}_contribution, over all sealed interactions)
    σ_d   = std(jt_{d}_contribution)
    ratio = σ_d / μ_d          // coefficient of variation

    if μ_d > α_floor AND ratio > ratio_threshold:
        verdict[d] = "ACTIVE"
    else:
        verdict[d] = "structural_zero"

// Critical: α_floor ≠ 0 (not just "is mean positive?")
//   Normalizer floor σ(-2.5) ≈ 0.076 → null dimensions score ~0.076
//   α_floor = 0.01 < 0.076 → threshold-fragile if dimensions sit near floor
//   Reflexive audit found this; calibrated finding is the corrected result`,
      cpNote: `// ADC in software engineering terms: a CI/CD test suite for ML governance
//   Each JT dimension = one CI assertion
//   PASS = assertion holds → dimension is doing work
//   structural_zero = assertion fails → dimension is dead weight
//   Run post-seal → like integration tests against production snapshot
//
// Key invariant: ADC reads the trajectory store (immutable after seal)
//   → no feedback loop into runtime
//   → blast radius = zero (cannot break live system)
//
// Reflexive calibration = "eating your own dog food":
//   The instrument classified its own normalizer as producing a floor
//   artifact → filed structural_zero against its own headline
//   This is rare in ML systems — most instruments are not self-auditing`},

    {
      id: 'event-sourcing',
      name: 'Event-Sourced Architecture + Outbox Pattern',
      short: 'EventSrc',
      category: 'Architecture',
      citation: 'Fowler (2005). "Event Sourcing." martinfowler.com. Vernon (2013). "Implementing Domain-Driven Design." Addison-Wesley. Richardson (2018). "Microservices Patterns." (Outbox pattern.)',
      theorem: t('theory.eventSrcTheorem'),
      hcieRole: t('theory.eventSrcRole'),
      component: 'outbox_events table + Kafka + trajectory_recorder consumer',
      grounding: 'PASS',
      groundingNote: t('theory.eventSrcGrounding'),
      formula: `// Outbox-first state mutation:
BEGIN TRANSACTION
  INSERT INTO interactions (learner_id, concept_id, correct, ...)
  INSERT INTO outbox_events (aggregate_id, event_type, payload, ...)
COMMIT                        // atomic: both succeed or neither does

// Kafka consumer reads outbox → publishes to topic
// Trajectory consumer writes experiment_trajectories with JT columns
// trajectory_recorder consumer is the ONLY writer to jt_* columns

// Replay guarantee:
replay(events=experiment_trajectories WHERE run_id='run-94a3b8ba')
  → same JT scores to 5 decimals (PYTHONHASHSEED pinned)`,
      cpNote: `// Why event-sourcing is a research infrastructure choice:
// Traditional CRUD: state is current value — history is gone
//   UPDATE learner SET mastery = 0.7  → can't replay what led to 0.7
// Event-sourced: state = replay of events
//   → can audit EVERY decision: "why did system recommend concept X at t=42?"
//   → answer: replay events 1..42, recompute JT scores, inspect signal values
//
// Outbox pattern solves the dual-write problem:
//   WITHOUT outbox: INSERT interactions; publish to Kafka
//     If Kafka publish fails → interaction saved, event lost → diverged state
//   WITH outbox: INSERT interactions + INSERT outbox_row (one transaction)
//     Separate relay process reads outbox → publishes → marks delivered
//     If relay fails → retry; idempotent; no event loss
//
// For research: this means trajectory store is COMPLETE and AUDITABLE
//   Every number in the thesis traces back to an outbox event`},

    {
      id: 'bkt-baseline',
      name: 'BKT Baseline (Corbett-Anderson HMM)',
      short: 'BKT',
      category: 'Baseline',
      citation: 'Corbett & Anderson (1995). "Knowledge Tracing: Modeling the Acquisition of Procedural Knowledge." UMUAI 4(4). Yudelson et al. (2013). "Individualized Bayesian Knowledge Tracing Models" for individualized priors.',
      theorem: t('theory.bktTheorem'),
      hcieRole: t('theory.bktRole'),
      component: 'Evaluation baseline only',
      grounding: 'N/A',
      groundingNote: t('theory.bktGrounding'),
      formula: `// BKT update (4-parameter HMM):
// Given outcome r_t:
P(K_t | r) = P(K_{t-1}) * (1-S)     / Z    if r=1  // learned + no slip
           + P(K_{t-1}) * G           / Z    if r=1  // unlearned + guessed

// Transition after update:
P(K_{t+1}) = P(K_t | r) + (1 - P(K_t | r)) * T

// Parameter fitting: EM (Expectation-Maximization)
//   E-step: forward-backward on each learner sequence → P(K_t | observations)
//   M-step: update L0, T, G, S from soft counts
//   Complexity: O(|learners| * T * 4) per EM iteration`,
      cpNote: `// BKT weakness on cold-start:
// P(L0) is population-level; per-learner estimate needs ≥5-10 obs to stabilize
// EM requires offline pass → no online update
// At ≤5 attempts: EM hasn't converged → random-ish predictions
// ASSISTments-2009, ≤5 attempts: BKT AUC=0.598 vs HCIE AUC=0.635 (+0.037)
// Mechanism: HCIE uses KF uncertainty σ² → explores diverse concepts first
//   → more informative signal → better mastery estimate at t=5
//   BKT has no exploration mechanism — just updates on whatever comes in`},

    // ── NEW ENTRIES FROM V2 THESIS ──────────────────────────────────────────────

    {
      id: 'time-placebo',
      name: 'Time-Placebo Negative Control',
      short: 'PlaceboCtrl',
      category: 'Causal',
      citation: 'Novel to this thesis (§3.3.6, §4.6). Design principle from difference-in-differences causal inference. Related: Angrist & Pischke (2009). "Mostly Harmless Econometrics."',
      theorem: t('theory.timePlaceboTheorem'),
      hcieRole: t('theory.timePlaceboRole'),
      component: 'probe_prospective_transfer.py (causal audit)',
      grounding: 'PASS',
      groundingNote: t('theory.timePlaceboGrounding'),
      formula: `// Time-placebo design:
treatment_group = {(i,k) : learner i mastered prereq A BEFORE attempt on B}
placebo_group   = {(i,k) : learner i will master prereq A AFTER attempt on B}

// Both groups: same learner, same concept pair — only timing differs
b_treatment = E[correct_B | crossed_A→B_before]  // 0.099
b_placebo   = E[correct_B | crossed_A→B_after]   // 0.041

causal_effect = b_treatment - b_placebo           // 0.058 ≈ "raw" effect
// Within-learner fixed effects further reduce selection to get ≈+0.053

// Key: placebo group has same MOTIVATED learners (selection matched)
//      difference is ONLY the causal order → isolates topology contribution`,
      cpNote: `// Why this control matters (in algorithm testing terms):
// Without placebo: "learners who traverse more graph edges score better"
//   But high-ability learners ALSO traverse more edges
//   → correlation, not causation (confounded by learner ability)
//
// With time-placebo:
//   We compare "crossed edge before vs after" WITHIN the same learner
//   Future-edge group = same ability, same motivation, same concept pair
//   The ONLY difference is whether the causal mechanism had time to act
//   → difference in outcome = pure topology effect
//
// This is analogous to a "fuzzy regression discontinuity" in causal ML:
//   the "cutoff" is event timing rather than a score threshold
//   Placement near the cutoff (same learner, different event timing) makes groups comparable`},

    {
      id: 'fixed-effects',
      name: 'Within-Learner Fixed Effects',
      short: 'FE',
      category: 'Causal',
      citation: 'Standard panel data / econometrics method. Wooldridge (2002). "Econometric Analysis of Cross Section and Panel Data." Hsiao (2014). "Analysis of Panel Data."',
      theorem: t('theory.fixedEffectsTheorem'),
      hcieRole: t('theory.fixedEffectsRole'),
      component: 'probe_prospective_transfer.py (causal audit)',
      grounding: 'PASS',
      groundingNote: t('theory.fixedEffectsGrounding'),
      formula: `// Within-learner demeaning (fixed effects transformation):
y_{it} = α_i + β·x_{it} + ε_{it}     // learner i, attempt t

// "Within" transform: subtract learner mean
ȳ_i = mean(y_{it}) over t
x̄_i = mean(x_{it}) over t

(y_{it} - ȳ_i) = β·(x_{it} - x̄_i) + (ε_{it} - ε̄_i)

// α_i (learner fixed effect) drops out → estimation uses ONLY
//   within-learner variation in topology traversal
// Identifies β = topology effect purged of all stable learner confounders`,
      cpNote: `// Fixed effects in algorithm terms:
// Standard regression: regress outcome on treatment across all learners
//   Problem: high-ability learners do more prereqs AND score better → spurious +β
// Fixed effects: compare each learner to themselves
//   "Does THIS learner score better on concepts where they traversed prerequisites?"
//   → learner ability cancels out (same learner both sides of comparison)
//
// Implementation: GROUP BY learner_id, subtract learner mean from Y and X
//   then run OLS on de-meaned data — O(N) extra computation
//
// Limitation: cannot control for time-varying confounders
//   → complemented by time-placebo which addresses the temporal ordering issue`},

    {
      id: 'permutation-test',
      name: 'Permutation / Randomization Test',
      short: 'PermTest',
      category: 'Causal',
      citation: 'Fisher (1935). "The Design of Experiments." Good (2000). "Permutation Tests." Applied here as shuffled-DAG permutation: K=100 random edge relabelings.',
      theorem: t('theory.permTestTheorem'),
      hcieRole: t('theory.permTestRole'),
      component: 'run_sealing.py + shuffled_dag_control (causal audit)',
      grounding: 'PASS',
      groundingNote: t('theory.permTestGrounding'),
      formula: `// Permutation test for topology effect:
observed_effect = estimate_topology_effect(real_DAG)   // 0.099 - 0.041 = 0.058

null_effects = []
for k in 1..K=100:
    G_k = shuffle_edges(G, preserve_degree_sequence=True)
    null_effects.append(estimate_topology_effect(G_k))

p_value = sum(1 for e in null_effects if e >= observed_effect) / K
// p_value < 0.01 → reject null of no topology effect

// Mean null: -0.011 ± 0.023  (not even near observed 0.058)
// Permuted graph typically shows NEGATIVE effect (wrong edges mislead)`,
      cpNote: `// Why permutation test is the right choice here (not t-test):
// t-test assumes: H0: μ = 0, data ~ Normal → reject if |t| > critical value
//   Problem: the null distribution for "random graph effect" is NOT known analytically
//   The shuffled-DAG null could be skewed, fat-tailed — we don't know
//
// Permutation test: directly simulates the null by GENERATING random graphs
//   No distributional assumption — just counts how many random-graph effects
//   exceed the observed real-graph effect
//   K=100: minimum resolvable p = 0.01 (1/100)
//   For full-corpus seal: same design but larger N → tighter null distribution
//
// The null mean is -0.011 (not 0!) because wrong edges ADD NOISE that hurts
// performance slightly. This is additional evidence the real DAG is doing work.`},

    {
      id: 'clt-multimedia',
      name: 'Cognitive Load Theory + Multimedia Learning',
      short: 'CLT/MML',
      category: 'Pedagogy',
      citation: 'Sweller (2024). "Cognitive Load Theory and Educational Technology." Mayer (2020). "Cognitive Theory of Multimedia Learning." Ainsworth (2021). "How Multiple Representations Support Learning." Scheiter & Gerjets (2007).',
      theorem: t('theory.cltTheorem'),
      hcieRole: t('theory.cltRole'),
      component: 'bandit.py arms + representation_selector (live deployment)',
      grounding: 'DISCLOSE',
      groundingNote: t('theory.cltGrounding'),
      formula: `// CLT model (Sweller 2004 — not directly coded, but motivating):
total_load = intrinsic_load + extraneous_load + germane_load
learning_fails if total_load > working_memory_capacity (~7 chunks)

// HCIE's interpretation:
//   intrinsic_load  = concept difficulty (JT Challenge signal)
//   extraneous_load = modality mismatch (wrong representation format)
//   germane_load    = schema formation (targeted by ZPD signal)

// Bandit resolves extraneous_load per learner:
//   arm = argmax Thompson_sample(Beta(α_{learner,concept,modality}, β_...))
//   → minimizes extraneous_load by finding the right format for this learner`,
      cpNote: `// CLT in algorithm terms:
// It's a capacity constraint: working_memory ~ a buffer of size 7
//   If the "decode representation" cost is high (extraneous), less capacity for "learn concept"
//   Different people have different decode costs for different formats
//   (e.g. a programmer has low code-decode cost; non-programmer has high)
//
// The bandit operationalizes this WITHOUT measuring cognitive load directly:
//   Proxy: if learner succeeds with format X → X has low extraneous load for them
//   Thompson Sampling → adaptive personalization of format per (learner, concept)
//
// Why not just pick the "best" format globally?
//   CLT says: optimal format is CONDITIONAL on learner + content complexity
//   Same concept at different difficulty levels may need different formats
//   → per-(learner, concept, modality) state is the right granularity`},

    {
      id: 't-prospective-failed',
      name: 'T_prospective — 5 Failed Formulations',
      short: 'T_prosp',
      category: 'Math/Stats',
      citation: 'Chen et al. (2018). "Prerequisite-Driven Deep Knowledge Tracing." Knowledge-Space Theory (Doignon & Falmagne 1999). DINA model (de la Torre 2009). PSI-KT (structural drift). All referenced in §3.3, p.118.',
      theorem: t('theory.tProspTheorem'),
      hcieRole: t('theory.tProspRole'),
      component: 'unified_brain.py (signal 6, hardcoded 0.0)',
      grounding: 'DISCLOSE',
      groundingNote: t('theory.tProspGrounding'),
      formula: `// 5 formulations attempted (all failed — shown for reference):

// F1 — Knowledge-Space outer-fringe:
T_prosp = |{k' : k' ∉ mastered, all_prereqs(k') ⊆ mastered}| / |K|
// Fails: topology-specificity test — shuffled-DAG shows similar effect

// F2 — DINA noisy-AND:
T_prosp = Π_{k' ∈ successors(k)} (1 - slip_k') * mastery(i,k)
// Fails: requires item-level slip/guess params not available in Junyi

// F3 — PSI-KT structural drift:
T_prosp = Σ KL(posterior_t || posterior_{t+delta}) over successor path
// Fails: redundant with KF uncertainty signal; also O(path_length) expensive

// F4 — Prerequisite-depth utility:
T_prosp = mastery(i,k) * depth(k) / max_depth
// Fails: global concept property, not learner-specific → same as Challenge

// F5 — Dijkstra reachability score:
T_prosp = Σ_{k' : reachable(k')} (1-mastery(i,k')) / Dijkstra_dist(k,k')
// Fails: O(|K| log |K|) per event — too expensive; also mildly topology-specific
//   but shuffled-DAG shows ~30% of effect survives → not topology-SPECIFIC enough

// CURRENT V1: T_prospective = 0.0  (hardcoded dormant)`,
      cpNote: `// Why documenting failed formulations matters scientifically:
// "5 formulations failed" is NOT a weakness — it's evidence the instrument works
//   The ADC classified T_prospective as structural_zero
//   If we had NOT tested 5 formulations, we'd have just asserted it works
//   The failure trail proves we tested the claim seriously
//
// Each failure maps to a different CS concept:
//   F1: set-reachability — FAILS topology specificity (graph presence enough)
//   F2: probabilistic AND-gate — FAILS data requirements (no item params)
//   F3: KL divergence drift — FAILS uniqueness (redundant with KF uncertainty)
//   F4: graph depth — FAILS personalization (not learner-specific)
//   F5: Dijkstra inverse-distance — FAILS computational bound AND specificity
//
// This is how a good algorithm paper documents exploration:
//   show the space of solutions attempted, prove why each fails,
//   then your final solution is justified by elimination`},

    {
      id: 'population-prior',
      name: 'Population Prior — Individualized BKT (Yudelson)',
      short: 'PopPrior',
      category: 'Math/Stats',
      citation: 'Yudelson et al. (2013). "Individualized Bayesian Knowledge Tracing Models." ITS 2013. Enables per-learner initial mastery estimation from population-level base rates.',
      theorem: t('theory.popPriorTheorem'),
      hcieRole: t('theory.popPriorRole'),
      component: 'bayesian_learner.py (init), population_prior_table (DB)',
      grounding: 'DISCLOSE',
      groundingNote: t('theory.popPriorGrounding'),
      formula: `// Population prior initialization (Yudelson 2013 adaptation):
// For concept k, collect all historical responses:
μ_k  = mean(correct_rate across all learners on k)
σ²_k = var(correct_rate across all learners on k)

// Method of moments to get Beta parameters:
κ = μ_k*(1-μ_k)/σ²_k - 1      // concentration (pseudo-count)
α₀ = μ_k * κ                  // "prior correct" count
β₀ = (1 - μ_k) * κ            // "prior incorrect" count

// New learner on concept k starts at Beta(α₀, β₀) instead of Beta(1,1)
// → posterior mean = μ_k at t=0 (not 0.5)
// → converges to true ability faster in first 5-10 attempts`,
      cpNote: `// Why population prior matters at cold-start:
// Beta(1,1) = uniform prior → E[p] = 0.5 for every learner/concept
//   Problem: if concept k has base rate 0.8 (easy), starting at 0.5 means
//   the system thinks it's much harder than it is → recommends it too much
//   → wastes interactions on "exploration" that isn't needed
//
// Population prior Beta(α₀, β₀):
//   E[p] = α₀/(α₀+β₀) = μ_k at cold-start → correct difficulty estimate immediately
//   The "pseudo-count" κ controls how fast the prior washes out:
//   high κ → strong prior (trust population); low κ → weak prior (adapt fast)
//
// This is why V2 (with population prior) beats V1 on ASSISTments cold-start:
//   ASSISTments has ~0.60 overall correct rate but HIGH variance across concepts
//   → population prior lets system immediately distinguish easy vs hard concepts
//   → JT Challenge + ZPD signals are more accurate → better cold-start AUC`},
  ]

  // ── Gap-resolution table ───────────────────────────────────────────────────────
  const GAPS = [
    {
      gap: t('theory.gap1Name'),
      prior: t('theory.gap1Prior'),
      hcie: t('theory.gap1Hcie'),
      theory: t('theory.gap1Theory'),
    },
    {
      gap: t('theory.gap2Name'),
      prior: t('theory.gap2Prior'),
      hcie: t('theory.gap2Hcie'),
      theory: t('theory.gap2Theory'),
    },
    {
      gap: t('theory.gap3Name'),
      prior: t('theory.gap3Prior'),
      hcie: t('theory.gap3Hcie'),
      theory: t('theory.gap3Theory'),
    },
  ]

  const cats = ['All', 'Math/Stats', 'ML/Online', 'Control', 'Pedagogy', 'Causal', 'Architecture', 'Baseline']
  const catLabel: Record<string, string> = {
    'All': t('theory.catAll'),
    'Math/Stats': t('theory.catMathStats'),
    'ML/Online': t('theory.catMlOnline'),
    'Control': t('theory.catControl'),
    'Pedagogy': t('theory.catPedagogy'),
    'Causal': t('theory.catCausal'),
    'Architecture': t('theory.catArchitecture'),
    'Baseline': t('theory.catBaseline'),
  }
  const visible = filter === 'All' ? FRAMEWORKS : FRAMEWORKS.filter(f => f.category === filter)

  // ── §3 Named results ─────────────────────────────────────────────────────────
  const NAMED_RESULTS = [
    {
      name: t('theory.namedShuffledName'),
      result: t('theory.namedShuffledResult'),
      numbers: 'b_durable=0.099, b_placebo=0.041, causal≈+0.053 (full-corpus N≈1.98M, p<0.01)',
      note: t('theory.namedShuffledNote'),
    },
    {
      name: t('theory.namedTaxonomyName'),
      result: t('theory.namedTaxonomyResult'),
      numbers: t('theory.namedTaxonomyNumbers'),
      note: t('theory.namedTaxonomyNote'),
    },
    {
      name: t('theory.namedReflexiveName'),
      result: t('theory.namedReflexiveResult'),
      numbers: 'α_floor=0.01 < normalizer_floor=0.076 → threshold-fragile → re-derived under shuffled-DAG',
      note: t('theory.namedReflexiveNote'),
    },
    {
      name: t('theory.namedColdStartName'),
      result: t('theory.namedColdStartResult'),
      numbers: '≤5: HCIE 0.6348 vs BKT 0.5980 (+0.037); ≤10: +0.044; overall: +0.013',
      note: t('theory.namedColdStartNote'),
    },
  ]

  // ── §4 pipeline steps ──────────────────────────────────────────────────────────
  const PIPELINE_STEPS = [
    { label: t('theory.pipeStep1Label'), sub: 'experiment_trajectories\nN=96,727 rows (immutable)' },
    { label: t('theory.pipeStep2Label'), sub: 'μ_d = mean(jt_{d})\nσ_d = std(jt_{d})' },
    { label: t('theory.pipeStep3Label'), sub: 'μ_d > α_floor AND\nσ_d/μ_d > ratio_thresh' },
    { label: t('theory.pipeStep4Label'), sub: t('theory.pipeStep4Sub') },
    { label: t('theory.pipeStep5Label'), sub: t('theory.pipeStep5Sub') },
  ]

  // ── §4.3 topology taxonomy rows ──────────────────────────────────────────────
  const TAXONOMY_ROWS = [
    { cls: t('theory.taxExplicitDag'),     struct: t('theory.taxExplicitDagStruct'),   ex: 'Junyi, ASSISTments-2009,\nCSEDM',                   pred: 'ACTIVE',          color: C.green,   reason: t('theory.taxExplicitDagReason') },
    { cls: t('theory.taxBipartite'),       struct: t('theory.taxBipartiteStruct'),     ex: 'ASSISTments-2015,\nmost IRT datasets',              pred: 'structural_zero', color: C.red,     reason: t('theory.taxBipartiteReason') },
    { cls: t('theory.taxFlat'),            struct: t('theory.taxFlatStruct'),          ex: 'EdNet (flat KC),\nKhan Academy basic',              pred: 'structural_zero', color: C.red,     reason: t('theory.taxFlatReason') },
    { cls: t('theory.taxTransition'),      struct: t('theory.taxTransitionStruct'),    ex: 'pyKT auto-generated\ngraph from response data',      pred: 'structural_zero', color: C.warn,    reason: t('theory.taxTransitionReason') },
    { cls: t('theory.taxNull'),            struct: t('theory.taxNullStruct'),          ex: 'Single-skill KT tasks,\nshuffled-DAG null',           pred: 'structural_zero', color: C.red,     reason: t('theory.taxNullReason') },
  ]

  // ── §5 ADC software-pattern cards ────────────────────────────────────────────
  const ADC_PATTERNS = [
    {
      analogy: t('theory.adcPatternCiTitle'),
      description: t('theory.adcPatternCiDesc'),
      code: '// assert mean_contribution > 0.01\n// assert cv > 0.08\n// → PASS or FAIL per dimension',
    },
    {
      analogy: t('theory.adcPatternHealthTitle'),
      description: t('theory.adcPatternHealthDesc'),
      code: 'GET /governance/health\n→ {"ΔM":"ACTIVE",\n   "T_prospective":"zero"}',
    },
    {
      analogy: t('theory.adcPatternCoverageTitle'),
      description: t('theory.adcPatternCoverageDesc'),
      code: '// coverage_rate[dimension]\n// structural_zero = 0% meaningful\n//                   coverage',
    },
    {
      analogy: t('theory.adcPatternAbiTitle'),
      description: t('theory.adcPatternAbiDesc'),
      code: '// contract: dim ∈ ACTIVE\n// violation: dim ∈ structural_zero\n// → disclose in Methods section',
    },
  ]

  return (
    <div style={{ padding: '32px 40px', maxWidth: 1000, fontFamily: 'Inter,system-ui,sans-serif', color: C.dark }}>

      {/* Header */}
      <div style={{ marginBottom: 32 }}>
        <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.12em',
                      color: C.muted, textTransform: 'uppercase' as const, marginBottom: 6 }}>
          {t('theory.headerEyebrow')}
        </div>
        <h1 style={{ fontSize: 22, fontWeight: 900, color: C.dark, marginBottom: 10 }}>
          {t('theory.headerTitle')}
        </h1>
        <p style={{ fontSize: 13, color: C.neutral, lineHeight: 1.75, maxWidth: 720, marginBottom: 14 }}>
          {t('theory.headerIntro')}
        </p>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' as const }}>
          <Tag label={t('theory.legendPass')} color={C.green} bg={C.greenL} />
          <Tag label={t('theory.legendDisclose')} color={C.warn} bg={C.warnL} />
          <Tag label={t('theory.legendNa')} color={C.muted} bg="#F1F5F9" />
        </div>
      </div>

      {/* §1: Gap resolution */}
      <SectionHead n="§1" title={t('theory.sec1Title')} sub={t('theory.sec1Sub')} />
      <div style={{ overflowX: 'auto', marginBottom: 32 }}>
        <table style={{ borderCollapse: 'collapse', fontSize: 12, width: '100%' }}>
          <thead>
            <tr style={{ background: '#F1F5F9' }}>
              {[t('theory.gapColGap'), t('theory.gapColPrior'), t('theory.gapColHcie'), t('theory.gapColTheory')].map(h => (
                <th key={h} style={{ padding: '8px 12px', color: C.neutral, fontWeight: 700,
                                      textAlign: 'left', borderBottom: '2px solid #CBD5E0',
                                      whiteSpace: 'nowrap' as const }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {GAPS.map((g, i) => (
              <tr key={i} style={{ background: i % 2 === 0 ? '#fff' : '#F8FAFC' }}>
                <td style={{ padding: '8px 12px', borderBottom: '1px solid #EDF2F7',
                              fontWeight: 700, color: C.accent, whiteSpace: 'nowrap' as const }}>
                  {g.gap}
                </td>
                <td style={{ padding: '8px 12px', borderBottom: '1px solid #EDF2F7',
                              color: C.neutral, lineHeight: 1.6 }}>{g.prior}</td>
                <td style={{ padding: '8px 12px', borderBottom: '1px solid #EDF2F7',
                              color: C.dark, lineHeight: 1.6 }}>{g.hcie}</td>
                <td style={{ padding: '8px 12px', borderBottom: '1px solid #EDF2F7',
                              fontStyle: 'italic', color: C.teal, fontSize: 11 }}>{g.theory}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* §2: Framework cards */}
      <SectionHead n="§2" title={t('theory.sec2Title')} sub={t('theory.sec2Sub')} />

      {/* Category filter */}
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' as const, marginBottom: 16 }}>
        {cats.map(c => (
          <button key={c} onClick={() => setFilter(c)} style={{
            padding: '4px 12px', borderRadius: 16, fontSize: 11, fontWeight: 700,
            border: `1.5px solid ${c === filter ? C.accent : C.border}`,
            background: c === filter ? C.accent : '#fff',
            color: c === filter ? '#fff' : C.neutral,
            cursor: 'pointer', transition: 'all 0.15s',
          }}>{catLabel[c] ?? c}</button>
        ))}
      </div>

      {visible.map(fw => <FrameworkCard key={fw.id} fw={fw} />)}

      {/* §3: Named results */}
      <SectionHead n="§3" title={t('theory.sec3Title')} sub={t('theory.sec3Sub')} />

      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {NAMED_RESULTS.map((r, i) => (
          <div key={i} style={{ border: `1px solid ${C.border}`, borderRadius: 8, overflow: 'hidden' }}>
            <div style={{ background: C.accentL, padding: '10px 16px',
                          fontWeight: 700, fontSize: 13, color: C.accent }}>{r.name}</div>
            <div style={{ padding: '12px 16px' }}>
              <div style={{ fontSize: 12, color: C.dark, lineHeight: 1.7, marginBottom: 8 }}>{r.result}</div>
              <div style={{ fontFamily: 'Consolas,monospace', fontSize: 11, color: C.green,
                             background: C.greenL, borderRadius: 6, padding: '4px 10px',
                             marginBottom: 8 }}>{r.numbers}</div>
              <div style={{ fontSize: 11, color: C.neutral, fontStyle: 'italic' }}>{r.note}</div>
            </div>
          </div>
        ))}
      </div>

      {/* §4 — ADC deep dive */}
      <SectionHead n="§4" title={t('theory.sec4Title')} sub={t('theory.sec4Sub')} />

      {/* Pipeline overview */}
      <div style={{ background: C.accentL, border: `1.5px solid ${C.accent}`, borderRadius: 10,
                    padding: '16px 20px', marginBottom: 20 }}>
        <div style={{ fontWeight: 800, fontSize: 14, color: C.accent, marginBottom: 12 }}>
          {t('theory.pipelineTitle')}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 0, flexWrap: 'wrap' as const }}>
          {PIPELINE_STEPS.map((step, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center' }}>
              <div style={{
                background: '#fff', border: `1px solid ${C.accent}`, borderRadius: 8,
                padding: '8px 12px', textAlign: 'center' as const, minWidth: 120,
              }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: C.accent, marginBottom: 2 }}>{step.label}</div>
                <div style={{ fontSize: 10, color: C.neutral, lineHeight: 1.4, whiteSpace: 'pre' as const }}>{step.sub}</div>
              </div>
              {i < 4 && (
                <div style={{ fontSize: 18, color: C.accent, margin: '0 6px', fontWeight: 300 }}>→</div>
              )}
            </div>
          ))}
        </div>
        <div style={{ marginTop: 12, fontSize: 11, color: C.neutral }}>
          <strong>{t('theory.pipelineInvariantLabel')}</strong> {t('theory.pipelineInvariantBody')}
        </div>
      </div>

      {/* The classification algorithm */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ fontWeight: 700, fontSize: 14, color: C.dark, marginBottom: 10 }}>
          {t('theory.sec4Sub1Title')}
        </div>
        <pre style={{
          margin: 0, padding: '14px 18px', background: '#0F172A',
          borderRadius: 8, fontSize: 11, lineHeight: 1.7, overflowX: 'auto',
          fontFamily: '"Fira Code","Cascadia Code",Consolas,monospace',
        }}>
          {`// ADC classification — runs post-seal on frozen trajectory snapshot
// Input:  experiment_trajectories WHERE run_id = '<sealed_run>'
// Output: verdict[d] ∈ {ACTIVE, structural_zero} for each d

α_floor          = 0.01   // pre-registered, sealed before data analysis
ratio_threshold  = 0.08   // pre-registered

DIMENSIONS = {
  "ΔM":            "jt_delta_m_contribution",
  "T_realized":    "jt_transfer_contribution",
  "Challenge":     "jt_challenge_contribution",
  "Uncertainty":   "jt_uncertainty_contribution",
  "ZPD":           "jt_zpd_contribution",
  "T_prospective": "jt_transfer_prospective_contribution",
}

for name, col in DIMENSIONS:
    values = SELECT col FROM experiment_trajectories WHERE run_id = sealed_run
    μ_d    = mean(values)
    σ_d    = std(values)
    ratio  = σ_d / μ_d        // coefficient of variation

    // TWO-THRESHOLD GATE:
    if μ_d > α_floor AND ratio > ratio_threshold:
        verdict[name] = "ACTIVE"         // dimension carries signal
    else:
        verdict[name] = "structural_zero" // dimension is dead weight

// Sealed V1 results (run-94a3b8ba, N=96,727):
// ΔM:           μ=0.083  cv=0.43  → ACTIVE
// Challenge:    μ=0.158  cv=0.22  → ACTIVE   ← largest contributor
// Uncertainty:  μ=0.047  cv=0.38  → ACTIVE
// ZPD:          μ=0.052  cv=0.15  → ACTIVE   (near structural_zero border)
// T_realized:   μ=0.031  cv=0.29  → ACTIVE   (on explicit-DAG datasets)
// T_prospective:μ=0.000  cv=N/A  → structural_zero (hardcoded 0.0)`
            .split('\n').map((line, i) => (
              <span key={i} style={{
                color: line.trim().startsWith('//') ? '#4ADE80'
                     : /^(α_floor|ratio_threshold|DIMENSIONS|for |if |else:|verdict)/.test(line.trim()) ? '#93C5FD'
                     : /^\/\/ Sealed V1/.test(line.trim()) ? '#FACC15'
                     : '#E2E8F0',
                display: 'block',
              }}>{line}</span>
            ))}
        </pre>
      </div>

      {/* The floor artifact bug */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ fontWeight: 700, fontSize: 14, color: C.dark, marginBottom: 10 }}>
          {t('theory.sec4Sub2Title')}
        </div>
        <div style={{
          background: C.warnL, border: `1.5px solid ${C.warn}`, borderRadius: 8,
          padding: '12px 16px', marginBottom: 10, fontSize: 12, color: C.dark, lineHeight: 1.75,
        }}>
          <strong>{t('theory.floorBugReportLabel')}</strong> {t('theory.floorBugReportA')} <Mono>σ(x) = 1/(1+e^(-x))</Mono>.
          {' '}{t('theory.floorBugReportB')} <Mono>σ(−2.5) ≈ 0.076</Mono>. {t('theory.floorBugReportC')} <em>{t('theory.floorBugReportNull')}</em>
          {' '}{t('theory.floorBugReportD')} <Mono>α_floor = 0.01 &lt; 0.076</Mono> {t('theory.floorBugReportE')}
          {' '}{t('theory.floorBugReportF')} <strong>{t('theory.floorBugReportFragile')}</strong>.
        </div>
        <pre style={{
          margin: 0, padding: '14px 18px', background: '#0F172A',
          borderRadius: 8, fontSize: 11, lineHeight: 1.7, overflowX: 'auto',
          fontFamily: '"Fira Code","Cascadia Code",Consolas,monospace',
        }}>
          {`// The normalizer (V1 — no zero-guard):
def normalize_jt(raw_jt):
    return sigmoid(raw_jt)       // = 1 / (1 + exp(-raw_jt))

// At raw_jt = 0 (null dimension):
sigmoid(0) = 0.5                 // NOT zero — midpoint of sigmoid

// At raw_jt = -2.5 (weak signal near null):
sigmoid(-2.5) ≈ 0.076            // floor artifact

// Result: "null" dimensions get mean_contribution ≈ 0.076
//         α_floor = 0.01 < 0.076 → threshold would classify them as ACTIVE
//         But they're not — they're just sitting on the normalizer floor

// Why the ADC caught this:
// It computed mean_contribution for T_prospective = 0.000 (hardcoded 0.0)
//   → T_prospective bypasses the sigmoid (explicitly zeroed)
//   → other "active" dimensions might also be near the floor
//   → the ADC filed structural_zero against its own verdict
//   → re-derived under shuffled-DAG control for topology-specific confirmation

// The fix (V2 plan — F4):
def normalize_jt_v2(raw_jt, zero_guard=True):
    if zero_guard and raw_jt == 0:
        return 0.0               // explicit zero → no floor artifact
    return max(0, sigmoid(raw_jt) - sigmoid(0))  // center at true zero`
            .split('\n').map((line, i) => (
              <span key={i} style={{
                color: line.trim().startsWith('//') ? '#4ADE80'
                     : line.trim().startsWith('def ') ? '#93C5FD'
                     : '#E2E8F0',
                display: 'block',
              }}>{line}</span>
            ))}
        </pre>
      </div>

      {/* Topology taxonomy */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ fontWeight: 700, fontSize: 14, color: C.dark, marginBottom: 10 }}>
          {t('theory.sec4Sub3Title')}
        </div>
        <div style={{ fontSize: 12, color: C.neutral, lineHeight: 1.7, marginBottom: 10 }}>
          {t('theory.sec4Sub3Intro')}
        </div>
        <div style={{ overflowX: 'auto', marginBottom: 10 }}>
          <table style={{ borderCollapse: 'collapse', fontSize: 12, width: '100%' }}>
            <thead>
              <tr style={{ background: '#F1F5F9' }}>
                {[t('theory.taxColClass'), t('theory.taxColStructure'), t('theory.taxColExamples'), t('theory.taxColPrediction'), t('theory.taxColReason')].map(h => (
                  <th key={h} style={{ padding: '7px 12px', color: C.neutral, fontWeight: 700,
                                        textAlign: 'left', borderBottom: '2px solid #CBD5E0',
                                        whiteSpace: 'nowrap' as const, fontSize: 11 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {TAXONOMY_ROWS.map((r, i) => (
                <tr key={i} style={{ background: i % 2 === 0 ? '#fff' : '#F8FAFC' }}>
                  <td style={{ padding: '7px 12px', borderBottom: '1px solid #EDF2F7',
                                fontWeight: 700, color: C.dark, whiteSpace: 'pre' as const, fontSize: 11 }}>{r.cls}</td>
                  <td style={{ padding: '7px 12px', borderBottom: '1px solid #EDF2F7',
                                color: C.neutral, whiteSpace: 'pre' as const, fontSize: 11 }}>{r.struct}</td>
                  <td style={{ padding: '7px 12px', borderBottom: '1px solid #EDF2F7',
                                color: C.muted, whiteSpace: 'pre' as const, fontSize: 11 }}>{r.ex}</td>
                  <td style={{ padding: '7px 12px', borderBottom: '1px solid #EDF2F7',
                                fontWeight: 700, color: r.color, fontFamily: 'Consolas,monospace', fontSize: 11 }}>{r.pred}</td>
                  <td style={{ padding: '7px 12px', borderBottom: '1px solid #EDF2F7',
                                color: C.neutral, whiteSpace: 'pre' as const, fontSize: 11 }}>{r.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <pre style={{
          margin: 0, padding: '14px 18px', background: '#0F172A',
          borderRadius: 8, fontSize: 11, lineHeight: 1.7, overflowX: 'auto',
          fontFamily: '"Fira Code","Cascadia Code",Consolas,monospace',
        }}>
          {`// Taxonomy as a decision function (O(1) lookup):
def predict_transfer_activation(dataset):
    if dataset.has_explicit_prerequisite_DAG():
        return "ACTIVE"                  // multi-level concept→concept edges
    elif dataset.is_bipartite_Q_matrix():
        return "structural_zero"         // item×skill, no skill→skill edges
    elif dataset.has_flat_skill_tags():
        return "structural_zero"         // single-level taxonomy, no hierarchy
    elif dataset.is_transition_graph():
        return "structural_zero"         // empirical co-occurrence ≠ prerequisite
    else:
        return "structural_zero"         // null / single-concept

// Why this matters for SYSTEM SELECTION (not just evaluation):
//   If you deploy HCIE on a dataset with flat skill tags:
//     T_realized = 0 for all learners → the JT is effectively 5-dimensional
//     Challenge dominates (μ=0.158, cv=0.22) → system degrades to difficulty-based selection
//   If you deploy on explicit DAG (Junyi):
//     T_realized active → topology drives transfer signal → causal benefit ≈ +0.053
//   The taxonomy tells you IN ADVANCE which regime you're in`
            .split('\n').map((line, i) => (
              <span key={i} style={{
                color: line.trim().startsWith('//') ? '#4ADE80'
                     : line.trim().startsWith('def ') || line.trim().startsWith('return') ? '#93C5FD'
                     : '#E2E8F0',
                display: 'block',
              }}>{line}</span>
            ))}
        </pre>
      </div>

      {/* Reflexive calibration */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ fontWeight: 700, fontSize: 14, color: C.dark, marginBottom: 10 }}>
          {t('theory.sec4Sub4Title')}
        </div>
        <pre style={{
          margin: 0, padding: '14px 18px', background: '#0F172A',
          borderRadius: 8, fontSize: 11, lineHeight: 1.7, overflowX: 'auto',
          fontFamily: '"Fira Code","Cascadia Code",Consolas,monospace',
        }}>
          {`// Reflexive calibration = running the ADC ON the ADC's own output
// This is unusual — most instruments don't self-audit

// Step 1: Initial sealed verdict (pre-calibration)
initial_verdict = {
  "ΔM":           "ACTIVE",          // μ=0.083 > 0.01  ✓
  "Challenge":    "ACTIVE",          // μ=0.158 > 0.01  ✓ (largest contributor)
  "Uncertainty":  "ACTIVE",          // μ=0.047 > 0.01  ✓
  "ZPD":          "ACTIVE",          // μ=0.052 > 0.01  ✓
  "T_realized":   "ACTIVE",          // μ=0.031 > 0.01  ✓
  "T_prospective":"structural_zero", // μ=0.000 (hardcoded 0.0)
}

// Step 2: ADC audits the normalizer
normalizer_floor = sigmoid(-2.5)     // ≈ 0.076
// Observation: some "ACTIVE" μ values (0.031, 0.047, 0.052) are NEAR the floor
//   T_realized μ=0.031 << normalizer_floor 0.076 → inconsistent!
//   How can a real signal have lower mean than the floor of a null dimension?
//   Answer: T_realized is genuinely near-dormant on the specific topology tested

// Step 3: ADC files structural_zero about its own headline
calibration_event = {
  "type":   "REFLEXIVE_AUDIT",
  "finding":"normalizer_floor_artifact",
  "detail": "σ(-2.5) ≈ 0.076 → null dimensions score > α_floor=0.01 → threshold-fragile",
  "action": "re-derive topology effect under shuffled-DAG control",
}

// Step 4: Re-derive under shuffled-DAG + time-placebo
// (see Time-Placebo card for the causal estimator)
calibrated_result = {
  "b_durable":      0.099,
  "b_placebo":      0.041,
  "causal_delta":  "+0.053",
  "null_shuffled": "≈ 0",
  "p_value":       "< 0.01",
  "verdict":       "REAL causal topology effect — not just floor artifact",
}

// Why this is the contribution (not the original categorical verdict):
// Any instrument can produce verdicts.
// Only an instrument willing to REVISE its own verdict earns trust.
// The ADC found its own floor bug, re-derived, and got a STRONGER result.
// That chain — find bug → rerun under control → confirm effect — is the science.`
            .split('\n').map((line, i) => (
              <span key={i} style={{
                color: line.trim().startsWith('//') ? '#4ADE80'
                     : /^(initial_verdict|normalizer_floor|calibration_event|calibrated_result)/.test(line.trim()) ? '#FACC15'
                     : /^(Step \d)/.test(line.trim()) ? '#FACC15'
                     : '#E2E8F0',
                display: 'block',
              }}>{line}</span>
            ))}
        </pre>
      </div>

      {/* ADC as a software pattern */}
      <div style={{ marginBottom: 0 }}>
        <div style={{ fontWeight: 700, fontSize: 14, color: C.dark, marginBottom: 10 }}>
          {t('theory.sec4Sub5Title')}
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 12 }}>
          {ADC_PATTERNS.map((item, i) => (
            <div key={i} style={{
              border: `1px solid ${C.border}`, borderRadius: 8, overflow: 'hidden',
            }}>
              <div style={{ background: C.accentL, padding: '8px 12px',
                             fontWeight: 700, fontSize: 12, color: C.accent }}>{item.analogy}</div>
              <div style={{ padding: '10px 12px' }}>
                <div style={{ fontSize: 11, color: C.neutral, lineHeight: 1.65, marginBottom: 8 }}>
                  {item.description}
                </div>
                <pre style={{
                  margin: 0, padding: '6px 10px', background: '#0F172A',
                  borderRadius: 4, fontSize: 10, color: '#4ADE80', lineHeight: 1.5,
                  fontFamily: '"Fira Code",Consolas,monospace',
                }}>{item.code}</pre>
              </div>
            </div>
          ))}
        </div>
        <div style={{
          background: C.greenL, border: `1px solid ${C.green}`,
          borderRadius: 8, padding: '12px 16px', fontSize: 12, color: C.dark, lineHeight: 1.75,
        }}>
          <strong>{t('theory.sec4KeyInvariantLabel')}</strong> {t('theory.sec4KeyInvariantBody')}
        </div>
      </div>

      <NextSteps />

    </div>
  )
}
