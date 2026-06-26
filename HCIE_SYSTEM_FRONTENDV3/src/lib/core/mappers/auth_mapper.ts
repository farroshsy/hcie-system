/**
 * Authentication Mapper Implementation
 * 
 * Implements the IAuthMapper protocol for mapping authentication data between different representations.
 * This mapper handles conversion between API responses and domain models.
 */

import type {
  IAuthMapper,
  User,
  AuthResponse,
  LoginCredentials,
  RegistrationData,
} from '../interfaces'

/**
 * Authentication Mapper Implementation
 */
export class AuthMapper implements IAuthMapper {
  /**
   * Map API response to auth response
   */
  apiToAuthResponse(apiResponse: unknown): AuthResponse {
    const response = apiResponse as Record<string, unknown>
    
    return {
      access_token: response.access_token as string,
      refresh_token: response.refresh_token as string,
      token_type: response.token_type as string || 'bearer',
      expires_in: (response.expires_in as number) || 3600,
      user: this.apiToUser(response.user),
    }
  }

  /**
   * Map login credentials to API request format
   */
  credentialsToApi(credentials: LoginCredentials): Record<string, unknown> {
    return {
      email: credentials.email,
      password: credentials.password,
    }
  }

  /**
   * Map registration data to API request format
   */
  registrationToApi(data: RegistrationData): Record<string, unknown> {
    return {
      username: data.username,
      email: data.email,
      password: data.password,
      confirm_password: data.confirm_password,
    }
  }

  /**
   * Map API response to user profile
   */
  apiToUser(apiResponse: unknown): User {
    const response = apiResponse as Record<string, unknown>
    
    return {
      id: response.id as string,
      username: response.username as string,
      email: response.email as string,
      role: (response.role as 'user' | 'admin') || 'user',
      permissions: (response.permissions as string[]) || [],
      created_at: response.created_at as string || new Date().toISOString(),
      last_login: response.last_login as string,
      is_active: (response.is_active as boolean) ?? true,
    }
  }
}
