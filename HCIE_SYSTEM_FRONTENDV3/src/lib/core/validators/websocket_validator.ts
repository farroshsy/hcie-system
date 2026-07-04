/**
 * WebSocket Validator Implementation
 * 
 * Implements the IWebSocketValidator protocol for validating WebSocket-related data.
 * This validator uses Zod schemas for runtime type checking and validation.
 */

import { z } from 'zod'
import type {
  IWebSocketValidator,
  WebSocketConfig,
  WebSocketMessage,
  ProjectionUpdateEvent,
  LearningStateUpdateEvent,
  ExperimentUpdateEvent,
  ErrorEvent,
} from '../interfaces'

/**
 * Zod schemas for WebSocket-related data
 */
const WebSocketConfigSchema = z.object({
  url: z.string().url(),
  authToken: z.string(),
  reconnectInterval: z.number().min(0).optional(),
  maxReconnectAttempts: z.number().min(0).optional(),
  debug: z.boolean().optional(),
})

const WebSocketMessageSchema = z.object({
  type: z.string(),
  data: z.any(),
  timestamp: z.string(),
  id: z.string().optional(),
}) as z.ZodType<WebSocketMessage<unknown>>

const ProjectionUpdateEventSchema = z.object({
  user_id: z.string(),
  projection: z.object({
    mastery: z.record(z.string(), z.number()),
    ensemble_weights: z.record(z.string(), z.number()),
    governance_metrics: z.object({
      constitutional_weights: z.record(z.string(), z.number()),
      volatility: z.number(),
      stability: z.number(),
      attribution: z.record(z.string(), z.number()),
    }),
    timestamp: z.string(),
  }),
})

const LearningStateUpdateEventSchema = z.object({
  user_id: z.string(),
  learning_state: z.object({
    user_id: z.string(),
    mastery: z.record(z.string(), z.number()),
    current_task: z.unknown().nullable(),
    recommendations: z.array(z.unknown()),
    projection: z.unknown(),
    last_updated: z.string(),
  }),
}) as z.ZodType<LearningStateUpdateEvent>

const ExperimentUpdateEventSchema = z.object({
  experiment_id: z.string(),
  status: z.enum(['created', 'running', 'paused', 'completed', 'failed']),
  progress: z.number().min(0).max(100),
  timestamp: z.string(),
})

const ErrorEventSchema = z.object({
  message: z.string(),
  code: z.string(),
  details: z.record(z.string(), z.unknown()).optional(),
  timestamp: z.string(),
})

/**
 * WebSocket Validator Implementation
 */
export class WebSocketValidator implements IWebSocketValidator {
  /**
   * Validate WebSocket configuration
   */
  validateConfig(config: unknown): config is WebSocketConfig {
    return WebSocketConfigSchema.safeParse(config).success
  }

  /**
   * Validate WebSocket message
   */
  validateMessage(message: unknown): message is WebSocketMessage {
    return WebSocketMessageSchema.safeParse(message).success
  }

  /**
   * Validate projection update event
   */
  validateProjectionEvent(event: unknown): event is ProjectionUpdateEvent {
    return ProjectionUpdateEventSchema.safeParse(event).success
  }

  /**
   * Validate learning state update event
   */
  validateLearningStateEvent(event: unknown): event is LearningStateUpdateEvent {
    return LearningStateUpdateEventSchema.safeParse(event).success
  }

  /**
   * Validate experiment update event
   */
  validateExperimentEvent(event: unknown): event is ExperimentUpdateEvent {
    return ExperimentUpdateEventSchema.safeParse(event).success
  }

  /**
   * Validate error event
   */
  validateErrorEvent(event: unknown): event is ErrorEvent {
    return ErrorEventSchema.safeParse(event).success
  }

  /**
   * Validate and parse config (throws on error)
   */
  parseConfig(config: unknown): WebSocketConfig {
    return WebSocketConfigSchema.parse(config)
  }

  /**
   * Validate and parse message (throws on error)
   */
  parseMessage(message: unknown): WebSocketMessage {
    return WebSocketMessageSchema.parse(message)
  }

  /**
   * Validate and parse projection event (throws on error)
   */
  parseProjectionEvent(event: unknown): ProjectionUpdateEvent {
    return ProjectionUpdateEventSchema.parse(event)
  }

  /**
   * Validate and parse learning state event (throws on error)
   */
  parseLearningStateEvent(event: unknown): LearningStateUpdateEvent {
    return LearningStateUpdateEventSchema.parse(event)
  }

  /**
   * Validate and parse experiment event (throws on error)
   */
  parseExperimentEvent(event: unknown): ExperimentUpdateEvent {
    return ExperimentUpdateEventSchema.parse(event)
  }

  /**
   * Validate and parse error event (throws on error)
   */
  parseErrorEvent(event: unknown): ErrorEvent {
    return ErrorEventSchema.parse(event)
  }
}
