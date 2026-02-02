# Feature Specification: Corvit Agentic System — Phase 1

**Feature Branch**: `001-corvit-agentic-system`
**Created**: 2026-02-02
**Status**: Draft
**Input**: User description: "Project divided into optimized chunks for context and standard optimization. Real-time production application with less work but standard design and production ready."

## Chunking Strategy

This specification divides the full Corvit Agentic System Phase 1 into **7 implementation chunks**. Each chunk is a self-contained, independently testable, and deployable unit. Chunks are ordered by dependency — each builds on the previous one. This chunking strategy optimizes for:

- **Context window efficiency**: Each chunk fits within a single AI-assisted session
- **Incremental delivery**: Every chunk produces a working, demonstrable system
- **Minimal rework**: Shared infrastructure is built once in Chunk 1, reused everywhere
- **Production readiness**: Frontend uses a component library (shadcn/ui + Next.js) to maximize output with minimal custom code

| Chunk | Name | Scope | Deliverable |
|-------|------|-------|-------------|
| 1 | Foundation | Config, DB connection, Docker, project scaffold | Running FastAPI + PostgreSQL + Redis with health check |
| 2 | Data Layer | 17 ORM models, migrations, seed data | Populated database with all tables and sample data |
| 3 | Intelligence | Vector DB, LLM provider, RAG pipeline, rule engine | Working RAG queries and rule evaluations |
| 4 | Auth & API | JWT auth, all 8 CRUD route sets, schemas | Complete REST API with 50+ endpoints at `/docs` |
| 5 | Director Agent | Intent router, agent tools, chat API | End-to-end chat: user question → agent → response |
| 6 | Frontend Core | Next.js scaffold, design system, layout, auth pages, dashboard | Running frontend with login, dashboard, navigation |
| 7 | Frontend Pages | All remaining pages: chat, students, teachers, courses, batches, enrollments, attendance, fees, exams, settings | Complete production application |

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Admin Manages Institute Data (Priority: P1)

An institute administrator logs in to the Corvit system and manages all core data: students, teachers, courses, batches, enrollments, attendance records, fee payments, and exam results. They can create, view, update, and delete records through both the API and a professional web interface with data tables, search, filtering, and pagination.

**Why this priority**: Without data management, no other feature works. This is the backbone of the entire system — the Director Agent, RAG pipeline, and rule engine all depend on having real data in the database.

**Independent Test**: Can be fully tested by logging in as admin, performing CRUD operations on all 8 entities, and verifying data persistence. Delivers immediate value as a standalone institute management system.

**Acceptance Scenarios**:

1. **Given** an admin user exists, **When** they log in with valid credentials, **Then** they receive a JWT token and can access protected endpoints
2. **Given** the admin is authenticated, **When** they create a new student record, **Then** the student appears in the database and in the students data table
3. **Given** existing student records, **When** the admin searches by name, **Then** matching students are displayed with pagination
4. **Given** a student record, **When** the admin updates the student's phone number, **Then** the change persists and displays correctly
5. **Given** a student with no enrollments, **When** the admin deletes the student, **Then** the record is removed from the database
6. **Given** the admin navigates to any entity page, **When** the page loads, **Then** a data table with sorting, search, filter, and pagination is displayed

---

### User Story 2 — User Chats with Director Agent (Priority: P2)

A user (admin, teacher, or student) opens the chat interface and asks natural-language questions about courses, fees, teachers, attendance, or enrollment. The Director Agent classifies the intent, retrieves relevant context via RAG from the vector database, applies rule-based checks where applicable (attendance/fee thresholds), and returns an accurate, sourced response. For action-oriented requests (e.g., "enroll me in CCNA"), the agent can execute database operations with confirmation.

**Why this priority**: This is the core differentiator — an AI-powered institute assistant. It depends on the data layer (Chunk 2) and intelligence layer (Chunk 3) being in place.

**Independent Test**: Can be fully tested by sending chat messages via the `/api/chat` endpoint or through the chat UI. Verify intent classification, RAG answer quality, source citations, and rule-based alerts.

**Acceptance Scenarios**:

1. **Given** a user is authenticated, **When** they ask "What courses do you offer?", **Then** the agent returns a list of courses with fees, sourced from the vector database
2. **Given** a student with 70% attendance, **When** they ask about their attendance, **Then** the agent triggers the orange-level rule and warns about the threshold
3. **Given** a user asks "Enroll me in CCNA batch", **When** the agent classifies intent as enrollment, **Then** it confirms the action before executing the database operation
4. **Given** any agent response, **When** displayed in the chat UI, **Then** it shows the intent badge, source citations, and formatted markdown
5. **Given** the agent is processing, **When** the user is waiting, **Then** a typing indicator is displayed in real-time

---

### User Story 3 — Dashboard Overview (Priority: P3)

An authenticated user lands on the dashboard and sees an at-a-glance overview of the institute: total students, active batches, revenue collected, overdue fees count, attendance averages, and recent system activity. Key performance indicators are displayed in cards, with charts for trends over time.

**Why this priority**: The dashboard provides immediate visual value but depends on having data (Chunk 2) and API endpoints (Chunk 4) in place. It is the landing page after login and creates the "production feel" of the application.

**Independent Test**: Can be fully tested by logging in and verifying that dashboard KPI cards display accurate counts from the database, charts render with correct data, and the page loads within performance targets.

**Acceptance Scenarios**:

1. **Given** an admin is logged in, **When** they land on the dashboard, **Then** they see KPI cards for total students, active courses, total revenue, and overdue fees
2. **Given** attendance data exists, **When** the dashboard loads, **Then** an attendance trend chart displays the last 30 days
3. **Given** recent enrollment activity, **When** the dashboard loads, **Then** a recent activity feed shows the latest 10 events
4. **Given** the system health endpoint is available, **When** the dashboard loads, **Then** a system health indicator shows PostgreSQL, Redis, Ollama, and VectorDB status

---

### User Story 4 — Attendance & Fee Alerts (Priority: P4)

Teachers and admins receive automated alerts when students cross attendance or fee thresholds. The rule engine evaluates all students against configurable thresholds (attendance < 85% yellow, < 75% orange, < 60% red; fees 7/15/30 days overdue) and surfaces alerts in the UI and through the Director Agent.

**Why this priority**: This is the "zero-token" intelligence layer — pure rule-based computation with no LLM cost. It provides immediate operational value to the institute.

**Independent Test**: Can be tested by creating students with varying attendance percentages and fee overdue dates, then verifying that the correct alert levels appear on the attendance and fee management pages.

**Acceptance Scenarios**:

1. **Given** a student with 80% attendance, **When** the attendance page loads, **Then** a yellow warning badge is displayed next to their name
2. **Given** a fee record 20 days overdue, **When** the fees page loads, **Then** an orange overdue indicator is shown with escalation status
3. **Given** a student asks the Director Agent about their attendance, **When** their attendance is below 75%, **Then** the agent includes the rule-based warning in its response

---

### User Story 5 — Course Catalog & Enrollment Workflow (Priority: P5)

A prospective or current student browses the course catalog displayed as cards with course details, sees available batches with schedule/teacher/room information, and can request enrollment through the UI. Admins process enrollment requests and assign students to batches.

**Why this priority**: This is the student-facing onboarding flow. It makes the system useful beyond admin data entry.

**Independent Test**: Can be tested by browsing courses, viewing batch details, and completing an enrollment request through the UI.

**Acceptance Scenarios**:

1. **Given** courses exist in the system, **When** a user visits the courses page, **Then** courses are displayed as cards with name, duration, fee, and batch count
2. **Given** a course card is clicked, **When** the detail view opens, **Then** available batches are listed with teacher, schedule, room, and seat availability
3. **Given** a student selects a batch, **When** they request enrollment, **Then** the enrollment is recorded and the admin is notified

---

### Edge Cases

- What happens when Ollama is not running? The health check reports it down; the chat endpoint returns a graceful error "AI service temporarily unavailable"; all non-AI features continue working
- What happens when the vector database has no relevant documents for a query? The RAG pipeline returns a response stating "I don't have specific information about that topic" with no hallucinated sources
- What happens when a user tries to enroll in a full batch? The system returns a clear message "This batch is at capacity" and suggests alternative batches
- What happens when the JWT token expires? The frontend detects 401 responses, clears the session, and redirects to the login page with a "Session expired" message
- What happens when bulk attendance marking is submitted with invalid data? Each row is validated independently; valid rows are saved, invalid rows return field-level errors
- What happens when the database is empty (no seed data)? All pages show empty state illustrations with calls-to-action (e.g., "No students yet. Add your first student.")
- What happens on mobile viewport? All pages collapse the sidebar into a hamburger menu, data tables become responsive card lists, and forms stack vertically

## Requirements *(mandatory)*

### Functional Requirements

**Chunk 1 — Foundation**

- **FR-001**: System MUST load configuration from environment variables with sensible defaults
- **FR-002**: System MUST connect to PostgreSQL asynchronously using connection pooling
- **FR-003**: System MUST connect to Redis for caching and session management
- **FR-004**: System MUST expose a health endpoint that checks PostgreSQL, Redis, Ollama, and ChromaDB status
- **FR-005**: System MUST run PostgreSQL and Redis via Docker Compose with persistent volumes

**Chunk 2 — Data Layer**

- **FR-006**: System MUST define 17 database tables as ORM models with proper relationships and constraints
- **FR-007**: System MUST track all schema changes through versioned migrations
- **FR-008**: System MUST provide a seed script that populates the database with sample data (5 courses, 4 teachers, 5 batches, 20 students, enrollment records, 30 days attendance, fee records, lab equipment, 1 admin user)
- **FR-009**: All models MUST include created_at and updated_at timestamps

**Chunk 3 — Intelligence**

- **FR-010**: System MUST query ChromaDB across 4 collections (courses, teachers, infrastructure, policies) and merge top-N results as context
- **FR-011**: System MUST communicate with Ollama via HTTP to generate LLM responses
- **FR-012**: LLM provider MUST be swappable via a single environment variable with no code changes
- **FR-013**: RAG pipeline MUST return structured responses with answer text, source citations, and model metadata
- **FR-014**: Rule engine MUST evaluate attendance and fee thresholds using pure computation (no LLM tokens)
- **FR-015**: Rule engine MUST support configurable thresholds loaded from YAML

**Chunk 4 — Auth & API**

- **FR-016**: System MUST support user registration with username, email, password, and role
- **FR-017**: System MUST authenticate users via username/password and issue JWT tokens
- **FR-018**: System MUST enforce role-based access control (admin, teacher, student) on all protected endpoints
- **FR-019**: System MUST provide full CRUD endpoints for all 8 entities (students, teachers, courses, batches, enrollments, attendance, fees, exams) with pagination, filtering, and sorting
- **FR-020**: Every entity endpoint MUST support: POST (create), GET list (paginated), GET by ID, PUT (update), DELETE
- **FR-021**: System MUST provide entity-specific convenience endpoints (e.g., student attendance history, batch student roster, overdue fees list)
- **FR-022**: All API responses MUST follow a consistent format with standardized error handling

**Chunk 5 — Director Agent**

- **FR-023**: Director Agent MUST classify user messages into 9 intent categories (course_inquiry, enrollment, fee_query, attendance_query, counseling, complaint, general, class_related, lab_related)
- **FR-024**: Agent MUST route each intent to the correct handler (RAG pipeline, rule engine, DB action, or future agent stub)
- **FR-025**: Agent MUST maintain bounded authority — it can route, warn, and recommend but MUST NOT autonomously expel students, change fees, modify policies, or process large refunds
- **FR-026**: Chat API MUST accept a message and optional session_id and return reply, intent, action_taken, data, and sources
- **FR-027**: Agent responses MUST include source citations when RAG is used

**Chunk 6 — Frontend Core**

- **FR-028**: Frontend MUST provide a login page with username/password form and role indicator
- **FR-029**: Frontend MUST provide a registration page with role selection
- **FR-030**: Frontend MUST store JWT token securely and include it in all API requests
- **FR-031**: Frontend MUST redirect unauthenticated users to the login page
- **FR-032**: Frontend MUST display a persistent sidebar navigation with links to all 12 pages
- **FR-033**: Frontend MUST display a top navbar with logo, global search, notifications area, and user avatar/menu
- **FR-034**: Frontend MUST provide a dashboard page with KPI cards, charts, recent activity, and system health
- **FR-035**: Frontend MUST use a consistent design system (colors, typography, spacing, shadows) across all pages
- **FR-036**: Frontend MUST be fully responsive across desktop, tablet, and mobile viewports

**Chunk 7 — Frontend Pages**

- **FR-037**: Chat page MUST display a real-time message thread with user/agent bubbles, typing indicator, intent badges, source citations, and markdown rendering
- **FR-038**: Chat page MUST support session history in a collapsible sidebar
- **FR-039**: Students page MUST display a data table with sorting, search, filtering, pagination, and CRUD modals
- **FR-040**: Teachers page MUST display a data table with sorting, search, filtering, pagination, and CRUD modals
- **FR-041**: Courses page MUST display a card grid view with course details and batch information
- **FR-042**: Batches page MUST display schedule information, student roster, and teacher assignment
- **FR-043**: Enrollments page MUST provide a step-by-step enrollment workflow with batch selection
- **FR-044**: Attendance page MUST provide a calendar/grid view with bulk marking capability and alert indicators
- **FR-045**: Fees page MUST display payment status, overdue alerts, and payment recording functionality
- **FR-046**: Exams page MUST support exam scheduling, result entry, and grade distribution display
- **FR-047**: Settings page MUST allow profile editing and display role-based visibility controls
- **FR-048**: All entity pages MUST show empty state illustrations when no data exists
- **FR-049**: All destructive actions (delete) MUST require confirmation dialogs
- **FR-050**: All forms MUST provide inline field-level validation with error messages

### Key Entities

- **Student**: Name, email, phone, CNIC, guardian info, enrollment date. Has many enrollments, attendance records, fee records, exam results
- **Teacher**: Name, email, phone, specialization, qualification. Has many batches
- **Course**: Name, code, duration, fee amount, description, category. Has many batches
- **Batch**: Course reference, teacher reference, room, schedule (days + time), start date, end date, max capacity. Has many enrollments
- **Enrollment**: Student reference, batch reference, enrollment date, status (active/completed/dropped)
- **Attendance**: Student reference, batch reference, date, status (present/absent/late/excused)
- **Fee**: Student reference, course reference, amount, due date, paid amount, paid date, status (pending/partial/paid/overdue)
- **Exam**: Batch reference, title, date, total marks, exam type (midterm/final/quiz)
- **Exam Result**: Exam reference, student reference, marks obtained, grade, remarks
- **User**: Username, email, hashed password, role (admin/teacher/student), active status
- **Certification**: Student reference, name, vendor, issue date, expiry date
- **Lab Booking**: Student/batch reference, lab, date, time slot, equipment list
- **Equipment**: Name, lab, quantity, working status
- **Project**: Student reference, batch reference, title, description, status, grade
- **Message**: Sender agent, receiver agent, content, message type, status
- **Agent Memory**: Agent identifier, key, value, context
- **Event Log**: Event type, actor, target, details, timestamp (audit trail)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Admin can complete full CRUD lifecycle (create → read → update → delete) for any entity within 60 seconds through the web interface
- **SC-002**: Users receive accurate, sourced answers from the Director Agent for 95% of course, fee, and teacher inquiries
- **SC-003**: Agent response time is under 5 seconds from message submission to answer display (including LLM processing)
- **SC-004**: All 12 frontend pages load and become interactive within 3 seconds on a standard connection
- **SC-005**: Rule engine correctly identifies 100% of attendance and fee threshold violations with zero false negatives
- **SC-006**: System health check confirms all 4 backends (PostgreSQL, Redis, Ollama, ChromaDB) are operational
- **SC-007**: Frontend renders correctly without layout breaks on viewports from 320px to 2560px wide
- **SC-008**: Zero secrets (passwords, API keys, JWT secrets) appear in any committed file
- **SC-009**: End-to-end chat test: a real question ("What courses do you offer?") returns an accurate answer with source citations
- **SC-010**: 100% of CRUD API endpoints return correct HTTP status codes and follow the standardized response format

### Assumptions

- Ollama with qwen2.5:7b model is installed and running on the host machine (not in Docker)
- Docker Desktop with WSL2 is available for PostgreSQL and Redis containers
- The existing ChromaDB with 4 collections and 24 documents is migrated from the previous project directory
- The frontend framework choice is Next.js with shadcn/ui component library (maximum production output with minimal custom CSS)
- The system runs on a single machine (no distributed deployment in Phase 1)
- Internet is not required after initial setup (all AI inference is local)
- The `corvit_data.json` file contains accurate, current institute data for vector DB seeding
