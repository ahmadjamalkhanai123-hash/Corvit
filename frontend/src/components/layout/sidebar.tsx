"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { NAV_ITEMS } from "@/lib/constants"
import { useAuth } from "@/hooks/use-auth"
import { Sheet, SheetContent } from "@/components/ui/sheet"

interface SidebarContentProps {
  onNavigate?: () => void
}

function SidebarContent({ onNavigate }: SidebarContentProps) {
  const pathname = usePathname()
  const { user } = useAuth()

  const filteredItems = NAV_ITEMS.filter(
    (item) => !item.roles || (user?.role && item.roles.includes(user.role)),
  )

  return (
    <nav className="flex flex-col gap-1 p-3">
      {filteredItems.map((item) => {
        const Icon = item.icon
        const isActive = pathname === item.href || pathname.startsWith(item.href + "/")
        return (
          <Link
            key={item.href}
            href={item.href}
            onClick={onNavigate}
            className={cn(
              "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
              isActive
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:bg-muted hover:text-foreground",
            )}
          >
            <Icon className="h-4 w-4 shrink-0" />
            {item.label}
          </Link>
        )
      })}
    </nav>
  )
}

interface SidebarProps {
  open: boolean
  onClose: () => void
}

export function Sidebar({ open, onClose }: SidebarProps) {
  return (
    <>
      {/* Desktop sidebar */}
      <aside className="hidden md:flex w-[240px] shrink-0 flex-col border-r bg-background">
        <SidebarContent />
      </aside>

      {/* Mobile sidebar */}
      <Sheet open={open} onOpenChange={onClose}>
        <SheetContent side="left" className="w-[240px] p-0">
          <div className="flex h-16 items-center border-b px-4">
            <span className="text-lg font-semibold">Corvit</span>
          </div>
          <SidebarContent onNavigate={onClose} />
        </SheetContent>
      </Sheet>
    </>
  )
}
