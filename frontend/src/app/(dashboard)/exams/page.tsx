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
import type { Exam, ExamType, Batch } from "@/types/entities"

const TYPE_OPTIONS = [
  { label: "Quiz", value: "quiz" },
  { label: "Midterm", value: "midterm" },
  { label: "Final", value: "final" },
  { label: "Practical", value: "practical" },
]

const typeVariant: Record<ExamType, "default" | "secondary" | "outline" | "destructive"> = {
  quiz: "outline",
  midterm: "secondary",
  final: "default",
  practical: "destructive",
}

const emptyExam = { batch_id: "", title: "", exam_type: "midterm" as ExamType, date: "", total_marks: "100" }

export default function ExamsPage() {
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [search, setSearch] = useState("")
  const [typeFilter, setTypeFilter] = useState<string[]>([])
  const debouncedSearch = useDebounce(search, 300)

  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [form, setForm] = useState(emptyExam)
  const [deleteId, setDeleteId] = useState<string | null>(null)

  const typeParam = typeFilter.length === 1 ? `&exam_type=${typeFilter[0]}` : ""
  const { data, isLoading, mutate } = useList<Exam>(
    `exams${typeParam}`,
    page,
    pageSize,
    debouncedSearch,
  )
  const { data: batchesData } = useList<Batch>("batches", 1, 100)
  const { create, update, remove } = useCRUD<Exam>("exams")

  const openCreate = () => {
    setEditingId(null)
    setForm(emptyExam)
    setDialogOpen(true)
  }

  const openEdit = (exam: Exam) => {
    setEditingId(exam.id)
    setForm({
      batch_id: exam.batch_id,
      title: exam.title,
      exam_type: exam.exam_type,
      date: exam.date,
      total_marks: String(exam.total_marks),
    })
    setDialogOpen(true)
  }

  const handleSubmit = async () => {
    try {
      const payload = { ...form, total_marks: Number(form.total_marks) }
      if (editingId) {
        await update(editingId, payload)
        toast.success("Exam updated")
      } else {
        await create(payload)
        toast.success("Exam created")
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
      toast.success("Exam deleted")
      setDeleteId(null)
      mutate()
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Delete failed")
    }
  }

  const columns: ColumnDef<Exam>[] = [
    { accessorKey: "title", header: "Title" },
    { accessorKey: "batch_name", header: "Batch" },
    {
      accessorKey: "exam_type",
      header: "Type",
      cell: ({ row }) => (
        <Badge variant={typeVariant[row.original.exam_type]}>{row.original.exam_type}</Badge>
      ),
    },
    {
      accessorKey: "date",
      header: "Date",
      cell: ({ row }) => formatDate(row.original.date),
    },
    { accessorKey: "total_marks", header: "Total Marks" },
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
      <PageHeader title="Exams" breadcrumbs={[{ label: "Exams" }]} />

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
        searchPlaceholder="Search exams..."
        isLoading={isLoading}
        onAdd={openCreate}
        addLabel="Add Exam"
        filterComponent={
          <FacetedFilter
            title="Type"
            options={TYPE_OPTIONS}
            selected={typeFilter}
            onSelectionChange={setTypeFilter}
          />
        }
      />

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>{editingId ? "Edit Exam" : "Add Exam"}</DialogTitle>
          </DialogHeader>
          <div className="grid gap-3 py-2">
            <div>
              <Label>Title *</Label>
              <Input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
            </div>
            <div>
              <Label>Batch *</Label>
              <Select value={form.batch_id} onValueChange={(v) => setForm({ ...form, batch_id: v })}>
                <SelectTrigger><SelectValue placeholder="Select batch" /></SelectTrigger>
                <SelectContent>
                  {(batchesData?.items ?? []).map((b) => (
                    <SelectItem key={b.id} value={b.id}>{b.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Type *</Label>
              <Select value={form.exam_type} onValueChange={(v) => setForm({ ...form, exam_type: v as ExamType })}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {TYPE_OPTIONS.map((t) => (
                    <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <Label>Date *</Label>
                <Input type="date" value={form.date} onChange={(e) => setForm({ ...form, date: e.target.value })} />
              </div>
              <div>
                <Label>Total Marks *</Label>
                <Input type="number" value={form.total_marks} onChange={(e) => setForm({ ...form, total_marks: e.target.value })} />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleSubmit} disabled={!form.title || !form.batch_id || !form.date}>
              {editingId ? "Save" : "Create"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <ConfirmDialog
        open={!!deleteId}
        onOpenChange={() => setDeleteId(null)}
        title="Delete Exam"
        description="Are you sure you want to delete this exam? This action cannot be undone."
        confirmLabel="Delete"
        destructive
        onConfirm={handleDelete}
      />
    </div>
  )
}
