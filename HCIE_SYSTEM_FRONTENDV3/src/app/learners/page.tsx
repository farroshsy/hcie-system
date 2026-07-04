'use client'

/**
 * /learners — the entry point for the three real learner classes. Browse any
 * learner the pipeline actually processed (real / synthetic / dataset) and open
 * its full end-to-end view. Everything here is real data from
 * /v3/frontend/dashboard/learner-cohort — no fabricated learners.
 */
import { useRouter } from 'next/navigation'
import { LearnerSelector, CLASS_META, LearnerRow, LearnerClass } from '@/components/learners/LearnerSelector'
import Link from 'next/link'
import { Panel, Tag, Callout, Eyebrow } from '@/lib/ui/primitives'
import { t as ui } from '@/lib/ui/theme'
import { useT } from '@/contexts/language_context'
import { NextSteps } from '@/components/review/NextSteps'

export default function LearnersPage() {
  const t = useT()
  const router = useRouter()
  const open = (l: LearnerRow) =>
    router.push(`/dashboard/learner?user_id=${encodeURIComponent(l.user_id)}`)

  // Localized label/description per learner class. Kept in the component so t()
  // is in scope; falls back to the structural meta in CLASS_META for colors.
  const classLabel: Record<LearnerClass, string> = {
    real: t('learnersPage.classRealLabel'),
    synthetic: t('learnersPage.classSyntheticLabel'),
    dataset: t('learnersPage.classDatasetLabel'),
  }
  const classDesc: Record<LearnerClass, string> = {
    real: t('learnersPage.classRealDesc'),
    synthetic: t('learnersPage.classSyntheticDesc'),
    dataset: t('learnersPage.classDatasetDesc'),
  }

  return (
    <div style={{ maxWidth: 1120, margin: '0 auto', padding: `${ui.space.xl + 8}px ${ui.space.lg}px 80px`, fontFamily: 'Inter, system-ui, sans-serif' }}>
      <Eyebrow color={ui.tone.info.fg}>{t('learnersPage.eyebrow')}</Eyebrow>
      <h1 style={{ fontSize: ui.font.size.h1, fontWeight: ui.font.weight.heavy, color: ui.color.ink, margin: `0 0 ${ui.space.sm}px` }}>{t('learnersPage.title')}</h1>
      <p style={{ fontSize: ui.font.size.md, color: ui.color.body, maxWidth: 820, lineHeight: 1.6, margin: `0 0 ${ui.space.lg}px` }}>
        {t('learnersPage.introLead')} <b>{t('learnersPage.introPipeline')}</b> {t('learnersPage.introMid')}
        <code>experiment_trajectories</code>{t('learnersPage.introTail')}
      </p>

      {/* Canonical population counts — educational claim kept separate from the human+replay total */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: ui.space.md, marginBottom: ui.space.md }}>
        <Panel tone="ok" pad="md">
          <div style={{ fontSize: ui.font.size.h2, fontWeight: ui.font.weight.heavy, color: ui.tone.ok.fg }}>
            54 <span style={{ fontSize: ui.font.size.md, fontWeight: ui.font.weight.bold }}>{t('learnersPage.humanLearners')}</span>
          </div>
          <div style={{ fontSize: ui.font.size.base, color: ui.color.heading, marginTop: 2 }}>· 661 {t('learnersPage.humanInteractions')}</div>
          <div style={{ fontSize: ui.font.size.sm, color: ui.color.muted, marginTop: ui.space.xs }}>{t('learnersPage.humanScope')}</div>
        </Panel>
        <Panel pad="md">
          <div style={{ fontSize: ui.font.size.h2, fontWeight: ui.font.weight.heavy, color: ui.color.heading }}>
            773 <span style={{ fontSize: ui.font.size.md, fontWeight: ui.font.weight.bold }}>{t('learnersPage.realLearners')}</span>
          </div>
          <div style={{ fontSize: ui.font.size.base, color: ui.color.heading, marginTop: 2 }}>· 108,602 {t('learnersPage.realInteractions')}</div>
          <div style={{ fontSize: ui.font.size.sm, color: ui.color.muted, marginTop: ui.space.xs }}>{t('learnersPage.realScope')}</div>
        </Panel>
        <Panel tone="info" pad="md">
          <div style={{ display: 'flex', alignItems: 'center', gap: ui.space.sm, marginBottom: ui.space.xs }}>
            <span style={{ fontSize: ui.font.size.base, fontWeight: ui.font.weight.heavy, color: ui.tone.info.fg }}>{t('learnersPage.sealedSource')}</span>
            <Tag tone="info">pass17</Tag>
          </div>
          <div style={{ fontSize: ui.font.size.sm, color: ui.color.body, lineHeight: 1.5 }}>{t('learnersPage.sealedBody1')} <code>seal-bae44d1a</code> · git_dirty=false. {t('learnersPage.sealedBody2')}</div>
        </Panel>
      </div>

      {/* 3-class legend */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: ui.space.md, marginBottom: ui.space.xl + 2 }}>
        {(['real', 'synthetic', 'dataset'] as LearnerClass[]).map(c => {
          const m = CLASS_META[c]
          return (
            <Panel key={c} pad="md" style={{ background: m.bg, borderColor: m.border }}>
              <div style={{ fontSize: ui.font.size.base, fontWeight: ui.font.weight.heavy, color: m.color, marginBottom: ui.space.xs }}>{classLabel[c]}</div>
              <div style={{ fontSize: ui.font.size.base, color: ui.color.heading, lineHeight: 1.5 }}>{classDesc[c]}</div>
            </Panel>
          )
        })}
      </div>

      {/* launch synthetic cohort (real generation through the live loop) */}
      <Panel tone="accent" pad="md" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: ui.space.md, marginBottom: ui.space.lg + 2, flexWrap: 'wrap' }}>
        <div style={{ fontSize: ui.font.size.md, color: ui.tone.accent.fg }}>
          <b>{t('learnersPage.launchPrompt')}</b> {t('learnersPage.launchBody')}
        </div>
        <Link href="/learners/launch" style={{ textDecoration: 'none', fontSize: ui.font.size.md, fontWeight: ui.font.weight.bold, color: '#fff',
                background: ui.modelColor.gkt, borderRadius: ui.radius.md, padding: `${ui.space.sm}px ${ui.space.lg}px`, whiteSpace: 'nowrap' }}>
          {t('learnersPage.launchButton')}
        </Link>
      </Panel>

      <Panel pad="lg" style={{ borderRadius: ui.radius.xl }}>
        <LearnerSelector onSelect={open} />
      </Panel>

      <Callout tone="neutral" style={{ marginTop: ui.space.lg }}>
        {t('learnersPage.calloutLead')} <code>/dashboard/learner?user_id=…</code> {t('learnersPage.calloutMid')}
        {t('learnersPage.calloutTail')}
      </Callout>

      <NextSteps />
    </div>
  )
}
