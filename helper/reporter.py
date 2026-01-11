from sqlmodel import Session, select
from models import Task

def generate_markdown_report(session: Session):
    """
    Skill: Generates a beautiful Markdown summary of all active tasks.
    """
    statement = select(Task).order_by(Task.priority.desc(), Task.due_date.asc())
    tasks = session.exec(statement).all()
    
    report = "# Task Management Report\n\n"
    report += f"Generated on: {Session}\n\n" # Placeholder for time
    
    status_emoji = {
        "todo": "📅",
        "in_progress": "🚧",
        "completed": "✅",
        "overdue": "🚨"
    }
    
    report += "| Status | Priority | Title | Due Date |\n"
    report += "| --- | --- | --- | --- |\n"
    
    for task in tasks:
        emoji = status_emoji.get(task.status, "📝")
        due = task.due_date.strftime("%Y-%m-%d %H:%M") if task.due_date else "No deadline"
        report += f"| {emoji} {task.status} | {'⭐' * task.priority} | {task.title} | {due} |\n"
        
    return report
