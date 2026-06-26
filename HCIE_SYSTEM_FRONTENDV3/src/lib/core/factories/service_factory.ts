/**
 * Service Factory Implementation
 * 
 * Central factory for creating service instances with their dependencies.
 * This factory implements dependency injection and ensures proper initialization
 * of all services with their required validators and mappers.
 */

import { LearningService } from '../services/learning_service'
import { AuthService } from '../services/auth_service'
import { DashboardService } from '../services/dashboard_service'
import { ExperimentService } from '../services/experiment_service'
import { WebSocketService } from '../services/websocket_service'

import { LearningValidator } from '../validators/learning_validator'
import { AuthValidator } from '../validators/auth_validator'
import { DashboardValidator } from '../validators/dashboard_validator'
import { ExperimentValidator } from '../validators/experiment_validator'
import { WebSocketValidator } from '../validators/websocket_validator'

import { LearningMapper } from '../mappers/learning_mapper'
import { AuthMapper } from '../mappers/auth_mapper'
import { DashboardMapper } from '../mappers/dashboard_mapper'
import { ExperimentMapper } from '../mappers/experiment_mapper'
import { WebSocketMapper } from '../mappers/websocket_mapper'

import type {
  ILearningServiceFactory,
  IAuthServiceFactory,
  IDashboardServiceFactory,
  IExperimentServiceFactory,
  LearningServiceConfig,
  AuthServiceConfig,
  DashboardServiceConfig,
  ExperimentServiceConfig,
  WebSocketConfig,
} from '../interfaces'

/**
 * Learning Service Factory
 * 
 * Factory for creating learning service instances with their dependencies.
 */
export class LearningServiceFactory implements ILearningServiceFactory {
  private validator: LearningValidator | null = null
  private mapper: LearningMapper | null = null

  /**
   * Create a learning service instance
   */
  create(config: LearningServiceConfig): LearningService {
    return new LearningService(config)
  }

  /**
   * Create a learning validator instance
   */
  createValidator(): LearningValidator {
    if (!this.validator) {
      this.validator = new LearningValidator()
    }
    return this.validator
  }

  /**
   * Create a learning mapper instance
   */
  createMapper(): LearningMapper {
    if (!this.mapper) {
      this.mapper = new LearningMapper()
    }
    return this.mapper
  }
}

/**
 * Authentication Service Factory
 * 
 * Factory for creating authentication service instances with their dependencies.
 */
export class AuthServiceFactory implements IAuthServiceFactory {
  private validator: AuthValidator | null = null
  private mapper: AuthMapper | null = null

  /**
   * Create an authentication service instance
   */
  create(config: AuthServiceConfig): AuthService {
    return new AuthService(config)
  }

  /**
   * Create an authentication validator instance
   */
  createValidator(): AuthValidator {
    if (!this.validator) {
      this.validator = new AuthValidator()
    }
    return this.validator
  }

  /**
   * Create an authentication mapper instance
   */
  createMapper(): AuthMapper {
    if (!this.mapper) {
      this.mapper = new AuthMapper()
    }
    return this.mapper
  }
}

/**
 * Dashboard Service Factory
 * 
 * Factory for creating dashboard service instances with their dependencies.
 */
export class DashboardServiceFactory implements IDashboardServiceFactory {
  private validator: DashboardValidator | null = null
  private mapper: DashboardMapper | null = null

  /**
   * Create a dashboard service instance
   */
  create(config: DashboardServiceConfig): DashboardService {
    return new DashboardService(config)
  }

  /**
   * Create a dashboard validator instance
   */
  createValidator(): DashboardValidator {
    if (!this.validator) {
      this.validator = new DashboardValidator()
    }
    return this.validator
  }

  /**
   * Create a dashboard mapper instance
   */
  createMapper(): DashboardMapper {
    if (!this.mapper) {
      this.mapper = new DashboardMapper()
    }
    return this.mapper
  }
}

/**
 * Experiment Service Factory
 * 
 * Factory for creating experiment service instances with their dependencies.
 */
export class ExperimentServiceFactory implements IExperimentServiceFactory {
  private validator: ExperimentValidator | null = null
  private mapper: ExperimentMapper | null = null

  /**
   * Create an experiment service instance
   */
  create(config: ExperimentServiceConfig): ExperimentService {
    return new ExperimentService(config)
  }

  /**
   * Create an experiment validator instance
   */
  createValidator(): ExperimentValidator {
    if (!this.validator) {
      this.validator = new ExperimentValidator()
    }
    return this.validator
  }

  /**
   * Create an experiment mapper instance
   */
  createMapper(): ExperimentMapper {
    if (!this.mapper) {
      this.mapper = new ExperimentMapper()
    }
    return this.mapper
  }
}

/**
 * WebSocket Service Factory
 * 
 * Factory for creating WebSocket service instances with their dependencies.
 * Note: Event handlers are implemented in the application layer.
 */
export class WebSocketServiceFactory {
  private validator: WebSocketValidator | null = null
  private mapper: WebSocketMapper | null = null

  /**
   * Create a WebSocket service instance
   */
  create(config: WebSocketConfig): WebSocketService {
    return new WebSocketService(config)
  }

  /**
   * Create a WebSocket validator instance
   */
  createValidator(): WebSocketValidator {
    if (!this.validator) {
      this.validator = new WebSocketValidator()
    }
    return this.validator
  }

  /**
   * Create a WebSocket mapper instance
   */
  createMapper(): WebSocketMapper {
    if (!this.mapper) {
      this.mapper = new WebSocketMapper()
    }
    return this.mapper
  }
}

/**
 * Unified Service Factory
 * 
 * Central factory that provides access to all service factories.
 */
export class ServiceFactory {
  private learningFactory: LearningServiceFactory
  private authFactory: AuthServiceFactory
  private dashboardFactory: DashboardServiceFactory
  private experimentFactory: ExperimentServiceFactory
  private webSocketFactory: WebSocketServiceFactory

  constructor() {
    this.learningFactory = new LearningServiceFactory()
    this.authFactory = new AuthServiceFactory()
    this.dashboardFactory = new DashboardServiceFactory()
    this.experimentFactory = new ExperimentServiceFactory()
    this.webSocketFactory = new WebSocketServiceFactory()
  }

  get learning(): LearningServiceFactory {
    return this.learningFactory
  }

  get auth(): AuthServiceFactory {
    return this.authFactory
  }

  get dashboard(): DashboardServiceFactory {
    return this.dashboardFactory
  }

  get experiment(): ExperimentServiceFactory {
    return this.experimentFactory
  }

  get websocket(): WebSocketServiceFactory {
    return this.webSocketFactory
  }
}

// Singleton instance
let factoryInstance: ServiceFactory | null = null

/**
 * Get the singleton service factory instance
 */
export function getServiceFactory(): ServiceFactory {
  if (!factoryInstance) {
    factoryInstance = new ServiceFactory()
  }
  return factoryInstance
}
