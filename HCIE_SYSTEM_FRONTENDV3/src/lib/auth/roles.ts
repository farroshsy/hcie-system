/**
 * Role-based access — the SINGLE source of truth (decision D).
 *
 * Roles are hierarchical: student < researcher < admin.
 * This is a UX / navigation layer, NOT a security boundary — the audit/research
 * endpoints are deliberately open (transparency is the ADC ethos). It decides
 * which pages a role SEES and is redirected to, not what the backend authorizes.
 *
 * Decisions baked in:
 *  - A: "instructor" folds into RESEARCHER.
 *  - B: admin is granted by config allow-list (NEXT_PUBLIC_ADMIN_EMAILS), never
 *       self-registered.
 */

export type Role = 'student' | 'researcher' | 'admin'

const LEVEL: Record<Role, number> = { student: 1, researcher: 2, admin: 3 }

// No personal email is hardcoded here (privacy). Set NEXT_PUBLIC_ADMIN_EMAILS at deploy
// time if you want allow-list admins; otherwise admin is granted only by a user's stored
// DB role === 'admin' (see roleOf below).
const ADMIN_EMAILS = (process.env.NEXT_PUBLIC_ADMIN_EMAILS || '')
  .split(',').map(s => s.trim().toLowerCase()).filter(Boolean)

type UserLike = { role?: string | null; email?: string | null } | null | undefined

export function roleOf(user: UserLike): Role {
  if (!user) return 'student'
  const email = (user.email || '').toLowerCase()
  if (email && ADMIN_EMAILS.includes(email)) return 'admin'
  const r = (user.role || '').toLowerCase()
  if (r === 'admin') return 'admin'
  // instructor / teacher fold into researcher (decision A)
  if (r === 'researcher' || r === 'instructor' || r === 'teacher') return 'researcher'
  return 'student'
}

export function atLeast(role: Role, required: Role): boolean {
  return LEVEL[role] >= LEVEL[required]
}

/** Routes anyone (even logged-out) may hit. */
const PUBLIC = new Set(['/', '/login', '/register', '/not-found', '/backend-connection'])

/**
 * pathname-prefix → minimum role. Longest matching prefix wins, so a specific
 * route (e.g. /dashboard/audit = researcher) overrides its parent
 * (/dashboard = student).
 */
const ROUTE_ROLE: Array<[string, Role]> = [
  // ── ADMIN ──
  ['/infrastructure', 'admin'],
  ['/dashboard/infrastructure', 'admin'],
  ['/dashboard/observability', 'admin'],
  ['/dashboard/replay-verify', 'admin'],
  ['/system-status', 'admin'],
  ['/learners/launch', 'admin'],
  ['/admin', 'admin'],
  ['/dev-bypass', 'admin'],
  // ── RESEARCHER ──
  ['/concepts', 'researcher'],
  ['/research', 'researcher'],
  ['/review', 'researcher'],
  ['/learners', 'researcher'],
  ['/cold-start', 'researcher'],
  ['/replay', 'researcher'],
  ['/evidence', 'researcher'],
  ['/visualizations', 'researcher'],
  ['/dashboard/data', 'researcher'],
  ['/dashboard/cohorts', 'researcher'],
  ['/dashboard/benchmarks', 'researcher'],
  ['/dashboard/ablation', 'researcher'],
  ['/dashboard/audit', 'researcher'],
  ['/dashboard/governance', 'researcher'],
  ['/dashboard/method-grounding', 'researcher'],
  ['/dashboard/thesis-evidence', 'researcher'],
  ['/dashboard/reproducibility', 'researcher'],
  ['/dashboard/archetype-modality', 'researcher'],
  ['/dashboard/instructor', 'researcher'],
  ['/dashboard/learner-journey', 'researcher'],
  ['/dashboard/live-users', 'researcher'],
  ['/dashboard/cold-start-journey', 'researcher'],
  // ── LEARNER (student+) — explicit; everything else defaults to student ──
  ['/learn', 'student'],
  ['/dashboard/learner', 'student'],
  ['/profile', 'student'],
  // bare hub is the researcher lens; the student's "hub" is /dashboard/learner
  // (more-specific prefix above keeps it student-level). Students hitting
  // /dashboard get bounced to /learn by the guard.
  ['/dashboard', 'researcher'],
]

export function requiredRoleFor(pathname: string): Role | null {
  if (PUBLIC.has(pathname)) return null
  let match: [string, Role] | null = null
  for (const entry of ROUTE_ROLE) {
    if (pathname === entry[0] || pathname.startsWith(entry[0] + '/')) {
      if (!match || entry[0].length > match[0].length) match = entry
    }
  }
  return match ? match[1] : 'student' // unknown authed routes default to learner-level
}

export function canAccessRoute(pathname: string, role: Role): boolean {
  const req = requiredRoleFor(pathname)
  return req === null ? true : atLeast(role, req)
}

/** Where a role lands by default (login / unauthorized redirect). */
export function homeFor(role: Role): string {
  return role === 'admin' ? '/infrastructure' : role === 'researcher' ? '/dashboard' : '/learn'
}

export interface NavItem { label: string; href: string; icon: string }

export function navItemsForRole(role: Role): NavItem[] {
  const learner: NavItem[] = [
    { label: 'Learn', href: '/learn', icon: '🎓' },
    { label: 'My Progress', href: '/dashboard/learner', icon: '📊' },
    { label: 'Profile', href: '/profile', icon: '👤' },
  ]
  const researcher: NavItem[] = [
    { label: 'Hub', href: '/dashboard', icon: '⬡' },
    { label: 'Data', href: '/dashboard/data', icon: '🗂' },
    { label: 'Cohorts', href: '/dashboard/cohorts', icon: '⚗' },
    { label: 'Benchmarks', href: '/dashboard/benchmarks', icon: '📈' },
    { label: 'Methods', href: '/dashboard/method-grounding', icon: '✓' },
    { label: 'Evidence', href: '/dashboard/thesis-evidence', icon: '🧾' },
    { label: 'Reproducibility', href: '/dashboard/reproducibility', icon: '🔁' },
    { label: 'Governance', href: '/dashboard/governance', icon: '◉' },
    { label: 'Review', href: '/review', icon: '◈' },
    { label: 'Learners', href: '/learners', icon: '🧑‍🎓' },
    { label: 'Cold-Start', href: '/dashboard/cold-start-journey', icon: '❄' },
    { label: 'Quality', href: '/dashboard/quality', icon: '🩺' },
    { label: 'Profile', href: '/profile', icon: '👤' },
  ]
  const admin: NavItem[] = [
    { label: 'Infra', href: '/infrastructure', icon: '🛠' },
    { label: 'Observability', href: '/dashboard/observability', icon: '📡' },
    { label: 'Integrity', href: '/dashboard/replay-verify', icon: '🔒' },
    { label: 'Launch', href: '/learners/launch', icon: '🚀' },
  ]
  if (role === 'admin') return [...researcher, ...admin]
  if (role === 'researcher') return researcher
  return learner
}
