"""
LESSON 11: Production Project Structure
=======================================

Learn how to structure a large FastAPI project with
multiple layers, routers, and proper separation.

This lesson explains the structure - see src/app/ for implementation.

Project Structure:
-----------------

src/
└── app/
    ├── main.py              # Application entry point
    ├── core/                # Core configuration
    │   ├── config.py        # Settings and environment
    │   ├── security.py      # Auth utilities
    │   └── exceptions.py    # Custom exceptions
    │
    ├── api/                 # API layer
    │   └── v1/              # API version 1
    │       ├── router.py    # Main router
    │       └── endpoints/   # Endpoint modules
    │           ├── users.py
    │           ├── items.py
    │           └── auth.py
    │
    ├── models/              # Database models (SQLAlchemy)
    │   ├── base.py
    │   ├── user.py
    │   └── item.py
    │
    ├── schemas/             # Pydantic schemas
    │   ├── user.py
    │   └── item.py
    │
    ├── services/            # Business logic layer
    │   ├── user_service.py
    │   └── item_service.py
    │
    ├── db/                  # Database configuration
    │   ├── session.py       # Session management
    │   └── base.py          # Import all models
    │
    ├── middleware/          # Custom middleware
    │   └── logging.py
    │
    └── utils/               # Utility functions
        └── helpers.py

"""

# This is a documentation file - run the actual app with:
# uv run uvicorn src.app.main:app --reload

print("""
==============================================
PRODUCTION PROJECT STRUCTURE
==============================================

Key Principles:
--------------
1. SEPARATION OF CONCERNS
   - API layer: handles HTTP (routes, validation)
   - Service layer: contains business logic
   - Data layer: database operations

2. SINGLE RESPONSIBILITY
   - Each file/class has one purpose
   - Easy to test in isolation

3. DEPENDENCY INJECTION
   - Services injected into endpoints
   - Database sessions as dependencies
   - Easy to mock for testing

4. VERSIONED APIs
   - /api/v1/, /api/v2/
   - Breaking changes in new version
   - Old versions can be deprecated

5. CONFIGURATION MANAGEMENT
   - Environment-based settings
   - No hardcoded secrets
   - Different configs for dev/prod


Layer Responsibilities:
----------------------

API LAYER (endpoints):
- Parse request data
- Validate input (Pydantic)
- Call appropriate service
- Format response
- Handle HTTP concerns

SERVICE LAYER:
- Implement business logic
- Coordinate between repos
- Validate business rules
- Not aware of HTTP

DATA LAYER (models/repos):
- Database operations
- Data persistence
- Query building
- Not aware of business rules


Example Flow:
------------

POST /api/v1/users
        │
        ▼
┌─────────────────┐
│  API Endpoint   │  ← Validates request body
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  UserService    │  ← Hashes password, applies business rules
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  UserModel/DB   │  ← Stores in database
└─────────────────┘

Run the production app:
    uv run uvicorn src.app.main:app --reload
""")
