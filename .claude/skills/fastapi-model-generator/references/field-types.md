# SQLModel Field Types Reference

## Basic Types

| Python Type | Database Type | Example |
|-------------|---------------|---------|
| `str` | VARCHAR | `name: str` |
| `int` | INTEGER | `age: int` |
| `float` | FLOAT | `price: float` |
| `bool` | BOOLEAN | `is_active: bool` |
| `datetime` | DATETIME | `created_at: datetime` |
| `date` | DATE | `birth_date: date` |
| `Decimal` | DECIMAL | `amount: Decimal` |

## Field Constraints

### String Fields

```python
# Basic string
name: str

# With max length
title: str = Field(max_length=100)

# With index
email: str = Field(index=True, unique=True)

# Optional string
description: Optional[str] = None

# With pattern validation
status: str = Field(pattern="^(todo|done)$")
```

### Integer Fields

```python
# Primary key
id: Optional[int] = Field(default=None, primary_key=True)

# With constraints
priority: int = Field(ge=1, le=5)  # Between 1 and 5
age: int = Field(gt=0, lt=150)  # Greater than 0, less than 150

# Foreign key
user_id: Optional[int] = Field(default=None, foreign_key="user.id")
```

### Boolean Fields

```python
# Default True
is_active: bool = Field(default=True)

# Default False
is_deleted: bool = Field(default=False)

# Optional boolean
is_verified: Optional[bool] = None
```

### DateTime Fields

```python
from datetime import datetime

# Auto-set on creation
created_at: datetime = Field(default_factory=datetime.utcnow)

# Optional datetime
due_date: Optional[datetime] = None

# With timezone
from datetime import timezone
created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

### Decimal Fields

```python
from decimal import Decimal

# For precise numbers (money)
price: Decimal = Field(max_digits=10, decimal_places=2)
amount: Decimal
```

### Enum Fields

```python
from enum import Enum

class Status(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"

class Task(SQLModel, table=True):
    status: Status = Field(default=Status.TODO)
```

### JSON Fields

```python
from typing import Dict, Any
from sqlalchemy import Column
from sqlalchemy.types import JSON

class Task(SQLModel, table=True):
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON)
    )
```

### List Fields (JSON)

```python
from typing import List

class Task(SQLModel, table=True):
    tags: List[str] = Field(default_factory=list, sa_column=Column(JSON))
```

## Field Parameters

### Common Parameters

```python
# Default value
status: str = Field(default="active")

# Default factory (for mutable defaults)
tags: List[str] = Field(default_factory=list)

# Max/Min length
title: str = Field(min_length=1, max_length=100)

# Greater than / Less than
priority: int = Field(ge=1, le=5)  # >=1, <=5
age: int = Field(gt=0, lt=150)     # >0, <150

# Index
email: str = Field(index=True)

# Unique constraint
email: str = Field(unique=True)

# Primary key
id: Optional[int] = Field(default=None, primary_key=True)

# Foreign key
user_id: Optional[int] = Field(default=None, foreign_key="user.id")

# Description (for API docs)
priority: int = Field(description="Priority from 1 (low) to 5 (high)")
```

## Optional vs Required

```python
# Required fields (no default, not Optional)
title: str
priority: int

# Optional with default
status: str = Field(default="todo")

# Optional without default (nullable)
description: Optional[str] = None
due_date: Optional[datetime] = None

# Optional with default
is_active: Optional[bool] = Field(default=True)
```

## Auto-incrementing ID

```python
# Standard auto-increment primary key
id: Optional[int] = Field(default=None, primary_key=True)
```

## UUID Primary Key

```python
from uuid import UUID, uuid4

class Task(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
```

## Timestamps Pattern

```python
from datetime import datetime

class TaskBase(SQLModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Task(TaskBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
```

## Best Practices

1. **Use Optional for nullable fields**
   ```python
   description: Optional[str] = None  # ✅
   description: str = None  # ❌ Type error
   ```

2. **Use default_factory for mutable defaults**
   ```python
   tags: List[str] = Field(default_factory=list)  # ✅
   tags: List[str] = []  # ❌ Shared across instances
   ```

3. **Add indexes to frequently queried fields**
   ```python
   email: str = Field(index=True, unique=True)  # ✅
   status: str = Field(index=True)  # ✅ for filtering
   ```

4. **Use max_length for strings**
   ```python
   title: str = Field(max_length=100)  # ✅ Prevents huge strings
   ```

5. **Use ge/le for bounded numbers**
   ```python
   priority: int = Field(ge=1, le=5)  # ✅ Enforces range
   ```
