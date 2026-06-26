/**
 * Admin Navigation Component
 * 
 * Navigation bar for admin dashboard screens.
 */

'use client'

import { useState } from 'react'
import type { ReactNode } from 'react'

type AdminScreen = 'home' | 'experiments' | 'replay' | 'cold-start' | 'analytics' | 'users' | 'settings'

interface AdminNavigationProps {
  currentScreen: AdminScreen
  onNavigate: (screen: AdminScreen) => void
  children: ReactNode
}

export function AdminNavigation({ currentScreen, onNavigate, children }: AdminNavigationProps) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

  const navItems = [
    { id: 'home' as AdminScreen, label: 'Dashboard', icon: '🏠' },
    { id: 'experiments' as AdminScreen, label: 'Experiments', icon: '🧪' },
    { id: 'replay' as AdminScreen, label: 'Replay', icon: '🔄' },
    { id: 'cold-start' as AdminScreen, label: 'Cold Start', icon: '❄️' },
    { id: 'analytics' as AdminScreen, label: 'Analytics', icon: '📊' },
    { id: 'users' as AdminScreen, label: 'Users', icon: '👥' },
    { id: 'settings' as AdminScreen, label: 'Settings', icon: '⚙️' },
  ]

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar - Desktop */}
      <aside className="hidden md:flex flex-col w-64 bg-white shadow-lg">
        <div className="p-6 border-b">
          <h1 className="text-2xl font-bold text-blue-600">HCIE Admin</h1>
        </div>
        <nav className="flex-1 p-4 space-y-2">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition ${
                currentScreen === item.id
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              <span className="text-xl">{item.icon}</span>
              <span className="font-medium">{item.label}</span>
            </button>
          ))}
        </nav>
        <div className="p-4 border-t">
          <button className="w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-gray-700 hover:bg-gray-100 transition">
            <span className="text-xl">🚪</span>
            <span className="font-medium">Exit Admin</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Mobile Header */}
        <header className="md:hidden bg-white shadow-sm p-4 flex justify-between items-center">
          <h1 className="text-xl font-bold text-blue-600">HCIE Admin</h1>
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="text-gray-700"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {isMobileMenuOpen ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              )}
            </svg>
          </button>
        </header>

        {/* Mobile Navigation */}
        {isMobileMenuOpen && (
          <nav className="md:hidden bg-white shadow-md p-4 space-y-2">
            {navItems.map((item) => (
              <button
                key={item.id}
                onClick={() => {
                  onNavigate(item.id)
                  setIsMobileMenuOpen(false)
                }}
                className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition ${
                  currentScreen === item.id
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                <span className="text-xl">{item.icon}</span>
                <span className="font-medium">{item.label}</span>
              </button>
            ))}
          </nav>
        )}

        {/* Content */}
        <main className="flex-1 overflow-auto">{children}</main>
      </div>
    </div>
  )
}
