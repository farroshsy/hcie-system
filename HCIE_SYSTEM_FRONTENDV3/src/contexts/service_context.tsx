/**
 * Service Context Provider
 * 
 * Provides initialized services to the application via React Context.
 * This allows components to access services without prop drilling.
 */

'use client'

import { createContext, useContext, type ReactNode } from 'react'
import { getServiceContainer, type ServiceContainer } from '@/lib/application/services'

/**
 * Service context interface
 */
interface ServiceContextValue {
  services: ServiceContainer
}

/**
 * Service context
 */
const ServiceContext = createContext<ServiceContextValue | null>(null)

/**
 * Service context provider props
 */
interface ServiceProviderProps {
  children: ReactNode
}

/**
 * Service context provider component
 */
export function ServiceProvider({ children }: ServiceProviderProps) {
  const services = getServiceContainer()

  return (
    <ServiceContext.Provider value={{ services }}>
      {children}
    </ServiceContext.Provider>
  )
}

/**
 * Hook to use service context
 */
export function useServices(): ServiceContainer {
  const context = useContext(ServiceContext)
  if (!context) {
    throw new Error('useServices must be used within ServiceProvider')
  }
  return context.services
}
