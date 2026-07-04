/**
 * Navigation — top bar, intent-grouped.
 *
 * The role-filtered flat list (navItemsForRole) is bucketed into a few intent
 * groups so a reviewer reads the surface by purpose, not as a 16-item overflow:
 *   Hub · Results · Methods & Audit · System · Evidence Portal
 * Learner role (3 items) renders flat — no dropdowns needed. Labels resolve
 * through the i18n `nav.*` namespace (EN/ID), and the System group surfaces the
 * live monitoring stack (Grafana/Prometheus/Kafka-UI) as external links.
 */

'use client'

import { useState } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { useAuth } from '@/contexts'
import { useT } from '@/contexts/language_context'
import { roleOf, navItemsForRole, homeFor, type NavItem } from '@/lib/auth/roles'

// href → i18n label key (overrides the English fallback labels in roles.ts)
const LABEL_KEY: Record<string, string> = {
  '/dashboard': 'nav.hub', '/dashboard/data': 'nav.data', '/dashboard/cohorts': 'nav.cohorts',
  '/dashboard/benchmarks': 'nav.benchmarks', '/dashboard/method-grounding': 'nav.methods',
  '/dashboard/thesis-evidence': 'nav.evidence', '/dashboard/reproducibility': 'nav.reproducibility',
  '/dashboard/governance': 'nav.governance', '/review': 'nav.review', '/learners': 'nav.learners',
  '/dashboard/cold-start-journey': 'nav.coldStart', '/profile': 'nav.profile',
  '/dashboard/quality': 'nav.quality',
  '/infrastructure': 'nav.infrastructure', '/dashboard/observability': 'nav.observability',
  '/dashboard/replay-verify': 'nav.integrity', '/learners/launch': 'nav.launch',
  '/learn': 'nav.learn', '/dashboard/learner': 'nav.myProgress',
}

// intent groups — hrefs that collapse into one dropdown
const GROUP_DEFS: { key: string; labelKey: string; icon: string; hrefs: string[] }[] = [
  { key: 'results', labelKey: 'nav.grpResults', icon: '📈',
    hrefs: ['/dashboard/benchmarks', '/dashboard/cold-start-journey', '/dashboard/cohorts', '/learners'] },
  { key: 'methods', labelKey: 'nav.grpMethods', icon: '✓',
    hrefs: ['/dashboard/method-grounding', '/dashboard/governance', '/dashboard/reproducibility', '/dashboard/thesis-evidence'] },
  { key: 'system', labelKey: 'nav.grpSystem', icon: '🛠',
    hrefs: ['/dashboard/data', '/dashboard/quality', '/dashboard/observability', '/dashboard/replay-verify', '/infrastructure', '/learners/launch'] },
]
// shown as direct top-level links (in this order), not inside any group
const PINNED = ['/dashboard', '/review']
// live monitoring stack — appended to the System dropdown as external links
const EXTERNAL = [
  { href: '/grafana/', key: 'nav.grafana' },
  { href: '/prometheus/', key: 'nav.prometheus' },
  { href: '/kafka-ui/', key: 'nav.kafkaUi' },
]

export function Navigation() {
  const t = useT()
  const { user, logout } = useAuth()
  const router = useRouter()
  const pathname = usePathname()
  const [menuOpen, setMenuOpen] = useState(false)
  const [openGroup, setOpenGroup] = useState<string | null>(null)

  const role = roleOf(user as { role?: string | null; email?: string | null } | null)
  const items = navItemsForRole(role)
  const present = new Set(items.map(i => i.href))
  const byHref = new Map(items.map(i => [i.href, i]))
  const label = (href: string, fallback: string) => t(LABEL_KEY[href] ?? '', fallback)

  const isActive = (href: string) => pathname === href || pathname.startsWith(href + '/')
  const groupActive = (hrefs: string[]) => hrefs.some(isActive)

  // "rich" nav = role has grouped surfaces (researcher/admin). Learner stays flat.
  const groups = GROUP_DEFS
    .map(g => ({ ...g, members: g.hrefs.filter(h => present.has(h)) }))
    .filter(g => g.members.length > 0)
  const rich = groups.length > 0
  const pinned = PINNED.filter(h => present.has(h))
  // anything not pinned, not grouped, not profile → flat extras (learner: Learn, My Progress)
  const grouped = new Set([...PINNED, ...GROUP_DEFS.flatMap(g => g.hrefs), '/profile'])
  const extras = items.filter(i => !grouped.has(i.href))

  const go = (href: string) => { router.push(href); setOpenGroup(null); setMenuOpen(false) }
  const handleLogout = async () => { await logout(); router.push('/login') }

  const linkClass = (active: boolean) =>
    `flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition ${
      active ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-100'
    }`

  const ItemBtn = ({ it }: { it: NavItem }) => (
    <button onClick={() => go(it.href)} className={linkClass(isActive(it.href))}>
      <span>{it.icon}</span><span>{label(it.href, it.label)}</span>
    </button>
  )

  return (
    <nav className="bg-white shadow-md relative z-40">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex justify-between items-center h-16">

          {/* Logo — bounce each role to its own home */}
          <button onClick={() => go(homeFor(role))}
            className="text-2xl font-bold text-blue-600 hover:text-blue-700 transition shrink-0">
            HCIE
          </button>

          {/* Desktop nav */}
          <div className="hidden md:flex items-center gap-1">
            {pinned.map(h => byHref.get(h) && <ItemBtn key={h} it={byHref.get(h)!} />)}
            {extras.map(it => <ItemBtn key={it.href} it={it} />)}

            {rich && groups.map(g => (
              <div key={g.key} className="relative">
                <button
                  onClick={() => setOpenGroup(openGroup === g.key ? null : g.key)}
                  className={linkClass(groupActive(g.members) || openGroup === g.key)}>
                  <span>{g.icon}</span><span>{t(g.labelKey)}</span>
                  <span className="text-[10px] opacity-60">▾</span>
                </button>
                {openGroup === g.key && (
                  <div className="absolute left-0 mt-1 w-60 bg-white rounded-xl shadow-lg border border-gray-100 py-1.5 z-50">
                    {g.members.map(h => {
                      const it = byHref.get(h)!
                      return (
                        <button key={h} onClick={() => go(h)}
                          className={`w-full flex items-center gap-2 px-3 py-2 text-sm text-left transition ${
                            isActive(h) ? 'bg-blue-50 text-blue-700' : 'text-gray-700 hover:bg-gray-50'
                          }`}>
                          <span className="w-5 text-center">{it.icon}</span>
                          <span>{label(h, it.label)}</span>
                        </button>
                      )
                    })}
                    {g.key === 'system' && (
                      <>
                        <div className="my-1 mx-3 border-t border-gray-100" />
                        <div className="px-3 pb-1 pt-0.5 text-[10px] uppercase tracking-wide text-gray-400">{t('nav.extMonitoring')}</div>
                        {EXTERNAL.map(e => (
                          <a key={e.href} href={e.href} target="_blank" rel="noopener noreferrer"
                            className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 transition">
                            <span className="w-5 text-center">↗</span><span>{t(e.key)}</span>
                          </a>
                        ))}
                      </>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* User + logout */}
          <div className="hidden md:flex items-center gap-3 shrink-0">
            {present.has('/profile') && (
              <button onClick={() => go('/profile')} className={linkClass(isActive('/profile'))}>
                <span>👤</span><span>{t('nav.profile', 'Profile')}</span>
              </button>
            )}
            <span className="text-xs text-gray-400 truncate max-w-[140px]">{user?.email}</span>
            <button onClick={handleLogout} className="text-sm text-gray-500 hover:text-gray-800 transition">
              {t('profile.signOut')}
            </button>
          </div>

          {/* Mobile hamburger */}
          <button onClick={() => setMenuOpen(!menuOpen)} className="md:hidden text-gray-700 p-2" aria-label="Toggle menu">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {menuOpen
                ? <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                : <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />}
            </svg>
          </button>
        </div>

        {/* Mobile menu — groups as labeled sections */}
        {menuOpen && (
          <div className="md:hidden py-3 border-t space-y-1">
            {[...pinned, ...extras.map(e => e.href)].map(h => byHref.get(h) && <ItemBtn key={h} it={byHref.get(h)!} />)}
            {rich && groups.map(g => (
              <div key={g.key} className="pt-2">
                <div className="px-3 pb-1 text-[11px] uppercase tracking-wide text-gray-400">{t(g.labelKey)}</div>
                {g.members.map(h => byHref.get(h) && <ItemBtn key={h} it={byHref.get(h)!} />)}
                {g.key === 'system' && EXTERNAL.map(e => (
                  <a key={e.href} href={e.href} target="_blank" rel="noopener noreferrer"
                    className="flex items-center gap-2 px-3 py-2.5 text-sm text-gray-700 hover:bg-gray-50 rounded-lg">
                    <span>↗</span><span>{t(e.key)}</span>
                  </a>
                ))}
              </div>
            ))}
            <div className="border-t mt-2 pt-2 px-4">
              {present.has('/profile') && (
                <button onClick={() => go('/profile')} className="block py-2 text-sm text-gray-700">👤 {t('nav.profile', 'Profile')}</button>
              )}
              <p className="text-xs text-gray-400 mb-2">{user?.email}</p>
              <button onClick={handleLogout} className="text-sm text-gray-600 hover:text-gray-900">{t('profile.signOut')}</button>
            </div>
          </div>
        )}
      </div>

      {/* click-away backdrop for open dropdown */}
      {openGroup && <div className="fixed inset-0 z-30" onClick={() => setOpenGroup(null)} />}
    </nav>
  )
}
