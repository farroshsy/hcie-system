import { http, HttpResponse } from 'msw'

export const handlers = [
  // Learning API
  http.get('/api/learning', ({ request }) => {
    const url = new URL(request.url)
    const userId = url.searchParams.get('userId')
    const action = url.searchParams.get('action')

    if (!userId) {
      return HttpResponse.json({ error: 'userId is required' }, { status: 400 })
    }

    switch (action) {
      case 'state':
        return HttpResponse.json({
          user_id: userId,
          mastery: { algebra: 0.75, geometry: 0.68, calculus: 0.45 },
          tasks_completed: 38,
          streak: 7,
          last_updated: new Date().toISOString(),
        })
      case 'next-task':
        return HttpResponse.json({
          task_id: 'task_001',
          concept: 'Algebra',
          difficulty: 0.6,
          content: 'Solve for x: 2x + 5 = 15',
          options: ['x = 5', 'x = 10', 'x = 7', 'x = 3'],
        })
      case 'recommendations':
        return HttpResponse.json([
          { task_id: 'task_002', concept: 'Geometry', confidence: 0.85, reason: 'Based on your progress' },
          { task_id: 'task_003', concept: 'Algebra', confidence: 0.78, reason: 'Reinforce learning' },
        ])
      default:
        return HttpResponse.json({ error: 'Invalid action' }, { status: 400 })
    }
  }),

  // Dashboard API
  http.get('/api/dashboard', ({ request }) => {
    const url = new URL(request.url)
    const userId = url.searchParams.get('userId')

    return HttpResponse.json({
      user_id: userId,
      total_tasks: 150,
      completed_tasks: 38,
      avg_score: 0.85,
      concepts_mastered: 5,
      current_streak: 7,
      recent_activity: [
        { task_id: 'task_001', concept: 'Algebra', score: 0.9, timestamp: new Date().toISOString() },
        { task_id: 'task_002', concept: 'Geometry', score: 0.8, timestamp: new Date(Date.now() - 86400000).toISOString() },
      ],
    })
  }),

  // Experiments API
  http.get('/api/experiments', () => {
    return HttpResponse.json({
      experiments: [
        {
          experiment_id: 'exp_001',
          name: 'Bandit Strategy A vs B',
          description: 'Comparing epsilon-greedy and Thompson sampling',
          status: 'completed',
          config: { policy: 'bandit', algorithm: 'thompson' },
          created_at: new Date().toISOString(),
        },
      ],
    })
  }),

  // Users API
  http.get('/api/users', () => {
    return HttpResponse.json({
      users: [
        { user_id: 'user_001', name: 'Test User', email: 'test@example.com', role: 'student' },
        { user_id: 'user_002', name: 'Admin User', email: 'admin@example.com', role: 'admin' },
      ],
      total: 2,
    })
  }),

  // System Health API
  http.get('/api/system', ({ request }) => {
    const url = new URL(request.url)
    const action = url.searchParams.get('action')

    switch (action) {
      case 'health':
        return HttpResponse.json({
          status: 'healthy',
          timestamp: new Date().toISOString(),
          services: {
            api: 'running',
            database: 'connected',
            redis: 'connected',
            kafka: 'connected',
          },
        })
      case 'metrics':
        return HttpResponse.json({
          uptime: 3600,
          memory_usage: 512,
          cpu_usage: 0.45,
          active_connections: 10,
          requests_per_minute: 120,
        })
      default:
        return HttpResponse.json({ error: 'Invalid action' }, { status: 400 })
    }
  }),
]
