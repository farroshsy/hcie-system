/**
 * Application Configuration
 * 
 * Central configuration management for the HCIE frontend application.
 */
import { getBackendUrl } from '@/lib/api/backend-url'

export interface AppConfig {
  environment: 'development' | 'production' | 'test'
  api: {
    baseUrl: string
    timeout: number
  }
  ui: {
    theme: 'light' | 'dark' | 'system'
    defaultLanguage: string
    animations: boolean
    accessibility: boolean
  }
  features: {
    experimentalFeatures: boolean
    realTimeUpdates: boolean
    debugMode: boolean
  }
  auth: {
    tokenExpiration: number
    refreshInterval: number
    tokenStorageKey: string
    refreshTokenStorageKey: string
    autoRefresh: boolean
    refreshThreshold: number
  }
  cache: {
    enabled: boolean
    ttl: number
    maxSize: number
    defaultDuration: number
  }
  monitoring: {
    enabled: boolean
    sampleRate: number
    logLevel: string
  }
  websocket: {
    enabled: boolean
    reconnectInterval: number
    maxRetries: number
    url: string
    maxReconnectAttempts: number
    debug: boolean
  }
}

const defaultConfig: AppConfig = {
  environment: process.env.NODE_ENV === 'production' ? 'production' : 'development',
  api: {
    baseUrl: getBackendUrl(),
    timeout: 30000,
  },
  ui: {
    theme: 'light',
    defaultLanguage: 'en',
    animations: true,
    accessibility: true,
  },
  features: {
    experimentalFeatures: false,
    realTimeUpdates: true,
    debugMode: process.env.NODE_ENV === 'development',
  },
  auth: {
    tokenExpiration: 3600,
    refreshInterval: 300,
    tokenStorageKey: 'hcie_auth_token',
    refreshTokenStorageKey: 'hcie_refresh_token',
    autoRefresh: true,
    refreshThreshold: 300,
  },
  cache: {
    enabled: true,
    ttl: 300,
    maxSize: 100,
    defaultDuration: 60,
  },
  monitoring: {
    enabled: true,
    sampleRate: 0.1,
    logLevel: 'info',
  },
  websocket: {
    enabled: true,
    reconnectInterval: 5000,
    maxRetries: 3,
    url: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8011',
    maxReconnectAttempts: 10,
    debug: process.env.NODE_ENV === 'development',
  },
}

let config: AppConfig = { ...defaultConfig }

export function getConfig(): AppConfig {
  return config
}

export function setConfig(newConfig: Partial<AppConfig>): void {
  config = { ...config, ...newConfig }
}

export function resetConfig(): void {
  config = { ...defaultConfig }
}
