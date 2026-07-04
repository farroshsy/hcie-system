/**
 * Learning Types
 * 
 * Type definitions for multi-method learning system
 */

export type LearningMethod = 'text' | 'code' | 'multiple_choice' | 'video' | 'interactive'

export interface Concept {
  id: string
  gradeBand: 'K-2' | 'K-5' | 'K-8' | 'K-12'
  conceptArea: string
  cognitiveLevel: number // 1-4
  difficulty: number // 0.2-0.8
  description: string
  learningObjectives: string[]
  masteryLevel: number // 0-100
  masteryProbability: number // 0-1 from knowledge tracing
  confidenceInterval: { lower: number; upper: number } // confidence interval for mastery
  prerequisites: string[] // prerequisite concept IDs
  dependsOn: string[] // concepts that depend on this one
  tasks: Task[]
  estimatedTime: number // in minutes
  banditScore?: number // bandit selection score
  recommended?: boolean // whether bandit recommends this concept
  spacedRepetition?: {
    nextReview: string // ISO date
    interval: number // days until next review
    easeFactor: number // spaced repetition ease factor
  }
  learningCurve?: {
    timestamps: number[]
    masteryValues: number[]
  }
}

export interface Task {
  id: string
  conceptId: string
  name: string
  description: string
  method: LearningMethod
  order: number
  content: TaskContent
  difficulty: number // 1-10
  estimatedTime: number // in minutes
  completed: boolean
  score?: number
  irtDifficulty?: number // IRT-calibrated difficulty
  irtDiscrimination?: number // IRT discrimination parameter
  responseTime?: number // average response time in seconds
  attempts?: number // number of attempts
  microSteps?: MicroStep[] // bite-sized steps for Brilliant-style interaction
}

export interface MicroStep {
  id: string
  taskId: string
  order: number
  prompt: string
  type: 'multiple_choice' | 'text_input' | 'math_input' | 'dropdown'
  options?: string[] // for multiple choice
  correctAnswer: string | number
  hint?: string
  completed: boolean
  userAnswer?: string | number
  isCorrect?: boolean
}

export interface TaskContent {
  text?: {
    content: string
    examples?: string[]
    exercises?: Exercise[]
  }
  video?: {
    url: string
    duration: number
    transcript?: string
    subtitles?: string
  }
  audio?: {
    url: string
    duration: number
    transcript?: string
  }
  code?: {
    starterCode: string
    solution: string
    language: string
    tests?: TestCase[]
    hints?: string[]
  }
  gamification?: {
    type: 'quiz' | 'simulation' | 'game' | 'challenge'
    config: Record<string, any>
    scoring: {
      points: number
      timeBonus: boolean
      accuracyBonus: boolean
    }
  }
  interactive?: {
    type: 'simulation' | 'visualization' | 'exploration'
    config: Record<string, any>
  }
  quiz?: {
    questions: Question[]
    passingScore: number
    timeLimit?: number
  }
}

export interface Exercise {
  id: string
  question: string
  type: 'multiple-choice' | 'fill-in-blank' | 'short-answer' | 'essay'
  options?: string[]
  correctAnswer: string | string[]
  explanation?: string
}

export interface TestCase {
  id: string
  input: string
  expectedOutput: string
  isHidden: boolean
}

export interface Question {
  id: string
  question: string
  type: 'multiple-choice' | 'true-false' | 'short-answer' | 'matching'
  options?: string[]
  correctAnswer: string | string[]
  explanation?: string
  points: number
}

export interface LearningProgress {
  conceptId: string
  completedTasks: string[]
  currentTaskId: string | null
  totalTimeSpent: number
  averageScore: number
  lastAccessed: Date
  preferredMethods: LearningMethod[]
}

export interface LearningSession {
  id: string
  conceptId: string
  taskId: string
  method: LearningMethod
  startTime: Date
  endTime?: Date
  completed: boolean
  score?: number
  answers: Record<string, any>
  timeSpent: number
}

export interface EngagementMetrics {
  totalSessions: number
  tasksCompleted: number
  accuracy: number
  avgSessionDuration: number // in seconds
  avgTimeOnTask: number // in seconds
  retentionRate: number
}

export interface PerformanceMetrics {
  overallAccuracy: number
  avgResponseTime: number
  completionRate: number
  learningGain: number
  retentionRate: number
}

export interface AnalyticsData {
  engagement_metrics: EngagementMetrics
  performance_metrics: PerformanceMetrics
  learning_curves: {
    concept: string
    current_mastery: number
    target_mastery: number
  }[]
  heatmap_data?: {
    timeOfDay: { hour: number; performance: number }[]
    conceptDifficulty: { concept: string; difficulty: number; performance: number }[]
  }
}

export interface ExportData {
  userId: string
  exportDate: string
  concepts: Concept[]
  sessions: LearningSession[]
  analytics: AnalyticsData
}

export interface Badge {
  id: string
  name: string
  description: string
  icon: string
  rarity: 'common' | 'rare' | 'epic' | 'legendary'
  earnedAt?: Date
  progress: number // 0-100
  requirement: string
}

export interface Achievement {
  id: string
  title: string
  description: string
  points: number
  completed: boolean
  completedAt?: Date
  category: 'mastery' | 'streak' | 'speed' | 'exploration' | 'collaboration'
}

export interface LeaderboardEntry {
  userId: string
  email: string
  totalPoints: number
  rank: number
  badges: number
  currentStreak: number
}

export interface StudyGroup {
  id: string
  name: string
  description: string
  members: string[]
  currentConcept: string
  progress: number
  createdAt: Date
  isOwner: boolean
}

export interface PeerHelpRequest {
  id: string
  userId: string
  email: string
  conceptId: string
  conceptName: string
  question: string
  status: 'open' | 'answered' | 'closed'
  createdAt: Date
  answers?: {
    userId: string
    email: string
    answer: string
    helpful: number
    createdAt: Date
  }[]
}

export interface LearningGoal {
  id: string
  type: 'daily' | 'weekly' | 'monthly' | 'custom'
  target: number
  current: number
  unit: 'minutes' | 'concepts' | 'tasks' | 'points'
  deadline: Date
  completed: boolean
  createdAt: Date
}

export interface Reminder {
  id: string
  type: 'spaced_review' | 'daily_goal' | 'streak' | 'absence'
  message: string
  scheduledFor: Date
  dismissed: boolean
  actionUrl?: string
}

export interface LearningIntelligence {
  mastery: number
  uncertainty: number
  confidence: number
  zpdScore: number
  delta: number | null
  systemReasoning: string
  banditDecision: {
    selectedConcept: string
    expectedReward: number
    alternatives: {
      concept: string
      expectedReward: number
    }[]
  }
}

export interface AdaptivePath {
  currentConcept: string
  recommendedNext: string[]
  reasoning: string[]
  prerequisites: {
    concept: string
    status: 'completed' | 'in_progress' | 'blocked'
    urgency: 'high' | 'medium' | 'low'
  }[]
  alternativePaths: {
    name: string
    concepts: string[]
    estimatedSuccess: number
  }[]
}

export interface PersonalAnalytics {
  learningVelocity: number
  transferEffectiveness: number
  responseTimeTrend: {
    timestamp: number
    time: number
    difficulty: number
  }[]
  masteryCurve: {
    timestamp: number
    mastery: number
  }[]
  peerComparison: {
    percentile: number
    metrics: {
      avgMastery: number
      yourMastery: number
    }
  }
  predictedTimeToMastery: {
    concept: string
    estimatedHours: number
    confidence: number
  }[]
}
