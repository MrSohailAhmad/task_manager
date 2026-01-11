# HTTP Status Codes for FastAPI

Quick reference for choosing appropriate status codes.

## Success Codes (2xx)

| Code | Name | Use When | Example |
|------|------|----------|---------|
| **200** | OK | GET/PATCH/DELETE successful | GET /tasks returns list |
| **201** | Created | Resource created via POST | POST /tasks creates new task |
| **204** | No Content | Successful DELETE with no body | DELETE /tasks/1 (no response body) |

### Usage Examples

```python
# 200 OK (default for GET)
@app.get("/tasks")
def get_tasks():
    return tasks

# 201 Created
@app.post("/tasks", status_code=201)
def create_task(task: TaskCreate):
    return created_task

# 204 No Content
@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    session.delete(task)
    session.commit()
    return  # No body with 204
```

---

## Client Error Codes (4xx)

| Code | Name | Use When | Example |
|------|------|----------|---------|
| **400** | Bad Request | Invalid data, validation failed | Missing required field |
| **401** | Unauthorized | Authentication required/failed | No token or invalid token |
| **403** | Forbidden | Authenticated but no permission | User can't delete others' tasks |
| **404** | Not Found | Resource doesn't exist | GET /tasks/999 (doesn't exist) |
| **409** | Conflict | Resource conflict (duplicate) | POST /tasks (title already exists) |
| **422** | Unprocessable Entity | Pydantic validation failure | FastAPI auto-returns this |
| **429** | Too Many Requests | Rate limit exceeded | User exceeded API rate limit |

### Usage Examples

```python
# 400 Bad Request
@app.post("/tasks")
def create_task(task: TaskCreate):
    if not validate_due_date(task.due_date):
        raise HTTPException(
            status_code=400,
            detail="Due date must be in the future"
        )
    return created_task

# 401 Unauthorized
@app.get("/tasks")
def get_tasks(token: str = Depends(oauth2_scheme)):
    if not verify_token(token):
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return tasks

# 403 Forbidden
@app.delete("/tasks/{task_id}")
def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user)
):
    task = session.get(Task, task_id)
    if task.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to delete this task"
        )
    session.delete(task)
    session.commit()

# 404 Not Found
@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )
    return task

# 409 Conflict
@app.post("/tasks")
def create_task(task: TaskCreate, session: Session = Depends(get_session)):
    existing = session.exec(
        select(Task).where(Task.title == task.title)
    ).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail="Task with this title already exists"
        )
    return created_task
```

### 422 vs 400

FastAPI automatically returns **422** for Pydantic validation failures:

```python
class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    priority: int = Field(ge=1, le=5)

# If client sends {"title": "", "priority": 6}
# FastAPI automatically returns 422 with validation details
```

Use **400** for business logic validation:

```python
@app.post("/tasks")
def create_task(task: TaskCreate):
    # Pydantic already validated structure (422 if bad)

    # Business logic validation (400 if bad)
    if task.due_date < datetime.now():
        raise HTTPException(
            status_code=400,
            detail="Due date cannot be in the past"
        )
```

---

## Server Error Codes (5xx)

| Code | Name | Use When | Example |
|------|------|----------|---------|
| **500** | Internal Server Error | Unexpected server error | Database connection failed |
| **503** | Service Unavailable | Service temporarily down | Database maintenance |

### Usage Examples

```python
# 500 Internal Server Error (caught by exception handler)
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# 503 Service Unavailable
@app.get("/tasks")
def get_tasks():
    try:
        session = get_db_session()
    except ConnectionError:
        raise HTTPException(
            status_code=503,
            detail="Database temporarily unavailable"
        )
    return tasks
```

---

## Decision Tree

```
Was the request successful?
├─ Yes
│   ├─ Created new resource? → 201 Created
│   ├─ Deleted with no response body? → 204 No Content
│   └─ Other success → 200 OK
│
└─ No
    ├─ Client's fault?
    │   ├─ Invalid data/validation failed? → 400 Bad Request
    │   ├─ No/invalid authentication? → 401 Unauthorized
    │   ├─ Authenticated but no permission? → 403 Forbidden
    │   ├─ Resource not found? → 404 Not Found
    │   ├─ Duplicate/conflict? → 409 Conflict
    │   ├─ Pydantic validation failed? → 422 Unprocessable Entity (auto)
    │   └─ Rate limited? → 429 Too Many Requests
    │
    └─ Server's fault?
        ├─ Unexpected error? → 500 Internal Server Error
        └─ Service down? → 503 Service Unavailable
```

---

## Quick Reference by Operation

### GET (Read)
- **200**: Found resource(s)
- **404**: Resource not found
- **401/403**: Not authenticated/authorized

### POST (Create)
- **201**: Resource created
- **400**: Invalid data
- **409**: Duplicate resource
- **422**: Validation failed (auto)
- **401/403**: Not authenticated/authorized

### PATCH/PUT (Update)
- **200**: Resource updated
- **404**: Resource not found
- **400**: Invalid update data
- **422**: Validation failed (auto)
- **401/403**: Not authenticated/authorized

### DELETE (Delete)
- **200**: Deleted with message/data
- **204**: Deleted with no body
- **404**: Resource not found
- **401/403**: Not authenticated/authorized

---

## Best Practices

1. **Be Specific**: Use the most specific code that applies
   - Not found? 404 (not 400)
   - Duplicate? 409 (not 400)

2. **Consistent Messages**: Use clear, consistent error messages
   ```python
   # Good
   raise HTTPException(404, detail="Task not found")

   # Bad
   raise HTTPException(404, detail="Oops! That doesn't exist!")
   ```

3. **Let FastAPI Handle 422**: Don't manually raise 422
   ```python
   # Good - Pydantic handles this automatically
   class TaskCreate(BaseModel):
       priority: int = Field(ge=1, le=5)

   # Bad - Don't do this
   if not (1 <= task.priority <= 5):
       raise HTTPException(422, "Invalid priority")
   ```

4. **Include Helpful Details**: Provide actionable error messages
   ```python
   # Good
   raise HTTPException(
       400,
       detail="Due date must be in format YYYY-MM-DD"
   )

   # Bad
   raise HTTPException(400, detail="Invalid date")
   ```

5. **Log Server Errors**: Always log 5xx errors for debugging
   ```python
   try:
       result = complex_operation()
   except Exception as e:
       logger.error(f"Operation failed: {e}", exc_info=True)
       raise HTTPException(500, "Internal server error")
   ```
