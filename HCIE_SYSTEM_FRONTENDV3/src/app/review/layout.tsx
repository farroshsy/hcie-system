'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useT } from '@/contexts/language_context'

// Grouped by intent so a reviewer starts on the guided path, then drills into
// evidence, then reference. The guided group is the recommended entry.
const GROUPS = [
  { titleKey: 'nav.grpGuided', items: [
    { href: '/review/start-here',      labelKey: 'nav.reviewStartHere',     icon: '◆' },
    { href: '/review/run-it-yourself', labelKey: 'nav.reviewRunLoop',       icon: '▷' },
    { href: '/review/system-journey',  labelKey: 'nav.reviewSystemJourney', icon: '⬡' },
    { href: '/review/cross-dataset',   labelKey: 'nav.reviewCrossDataset',  icon: '⊞' },
  ] },
  { titleKey: 'nav.grpEvidence', items: [
    { href: '/review',           labelKey: 'common.overview',     icon: '⌂' },
    { href: '/review/methods',   labelKey: 'nav.methods',         icon: '⚗' },
    { href: '/review/baselines', labelKey: 'nav.reviewBaselines', icon: '≋' },
    { href: '/review/topology',  labelKey: 'nav.reviewTopology',  icon: '◈' },
    { href: '/review/ablation',  labelKey: 'nav.reviewAblation',  icon: '⊿' },
    { href: '/review/trace',     labelKey: 'nav.reviewTrace',     icon: '◉' },
    { href: '/review/replay',    labelKey: 'nav.reviewReplay',    icon: '▶' },
  ] },
  { titleKey: 'nav.grpReference', items: [
    { href: '/review/theory',        labelKey: 'nav.reviewTheory',       icon: '∑' },
    { href: '/review/architecture',  labelKey: 'nav.reviewArchitecture', icon: '⬢' },
    { href: '/review/adc-general',   labelKey: 'nav.reviewAdcGeneral',   icon: '⊛' },
    { href: '/review/algo-compare',  labelKey: 'nav.reviewAlgoCompare',  icon: '⊕' },
    { href: '/review/figures',       labelKey: 'nav.reviewFigures',      icon: '⊟' },
    { href: '/review/narrative',     labelKey: 'nav.reviewNarrative',    icon: '⊗' },
    { href: '/review/story',         labelKey: 'nav.reviewStory',        icon: '◎' },
    { href: '/review/paper',         labelKey: 'nav.reviewPaper',        icon: '⊟' },
  ] },
]

export default function ReviewLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const t = useT()

  return (
    <div className="flex min-h-screen" style={{ fontFamily: 'Inter, system-ui, sans-serif' }}>
      {/* Sidebar */}
      <aside style={{ width: 240, background: '#1A2332', flexShrink: 0 }}
             className="flex flex-col sticky top-0 h-screen overflow-y-auto">
        {/* Header */}
        <div style={{ padding: '20px 16px 12px', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
          <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: '0.12em', color: '#64B5F6',
                        textTransform: 'uppercase', marginBottom: 4 }}>
            HCIE
          </div>
          <div style={{ fontSize: 14, fontWeight: 700, color: '#FFFFFF', lineHeight: 1.3 }}>
            {t('nav.review')}
          </div>
          <div style={{ marginTop: 8, display: 'inline-flex', alignItems: 'center', gap: 4,
                        background: 'rgba(46,213,115,0.15)', borderRadius: 10,
                        padding: '2px 8px' }}>
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#2ED573', display: 'inline-block' }} />
            <span style={{ fontSize: 10, color: '#2ED573', fontWeight: 600 }}>{t('common.noLogin')}</span>
          </div>
        </div>

        <div style={{ padding: '10px 8px 6px', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
          <Link
            href="/dashboard"
            style={{
              display: 'flex', alignItems: 'center', gap: 8,
              padding: '8px 10px', borderRadius: 6,
              textDecoration: 'none',
              background: 'rgba(255,255,255,0.06)',
              color: '#E2E8F0',
              fontWeight: 600,
              fontSize: 12,
              transition: 'background 0.15s, color 0.15s',
            }}
          >
            <span aria-hidden style={{ fontSize: 14 }}>←</span>
            {t('nav.dashboard')}
          </Link>
        </div>

        {/* Nav — grouped by intent (guided → evidence → reference) */}
        <nav style={{ padding: '8px 8px', flex: 1 }}>
          {GROUPS.map((group, gi) => (
            <div key={group.titleKey} style={{ marginTop: gi === 0 ? 0 : 14 }}>
              <div style={{ padding: '4px 10px 6px', fontSize: 10, fontWeight: 700, letterSpacing: '0.1em',
                            textTransform: 'uppercase', color: 'rgba(255,255,255,0.32)' }}>
                {t(group.titleKey)}
              </div>
              {group.items.map(({ href, labelKey, icon }) => {
                const active = pathname === href || (href !== '/review' && pathname.startsWith(href))
                return (
                  <Link key={href} href={href}
                    style={{
                      display: 'flex', alignItems: 'center', gap: 10,
                      padding: '8px 10px', borderRadius: 6, marginBottom: 2,
                      textDecoration: 'none',
                      background: active ? 'rgba(100,181,246,0.15)' : 'transparent',
                      color: active ? '#64B5F6' : 'rgba(255,255,255,0.65)',
                      fontWeight: active ? 600 : 400,
                      fontSize: 13,
                      transition: 'background 0.15s, color 0.15s',
                    }}>
                    <span style={{ fontSize: 15, opacity: active ? 1 : 0.7 }}>{icon}</span>
                    {t(labelKey)}
                  </Link>
                )
              })}
            </div>
          ))}
        </nav>

        {/* Footer */}
        <div style={{ padding: '12px 16px', borderTop: '1px solid rgba(255,255,255,0.08)',
                      fontSize: 10, color: 'rgba(255,255,255,0.3)', lineHeight: 1.5 }}>
          <div>Sealed seal-bae44d1a · N=96,727</div>
          <div>α_floor = 0.01 · signal_ratio = std/mean ≥ 0.08</div>
          <div style={{ marginTop: 4, color: 'rgba(255,255,255,0.2)' }}>calibrated: +0.053 (shuffled-DAG)</div>
        </div>
      </aside>

      {/* Content */}
      <main style={{ flex: 1, background: '#F8FAFC', minHeight: '100vh', overflow: 'auto' }}>
        {children}
      </main>
    </div>
  )
}
