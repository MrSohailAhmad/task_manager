from fastapi import FastAPI, Depends, HTTPException, Query
from sqlmodel import Session, select
from typing import List
from database import engine, create_db_and_tables, get_session
from models import Task, TaskCreate, TaskRead, TaskUpdate
from datetime import datetime

from skills.priority import auto_prioritize_tasks
from skills.cleanup import archive_completed_tasks
from skills.reporter import generate_markdown_report
from skills.search import advanced_search
from skills.daily_brief import get_daily_brief

app = FastAPI(title="Task Management API", version="1.0.0", description="Task Management API")

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/datetime")
def get_current_datetime():
    """
    Get current server date and time.
    """
    current_time = datetime.now()
    return {
        "datetime": current_time.isoformat(),
        "timestamp": current_time.timestamp()
    }

# ... existing endpoints ...

@app.post("/skills/prioritize")
def run_prioritize(session: Session = Depends(get_session)):
    updated = auto_prioritize_tasks(session)
    return {"message": f"Successfully updated priority for {updated} tasks"}

@app.post("/skills/cleanup")
def run_cleanup(days: int = 7, session: Session = Depends(get_session)):
    deleted = archive_completed_tasks(session, days_old=days)
    return {"message": f"Successfully archived {deleted} old tasks"}

@app.get("/skills/report")
def get_report(session: Session = Depends(get_session)):
    report = generate_markdown_report(session)
    return {"report": report}

@app.get("/skills/search")
def run_search(q: str, session: Session = Depends(get_session)):
    results = advanced_search(session, q)
    return results

@app.get("/skills/brief")
def run_brief(session: Session = Depends(get_session)):
    brief = get_daily_brief(session)
    return {"brief": brief}

@app.post("/tasks/", response_model=TaskRead)
def create_task(task: TaskCreate, session: Session = Depends(get_session)):
    db_task = Task.model_validate(task)
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return db_task

@app.get("/tasks/", response_model=List[TaskRead])
def read_tasks(
    offset: int = 0,
    limit: int = Query(default=100, le=100),
    session: Session = Depends(get_session)
):
    tasks = session.exec(select(Task).offset(offset).limit(limit)).all()
    return tasks

@app.get("/tasks/{task_id}", response_model=TaskRead)
def read_task(task_id: int, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.patch("/tasks/{task_id}", response_model=TaskRead)
def update_task(task_id: int, task: TaskUpdate, session: Session = Depends(get_session)):
    db_task = session.get(Task, task_id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_data = task.model_dump(exclude_unset=True)
    for key, value in task_data.items():
        setattr(db_task, key, value)
    
    db_task.updated_at = datetime.utcnow()
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return db_task

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    session.delete(task)
    session.commit()
    return {"ok": True}
