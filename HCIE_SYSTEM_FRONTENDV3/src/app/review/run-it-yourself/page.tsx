'use client'

/**
 * /review/run-it-yourself — the interactive "run the loop yourself" walkthrough.
 *
 * The reviewer scrubs/steps through ONE real sealed learner's frozen cold-start sequence and watches
 * the AUDITABLE CLOSED LOOP update each step — observe -> Kalman+Bayesian state -> JT/ADC governance ->
 * Thompson decision. Each stage is clickable for the "why" (context + which RQ it answers). Ends in the
 * 8-axis capability map (thesis Tabel 4.15 — the actual contribution) + provenance. Static data only
 * (src/data/run_it_yourself.json), so it works for a repo-only reviewer and is reproducible.
 */

import Link from 'next/link'
import { useState } from 'react'
import data from '@/data/run_it_yourself.json'
import { useT } from '@/contexts/language_context'
import { Panel, Callout, Eyebrow, Tag } from '@/lib/ui/primitives'
import { t as ui } from '@/lib/ui/theme'  // aliased: `t` is taken by useT() (translations)
import PageGuide, { TourStep } from '@/components/help/PageGuide'

type Step = (typeof data.steps)[number]
const STEPS = data.steps as Step[]
const num = (v: unknown, d = 0) => (typeof v === 'number' ? v : d)
const pct = (v: number, lo = 0, hi = 1) => Math.max(2, Math.min(100, ((v - lo) / (hi - lo)) * 100))

const cell = (v: string) =>
  v === '✓' || v === 'Full' ? ui.tone.ok.fg : v === '✗' || v === 'Weakest' ? ui.tone.bad.fg
  : v === 'Limited' || v === 'Strong*' ? ui.tone.warn.fg : ui.color.body

const STEPS_TOUR: TourStep[] = [
  {
    selector: '[data-tour="scrubber"]',
    title: { en: 'Step through the loop', id: 'Telusuri loop' },
    body: {
      en: 'Drag this slider or use the arrows to move through one real learner\'s interactions, one at a time. Every panel below updates to that exact step.',
      id: 'Geser slider ini atau pakai panah untuk berpindah antar interaksi satu learner nyata, satu per satu. Semua panel di bawah ikut berubah mengikuti step itu.',
    },
  },
  {
    selector: '[data-tour="stage-observe"]',
    title: { en: 'Stage 1: what happened', id: 'Tahap 1: apa yang terjadi' },
    body: {
      en: 'This is the raw input for the current step: whether the learner answered correctly or wrong. Click any stage card to read why it matters.',
      id: 'Ini input mentah untuk step saat ini: apakah learner menjawab benar atau salah. Klik kartu tahap mana pun untuk membaca kenapa itu penting.',
    },
  },
  {
    selector: '[data-tour="stage-estimate"]',
    title: { en: 'Stage 2: estimate skill', id: 'Tahap 2: estimasi skill' },
    body: {
      en: 'Two estimators react to the answer: a Kalman mastery bar and a Bayesian estimate. Watch both bars shift as you step forward.',
      id: 'Dua estimator merespons jawaban: bar Kalman mastery dan estimasi Bayesian. Perhatikan kedua bar bergeser saat Anda maju satu step.',
    },
  },
  {
    selector: '[data-tour="stage-govern"]',
    title: { en: 'Stage 4: governance', id: 'Tahap 4: governance' },
    body: {
      en: 'The JT/ADC governance layer decides how much knowledge transfers across concepts. A lightning bolt marks steps with real transfer.',
      id: 'Lapisan governance JT/ADC menentukan seberapa banyak pengetahuan transfer antar konsep. Ikon petir menandai step dengan transfer nyata.',
    },
  },
  {
    selector: '[data-tour="mastery-curve"]',
    title: { en: 'The mastery journey', id: 'Perjalanan mastery' },
    body: {
      en: 'This curve shows mastery growing across all steps. Click anywhere on it to jump straight to that interaction.',
      id: 'Kurva ini menunjukkan mastery tumbuh sepanjang semua step. Klik di mana saja pada kurva untuk lompat langsung ke interaksi itu.',
    },
  },
  {
    selector: '[data-tour="capability-map"]',
    title: { en: 'The 8-axis result', id: 'Hasil 8-aksis' },
    body: {
      en: 'The real contribution: HCIE versus other models across 8 capabilities, not just AUC. Each cell shows whether a model has that capability.',
      id: 'Kontribusi sebenarnya: HCIE dibanding model lain pada 8 kapabilitas, bukan cuma AUC. Tiap sel menunjukkan apakah sebuah model punya kapabilitas itu.',
    },
  },
]

export default function RunItYourself() {
  const t = useT()
  const [i, setI] = useState(0)
  const [open, setOpen] = useState<string | null>('observe')
  const s = STEPS[i]
  const bayesMean = num(s.bayesian_alpha_after) / Math.max(1e-6, num(s.bayesian_alpha_after) + num(s.bayesian_beta_after))
  const correct = (s as { correctness?: boolean }).correctness
  const transfer = num(s.transfer_amount)
  const window = s.interaction_number <= 5 ? t('runItYourself.windowColdStart') : s.interaction_number <= 10 ? t('runItYourself.windowEarly') : t('runItYourself.windowWarming')

  // The five stages of the auditable closed loop. why = the context tying to a research question.
  // Kept inside the component so the display text can resolve through t().
  const STAGES = [
    { id: 'observe', n: '1', icon: '◉', title: t('runItYourself.stageObserveTitle'), rq: 'RM1',
      why: t('runItYourself.stageObserveWhy') },
    { id: 'estimate', n: '2', icon: '⚖', title: t('runItYourself.stageEstimateTitle'), rq: 'RM1',
      why: t('runItYourself.stageEstimateWhy') },
    { id: 'state', n: '3', icon: '◈', title: t('runItYourself.stageStateTitle'), rq: 'RM1',
      why: t('runItYourself.stageStateWhy') },
    { id: 'govern', n: '4', icon: '⬡', title: t('runItYourself.stageGovernTitle'), rq: 'RM3 · RM4',
      why: t('runItYourself.stageGovernWhy') },
    { id: 'decide', n: '5', icon: '▷', title: t('runItYourself.stageDecideTitle'), rq: 'RM2',
      why: t('runItYourself.stageDecideWhy') },
  ] as const

  // Thesis Tabel 4.15 — the 8-axis capability map (the ACTUAL contribution; AUC is only the last row).
  const AXES = [
    { axis: t('runItYourself.axisColdStart'), hcie: '✓', bkt: '✓', dkt: '✗', sakt: '✗', gkt: '✗' },
    { axis: t('runItYourself.axisEmbeddingFree'), hcie: 'Full', bkt: 'Limited', dkt: '✗', sakt: '✗', gkt: '✗' },
    { axis: t('runItYourself.axisUpdateCost'), hcie: 'O(1)', bkt: 'O(1)', dkt: 'O(d²)', sakt: 'O(M²d)', gkt: 'O(L·|E|·d)' },
    { axis: t('runItYourself.axisGovernance'), hcie: '✓', bkt: '✗', dkt: '✗', sakt: '✗', gkt: '✗' },
    { axis: t('runItYourself.axisTraceability'), hcie: '✓', bkt: '✗', dkt: '✗', sakt: '✗', gkt: '✗' },
    { axis: t('runItYourself.axisAdcTransparency'), hcie: '✓', bkt: '✗', dkt: '✗', sakt: '✗', gkt: '✗' },
    { axis: t('runItYourself.axisSealed'), hcie: '✓', bkt: '✗', dkt: '✗', sakt: '✗', gkt: '✗' },
    { axis: t('runItYourself.axisRepresentation'), hcie: '✓', bkt: '✗', dkt: '✗', sakt: '✗', gkt: '✗' },
    { axis: t('runItYourself.axisPredictiveAuc'), hcie: t('runItYourself.cellCompetitive'), bkt: t('runItYourself.cellCompetitive'), dkt: 'Strong*', sakt: 'Strong*', gkt: 'Weakest' },
  ] as const

  // "Verify each claim yourself" deep-link cards.
  const VERIFY = [
    { href: '/dashboard/benchmarks', t: t('runItYourself.cardNumbersTitle'), b: t('runItYourself.cardNumbersBody') },
    { href: '/dashboard/audit', t: t('runItYourself.cardTopologyTitle'), b: t('runItYourself.cardTopologyBody') },
    { href: '/dashboard/governance', t: t('runItYourself.cardGovernanceTitle'), b: t('runItYourself.cardGovernanceBody') },
    { href: '/dashboard/reproducibility', t: t('runItYourself.cardReproTitle'), b: t('runItYourself.cardReproBody') },
    { href: '/learn', t: t('runItYourself.cardTutorTitle'), b: t('runItYourself.cardTutorBody') },
  ]

  return (
    <div style={{ padding: '40px 48px', maxWidth: 960 }}>
      <Eyebrow color={ui.tone.info.fg}>{t('runItYourself.eyebrow')}</Eyebrow>
      <h1 style={{ fontSize: ui.font.size.h1, fontWeight: ui.font.weight.heavy, color: ui.color.ink, lineHeight: 1.25, marginBottom: ui.space.md }}>
        {t('runItYourself.heroTitle')}
      </h1>
      <p style={{ fontSize: ui.font.size.lg, color: ui.color.body, lineHeight: 1.6, maxWidth: 760, marginBottom: ui.space.lg }}>
        {t('runItYourself.introA')} <strong>{t('runItYourself.introOneLearner')}</strong>{t('runItYourself.introB')} <strong>{t('runItYourself.introLoop')}</strong>.
        {' '}{t('runItYourself.introC')}
      </p>

      {/* Step scrubber */}
      <Panel data-tour="scrubber" pad="lg" style={{ marginBottom: ui.space.lg }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: ui.space.md, marginBottom: ui.space.sm, flexWrap: 'wrap' }}>
          <button onClick={() => setI(Math.max(0, i - 1))} disabled={i === 0} aria-label={t('runItYourself.ariaPrev')}
            style={{ fontSize: ui.font.size.lg, padding: '4px 12px', borderRadius: ui.radius.md, cursor: i === 0 ? 'default' : 'pointer', border: `1px solid ${ui.color.line}`, background: ui.color.surface, color: ui.color.ink, opacity: i === 0 ? 0.4 : 1 }}>◀</button>
          <input type="range" min={0} max={STEPS.length - 1} value={i} onChange={e => setI(Number(e.target.value))} aria-label={t('runItYourself.ariaSlider')} style={{ flex: 1, accentColor: ui.modelColor.hcie, cursor: 'pointer' }} />
          <button onClick={() => setI(Math.min(STEPS.length - 1, i + 1))} disabled={i === STEPS.length - 1} aria-label={t('runItYourself.ariaNext')}
            style={{ fontSize: ui.font.size.lg, padding: '4px 12px', borderRadius: ui.radius.md, cursor: 'pointer', border: `1px solid ${ui.color.line}`, background: ui.color.surface, color: ui.color.ink, opacity: i === STEPS.length - 1 ? 0.4 : 1 }}>▶</button>
        </div>
        <div style={{ display: 'flex', gap: ui.space.md, alignItems: 'center', fontSize: ui.font.size.md, color: ui.color.body, flexWrap: 'wrap' }}>
          <span style={{ fontWeight: ui.font.weight.bold, color: ui.color.ink }}>{t('runItYourself.interaction')} {s.interaction_number} / {STEPS.length}</span>
          <Tag tone={window === t('runItYourself.windowColdStart') ? 'info' : window === t('runItYourself.windowEarly') ? 'warn' : 'neutral'}>{window}</Tag>
          <span style={{ color: ui.color.muted }}>{t('runItYourself.concept')}: <code style={{ color: ui.color.ink }}>{s.concept}</code></span>
        </div>
      </Panel>

      {/* The closed loop — 5 clickable stages */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: ui.space.xs, marginBottom: ui.space.sm }}>
        {STAGES.map((st, idx) => {
          const on = open === st.id
          return (
            <div key={st.id} data-tour={`stage-${st.id}`} onClick={() => setOpen(on ? null : st.id)} style={{
              position: 'relative', background: on ? ui.tone.info.bg : ui.color.surface,
              border: `1px solid ${on ? ui.tone.info.border : ui.color.line}`, borderRadius: ui.radius.md,
              padding: ui.space.sm, cursor: 'pointer', transition: 'all .15s', minHeight: 124,
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginBottom: 4 }}>
                <span style={{ fontSize: ui.font.size.sm, fontWeight: ui.font.weight.heavy, color: ui.tone.info.fg }}>{st.n}</span>
                <span style={{ fontSize: 15, color: ui.tone.info.fg }} aria-hidden>{st.icon}</span>
              </div>
              <div style={{ fontSize: ui.font.size.sm, fontWeight: ui.font.weight.bold, color: ui.color.ink, lineHeight: 1.2, marginBottom: 6 }}>{st.title}</div>
              {/* live per-stage value */}
              {st.id === 'observe' && (
                <div style={{ fontSize: ui.font.size.h2, fontWeight: ui.font.weight.heavy, color: correct ? ui.tone.ok.fg : ui.tone.bad.fg }}>{correct ? t('runItYourself.correct') : t('runItYourself.wrong')}</div>
              )}
              {st.id === 'estimate' && (<>
                <div style={{ fontSize: ui.font.size.xs, color: ui.color.muted }}>{t('runItYourself.kalmanM')}</div>
                <Bar v={num(s.kalman_mastery_after)} c={ui.modelColor.hcie} />
                <div style={{ fontSize: ui.font.size.xs, color: ui.color.muted, marginTop: 2 }}>{t('runItYourself.bayesian')} {bayesMean.toFixed(2)}</div>
                <Bar v={bayesMean} c={ui.modelColor.bkt} />
              </>)}
              {st.id === 'state' && (<>
                <div style={{ fontSize: ui.font.size.lg, fontWeight: ui.font.weight.heavy, color: ui.modelColor.hcie }}>{num(s.canonical_mastery_after).toFixed(3)}</div>
                <div style={{ fontSize: ui.font.size.xs, color: ui.color.muted }}>±{num(s.uncertainty_after).toFixed(3)} {t('runItYourself.uncAbbrev')}</div>
              </>)}
              {st.id === 'govern' && (<>
                <div style={{ fontSize: ui.font.size.xs, color: ui.color.muted }}>{t('runItYourself.transfer')}</div>
                <div style={{ fontSize: ui.font.size.md, fontWeight: ui.font.weight.bold, color: transfer > 0.01 ? ui.tone.ok.fg : ui.color.body }}>{transfer.toFixed(4)}{transfer > 0.01 ? ' ⚡' : ''}</div>
                <div style={{ fontSize: ui.font.size.xs, color: ui.color.muted, marginTop: 2 }}>ZPD {num(s.zpd_score).toFixed(2)} · JT {num(s.jt_value).toFixed(2)}</div>
              </>)}
              {st.id === 'decide' && (<>
                <div style={{ fontSize: ui.font.size.sm, fontWeight: ui.font.weight.bold, color: ui.color.ink }}>{String((s as { arm_selected?: string }).arm_selected ?? '—')}</div>
                <div style={{ fontSize: ui.font.size.xs, color: ui.color.muted }}>{String((s as { policy?: string }).policy ?? '')}</div>
              </>)}
              {idx < STAGES.length - 1 && <span style={{ position: 'absolute', right: -9, top: '46%', color: ui.color.muted, fontSize: 14, zIndex: 1 }} aria-hidden>→</span>}
            </div>
          )
        })}
      </div>
      {open && (() => { const st = STAGES.find(x => x.id === open)!; return (
        <Callout tone="info" title={`${st.n}. ${st.title} — ${t('runItYourself.whyItMatters')} (${st.rq})`} style={{ marginBottom: ui.space.lg }}>{st.why}</Callout>
      ) })()}

      {/* Mastery over time — the journey */}
      <Eyebrow color={ui.tone.accent.fg}>{t('runItYourself.masteryEyebrow')}</Eyebrow>
      <Panel data-tour="mastery-curve" pad="lg" style={{ marginBottom: ui.space.xl }}>
        <Spark steps={STEPS} cur={i} onPick={setI} />
        <div style={{ fontSize: ui.font.size.sm, color: ui.color.faint, marginTop: ui.space.xs }}>
          {t('runItYourself.masteryCaption')}
        </div>
      </Panel>

      {/* The result — 8-axis capability map (thesis Tabel 4.15) */}
      <Eyebrow color={ui.tone.accent.fg}>{t('runItYourself.contributionEyebrow')}</Eyebrow>
      <p style={{ fontSize: ui.font.size.md, color: ui.color.body, lineHeight: 1.6, marginBottom: ui.space.sm, maxWidth: 760 }}>
        {t('runItYourself.contributionLeadA')} <strong>{t('runItYourself.contributionCompetitive')}</strong>{t('runItYourself.contributionLeadB')}
        <strong> {t('runItYourself.contributionStructuralAxes')}</strong> {t('runItYourself.contributionLeadC')}
      </p>
      <Panel data-tour="capability-map" pad="md" style={{ marginBottom: ui.space.sm, overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: ui.font.size.sm }}>
          <thead><tr style={{ color: ui.color.muted, textAlign: 'left' }}>
            {[t('runItYourself.colCapability'), 'HCIE', 'BKT', 'DKT', 'SAKT', 'GKT'].map(h => <th key={h} style={{ padding: '4px 8px', borderBottom: `1px solid ${ui.color.line}`, color: h === 'HCIE' ? ui.modelColor.hcie : ui.color.muted, fontWeight: h === 'HCIE' ? ui.font.weight.bold : ui.font.weight.medium }}>{h}</th>)}
          </tr></thead>
          <tbody>{AXES.map((a, k) => (
            <tr key={a.axis} style={{ background: k % 2 ? ui.color.subtle : 'transparent' }}>
              <td style={{ padding: '4px 8px', color: ui.color.ink }}>{a.axis}</td>
              {(['hcie', 'bkt', 'dkt', 'sakt', 'gkt'] as const).map(m => (
                <td key={m} style={{ padding: '4px 8px', fontWeight: m === 'hcie' ? ui.font.weight.bold : ui.font.weight.medium, color: cell(a[m]) }}>{a[m]}</td>
              ))}
            </tr>
          ))}</tbody>
        </table>
      </Panel>
      <p style={{ fontSize: ui.font.size.xs, color: ui.color.faint, marginBottom: ui.space.xl }}>{t('runItYourself.tableFootnote')}</p>

      {/* Dig deeper */}
      <Eyebrow>{t('runItYourself.verifyEyebrow')}</Eyebrow>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: ui.space.sm, marginBottom: ui.space.xl }}>
        {VERIFY.map(c => (
          <Link key={c.href} href={c.href} style={{ textDecoration: 'none' }}>
            <div style={{ background: ui.color.surface, border: `1px solid ${ui.color.line}`, borderRadius: ui.radius.md, padding: ui.space.md, height: '100%', cursor: 'pointer' }}
              onMouseEnter={e => { (e.currentTarget as HTMLDivElement).style.borderColor = ui.tone.info.border }}
              onMouseLeave={e => { (e.currentTarget as HTMLDivElement).style.borderColor = ui.color.line }}>
              <div style={{ fontSize: ui.font.size.md, fontWeight: ui.font.weight.bold, color: ui.color.ink }}>{c.t}</div>
              <div style={{ fontSize: ui.font.size.sm, color: ui.color.body, marginTop: 2, lineHeight: 1.4 }}>{c.b}</div>
            </div>
          </Link>
        ))}
      </div>

      <Callout tone="neutral" title={t('runItYourself.reproducibleTitle')}>
        {data.meta.learner} · {data.meta.run} · content-hash {data.meta.content_hash}. {data.meta.n} {t('runItYourself.reproducibleBody')}
      </Callout>

      <PageGuide tourId="run-it-yourself" steps={STEPS_TOUR} />
    </div>
  )
}

function Bar({ v, c }: { v: number; c: string }) {
  return (
    <div style={{ background: ui.color.grid, borderRadius: 3, height: 8, marginTop: 2 }}>
      <div style={{ width: `${pct(v)}%`, height: '100%', borderRadius: 3, background: c, transition: 'width .25s' }} />
    </div>
  )
}

function Spark({ steps, cur, onPick }: { steps: Step[]; cur: number; onPick: (i: number) => void }) {
  const W = 880, H = 90, pad = 6
  const xs = (k: number) => pad + (k / Math.max(1, steps.length - 1)) * (W - 2 * pad)
  const ys = (v: number) => H - pad - v * (H - 2 * pad)
  const pts = steps.map((s, k) => `${xs(k)},${ys(num(s.canonical_mastery_after))}`).join(' ')
  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', height: 'auto', cursor: 'pointer' }}
      onClick={e => {
        const r = (e.currentTarget as SVGSVGElement).getBoundingClientRect()
        const x = ((e.clientX - r.left) / r.width) * W
        onPick(Math.round(((x - pad) / (W - 2 * pad)) * (steps.length - 1)))
      }}>
      <line x1={pad} y1={ys(0.5)} x2={W - pad} y2={ys(0.5)} stroke={ui.color.line} strokeDasharray="3 3" />
      <polyline points={pts} fill="none" stroke={ui.modelColor.hcie} strokeWidth={2} />
      <circle cx={xs(cur)} cy={ys(num(steps[cur].canonical_mastery_after))} r={5} fill={ui.modelColor.hcie} />
    </svg>
  )
}
