---
id: 003
title: Implementation Plan All Chunks
stage: plan
date: 2026-02-02
surface: agent
model: claude-opus-4-5-20251101
feature: corvit-agentic-system
branch: 001-corvit-agentic-system
user: jamalafridi
command: /sp.plan
labels: [plan, architecture, contracts, data-model, research]
links:
  spec: specs/001-corvit-agentic-system/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/001-corvit-agentic-system/plan.md
  - specs/001-corvit-agentic-system/research.md
  - specs/001-corvit-agentic-system/data-model.md
  - specs/001-corvit-agentic-system/quickstart.md
  - specs/001-corvit-agentic-system/contracts/health.md
  - specs/001-corvit-agentic-system/contracts/auth.md
  - specs/001-corvit-agentic-system/contracts/students.md
  - specs/001-corvit-agentic-system/contracts/teachers.md
  - specs/001-corvit-agentic-system/contracts/courses.md
  - specs/001-corvit-agentic-system/contracts/batches.md
  - specs/001-corvit-agentic-system/contracts/enrollments.md
  - specs/001-corvit-agentic-system/contracts/attendance.md
  - specs/001-corvit-agentic-system/contracts/fees.md
  - specs/001-corvit-agentic-system/contracts/exams.md
  - specs/001-corvit-agentic-system/contracts/chat.md
  - specs/001-corvit-agentic-system/contracts/dashboard.md
  - CLAUDE.md
tests:
---

## Prompt

/sp.plan, Now continue your process

## Response snapshot

Generated complete implementation plan for Corvit Agentic System Phase 1:

**Phase 0 — Research** (research.md): 10 technology decisions documented with rationale and alternatives:
1. Next.js 14 (App Router) for frontend
2. shadcn/ui + Tailwind CSS for component library
3. TanStack Table for data tables
4. Recharts for dashboard charts
5. SSE for real-time chat streaming
6. SWR for client-side state management
7. Native fetch wrapper for API client
8. Monorepo (backend/ + frontend/) structure
9. Abstract LLMProvider with factory pattern
10. JWT in httpOnly cookie for auth

**Phase 1 — Design** (5 artifacts):
- data-model.md: 17 entities with fields, types, constraints, relationships, indexes, state transitions, and rule engine triggers
- contracts/: 12 API contract files covering all 50+ endpoints with request/response schemas
- quickstart.md: Developer setup guide from clone to running system
- CLAUDE.md: Updated agent context with tech stack

**Constitution Check**: ALL 6 PRINCIPLES PASS (pre-design and post-design).

## Outcome

- Impact: Complete technical blueprint ready for task generation
- Tests: N/A (planning document)
- Files: 18 files created/updated
- Next prompts: /sp.tasks to generate actionable implementation tasks
- Reflection: Web app structure (backend/ + frontend/) selected for independent deployment. shadcn/ui maximizes production output with minimal custom work per user request.

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): Constitution check — all 6 principles PASS
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
