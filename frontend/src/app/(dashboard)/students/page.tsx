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
import type { Student, StudentStatus } from "@/types/entities"

const STATUS_OPTIONS = [
  { label: "Active", value: "active" },
  { label: "Graduated", value: "graduated" },
  { label: "Dropped", value: "dropped" },
]

const statusVariant: Record<StudentStatus, "default" | "secondary" | "destructive"> = {
  active: "default",
  graduated: "secondary",
  dropped: "destructive",
}

const emptyStudent = { name: "", email: "", phone: "", cnic: "", guardian_name: "", guardian_phone: "", address: "" }

export default function StudentsPage() {
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [search, setSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState<string[]>([])
  const debouncedSearch = useDebounce(search, 300)

  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [form, setForm] = useState(emptyStudent)
  const [deleteId, setDeleteId] = useState<string | null>(null)

  const statusParam = statusFilter.length === 1 ? `&status=${statusFilter[0]}` : ""
  const { data, isLoading, mutate } = useList<Student>(
    `students${statusParam ? `${statusParam}` : ""}`,
    page,
    pageSize,
    debouncedSearch,
  )
  const { create, update, remove } = useCRUD<Student>("students")

  const openCreate = () => {
    setEditingId(null)
    setForm(emptyStudent)
    setDialogOpen(true)
  }

  const openEdit = (student: Student) => {
    setEditingId(student.id)
    setForm({
      name: student.name,
      email: student.email,
      phone: student.phone,
      cnic: student.cnic ?? "",
      guardian_name: student.guardian_name ?? "",
      guardian_phone: student.guardian_phone ?? "",
      address: student.address ?? "",
    })
    setDialogOpen(true)
  }

  const handleSubmit = async () => {
    try {
      if (editingId) {
        await update(editingId, form)
        toast.success("Student updated")
      } else {
        await create(form)
        toast.success("Student created")
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
      toast.success("Student deleted")
      setDeleteId(null)
      mutate()
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Delete failed")
    }
  }

  const columns: ColumnDef<Student>[] = [
    { accessorKey: "name", header: "Name" },
    { accessorKey: "email", header: "Email" },
    { accessorKey: "phone", header: "Phone" },
    {
      accessorKey: "status",
      header: "Status",
      cell: ({ row }) => (
        <Badge variant={statusVariant[row.original.status]}>{row.original.status}</Badge>
      ),
    },
    {
      accessorKey: "enrollment_date",
      header: "Enrolled",
      cell: ({ row }) => formatDate(row.original.enrollment_date),
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
      <PageHeader title="Students" breadcrumbs={[{ label: "Students" }]} />

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
        searchPlaceholder="Search students..."
        isLoading={isLoading}
        onAdd={openCreate}
        addLabel="Add Student"
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
            <DialogTitle>{editingId ? "Edit Student" : "Add Student"}</DialogTitle>
          </DialogHeader>
          <div className="grid gap-3 py-2">
            <div>
              <Label>Name *</Label>
              <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            </div>
            <div>
              <Label>Email *</Label>
              <Input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
            </div>
            <div>
              <Label>Phone *</Label>
              <Input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
            </div>
            <div>
              <Label>CNIC</Label>
              <Input value={form.cnic} onChange={(e) => setForm({ ...form, cnic: e.target.value })} />
            </div>
            <div>
              <Label>Guardian Name</Label>
              <Input value={form.guardian_name} onChange={(e) => setForm({ ...form, guardian_name: e.target.value })} />
            </div>
            <div>
              <Label>Guardian Phone</Label>
              <Input value={form.guardian_phone} onChange={(e) => setForm({ ...form, guardian_phone: e.target.value })} />
            </div>
            <div>
              <Label>Address</Label>
              <Input value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleSubmit} disabled={!form.name || !form.email || !form.phone}>
              {editingId ? "Save" : "Create"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <ConfirmDialog
        open={!!deleteId}
        onOpenChange={() => setDeleteId(null)}
        title="Delete Student"
        description="Are you sure you want to delete this student? This action cannot be undone."
        confirmLabel="Delete"
        destructive
        onConfirm={handleDelete}
      />
    </div>
  )
}
