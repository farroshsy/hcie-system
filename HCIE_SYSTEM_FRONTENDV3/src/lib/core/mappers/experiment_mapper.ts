/**
 * Experiment Mapper Implementation
 * 
 * Implements the IExperimentMapper protocol for mapping experiment data between different representations.
 * This mapper handles conversion between API responses and domain models.
 */

import type {
  IExperimentMapper,
  Experiment,
  ExperimentConfig,
  CreateExperimentData,
  ExperimentResults,
  ExperimentListResponse,
} from '../interfaces'

/**
 * Experiment Mapper Implementation
 */
export class ExperimentMapper implements IExperimentMapper {
  /**
   * Map API response to experiment
   */
  apiToExperiment(apiResponse: unknown): Experiment {
    const response = apiResponse as Record<string, unknown>
    
    return {
      experiment_id: response.experiment_id as string,
      name: response.name as string,
      description: response.description as string,
      config: this.apiToConfig(response.config),
      status: (response.status as 'created' | 'running' | 'paused' | 'completed' | 'failed') || 'created',
      created_at: response.created_at as string,
      started_at: response.started_at as string,
      completed_at: response.completed_at as string,
      participant_count: (response.participant_count as number) || 0,
      results: response.results as ExperimentResults,
    }
  }

  /**
   * Map experiment creation data to API request format
   */
  createDataToApi(data: CreateExperimentData): Record<string, unknown> {
    return {
      name: data.name,
      description: data.description,
      config: this.configToApi(data.config),
      cohort: data.cohort,
    }
  }

  /**
   * Map experiment config to API request format
   */
  configToApi(config: ExperimentConfig): Record<string, unknown> {
    return {
      policy: config.policy,
      parameters: config.parameters,
      cohort_size: config.cohort_size,
      duration_days: config.duration_days,
      control_group: config.control_group,
      treatment_group: config.treatment_group,
    }
  }

  /**
   * Map API response to experiment results
   */
  apiToExperimentResults(apiResponse: unknown): ExperimentResults {
    const response = apiResponse as Record<string, unknown>
    
    return {
      experiment_id: response.experiment_id as string,
      control_group: response.control_group as {
        group_id: string
        participant_count: number
        avg_accuracy: number
        avg_learning_gain: number
        avg_completion_rate: number
        participant_results: Array<{
          user_id: string
          group_id: string
          accuracy: number
          learning_gain: number
          tasks_completed: number
          time_spent: number
        }>
      },
      treatment_group: response.treatment_group as {
        group_id: string
        participant_count: number
        avg_accuracy: number
        avg_learning_gain: number
        avg_completion_rate: number
        participant_results: Array<{
          user_id: string
          group_id: string
          accuracy: number
          learning_gain: number
          tasks_completed: number
          time_spent: number
        }>
      },
      statistical_analysis: response.statistical_analysis as {
        p_value: number
        effect_size: number
        confidence_interval: { lower: number; upper: number }
        significant: boolean
        test_used: string
      },
      figures: response.figures as Array<{
        figure_id: string
        type: 'learning_curve' | 'ensemble_weights' | 'governance_metrics' | 'trajectory'
        title: string
        data_url: string
        format: 'png' | 'svg' | 'pdf'
        metadata?: Record<string, unknown>
      }>,
      completed_at: response.completed_at as string,
    }
  }

  /**
   * Map API response to experiment list
   */
  apiToExperimentList(apiResponse: unknown): ExperimentListResponse {
    const response = apiResponse as Record<string, unknown>
    
    return {
      experiments: (response.experiments as unknown[]).map(exp => this.apiToExperiment(exp)),
      total: (response.total as number) || 0,
      page: (response.page as number) || 1,
      limit: (response.limit as number) || 10,
    }
  }

  /**
   * Map API response to config
   */
  private apiToConfig(apiResponse: unknown): ExperimentConfig {
    const response = apiResponse as Record<string, unknown>
    
    return {
      policy: response.policy as string,
      parameters: (response.parameters as Record<string, unknown>) || {},
      cohort_size: (response.cohort_size as number) || 0,
      duration_days: (response.duration_days as number) || 0,
      control_group: response.control_group as {
        group_id: string
        policy: string
        parameters: Record<string, unknown>
      },
      treatment_group: response.treatment_group as {
        group_id: string
        policy: string
        parameters: Record<string, unknown>
      },
    }
  }
}
