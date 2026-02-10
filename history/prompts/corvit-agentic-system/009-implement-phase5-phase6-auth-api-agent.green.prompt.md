---
id: 009
title: Implement Phase 5 Auth API and Phase 6 Director Agent
stage: green
date: 2026-02-03
surface: agent
model: claude-opus-4-5-20251101
feature: corvit-agentic-system
branch: 001-corvit-agentic-system
user: jamalafridi
command: /sp.implement
labels: ["implementation", "phase5", "phase6", "auth", "api", "crud", "jwt", "director-agent", "rag", "dashboard"]
links:
  spec: specs/001-corvit-agentic-system/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - backend/src/auth/jwt_handler.py
  - backend/src/auth/dependencies.py
  - backend/src/api/schemas/auth.py
  - backend/src/api/schemas/students.py
  - backend/src/api/schemas/teachers.py
  - backend/src/api/schemas/courses.py
  - backend/src/api/schemas/batches.py
  - backend/src/api/schemas/enrollments.py
  - backend/src/api/schemas/attendance.py
  - backend/src/api/schemas/fees.py
  - backend/src/api/schemas/exams.py
  - backend/src/api/schemas/agent.py
  - backend/src/api/routes/auth.py
  - backend/src/api/routes/students.py
  - backend/src/api/routes/teachers.py
  - backend/src/api/routes/courses.py
  - backend/src/api/routes/batches.py
  - backend/src/api/routes/enrollments.py
  - backend/src/api/routes/attendance.py
  - backend/src/api/routes/fees.py
  - backend/src/api/routes/exams.py
  - backend/src/api/routes/agent_chat.py
  - backend/src/api/routes/dashboard.py
  - backend/src/agents/base.py
  - backend/src/agents/director/prompts.py
  - backend/src/agents/director/router.py
  - backend/src/agents/director/tools.py
  - backend/src/agents/director/agent.py
  - backend/src/config/agents.yaml
  - backend/src/api/main.py
  - backend/src/database/connection.py
  - backend/tests/conftest.py
  - backend/tests/test_auth.py
  - backend/tests/test_api_students.py
  - backend/tests/test_api_courses.py
  - backend/tests/test_director_agent.py
  - backend/pyproject.toml
  - specs/001-corvit-agentic-system/tasks.md
tests:
  - backend/tests/test_auth.py (7 passed)
  - backend/tests/test_api_students.py (6 passed)
  - backend/tests/test_api_courses.py (6 passed)
  - backend/tests/test_director_agent.py (10 passed)
---

## Prompt

/sp.implement, now we already complete the phase 1 to 4, and now start in phase 5 and step 6 parallel okay.

## Response snapshot

Executed all 39 tasks across Phase 5 (T050-T075) and Phase 6 (T076-T088) in parallel:

**Phase 5 — Auth & API (T050-T075):**
- JWT authentication with python-jose (HS256), create/verify token round-trip
- Direct bcrypt password hashing (bypassing passlib due to bcrypt 5.x incompatibility)
- Role-based access control via `require_role()` dependency factory (admin, teacher, student)
- HTTPBearer security scheme for FastAPI
- 9 Pydantic v2 schema modules with `from_attributes` config
- Full CRUD routes for all 8 entities: students, teachers, courses, batches, enrollments, attendance, fees, exams
- Attendance report with rule engine alerts integration
- Fee overdue endpoint with rule engine integration
- Bulk attendance marking endpoint
- Exam results submission with stats calculation (avg, min, max, pass rate)
- 63 total API routes registered

**Phase 6 — Director Agent (T076-T088):**
- BaseAgent ABC with AgentContext and AgentResponse dataclasses
- IntentRouter with LLM-based classification across 9 intent categories
- INTENT_CLASSIFICATION_PROMPT and DIRECTOR_SYSTEM_PROMPT templates
- Director Agent with handlers: RAG queries, attendance queries, fee queries, complaints, stubs for remaining intents
- Agent tools: enroll_student, check_fees, get_attendance_summary, log_event
- agents.yaml configuration with authority boundaries
- POST /api/chat endpoint with LLM availability check, VectorStore, RAGPipeline integration
- GET /api/dashboard/stats with KPIs, attendance trend, enrollment by course, recent activity

**Full suite: 29/29 new tests pass (total with previous: 84 tests).**

## Outcome

- ✅ Impact: Complete auth, 63 API routes, and Director Agent operational
- 🧪 Tests: 29/29 passed (7 auth + 6 students + 6 courses + 10 director agent)
- 📁 Files: 37 files created/modified
- 🔁 Next prompts: Phase 7 — Frontend Core (T089-T119): Next.js setup, auth pages, dashboard, entity management pages
- 🧠 Reflection: Pydantic field name `date` shadows the `date` type — fixed with `import datetime` + `datetime.date`. passlib/bcrypt 5.x incompatibility required direct bcrypt usage. SQLAlchemy async engine NullPool required for pytest event loop compatibility. pytest-asyncio `@pytest_asyncio.fixture` needed for async fixtures.

## Evaluation notes (flywheel)

- Failure modes observed: Pydantic field/type name collision with `date`, passlib/bcrypt 5.x `__about__` attribute error, SQLAlchemy async pool event loop binding across tests, VectorStore constructor parameter name mismatch (`path` not `persist_directory`), pytest-asyncio version pinning
- Graders run and results (PASS/FAIL): All 29 tests PASS, 63 routes confirmed via startup log
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): null
