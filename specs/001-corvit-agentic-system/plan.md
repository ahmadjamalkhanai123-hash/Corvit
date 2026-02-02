# Implementation Plan: Corvit Agentic System — Phase 1

**Branch**: `001-corvit-agentic-system` | **Date**: 2026-02-02 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-corvit-agentic-system/spec.md`

## Summary

Build the Corvit Agentic System Phase 1: a full-stack institute management platform with an AI-powered Director Agent. The backend is a FastAPI async API with 17 PostgreSQL tables, JWT auth, 50+ REST endpoints, a RAG pipeline (ChromaDB + Ollama qwen2.5:7b), and a rule engine for attendance/fee alerts. The frontend is a Next.js 14 app with shadcn/ui providing 12 production pages including a real-time chat interface. The system is divided into 7 implementation chunks, each independently deliverable and context-window optimized.

## Technical Context

**Language/Version**: Python 3.13.1 (backend), TypeScript 5.x (frontend)
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 (async), Next.js 14, shadcn/ui, Tailwind CSS 3
**Storage**: PostgreSQL 16 (Docker), Redis 7 (Docker), ChromaDB (local), Ollama (local)
**Testing**: pytest + pytest-asyncio (backend), Vitest + Playwright (frontend)
**Target Platform**: WSL2/Linux server (development), any modern browser (frontend)
**Project Type**: Web application (backend + frontend)
**Performance Goals**: <5s agent response, <3s page load, <1.5s FCP, 50+ concurrent users
**Constraints**: $0 cost (all local), 8GB RAM minimum, CPU-only LLM inference
**Scale/Scope**: Single institute, ~100 students, 12 frontend pages, 50+ API endpoints

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Status | Evidence |
|---|-----------|--------|----------|
| I | Spec-Driven Development | PASS | All 21 YAML specs defined in Blueprint; spec.md written before plan |
| II | Zero-Cost Local-First | PASS | Ollama (local), PostgreSQL/Redis (Docker), ChromaDB (local) — $0 total |
| III | Test-First Quality Gate | PASS | TDD cycle enforced per chunk; pytest for backend, Vitest/Playwright for frontend |
| IV | Production-Grade Frontend | PASS | 12 pages defined; shadcn/ui provides all required components; responsive + accessible |
| V | API-First Contract Design | PASS | All endpoints defined in contracts/ before implementation; FastAPI auto-generates OpenAPI |
| VI | Security by Default | PASS | JWT + bcrypt + RBAC; .env for secrets; SQLAlchemy ORM prevents injection; bounded agent authority |

**Gate result: ALL PASS — proceed to Phase 0.**

## Project Structure

### Documentation (this feature)

```text
specs/001-corvit-agentic-system/
├── plan.md              # This file
├── research.md          # Phase 0: technology decisions
├── data-model.md        # Phase 1: all 17 entities with fields/relationships
├── quickstart.md        # Phase 1: developer setup guide
├── contracts/           # Phase 1: API endpoint contracts
│   ├── health.md
│   ├── auth.md
│   ├── students.md
│   ├── teachers.md
│   ├── courses.md
│   ├── batches.md
│   ├── enrollments.md
│   ├── attendance.md
│   ├── fees.md
│   ├── exams.md
│   ├── chat.md
│   └── dashboard.md
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2: /sp.tasks output (NOT created by /sp.plan)
```

### Source Code (repository root)

```text
backend/
├── pyproject.toml
├── uv.lock
├── .python-version
├── .env
├── .env.example
├── docker-compose.yml
├── alembic.ini
├── specs/                          # 21 YAML spec files
│   ├── 00-project.yaml
│   ├── 01-config.yaml
│   ├── 02-database-models.yaml
│   ├── ...
│   └── 20-agent-chat-api.yaml
├── src/
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py             # Pydantic Settings
│   │   ├── rules.yaml              # Rule engine thresholds
│   │   └── agents.yaml             # Agent definitions
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py               # 17 SQLAlchemy ORM models
│   │   ├── connection.py           # Async engine + session factory
│   │   └── seed.py                 # Seed data loader
│   ├── vectordb/
│   │   ├── __init__.py
│   │   ├── store.py                # ChromaDB interface
│   │   ├── embedder.py             # Document embedding
│   │   ├── data/
│   │   │   └── corvit_data.json
│   │   └── chroma_db/              # Pre-built vector DB
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── base.py                 # Abstract LLMProvider
│   │   ├── ollama_provider.py      # Ollama HTTP client
│   │   └── factory.py              # Provider factory
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── pipeline.py             # RAG orchestrator
│   │   └── prompts.py              # Jinja2 prompt templates
│   ├── rules/
│   │   ├── __init__.py
│   │   ├── engine.py               # YAML rule loader
│   │   ├── attendance_rules.py     # Attendance thresholds
│   │   └── fee_rules.py            # Fee overdue thresholds
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py                 # Abstract BaseAgent
│   │   └── director/
│   │       ├── __init__.py
│   │       ├── agent.py            # Director Agent
│   │       ├── router.py           # Intent classification
│   │       ├── tools.py            # DB action functions
│   │       └── prompts.py          # System prompts
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── jwt_handler.py          # JWT create/verify
│   │   └── dependencies.py         # FastAPI auth deps
│   └── api/
│       ├── __init__.py
│       ├── main.py                 # FastAPI app factory
│       ├── deps.py                 # Shared dependencies
│       ├── routes/
│       │   ├── __init__.py
│       │   ├── auth.py
│       │   ├── students.py
│       │   ├── teachers.py
│       │   ├── courses.py
│       │   ├── batches.py
│       │   ├── enrollments.py
│       │   ├── attendance.py
│       │   ├── fees.py
│       │   ├── exams.py
│       │   └── agent_chat.py
│       └── schemas/
│           ├── __init__.py
│           ├── common.py           # Shared pagination/error schemas
│           ├── students.py
│           ├── teachers.py
│           ├── courses.py
│           ├── batches.py
│           ├── enrollments.py
│           ├── attendance.py
│           ├── fees.py
│           ├── exams.py
│           ├── auth.py
│           └── agent.py
├── migrations/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 001_initial_schema.py
├── scripts/
│   ├── seed_vectordb.py
│   └── seed_database.py
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_config.py
    ├── test_database_models.py
    ├── test_vectordb.py
    ├── test_llm_provider.py
    ├── test_rag_pipeline.py
    ├── test_rule_engine.py
    ├── test_auth.py
    ├── test_api_students.py
    ├── test_api_courses.py
    └── test_director_agent.py

frontend/
├── package.json
├── next.config.ts
├── tailwind.config.ts
├── tsconfig.json
├── components.json                  # shadcn/ui config
├── .env.local
├── public/
│   ├── logo.svg
│   └── favicon.ico
├── src/
│   ├── app/
│   │   ├── layout.tsx               # Root layout (Inter font, providers)
│   │   ├── page.tsx                 # Redirect to /dashboard or /auth
│   │   ├── (auth)/
│   │   │   ├── login/page.tsx
│   │   │   └── register/page.tsx
│   │   └── (dashboard)/
│   │       ├── layout.tsx           # Sidebar + Navbar shell
│   │       ├── dashboard/page.tsx
│   │       ├── chat/page.tsx
│   │       ├── students/page.tsx
│   │       ├── teachers/page.tsx
│   │       ├── courses/page.tsx
│   │       ├── batches/page.tsx
│   │       ├── enrollments/page.tsx
│   │       ├── attendance/page.tsx
│   │       ├── fees/page.tsx
│   │       ├── exams/page.tsx
│   │       └── settings/page.tsx
│   ├── components/
│   │   ├── ui/                      # shadcn/ui primitives (auto-generated)
│   │   │   ├── button.tsx
│   │   │   ├── input.tsx
│   │   │   ├── card.tsx
│   │   │   ├── dialog.tsx
│   │   │   ├── table.tsx
│   │   │   ├── badge.tsx
│   │   │   ├── toast.tsx
│   │   │   ├── skeleton.tsx
│   │   │   ├── avatar.tsx
│   │   │   ├── select.tsx
│   │   │   ├── dropdown-menu.tsx
│   │   │   ├── sheet.tsx
│   │   │   ├── breadcrumb.tsx
│   │   │   └── ...
│   │   ├── layout/
│   │   │   ├── sidebar.tsx
│   │   │   ├── navbar.tsx
│   │   │   └── page-header.tsx
│   │   ├── data-table/
│   │   │   ├── data-table.tsx       # Generic DataTable with TanStack Table
│   │   │   ├── columns.tsx
│   │   │   ├── toolbar.tsx
│   │   │   ├── pagination.tsx
│   │   │   └── faceted-filter.tsx
│   │   ├── charts/
│   │   │   ├── kpi-card.tsx
│   │   │   ├── line-chart.tsx
│   │   │   └── bar-chart.tsx
│   │   ├── chat/
│   │   │   ├── chat-thread.tsx
│   │   │   ├── message-bubble.tsx
│   │   │   ├── typing-indicator.tsx
│   │   │   ├── source-citation.tsx
│   │   │   └── intent-badge.tsx
│   │   └── shared/
│   │       ├── empty-state.tsx
│   │       ├── confirm-dialog.tsx
│   │       ├── loading-spinner.tsx
│   │       └── error-boundary.tsx
│   ├── lib/
│   │   ├── api-client.ts            # Axios/fetch wrapper with JWT
│   │   ├── auth.ts                  # Token management
│   │   ├── utils.ts                 # cn() helper, formatters
│   │   └── constants.ts
│   ├── hooks/
│   │   ├── use-auth.ts
│   │   ├── use-api.ts               # Generic CRUD hook
│   │   ├── use-websocket.ts
│   │   └── use-debounce.ts
│   └── types/
│       ├── api.ts                   # API response types
│       ├── entities.ts              # Student, Teacher, Course, etc.
│       └── auth.ts
└── tests/
    ├── e2e/
    │   ├── auth.spec.ts
    │   ├── dashboard.spec.ts
    │   └── chat.spec.ts
    └── components/
        ├── data-table.test.tsx
        └── chat-thread.test.tsx
```

**Structure Decision**: Web application structure selected — `backend/` (FastAPI + Python) and `frontend/` (Next.js + TypeScript) as separate projects at repository root. This separation enables independent deployment, testing, and development while sharing a common API contract.

## Chunk Implementation Map

### Chunk 1: Foundation
**Files**: backend/pyproject.toml, docker-compose.yml, .env, .env.example, src/config/settings.py, src/database/connection.py, src/api/main.py, src/api/deps.py, src/api/routes/__init__.py, tests/conftest.py, tests/test_config.py
**Deliverable**: `GET /api/health` returns all-green; FastAPI running on port 8000

### Chunk 2: Data Layer
**Files**: src/database/models.py (17 models), migrations/versions/001_initial_schema.py, src/database/seed.py, scripts/seed_database.py, tests/test_database_models.py
**Deliverable**: All 17 tables created, seed data loaded, model tests pass

### Chunk 3: Intelligence
**Files**: src/vectordb/*, src/llm/base.py, src/llm/ollama_provider.py, src/llm/factory.py, src/rag/pipeline.py, src/rag/prompts.py, src/config/rules.yaml, src/rules/engine.py, src/rules/attendance_rules.py, src/rules/fee_rules.py, scripts/seed_vectordb.py, tests/test_vectordb.py, tests/test_llm_provider.py, tests/test_rag_pipeline.py, tests/test_rule_engine.py
**Deliverable**: RAG returns sourced answers; rule engine fires correct alerts

### Chunk 4: Auth & API
**Files**: src/auth/*, src/api/schemas/* (11 files), src/api/routes/* (9 route files), tests/test_auth.py, tests/test_api_students.py, tests/test_api_courses.py
**Deliverable**: 50+ endpoints live at `/docs` with JWT protection

### Chunk 5: Director Agent
**Files**: src/agents/base.py, src/agents/director/* (4 files), src/config/agents.yaml, src/api/routes/agent_chat.py, src/api/schemas/agent.py, tests/test_director_agent.py
**Deliverable**: POST /api/chat returns intent-classified, sourced responses

### Chunk 6: Frontend Core
**Files**: frontend/ scaffold (package.json, next.config.ts, tailwind.config.ts), components/ui/* (shadcn), components/layout/*, src/app/layout.tsx, src/app/(auth)/*, src/app/(dashboard)/layout.tsx, src/app/(dashboard)/dashboard/page.tsx, src/lib/*, src/hooks/*
**Deliverable**: Running frontend at localhost:3000 with login, dashboard, sidebar

### Chunk 7: Frontend Pages
**Files**: All remaining page.tsx files (chat, students, teachers, courses, batches, enrollments, attendance, fees, exams, settings), components/data-table/*, components/chat/*, components/charts/*, components/shared/*
**Deliverable**: All 12 pages functional, connected to live API

## Complexity Tracking

> No constitution violations detected. All design decisions align with the 6 principles.
