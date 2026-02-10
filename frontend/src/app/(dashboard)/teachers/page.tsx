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
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { PageHeader } from "@/components/layout/page-header"
import { DataTable } from "@/components/data-table/data-table"
import { ConfirmDialog } from "@/components/shared/confirm-dialog"
import { useList, useCRUD } from "@/hooks/use-api"
import { useDebounce } from "@/hooks/use-debounce"
import type { Teacher } from "@/types/entities"

const emptyTeacher = { name: "", email: "", phone: "", specialization: "", qualification: "" }

export default function TeachersPage() {
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [search, setSearch] = useState("")
  const debouncedSearch = useDebounce(search, 300)

  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [form, setForm] = useState(emptyTeacher)
  const [deleteId, setDeleteId] = useState<string | null>(null)

  const { data, isLoading, mutate } = useList<Teacher>("teachers", page, pageSize, debouncedSearch)
  const { create, update, remove } = useCRUD<Teacher>("teachers")

  const openCreate = () => {
    setEditingId(null)
    setForm(emptyTeacher)
    setDialogOpen(true)
  }

  const openEdit = (teacher: Teacher) => {
    setEditingId(teacher.id)
    setForm({
      name: teacher.name,
      email: teacher.email,
      phone: teacher.phone,
      specialization: teacher.specialization ?? "",
      qualification: teacher.qualification ?? "",
    })
    setDialogOpen(true)
  }

  const handleSubmit = async () => {
    try {
      if (editingId) {
        await update(editingId, form)
        toast.success("Teacher updated")
      } else {
        await create(form)
        toast.success("Teacher created")
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
      toast.success("Teacher deleted")
      setDeleteId(null)
      mutate()
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Delete failed")
    }
  }

  const columns: ColumnDef<Teacher>[] = [
    { accessorKey: "name", header: "Name" },
    { accessorKey: "email", header: "Email" },
    { accessorKey: "specialization", header: "Specialization" },
    { accessorKey: "qualification", header: "Qualification" },
    {
      accessorKey: "is_active",
      header: "Status",
      cell: ({ row }) => (
        <Badge variant={row.original.is_active ? "default" : "secondary"}>
          {row.original.is_active ? "Active" : "Inactive"}
        </Badge>
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
      <PageHeader title="Teachers" breadcrumbs={[{ label: "Teachers" }]} />

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
        searchPlaceholder="Search teachers..."
        isLoading={isLoading}
        onAdd={openCreate}
        addLabel="Add Teacher"
      />

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>{editingId ? "Edit Teacher" : "Add Teacher"}</DialogTitle>
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
              <Label>Specialization</Label>
              <Input value={form.specialization} onChange={(e) => setForm({ ...form, specialization: e.target.value })} />
            </div>
            <div>
              <Label>Qualification</Label>
              <Input value={form.qualification} onChange={(e) => setForm({ ...form, qualification: e.target.value })} />
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
        title="Delete Teacher"
        description="Are you sure you want to delete this teacher? This action cannot be undone."
        confirmLabel="Delete"
        destructive
        onConfirm={handleDelete}
      />
    </div>
  )
}
