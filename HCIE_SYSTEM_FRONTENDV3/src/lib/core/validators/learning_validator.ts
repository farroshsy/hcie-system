/**
 * Learning Validator Implementation
 * 
 * Implements the ILearningValidator protocol for validating learning-related data.
 * This validator uses Zod schemas for runtime type checking and validation.
 */

import { z } from 'zod'
import type {
  ILearningValidator,
  Task,
  TaskSubmission,
  LearningState,
  Recommendation,
} from '../interfaces'

/**
 * Zod schemas for learning-related data
 */
const TaskSchema = z.object({
  task_id: z.string(),
  concept: z.string(),
  difficulty: z.number().min(0).max(1),
  content: z.string(),
  options: z.array(z.string()).optional(),
  representation: z.enum(['text', 'mcq', 'video_question', 'audio_listen', 'code']),
  estimated_time: z.number().optional(),
  prerequisites: z.array(z.string()).optional(),
})

const TaskSubmissionSchema = z.object({
  user_id: z.string(),
  task_id: z.string(),
  answer: z.union([z.string(), z.number()]),
  response_time: z.number().min(0),
  timestamp: z.string(),
})

const RecommendationSchema = z.object({
  task_id: z.string(),
  reason: z.string(),
  confidence: z.number().min(0).max(1),
  expected_mastery: z.number().min(0).max(1),
  policy: z.string(),
})

const LearningStateSchema = z.object({
  user_id: z.string(),
  mastery: z.record(z.string(), z.number().min(0).max(1)),
  current_task: TaskSchema.nullable(),
  recommendations: z.array(RecommendationSchema),
  projection: z.object({
    mastery: z.record(z.string(), z.number().min(0).max(1)),
    ensemble_weights: z.record(z.string(), z.number()),
    governance_metrics: z.object({
      constitutional_weights: z.record(z.string(), z.number()),
      volatility: z.number(),
      stability: z.number(),
      attribution: z.record(z.string(), z.number()),
    }),
    timestamp: z.string(),
  }),
  last_updated: z.string(),
  tasks_completed: z.number().min(0),
  streak: z.number().min(0),
})

/**
 * Learning Validator Implementation
 */
export class LearningValidator implements ILearningValidator {
  /**
   * Validate a task object
   */
  validateTask(task: unknown): task is Task {
    return TaskSchema.safeParse(task).success
  }

  /**
   * Validate a task submission
   */
  validateSubmission(submission: unknown): submission is TaskSubmission {
    return TaskSubmissionSchema.safeParse(submission).success
  }

  /**
   * Validate a learning state
   */
  validateLearningState(state: unknown): state is LearningState {
    return LearningStateSchema.safeParse(state).success
  }

  /**
   * Validate a recommendation
   */
  validateRecommendation(recommendation: unknown): recommendation is Recommendation {
    return RecommendationSchema.safeParse(recommendation).success
  }

  /**
   * Validate and parse a task object (throws on error)
   */
  parseTask(task: unknown): Task {
    return TaskSchema.parse(task)
  }

  /**
   * Validate and parse a task submission (throws on error)
   */
  parseSubmission(submission: unknown): TaskSubmission {
    return TaskSubmissionSchema.parse(submission)
  }

  /**
   * Validate and parse a learning state (throws on error)
   */
  parseLearningState(state: unknown): LearningState {
    return LearningStateSchema.parse(state)
  }

  /**
   * Validate and parse a recommendation (throws on error)
   */
  parseRecommendation(recommendation: unknown): Recommendation {
    return RecommendationSchema.parse(recommendation)
  }
}
