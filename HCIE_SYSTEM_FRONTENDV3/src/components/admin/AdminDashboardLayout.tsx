/**
 * Admin Dashboard Layout
 * 
 * Main layout component for the admin dashboard.
 * Integrates navigation with admin screens.
 */

'use client'

import { useState } from 'react'
import { AdminNavigation } from './AdminNavigation'
import AdminHomeScreen from './AdminHome'
import ExperimentsScreen from './ExperimentsScreen'
import AnalyticsScreen from './AnalyticsScreen'
import UsersScreen from './UsersScreen'
import AdminSettingsScreen from './AdminSettingsScreen'

type AdminScreen = 'home' | 'experiments' | 'replay' | 'cold-start' | 'analytics' | 'users' | 'settings'

export function AdminDashboardLayout() {
  const [currentScreen, setCurrentScreen] = useState<AdminScreen>('home')

  const renderScreen = () => {
    switch (currentScreen) {
      case 'home':
        return <AdminHomeScreen />
      case 'experiments':
        return <ExperimentsScreen />
      case 'replay':
        return <AdminHomeScreen /> // TODO: Create ReplayScreen
      case 'cold-start':
        return <AdminHomeScreen /> // TODO: Create ColdStartScreen
      case 'analytics':
        return <AnalyticsScreen />
      case 'users':
        return <UsersScreen />
      case 'settings':
        return <AdminSettingsScreen />
      default:
        return <AdminHomeScreen />
    }
  }

  return (
    <AdminNavigation currentScreen={currentScreen} onNavigate={setCurrentScreen}>
      {renderScreen()}
    </AdminNavigation>
  )
}
