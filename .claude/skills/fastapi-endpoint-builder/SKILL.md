---
name: fastapi-endpoint-builder
description: |
  Creates FastAPI REST API endpoints with proper validation, error handling, response models, and dependency injection.
  This skill should be used when developers need to add new endpoints to their FastAPI application with best practices for async/sync handling, security, and maintainability.
---

# FastAPI Endpoint Builder

Creates production-ready FastAPI endpoints following best practices.

## What This Skill Does

- Generates CRUD endpoints with proper HTTP methods
- Implements request validation using Pydantic models
- Adds appropriate error handling and status codes
- Configures dependency injection (database sessions, auth)
- Handles async/sync operations correctly
- Includes response models and status codes

## What This Skill Does NOT Do

- Create database models (use fastapi-model-generator)
- Set up authentication systems (use fastapi-auth-setup)
- Generate tests (use fastapi-test-generator)
- Modify existing endpoints without explicit instruction

---

## Before Implementation

Gather context to ensure successful implementation:

| Source | Gather |
|--------|--------|
| **Codebase** | Existing FastAPI app structure, router organization, dependency patterns |
| **Conversation** | Endpoint requirements, HTTP methods, validation rules, business logic |
| **Skill References** | FastAPI patterns from `references/` (best practices, anti-patterns) |
| **User Guidelines** | Project-specific conventions, naming patterns, error handling |

Ensure all required context is gathered before implementing.
Only ask user for THEIR specific requirements (domain expertise is in this skill).

---

## Clarifications

Ask user about endpoint specifics:

1. **Resource & Operations** - What resource and which operations (GET/POST/PATCH/DELETE)?
2. **Request Data** - What input fields and validation rules?
3. **Response Format** - What should the endpoint return?
4. **Dependencies** - Does it need database access, authentication, or other dependencies?

---

## Implementation Workflow

### 1. Analyze Existing Structure

Search codebase for:
- Main FastAPI app file (usually `main.py` or `app.py`)
- Existing routers and endpoint patterns
- Database session dependency pattern
- Response model patterns
- Error handling approach

### 2. Choose Async vs Sync

Decision tree:

```
Does endpoint perform I/O operations?
├─ Yes → Does it use async-compatible libraries (asyncpg, httpx, etc)?
│   ├─ Yes → Use async def
│   └─ No → Use def (sync, runs in threadpool)
└─ No (CPU-only) → Use def
```

**Critical**: Never mix `async def` with blocking I/O. See `references/async-patterns.md`.

### 3. Structure Endpoint

```python
@router.{method}("/{path}", response_model=ResponseModel, status_code=status_code)
def endpoint_name(
    # Path parameters first
    id: int,
    # Query parameters with defaults
    limit: int = Query(default=100, le=100),
    # Request body
    data: RequestModel,
    # Dependencies last
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
) -> ResponseModel:
    """
    Brief description of what this endpoint does.
    """
    # Implementation
```

### 4. Add Error Handling

Common patterns:

```python
# Not found
resource = session.get(Model, id)
if not resource:
    raise HTTPException(status_code=404, detail=f"{Model.__name__} not found")

# Validation error
if not validate_business_rule(data):
    raise HTTPException(status_code=400, detail="Validation message")

# Conflict
if duplicate_exists(session, data.unique_field):
    raise HTTPException(status_code=409, detail="Resource already exists")
```

### 5. Implement CRUD Operations

Follow existing patterns in codebase:

**CREATE** (POST):
```python
db_obj = Model.model_validate(data)
session.add(db_obj)
session.commit()
session.refresh(db_obj)
return db_obj
```

**READ** (GET):
```python
# Single
obj = session.get(Model, id)
# Multiple with pagination
statement = select(Model).offset(offset).limit(limit)
objects = session.exec(statement).all()
```

**UPDATE** (PATCH):
```python
db_obj = session.get(Model, id)
update_data = data.model_dump(exclude_unset=True)
for key, value in update_data.items():
    setattr(db_obj, key, value)
session.add(db_obj)
session.commit()
session.refresh(db_obj)
```

**DELETE** (DELETE):
```python
obj = session.get(Model, id)
session.delete(obj)
session.commit()
```

### 6. Set Correct Status Codes

| Operation | Success Code |
|-----------|--------------|
| GET (found) | 200 OK |
| POST (created) | 201 Created |
| PATCH (updated) | 200 OK |
| DELETE (deleted) | 204 No Content or 200 with message |
| GET (list) | 200 OK |

### 7. Add to Router/App

If endpoint belongs to existing resource:
- Add to existing router file
- Keep related endpoints together

If new resource:
- Ask if user wants new router file
- Import and include in main app

---

## Quality Checklist

Before delivering endpoint, verify:

- [ ] Correct async/sync (no blocking I/O in async def)
- [ ] Request validation with Pydantic models
- [ ] Response model specified
- [ ] Appropriate status code set
- [ ] Error cases handled (404, 400, 409)
- [ ] Dependencies injected properly
- [ ] Follows existing code style
- [ ] Added to correct router/app
- [ ] Database session committed and refreshed
- [ ] No security vulnerabilities (SQL injection, etc.)

---

## Common Patterns

### Pagination
```python
def list_resources(
    offset: int = 0,
    limit: int = Query(default=100, le=100),
    session: Session = Depends(get_session)
):
    statement = select(Model).offset(offset).limit(limit)
    return session.exec(statement).all()
```

### Filtering
```python
def search_resources(
    q: str | None = None,
    status: str | None = None,
    session: Session = Depends(get_session)
):
    statement = select(Model)
    if q:
        statement = statement.where(Model.name.contains(q))
    if status:
        statement = statement.where(Model.status == status)
    return session.exec(statement).all()
```

### Soft Delete
```python
def delete_resource(id: int, session: Session = Depends(get_session)):
    obj = session.get(Model, id)
    if not obj:
        raise HTTPException(status_code=404, detail="Not found")
    obj.deleted_at = datetime.utcnow()
    session.add(obj)
    session.commit()
    return {"ok": True}
```

---

## Anti-Patterns to Avoid

❌ **Blocking I/O in async def**
```python
async def bad():  # async def
    result = requests.get(url)  # Blocking!
```

❌ **Missing error handling**
```python
def bad(id: int, session: Session = Depends(get_session)):
    obj = session.get(Model, id)  # Could be None!
    return obj  # Crashes if None
```

❌ **Forgetting to commit**
```python
def bad(data: Create, session: Session = Depends(get_session)):
    obj = Model(**data.dict())
    session.add(obj)
    # Missing commit!
    return obj
```

❌ **Endpoint-to-endpoint calls**
```python
def bad():
    response = httpx.get("http://localhost:8000/other-endpoint")  # Bad!
    # Extract logic to shared function instead
```

See `references/anti-patterns.md` for complete list.

---

## Reference Files

| File | When to Read |
|------|--------------|
| `references/async-patterns.md` | Deciding async vs sync, avoiding event loop blocking |
| `references/anti-patterns.md` | Common mistakes and how to avoid them |
| `references/status-codes.md` | HTTP status code reference |
| `references/validation-patterns.md` | Advanced Pydantic validation patterns |
