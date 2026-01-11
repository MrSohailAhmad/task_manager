# SQLModel Relationships

## Relationship Types

### One-to-Many

**Example**: One user has many tasks

```python
from typing import List, Optional
from sqlmodel import Field, SQLModel, Relationship

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

    # One user has many tasks
    tasks: List["Task"] = Relationship(back_populates="owner")

class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str

    # Foreign key to user
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")

    # Many tasks belong to one user
    owner: Optional[User] = Relationship(back_populates="tasks")
```

**Usage**:
```python
# Create user with tasks
user = User(name="John")
task1 = Task(title="Task 1", owner=user)
task2 = Task(title="Task 2", owner=user)

session.add(user)
session.commit()

# Access relationship
user_tasks = user.tasks  # List of Task objects
task_owner = task1.owner  # User object
```

### One-to-One

**Example**: User has one profile

```python
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

    # One-to-one relationship
    profile: Optional["Profile"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"uselist": False}
    )

class Profile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    bio: str

    user_id: int = Field(foreign_key="user.id", unique=True)
    user: User = Relationship(back_populates="profile")
```

### Many-to-Many

**Example**: Tasks can have multiple tags, tags can belong to multiple tasks

```python
# Link table
class TaskTagLink(SQLModel, table=True):
    task_id: Optional[int] = Field(
        default=None,
        foreign_key="task.id",
        primary_key=True
    )
    tag_id: Optional[int] = Field(
        default=None,
        foreign_key="tag.id",
        primary_key=True
    )

class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str

    # Many-to-many with tags
    tags: List["Tag"] = Relationship(
        back_populates="tasks",
        link_model=TaskTagLink
    )

class Tag(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True)

    # Many-to-many with tasks
    tasks: List["Task"] = Relationship(
        back_populates="tags",
        link_model=TaskTagLink
    )
```

**Usage**:
```python
# Create task with tags
task = Task(title="Build feature")
tag1 = Tag(name="urgent")
tag2 = Tag(name="backend")

task.tags = [tag1, tag2]
session.add(task)
session.commit()

# Access relationships
task_tags = task.tags  # List of Tag objects
tag_tasks = tag1.tasks  # List of Task objects
```

## Advanced Patterns

### Self-Referential Relationship

**Example**: Tasks can have subtasks

```python
class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str

    # Parent task (optional)
    parent_id: Optional[int] = Field(default=None, foreign_key="task.id")

    # Relationships
    parent: Optional["Task"] = Relationship(
        back_populates="subtasks",
        sa_relationship_kwargs={
            "remote_side": "Task.id"
        }
    )
    subtasks: List["Task"] = Relationship(back_populates="parent")
```

### Cascade Delete

**Example**: Delete all tasks when user is deleted

```python
from sqlmodel import Relationship

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

    tasks: List["Task"] = Relationship(
        back_populates="owner",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    owner: Optional[User] = Relationship(back_populates="tasks")
```

### Eager Loading

By default, relationships are lazy-loaded. Use `selectinload` for eager loading:

```python
from sqlmodel import select
from sqlalchemy.orm import selectinload

# Eager load tasks with owner
statement = select(Task).options(selectinload(Task.owner))
tasks = session.exec(statement).all()

# No additional query needed
for task in tasks:
    print(task.owner.name)  # Already loaded
```

## Relationship Parameters

### back_populates

Links both sides of the relationship:

```python
# Must be set on both sides
owner: Optional[User] = Relationship(back_populates="tasks")
tasks: List["Task"] = Relationship(back_populates="owner")
```

### link_model

For many-to-many relationships:

```python
tags: List["Tag"] = Relationship(
    back_populates="tasks",
    link_model=TaskTagLink
)
```

### sa_relationship_kwargs

Pass additional SQLAlchemy relationship arguments:

```python
# One-to-one
profile: Optional["Profile"] = Relationship(
    back_populates="user",
    sa_relationship_kwargs={"uselist": False}
)

# Cascade delete
tasks: List["Task"] = Relationship(
    back_populates="owner",
    sa_relationship_kwargs={"cascade": "all, delete-orphan"}
)

# Self-referential
parent: Optional["Task"] = Relationship(
    back_populates="subtasks",
    sa_relationship_kwargs={"remote_side": "Task.id"}
)
```

## API Schemas with Relationships

### Avoid Circular Imports

```python
# models.py

# Base models (no relationships in schemas)
class UserBase(SQLModel):
    name: str

class TaskBase(SQLModel):
    title: str
    user_id: Optional[int] = None

# Table models (with relationships)
class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tasks: List["Task"] = Relationship(back_populates="owner")

class Task(TaskBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    owner: Optional[User] = Relationship(back_populates="tasks")

# API schemas (no relationships, IDs only)
class UserCreate(UserBase):
    pass

class TaskCreate(TaskBase):
    pass

class UserRead(UserBase):
    id: int

class TaskRead(TaskBase):
    id: int
    user_id: Optional[int]
```

### Including Related Data in Responses

Create separate schemas for nested responses:

```python
class TaskRead(TaskBase):
    id: int
    user_id: Optional[int]

class UserRead(UserBase):
    id: int

class UserReadWithTasks(UserRead):
    tasks: List[TaskRead] = []
```

Usage in endpoint:

```python
@app.get("/users/{user_id}", response_model=UserReadWithTasks)
def get_user(user_id: int, session: Session = Depends(get_session)):
    statement = select(User).where(User.id == user_id).options(
        selectinload(User.tasks)
    )
    user = session.exec(statement).first()
    if not user:
        raise HTTPException(404, "User not found")
    return user
```

## Best Practices

1. **Always use back_populates on both sides**
   ```python
   # ✅ Correct
   owner: Optional[User] = Relationship(back_populates="tasks")
   tasks: List["Task"] = Relationship(back_populates="owner")

   # ❌ Wrong - missing back_populates
   owner: Optional[User] = Relationship()
   ```

2. **Use Optional for nullable relationships**
   ```python
   owner: Optional[User] = Relationship(back_populates="tasks")  # ✅
   ```

3. **Forward references for circular imports**
   ```python
   tasks: List["Task"] = Relationship(back_populates="owner")  # ✅
   ```

4. **Don't include relationships in API schemas**
   ```python
   # TaskCreate schema - only IDs, no relationship objects
   class TaskCreate(TaskBase):
       user_id: Optional[int] = None  # ✅ Just the ID
   ```

5. **Use eager loading when accessing relationships**
   ```python
   # ✅ Efficient - one query
   statement = select(Task).options(selectinload(Task.owner))
   tasks = session.exec(statement).all()

   # ❌ N+1 problem - one query per task
   tasks = session.exec(select(Task)).all()
   for task in tasks:
       print(task.owner.name)  # Separate query each time
   ```

## Common Patterns

### Optional Parent (Self-referential)

```python
parent_id: Optional[int] = Field(default=None, foreign_key="task.id")
parent: Optional["Task"] = Relationship(back_populates="subtasks")
subtasks: List["Task"] = Relationship(back_populates="parent")
```

### Required Parent

```python
user_id: int = Field(foreign_key="user.id")
owner: User = Relationship(back_populates="tasks")
```

### Through Model with Extra Fields

```python
class TaskTagLink(SQLModel, table=True):
    task_id: int = Field(foreign_key="task.id", primary_key=True)
    tag_id: int = Field(foreign_key="tag.id", primary_key=True)

    # Extra fields in link table
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[int] = None
```
