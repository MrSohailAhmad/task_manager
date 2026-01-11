from datetime import datetime, timezone, timedelta
from sqlmodel import Session, select
from models import Task

def get_daily_brief(session: Session):
    """
    Skill: Provides a summary of tasks due today or overdue.
    """
    now = datetime.now(timezone.utc)
    today_end = now + timedelta(days=1)
    
    statement = select(Task).where(
        Task.status != "completed",
        Task.due_date <= today_end
    ).order_by(Task.due_date)
    
    tasks = session.exec(statement).all()
    
    if not tasks:
        return "You're all caught up! No tasks due today."
        
    brief = f"Good morning! You have {len(tasks)} tasks needing attention today:\n"
    for task in tasks:
        due_str = "Overdue!" if task.due_date and task.due_date.replace(tzinfo=timezone.utc) < now else "Due today"
        brief += f"- [{task.priority}] {task.title} ({due_str})\n"
        
    return brief
