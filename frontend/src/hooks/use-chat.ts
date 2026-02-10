"use client"

import { useCallback, useState } from "react"
import { apiClient } from "@/lib/api-client"
import type { ChatRequest, ChatResponse } from "@/types/api"

export interface ChatMessage {
  id: string
  role: "user" | "agent"
  content: string
  intent?: string
  confidence?: number
  sources?: ChatResponse["sources"]
  timestamp: Date
}

export function useChat(initialSessionId?: string) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [sessionId, setSessionId] = useState<string | undefined>(initialSessionId)

  const sendMessage = useCallback(
    async (content: string) => {
      const userMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "user",
        content,
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, userMessage])
      setIsLoading(true)

      try {
        const res = await apiClient.post<ChatResponse>("/api/chat", {
          message: content,
          session_id: sessionId,
        } satisfies ChatRequest)

        setSessionId(res.session_id)

        const agentMessage: ChatMessage = {
          id: crypto.randomUUID(),
          role: "agent",
          content: res.response,
          intent: res.intent,
          confidence: res.confidence,
          sources: res.sources,
          timestamp: new Date(),
        }

        setMessages((prev) => [...prev, agentMessage])
      } catch {
        const errorMessage: ChatMessage = {
          id: crypto.randomUUID(),
          role: "agent",
          content: "Sorry, I encountered an error. Please try again.",
          timestamp: new Date(),
        }
        setMessages((prev) => [...prev, errorMessage])
      } finally {
        setIsLoading(false)
      }
    },
    [sessionId],
  )

  const clearMessages = useCallback(() => {
    setMessages([])
    setSessionId(undefined)
  }, [])

  return { messages, isLoading, sessionId, sendMessage, clearMessages }
}
