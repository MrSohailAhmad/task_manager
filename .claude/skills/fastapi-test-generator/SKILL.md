---
name: fastapi-test-generator
description: |
  Generates pytest tests for FastAPI endpoints with fixtures, test data, and coverage for success/error cases.
  This skill should be used when developers need to create tests for their FastAPI endpoints, ensure test coverage, or add test cases for new features.
---

# FastAPI Test Generator

Generates comprehensive pytest tests for FastAPI applications.

## What This Skill Does

- Creates pytest test files for endpoints
- Generates test fixtures (client, database, test data)
- Tests success cases and error cases
- Tests authentication and authorization
- Adds database test isolation
- Follows pytest best practices

## What This Skill Does NOT Do

- Run tests (use pytest command)
- Set up CI/CD pipelines
- Generate load/performance tests
- Create integration tests with external services

---

## Before Implementation

Gather context:

| Source | Gather |
|--------|--------|
| **Codebase** | Existing tests, fixtures, endpoint structure |
| **Conversation** | Which endpoints to test, coverage requirements |
| **Skill References** | Pytest patterns, test isolation techniques |
| **User Guidelines** | Testing standards, coverage targets |

---

## Clarifications

1. **Test Target** - Which endpoint(s) need tests?
2. **Test Database** - Use in-memory SQLite or separate test DB?
3. **Authentication** - Do endpoints require authentication?
4. **Coverage** - What cases to cover? (happy path, errors, edge cases)

---

## Implementation Workflow

### 1. Install Test Dependencies

```bash
pip install pytest pytest-cov httpx
```

Or `pyproject.toml`:
```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "httpx>=0.24.0",
]
```

### 2. Create conftest.py with Fixtures

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from main import app
from database import get_session
from models import User
from auth.password import get_password_hash

@pytest.fixture(name="session")
def session_fixture():
    """Create test database session"""
    engine = create_engine(
        "sqlite://",  # In-memory database
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture(name="client")
def client_fixture(session: Session):
    """Create test client with overridden database"""
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

@pytest.fixture
def test_user(session: Session) -> User:
    """Create test user"""
    user = User(
        email="test@example.com",
        name="Test User",
        hashed_password=get_password_hash("testpass123")
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@pytest.fixture
def auth_token(client: TestClient, test_user: User) -> str:
    """Get auth token for test user"""
    response = client.post(
        "/auth/token",
        data={"username": test_user.email, "password": "testpass123"}
    )
    return response.json()["access_token"]
```

### 3. Test Endpoint Structure

```python
# tests/test_tasks.py
from fastapi.testclient import TestClient
from sqlmodel import Session
from models import Task, User

def test_create_task_success(client: TestClient, auth_token: str):
    """Test successful task creation"""
    response = client.post(
        "/tasks",
        json={"title": "Test Task", "description": "Test description"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["description"] == "Test description"
    assert "id" in data

def test_create_task_unauthorized(client: TestClient):
    """Test task creation without auth"""
    response = client.post(
        "/tasks",
        json={"title": "Test Task"}
    )
    assert response.status_code == 401

def test_create_task_invalid_data(client: TestClient, auth_token: str):
    """Test task creation with invalid data"""
    response = client.post(
        "/tasks",
        json={"title": ""},  # Empty title
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 422  # Validation error

def test_get_task_success(client: TestClient, session: Session, auth_token: str, test_user: User):
    """Test getting task by ID"""
    # Create test task
    task = Task(title="Test Task", user_id=test_user.id)
    session.add(task)
    session.commit()

    response = client.get(
        f"/tasks/{task.id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task.id
    assert data["title"] == "Test Task"

def test_get_task_not_found(client: TestClient, auth_token: str):
    """Test getting non-existent task"""
    response = client.get(
        "/tasks/99999",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 404

def test_update_task_success(client: TestClient, session: Session, auth_token: str, test_user: User):
    """Test updating task"""
    task = Task(title="Old Title", user_id=test_user.id)
    session.add(task)
    session.commit()

    response = client.patch(
        f"/tasks/{task.id}",
        json={"title": "New Title"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "New Title"

def test_delete_task_success(client: TestClient, session: Session, auth_token: str, test_user: User):
    """Test deleting task"""
    task = Task(title="To Delete", user_id=test_user.id)
    session.add(task)
    session.commit()

    response = client.delete(
        f"/tasks/{task.id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 200

    # Verify deleted
    response = client.get(
        f"/tasks/{task.id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 404

def test_list_tasks(client: TestClient, session: Session, auth_token: str, test_user: User):
    """Test listing tasks"""
    # Create test tasks
    for i in range(3):
        task = Task(title=f"Task {i}", user_id=test_user.id)
        session.add(task)
    session.commit()

    response = client.get(
        "/tasks",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
```

### 4. Test Authentication

```python
# tests/test_auth.py

def test_register_success(client: TestClient):
    """Test user registration"""
    response = client.post(
        "/auth/register",
        json={
            "email": "newuser@example.com",
            "name": "New User",
            "password": "password123"
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert "hashed_password" not in data  # Should not expose

def test_register_duplicate_email(client: TestClient, test_user: User):
    """Test registering with existing email"""
    response = client.post(
        "/auth/register",
        json={
            "email": test_user.email,
            "name": "Another User",
            "password": "password123"
        }
    )
    assert response.status_code == 400

def test_login_success(client: TestClient, test_user: User):
    """Test successful login"""
    response = client.post(
        "/auth/token",
        data={"username": test_user.email, "password": "testpass123"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_wrong_password(client: TestClient, test_user: User):
    """Test login with wrong password"""
    response = client.post(
        "/auth/token",
        data={"username": test_user.email, "password": "wrongpassword"}
    )
    assert response.status_code == 401

def test_login_nonexistent_user(client: TestClient):
    """Test login with non-existent user"""
    response = client.post(
        "/auth/token",
        data={"username": "nobody@example.com", "password": "password"}
    )
    assert response.status_code == 401
```

---

## Running Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=. --cov-report=html

# Specific test file
pytest tests/test_tasks.py

# Specific test
pytest tests/test_tasks.py::test_create_task_success

# Verbose output
pytest -v

# Stop on first failure
pytest -x
```

---

## Quality Checklist

- [ ] Test fixtures in conftest.py
- [ ] In-memory test database
- [ ] Test isolation (clean DB per test)
- [ ] Success cases tested
- [ ] Error cases tested (404, 401, 422)
- [ ] Authentication tested if required
- [ ] Edge cases covered
- [ ] Clear test names (test_operation_condition)
- [ ] Assertions check status code and data
- [ ] No test interdependencies

---

## Reference Files

| File | When to Read |
|------|--------------|
| `references/pytest-patterns.md` | Pytest best practices and patterns |
| `references/test-isolation.md` | Database isolation techniques |
