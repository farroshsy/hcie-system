/**
 * Idempotency Key Management
 * 
 * Prevents duplicate request execution by:
 * - Generating unique idempotency keys for critical operations
 * - Tracking request status (pending, completed, failed)
 * - Returning cached responses for duplicate requests
 * - Expiring old idempotency records
 */

export enum IdempotencyStatus {
  PENDING = 'pending',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

export interface IdempotencyRecord {
  key: string
  status: IdempotencyStatus
  response?: unknown
  error?: string
  timestamp: number
  expiresAt: number
}

export class IdempotencyManager {
  private records: Map<string, IdempotencyRecord> = new Map()
  private defaultTTL: number = 60000 // 1 minute

  /**
   * Generate idempotency key
   */
  generateKey(method: string, endpoint: string, data: Record<string, unknown>): string {
    const sortedParams = Object.keys(data)
      .sort((a, b) => a.localeCompare(b))
      .map(key => `${key}:${JSON.stringify(data[key])}`)
      .join('|')
    return `${method}:${endpoint}:${sortedParams}`
  }

  /**
   * Check if request is duplicate
   */
  isDuplicate(key: string): boolean {
    const record = this.records.get(key)
    if (!record) return false
    
    // Check if expired
    if (Date.now() > record.expiresAt) {
      this.records.delete(key)
      return false
    }
    
    return true
  }

  /**
   * Get cached response for duplicate request
   */
  getCachedResponse(key: string): { response?: unknown; error?: string; status: IdempotencyStatus } | null {
    const record = this.records.get(key)
    if (!record) return null
    
    if (Date.now() > record.expiresAt) {
      this.records.delete(key)
      return null
    }
    
    return {
      response: record.response,
      error: record.error,
      status: record.status,
    }
  }

  /**
   * Mark request as pending
   */
  markPending(key: string, ttl?: number): void {
    this.records.set(key, {
      key,
      status: IdempotencyStatus.PENDING,
      timestamp: Date.now(),
      expiresAt: Date.now() + (ttl || this.defaultTTL),
    })
  }

  /**
   * Mark request as completed with response
   */
  markCompleted(key: string, response: unknown, ttl?: number): void {
    const record = this.records.get(key)
    if (record) {
      record.status = IdempotencyStatus.COMPLETED
      record.response = response
      record.expiresAt = Date.now() + (ttl || this.defaultTTL)
    }
  }

  /**
   * Mark request as failed with error
   */
  markFailed(key: string, error: string, ttl?: number): void {
    const record = this.records.get(key)
    if (record) {
      record.status = IdempotencyStatus.FAILED
      record.error = error
      record.expiresAt = Date.now() + (ttl || this.defaultTTL)
    }
  }

  /**
   * Clear expired records
   */
  clearExpired(): void {
    const now = Date.now()
    for (const [key, record] of this.records.entries()) {
      if (now > record.expiresAt) {
        this.records.delete(key)
      }
    }
  }

  /**
   * Clear all records
   */
  clearAll(): void {
    this.records.clear()
  }

  /**
   * Get record count
   */
  getRecordCount(): number {
    return this.records.size
  }
}

// Singleton instance
let idempotencyManagerInstance: IdempotencyManager | null = null

export function getIdempotencyManager(): IdempotencyManager {
  if (!idempotencyManagerInstance) {
    idempotencyManagerInstance = new IdempotencyManager()
  }
  return idempotencyManagerInstance
}
