'use client'

/**
 * Reproducibility — the event-sourced argument (Bab 4 §4.1.2.c).
 *
 * Static narrative surface: HCIE guarantees reproducibility at the EVENT/ARTIFACT level
 * (sealed event log + content-hash), not by re-executing evolving code. The measured
 * re-execution divergence is shown as the *motivation* for the event-sourced paradigm,
 * not as a defect. Evidence is fixed against the sealed anchor (seal-bae44d1a).
 */

import React, { useState } from 'react'
import Link from 'next/link'
import { Panel, Tag, Callout, SectionTitle, Eyebrow, Stat } from '@/lib/ui/primitives'
import { t as ui } from '@/lib/ui/theme'
import { useT } from '@/contexts/language_context'

const ANCHOR = {
  seal: 'seal-bae44d1a-a314-48f5-b145-c92e6cbe08d7',
  run: 'run-d2154070-b6e4-4abe-94e6-a2e6ccfbefc1',
  content_hash: '85690d8be722e1e6271abb2f860290dd',
  git_sha: '035b37ca374cf8723b80e217a8c4cad5acb2be3b',
  rows: 96727,
  git_dirty: false,
}

// Display text lives in the dictionary (resolved via t() inside the component);
// only stable keys + tone live at module level.
const PARADIGMS = [
  { key: 'reexec', tone: 'bad' as const },
  { key: 'eventSourced', tone: 'ok' as const },
]

const EVIDENCE = [
  { key: 'inputsHash', value: '100.0%', tone: 'ok' as const },
  { key: 'canonicalKalman', value: 'max|Δ| = 0.0', tone: 'ok' as const },
  { key: 'bitIdentical', value: 'md5 match', tone: 'ok' as const },
  { key: 'sealedContentHash', value: '85690d8b…', tone: 'info' as const },
  { key: 'codeProvenance', value: 'git_dirty = false', tone: 'ok' as const },
  { key: 'rowsSealed', value: '96,727', tone: 'neutral' as const },
]

const DIVERGENCE = [
  { key: 'mastery', field: 'mastery', value: '0.74' },
  { key: 'kalman', field: 'Kalman', value: '0.48' },
  { key: 'jt', field: 'JT', value: '0.054' },
]

export default function ReproducibilityPage() {
  const t = useT()
  const [auc, setAuc] = useState(74)
  const av = auc / 100
  const aucBand =
    av < 0.55 ? t('reproducibilityPage.aucBandCoinFlip')
    : av < 0.65 ? t('reproducibilityPage.aucBandWeak')
    : av < 0.75 ? t('reproducibilityPage.aucBandDecent')
    : av < 0.85 ? t('reproducibilityPage.aucBandGood')
    : t('reproducibilityPage.aucBandStrong')
  const aucColor = av < 0.55 ? ui.tone.bad.fg : av < 0.65 ? ui.tone.warn.fg : ui.tone.ok.fg
  return (
    <div style={{ maxWidth: 1080, margin: '0 auto', padding: `${ui.space.xl}px ${ui.space.lg}px 64px` }}>
      <Eyebrow>Bab 4 · §4.1.2.c</Eyebrow>
      <SectionTitle sub={t('reproducibilityPage.heroSub')}>
        {t('reproducibilityPage.heroTitle')}
      </SectionTitle>

      {/* Friendly ELI5 concepts (for non-technical reviewers) — added 2026-06-25 */}
      <Panel tone="neutral" style={{ marginTop: ui.space.lg }}>
        <Eyebrow color={ui.tone.accent.fg}>{t('reproducibilityPage.plainLanguageEyebrow')}</Eyebrow>
        <div style={{ fontSize: ui.font.size.lg, fontWeight: ui.font.weight.bold, color: ui.color.ink, marginBottom: ui.space.xs }}>{t('reproducibilityPage.scoreMeaningTitle')}</div>
        <p style={{ fontSize: ui.font.size.md, color: ui.color.body, lineHeight: 1.6, marginBottom: ui.space.md }}>
          {t('reproducibilityPage.scoreMeaningBodyA')} (<strong>AUC</strong>) {t('reproducibilityPage.scoreMeaningBodyB')}
        </p>
        <div style={{ display: 'flex', alignItems: 'center', gap: ui.space.md, marginBottom: ui.space.sm }}>
          <span style={{ fontSize: ui.font.size.sm, color: ui.color.muted }}>0.50</span>
          <input type="range" min={50} max={100} value={auc} onChange={(e) => setAuc(+e.target.value)} style={{ flex: 1 }} aria-label={t('reproducibilityPage.aucSliderAria')} />
          <span style={{ fontSize: ui.font.size.sm, color: ui.color.muted }}>1.00</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: ui.space.md, flexWrap: 'wrap' }}>
          <span style={{ fontSize: ui.font.size.h2, fontWeight: ui.font.weight.heavy, color: aucColor }}>{av.toFixed(2)}</span>
          <span style={{ fontSize: ui.font.size.md, color: ui.color.body }}>{t('reproducibilityPage.betsOnRight')} <strong>{auc} {t('reproducibilityPage.outOf100')}</strong> — {aucBand}</span>
        </div>
        <div style={{ display: 'flex', gap: ui.space.lg, fontSize: ui.font.size.xs, color: ui.color.faint, marginTop: ui.space.xs }}>
          <span>{t('reproducibilityPage.scaleCoinFlip')}</span><span>{t('reproducibilityPage.scaleHcieHeadline')}</span><span>{t('reproducibilityPage.scalePerfect')}</span>
        </div>
        <div style={{ borderTop: `1px solid ${ui.color.line}`, marginTop: ui.space.lg, paddingTop: ui.space.md }}>
          <div style={{ fontSize: ui.font.size.lg, fontWeight: ui.font.weight.bold, color: ui.color.ink, marginBottom: ui.space.sm }}>{t('reproducibilityPage.sealedReproTitle')}</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: ui.space.sm, flexWrap: 'wrap', fontSize: ui.font.size.md }}>
            <span style={{ background: ui.tone.info.bg, color: ui.tone.info.fg, padding: '4px 10px', borderRadius: ui.radius.md }}>{t('reproducibilityPage.flowExactResults')}</span>
            <span style={{ color: ui.color.faint }}>→</span>
            <span style={{ background: ui.tone.accent.bg, color: ui.tone.accent.fg, padding: '4px 10px', borderRadius: ui.radius.md, fontFamily: 'monospace', fontSize: ui.font.size.sm }}>{t('reproducibilityPage.flowFingerprint')} 85690d8b…</span>
            <span style={{ color: ui.color.faint }}>→</span>
            <span style={{ background: ui.tone.ok.bg, color: ui.tone.ok.fg, padding: '4px 10px', borderRadius: ui.radius.md }}>{t('reproducibilityPage.flowRunAgain')} ✓</span>
          </div>
          <p style={{ fontSize: ui.font.size.sm, color: ui.color.muted, marginTop: ui.space.sm, lineHeight: 1.55 }}>
            <strong>{t('reproducibilityPage.sealedTerm')}</strong> {t('reproducibilityPage.sealedDef')} <strong>{t('reproducibilityPage.reproducibleTerm')}</strong> {t('reproducibilityPage.reproducibleDef')}
          </p>
        </div>
      </Panel>

      <Panel tone="info" style={{ marginTop: ui.space.lg }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: ui.space.sm }}>
          <Stat label="seal" value={ANCHOR.seal.slice(0, 13) + '…'} tone="info" />
          <Stat label="run" value={ANCHOR.run.slice(0, 14) + '…'} />
          <Stat label="content_hash" value={ANCHOR.content_hash.slice(0, 12) + '…'} />
          <Stat label="rows" value={'96,727'} />
          <Stat label="git_dirty" value="false" tone="ok" />
        </div>
      </Panel>

      {/* Two paradigms */}
      <section style={{ marginTop: ui.space.xxl }}>
        <h2 style={{ fontSize: ui.font.size.h2, fontWeight: ui.font.weight.heavy, color: ui.color.heading, marginBottom: ui.space.md, borderBottom: `2px solid ${ui.color.line}`, paddingBottom: ui.space.xs }}>
          {t('reproducibilityPage.twoNotionsTitle')}
        </h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: ui.space.lg }}>
          {PARADIGMS.map((p) => (
            <Panel key={p.key} tone={p.tone}>
              <div style={{ display: 'flex', alignItems: 'center', gap: ui.space.sm, marginBottom: ui.space.sm }}>
                <span style={{ fontSize: ui.font.size.lg, fontWeight: ui.font.weight.heavy, color: ui.color.ink }}>{t(`reproducibilityPage.paradigm_${p.key}_name`)}</span>
                <Tag tone={p.tone}>{p.tone === 'ok' ? t('reproducibilityPage.tagHolds') : t('reproducibilityPage.tagFails')}</Tag>
              </div>
              <p style={{ margin: 0, fontSize: ui.font.size.md, color: ui.color.body, lineHeight: 1.5 }}><strong>{t('reproducibilityPage.claimLabel')}</strong> {t(`reproducibilityPage.paradigm_${p.key}_claim`)}</p>
              <p style={{ margin: `${ui.space.xs}px 0 0`, fontSize: ui.font.size.sm, color: ui.color.muted, lineHeight: 1.5 }}><strong>{t('reproducibilityPage.failureModeLabel')}</strong> {t(`reproducibilityPage.paradigm_${p.key}_failure`)}</p>
              <p style={{ margin: `${ui.space.xs}px 0 0`, fontSize: ui.font.size.sm, color: p.tone === 'ok' ? ui.tone.ok.fg : ui.tone.bad.fg, lineHeight: 1.5, fontWeight: ui.font.weight.medium }}>{t(`reproducibilityPage.paradigm_${p.key}_hcie`)}</p>
            </Panel>
          ))}
        </div>
      </section>

      {/* Evidence */}
      <section style={{ marginTop: ui.space.xxl }}>
        <h2 style={{ fontSize: ui.font.size.h2, fontWeight: ui.font.weight.heavy, color: ui.color.heading, marginBottom: ui.space.md, borderBottom: `2px solid ${ui.color.line}`, paddingBottom: ui.space.xs }}>
          {t('reproducibilityPage.guaranteeEvidenceTitle')}
        </h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: ui.space.md }}>
          {EVIDENCE.map((e) => (
            <Panel key={e.key} tone={e.tone} pad="md">
              <div style={{ fontSize: ui.font.size.xl, fontWeight: ui.font.weight.heavy, color: ui.tone[e.tone].fg }}>{e.value}</div>
              <div style={{ fontSize: ui.font.size.sm, fontWeight: ui.font.weight.bold, color: ui.color.heading, marginTop: 2 }}>{t(`reproducibilityPage.evidence_${e.key}_label`)}</div>
              <div style={{ fontSize: ui.font.size.xs, color: ui.color.muted, marginTop: 2 }}>{t(`reproducibilityPage.evidence_${e.key}_sub`)}</div>
            </Panel>
          ))}
        </div>
        <div style={{ marginTop: ui.space.md, display: 'flex', gap: ui.space.md, flexWrap: 'wrap' }}>
          <Link href="/dashboard/replay-verify" style={{ fontSize: ui.font.size.sm, color: ui.tone.info.fg, fontWeight: ui.font.weight.bold, textDecoration: 'none' }}>{t('reproducibilityPage.linkReplayIntegrity')}</Link>
          <Link href="/dashboard/thesis-evidence" style={{ fontSize: ui.font.size.sm, color: ui.tone.info.fg, fontWeight: ui.font.weight.bold, textDecoration: 'none' }}>{t('reproducibilityPage.linkThesisEvidence')}</Link>
          <Link href="/dashboard/method-grounding" style={{ fontSize: ui.font.size.sm, color: ui.tone.info.fg, fontWeight: ui.font.weight.bold, textDecoration: 'none' }}>{t('reproducibilityPage.linkMethodGrounding')}</Link>
        </div>
      </section>

      {/* Divergence as evidence */}
      <section style={{ marginTop: ui.space.xxl }}>
        <h2 style={{ fontSize: ui.font.size.h2, fontWeight: ui.font.weight.heavy, color: ui.color.heading, marginBottom: ui.space.md, borderBottom: `2px solid ${ui.color.line}`, paddingBottom: ui.space.xs }}>
          {t('reproducibilityPage.whyEventSourcedTitle')}
        </h2>
        <Callout tone="warn" title={t('reproducibilityPage.divergenceCalloutTitle')}>
          {t('reproducibilityPage.divergenceCalloutBodyA')}
          <strong> {t('reproducibilityPage.divergenceCalloutCurrent')}</strong> {t('reproducibilityPage.divergenceCalloutBodyB')} <strong>{t('reproducibilityPage.divergenceCalloutNot')}</strong> {t('reproducibilityPage.divergenceCalloutBodyC')}
        </Callout>
        <div style={{ marginTop: ui.space.md, display: 'flex', gap: ui.space.md, flexWrap: 'wrap' }}>
          {DIVERGENCE.map((d) => (
            <Stat key={d.key} label={`${t('reproducibilityPage.maxDeltaLabel')} ${d.field}`} value={d.value} tone="warn" />
          ))}
        </div>
        <p style={{ marginTop: ui.space.md, fontSize: ui.font.size.md, color: ui.color.body, lineHeight: 1.6 }}>
          {t('reproducibilityPage.divergenceParaA')} <strong>{t('reproducibilityPage.divergenceParaSeals')}</strong> {t('reproducibilityPage.divergenceParaB')}<em>{t('reproducibilityPage.divergenceParaSeal')}</em>{t('reproducibilityPage.divergenceParaC')}
        </p>
      </section>

      <Callout tone="neutral" style={{ marginTop: ui.space.xxl }} title={t('reproducibilityPage.honestScopeTitle')}>
        {t('reproducibilityPage.honestScopeBodyA')} <strong>{t('reproducibilityPage.honestScopeInProcessBrain')}</strong> {t('reproducibilityPage.honestScopeBodyB')}
        <strong> {t('reproducibilityPage.honestScopeEventSourced')}</strong>{t('reproducibilityPage.honestScopeBodyC')}
      </Callout>
    </div>
  )
}
