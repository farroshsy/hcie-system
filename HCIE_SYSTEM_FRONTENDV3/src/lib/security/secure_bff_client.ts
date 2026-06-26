/**
 * Secure BFF Client with State Synchronization
 * 
 * Acts as a Backend for Frontend (BFF) layer that:
 * - Sequences state-changing requests to prevent desynchronization
 * - Validates state versions before applying updates
 * - Implements idempotency for critical operations
 * - Deduplicates concurrent requests
 * - Enforces request ordering for educational progress
 */

import { getRequestSequencer } from './request_sequencer'
import { getStateVersionManager } from './state_versioning'
import { getIdempotencyManager, IdempotencyStatus } from './idempotency'
import { trackError } from '@/lib/telemetry'

interface SecureRequestOptions {
  sequence?: boolean // Enable request sequencing
  versionCheck?: { entityType: string; entityId: string; expectedVersion: number }
  idempotent?: boolean // Enable idempotency
  deduplicate?: boolean // Enable request deduplication
  ttl?: number // Time-to-live for idempotency records
}

export class SecureBFFClient {
  private baseUrl: string
  private sequencer = getRequestSequencer()
  private versionManager = getStateVersionManager()
  private idempotencyManager = getIdempotencyManager()
  private pendingRequests: Map<string, Promise<any>> = new Map()

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl
  }

  /**
   * Secure GET request
   */
  async get<T>(endpoint: string, options: SecureRequestOptions = {}): Promise<T> {
    return this.request<T>('GET', endpoint, null, options)
  }

  /**
   * Secure POST request
   */
  async post<T>(endpoint: string, data: unknown, options: SecureRequestOptions = {}): Promise<T> {
    return this.request<T>('POST', endpoint, data, options)
  }

  /**
   * Secure PUT request
   */
  async put<T>(endpoint: string, data: unknown, options: SecureRequestOptions = {}): Promise<T> {
    return this.request<T>('PUT', endpoint, data, options)
  }

  /**
   * Secure PATCH request
   */
  async patch<T>(endpoint: string, data: unknown, options: SecureRequestOptions = {}): Promise<T> {
    return this.request<T>('PATCH', endpoint, data, options)
  }

  /**
   * Secure DELETE request
   */
  async delete<T>(endpoint: string, options: SecureRequestOptions = {}): Promise<T> {
    return this.request<T>('DELETE', endpoint, null, options)
  }

  /**
   * Core request method with security features
   */
  private async request<T>(
    method: string,
    endpoint: string,
    data: unknown,
    options: SecureRequestOptions
  ): Promise<T> {
    // Generate request key for deduplication
    const requestKey = this.generateRequestKey(method, endpoint, data)

    // Check for duplicate request if deduplication is enabled
    if (options.deduplicate && this.pendingRequests.has(requestKey)) {
      return this.pendingRequests.get(requestKey)!
    }

    // Check idempotency if enabled
    if (options.idempotent) {
      const idempotencyKey = this.idempotencyManager.generateKey(method, endpoint, data as Record<string, unknown>)
      
      if (this.idempotencyManager.isDuplicate(idempotencyKey)) {
        const cached = this.idempotencyManager.getCachedResponse(idempotencyKey)
        if (cached) {
          if (cached.status === IdempotencyStatus.COMPLETED && cached.response) {
            return cached.response as T
          }
          if (cached.status === IdempotencyStatus.FAILED && cached.error) {
            throw new Error(cached.error)
          }
          if (cached.status === IdempotencyStatus.PENDING) {
            // Wait for pending request
            return this.waitForPending(idempotencyKey)
          }
        }
      }
      
      this.idempotencyManager.markPending(idempotencyKey, options.ttl)
    }

    // Validate state version if required
    if (options.versionCheck) {
      const isValid = this.versionManager.validateVersion(
        options.versionCheck.entityType,
        options.versionCheck.entityId,
        options.versionCheck.expectedVersion
      )
      
      if (!isValid) {
        const error = new Error('State version conflict')
        trackError(error, {
          context: 'state_version_mismatch',
          entityType: options.versionCheck.entityType,
          entityId: options.versionCheck.entityId,
        })
        throw error
      }
    }

    // Create request promise
    const requestPromise = this.executeRequest<T>(method, endpoint, data, options, requestKey)

    // Store for deduplication
    if (options.deduplicate) {
      this.pendingRequests.set(requestKey, requestPromise)
      requestPromise.finally(() => {
        this.pendingRequests.delete(requestKey)
      })
    }

    return requestPromise
  }

  /**
   * Execute the actual HTTP request
   */
  private async executeRequest<T>(
    method: string,
    endpoint: string,
    data: unknown,
    options: SecureRequestOptions,
    requestKey: string
  ): Promise<T> {
    const executor = async () => {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'X-Request-ID': requestKey,
        },
        credentials: 'include',
        body: data ? JSON.stringify(data) : undefined,
      })

      if (!response.ok) {
        const error = new Error(`Request failed: ${response.status} ${response.statusText}`)
        
        // Update idempotency record on failure
        if (options.idempotent) {
          const idempotencyKey = this.idempotencyManager.generateKey(method, endpoint, data as Record<string, unknown>)
          this.idempotencyManager.markFailed(idempotencyKey, error.message, options.ttl)
        }
        
        throw error
      }

      const result = await response.json()

      // Update idempotency record on success
      if (options.idempotent) {
        const idempotencyKey = this.idempotencyManager.generateKey(method, endpoint, data as Record<string, unknown>)
        this.idempotencyManager.markCompleted(idempotencyKey, result, options.ttl)
      }

      // Update state version if response contains version info
      if (result.version && options.versionCheck) {
        this.versionManager.setVersion(
          options.versionCheck.entityType,
          options.versionCheck.entityId,
          result.version
        )
      }

      return result as T
    }

    // Use sequencer if sequencing is enabled
    if (options.sequence) {
      return this.sequencer.enqueue(endpoint, method, data, executor)
    }

    return executor()
  }

  /**
   * Generate unique request key
   */
  private generateRequestKey(method: string, endpoint: string, data: unknown): string {
    const dataStr = data ? JSON.stringify(data) : ''
    return `${method}:${endpoint}:${dataStr}`
  }

  /**
   * Wait for pending idempotent request
   */
  private async waitForPending(idempotencyKey: string): Promise<any> {
    const maxWait = 10000 // 10 seconds
    const interval = 100
    let elapsed = 0

    while (elapsed < maxWait) {
      const cached = this.idempotencyManager.getCachedResponse(idempotencyKey)
      if (cached && cached.status !== IdempotencyStatus.PENDING) {
        if (cached.status === IdempotencyStatus.COMPLETED) {
          return cached.response
        }
        if (cached.status === IdempotencyStatus.FAILED) {
          throw new Error(cached.error || 'Request failed')
        }
      }
      await new Promise(resolve => setTimeout(resolve, interval))
      elapsed += interval
    }

    throw new Error('Idempotency wait timeout')
  }

  /**
   * Update state version manually
   */
  updateStateVersion(entityType: string, entityId: string, version: number): void {
    this.versionManager.setVersion(entityType, entityId, version)
  }

  /**
   * Get current state version
   */
  getStateVersion(entityType: string, entityId: string): number | null {
    const version = this.versionManager.getVersion(entityType, entityId)
    return version ? version.version : null
  }

  /**
   * Clear all security state
   */
  clearSecurityState(): void {
    this.sequencer.clearQueue()
    this.versionManager.clearAll()
    this.idempotencyManager.clearAll()
    this.pendingRequests.clear()
  }
}

// Singleton instance
let bffClientInstance: SecureBFFClient | null = null

export function createSecureBFFClient(baseUrl: string): SecureBFFClient {
  if (!bffClientInstance) {
    bffClientInstance = new SecureBFFClient(baseUrl)
  }
  return bffClientInstance
}

export function getSecureBFFClient(): SecureBFFClient {
  if (!bffClientInstance) {
    throw new Error('Secure BFF client not initialized. Call createSecureBFFClient first.')
  }
  return bffClientInstance
}
