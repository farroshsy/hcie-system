/**
 * Authentication Interface Protocol
 * 
 * Defines the contract for authentication and authorization operations in the HCIE system.
 * This protocol ensures type safety and provides clear contracts for user authentication,
 * token management, and authorization.
 */

// ============================================================================
// Domain Types
// ============================================================================

/**
 * Represents a user in the system
 */
export interface User {
  /** Unique identifier for the user */
  id: string
  /** Username */
  username: string
  /** Email address */
  email: string
  /** User role — backend assigns one of these; frontend gates UI on `role`. */
  role: 'user' | 'student' | 'researcher' | 'admin'
  /** List of permissions */
  permissions: string[]
  /** Account creation timestamp */
  created_at: string
  /** Last login timestamp */
  last_login?: string
  /** Whether the account is active */
  is_active: boolean
}

/**
 * Represents authentication response
 */
export interface AuthResponse {
  /** JWT access token */
  access_token: string
  /** JWT refresh token */
  refresh_token: string
  /** Token type (usually "bearer") */
  token_type: string
  /** Token expiration time in seconds */
  expires_in: number
  /** User information */
  user: User
}

/**
 * Represents login credentials
 */
export interface LoginCredentials {
  /** Email address */
  email: string
  /** User password */
  password: string
}

/**
 * Represents registration data
 */
export interface RegistrationData {
  /** Username */
  username: string
  /** Email address */
  email: string
  /** Password */
  password: string
  /** Confirm password */
  confirm_password: string
}

/**
 * Represents token refresh request
 */
export interface TokenRefreshRequest {
  /** Refresh token */
  refresh_token: string
}

/**
 * Represents token refresh response
 */
export interface TokenRefreshResponse {
  /** New access token */
  access_token: string
  /** Token type */
  token_type: string
  /** Token expiration time in seconds */
  expires_in: number
}

/**
 * Represents permission check result
 */
export interface PermissionCheck {
  /** Whether the user has the permission */
  has_permission: boolean
  /** Required permission */
  permission: string
  /** User's permissions */
  user_permissions: string[]
}

// ============================================================================
// Service Protocol
// ============================================================================

/**
 * Authentication Service Protocol
 * 
 * Defines the contract for authentication and authorization operations.
 * All implementations must adhere to this protocol.
 */
export interface IAuthService {
  /**
   * Authenticate a user with credentials
   * @param credentials - Login credentials
   * @returns Promise resolving to authentication response
   * @throws Error if credentials are invalid or API request fails
   */
  login(credentials: LoginCredentials): Promise<AuthResponse>

  /**
   * Register a new user
   * @param data - Registration data
   * @returns Promise resolving to authentication response
   * @throws Error if registration fails or API request fails
   */
  register(data: RegistrationData): Promise<AuthResponse>

  /**
   * Logout the current user
   * @param refreshToken - Refresh token to invalidate
   * @returns Promise resolving when logout is complete
   * @throws Error if logout fails or API request fails
   */
  logout(refreshToken: string): Promise<void>

  /**
   * Refresh access token using refresh token
   * @param request - Token refresh request
   * @returns Promise resolving to token refresh response
   * @throws Error if refresh token is invalid or expired
   */
  refreshToken(request: TokenRefreshRequest): Promise<TokenRefreshResponse>

  /**
   * Get current user profile
   * @returns Promise resolving to user profile
   * @throws Error if user not authenticated or API request fails
   */
  getProfile(): Promise<User>

  /**
   * Update user profile
   * @param updates - User profile updates
   * @returns Promise resolving to updated user profile
   * @throws Error if update fails or API request fails
   */
  updateProfile(updates: Partial<User>): Promise<User>

  /**
   * Check if user has a specific permission
   * @param permission - Permission to check
   * @returns Promise resolving to permission check result
   */
  hasPermission(permission: string): Promise<PermissionCheck>

  /**
   * Check if user has any of the specified permissions
   * @param permissions - List of permissions to check
   * @returns Promise resolving to whether user has any permission
   */
  hasAnyPermission(permissions: string[]): Promise<boolean>

  /**
   * Check if user has all of the specified permissions
   * @param permissions - List of permissions to check
   * @returns Promise resolving to whether user has all permissions
   */
  hasAllPermissions(permissions: string[]): Promise<boolean>
}

// ============================================================================
// Validator Protocol
// ============================================================================

/**
 * Authentication Validator Protocol
 * 
 * Defines the contract for validating authentication-related data.
 */
export interface IAuthValidator {
  /**
   * Validate login credentials
   * @param credentials - Credentials to validate
   * @returns Whether the credentials are valid
   */
  validateCredentials(credentials: unknown): credentials is LoginCredentials

  /**
   * Validate registration data
   * @param data - Registration data to validate
   * @returns Whether the registration data is valid
   */
  validateRegistration(data: unknown): data is RegistrationData

  /**
   * Validate user object
   * @param user - User to validate
   * @returns Whether the user is valid
   */
  validateUser(user: unknown): user is User

  /**
   * Validate authentication response
   * @param response - Auth response to validate
   * @returns Whether the response is valid
   */
  validateAuthResponse(response: unknown): response is AuthResponse
}

// ============================================================================
// Mapper Protocol
// ============================================================================

/**
 * Authentication Mapper Protocol
 * 
 * Defines the contract for mapping authentication data between different representations.
 */
export interface IAuthMapper {
  /**
   * Map API response to auth response
   * @param apiResponse - Raw API response
   * @returns Mapped auth response
   */
  apiToAuthResponse(apiResponse: unknown): AuthResponse

  /**
   * Map login credentials to API request format
   * @param credentials - Login credentials
   * @returns API request format
   */
  credentialsToApi(credentials: LoginCredentials): Record<string, unknown>

  /**
   * Map registration data to API request format
   * @param data - Registration data
   * @returns API request format
   */
  registrationToApi(data: RegistrationData): Record<string, unknown>

  /**
   * Map API response to user profile
   * @param apiResponse - Raw API response
   * @returns Mapped user profile
   */
  apiToUser(apiResponse: unknown): User
}

// ============================================================================
// Factory Protocol
// ============================================================================

/**
 * Authentication Service Factory Protocol
 * 
 * Defines the contract for creating authentication service instances.
 */
export interface IAuthServiceFactory {
  /**
   * Create an authentication service instance
   * @param config - Service configuration
   * @returns Authentication service instance
   */
  create(config: AuthServiceConfig): IAuthService

  /**
   * Create an authentication validator instance
   * @returns Authentication validator instance
   */
  createValidator(): IAuthValidator

  /**
   * Create an authentication mapper instance
   * @returns Authentication mapper instance
   */
  createMapper(): IAuthMapper
}

/**
 * Authentication service configuration
 */
export interface AuthServiceConfig {
  /** API base URL */
  apiUrl: string
  /** Token storage key */
  tokenStorageKey?: string
  /** Refresh token storage key */
  refreshTokenStorageKey?: string
  /** User storage key */
  userStorageKey?: string
  /** Enable automatic token refresh */
  autoRefresh?: boolean
  /** Token refresh threshold (seconds before expiration) */
  refreshThreshold?: number
  /** Enable debug logging */
  debug?: boolean
}
