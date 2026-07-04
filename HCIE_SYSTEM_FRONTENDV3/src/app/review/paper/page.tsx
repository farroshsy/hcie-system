'use client'

import ProvenanceBadge from '@/components/review/ProvenanceBadge'
import { NextSteps } from '@/components/review/NextSteps'
import { useT } from '@/contexts/language_context'
import { Panel, Callout, Eyebrow } from '@/lib/ui/primitives'
import { t as ui } from '@/lib/ui/theme'  // aliased: `t` is taken by useT() (translations)

export default function PaperPage() {
  const t = useT()

  const ARTIFACTS = [
    {
      file: '/data/adc/topology_taxonomy.json',
      label: 'topology_taxonomy.json',
      desc: t('paperReview.artifactTopologyTaxonomyDesc'),
      icon: '◈',
      color: '#1565C0',
      size: '~5 KB',
    },
    {
      file: '/data/adc/r12_ablation.json',
      label: 'r12_ablation.json',
      desc: t('paperReview.artifactR12AblationDesc'),
      icon: '⊿',
      color: '#C0392B',
      size: '~2 KB',
    },
    {
      file: '/data/adc/governance_trace.json',
      label: 'governance_trace.json',
      desc: t('paperReview.artifactGovernanceTraceDesc'),
      icon: '◉',
      color: '#6A1E55',
      size: '~80 KB',
    },
    {
      file: '/data/adc/baseline_comparison.json',
      label: 'baseline_comparison.json',
      desc: t('paperReview.artifactBaselineComparisonDesc'),
      icon: '≋',
      color: '#1E8449',
      size: '~3 KB',
    },
    {
      file: '/data/adc/canonical_figure.png',
      label: 'canonical_figure.png',
      desc: t('paperReview.artifactCanonicalFigureDesc'),
      icon: '⬡',
      color: '#D35400',
      size: '~120 KB',
      isImage: true,
    },
  ]

  const RUN_IDS = [
    { label: t('paperReview.runPhase1Label'), id: 'run-217532ca-39e6-4859-a41f-88ed53e904a2', color: '#718096' },
    { label: t('paperReview.runPhase2Label'), id: 'run-94a3b8ba-015b-4d84-b288-004fe60bc282', color: '#1E8449' },
    { label: t('paperReview.runR12Label'), id: 'run-aecd9059-aac1-4800-b738-d508eef79608', color: '#C0392B' },
  ]

  return (
    <div style={{ padding: '32px 40px', maxWidth: 860 }}>
      <div style={{ marginBottom: ui.space.xxl }}>
        <Eyebrow color={ui.color.body}>{t('nav.reviewPaper')} · ADC Release v1 · 2026-05-26</Eyebrow>
        <h1 style={{ fontSize: ui.font.size.h2, fontWeight: ui.font.weight.heavy, color: ui.color.ink, marginBottom: ui.space.sm }}>
          {t('nav.reviewPaper')}
        </h1>
        <p style={{ fontSize: ui.font.size.md, color: ui.color.body, lineHeight: 1.6, maxWidth: 680 }}>
          {t('paperReview.introLead')}
        </p>
      </div>

      <ProvenanceBadge
        source="frozen"
        generatedAt="2026-05-26T00:00:00+00:00"
        note={t('paperReview.provenanceNote')}
      />

      {/* Sealed thresholds */}
      <Callout tone="warn" style={{ marginBottom: ui.space.xxl, lineHeight: 1.8 }}>
        <div style={{ fontWeight: ui.font.weight.bold, color: ui.tone.warn.fg, marginBottom: ui.space.xs }}>{t('paperReview.sealedThresholdsTitle')}</div>
        <code style={{ fontFamily: 'monospace', color: ui.tone.warn.fg }}>
          alpha_floor = 0.01 &nbsp;·&nbsp; signal_ratio_threshold = 0.08
        </code>
        <div style={{ marginTop: ui.space.xs, color: '#B7770D', fontSize: ui.font.size.sm }}>
          {t('paperReview.sealedThresholdsNote')}
        </div>
      </Callout>

      {/* Artifacts */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: ui.space.md, marginBottom: ui.space.xxl }}>
        {ARTIFACTS.map(a => (
          <Panel key={a.file} pad="md" style={{ display: 'flex', alignItems: 'flex-start', gap: ui.space.lg }}>
            <span style={{ fontSize: ui.font.size.h2, color: a.color, marginTop: 2 }}>{a.icon}</span>
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: ui.space.xs }}>
                <code style={{ fontSize: ui.font.size.md, fontWeight: ui.font.weight.bold, color: ui.color.ink }}>{a.label}</code>
                <span style={{ fontSize: ui.font.size.xs, color: ui.color.faint }}>{a.size}</span>
              </div>
              <div style={{ fontSize: ui.font.size.base, color: ui.color.body, lineHeight: 1.5 }}>{a.desc}</div>
            </div>
            <a href={a.file} download={a.label}
              style={{
                padding: '5px 14px', borderRadius: ui.radius.sm, textDecoration: 'none',
                background: a.color, color: ui.color.surface, fontSize: ui.font.size.sm, fontWeight: ui.font.weight.bold,
                whiteSpace: 'nowrap', alignSelf: 'center',
              }}>
              ↓ {t('paperReview.downloadLabel')}
            </a>
          </Panel>
        ))}
      </div>

      {/* Canonical figure preview */}
      <Panel style={{ padding: ui.space.xl, marginBottom: ui.space.xxl }}>
        <div style={{ fontSize: ui.font.size.base, fontWeight: ui.font.weight.bold, color: ui.color.body, marginBottom: ui.space.md }}>
          {t('paperReview.figurePreviewTitle')}
        </div>
        <img src="/data/adc/canonical_figure.png" alt={t('paperReview.figureAlt')}
          style={{ maxWidth: '100%', borderRadius: ui.radius.sm, border: `1px solid ${ui.color.line}` }} />
        <div style={{ marginTop: ui.space.sm, fontSize: ui.font.size.xs, color: ui.color.faint, lineHeight: 1.5 }}>
          {t('paperReview.figureCaption1')} <code>research_validation/paper/figures/generate_figure_canonical_chain.py</code> {t('paperReview.figureCaption2')}
        </div>
      </Panel>

      {/* Run IDs */}
      <div style={{ background: ui.color.ink, borderRadius: ui.radius.lg, padding: `${ui.space.lg}px ${ui.space.xl}px`, marginBottom: ui.space.xl }}>
        <div style={{ fontSize: ui.font.size.sm, fontWeight: ui.font.weight.bold, color: '#64B5F6', marginBottom: ui.space.sm,
                      textTransform: 'uppercase', letterSpacing: '0.08em' }}>
          {t('paperReview.runIdsTitle')} — hcie-final-postgres
        </div>
        {RUN_IDS.map(r => (
          <div key={r.id} style={{ marginBottom: ui.space.sm }}>
            <div style={{ fontSize: ui.font.size.xs, color: 'rgba(255,255,255,0.45)', marginBottom: 2 }}>{r.label}</div>
            <code style={{ fontSize: ui.font.size.sm, color: r.color, fontFamily: 'monospace' }}>{r.id}</code>
          </div>
        ))}
      </div>

      {/* ADC Claim */}
      <blockquote style={{
        margin: 0, padding: `${ui.space.lg}px ${ui.space.xl}px`,
        borderLeft: `4px solid ${ui.tone.info.fg}`, background: ui.tone.info.bg,
        borderRadius: `0 ${ui.radius.md}px ${ui.radius.md}px 0`, fontSize: ui.font.size.md, color: ui.tone.info.fg,
        fontStyle: 'italic', lineHeight: 1.65,
      }}>
        {t('paperReview.adcClaim')}
      </blockquote>

      <NextSteps />
    </div>
  )
}
