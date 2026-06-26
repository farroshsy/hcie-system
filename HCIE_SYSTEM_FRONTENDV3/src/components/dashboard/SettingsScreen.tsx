/**
 * Settings Screen
 * 
 * Application settings including theme, language, notifications, and other preferences.
 */

'use client'

import { useState } from 'react'
import { useConfig } from '@/contexts'
import { useLanguage, useT } from '@/contexts/language_context'

export default function SettingsScreen() {
  const t = useT()
  const config = useConfig()
  // Wire the Settings language picker into the real language context so the
  // single in-app source of truth (also driven by the top-right floater)
  // updates instantly across every page.
  const { language, setLanguage } = useLanguage()
  const [theme, setTheme] = useState(config.ui.theme)
  const [animations, setAnimations] = useState(config.ui.animations)
  const [accessibility, setAccessibility] = useState(config.ui.accessibility)

  const handleThemeChange = (newTheme: 'light' | 'dark' | 'system') => {
    setTheme(newTheme)
  }

  const handleSaveSettings = () => {
    // Theme/animations/accessibility wiring is deferred to a follow-up; language
    // already persists via the LanguageProvider's localStorage key.
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-8">
        <div className="bg-white rounded-lg shadow p-8">
          {/* Header */}
          <div className="mb-6">
            <h1 className="text-2xl font-bold text-gray-900">{t('settingsPage.title')}</h1>
            <p className="text-sm text-gray-500 mt-1">{t('settingsPage.eyebrow')}</p>
          </div>

          {/* Appearance Section */}
          <div className="mb-8">
            <h2 className="text-xl font-bold text-gray-900 mb-6">{t('settingsPage.appearance')}</h2>

            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">{t('settingsPage.themeLabel')}</label>
                <div className="flex gap-4">
                  {(['light', 'dark', 'system'] as const).map((th) => (
                    <button
                      key={th}
                      onClick={() => handleThemeChange(th)}
                      className={`px-4 py-2 rounded-lg border-2 transition ${
                        theme === th
                          ? 'border-blue-500 bg-blue-50 text-blue-700'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      {t(`settingsPage.theme.${th}`)}
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <label className="block text-sm font-medium text-gray-700">{t('settingsPage.animationsLabel')}</label>
                </div>
                <button
                  onClick={() => setAnimations(!animations)}
                  className={`w-12 h-6 rounded-full transition ${
                    animations ? 'bg-blue-600' : 'bg-gray-300'
                  }`}
                >
                  <div
                    className={`w-5 h-5 bg-white rounded-full transition transform ${
                      animations ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
            </div>
          </div>

          {/* Language Section */}
          <div className="mb-8 border-t pt-8">
            <h2 className="text-xl font-bold text-gray-900 mb-2">{t('settingsPage.language')}</h2>
            <p className="text-sm text-gray-500 mb-6">{t('settingsPage.languageDesc')}</p>

            <div className="flex gap-4">
              {(['en', 'id'] as const).map((lang) => (
                <button
                  key={lang}
                  onClick={() => setLanguage(lang)}
                  className={`px-4 py-2 rounded-lg border-2 transition ${
                    language === lang
                      ? 'border-blue-500 bg-blue-50 text-blue-700'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  {lang === 'en' ? 'English' : 'Bahasa Indonesia'}
                </button>
              ))}
            </div>
          </div>

          {/* Accessibility Section */}
          <div className="mb-8 border-t pt-8">
            <h2 className="text-xl font-bold text-gray-900 mb-6">{t('settingsPage.accessibility')}</h2>

            <div className="flex items-center justify-between">
              <div>
                <label className="block text-sm font-medium text-gray-700">{t('settingsPage.accessibilityLabel')}</label>
              </div>
              <button
                onClick={() => setAccessibility(!accessibility)}
                className={`w-12 h-6 rounded-full transition ${
                  accessibility ? 'bg-blue-600' : 'bg-gray-300'
                }`}
              >
                <div
                  className={`w-5 h-5 bg-white rounded-full transition transform ${
                    accessibility ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          </div>

          {/* Debug Section - Only in development */}
          {config.environment === 'development' && (
            <div className="mb-8 border-t pt-8">
              <h2 className="text-xl font-bold text-gray-900 mb-6">{t('settingsPage.debugTitle')}</h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">{t('settingsPage.environment')}</label>
                  <p className="text-sm text-gray-900">{config.environment}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">{t('settingsPage.apiUrl')}</label>
                  <p className="text-sm text-gray-900">{config.api.baseUrl}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">{t('settingsPage.websocketUrl')}</label>
                  <p className="text-sm text-gray-900">{config.websocket.url}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">{t('settingsPage.featureFlags')}</label>
                  <div className="space-y-1">
                    <p className="text-sm text-gray-900">
                      {t('settingsPage.flagExperimental')}: {config.features.experimentalFeatures ? t('settingsPage.enabled') : t('settingsPage.disabled')}
                    </p>
                    <p className="text-sm text-gray-900">
                      {t('settingsPage.flagRealTime')}: {config.features.realTimeUpdates ? t('settingsPage.enabled') : t('settingsPage.disabled')}
                    </p>
                    <p className="text-sm text-gray-900">
                      {t('settingsPage.flagDebug')}: {config.features.debugMode ? t('settingsPage.enabled') : t('settingsPage.disabled')}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Save Button */}
          <div className="flex justify-end pt-6 border-t">
            <button
              onClick={handleSaveSettings}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg font-semibold hover:bg-blue-700 transition"
            >
              {t('settingsPage.save')}
            </button>
          </div>
        </div>
      </main>
    </div>
  )
}
