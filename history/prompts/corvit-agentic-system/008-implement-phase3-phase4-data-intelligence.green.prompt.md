---
id: 008
title: Implement Phase 3 Data Layer and Phase 4 Intelligence
stage: green
date: 2026-02-03
surface: agent
model: claude-opus-4-5-20251101
feature: corvit-agentic-system
branch: 001-corvit-agentic-system
user: jamalafridi
command: /sp.implement
labels: ["implementation", "phase3", "phase4", "data-layer", "intelligence", "rag", "rules"]
links:
  spec: specs/001-corvit-agentic-system/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - backend/src/database/models.py
  - backend/src/database/seed.py
  - backend/scripts/seed_database.py
  - backend/scripts/seed_vectordb.py
  - backend/migrations/env.py
  - backend/migrations/versions/98ef6195904c_initial_schema.py
  - backend/src/vectordb/store.py
  - backend/src/vectordb/embedder.py
  - backend/src/vectordb/data/corvit_data.json
  - backend/src/llm/base.py
  - backend/src/llm/ollama_provider.py
  - backend/src/llm/factory.py
  - backend/src/rag/prompts.py
  - backend/src/rag/pipeline.py
  - backend/src/config/rules.yaml
  - backend/src/rules/engine.py
  - backend/src/rules/attendance_rules.py
  - backend/src/rules/fee_rules.py
  - backend/tests/test_database_models.py
  - backend/tests/test_vectordb.py
  - backend/tests/test_llm_provider.py
  - backend/tests/test_rag_pipeline.py
  - backend/tests/test_rule_engine.py
tests:
  - backend/tests/test_database_models.py (17 passed)
  - backend/tests/test_vectordb.py (5 passed)
  - backend/tests/test_llm_provider.py (6 passed)
  - backend/tests/test_rag_pipeline.py (5 passed)
  - backend/tests/test_rule_engine.py (22 passed)
---

## Prompt

/sp.implement, now start and complete phase 3 and 4.

## Response snapshot

Executed all 26 tasks across Phase 3 (T024-T031) and Phase 4 (T032-T049):

**Phase 3 — Data Layer:**
- Defined all 17 SQLAlchemy ORM models with full relationships, indexes, unique constraints, and enum types
- Generated and applied Alembic migration (async engine). Fixed env.py to import models for autogenerate detection
- Created seed script populating: 5 users, 20 students, 4 teachers, 5 courses, 5 batches, 20 enrollments, 420 attendance records, 20 fees, 5 exams, 20 exam results, 5 equipment
- 17 model tests passing

**Phase 4 — Intelligence:**
- ChromaDB VectorStore with query_collection and query_all_collections
- Document embedder using ChromaDB default embeddings (all-MiniLM-L6-v2)
- Created corvit_data.json with 20 documents across 4 collections (courses, teachers, infrastructure, policies)
- Abstract LLMProvider + OllamaProvider + factory pattern
- Jinja2 RAG prompt templates with context injection
- RAGPipeline: query → vector search → context build → LLM → answer+sources
- RuleEngine loading rules.yaml with attendance thresholds (85/75/60/3-consecutive) and fee thresholds (7/15/30 days)
- Attendance and fee evaluation functions querying real DB data
- 38 intelligence tests passing

**Full suite: 55/55 tests pass.**

## Outcome

- ✅ Impact: Complete data layer (17 tables, seeded) and intelligence layer (RAG + rules) operational
- 🧪 Tests: 55/55 passed (17 models + 5 vectordb + 6 llm + 5 rag + 22 rules)
- 📁 Files: 23 files created/modified
- 🔁 Next prompts: Phase 5 — Auth & API (T050-T075): JWT auth, role-based access, CRUD endpoints for all 8 entities
- 🧠 Reflection: SQLAlchemy reserved attribute 'metadata' on Message model required renaming to 'extra_data'. passlib+bcrypt incompatibility on Python 3.13 fixed by using bcrypt directly. Alembic env.py needed explicit model import for autogenerate.

## Evaluation notes (flywheel)

- Failure modes observed: passlib/bcrypt Python 3.13 incompatibility, SQLAlchemy 'metadata' reserved attribute, Alembic empty migration due to missing model import, test fixture async session transaction cleanup
- Graders run and results (PASS/FAIL): All 55 tests PASS, seed data verified in PostgreSQL, ChromaDB 4 collections with 20 docs confirmed
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): null
