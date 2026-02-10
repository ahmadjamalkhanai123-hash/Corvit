"use client"

import { Menu, Bell, LogOut, User } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { useAuth } from "@/hooks/use-auth"
import { Badge } from "@/components/ui/badge"
import { ROLES } from "@/lib/constants"

interface NavbarProps {
  onToggleSidebar: () => void
}

export function Navbar({ onToggleSidebar }: NavbarProps) {
  const { user, logout } = useAuth()

  const initials = user?.username?.slice(0, 2).toUpperCase() ?? "?"
  const roleInfo = user?.role ? ROLES[user.role] : null

  return (
    <header className="sticky top-0 z-50 flex h-16 items-center gap-4 border-b bg-background px-4 md:px-6">
      <Button variant="ghost" size="icon" onClick={onToggleSidebar} className="md:hidden">
        <Menu className="h-5 w-5" />
      </Button>

      <div className="flex items-center gap-2">
        <span className="text-lg font-semibold">Corvit</span>
        <span className="text-sm text-muted-foreground hidden sm:inline">Agentic System</span>
      </div>

      <div className="ml-auto flex items-center gap-3">
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="h-5 w-5" />
        </Button>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="flex items-center gap-2 px-2">
              <Avatar className="h-8 w-8">
                <AvatarFallback className="text-xs">{initials}</AvatarFallback>
              </Avatar>
              <span className="hidden md:inline text-sm">{user?.username}</span>
              {roleInfo && (
                <Badge variant="secondary" className={`text-xs hidden md:inline ${roleInfo.color}`}>
                  {roleInfo.label}
                </Badge>
              )}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-48">
            <DropdownMenuItem className="flex items-center gap-2">
              <User className="h-4 w-4" />
              Profile
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={logout} className="flex items-center gap-2 text-destructive">
              <LogOut className="h-4 w-4" />
              Logout
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  )
}
