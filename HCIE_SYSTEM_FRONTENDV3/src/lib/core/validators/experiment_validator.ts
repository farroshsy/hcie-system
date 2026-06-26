/**
 * Experiment Validator Implementation
 * 
 * Implements the IExperimentValidator protocol for validating experiment-related data.
 * This validator uses Zod schemas for runtime type checking and validation.
 */

import { z } from 'zod'
import type {
  IExperimentValidator,
  ExperimentConfig,
  CreateExperimentData,
  Experiment,
  CohortConfig,
} from '../interfaces'

/**
 * Zod schemas for experiment-related data
 */
const ExperimentConfigSchema = z.object({
  policy: z.string(),
  parameters: z.record(z.string(), z.unknown()),
  cohort_size: z.number().min(1),
  duration_days: z.number().min(1),
  control_group: z.object({
    group_id: z.string(),
    policy: z.string(),
    parameters: z.record(z.string(), z.unknown()),
  }).optional(),
  treatment_group: z.object({
    group_id: z.string(),
    policy: z.string(),
    parameters: z.record(z.string(), z.unknown()),
  }).optional(),
})

const CohortConfigSchema = z.object({
  cohort_id: z.string(),
  user_ids: z.array(z.string()),
  metadata: z.record(z.string(), z.unknown()).optional(),
})

const CreateExperimentDataSchema = z.object({
  name: z.string().min(1),
  description: z.string().min(1),
  config: ExperimentConfigSchema,
  cohort: CohortConfigSchema,
})

const ExperimentSchema = z.object({
  experiment_id: z.string(),
  name: z.string(),
  description: z.string(),
  config: ExperimentConfigSchema,
  status: z.enum(['created', 'running', 'paused', 'completed', 'failed']),
  created_at: z.string(),
  started_at: z.string().optional(),
  completed_at: z.string().optional(),
  participant_count: z.number().min(0),
  results: z.any().optional(),
})

/**
 * Experiment Validator Implementation
 */
export class ExperimentValidator implements IExperimentValidator {
  /**
   * Validate experiment configuration
   */
  validateConfig(config: unknown): config is ExperimentConfig {
    return ExperimentConfigSchema.safeParse(config).success
  }

  /**
   * Validate experiment creation data
   */
  validateCreateData(data: unknown): data is CreateExperimentData {
    return CreateExperimentDataSchema.safeParse(data).success
  }

  /**
   * Validate experiment
   */
  validateExperiment(experiment: unknown): experiment is Experiment {
    return ExperimentSchema.safeParse(experiment).success
  }

  /**
   * Validate cohort configuration
   */
  validateCohort(cohort: unknown): cohort is CohortConfig {
    return CohortConfigSchema.safeParse(cohort).success
  }

  /**
   * Validate and parse experiment config (throws on error)
   */
  parseConfig(config: unknown): ExperimentConfig {
    return ExperimentConfigSchema.parse(config)
  }

  /**
   * Validate and parse creation data (throws on error)
   */
  parseCreateData(data: unknown): CreateExperimentData {
    return CreateExperimentDataSchema.parse(data)
  }

  /**
   * Validate and parse experiment (throws on error)
   */
  parseExperiment(experiment: unknown): Experiment {
    return ExperimentSchema.parse(experiment)
  }

  /**
   * Validate and parse cohort config (throws on error)
   */
  parseCohort(cohort: unknown): CohortConfig {
    return CohortConfigSchema.parse(cohort)
  }
}
