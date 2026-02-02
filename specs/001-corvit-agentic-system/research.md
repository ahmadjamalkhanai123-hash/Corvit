# Research: Corvit Agentic System — Phase 1

**Branch**: `001-corvit-agentic-system` | **Date**: 2026-02-02
**Input**: Technical Context unknowns from plan.md

## Decision 1: Frontend Framework

**Decision**: Next.js 14 (App Router) with TypeScript

**Rationale**:
- App Router provides file-based routing matching the 12-page structure exactly
- Route groups `(auth)` and `(dashboard)` enable different layouts without nesting
- Server components reduce client-side JavaScript bundle
- Built-in code splitting per route satisfies constitution performance targets
- Largest ecosystem for React-based production apps

**Alternatives considered**:
- Vite + React Router: Lighter weight but requires manual code splitting, no SSR out of the box
- Remix: Strong data loading but smaller ecosystem, overkill for admin panel
- SvelteKit: Excellent performance but team would need to learn new framework
- Plain HTML/Jinja2 from FastAPI: Simplest but no real-time capabilities, poor component reuse

## Decision 2: UI Component Library

**Decision**: shadcn/ui + Tailwind CSS 3 + Radix UI primitives

**Rationale**:
- Components are copied into the project (not a dependency) — full control, no version lock-in
- Provides all required components from constitution: Button, Input, Select, DataTable, Card, Dialog/Modal, Toast, Skeleton, Avatar, Badge, Breadcrumb, DropdownMenu, Sheet (mobile sidebar)
- Built on Radix UI which handles WCAG 2.1 AA accessibility (keyboard nav, ARIA, focus management) out of the box
- Tailwind CSS enables the 4px grid system and design tokens from constitution
- TanStack Table integration for the DataTable component with sorting, filtering, pagination

**Alternatives considered**:
- MUI (Material UI): Heavier bundle, opinionated design harder to customize
- Ant Design: Enterprise-ready but very large, Chinese-first documentation
- Chakra UI: Good accessibility but fewer components than needed
- Custom components: Maximum control but orders of magnitude more work

## Decision 3: Data Table Implementation

**Decision**: TanStack Table (v8) wrapped in a shadcn/ui DataTable component

**Rationale**:
- Headless — renders with any UI library (Tailwind + Radix)
- Built-in column sorting, filtering, pagination, row selection, column visibility
- shadcn/ui provides a pre-built DataTable pattern that matches constitution requirements exactly
- Single generic DataTable component reused across all 8 entity pages (students, teachers, courses, batches, enrollments, attendance, fees, exams)

**Alternatives considered**:
- AG Grid: Powerful but commercial license, heavy
- React Table v7: Outdated, no active development
- Custom table: Too much effort for 8 entity pages

## Decision 4: Chart Library

**Decision**: Recharts

**Rationale**:
- Built on React + D3, declarative API
- Supports LineChart, BarChart, PieChart needed for dashboard KPIs
- Lightweight (~40KB gzipped), responsive by default
- shadcn/ui has chart component examples using Recharts

**Alternatives considered**:
- Chart.js + react-chartjs-2: Good but canvas-based (harder to style with Tailwind)
- Nivo: Beautiful but heavier
- Tremor: Built for dashboards but tightly coupled to its own design system

## Decision 5: Real-Time Communication

**Decision**: Server-Sent Events (SSE) for chat streaming, REST polling for dashboard

**Rationale**:
- SSE is simpler than WebSocket for unidirectional streaming (agent → user)
- FastAPI natively supports `StreamingResponse` for SSE
- No additional infrastructure needed (no WebSocket server, no Redis pub/sub for WS)
- Dashboard metrics update on page load + 30-second polling interval (sufficient for institute scale)
- Reduces complexity while meeting real-time requirement from constitution

**Alternatives considered**:
- WebSocket: Bidirectional but unnecessary — user sends HTTP POST, agent streams SSE response
- Long polling: Works but less efficient than SSE for streaming text
- Socket.io: Heavy dependency for a simple use case

## Decision 6: State Management (Frontend)

**Decision**: React Server Components + SWR for client-side data fetching

**Rationale**:
- Server Components handle initial data loading (dashboard KPIs, page data)
- SWR provides client-side caching, revalidation, optimistic updates for CRUD operations
- No global state library needed — auth state in a React context, entity data in SWR cache
- Simpler than Redux/Zustand for this scale

**Alternatives considered**:
- Redux Toolkit + RTK Query: Powerful but overkill for 12 pages
- Zustand: Light but SWR already handles data fetching state
- TanStack Query: Excellent but SWR is simpler and sufficient

## Decision 7: API Client

**Decision**: Native fetch with a thin wrapper (api-client.ts)

**Rationale**:
- Next.js 14 extends native fetch with caching and revalidation
- JWT token injection via a simple wrapper function
- No additional dependency needed
- Typed responses using shared TypeScript interfaces from `types/`

**Alternatives considered**:
- Axios: Popular but unnecessary with modern fetch
- ky: Lightweight fetch wrapper but adds a dependency for minimal value

## Decision 8: Backend Project Structure

**Decision**: Monorepo with `backend/` and `frontend/` at root level

**Rationale**:
- Single git repository simplifies versioning and CI/CD
- Separate `pyproject.toml` and `package.json` prevent dependency conflicts
- Independent deployment: backend on port 8000, frontend on port 3000
- Shared API contracts via the spec documentation (not code sharing)

**Alternatives considered**:
- Two separate repositories: Harder to keep in sync, more git overhead
- Python monorepo with frontend as a static build: Tighter coupling, harder to develop frontend independently

## Decision 9: LLM Provider Abstraction

**Decision**: Abstract `LLMProvider` base class with `OllamaProvider` implementation

**Rationale**:
- Constitution requires swap-ready LLM provider via `.env` change
- Abstract base defines `generate()` and `is_available()` interface
- Factory pattern selects provider from `LLM_PROVIDER` environment variable
- Ollama provider uses httpx for async HTTP calls to `http://localhost:11434/api/chat`
- Future `ClaudeProvider` would implement same interface

**Alternatives considered**:
- LangChain: Heavy dependency for a simple HTTP call
- LiteLLM: Good abstraction but adds dependency; our interface is simpler
- Direct httpx calls without abstraction: Violates constitution swappability requirement

## Decision 10: Authentication Flow (Frontend)

**Decision**: JWT stored in httpOnly cookie (set by backend), with client-side auth context

**Rationale**:
- httpOnly cookie prevents XSS token theft (constitution security requirement)
- Backend sets cookie on login response, clears on logout
- Frontend auth context reads user info from `/api/auth/me` on mount
- 401 responses trigger redirect to login page
- Role-based route protection via middleware in Next.js

**Alternatives considered**:
- localStorage JWT: Vulnerable to XSS
- Session-based auth: Would require Redis session store, more complex
- NextAuth.js: Designed for OAuth providers, overkill for simple JWT

## Unresolved Items

None. All technical decisions resolved.
