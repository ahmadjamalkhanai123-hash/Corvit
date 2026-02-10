"use client"

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react"
import { useRouter } from "next/navigation"
import type { AuthUser } from "@/types/auth"
import * as authLib from "@/lib/auth"

interface AuthState {
  user: AuthUser | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (username: string, password: string) => Promise<void>
  register: (username: string, email: string, password: string, role: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    const token = authLib.getStoredToken()
    if (!token) {
      setIsLoading(false)
      return
    }
    authLib
      .getMe()
      .then(setUser)
      .catch(() => {
        authLib.logout()
      })
      .finally(() => setIsLoading(false))
  }, [])

  const login = useCallback(
    async (username: string, password: string) => {
      const res = await authLib.login({ username, password })
      setUser(res.user)
      router.push("/dashboard")
    },
    [router],
  )

  const register = useCallback(
    async (username: string, email: string, password: string, role: string) => {
      await authLib.register({ username, email, password, role })
      router.push("/login")
    },
    [router],
  )

  const logout = useCallback(() => {
    authLib.logout()
    setUser(null)
    router.push("/login")
  }, [router])

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error("useAuth must be used within AuthProvider")
  return ctx
}
