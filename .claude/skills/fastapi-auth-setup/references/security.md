# FastAPI Authentication Security Best Practices

## Secret Key Management

### ❌ NEVER DO THIS
```python
SECRET_KEY = "my-secret-key"  # Hardcoded!
```

### ✅ USE ENVIRONMENT VARIABLES
```python
# .env
SECRET_KEY=your-super-secret-key-min-32-characters

# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str
    class Config:
        env_file = ".env"
```

### Generate Secure Secret Key
```bash
# Using openssl
openssl rand -hex 32

# Using Python
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Password Security

### ✅ Always Hash Passwords
```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hash on registration
hashed = pwd_context.hash(plain_password)

# Verify on login
pwd_context.verify(plain_password, hashed_password)
```

### ✅ Password Requirements
```python
def validate_password(password: str) -> bool:
    if len(password) < 8:
        return False
    if not any(c.isupper() for c in password):
        return False
    if not any(c.isdigit() for c in password):
        return False
    return True
```

### ❌ Never Store Plain Passwords
```python
# NEVER DO THIS
class User(SQLModel, table=True):
    password: str  # ❌ Plain text!

# ✅ ALWAYS HASH
class User(SQLModel, table=True):
    hashed_password: str  # ✅
```

### ❌ Never Return Hashed Passwords
```python
# ❌ Bad - exposes hash
class UserRead(SQLModel):
    email: str
    hashed_password: str  # ❌ Never expose

# ✅ Good - excludes hash
class UserRead(SQLModel):
    email: str
    # No password field
```

---

## JWT Security

### Token Expiration
```python
# ✅ Short expiration for access tokens
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# ✅ Longer for refresh tokens
REFRESH_TOKEN_EXPIRE_DAYS = 7
```

### Token Payload
```python
# ✅ Minimal data in token
def create_access_token(user_id: int):
    return jwt.encode(
        {"sub": str(user_id), "exp": expire_time},
        SECRET_KEY
    )

# ❌ Don't include sensitive data
def bad_token(user):
    return jwt.encode(
        {"email": user.email, "password": user.hashed_password},  # ❌
        SECRET_KEY
    )
```

---

## HTTPS in Production

### ✅ Always Use HTTPS
```python
# In production, enforce HTTPS
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

if settings.ENVIRONMENT == "production":
    app.add_middleware(HTTPSRedirectMiddleware)
```

---

## Rate Limiting

### ✅ Protect Login Endpoint
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/auth/token")
@limiter.limit("5/minute")  # 5 attempts per minute
def login(request: Request, ...):
    ...
```

---

## Error Messages

### ❌ Don't Leak Information
```python
# ❌ Bad - tells attacker email exists
if not user:
    raise HTTPException(401, "User not found")
if not verify_password(password, user.hashed_password):
    raise HTTPException(401, "Wrong password")

# ✅ Good - generic message
if not user or not verify_password(password, user.hashed_password):
    raise HTTPException(401, "Incorrect username or password")
```

---

## Summary

| Security Concern | Solution |
|------------------|----------|
| Secret keys | Environment variables, min 32 chars |
| Passwords | bcrypt hashing, never plain text |
| Token expiry | 30 min for access, 7 days for refresh |
| HTTPS | Always in production |
| Rate limiting | Protect login endpoints |
| Error messages | Don't leak user existence |
| Token payload | Minimal data, no secrets |
| Password exposure | Never in API responses |
