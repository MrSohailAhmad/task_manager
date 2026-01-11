import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from datetime import datetime, timedelta, timezone
from models import Task
from skills.priority import auto_prioritize_tasks
from skills.cleanup import archive_completed_tasks
from skills.search import advanced_search
from skills.daily_brief import get_daily_brief

@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

def test_priority_skill(session: Session):
    now = datetime.now(timezone.utc)
    task1 = Task(title="Due soon", due_date=now + timedelta(hours=1), priority=1)
    task2 = Task(title="Due later", due_date=now + timedelta(days=5), priority=1)
    session.add(task1)
    session.add(task2)
    session.commit()
    
    updated = auto_prioritize_tasks(session)
    assert updated >= 1
    session.refresh(task1)
    assert task1.priority == 5

def test_cleanup_skill(session: Session):
    now = datetime.now(timezone.utc)
    old_task = Task(
        title="Old", 
        status="completed", 
        updated_at=now - timedelta(days=10)
    )
    new_task = Task(
        title="New", 
        status="completed", 
        updated_at=now - timedelta(days=1)
    )
    session.add(old_task)
    session.add(new_task)
    session.commit()
    
    deleted = archive_completed_tasks(session, days_old=7)
    assert deleted == 1
    
def test_search_skill(session: Session):
    session.add(Task(title="Buy Milk", description="From the store"))
    session.add(Task(title="Work", description="On the project"))
    session.commit()
    
    results = advanced_search(session, "Milk")
    assert len(results) == 1
    assert results[0].title == "Buy Milk"

def test_daily_brief_skill(session: Session):
    now = datetime.now(timezone.utc)
    session.add(Task(title="Urgent", due_date=now - timedelta(hours=1), status="todo"))
    session.commit()
    
    brief = get_daily_brief(session)
    assert "Urgent" in brief
    assert "Overdue" in brief
