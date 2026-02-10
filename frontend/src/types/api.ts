export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}

export interface ErrorResponse {
  detail: string
}

export interface HealthCheck {
  status: string
  postgres: string
  redis: string
  ollama: string
  vectordb: string
}

export interface DashboardStats {
  kpis: {
    total_students: number
    active_courses: number
    active_batches: number
    total_revenue: number
    overdue_fees_count: number
    overdue_fees_amount: number
    average_attendance: number
  }
  attendance_trend: { date: string; percentage: number }[]
  enrollment_by_course: { course: string; count: number }[]
  recent_activity: {
    id: string
    event_type: string
    actor: string
    target?: string | null
    timestamp?: string | null
  }[]
  timestamp: string
}

export interface ChatRequest {
  message: string
  session_id?: string
}

export interface ChatResponse {
  response: string
  intent: string
  confidence: number
  sources: SourceCitation[]
  session_id: string
}

export interface SourceCitation {
  collection: string
  content: string
  score: number
}
