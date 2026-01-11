# Pydantic Validation Patterns for FastAPI

Advanced validation patterns for request and response models.

## Basic Field Validation

```python
from pydantic import BaseModel, Field

class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    priority: int = Field(ge=1, le=5, description="Priority from 1 (low) to 5 (high)")
    status: str = Field(pattern="^(todo|in_progress|done)$")
    due_date: datetime | None = None
```

## Common Validation Patterns

### String Validation

```python
from pydantic import BaseModel, Field, field_validator

class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=1000)
    email: str = Field(pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')

    @field_validator('title')
    @classmethod
    def title_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Title cannot be empty or whitespace')
        return v.strip()
```

### Date/Time Validation
```python
from datetime import datetime
from pydantic import field_validator

class TaskCreate(BaseModel):
    title: str
    due_date: datetime | None = None

    @field_validator('due_date')
    @classmethod
    def validate_due_date(cls, v):
        if v and v < datetime.now(timezone.utc):
            raise ValueError('Due date must be in the future')
        return v
```

---

## 2. Custom Validators

### Field Validator
```python
from pydantic import field_validator

class TaskCreate(BaseModel):
    title: str
    status: str

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        allowed = ['todo', 'in_progress', 'done']
        if v not in allowed:
            raise ValueError(f"Status must be one of: {', '.join(allowed)}")
        return v
```

### Model Validator
```python
from pydantic import model_validator

class TaskCreate(BaseModel):
    start_date: datetime
    due_date: datetime

    @model_validator(mode='after')
    def validate_dates(self):
        if self.due_date < self.start_date:
            raise ValueError("Due date must be after start date")
        return self
```

---

## Validation Patterns

### Email Validation
```python
from pydantic import EmailStr, Field

class UserCreate(BaseModel):
    email: EmailStr  # Built-in email validation
```

### String Constraints
```python
class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    status: str = Field(pattern="^(todo|in_progress|done)$")
```

### Numeric Constraints
```python
class TaskCreate(BaseModel):
    priority: int = Field(ge=1, le=5)  # 1 to 5
    progress: int = Field(ge=0, le=100)  # 0-100%
```

### List Validation
```python
from typing import List

class TaskCreate(BaseModel):
    title: str
    tags: List[str] = Field(default=[], max_length=10)  # Max 10 tags
    priority: int = Field(ge=1, le=5)
```

### Custom Validators
```python
from pydantic import field_validator, BaseModel
from datetime import datetime

class TaskCreate(BaseModel):
    title: str
    due_date: datetime | None = None

    @field_validator('due_date')
    @classmethod
    def due_date_must_be_future(cls, v):
        if v and v < datetime.now():
            raise ValueError('Due date must be in the future')
        return v
```

---

## Summary

Use the right status code for the situation. When in doubt:
- Success with data? → 200
- Created something? → 201
- Client sent bad data? → 400
- Not logged in? → 401
- Logged in but no access? → 403
- Not found? → 404
- Duplicate? → 409
- Server error? → 500
