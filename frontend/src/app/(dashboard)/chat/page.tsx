"use client"

import { Plus } from "lucide-react"
import { Button } from "@/components/ui/button"
import { ChatThread } from "@/components/chat/chat-thread"
import { useChat } from "@/hooks/use-chat"
import { PageHeader } from "@/components/layout/page-header"

export default function ChatPage() {
  const { messages, isLoading, sendMessage, clearMessages } = useChat()

  return (
    <div className="flex h-full flex-col">
      <PageHeader
        title="Chat"
        breadcrumbs={[{ label: "Chat" }]}
        actions={
          <Button variant="outline" size="sm" onClick={clearMessages}>
            <Plus className="mr-2 h-4 w-4" />
            New Chat
          </Button>
        }
      />
      <div className="mt-4 flex-1 overflow-hidden rounded-md border">
        <ChatThread messages={messages} isLoading={isLoading} onSendMessage={sendMessage} />
      </div>
    </div>
  )
}
