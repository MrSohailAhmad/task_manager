# SQLModel Anti-Patterns

## 1. Mutable Defaults

**❌ ANTI-PATTERN**
```python
class Task(SQLModel, table=True):
    tags: List[str] = []  # Same list shared across ALL instances!
```

**✅ CORRECT**
```python
class Task(SQLModel, table=True):
    tags: List[str] = Field(default_factory=list)
```

---

## 2. Missing Optional for Nullable Fields

**❌ ANTI-PATTERN**
```python
class Task(SQLModel, table=True):
    description: str = None  # Type error!
```

**✅ CORRECT**
```python
class Task(SQLModel, table=True):
    description: Optional[str] = None
```

---

## 3. Relationships Without back_populates

**❌ ANTI-PATTERN**
```python
class Task(SQLModel, table=True):
    owner: Optional["User"] = Relationship()  # One-way only
```

**✅ CORRECT**
```python
class User(SQLModel, table=True):
    tasks: List["Task"] = Relationship(back_populates="owner")

class Task(SQLModel, table=True):
    owner: Optional[User] = Relationship(back_populates="tasks")
```

---

## 4. Including Relationships in Create Schemas

**❌ ANTI-PATTERN**
```python
class TaskCreate(TaskBase):
    owner: User  # Nested object - hard to use!
```

**✅ CORRECT**
```python
class TaskCreate(TaskBase):
    user_id: Optional[int] = None  # Just the ID
```

---

## 5. No Primary Key

**❌ ANTI-PATTERN**
```python
class Task(SQLModel, table=True):
    title: str  # No primary key!
```

**✅ CORRECT**
```python
class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
```

---

## 6. Forgetting Foreign Key Index

**❌ ANTI-PATTERN**
```python
class Task(SQLModel, table=True):
    user_id: Optional[int] = None  # No foreign key constraint
```

**✅ CORRECT**
```python
class Task(SQLModel, table=True):
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
```

---

## 7. No max_length on Strings

**❌ ANTI-PATTERN**
```python
class Task(SQLModel, table=True):
    title: str  # Unlimited length!
```

**✅ CORRECT**
```python
class Task(SQLModel, table=True):
    title: str = Field(max_length=100)
```

---

## 8. Missing Indexes on Filtered Fields

**❌ ANTI-PATTERN**
```python
class Task(SQLModel, table=True):
    status: str  # Frequently filtered, no index
```

**✅ CORRECT**
```python
class Task(SQLModel, table=True):
    status: str = Field(index=True)
```

---

## 9. Incorrect Update Model

**❌ ANTI-PATTERN**
```python
class TaskUpdate(TaskBase):  # All fields required for update!
    pass
```

**✅ CORRECT**
```python
class TaskUpdate(SQLModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    # All fields optional for partial updates
```

---

## 10. Missing Timestamps

**❌ ANTI-PATTERN**
```python
class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    # No created_at/updated_at
```

**✅ CORRECT**
```python
class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

---

## 11. N+1 Query Problem

**❌ ANTI-PATTERN**
```python
tasks = session.exec(select(Task)).all()
for task in tasks:
    print(task.owner.name)  # Separate query for each task!
```

**✅ CORRECT**
```python
from sqlalchemy.orm import selectinload

statement = select(Task).options(selectinload(Task.owner))
tasks = session.exec(statement).all()
for task in tasks:
    print(task.owner.name)  # Already loaded
```

---

## 12. Using Dict Instead of Model Validation

**❌ ANTI-PATTERN**
```python
task = Task(**request_dict)  # No validation!
```

**✅ CORRECT**
```python
task_create = TaskCreate(**request_dict)
task = Task.model_validate(task_create)
```

---

## Summary Table

| Anti-Pattern | Issue | Fix |
|--------------|-------|-----|
| Mutable defaults | Shared state | Use default_factory |
| Missing Optional | Type errors | Add Optional for nullable |
| No back_populates | One-way relationship | Add on both sides |
| Relationships in schemas | API complexity | Use IDs only |
| No primary key | Can't identify rows | Add id field |
| No foreign key | No referential integrity | Add foreign_key |
| No max_length | Unlimited strings | Add max_length |
| No indexes | Slow queries | Index filtered fields |
| Wrong Update model | Can't partial update | All fields Optional |
| No timestamps | Can't track changes | Add created_at/updated_at |
| N+1 queries | Performance | Use selectinload |
| Skip validation | Security issues | Use model_validate |
