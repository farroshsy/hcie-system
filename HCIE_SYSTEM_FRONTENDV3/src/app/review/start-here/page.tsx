'use client'

/**
 * /review/start-here — the friendly "for reviewers" landing.
 *
 * One pane of glass for a NON-technical reviewer (a child, a 70-year-old examiner): a plain-language
 * question, a guided path, an HONEST interactive result, and the calibration win.
 *
 * Numbers = the canonical m_K (Kalman-alone) readout on the CITED anchor (seal-bae44d1a / run-d2154070).
 * "Whole course" bars = the cited matched-eval headline (HCIE 0.605, leads all trained baselines).
 * "Cold-start" view = the per-window HCIE-BKT margin with 95% CIs from the n=76 robust matched eval
 * (research_validation/reports/tier1_evidence.json) — HONEST: HCIE's edge is overall, NOT a robust
 * cold-start win. Static data only (no fetch) so a repo-only reviewer sees the same; the live endpoints
 * still serve the deployed-fusion / pre-tie-aware numbers (backend refresh pending), which is why this
 * page is pinned to the canonical values.
 */

import Link from 'next/link'
import { useState } from 'react'
import { Panel, Callout, Eyebrow, Tag } from '@/lib/ui/primitives'
import { t as ui } from '@/lib/ui/theme'  // aliased: `t` is taken by useT() (translations)
import { useT } from '@/contexts/language_context'
import PageGuide, { TourStep } from '@/components/help/PageGuide'

// Causal evidence (within-learner transfer, shuffled-DAG control). benchmark_kalman_canonical honesty + audit.
// Numbers only — no display text, so this stays at module level.
const CAUSAL = { durable: 0.053, p: 0.0099, shuffled: 0.0, n: '1.98M' }

// scale 0.50 (coin flip) → 0.80 onto 0–100% for the score bars
const bar = (auc: number) => Math.max(2, Math.min(100, ((auc - 0.5) / 0.3) * 100))
// map a margin in [-0.08, +0.08] onto [-100%, +100%] of a half-width for the diverging bar
const half = (m: number) => Math.max(-100, Math.min(100, (m / 0.08) * 100))

const STEPS: TourStep[] = [
  {
    selector: '[data-tour="hero-title"]',
    title: { en: 'Start here', id: 'Mulai di sini' },
    body: {
      en: 'This is the plain-language overview of what the system does. Read it first to get the big picture before exploring.',
      id: 'Ini ikhtisar dengan bahasa sederhana tentang apa yang dilakukan sistem. Baca dulu untuk gambaran besar sebelum menjelajah.',
    },
  },
  {
    selector: '[data-tour="guided-paths"]',
    title: { en: 'Where to go next', id: 'Ke mana selanjutnya' },
    body: {
      en: 'Each card is a guided path into the evidence. Click any card to open that page.',
      id: 'Setiap kartu adalah jalur terpandu menuju bukti. Klik kartu mana pun untuk membuka halamannya.',
    },
  },
  {
    selector: '[data-tour="result-views"]',
    title: { en: 'Switch the view', id: 'Ganti tampilan' },
    body: {
      en: 'These two buttons toggle the result between the whole-course score and the cold-start (early-question) view. Click to compare them.',
      id: 'Dua tombol ini mengganti hasil antara skor seluruh kursus dan tampilan cold-start (soal-soal awal). Klik untuk membandingkan.',
    },
  },
  {
    selector: '[data-tour="score-panel"]',
    title: { en: 'The headline result', id: 'Hasil utama' },
    body: {
      en: 'Each bar is a model’s accuracy (AUC); higher is better. The top row is HCIE, which leads here without any training.',
      id: 'Setiap batang adalah akurasi model (AUC); makin tinggi makin baik. Baris teratas adalah HCIE, yang unggul di sini tanpa training.',
    },
  },
  {
    selector: '[data-tour="calibration"]',
    title: { en: 'The calibration win', id: 'Keunggulan kalibrasi' },
    body: {
      en: 'This panel shows the miscalibration dropping from 0.062 to 0.014 — lower means the confidence scores can be trusted more.',
      id: 'Panel ini menunjukkan miscalibration turun dari 0,062 ke 0,014 — makin rendah berarti skor confidence makin bisa dipercaya.',
    },
  },
]

export default function StartHere() {
  const t = useT()
  const [view, setView] = useState<'scores' | 'coldstart'>('scores')

  // Whole-course matched eval, canonical m_K, CITED anchor d2154070 (lagged_kalman_auc_anchor.json).
  const OVERALL = [
    { id: 'hcie', label: t('startHere.modelHcieNoTraining'), auc: 0.605 },
    { id: 'bkt',  label: t('startHere.modelBktTrained'),     auc: 0.596 },
    { id: 'dkt',  label: t('startHere.modelDktTrained'),     auc: 0.589 },
    { id: 'sakt', label: t('startHere.modelSaktTrained'),    auc: 0.573 },
    { id: 'gkt',  label: t('startHere.modelGktTrained'),     auc: 0.571 },
  ] as const

  // Per-window HCIE-BKT margin + 95% bootstrap CI, n=76 robust matched eval (tier1_evidence.json).
  // Honest: only the whole course is significant; cold-start is competitive, not a robust win.
  const COLDSTART = [
    { win: t('startHere.winFirst5'),  margin: 0.037,  lo: -0.002, hi: 0.075, verdict: t('startHere.verdictFirst5'),  tone: 'info' as const },
    { win: t('startHere.winFirst10'), margin: -0.017, lo: -0.070, hi: 0.032, verdict: t('startHere.verdictFirst10'), tone: 'warn' as const },
    { win: t('startHere.winFirst20'), margin: -0.031, lo: -0.077, hi: 0.011, verdict: t('startHere.verdictFirst20'), tone: 'warn' as const },
    { win: t('startHere.winWholeCourse'), margin: 0.013, lo: 0.002, hi: 0.023, verdict: t('startHere.verdictWholeCourse'), tone: 'ok' as const },
  ]

  // No-history sub-population (Junyi anchor, first-encounter per user×concept, n=4,379, m_K).
  // Simpson: warmed-BKT collapses to chance on a brand-new topic; HCIE still informs with zero
  // training; the pre-trained deep models still edge it on the very first no-history items.
  const SIMPSON = [
    { id: 'hcie', label: t('startHere.modelHcieNoTraining'),  auc: 0.580 },
    { id: 'bkt',  label: t('startHere.modelBktWarmed'),       auc: 0.500 },
    { id: 'dkt',  label: t('startHere.modelDktPretrained'),   auc: 0.688 },
    { id: 'sakt', label: t('startHere.modelSaktPretrained'),  auc: 0.687 },
    { id: 'gkt',  label: t('startHere.modelGktPretrained'),   auc: 0.489 },
  ] as const

  // Cross-dataset breadth, canonical m_K overall (cross_dataset_mK_unified.json).
  const DATASETS = [
    { name: 'Junyi', mk: 0.741, note: 'leads', noteLabel: t('startHere.noteLeads') },
    { name: 'ASSISTments', mk: 0.630, note: 'leads', noteLabel: t('startHere.noteLeads') },
    { name: 'CSEDM', mk: 0.672, note: 'competitive', noteLabel: t('startHere.noteCompetitive') },
    { name: 'EdNet', mk: 0.575, note: 'fusion helps here (disclosed)', noteLabel: t('startHere.noteFusionHelps') },
  ]

  const PATHS = [
    { href: '/review/run-it-yourself', icon: '◉', title: t('startHere.pathRunLoopTitle'),    body: t('startHere.pathRunLoopBody') },
    { href: '/review/system-journey',  icon: '⬡', title: t('startHere.pathLearnerResearcherTitle'), body: t('startHere.pathLearnerResearcherBody') },
    { href: '/review/cross-dataset',   icon: '⊞', title: t('startHere.pathScrubDatasetsTitle'), body: t('startHere.pathScrubDatasetsBody') },
    { href: '/learn',                  icon: '▶', title: t('startHere.pathRealTutorTitle'),   body: t('startHere.pathRealTutorBody') },
    { href: '/review/story',           icon: '✦', title: t('startHere.pathStoryTitle'),       body: t('startHere.pathStoryBody') },
    { href: '/dashboard/reproducibility', icon: '?', title: t('startHere.pathWordsMeanTitle'), body: t('startHere.pathWordsMeanBody') },
    { href: '/dashboard/benchmarks',   icon: '▦', title: t('startHere.pathDeepProofTitle'),   body: t('startHere.pathDeepProofBody') },
  ]

  return (
    <div style={{ padding: '40px 48px', maxWidth: 900 }}>
      {/* Hero */}
      <Eyebrow color={ui.tone.info.fg}>{t('startHere.heroEyebrow')}</Eyebrow>
      <h1 data-tour="hero-title" style={{ fontSize: ui.font.size.h1, fontWeight: ui.font.weight.heavy, color: ui.color.ink, lineHeight: 1.25, marginBottom: ui.space.md }}>
        {t('startHere.heroTitle')}
      </h1>
      <p style={{ fontSize: ui.font.size.lg, color: ui.color.body, lineHeight: 1.65, maxWidth: 740, marginBottom: ui.space.xxl }}>
        {t('startHere.heroLead1')} <strong>{t('startHere.heroLeadNoTraining')}</strong> {t('startHere.heroLead2')} <strong>{t('startHere.heroLeadKalmanAlone')}</strong> {t('startHere.heroLead3')}
      </p>

      {/* Guided path */}
      <div data-tour="guided-paths" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: ui.space.md, marginBottom: ui.space.xxl }}>
        {PATHS.map(p => (
          <Link key={p.href} href={p.href} style={{ textDecoration: 'none' }}>
            <div style={{ background: ui.color.surface, border: `1px solid ${ui.color.line}`, borderRadius: ui.radius.lg, padding: ui.space.lg, height: '100%', cursor: 'pointer', transition: 'border-color .15s, box-shadow .15s' }}
              onMouseEnter={e => { (e.currentTarget as HTMLDivElement).style.borderColor = ui.tone.info.border; (e.currentTarget as HTMLDivElement).style.boxShadow = '0 4px 16px rgba(0,0,0,0.07)' }}
              onMouseLeave={e => { (e.currentTarget as HTMLDivElement).style.borderColor = ui.color.line; (e.currentTarget as HTMLDivElement).style.boxShadow = 'none' }}>
              <div style={{ fontSize: 22, color: ui.tone.info.fg, marginBottom: ui.space.xs }} aria-hidden>{p.icon}</div>
              <div style={{ fontSize: ui.font.size.lg, fontWeight: ui.font.weight.bold, color: ui.color.ink, marginBottom: 2 }}>{p.title}</div>
              <div style={{ fontSize: ui.font.size.md, color: ui.color.body, lineHeight: 1.5 }}>{p.body}</div>
            </div>
          </Link>
        ))}
      </div>

      {/* Interactive result */}
      <Eyebrow color={ui.tone.accent.fg}>{t('startHere.resultEyebrow')}</Eyebrow>
      <h2 style={{ fontSize: ui.font.size.h2, fontWeight: ui.font.weight.heavy, color: ui.color.ink, marginBottom: ui.space.xs }}>{t('startHere.resultTitle')}</h2>
      <p style={{ fontSize: ui.font.size.md, color: ui.color.body, lineHeight: 1.6, marginBottom: ui.space.lg }}>
        {t('startHere.resultLead1')} <strong>{t('startHere.resultLeadNoTraining')}</strong> {t('startHere.resultLead2')}
      </p>

      {/* two honest views */}
      <div data-tour="result-views" style={{ display: 'flex', gap: ui.space.sm, flexWrap: 'wrap', marginBottom: ui.space.lg }}>
        {([['scores', t('startHere.viewWholeCourse')], ['coldstart', t('startHere.viewWinAtStart')]] as const).map(([k, lbl]) => {
          const on = view === k
          return (
            <button key={k} onClick={() => setView(k as 'scores' | 'coldstart')} style={{
              fontSize: ui.font.size.md, padding: '6px 14px', borderRadius: ui.radius.md, cursor: 'pointer',
              border: `1px solid ${on ? ui.tone.info.border : ui.color.line}`,
              background: on ? ui.tone.info.bg : ui.color.surface, color: on ? ui.tone.info.fg : ui.color.muted,
              fontWeight: on ? ui.font.weight.bold : ui.font.weight.medium,
            }}>{lbl}</button>
          )
        })}
      </div>

      {view === 'scores' ? (
        <>
          <Panel pad="xl" data-tour="score-panel" style={{ marginBottom: ui.space.md }}>
            {OVERALL.map(m => {
              const isH = m.id === 'hcie'
              return (
                <div key={m.id} style={{ display: 'flex', alignItems: 'center', gap: ui.space.md, marginBottom: ui.space.sm }}>
                  <div style={{ width: 150, fontSize: ui.font.size.md, color: isH ? ui.color.ink : ui.color.muted, fontWeight: isH ? ui.font.weight.bold : ui.font.weight.medium }}>{m.label}</div>
                  <div style={{ flex: 1, background: ui.color.grid, borderRadius: ui.radius.sm, height: isH ? 22 : 16 }}>
                    <div style={{ width: `${bar(m.auc)}%`, height: '100%', borderRadius: ui.radius.sm, background: ui.modelColor[m.id], transition: 'width .35s' }} />
                  </div>
                  <div style={{ width: 48, textAlign: 'right', fontSize: ui.font.size.md, fontWeight: isH ? ui.font.weight.heavy : ui.font.weight.medium, color: isH ? ui.modelColor.hcie : ui.color.body }}>{m.auc.toFixed(3)}</div>
                </div>
              )
            })}
          </Panel>
          <Callout tone="ok" style={{ marginBottom: ui.space.xs }} title={t('startHere.scoresCalloutTitle')}>
            {t('startHere.scoresCalloutBody')}
          </Callout>
        </>
      ) : (
        <>
          <Panel pad="xl" style={{ marginBottom: ui.space.md }}>
            <div style={{ fontSize: ui.font.size.sm, color: ui.color.muted, marginBottom: ui.space.md }}>
              {t('startHere.coldstartIntro')}
            </div>
            {COLDSTART.map(c => {
              const pos = c.margin >= 0
              const col = pos ? ui.tone.ok.fg : ui.tone.bad.fg
              const sig = c.lo > 0
              return (
                <div key={c.win} style={{ display: 'flex', alignItems: 'center', gap: ui.space.md, marginBottom: ui.space.md }}>
                  <div style={{ width: 150, fontSize: ui.font.size.md, color: ui.color.ink }}>{c.win}</div>
                  {/* diverging axis */}
                  <div style={{ flex: 1, position: 'relative', height: 22, background: ui.color.grid, borderRadius: ui.radius.sm }}>
                    <div style={{ position: 'absolute', left: '50%', top: 0, bottom: 0, width: 1, background: ui.color.muted }} />
                    {/* CI line */}
                    <div style={{ position: 'absolute', top: '50%', height: 2, background: ui.color.muted,
                      left: `${50 + Math.min(half(c.lo), half(c.hi)) / 2}%`,
                      width: `${Math.abs(half(c.hi) - half(c.lo)) / 2}%`, transform: 'translateY(-50%)' }} />
                    {/* margin bar from center */}
                    <div style={{ position: 'absolute', top: 4, bottom: 4, borderRadius: 2, background: col,
                      left: pos ? '50%' : `${50 + half(c.margin) / 2}%`, width: `${Math.abs(half(c.margin)) / 2}%` }} />
                  </div>
                  <div style={{ width: 120, textAlign: 'right', fontSize: ui.font.size.sm }}>
                    <span style={{ fontWeight: ui.font.weight.bold, color: col }}>{pos ? '+' : ''}{c.margin.toFixed(3)}</span>
                    <Tag tone={sig ? 'ok' : 'neutral'}>{sig ? t('startHere.tagSignificant') : t('startHere.tagTie')}</Tag>
                  </div>
                </div>
              )
            })}
          </Panel>
          <Callout tone="info" style={{ marginBottom: ui.space.xs }} title={t('startHere.coldstartCalloutTitle')}>
            {t('startHere.coldstartCalloutBody1')} <strong>{t('startHere.coldstartCalloutWholeCourse')}</strong> {t('startHere.coldstartCalloutBody2')}
            <strong> {t('startHere.coldstartCalloutCompetitive')}</strong>{t('startHere.coldstartCalloutBody3')}
            {t('startHere.coldstartCalloutBody4')} <strong>{t('startHere.coldstartCalloutNoTraining')}</strong> {t('startHere.coldstartCalloutBody5')}
          </Callout>
          <div style={{ marginTop: ui.space.lg }}>
            <Eyebrow color={ui.tone.accent.fg}>{t('startHere.simpsonEyebrow')}</Eyebrow>
            <p style={{ fontSize: ui.font.size.sm, color: ui.color.body, lineHeight: 1.55, marginBottom: ui.space.sm }}>
              {t('startHere.simpsonIntro1')} <strong>{t('startHere.simpsonIntroBktCollapses')}</strong> {t('startHere.simpsonIntro2')} <strong>{t('startHere.simpsonIntroZeroTraining')}</strong>{t('startHere.simpsonIntro3')}
            </p>
            <Panel pad="lg">
              {SIMPSON.map(m => {
                const isH = m.id === 'hcie'
                return (
                  <div key={m.id} style={{ display: 'flex', alignItems: 'center', gap: ui.space.md, marginBottom: ui.space.xs }}>
                    <div style={{ width: 160, fontSize: ui.font.size.sm, color: isH ? ui.color.ink : ui.color.muted, fontWeight: isH ? ui.font.weight.bold : ui.font.weight.medium }}>{m.label}</div>
                    <div style={{ flex: 1, background: ui.color.grid, borderRadius: ui.radius.sm, height: isH ? 18 : 14 }}>
                      <div style={{ width: `${bar(m.auc)}%`, height: '100%', borderRadius: ui.radius.sm, background: ui.modelColor[m.id], transition: 'width .35s' }} />
                    </div>
                    <div style={{ width: 44, textAlign: 'right', fontSize: ui.font.size.sm, fontWeight: isH ? ui.font.weight.heavy : ui.font.weight.medium, color: isH ? ui.modelColor.hcie : ui.color.body }}>{m.auc.toFixed(3)}</div>
                  </div>
                )
              })}
            </Panel>
          </div>
        </>
      )}
      <p style={{ fontSize: ui.font.size.sm, color: ui.color.faint, marginTop: ui.space.sm, marginBottom: ui.space.xxl }}>
        {t('startHere.provenanceNote')}
      </p>

      {/* Breadth + calibration */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: ui.space.lg, marginBottom: ui.space.xxl }}>
        <div>
          <Eyebrow>{t('startHere.datasetsEyebrow')}</Eyebrow>
          {DATASETS.map(ds => (
            <div key={ds.name} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 0', borderBottom: `1px solid ${ui.color.line}` }}>
              <span style={{ fontSize: ui.font.size.md, color: ui.color.ink }}>{ds.name}</span>
              <span style={{ display: 'flex', alignItems: 'center', gap: ui.space.sm }}>
                <span style={{ fontSize: ui.font.size.md, fontWeight: ui.font.weight.bold, color: ui.modelColor.hcie }}>{ds.mk.toFixed(3)}</span>
                <Tag tone={ds.note === 'leads' ? 'ok' : ds.note === 'competitive' ? 'info' : 'warn'}>{ds.noteLabel}</Tag>
              </span>
            </div>
          ))}
        </div>
        <Panel tone="ok" pad="lg" data-tour="calibration">
          <Eyebrow color={ui.tone.ok.fg}>{t('startHere.calibrationEyebrow')}</Eyebrow>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: ui.space.sm, fontSize: ui.font.size.lg, marginBottom: ui.space.xs }}>
            <span style={{ color: ui.color.muted }}>{t('startHere.calibrationMiscalibration')}</span>
            <span style={{ color: ui.tone.bad.fg, fontWeight: ui.font.weight.bold }}>0.062</span>
            <span style={{ color: ui.color.faint }}>→</span>
            <span style={{ color: ui.tone.ok.fg, fontWeight: ui.font.weight.heavy }}>0.014</span>
          </div>
          <p style={{ fontSize: ui.font.size.sm, color: ui.color.body, lineHeight: 1.55 }}>
            {t('startHere.calibrationBody')}
          </p>
        </Panel>
      </div>

      {/* Causal evidence — why it works (measured) */}
      <Panel tone="info" pad="lg" style={{ marginBottom: ui.space.xxl }}>
        <Eyebrow color={ui.tone.info.fg}>{t('startHere.causalEyebrow')}</Eyebrow>
        <div style={{ display: 'flex', gap: ui.space.xl, flexWrap: 'wrap', alignItems: 'baseline', marginTop: ui.space.xs, marginBottom: ui.space.xs }}>
          <div><span style={{ fontSize: ui.font.size.h2, fontWeight: ui.font.weight.heavy, color: ui.tone.ok.fg }}>+{CAUSAL.durable.toFixed(3)}</span> <span style={{ fontSize: ui.font.size.sm, color: ui.color.muted }}>{t('startHere.causalDurableLabel')}</span></div>
          <div><span style={{ fontSize: ui.font.size.lg, fontWeight: ui.font.weight.bold, color: ui.color.ink }}>p = {CAUSAL.p}</span> <span style={{ fontSize: ui.font.size.sm, color: ui.color.muted }}>{t('startHere.causalPermutationLabel')} (N≈{CAUSAL.n})</span></div>
          <div><span style={{ fontSize: ui.font.size.lg, fontWeight: ui.font.weight.bold, color: ui.color.ink }}>≈{CAUSAL.shuffled.toFixed(2)}</span> <span style={{ fontSize: ui.font.size.sm, color: ui.color.muted }}>{t('startHere.causalShuffledLabel')}</span></div>
        </div>
        <p style={{ fontSize: ui.font.size.sm, color: ui.color.body, lineHeight: 1.55 }}>
          {t('startHere.causalBody')}
        </p>
      </Panel>

      {/* Provenance */}
      <Callout tone="neutral" title={t('startHere.sealedCalloutTitle')}>
        {t('startHere.sealedCalloutBody1')} <strong>seal-bae44d1a</strong>{t('startHere.sealedCalloutBody2')} <strong>seal-e7b56a2c</strong>{t('startHere.sealedCalloutBody3')}
      </Callout>

      <PageGuide tourId="start-here" steps={STEPS} />
    </div>
  )
}
