---
id: 013
title: E2E Smoke Test Backend
stage: green
date: 2026-02-04
surface: agent
model: claude-opus-4-5-20251101
feature: corvit-agentic-system
branch: 001-corvit-agentic-system
user: jamalafridi
command: smoke-test
labels: ["e2e", "smoke-test", "backend", "api"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - (no files modified — read-only test)
tests:
  - "POST /api/auth/register -> 201 PASS"
  - "POST /api/auth/login -> 200 PASS"
  - "GET /api/dashboard/stats -> 200 PASS"
  - "POST /api/chat -> 503 FAIL (Ollama down)"
  - "POST /api/students -> 201 PASS"
  - "GET /api/students -> 200 PASS"
  - "GET /api/students/<id> -> 200 PASS"
  - "PUT /api/students/<id> -> 200 PASS"
  - "DELETE /api/students/<id> -> 204 PASS"
  - "GET /api/health -> 503 FAIL (degraded, Ollama down)"
---

## Prompt

Run an end-to-end smoke test against the running backend at http://localhost:8000. Use curl commands to test the following flow. Do NOT make any code changes — just test and report results.

1. **Register**: POST http://localhost:8000/api/auth/register with body {"username":"smoketest_user","email":"smoke@test.com","password":"Test1234!","role":"admin"}
2. **Login**: POST http://localhost:8000/api/auth/login with body {"username":"smoketest_user","password":"Test1234!"} — capture the JWT token from response
3. **Dashboard**: GET http://localhost:8000/api/dashboard/stats with Authorization: Bearer <token>
4. **Chat**: POST http://localhost:8000/api/chat with Authorization: Bearer <token> and body {"message":"What courses do you offer?"}
5. **Students CRUD**:
   - POST http://localhost:8000/api/students with body {"name":"Smoke Test","email":"smokestu@test.com","phone":"03001111111"}
   - GET http://localhost:8000/api/students (list)
   - GET http://localhost:8000/api/students/<id> (get created student)
   - PUT http://localhost:8000/api/students/<id> with body {"name":"Smoke Updated"}
   - DELETE http://localhost:8000/api/students/<id>
6. **Health**: GET http://localhost:8000/api/health

For each step, report: HTTP status code, whether it succeeded or failed, and a brief summary of the response. Use the JWT token from login for all authenticated requests.

Report a summary table at the end: step name, status code, pass/fail.

## Response snapshot

8/10 endpoints PASS, 2/10 FAIL. Both failures caused by Ollama being down: chat returns 503 and health reports degraded status. All other services (Postgres, Redis, ChromaDB, auth, CRUD, dashboard) fully operational. Full CRUD lifecycle for students verified (create, list, get, update, delete).

## Outcome

- Impact: Validated backend API readiness; 8/10 endpoints green, 2 blocked by Ollama service
- Tests: 10 HTTP endpoint tests executed; 8 PASS, 2 FAIL
- Files: No files modified (read-only smoke test)
- Next prompts: Start Ollama and re-test chat endpoint; verify frontend integration
- Reflection: Backend is production-ready for all non-LLM features; Ollama dependency is the single blocker

## Evaluation notes (flywheel)

- Failure modes observed: Ollama service not running causes chat 503 and health degraded
- Graders run and results (PASS/FAIL): 8 PASS / 2 FAIL
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): Start Ollama and re-run chat + health tests
