---
name: fastapi-auth-setup
description: |
  Sets up JWT-based authentication and authorization for FastAPI applications with password hashing, token generation, and protected endpoints.
  This skill should be used when developers need to add authentication to their FastAPI application, protect endpoints, or implement user login/registration.
---

# FastAPI Authentication Setup

Sets up production-ready JWT authentication for FastAPI applications.

## What This Skill Does

- Creates JWT token-based authentication
- Implements password hashing with bcrypt
- Generates login/register endpoints
- Adds authentication dependencies
- Protects endpoints with auth requirements
- Implements token refresh logic

## What This Skill Does NOT Do

- Create complete user management system
- Implement OAuth2 providers (Google, GitHub, etc.)
- Set up 2FA/MFA
- Handle email verification
- Create password reset flows (suggest as follow-up)

---

## Before Implementation

Gather context:

| Source | Gather |
|--------|--------|
| **Codebase** | Existing user model, dependencies, app structure |
| **Conversation** | Auth requirements, token expiry, protected endpoints |
| **Skill References** | JWT patterns, security best practices |
| **User Guidelines** | Security requirements, compliance needs |

---

## Clarifications

1. **User Model** - Do you have a User model? What fields does it have?
2. **Protected Endpoints** - Which endpoints need authentication?
3. **Token Expiry** - How long should tokens be valid? (default: 30 min)
4. **Additional Features** - Need refresh tokens? Role-based access?

---

## Implementation Workflow

### 1. Install Dependencies

```bash
pip install python-jose[cryptography] passlib[bcrypt] python-multipart
```

Or add to `pyproject.toml`:
```toml
dependencies = [
    "python-jose[cryptography]>=3.3.0",
    "passlib[bcrypt]>=1.7.4",
    "python-multipart>=0.0.6",
]
```

### 2. Create Auth Configuration

```python
# config.py or settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str = "your-secret-key-here"  # Change in production!
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"

settings = Settings()
```

### 3. Create Password Utilities

```python
# auth/password.py
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
```

### 4. Create JWT Token Functions

```python
# auth/jwt.py
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from config import settings

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
```

### 5. Create Authentication Dependency

```python
# auth/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
from models import User
from database import get_session
from auth.jwt import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id: int = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    user = session.get(User, user_id)
    if user is None:
        raise credentials_exception

    return user
```

### 6. Create Login Endpoint

```python
# routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from datetime import timedelta
from models import User
from database import get_session
from auth.password import verify_password
from auth.jwt import create_access_token
from config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/token")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session)
):
    # Find user by username/email
    user = session.exec(
        select(User).where(User.email == form_data.username)
    ).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}
```

### 7. Create Register Endpoint

```python
@router.post("/register", response_model=UserRead, status_code=201)
def register(
    user: UserCreate,
    session: Session = Depends(get_session)
):
    # Check if user exists
    existing = session.exec(
        select(User).where(User.email == user.email)
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="User with this email already exists"
        )

    # Create user with hashed password
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        hashed_password=hashed_password,
        name=user.name
    )

    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user
```

### 8. Protect Endpoints

```python
# routes/tasks.py
from auth.dependencies import get_current_user
from models import User

@app.get("/tasks", response_model=List[TaskRead])
def get_tasks(
    current_user: User = Depends(get_current_user),  # Add this
    session: Session = Depends(get_session)
):
    # Only return current user's tasks
    tasks = session.exec(
        select(Task).where(Task.user_id == current_user.id)
    ).all()
    return tasks
```

### 9. Update User Model

Ensure User model has:

```python
class UserBase(SQLModel):
    email: str = Field(unique=True, index=True)
    name: str

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str  # Never expose in Read schema

class UserCreate(SQLModel):
    email: str
    name: str
    password: str  # Plain password for registration

class UserRead(UserBase):
    id: int
    # Note: no hashed_password here!
```

---

## Quality Checklist

- [ ] SECRET_KEY in .env (not hardcoded)
- [ ] Password hashing with bcrypt
- [ ] JWT tokens with expiration
- [ ] OAuth2PasswordBearer configured
- [ ] get_current_user dependency working
- [ ] Login endpoint returns JWT token
- [ ] Register endpoint hashes passwords
- [ ] Protected endpoints use get_current_user
- [ ] User model has hashed_password field
- [ ] UserRead schema excludes hashed_password
- [ ] 401 errors for invalid tokens
- [ ] Dependencies installed

---

## Testing Authentication

```bash
# Register user
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "name": "User", "password": "password123"}'

# Login
curl -X POST "http://localhost:8000/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=password123"

# Access protected endpoint
curl -X GET "http://localhost:8000/tasks" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## Reference Files

| File | When to Read |
|------|--------------|
| `references/jwt-patterns.md` | JWT token patterns and security |
| `references/security.md` | Security best practices |
| `references/rbac.md` | Role-based access control (optional) |
