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
import type { Enrollment, EnrollmentStatus, Student, Batch } from "@/types/entities"

const STATUS_OPTIONS = [
  { label: "Active", value: "active" },
  { label: "Completed", value: "completed" },
  { label: "Dropped", value: "dropped" },
]

const statusVariant: Record<EnrollmentStatus, "default" | "secondary" | "destructive"> = {
  active: "default",
  completed: "secondary",
  dropped: "destructive",
}

export default function EnrollmentsPage() {
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [search, setSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState<string[]>([])
  const debouncedSearch = useDebounce(search, 300)

  const [dialogOpen, setDialogOpen] = useState(false)
  const [form, setForm] = useState({ student_id: "", batch_id: "" })
  const [deleteId, setDeleteId] = useState<string | null>(null)

  const statusParam = statusFilter.length === 1 ? `&status=${statusFilter[0]}` : ""
  const { data, isLoading, mutate } = useList<Enrollment>(
    `enrollments${statusParam}`,
    page,
    pageSize,
    debouncedSearch,
  )
  const { data: studentsData } = useList<Student>("students", 1, 100)
  const { data: batchesData } = useList<Batch>("batches", 1, 100)
  const { create, remove } = useCRUD<Enrollment>("enrollments")

  const openCreate = () => {
    setForm({ student_id: "", batch_id: "" })
    setDialogOpen(true)
  }

  const handleSubmit = async () => {
    try {
      await create(form)
      toast.success("Student enrolled successfully")
      setDialogOpen(false)
      mutate()
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Enrollment failed")
    }
  }

  const handleDelete = async () => {
    if (!deleteId) return
    try {
      await remove(deleteId)
      toast.success("Enrollment removed")
      setDeleteId(null)
      mutate()
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Delete failed")
    }
  }

  const columns: ColumnDef<Enrollment>[] = [
    { accessorKey: "student_name", header: "Student" },
    { accessorKey: "batch_name", header: "Batch" },
    { accessorKey: "course_name", header: "Course" },
    {
      accessorKey: "enrollment_date",
      header: "Date",
      cell: ({ row }) => formatDate(row.original.enrollment_date),
    },
    {
      accessorKey: "status",
      header: "Status",
      cell: ({ row }) => (
        <Badge variant={statusVariant[row.original.status]}>{row.original.status}</Badge>
      ),
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
            <DropdownMenuItem
              className="text-destructive"
              onClick={() => setDeleteId(row.original.id)}
            >
              <Trash2 className="mr-2 h-4 w-4" /> Remove
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      ),
    },
  ]

  return (
    <div className="space-y-4">
      <PageHeader title="Enrollments" breadcrumbs={[{ label: "Enrollments" }]} />

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
        searchPlaceholder="Search enrollments..."
        isLoading={isLoading}
        onAdd={openCreate}
        addLabel="Enroll Student"
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
            <DialogTitle>Enroll Student</DialogTitle>
          </DialogHeader>
          <div className="grid gap-3 py-2">
            <div>
              <Label>Student *</Label>
              <Select value={form.student_id} onValueChange={(v) => setForm({ ...form, student_id: v })}>
                <SelectTrigger><SelectValue placeholder="Select student" /></SelectTrigger>
                <SelectContent>
                  {(studentsData?.items ?? []).map((s) => (
                    <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Batch *</Label>
              <Select value={form.batch_id} onValueChange={(v) => setForm({ ...form, batch_id: v })}>
                <SelectTrigger><SelectValue placeholder="Select batch" /></SelectTrigger>
                <SelectContent>
                  {(batchesData?.items ?? []).map((b) => (
                    <SelectItem key={b.id} value={b.id}>
                      {b.name} {b.course_name ? `(${b.course_name})` : ""}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleSubmit} disabled={!form.student_id || !form.batch_id}>Enroll</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <ConfirmDialog
        open={!!deleteId}
        onOpenChange={() => setDeleteId(null)}
        title="Remove Enrollment"
        description="Are you sure you want to remove this enrollment?"
        confirmLabel="Remove"
        destructive
        onConfirm={handleDelete}
      />
    </div>
  )
}
