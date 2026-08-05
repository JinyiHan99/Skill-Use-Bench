---
name: python-anti-patterns
description: 'Use this skill when writing or reviewing Python code. Ensures code avoids common anti-patterns including bare exceptions, hardcoded configuration, missing type hints, blocking calls in async, and improper resource management.'
---

# Python Anti-Patterns Checklist

## Overview

This skill defines a mandatory checklist of Python anti-patterns that must be avoided in all production code. Each pattern represents a concrete code smell that leads to maintenance problems, security vulnerabilities, or runtime failures. Code that violates these patterns must be refactored before being considered complete.

## When to Use

- When writing any new Python module, class, or function
- When reviewing or refactoring existing Python code
- When fixing bugs (apply anti-pattern fixes to touched code)
- When adding features to existing modules

## Anti-Pattern Rules

### AP-1: No Bare Exception Handling

Never write `except Exception: pass` or bare `except:` blocks. Every exception handler must:
1. Catch a specific exception type (not `Exception` or `BaseException`)
2. Either handle it meaningfully, re-raise it, or log it with context

```python
# WRONG — swallows all errors silently
try:
    process_data(input)
except Exception:
    pass

# WRONG — catches too broadly
try:
    parse_config(path)
except Exception as e:
    logger.error(e)

# CORRECT — specific exception with meaningful handling
try:
    parse_config(path)
except FileNotFoundError:
    logger.warning(f"Config not found at {path}, using defaults")
    return default_config()
except json.JSONDecodeError as e:
    raise ConfigurationError(f"Invalid JSON in {path}: {e}") from e
```

### AP-2: No Hardcoded Configuration or Secrets

Never embed configuration values, URLs, passwords, API keys, or connection strings directly in source code. All configuration must come from environment variables, configuration files, or a settings management system.

```python
# WRONG — hardcoded values in source
DATABASE_URL = "postgresql://admin:password123@localhost:5432/mydb"
API_KEY = "sk-abc123xyz"
TIMEOUT = 30
BASE_URL = "https://api.production.example.com"

# CORRECT — externalized configuration
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    api_key: str
    timeout: int = 30
    base_url: str

    class Config:
        env_file = ".env"

settings = Settings()
```

### AP-3: All Public Functions Must Have Type Hints

Every public function (not starting with `_`) must have complete type annotations for all parameters and the return type. Use `collections.abc` types over `typing` equivalents where possible.

```python
# WRONG — no type hints
def calculate_total(items, discount):
    return sum(i.price for i in items) * (1 - discount)

# CORRECT — full type annotations
def calculate_total(items: list[Item], discount: float) -> Decimal:
    return sum(i.price for i in items) * (1 - discount)
```

### AP-4: Collections Must Have Type Parameters

All collection types must specify their element types. Never use bare `list`, `dict`, `set`, or `tuple` in annotations.

```python
# WRONG — unparameterized collections
def get_users() -> list:
    ...

def get_config() -> dict:
    ...

# CORRECT — parameterized collections
def get_users() -> list[User]:
    ...

def get_config() -> dict[str, Any]:
    ...
```

### AP-5: No Blocking Calls in Async Functions

Never use synchronous blocking calls inside `async def` functions. This blocks the event loop and defeats the purpose of async.

```python
# WRONG — blocking calls in async context
async def fetch_data(url: str) -> dict:
    response = requests.get(url)  # blocks event loop!
    time.sleep(1)  # blocks event loop!
    data = open("cache.json").read()  # blocks event loop!
    return json.loads(data)

# CORRECT — async-native alternatives
async def fetch_data(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
    await asyncio.sleep(1)
    async with aiofiles.open("cache.json") as f:
        data = await f.read()
    return json.loads(data)
```

### AP-6: Use Context Managers for Resources

All resources (files, database connections, locks, network sessions) must be managed with context managers (`with` statement). Never open a resource without ensuring it is closed.

```python
# WRONG — resource leak risk
f = open("data.csv")
content = f.read()
# f.close() might never be reached if exception occurs

conn = psycopg2.connect(dsn)
cursor = conn.cursor()
cursor.execute(query)

# CORRECT — context managers ensure cleanup
with open("data.csv") as f:
    content = f.read()

with psycopg2.connect(dsn) as conn:
    with conn.cursor() as cursor:
        cursor.execute(query)
```

### AP-7: No Exposed Internal Types in Public APIs

ORM models, internal data structures, and implementation-specific types must never be exposed in public API interfaces. Use DTOs, Pydantic models, or dataclasses for API boundaries.

```python
# WRONG — ORM model leaked to API layer
@app.get("/users/{user_id}")
def get_user(user_id: int) -> UserORM:  # exposes SQLAlchemy model
    return db.query(UserORM).get(user_id)

# CORRECT — DTO/schema at API boundary
@app.get("/users/{user_id}")
def get_user(user_id: int) -> UserResponse:  # Pydantic response model
    user = db.query(UserORM).get(user_id)
    return UserResponse.model_validate(user)
```

### AP-8: Input Validation Must Be Present

All external inputs (API requests, file contents, user inputs, environment variables) must be validated before use. Use Pydantic models or explicit validation functions.

```python
# WRONG — no input validation
def process_order(data: dict) -> Order:
    return Order(
        quantity=data["quantity"],
        price=data["price"],
    )

# CORRECT — validated input
from pydantic import BaseModel, field_validator

class OrderInput(BaseModel):
    quantity: int
    price: Decimal

    @field_validator("quantity")
    @classmethod
    def quantity_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Quantity must be positive")
        return v

def process_order(data: OrderInput) -> Order:
    return Order(quantity=data.quantity, price=data.price)
```

### AP-9: Use Exception Chaining

When catching and re-raising exceptions, always use `raise ... from e` to preserve the exception chain. Never raise a new exception without chaining to the original cause.

```python
# WRONG — original traceback lost
try:
    result = json.loads(raw_data)
except json.JSONDecodeError:
    raise ValueError("Invalid input data")  # original error is hidden

# CORRECT — exception chaining preserves context
try:
    result = json.loads(raw_data)
except json.JSONDecodeError as e:
    raise ValueError(f"Invalid input data at position {e.pos}") from e
```

### AP-10: Error Messages Must Include Context

All raised exceptions must include contextual information (variable values, file paths, identifiers) in their message to aid debugging.

```python
# WRONG — useless error message
if user is None:
    raise ValueError("User not found")

# CORRECT — includes debugging context
if user is None:
    raise ValueError(f"User not found: user_id={user_id}, source={source}")
```

### AP-11: Error Paths Must Be Tested

For every function that can raise exceptions or return error states, there must be corresponding tests using `pytest.raises` that verify the error behavior.

```python
# Required test pattern
def test_parse_config_missing_file_raises_file_not_found():
    with pytest.raises(FileNotFoundError, match="config.yaml"):
        parse_config("/nonexistent/config.yaml")

def test_process_order_negative_quantity_raises_validation_error():
    with pytest.raises(ValidationError, match="positive"):
        process_order(OrderInput(quantity=-1, price=Decimal("10.00")))
```

## Verification Checklist

Before marking code complete, verify:

- [ ] No `except Exception: pass` or bare `except:` blocks exist
- [ ] No hardcoded passwords, API keys, URLs, or connection strings in source
- [ ] All public functions have complete type annotations (parameters + return)
- [ ] All collections in type annotations are parameterized (`list[X]`, not `list`)
- [ ] No `requests.get`, `time.sleep`, or synchronous I/O in `async def` functions
- [ ] All file/connection/resource opens use `with` statements
- [ ] No ORM models exposed in API response types
- [ ] All external inputs validated with Pydantic or explicit validators
- [ ] All `raise` in `except` blocks use `from e` chaining
- [ ] All error messages include contextual variable values
- [ ] Error paths have corresponding `pytest.raises` test cases
