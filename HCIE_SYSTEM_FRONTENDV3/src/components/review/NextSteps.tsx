'use client'

/**
 * NextSteps — a small bilingual "where to go next" strip.
 *
 * The page audit found many review/evidence pages were dead ends (a long dense
 * page with no onward link), so a reviewer would get stuck. Drop <NextSteps />
 * at the bottom of a page and it looks up sensible next destinations by route
 * and renders them. Labels resolve through the nav.* i18n namespace (EN/ID).
 */

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useT } from '@/contexts/language_context'

type Step = { href: string; labelKey: string }

// route → recommended onward destinations (from the page-flow audit)
const NEXT: Record<string, Step[]> = {
  '/review/story': [{ href: '/review/narrative', labelKey: 'nav.reviewNarrative' }, { href: '/review/start-here', labelKey: 'nav.reviewStartHere' }],
  '/review/narrative': [{ href: '/review/theory', labelKey: 'nav.reviewTheory' }, { href: '/review/architecture', labelKey: 'nav.reviewArchitecture' }],
  '/review/theory': [{ href: '/review/adc-general', labelKey: 'nav.reviewAdcGeneral' }, { href: '/review/architecture', labelKey: 'nav.reviewArchitecture' }],
  '/review/adc-general': [{ href: '/review/theory', labelKey: 'nav.reviewTheory' }, { href: '/review/architecture', labelKey: 'nav.reviewArchitecture' }],
  '/review/architecture': [{ href: '/review/methods', labelKey: 'nav.methods' }, { href: '/review/system-journey', labelKey: 'nav.reviewSystemJourney' }],
  '/review/figures': [{ href: '/dashboard/benchmarks', labelKey: 'nav.benchmarks' }, { href: '/review/start-here', labelKey: 'nav.reviewStartHere' }],
  '/review/algo-compare': [{ href: '/review/theory', labelKey: 'nav.reviewTheory' }, { href: '/review/baselines', labelKey: 'nav.reviewBaselines' }],
  '/review/baselines': [{ href: '/review/topology', labelKey: 'nav.reviewTopology' }, { href: '/review/cross-dataset', labelKey: 'nav.reviewCrossDataset' }],
  '/review/ablation': [{ href: '/review/topology', labelKey: 'nav.reviewTopology' }, { href: '/review/trace', labelKey: 'nav.reviewTrace' }],
  '/review/trace': [{ href: '/review/topology', labelKey: 'nav.reviewTopology' }, { href: '/dashboard/audit', labelKey: 'nav.audit' }],
  '/review/topology': [{ href: '/review/ablation', labelKey: 'nav.reviewAblation' }, { href: '/review/cross-dataset', labelKey: 'nav.reviewCrossDataset' }],
  '/review/methods': [{ href: '/review/baselines', labelKey: 'nav.reviewBaselines' }, { href: '/review/topology', labelKey: 'nav.reviewTopology' }],
  '/review/paper': [{ href: '/review/start-here', labelKey: 'nav.reviewStartHere' }, { href: '/dashboard/reproducibility', labelKey: 'nav.reproducibility' }],
  '/review/replay': [{ href: '/dashboard/reproducibility', labelKey: 'nav.reproducibility' }, { href: '/review/trace', labelKey: 'nav.reviewTrace' }],
  '/dashboard/quality': [{ href: '/dashboard/reproducibility', labelKey: 'nav.reproducibility' }, { href: '/dashboard/observability', labelKey: 'nav.observability' }, { href: '/dashboard/method-grounding', labelKey: 'nav.methods' }],
  '/dashboard/replay-verify': [{ href: '/dashboard/reproducibility', labelKey: 'nav.reproducibility' }, { href: '/dashboard/quality', labelKey: 'nav.quality' }],
  '/research': [{ href: '/dashboard', labelKey: 'nav.hub' }, { href: '/dashboard/benchmarks', labelKey: 'nav.benchmarks' }],
}

export function NextSteps({ steps }: { steps?: Step[] }) {
  const t = useT()
  const pathname = usePathname()
  const list = steps ?? NEXT[pathname] ?? []
  if (!list.length) return null
  return (
    <div style={{ marginTop: 32, paddingTop: 16, borderTop: '1px solid #E2E8F0',
                  display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
      <span style={{ fontSize: 12, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: '#94A3B8' }}>
        {t('nav.nextLabel')}
      </span>
      {list.map(s => (
        <Link key={s.href} href={s.href}
          style={{ fontSize: 13, fontWeight: 600, color: '#2563EB', textDecoration: 'none',
                   border: '1px solid #BFDBFE', background: '#EFF6FF', borderRadius: 8, padding: '6px 12px' }}>
          {t(s.labelKey)} →
        </Link>
      ))}
    </div>
  )
}
