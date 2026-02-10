"use client"

import { Badge } from "@/components/ui/badge"

const INTENT_COLORS: Record<string, string> = {
  course_inquiry: "bg-blue-100 text-blue-800",
  enrollment: "bg-green-100 text-green-800",
  fee_query: "bg-amber-100 text-amber-800",
  attendance_query: "bg-purple-100 text-purple-800",
  counseling: "bg-pink-100 text-pink-800",
  complaint: "bg-red-100 text-red-800",
  general: "bg-gray-100 text-gray-800",
  class_related: "bg-cyan-100 text-cyan-800",
  lab_related: "bg-teal-100 text-teal-800",
}

interface IntentBadgeProps {
  intent: string
  confidence?: number
}

export function IntentBadge({ intent, confidence }: IntentBadgeProps) {
  const colorClass = INTENT_COLORS[intent] ?? INTENT_COLORS.general

  return (
    <Badge variant="outline" className={colorClass}>
      {intent.replace(/_/g, " ")}
      {confidence !== undefined && (
        <span className="ml-1 opacity-70">{Math.round(confidence * 100)}%</span>
      )}
    </Badge>
  )
}
