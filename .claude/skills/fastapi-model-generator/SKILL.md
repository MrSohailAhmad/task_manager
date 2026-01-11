---
name: fastapi-model-generator
description: |
  Generates SQLModel database models with relationships, Pydantic schemas for API validation, and proper table configurations.
  This skill should be used when developers need to create new database models, update existing models, or add relationships between models in FastAPI applications using SQLModel.
---

# FastAPI Model Generator

Generates SQLModel/Pydantic models for FastAPI applications with database tables.

## What This Skill Does

- Creates SQLModel table models with proper field types
- Generates Pydantic schemas (Create, Read, Update)
- Configures relationships between models
- Adds proper indexes and constraints
- Implements validation rules
- Follows SQLModel/Pydantic best practices

## What This Skill Does NOT Do

- Create database migrations (recommend using Alembic)
- Generate API endpoints (use fastapi-endpoint-builder)
- Set up database connection
- Create database tables at runtime (production should use migrations)

---

## Before Implementation

Gather context to ensure successful implementation:

| Source | Gather |
|--------|--------|
| **Codebase** | Existing models structure, naming conventions, relationship patterns |
| **Conversation** | Model requirements, fields, validations, relationships |
| **Skill References** | SQLModel patterns from `references/` (best practices, relationships, field types) |
| **User Guidelines** | Project-specific conventions, database standards |

Ensure all required context is gathered before implementing.
Only ask user for THEIR specific requirements (domain expertise is in this skill).

---

## Clarifications

Ask user about model specifics:

1. **Model Purpose** - What resource/entity does this model represent?
2. **Fields** - What fields should the model have? (name, type, constraints)
3. **Relationships** - Does it relate to other models? (one-to-many, many-to-many)
4. **Validations** - Any special validation rules or constraints?

---

## Implementation Workflow

### 1. Analyze Existing Models

Search codebase for:
- Existing models file (usually `models.py`)
- Field naming conventions (snake_case, camelCase)
- Timestamp patterns (created_at, updated_at)
- ID field patterns (autoincrement, UUID)
- Relationship patterns

### 2. Determine Model Structure

```
Base Model (SQLModel with fields)
    ↓
Table Model (with table=True)
    ↓
API Schemas (Create, Read, Update)
```

### 3. Generate Models

Follow this pattern:

```python
from sqlmodel import Field, SQLModel, Relationship
from typing import Optional
from datetime import datetime

# Base model with shared fields
class TaskBase(SQLModel):
    title: str = Field(index=True, max_length=100)
    description: Optional[str] = Field(default=None, max_length=1000)
    status: str = Field(default="todo", index=True)
    priority: int = Field(default=1, ge=1, le=5)
    due_date: Optional[datetime] = None

# Table model
class Task(TaskBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    # owner: Optional["User"] = Relationship(back_populates="tasks")

# API Schemas
class TaskCreate(TaskBase):
    pass

class TaskRead(TaskBase):
    id: int
    created_at: datetime
    updated_at: datetime

class TaskUpdate(SQLModel):
    title: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
    due_date: Optional[datetime] = None
```

### 4. Add Field Types and Constraints

Common field patterns:

```python
# String fields
title: str = Field(max_length=100, index=True)
email: str = Field(unique=True, index=True)
status: str = Field(default="active")

# Integer fields
id: Optional[int] = Field(default=None, primary_key=True)
priority: int = Field(default=1, ge=1, le=5)

# Boolean fields
is_active: bool = Field(default=True)

# DateTime fields
created_at: datetime = Field(default_factory=datetime.utcnow)
updated_at: datetime = Field(default_factory=datetime.utcnow)

# Optional fields
description: Optional[str] = Field(default=None)
due_date: Optional[datetime] = None

# Foreign keys
user_id: Optional[int] = Field(default=None, foreign_key="user.id")
```

### 5. Add Relationships

See `references/relationships.md` for detailed patterns.

**One-to-Many**:
```python
# User has many tasks
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tasks: List["Task"] = Relationship(back_populates="owner")

class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    owner: Optional[User] = Relationship(back_populates="tasks")
```

**Many-to-Many**:
```python
# Tasks and Tags (with link table)
class TaskTagLink(SQLModel, table=True):
    task_id: Optional[int] = Field(default=None, foreign_key="task.id", primary_key=True)
    tag_id: Optional[int] = Field(default=None, foreign_key="tag.id", primary_key=True)

class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tags: List["Tag"] = Relationship(back_populates="tasks", link_model=TaskTagLink)

class Tag(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tasks: List["Task"] = Relationship(back_populates="tags", link_model=TaskTagLink)
```

### 6. Add Validations

```python
from pydantic import field_validator

class TaskBase(SQLModel):
    title: str = Field(max_length=100)
    due_date: Optional[datetime] = None

    @field_validator('title')
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()

    @field_validator('due_date')
    @classmethod
    def validate_due_date(cls, v):
        if v and v < datetime.now():
            raise ValueError('Due date must be in the future')
        return v
```

### 7. Configure Table

```python
class Task(TaskBase, table=True):
    __tablename__ = "tasks"  # Optional: override table name

    id: Optional[int] = Field(default=None, primary_key=True)

    class Config:
        # Enable ORM mode for compatibility
        from_attributes = True
```

---

## Quality Checklist

Before delivering models, verify:

- [ ] Base model with shared fields
- [ ] Table model with `table=True`
- [ ] API schemas (Create, Read, Update) properly defined
- [ ] Primary key field (usually `id`)
- [ ] Timestamps (created_at, updated_at) if needed
- [ ] Indexes on frequently queried fields
- [ ] Foreign keys for relationships
- [ ] Relationships with back_populates
- [ ] Field constraints (max_length, ge, le)
- [ ] Optional fields properly typed
- [ ] Validators for business logic
- [ ] Follows existing code style
- [ ] Update model added to models file

---

## Common Patterns

### Soft Delete
```python
class Task(TaskBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    deleted_at: Optional[datetime] = None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
```

### Audit Fields
```python
class TaskBase(SQLModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[int] = Field(default=None, foreign_key="user.id")
    updated_by: Optional[int] = Field(default=None, foreign_key="user.id")
```

### Enum Fields
```python
from enum import Enum

class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"

class TaskBase(SQLModel):
    status: TaskStatus = Field(default=TaskStatus.TODO)
```

### JSON Fields
```python
from typing import Dict, Any

class Task(TaskBase, table=True):
    metadata: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
```

---

## Anti-Patterns to Avoid

❌ **Mutable defaults**
```python
tags: List[str] = []  # Same list shared across instances!
```

✅ **Correct**
```python
tags: List[str] = Field(default_factory=list)
```

❌ **Missing Optional for nullable fields**
```python
description: str = None  # Type mismatch!
```

✅ **Correct**
```python
description: Optional[str] = None
```

❌ **Relationships without back_populates**
```python
owner: Optional["User"] = Relationship()  # One-way only
```

✅ **Correct**
```python
owner: Optional["User"] = Relationship(back_populates="tasks")
```

See `references/anti-patterns.md` for complete list.

---

## Reference Files

| File | When to Read |
|------|--------------|
| `references/field-types.md` | Field type reference and constraints |
| `references/relationships.md` | Relationship patterns and configurations |
| `references/anti-patterns.md` | Common mistakes and how to avoid them |
| `references/validation.md` | Advanced validation patterns |
