/**
 * Authentication Validator Implementation
 * 
 * Implements the IAuthValidator protocol for validating authentication-related data.
 * This validator uses Zod schemas for runtime type checking and validation.
 */

import { z } from 'zod'
import type {
  IAuthValidator,
  LoginCredentials,
  RegistrationData,
  User,
  AuthResponse,
} from '../interfaces'

/**
 * Zod schemas for authentication-related data
 */
const LoginCredentialsSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
})

const RegistrationDataSchema = z.object({
  username: z.string().min(3),
  email: z.string().email(),
  password: z.string().min(8),
  confirm_password: z.string().min(8),
}).refine((data) => data.password === data.confirm_password, {
  message: "Passwords don't match",
  path: ["confirm_password"],
})

const UserSchema = z.object({
  id: z.string(),
  username: z.string(),
  email: z.string().email(),
  role: z.enum(['user', 'admin']),
  permissions: z.array(z.string()),
  created_at: z.string(),
  last_login: z.string().optional(),
  is_active: z.boolean(),
})

const AuthResponseSchema = z.object({
  access_token: z.string(),
  refresh_token: z.string(),
  token_type: z.string(),
  expires_in: z.number(),
  user: UserSchema,
})

/**
 * Authentication Validator Implementation
 */
export class AuthValidator implements IAuthValidator {
  /**
   * Validate login credentials
   */
  validateCredentials(credentials: unknown): credentials is LoginCredentials {
    return LoginCredentialsSchema.safeParse(credentials).success
  }

  /**
   * Validate registration data
   */
  validateRegistration(data: unknown): data is RegistrationData {
    return RegistrationDataSchema.safeParse(data).success
  }

  /**
   * Validate user object
   */
  validateUser(user: unknown): user is User {
    return UserSchema.safeParse(user).success
  }

  /**
   * Validate authentication response
   */
  validateAuthResponse(response: unknown): response is AuthResponse {
    return AuthResponseSchema.safeParse(response).success
  }

  /**
   * Validate and parse login credentials (throws on error)
   */
  parseCredentials(credentials: unknown): LoginCredentials {
    return LoginCredentialsSchema.parse(credentials)
  }

  /**
   * Validate and parse registration data (throws on error)
   */
  parseRegistration(data: unknown): RegistrationData {
    return RegistrationDataSchema.parse(data)
  }

  /**
   * Validate and parse user object (throws on error)
   */
  parseUser(user: unknown): User {
    return UserSchema.parse(user)
  }

  /**
   * Validate and parse auth response (throws on error)
   */
  parseAuthResponse(response: unknown): AuthResponse {
    return AuthResponseSchema.parse(response)
  }
}
