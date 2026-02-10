"use client"

import useSWR from "swr"
import { Users, BookOpen, Banknote, CalendarCheck } from "lucide-react"
import { apiClient } from "@/lib/api-client"
import { formatCurrency, formatRelative } from "@/lib/utils"
import type { DashboardStats } from "@/types/api"
import { PageHeader } from "@/components/layout/page-header"
import { KPICard } from "@/components/charts/kpi-card"
import { LineChart } from "@/components/charts/line-chart"
import { BarChart } from "@/components/charts/bar-chart"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"

const fetcher = (url: string) => apiClient.get<DashboardStats>(url)

export default function DashboardPage() {
  const { data, isLoading } = useSWR("/api/dashboard/stats", fetcher, {
    refreshInterval: 30000,
  })

  if (isLoading || !data) {
    return (
      <div className="space-y-6">
        <PageHeader title="Dashboard" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-[120px]" />
          ))}
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          <Skeleton className="h-[320px]" />
          <Skeleton className="h-[320px]" />
        </div>
      </div>
    )
  }

  const { kpis, attendance_trend, enrollment_by_course, recent_activity } = data

  return (
    <div className="space-y-6">
      <PageHeader title="Dashboard" breadcrumbs={[{ label: "Dashboard" }]} />

      {/* KPI Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KPICard title="Total Students" value={kpis.total_students} icon={Users} />
        <KPICard title="Active Courses" value={kpis.active_courses} icon={BookOpen} />
        <KPICard title="Total Revenue" value={formatCurrency(kpis.total_revenue)} icon={Banknote} />
        <KPICard
          title="Avg Attendance"
          value={`${kpis.average_attendance}%`}
          icon={CalendarCheck}
        />
      </div>

      {/* Charts */}
      <div className="grid gap-4 md:grid-cols-2">
        <LineChart
          title="Attendance Trend (7 days)"
          data={attendance_trend}
          xKey="date"
          yKey="percentage"
        />
        <BarChart
          title="Enrollment by Course"
          data={enrollment_by_course}
          xKey="course"
          yKey="count"
        />
      </div>

      {/* Recent Activity + Overdue */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Recent Activity</CardTitle>
          </CardHeader>
          <CardContent>
            {recent_activity.length === 0 ? (
              <p className="text-sm text-muted-foreground">No recent activity</p>
            ) : (
              <div className="space-y-3">
                {recent_activity.map((event) => (
                  <div key={event.id} className="flex items-start justify-between gap-2">
                    <div className="space-y-0.5">
                      <p className="text-sm font-medium">{event.event_type}</p>
                      <p className="text-xs text-muted-foreground">
                        {event.actor}
                        {event.target ? ` → ${event.target}` : ""}
                      </p>
                    </div>
                    {event.timestamp && (
                      <span className="text-xs text-muted-foreground whitespace-nowrap">
                        {formatRelative(event.timestamp)}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Overdue Fees</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Overdue count</span>
                <Badge variant="destructive">{kpis.overdue_fees_count}</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Total overdue</span>
                <span className="text-lg font-bold text-destructive">
                  {formatCurrency(kpis.overdue_fees_amount)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Active batches</span>
                <span className="text-sm font-medium">{kpis.active_batches}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
