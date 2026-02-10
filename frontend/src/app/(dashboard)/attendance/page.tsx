"use client"

import { useState } from "react"
import useSWR from "swr"
import { toast } from "sonner"
import { CalendarCheck, Check, X, Clock } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { PageHeader } from "@/components/layout/page-header"
import { LoadingSpinner } from "@/components/shared/loading-spinner"
import { EmptyState } from "@/components/shared/empty-state"
import { useList } from "@/hooks/use-api"
import { apiClient } from "@/lib/api-client"
import type { Batch } from "@/types/entities"

interface AttendanceRecord {
  student_id: string
  status: "present" | "absent" | "late"
}

interface BatchStudent {
  id: string
  name: string
  email: string
  enrollment_status: string
  attendance_percentage: number
}

interface BatchStudentsResponse {
  batch_id: string
  batch_name: string
  students: BatchStudent[]
  total_enrolled: number
}

interface AttendanceReportStudent {
  student_id: string
  name: string
  present: number
  absent: number
  late: number
  percentage: number
  alert_level: string | null
}

interface AttendanceReport {
  batch_id: string
  batch_name: string
  period: { from: string; to: string }
  summary: { total_classes: number; average_attendance: number }
  students: AttendanceReportStudent[]
}

const ALERT_COLORS: Record<string, string> = {
  yellow: "bg-yellow-100 text-yellow-800",
  orange: "bg-orange-100 text-orange-800",
  red: "bg-red-100 text-red-800",
}

export default function AttendancePage() {
  const [selectedBatch, setSelectedBatch] = useState("")
  const [date, setDate] = useState(new Date().toISOString().split("T")[0])
  const [records, setRecords] = useState<Record<string, AttendanceRecord["status"]>>({})
  const [submitting, setSubmitting] = useState(false)

  const { data: batchesData } = useList<Batch>("batches", 1, 100)

  const { data: studentsData, isLoading: studentsLoading } = useSWR<BatchStudentsResponse>(
    selectedBatch ? `/api/batches/${selectedBatch}/students` : null,
    { fetcher: (url: string) => apiClient.get<BatchStudentsResponse>(url) },
  )

  const { data: reportData } = useSWR<AttendanceReport>(
    selectedBatch ? `/api/attendance/report/${selectedBatch}` : null,
    { fetcher: (url: string) => apiClient.get<AttendanceReport>(url) },
  )

  const toggleStatus = (studentId: string) => {
    const current = records[studentId] ?? "present"
    const next = current === "present" ? "absent" : current === "absent" ? "late" : "present"
    setRecords({ ...records, [studentId]: next })
  }

  const handleBulkMark = async () => {
    if (!selectedBatch || !studentsData) return
    setSubmitting(true)
    try {
      const attendanceRecords = studentsData.students.map((s) => ({
        student_id: s.id,
        status: records[s.id] ?? "present",
      }))
      await apiClient.post("/api/attendance/mark", {
        batch_id: selectedBatch,
        date,
        records: attendanceRecords,
      })
      toast.success(`Attendance marked for ${attendanceRecords.length} students`)
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Failed to mark attendance")
    } finally {
      setSubmitting(false)
    }
  }

  const statusIcon = (status: string) => {
    switch (status) {
      case "present":
        return <Check className="h-4 w-4 text-green-600" />
      case "absent":
        return <X className="h-4 w-4 text-red-600" />
      case "late":
        return <Clock className="h-4 w-4 text-yellow-600" />
      default:
        return null
    }
  }

  return (
    <div className="space-y-4">
      <PageHeader title="Attendance" breadcrumbs={[{ label: "Attendance" }]} />

      <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
        <div className="w-full sm:w-64">
          <Label>Batch</Label>
          <Select value={selectedBatch} onValueChange={setSelectedBatch}>
            <SelectTrigger><SelectValue placeholder="Select batch" /></SelectTrigger>
            <SelectContent>
              {(batchesData?.items ?? []).map((b) => (
                <SelectItem key={b.id} value={b.id}>{b.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="w-full sm:w-48">
          <Label>Date</Label>
          <Input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
        </div>
        <Button onClick={handleBulkMark} disabled={!selectedBatch || submitting || !studentsData?.students.length}>
          <CalendarCheck className="mr-2 h-4 w-4" />
          {submitting ? "Marking..." : "Mark Attendance"}
        </Button>
      </div>

      {!selectedBatch ? (
        <EmptyState title="Select a batch" description="Choose a batch to mark attendance or view reports." />
      ) : studentsLoading ? (
        <LoadingSpinner className="py-12" />
      ) : !studentsData?.students.length ? (
        <EmptyState title="No students" description="No students enrolled in this batch." />
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          {/* Marking Grid */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Mark Attendance — {date}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {studentsData.students.map((s) => {
                  const status = records[s.id] ?? "present"
                  return (
                    <button
                      key={s.id}
                      onClick={() => toggleStatus(s.id)}
                      className="flex w-full items-center justify-between rounded-md border p-2 text-left transition-colors hover:bg-muted"
                    >
                      <span className="text-sm font-medium">{s.name}</span>
                      <div className="flex items-center gap-2">
                        {statusIcon(status)}
                        <Badge
                          variant={status === "present" ? "default" : status === "absent" ? "destructive" : "secondary"}
                        >
                          {status}
                        </Badge>
                      </div>
                    </button>
                  )
                })}
              </div>
            </CardContent>
          </Card>

          {/* Report Section */}
          {reportData && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">
                  Attendance Report
                  <span className="ml-2 text-sm font-normal text-muted-foreground">
                    Avg: {reportData.summary.average_attendance.toFixed(1)}%
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {reportData.students.map((s) => (
                    <div key={s.student_id} className="flex items-center justify-between rounded-md border p-2 text-sm">
                      <div>
                        <span className="font-medium">{s.name}</span>
                        <span className="ml-2 text-muted-foreground">
                          P:{s.present} A:{s.absent} L:{s.late}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{s.percentage.toFixed(1)}%</span>
                        {s.alert_level && (
                          <Badge className={ALERT_COLORS[s.alert_level] ?? ""}>
                            {s.alert_level}
                          </Badge>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  )
}
