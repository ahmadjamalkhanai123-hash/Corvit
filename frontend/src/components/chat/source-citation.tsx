"use client"

import { useState } from "react"
import { ChevronDown, ChevronRight, FileText } from "lucide-react"
import type { SourceCitation as SourceCitationType } from "@/types/api"

interface SourceCitationProps {
  source: SourceCitationType
}

export function SourceCitation({ source }: SourceCitationProps) {
  const [expanded, setExpanded] = useState(false)

  return (
    <button
      onClick={() => setExpanded(!expanded)}
      className="w-full rounded border bg-background/50 p-2 text-left text-xs transition-colors hover:bg-background"
    >
      <div className="flex items-center gap-1.5">
        {expanded ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
        <FileText className="h-3 w-3 text-muted-foreground" />
        <span className="font-medium capitalize">{source.collection}</span>
        <span className="ml-auto text-muted-foreground">{Math.round(source.score * 100)}%</span>
      </div>
      {expanded && (
        <p className="mt-1.5 whitespace-pre-wrap text-muted-foreground">{source.content}</p>
      )}
    </button>
  )
}
