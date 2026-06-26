'use client'

/**
 * Methods Sandbox — reviewer-facing, interactive, honest.
 *
 * Every number in the thesis that a reviewer might ask "why this value?" is made explorable here,
 * with a JUDGEMENT card: is the formula grounded in real math/literature, semi-grounded (a sensible
 * default), cosmetic (no real meaning), or a BUG? All math runs in the browser on real recorded
 * values (DB-verified), so this page never queries the backend — drag freely.
 */

import { useState, useMemo } from 'react'
import { useT } from '@/contexts/language_context'
import { LearnerSelector, LearnerRow } from '@/components/learners/LearnerSelector'
import { NextSteps } from '@/components/review/NextSteps'

// ── Real DB-verified ADC inputs (sealed formula: ACTIVE iff mean>α_floor AND std/mean≥sig_ratio) ──
// Source: experiment_trajectories, AVG/STDDEV_POP(jt_transfer_contribution), 2026-05-30.
// 4 are live in the DB (real mean/std). The other 4 are external datasets analyzed offline
// (means from the reports; std not recomputed locally) — all sit below α_floor regardless.
const DATASETS: { name: string; topo: string; n: number | null; mean: number; std: number | null; sealed?: boolean; live: boolean; phase?: 1 | 2 }[] = [
  { name: 'Junyi 2015 · Phase 2', topo: 'explicit_dag · DAG injected',  n: 96727, mean: 0.01543, std: 0.02539, sealed: true, live: true, phase: 2 },
  { name: 'STATICS 2011',          topo: 'bipartite_qmatrix',           n: 5705,  mean: 0.00785, std: 0.00118, live: true },
  { name: 'ASSISTments 2009 SB',   topo: 'flat_skill_tag',              n: 9019,  mean: 0.00715, std: 0.00131, live: true },
  { name: 'ASSISTments 2012 SB',   topo: 'flat_skill_tag',              n: 6433,  mean: 0.00760, std: null,    live: false },
  { name: 'ASSISTments 2015',      topo: 'flat_skill_tag',              n: null,  mean: 0.00639, std: null,    live: false },
  { name: 'Junyi 2015 · Phase 1',  topo: 'explicit_dag · no injection', n: 9838,  mean: 0.00603, std: 0.00006, live: true, phase: 1 },
  { name: 'EdNet KT1',             topo: 'transition_only',             n: null,  mean: 0.00591, std: null,    live: false },
  { name: 'CSEDM F19',             topo: 'null_graph',                  n: null,  mean: 0.00589, std: null,    live: false },
]

// sym = the (verbatim) governance symbol; descKey = translatable description.
const JT_DIMS = [
  { key: 'w1', sym: 'ΔM',            descKey: 'methodsSandbox.jtMasteryGain',       def: 0.25, color: '#2980B9' },
  { key: 'w2', sym: 'T_realized',    descKey: 'methodsSandbox.jtRealizedTransfer',  def: 0.15, color: '#C0392B' },
  { key: 'w3', sym: 'T_prospective', descKey: 'methodsSandbox.jtStructuralUtility', def: 0.15, color: '#16A085' },
  { key: 'w4', sym: 'C',             descKey: 'methodsSandbox.jtChallenge',         def: 0.15, color: '#8E44AD' },
  { key: 'w5', sym: 'U',             descKey: 'methodsSandbox.jtUncertainty',       def: 0.15, color: '#D35400' },
  { key: 'w6', sym: 'Z',             descKey: 'methodsSandbox.jtZpd',               def: 0.15, color: '#27AE60' },
] as const

type Verdict = 'GROUNDED' | 'SEMI-GROUNDED' | 'COSMETIC' | 'BUG' | 'DISCLOSED' | 'DEFERRED'
const VERDICT_COLOR: Record<Verdict, string> = {
  'GROUNDED': '#1E8449', 'SEMI-GROUNDED': '#B9770E', 'COSMETIC': '#7F8C8D', 'BUG': '#C0392B', 'DISCLOSED': '#7F8C8D', 'DEFERRED': '#5B6B7B',
}

// Whole-core-layer signal justification — live activation on the sealed run (run-94a3b8ba, N=96,727).
// cv = sd/mean (how much a signal actually varies). ⚠ The F4 normalizer zero-guard is applied in
// source but NOT yet re-sealed → these means/cv shift slightly on the next sealed run.
// basisKey / noteKey are translatable; grp + name stay verbatim (technical labels).
const SIGNALS: { grp: string; name: string; mean: number | null; cv: number | null; verdict: Verdict; basisKey: string; noteKey: string }[] = [
  { grp: 'JT dim',   name: 'ΔM · mastery delta',  mean: 0.083, cv: 0.43, verdict: 'GROUNDED',      basisKey: 'methodsSandbox.sigDmBasis',          noteKey: 'methodsSandbox.sigDmNote' },
  { grp: 'JT dim',   name: 'T_realized',          mean: 0.015, cv: 1.65, verdict: 'SEMI-GROUNDED', basisKey: 'methodsSandbox.sigTrealizedBasis',   noteKey: 'methodsSandbox.sigTrealizedNote' },
  { grp: 'JT dim',   name: 'T_prospective',       mean: 0.000, cv: null, verdict: 'DISCLOSED',     basisKey: 'methodsSandbox.sigTprospBasis',      noteKey: 'methodsSandbox.sigTprospNote' },
  { grp: 'JT dim',   name: 'Challenge',           mean: 0.158, cv: 0.22, verdict: 'COSMETIC',      basisKey: 'methodsSandbox.sigChallengeBasis',   noteKey: 'methodsSandbox.sigChallengeNote' },
  { grp: 'JT dim',   name: 'Uncertainty',         mean: 0.119, cv: 0.58, verdict: 'GROUNDED',      basisKey: 'methodsSandbox.sigUncertaintyBasis', noteKey: 'methodsSandbox.sigUncertaintyNote' },
  { grp: 'JT dim',   name: 'ZPD',                 mean: 0.044, cv: 1.29, verdict: 'SEMI-GROUNDED', basisKey: 'methodsSandbox.sigZpdBasis',         noteKey: 'methodsSandbox.sigZpdNote' },
  { grp: 'Ensemble', name: 'Bayesian learner',    mean: 0.637, cv: 0.28, verdict: 'GROUNDED',      basisKey: 'methodsSandbox.sigBayesBasis',       noteKey: 'methodsSandbox.sigBayesNote' },
  { grp: 'Ensemble', name: 'Kalman learner',      mean: 0.783, cv: 0.28, verdict: 'GROUNDED',      basisKey: 'methodsSandbox.sigKalmanBasis',      noteKey: 'methodsSandbox.sigKalmanNote' },
  { grp: 'Ensemble', name: 'BoundedStability (ex-Lyapunov)', mean: 0.570, cv: 0.30, verdict: 'COSMETIC', basisKey: 'methodsSandbox.sigBoundedBasis', noteKey: 'methodsSandbox.sigBoundedNote' },
  { grp: 'Bandit',   name: 'Thompson selector',   mean: null,  cv: null, verdict: 'GROUNDED',      basisKey: 'methodsSandbox.sigThompsonBasis',    noteKey: 'methodsSandbox.sigThompsonNote' },
  { grp: 'Bandit',   name: 'policy_multiplier',   mean: 1.000, cv: 0.00, verdict: 'COSMETIC',      basisKey: 'methodsSandbox.sigPolicyMultBasis',  noteKey: 'methodsSandbox.sigPolicyMultNote' },
  { grp: 'Bandit',   name: '−difficulty term',    mean: null,  cv: null, verdict: 'BUG',           basisKey: 'methodsSandbox.sigDifftermBasis',    noteKey: 'methodsSandbox.sigDifftermNote' },
  { grp: 'Rate',     name: 'adaptive_rate η',     mean: 0.090, cv: 0.67, verdict: 'GROUNDED',      basisKey: 'methodsSandbox.sigAdaptiveRateBasis', noteKey: 'methodsSandbox.sigAdaptiveRateNote' },
]

// ── Beta sampler for the Thompson-sampling demo (client-side sim; backend uses a deterministic RNG stream) ──
function gaussian() { return Math.sqrt(-2 * Math.log(Math.random() || 1e-9)) * Math.cos(2 * Math.PI * Math.random()) }
function gammaSample(k: number): number {
  if (k < 1) return gammaSample(1 + k) * Math.pow(Math.random() || 1e-9, 1 / k)
  const d = k - 1 / 3, c = 1 / Math.sqrt(9 * d)
  for (;;) {
    let x = 0, v = 0
    do { x = gaussian(); v = 1 + c * x } while (v <= 0)
    v = v * v * v
    const u = Math.random()
    if (u < 1 - 0.0331 * x * x * x * x) return d * v
    if (Math.log(u || 1e-9) < 0.5 * x * x + d * (1 - v + Math.log(v))) return d * v
  }
}
function betaSample(a: number, b: number) { const x = gammaSample(a), y = gammaSample(b); return x / (x + y) }
// unnormalized Beta pdf for the curve
function betaPdf(x: number, a: number, b: number) { return Math.pow(x, a - 1) * Math.pow(1 - x, b - 1) }
const ARMS_DEF = [
  { name: 'text', rate: 0.50, color: '#2980B9' },
  { name: 'visual', rate: 0.72, color: '#16A085' },
  { name: 'interactive', rate: 0.60, color: '#D35400' },
]

// Colour per live modality (the real representation-bandit vocabulary).
const MODALITY_COLOR: Record<string, string> = {
  text: '#2980B9', mcq: '#8E44AD', video_question: '#C0392B',
  audio_listen: '#16A085', code: '#D35400', visual: '#16A085', interactive: '#D35400',
}
type BanditArm = { name: string; rate: number; color: string; alpha: number; beta: number; pulls: number; lastSample: number }
const DEMO_SEED: BanditArm[] = ARMS_DEF.map(a => ({ ...a, alpha: 1, beta: 1, pulls: 0, lastSample: 0.5 }))

function Slider({ label, value, min, max, step, onChange, fmt, color }: {
  label: string; value: number; min: number; max: number; step: number
  onChange: (v: number) => void; fmt?: (v: number) => string; color?: string
}) {
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 4 }}>
        <span style={{ color: '#4A5568', fontWeight: 600 }}>{label}</span>
        <span style={{ fontFamily: 'ui-monospace, monospace', color: color ?? '#1A2332', fontWeight: 700 }}>
          {fmt ? fmt(value) : value.toFixed(3)}
        </span>
      </div>
      <input type="range" min={min} max={max} step={step} value={value}
        onChange={e => onChange(parseFloat(e.target.value))}
        style={{ width: '100%', accentColor: color ?? '#1A5276' }} />
    </div>
  )
}

function JudgementCard({ t, formula, source, basis, verdict, why, improve }: {
  t: (k: string) => string
  formula: string; source: string; basis: string; verdict: Verdict; why: string; improve: string
}) {
  return (
    <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10, padding: 18, marginTop: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
        <span style={{ fontSize: 10, fontWeight: 800, letterSpacing: '0.08em', textTransform: 'uppercase',
                       color: '#fff', background: VERDICT_COLOR[verdict], borderRadius: 4, padding: '3px 8px' }}>
          {verdict}
        </span>
        <span style={{ fontSize: 11, color: '#718096' }}>{t('methodsSandbox.judgementTagline')}</span>
      </div>
      <div style={{ fontFamily: 'ui-monospace, monospace', fontSize: 13, background: '#1A2332', color: '#E2E8F0',
                    borderRadius: 6, padding: '10px 12px', marginBottom: 12, whiteSpace: 'pre-wrap' }}>{formula}</div>
      <Row k={t('methodsSandbox.rowSource')} v={source} />
      <Row k={t('methodsSandbox.rowBasis')} v={basis} />
      <Row k={t('methodsSandbox.rowWhy')} v={why} />
      <Row k={t('methodsSandbox.rowImprove')} v={improve} />
    </div>
  )
}
function Row({ k, v }: { k: string; v: string }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '170px 1fr', gap: 12, fontSize: 13, padding: '5px 0',
                  borderTop: '1px solid #F1F5F9' }}>
      <span style={{ color: '#718096', fontWeight: 600 }}>{k}</span>
      <span style={{ color: '#2D3748', lineHeight: 1.55 }}>{v}</span>
    </div>
  )
}
function H({ t, n, titleKey, subKey }: { t: (k: string) => string; n: string; titleKey: string; subKey: string }) {
  return (
    <div style={{ marginBottom: 16 }}>
      <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.1em', color: '#1A5276', textTransform: 'uppercase' }}>
        {t('methodsSandbox.sandboxEyebrow')} {n}
      </div>
      <h2 style={{ fontSize: 22, fontWeight: 800, color: '#1A2332', margin: '4px 0 6px' }}>{t(titleKey)}</h2>
      <p style={{ fontSize: 14, color: '#5A6776', margin: 0, maxWidth: 760, lineHeight: 1.55 }}>{t(subKey)}</p>
    </div>
  )
}

function Toggle({ t, label, sub, on, onChange, refTag }: {
  t: (k: string) => string
  label: string; sub: string; on: boolean; onChange: (v: boolean) => void; refTag: string
}) {
  return (
    <button onClick={() => onChange(!on)} style={{
      textAlign: 'left', width: '100%', cursor: 'pointer', display: 'block',
      background: on ? '#F0FAF4' : '#FFF5F5', border: `1px solid ${on ? '#B7E0D7' : '#F5C6C6'}`,
      borderRadius: 8, padding: '10px 12px', marginBottom: 8 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8 }}>
        <span style={{ fontSize: 12.5, fontWeight: 700, color: on ? '#1B5E55' : '#9B2C2C' }}>{label}</span>
        <span style={{ fontSize: 9, fontWeight: 800, color: '#fff', background: on ? '#1E8449' : '#C0392B',
                       borderRadius: 10, padding: '2px 9px', whiteSpace: 'nowrap' }}>{on ? t('methodsSandbox.toggleLocked') : t('methodsSandbox.toggleOff')}</span>
      </div>
      <div style={{ fontSize: 10.5, color: '#94A3B8', marginTop: 3, fontFamily: 'ui-monospace, monospace' }}>{refTag}</div>
      <div style={{ fontSize: 11.5, color: '#5A6776', marginTop: 3, lineHeight: 1.45 }}>{sub}</div>
    </button>
  )
}

export default function MethodsSandbox() {
  const t = useT()
  // ── Section A: ADC verdict ──
  const [alphaFloor, setAlphaFloor] = useState(0.01)
  const [sigRatio, setSigRatio] = useState(0.08)
  const verdicts = useMemo(() => DATASETS.map(d => {
    const hasStd = d.std != null
    const cv = hasStd ? (d.std as number) / d.mean : NaN
    const meanPass = d.mean > alphaFloor
    const cvPass = hasStd ? cv >= sigRatio : true   // external: std not recomputed; mean gate decides
    const active = meanPass && cvPass
    return { ...d, cv, hasStd, meanPass, cvPass, active,
      why: active ? t('methodsSandbox.whyBothPass')
         : !meanPass ? t('methodsSandbox.whyMeanFail')
         : !hasStd ? t('methodsSandbox.whyExternal')
         : t('methodsSandbox.whyRatioFail') }
  }), [alphaFloor, sigRatio, t])
  const maxMean = 0.028

  // ── Section B: JT weights ──
  const [w, setW] = useState<number[]>(JT_DIMS.map(d => d.def))
  const wSum = w.reduce((a, b) => a + b, 0)
  const wNorm = w.map(x => x / (wSum || 1))
  // sample interaction (illustrative per-dim signal in [0,1])
  const SAMPLE = [0.62, 0.30, 0.10, 0.45, 0.55, 0.40]
  const contribs = wNorm.map((wi, i) => wi * SAMPLE[i])
  const jt = contribs.reduce((a, b) => a + b, 0)

  // ── Section C: normalizer floor artifact ──
  const [z, setZ] = useState(0.0)
  const [guard, setGuard] = useState(false)
  const sigmoid = (x: number) => 1 / (1 + Math.exp(-(x - 0.5) * 5))
  const N = (x: number) => (guard && x <= 1e-9) ? 0 : sigmoid(x)
  const w2 = wNorm[1]
  const jtTransfer = w2 * N(z)
  const floor = sigmoid(0) // ≈0.0759

  // ── Section D: the 3-learner mastery ensemble (real updates, in-browser) ──
  const clamp = (x: number, lo: number, hi: number) => Math.max(lo, Math.min(hi, x))
  const [bayes, setBayes] = useState({ a: 3, b: 7 })
  const [kal, setKal] = useState({ m: 0.3, P: 0.1, K: 0 })
  const [lyap, setLyap] = useState({ m: 0.3, g: 0 })
  const [correct, setCorrect] = useState(true)
  const [diff, setDiff] = useState(0.5)
  const [steps, setSteps] = useState(0)
  const bayesM = bayes.a / (bayes.a + bayes.b)
  const stepEnsemble = () => {
    const y = correct ? 1 : 0
    setBayes(s => ({ a: s.a + (correct ? 1 : 0), b: s.b + (correct ? 0 : 1) }))   // Beta-Bernoulli conjugate (core)
    setKal(s => { const Pp = s.P + 0.01; const K = Pp / (Pp + 0.1); return { m: clamp(s.m + K * (y - s.m), 0.05, 0.95), P: (1 - K) * Pp, K } })
    setLyap(s => { const a = 0.2 * (1 - s.m); const g = correct ? a * (1 - s.m) * diff : -a * s.m * (1 - diff); return { m: clamp(s.m + g, 0.05, 0.95), g } })
    setSteps(n => n + 1)
  }
  const resetEnsemble = () => { setBayes({ a: 3, b: 7 }); setKal({ m: 0.3, P: 0.1, K: 0 }); setLyap({ m: 0.3, g: 0 }); setSteps(0) }
  const learnerPanels = [
    { color: '#2980B9', name: 'Bayesian', verdict: 'GROUNDED' as Verdict, mastery: bayesM,
      lines: [`Beta(α=${bayes.a.toFixed(0)}, β=${bayes.b.toFixed(0)})`, `α/(α+β) = ${bayesM.toFixed(3)}`, `correct→α+1 · wrong→β+1`] },
    { color: '#16A085', name: 'Kalman', verdict: 'GROUNDED' as Verdict, mastery: kal.m,
      lines: [`K = P/(P+R) = ${kal.K.toFixed(3)}`, `m += K·(y−m)`, `P = ${kal.P.toFixed(3)} · Q=.01 R=.1`] },
    { color: '#C0392B', name: 'BoundedStability (ex-Lyapunov)', verdict: 'COSMETIC' as Verdict, mastery: lyap.m,
      lines: [`α = 0.2(1−m)`, `gain = ${lyap.g.toFixed(4)}`, `no Lyapunov fn — ~0.92 corr w/ Bayesian`] },
  ]

  // ── Section E: Thompson-sampling bandit (illustrative demo OR live learner) ──
  const [arms, setArms] = useState<BanditArm[]>(DEMO_SEED.map(a => ({ ...a })))
  const [pulls, setPulls] = useState(0)
  const [lastPick, setLastPick] = useState<number | null>(null)
  // Live seeding: pull a real learner's per-modality Beta(α,β) from the backend
  // (/v3/research/learner/{id}/representation-arms) and watch Thompson sampling
  // continue from THEIR actual beliefs rather than illustrative arms.
  const [armSource, setArmSource] = useState<'demo' | 'live'>('demo')
  const [liveLearner, setLiveLearner] = useState<LearnerRow | null>(null)
  const [liveConcept, setLiveConcept] = useState<string | null>(null)
  const [liveConcepts, setLiveConcepts] = useState<{ concept_id: string; n_modalities: number; attempts: number }[]>([])
  const [livePickerOpen, setLivePickerOpen] = useState(false)
  const [liveLoading, setLiveLoading] = useState(false)
  const [liveErr, setLiveErr] = useState<string | null>(null)
  const pullN = (n: number) => {
    let pick = lastPick
    setArms(prev => {
      let cur = prev.map(a => ({ ...a }))
      for (let k = 0; k < n; k++) {
        const samples = cur.map(a => betaSample(a.alpha, a.beta))
        pick = samples.indexOf(Math.max(...samples))
        const reward = Math.random() < cur[pick].rate ? 1 : 0
        cur = cur.map((a, i) => ({ ...a, lastSample: samples[i],
          ...(i === pick ? { alpha: a.alpha + reward, beta: a.beta + (1 - reward), pulls: a.pulls + 1 } : {}) }))
      }
      return cur
    })
    setLastPick(pick)
    setPulls(p => p + n)
  }
  const loadDemoArms = () => {
    setArms(DEMO_SEED.map(a => ({ ...a }))); setArmSource('demo')
    setLiveLearner(null); setLiveConcept(null); setLiveConcepts([]); setPulls(0); setLastPick(null); setLiveErr(null)
  }
  const loadLiveArms = (learner: LearnerRow, concept: string | null) => {
    setLiveLoading(true); setLiveErr(null)
    const token = typeof window !== 'undefined'
      ? (localStorage.getItem('hcie_auth_token') || localStorage.getItem('access_token') || '') : ''
    const url = `/v3/research/learner/${encodeURIComponent(learner.user_id)}/representation-arms`
      + (concept ? `?concept_id=${encodeURIComponent(concept)}` : '')
    fetch(url, { headers: token ? { Authorization: `Bearer ${token}` } : {}, signal: AbortSignal.timeout(9000) })
      .then(r => (r.ok ? r.json() : null))
      .then((d: any) => {
        if (!d || d.status !== 'ok' || !Array.isArray(d.arms) || d.arms.length === 0) {
          setLiveErr(t('methodsSandbox.eErrNoHistory'))
          setLiveLoading(false); return
        }
        setLiveConcepts(Array.isArray(d.multi_modal_concepts) ? d.multi_modal_concepts : [])
        setArms(d.arms.map((a: any) => ({
          name: String(a.representation),
          rate: typeof a.est_success_rate === 'number' ? a.est_success_rate : 0.5,
          color: MODALITY_COLOR[a.representation] || '#5A6776',
          alpha: Number(a.alpha) || 1, beta: Number(a.beta) || 1, pulls: Number(a.attempts) || 0, lastSample: 0.5,
        })))
        setArmSource('live'); setLiveLearner(learner); setLiveConcept(concept)
        setPulls(0); setLastPick(null); setLiveLoading(false)
      })
      .catch(() => { setLiveErr(t('methodsSandbox.eErrLoad')); setLiveLoading(false) })
  }
  const resetBandit = () => {
    if (armSource === 'live' && liveLearner) loadLiveArms(liveLearner, liveConcept)
    else { setArms(DEMO_SEED.map(a => ({ ...a }))); setPulls(0); setLastPick(null) }
  }

  // ── Section H: causal topology decomposition (shuffled-DAG + time-placebo; full-corpus seal) ──
  // Sealed values from prospective_probe_v3_full.json (N=1,976,020 / 232,440 learners):
  //   past-mastery cross-concept 0.09147 ; future-mastery placebo 0.03812 ; proximity 0.13372
  //   permutation null mean −0.01112, sd 0.02284, K=100 → cross_perm_p = 0.0099.
  const [pastCoef, setPastCoef] = useState(0.091)
  const [placeboCoef, setPlaceboCoef] = useState(0.038)
  const causalLift = Math.max(0, pastCoef - placeboCoef)
  const selectionPct = pastCoef > 1e-9 ? Math.min(1, placeboCoef / pastCoef) : 0
  const H_NULL_MEAN = -0.011, H_NULL_SD = 0.023, H_PROXIMITY = 0.134
  const hZ = (causalLift - H_NULL_MEAN) / H_NULL_SD
  const atSealed = Math.abs(pastCoef - 0.091) < 1e-6 && Math.abs(placeboCoef - 0.038) < 1e-6

  // ── Section I: decision-aware acceptance — toggle the user-locked decisions, watch criteria adjudicate ──
  const [dec, setDec] = useState({
    bundle_a_defer: true,    // A2 + A5b → DEFERRED (off the ADC-first critical path)
    audit_only: true,        // A3 → PASS (V2 dims are a recorded overlay; no selection impact by design)
    ensemble_fusion: true,   // A4c → DISCLOSED (canonical mastery ≈ Kalman; don't chase ensemble>Kalman)
    bounded_stability: true, // A5a → PASS (Bayesian-BoundedStability 0.92 redundancy disclosed, kept in fusion)
  })
  type AccV = 'PASS' | 'WARN' | 'UNMEASURED' | 'DISCLOSED' | 'DEFERRED'
  const accCriteria: { id: string; title: string; verdict: AccV; ref: string; raw: string }[] = [
    { id: 'A1', title: t('methodsSandbox.accA1'), verdict: 'PASS', ref: 'tier5_baselines', raw: 'HCIE 0.609 vs BKT 0.612 (Δ−0.003)' },
    { id: 'A2', title: t('methodsSandbox.accA2'), verdict: dec.bundle_a_defer ? 'DEFERRED' : 'UNMEASURED', ref: 'bundle_a_defer=DEFER', raw: '3 external datasets not run' },
    { id: 'A3', title: t('methodsSandbox.accA3'), verdict: dec.audit_only ? 'PASS' : 'WARN', ref: 'v2_integration_mode=audit_only', raw: '4 core dims active; V2 dims overlay-only' },
    { id: 'A4a', title: t('methodsSandbox.accA4a'), verdict: 'PASS', ref: 'tier2_5_replay', raw: 'r=0.3797 ≥ 0.20' },
    { id: 'A4b', title: t('methodsSandbox.accA4b'), verdict: 'DISCLOSED', ref: 'ecology structural_zero', raw: '0% trigger — no assessment metadata' },
    { id: 'A4c', title: t('methodsSandbox.accA4c'), verdict: dec.ensemble_fusion ? 'DISCLOSED' : 'WARN', ref: 'ensemble_fusion=DISCLOSE_CANONICAL_KALMAN', raw: 'ensemble 0.311 < Kalman 0.332' },
    { id: 'A5a', title: t('methodsSandbox.accA5a'), verdict: dec.bounded_stability ? 'PASS' : 'WARN', ref: 'learner_bounded_stability=DISCLOSE', raw: 'Kalman-Bayesian 0.78; Bayes-BoundedStab 0.92' },
    { id: 'A5b', title: t('methodsSandbox.accA5b'), verdict: dec.bundle_a_defer ? 'DEFERRED' : 'UNMEASURED', ref: 'depends on Bundle A (deferred)', raw: 'no cross-dataset evidence' },
    { id: 'A5c', title: t('methodsSandbox.accA5c'), verdict: 'PASS', ref: 'tier2_5_replay', raw: 'hash_1 == hash_2 over 96,727 rows' },
  ]
  const TERMINAL_V = new Set<AccV>(['PASS', 'DISCLOSED', 'DEFERRED'])
  const accTerminal = accCriteria.filter(c => TERMINAL_V.has(c.verdict)).length
  const accOpen = accCriteria.length - accTerminal
  const allLocked = dec.bundle_a_defer && dec.audit_only && dec.ensemble_fusion && dec.bounded_stability
  const ACC_COLOR: Record<AccV, string> = {
    PASS: '#1E8449', WARN: '#B9770E', UNMEASURED: '#94A3B8', DISCLOSED: '#5B7C8A', DEFERRED: '#5B6B7B',
  }

  return (
    <div style={{ padding: '28px 36px 80px', maxWidth: 1040, fontFamily: 'Inter, system-ui, sans-serif' }}>
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: 28, fontWeight: 800, color: '#1A2332', margin: 0 }}>{t('methodsSandbox.pageTitle')}</h1>
        <p style={{ fontSize: 15, color: '#5A6776', marginTop: 8, maxWidth: 820, lineHeight: 1.6 }}
           dangerouslySetInnerHTML={{ __html: t('methodsSandbox.pageLead') }} />
        <div style={{ background: '#EBF5FB', border: '1px solid #AED6F1', borderRadius: 8, padding: '12px 16px',
                      marginTop: 12, fontSize: 13, color: '#1A5276', lineHeight: 1.55 }}
             dangerouslySetInnerHTML={{ __html: t('methodsSandbox.rerunGate') }} />
        <div style={{ display: 'flex', gap: 8, marginTop: 12, flexWrap: 'wrap' }}>
          {(['GROUNDED', 'SEMI-GROUNDED', 'COSMETIC', 'BUG', 'DISCLOSED', 'DEFERRED'] as Verdict[]).map(v => (
            <span key={v} style={{ fontSize: 11, fontWeight: 700, color: '#fff', background: VERDICT_COLOR[v],
                                   borderRadius: 4, padding: '3px 9px' }}>{v}</span>
          ))}
        </div>
      </div>

      {/* ════ SECTION A — ADC verdict ════ */}
      <section style={{ marginBottom: 44 }}>
        <H t={t} n="A" titleKey="methodsSandbox.aTitle" subKey="methodsSandbox.aSub" />
        <div style={{ display: 'grid',
                      gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                      gap: 24 }}>
          <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10, padding: 18 }}>
            <Slider label={`α_floor (${t('methodsSandbox.aMeanGate')})`} value={alphaFloor} min={0.001} max={0.02} step={0.0005}
              onChange={setAlphaFloor} fmt={v => v.toFixed(4)} color="#C0392B" />
            <Slider label={`signal_ratio (${t('methodsSandbox.aRatioGate')})`} value={sigRatio} min={0.01} max={2.0} step={0.01}
              onChange={setSigRatio} fmt={v => v.toFixed(2)} color="#8E44AD" />
            <button onClick={() => { setAlphaFloor(0.01); setSigRatio(0.08) }}
              style={{ marginTop: 6, fontSize: 12, fontFamily: 'ui-monospace, monospace', color: '#1A5276',
                       background: '#EBF5FB', border: '1px solid #AED6F1', borderRadius: 6, padding: '6px 12px', cursor: 'pointer' }}>
              {t('methodsSandbox.aResetSealed')}
            </button>
            <p style={{ fontSize: 12, color: '#718096', marginTop: 12, lineHeight: 1.5 }}
               dangerouslySetInnerHTML={{ __html: t('methodsSandbox.aTry') }} />
          </div>

          <div>
            {/* number line: mean of each dataset vs α_floor */}
            <div style={{ position: 'relative', height: 182, background: '#fff', border: '1px solid #E2E8F0',
                          borderRadius: 10, padding: '18px 20px' }}>
              <div style={{ position: 'absolute', left: `${(alphaFloor / maxMean) * 100}%`, top: 10, bottom: 10,
                            borderLeft: '2px dashed #C0392B' }}>
                <span style={{ position: 'absolute', top: -2, left: 4, fontSize: 10, color: '#C0392B', whiteSpace: 'nowrap',
                               fontFamily: 'ui-monospace, monospace' }}>α_floor {alphaFloor.toFixed(4)}</span>
              </div>
              {verdicts.map((d, i) => (
                <div key={d.name} style={{ position: 'absolute', left: `${Math.min(98, (d.mean / maxMean) * 100)}%`,
                                           top: 26 + i * 18, transform: 'translateX(-50%)' }}>
                  <div style={{ width: 11, height: 11, borderRadius: '50%',
                                background: d.active ? '#2ED573' : d.live ? '#CBD5E0' : '#EDF2F7',
                                border: '2px solid #fff',
                                boxShadow: '0 0 0 1px ' + (d.active ? '#1E8449' : '#A0AEC0') }} title={d.name} />
                </div>
              ))}
            </div>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13, marginTop: 12 }}>
              <thead><tr style={{ textAlign: 'left', color: '#718096', fontSize: 11, textTransform: 'uppercase' }}>
                <th style={{ padding: '6px 8px' }}>{t('methodsSandbox.colDataset')}</th><th>mean</th><th>std/mean</th><th>{t('methodsSandbox.colVerdict')}</th><th>{t('methodsSandbox.colWhy')}</th>
              </tr></thead>
              <tbody>
                {verdicts.map(d => (
                  <tr key={d.name} style={{ borderTop: '1px solid #F1F5F9' }}>
                    <td style={{ padding: '6px 8px', color: '#2D3748' }}>{d.name}
                      {d.sealed && <span style={{ color: '#1E8449', fontSize: 10 }}> · {t('methodsSandbox.tagSealed')}</span>}
                      {!d.live && <span style={{ color: '#A0AEC0', fontSize: 10 }}> · {t('methodsSandbox.tagExternal')}</span>}</td>
                    <td style={{ fontFamily: 'ui-monospace, monospace', color: d.meanPass ? '#1E8449' : '#C0392B' }}>{d.mean.toFixed(5)}</td>
                    <td style={{ fontFamily: 'ui-monospace, monospace', color: d.hasStd ? (d.cvPass ? '#1E8449' : '#C0392B') : '#A0AEC0' }}>{d.hasStd ? d.cv.toFixed(3) : '—'}</td>
                    <td><span style={{ fontWeight: 700, fontSize: 11, color: '#fff', borderRadius: 4, padding: '2px 7px',
                                       background: d.active ? '#2ED573' : '#94A3B8' }}>{d.active ? 'ACTIVE' : 'DORMANT'}</span></td>
                    <td style={{ color: '#718096', fontSize: 12 }}>{d.why}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        {/* The reasoning the verdicts need — why these, why phases, why only some shown */}
        <div style={{ display: 'grid',
                      gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
                      gap: 16, marginTop: 16 }}>
          <div style={{ background: '#F0FAF4', border: '1px solid #B7E0D7', borderRadius: 10, padding: 16 }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: '#1B5E55', marginBottom: 6 }}>{t('methodsSandbox.aPhaseTitle')}</div>
            <p style={{ fontSize: 13, color: '#2D3748', margin: 0, lineHeight: 1.55 }}
               dangerouslySetInnerHTML={{ __html: t('methodsSandbox.aPhaseBody') }} />
          </div>
          <div style={{ background: '#FEF9F0', border: '1px solid #F5D5A0', borderRadius: 10, padding: 16 }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: '#7E5109', marginBottom: 6 }}>{t('methodsSandbox.aJunyiTitle')}</div>
            <p style={{ fontSize: 13, color: '#2D3748', margin: 0, lineHeight: 1.55 }}
               dangerouslySetInnerHTML={{ __html: t('methodsSandbox.aJunyiBody') }} />
          </div>
        </div>
        <p style={{ fontSize: 12, color: '#718096', marginTop: 10, lineHeight: 1.5 }}
           dangerouslySetInnerHTML={{ __html: t('methodsSandbox.aFootnote') }} />
        <JudgementCard
          t={t}
          formula={"ACTIVE  iff  mean > α_floor (0.01)  AND  std/mean ≥ signal_ratio (0.08)\nsealed signal_ratio = 1.6449 = 0.02539 / 0.01543   (std/mean, NOT mean/α_floor)"}
          source={t('methodsSandbox.aJcSource')}
          basis={t('methodsSandbox.aJcBasis')}
          verdict="COSMETIC"
          why={t('methodsSandbox.aJcWhy')}
          improve={t('methodsSandbox.aJcImprove')}
        />
      </section>

      {/* ════ SECTION B — JT weights ════ */}
      <section style={{ marginBottom: 44 }}>
        <H t={t} n="B" titleKey="methodsSandbox.bTitle" subKey="methodsSandbox.bSub" />
        <div style={{ display: 'grid',
                      gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                      gap: 24 }}>
          <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10, padding: 18 }}>
            {JT_DIMS.map((d, i) => (
              <Slider key={d.key} label={`${d.sym} · ${t(d.descKey)}`} value={w[i]} min={0} max={0.5} step={0.01} color={d.color}
                onChange={v => setW(prev => prev.map((x, j) => j === i ? v : x))}
                fmt={() => `${(wNorm[i] * 100).toFixed(0)}%`} />
            ))}
            <button onClick={() => setW(JT_DIMS.map(d => d.def))}
              style={{ marginTop: 4, fontSize: 12, fontFamily: 'ui-monospace, monospace', color: '#1A5276',
                       background: '#EBF5FB', border: '1px solid #AED6F1', borderRadius: 6, padding: '6px 12px', cursor: 'pointer' }}>
              {t('methodsSandbox.bResetDefaults')}
            </button>
          </div>
          <div>
            <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10, padding: 18 }}>
              <div style={{ fontSize: 12, color: '#718096', marginBottom: 12 }}>
                JT(t) = Σ wᵢ · signalᵢ  {t('methodsSandbox.bOnSample')} →
                <b style={{ color: '#1A2332', fontFamily: 'ui-monospace, monospace', marginLeft: 6 }}>JT = {jt.toFixed(3)}</b>
              </div>
              {JT_DIMS.map((d, i) => (
                <div key={d.key} style={{ marginBottom: 8 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: '#4A5568' }}>
                    <span>{d.sym} <span style={{ color: '#A0AEC0' }}>· {t('methodsSandbox.signalLabel')} {SAMPLE[i].toFixed(2)}</span></span>
                    <span style={{ fontFamily: 'ui-monospace, monospace' }}>{contribs[i].toFixed(3)}</span>
                  </div>
                  <div style={{ height: 10, background: '#F1F5F9', borderRadius: 5, overflow: 'hidden' }}>
                    <div style={{ width: `${(contribs[i] / 0.25) * 100}%`, height: '100%', background: d.color }} />
                  </div>
                </div>
              ))}
            </div>
            <p style={{ fontSize: 12, color: '#718096', marginTop: 10, lineHeight: 1.5 }}
               dangerouslySetInnerHTML={{ __html: t('methodsSandbox.bTry') }} />
          </div>
        </div>
        <JudgementCard
          t={t}
          formula={"default = { ΔM: 0.25, T_realized: 0.15, T_prospective: 0.15, C: 0.15, U: 0.15, Z: 0.15 }   (Σ = 1)\nadapt:   wᵢ ← momentum·wᵢ + (1−momentum)·target ;  momentum = 0.7 ;  bounds: Σw=1, 0≤w≤1"}
          source={t('methodsSandbox.bJcSource')}
          basis={t('methodsSandbox.bJcBasis')}
          verdict="SEMI-GROUNDED"
          why={t('methodsSandbox.bJcWhy')}
          improve={t('methodsSandbox.bJcImprove')}
        />
      </section>

      {/* ════ SECTION C — normalizer floor artifact ════ */}
      <section style={{ marginBottom: 24 }}>
        <H t={t} n="C" titleKey="methodsSandbox.cTitle" subKey="methodsSandbox.cSub" />
        <div style={{ display: 'grid',
                      gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                      gap: 24 }}>
          <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10, padding: 18 }}>
            <Slider label={`transfer_realized (${t('methodsSandbox.cRawSignal')})`} value={z} min={0} max={1} step={0.01}
              onChange={setZ} fmt={v => v.toFixed(2)} color="#16A085" />
            <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: '#2D3748',
                            marginTop: 10, cursor: 'pointer' }}>
              <input type="checkbox" checked={guard} onChange={e => setGuard(e.target.checked)} />
              {t('methodsSandbox.cApplyFix')}
            </label>
            <div style={{ marginTop: 14, fontFamily: 'ui-monospace, monospace', fontSize: 13, lineHeight: 1.8 }}>
              <div>N(z) = <b style={{ color: '#16A085' }}>{N(z).toFixed(4)}</b></div>
              <div>jt_transfer = w2·N(z) = <b style={{ color: '#1A2332' }}>{jtTransfer.toFixed(4)}</b></div>
              <div style={{ color: z <= 1e-9 && !guard ? '#C0392B' : '#A0AEC0' }}>
                at z=0 → N = {guard ? '0.0000 ✓' : floor.toFixed(4) + ' ✗ ' + t('methodsSandbox.cFloorWord')}
              </div>
            </div>
          </div>
          <div>
            {/* curve */}
            <svg viewBox="0 0 320 150" style={{ width: '100%', height: 170, background: '#fff',
                 border: '1px solid #E2E8F0', borderRadius: 10 }}>
              <line x1="30" y1="120" x2="310" y2="120" stroke="#CBD5E0" />
              <line x1="30" y1="20" x2="30" y2="120" stroke="#CBD5E0" />
              {/* floor line */}
              {!guard && <line x1="30" y1={120 - floor * 100} x2="310" y2={120 - floor * 100} stroke="#C0392B" strokeDasharray="3 3" />}
              {/* sigmoid curve */}
              <path d={Array.from({ length: 60 }, (_, k) => {
                const x = k / 59; const yv = N(x)
                return `${k === 0 ? 'M' : 'L'} ${30 + x * 280} ${120 - yv * 100}`
              }).join(' ')} fill="none" stroke="#16A085" strokeWidth="2" />
              {/* current point */}
              <circle cx={30 + z * 280} cy={120 - N(z) * 100} r="4" fill="#1A2332" />
              <text x="34" y={120 - floor * 100 - 4} fontSize="9" fill="#C0392B" fontFamily="monospace">
                {!guard && `${t('methodsSandbox.cFloorWord')} σ(−2.5) ≈ ${floor.toFixed(3)}`}
              </text>
            </svg>
            <p style={{ fontSize: 12, color: '#718096', marginTop: 10, lineHeight: 1.5 }}
               dangerouslySetInnerHTML={{ __html: t('methodsSandbox.cExplain') }} />
          </div>
        </div>
        <JudgementCard
          t={t}
          formula={"N(z) = 1 / (1 + exp(−(z − 0.5)·5))        ← centered at 0.5, steepness 5\nN(0) = σ(−2.5) ≈ 0.0759   (a non-zero FLOOR, even when transfer is exactly zero)"}
          source={t('methodsSandbox.cJcSource')}
          basis={t('methodsSandbox.cJcBasis')}
          verdict="BUG"
          why={t('methodsSandbox.cJcWhy')}
          improve={t('methodsSandbox.cJcImprove')}
        />
      </section>

      {/* ════ SECTION D — the 3-learner ensemble ════ */}
      <section style={{ marginBottom: 44 }}>
        <H t={t} n="D" titleKey="methodsSandbox.dTitle" subKey="methodsSandbox.dSub" />
        <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10, padding: 18, marginBottom: 16 }}>
          <div style={{ display: 'flex', gap: 18, alignItems: 'center', flexWrap: 'wrap' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, color: '#2D3748' }}>
              <input type="checkbox" checked={correct} onChange={e => setCorrect(e.target.checked)} /> {t('methodsSandbox.dAnswerCorrect')}
            </label>
            <div style={{ flex: 1, minWidth: 200, marginBottom: -12 }}>
              <Slider label={t('methodsSandbox.dDifficulty')} value={diff} min={0} max={1} step={0.05} onChange={setDiff} fmt={v => v.toFixed(2)} color="#8E44AD" />
            </div>
            <button onClick={stepEnsemble} style={{ padding: '8px 18px', background: '#1A5276', color: '#fff', border: 'none', borderRadius: 8, fontSize: 13, fontWeight: 700, cursor: 'pointer' }}>
              {t('methodsSandbox.dSubmit')} · {steps}
            </button>
            <button onClick={resetEnsemble} style={{ fontSize: 12, fontFamily: 'ui-monospace, monospace', color: '#718096', background: '#F1F5F9', border: '1px solid #CBD5E0', borderRadius: 6, padding: '7px 12px', cursor: 'pointer' }}>{t('methodsSandbox.reset')}</button>
          </div>
          <div style={{ display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                        gap: 14, marginTop: 16 }}>
            {learnerPanels.map(p => (
              <div key={p.name} style={{ border: `1px solid ${p.color}30`, borderRadius: 8, padding: 14, background: p.color + '08' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <span style={{ fontWeight: 700, color: p.color, fontSize: 14 }}>{p.name}</span>
                  <span style={{ fontSize: 9, fontWeight: 800, color: '#fff', background: VERDICT_COLOR[p.verdict], borderRadius: 3, padding: '2px 6px' }}>{p.verdict}</span>
                </div>
                <div style={{ fontSize: 30, fontWeight: 800, color: '#1A2332', fontFamily: 'ui-monospace, monospace' }}>{p.mastery.toFixed(3)}</div>
                <div style={{ height: 8, background: '#F1F5F9', borderRadius: 4, overflow: 'hidden', margin: '6px 0 10px' }}>
                  <div style={{ width: `${p.mastery * 100}%`, height: '100%', background: p.color }} />
                </div>
                {p.lines.map((l, i) => (
                  <div key={i} style={{ fontFamily: 'ui-monospace, monospace', fontSize: 11, color: '#5A6776', lineHeight: 1.7 }}>{l}</div>
                ))}
              </div>
            ))}
          </div>
          <p style={{ fontSize: 12, color: '#718096', marginTop: 12, lineHeight: 1.5 }}
             dangerouslySetInnerHTML={{ __html: t('methodsSandbox.dExplain') }} />
        </div>
        <JudgementCard
          t={t}
          formula={"Bayesian:   α/(α+β), conjugate Beta-Bernoulli\nKalman:     K=P/(P+R); m+=K(y−m); P=(1−K)(P+Q)\n\"Lyapunov\": m += 0.2(1−m)·(1−m)·d [correct], clip[0.05,0.95]   ← no Lyapunov function"}
          source={'04_learners/{bayesian,kalman,lyapunov}_learner.py + mastery_model.py (Bayesian step) + confidence_weighted_learner.py (modulation).'}
          basis={t('methodsSandbox.dJcBasis')}
          verdict="SEMI-GROUNDED"
          why={t('methodsSandbox.dJcWhy')}
          improve={t('methodsSandbox.dJcImprove')}
        />
      </section>

      {/* ════ SECTION E — Thompson-sampling bandit ════ */}
      <section style={{ marginBottom: 44 }}>
        <H t={t} n="E" titleKey="methodsSandbox.eTitle" subKey="methodsSandbox.eSub" />
        <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10, padding: 18, marginBottom: 16 }}>
          {/* live-learner seed: bind the sandbox to a real learner's modality arms */}
          <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap', marginBottom: 12,
                        paddingBottom: 12, borderBottom: '1px dashed #E2E8F0' }}>
            <span style={{ fontSize: 12, fontWeight: 700, color: armSource === 'live' ? '#16A085' : '#718096' }}>
              {armSource === 'live'
                ? `● LIVE · ${liveLearner?.short_id ?? ''}${liveConcept ? ' · ' + liveConcept : ' · ' + t('methodsSandbox.eAllConcepts')}`
                : '○ ' + t('methodsSandbox.eDemoArms')}
            </span>
            <button onClick={() => setLivePickerOpen(o => !o)} style={{
              fontSize: 12, fontWeight: 700, color: '#fff', background: '#16A085', border: 'none',
              borderRadius: 7, padding: '6px 12px', cursor: 'pointer' }}>
              {armSource === 'live' ? t('methodsSandbox.eChangeLearner') : t('methodsSandbox.eSeedLearner')}
            </button>
            {armSource === 'live' && (
              <button onClick={loadDemoArms} style={{
                fontSize: 12, color: '#718096', background: '#F1F5F9', border: '1px solid #CBD5E0',
                borderRadius: 7, padding: '6px 12px', cursor: 'pointer' }}>{t('methodsSandbox.eBackToDemo')}</button>
            )}
            {liveLoading && <span style={{ fontSize: 12, color: '#A0AEC0' }}>⟳ {t('methodsSandbox.loading')}</span>}
            {liveErr && <span style={{ fontSize: 12, color: '#C0392B' }}>{liveErr}</span>}
            <a href="/dashboard/archetype-modality" style={{ marginLeft: 'auto', fontSize: 12, fontWeight: 700, color: '#6C3483', textDecoration: 'none', whiteSpace: 'nowrap' }}>
              {t('methodsSandbox.eArchetypeLink')} →
            </a>
          </div>
          {livePickerOpen && (
            <div style={{ border: '1px solid #E2E8F0', borderRadius: 8, padding: 10, marginBottom: 12, background: '#F8FAFC' }}>
              <LearnerSelector compact selectedId={liveLearner?.user_id ?? undefined}
                onSelect={l => { setLivePickerOpen(false); loadLiveArms(l, null) }} />
            </div>
          )}
          {armSource === 'live' && liveConcepts.length > 0 && (
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center', marginBottom: 12 }}>
              <span style={{ fontSize: 11, color: '#718096' }}>{t('methodsSandbox.eScope')}</span>
              <button onClick={() => loadLiveArms(liveLearner!, null)} style={{
                fontSize: 11, fontWeight: 600, borderRadius: 6, padding: '3px 9px', cursor: 'pointer',
                border: `1px solid ${liveConcept === null ? '#16A085' : '#CBD5E0'}`,
                background: liveConcept === null ? '#16A085' : '#fff', color: liveConcept === null ? '#fff' : '#4A5568' }}>{t('methodsSandbox.eAllConcepts')}</button>
              {liveConcepts.map(c => (
                <button key={c.concept_id} onClick={() => loadLiveArms(liveLearner!, c.concept_id)} style={{
                  fontSize: 11, fontWeight: 600, borderRadius: 6, padding: '3px 9px', cursor: 'pointer',
                  border: `1px solid ${liveConcept === c.concept_id ? '#16A085' : '#CBD5E0'}`,
                  background: liveConcept === c.concept_id ? '#16A085' : '#fff', color: liveConcept === c.concept_id ? '#fff' : '#4A5568' }}>
                  {c.concept_id} · {c.n_modalities} {t('methodsSandbox.eModes')}
                </button>
              ))}
            </div>
          )}
          {armSource === 'live' && (
            <div style={{ fontSize: 11.5, color: '#5A6776', marginBottom: 12, lineHeight: 1.5 }}
                 dangerouslySetInnerHTML={{ __html: t('methodsSandbox.eLiveNote') }} />
          )}
          <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginBottom: 14 }}>
            <button onClick={() => pullN(1)} style={{ padding: '8px 16px', background: '#1A5276', color: '#fff', border: 'none', borderRadius: 8, fontSize: 13, fontWeight: 700, cursor: 'pointer' }}>{t('methodsSandbox.eSamplePull')}</button>
            <button onClick={() => pullN(20)} style={{ padding: '8px 16px', background: '#2980B9', color: '#fff', border: 'none', borderRadius: 8, fontSize: 13, fontWeight: 700, cursor: 'pointer' }}>×20</button>
            <button onClick={resetBandit} style={{ fontSize: 12, fontFamily: 'ui-monospace, monospace', color: '#718096', background: '#F1F5F9', border: '1px solid #CBD5E0', borderRadius: 6, padding: '7px 12px', cursor: 'pointer' }}>{t('methodsSandbox.reset')}</button>
            <span style={{ fontSize: 12, color: '#718096', fontFamily: 'ui-monospace, monospace' }}>{t('methodsSandbox.ePulls')}: {pulls}</span>
          </div>
          <div style={{ display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                        gap: 14 }}>
            {arms.map((a, i) => {
              const mean = a.alpha / (a.alpha + a.beta)
              const picked = lastPick === i
              const maxPdf = Math.max(...Array.from({ length: 40 }, (_, k) => betaPdf((k + 0.5) / 40, a.alpha, a.beta)).filter(Number.isFinite), 0.01)
              return (
                <div key={a.name} style={{ border: `1px solid ${picked ? a.color : '#E2E8F0'}`, borderRadius: 8, padding: 14,
                                           background: picked ? a.color + '10' : '#fff', boxShadow: picked ? `0 0 0 1px ${a.color}` : 'none' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                    <span style={{ fontWeight: 700, color: a.color, fontSize: 14 }}>{a.name}{picked && <span style={{ fontSize: 10, color: a.color }}> · {t('methodsSandbox.ePicked')}</span>}</span>
                    <span style={{ fontSize: 11, color: '#A0AEC0', fontFamily: 'ui-monospace, monospace' }}>{armSource === 'live' ? t('methodsSandbox.eObs') : t('methodsSandbox.eTrue')} {a.rate.toFixed(2)}</span>
                  </div>
                  <svg viewBox="0 0 120 44" style={{ width: '100%', height: 50 }}>
                    <path d={Array.from({ length: 40 }, (_, k) => { const x = (k + 0.5) / 40; const y = betaPdf(x, a.alpha, a.beta) / maxPdf; return `${k === 0 ? 'M' : 'L'} ${x * 120} ${42 - y * 38}` }).join(' ')} fill="none" stroke={a.color} strokeWidth="1.5" />
                  </svg>
                  <div style={{ fontSize: 12, fontFamily: 'ui-monospace, monospace', color: '#1A2332', marginTop: 4 }}>
                    Beta({a.alpha.toFixed(0)},{a.beta.toFixed(0)}) · est {mean.toFixed(2)} · {a.pulls} {t('methodsSandbox.ePullsWord')}
                  </div>
                </div>
              )
            })}
          </div>
          <p style={{ fontSize: 12, color: '#718096', marginTop: 12, lineHeight: 1.5 }}
             dangerouslySetInnerHTML={{ __html: t('methodsSandbox.eExplain') }} />
        </div>
        <JudgementCard
          t={t}
          formula={"pick = argmax( θ*ₐ + φ* + γ·uncertainty + η·JT − difficulty )\nθ*ₐ ~ Beta(αₐ, βₐ)   (prior 1,1; reward → α+1, miss → β+1)\nγ = 0.1 (explore)   η = 0.05 (JT)"}
          source={t('methodsSandbox.eJcSource')}
          basis={t('methodsSandbox.eJcBasis')}
          verdict="GROUNDED"
          why={t('methodsSandbox.eJcWhy')}
          improve={t('methodsSandbox.eJcImprove')}
        />
      </section>

      {/* ════ SECTION F — whole-core-layer signal justification ════ */}
      <section style={{ marginBottom: 44 }}>
        <H t={t} n="F" titleKey="methodsSandbox.fTitle" subKey="methodsSandbox.fSub" />
        <div style={{ background: '#FFF8E1', border: '1px solid #FFE082', borderRadius: 8, padding: '10px 14px', marginBottom: 16, fontSize: 12, color: '#7E5109' }}
             dangerouslySetInnerHTML={{ __html: t('methodsSandbox.fCallout') }} />
        <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10, overflow: 'hidden' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '190px 64px 96px 116px 1fr', gap: 8, padding: '9px 14px', background: '#F8FAFC', fontSize: 10, fontWeight: 700, color: '#64748B', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            <span>{t('methodsSandbox.fColSignal')}</span><span>mean</span><span>cv · {t('methodsSandbox.fColInfo')}</span><span>{t('methodsSandbox.colVerdict')}</span><span>{t('methodsSandbox.fColBasisNote')}</span>
          </div>
          {SIGNALS.map((s, i) => (
            <div key={i} style={{ display: 'grid', gridTemplateColumns: '190px 64px 96px 116px 1fr', gap: 8, padding: '9px 14px', borderTop: '1px solid #F1F5F9', fontSize: 12, alignItems: 'center' }}>
              <span style={{ color: '#1A2332' }}>
                <span style={{ color: '#94A3B8', fontSize: 9.5, fontWeight: 700, textTransform: 'uppercase' }}>{s.grp}</span><br />
                <b>{s.name}</b>
              </span>
              <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 11.5 }}>{s.mean == null ? '—' : s.mean.toFixed(3)}</span>
              <span>
                {s.cv == null ? <span style={{ color: '#CBD5E1' }}>—</span> : (
                  <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                    <span style={{ width: 40, height: 6, background: '#F1F5F9', borderRadius: 3, overflow: 'hidden' }}>
                      <span style={{ display: 'block', width: `${Math.min(100, s.cv * 50)}%`, height: '100%', background: s.cv < 0.3 ? '#C0392B' : s.cv < 0.6 ? '#B9770E' : '#1E8449' }} />
                    </span>
                    <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 11 }}>{s.cv.toFixed(2)}</span>
                  </span>
                )}
              </span>
              <span><span style={{ fontSize: 9, fontWeight: 800, letterSpacing: '0.04em', color: '#fff', background: VERDICT_COLOR[s.verdict], borderRadius: 3, padding: '2px 6px', whiteSpace: 'nowrap' }}>{s.verdict}</span></span>
              <span style={{ color: '#475569', fontSize: 11.5, lineHeight: 1.4 }}><b>{t(s.basisKey)}.</b> {t(s.noteKey)}</span>
            </div>
          ))}
        </div>
        <p style={{ fontSize: 12, color: '#718096', marginTop: 10, lineHeight: 1.5 }}
           dangerouslySetInnerHTML={{ __html: t('methodsSandbox.fExplain') }} />
        <JudgementCard
          t={t}
          formula={"defensible(signal)  ⟺  honest( what · why/literature · math-faithful · carries-signal · impl = claim )\nverdict drawn from LIVE activation on the sealed run — not asserted"}
          source={t('methodsSandbox.fJcSource')}
          basis={t('methodsSandbox.fJcBasis')}
          verdict="SEMI-GROUNDED"
          why={t('methodsSandbox.fJcWhy')}
          improve={t('methodsSandbox.fJcImprove')}
        />
      </section>

      {/* ════ SECTION G — rerun gate checklist ════ */}
      <section style={{ marginBottom: 44 }}>
        <H t={t} n="G" titleKey="methodsSandbox.gTitle" subKey="methodsSandbox.gSub" />
        <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10, overflow: 'hidden' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1.1fr 1.4fr 1fr 0.7fr 0.6fr', gap: 8, padding: '9px 14px',
                        background: '#F8FAFC', fontSize: 10, fontWeight: 700, color: '#64748B', textTransform: 'uppercase' }}>
            <span>{t('methodsSandbox.gColClaim')}</span><span>{t('methodsSandbox.gColScript')}</span><span>{t('methodsSandbox.gColData')}</span><span>{t('methodsSandbox.gColStatus')}</span><span>{t('methodsSandbox.gColSeal')}</span>
          </div>
          {([
            { claim: t('methodsSandbox.gClaimAdcSeal'), script: 'run_sealing.py', data: 'magnitudes run-94a3b8ba (inherited) → overlay run-d2154070 · N=96,727', status: '🟢', seal: 'seal-bae44d1a' },
            { claim: t('methodsSandbox.gClaimJt5d'), script: '_justification_activation.sql', data: t('methodsSandbox.gDataSameRun'), status: '🟢', seal: t('methodsSandbox.gSealSame') },
            { claim: t('methodsSandbox.gClaimTopology'), script: 'probe_prospective_transfer_v3.py --full', data: 'junyi · 1.98M first-enc', status: '🟢', seal: t('methodsSandbox.gSealFullN') },
            { claim: t('methodsSandbox.gClaimSuperseded'), script: t('methodsSandbox.gScriptLost'), data: '—', status: '🔴', seal: t('methodsSandbox.gSealDoNotCite') },
            { claim: t('methodsSandbox.gClaimBaselines'), script: 'evaluate_all_baselines_auc.py', data: 'run-d2154070 · N=96,727', status: '🟢', seal: 'seal-bae44d1a' },
            { claim: t('methodsSandbox.gClaimR12'), script: 'run_r12_ablation.py', data: t('methodsSandbox.gDataConfounded'), status: '🔴', seal: t('methodsSandbox.gSealWithdrawn') },
            { claim: t('methodsSandbox.gClaimCascade'), script: '_cascade_status.py', data: t('methodsSandbox.gDataCascade'), status: '🟢', seal: t('methodsSandbox.gSealComplete') },
            { claim: t('methodsSandbox.gClaimReplay'), script: 'smoke_replay_determinism.py', data: t('methodsSandbox.gDataSeedContingent'), status: '🟢', seal: t('methodsSandbox.gSealDisclosed') },
            { claim: t('methodsSandbox.gClaimPathC'), script: 'ENSEMBLE_REDESIGN_SPEC.md', data: '—', status: '🔴', seal: t('methodsSandbox.gSealStandDown') },
          ] as const).map((row, i) => (
            <div key={i} style={{ display: 'grid', gridTemplateColumns: '1.1fr 1.4fr 1fr 0.7fr 0.6fr', gap: 8,
                                  padding: '9px 14px', borderTop: '1px solid #F1F5F9', fontSize: 12, alignItems: 'center' }}>
              <span style={{ fontWeight: 600, color: '#1A2332' }}>{row.claim}</span>
              <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 11, color: '#475569' }}>{row.script}</span>
              <span style={{ fontSize: 11, color: '#64748B' }}>{row.data}</span>
              <span>{row.status}</span>
              <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 10, color: '#64748B' }}>{row.seal}</span>
            </div>
          ))}
        </div>
        <p style={{ fontSize: 12, color: '#718096', marginTop: 10, lineHeight: 1.5 }}
           dangerouslySetInnerHTML={{ __html: t('methodsSandbox.gFootnote') }} />
      </section>

      {/* ════ SECTION H — causal topology decomposition (the +0.053 finding) ════ */}
      <section style={{ marginBottom: 44 }}>
        <H t={t} n="H" titleKey="methodsSandbox.hTitle" subKey="methodsSandbox.hSub" />
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 24 }}>
          <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10, padding: 18 }}>
            <Slider label={`${t('methodsSandbox.hPastCoef')} (b_durable_CROSS_past)`} value={pastCoef} min={0} max={0.16} step={0.001}
              onChange={setPastCoef} fmt={v => v.toFixed(3)} color="#16A085" />
            <Slider label={t('methodsSandbox.hPlaceboCoef')} value={placeboCoef} min={0} max={0.16} step={0.001}
              onChange={setPlaceboCoef} fmt={v => v.toFixed(3)} color="#C0392B" />
            <button onClick={() => { setPastCoef(0.091); setPlaceboCoef(0.038) }}
              style={{ marginTop: 6, fontSize: 12, fontFamily: 'ui-monospace, monospace', color: '#1A5276',
                       background: '#EBF5FB', border: '1px solid #AED6F1', borderRadius: 6, padding: '6px 12px', cursor: 'pointer' }}>
              {t('methodsSandbox.hResetSealed')}
            </button>
            <div style={{ marginTop: 16 }}>
              <div style={{ fontSize: 11, color: '#718096', textTransform: 'uppercase', letterSpacing: '0.04em' }}>{t('methodsSandbox.hLiftLabel')}</div>
              <div style={{ fontSize: 40, fontWeight: 800, color: '#16A085', fontFamily: 'ui-monospace, monospace', lineHeight: 1.1 }}>
                {causalLift >= 0 ? '+' : ''}{causalLift.toFixed(3)}
              </div>
              <div style={{ fontSize: 12, color: '#718096' }}>{t('methodsSandbox.hPlaceboRemoves')} ≈ {(selectionPct * 100).toFixed(0)}% {t('methodsSandbox.hAsSelection')}{atSealed ? ' (' + t('methodsSandbox.tagSealed') + ')' : ''}</div>
            </div>
          </div>
          <div>
            <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10, padding: 18 }}>
              <div style={{ fontSize: 12, color: '#718096', marginBottom: 8 }}>{t('methodsSandbox.hRawSplit')}</div>
              <div style={{ display: 'flex', height: 30, borderRadius: 6, overflow: 'hidden', border: '1px solid #E2E8F0' }}>
                <div style={{ width: `${(causalLift / Math.max(pastCoef, 1e-6)) * 100}%`, background: '#16A085', minWidth: causalLift > 0 ? 2 : 0 }} title={t('methodsSandbox.hDurableCausal')} />
                <div style={{ width: `${selectionPct * 100}%`, background: '#E2A6A6' }} title={t('methodsSandbox.hStateSelection')} />
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, marginTop: 6 }}>
                <span style={{ color: '#16A085', fontWeight: 700 }}>■ {t('methodsSandbox.hDurableCausal')} {causalLift.toFixed(3)}</span>
                <span style={{ color: '#C0392B', fontWeight: 700 }}>■ {t('methodsSandbox.hSelection')} {placeboCoef.toFixed(3)}</span>
              </div>
              <div style={{ fontSize: 12, color: '#718096', margin: '16px 0 6px' }}>{t('methodsSandbox.hPositionNull')}</div>
              <svg viewBox="0 0 320 72" style={{ width: '100%', height: 78 }}>
                {(() => {
                  const x0 = -0.06, x1 = 0.10, sx = (v: number) => 20 + ((v - x0) / (x1 - x0)) * 280
                  const nm = H_NULL_MEAN, ns = H_NULL_SD
                  const bell = Array.from({ length: 60 }, (_, k) => { const v = x0 + (k / 59) * (x1 - x0); const y = Math.exp(-0.5 * ((v - nm) / ns) ** 2); return `${k === 0 ? 'M' : 'L'} ${sx(v).toFixed(1)} ${(55 - y * 40).toFixed(1)}` }).join(' ')
                  const cx = sx(Math.max(x0, Math.min(x1, causalLift)))
                  return (<>
                    <line x1="20" y1="55" x2="300" y2="55" stroke="#CBD5E0" />
                    <path d={bell} fill="#EDF2F7" stroke="#A0AEC0" strokeWidth="1" />
                    <line x1={sx(0)} y1="14" x2={sx(0)} y2="55" stroke="#CBD5E0" strokeDasharray="2 2" />
                    <text x={sx(0)} y="68" fontSize="8" fill="#A0AEC0" textAnchor="middle" fontFamily="monospace">0</text>
                    <line x1={cx} y1="10" x2={cx} y2="55" stroke="#16A085" strokeWidth="2" />
                    <circle cx={cx} cy="10" r="4" fill="#16A085" />
                    <text x={cx} y="68" fontSize="8" fill="#16A085" textAnchor="middle" fontFamily="monospace">{causalLift.toFixed(3)}</text>
                  </>)
                })()}
              </svg>
              <div style={{ fontSize: 12, fontFamily: 'ui-monospace, monospace', color: '#1A2332', marginTop: 4 }}>
                {hZ.toFixed(1)} {t('methodsSandbox.hNullSds')} ({H_NULL_MEAN}) · {t('methodsSandbox.hSealedPerm')} <b>p = 0.0099</b>
              </div>
            </div>
            <p style={{ fontSize: 12, color: '#718096', marginTop: 10, lineHeight: 1.5 }}
               dangerouslySetInnerHTML={{ __html: t('methodsSandbox.hExplain').replace('{{prox}}', H_PROXIMITY.toFixed(2)) }} />
          </div>
        </div>
        <JudgementCard
          t={t}
          formula={"durable causal = b_durable_CROSS_past − b_FUTURE_cross_PLACEBO\n             = 0.09147 − 0.03812 = +0.05335   (full corpus: N=1,976,020 / 232,440 learners)\npermutation null: mean −0.011, sd 0.023, K=100 → cross_perm_p = 0.0099"}
          source={t('methodsSandbox.hJcSource')}
          basis={t('methodsSandbox.hJcBasis')}
          verdict="GROUNDED"
          why={t('methodsSandbox.hJcWhy')}
          improve={t('methodsSandbox.hJcImprove')}
        />
      </section>

      {/* ════ SECTION I — decision-aware acceptance / cascade completion ════ */}
      <section style={{ marginBottom: 44 }}>
        <H t={t} n="I" titleKey="methodsSandbox.iTitle" subKey="methodsSandbox.iSub" />
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 24 }}>
          <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10, padding: 18 }}>
            <div style={{ fontSize: 11, color: '#718096', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: 8 }}>{t('methodsSandbox.iLockedDecisions')}</div>
            <Toggle t={t} label={t('methodsSandbox.iTogBundleA')} refTag="bundle_a_defer=DEFER" on={dec.bundle_a_defer} onChange={v => setDec(s => ({ ...s, bundle_a_defer: v }))}
              sub={t('methodsSandbox.iTogBundleASub')} />
            <Toggle t={t} label={t('methodsSandbox.iTogV2')} refTag="v2_integration_mode=audit_only" on={dec.audit_only} onChange={v => setDec(s => ({ ...s, audit_only: v }))}
              sub={t('methodsSandbox.iTogV2Sub')} />
            <Toggle t={t} label={t('methodsSandbox.iTogEnsemble')} refTag="ensemble_fusion=DISCLOSE_CANONICAL_KALMAN" on={dec.ensemble_fusion} onChange={v => setDec(s => ({ ...s, ensemble_fusion: v }))}
              sub={t('methodsSandbox.iTogEnsembleSub')} />
            <Toggle t={t} label={t('methodsSandbox.iTogBounded')} refTag="learner_bounded_stability=DISCLOSE" on={dec.bounded_stability} onChange={v => setDec(s => ({ ...s, bounded_stability: v }))}
              sub={t('methodsSandbox.iTogBoundedSub')} />
            <button onClick={() => setDec({ bundle_a_defer: true, audit_only: true, ensemble_fusion: true, bounded_stability: true })}
              style={{ marginTop: 4, fontSize: 12, fontFamily: 'ui-monospace, monospace', color: '#1A5276',
                       background: '#EBF5FB', border: '1px solid #AED6F1', borderRadius: 6, padding: '6px 12px', cursor: 'pointer' }}>
              {t('methodsSandbox.iReLockAll')}
            </button>
          </div>
          <div>
            <div style={{ background: allLocked ? '#F0FAF4' : '#FFF8E1', border: `1px solid ${allLocked ? '#B7E0D7' : '#FFE082'}`,
                          borderRadius: 10, padding: '14px 16px', marginBottom: 14 }}>
              <div style={{ fontSize: 13, fontWeight: 800, color: allLocked ? '#1B5E55' : '#7E5109' }}>
                {allLocked
                  ? `✓ ${t('methodsSandbox.iAcceptComplete')}`
                  : `⚠ ${accOpen} ${accOpen === 1 ? t('methodsSandbox.iCriterion') : t('methodsSandbox.iCriteria')} ${t('methodsSandbox.iReopened')} — ${accTerminal}/9 ${t('methodsSandbox.iTerminal')}`}
              </div>
              <div style={{ fontSize: 12, color: '#5A6776', marginTop: 4, lineHeight: 1.5 }}>
                {allLocked
                  ? t('methodsSandbox.iCompleteBody')
                  : `${t('methodsSandbox.iReopenedBodyA')} ${accOpen} ${t('methodsSandbox.iReopenedBodyB')}`}
              </div>
            </div>
            <div style={{ background: '#fff', border: '1px solid #E2E8F0', borderRadius: 10, overflow: 'hidden' }}>
              {accCriteria.map((c, i) => (
                <div key={c.id} style={{ display: 'grid', gridTemplateColumns: '38px 1fr 104px', gap: 8, padding: '8px 12px',
                                         borderTop: i ? '1px solid #F1F5F9' : 'none', alignItems: 'center',
                                         background: TERMINAL_V.has(c.verdict) ? '#fff' : '#FFFBEB' }}>
                  <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 12, fontWeight: 700, color: '#64748B' }}>{c.id}</span>
                  <span>
                    <span style={{ fontSize: 12.5, color: '#1A2332' }}>{c.title}</span>
                    <span style={{ display: 'block', fontSize: 10.5, color: '#94A3B8', fontFamily: 'ui-monospace, monospace' }}>{c.ref} · {c.raw}</span>
                  </span>
                  <span style={{ justifySelf: 'end' }}>
                    <span style={{ fontSize: 9.5, fontWeight: 800, color: '#fff', background: ACC_COLOR[c.verdict],
                                   borderRadius: 4, padding: '3px 8px', whiteSpace: 'nowrap' }}>{c.verdict}</span>
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
        <JudgementCard
          t={t}
          formula={"step is COMPLETE  ⟺  every criterion ∈ {PASS, DISCLOSED, DEFERRED}\nDISCLOSED / DEFERRED  ⟸  a user-locked decision in jt_design_decisions.json (raw finding kept + cited)"}
          source={t('methodsSandbox.iJcSource')}
          basis={t('methodsSandbox.iJcBasis')}
          verdict="GROUNDED"
          why={t('methodsSandbox.iJcWhy')}
          improve={t('methodsSandbox.iJcImprove')}
        />
      </section>

      <div style={{ fontSize: 12, color: '#94A3B8', borderTop: '1px solid #E2E8F0', paddingTop: 14 }}
           dangerouslySetInnerHTML={{ __html: t('methodsSandbox.pageFooter') }} />

      <NextSteps />
    </div>
  )
}
