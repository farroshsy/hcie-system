'use client'

/**
 * / — landing. One job: get each visitor onto the RIGHT path in one click.
 *
 * Three role-doors instead of a flat card grid: Reviewer (primary → the guided
 * evidence portal), Learner (→ the live tutor), Researcher (→ the dashboards).
 * The reviewer door is highlighted because that's the defense audience, and it
 * routes into /review/start-here which then guides the rest of the flow. Bilingual
 * via the `landing` namespace; quick-jump row for people who already know where to go.
 */

import Link from 'next/link'
import { useT } from '@/contexts/language_context'
import PageGuide, { TourStep } from '@/components/help/PageGuide'

const STEPS: TourStep[] = [
  {
    selector: '[data-tour="tagline"]',
    title: { en: 'What HCIE is', id: 'Apa itu HCIE' },
    body: {
      en: 'This headline sums up the project in one line. Read it first to know what the whole site is about.',
      id: 'Headline ini merangkum proyek dalam satu baris. Baca lebih dulu untuk tahu isi seluruh situs.',
    },
  },
  {
    selector: '[data-tour="door-reviewer"]',
    title: { en: 'Reviewer door', id: 'Pintu Reviewer' },
    body: {
      en: 'Start here if you are a defense reviewer. It opens the guided evidence portal with no login needed.',
      id: 'Mulai di sini jika Anda reviewer sidang. Membuka portal bukti terpandu tanpa perlu login.',
    },
  },
  {
    selector: '[data-tour="door-learner"]',
    title: { en: 'Student door', id: 'Pintu Mahasiswa' },
    body: {
      en: 'Click here to try the live tutor and learn a concept yourself, step by step.',
      id: 'Klik di sini untuk mencoba tutor langsung dan belajar konsep sendiri, langkah demi langkah.',
    },
  },
  {
    selector: '[data-tour="door-researcher"]',
    title: { en: 'Researcher door', id: 'Pintu Peneliti' },
    body: {
      en: 'Open the dashboards to inspect experiments, AUC results, and JT attribution data.',
      id: 'Buka dashboard untuk memeriksa eksperimen, hasil AUC, dan data atribusi JT.',
    },
  },
  {
    selector: '[data-tour="quick-jump"]',
    title: { en: 'Quick links', id: 'Tautan cepat' },
    body: {
      en: 'Already know where to go? Use these shortcuts to jump straight to a specific page.',
      id: 'Sudah tahu tujuan Anda? Gunakan pintasan ini untuk langsung ke halaman tertentu.',
    },
  },
]

export default function HomePage() {
  const t = useT()

  const DOORS = [
    {
      id: 'reviewer', href: '/review/start-here', primary: true, icon: '🔍',
      tag: t('landing.reviewerTag'), title: t('landing.reviewerTitle'),
      desc: t('landing.reviewerDesc'), cta: t('landing.reviewerCta'),
      accent: '#2E86C1', noLogin: true,
    },
    {
      id: 'learner', href: '/learn', primary: false, icon: '🎓',
      tag: t('landing.learnerTag'), title: t('landing.learnerTitle'),
      desc: t('landing.learnerDesc'), cta: t('landing.learnerCta'),
      accent: '#117A65', noLogin: false,
    },
    {
      id: 'researcher', href: '/dashboard', primary: false, icon: '🔬',
      tag: t('landing.researcherTag'), title: t('landing.researcherTitle'),
      desc: t('landing.researcherDesc'), cta: t('landing.researcherCta'),
      accent: '#6C3483', noLogin: false,
    },
  ]

  const JUMP = [
    { href: '/dashboard/benchmarks', label: t('nav.benchmarks') },
    { href: '/dashboard/governance', label: t('nav.governance') },
    { href: '/dashboard/quality', label: t('nav.quality') },
    { href: '/review', label: t('nav.review') },
  ]

  const ARCH = [
    { icon: '⚡', label: 'Event Sourcing', items: ['Kafka topics', 'Transactional outbox', 'CDC connector', 'DLQ replay'] },
    { icon: '🧠', label: 'ITS Governance', items: ['MAB policy selection', 'JT 6D attribution', 'Cold-start bootstrap', 'ADC observability'] },
    { icon: '📡', label: 'Mastery Ensemble', items: ['Bayesian BKT', 'Kalman filter', 'Population-prior cold-start', '2-learner fusion'] },
    { icon: '🔭', label: 'Observability', items: ['Prometheus metrics', 'Grafana dashboards', 'Kafka UI', 'Self-healing agents'] },
  ]

  return (
    <div style={{ minHeight: '100vh', background: 'linear-gradient(135deg, #0D1B2A 0%, #1A2A4A 50%, #0D1B2A 100%)' }}>
      <div style={{ maxWidth: 1080, margin: '0 auto', padding: '56px 24px 64px' }}>

        {/* Hero */}
        <div style={{ textAlign: 'center', marginBottom: 44 }}>
          <div style={{ display: 'inline-block', background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)',
                        borderRadius: 999, padding: '4px 16px', fontSize: 11, fontWeight: 700, letterSpacing: '0.15em',
                        color: '#85C1E9', marginBottom: 16, textTransform: 'uppercase' }}>
            {t('landing.eyebrow')}
          </div>
          <h1 style={{ fontSize: 52, fontWeight: 900, color: '#fff', margin: '0 0 10px', letterSpacing: '-0.02em', lineHeight: 1.05 }}>
            HCIE
          </h1>
          <p data-tour="tagline" style={{ fontSize: 18, color: '#A0B4C8', margin: '0 auto 6px', maxWidth: 640, lineHeight: 1.5 }}>
            {t('landing.subtitle')}
          </p>
          <p style={{ fontSize: 14, color: '#6B8AA8', margin: '0 auto', maxWidth: 560, lineHeight: 1.6 }}>
            {t('landing.lead')}
          </p>
        </div>

        {/* Pick-your-path */}
        <div style={{ textAlign: 'center', fontSize: 12, fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase',
                      color: '#4A6B84', marginBottom: 16 }}>
          {t('landing.pickPath')}
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 16, marginBottom: 36 }}>
          {DOORS.map(d => (
            <Link key={d.id} href={d.href} style={{ textDecoration: 'none' }}>
              <div data-tour={`door-${d.id}`} style={{
                background: d.primary ? 'rgba(46,134,193,0.14)' : 'rgba(255,255,255,0.04)',
                border: `1px solid ${d.primary ? 'rgba(133,193,233,0.45)' : 'rgba(255,255,255,0.1)'}`,
                borderRadius: 16, padding: 22, height: '100%', cursor: 'pointer', transition: 'all 0.2s',
                boxShadow: d.primary ? '0 8px 30px rgba(46,134,193,0.18)' : 'none',
              }}
              onMouseEnter={e => { const el = e.currentTarget as HTMLDivElement; el.style.transform = 'translateY(-3px)'; el.style.borderColor = 'rgba(133,193,233,0.6)' }}
              onMouseLeave={e => { const el = e.currentTarget as HTMLDivElement; el.style.transform = 'translateY(0)'; el.style.borderColor = d.primary ? 'rgba(133,193,233,0.45)' : 'rgba(255,255,255,0.1)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                  <span style={{ fontSize: 30 }}>{d.icon}</span>
                  <span style={{ fontSize: 9, fontWeight: 800, letterSpacing: '0.12em', textTransform: 'uppercase',
                                 color: d.accent, background: `${d.accent}22`, padding: '3px 9px', borderRadius: 5 }}>
                    {d.tag}{d.primary ? ' ★' : ''}
                  </span>
                </div>
                <div style={{ fontSize: 18, fontWeight: 800, color: '#E8F0F8', marginBottom: 8, lineHeight: 1.25 }}>{d.title}</div>
                <div style={{ fontSize: 13, color: '#8AA3B8', lineHeight: 1.6, marginBottom: 16 }}>{d.desc}</div>
                <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 13, fontWeight: 700,
                              color: d.primary ? '#fff' : d.accent, background: d.primary ? '#2E86C1' : 'transparent',
                              padding: d.primary ? '9px 16px' : '0', borderRadius: 8 }}>
                  {d.cta}
                  {d.noLogin && <span style={{ fontSize: 10, opacity: 0.75, fontWeight: 600 }}>· {t('common.noLogin')}</span>}
                </div>
              </div>
            </Link>
          ))}
        </div>

        {/* Quick jump */}
        <div data-tour="quick-jump" style={{ textAlign: 'center', marginBottom: 44 }}>
          <span style={{ fontSize: 12, color: '#4A6B84', marginRight: 10 }}>{t('landing.jumpLabel')}:</span>
          {JUMP.map((j, i) => (
            <span key={j.href}>
              <Link href={j.href} style={{ fontSize: 13, color: '#85C1E9', fontWeight: 600, textDecoration: 'none' }}>{j.label}</Link>
              {i < JUMP.length - 1 && <span style={{ color: '#2E4A5E', margin: '0 8px' }}>·</span>}
            </span>
          ))}
        </div>

        {/* System architecture */}
        <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 14, padding: '20px 24px', marginBottom: 28 }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: '#4A6B84', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 16 }}>
            {t('landing.archTitle')}
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
            {ARCH.map(({ icon, label, items }) => (
              <div key={label}>
                <div style={{ fontSize: 16, marginBottom: 6 }}>{icon}</div>
                <div style={{ fontSize: 12, fontWeight: 700, color: '#A0B4C8', marginBottom: 8 }}>{label}</div>
                <ul style={{ margin: 0, paddingLeft: 14, listStyle: 'disc' }}>
                  {items.map(item => <li key={item} style={{ fontSize: 11, color: '#5D7A8A', marginBottom: 3 }}>{item}</li>)}
                </ul>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div style={{ textAlign: 'center', fontSize: 11, color: '#2E4A5E', lineHeight: 1.6 }}>
          HCIE — Hierarchical Cognitive Inference Engine · {t('landing.footer')}
        </div>
      </div>
      <PageGuide tourId="home" steps={STEPS} />
    </div>
  )
}
