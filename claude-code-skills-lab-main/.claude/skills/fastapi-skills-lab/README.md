# FastAPI Skills Lab

A comprehensive FastAPI skill for Claude Code - from beginner to production-ready applications.

## Skill Structure (Pure Skill - No Environment)

```
fastapi-skills-lab/
├── lessons/                    # Learning modules (17 lessons)
│   ├── 01_beginner/           # Basics: routes, params, Pydantic
│   ├── 02_intermediate/       # Database, auth, middleware, security
│   └── 03_advanced/           # Architecture, OAuth, RBAC, Graph/Vector DBs
│
├── src/app/                   # Production templates
│   ├── main.py               # Application entry point
│   ├── core/                 # Config, security, dependencies
│   ├── api/v1/               # API endpoints
│   ├── models/               # SQLAlchemy models
│   ├── schemas/              # Pydantic schemas
│   ├── services/             # Business logic
│   ├── db/                   # Multi-database support
│   └── middleware/           # Custom middleware
│
└── tests/                     # Test patterns
```

## Learning Path

### Beginner (lessons/01_beginner/)
1. **01_hello_world.py** - Your first FastAPI app
2. **02_path_parameters.py** - URL path parameters
3. **03_query_parameters.py** - Query string parameters
4. **04_request_body.py** - POST data with Pydantic
5. **05_responses.py** - Status codes & error handling
6. **06_async_basics.py** - Async/await introduction

### Intermediate (lessons/02_intermediate/)
1. **01_database_sqlalchemy.py** - SQLAlchemy ORM integration
2. **02_authentication.py** - JWT authentication
3. **03_middleware.py** - Custom middleware
4. **04_dependencies.py** - Dependency injection
5. **05_advanced_dependencies.py** - Scoped, factory, contextual DI
6. **06_database_config.py** - PostgreSQL & MySQL setup
7. **07_advanced_security.py** - Refresh tokens, rate limiting, API keys
8. **08_basic_auth.py** - API keys, HTTP Basic auth

### Advanced (lessons/03_advanced/)
1. **01_project_structure.py** - Production architecture
2. **02_mcp_integration.py** - MCP & browser automation
3. **03_graph_database.py** - Neo4j integration
4. **04_vector_database.py** - ChromaDB, pgvector, Pinecone
5. **05_oauth2_providers.py** - Google, GitHub, Microsoft OAuth2
6. **06_openid_sso.py** - OpenID Connect, SSO
7. **07_rbac.py** - Role-Based Access Control
8. **08_abac.py** - Attribute-Based Access Control
9. **09_permission_scopes.py** - OAuth2-style API scopes

## Production Features

### Security
- JWT access + refresh tokens
- Argon2 & bcrypt password hashing
- API key authentication
- Rate limiting middleware
- Security headers
- Token blacklisting

### Authentication & Authorization
- OAuth2 providers (Google, GitHub, Microsoft)
- OpenID Connect / SSO
- RBAC (Role-Based Access Control)
- ABAC (Attribute-Based Access Control)
- Permission scopes

### Database Support
- PostgreSQL (asyncpg)
- MySQL (aiomysql)
- Neo4j (graph database)
- ChromaDB, Pinecone, pgvector (vector databases)
- Connection pooling

### Architecture
- Multi-layer design (API → Service → Data)
- Dependency injection patterns
- Configuration management
- API versioning

## Project Types

This skill is designed for:
- REST API backends
- SaaS applications
- Microservices
- Enterprise apps with SSO
- AI/ML applications (vector DBs)
- E-commerce platforms
- Internal tools

## API Endpoints (Production App)

### Authentication
- `POST /api/v1/auth/register` - Register user
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/refresh` - Refresh tokens

### OAuth
- `GET /api/v1/oauth/{provider}/login` - Start OAuth flow
- `GET /api/v1/oauth/{provider}/callback` - OAuth callback

### Users
- `GET /api/v1/users/me` - Current user
- `PUT /api/v1/users/me` - Update profile

### Items
- `GET /api/v1/items` - List items
- `POST /api/v1/items` - Create item
- `GET /api/v1/items/{id}` - Get item
- `PUT /api/v1/items/{id}` - Update item
- `DELETE /api/v1/items/{id}` - Delete item
