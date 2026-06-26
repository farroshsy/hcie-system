/**
 * Experiment Interface Protocol
 * 
 * Defines the contract for experiment-related operations in the HCIE system.
 * This protocol ensures type safety and provides clear contracts for
 * experiment management, configuration, and monitoring.
 */

// ============================================================================
// Domain Types
// ============================================================================

/**
 * Represents an experiment
 */
export interface Experiment {
  /** Unique identifier for the experiment */
  experiment_id: string
  /** Experiment name */
  name: string
  /** Experiment description */
  description: string
  /** Experiment configuration */
  config: ExperimentConfig
  /** Experiment status */
  status: 'created' | 'running' | 'paused' | 'completed' | 'failed'
  /** Creation timestamp */
  created_at: string
  /** Start timestamp (if started) */
  started_at?: string
  /** Completion timestamp (if completed) */
  completed_at?: string
  /** Number of participants */
  participant_count: number
  /** Experiment results (if completed) */
  results?: ExperimentResults
}

/**
 * Represents experiment configuration
 */
export interface ExperimentConfig {
  /** Policy to use for adaptation */
  policy: string
  /** Policy parameters */
  parameters: Record<string, unknown>
  /** Cohort size */
  cohort_size: number
  /** Experiment duration in days */
  duration_days: number
  /** Control group configuration */
  control_group?: ControlGroupConfig
  /** Treatment group configuration */
  treatment_group?: TreatmentGroupConfig
}

/**
 * Represents control group configuration
 */
export interface ControlGroupConfig {
  /** Group identifier */
  group_id: string
  /** Policy for control group */
  policy: string
  /** Policy parameters */
  parameters: Record<string, unknown>
}

/**
 * Represents treatment group configuration
 */
export interface TreatmentGroupConfig {
  /** Group identifier */
  group_id: string
  /** Policy for treatment group */
  policy: string
  /** Policy parameters */
  parameters: Record<string, unknown>
}

/**
 * Represents cohort configuration
 */
export interface CohortConfig {
  /** Cohort identifier */
  cohort_id: string
  /** User IDs in cohort */
  user_ids: string[]
  /** Cohort metadata */
  metadata?: Record<string, unknown>
}

/**
 * Represents experiment results
 */
export interface ExperimentResults {
  /** Experiment ID */
  experiment_id: string
  /** Control group results */
  control_group: GroupResults
  /** Treatment group results */
  treatment_group: GroupResults
  /** Statistical analysis */
  statistical_analysis: StatisticalAnalysis
  /** Generated figures */
  figures: GeneratedFigure[]
  /** Completion timestamp */
  completed_at: string
}

/**
 * Represents group results
 */
export interface GroupResults {
  /** Group ID */
  group_id: string
  /** Number of participants */
  participant_count: number
  /** Average accuracy */
  avg_accuracy: number
  /** Average learning gain */
  avg_learning_gain: number
  /** Average completion rate */
  avg_completion_rate: number
  /** Individual participant results */
  participant_results: ParticipantResult[]
}

/**
 * Represents participant result
 */
export interface ParticipantResult {
  /** User ID */
  user_id: string
  /** Group ID */
  group_id: string
  /** Accuracy */
  accuracy: number
  /** Learning gain */
  learning_gain: number
  /** Tasks completed */
  tasks_completed: number
  /** Time spent (seconds) */
  time_spent: number
}

/**
 * Represents statistical analysis
 */
export interface StatisticalAnalysis {
  /** P-value for significance test */
  p_value: number
  /** Effect size (Cohen's d) */
  effect_size: number
  /** Confidence interval */
  confidence_interval: {
    lower: number
    upper: number
  }
  /** Whether results are statistically significant */
  significant: boolean
  /** Statistical test used */
  test_used: string
}

/**
 * Represents a generated figure
 */
export interface GeneratedFigure {
  /** Figure ID */
  figure_id: string
  /** Figure type */
  type: 'learning_curve' | 'ensemble_weights' | 'governance_metrics' | 'trajectory'
  /** Figure title */
  title: string
  /** Figure data URL */
  data_url: string
  /** Figure format */
  format: 'png' | 'svg' | 'pdf'
  /** Figure metadata */
  metadata?: Record<string, unknown>
}

/**
 * Represents experiment status
 */
export interface ExperimentStatus {
  /** Experiment ID */
  experiment_id: string
  /** Current status */
  status: 'created' | 'running' | 'paused' | 'completed' | 'failed'
  /** Progress percentage (0-100) */
  progress: number
  /** Current participant count */
  current_participants: number
  /** Target participant count */
  target_participants: number
  /** Estimated completion timestamp */
  estimated_completion?: string
  /** Last updated timestamp */
  last_updated: string
}

/**
 * Represents experiment list query parameters
 */
export interface ExperimentListParams {
  /** Filter by status */
  status?: 'created' | 'running' | 'paused' | 'completed' | 'failed'
  /** Page number */
  page?: number
  /** Items per page */
  limit?: number
  /** Search query */
  search?: string
}

/**
 * Represents experiment list response
 */
export interface ExperimentListResponse {
  /** List of experiments */
  experiments: Experiment[]
  /** Total count */
  total: number
  /** Current page */
  page: number
  /** Items per page */
  limit: number
}

// ============================================================================
// Service Protocol
// ============================================================================

/**
 * Experiment Service Protocol
 * 
 * Defines the contract for experiment-related operations.
 * All implementations must adhere to this protocol.
 */
export interface IExperimentService {
  /**
   * List all experiments
   * @param params - Query parameters
   * @returns Promise resolving to experiment list
   * @throws Error if API request fails
   */
  listExperiments(params?: ExperimentListParams): Promise<ExperimentListResponse>

  /**
   * Get experiment details
   * @param experimentId - Experiment identifier
   * @returns Promise resolving to experiment details
   * @throws Error if experiment not found or API request fails
   */
  getExperiment(experimentId: string): Promise<Experiment>

  /**
   * Create a new experiment
   * @param data - Experiment creation data
   * @returns Promise resolving to created experiment
   * @throws Error if creation fails or API request fails
   */
  createExperiment(data: CreateExperimentData): Promise<{ experiment_id: string; status: string }>

  /**
   * Update experiment configuration
   * @param experimentId - Experiment identifier
   * @param updates - Configuration updates
   * @returns Promise resolving to updated experiment
   * @throws Error if update fails or API request fails
   */
  updateExperiment(experimentId: string, updates: Partial<ExperimentConfig>): Promise<{ experiment_id: string; updated_at: string }>

  /**
   * Start an experiment
   * @param experimentId - Experiment identifier
   * @returns Promise resolving to experiment status
   * @throws Error if start fails or API request fails
   */
  startExperiment(experimentId: string): Promise<{ experiment_id: string; status: string; started_at: string }>

  /**
   * Pause an experiment
   * @param experimentId - Experiment identifier
   * @returns Promise resolving to experiment status
   * @throws Error if pause fails or API request fails
   */
  pauseExperiment(experimentId: string): Promise<{ experiment_id: string; status: string; paused_at: string }>

  /**
   * Stop an experiment
   * @param experimentId - Experiment identifier
   * @returns Promise resolving to experiment status
   * @throws Error if stop fails or API request fails
   */
  stopExperiment(experimentId: string): Promise<{ experiment_id: string; status: string; stopped_at: string }>

  /**
   * Delete an experiment
   * @param experimentId - Experiment identifier
   * @returns Promise resolving when deleted
   * @throws Error if deletion fails or API request fails
   */
  deleteExperiment(experimentId: string): Promise<{ message: string }>

  /**
   * Get experiment status
   * @param experimentId - Experiment identifier
   * @returns Promise resolving to experiment status
   * @throws Error if experiment not found or API request fails
   */
  getExperimentStatus(experimentId: string): Promise<ExperimentStatus>

  /**
   * Get experiment results
   * @param experimentId - Experiment identifier
   * @returns Promise resolving to experiment results
   * @throws Error if results not available or API request fails
   */
  getExperimentResults(experimentId: string): Promise<ExperimentResults>

  /**
   * Generate figures for experiment
   * @param experimentId - Experiment identifier
   * @param figureTypes - Types of figures to generate
   * @returns Promise resolving to generated figures
   * @throws Error if figure generation fails or API request fails
   */
  generateFigures(experimentId: string, figureTypes: string[]): Promise<GeneratedFigure[]>

  /**
   * Download figure
   * @param figureId - Figure identifier
   * @param format - Download format
   * @returns Promise resolving to figure data URL
   * @throws Error if figure not found or API request fails
   */
  downloadFigure(figureId: string, format?: 'png' | 'svg' | 'pdf'): Promise<string>
}

/**
 * Experiment creation data
 */
export interface CreateExperimentData {
  /** Experiment name */
  name: string
  /** Experiment description */
  description: string
  /** Experiment configuration */
  config: ExperimentConfig
  /** Cohort configuration */
  cohort: CohortConfig
}

// ============================================================================
// Validator Protocol
// ============================================================================

/**
 * Experiment Validator Protocol
 * 
 * Defines the contract for validating experiment-related data.
 */
export interface IExperimentValidator {
  /**
   * Validate experiment configuration
   * @param config - Configuration to validate
   * @returns Whether the configuration is valid
   */
  validateConfig(config: unknown): config is ExperimentConfig

  /**
   * Validate experiment creation data
   * @param data - Data to validate
   * @returns Whether the data is valid
   */
  validateCreateData(data: unknown): data is CreateExperimentData

  /**
   * Validate experiment
   * @param experiment - Experiment to validate
   * @returns Whether the experiment is valid
   */
  validateExperiment(experiment: unknown): experiment is Experiment

  /**
   * Validate cohort configuration
   * @param cohort - Cohort to validate
   * @returns Whether the cohort is valid
   */
  validateCohort(cohort: unknown): cohort is CohortConfig
}

// ============================================================================
// Mapper Protocol
// ============================================================================

/**
 * Experiment Mapper Protocol
 * 
 * Defines the contract for mapping experiment data between different representations.
 */
export interface IExperimentMapper {
  /**
   * Map API response to experiment
   * @param apiResponse - Raw API response
   * @returns Mapped experiment
   */
  apiToExperiment(apiResponse: unknown): Experiment

  /**
   * Map experiment creation data to API request format
   * @param data - Creation data
   * @returns API request format
   */
  createDataToApi(data: CreateExperimentData): Record<string, unknown>

  /**
   * Map experiment config to API request format
   * @param config - Configuration
   * @returns API request format
   */
  configToApi(config: ExperimentConfig): Record<string, unknown>

  /**
   * Map API response to experiment results
   * @param apiResponse - Raw API response
   * @returns Mapped experiment results
   */
  apiToExperimentResults(apiResponse: unknown): ExperimentResults

  /**
   * Map API response to experiment list
   * @param apiResponse - Raw API response
   * @returns Mapped experiment list
   */
  apiToExperimentList(apiResponse: unknown): ExperimentListResponse
}

// ============================================================================
// Factory Protocol
// ============================================================================

/**
 * Experiment Service Factory Protocol
 * 
 * Defines the contract for creating experiment service instances.
 */
export interface IExperimentServiceFactory {
  /**
   * Create an experiment service instance
   * @param config - Service configuration
   * @returns Experiment service instance
   */
  create(config: ExperimentServiceConfig): IExperimentService

  /**
   * Create an experiment validator instance
   * @returns Experiment validator instance
   */
  createValidator(): IExperimentValidator

  /**
   * Create an experiment mapper instance
   * @returns Experiment mapper instance
   */
  createMapper(): IExperimentMapper
}

/**
 * Experiment service configuration
 */
export interface ExperimentServiceConfig {
  /** API base URL */
  apiUrl: string
  /** Authentication token */
  authToken: string
  /** Cache duration in milliseconds */
  cacheDuration?: number
  /** Enable real-time updates */
  enableRealtime?: boolean
  /** WebSocket URL for real-time updates */
  wsUrl?: string
  /** Enable debug logging */
  debug?: boolean
}
