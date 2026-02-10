"use client"

import { useState } from "react"
import { Plus, Pencil, Trash2, Clock, Banknote, Layers } from "lucide-react"
import { toast } from "sonner"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import { Skeleton } from "@/components/ui/skeleton"
import { PageHeader } from "@/components/layout/page-header"
import { ConfirmDialog } from "@/components/shared/confirm-dialog"
import { EmptyState } from "@/components/shared/empty-state"
import { useList, useCRUD } from "@/hooks/use-api"
import { useDebounce } from "@/hooks/use-debounce"
import { formatCurrency } from "@/lib/utils"
import { apiClient } from "@/lib/api-client"
import type { Course, Batch } from "@/types/entities"

const emptyCourse = { name: "", code: "", duration_weeks: "12", fee_amount: "", description: "", category: "" }

interface CourseBatchesResponse {
  course_id: string
  course_name: string
  batches: (Batch & { seats_available?: number })[]
}

export default function CoursesPage() {
  const [search, setSearch] = useState("")
  const debouncedSearch = useDebounce(search, 300)

  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [form, setForm] = useState(emptyCourse)
  const [deleteId, setDeleteId] = useState<string | null>(null)

  const [detailCourse, setDetailCourse] = useState<Course | null>(null)
  const [detailBatches, setDetailBatches] = useState<CourseBatchesResponse | null>(null)

  const { data, isLoading, mutate } = useList<Course>("courses", 1, 100, debouncedSearch)
  const { create, update, remove } = useCRUD<Course>("courses")

  const openCreate = () => {
    setEditingId(null)
    setForm(emptyCourse)
    setDialogOpen(true)
  }

  const openEdit = (course: Course) => {
    setEditingId(course.id)
    setForm({
      name: course.name,
      code: course.code,
      duration_weeks: String(course.duration_weeks),
      fee_amount: String(course.fee_amount),
      description: course.description ?? "",
      category: course.category ?? "",
    })
    setDialogOpen(true)
  }

  const openDetail = async (course: Course) => {
    setDetailCourse(course)
    try {
      const res = await apiClient.get<CourseBatchesResponse>(`/api/courses/${course.id}/batches`)
      setDetailBatches(res)
    } catch {
      setDetailBatches(null)
    }
  }

  const handleSubmit = async () => {
    try {
      const payload = {
        ...form,
        duration_weeks: Number(form.duration_weeks),
        fee_amount: Number(form.fee_amount),
      }
      if (editingId) {
        await update(editingId, payload)
        toast.success("Course updated")
      } else {
        await create(payload)
        toast.success("Course created")
      }
      setDialogOpen(false)
      mutate()
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Operation failed")
    }
  }

  const handleDelete = async () => {
    if (!deleteId) return
    try {
      await remove(deleteId)
      toast.success("Course deleted")
      setDeleteId(null)
      mutate()
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Delete failed")
    }
  }

  return (
    <div className="space-y-4">
      <PageHeader
        title="Courses"
        breadcrumbs={[{ label: "Courses" }]}
        actions={
          <Button size="sm" onClick={openCreate}>
            <Plus className="mr-2 h-4 w-4" /> Add Course
          </Button>
        }
      />

      <Input
        placeholder="Search courses..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="max-w-sm"
      />

      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-5 w-32" />
                <Skeleton className="h-3 w-20" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-4 w-full" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : !data?.items.length ? (
        <EmptyState
          title="No courses found"
          description="Create your first course to get started."
          actionLabel="Add Course"
          onAction={openCreate}
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {data.items.map((course) => (
            <Card
              key={course.id}
              className="cursor-pointer transition-shadow hover:shadow-md"
              onClick={() => openDetail(course)}
            >
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-lg">{course.name}</CardTitle>
                    <CardDescription>{course.code}</CardDescription>
                  </div>
                  {course.category && (
                    <Badge variant="secondary">{course.category}</Badge>
                  )}
                </div>
              </CardHeader>
              <CardContent className="pb-2">
                {course.description && (
                  <p className="text-sm text-muted-foreground line-clamp-2">{course.description}</p>
                )}
                <div className="mt-3 flex flex-wrap gap-3 text-sm text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <Clock className="h-3.5 w-3.5" /> {course.duration_weeks} weeks
                  </span>
                  <span className="flex items-center gap-1">
                    <Banknote className="h-3.5 w-3.5" /> {formatCurrency(course.fee_amount)}
                  </span>
                </div>
              </CardContent>
              <CardFooter className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation()
                    openEdit(course)
                  }}
                >
                  <Pencil className="mr-1 h-3 w-3" /> Edit
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  className="text-destructive"
                  onClick={(e) => {
                    e.stopPropagation()
                    setDeleteId(course.id)
                  }}
                >
                  <Trash2 className="mr-1 h-3 w-3" /> Delete
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}

      {/* Course Detail Sheet */}
      <Sheet open={!!detailCourse} onOpenChange={() => { setDetailCourse(null); setDetailBatches(null) }}>
        <SheetContent className="overflow-y-auto">
          {detailCourse && (
            <>
              <SheetHeader>
                <SheetTitle>{detailCourse.name}</SheetTitle>
              </SheetHeader>
              <div className="mt-4 space-y-4">
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <span className="text-muted-foreground">Code</span>
                  <span>{detailCourse.code}</span>
                  <span className="text-muted-foreground">Duration</span>
                  <span>{detailCourse.duration_weeks} weeks</span>
                  <span className="text-muted-foreground">Fee</span>
                  <span>{formatCurrency(detailCourse.fee_amount)}</span>
                  <span className="text-muted-foreground">Category</span>
                  <span>{detailCourse.category ?? "—"}</span>
                </div>
                {detailCourse.description && (
                  <p className="text-sm">{detailCourse.description}</p>
                )}
                <div>
                  <h4 className="mb-2 font-semibold flex items-center gap-1">
                    <Layers className="h-4 w-4" /> Batches
                  </h4>
                  {detailBatches?.batches.length ? (
                    <div className="space-y-2">
                      {detailBatches.batches.map((b) => (
                        <div key={b.id} className="rounded border p-3 text-sm">
                          <div className="font-medium">{b.name}</div>
                          <div className="text-muted-foreground">
                            {b.teacher_name} &middot; {b.schedule_days} {b.schedule_time}
                          </div>
                          <div className="mt-1 text-muted-foreground">
                            {b.enrolled_count ?? 0}/{b.max_capacity} enrolled
                            {b.seats_available !== undefined && ` (${b.seats_available} available)`}
                          </div>
                          <Badge variant={b.status === "active" ? "default" : "secondary"} className="mt-1">
                            {b.status}
                          </Badge>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">No batches for this course.</p>
                  )}
                </div>
              </div>
            </>
          )}
        </SheetContent>
      </Sheet>

      {/* Create/Edit Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>{editingId ? "Edit Course" : "Add Course"}</DialogTitle>
          </DialogHeader>
          <div className="grid gap-3 py-2">
            <div>
              <Label>Name *</Label>
              <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            </div>
            <div>
              <Label>Code *</Label>
              <Input value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} />
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <Label>Duration (weeks) *</Label>
                <Input type="number" value={form.duration_weeks} onChange={(e) => setForm({ ...form, duration_weeks: e.target.value })} />
              </div>
              <div>
                <Label>Fee (PKR) *</Label>
                <Input type="number" value={form.fee_amount} onChange={(e) => setForm({ ...form, fee_amount: e.target.value })} />
              </div>
            </div>
            <div>
              <Label>Category</Label>
              <Input value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} />
            </div>
            <div>
              <Label>Description</Label>
              <Input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleSubmit} disabled={!form.name || !form.code || !form.fee_amount}>
              {editingId ? "Save" : "Create"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <ConfirmDialog
        open={!!deleteId}
        onOpenChange={() => setDeleteId(null)}
        title="Delete Course"
        description="Are you sure you want to delete this course? This action cannot be undone."
        confirmLabel="Delete"
        destructive
        onConfirm={handleDelete}
      />
    </div>
  )
}
