# Quickstart: Corvit Agentic System — Phase 1

**Branch**: `001-corvit-agentic-system` | **Date**: 2026-02-02

## Prerequisites

- Python 3.13.1 with uv 0.9.24+
- Node.js 20+ with npm/pnpm
- Docker Desktop with WSL2
- Ollama installed (`winget install Ollama.Ollama`)

## 1. Clone & Enter Project

```bash
cd /home/jamalafridi/AI-Project/CorvitRag
git checkout 001-corvit-agentic-system
```

## 2. Backend Setup

```bash
cd backend

# Initialize Python project
uv init --name corvit-agentic-system
uv python pin 3.13.1

# Install dependencies
uv add fastapi "uvicorn[standard]" "sqlalchemy[asyncio]" asyncpg \
  alembic pydantic pydantic-settings chromadb httpx \
  "python-jose[cryptography]" "passlib[bcrypt]" pyyaml redis jinja2
uv add --dev pytest pytest-asyncio pytest-httpx

# Copy environment file
cp .env.example .env

# Start Docker services (PostgreSQL + Redis)
docker compose up -d

# Wait for services to be healthy
docker compose ps

# Run database migrations
uv run alembic upgrade head

# Seed PostgreSQL with sample data
uv run python scripts/seed_database.py

# Seed Vector DB (if ChromaDB not already migrated)
uv run python scripts/seed_vectordb.py

# Start the API server
uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

**Verify**: Open `http://localhost:8000/api/health` — all 4 backends should be "up".
**API Docs**: Open `http://localhost:8000/docs` for interactive Swagger UI.

## 3. Pull Ollama Model

```bash
ollama pull qwen2.5:7b
# Verify
curl http://localhost:11434/api/tags
```

## 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install
# or: pnpm install

# Copy environment file
cp .env.local.example .env.local
# Set: NEXT_PUBLIC_API_URL=http://localhost:8000

# Start development server
npm run dev
```

**Verify**: Open `http://localhost:3000` — should redirect to login page.

## 5. Test Login

1. Open `http://localhost:3000/login`
2. Login with: `admin` / `admin123`
3. Should redirect to dashboard with KPI cards

## 6. Test Chat

1. Navigate to Chat page
2. Type: "What courses do you offer?"
3. Should receive a sourced answer from the Director Agent

## 7. Run Tests

```bash
# Backend tests
cd backend
uv run pytest tests/ -v

# Frontend tests (when available)
cd frontend
npm run test
```

## Environment Variables

### Backend (.env)

```env
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

### Frontend (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Common Issues

| Issue | Solution |
|-------|---------|
| Docker containers not starting | Run `docker compose down -v && docker compose up -d` |
| Ollama connection refused | Run `ollama serve` in a separate terminal |
| Database migration fails | Check DATABASE_URL in .env matches docker-compose.yml |
| Frontend CORS errors | Ensure backend CORS allows `http://localhost:3000` |
| ChromaDB import error | Verify chroma_db/ directory exists at CHROMA_DB_PATH |
