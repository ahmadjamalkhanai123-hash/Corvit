import { apiClient } from "./api-client"
import type { LoginRequest, RegisterRequest, TokenResponse, AuthUser } from "@/types/auth"

export async function login(data: LoginRequest): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>("/api/auth/login", data)
  localStorage.setItem("access_token", response.access_token)
  return response
}

export async function register(data: RegisterRequest): Promise<AuthUser> {
  return apiClient.post<AuthUser>("/api/auth/register", data)
}

export async function getMe(): Promise<AuthUser> {
  return apiClient.get<AuthUser>("/api/auth/me")
}

export function logout(): void {
  localStorage.removeItem("access_token")
}

export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null
  return localStorage.getItem("access_token")
}
