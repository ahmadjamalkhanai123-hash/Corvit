---
id: 010
title: Implement Phase 7 Frontend Core
stage: green
date: 2026-02-03
surface: agent
model: claude-opus-4-5-20251101
feature: corvit-agentic-system
branch: 001-corvit-agentic-system
user: jamalafridi
command: start phase 7
labels: ["implementation", "phase7", "frontend", "nextjs", "shadcn", "dashboard", "auth"]
links:
  spec: specs/001-corvit-agentic-system/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - frontend/src/lib/utils.ts
  - frontend/src/lib/constants.ts
  - frontend/src/lib/api-client.ts
  - frontend/src/lib/auth.ts
  - frontend/src/types/entities.ts
  - frontend/src/types/api.ts
  - frontend/src/types/auth.ts
  - frontend/src/hooks/use-auth.tsx
  - frontend/src/hooks/use-api.ts
  - frontend/src/hooks/use-debounce.ts
  - frontend/src/components/layout/navbar.tsx
  - frontend/src/components/layout/sidebar.tsx
  - frontend/src/components/layout/page-header.tsx
  - frontend/src/components/shared/empty-state.tsx
  - frontend/src/components/shared/confirm-dialog.tsx
  - frontend/src/components/shared/loading-spinner.tsx
  - frontend/src/components/shared/error-boundary.tsx
  - frontend/src/components/charts/kpi-card.tsx
  - frontend/src/components/charts/line-chart.tsx
  - frontend/src/components/charts/bar-chart.tsx
  - frontend/src/app/layout.tsx
  - frontend/src/app/providers.tsx
  - frontend/src/app/page.tsx
  - frontend/src/app/(auth)/login/page.tsx
  - frontend/src/app/(auth)/register/page.tsx
  - frontend/src/app/(dashboard)/layout.tsx
  - frontend/src/app/(dashboard)/dashboard/page.tsx
  - frontend/src/components/ui/*.tsx (16 shadcn components)
  - specs/001-corvit-agentic-system/tasks.md
tests:
  - npm run build (0 errors, 4 routes generated)
---

## Prompt

start phase 7

## Response snapshot

Implemented all 31 tasks (T089-T119) for Phase 7 — Frontend Core:

**Dependencies (T089-T090):**
- Installed 16 shadcn/ui components (button, input, card, dialog, table, badge, sonner, skeleton, avatar, select, dropdown-menu, sheet, breadcrumb, separator, label, tabs)
- Installed SWR, Recharts, react-markdown, @tanstack/react-table, date-fns

**Types & Utilities (T091-T097):**
- utils.ts: cn(), formatDate, formatDateTime, formatRelative, formatCurrency (PKR)
- constants.ts: API_URL, NAV_ITEMS (11 pages with Lucide icons + role filters), ROLES
- entities.ts: 11 TypeScript interfaces matching all backend models
- api.ts: PaginatedResponse<T>, DashboardStats, ChatRequest/Response, SourceCitation
- auth.ts: LoginRequest, RegisterRequest, TokenResponse, AuthUser
- api-client.ts: fetch wrapper with JWT Bearer injection, ApiError class
- auth.ts lib: login/register/logout/getMe/getStoredToken functions

**Hooks (T098-T100):**
- use-auth.tsx: AuthProvider context with login/register/logout, auto-fetch /me on mount
- use-api.ts: useList (paginated SWR), useDetail, useCRUD (create/update/remove)
- use-debounce.ts: generic debounce hook

**Layout & Shared Components (T101-T108):**
- navbar.tsx: top bar with Corvit branding, notification bell, avatar dropdown with role badge
- sidebar.tsx: desktop fixed + mobile Sheet, role-filtered nav items, active route highlight
- page-header.tsx: title + breadcrumb component
- 4 shared components: empty-state, confirm-dialog, loading-spinner, error-boundary
- Tailwind v4 CSS-based theme already configured (globals.css design system)

**App Pages (T109-T119):**
- Root layout with Geist fonts, AuthProvider, Sonner toaster
- Root page: auto-redirect to /dashboard or /login based on auth state
- Login page: username/password form, error handling, redirect to dashboard
- Register page: username/email/password/role form, redirect to login
- Dashboard layout: auth guard, navbar + sidebar + main content area
- Dashboard page: 4 KPI cards, attendance LineChart, enrollment BarChart, recent activity feed, overdue fees card — all from /api/dashboard/stats with 30s SWR refresh

**Build: 0 errors, 4 routes (/, /login, /register, /dashboard)**

## Outcome

- ✅ Impact: Complete frontend core — auth flow, dashboard with live data, responsive layout
- 🧪 Build: `npm run build` passes with 0 errors
- 📁 Files: 27 files created/modified + 16 shadcn components
- 🔁 Next: Phase 8 — Frontend Pages (T120-T142): DataTable, chat, entity CRUD pages
- 🧠 Reflection: shadcn toast deprecated in favor of sonner. Tailwind v4 uses CSS-based config instead of tailwind.config.ts. Next.js 16 with React 19 (newer than spec's Next.js 14).

## Evaluation notes (flywheel)

- Failure modes observed: shadcn toast component deprecated (replaced with sonner), page.tsx required reading before writing
- Graders run and results (PASS/FAIL): Build PASS, 4 routes generated successfully
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): null
