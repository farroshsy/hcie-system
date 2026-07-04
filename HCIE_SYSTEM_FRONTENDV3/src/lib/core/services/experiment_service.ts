/**
 * Experiment Service Implementation
 * 
 * Implements the IExperimentService protocol for experiment-related operations.
 * This service handles experiment management, configuration, and monitoring.
 */

import type {
  IExperimentService,
  ExperimentServiceConfig,
  Experiment,
  ExperimentConfig,
  ExperimentStatus,
  ExperimentResults,
  ExperimentListParams,
  ExperimentListResponse,
  CreateExperimentData,
  GeneratedFigure,
} from '../interfaces'

/**
 * Experiment Service Implementation
 */
export class ExperimentService implements IExperimentService {
  private apiUrl: string
  private authToken: string
  private cacheDuration: number
  private enableRealtime: boolean
  private wsUrl: string | undefined
  private debug: boolean
  private cache: Map<string, { data: unknown; timestamp: number }>

  constructor(config: ExperimentServiceConfig) {
    this.apiUrl = config.apiUrl
    this.authToken = config.authToken
    this.cacheDuration = config.cacheDuration || 5 * 60 * 1000 // 5 minutes default
    this.enableRealtime = config.enableRealtime || false
    this.wsUrl = config.wsUrl
    this.debug = config.debug || false
    this.cache = new Map()
  }

  /**
   * List all experiments
   */
  async listExperiments(params?: ExperimentListParams): Promise<ExperimentListResponse> {
    const cacheKey = `experiments-${JSON.stringify(params || {})}`
    const cached = this.getFromCache(cacheKey)
    
    if (cached) {
      this.log('Cache hit for experiments list')
      return cached as ExperimentListResponse
    }

    this.log('Fetching experiments list with params:', params)
    
    try {
      const queryParams = new URLSearchParams()
      
      if (params?.status) {
        queryParams.append('status', params.status)
      }
      
      if (params?.page) {
        queryParams.append('page', params.page.toString())
      }
      
      if (params?.limit) {
        queryParams.append('limit', params.limit.toString())
      }
      
      if (params?.search) {
        queryParams.append('search', params.search)
      }

      const queryString = queryParams.toString()
      const response = await fetch(`${this.apiUrl}/experiments${queryString ? `?${queryString}` : ''}`, {
        headers: {
          'Authorization': `Bearer ${this.authToken}`,
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`Failed to fetch experiments: ${response.statusText}`)
      }

      const data = await response.json()
      this.setCache(cacheKey, data)
      
      return data as ExperimentListResponse
    } catch (error) {
      this.log('Error fetching experiments list:', error)
      throw new Error(`Unable to fetch experiments: ${error instanceof Error ? error.message : String(error)}`)
    }
  }

  /**
   * Get experiment details
   */
  async getExperiment(experimentId: string): Promise<Experiment> {
    const cacheKey = `experiment-${experimentId}`
    const cached = this.getFromCache(cacheKey)
    
    if (cached) {
      this.log('Cache hit for experiment:', experimentId)
      return cached as Experiment
    }

    this.log('Fetching experiment details:', experimentId)
    
    try {
      const response = await fetch(`${this.apiUrl}/experiments/${experimentId}`, {
        headers: {
          'Authorization': `Bearer ${this.authToken}`,
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`Failed to fetch experiment: ${response.statusText}`)
      }

      const data = await response.json()
      this.setCache(cacheKey, data)
      
      return data as Experiment
    } catch (error) {
      this.log('Error fetching experiment:', error)
      throw new Error(`Unable to fetch experiment: ${error instanceof Error ? error.message : String(error)}`)
    }
  }

  /**
   * Create a new experiment
   */
  async createExperiment(data: CreateExperimentData): Promise<{ experiment_id: string; status: string }> {
    this.log('Creating experiment:', data.name)
    
    try {
      const response = await fetch(`${this.apiUrl}/experiments`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.authToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      })

      if (!response.ok) {
        throw new Error(`Failed to create experiment: ${response.statusText}`)
      }

      const result = await response.json()
      
      // Invalidate experiments list cache
      this.invalidateCache('experiments-')
      
      return result as { experiment_id: string; status: string }
    } catch (error) {
      this.log('Error creating experiment:', error)
      throw new Error(`Unable to create experiment: ${error instanceof Error ? error.message : String(error)}`)
    }
  }

  /**
   * Update experiment configuration
   */
  async updateExperiment(experimentId: string, updates: Partial<ExperimentConfig>): Promise<{ experiment_id: string; updated_at: string }> {
    this.log('Updating experiment:', experimentId)
    
    try {
      const response = await fetch(`${this.apiUrl}/experiments/${experimentId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${this.authToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updates),
      })

      if (!response.ok) {
        throw new Error(`Failed to update experiment: ${response.statusText}`)
      }

      const result = await response.json()
      
      // Invalidate caches
      this.invalidateCache(`experiment-${experimentId}`)
      this.invalidateCache('experiments-')
      
      return result as { experiment_id: string; updated_at: string }
    } catch (error) {
      this.log('Error updating experiment:', error)
      throw new Error(`Unable to update experiment: ${error instanceof Error ? error.message : String(error)}`)
    }
  }

  /**
   * Start an experiment
   */
  async startExperiment(experimentId: string): Promise<{ experiment_id: string; status: string; started_at: string }> {
    this.log('Starting experiment:', experimentId)
    
    try {
      const response = await fetch(`${this.apiUrl}/experiments/${experimentId}/start`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.authToken}`,
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`Failed to start experiment: ${response.statusText}`)
      }

      const result = await response.json()
      
      // Invalidate caches
      this.invalidateCache(`experiment-${experimentId}`)
      this.invalidateCache('experiments-')
      
      return result as { experiment_id: string; status: string; started_at: string }
    } catch (error) {
      this.log('Error starting experiment:', error)
      throw new Error(`Unable to start experiment: ${error instanceof Error ? error.message : String(error)}`)
    }
  }

  /**
   * Pause an experiment
   */
  async pauseExperiment(experimentId: string): Promise<{ experiment_id: string; status: string; paused_at: string }> {
    this.log('Pausing experiment:', experimentId)
    
    try {
      const response = await fetch(`${this.apiUrl}/experiments/${experimentId}/pause`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.authToken}`,
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`Failed to pause experiment: ${response.statusText}`)
      }

      const result = await response.json()
      
      // Invalidate caches
      this.invalidateCache(`experiment-${experimentId}`)
      this.invalidateCache('experiments-')
      
      return result as { experiment_id: string; status: string; paused_at: string }
    } catch (error) {
      this.log('Error pausing experiment:', error)
      throw new Error(`Unable to pause experiment: ${error instanceof Error ? error.message : String(error)}`)
    }
  }

  /**
   * Stop an experiment
   */
  async stopExperiment(experimentId: string): Promise<{ experiment_id: string; status: string; stopped_at: string }> {
    this.log('Stopping experiment:', experimentId)
    
    try {
      const response = await fetch(`${this.apiUrl}/experiments/${experimentId}/stop`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.authToken}`,
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`Failed to stop experiment: ${response.statusText}`)
      }

      const result = await response.json()
      
      // Invalidate caches
      this.invalidateCache(`experiment-${experimentId}`)
      this.invalidateCache('experiments-')
      
      return result as { experiment_id: string; status: string; stopped_at: string }
    } catch (error) {
      this.log('Error stopping experiment:', error)
      throw new Error(`Unable to stop experiment: ${error instanceof Error ? error.message : String(error)}`)
    }
  }

  /**
   * Delete an experiment
   */
  async deleteExperiment(experimentId: string): Promise<{ message: string }> {
    this.log('Deleting experiment:', experimentId)
    
    try {
      const response = await fetch(`${this.apiUrl}/experiments/${experimentId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${this.authToken}`,
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`Failed to delete experiment: ${response.statusText}`)
      }

      const result = await response.json()
      
      // Invalidate caches
      this.invalidateCache(`experiment-${experimentId}`)
      this.invalidateCache('experiments-')
      
      return result as { message: string }
    } catch (error) {
      this.log('Error deleting experiment:', error)
      throw new Error(`Unable to delete experiment: ${error instanceof Error ? error.message : String(error)}`)
    }
  }

  /**
   * Get experiment status
   */
  async getExperimentStatus(experimentId: string): Promise<ExperimentStatus> {
    const cacheKey = `experiment-status-${experimentId}`
    const cached = this.getFromCache(cacheKey)
    
    if (cached) {
      this.log('Cache hit for experiment status:', experimentId)
      return cached as ExperimentStatus
    }

    this.log('Fetching experiment status:', experimentId)
    
    try {
      const response = await fetch(`${this.apiUrl}/experiments/${experimentId}/status`, {
        headers: {
          'Authorization': `Bearer ${this.authToken}`,
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`Failed to fetch experiment status: ${response.statusText}`)
      }

      const data = await response.json()
      this.setCache(cacheKey, data)
      
      return data as ExperimentStatus
    } catch (error) {
      this.log('Error fetching experiment status:', error)
      throw new Error(`Unable to fetch experiment status: ${error instanceof Error ? error.message : String(error)}`)
    }
  }

  /**
   * Get experiment results
   */
  async getExperimentResults(experimentId: string): Promise<ExperimentResults> {
    const cacheKey = `experiment-results-${experimentId}`
    const cached = this.getFromCache(cacheKey)
    
    if (cached) {
      this.log('Cache hit for experiment results:', experimentId)
      return cached as ExperimentResults
    }

    this.log('Fetching experiment results:', experimentId)
    
    try {
      const response = await fetch(`${this.apiUrl}/experiments/${experimentId}/results`, {
        headers: {
          'Authorization': `Bearer ${this.authToken}`,
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`Failed to fetch experiment results: ${response.statusText}`)
      }

      const data = await response.json()
      this.setCache(cacheKey, data)
      
      return data as ExperimentResults
    } catch (error) {
      this.log('Error fetching experiment results:', error)
      throw new Error(`Unable to fetch experiment results: ${error instanceof Error ? error.message : String(error)}`)
    }
  }

  /**
   * Generate figures for experiment
   */
  async generateFigures(experimentId: string, figureTypes: string[]): Promise<GeneratedFigure[]> {
    this.log('Generating figures for experiment:', experimentId, 'types:', figureTypes)
    
    try {
      const response = await fetch(`${this.apiUrl}/experiments/${experimentId}/figures`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.authToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ figure_types: figureTypes }),
      })

      if (!response.ok) {
        throw new Error(`Failed to generate figures: ${response.statusText}`)
      }

      const data = await response.json()
      
      return data as GeneratedFigure[]
    } catch (error) {
      this.log('Error generating figures:', error)
      throw new Error(`Unable to generate figures: ${error instanceof Error ? error.message : String(error)}`)
    }
  }

  /**
   * Download figure
   */
  async downloadFigure(figureId: string, format: 'png' | 'svg' | 'pdf' = 'png'): Promise<string> {
    this.log('Downloading figure:', figureId, 'format:', format)
    
    try {
      const response = await fetch(`${this.apiUrl}/experiments/figures/${figureId}?format=${format}`, {
        headers: {
          'Authorization': `Bearer ${this.authToken}`,
        },
      })

      if (!response.ok) {
        throw new Error(`Failed to download figure: ${response.statusText}`)
      }

      const blob = await response.blob()
      return URL.createObjectURL(blob)
    } catch (error) {
      this.log('Error downloading figure:', error)
      throw new Error(`Unable to download figure: ${error instanceof Error ? error.message : String(error)}`)
    }
  }

  /**
   * Get data from cache if not expired
   */
  private getFromCache(key: string): unknown | null {
    const cached = this.cache.get(key)
    if (!cached) return null
    
    const now = Date.now()
    if (now - cached.timestamp > this.cacheDuration) {
      this.cache.delete(key)
      return null
    }
    
    return cached.data
  }

  /**
   * Set data in cache
   */
  private setCache(key: string, data: unknown): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
    })
  }

  /**
   * Invalidate cache entry
   */
  private invalidateCache(key: string): void {
    // Delete all keys that start with the given key
    for (const cacheKey of this.cache.keys()) {
      if (cacheKey.startsWith(key)) {
        this.cache.delete(cacheKey)
      }
    }
  }

  /**
   * Clear all cache
   */
  clearCache(): void {
    this.cache.clear()
  }

  /**
   * Debug logging
   */
  private log(...args: unknown[]): void {
    if (this.debug) {
      console.log('[ExperimentService]', ...args)
    }
  }
}
