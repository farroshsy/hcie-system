/**
 * Shared types for the user dashboard.
 *
 * Centralized so that ``DashboardLayout`` and ``Navigation`` (and any future
 * screen-aware component) can never drift apart. Previously both files
 * declared local ``Screen`` unions that disagreed, which silently passed type
 * checking until the Docker production build refused to compile.
 */

export type Screen =
  | 'home'
  | 'learning'
  | 'progress'
  | 'profile'
  | 'settings'
  | 'visualizations'
  | 'research'
  | 'system-status'

/**
 * Subset of ``Screen`` values that are rendered inline by ``DashboardLayout``.
 * External screens (``research``, ``system-status``, ``visualizations``) are
 * handled by ``next/navigation`` instead and are intentionally excluded.
 */
export type InlineScreen = Exclude<
  Screen,
  'research' | 'system-status' | 'visualizations'
>
