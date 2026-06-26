'use client'

import Link from 'next/link'
import ProvisionalBanner from '@/components/review/ProvisionalBanner'
import { useT } from '@/contexts/language_context'
import { Panel, Callout, Eyebrow } from '@/lib/ui/primitives'
import { t as ui } from '@/lib/ui/theme'  // aliased: `t` is taken by useT() (translations)

const SHOWCASES = [
  {
    href: '/review/topology',
    badge: '8 / 8',
    badgeColor: '#1E8449',
    title: 'Topology Taxonomy',
    body: 'ADC sealed thresholds correctly predicted activation class for all 8 dataset/phase pairs — before any run data was seen.',
    tag: 'MEASUREMENT',
    tagColor: '#1565C0',
  },
  {
    href: '/review/trace',
    badge: '8×',
    badgeColor: '#C0392B',
    title: 'Governance Trace',
    body: 'Learner ex_junyi_graph_135350: at interaction 25 (division_4 first encounter) T_realized share spikes 3.3% → 25.6%.',
    tag: 'CAUSAL',
    tagColor: '#6A1E55',
  },
  {
    href: '/review/ablation',
    badge: 'WITHDRAWN',
    badgeColor: '#C0392B',
    title: 'R12 Ablation',
    body: 'Attempted same-user graph ON/OFF replay; re-derivation showed a confounded, sign-unstable graph-OFF control. No R12 ΔAUC is shipped.',
    tag: 'CONTROL',
    tagColor: '#5D4037',
  },
  {
    href: '/review/baselines',
    badge: '0.609',
    badgeColor: '#1E8449',
    title: 'Baseline Comparison',
    body: 'Sealed matched evaluation: HCIE is competitive overall (0.609), within 0.003 of BKT (0.612) and ahead of DKT (0.589), SAKT (0.573), and GKT (0.571).',
    tag: 'MEASUREMENT',
    tagColor: '#1565C0',
  },
  {
    href: '/review/replay',
    badge: '100',
    badgeColor: '#5D4037',
    title: 'Replay Explorer',
    body: 'Inspect any of 100 interactions: see the full Event → DAG lookup → JT attribution → mastery update causal chain.',
    tag: 'TRACE',
    tagColor: '#4A235A',
  },
]

export default function ReviewOverview() {
  const t = useT()
  return (
    <div style={{ padding: '40px 48px', maxWidth: 900 }}>
      {/* Hero */}
      <div style={{ marginBottom: 40 }}>
        <Eyebrow color={ui.tone.info.fg}>{t('review.eyebrow')}</Eyebrow>
        <h1 style={{ fontSize: ui.font.size.h1, fontWeight: ui.font.weight.heavy, color: ui.color.ink, lineHeight: 1.25, marginBottom: ui.space.lg }}>
          {t('review.title')}
        </h1>
        <p style={{ fontSize: ui.font.size.lg, color: ui.color.body, lineHeight: 1.65, maxWidth: 740 }}>
          {t('review.intro')}
        </p>
      </div>

      {/* For-reviewers friendly entry */}
      <Link href="/review/start-here" style={{ textDecoration: 'none' }}>
        <Panel tone="info" pad="lg" style={{ marginBottom: 28, display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer' }}>
          <div>
            <div style={{ fontSize: ui.font.size.lg, fontWeight: ui.font.weight.bold, color: ui.tone.info.fg }}>New here? Start with the plain-language overview →</div>
            <div style={{ fontSize: ui.font.size.md, color: ui.color.body, marginTop: 2 }}>The result, the live tutor, and what the words mean — readable by any reviewer.</div>
          </div>
          <span style={{ fontSize: 24, color: ui.tone.info.fg }} aria-hidden>→</span>
        </Panel>
      </Link>

      {/* Portal-wide PROVISIONAL caveat (scope, not run identity — the
          ProvenanceBadge on each page pins WHICH run; this pins WHICH protocol). */}
      <ProvisionalBanner
        headline="Portal numbers predate the Option-2 sealed re-run"
        body={<>
          The figures in this portal were computed on the original run set. The hypothesis — HCIE wins
          at <strong>cold-start specifically</strong> because it is O(1) embedding-free — actually requires
          a <strong>train-on-few / evaluate-on-unseen-users</strong> protocol. The current &quot;cold-start&quot;
          here is the <em>first-N interaction slice of a full-population run</em>, not that protocol.
          Read this portal as the calibrated evidence trail that motivates the sealed re-run, not as a
          terminal result.
        </>}
        flipsAfter={[
          'Benchmark/baselines re-pointed at train-on-few/eval-on-unseen runs',
          'Graph-KT widened beyond N=10 eval users',
          'JT 6-dim ablation re-run at results-grade (replaces smoke runs)',
          'Each new run sealed via Stage 0 and surfaced on /infrastructure → sealed runs',
        ]}
      />

      {/* Causal chain banner */}
      <Panel tone="info" pad="md" style={{ marginBottom: 36, display: 'flex',
                    alignItems: 'center', gap: ui.space.sm, flexWrap: 'wrap', fontSize: ui.font.size.md }}>
        {['Topology Class', 'ADC Prediction', 'Observed Activation', 'Governance Trace', 'Shuffled-DAG Control', 'Prediction Delta'].map((step, i, arr) => (
          <span key={step} style={{ display: 'inline-flex', alignItems: 'center', gap: ui.space.sm }}>
            <span style={{ fontWeight: ui.font.weight.medium, color: '#1A5276' }}>{step}</span>
            {i < arr.length - 1 && <span style={{ color: '#7FB3D3', fontSize: 16 }}>→</span>}
          </span>
        ))}
      </Panel>

      {/* Showcase cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(380px, 1fr))', gap: ui.space.lg }}>
        {SHOWCASES.map(({ href, badge, badgeColor, title, body, tag, tagColor }) => (
          <Link key={href} href={href} style={{ textDecoration: 'none' }}>
            <div style={{
              background: ui.color.surface, border: `1px solid ${ui.color.line}`, borderRadius: ui.radius.lg,
              padding: `${ui.space.xl}px ${ui.space.xl}px`, cursor: 'pointer',
              transition: 'box-shadow 0.15s, border-color 0.15s',
              height: '100%',
            }}
            onMouseEnter={e => {
              (e.currentTarget as HTMLDivElement).style.boxShadow = '0 4px 16px rgba(0,0,0,0.08)'
              ;(e.currentTarget as HTMLDivElement).style.borderColor = ui.tone.info.border
            }}
            onMouseLeave={e => {
              (e.currentTarget as HTMLDivElement).style.boxShadow = 'none'
              ;(e.currentTarget as HTMLDivElement).style.borderColor = ui.color.line
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: ui.space.md }}>
                <span style={{ fontSize: ui.font.size.h2, fontWeight: ui.font.weight.heavy, color: badgeColor }}>{badge}</span>
                <span style={{ fontSize: ui.font.size.xs, fontWeight: ui.font.weight.bold, letterSpacing: '0.08em',
                               background: `${tagColor}18`, color: tagColor,
                               padding: '2px 8px', borderRadius: ui.radius.sm }}>
                  {tag}
                </span>
              </div>
              <div style={{ fontSize: ui.font.size.lg, fontWeight: ui.font.weight.bold, color: ui.color.ink, marginBottom: ui.space.xs }}>{title}</div>
              <div style={{ fontSize: ui.font.size.md, color: ui.color.body, lineHeight: 1.55 }}>{body}</div>
            </div>
          </Link>
        ))}
      </div>

      {/* Sealed thresholds note */}
      <Callout tone="warn" style={{ marginTop: 36 }} title="Sealed thresholds (immutable):">
        α_floor = 0.01 · signal_ratio_threshold = 0.08 · Frozen before any run data was observed.
        Run IDs are permanent in hcie-final-postgres.
      </Callout>
    </div>
  )
}
