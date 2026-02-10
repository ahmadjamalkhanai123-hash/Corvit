"use client"

import { useEffect, useRef, useState } from "react"
import { Send } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { MessageBubble } from "./message-bubble"
import { TypingIndicator } from "./typing-indicator"
import type { ChatMessage } from "@/hooks/use-chat"

interface ChatThreadProps {
  messages: ChatMessage[]
  isLoading: boolean
  onSendMessage: (content: string) => void
}

export function ChatThread({ messages, isLoading, onSendMessage }: ChatThreadProps) {
  const [input, setInput] = useState("")
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, isLoading])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const trimmed = input.trim()
    if (!trimmed || isLoading) return
    onSendMessage(trimmed)
    setInput("")
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 overflow-y-auto p-4">
        <div className="mx-auto max-w-3xl space-y-4">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <h3 className="text-lg font-semibold">Corvit Assistant</h3>
              <p className="mt-1 text-sm text-muted-foreground max-w-sm">
                Ask me about courses, enrollment, attendance, fees, or anything about Corvit Systems.
              </p>
            </div>
          )}

          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}

          {isLoading && <TypingIndicator />}
          <div ref={messagesEndRef} />
        </div>
      </div>

      <div className="border-t p-4">
        <form onSubmit={handleSubmit} className="mx-auto flex max-w-3xl gap-2">
          <Input
            ref={inputRef}
            placeholder="Type your message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isLoading}
            className="flex-1"
          />
          <Button type="submit" size="icon" disabled={!input.trim() || isLoading}>
            <Send className="h-4 w-4" />
          </Button>
        </form>
      </div>
    </div>
  )
}
