/**
 * Authentication Service Implementation
 * 
 * Implements the IAuthService protocol for authentication and authorization operations.
 * This service handles user authentication, token management, and permission checks.
 */

import type {
  IAuthService,
  AuthServiceConfig,
  User,
  AuthResponse,
  LoginCredentials,
  RegistrationData,
  TokenRefreshRequest,
  TokenRefreshResponse,
  PermissionCheck,
} from '../interfaces'
import { buildApiUrl } from '@/lib/api/backend-url'

/**
 * Authentication Service Implementation
 */
export class AuthService implements IAuthService {
  private apiUrl: string
  private tokenStorageKey: string
  private refreshTokenStorageKey: string
  private userStorageKey: string
  private autoRefresh: boolean
  private refreshThreshold: number
  private debug: boolean
  private refreshTimer: NodeJS.Timeout | null = null

  constructor(config: AuthServiceConfig) {
    this.apiUrl = config.apiUrl
    this.tokenStorageKey = config.tokenStorageKey || 'access_token'
    this.refreshTokenStorageKey = config.refreshTokenStorageKey || 'refresh_token'
    this.userStorageKey = config.userStorageKey || 'user'
    this.autoRefresh = config.autoRefresh ?? true
    this.refreshThreshold = config.refreshThreshold || 300 // 5 minutes default
    this.debug = config.debug || false
  }

  /**
   * Authenticate a user with credentials
   */
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    this.log('Logging in user:', credentials.email)
    
    try {
      const response = await fetch(this.authUrl('/login'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials),
      })

      if (!response.ok) {
        throw new Error(`Login failed: ${response.statusText}`)
      }

      const raw = await response.json()
      const data = this.normalizeAuthResponse(raw)
      
      // Store tokens and user
      this.setAccessToken(data.access_token)
      this.setRefreshToken(data.refresh_token)
      this.setUser(data.user)
      
      // Start auto-refresh if enabled
      if (this.autoRefresh) {
        this.startAutoRefresh(data.expires_in)
      }
      
      return data
    } catch (error) {
      this.log('Error during login:', error)
      throw new Error(`Login failed: ${error instanceof Error ? error.message : String(error)}`)
    }
  }

  /**
   * Register a new user
   */
  async register(data: RegistrationData): Promise<AuthResponse> {
    this.log('Registering user:', data.username)
    
    try {
      const response = await fetch(this.authUrl('/register'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: data.email,
          password: data.password,
          name: data.username,
          role: 'student',
        }),
      })

      if (!response.ok) {
        throw new Error(`Registration failed: ${response.statusText}`)
      }

      const raw = await response.json()
      const authResponse = this.normalizeAuthResponse(raw)
      
      // Store tokens and user
      this.setAccessToken(authResponse.access_token)
      this.setRefreshToken(authResponse.refresh_token)
      this.setUser(authResponse.user)
      
      // Start auto-refresh if enabled
      if (this.autoRefresh) {
        this.startAutoRefresh(authResponse.expires_in)
      }
      
      return authResponse
    } catch (error) {
      this.log('Error during registration:', error)
      throw new Error(`Registration failed: ${error instanceof Error ? error.message : String(error)}`)
    }
  }

  /**
   * Logout the current user
   */
  async logout(refreshToken: string): Promise<void> {
    this.log('Logging out user')
    
    try {
      await fetch(this.authUrl('/logout'), {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.getAccessToken()}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      })
    } catch (error) {
      this.log('Error during logout:', error)
      // Continue with cleanup even if API call fails
    } finally {
      // Clear stored data
      this.clearAuthData()
      this.stopAutoRefresh()
    }
  }

  /**
   * Refresh access token using refresh token
   */
  async refreshToken(request: TokenRefreshRequest): Promise<TokenRefreshResponse> {
    this.log('Refreshing access token')
    
    try {
      const response = await fetch(this.authUrl('/refresh'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      })

      if (!response.ok) {
        throw new Error(`Token refresh failed: ${response.statusText}`)
      }

      const raw = await response.json()
      const data = {
        token_type: raw.token_type || 'bearer',
        expires_in: raw.expires_in || 3600,
        ...raw,
      } as TokenRefreshResponse
      
      // Update access token
      this.setAccessToken(data.access_token)
      
      // Restart auto-refresh with new expiration
      if (this.autoRefresh) {
        this.startAutoRefresh(data.expires_in)
      }
      
      return data
    } catch (error) {
      this.log('Error refreshing token:', error)
      // Clear auth data on refresh failure
      this.clearAuthData()
      this.stopAutoRefresh()
      throw new Error(`Token refresh failed: ${error instanceof Error ? error.message : String(error)}`)
    }
  }

  /**
   * Get current user profile
   */
  async getProfile(): Promise<User> {
    this.log('Fetching user profile')
    
    try {
      const response = await fetch(this.authUrl('/profile'), {
        headers: {
          'Authorization': `Bearer ${this.getAccessToken()}`,
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`Failed to fetch profile: ${response.statusText}`)
      }

      const data = await response.json()
      const user = this.normalizeUser(data.user || data)
      this.setUser(user)
      
      return user
    } catch (error) {
      this.log('Error fetching profile:', error)
      throw new Error(`Unable to fetch profile: ${error instanceof Error ? error.message : String(error)}`)
    }
  }

  /**
   * Update user profile
   */
  async updateProfile(updates: Partial<User>): Promise<User> {
    this.log('Updating user profile')
    
    try {
      const response = await fetch(this.authUrl('/profile'), {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${this.getAccessToken()}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updates),
      })

      if (!response.ok) {
        throw new Error(`Failed to update profile: ${response.statusText}`)
      }

      const data = await response.json()
      const user = this.normalizeUser(data.user || data)
      this.setUser(user)
      
      return user
    } catch (error) {
      this.log('Error updating profile:', error)
      throw new Error(`Unable to update profile: ${error instanceof Error ? error.message : String(error)}`)
    }
  }

  /**
   * Check if user has a specific permission
   */
  async hasPermission(permission: string): Promise<PermissionCheck> {
    this.log('Checking permission:', permission)
    
    const user = this.getUser()
    if (!user) {
      return {
        has_permission: false,
        permission,
        user_permissions: [],
      }
    }

    return {
      has_permission: user.permissions.includes(permission),
      permission,
      user_permissions: user.permissions,
    }
  }

  /**
   * Check if user has any of the specified permissions
   */
  async hasAnyPermission(permissions: string[]): Promise<boolean> {
    const user = this.getUser()
    if (!user) return false

    return permissions.some(permission => user.permissions.includes(permission))
  }

  /**
   * Check if user has all of the specified permissions
   */
  async hasAllPermissions(permissions: string[]): Promise<boolean> {
    const user = this.getUser()
    if (!user) return false

    return permissions.every(permission => user.permissions.includes(permission))
  }

  /**
   * Get access token from storage
   */
  private getAccessToken(): string {
    return localStorage.getItem(this.tokenStorageKey) || localStorage.getItem('access_token') || ''
  }

  /**
   * Set access token in storage
   */
  private setAccessToken(token: string): void {
    localStorage.setItem(this.tokenStorageKey, token)
    if (this.tokenStorageKey !== 'access_token') {
      localStorage.setItem('access_token', token)
    }
  }

  /**
   * Get refresh token from storage
   */
  private getRefreshToken(): string {
    return localStorage.getItem(this.refreshTokenStorageKey) || localStorage.getItem('refresh_token') || ''
  }

  /**
   * Set refresh token in storage
   */
  private setRefreshToken(token: string): void {
    localStorage.setItem(this.refreshTokenStorageKey, token)
    if (this.refreshTokenStorageKey !== 'refresh_token') {
      localStorage.setItem('refresh_token', token)
    }
  }

  /**
   * Get user from storage
   */
  private getUser(): User | null {
    const userStr = localStorage.getItem(this.userStorageKey)
    if (!userStr) return null
    try {
      return JSON.parse(userStr) as User
    } catch {
      return null
    }
  }

  /**
   * Set user in storage
   */
  private setUser(user: User): void {
    localStorage.setItem(this.userStorageKey, JSON.stringify(user))
  }

  /**
   * Clear all authentication data
   */
  private clearAuthData(): void {
    localStorage.removeItem(this.tokenStorageKey)
    localStorage.removeItem('access_token')
    localStorage.removeItem(this.refreshTokenStorageKey)
    localStorage.removeItem('refresh_token')
    localStorage.removeItem(this.userStorageKey)
  }

  private authUrl(path: string): string {
    return buildApiUrl(this.apiUrl, `/v3/auth${path}`)
  }

  private normalizeAuthResponse(raw: any): AuthResponse {
    return {
      token_type: raw.token_type || 'bearer',
      expires_in: raw.expires_in || 3600,
      ...raw,
      user: this.normalizeUser(raw.user),
    } as AuthResponse
  }

  private normalizeUser(raw: any): User {
    const id = raw?.id || raw?.user_id || raw?.sub || raw?.email || 'unknown-user'
    const email = raw?.email || `${id}@local.hcie`
    // Pass through whatever role the backend assigns. Backend roles include
    // 'student', 'user', 'researcher', 'admin' — collapsing to user/admin only
    // breaks role-gated UI for researchers.
    const role = (typeof raw?.role === 'string' ? raw.role : 'user') as User['role']

    return {
      id,
      username: raw?.username || email.split('@')[0] || id,
      email,
      role,
      permissions: raw?.permissions || ['read:learning', 'write:learning'],
      created_at: raw?.created_at || new Date(0).toISOString(),
      last_login: raw?.last_login,
      is_active: raw?.is_active ?? true,
    }
  }

  /**
   * Start automatic token refresh
   */
  private startAutoRefresh(expiresIn: number): void {
    this.stopAutoRefresh()
    
    const refreshTime = (expiresIn - this.refreshThreshold) * 1000
    this.log('Starting auto-refresh in', refreshTime, 'ms')
    
    this.refreshTimer = setTimeout(async () => {
      try {
        const token = this.getRefreshToken()
        if (token) {
          await this.refreshToken({ refresh_token: token })
        }
      } catch (error) {
        this.log('Auto-refresh failed:', error)
      }
    }, refreshTime)
  }

  /**
   * Stop automatic token refresh
   */
  private stopAutoRefresh(): void {
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer)
      this.refreshTimer = null
    }
  }

  /**
   * Debug logging
   */
  private log(...args: unknown[]): void {
    if (this.debug) {
      console.log('[AuthService]', ...args)
    }
  }
}
