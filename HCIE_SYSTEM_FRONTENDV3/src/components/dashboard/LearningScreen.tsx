/**
 * Learning Screen
 * 
 * Main learning interface where users interact with tasks and receive feedback.
 * Displays current task, submission form, and learning progress.
 */

'use client'

import { useEffect, useState } from 'react'
import { useAuth } from '@/contexts'
import { useServices } from '@/contexts'
import { useT } from '@/contexts/language_context'
import { useLearningProgress } from '@/hooks/useWebSocket'
import type { Task, TaskSubmission, SubmissionResult } from '@/lib/core'
import { TrendingUp, Target, Activity } from 'lucide-react'

export default function LearningScreen() {
  const t = useT()
  const { user } = useAuth()
  const services = useServices()
  const [currentTask, setCurrentTask] = useState<Task | null>(null)
  const [answer, setAnswer] = useState<string>('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [result, setResult] = useState<SubmissionResult | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Real-time learning progress via WebSocket
  const { masteryUpdates, banditScores, notifications } = useLearningProgress()

  useEffect(() => {
    if (user) {
      loadNextTask()
    }
  }, [user])

  const loadNextTask = async () => {
    try {
      setIsLoading(true)
      const { task } = await services.learning.getNextTask(user!.id)
      setCurrentTask(task)
      setAnswer('')
      setResult(null)
    } catch (error) {
      console.error('Failed to load task:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSubmit = async () => {
    if (!currentTask || !user) return

    try {
      setIsSubmitting(true)
      const submission: TaskSubmission = {
        user_id: user.id,
        task_id: currentTask.task_id,
        answer,
        response_time: 0, // Would be tracked in production
        timestamp: new Date().toISOString(),
      }
      const submissionResult = await services.learning.submitAnswer(submission)
      setResult(submissionResult)
    } catch (error) {
      console.error('Failed to submit answer:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-gray-600">{t('common.loading')}</div>
      </div>
    )
  }

  if (!currentTask) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-gray-600">{t('common.noResults')}</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-8">
        {/* Real-time Progress */}
        {(Object.keys(masteryUpdates).length > 0 || Object.keys(banditScores).length > 0) && (
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Activity className="w-5 h-5 text-blue-600" />
              Real-time Progress
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.keys(masteryUpdates).length > 0 && (
                <div className="bg-blue-50 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <TrendingUp className="w-4 h-4 text-blue-600" />
                    <span className="text-sm font-medium text-gray-700">Mastery Updates</span>
                  </div>
                  <div className="space-y-1">
                    {Object.entries(masteryUpdates).slice(0, 3).map(([concept, value]) => (
                      <div key={concept} className="flex justify-between text-sm">
                        <span className="text-gray-600">{concept}</span>
                        <span className="font-medium text-gray-900">{(value * 100).toFixed(1)}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {Object.keys(banditScores).length > 0 && (
                <div className="bg-green-50 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Target className="w-4 h-4 text-green-600" />
                    <span className="text-sm font-medium text-gray-700">Bandit Scores</span>
                  </div>
                  <div className="space-y-1">
                    {Object.entries(banditScores).slice(0, 3).map(([policy, score]) => (
                      <div key={policy} className="flex justify-between text-sm">
                        <span className="text-gray-600">{policy}</span>
                        <span className="font-medium text-gray-900">{score.toFixed(3)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
            {notifications.length > 0 && (
              <div className="mt-4 space-y-2">
                {notifications.slice(0, 2).map((notification, index) => (
                  <div key={index} className="text-sm text-gray-600 bg-gray-50 rounded px-3 py-2">
                    {notification}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Task Card */}
        <div className="bg-white rounded-lg shadow p-8 mb-6">
          <div className="mb-6">
            <span className="inline-block px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
              {currentTask.concept}
            </span>
            <span className="inline-block px-3 py-1 bg-gray-100 text-gray-800 rounded-full text-sm font-medium ml-2">
              Difficulty: {Math.round(currentTask.difficulty * 100)}%
            </span>
          </div>

          <div className="mb-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Task</h2>
            <div className="bg-gray-50 rounded-lg p-6">
              <p className="text-gray-700 text-lg">{currentTask.content}</p>
            </div>
          </div>

          {currentTask.options && currentTask.options.length > 0 && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Options</h3>
              <div className="space-y-2">
                {currentTask.options.map((option, index) => (
                  <button
                    key={index}
                    onClick={() => setAnswer(option)}
                    className={`w-full text-left px-4 py-3 rounded-lg border-2 transition ${
                      answer === option
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    {option}
                  </button>
                ))}
              </div>
            </div>
          )}

          {!currentTask.options && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Your Answer</h3>
              <input
                type="text"
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Enter your answer..."
              />
            </div>
          )}

          <button
            onClick={handleSubmit}
            disabled={!answer || isSubmitting}
            className="w-full bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition"
          >
            {isSubmitting ? 'Submitting...' : 'Submit Answer'}
          </button>
        </div>

        {/* Result Card */}
        {result && (
          <div className={`rounded-lg shadow p-8 ${result.correct ? 'bg-green-50 border-2 border-green-200' : 'bg-red-50 border-2 border-red-200'}`}>
            <div className="flex items-center mb-4">
              <div className={`text-4xl mr-4 ${result.correct ? 'text-green-600' : 'text-red-600'}`}>
                {result.correct ? '✓' : '✗'}
              </div>
              <div>
                <h3 className={`text-xl font-bold ${result.correct ? 'text-green-800' : 'text-red-800'}`}>
                  {result.correct ? 'Correct!' : 'Incorrect'}
                </h3>
                <p className={result.correct ? 'text-green-700' : 'text-red-700'}>{result.feedback}</p>
              </div>
            </div>

            {result.points_earned > 0 && (
              <p className="text-lg font-semibold text-gray-700 mb-4">
                Points earned: {result.points_earned}
              </p>
            )}

            <button
              onClick={loadNextTask}
              className="bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition"
            >
              Next Task
            </button>
          </div>
        )}
      </main>
    </div>
  )
}
