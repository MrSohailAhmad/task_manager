# SQLModel Validation Patterns

## Field-Level Validation

### Using field_validator

```python
from pydantic import field_validator

class TaskBase(SQLModel):
    title: str = Field(max_length=100)
    priority: int = Field(ge=1, le=5)

    @field_validator('title')
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Title cannot be empty or whitespace')
        return v.strip()

    @field_validator('priority')
    @classmethod
    def priority_in_range(cls, v: int) -> int:
        if v < 1 or v > 5:
            raise ValueError('Priority must be between 1 and 5')
        return v
```

## Model-Level Validation

### Using model_validator

```python
from pydantic import model_validator
from datetime import datetime

class TaskBase(SQLModel):
    start_date: datetime
    due_date: datetime

    @model_validator(mode='after')
    def validate_dates(self):
        if self.due_date < self.start_date:
            raise ValueError('Due date must be after start date')
        return self
```

## Common Validation Patterns

### Date Validation

```python
from datetime import datetime, timezone

class TaskBase(SQLModel):
    due_date: Optional[datetime] = None

    @field_validator('due_date')
    @classmethod
    def due_date_must_be_future(cls, v):
        if v and v < datetime.now(timezone.utc):
            raise ValueError('Due date must be in the future')
        return v
```

### Email Validation

```python
from pydantic import EmailStr

class UserBase(SQLModel):
    email: EmailStr  # Built-in email validation
```

### String Constraints

```python
class TaskBase(SQLModel):
    title: str = Field(min_length=1, max_length=100)
    slug: str = Field(pattern=r'^[a-z0-9-]+$')
```

### Enum Validation

```python
from enum import Enum

class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"

class TaskBase(SQLModel):
    status: TaskStatus = Field(default=TaskStatus.TODO)
```

### URL Validation

```python
from pydantic import HttpUrl

class TaskBase(SQLModel):
    url: Optional[HttpUrl] = None
```

### Custom Complex Validation

```python
class TaskBase(SQLModel):
    password: str

    @field_validator('password')
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain a number')
        return v
```

## Best Practices

1. **Use Built-in Constraints First**
   ```python
   # ✅ Prefer built-in
   priority: int = Field(ge=1, le=5)

   # ❌ Avoid custom validator for simple constraints
   @field_validator('priority')
   @classmethod
   def validate_priority(cls, v):
       if v < 1 or v > 5:
           raise ValueError('Invalid priority')
       return v
   ```

2. **Provide Clear Error Messages**
   ```python
   # ✅ Clear message
   raise ValueError('Due date must be in format YYYY-MM-DD')

   # ❌ Vague message
   raise ValueError('Invalid date')
   ```

3. **Validate on Create, Not on Table Model**
   ```python
   # ✅ Validate in Base model (used by Create/Update)
   class TaskBase(SQLModel):
       @field_validator('title')
       @classmethod
       def validate_title(cls, v):
           return v.strip()

   class Task(TaskBase, table=True):
       id: Optional[int] = Field(default=None, primary_key=True)

   class TaskCreate(TaskBase):
       pass  # Inherits validation
   ```

4. **Strip Whitespace**
   ```python
   @field_validator('title')
   @classmethod
   def strip_title(cls, v: str) -> str:
       return v.strip()
   ```
