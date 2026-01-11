import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from main import app, get_session
from models import Task

@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session
    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

def test_create_task(client: TestClient):
    response = client.post(
        "/tasks/", json={"title": "Test Task", "description": "A test task", "priority": 3}
    )
    data = response.json()
    assert response.status_code == 200
    assert data["title"] == "Test Task"
    assert data["priority"] == 3
    assert "id" in data

def test_read_tasks(client: TestClient):
    client.post("/tasks/", json={"title": "Task 1", "priority": 1})
    client.post("/tasks/", json={"title": "Task 2", "priority": 2})
    
    response = client.get("/tasks/")
    data = response.json()
    assert response.status_code == 200
    assert len(data) == 2

def test_read_task(client: TestClient):
    response = client.post("/tasks/", json={"title": "Single Task"})
    task_id = response.json()["id"]
    
    response = client.get(f"/tasks/{task_id}")
    data = response.json()
    assert response.status_code == 200
    assert data["title"] == "Single Task"

def test_update_task(client: TestClient):
    response = client.post("/tasks/", json={"title": "Old Title"})
    task_id = response.json()["id"]
    
    response = client.patch(f"/tasks/{task_id}", json={"title": "New Title"})
    data = response.json()
    assert response.status_code == 200
    assert data["title"] == "New Title"

def test_delete_task(client: TestClient):
    response = client.post("/tasks/", json={"title": "To Delete"})
    task_id = response.json()["id"]
    
    response = client.delete(f"/tasks/{task_id}")
    assert response.status_code == 200
    
    response = client.get(f"/tasks/{task_id}")
    assert response.status_code == 404
