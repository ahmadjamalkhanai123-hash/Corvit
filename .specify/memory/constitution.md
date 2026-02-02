<!--
  Sync Impact Report
  ==================
  Version change: 0.0.0 → 1.0.0 (initial ratification)

  Modified principles:
    - [NEW] I. Spec-Driven Development
    - [NEW] II. Zero-Cost Local-First Architecture
    - [NEW] III. Test-First Quality Gate (NON-NEGOTIABLE)
    - [NEW] IV. Production-Grade Frontend Standards
    - [NEW] V. API-First Contract Design
    - [NEW] VI. Security by Default

  Added sections:
    - Technology Stack & Constraints
    - Frontend Architecture & UI Design Standards
    - Development Workflow & Quality Gates
    - Governance

  Removed sections: none (initial constitution)

  Templates requiring updates:
    - .specify/templates/plan-template.md ✅ (no updates needed, Constitution Check is generic)
    - .specify/templates/spec-template.md ✅ (no updates needed, spec template is generic)
    - .specify/templates/tasks-template.md ✅ (no updates needed, task template is generic)
    - CLAUDE.md ✅ (references constitution.md, no direct updates needed)

  Follow-up TODOs: none
-->

# Corvit Agentic System Constitution

## Core Principles

### I. Spec-Driven Development

Every module, API route, database model, and frontend page MUST begin with a
YAML specification written BEFORE any implementation code. The development
cycle is: **Write Spec → Implement from Spec → Test against Spec**. No pull
request or merge is accepted without a corresponding spec file in the `specs/`
directory. Specifications are the single source of truth for system behavior;
code that deviates from its spec is considered a defect. All 21 YAML spec
files defined in the Blueprint (00-project through 20-agent-chat-api) MUST
exist and be approved before their implementation begins.

### II. Zero-Cost Local-First Architecture

The entire system MUST run at zero monetary cost. All infrastructure choices
MUST use free, open-source, locally-hosted components: Ollama + qwen2.5:7b
for LLM inference, PostgreSQL 16 for relational data, Redis 7 for caching,
ChromaDB for vector storage, and FastAPI for the backend API. No paid API
keys, no cloud-hosted AI services, and no SaaS subscriptions are permitted
in Phase 1. The LLM provider layer MUST use an abstract interface
(`LLMProvider`) so swapping to a paid provider (e.g., Claude API) in
future phases requires only an `.env` change with zero code modifications.

### III. Test-First Quality Gate (NON-NEGOTIABLE)

TDD is mandatory for all backend modules. The Red-Green-Refactor cycle MUST
be strictly enforced: tests are written first, tests MUST fail (red), then
implementation satisfies them (green), then code is cleaned up (refactor).
Test coverage targets: >95% intent routing accuracy for the Director Agent,
100% CRUD endpoint functionality, 100% rule engine trigger accuracy, >90%
RAG query relevance. Integration tests MUST cover: database model
relationships, API endpoint request/response contracts, agent chat
end-to-end flow, and health check multi-backend validation. Frontend pages
MUST have visual regression and interaction tests for all critical user
flows.

### IV. Production-Grade Frontend Standards

The frontend MUST be a real-time, production-level, multi-page application
that meets professional UI/UX design standards. Every page MUST follow these
non-negotiable design rules:

- **Design System**: A unified design system with consistent color palette
  (primary, secondary, accent, neutral, semantic colors for
  success/warning/error/info), typography scale (heading 1-6, body, caption,
  overline), spacing system (4px base grid), and elevation/shadow hierarchy.
- **Responsive Layout**: All pages MUST render correctly across desktop
  (1440px+), tablet (768px–1439px), and mobile (320px–767px) breakpoints
  using a 12-column fluid grid. No horizontal scroll on any viewport.
- **Component Library**: Reusable, composable UI components: Button, Input,
  Select, DataTable, Card, Modal, Toast/Notification, Sidebar, Navbar,
  Breadcrumb, Badge, Avatar, Skeleton loader, EmptyState, and Chart
  components. Every component MUST have hover, focus, active, disabled, and
  loading states defined.
- **Accessibility**: WCAG 2.1 AA compliance minimum. All interactive
  elements MUST have keyboard navigation, focus indicators, ARIA labels,
  sufficient color contrast (4.5:1 for text, 3:1 for large text), and
  screen reader compatibility.
- **Performance**: First Contentful Paint < 1.5s, Largest Contentful Paint
  < 2.5s, Cumulative Layout Shift < 0.1, Time to Interactive < 3.5s.
  Images MUST use lazy loading and modern formats (WebP/AVIF). Code
  splitting MUST be implemented per route.
- **Real-Time Updates**: The chat interface and dashboard metrics MUST
  update in real-time via WebSocket or SSE connections without requiring
  page refresh.
- **Error Handling UI**: Every API failure MUST surface a user-friendly
  error message. Network failures MUST show retry options. Form validation
  MUST provide inline, field-level error feedback.

**Required Pages (minimum):**

| # | Page | Route | Purpose |
|---|------|-------|---------|
| 1 | Login / Register | `/auth` | JWT authentication with role selection |
| 2 | Dashboard | `/dashboard` | KPI cards, charts, recent activity, system health |
| 3 | Chat Interface | `/chat` | Real-time Director Agent conversation UI |
| 4 | Students Management | `/students` | DataTable with CRUD, search, filter, pagination |
| 5 | Teachers Management | `/teachers` | DataTable with CRUD, search, filter, pagination |
| 6 | Courses Catalog | `/courses` | Card grid + detail view with batch info |
| 7 | Batches Management | `/batches` | Schedule view, student roster, teacher assignment |
| 8 | Enrollments | `/enrollments` | Enrollment workflow, batch selection, status tracking |
| 9 | Attendance Tracker | `/attendance` | Calendar/grid view, bulk marking, alert indicators |
| 10 | Fee Management | `/fees` | Payment status, overdue alerts, payment recording |
| 11 | Exams & Results | `/exams` | Exam scheduling, result entry, grade distribution |
| 12 | Settings / Profile | `/settings` | User profile, preferences, role-based visibility |

### V. API-First Contract Design

Every API endpoint MUST be fully defined with request/response schemas
(Pydantic models), HTTP methods, status codes, error responses, and
authentication requirements BEFORE frontend or integration work begins.
The FastAPI app MUST auto-generate OpenAPI 3.0 documentation at `/docs`.
All endpoints MUST follow RESTful conventions: proper HTTP verbs,
consistent URL patterns (`/api/{resource}`), pagination via query params
(`?page=1&limit=20`), and standardized error response format
(`{detail, error_code, timestamp}`). CORS MUST be configured to allow
the frontend origin. Rate limiting MUST be applied to auth endpoints.

### VI. Security by Default

Authentication uses JWT tokens with HS256 signing algorithm, configurable
expiration (default 480 minutes), and role-based access control (admin,
teacher, student). Secrets (JWT_SECRET, database credentials) MUST NEVER
be committed to version control; they reside in `.env` (gitignored) with
`.env.example` as the template. All user passwords MUST be hashed with
bcrypt via passlib. SQL injection is prevented by exclusive use of
SQLAlchemy ORM (no raw SQL). XSS is mitigated by treating all user input
as untrusted in both backend responses and frontend rendering. The
Director Agent's decision authority MUST be bounded: it can route queries,
send warnings, and recommend actions, but it MUST NOT autonomously expel
students, change fee structures, modify policies, or process refunds above
threshold without human approval.

## Technology Stack & Constraints

| Layer | Technology | Version | Constraint |
|-------|-----------|---------|------------|
| Package Manager | uv (Astral) | 0.9.24+ | MUST be used for all Python dependency management |
| Backend | FastAPI | Latest stable | Async-first, all endpoints async |
| Database | PostgreSQL | 16-alpine (Docker) | 17 tables as defined in Blueprint |
| Cache | Redis | 7-alpine (Docker) | Session and queue management |
| Vector DB | ChromaDB | Latest stable | 4 collections, 24+ documents |
| LLM | Ollama + qwen2.5:7b | Local | CPU-only, <5s response target |
| ORM | SQLAlchemy 2.0 | Async + asyncpg | No raw SQL queries permitted |
| Migrations | Alembic | Latest stable | Every schema change tracked |
| Auth | python-jose + passlib | Latest stable | JWT + bcrypt only |
| Frontend | Modern JS framework | Latest stable | SSR or CSR with code splitting |
| Testing | pytest + pytest-asyncio | Latest stable | Async test support required |

**Hardware minimums**: 8 GB RAM, 15 GB storage, any modern multi-core CPU.
Docker Desktop with WSL2 MUST be running for PostgreSQL and Redis
containers. Ollama runs natively on the host OS.

## Frontend Architecture & UI Design Standards

### Visual Design System

- **Color Palette**: Define a primary brand color derived from Corvit
  Systems branding, with semantic variants (success: green, warning: amber,
  error: red, info: blue). Dark mode support is RECOMMENDED but not
  required in Phase 1.
- **Typography**: Use a professional sans-serif system font stack
  (`Inter`, `system-ui`, `-apple-system`, `Segoe UI` fallback chain).
  Font sizes MUST follow a modular scale (e.g., 1.25 ratio). Line height
  MUST be 1.5 for body text, 1.2 for headings.
- **Spacing & Layout**: 4px base unit. All margins, paddings, and gaps
  MUST be multiples of 4px. Maximum content width: 1280px centered. Sidebar
  width: 260px collapsible. Page gutter: 24px on desktop, 16px on mobile.
- **Elevation**: Three-tier shadow system — `shadow-sm` (cards),
  `shadow-md` (dropdowns, popovers), `shadow-lg` (modals, dialogs).
- **Iconography**: Use a single, consistent icon library (e.g., Lucide,
  Heroicons, or Phosphor). Icons MUST be 20px for inline, 24px for
  actions, 48px for empty states.
- **Motion**: Transitions MUST use `ease-out` with 150ms for micro
  interactions and 300ms for page/panel transitions. No animation MUST
  block user interaction.

### Page Layout Standard

Every authenticated page MUST follow this layout skeleton:

```
┌─────────────────────────────────────────────────────┐
│  Navbar (fixed top, 64px height)                    │
│  Logo | Search | Notifications | User Avatar        │
├────────────┬────────────────────────────────────────┤
│  Sidebar   │  Main Content Area                     │
│  (260px)   │  ┌──────────────────────────────────┐  │
│            │  │ Page Header (title + breadcrumb) │  │
│  Nav Items │  ├──────────────────────────────────┤  │
│  - Dash    │  │ Action Bar (filters + buttons)   │  │
│  - Chat    │  ├──────────────────────────────────┤  │
│  - Students│  │ Content (tables/cards/forms)     │  │
│  - Teachers│  │                                  │  │
│  - Courses │  │                                  │  │
│  - Batches │  ├──────────────────────────────────┤  │
│  - Enroll  │  │ Pagination / Footer              │  │
│  - Attend  │  └──────────────────────────────────┘  │
│  - Fees    │                                        │
│  - Exams   │                                        │
│  - Settings│                                        │
├────────────┴────────────────────────────────────────┤
│  Toast Notifications (bottom-right, stacked)        │
└─────────────────────────────────────────────────────┘
```

### Data Table Standard

All entity management pages (Students, Teachers, Courses, Batches,
Enrollments, Attendance, Fees, Exams) MUST use a consistent DataTable
component with: column sorting, column visibility toggle, global search,
column-level filters, row selection (single + bulk), pagination
(10/25/50/100 rows per page), export to CSV, loading skeleton during
fetch, and empty state illustration when no data matches filters.

### Form Standard

All create/edit forms MUST include: field-level validation with inline
error messages, required field indicators (*), loading state on submit
button, success toast on completion, confirmation dialog for destructive
actions (delete), and autofocus on first input field.

### Chat Interface Standard

The Agent Chat page MUST provide: a message thread with user/agent
message bubbles, typing indicator while agent processes, source citation
display (collection + document), intent badge on each agent response,
action confirmation dialogs for DB mutations (enroll, pay fee), session
history in a collapsible sidebar, and markdown rendering in agent
responses.

## Development Workflow & Quality Gates

### Workflow

1. **Spec Phase**: Write YAML spec for the module → Team review → Approve.
2. **Red Phase**: Write failing tests that validate spec contracts.
3. **Green Phase**: Implement minimum code to pass all tests.
4. **Refactor Phase**: Clean up code without changing behavior; all tests
   MUST still pass.
5. **Review Phase**: Code review against spec, constitution principles,
   and test coverage.
6. **Merge**: Only after all checks pass.

### Quality Gates (every merge MUST pass)

- All pytest tests pass (`uv run pytest tests/ -v`).
- No secrets in committed files (`.env` is gitignored).
- Spec file exists and matches implementation.
- API schemas match OpenAPI auto-generated docs.
- Frontend pages render without console errors on all target viewports.
- Health endpoint (`GET /api/health`) returns all-green for postgres,
  redis, ollama, and vectordb.

### Commit Convention

Use conventional commits: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`,
`chore:`. Each commit message MUST reference the spec or step number
(e.g., `feat(step-2): add 17 database models per specs/02-database-models`).

## Governance

This constitution is the supreme authority for all development decisions
in the Corvit Agentic System project. It supersedes informal agreements,
chat discussions, and ad-hoc decisions. All code reviews and pull requests
MUST verify compliance with these principles.

**Amendment procedure:**
1. Propose amendment with rationale in a dedicated discussion.
2. Document the change with MAJOR/MINOR/PATCH version bump reasoning.
3. Update this file and propagate changes to dependent templates.
4. All active team members MUST acknowledge the amendment.

**Versioning policy:**
- MAJOR: Backward-incompatible principle removal or redefinition.
- MINOR: New principle added or existing principle materially expanded.
- PATCH: Clarification, typo fix, or non-semantic refinement.

**Compliance expectation:**
Every developer and AI agent MUST read this constitution before starting
work. Violations MUST be flagged during code review. Repeated violations
require a team retrospective to determine if the principle needs amendment
or if the workflow needs adjustment.

**Version**: 1.0.0 | **Ratified**: 2026-02-02 | **Last Amended**: 2026-02-02
