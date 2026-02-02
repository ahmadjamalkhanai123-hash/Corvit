"""
LESSON 15: Advanced Security Patterns
=====================================

Implement production-grade security measures for FastAPI applications.

Key Concepts:
- Password hashing comparison (bcrypt vs argon2)
- JWT refresh tokens implementation
- Token blacklisting/revocation
- Rate limiting middleware
- API key authentication
- Security headers middleware
- CORS best practices

To run this lesson:
    cd fastapi-skills-lab
    uv run uvicorn lessons.02_intermediate.07_advanced_security:app --reload

Then visit: http://127.0.0.1:8000/docs
"""

from datetime import datetime, timedelta, timezone
from typing import Annotated
from contextlib import asynccontextmanager
import secrets
import hashlib

from fastapi import FastAPI, Depends, HTTPException, status, Security, Request, Response
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, EmailStr, Field
from jose import JWTError, jwt

# =============================================================================
# SECTION 1: Password Hashing Comparison (bcrypt vs argon2)
# =============================================================================

"""
Password hashing is critical for security. Two main algorithms:

1. bcrypt - Industry standard, time-tested
   - Adjustable work factor (cost)
   - Built-in salt handling
   - Widely supported

2. argon2 - Winner of Password Hashing Competition (2015)
   - Memory-hard (resistant to GPU attacks)
   - Three variants: argon2d, argon2i, argon2id (recommended)
   - More modern, considered more secure
"""

# Using passlib for both algorithms
from passlib.context import CryptContext

# bcrypt context - traditional choice
bcrypt_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Work factor (default is 12)
)

# argon2 context - modern choice (recommended)
argon2_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__memory_cost=65536,  # 64 MB
    argon2__time_cost=3,        # iterations
    argon2__parallelism=4       # threads
)

def hash_password_bcrypt(password: str) -> str:
    """Hash password using bcrypt."""
    return bcrypt_context.hash(password)

def verify_password_bcrypt(plain_password: str, hashed_password: str) -> bool:
    """Verify password against bcrypt hash."""
    return bcrypt_context.verify(plain_password, hashed_password)

def hash_password_argon2(password: str) -> str:
    """Hash password using argon2 (recommended)."""
    return argon2_context.hash(password)

def verify_password_argon2(plain_password: str, hashed_password: str) -> bool:
    """Verify password against argon2 hash."""
    return argon2_context.verify(plain_password, hashed_password)


# =============================================================================
# SECTION 2: JWT Refresh Tokens
# =============================================================================

"""
Refresh Token Flow:
1. User logs in -> receives access_token (short-lived) + refresh_token (long-lived)
2. Access token expires -> client uses refresh_token to get new access_token
3. Refresh token expires -> user must log in again

Benefits:
- Access tokens are short-lived (15 min) - limits damage if stolen
- Refresh tokens are long-lived (7 days) - better UX
- Can revoke refresh tokens without affecting all sessions
"""

SECRET_KEY = "your-secret-key-change-in-production-use-secrets-token-hex-32"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

class TokenPair(BaseModel):
    """Response model for token pair."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    """JWT token payload."""
    sub: str  # subject (user id)
    exp: datetime  # expiration
    type: str  # "access" or "refresh"
    jti: str  # JWT ID (for blacklisting)

def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    """Create a short-lived access token."""
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {
        "sub": subject,
        "exp": expire,
        "type": "access",
        "jti": secrets.token_hex(16)  # Unique token ID
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(subject: str, expires_delta: timedelta | None = None) -> str:
    """Create a long-lived refresh token."""
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
    payload = {
        "sub": subject,
        "exp": expire,
        "type": "refresh",
        "jti": secrets.token_hex(16)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def create_token_pair(subject: str) -> TokenPair:
    """Create both access and refresh tokens."""
    return TokenPair(
        access_token=create_access_token(subject),
        refresh_token=create_refresh_token(subject)
    )

def verify_token(token: str, expected_type: str = "access") -> TokenPayload:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type. Expected {expected_type}."
            )
        return TokenPayload(**payload)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


# =============================================================================
# SECTION 3: Token Blacklisting/Revocation
# =============================================================================

"""
Token blacklisting allows you to invalidate tokens before expiration.
Use cases:
- User logout
- Password change
- Security breach
- Account suspension

Storage options:
- In-memory (demo only)
- Redis (recommended for production)
- Database
"""

class TokenBlacklist:
    """
    Token blacklist for revoking tokens.

    In production, use Redis:
        import redis
        r = redis.Redis()
        r.setex(f"blacklist:{jti}", ttl_seconds, "1")
    """

    def __init__(self):
        self._blacklist: set[str] = set()

    def add(self, jti: str, expires_at: datetime) -> None:
        """Add token to blacklist."""
        # In production, set TTL based on expires_at
        self._blacklist.add(jti)

    def is_blacklisted(self, jti: str) -> bool:
        """Check if token is blacklisted."""
        return jti in self._blacklist

    def remove_expired(self) -> None:
        """Clean up expired tokens (for in-memory only)."""
        # In production with Redis, TTL handles this automatically
        pass

# Global blacklist instance
token_blacklist = TokenBlacklist()

def revoke_token(token: str) -> None:
    """Revoke a token by adding to blacklist."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        jti = payload.get("jti")
        exp = datetime.fromtimestamp(payload.get("exp"), tz=timezone.utc)
        if jti:
            token_blacklist.add(jti, exp)
    except JWTError:
        pass  # Invalid token, nothing to revoke


# =============================================================================
# SECTION 4: Rate Limiting
# =============================================================================

"""
Rate limiting protects your API from:
- DDoS attacks
- Brute force attempts
- API abuse
- Resource exhaustion

Common strategies:
- Fixed window (simple)
- Sliding window (smoother)
- Token bucket (flexible)
"""

from collections import defaultdict
import time

class RateLimiter:
    """
    Simple sliding window rate limiter.

    In production, use slowapi or Redis-based solutions:
        from slowapi import Limiter
        limiter = Limiter(key_func=get_remote_address)
    """

    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.window_size = 60  # seconds
        self.requests: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed for given key (IP/user)."""
        now = time.time()
        window_start = now - self.window_size

        # Clean old requests
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if req_time > window_start
        ]

        # Check limit
        if len(self.requests[key]) >= self.requests_per_minute:
            return False

        # Record request
        self.requests[key].append(now)
        return True

    def get_remaining(self, key: str) -> int:
        """Get remaining requests for key."""
        now = time.time()
        window_start = now - self.window_size
        current_requests = len([
            r for r in self.requests[key] if r > window_start
        ])
        return max(0, self.requests_per_minute - current_requests)

# Global rate limiter
rate_limiter = RateLimiter(requests_per_minute=60)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to apply rate limiting to all requests."""

    async def dispatch(self, request: Request, call_next):
        # Use client IP as key (in production, consider user ID for authenticated requests)
        client_ip = request.client.host if request.client else "unknown"

        if not rate_limiter.is_allowed(client_ip):
            return Response(
                content='{"detail": "Rate limit exceeded. Try again later."}',
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                media_type="application/json"
            )

        response = await call_next(request)

        # Add rate limit headers
        remaining = rate_limiter.get_remaining(client_ip)
        response.headers["X-RateLimit-Limit"] = str(rate_limiter.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response


# =============================================================================
# SECTION 5: API Key Authentication
# =============================================================================

"""
API keys are simple authentication for:
- Server-to-server communication
- Third-party integrations
- Public APIs with usage tracking

Best practices:
- Hash stored keys (never store plain text)
- Use prefix for identification (e.g., "sk_live_...")
- Set expiration dates
- Track usage per key
"""

# Simulated API key storage (use database in production)
API_KEYS_DB: dict[str, dict] = {
    # key_hash: {owner, created_at, expires_at, scopes}
}

def generate_api_key(owner: str, prefix: str = "sk_live") -> tuple[str, str]:
    """
    Generate a new API key.
    Returns (full_key, key_hash) - store only the hash!
    """
    random_part = secrets.token_hex(24)
    full_key = f"{prefix}_{random_part}"
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()

    # Store metadata (in production, use database)
    API_KEYS_DB[key_hash] = {
        "owner": owner,
        "created_at": datetime.now(timezone.utc),
        "expires_at": datetime.now(timezone.utc) + timedelta(days=365),
        "scopes": ["read", "write"]
    }

    return full_key, key_hash

def verify_api_key(api_key: str) -> dict | None:
    """Verify an API key and return its metadata."""
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    key_data = API_KEYS_DB.get(key_hash)

    if not key_data:
        return None

    # Check expiration
    if datetime.now(timezone.utc) > key_data["expires_at"]:
        return None

    return key_data

# FastAPI API key security scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_api_key(
    api_key: str = Security(api_key_header)
) -> dict:
    """Dependency to validate API key."""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )

    key_data = verify_api_key(api_key)
    if not key_data:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or expired API key"
        )

    return key_data


# =============================================================================
# SECTION 6: Security Headers Middleware
# =============================================================================

"""
Security headers protect against common web vulnerabilities:
- XSS (Cross-Site Scripting)
- Clickjacking
- MIME sniffing
- Man-in-the-middle attacks
"""

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Prevent XSS attacks
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Enforce HTTPS (enable in production)
        # response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Content Security Policy (customize based on your needs)
        response.headers["Content-Security-Policy"] = "default-src 'self'"

        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy (formerly Feature-Policy)
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        return response


# =============================================================================
# SECTION 7: CORS Best Practices
# =============================================================================

"""
CORS (Cross-Origin Resource Sharing) controls which domains can access your API.

Best practices:
- Never use allow_origins=["*"] in production with credentials
- Be specific about allowed origins
- Limit allowed methods and headers
- Set appropriate max_age for preflight caching
"""

def get_cors_config():
    """Get CORS configuration based on environment."""
    # In production, load from environment variables
    return {
        "allow_origins": [
            "http://localhost:3000",      # Local development
            "http://localhost:5173",      # Vite dev server
            "https://yourdomain.com",     # Production frontend
        ],
        "allow_credentials": True,
        "allow_methods": ["GET", "POST", "PUT", "DELETE", "PATCH"],
        "allow_headers": [
            "Authorization",
            "Content-Type",
            "X-API-Key",
            "X-Request-ID",
        ],
        "expose_headers": [
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-Request-ID",
        ],
        "max_age": 600,  # Cache preflight for 10 minutes
    }


# =============================================================================
# APPLICATION SETUP
# =============================================================================

# In-memory user database for demo
users_db: dict[str, dict] = {}
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create demo API key
    full_key, _ = generate_api_key("demo_user")
    print(f"\nDemo API Key: {full_key}\n")
    yield
    # Shutdown

app = FastAPI(
    title="Advanced Security Patterns",
    description="Learn production-grade security for FastAPI",
    version="1.0.0",
    lifespan=lifespan
)

# Add middlewares (order matters - last added runs first)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)

# Add CORS
cors_config = get_cors_config()
app.add_middleware(
    CORSMiddleware,
    **cors_config
)


# =============================================================================
# SCHEMAS
# =============================================================================

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)

class UserResponse(BaseModel):
    username: str
    email: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str


# =============================================================================
# DEPENDENCIES
# =============================================================================

async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """Get current user from access token."""
    payload = verify_token(token, expected_type="access")

    # Check blacklist
    if token_blacklist.is_blacklisted(payload.jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked"
        )

    user = users_db.get(payload.sub)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user


# =============================================================================
# ENDPOINTS
# =============================================================================

@app.post("/auth/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    """Register a new user with argon2 password hashing."""
    if user_data.username in users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    # Use argon2 for password hashing (recommended)
    hashed_password = hash_password_argon2(user_data.password)

    users_db[user_data.username] = {
        "username": user_data.username,
        "email": user_data.email,
        "hashed_password": hashed_password
    }

    return UserResponse(username=user_data.username, email=user_data.email)


@app.post("/auth/login", response_model=TokenPair)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login and receive access + refresh token pair."""
    user = users_db.get(form_data.username)

    if not user or not verify_password_argon2(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    return create_token_pair(form_data.username)


@app.post("/auth/refresh", response_model=TokenPair)
async def refresh_tokens(request: RefreshTokenRequest):
    """Get new token pair using refresh token."""
    payload = verify_token(request.refresh_token, expected_type="refresh")

    # Check blacklist
    if token_blacklist.is_blacklisted(payload.jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked"
        )

    # Revoke old refresh token (rotation)
    revoke_token(request.refresh_token)

    # Issue new token pair
    return create_token_pair(payload.sub)


@app.post("/auth/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    """Logout by revoking current token."""
    revoke_token(token)
    return {"message": "Successfully logged out"}


@app.get("/users/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user (requires authentication)."""
    return UserResponse(**current_user)


@app.get("/api/protected")
async def protected_with_api_key(key_data: dict = Depends(get_api_key)):
    """Endpoint protected by API key."""
    return {
        "message": "Access granted",
        "owner": key_data["owner"],
        "scopes": key_data["scopes"]
    }


@app.get("/health")
async def health_check():
    """Public health check endpoint."""
    return {"status": "healthy"}


# =============================================================================
# KEY CONCEPTS SUMMARY
# =============================================================================

"""
KEY CONCEPTS:
=============

1. PASSWORD HASHING:
   - bcrypt: Traditional, widely used, adjustable work factor
   - argon2: Modern, memory-hard, recommended for new projects
   - Always use password hashing libraries, never roll your own

2. JWT REFRESH TOKENS:
   - Access tokens: Short-lived (15 min), used for API requests
   - Refresh tokens: Long-lived (7 days), used to get new access tokens
   - Token rotation: Revoke old refresh token when issuing new pair

3. TOKEN BLACKLISTING:
   - Store revoked token IDs (jti) until expiration
   - Use Redis in production for distributed systems
   - Required for: logout, password change, security incidents

4. RATE LIMITING:
   - Protect against abuse and DDoS
   - Use sliding window for smoother limits
   - Include rate limit headers in responses
   - Consider user-based limits for authenticated endpoints

5. API KEY AUTHENTICATION:
   - Simple auth for server-to-server communication
   - Hash stored keys, never store plain text
   - Use prefixes for identification (sk_live_, sk_test_)
   - Set expiration and track usage

6. SECURITY HEADERS:
   - X-XSS-Protection: Prevent XSS
   - X-Content-Type-Options: Prevent MIME sniffing
   - X-Frame-Options: Prevent clickjacking
   - Strict-Transport-Security: Enforce HTTPS
   - Content-Security-Policy: Control resource loading

7. CORS:
   - Whitelist specific origins, avoid wildcards with credentials
   - Limit methods and headers to what's needed
   - Cache preflight responses to reduce requests

PRODUCTION TIPS:
================
- Use environment variables for secrets
- Implement proper logging and monitoring
- Set up alerting for rate limit violations
- Rotate secrets regularly
- Use HTTPS everywhere
- Consider WAF (Web Application Firewall) for additional protection
"""


# =============================================================================
# EXERCISES
# =============================================================================

"""
EXERCISE 1: Implement Password Reset Flow
-----------------------------------------
Create endpoints for:
1. POST /auth/forgot-password - Send reset token to email
2. POST /auth/reset-password - Reset password with token

Requirements:
- Generate short-lived reset token (15 minutes)
- Hash the reset token before storing
- Invalidate token after use
- Rate limit the forgot-password endpoint


EXERCISE 2: Implement API Key Scopes
------------------------------------
Enhance the API key system with scopes:
1. Define scope hierarchy (read < write < admin)
2. Modify get_api_key to accept required scopes
3. Create endpoints that require specific scopes:
   - GET /data - requires "read" scope
   - POST /data - requires "write" scope
   - DELETE /data - requires "admin" scope

Example dependency:
    def require_scope(required: str):
        async def checker(key_data: dict = Depends(get_api_key)):
            if required not in key_data["scopes"]:
                raise HTTPException(403, "Insufficient scope")
            return key_data
        return checker
"""
