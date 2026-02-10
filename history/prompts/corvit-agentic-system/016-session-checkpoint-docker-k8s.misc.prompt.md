---
id: 016
title: Session Checkpoint Docker to K8s
stage: misc
date: 2026-02-04
surface: agent
model: claude-opus-4-5-20251101
feature: corvit-agentic-system
branch: 001-corvit-agentic-system
user: jamalafridi
command: checkpoint
labels: ["checkpoint", "docker", "kubernetes", "deployment"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .dockerignore
  - Dockerfile
  - docker/supervisord.conf
  - docker/entrypoint.sh
  - docker-compose.yml
  - frontend/next.config.ts
tests:
  - pending: docker compose up -d --build
---

## Prompt

Save session checkpoint — next session will push image to Docker Hub and deploy to Kubernetes.

## Response snapshot

### Session Checkpoint — Docker Image Ready, K8s Next

## What Was Done (This Session)

### Files Created
| File | Purpose |
|------|---------|
| `.dockerignore` | Excludes .git, .venv, node_modules, .next, __pycache__, specs, history, env files |
| `Dockerfile` | 3-stage multi-stage build: `node:22-alpine` → `python:3.13-slim` → `python:3.13-slim` final |
| `docker/supervisord.conf` | Runs uvicorn (port 8000) + Next.js standalone server (port 3000) |
| `docker/entrypoint.sh` | Alembic migrations → optional DB/VectorDB seeding → supervisord |
| `docker-compose.yml` | Orchestrates: app + postgres:16-alpine + redis:7-alpine, Ollama via host.docker.internal |

### Files Modified
| File | Change |
|------|--------|
| `frontend/next.config.ts` | Added `output: "standalone"` + rewrites for `/api/*`, `/docs`, `/openapi.json` → backend |

### Architecture Decisions
- **Single container** for frontend + backend (supervisord manages both)
- **python:3.13-slim** base (not Alpine — ChromaDB needs glibc)
- **Next.js standalone** output (~20MB vs ~725MB)
- **Next.js rewrites** proxy API calls — users only need port 3000
- **Ollama stays external** on host, accessed via `host.docker.internal:11434`
- **ChromaDB data** persists in named volume `chroma_data`
- **Estimated image size:** ~570MB

### Environment Variables (in docker-compose.yml)
```
DATABASE_URL=postgresql+asyncpg://corvit:corvit123@postgres:5432/corvit_db
REDIS_URL=redis://redis:6379/0
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=qwen2.5:7b
CHROMA_DB_PATH=/app/data/chroma_db
JWT_SECRET=corvit-dev-secret-change-in-production
```

## What's NOT Done Yet (Pending Verification)
- [ ] `docker compose up -d --build` — has not been run yet
- [ ] Image size verification (target < 600MB)
- [ ] End-to-end test (frontend loads, API proxied, login works)

---

## Next Session Plan

### Step 1: Build & Verify Locally
```bash
docker compose up -d --build
docker images  # check corvit_app size
# test http://localhost:3000 and http://localhost:3000/docs
```

### Step 2: Push to Docker Hub
```bash
docker login
docker tag corvit_app:latest <dockerhub-user>/corvit-app:latest
docker push <dockerhub-user>/corvit-app:latest
```

### Step 3: Kubernetes Deployment
Files to create:
- `k8s/namespace.yaml`
- `k8s/configmap.yaml` (env vars)
- `k8s/secret.yaml` (DB password, JWT secret)
- `k8s/postgres-deployment.yaml` + service + PVC
- `k8s/redis-deployment.yaml` + service
- `k8s/app-deployment.yaml` + service
- `k8s/ingress.yaml` (if needed)

Key K8s considerations:
- Ollama: will it run as a DaemonSet, sidecar, or external service?
- Resource limits: app container ~512Mi-768Mi RAM, 0.5 CPU
- PostgreSQL: use PVC for persistence
- ChromaDB: PVC or emptyDir with init container for seeding
- Secrets management: K8s secrets or external (Vault, etc.)

---

## Branch State
- Branch: `001-corvit-agentic-system`
- All changes are unstaged/untracked (no commit made)
- No PR created yet

## Outcome

- ✅ Impact: Checkpoint saved for session continuity
- 🧪 Tests: none
- 📁 Files: 1 checkpoint file
- 🔁 Next prompts: Build Docker image locally, push to Docker Hub, create K8s manifests
- 🧠 Reflection: Docker infra complete but untested — next session should verify build before pushing

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): Run docker compose build and validate
