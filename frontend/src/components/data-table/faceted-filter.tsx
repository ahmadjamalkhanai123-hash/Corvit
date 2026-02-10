"use client"

import { Check } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { cn } from "@/lib/utils"

interface FacetedFilterOption {
  label: string
  value: string
  icon?: React.ReactNode
}

interface FacetedFilterProps {
  title: string
  options: FacetedFilterOption[]
  selected: string[]
  onSelectionChange: (values: string[]) => void
}

export function FacetedFilter({ title, options, selected, onSelectionChange }: FacetedFilterProps) {
  const toggle = (value: string) => {
    if (selected.includes(value)) {
      onSelectionChange(selected.filter((v) => v !== value))
    } else {
      onSelectionChange([...selected, value])
    }
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm" className="h-9 border-dashed">
          {title}
          {selected.length > 0 && (
            <>
              <Separator orientation="vertical" className="mx-2 h-4" />
              <Badge variant="secondary" className="rounded-sm px-1 font-normal">
                {selected.length}
              </Badge>
            </>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-[200px]">
        {options.map((option) => {
          const isSelected = selected.includes(option.value)
          return (
            <DropdownMenuItem key={option.value} onSelect={() => toggle(option.value)}>
              <div
                className={cn(
                  "mr-2 flex h-4 w-4 items-center justify-center rounded-sm border",
                  isSelected ? "bg-primary border-primary text-primary-foreground" : "opacity-50",
                )}
              >
                {isSelected && <Check className="h-3 w-3" />}
              </div>
              {option.icon && <span className="mr-2">{option.icon}</span>}
              <span>{option.label}</span>
            </DropdownMenuItem>
          )
        })}
        {selected.length > 0 && (
          <>
            <DropdownMenuSeparator />
            <DropdownMenuItem onSelect={() => onSelectionChange([])}>Clear filters</DropdownMenuItem>
          </>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
