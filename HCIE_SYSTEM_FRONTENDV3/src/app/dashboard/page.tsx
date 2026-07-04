'use client'

/**
 * Dashboard hub home — the single landing that makes every page discoverable.
 * Learner CTA on top (HomeScreen), then a directory of all surfaces grouped by
 * audience so nothing is buried in a footer.
 *
 * All copy goes through `useT()` so the hub fully translates EN ↔ ID.
 */

import Link from 'next/link'
import HomeScreen from '@/components/dashboard/HomeScreen'
import { useT } from '@/contexts/language_context'
import { t as ui } from '@/lib/ui/theme'  // aliased: `t` is taken by useT() (translations)

interface Card { href: string; icon: string; titleKey: string; descKey: string; external?: boolean }

const GROUPS: { labelKey: string; color: string; bg: string; cards: Card[] }[] = [
  {
    labelKey: 'dashboardHub.groupLearner', color: '#1A5276', bg: '#EBF5FB',
    cards: [
      { href: '/learn',            icon: '🎓', titleKey: 'dashboardHub.cards.learnTitle',       descKey: 'dashboardHub.cards.learnDesc' },
      { href: '/learn/concepts',   icon: '🗺', titleKey: 'dashboardHub.cards.conceptMapTitle',  descKey: 'dashboardHub.cards.conceptMapDesc' },
      { href: '/dashboard/learner',icon: '📊', titleKey: 'dashboardHub.cards.myProgressTitle',  descKey: 'dashboardHub.cards.myProgressDesc' },
      { href: '/profile',          icon: '👤', titleKey: 'dashboardHub.cards.profileTitle',     descKey: 'dashboardHub.cards.profileDesc' },
    ],
  },
  {
    labelKey: 'dashboardHub.groupExperiments', color: '#9A7D0A', bg: '#FEF9E7',
    cards: [
      { href: '/dashboard/benchmarks', icon: '📈', titleKey: 'dashboardHub.cards.benchmarksTitle',  descKey: 'dashboardHub.cards.benchmarksDesc' },
      { href: '/dashboard/cohorts',    icon: '⚗', titleKey: 'dashboardHub.cards.cohortStudyTitle', descKey: 'dashboardHub.cards.cohortStudyDesc' },
      { href: '/dashboard/ablation',   icon: '🔬', titleKey: 'dashboardHub.cards.ablationTitle',    descKey: 'dashboardHub.cards.ablationDesc' },
      { href: '/dashboard/audit',      icon: '🧪', titleKey: 'dashboardHub.cards.auditTitle',       descKey: 'dashboardHub.cards.auditDesc' },
    ],
  },
  {
    labelKey: 'dashboardHub.groupData', color: '#117A65', bg: '#E8F8F5',
    cards: [
      { href: '/dashboard/data',       icon: '🗂', titleKey: 'dashboardHub.cards.dataTitle',          descKey: 'dashboardHub.cards.dataDesc' },
      { href: '/dashboard/live-users', icon: '👥', titleKey: 'dashboardHub.cards.liveUsersTitle',     descKey: 'dashboardHub.cards.liveUsersDesc' },
      { href: '/infrastructure',       icon: '🔒', titleKey: 'dashboardHub.cards.infrastructureTitle', descKey: 'dashboardHub.cards.infrastructureDesc' },
      { href: '/dashboard/governance', icon: '⚡', titleKey: 'dashboardHub.cards.governanceTitle',    descKey: 'dashboardHub.cards.governanceDesc' },
      { href: '/dashboard/instructor', icon: '🏫', titleKey: 'dashboardHub.cards.instructorTitle',    descKey: 'dashboardHub.cards.instructorDesc' },
    ],
  },
  {
    labelKey: 'dashboardHub.groupPaper', color: '#1F3A5C', bg: '#EBF5FB',
    cards: [
      { href: '/review',         icon: '📄', titleKey: 'dashboardHub.cards.reviewTitle',  descKey: 'dashboardHub.cards.reviewDesc',  external: true },
      { href: '/review/methods', icon: '🧮', titleKey: 'dashboardHub.cards.methodsTitle', descKey: 'dashboardHub.cards.methodsDesc', external: true },
      { href: '/dashboard/method-grounding', icon: '📋', titleKey: 'dashboardHub.cards.groundingTitle', descKey: 'dashboardHub.cards.groundingDesc' },
      { href: '/dashboard/thesis-evidence', icon: '🧾', titleKey: 'dashboardHub.cards.evidenceTitle', descKey: 'dashboardHub.cards.evidenceDesc' },
      { href: '/dashboard/reproducibility', icon: '🔁', titleKey: 'dashboardHub.cards.reproTitle', descKey: 'dashboardHub.cards.reproDesc' },
    ],
  },
]

export default function DashboardPage() {
  const t = useT()
  return (
    <div>
      {/* Learner CTA + live stats */}
      <HomeScreen />

      {/* Page directory — everything discoverable */}
      <div style={{ maxWidth: 1120, margin: '0 auto', padding: `0 ${ui.space.lg}px 48px` }}>
        <div style={{ borderTop: `1px solid ${ui.color.line}`, paddingTop: 28, marginTop: ui.space.sm }}>
          <h2 style={{ fontSize: ui.font.size.xl, fontWeight: ui.font.weight.heavy, color: ui.color.ink, marginBottom: ui.space.xs }}>
            {t('dashboardHub.explore')}
          </h2>
          <p style={{ fontSize: ui.font.size.md, color: ui.color.muted, marginBottom: ui.space.xxl }}>
            {t('dashboardHub.exploreSub')}
          </p>

          {GROUPS.map(g => (
            <div key={g.labelKey} style={{ marginBottom: 28 }}>
              <div style={{ display: 'inline-block', fontSize: ui.font.size.sm, fontWeight: ui.font.weight.heavy,
                            color: g.color, background: g.bg, borderRadius: ui.radius.sm,
                            padding: '3px 10px', textTransform: 'uppercase',
                            letterSpacing: '0.06em', marginBottom: ui.space.md }}>
                {t(g.labelKey)}
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: ui.space.md }}>
                {g.cards.map(c => {
                  const inner = (
                    <div style={{ background: ui.color.surface, border: `1px solid ${ui.color.line}`, borderRadius: ui.radius.lg,
                                  padding: `${ui.space.md}px ${ui.space.lg}px`, height: '100%', cursor: 'pointer',
                                  transition: 'all 0.15s' }}
                      onMouseEnter={e => { const el = e.currentTarget as HTMLDivElement; el.style.borderColor = g.color; el.style.transform = 'translateY(-2px)'; el.style.boxShadow = '0 4px 12px rgba(0,0,0,0.06)' }}
                      onMouseLeave={e => { const el = e.currentTarget as HTMLDivElement; el.style.borderColor = ui.color.line; el.style.transform = 'translateY(0)'; el.style.boxShadow = 'none' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: ui.space.sm, marginBottom: ui.space.xs }}>
                        <span style={{ fontSize: ui.font.size.h2 }}>{c.icon}</span>
                        <span style={{ fontSize: ui.font.size.md, fontWeight: ui.font.weight.heavy, color: ui.color.ink }}>{t(c.titleKey)}</span>
                        {c.external && <span style={{ fontSize: ui.font.size.xs, color: g.color, fontWeight: ui.font.weight.bold, marginLeft: 'auto' }}>{t('common.noLogin')}</span>}
                      </div>
                      <div style={{ fontSize: ui.font.size.base, color: ui.color.muted, lineHeight: 1.5 }}>{t(c.descKey)}</div>
                    </div>
                  )
                  return c.external
                    ? <a key={c.href} href={c.href} style={{ textDecoration: 'none' }}>{inner}</a>
                    : <Link key={c.href} href={c.href} style={{ textDecoration: 'none' }}>{inner}</Link>
                })}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
