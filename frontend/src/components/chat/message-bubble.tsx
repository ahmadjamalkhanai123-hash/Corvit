"use client"

import ReactMarkdown from "react-markdown"
import { cn } from "@/lib/utils"
import { IntentBadge } from "./intent-badge"
import { SourceCitation } from "./source-citation"
import type { ChatMessage } from "@/hooks/use-chat"

interface MessageBubbleProps {
  message: ChatMessage
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user"

  return (
    <div className={cn("flex w-full", isUser ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "max-w-[80%] rounded-lg px-4 py-2.5",
          isUser
            ? "bg-primary text-primary-foreground"
            : "bg-muted text-foreground",
        )}
      >
        {!isUser && message.intent && (
          <div className="mb-2">
            <IntentBadge intent={message.intent} confidence={message.confidence} />
          </div>
        )}

        <div className={cn("prose prose-sm max-w-none", isUser && "prose-invert")}>
          <ReactMarkdown>{message.content}</ReactMarkdown>
        </div>

        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="mt-2 space-y-1">
            {message.sources.map((source, i) => (
              <SourceCitation key={i} source={source} />
            ))}
          </div>
        )}

        <p className={cn("mt-1 text-xs", isUser ? "text-primary-foreground/70" : "text-muted-foreground")}>
          {message.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
        </p>
      </div>
    </div>
  )
}
