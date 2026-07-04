'use client'

/**
 * Floating language toggle rendered from the root layout.
 *
 * Why this exists
 * ───────────────
 * Wiring an inline <LanguageToggle/> into 43 page headers is churn-heavy and
 * easy to forget on new pages. A single fixed-position component anchored at
 * the bottom-left covers every route — dashboard, review, learn, auth, home.
 *
 * Earlier design issues we are fixing here
 * ────────────────────────────────────────
 *  1) Top-right placement collided with the dashboard nav's Sign-out button
 *     and the mobile hamburger. Now anchored bottom-LEFT, where every layout
 *     in this app leaves the corner empty.
 *  2) "Collapsed pill, expands on hover" was unreadable — on dense pages like
 *     /review/methods the 2-letter chip looked like part of the sidebar
 *     footer, and on touch devices :hover does nothing. Now ALWAYS shows
 *     both EN and ID as a labeled segmented control.
 *  3) Depending on the Providers tree meant the toggle vanished during page
 *     transitions or pre-hydration. The toggle now reads/writes the same
 *     localStorage key the LanguageProvider uses, AND nudges the provider
 *     when present, so it works even before/after providers are ready.
 *  4) Auto-hides under @media print so PDF exports stay clean.
 */

import { useEffect, useState, useSyncExternalStore } from 'react'

const STORAGE_KEY = 'hcie_lang'
type Lang = 'en' | 'id'

// Custom event shared with LanguageProvider so the two stay in sync even
// though this toggle is rendered OUTSIDE the provider tree.
const STORAGE_EVENT = 'hcie-lang-change'

function readStored(): Lang {
  if (typeof window === 'undefined') return 'en'
  try {
    const v = localStorage.getItem(STORAGE_KEY)
    return v === 'id' ? 'id' : 'en'
  } catch { return 'en' }
}

function subscribe(callback: () => void) {
  if (typeof window === 'undefined') return () => {}
  const onStorage = (e: StorageEvent) => {
    if (e.key === STORAGE_KEY) callback()
  }
  const onCustom = () => callback()
  window.addEventListener('storage', onStorage)
  window.addEventListener(STORAGE_EVENT, onCustom)
  return () => {
    window.removeEventListener('storage', onStorage)
    window.removeEventListener(STORAGE_EVENT, onCustom)
  }
}

export function GlobalLanguageToggle() {
  // This component is mounted OUTSIDE <Providers> on purpose — it must keep
  // working even if any provider in the app's tree errors during hydration.
  // It owns localStorage directly; LanguageProvider listens on the same key
  // + custom event, so the rest of the app stays in sync automatically.
  const stored = useSyncExternalStore(subscribe, readStored, () => 'en' as Lang)

  // SSR guard: render same initial markup on server + first client paint to
  // avoid hydration warnings. Default to 'en' until effects run.
  const [hydrated, setHydrated] = useState(false)
  useEffect(() => { setHydrated(true) }, [])
  const shown: Lang = hydrated ? stored : 'en'

  const setLang = (l: Lang) => {
    try {
      localStorage.setItem(STORAGE_KEY, l)
      window.dispatchEvent(new Event(STORAGE_EVENT))
    } catch { /* ignore */ }
  }

  return (
    <>
      <div
        className="hcie-global-lang-toggle"
        role="group"
        aria-label="Language"
        style={{
          position: 'fixed',
          bottom: 16,
          left: 16,
          zIndex: 1000,                        // above almost any page chrome
          display: 'inline-flex',
          alignItems: 'center',
          gap: 6,
          background: 'rgba(255, 255, 255, 0.97)',
          backdropFilter: 'blur(8px)',
          WebkitBackdropFilter: 'blur(8px)',
          padding: '4px 6px 4px 8px',
          borderRadius: 999,
          border: '1px solid rgba(148, 163, 184, 0.55)',
          boxShadow: '0 4px 12px rgba(15, 23, 42, 0.12), 0 1px 2px rgba(15, 23, 42, 0.06)',
          pointerEvents: 'auto',
          fontFamily: 'Inter, system-ui, sans-serif',
        }}
      >
        <span
          aria-hidden
          style={{
            fontSize: 13, lineHeight: 1,
            filter: 'saturate(0.85)',
          }}
        >
          🌐
        </span>

        {(['en', 'id'] as const).map(l => {
          const active = shown === l
          return (
            <button
              key={l}
              type="button"
              onClick={() => setLang(l)}
              aria-pressed={active}
              style={{
                padding: '4px 10px',
                fontSize: 11,
                fontWeight: 700,
                letterSpacing: '0.02em',
                border: 'none',
                borderRadius: 999,
                cursor: 'pointer',
                background: active ? '#6C3483' : 'transparent',
                color: active ? '#fff' : '#475569',
                transition: 'background-color 0.12s, color 0.12s',
                minWidth: 26,
              }}
            >
              {l.toUpperCase()}
            </button>
          )
        })}
      </div>

      <style jsx global>{`
        @media print {
          .hcie-global-lang-toggle { display: none !important; }
        }
        @media (max-width: 600px) {
          .hcie-global-lang-toggle {
            bottom: 10px;
            left: 10px;
            transform: scale(0.94);
            transform-origin: bottom left;
          }
        }
      `}</style>
    </>
  )
}
