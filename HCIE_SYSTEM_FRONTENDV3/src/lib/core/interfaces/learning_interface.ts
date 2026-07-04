/**
 * Learning Interface Protocol
 * 
 * Defines the contract for learning-related operations in the HCIE system.
 * This protocol ensures type safety and provides clear contracts for
 * learning state management, task recommendations, and progress tracking.
 */

// ============================================================================
// Domain Types
// ============================================================================

/**
 * Represents a learning task that can be presented to a student
 */
export interface Task {
  /** Unique identifier for the task */
  task_id: string
  /** The concept or knowledge component this task addresses */
  concept: string
  /** Difficulty level (0-1, higher is more difficult) */
  difficulty: number
  /** Task content (may include math notation) */
  content: string
  /** Available options for multiple-choice tasks */
  options?: string[]
  /** Representation type of the task */
  representation: 'text' | 'mcq' | 'video_question' | 'audio_listen' | 'code'
  /** Estimated time to complete (seconds) */
  estimated_time?: number
  /** Prerequisite concepts */
  prerequisites?: string[]
}

/**
 * Represents a task recommendation with confidence
 */
export interface Recommendation {
  /** The recommended task */
  task_id: string
  /** Explanation of why this task was recommended */
  reason: string
  /** Confidence in the recommendation (0-1) */
  confidence: number
  /** Expected mastery after completing this task */
  expected_mastery: number
  /** The policy that generated this recommendation */
  policy: string
}

/**
 * Represents the current learning state of a student
 */
export interface LearningState {
  /** User identifier */
  user_id: string
  /** Current mastery levels per concept (0-1) */
  mastery: Record<string, number>
  /** Currently active task (null if no active task) */
  current_task: Task | null
  /** List of recommended tasks */
  recommendations: Recommendation[]
  /** Current projection of future state */
  projection: Projection
  /** Timestamp of last update */
  last_updated: string
  /** Total number of tasks completed */
  tasks_completed: number
  /** Current streak of correct answers */
  streak: number
}

/**
 * Represents a projection of future learning state
 */
export interface Projection {
  /** Projected mastery levels per concept */
  mastery: Record<string, number>
  /** Ensemble weights per learner */
  ensemble_weights: Record<string, number>
  /** Governance metrics */
  governance_metrics: GovernanceMetrics
  /** Timestamp of projection */
  timestamp: string
}

/**
 * Represents governance metrics from the ensemble
 */
export interface GovernanceMetrics {
  /** Constitutional weights per signal */
  constitutional_weights: Record<string, number>
  /** Volatility metric (0-1, higher is more volatile) */
  volatility: number
  /** Stability index (0-1, higher is more stable) */
  stability: number
  /** Attribution per learner */
  attribution: Record<string, number>
}

/**
 * Represents learning progress metrics
 */
export interface Progress {
  /** User identifier */
  user_id: string
  /** Total number of tasks in curriculum */
  total_tasks: number
  /** Number of tasks completed */
  completed_tasks: number
  /** Overall accuracy (0-1) */
  accuracy: number
  /** List of mastered concepts */
  concepts_mastered: string[]
  /** Total time spent learning (seconds) */
  time_spent: number
  /** Current streak */
  streak: number
  /** Longest streak achieved */
  longest_streak: number
}

/**
 * Represents a task submission
 */
export interface TaskSubmission {
  /** User identifier */
  user_id: string
  /** Task identifier */
  task_id: string
  /** Student's answer */
  answer: string | number
  /** Time taken to answer (milliseconds) */
  response_time: number
  /** Timestamp of submission */
  timestamp: string
}

/**
 * Represents the result of a task submission
 */
export interface SubmissionResult {
  /** Whether the submission was successful */
  success: boolean
  /** Whether the answer was correct */
  correct: boolean
  /** Feedback message */
  feedback: string
  /** Updated mastery levels */
  updated_mastery: Record<string, number>
  /** Next recommended task (null if no more tasks) */
  next_task: Task | null
  /** Points earned */
  points_earned: number
}

// ============================================================================
// Service Protocol
// ============================================================================

/**
 * Learning Service Protocol
 * 
 * Defines the contract for learning-related operations.
 * All implementations must adhere to this protocol.
 */
export interface ILearningService {
  /**
   * Fetch the current learning state for a user
   * @param userId - User identifier
   * @returns Promise resolving to learning state
   * @throws Error if user not found or API request fails
   */
  getLearningState(userId: string): Promise<LearningState>

  /**
   * Fetch task recommendations for a user
   * @param userId - User identifier
   * @param count - Number of recommendations to fetch (default: 5)
   * @returns Promise resolving to list of recommendations
   * @throws Error if user not found or API request fails
   */
  getRecommendations(userId: string, count?: number): Promise<Recommendation[]>

  /**
   * Submit a task answer
   * @param submission - Task submission data
   * @returns Promise resolving to submission result
   * @throws Error if submission is invalid or API request fails
   */
  submitAnswer(submission: TaskSubmission): Promise<SubmissionResult>

  /**
   * Fetch learning progress for a user
   * @param userId - User identifier
   * @returns Promise resolving to progress metrics
   * @throws Error if user not found or API request fails
   */
  getProgress(userId: string): Promise<Progress>

  /**
   * Fetch the next recommended task for a user
   * @param userId - User identifier
   * @returns Promise resolving to task with recommendation context
   * @throws Error if user not found or no tasks available
   */
  getNextTask(userId: string): Promise<{ task: Task; reason: string; confidence: number }>

  /**
   * Reset learning state for a user (admin only)
   * @param userId - User identifier
   * @returns Promise resolving when reset is complete
   * @throws Error if user not found or insufficient permissions
   */
  resetLearningState(userId: string): Promise<void>
}

// ============================================================================
// Validator Protocol
// ============================================================================

/**
 * Learning Validator Protocol
 * 
 * Defines the contract for validating learning-related data.
 */
export interface ILearningValidator {
  /**
   * Validate a task object
   * @param task - Task to validate
   * @returns Whether the task is valid
   */
  validateTask(task: unknown): task is Task

  /**
   * Validate a task submission
   * @param submission - Submission to validate
   * @returns Whether the submission is valid
   */
  validateSubmission(submission: unknown): submission is TaskSubmission

  /**
   * Validate a learning state
   * @param state - Learning state to validate
   * @returns Whether the state is valid
   */
  validateLearningState(state: unknown): state is LearningState

  /**
   * Validate a recommendation
   * @param recommendation - Recommendation to validate
   * @returns Whether the recommendation is valid
   */
  validateRecommendation(recommendation: unknown): recommendation is Recommendation
}

// ============================================================================
// Mapper Protocol
// ============================================================================

/**
 * Learning Mapper Protocol
 * 
 * Defines the contract for mapping learning data between different representations.
 */
export interface ILearningMapper {
  /**
   * Map API response to learning state
   * @param apiResponse - Raw API response
   * @returns Mapped learning state
   */
  apiToLearningState(apiResponse: unknown): LearningState

  /**
   * Map learning state to API request format
   * @param state - Learning state
   * @returns API request format
   */
  learningStateToApi(state: LearningState): Record<string, unknown>

  /**
   * Map task submission to API request format
   * @param submission - Task submission
   * @returns API request format
   */
  submissionToApi(submission: TaskSubmission): Record<string, unknown>

  /**
   * Map API response to submission result
   * @param apiResponse - Raw API response
   * @returns Mapped submission result
   */
  apiToSubmissionResult(apiResponse: unknown): SubmissionResult
}

// ============================================================================
// Factory Protocol
// ============================================================================

/**
 * Learning Service Factory Protocol
 * 
 * Defines the contract for creating learning service instances.
 */
export interface ILearningServiceFactory {
  /**
   * Create a learning service instance
   * @param config - Service configuration
   * @returns Learning service instance
   */
  create(config: LearningServiceConfig): ILearningService

  /**
   * Create a learning validator instance
   * @returns Learning validator instance
   */
  createValidator(): ILearningValidator

  /**
   * Create a learning mapper instance
   * @returns Learning mapper instance
   */
  createMapper(): ILearningMapper
}

/**
 * Learning service configuration
 */
export interface LearningServiceConfig {
  /** API base URL */
  apiUrl: string
  /** Authentication token */
  authToken: string
  /** Cache duration in milliseconds */
  cacheDuration?: number
  /** Enable debug logging */
  debug?: boolean
}
