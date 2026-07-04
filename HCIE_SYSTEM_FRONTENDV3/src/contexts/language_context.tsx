'use client'

/**
 * Lightweight language context (EN ↔ ID).
 *
 * Why not next-intl?
 * ──────────────────
 * The repo had a leftover next-intl stub (i18n/request.ts, an unwired toggle)
 * but no `app/[locale]/...` route restructure, no middleware, and no message
 * files. Finishing next-intl would force a route refactor across the whole
 * frontend. This context is the pragmatic middle: client-side, opt-in per
 * string, persistent via localStorage, no route changes required.
 *
 * Usage
 * ─────
 *   const t = useT()
 *   t('common.all')                 → "All" / "Semua"
 *   t('common.missing', 'Fallback') → "Fallback" (key not in dict)
 *   const { language, setLanguage } = useLanguage()
 */

import { createContext, useContext, useEffect, useState, useCallback } from 'react'
import { dictionary, resolveKey, type Lang } from '@/lib/i18n/dictionary'

const STORAGE_KEY = 'hcie_lang'
// Custom event name shared with GlobalLanguageToggle so toggles rendered
// outside the provider tree (or before hydration) can sync with provider state.
const STORAGE_EVENT = 'hcie-lang-change'

type LanguageContextValue = {
  language: Lang
  setLanguage: (lang: Lang) => void
  t: (key: string, fallback?: string) => string
}

const LanguageContext = createContext<LanguageContextValue | null>(null)

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  // SSR safety: default to 'en' on first render, then hydrate from localStorage
  // in an effect. This avoids a hydration mismatch warning while still letting
  // the toggle persist across navigations.
  const [language, setLanguageState] = useState<Lang>('en')

  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY) as Lang | null
      if (stored === 'en' || stored === 'id') setLanguageState(stored)
    } catch { /* localStorage unavailable */ }
    // Listen for changes coming from other tabs or from the global toggle
    // (which writes localStorage directly so it works pre-hydration).
    const sync = () => {
      try {
        const v = localStorage.getItem(STORAGE_KEY)
        if (v === 'en' || v === 'id') setLanguageState(v)
      } catch { /* ignore */ }
    }
    window.addEventListener('storage', sync)
    window.addEventListener(STORAGE_EVENT, sync)
    return () => {
      window.removeEventListener('storage', sync)
      window.removeEventListener(STORAGE_EVENT, sync)
    }
  }, [])

  const setLanguage = useCallback((lang: Lang) => {
    setLanguageState(lang)
    try {
      localStorage.setItem(STORAGE_KEY, lang)
      window.dispatchEvent(new Event(STORAGE_EVENT))
    } catch { /* ignore */ }
  }, [])

  const t = useCallback((key: string, fallback?: string): string => {
    // Try the active language first; if missing, fall back to English; if
    // still missing, return the provided fallback (or the key itself so the
    // gap is visible in the UI).
    const primary = resolveKey(dictionary[language], key)
    if (primary != null) return primary
    const en = resolveKey(dictionary.en, key)
    if (en != null) return en
    return fallback ?? key
  }, [language])

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  )
}

export function useLanguage() {
  const ctx = useContext(LanguageContext)
  if (!ctx) {
    // Soft fallback so any page that forgets to wrap in the provider still
    // renders English instead of crashing.
    return {
      language: 'en' as Lang,
      setLanguage: () => { /* no-op */ },
      t: (key: string, fallback?: string) =>
        resolveKey(dictionary.en, key) ?? fallback ?? key,
    }
  }
  return ctx
}

/** Convenience hook for the most common use — just the translator function. */
export function useT() {
  return useLanguage().t
}
