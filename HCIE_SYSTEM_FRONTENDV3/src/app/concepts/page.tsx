'use client'

/**
 * /concepts — RESEARCHER concept explorer. The real concept set + mastery +
 * prerequisite-edge structure from the backend, for any learner class (real /
 * synthetic / dataset). This is a viewing/analysis surface — NOT the live tutor.
 *
 *   • A learner's own locked/unlocked journey → /learn/concepts
 *   • Run the live adaptive tutor (recommend → answer)  → /learn
 *   • The full Junyi prerequisite DAG                    → /dashboard/data
 *
 * (The old authored "try a task" sandbox + mock bandit-recommendation card were
 * removed: the live recommend/representation decision belongs on /learn, and a
 * fabricated recommendation does not belong on a real-data explorer.)
 */
import { RealConceptMap } from '@/components/learners/RealConceptMap'
import { NextSteps } from '@/components/review/NextSteps'
import { useT } from '@/contexts/language_context'
import Link from 'next/link'

export default function ConceptsPage() {
  const t = useT()
  return (
    <div style={{ maxWidth: 1120, margin: '0 auto', padding: '28px 24px 80px', fontFamily: 'Inter, system-ui, sans-serif' }}>
      <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.1em', color: '#1A5276', textTransform: 'uppercase' }}>
        {t('conceptsPage.eyebrow')}
      </div>
      <h1 style={{ fontSize: 26, fontWeight: 800, color: '#1A2332', margin: '6px 0 8px' }}>{t('conceptsPage.heroTitle')}</h1>
      <p style={{ fontSize: 14, color: '#5A6776', maxWidth: 840, lineHeight: 1.6, margin: '0 0 14px' }}>
        {t('conceptsPage.heroBodyA')}
        {' '}<b>{t('conceptsPage.heroReal')}</b>, <b>{t('conceptsPage.heroSynthetic')}</b>, {t('conceptsPage.heroOr')} <b>{t('conceptsPage.heroDataset')}</b> {t('conceptsPage.heroBodyB')}
      </p>
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 20, fontSize: 13 }}>
        <Link href="/learn/concepts" style={{ color: '#1A5276', textDecoration: 'none', background: '#EBF5FB', border: '1px solid #AED6F1', borderRadius: 8, padding: '6px 12px' }}>
          🗺 {t('conceptsPage.linkJourney')} →
        </Link>
        <Link href="/learn" style={{ color: '#1B5E55', textDecoration: 'none', background: '#F0FAF4', border: '1px solid #B7E0D7', borderRadius: 8, padding: '6px 12px' }}>
          🎓 {t('conceptsPage.linkTutor')} →
        </Link>
        <Link href="/dashboard/data" style={{ color: '#6C3483', textDecoration: 'none', background: '#F4ECF7', border: '1px solid #D7BDE2', borderRadius: 8, padding: '6px 12px' }}>
          🕸 {t('conceptsPage.linkDag')} →
        </Link>
      </div>

      <RealConceptMap />

      <NextSteps />
    </div>
  )
}
