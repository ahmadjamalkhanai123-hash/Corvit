import {
  LayoutDashboard,
  Users,
  GraduationCap,
  BookOpen,
  Layers,
  ClipboardList,
  CalendarCheck,
  Banknote,
  FileText,
  MessageSquare,
  Settings,
  type LucideIcon,
} from "lucide-react"

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

export interface NavItem {
  label: string
  href: string
  icon: LucideIcon
  roles?: string[]
}

export const NAV_ITEMS: NavItem[] = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Students", href: "/students", icon: Users, roles: ["admin", "teacher"] },
  { label: "Teachers", href: "/teachers", icon: GraduationCap, roles: ["admin"] },
  { label: "Courses", href: "/courses", icon: BookOpen },
  { label: "Batches", href: "/batches", icon: Layers, roles: ["admin", "teacher"] },
  { label: "Enrollments", href: "/enrollments", icon: ClipboardList, roles: ["admin"] },
  { label: "Attendance", href: "/attendance", icon: CalendarCheck, roles: ["admin", "teacher"] },
  { label: "Fees", href: "/fees", icon: Banknote, roles: ["admin"] },
  { label: "Exams", href: "/exams", icon: FileText, roles: ["admin", "teacher"] },
  { label: "Chat", href: "/chat", icon: MessageSquare },
  { label: "Settings", href: "/settings", icon: Settings },
]

export const ROLES = {
  admin: { label: "Admin", color: "bg-red-100 text-red-800" },
  teacher: { label: "Teacher", color: "bg-blue-100 text-blue-800" },
  student: { label: "Student", color: "bg-green-100 text-green-800" },
} as const
