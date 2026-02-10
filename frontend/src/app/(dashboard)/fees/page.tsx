"use client"

import { useState } from "react"
import type { ColumnDef } from "@tanstack/react-table"
import { MoreHorizontal, Banknote } from "lucide-react"
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { PageHeader } from "@/components/layout/page-header"
import { DataTable } from "@/components/data-table/data-table"
import { FacetedFilter } from "@/components/data-table/faceted-filter"
import { useList, useCRUD } from "@/hooks/use-api"
import { useDebounce } from "@/hooks/use-debounce"
import { formatCurrency, formatDate } from "@/lib/utils"
import { apiClient } from "@/lib/api-client"
import type { Fee, FeeStatus, Student, Course } from "@/types/entities"

const STATUS_OPTIONS = [
  { label: "Pending", value: "pending" },
  { label: "Partial", value: "partial" },
  { label: "Paid", value: "paid" },
  { label: "Overdue", value: "overdue" },
]

const statusVariant: Record<FeeStatus, "default" | "secondary" | "outline" | "destructive"> = {
  paid: "default",
  partial: "secondary",
  pending: "outline",
  overdue: "destructive",
}

const ALERT_COLORS: Record<string, string> = {
  yellow: "bg-yellow-100 text-yellow-800",
  orange: "bg-orange-100 text-orange-800",
  red: "bg-red-100 text-red-800",
}

interface OverdueFee extends Fee {
  days_overdue: number
  alert_level: string
}

interface OverdueResponse {
  items: OverdueFee[]
  total_overdue_count: number
  total_overdue_amount: number
}

const emptyFee = { student_id: "", course_id: "", amount: "", due_date: "" }

export default function FeesPage() {
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [search, setSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState<string[]>([])
  const [tab, setTab] = useState("all")
  const debouncedSearch = useDebounce(search, 300)

  const [createOpen, setCreateOpen] = useState(false)
  const [form, setForm] = useState(emptyFee)

  const [payOpen, setPayOpen] = useState(false)
  const [payFeeId, setPayFeeId] = useState<string | null>(null)
  const [payAmount, setPayAmount] = useState("")

  const statusParam = statusFilter.length === 1 ? `&status=${statusFilter[0]}` : ""
  const { data, isLoading, mutate } = useList<Fee>(
    `fees${statusParam}`,
    page,
    pageSize,
    debouncedSearch,
  )
  const { data: studentsData } = useList<Student>("students", 1, 100)
  const { data: coursesData } = useList<Course>("courses", 1, 100)
  const { create } = useCRUD<Fee>("fees")

  const [overdueData, setOverdueData] = useState<OverdueResponse | null>(null)
  const [overdueLoading, setOverdueLoading] = useState(false)

  const loadOverdue = async () => {
    setOverdueLoading(true)
    try {
      const res = await apiClient.get<OverdueResponse>("/api/fees/overdue")
      setOverdueData(res)
    } catch {
      toast.error("Failed to load overdue fees")
    } finally {
      setOverdueLoading(false)
    }
  }

  const handleCreate = async () => {
    try {
      await create({ ...form, amount: Number(form.amount) } as unknown as Partial<Fee>)
      toast.success("Fee record created")
      setCreateOpen(false)
      mutate()
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Failed to create fee")
    }
  }

  const handlePay = async () => {
    if (!payFeeId) return
    try {
      await apiClient.post(`/api/fees/${payFeeId}/pay`, {
        amount: Number(payAmount),
        payment_date: new Date().toISOString().split("T")[0],
      })
      toast.success("Payment recorded")
      setPayOpen(false)
      setPayFeeId(null)
      setPayAmount("")
      mutate()
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Payment failed")
    }
  }

  const openPay = (fee: Fee) => {
    setPayFeeId(fee.id)
    setPayAmount(String(fee.amount - fee.paid_amount))
    setPayOpen(true)
  }

  const columns: ColumnDef<Fee>[] = [
    { accessorKey: "student_name", header: "Student" },
    { accessorKey: "course_name", header: "Course" },
    {
      accessorKey: "amount",
      header: "Amount",
      cell: ({ row }) => formatCurrency(row.original.amount),
    },
    {
      id: "paid",
      header: "Paid",
      cell: ({ row }) => formatCurrency(row.original.paid_amount),
    },
    {
      accessorKey: "due_date",
      header: "Due Date",
      cell: ({ row }) => formatDate(row.original.due_date),
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
            <DropdownMenuItem onClick={() => openPay(row.original)}>
              <Banknote className="mr-2 h-4 w-4" /> Record Payment
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      ),
    },
  ]

  const overdueColumns: ColumnDef<OverdueFee>[] = [
    { accessorKey: "student_name", header: "Student" },
    { accessorKey: "course_name", header: "Course" },
    {
      accessorKey: "amount",
      header: "Amount",
      cell: ({ row }) => formatCurrency(row.original.amount),
    },
    {
      id: "remaining",
      header: "Remaining",
      cell: ({ row }) => formatCurrency(row.original.amount - row.original.paid_amount),
    },
    {
      accessorKey: "days_overdue",
      header: "Days Overdue",
    },
    {
      accessorKey: "alert_level",
      header: "Alert",
      cell: ({ row }) => (
        <Badge className={ALERT_COLORS[row.original.alert_level] ?? ""}>
          {row.original.alert_level}
        </Badge>
      ),
    },
    {
      id: "actions",
      cell: ({ row }) => (
        <Button size="sm" variant="outline" onClick={() => openPay(row.original)}>
          <Banknote className="mr-1 h-3 w-3" /> Pay
        </Button>
      ),
    },
  ]

  return (
    <div className="space-y-4">
      <PageHeader title="Fees" breadcrumbs={[{ label: "Fees" }]} />

      <Tabs
        value={tab}
        onValueChange={(v) => {
          setTab(v)
          if (v === "overdue") loadOverdue()
        }}
      >
        <TabsList>
          <TabsTrigger value="all">All Fees</TabsTrigger>
          <TabsTrigger value="overdue">Overdue</TabsTrigger>
        </TabsList>

        <TabsContent value="all" className="mt-4">
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
            searchPlaceholder="Search fees..."
            isLoading={isLoading}
            onAdd={() => { setForm(emptyFee); setCreateOpen(true) }}
            addLabel="Add Fee"
            filterComponent={
              <FacetedFilter
                title="Status"
                options={STATUS_OPTIONS}
                selected={statusFilter}
                onSelectionChange={setStatusFilter}
              />
            }
          />
        </TabsContent>

        <TabsContent value="overdue" className="mt-4">
          {overdueData && (
            <div className="mb-4 flex gap-4 text-sm">
              <span>Total overdue: <strong>{overdueData.total_overdue_count}</strong></span>
              <span>Amount: <strong>{formatCurrency(overdueData.total_overdue_amount)}</strong></span>
            </div>
          )}
          <DataTable
            columns={overdueColumns}
            data={overdueData?.items ?? []}
            total={overdueData?.items.length ?? 0}
            isLoading={overdueLoading}
          />
        </TabsContent>
      </Tabs>

      {/* Create Fee Dialog */}
      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Add Fee Record</DialogTitle>
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
            <div className="grid grid-cols-2 gap-2">
              <div>
                <Label>Amount (PKR) *</Label>
                <Input type="number" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} />
              </div>
              <div>
                <Label>Due Date *</Label>
                <Input type="date" value={form.due_date} onChange={(e) => setForm({ ...form, due_date: e.target.value })} />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateOpen(false)}>Cancel</Button>
            <Button onClick={handleCreate} disabled={!form.student_id || !form.course_id || !form.amount || !form.due_date}>
              Create
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Payment Dialog */}
      <Dialog open={payOpen} onOpenChange={setPayOpen}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>Record Payment</DialogTitle>
          </DialogHeader>
          <div className="grid gap-3 py-2">
            <div>
              <Label>Amount (PKR)</Label>
              <Input type="number" value={payAmount} onChange={(e) => setPayAmount(e.target.value)} />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setPayOpen(false)}>Cancel</Button>
            <Button onClick={handlePay} disabled={!payAmount || Number(payAmount) <= 0}>
              Record Payment
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
