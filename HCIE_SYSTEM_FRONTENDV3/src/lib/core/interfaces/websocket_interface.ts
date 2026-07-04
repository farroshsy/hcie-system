/**
 * WebSocket Interface Protocol
 * 
 * Defines the contract for WebSocket-related operations in the HCIE system.
 * This protocol ensures type safety and provides clear contracts for
 * real-time communication, event handling, and connection management.
 */

// ============================================================================
// Domain Types
// ============================================================================

/**
 * Represents WebSocket connection state
 */
export type ConnectionState = 'connecting' | 'connected' | 'disconnected' | 'error'

/**
 * Represents WebSocket configuration
 */
export interface WebSocketConfig {
  /** WebSocket server URL */
  url: string
  /** Authentication token */
  authToken: string
  /** Reconnection interval (milliseconds) */
  reconnectInterval?: number
  /** Maximum reconnection attempts */
  maxReconnectAttempts?: number
  /** Enable debug logging */
  debug?: boolean
}

/**
 * Represents a WebSocket message
 */
export interface WebSocketMessage<T = unknown> {
  /** Message type */
  type: string
  /** Message payload */
  data: T
  /** Message timestamp */
  timestamp: string
  /** Message ID (for correlation) */
  id?: string
}

/**
 * Represents projection update event
 */
export interface ProjectionUpdateEvent {
  /** User ID */
  user_id: string
  /** Updated projection */
  projection: {
    mastery: Record<string, number>
    ensemble_weights: Record<string, number>
    governance_metrics: {
      constitutional_weights: Record<string, number>
      volatility: number
      stability: number
      attribution: Record<string, number>
    }
    timestamp: string
  }
}

/**
 * Represents learning state update event
 */
export interface LearningStateUpdateEvent {
  /** User ID */
  user_id: string
  /** Updated learning state */
  learning_state: {
    user_id: string
    mastery: Record<string, number>
    current_task: unknown | null
    recommendations: unknown[]
    projection: unknown
    last_updated: string
  }
}

/**
 * Represents experiment update event
 */
export interface ExperimentUpdateEvent {
  /** Experiment ID */
  experiment_id: string
  /** Experiment status */
  status: 'created' | 'running' | 'paused' | 'completed' | 'failed'
  /** Progress percentage */
  progress: number
  /** Timestamp */
  timestamp: string
}

/**
 * Represents error event
 */
export interface ErrorEvent {
  /** Error message */
  message: string
  /** Error code */
  code: string
  /** Error details */
  details?: Record<string, unknown>
  /** Timestamp */
  timestamp: string
}

/**
 * Represents connection event
 */
export interface ConnectionEvent {
  /** Connection state */
  state: ConnectionState
  /** User ID (if connected) */
  user_id?: string
  /** Timestamp */
  timestamp: string
}

/**
 * Type union for all WebSocket events
 */
export type WebSocketEvent = 
  | ProjectionUpdateEvent
  | LearningStateUpdateEvent
  | ExperimentUpdateEvent
  | ErrorEvent
  | ConnectionEvent

/**
 * Represents event handler
 */
export type EventHandler<T = unknown> = (event: T) => void

/**
 * Represents event subscription
 */
export interface EventSubscription {
  /** Event type */
  eventType: string
  /** Handler function */
  handler: EventHandler
  /** Unsubscribe function */
  unsubscribe: () => void
}

// ============================================================================
// Service Protocol
// ============================================================================

/**
 * WebSocket Service Protocol
 * 
 * Defines the contract for WebSocket-related operations.
 * All implementations must adhere to this protocol.
 */
export interface IWebSocketService {
  /**
   * Connect to WebSocket server
   * @param userId - User identifier
   * @returns Promise resolving when connected
   * @throws Error if connection fails
   */
  connect(userId: string): Promise<void>

  /**
   * Disconnect from WebSocket server
   * @returns Promise resolving when disconnected
   */
  disconnect(): Promise<void>

  /**
   * Get current connection state
   * @returns Current connection state
   */
  getConnectionState(): ConnectionState

  /**
   * Check if connected
   * @returns Whether currently connected
   */
  isConnected(): boolean

  /**
   * Send a message to the server
   * @param message - Message to send
   * @returns Promise resolving when message is sent
   * @throws Error if not connected or send fails
   */
  send<T = unknown>(message: WebSocketMessage<T>): Promise<void>

  /**
   * Subscribe to an event type
   * @param eventType - Event type to subscribe to
   * @param handler - Event handler function
   * @returns Unsubscribe function
   */
  subscribe<T = unknown>(eventType: string, handler: EventHandler<T>): () => void

  /**
   * Subscribe to all events
   * @param handler - Event handler function
   * @returns Unsubscribe function
   */
  subscribeAll(handler: EventHandler<WebSocketEvent>): () => void

  /**
   * Unsubscribe from an event type
   * @param eventType - Event type to unsubscribe from
   * @param handler - Event handler function
   */
  unsubscribe(eventType: string, handler: EventHandler): void

  /**
   * Clear all event subscriptions
   */
  clearSubscriptions(): void

  /**
   * Get connection statistics
   * @returns Connection statistics
   */
  getStatistics(): ConnectionStatistics
}

/**
 * Represents connection statistics
 */
export interface ConnectionStatistics {
  /** Connection state */
  state: ConnectionState
  /** Number of reconnection attempts */
  reconnectAttempts: number
  /** Time since last connection (milliseconds) */
  timeSinceLastConnection: number
  /** Number of messages received */
  messagesReceived: number
  /** Number of messages sent */
  messagesSent: number
  /** Connection duration (milliseconds) */
  connectionDuration: number
}

// ============================================================================
// Handler Protocol
// ============================================================================

/**
 * Projection Handler Protocol
 * 
 * Defines the contract for handling projection update events.
 */
export interface IProjectionHandler {
  /**
   * Handle projection update event
   * @param event - Projection update event
   */
  handle(event: ProjectionUpdateEvent): void

  /**
   * Validate projection update event
   * @param event - Event to validate
   * @returns Whether the event is valid
   */
  validate(event: unknown): event is ProjectionUpdateEvent
}

/**
 * Learning State Handler Protocol
 * 
 * Defines the contract for handling learning state update events.
 */
export interface ILearningStateHandler {
  /**
   * Handle learning state update event
   * @param event - Learning state update event
   */
  handle(event: LearningStateUpdateEvent): void

  /**
   * Validate learning state update event
   * @param event - Event to validate
   * @returns Whether the event is valid
   */
  validate(event: unknown): event is LearningStateUpdateEvent
}

/**
 * Experiment Handler Protocol
 * 
 * Defines the contract for handling experiment update events.
 */
export interface IExperimentHandler {
  /**
   * Handle experiment update event
   * @param event - Experiment update event
   */
  handle(event: ExperimentUpdateEvent): void

  /**
   * Validate experiment update event
   * @param event - Event to validate
   * @returns Whether the event is valid
   */
  validate(event: unknown): event is ExperimentUpdateEvent
}

/**
 * Error Handler Protocol
 * 
 * Defines the contract for handling error events.
 */
export interface IErrorHandler {
  /**
   * Handle error event
   * @param event - Error event
   */
  handle(event: ErrorEvent): void

  /**
   * Validate error event
   * @param event - Event to validate
   * @returns Whether the event is valid
   */
  validate(event: unknown): event is ErrorEvent
}

// ============================================================================
// Validator Protocol
// ============================================================================

/**
 * WebSocket Validator Protocol
 * 
 * Defines the contract for validating WebSocket-related data.
 */
export interface IWebSocketValidator {
  /**
   * Validate WebSocket configuration
   * @param config - Configuration to validate
   * @returns Whether the configuration is valid
   */
  validateConfig(config: unknown): config is WebSocketConfig

  /**
   * Validate WebSocket message
   * @param message - Message to validate
   * @returns Whether the message is valid
   */
  validateMessage(message: unknown): message is WebSocketMessage

  /**
   * Validate projection update event
   * @param event - Event to validate
   * @returns Whether the event is valid
   */
  validateProjectionEvent(event: unknown): event is ProjectionUpdateEvent

  /**
   * Validate learning state update event
   * @param event - Event to validate
   * @returns Whether the event is valid
   */
  validateLearningStateEvent(event: unknown): event is LearningStateUpdateEvent

  /**
   * Validate experiment update event
   * @param event - Event to validate
   * @returns Whether the event is valid
   */
  validateExperimentEvent(event: unknown): event is ExperimentUpdateEvent

  /**
   * Validate error event
   * @param event - Event to validate
   * @returns Whether the event is valid
   */
  validateErrorEvent(event: unknown): event is ErrorEvent
}

// ============================================================================
// Factory Protocol
// ============================================================================

/**
 * WebSocket Service Factory Protocol
 * 
 * Defines the contract for creating WebSocket service instances.
 */
export interface IWebSocketServiceFactory {
  /**
   * Create a WebSocket service instance
   * @param config - Service configuration
   * @returns WebSocket service instance
   */
  create(config: WebSocketConfig): IWebSocketService

  /**
   * Create a projection handler instance
   * @returns Projection handler instance
   */
  createProjectionHandler(): IProjectionHandler

  /**
   * Create a learning state handler instance
   * @returns Learning state handler instance
   */
  createLearningStateHandler(): ILearningStateHandler

  /**
   * Create an experiment handler instance
   * @returns Experiment handler instance
   */
  createExperimentHandler(): IExperimentHandler

  /**
   * Create an error handler instance
   * @returns Error handler instance
   */
  createErrorHandler(): IErrorHandler

  /**
   * Create a WebSocket validator instance
   * @returns WebSocket validator instance
   */
  createValidator(): IWebSocketValidator
}
