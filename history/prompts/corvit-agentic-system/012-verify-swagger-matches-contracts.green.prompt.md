---
id: 012
title: Verify Swagger matches contracts
stage: green
date: 2026-02-04
surface: agent
model: claude-opus-4-5-20251101
feature: corvit-agentic-system
branch: 001-corvit-agentic-system
user: jamalafridi
command: verify swagger vs contracts
labels: ["swagger", "openapi", "contracts", "verification"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
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
tests:
  - none (read-only verification)
---

## Prompt

Verify that the Swagger/OpenAPI endpoints at http://localhost:8000 match the contract files in /home/jamalafridi/AI-Project/CorvitRag/specs/001-corvit-agentic-system/contracts/.

Steps:
1. Fetch the OpenAPI spec from http://localhost:8000/openapi.json using curl
2. List all contract files in the contracts directory
3. Read each contract file
4. Compare the endpoints defined in each contract against what exists in the OpenAPI spec

For each contract, check:
- All endpoints exist in Swagger
- HTTP methods match
- Path parameters match

Report which contracts are fully covered and any gaps. Do NOT make any changes -- just report findings.

## Response snapshot

All 12 contract files (health, auth, students, teachers, courses, batches, enrollments, attendance, fees, exams, chat, dashboard) were compared against the live OpenAPI spec at localhost:8000/openapi.json. All 59 endpoints across all contracts are present in Swagger with correct HTTP methods and path structures. One cosmetic difference noted: contracts use generic {id} while Swagger uses descriptive names ({student_id}, {teacher_id}, etc.) -- no functional impact.

## Outcome

- Impact: Confirmed 100% endpoint coverage between contracts and live API
- Tests: none (read-only verification)
- Files: 12 contract files read, 0 modified
- Next prompts: End-to-end smoke test, quickstart.md verification
- Reflection: Full alignment between spec contracts and implementation is a strong indicator of spec-driven discipline

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): PASS -- all 59/59 endpoints match
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): Could add automated contract-vs-openapi comparison script
