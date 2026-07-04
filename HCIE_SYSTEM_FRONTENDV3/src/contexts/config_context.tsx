/**
 * Configuration Context Provider
 * 
 * Provides application configuration to the application via React Context.
 * This allows components to access configuration without prop drilling.
 */

'use client'

import { createContext, useContext, type ReactNode } from 'react'
import { getConfig, type AppConfig } from '@/config'

/**
 * Config context
 */
const ConfigContext = createContext<AppConfig | null>(null)

/**
 * Config context provider props
 */
interface ConfigProviderProps {
  children: ReactNode
}

/**
 * Config context provider component
 */
export function ConfigProvider({ children }: ConfigProviderProps) {
  const config = getConfig()

  return <ConfigContext.Provider value={config}>{children}</ConfigContext.Provider>
}

/**
 * Hook to use config context
 */
export function useConfig(): AppConfig {
  const context = useContext(ConfigContext)
  if (!context) {
    throw new Error('useConfig must be used within ConfigProvider')
  }
  return context
}
