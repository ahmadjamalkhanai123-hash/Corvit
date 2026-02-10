import type { UserRole } from "./entities"

export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
  role: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: AuthUser
}

export interface AuthUser {
  id: string
  username: string
  email: string
  role: UserRole
  is_active: boolean
  created_at: string
}
