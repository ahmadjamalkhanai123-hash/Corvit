# Tasks: Corvit Agentic System — Phase 1

**Input**: Design documents from `/specs/001-corvit-agentic-system/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Constitution Principle III mandates TDD — test tasks are included for backend modules.

**Organization**: Tasks are organized by the 7 implementation chunks (mapped to user stories) for context-optimized, incremental delivery.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story/chunk this task belongs to
- Include exact file paths in descriptions

## Phase 1: Setup (Project Scaffold)

**Purpose**: Initialize backend and frontend project structures, Docker services, environment configuration.

- [ ] T001 Create `backend/` directory with `pyproject.toml` via `uv init --name corvit-agentic-system`
- [ ] T002 Pin Python version with `uv python pin 3.13.1` in `backend/.python-version`
- [ ] T003 Install backend dependencies: fastapi, uvicorn, sqlalchemy, asyncpg, alembic, pydantic, pydantic-settings, chromadb, httpx, python-jose, passlib, pyyaml, redis, jinja2 via `uv add`
- [ ] T004 Install backend dev dependencies: pytest, pytest-asyncio, pytest-httpx via `uv add --dev`
- [ ] T005 [P] Create `backend/docker-compose.yml` with PostgreSQL 16-alpine and Redis 7-alpine services per Blueprint Section 8
- [ ] T006 [P] Create `backend/.env.example` with all config keys (DATABASE_URL, REDIS_URL, OLLAMA_BASE_URL, OLLAMA_MODEL, LLM_PROVIDER, JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_MINUTES, CHROMA_DB_PATH, DEBUG)
- [ ] T007 [P] Create `backend/.env` from `.env.example` with development values
- [ ] T008 [P] Create `backend/.gitignore` (include .env, __pycache__, .pytest_cache, chroma_db/, *.pyc, .venv/)
- [ ] T009 [P] Create `frontend/` directory with `npx create-next-app@latest` (TypeScript, Tailwind CSS, App Router, src/ directory)
- [ ] T010 [P] Initialize shadcn/ui in frontend via `npx shadcn-ui@latest init` with `components.json` config
- [ ] T011 [P] Create `frontend/.env.local` with `NEXT_PUBLIC_API_URL=http://localhost:8000`
- [ ] T012 Create `backend/src/__init__.py` and all package `__init__.py` files for: config, database, vectordb, llm, rag, rules, agents, agents/director, auth, api, api/routes, api/schemas

**Checkpoint**: Both `backend/` and `frontend/` directories exist with dependency manifests. Docker Compose ready.

---

## Phase 2: Foundational (Chunk 1 — Foundation)

**Purpose**: Core infrastructure that MUST be complete before ANY feature work. Config, database connection, FastAPI app factory, health endpoint.

**CRITICAL**: No chunk/story work can begin until this phase is complete.

- [ ] T013 Create `backend/src/config/settings.py` — Pydantic Settings class loading all .env variables with defaults per contracts/health.md
- [ ] T014 Write test `backend/tests/test_config.py` — verify settings load from env, defaults work, required fields validated
- [ ] T015 Create `backend/src/database/connection.py` — async SQLAlchemy engine, session factory, `get_db` FastAPI dependency
- [ ] T016 Create `backend/src/api/main.py` — FastAPI app factory with CORS middleware (allow localhost:3000), lifespan event for DB connection
- [ ] T017 Create `backend/src/api/deps.py` — shared dependencies (get_db, get_settings, get_redis)
- [ ] T018 Create `backend/src/api/schemas/common.py` — PaginatedResponse, ErrorResponse, HealthResponse Pydantic models
- [ ] T019 Create `backend/src/api/routes/health.py` — GET /api/health checking postgres, redis, ollama, vectordb per contracts/health.md
- [ ] T020 Create `backend/tests/conftest.py` — pytest fixtures for test DB session, test client, test settings
- [ ] T021 Run `docker compose up -d` and verify PostgreSQL + Redis are healthy
- [ ] T022 Initialize Alembic: `uv run alembic init backend/migrations`, configure `backend/alembic.ini` and `migrations/env.py` with async engine
- [ ] T023 Start FastAPI server `uv run uvicorn src.api.main:app --reload --port 8000` and verify GET /api/health returns 200

**Checkpoint**: FastAPI running on :8000, health check returns postgres=up, redis=up. Foundation ready.

---

## Phase 3: Data Layer (Chunk 2) — supports US1 🎯 MVP

**Goal**: All 17 database tables defined, migrated, and seeded with sample data.

**Independent Test**: Run `uv run pytest tests/test_database_models.py -v` — all model creation, relationship, and constraint tests pass. Verify seed data via `psql` or API.

### Tests for Data Layer

- [ ] T024 [P] Write `backend/tests/test_database_models.py` — test creation of all 17 models, test relationships (Student→Enrollment→Batch→Course), test unique constraints (student email, enrollment student+batch), test timestamps auto-set

### Implementation for Data Layer

- [ ] T025 Create `backend/src/database/models.py` — define all 17 SQLAlchemy ORM models per data-model.md: User, Student, Teacher, Course, Batch, Enrollment, Attendance, Fee, Exam, ExamResult, Certification, LabBooking, Equipment, Project, Message, AgentMemory, EventLog
- [ ] T026 Generate Alembic migration `backend/migrations/versions/001_initial_schema.py` via `uv run alembic revision --autogenerate -m "initial schema"`
- [ ] T027 Run migration `uv run alembic upgrade head` and verify all 17 tables exist in PostgreSQL
- [ ] T028 Create `backend/src/database/seed.py` — seed function that populates: 5 courses, 4 teachers, 5 batches, 20 students, enrollment records, 30 days attendance, fee records, lab equipment, 1 admin user per Blueprint Section 12
- [ ] T029 Create `backend/scripts/seed_database.py` — CLI runner that calls seed function
- [ ] T030 Run `uv run python scripts/seed_database.py` and verify data in database
- [ ] T031 Run `uv run pytest tests/test_database_models.py -v` — all tests pass

**Checkpoint**: 17 tables created, seed data loaded. Data layer complete.

---

## Phase 4: Intelligence (Chunk 3) — supports US2, US4

**Goal**: Working RAG pipeline (vector DB + LLM) and rule engine for attendance/fee alerts.

**Independent Test**: RAG query "What courses do you offer?" returns sourced answer. Rule engine correctly flags student with 70% attendance as orange alert.

### Tests for Intelligence

- [ ] T032 [P] Write `backend/tests/test_vectordb.py` — test ChromaDB connection, 4 collections exist, 24 docs loaded, query returns relevant results
- [ ] T033 [P] Write `backend/tests/test_llm_provider.py` — test abstract interface, test OllamaProvider.generate() returns LLMResponse, test OllamaProvider.is_available(), test factory creates correct provider from env
- [ ] T034 [P] Write `backend/tests/test_rag_pipeline.py` — test query→context→LLM→answer flow, test source citations included, test empty results handling
- [ ] T035 [P] Write `backend/tests/test_rule_engine.py` — test attendance thresholds (85%=yellow, 75%=orange, 60%=red, 3 consecutive absences=red), test fee thresholds (7d=yellow, 15d=orange, 30d=red), test YAML config loading

### Implementation for Intelligence

- [ ] T036 [P] Create `backend/src/vectordb/store.py` — ChromaDB interface: connect, get_collection, query_collection, query_all_collections
- [ ] T037 [P] Create `backend/src/vectordb/embedder.py` — document embedding pipeline using ChromaDB default embeddings
- [ ] T038 Migrate `corvit_data.json` to `backend/src/vectordb/data/corvit_data.json` and migrate `chroma_db/` directory
- [ ] T039 Create `backend/scripts/seed_vectordb.py` — seed script that embeds corvit_data.json into 4 ChromaDB collections (courses, teachers, infrastructure, policies)
- [ ] T040 Create `backend/src/llm/base.py` — abstract LLMProvider with generate(messages, temperature, max_tokens)→LLMResponse and is_available()→bool
- [ ] T041 Create `backend/src/llm/ollama_provider.py` — OllamaProvider implementing LLMProvider via httpx POST to http://localhost:11434/api/chat
- [ ] T042 Create `backend/src/llm/factory.py` — get_llm_provider(settings) factory that returns OllamaProvider (or future ClaudeProvider) based on LLM_PROVIDER env var
- [ ] T043 Create `backend/src/rag/prompts.py` — Jinja2 prompt templates: system prompt for Corvit assistant, RAG context injection template
- [ ] T044 Create `backend/src/rag/pipeline.py` — RAGPipeline class: query(question)→RAGResponse that queries ChromaDB, merges top-N results, calls LLM, returns answer+sources
- [ ] T045 Create `backend/src/config/rules.yaml` — YAML config for attendance thresholds (85/75/60/3-consecutive) and fee thresholds (7/15/30 days)
- [ ] T046 Create `backend/src/rules/engine.py` — RuleEngine class that loads rules.yaml and evaluates student data against thresholds
- [ ] T047 [P] Create `backend/src/rules/attendance_rules.py` — evaluate_attendance(student_id, batch_id)→AlertResult with level (yellow/orange/red) and message
- [ ] T048 [P] Create `backend/src/rules/fee_rules.py` — evaluate_fees(student_id)→AlertResult with level and days_overdue
- [ ] T049 Run all intelligence tests: `uv run pytest tests/test_vectordb.py tests/test_llm_provider.py tests/test_rag_pipeline.py tests/test_rule_engine.py -v`

**Checkpoint**: RAG pipeline returns sourced answers. Rule engine fires correct alerts. Intelligence layer complete.

---

## Phase 5: Auth & API (Chunk 4) — supports US1 🎯 MVP

**Goal**: JWT authentication, role-based access control, and full CRUD endpoints for all 8 entities.

**Independent Test**: Register user, login, get JWT, perform CRUD on students endpoint, verify role restrictions. Swagger UI at /docs shows all 50+ endpoints.

### Tests for Auth & API

- [ ] T050 [P] Write `backend/tests/test_auth.py` — test register, login, JWT creation/verification, role-based access (admin can CRUD, student read-only), expired token rejection
- [ ] T051 [P] Write `backend/tests/test_api_students.py` — test POST/GET/PUT/DELETE /api/students, test pagination, test search/filter, test GET /{id}/attendance, test GET /{id}/fees
- [ ] T052 [P] Write `backend/tests/test_api_courses.py` — test CRUD /api/courses, test GET /{id}/batches

### Implementation for Auth & API

- [ ] T053 Create `backend/src/auth/jwt_handler.py` — create_access_token(data, expires_delta), verify_token(token)→TokenData using python-jose HS256
- [ ] T054 Create `backend/src/auth/dependencies.py` — get_current_user FastAPI dependency, require_role(role) dependency factory
- [ ] T055 Create `backend/src/api/schemas/auth.py` — RegisterRequest, LoginRequest, TokenResponse, UserResponse per contracts/auth.md
- [ ] T056 Create `backend/src/api/routes/auth.py` — POST /api/auth/register, POST /api/auth/login, GET /api/auth/me per contracts/auth.md
- [ ] T057 [P] Create `backend/src/api/schemas/students.py` — StudentCreate, StudentUpdate, StudentResponse, StudentAttendanceSummary, StudentFeesSummary per contracts/students.md
- [ ] T058 [P] Create `backend/src/api/schemas/teachers.py` — TeacherCreate, TeacherUpdate, TeacherResponse, TeacherBatchesResponse per contracts/teachers.md
- [ ] T059 [P] Create `backend/src/api/schemas/courses.py` — CourseCreate, CourseUpdate, CourseResponse, CourseBatchesResponse per contracts/courses.md
- [ ] T060 [P] Create `backend/src/api/schemas/batches.py` — BatchCreate, BatchUpdate, BatchResponse, BatchStudentsResponse, BatchScheduleResponse per contracts/batches.md
- [ ] T061 [P] Create `backend/src/api/schemas/enrollments.py` — EnrollmentCreate, EnrollmentUpdate, EnrollmentResponse per contracts/enrollments.md
- [ ] T062 [P] Create `backend/src/api/schemas/attendance.py` — AttendanceCreate, BulkAttendanceRequest, AttendanceResponse, AttendanceReportResponse per contracts/attendance.md
- [ ] T063 [P] Create `backend/src/api/schemas/fees.py` — FeeCreate, FeePayRequest, FeeResponse, OverdueFeeResponse per contracts/fees.md
- [ ] T064 [P] Create `backend/src/api/schemas/exams.py` — ExamCreate, ExamResultSubmit, ExamResponse, ExamResultsResponse per contracts/exams.md
- [ ] T065 Create `backend/src/api/routes/students.py` — full CRUD + GET /{id}/attendance + GET /{id}/fees per contracts/students.md (admin write, any read)
- [ ] T066 [P] Create `backend/src/api/routes/teachers.py` — full CRUD + GET /{id}/batches per contracts/teachers.md
- [ ] T067 [P] Create `backend/src/api/routes/courses.py` — full CRUD + GET /{id}/batches per contracts/courses.md
- [ ] T068 [P] Create `backend/src/api/routes/batches.py` — full CRUD + GET /{id}/students + GET /{id}/schedule per contracts/batches.md
- [ ] T069 [P] Create `backend/src/api/routes/enrollments.py` — full CRUD + POST /enroll per contracts/enrollments.md
- [ ] T070 [P] Create `backend/src/api/routes/attendance.py` — full CRUD + POST /mark (bulk) + GET /report/{batch_id} per contracts/attendance.md
- [ ] T071 [P] Create `backend/src/api/routes/fees.py` — full CRUD + POST /{id}/pay + GET /overdue per contracts/fees.md
- [ ] T072 [P] Create `backend/src/api/routes/exams.py` — full CRUD + POST /{id}/results + GET /{id}/results per contracts/exams.md
- [ ] T073 Register all route routers in `backend/src/api/main.py` with `/api` prefix
- [ ] T074 Run auth and API tests: `uv run pytest tests/test_auth.py tests/test_api_students.py tests/test_api_courses.py -v`
- [ ] T075 Verify Swagger UI at http://localhost:8000/docs shows all endpoints

**Checkpoint**: 50+ endpoints live, JWT auth working, role-based access enforced. API layer complete.

---

## Phase 6: Director Agent (Chunk 5) — supports US2

**Goal**: End-to-end chat: user sends message → Director Agent classifies intent → routes to handler → returns sourced response.

**Independent Test**: POST /api/chat with "What courses do you offer?" returns intent=course_inquiry with sourced answer. POST with "My attendance?" for a low-attendance student returns rule-based alert.

### Tests for Director Agent

- [ ] T076 Write `backend/tests/test_director_agent.py` — test intent classification for all 9 categories, test RAG routing for course_inquiry, test rule engine routing for attendance_query, test bounded authority (rejects expel/refund requests), test chat API request/response format per contracts/chat.md

### Implementation for Director Agent

- [ ] T077 Create `backend/src/agents/base.py` — abstract BaseAgent with process_message(message, context)→AgentResponse
- [ ] T078 Create `backend/src/agents/director/prompts.py` — system prompt for Director Agent with intent classification instructions, Corvit context, authority boundaries
- [ ] T079 Create `backend/src/agents/director/router.py` — IntentRouter class that classifies messages into 9 intent categories using LLM
- [ ] T080 Create `backend/src/agents/director/tools.py` — DB action functions: enroll_student, check_fees, get_attendance_summary, log_event
- [ ] T081 Create `backend/src/agents/director/agent.py` — DirectorAgent implementing BaseAgent: classify intent → route to handler (RAG/rules/DB action/stub) → build response with sources
- [ ] T082 Create `backend/src/config/agents.yaml` — agent definitions: director agent name, authority boundaries, supported intents
- [ ] T083 Create `backend/src/api/schemas/agent.py` — ChatRequest, ChatResponse, SourceCitation per contracts/chat.md
- [ ] T084 Create `backend/src/api/routes/agent_chat.py` — POST /api/chat endpoint that instantiates DirectorAgent and processes message
- [ ] T085 Create `backend/src/api/routes/dashboard.py` — GET /api/dashboard/stats endpoint returning KPIs, trends, activity per contracts/dashboard.md
- [ ] T086 Register agent_chat and dashboard routers in `backend/src/api/main.py`
- [ ] T087 Run director agent tests: `uv run pytest tests/test_director_agent.py -v`
- [ ] T088 End-to-end test: POST /api/chat "What courses do you offer?" → verify sourced response

**Checkpoint**: Director Agent classifies intents, routes to handlers, returns sourced responses. Backend complete.

---

## Phase 7: Frontend Core (Chunk 6) — supports US1, US3

**Goal**: Running Next.js app with login, registration, authenticated dashboard layout (sidebar + navbar), and dashboard page with KPI cards and charts.

**Independent Test**: Open localhost:3000 → redirects to login → login with admin/admin123 → lands on dashboard with KPI cards, charts, sidebar navigation.

### Implementation for Frontend Core

- [ ] T089 Install shadcn/ui components: `npx shadcn-ui@latest add button input card dialog table badge toast skeleton avatar select dropdown-menu sheet breadcrumb separator label tabs`
- [ ] T090 Install additional frontend dependencies: `npm install swr recharts lucide-react react-markdown @tanstack/react-table date-fns`
- [ ] T091 Create `frontend/src/lib/utils.ts` — cn() class merge helper, date formatters, currency formatter (PKR)
- [ ] T092 Create `frontend/src/lib/constants.ts` — API_URL, nav items array (12 pages with icons, labels, routes), role definitions
- [ ] T093 Create `frontend/src/types/entities.ts` — TypeScript interfaces for all 17 entities matching data-model.md
- [ ] T094 Create `frontend/src/types/api.ts` — PaginatedResponse<T>, ErrorResponse, HealthCheck, ChatRequest, ChatResponse types
- [ ] T095 Create `frontend/src/types/auth.ts` — User, LoginRequest, RegisterRequest, TokenResponse types
- [ ] T096 Create `frontend/src/lib/api-client.ts` — fetch wrapper: apiClient.get/post/put/delete with JWT cookie injection, error handling, base URL from env
- [ ] T097 Create `frontend/src/lib/auth.ts` — login(), register(), logout(), getMe() functions using api-client
- [ ] T098 Create `frontend/src/hooks/use-auth.ts` — React context + provider for auth state (user, isLoading, isAuthenticated), auto-redirect to /login on 401
- [ ] T099 Create `frontend/src/hooks/use-api.ts` — generic useCRUD<T>(resource) hook using SWR: list (paginated), getById, create, update, delete with optimistic updates
- [ ] T100 Create `frontend/src/hooks/use-debounce.ts` — useDebounce(value, delay) for search inputs
- [ ] T101 Create `frontend/src/components/layout/navbar.tsx` — fixed top navbar (64px): Corvit logo, global search input, notification bell, user avatar with dropdown (profile, settings, logout)
- [ ] T102 Create `frontend/src/components/layout/sidebar.tsx` — collapsible sidebar (260px): nav items from constants with Lucide icons, active route highlight, mobile hamburger via Sheet component
- [ ] T103 Create `frontend/src/components/layout/page-header.tsx` — page title + breadcrumb component
- [ ] T104 Create `frontend/src/components/shared/empty-state.tsx` — illustration + title + description + CTA button component
- [ ] T105 [P] Create `frontend/src/components/shared/confirm-dialog.tsx` — reusable confirmation dialog for destructive actions
- [ ] T106 [P] Create `frontend/src/components/shared/loading-spinner.tsx` — centered spinner component
- [ ] T107 [P] Create `frontend/src/components/shared/error-boundary.tsx` — React error boundary with retry button
- [ ] T108 Configure `frontend/tailwind.config.ts` — extend theme with Corvit brand colors (primary blue, semantic colors), Inter font, 4px spacing scale, shadow tiers per constitution design system
- [ ] T109 Create `frontend/src/app/layout.tsx` — root layout: Inter font, AuthProvider wrapper, Toaster component, metadata
- [ ] T110 Create `frontend/src/app/(auth)/login/page.tsx` — login form (username, password), role badge, "Create account" link, JWT cookie handling, redirect to /dashboard on success
- [ ] T111 Create `frontend/src/app/(auth)/register/page.tsx` — register form (username, email, password, role select), redirect to /login on success
- [ ] T112 Create `frontend/src/app/(dashboard)/layout.tsx` — authenticated layout shell: auth guard, Navbar + Sidebar + main content area with proper grid per constitution page layout standard
- [ ] T113 Create `frontend/src/components/charts/kpi-card.tsx` — KPI card component: icon, title, value, trend indicator (up/down arrow + percentage)
- [ ] T114 Create `frontend/src/components/charts/line-chart.tsx` — Recharts line chart wrapper with responsive container, tooltips, grid
- [ ] T115 [P] Create `frontend/src/components/charts/bar-chart.tsx` — Recharts bar chart wrapper for enrollment distribution
- [ ] T116 Create `frontend/src/app/(dashboard)/dashboard/page.tsx` — dashboard page: 4 KPI cards (students, courses, revenue, overdue), attendance trend LineChart, enrollment BarChart, recent activity feed, system health indicator using GET /api/dashboard/stats
- [ ] T117 Create `frontend/src/app/page.tsx` — root page that redirects authenticated users to /dashboard, unauthenticated to /login
- [ ] T118 Verify frontend builds without errors: `npm run build`
- [ ] T119 Test full auth flow: login → dashboard → verify KPI data → logout

**Checkpoint**: Frontend running at :3000 with login, dashboard, sidebar navigation. Frontend core complete.

---

## Phase 8: Frontend Pages (Chunk 7) — supports US1, US2, US4, US5

**Goal**: All remaining 10 pages functional and connected to live API.

**Independent Test**: Navigate to each page, verify data loads, CRUD operations work, responsive layout correct on desktop/tablet/mobile.

### Data Table Foundation

- [ ] T120 Create `frontend/src/components/data-table/data-table.tsx` — generic DataTable<T> using TanStack Table with column sorting, global search, pagination (10/25/50/100), row selection, loading skeleton, empty state
- [ ] T121 Create `frontend/src/components/data-table/toolbar.tsx` — DataTable toolbar: search input, column visibility toggle, filter dropdowns, "Add new" button, CSV export button
- [ ] T122 Create `frontend/src/components/data-table/pagination.tsx` — DataTable pagination: page info, rows per page selector, prev/next/first/last buttons
- [ ] T123 Create `frontend/src/components/data-table/faceted-filter.tsx` — column-level filter with checkbox list (e.g., filter by status, role, course)

### Chat Page (US2)

- [ ] T124 Create `frontend/src/hooks/use-websocket.ts` — SSE hook: connect to /api/chat stream, handle typing indicator, parse streamed response chunks
- [ ] T125 Create `frontend/src/components/chat/message-bubble.tsx` — chat message bubble: user (right-aligned, blue) and agent (left-aligned, gray), markdown rendering via react-markdown
- [ ] T126 [P] Create `frontend/src/components/chat/typing-indicator.tsx` — animated dots indicator while agent processes
- [ ] T127 [P] Create `frontend/src/components/chat/intent-badge.tsx` — colored badge showing classified intent (course_inquiry=blue, enrollment=green, fee_query=amber, etc.)
- [ ] T128 [P] Create `frontend/src/components/chat/source-citation.tsx` — collapsible source citation: collection name, document preview, relevance score
- [ ] T129 Create `frontend/src/components/chat/chat-thread.tsx` — full chat thread: message list, scroll-to-bottom, message input with send button, session history sidebar (Sheet)
- [ ] T130 Create `frontend/src/app/(dashboard)/chat/page.tsx` — chat page: ChatThread component, session list sidebar, "New chat" button

### Entity Management Pages (US1)

- [ ] T131 Create `frontend/src/app/(dashboard)/students/page.tsx` — students DataTable page: columns (name, email, phone, status, enrollment_date), CRUD dialog, search, filters (status), row actions (edit, delete, view attendance/fees)
- [ ] T132 [P] Create `frontend/src/app/(dashboard)/teachers/page.tsx` — teachers DataTable page: columns (name, email, specialization, qualification, is_active), CRUD dialog, search, row actions (edit, delete, view batches)
- [ ] T133 [P] Create `frontend/src/app/(dashboard)/batches/page.tsx` — batches DataTable page: columns (name, course, teacher, room, schedule, status, enrolled/capacity), CRUD dialog, filter by course/status, row actions (view students, view schedule)
- [ ] T134 Create `frontend/src/app/(dashboard)/enrollments/page.tsx` — enrollments page: DataTable (student, batch, course, date, status), enrollment wizard dialog (select student → select course → select batch → confirm), filter by status
- [ ] T135 Create `frontend/src/app/(dashboard)/exams/page.tsx` — exams page: DataTable (title, batch, type, date, total_marks), create exam dialog, results entry dialog (bulk form per student), grade distribution chart

### Courses Page (US5 — Card Grid)

- [ ] T136 Create `frontend/src/app/(dashboard)/courses/page.tsx` — courses page: card grid view (name, code, duration, fee, batch count, category badge), click card → detail sheet with batch list (teacher, schedule, seats available), CRUD dialog for admins, search + category filter

### Attendance & Fee Pages (US4 — Alerts)

- [ ] T137 Create `frontend/src/app/(dashboard)/attendance/page.tsx` — attendance page: batch selector, calendar/date picker, grid view of students with present/absent/late toggles, bulk mark button, alert badges (yellow/orange/red) per rule engine, attendance report section with percentages
- [ ] T138 Create `frontend/src/app/(dashboard)/fees/page.tsx` — fees page: DataTable (student, course, amount, paid, due_date, status, alert_level), "Record payment" dialog, overdue filter tab with alert indicators (yellow/orange/red badges), payment history

### Settings Page

- [ ] T139 Create `frontend/src/app/(dashboard)/settings/page.tsx` — settings page: user profile form (username, email), password change form, role display (read-only), role-based visibility (admin sees system settings section)

### Final Integration

- [ ] T140 Add all page routes to sidebar navigation in `frontend/src/components/layout/sidebar.tsx` with correct Lucide icons
- [ ] T141 Verify all 12 pages load without console errors on desktop (1440px), tablet (768px), and mobile (375px) viewports
- [ ] T142 Verify all CRUD operations work end-to-end: create → appears in table → edit → changes persist → delete → confirms → removed

**Checkpoint**: All 12 pages functional. Complete production application.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final quality pass across all chunks.

- [ ] T143 [P] Run full backend test suite: `uv run pytest tests/ -v` — all tests pass
- [ ] T144 [P] Verify no secrets in committed files: scan for API keys, passwords, JWT secrets in all files
- [ ] T145 [P] Verify GET /api/health returns all 4 backends green (postgres, redis, ollama, vectordb)
- [ ] T146 [P] Verify Swagger UI at /docs matches all contract files in specs/001-corvit-agentic-system/contracts/
- [ ] T147 End-to-end smoke test: register → login → dashboard KPIs → chat "What courses?" → students CRUD → attendance bulk mark → fee payment → logout
- [ ] T148 [P] Verify frontend build passes: `npm run build` (no TypeScript errors, no build warnings)
- [ ] T149 [P] Run quickstart.md from scratch: verify a new developer can set up the entire system following the guide
- [ ] T150 Verify all conventional commit messages reference spec/step numbers

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundation)**: Depends on Phase 1 — BLOCKS all subsequent phases
- **Phase 3 (Data Layer)**: Depends on Phase 2
- **Phase 4 (Intelligence)**: Depends on Phase 2, can run in parallel with Phase 3
- **Phase 5 (Auth & API)**: Depends on Phase 3 (needs models)
- **Phase 6 (Director Agent)**: Depends on Phase 4 (needs RAG + rules) and Phase 5 (needs API framework)
- **Phase 7 (Frontend Core)**: Depends on Phase 5 (needs API endpoints for auth + dashboard)
- **Phase 8 (Frontend Pages)**: Depends on Phase 6 (needs chat API) and Phase 7 (needs frontend shell)
- **Phase 9 (Polish)**: Depends on all previous phases

### Optimal Execution Flow

```
Phase 1 (Setup)
    │
    ▼
Phase 2 (Foundation)
    │
    ├───────────────┐
    ▼               ▼
Phase 3          Phase 4
(Data Layer)     (Intelligence)
    │               │
    ▼               │
Phase 5 ◄──────────┘
(Auth & API)
    │
    ├───────────────┐
    ▼               ▼
Phase 6          Phase 7
(Director Agent) (Frontend Core)
    │               │
    └──────┬────────┘
           ▼
       Phase 8
    (Frontend Pages)
           │
           ▼
       Phase 9
       (Polish)
```

### Parallel Opportunities

- **Phase 3 + Phase 4**: Data layer and intelligence can be built simultaneously (different files, no dependencies)
- **Phase 6 + Phase 7**: Director agent and frontend core can be built simultaneously (backend vs frontend)
- **Within Phase 5**: All 8 schema files (T057-T064) can be created in parallel; all 8 route files (T065-T072) can be created in parallel
- **Within Phase 7**: All shared components (T104-T107) can be created in parallel
- **Within Phase 8**: Chat components (T125-T128) in parallel; entity pages (T131-T135) in parallel after DataTable foundation
- **Within Phase 9**: All verification tasks (T143-T149) in parallel

---

## Implementation Strategy

### MVP First (Chunks 1-2 + Chunk 4 API only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundation
3. Complete Phase 3: Data Layer
4. Complete Phase 5: Auth & API (just CRUD, no agent)
5. **STOP and VALIDATE**: All 50+ endpoints working at /docs, seed data loaded
6. This alone is a functional institute management API

### Incremental Delivery

1. Setup + Foundation → Backend running with health check
2. + Data Layer → 17 tables, seed data (**Chunk 1-2 deliverable**)
3. + Intelligence → RAG answers + rule alerts (**Chunk 3 deliverable**)
4. + Auth & API → 50+ endpoints live (**Chunk 4 deliverable**)
5. + Director Agent → Chat working (**Chunk 5 deliverable**)
6. + Frontend Core → Login + Dashboard (**Chunk 6 deliverable**)
7. + Frontend Pages → Complete app (**Chunk 7 deliverable**)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps tasks to user stories from spec.md
- Each chunk/phase produces an independently demonstrable increment
- TDD enforced: test tasks precede implementation in each phase
- Commit after each task or logical group using conventional commits
- All file paths are relative to repository root
