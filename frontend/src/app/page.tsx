"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/hooks/use-auth"
import { LoadingSpinner } from "@/components/shared/loading-spinner"

export default function RootPage() {
  const { isAuthenticated, isLoading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!isLoading) {
      router.replace(isAuthenticated ? "/dashboard" : "/login")
    }
  }, [isAuthenticated, isLoading, router])

  return (
    <div className="flex h-screen items-center justify-center">
      <LoadingSpinner size={32} />
    </div>
  )
}
