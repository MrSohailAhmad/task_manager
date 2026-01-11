# FastAPI Anti-Patterns

Common mistakes when building FastAPI endpoints and how to avoid them.

## 1. Mixing async def with Blocking I/O

**❌ ANTI-PATTERN**
```python
async def get_tasks(session: Session = Depends(get_session)):
    # session.exec is blocking - kills performance!
    return session.exec(select(Task)).all()
```

**✅ CORRECT**
```python
def get_tasks(session: Session = Depends(get_session)):
    # Sync function with blocking I/O - FastAPI runs in threadpool
    return session.exec(select(Task)).all()
```

**Impact**: Blocks the entire event loop, making all other async operations wait.

---

## 2. Endpoint-to-Endpoint Calls

**❌ ANTI-PATTERN**
```python
@app.get("/summary")
def get_summary():
    # Calling your own endpoint through HTTP
    tasks = httpx.get("http://localhost:8000/tasks").json()
    users = httpx.get("http://localhost:8000/users").json()
    return {"tasks": tasks, "users": users}
```

**✅ CORRECT**
```python
@app.get("/summary")
def get_summary(session: Session = Depends(get_session)):
    # Call business logic directly
    tasks = get_tasks_logic(session)
    users = get_users_logic(session)
    return {"tasks": tasks, "users": users}

def get_tasks_logic(session: Session):
    return session.exec(select(Task)).all()

def get_users_logic(session: Session):
    return session.exec(select(User)).all()
```

**Impact**: Adds unnecessary latency, couples endpoints, makes testing harder.

---

## 3. Missing Error Handling

**❌ ANTI-PATTERN**
```python
@app.get("/tasks/{task_id}")
def get_task(task_id: int, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)  # Returns None if not found
    return task  # Will fail if None
```

**✅ CORRECT**
```python
@app.get("/tasks/{task_id}")
def get_task(task_id: int, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
```

---

## 4. Forgetting to Commit

**❌ ANTI-PATTERN**
```python
@app.post("/tasks")
def create_task(task: TaskCreate, session: Session = Depends(get_session)):
    db_task = Task.model_validate(task)
    session.add(db_task)
    # Missing session.commit()!
    return db_task  # Changes not persisted
```

**✅ CORRECT**
```python
@app.post("/tasks")
def create_task(task: TaskCreate, session: Session = Depends(get_session)):
    db_task = Task.model_validate(task)
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return db_task
```

---

## 5. HTTPException in Business Logic

**❌ ANTI-PATTERN**
```python
# services/task_service.py
def create_task(session: Session, data: dict):
    if duplicate_exists(session, data["title"]):
        # Mixing presentation logic with business logic
        raise HTTPException(status_code=409, detail="Duplicate")
    return Task(**data)
```

**✅ CORRECT**
```python
# services/task_service.py
class DuplicateTaskError(Exception):
    pass

def create_task(session: Session, data: dict):
    if duplicate_exists(session, data["title"]):
        raise DuplicateTaskError("Task with this title exists")
    return Task(**data)

# routes/tasks.py
@app.post("/tasks")
def create_task_endpoint(task: TaskCreate, session: Session = Depends(get_session)):
    try:
        db_task = create_task(session, task.model_dump())
        session.add(db_task)
        session.commit()
        return db_task
    except DuplicateTaskError as e:
        raise HTTPException(status_code=409, detail=str(e))
```

---

## 6. Not Using Response Models

**❌ ANTI-PATTERN**
```python
@app.get("/tasks/{task_id}")
def get_task(task_id: int, session: Session = Depends(get_session)):
    return session.get(Task, task_id)  # No response model
```

**Issues**:
- No automatic validation
- May leak internal fields
- OpenAPI docs incomplete

**✅ CORRECT**
```python
@app.get("/tasks/{task_id}", response_model=TaskRead)
def get_task(task_id: int, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Not found")
    return task  # Automatically validates and filters
```

---

## 7. Improper Resource Cleanup

**❌ ANTI-PATTERN**
```python
def get_session():
    session = Session(engine)
    return session  # Session never closed!
```

**✅ CORRECT**
```python
def get_session():
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()
```

---

## 8. Exposing Stack Traces

**❌ ANTI-PATTERN**
```python
@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    # If error occurs, full stack trace leaks to client
    task = complex_operation(task_id)
    return task
```

**✅ CORRECT**
```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log the full error internally
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    # Return safe message to client
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

@app.get("/tasks/{task_id}")
def get_task(task_id: int, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
```

---

## 9. Wrong Status Codes

**❌ ANTI-PATTERN**
```python
@app.post("/tasks")  # Returns 200 by default
def create_task(task: TaskCreate, session: Session = Depends(get_session)):
    db_task = Task.model_validate(task)
    session.add(db_task)
    session.commit()
    return db_task  # Should be 201 Created
```

**✅ CORRECT**
```python
@app.post("/tasks", status_code=201)
def create_task(task: TaskCreate, session: Session = Depends(get_session)):
    db_task = Task.model_validate(task)
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return db_task
```

---

## 10. Ignoring exclude_unset in Updates

**❌ ANTI-PATTERN**
```python
@app.patch("/tasks/{task_id}")
def update_task(task_id: int, task: TaskUpdate, session: Session = Depends(get_session)):
    db_task = session.get(Task, task_id)
    # This will set unset fields to None!
    for key, value in task.model_dump().items():
        setattr(db_task, key, value)
    session.commit()
    return db_task
```

**✅ CORRECT**
```python
@app.patch("/tasks/{task_id}")
def update_task(task_id: int, task: TaskUpdate, session: Session = Depends(get_session)):
    db_task = session.get(Task, task_id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Not found")

    # Only update fields that were actually provided
    update_data = task.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_task, key, value)

    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return db_task
```

---

## 11. Using Mutable Defaults

**❌ ANTI-PATTERN**
```python
from typing import List

@app.get("/tasks")
def get_tasks(tags: List[str] = []):  # Mutable default!
    # Same list object reused across requests
    return filter_by_tags(tags)
```

**✅ CORRECT**
```python
from typing import List

@app.get("/tasks")
def get_tasks(tags: List[str] = Query(default=[])):
    return filter_by_tags(tags)
```

---

## 12. Not Validating Query Parameters

**❌ ANTI-PATTERN**
```python
@app.get("/tasks")
def get_tasks(limit: int = 100):  # No upper bound
    # User could request limit=999999999
    return session.exec(select(Task).limit(limit)).all()
```

**✅ CORRECT**
```python
@app.get("/tasks")
def get_tasks(
    limit: int = Query(default=100, ge=1, le=100)
):
    return session.exec(select(Task).limit(limit)).all()
```

---

## Summary

| Anti-Pattern | Impact | Fix |
|--------------|--------|-----|
| Blocking I/O in async | Kills performance | Use def for blocking I/O |
| Endpoint-to-endpoint calls | Latency, coupling | Extract shared logic |
| Missing error handling | 500 errors | Check for None, validate |
| No commit | Data loss | Always commit changes |
| HTTPException in services | Tight coupling | Use domain exceptions |
| No response models | Security, docs | Always specify response_model |
| Poor resource cleanup | Memory leaks | Use try/finally or yield |
| Exposed stack traces | Security risk | Global exception handler |
| Wrong status codes | Poor API design | Use appropriate codes |
| Ignoring exclude_unset | Unintended nulls | Use model_dump(exclude_unset=True) |
| Mutable defaults | Shared state bugs | Use Query(default=[]) |
| Unvalidated query params | DoS attacks | Use Query with constraints |
