
from datetime import datetime, timezone
from sqlmodel import Session, select, delete
from models import Task

def archive_completed_tasks(session: Session, days_old: int = 7):
    """
    Skill: Archives (deletes) tasks that were completed more than X days ago.
    This maintains database hygiene.
    """
    now = datetime.now(timezone.utc)
    # This is a simplified version using delete
    statement = select(Task).where(Task.status == "completed")
    tasks = session.exec(statement).all()
    
    deleted_count = 0
    for task in tasks:
        # Assuming updated_at tracks completion time or at least last change
        if task.updated_at.tzinfo is None:
            updated_at = task.updated_at.replace(tzinfo=timezone.utc)
        else:
            updated_at = task.updated_at
            
        diff = (now - updated_at).days
        if diff >= days_old:
            session.delete(task)
            deleted_count += 1
            
    session.commit()
    return deleted_count
