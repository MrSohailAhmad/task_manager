---
name: fastapi-boilerplate-generator
description: |
  Generates common FastAPI code patterns and boilerplate including CRUD operations, middleware, dependencies, and utility functions.
  This skill should be used when developers need to quickly scaffold common patterns, add middleware, create dependencies, or generate repetitive code structures in their FastAPI application.
---

# FastAPI Boilerplate Generator

Generates common FastAPI code patterns and boilerplate to speed up daily development.

## What This Skill Does

- Generates complete CRUD endpoint sets
- Creates common middleware (CORS, timing, logging)
- Builds reusable dependencies
- Creates utility functions (pagination, filtering)
- Generates error handlers
- Provides router templates

## What This Skill Does NOT Do

- Create entire applications from scratch
- Generate business logic
- Write tests (use fastapi-test-generator)
- Create database models (use fastapi-model-generator)

---

## Before Implementation

Gather context:

| Source | Gather |
|--------|--------|
| **Codebase** | Existing structure, patterns, naming conventions |
| **Conversation** | What boilerplate is needed, customization requirements |
| **Skill References** | Common patterns library |
| **User Guidelines** | Project conventions, style preferences |

---

## Clarifications

1. **Boilerplate Type** - What do you need? (CRUD, middleware, dependency, utility)
2. **Resource** - For CRUD: what resource/model?
3. **Customization** - Any specific requirements or modifications?

---

## Available Boilerplate Patterns

### 1. Complete CRUD Endpoints

Generates all CRUD operations for a resource:

```python
# router for Task resource
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from typing import List
from database import get_session
from models import Task, TaskCreate, TaskRead, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("/", response_model=TaskRead, status_code=201)
def create_task(
    task: TaskCreate,
    session: Session = Depends(get_session)
) -> Task:
    """Create a new task"""
    db_task = Task.model_validate(task)
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return db_task

@router.get("/", response_model=List[TaskRead])
def list_tasks(
    offset: int = 0,
    limit: int = Query(default=100, le=100),
    session: Session = Depends(get_session)
) -> List[Task]:
    """List all tasks with pagination"""
    tasks = session.exec(select(Task).offset(offset).limit(limit)).all()
    return tasks

@router.get("/{task_id}", response_model=TaskRead)
def get_task(
    task_id: int,
    session: Session = Depends(get_session)
) -> Task:
    """Get task by ID"""
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.patch("/{task_id}", response_model=TaskRead)
def update_task(
    task_id: int,
    task: TaskUpdate,
    session: Session = Depends(get_session)
) -> Task:
    """Update task by ID"""
    db_task = session.get(Task, task_id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    task_data = task.model_dump(exclude_unset=True)
    for key, value in task_data.items():
        setattr(db_task, key, value)

    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return db_task

@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    session: Session = Depends(get_session)
):
    """Delete task by ID"""
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    session.delete(task)
    session.commit()
    return {"ok": True}
```

### 2. Middleware Patterns

**CORS Middleware**:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Request Timing Middleware**:
```python
import time
from fastapi import Request

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

**Logging Middleware**:
```python
import logging
from fastapi import Request

logger = logging.getLogger(__name__)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"{request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Status: {response.status_code}")
    return response
```

### 3. Common Dependencies

**Pagination Dependency**:
```python
from fastapi import Query

class PaginationParams:
    def __init__(
        self,
        offset: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100)
    ):
        self.offset = offset
        self.limit = limit
```

**Filter Dependency**:
```python
from typing import Optional

class TaskFilters:
    def __init__(
        self,
        status: Optional[str] = None,
        priority: Optional[int] = None,
        search: Optional[str] = None
    ):
        self.status = status
        self.priority = priority
        self.search = search
```

**Current User Dependency** (with auth):
```python
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session)
) -> User:
    # Decode token and get user
    user = get_user_from_token(token, session)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
```

### 4. Utility Functions

**Pagination Helper**:
```python
from typing import List, TypeVar, Generic
from pydantic import BaseModel

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    offset: int
    limit: int

def paginate(
    items: List[T],
    total: int,
    offset: int,
    limit: int
) -> PaginatedResponse[T]:
    return PaginatedResponse(
        items=items,
        total=total,
        offset=offset,
        limit=limit
    )
```

**Filter Builder**:
```python
from sqlmodel import select, or_
from models import Task

def build_task_filters(statement, filters: TaskFilters):
    if filters.status:
        statement = statement.where(Task.status == filters.status)
    if filters.priority:
        statement = statement.where(Task.priority == filters.priority)
    if filters.search:
        statement = statement.where(
            or_(
                Task.title.contains(filters.search),
                Task.description.contains(filters.search)
            )
        )
    return statement
```

### 5. Error Handlers

**Global Exception Handler**:
```python
from fastapi import Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Resource not found"}
    )
```

### 6. Background Tasks Pattern

```python
from fastapi import BackgroundTasks

def send_email(email: str, message: str):
    # Email sending logic
    print(f"Sending email to {email}: {message}")

@app.post("/tasks")
def create_task(
    task: TaskCreate,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session)
):
    db_task = Task.model_validate(task)
    session.add(db_task)
    session.commit()

    # Send email in background
    background_tasks.add_task(
        send_email,
        "user@example.com",
        f"Task created: {task.title}"
    )

    return db_task
```

### 7. Health Check Endpoint

```python
from datetime import datetime

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health/db")
def health_check_db(session: Session = Depends(get_session)):
    try:
        # Simple query to check DB
        session.exec(select(1)).first()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": str(e)}
```

---

## Usage Patterns

### Complete Resource Router

1. Ask for resource name (e.g., "Task")
2. Generate complete CRUD router
3. Add to main.py
4. Generate tests

### Add Middleware

1. Ask for middleware type
2. Generate middleware code
3. Add to main.py

### Create Dependency

1. Ask for dependency purpose
2. Generate dependency function
3. Show usage example

---

## Quality Checklist

- [ ] Code follows project conventions
- [ ] Proper error handling included
- [ ] Type hints on all functions
- [ ] Docstrings for endpoints
- [ ] Status codes specified
- [ ] Dependencies injected properly
- [ ] Models validated correctly

---

## Reference Files

| File | When to Read |
|------|--------------|
| `references/crud-patterns.md` | Full CRUD operation templates |
| `references/middleware-patterns.md` | Common middleware examples |
| `references/dependency-patterns.md` | Reusable dependency patterns |
