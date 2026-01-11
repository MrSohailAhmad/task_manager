from datetime import datetime, timezone
from sqlmodel import Session, select
from models import Task

def auto_prioritize_tasks(session: Session):
    """
    Skill: Auto-prioritizes tasks based on due date proximity.
    Tasks due within 24 hours get priority 5 (highest).
    Tasks due within 3 days get priority 4.
    """
    now = datetime.now(timezone.utc)
    statement = select(Task).where(Task.status != "completed")
    tasks = session.exec(statement).all()
    
    updated_count = 0
    for task in tasks:
        if task.due_date:
            # Ensure due_date is timezone-aware for comparison if it's not
            due_date = task.due_date
            if due_date.tzinfo is None:
                due_date = due_date.replace(tzinfo=timezone.utc)
                
            diff = (due_date - now).total_seconds()
            
            new_priority = task.priority
            if diff < 86400: # 24 hours
                new_priority = 5
            elif diff < 259200: # 3 days
                new_priority = 4
            elif diff < 604800: # 1 week
                new_priority = 3
            
            if new_priority != task.priority:
                task.priority = new_priority
                session.add(task)
                updated_count += 1
    
    session.commit()
    return updated_count
