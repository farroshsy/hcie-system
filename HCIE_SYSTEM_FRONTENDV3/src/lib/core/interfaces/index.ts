/**
 * Core Interfaces Index
 * 
 * Exports all core interface protocols for the HCIE system.
 * These interfaces define the contracts for all core business logic.
 */

// Learning Interface
export type {
  Task,
  Recommendation,
  LearningState,
  Projection,
  GovernanceMetrics,
  Progress,
  TaskSubmission,
  SubmissionResult,
  ILearningService,
  ILearningValidator,
  ILearningMapper,
  ILearningServiceFactory,
  LearningServiceConfig,
} from './learning_interface'

// Auth Interface
export type {
  User,
  AuthResponse,
  LoginCredentials,
  RegistrationData,
  TokenRefreshRequest,
  TokenRefreshResponse,
  PermissionCheck,
  IAuthService,
  IAuthValidator,
  IAuthMapper,
  IAuthServiceFactory,
  AuthServiceConfig,
} from './auth_interface'

// State Interface
export type {
  StateTransition,
  ValidationResult,
  StateSnapshot,
  PersistenceConfig,
  AuthState,
  IAuthState,
  LearningUIState,
  ILearningState,
  DashboardUIState,
  IDashboardState,
  ExperimentUIState,
  IExperimentState,
  IState,
  IStateValidator,
  IStatePersistence,
  IStateFactory,
} from './state_interface'

// Dashboard Interface
export type {
  SystemOverview,
  UserDashboardData,
  Activity,
  Achievement,
  AnalyticsData,
  LearningCurve,
  EngagementMetrics,
  PerformanceMetrics,
  DashboardWidget,
  IDashboardService,
  AnalyticsQueryParams,
  IDashboardValidator,
  IDashboardMapper,
  IDashboardServiceFactory,
  DashboardServiceConfig,
} from './dashboard_interface'

// Experiment Interface
export type {
  Experiment,
  ExperimentConfig,
  ControlGroupConfig,
  TreatmentGroupConfig,
  CohortConfig,
  ExperimentResults,
  GroupResults,
  ParticipantResult,
  StatisticalAnalysis,
  GeneratedFigure,
  ExperimentStatus,
  ExperimentListParams,
  ExperimentListResponse,
  IExperimentService,
  CreateExperimentData,
  IExperimentValidator,
  IExperimentMapper,
  IExperimentServiceFactory,
  ExperimentServiceConfig,
} from './experiment_interface'

// WebSocket Interface
export type {
  ConnectionState,
  WebSocketConfig,
  WebSocketMessage,
  ProjectionUpdateEvent,
  LearningStateUpdateEvent,
  ExperimentUpdateEvent,
  ErrorEvent,
  ConnectionEvent,
  WebSocketEvent,
  EventHandler,
  EventSubscription,
  IWebSocketService,
  ConnectionStatistics,
  IProjectionHandler,
  ILearningStateHandler,
  IExperimentHandler,
  IErrorHandler,
  IWebSocketValidator,
  IWebSocketServiceFactory,
} from './websocket_interface'
