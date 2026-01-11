from sqlmodel import Session, select, or_
from models import Task

def advanced_search(session: Session, query: str):
    """
    Skill: Searches for tasks matching a query in title or description.
    """
    statement = select(Task).where(
        or_(
            Task.title.contains(query),
            Task.description.contains(query)
        )
    )
    results = session.exec(statement).all()
    return results
