/**
 * State Versioning for Synchronization
 * 
 * Prevents state desynchronization by:
 * - Tracking state versions for each entity
 * - Validating state versions before applying updates
 * - Detecting and handling version conflicts
 * - Implementing optimistic concurrency control
 */

export interface StateVersion {
  entityType: string
  entityId: string
  version: number
  lastModified: number
}

export class StateVersionManager {
  private versions: Map<string, StateVersion> = new Map()
  private pendingUpdates: Map<string, number> = new Map()

  /**
   * Get state version for an entity
   */
  getVersion(entityType: string, entityId: string): StateVersion | null {
    const key = this.getKey(entityType, entityId)
    return this.versions.get(key) || null
  }

  /**
   * Set state version for an entity
   */
  setVersion(entityType: string, entityId: string, version: number, lastModified?: number): void {
    const key = this.getKey(entityType, entityId)
    this.versions.set(key, {
      entityType,
      entityId,
      version,
      lastModified: lastModified || Date.now(),
    })
  }

  /**
   * Validate state version before update
   */
  validateVersion(entityType: string, entityId: string, expectedVersion: number): boolean {
    const current = this.getVersion(entityType, entityId)
    if (!current) return true // No version yet, allow
    return current.version === expectedVersion
  }

  /**
   * Increment state version
   */
  incrementVersion(entityType: string, entityId: string): number {
    const current = this.getVersion(entityType, entityId)
    const newVersion = current ? current.version + 1 : 1
    this.setVersion(entityType, entityId, newVersion)
    return newVersion
  }

  /**
   * Mark update as pending
   */
  markPending(entityType: string, entityId: string): void {
    const key = this.getKey(entityType, entityId)
    this.pendingUpdates.set(key, Date.now())
  }

  /**
   * Clear pending update
   */
  clearPending(entityType: string, entityId: string): void {
    const key = this.getKey(entityType, entityId)
    this.pendingUpdates.delete(key)
  }

  /**
   * Check if update is pending
   */
  isPending(entityType: string, entityId: string): boolean {
    const key = this.getKey(entityType, entityId)
    return this.pendingUpdates.has(key)
  }

  /**
   * Clear all versions
   */
  clearAll(): void {
    this.versions.clear()
    this.pendingUpdates.clear()
  }

  /**
   * Generate version key
   */
  private getKey(entityType: string, entityId: string): string {
    return `${entityType}:${entityId}`
  }
}

// Singleton instance
let versionManagerInstance: StateVersionManager | null = null

export function getStateVersionManager(): StateVersionManager {
  if (!versionManagerInstance) {
    versionManagerInstance = new StateVersionManager()
  }
  return versionManagerInstance
}
