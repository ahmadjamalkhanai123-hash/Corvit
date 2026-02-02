"""
LESSON 8: Authentication with JWT
=================================

Learn how to implement secure authentication using
JWT (JSON Web Tokens) and OAuth2.

Key Concepts:
- Password hashing
- JWT token creation/verification
- OAuth2 with password flow
- Protected endpoints
- Current user dependency

To run:
    uv run uvicorn lessons.02_intermediate.02_authentication:app --reload
"""

from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from jose import JWTError, jwt
from passlib.context import CryptContext

# Configuration
SECRET_KEY = "your-secret-key-change-in-production"  # Use env var in production!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI(title="Authentication Lesson")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme - tells FastAPI where to find the token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Pydantic models
class Token(BaseModel):
    """Response model for token endpoint"""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Data extracted from token"""
    username: str | None = None


class User(BaseModel):
    """Public user data"""
    username: str
    email: str
    full_name: str | None = None
    disabled: bool = False


class UserInDB(User):
    """User data including hashed password (for database)"""
    hashed_password: str


class UserCreate(BaseModel):
    """Data for creating new user"""
    username: str
    email: str
    password: str
    full_name: str | None = None


# Fake database - in real app, use actual database
fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "email": "john@example.com",
        "full_name": "John Doe",
        "disabled": False,
        "hashed_password": pwd_context.hash("secret123")
    }
}


# Helper functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def get_user(db: dict, username: str) -> UserInDB | None:
    """Get user from database."""
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)
    return None


def authenticate_user(db: dict, username: str, password: str) -> UserInDB | None:
    """Authenticate user with username and password."""
    user = get_user(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Create a JWT access token.

    The token contains:
    - sub (subject): the username
    - exp (expiration): when the token expires
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Dependency to get current user from token
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Dependency that extracts and validates the current user from JWT.

    This is used to protect endpoints - if token is invalid,
    raises 401 Unauthorized.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Dependency that also checks if user is active (not disabled)."""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


# Endpoints

@app.post("/register", response_model=User)
def register_user(user: UserCreate):
    """
    Register a new user.

    In production, add:
    - Email verification
    - Password strength validation
    - Rate limiting
    """
    if user.username in fake_users_db:
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )

    hashed_password = get_password_hash(user.password)
    user_dict = {
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "disabled": False,
        "hashed_password": hashed_password
    }
    fake_users_db[user.username] = user_dict
    return user_dict


@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token login.

    Send username and password as form data to get a JWT token.

    Test with:
    curl -X POST "http://localhost:8000/token" \
         -H "Content-Type: application/x-www-form-urlencoded" \
         -d "username=johndoe&password=secret123"
    """
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Get current user info.

    This endpoint is protected - requires valid JWT token.

    Test with:
    curl -X GET "http://localhost:8000/users/me" \
         -H "Authorization: Bearer <your-token>"
    """
    return current_user


@app.get("/protected-data")
async def get_protected_data(current_user: User = Depends(get_current_active_user)):
    """
    A protected endpoint that returns secret data.

    Only authenticated users can access this.
    """
    return {
        "message": f"Hello {current_user.full_name or current_user.username}!",
        "secret_data": "This is protected information",
        "accessed_by": current_user.username
    }


# Public endpoint for comparison
@app.get("/public")
def get_public_data():
    """Public endpoint - no authentication required."""
    return {"message": "This is public data, anyone can see it"}


"""
AUTHENTICATION FLOW:
-------------------

1. User registers with username/password
2. Password is hashed and stored
3. User logs in at /token endpoint
4. Server validates credentials, returns JWT
5. Client includes JWT in Authorization header
6. Protected endpoints validate JWT and extract user

SECURITY TIPS:
--------------
- Never store plain text passwords
- Use strong SECRET_KEY (generate with: openssl rand -hex 32)
- Set reasonable token expiration
- Use HTTPS in production
- Consider refresh tokens for better UX
- Rate limit login attempts


EXERCISE 1:
-----------
Add role-based access control:
- Add a "role" field to User (e.g., "user", "admin")
- Create a dependency that requires admin role
- Create an admin-only endpoint

EXERCISE 2:
-----------
Implement refresh tokens:
- Return both access and refresh tokens
- Create /refresh endpoint to get new access token
- Refresh tokens should have longer expiration
"""
