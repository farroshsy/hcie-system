/**
 * Profile Screen
 * 
 * Displays user profile information and allows profile management.
 */

'use client'

import { useEffect, useState } from 'react'
import { useAuth } from '@/contexts'
import { useUserInsights } from '@/hooks/useAnalytics'
import type { User } from '@/lib/core'
import { TrendingUp, Target, BarChart3, Activity } from 'lucide-react'

export default function ProfileScreen() {
  const { user, refreshUser } = useAuth()
  const [isEditing, setIsEditing] = useState(false)
  const [editedUser, setEditedUser] = useState<Partial<User>>({})

  // User insights from analytics
  const { data: userInsightsData } = useUserInsights(user?.id || '')
  const userInsights = userInsightsData?.data

  useEffect(() => {
    if (user) {
      setEditedUser(user)
    }
  }, [user])

  const handleSave = async () => {
    // In production, this would call the updateProfile service
    setIsEditing(false)
    await refreshUser()
  }

  if (!user) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-gray-600">Loading profile...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-8">
        <div className="bg-white rounded-lg shadow p-8">
          {/* Profile Header */}
          <div className="flex items-center mb-8">
            <div className="w-20 h-20 bg-blue-500 rounded-full flex items-center justify-center text-white text-3xl font-bold">
              {user.email.charAt(0).toUpperCase()}
            </div>
            <div className="ml-6">
              <h2 className="text-2xl font-bold text-gray-900">{user.email}</h2>
              <p className="text-gray-600">{user.email}</p>
              <span className="inline-block px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium mt-2">
                {user.role}
              </span>
            </div>
          </div>

          {/* Profile Details */}
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
              {isEditing ? (
                <input
                  type="email"
                  value={editedUser.email || ''}
                  onChange={(e) => setEditedUser({ ...editedUser, email: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              ) : (
                <p className="text-gray-900">{user.email}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Account Status</label>
              <p className={`text-sm font-medium ${user.is_active ? 'text-green-600' : 'text-red-600'}`}>
                {user.is_active ? 'Active' : 'Inactive'}
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Member Since</label>
              <p className="text-gray-900">{new Date(user.created_at).toLocaleDateString()}</p>
            </div>

            {user.last_login && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Last Login</label>
                <p className="text-gray-900">{new Date(user.last_login).toLocaleString()}</p>
              </div>
            )}

            {/* Permissions */}
            {user.permissions && user.permissions.length > 0 && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Permissions</label>
                <div className="flex flex-wrap gap-2">
                  {user.permissions.map((permission) => (
                    <span
                      key={permission}
                      className="px-3 py-1 bg-gray-100 text-gray-800 rounded-full text-sm"
                    >
                      {permission}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* User Insights */}
            {userInsights && (
              <div className="pt-6 border-t">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Learning Insights</h3>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div className="bg-blue-50 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <TrendingUp className="w-4 h-4 text-blue-600" />
                      <span className="text-sm font-medium text-gray-700">Learning Velocity</span>
                    </div>
                    <p className="text-2xl font-bold text-gray-900">{(userInsights.learning_velocity || 0).toFixed(3)}</p>
                  </div>
                  <div className="bg-green-50 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Target className="w-4 h-4 text-green-600" />
                      <span className="text-sm font-medium text-gray-700">Concept Diversity</span>
                    </div>
                    <p className="text-2xl font-bold text-gray-900">{(userInsights.concept_diversity || 0).toFixed(2)}</p>
                  </div>
                  <div className="bg-purple-50 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <BarChart3 className="w-4 h-4 text-purple-600" />
                      <span className="text-sm font-medium text-gray-700">Engagement Score</span>
                    </div>
                    <p className="text-2xl font-bold text-gray-900">{(userInsights.engagement_score || 0).toFixed(2)}</p>
                  </div>
                  <div className="bg-orange-50 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Activity className="w-4 h-4 text-orange-600" />
                      <span className="text-sm font-medium text-gray-700">Predicted Performance</span>
                    </div>
                    <p className="text-2xl font-bold text-gray-900">
                      {((userInsights.predicted_performance || 0) * 100).toFixed(1)}%
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-4 pt-6 border-t">
              {isEditing ? (
                <>
                  <button
                    onClick={handleSave}
                    className="bg-blue-600 text-white px-6 py-2 rounded-lg font-semibold hover:bg-blue-700 transition"
                  >
                    Save Changes
                  </button>
                  <button
                    onClick={() => {
                      setIsEditing(false)
                      setEditedUser(user)
                    }}
                    className="bg-gray-200 text-gray-800 px-6 py-2 rounded-lg font-semibold hover:bg-gray-300 transition"
                  >
                    Cancel
                  </button>
                </>
              ) : (
                <button
                  onClick={() => setIsEditing(true)}
                  className="bg-blue-600 text-white px-6 py-2 rounded-lg font-semibold hover:bg-blue-700 transition"
                >
                  Edit Profile
                </button>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
