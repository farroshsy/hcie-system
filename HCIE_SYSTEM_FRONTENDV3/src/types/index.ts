// Auth types
export interface User {
  id: string
  username: string
  email: string
  role: 'user' | 'student' | 'researcher' | 'admin'
  permissions: string[]
  created_at: string
}

export interface AuthResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: User
}

// Learning types
export interface Task {
  task_id: string
  concept: string
  difficulty: number
  content: string
  options?: string[]
  representation?: 'text' | 'mcq' | 'video_question' | 'audio_listen' | 'code'
}

export interface TaskSubmission {
  user_id: string
  task_id: string
  concept_id: string
  answer: string
  correct?: boolean
  response_time?: number
  event_id?: string
  deterministic?: boolean
  seed?: number
}

export interface TaskResult {
  correct: boolean
  mastery_update: number
  new_mastery: number
  next_task_id?: string
  feedback?: string
}

// V3 Experience types
export interface LearningState {
  user_id: string
  current_mastery: number
  concept_progress: ConceptProgress[]
  learning_velocity: number
  confidence_level: 'low' | 'medium' | 'high'
  session_continuity: boolean
  recovery_state: string | null
  active_challenges: string[]
  next_recommended_difficulty: number
  streak_count: number
  last_interaction_time: string
}

export interface ConceptProgress {
  concept: string
  mastery: number
  interactions: number
}

export interface Recommendation {
  user_id: string
  recommended_concept: string
  recommended_difficulty: number
  confidence_score: number
  reasoning_summary: string
  alternative_options: AlternativeOption[]
  continuity_context: ContinuityContext
  trajectory_alignment: number
  recovery_hints: string | null
  estimated_success_probability: number
}

export interface AlternativeOption {
  concept: string
  difficulty: number
  reason: string
}

export interface ContinuityContext {
  session_continuous: boolean
  context_preserved: boolean
  trajectory_aligned: boolean
}

export interface Progress {
  user_id: string
  overall_progress: number
  concept_progress: ConceptProgress[]
  recent_achievements: Achievement[]
  next_milestones: Milestone[]
}

export interface Achievement {
  id: string
  title: string
  description: string
  earned_at: string
}

export interface Milestone {
  id: string
  title: string
  description: string
  progress: number
  target: number
}

export interface SessionContinuity {
  user_id: string
  session_continuous: boolean
  context_preserved: boolean
  trajectory_aligned: boolean
  last_session_time: string
}

// Dashboard types
export interface SystemOverview {
  total_users: number
  active_sessions: number
  system_health: 'healthy' | 'degraded' | 'unhealthy'
  average_mastery: number
  learning_events_today: number
}

export interface UserDashboard {
  user_id: string
  total_interactions: number
  current_mastery: number
  learning_progress: ConceptProgress[]
  recommendations: Recommendation[]
}

// Experiment types
export interface Experiment {
  id: string
  name: string
  description: string
  groups: string[]
  user_count: number
  duration_days: number
  metrics: string[]
  auto_start: boolean
  status: 'pending' | 'running' | 'completed' | 'failed'
  created_at: string
  started_at?: string
  completed_at?: string
}

export interface ExperimentConfig {
  name: string
  description: string
  groups: string[]
  user_count: number
  duration_days: number
  metrics: string[]
  auto_start: boolean
}

// Health check types
export interface HealthStatus {
  status: 'healthy' | 'unhealthy'
  timestamp: string
  components?: {
    database: string
    redis: string
    kafka: string
  }
}

// DAG types
export interface DAGNode {
  id: string
  label: string
  type: 'concept' | 'skill' | 'prerequisite'
  data: {
    mastery?: number
    difficulty?: number
    interactions?: number
  }
}

export interface DAGEdge {
  id: string
  source: string
  target: string
  type: 'prerequisite' | 'transfer' | 'related'
  data?: {
    strength?: number
  }
}

// WebSocket types
export interface WebSocketMessage {
  type: 'projection_update' | 'learning_event' | 'system_status'
  data: any
  timestamp: string
}

export interface ProjectionUpdate {
  user_id: string
  concept: string
  event_id: string
  projection: {
    mastery: number
    confidence: number
    trajectory: number[]
  }
}
