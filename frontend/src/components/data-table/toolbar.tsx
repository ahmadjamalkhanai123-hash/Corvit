"use client"

import type { Table } from "@tanstack/react-table"
import { Plus, SlidersHorizontal } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

interface DataTableToolbarProps<TData> {
  table: Table<TData>
  searchValue?: string
  onSearchChange?: (value: string) => void
  searchPlaceholder?: string
  onAdd?: () => void
  addLabel?: string
  filterComponent?: React.ReactNode
}

export function DataTableToolbar<TData>({
  table,
  searchValue = "",
  onSearchChange,
  searchPlaceholder = "Search...",
  onAdd,
  addLabel = "Add new",
  filterComponent,
}: DataTableToolbarProps<TData>) {
  return (
    <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex flex-1 items-center gap-2">
        {onSearchChange && (
          <Input
            placeholder={searchPlaceholder}
            value={searchValue}
            onChange={(e) => onSearchChange(e.target.value)}
            className="h-9 w-full sm:max-w-[300px]"
          />
        )}
        {filterComponent}
      </div>

      <div className="flex items-center gap-2">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="sm" className="h-9">
              <SlidersHorizontal className="mr-2 h-4 w-4" />
              Columns
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            {table
              .getAllColumns()
              .filter((col) => col.getCanHide())
              .map((col) => (
                <DropdownMenuCheckboxItem
                  key={col.id}
                  className="capitalize"
                  checked={col.getIsVisible()}
                  onCheckedChange={(value) => col.toggleVisibility(!!value)}
                >
                  {col.id.replace(/_/g, " ")}
                </DropdownMenuCheckboxItem>
              ))}
          </DropdownMenuContent>
        </DropdownMenu>

        {onAdd && (
          <Button size="sm" className="h-9" onClick={onAdd}>
            <Plus className="mr-2 h-4 w-4" />
            {addLabel}
          </Button>
        )}
      </div>
    </div>
  )
}
