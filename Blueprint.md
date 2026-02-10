# Corvit Agentic System — Phase 1 Blueprint

## Spec-Driven Development | uv | Ollama | Zero Cost

**Date:** January 31, 2026
**Team:** Corvit Systems Peshawar — AI Division
**Status:** Ready for team review

---

## 1. What We're Building

Phase 1 = **Foundation + Director Agent**. A working system where a user can chat with the Director Agent, ask about courses, fees, teachers — and get accurate answers via RAG from the Vector DB, all powered by a **local Ollama model (zero cost)**.

### System at a Glance

```
User Message
    │
    ▼
FastAPI (POST /api/chat)
    │
    ▼
Director Agent
    │
    ├── Intent Classification (Ollama LLM)
    │
    ├── Rule Engine (zero tokens) ──► Attendance/Fee alerts
    │
    ├── RAG Pipeline ──► ChromaDB query → context → Ollama → answer
    │
    └── DB Actions ──► Enroll student, check fees, etc.
    │
    ▼
JSON Response (answer + sources + action taken)
```

---

## 2. Prerequisites

| Tool | Version | Status |
|------|---------|--------|
| uv | 0.9.24 | Installed |
| Python | 3.13.1 | Installed |
| Docker | 29.1.3 | Installed |
| Ollama | — | **NOT installed** (Step 0) |
| Vector DB (ChromaDB) | — | **COMPLETE** (migrate from old dir) |

### Existing Work (Completed)

The Vector DB is fully built in `C:\Users\AI-Project\Corvit_Agentic_System\vectordb\`:
- **4 collections:** courses (5 docs), teachers (4 docs), infrastructure (11 docs), policies (4 docs)
- **24 total documents** embedded and indexed
- **Data source:** `corvit_data.json` with real Corvit institute data
- **Files:** `store.py`, `embedder.py`, `seed_vectordb.py`

This will be migrated to the new project directory.

---

## 3. Tech Stack

| Component | Technology | Cost |
|-----------|-----------|------|
| Package Manager | **uv** (Astral) | Free |
| Backend API | **FastAPI** (async) | Free |
| Database | **PostgreSQL 16** (Docker) | Free |
| Cache/Queue | **Redis 7** (Docker) | Free |
| Vector DB | **ChromaDB** (local) | Free |
| LLM Provider | **Ollama + qwen2.5:7b** (local) | Free |
| ORM | **SQLAlchemy 2.0** (async + asyncpg) | Free |
| Migrations | **Alembic** | Free |
| Auth | **JWT** (python-jose + passlib) | Free |
| HTTP Client | **httpx** (for Ollama API calls) | Free |
| Templates | **Jinja2** (prompt templates) | Free |
| Testing | **pytest + pytest-asyncio** | Free |
| **Total** | | **$0** |

---

## 4. Step 0 — One-Time Setup

### 0a. Install Ollama + Pull Model

```powershell
winget install Ollama.Ollama
ollama pull qwen2.5:7b
```

**Model choice: qwen2.5:7b** (4.7GB download)
- Best quality/speed ratio for 8–16GB RAM
- Strong instruction-following for intent classification
- Runs on CPU (no GPU required), ~2–5 second responses
- Fallback option: `llama3.2:3b` (2GB) if RAM is tight

### 0b. Create New Project Directory

Team decides the path. Example:
```powershell
mkdir C:\Users\AI-Project\corvit-phase1
cd C:\Users\AI-Project\corvit-phase1
```

### 0c. Initialize uv Project

```powershell
uv init --name corvit-agentic-system
uv python pin 3.13.1
```

### 0d. Install All Dependencies

```powershell
uv add fastapi "uvicorn[standard]" "sqlalchemy[asyncio]" asyncpg alembic pydantic pydantic-settings chromadb httpx "python-jose[cryptography]" "passlib[bcrypt]" pyyaml redis jinja2
uv add --dev pytest pytest-asyncio pytest-httpx
```

### 0e. Start Docker Services

```powershell
docker compose up -d
```

### 0f. Migrate Vector DB

Copy from `C:\Users\AI-Project\Corvit_Agentic_System\`:

| Source | Destination | Changes |
|--------|------------|---------|
| `vectordb/store.py` | `src/vectordb/store.py` | Update path to use settings |
| `vectordb/embedder.py` | `src/vectordb/embedder.py` | Update import paths |
| `vectordb/data/corvit_data.json` | `src/vectordb/data/corvit_data.json` | No changes |
| `vectordb/chroma_db/` (entire dir) | `src/vectordb/chroma_db/` | No changes |
| `seed_vectordb.py` | `scripts/seed_vectordb.py` | Update imports |

### 0g. Initialize Alembic

```powershell
uv run alembic init migrations
```

---

## 5. Project Structure

```
{new-dir}/
│
├── pyproject.toml                      # uv project manifest
├── uv.lock                             # auto-generated lockfile
├── .python-version                     # pins 3.13.1
├── .env                                # local secrets (gitignored)
├── .env.example                        # template
├── .gitignore
├── docker-compose.yml                  # PostgreSQL + Redis
├── alembic.ini
│
├── specs/                              # YAML specs — written BEFORE code
│   ├── 00-project.yaml
│   ├── 01-config.yaml
│   ├── 02-database-models.yaml
│   ├── 03-database-connection.yaml
│   ├── 04-database-seed.yaml
│   ├── 05-vectordb.yaml
│   ├── 06-llm-provider.yaml
│   ├── 07-rag-pipeline.yaml
│   ├── 08-rule-engine.yaml
│   ├── 09-auth.yaml
│   ├── 10-api-core.yaml
│   ├── 11-api-students.yaml
│   ├── 12-api-teachers.yaml
│   ├── 13-api-courses.yaml
│   ├── 14-api-batches.yaml
│   ├── 15-api-enrollments.yaml
│   ├── 16-api-attendance.yaml
│   ├── 17-api-fees.yaml
│   ├── 18-api-exams.yaml
│   ├── 19-director-agent.yaml
│   └── 20-agent-chat-api.yaml
│
├── src/
│   ├── __init__.py
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py                 # Pydantic Settings (.env)
│   │   ├── rules.yaml                  # Attendance/fee rule definitions
│   │   └── agents.yaml                 # Agent definitions + authority
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py                   # 16 SQLAlchemy ORM models + User
│   │   ├── connection.py               # Async engine + session factory
│   │   └── seed.py                     # PostgreSQL seed data
│   │
│   ├── vectordb/                       # MIGRATED (already complete)
│   │   ├── __init__.py
│   │   ├── store.py                    # ChromaDB interface
│   │   ├── embedder.py                 # Document embedding pipeline
│   │   ├── data/
│   │   │   └── corvit_data.json        # Institute data
│   │   └── chroma_db/                  # Pre-built DB (4 collections)
│   │
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── base.py                     # Abstract LLMProvider interface
│   │   ├── ollama_provider.py          # Ollama via httpx
│   │   └── factory.py                  # Provider factory
│   │
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── pipeline.py                 # Query → Context → LLM → Answer
│   │   └── prompts.py                  # Jinja2 prompt templates
│   │
│   ├── rules/
│   │   ├── __init__.py
│   │   ├── engine.py                   # YAML rule loader + evaluator
│   │   ├── attendance_rules.py         # Threshold checks (zero tokens)
│   │   └── fee_rules.py               # Overdue checks (zero tokens)
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py                     # Abstract BaseAgent
│   │   └── director/
│   │       ├── __init__.py
│   │       ├── agent.py                # Director Agent implementation
│   │       ├── router.py               # Intent classification
│   │       ├── tools.py                # DB action functions
│   │       └── prompts.py              # System prompts
│   │
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── models.py                   # User model + roles enum
│   │   ├── jwt_handler.py              # Create/verify JWT
│   │   └── dependencies.py             # FastAPI auth deps
│   │
│   └── api/
│       ├── __init__.py
│       ├── main.py                     # FastAPI app factory
│       ├── deps.py                     # Shared dependencies
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
│       │   └── agent_chat.py           # POST /chat → Director Agent
│       └── schemas/
│           ├── __init__.py
│           ├── students.py
│           ├── teachers.py
│           ├── courses.py
│           ├── batches.py
│           ├── enrollments.py
│           ├── attendance.py
│           ├── fees.py
│           ├── exams.py
│           ├── auth.py
│           └── agent.py                # Chat request/response
│
├── migrations/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 001_initial_schema.py
│
├── scripts/
│   ├── seed_vectordb.py                # Migrated seeder
│   └── seed_database.py                # PostgreSQL seeder
│
└── tests/
    ├── __init__.py
    ├── conftest.py                     # Fixtures (test db, test client)
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
```

**Total: ~108 files** (21 specs, 67 source, 8 tests, 12 config/setup)

---

## 6. Spec-Driven Development Workflow

Every module follows this cycle:

```
1. Write YAML spec  →  2. Implement from spec  →  3. Test against spec
```

### Spec File Format

```yaml
module:
  name: "module_name"
  path: "src/module/file.py"
  purpose: "One-line description"

dependencies:
  internal: ["src/config/settings.py"]
  external: ["sqlalchemy", "pydantic"]

classes:
  - name: "ClassName"
    purpose: "What this class represents"
    attributes:
      - name: "attr_name"
        type: "str"
        description: "What it holds"
    methods:
      - name: "method_name"
        args: [{name: "arg1", type: "str"}]
        returns: "ReturnType"
        description: "What it does"

functions:
  - name: "function_name"
    args: [{name: "arg1", type: "str"}]
    returns: "ReturnType"
    description: "What it does"

contracts:
  inputs:
    - name: "InputName"
      fields: [{name: "field1", type: "str", required: true}]
  outputs:
    - name: "OutputName"
      fields: [{name: "field1", type: "str"}]

tests:
  - description: "Test that X does Y"
    given: "precondition"
    when: "action"
    then: "expected result"
```

---

## 7. Implementation Steps (14 Steps)

### Step 1: Config Module

| Item | Detail |
|------|--------|
| Spec | `specs/01-config.yaml` |
| Create | `src/config/settings.py` — Pydantic Settings from `.env` |
| Create | `.env`, `.env.example` |
| Test | `tests/test_config.py` |

**Key settings:**

```
DATABASE_URL=postgresql+asyncpg://corvit:corvit123@localhost:5432/corvit_db
REDIS_URL=redis://localhost:6379/0
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
LLM_PROVIDER=ollama
JWT_SECRET=corvit-dev-secret-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=480
CHROMA_DB_PATH=src/vectordb/chroma_db
DEBUG=true
```

---

### Step 2: Database Models

| Item | Detail |
|------|--------|
| Spec | `specs/02-database-models.yaml` |
| Create | `src/database/models.py` — 17 ORM models |
| Test | `tests/test_database_models.py` |

**Tables (17):**

| # | Table | Purpose |
|---|-------|---------|
| 1 | students | Student records |
| 2 | teachers | Teacher records |
| 3 | courses | Course catalog |
| 4 | batches | Course batches (course + teacher + room + schedule) |
| 5 | enrollments | Student-to-batch enrollment |
| 6 | attendance | Daily attendance records |
| 7 | fees | Fee records + payment tracking |
| 8 | exams | Scheduled exams |
| 9 | exam_results | Student exam scores |
| 10 | certifications | Vendor certifications |
| 11 | lab_bookings | Lab slot reservations |
| 12 | equipment | Lab equipment inventory |
| 13 | projects | Student projects |
| 14 | messages | Agent-to-agent messages |
| 15 | agent_memory | Agent state storage |
| 16 | event_log | System event audit trail |
| 17 | users | Auth users (admin/teacher/student) |

---

### Step 3: Database Connection + Migrations

| Item | Detail |
|------|--------|
| Spec | `specs/03-database-connection.yaml` |
| Create | `src/database/connection.py` — async engine, session factory, `get_db` dep |
| Create | `migrations/versions/001_initial_schema.py` |
| Run | `uv run alembic upgrade head` |

---

### Step 4: Vector DB Migration

| Item | Detail |
|------|--------|
| Spec | `specs/05-vectordb.yaml` |
| Action | Copy + update import paths from old project |
| Test | `tests/test_vectordb.py` — verify 4 collections, 24 docs, queries work |

---

### Step 5: LLM Provider (Ollama)

| Item | Detail |
|------|--------|
| Spec | `specs/06-llm-provider.yaml` |
| Create | `src/llm/base.py` — Abstract `LLMProvider` |
| Create | `src/llm/ollama_provider.py` — HTTP calls to Ollama |
| Create | `src/llm/factory.py` — Provider factory |
| Test | `tests/test_llm_provider.py` |

**LLM Provider Architecture (swap-ready):**

```
LLMProvider (abstract base)
    │
    ├── generate(messages, temperature, max_tokens) → LLMResponse
    └── is_available() → bool
         │
         ├── OllamaProvider    ← Phase 1 (free, local)
         │   POST http://localhost:11434/api/chat
         │
         └── ClaudeProvider    ← Future (just change .env)
             POST https://api.anthropic.com/v1/messages
```

**To swap to Claude later:** Change `LLM_PROVIDER=claude` in `.env`, add `ANTHROPIC_API_KEY`. Zero code changes needed in agents or RAG.

---

### Step 6: RAG Pipeline

| Item | Detail |
|------|--------|
| Spec | `specs/07-rag-pipeline.yaml` |
| Create | `src/rag/pipeline.py` — RAGPipeline class |
| Create | `src/rag/prompts.py` — Jinja2 templates |
| Test | `tests/test_rag_pipeline.py` |

**RAG Flow:**

```
User Question
    │
    ▼
Query ChromaDB (courses + teachers + policies + infrastructure)
    │
    ▼
Merge top-N results → Build context string
    │
    ▼
System Prompt + Context + User Question → Ollama
    │
    ▼
RAGResponse { answer, sources[], model }
```

---

### Step 7: Rule Engine (Zero Tokens)

| Item | Detail |
|------|--------|
| Spec | `specs/08-rule-engine.yaml` |
| Create | `src/config/rules.yaml` |
| Create | `src/rules/engine.py`, `attendance_rules.py`, `fee_rules.py` |
| Test | `tests/test_rule_engine.py` |

**Rules (pure Python, no LLM cost):**

| Trigger | Level | Action |
|---------|-------|--------|
| Attendance < 85% | Yellow | SMS warning to student |
| Attendance < 75% | Orange | SMS warning to student + mentor |
| Attendance < 60% | Red | Escalate to Director Agent |
| 3 consecutive absences | Red | Parent notification |
| Fee 7 days overdue | Yellow | SMS reminder to student |
| Fee 15 days overdue | Orange | SMS to student + parent |
| Fee 30 days overdue | Red | Escalate to Director Agent |

---

### Step 8: Auth System

| Item | Detail |
|------|--------|
| Spec | `specs/09-auth.yaml` |
| Create | `src/auth/jwt_handler.py`, `dependencies.py`, `models.py` |
| Test | `tests/test_auth.py` |

**Roles:** `admin`, `teacher`, `student`

---

### Step 9: API Core + Health

| Item | Detail |
|------|--------|
| Spec | `specs/10-api-core.yaml` |
| Create | `src/api/main.py`, `deps.py` |
| Endpoint | `GET /api/health` → checks postgres, redis, ollama, vectordb |

---

### Step 10: Auth API Route

| Item | Detail |
|------|--------|
| Create | `src/api/routes/auth.py` |
| Create | `src/api/schemas/auth.py` |
| Endpoints | `POST /register`, `POST /login`, `GET /me` |
| Test | `tests/test_api_auth.py` |

---

### Step 11: CRUD API Routes (8 Entities)

| Entity | Schema File | Route File | Extra Endpoints |
|--------|------------|------------|-----------------|
| students | `schemas/students.py` | `routes/students.py` | `GET /{id}/attendance`, `GET /{id}/fees` |
| teachers | `schemas/teachers.py` | `routes/teachers.py` | `GET /{id}/batches` |
| courses | `schemas/courses.py` | `routes/courses.py` | `GET /{id}/batches` |
| batches | `schemas/batches.py` | `routes/batches.py` | `GET /{id}/students`, `GET /{id}/schedule` |
| enrollments | `schemas/enrollments.py` | `routes/enrollments.py` | `POST /enroll` (convenience) |
| attendance | `schemas/attendance.py` | `routes/attendance.py` | `POST /mark` (bulk), `GET /report/{batch_id}` |
| fees | `schemas/fees.py` | `routes/fees.py` | `POST /{id}/pay`, `GET /overdue` |
| exams | `schemas/exams.py` | `routes/exams.py` | `POST /{id}/results`, `GET /{id}/results` |

**Every entity gets:** `POST /`, `GET /` (paginated), `GET /{id}`, `PUT /{id}`, `DELETE /{id}`

---

### Step 12: Seed Data

| Item | Detail |
|------|--------|
| Spec | `specs/04-database-seed.yaml` |
| Create | `src/database/seed.py` |
| Create | `scripts/seed_database.py` |

**Seed contents:**
- 5 courses (CCNA, CCNP, AI, Cyber Security, Cloud Computing)
- 4 teachers (Haleema Sayyar, Farooq Shahzad, Waseem Abbas, Adnan Khan)
- 5 batches (one per course)
- 20 sample students
- Enrollment records for all students
- 30 days of attendance data
- Fee records per course fee structure
- Lab equipment inventory
- 1 admin user (username: `admin`, password: `admin123`)

---

### Step 13: Director Agent

| Item | Detail |
|------|--------|
| Spec | `specs/19-director-agent.yaml` |
| Create | `src/agents/base.py`, `director/agent.py`, `router.py`, `tools.py`, `prompts.py` |
| Test | `tests/test_director_agent.py` |

**Intent Categories (9):**

| Intent | Handler | Uses LLM? |
|--------|---------|-----------|
| course_inquiry | RAG Pipeline | Yes |
| enrollment | DB Action + LLM | Yes |
| fee_query | RAG + DB | Yes |
| attendance_query | Rule Engine + DB | No |
| counseling | RAG Pipeline | Yes |
| complaint | LLM | Yes |
| general | RAG Pipeline | Yes |
| class_related | Route to Classes Agent (Phase 2) | No |
| lab_related | Route to Lab Agent (Phase 2) | No |

**Director Decision Authority:**

| Can Decide Alone | Needs Human Approval |
|-----------------|---------------------|
| Route queries to correct agent | Expel a student |
| Send attendance/fee warnings | Change fee structure |
| Recommend courses | Policy changes |
| Generate reports | Refund requests above threshold |

---

### Step 14: Agent Chat API + End-to-End

| Item | Detail |
|------|--------|
| Spec | `specs/20-agent-chat-api.yaml` |
| Create | `src/api/routes/agent_chat.py`, `src/api/schemas/agent.py` |
| Endpoint | `POST /api/chat` |

**Request:**
```json
{
  "message": "What courses do you offer?",
  "session_id": "optional-for-continuity"
}
```

**Response:**
```json
{
  "reply": "Corvit Systems offers 5 courses: CCNA (25,000 PKR)...",
  "intent": "course_inquiry",
  "action_taken": null,
  "data": null,
  "sources": [{"collection": "courses", "document": "..."}]
}
```

---

## 8. Docker Compose

```yaml
services:
  postgres:
    image: postgres:16-alpine
    container_name: corvit_postgres
    environment:
      POSTGRES_DB: corvit_db
      POSTGRES_USER: corvit
      POSTGRES_PASSWORD: corvit123
    ports:
      - "5432:5432"
    volumes:
      - corvit_pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U corvit -d corvit_db"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: corvit_redis
    ports:
      - "6379:6379"
    volumes:
      - corvit_redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  corvit_pgdata:
  corvit_redis_data:
```

**FastAPI + Ollama run natively on Windows** (not in Docker).

---

## 9. API Endpoints Summary

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/api/health` | System health check | None |
| `POST` | `/api/auth/register` | Register user | None |
| `POST` | `/api/auth/login` | Login, get JWT | None |
| `GET` | `/api/auth/me` | Current user info | Any |
| `POST` | `/api/chat` | Chat with Director Agent | Any |
| `CRUD` | `/api/students` | Student management | Admin |
| `CRUD` | `/api/teachers` | Teacher management | Admin |
| `CRUD` | `/api/courses` | Course catalog | Any/Admin |
| `CRUD` | `/api/batches` | Batch management | Admin |
| `CRUD` | `/api/enrollments` | Enrollment records | Admin |
| `CRUD` | `/api/attendance` | Attendance tracking | Admin/Teacher |
| `CRUD` | `/api/fees` | Fee management | Admin |
| `CRUD` | `/api/exams` | Exam management | Admin/Teacher |

---

## 10. Hardware Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| RAM | 8 GB | 16 GB |
| Storage | 15 GB free | 25 GB free |
| CPU | Any modern processor | Multi-core |
| OS | Windows with WSL2/Docker | Current setup works |
| Internet | Required for Ollama install | Not needed after setup |

---

## 11. Development Commands

```powershell
# Start infrastructure
docker compose up -d

# Run the API server (development)
uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Run migrations
uv run alembic upgrade head

# Seed Vector DB
uv run python scripts/seed_vectordb.py

# Seed PostgreSQL
uv run python scripts/seed_database.py

# Run tests
uv run pytest tests/ -v

# Check Ollama status
curl http://localhost:11434/api/tags
```

---

## 12. Success Criteria (Phase 1 Complete When)

| Metric | Target |
|--------|--------|
| Director Agent routes correctly | > 95% accuracy |
| Attendance alerts fire on time | 100% (rule-based) |
| Vector DB query relevance | > 90% relevant results |
| Agent response latency | < 5 seconds (local Ollama) |
| All CRUD endpoints working | 100% |
| Auth system functional | JWT + 3 roles |
| Health check passes | All 4 backends green |
| E2E chat test passes | Real questions get accurate answers |

---

## 13. Phase 2 Preview (Not in Scope)

After Phase 1 is complete and tested:

- **Classes & Attendance Agent** — timetable, batches, attendance, alerts
- **Lab & Project Agent** — lab booking, equipment, projects, practicals
- **Event Bus** — agent-to-agent communication
- **Notification System** — SMS/WhatsApp framework
- **Analytics** — enrollment, attendance, lab usage reports

---

## 14. Team Discussion Points

Before starting implementation, the team should decide:

1. **Project directory path** — Where to create the new project?
2. **Ollama model** — `qwen2.5:7b` (4.7GB, better quality) vs `llama3.2:3b` (2GB, faster)?
3. **Git strategy** — Initialize git repo? Branching strategy?
4. **Who implements what** — Split steps among team members?
5. **Testing strategy** — Run tests after each step or batch at the end?
6. **Data completeness** — Do we need more institute data beyond what's in `corvit_data.json`?

---

*Blueprint created: January 31, 2026*
*System: Corvit Systems Peshawar — 3-Agent Platinum FTE Agentic System*
*Phase: 1 of 2*
*Cost: $0*
