/**
 * Request Sequencer for State Synchronization
 * 
 * Prevents algorithmic state desynchronization by:
 * - Ensuring state-changing operations are processed in order
 * - Tracking request sequence numbers
 * - Detecting and handling out-of-order responses
 * - Implementing request queueing for critical operations
 */

interface QueuedRequest {
  id: string
  sequence: number
  endpoint: string
  method: string
  data: unknown
  resolve: (value: any) => void
  reject: (reason: any) => void
  timestamp: number
}

export class RequestSequencer {
  private queue: QueuedRequest[] = []
  private currentSequence: number = 0
  private processing: boolean = false
  private maxQueueSize: number = 100
  private requestTimeout: number = 30000 // 30 seconds

  /**
   * Enqueue a state-changing request
   */
  async enqueue<T>(
    endpoint: string,
    method: string,
    data: unknown,
    executor: (req: QueuedRequest) => Promise<T>
  ): Promise<T> {
    return new Promise((resolve, reject) => {
      const request: QueuedRequest = {
        id: this.generateRequestId(),
        sequence: this.currentSequence++,
        endpoint,
        method,
        data,
        resolve,
        reject,
        timestamp: Date.now(),
      }

      if (this.queue.length >= this.maxQueueSize) {
        reject(new Error('Request queue is full'))
        return
      }

      this.queue.push(request)
      this.processQueue(executor)
    })
  }

  /**
   * Process the request queue in sequence
   */
  private async processQueue<T>(executor: (req: QueuedRequest) => Promise<T>): Promise<void> {
    if (this.processing || this.queue.length === 0) {
      return
    }

    this.processing = true

    while (this.queue.length > 0) {
      const request = this.queue.shift()!

      try {
        // Check for timeout
        if (Date.now() - request.timestamp > this.requestTimeout) {
          request.reject(new Error('Request timeout'))
          continue
        }

        // Execute the request
        const result = await executor(request)
        request.resolve(result)
      } catch (error) {
        request.reject(error)
      }
    }

    this.processing = false
  }

  /**
   * Generate unique request ID
   */
  private generateRequestId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  }

  /**
   * Get current queue size
   */
  getQueueSize(): number {
    return this.queue.length
  }

  /**
   * Clear the queue
   */
  clearQueue(): void {
    this.queue.forEach(req => {
      req.reject(new Error('Queue cleared'))
    })
    this.queue = []
    this.processing = false
  }

  /**
   * Get current sequence number
   */
  getCurrentSequence(): number {
    return this.currentSequence
  }
}

// Singleton instance
let sequencerInstance: RequestSequencer | null = null

export function getRequestSequencer(): RequestSequencer {
  if (!sequencerInstance) {
    sequencerInstance = new RequestSequencer()
  }
  return sequencerInstance
}
