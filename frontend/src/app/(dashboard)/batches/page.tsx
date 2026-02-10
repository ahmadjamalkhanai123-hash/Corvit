"use client"

import { useState } from "react"
import type { ColumnDef } from "@tanstack/react-table"
import { MoreHorizontal, Pencil, Trash2 } from "lucide-react"
import { toast } from "sonner"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { PageHeader } from "@/components/layout/page-header"
import { DataTable } from "@/components/data-table/data-table"
import { FacetedFilter } from "@/components/data-table/faceted-filter"
import { ConfirmDialog } from "@/components/shared/confirm-dialog"
import { useList, useCRUD } from "@/hooks/use-api"
import { useDebounce } from "@/hooks/use-debounce"
import { formatDate } from "@/lib/utils"
import type { Batch, BatchStatus, Course, Teacher } from "@/types/entities"

const STATUS_OPTIONS = [
  { label: "Upcoming", value: "upcoming" },
  { label: "Active", value: "active" },
  { label: "Completed", value: "completed" },
]

const statusVariant: Record<BatchStatus, "default" | "secondary" | "outline"> = {
  active: "default",
  upcoming: "secondary",
  completed: "outline",
}

const emptyBatch = {
  name: "",
  course_id: "",
  teacher_id: "",
  room: "",
  schedule_days: "",
  schedule_time: "",
  start_date: "",
  end_date: "",
  max_capacity: "30",
}

export default function BatchesPage() {
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [search, setSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState<string[]>([])
  const debouncedSearch = useDebounce(search, 300)

  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [form, setForm] = useState(emptyBatch)
  const [deleteId, setDeleteId] = useState<string | null>(null)

  const statusParam = statusFilter.length === 1 ? `&status=${statusFilter[0]}` : ""
  const { data, isLoading, mutate } = useList<Batch>(
    `batches${statusParam}`,
    page,
    pageSize,
    debouncedSearch,
  )
  const { data: coursesData } = useList<Course>("courses", 1, 100)
  const { data: teachersData } = useList<Teacher>("teachers", 1, 100)
  const { create, update, remove } = useCRUD<Batch>("batches")

  const openCreate = () => {
    setEditingId(null)
    setForm(emptyBatch)
    setDialogOpen(true)
  }

  const openEdit = (batch: Batch) => {
    setEditingId(batch.id)
    setForm({
      name: batch.name,
      course_id: batch.course_id,
      teacher_id: batch.teacher_id,
      room: batch.room ?? "",
      schedule_days: batch.schedule_days ?? "",
      schedule_time: batch.schedule_time ?? "",
      start_date: batch.start_date,
      end_date: batch.end_date ?? "",
      max_capacity: String(batch.max_capacity),
    })
    setDialogOpen(true)
  }

  const handleSubmit = async () => {
    try {
      const payload = { ...form, max_capacity: Number(form.max_capacity) }
      if (editingId) {
        await update(editingId, payload)
        toast.success("Batch updated")
      } else {
        await create(payload)
        toast.success("Batch created")
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
      toast.success("Batch deleted")
      setDeleteId(null)
      mutate()
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Delete failed")
    }
  }

  const columns: ColumnDef<Batch>[] = [
    { accessorKey: "name", header: "Name" },
    { accessorKey: "course_name", header: "Course" },
    { accessorKey: "teacher_name", header: "Teacher" },
    { accessorKey: "room", header: "Room" },
    {
      id: "schedule",
      header: "Schedule",
      cell: ({ row }) => {
        const b = row.original
        return b.schedule_days ? `${b.schedule_days} ${b.schedule_time ?? ""}` : "—"
      },
    },
    {
      accessorKey: "status",
      header: "Status",
      cell: ({ row }) => (
        <Badge variant={statusVariant[row.original.status]}>{row.original.status}</Badge>
      ),
    },
    {
      id: "capacity",
      header: "Enrolled",
      cell: ({ row }) => `${row.original.enrolled_count ?? 0}/${row.original.max_capacity}`,
    },
    {
      accessorKey: "start_date",
      header: "Start",
      cell: ({ row }) => formatDate(row.original.start_date),
    },
    {
      id: "actions",
      cell: ({ row }) => (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="h-8 w-8">
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => openEdit(row.original)}>
              <Pencil className="mr-2 h-4 w-4" /> Edit
            </DropdownMenuItem>
            <DropdownMenuItem
              className="text-destructive"
              onClick={() => setDeleteId(row.original.id)}
            >
              <Trash2 className="mr-2 h-4 w-4" /> Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      ),
    },
  ]

  return (
    <div className="space-y-4">
      <PageHeader title="Batches" breadcrumbs={[{ label: "Batches" }]} />

      <DataTable
        columns={columns}
        data={data?.items ?? []}
        total={data?.total ?? 0}
        page={page}
        pageSize={pageSize}
        onPageChange={setPage}
        onPageSizeChange={setPageSize}
        searchValue={search}
        onSearchChange={setSearch}
        searchPlaceholder="Search batches..."
        isLoading={isLoading}
        onAdd={openCreate}
        addLabel="Add Batch"
        filterComponent={
          <FacetedFilter
            title="Status"
            options={STATUS_OPTIONS}
            selected={statusFilter}
            onSelectionChange={setStatusFilter}
          />
        }
      />

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>{editingId ? "Edit Batch" : "Add Batch"}</DialogTitle>
          </DialogHeader>
          <div className="grid gap-3 py-2">
            <div>
              <Label>Name *</Label>
              <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            </div>
            <div>
              <Label>Course *</Label>
              <Select value={form.course_id} onValueChange={(v) => setForm({ ...form, course_id: v })}>
                <SelectTrigger><SelectValue placeholder="Select course" /></SelectTrigger>
                <SelectContent>
                  {(coursesData?.items ?? []).map((c) => (
                    <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Teacher *</Label>
              <Select value={form.teacher_id} onValueChange={(v) => setForm({ ...form, teacher_id: v })}>
                <SelectTrigger><SelectValue placeholder="Select teacher" /></SelectTrigger>
                <SelectContent>
                  {(teachersData?.items ?? []).map((t) => (
                    <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <Label>Room</Label>
                <Input value={form.room} onChange={(e) => setForm({ ...form, room: e.target.value })} />
              </div>
              <div>
                <Label>Capacity</Label>
                <Input type="number" value={form.max_capacity} onChange={(e) => setForm({ ...form, max_capacity: e.target.value })} />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <Label>Days</Label>
                <Input placeholder="Mon,Wed,Fri" value={form.schedule_days} onChange={(e) => setForm({ ...form, schedule_days: e.target.value })} />
              </div>
              <div>
                <Label>Time</Label>
                <Input placeholder="10:00-12:00" value={form.schedule_time} onChange={(e) => setForm({ ...form, schedule_time: e.target.value })} />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <Label>Start Date *</Label>
                <Input type="date" value={form.start_date} onChange={(e) => setForm({ ...form, start_date: e.target.value })} />
              </div>
              <div>
                <Label>End Date</Label>
                <Input type="date" value={form.end_date} onChange={(e) => setForm({ ...form, end_date: e.target.value })} />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleSubmit} disabled={!form.name || !form.course_id || !form.teacher_id || !form.start_date}>
              {editingId ? "Save" : "Create"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <ConfirmDialog
        open={!!deleteId}
        onOpenChange={() => setDeleteId(null)}
        title="Delete Batch"
        description="Are you sure you want to delete this batch? This action cannot be undone."
        confirmLabel="Delete"
        destructive
        onConfirm={handleDelete}
      />
    </div>
  )
}
