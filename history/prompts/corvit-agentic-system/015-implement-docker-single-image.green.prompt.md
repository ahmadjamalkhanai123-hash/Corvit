---
id: 015
title: Implement Docker Single Image
stage: green
date: 2026-02-04
surface: agent
model: claude-opus-4-5-20251101
feature: corvit-agentic-system
branch: 001-corvit-agentic-system
user: jamalafridi
command: implement
labels: ["docker", "deployment", "infrastructure", "multi-stage-build"]
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
  - docker compose up -d --build (manual verification)
---

## Prompt

Implement the following plan:

# Plan: Optimized Single Docker Image for CorvitRag

## Goal
Create one combined Docker image (frontend + backend) that is as small as possible for a low-spec system (~8GB RAM). Ollama stays external on the host.

## Strategy
- **Multi-stage build** (3 stages) to discard build tools and dependencies
- **Next.js standalone output** reduces frontend from ~725MB to ~20MB
- **Next.js rewrites** proxy `/api/*` to backend — users only need port 3000
- **supervisord** manages both processes in one container
- **python:3.13-slim** base (not Alpine — ChromaDB needs glibc)

## Response snapshot

Created 5 new files and modified 1 existing file to implement a combined Docker image for the CorvitRag application:

- `.dockerignore` — excludes build artifacts, specs, env files
- `Dockerfile` — 3-stage multi-stage build (node:22-alpine → python:3.13-slim → python:3.13-slim final)
- `docker/supervisord.conf` — manages uvicorn + Next.js server processes
- `docker/entrypoint.sh` — runs Alembic migrations, optional seeding, starts supervisord
- `docker-compose.yml` — orchestrates app + postgres:16-alpine + redis:7-alpine
- `frontend/next.config.ts` — added `output: "standalone"` and API rewrites

Ollama stays external on the host via `host.docker.internal:11434`. ChromaDB data persists in a named volume.

## Outcome

- ✅ Impact: Complete Docker deployment setup for single-image frontend+backend
- 🧪 Tests: Manual — docker compose up -d --build
- 📁 Files: 5 created, 1 modified
- 🔁 Next prompts: Build and test the image, verify image size < 600MB, test end-to-end flows
- 🧠 Reflection: Used python:3.13-slim over Alpine due to ChromaDB glibc requirement. Next.js standalone reduces frontend footprint significantly.

## Evaluation notes (flywheel)

- Failure modes observed: none yet — needs build verification
- Graders run and results (PASS/FAIL): pending manual build test
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): Build image and verify size/functionality
