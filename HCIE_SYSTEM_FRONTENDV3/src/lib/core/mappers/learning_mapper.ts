/**
 * Learning Mapper Implementation
 * 
 * Implements the ILearningMapper protocol for mapping learning data between different representations.
 * This mapper handles conversion between API responses and domain models.
 */

import type {
  ILearningMapper,
  LearningState,
  Task,
  TaskSubmission,
  SubmissionResult,
  Recommendation,
} from '../interfaces'

/**
 * Learning Mapper Implementation
 */
export class LearningMapper implements ILearningMapper {
  /**
   * Map API response to learning state
   */
  apiToLearningState(apiResponse: unknown): LearningState {
    const response = apiResponse as Record<string, unknown>
    
    return {
      user_id: response.user_id as string,
      mastery: (response.mastery as Record<string, number>) || {},
      current_task: response.current_task as Task | null || null,
      recommendations: (response.recommendations as Recommendation[]) || [],
      projection: response.projection as {
        mastery: Record<string, number>
        ensemble_weights: Record<string, number>
        governance_metrics: {
          constitutional_weights: Record<string, number>
          volatility: number
          stability: number
          attribution: Record<string, number>
        }
        timestamp: string
      } || {
        mastery: {},
        ensemble_weights: {},
        governance_metrics: {
          constitutional_weights: {},
          volatility: 0,
          stability: 0,
          attribution: {},
        },
        timestamp: new Date().toISOString(),
      },
      last_updated: response.last_updated as string || new Date().toISOString(),
      tasks_completed: (response.tasks_completed as number) || 0,
      streak: (response.streak as number) || 0,
    }
  }

  /**
   * Map learning state to API request format
   */
  learningStateToApi(state: LearningState): Record<string, unknown> {
    return {
      user_id: state.user_id,
      mastery: state.mastery,
      current_task: state.current_task,
      recommendations: state.recommendations,
      projection: state.projection,
      last_updated: state.last_updated,
      tasks_completed: state.tasks_completed,
      streak: state.streak,
    }
  }

  /**
   * Map task submission to API request format
   */
  submissionToApi(submission: TaskSubmission): Record<string, unknown> {
    return {
      user_id: submission.user_id,
      task_id: submission.task_id,
      answer: submission.answer,
      response_time: submission.response_time,
      timestamp: submission.timestamp,
    }
  }

  /**
   * Map API response to submission result
   */
  apiToSubmissionResult(apiResponse: unknown): SubmissionResult {
    const response = apiResponse as Record<string, unknown>
    
    return {
      success: response.success as boolean || false,
      correct: response.correct as boolean || false,
      feedback: response.feedback as string || '',
      updated_mastery: (response.updated_mastery as Record<string, number>) || {},
      next_task: response.next_task as Task | null || null,
      points_earned: (response.points_earned as number) || 0,
    }
  }
}
