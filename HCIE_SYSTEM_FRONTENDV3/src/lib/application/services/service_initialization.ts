/**
 * Service Initialization
 * 
 * NASA-grade service initialization with configuration integration.
 * Creates and configures all service instances using the factory pattern.
 */

import { getConfig } from '@/config'
import { getServiceFactory } from '@/lib/core'
import type { LearningService, AuthService, DashboardService, ExperimentService, WebSocketService } from '@/lib/core'

/**
 * Service container for initialized services
 */
export interface ServiceContainer {
  learning: LearningService
  auth: AuthService
  dashboard: DashboardService
  experiment: ExperimentService
  websocket: WebSocketService
}

/**
 * Initialize all services with configuration
 */
export function initializeServices(): ServiceContainer {
  const config = getConfig()
  const factory = getServiceFactory()

  // Initialize learning service
  const learningService = factory.learning.create({
    apiUrl: config.api.baseUrl,
    authToken: '', // Will be set after authentication
    cacheDuration: config.cache.enabled ? config.cache.defaultDuration : undefined,
    debug: config.monitoring.logLevel === 'debug',
  })

  // Initialize auth service
  const authService = factory.auth.create({
    apiUrl: config.api.baseUrl,
    tokenStorageKey: config.auth.tokenStorageKey,
    refreshTokenStorageKey: config.auth.refreshTokenStorageKey,
    userStorageKey: 'hcie_user',
    autoRefresh: config.auth.autoRefresh,
    refreshThreshold: config.auth.refreshThreshold,
    debug: config.monitoring.logLevel === 'debug',
  })

  // Initialize dashboard service
  const dashboardService = factory.dashboard.create({
    apiUrl: config.api.baseUrl,
    authToken: '', // Will be set after authentication
    cacheDuration: config.cache.enabled ? config.cache.defaultDuration : undefined,
  })

  // Initialize experiment service
  const experimentService = factory.experiment.create({
    apiUrl: config.api.baseUrl,
    authToken: '', // Will be set after authentication
    cacheDuration: config.cache.enabled ? config.cache.defaultDuration : undefined,
  })

  // Initialize WebSocket service
  const webSocketService = factory.websocket.create({
    url: config.websocket.url,
    authToken: '', // Will be set after authentication
    reconnectInterval: config.websocket.reconnectInterval,
    maxReconnectAttempts: config.websocket.maxReconnectAttempts,
    debug: config.websocket.debug,
  })

  return {
    learning: learningService,
    auth: authService,
    dashboard: dashboardService,
    experiment: experimentService,
    websocket: webSocketService,
  }
}

// Singleton instance
let serviceContainer: ServiceContainer | null = null

/**
 * Get the singleton service container
 */
export function getServiceContainer(): ServiceContainer {
  if (!serviceContainer) {
    serviceContainer = initializeServices()
  }
  return serviceContainer
}

/**
 * Reset service container (useful for testing)
 */
export function resetServiceContainer(): void {
  serviceContainer = null
}
