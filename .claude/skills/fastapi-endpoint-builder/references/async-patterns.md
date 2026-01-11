# Async Patterns in FastAPI

## Key Principle

**FastAPI runs sync routes in a threadpool, so blocking I/O won't stop the event loop. Async routes are called via await, and FastAPI trusts you to only perform non-blocking I/O operations.**

If you execute blocking operations within `async def`, the event loop won't be able to run other tasks until the blocking operation completes.

## Decision Tree

```
Does the endpoint perform I/O operations?
├─ No (CPU-only operations)
│   └─ Use def (sync)
│
└─ Yes (I/O operations)
    ├─ Using async-compatible libraries?
    │   ├─ Yes (httpx, asyncpg, motor, aiofiles, etc.)
    │   │   └─ Use async def
    │   │
    │   └─ No (requests, psycopg2, pymongo, open(), etc.)
    │       └─ Use def (sync, runs in threadpool)
    │
    └─ Heavy computation (>0.5s CPU time)
        └─ Use def or run in background task
```

## Async-Compatible Libraries

### ✅ Async Libraries (use with async def)
- **HTTP**: httpx, aiohttp
- **PostgreSQL**: asyncpg, SQLAlchemy 2.0 async
- **MongoDB**: motor
- **Redis**: aioredis
- **File I/O**: aiofiles
- **S3**: aioboto3

### ❌ Blocking Libraries (use with def)
- **HTTP**: requests, urllib
- **PostgreSQL**: psycopg2, SQLAlchemy (sync mode)
- **MongoDB**: pymongo
- **Redis**: redis-py (sync)
- **File I/O**: open(), Path.read_text()
- **S3**: boto3

## Examples

### ✅ Correct: Sync with Blocking I/O
```python
def get_tasks(session: Session = Depends(get_session)):
    """SQLModel/SQLAlchemy sync - runs in threadpool"""
    return session.exec(select(Task)).all()
```

### ✅ Correct: Async with Non-Blocking I/O
```python
async def get_external_data():
    """httpx async client"""
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.com/data")
        return response.json()
```

### ❌ WRONG: Async with Blocking I/O
```python
async def bad_endpoint(session: Session = Depends(get_session)):
    """BLOCKS EVENT LOOP - session.exec is blocking!"""
    return session.exec(select(Task)).all()  # ❌ Blocking call in async
```

### ❌ WRONG: Async with Requests
```python
async def bad_external():
    """BLOCKS EVENT LOOP - requests is blocking!"""
    response = requests.get("https://api.example.com")  # ❌
    return response.json()
```

## When to Use Each

### Use `def` (sync) when:
- Using SQLModel/SQLAlchemy without async support
- Using requests, boto3, or other blocking libraries
- Performing CPU-intensive operations
- Simple operations with no I/O

### Use `async def` when:
- Using httpx, asyncpg, motor, or other async libraries
- Need concurrent execution of multiple async operations
- WebSocket endpoints
- Server-Sent Events (SSE)

## Mixed Operations

If you need both sync DB and async HTTP:

```python
def endpoint(session: Session = Depends(get_session)):
    """Keep it sync if using sync DB"""
    # Sync DB operation
    task = session.get(Task, 1)

    # For async HTTP, use anyio or just use sync requests
    import requests
    response = requests.get("https://api.example.com")

    return {"task": task, "external": response.json()}
```

Or use background tasks for external calls:

```python
from fastapi import BackgroundTasks

def endpoint(
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session)
):
    task = session.get(Task, 1)
    background_tasks.add_task(call_external_api, task.id)
    return task

def call_external_api(task_id: int):
    import requests
    requests.post("https://api.example.com/notify", json={"task_id": task_id})
```

## Performance Impact

**Myth**: "async is always faster"
**Reality**: async helps with I/O-bound operations by allowing concurrent handling

- **Sync in threadpool**: Good for blocking I/O, FastAPI handles it
- **Async with blocking I/O**: Terrible, blocks all other requests
- **Async with non-blocking I/O**: Excellent for concurrent operations
- **Sync for CPU-bound**: Appropriate, use background tasks for heavy work

## Summary

1. **Default to `def`** unless you have async-specific needs
2. **Use `async def`** only with async libraries (httpx, asyncpg, etc.)
3. **Never mix** `async def` with blocking I/O (requests, sync DB)
4. **SQLModel/SQLAlchemy sync** → use `def`, FastAPI handles threading
5. **Heavy CPU work** → use `def` or background tasks
