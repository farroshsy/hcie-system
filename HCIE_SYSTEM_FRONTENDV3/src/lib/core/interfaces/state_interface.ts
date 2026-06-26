/**
 * State Management Interface Protocol
 * 
 * Defines the contract for state management operations in the HCIE system.
 * This protocol ensures type safety and provides clear contracts for
 * UI state management, state transitions, and state persistence.
 */

// ============================================================================
// Domain Types
// ============================================================================

/**
 * Represents a state transition
 */
export interface StateTransition<T> {
  /** Previous state */
  previous: T | null
  /** New state */
  current: T
  /** Transition timestamp */
  timestamp: string
  /** Transition type */
  type: string
  /** Transition metadata */
  metadata?: Record<string, unknown>
}

/**
 * Represents state validation result
 */
export interface ValidationResult {
  /** Whether the state is valid */
  valid: boolean
  /** Validation errors */
  errors: string[]
  /** Validation warnings */
  warnings: string[]
}

/**
 * Represents state snapshot for time-travel debugging
 */
export interface StateSnapshot<T> {
  /** Snapshot ID */
  id: string
  /** State data */
  state: T
  /** Snapshot timestamp */
  timestamp: string
  /** Snapshot label */
  label?: string
}

/**
 * Represents state persistence configuration
 */
export interface PersistenceConfig<T> {
  /** Storage key */
  key: string
  /** Whether to persist to localStorage */
  useLocalStorage?: boolean
  /** Whether to persist to sessionStorage */
  useSessionStorage?: boolean
  /** Partial state to persist (if not persisting entire state) */
  partialize?: (state: T) => Partial<T>
  /** Hydration function */
  hydrate?: (persisted: Partial<T>) => T
}

// ============================================================================
// Auth State Protocol
// ============================================================================

/**
 * Authentication state
 */
export interface AuthState {
  /** Current user (null if not authenticated) */
  user: User | null
  /** Access token */
  accessToken: string | null
  /** Refresh token */
  refreshToken: string | null
  /** Whether authentication is in progress */
  loading: boolean
  /** Whether user is authenticated */
  isAuthenticated: boolean
  /** Authentication error (if any) */
  error: string | null
}

/**
 * User type (simplified from auth interface)
 */
export interface User {
  id: string
  username: string
  email: string
  role: 'user' | 'student' | 'researcher' | 'admin'
  permissions: string[]
  created_at: string
}

/**
 * Auth state protocol
 */
export interface IAuthState {
  /** Current auth state */
  state: AuthState
  
  /** Set user */
  setUser(user: User | null): void
  
  /** Set access token */
  setAccessToken(token: string | null): void
  
  /** Set refresh token */
  setRefreshToken(token: string | null): void
  
  /** Set loading state */
  setLoading(loading: boolean): void
  
  /** Set error */
  setError(error: string | null): void
  
  /** Reset auth state */
  reset(): void
  
  /** Subscribe to state changes */
  subscribe(listener: (state: AuthState) => void): () => void
}

// ============================================================================
// Learning State Protocol
// ============================================================================

/**
 * Learning UI state
 */
export interface LearningUIState {
  /** Current task (null if no active task) */
  currentTask: Task | null
  /** Task loading state */
  taskLoading: boolean
  /** Task error (if any) */
  taskError: string | null
  /** Show/hide adaptation explanation */
  showAdaptationExplanation: boolean
  /** Selected recommendation (null if none selected) */
  selectedRecommendation: string | null
  /** Answer input value */
  answerInput: string
  /** Submission loading state */
  submissionLoading: boolean
  /** Submission error (if any) */
  submissionError: string | null
}

/**
 * Task type (simplified from learning interface)
 */
export interface Task {
  task_id: string
  concept: string
  difficulty: number
  content: string
  options?: string[]
  representation: 'text' | 'mcq' | 'video_question' | 'audio_listen' | 'code'
}

/**
 * Learning state protocol
 */
export interface ILearningState {
  /** Current learning UI state */
  state: LearningUIState
  
  /** Set current task */
  setCurrentTask(task: Task | null): void
  
  /** Set task loading state */
  setTaskLoading(loading: boolean): void
  
  /** Set task error */
  setTaskError(error: string | null): void
  
  /** Toggle adaptation explanation */
  toggleAdaptationExplanation(): void
  
  /** Set selected recommendation */
  setSelectedRecommendation(taskId: string | null): void
  
  /** Set answer input */
  setAnswerInput(value: string): void
  
  /** Set submission loading state */
  setSubmissionLoading(loading: boolean): void
  
  /** Set submission error */
  setSubmissionError(error: string | null): void
  
  /** Reset learning state */
  reset(): void
  
  /** Subscribe to state changes */
  subscribe(listener: (state: LearningUIState) => void): () => void
}

// ============================================================================
// Dashboard State Protocol
// ============================================================================

/**
 * Dashboard UI state
 */
export interface DashboardUIState {
  /** Selected time range for analytics */
  timeRange: '24h' | '7d' | '30d' | '90d'
  /** Selected tab */
  selectedTab: 'overview' | 'analytics' | 'experiments'
  /** Show/hide sidebar */
  sidebarOpen: boolean
  /** Refreshing state */
  refreshing: boolean
  /** Selected experiment (null if none) */
  selectedExperiment: string | null
}

/**
 * Dashboard state protocol
 */
export interface IDashboardState {
  /** Current dashboard UI state */
  state: DashboardUIState
  
  /** Set time range */
  setTimeRange(range: '24h' | '7d' | '30d' | '90d'): void
  
  /** Set selected tab */
  setSelectedTab(tab: 'overview' | 'analytics' | 'experiments'): void
  
  /** Toggle sidebar */
  toggleSidebar(): void
  
  /** Set sidebar open state */
  setSidebarOpen(open: boolean): void
  
  /** Set refreshing state */
  setRefreshing(refreshing: boolean): void
  
  /** Set selected experiment */
  setSelectedExperiment(experimentId: string | null): void
  
  /** Reset dashboard state */
  reset(): void
  
  /** Subscribe to state changes */
  subscribe(listener: (state: DashboardUIState) => void): () => void
}

// ============================================================================
// Experiment State Protocol
// ============================================================================

/**
 * Experiment UI state
 */
export interface ExperimentUIState {
  /** Experiment creation form data */
  formData: ExperimentFormData | null
  /** Form validation errors */
  formErrors: Record<string, string>
  /** Form submitting state */
  formSubmitting: boolean
  /** Selected experiment for editing */
  editingExperiment: string | null
  /** Show/hide experiment details */
  showDetails: boolean
  /** Filter status */
  filterStatus: 'all' | 'running' | 'completed' | 'paused'
}

/**
 * Experiment form data
 */
export interface ExperimentFormData {
  name: string
  description: string
  policy: string
  cohort_size: number
  duration_days: number
}

/**
 * Experiment state protocol
 */
export interface IExperimentState {
  /** Current experiment UI state */
  state: ExperimentUIState
  
  /** Set form data */
  setFormData(data: ExperimentFormData | null): void
  
  /** Set form errors */
  setFormErrors(errors: Record<string, string>): void
  
  /** Set form submitting state */
  setFormSubmitting(submitting: boolean): void
  
  /** Set editing experiment */
  setEditingExperiment(experimentId: string | null): void
  
  /** Toggle experiment details */
  toggleDetails(): void
  
  /** Set filter status */
  setFilterStatus(status: 'all' | 'running' | 'completed' | 'paused'): void
  
  /** Reset experiment state */
  reset(): void
  
  /** Subscribe to state changes */
  subscribe(listener: (state: ExperimentUIState) => void): () => void
}

// ============================================================================
// Generic State Protocol
// ============================================================================

/**
 * Generic state protocol for type-safe state management
 */
export interface IState<T> {
  /** Current state */
  state: T
  
  /** Set state */
  setState(state: T | ((previous: T) => T)): void
  
  /** Partially update state */
  partialSet(partial: Partial<T> | ((previous: T) => Partial<T>)): void
  
  /** Reset state to initial value */
  reset(): void
  
  /** Subscribe to state changes */
  subscribe(listener: (state: T) => void): () => void
  
  /** Get current state */
  getState(): T
}

/**
 * State validator protocol
 */
export interface IStateValidator<T> {
  /**
   * Validate state
   * @param state - State to validate
   * @returns Validation result
   */
  validate(state: T): ValidationResult
  
  /**
   * Validate state transition
   * @param transition - State transition to validate
   * @returns Validation result
   */
  validateTransition(transition: StateTransition<T>): ValidationResult
}

/**
 * State persistence protocol
 */
export interface IStatePersistence<T> {
  /**
   * Persist state to storage
   * @param state - State to persist
   * @param config - Persistence configuration
   */
  persist(state: T, config: PersistenceConfig<T>): void
  
  /**
   * Hydrate state from storage
   * @param config - Persistence configuration
   * @returns Hydrated state or null if not found
   */
  hydrate(config: PersistenceConfig<T>): T | null
  
  /**
   * Clear persisted state
   * @param config - Persistence configuration
   */
  clear(config: PersistenceConfig<T>): void
}

/**
 * State factory protocol
 */
export interface IStateFactory {
  /**
   * Create auth state instance
   * @param initialState - Initial state
   * @returns Auth state instance
   */
  createAuthState(initialState?: Partial<AuthState>): IAuthState
  
  /**
   * Create learning state instance
   * @param initialState - Initial state
   * @returns Learning state instance
   */
  createLearningState(initialState?: Partial<LearningUIState>): ILearningState
  
  /**
   * Create dashboard state instance
   * @param initialState - Initial state
   * @returns Dashboard state instance
   */
  createDashboardState(initialState?: Partial<DashboardUIState>): IDashboardState
  
  /**
   * Create experiment state instance
   * @param initialState - Initial state
   * @returns Experiment state instance
   */
  createExperimentState(initialState?: Partial<ExperimentUIState>): IExperimentState
  
  /**
   * Create generic state instance
   * @param initialState - Initial state
   * @returns Generic state instance
   */
  createState<T>(initialState: T): IState<T>
}
