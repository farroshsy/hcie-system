'use client'

import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { User, AuthResponse } from '@/types'
import { apiClient } from '@/lib/api-client'

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<AuthResponse>
  logout: () => Promise<void>
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check for existing token on mount
    const token = localStorage.getItem('access_token')
    if (token) {
      fetchProfile()
    } else {
      setLoading(false)
    }
  }, [])

  const fetchProfile = async () => {
    try {
      const profile = await apiClient.getProfile()
      setUser(profile.user)
    } catch (error) {
      console.error('Failed to fetch profile:', error)
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    } finally {
      setLoading(false)
    }
  }

  const login = async (email: string, password: string): Promise<AuthResponse> => {
    setLoading(true)
    try {
      // Bypass login for testing
      if (email === 'demo' && password === 'demo') {
        const demoUser: User = {
          id: 'demo-user-123',
          username: 'demo',
          email: 'demo@hcie.com',
          role: 'user',
          permissions: ['read:learning', 'write:learning'],
          created_at: new Date().toISOString(),
        }
        
        setUser(demoUser)
        
        localStorage.setItem('access_token', 'demo-token')
        localStorage.setItem('refresh_token', 'demo-refresh-token')
        localStorage.setItem('user', JSON.stringify(demoUser))
        
        setLoading(false)
        return { user: demoUser, access_token: 'demo-token', refresh_token: 'demo-refresh-token', token_type: 'bearer', expires_in: 3600 }
      }

      const response = await apiClient.login(email, password)
      setUser(response.user)
      return response
    } catch (error) {
      console.error('Login failed:', error)
      throw error
    } finally {
      setLoading(false)
    }
  }

  const logout = async () => {
    await apiClient.logout()
    setUser(null)
  }

  const value = {
    user,
    loading,
    login,
    logout,
    isAuthenticated: !!user,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
