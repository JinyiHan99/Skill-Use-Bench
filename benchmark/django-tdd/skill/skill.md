---
name: django-tdd
description: Django testing strategies with pytest-django, TDD methodology, factory_boy, mocking, coverage, and testing Django REST Framework APIs.
origin: ECC
---

# Django Testing with TDD

Test-driven development for Django applications using pytest, factory_boy, and Django REST Framework.

## When to Activate

- Writing new Django applications or features
- Implementing Django REST Framework APIs
- Testing Django models, views, and serializers
- Setting up testing infrastructure for Django projects
- Adding tests to existing Django code

## TDD Workflow for Django

### Red-Green-Refactor Cycle

Every new feature or bugfix follows the strict red-green-refactor discipline. The test file must be created and the failing test committed (or at minimum, shown to fail via a pytest run) before any production code is written or modified. This sequence ensures that tests are not retrofitted after the fact, which tends to produce tests that merely confirm existing behavior rather than driving design.

The workflow for each unit of work:

1. **Write the test first** — create a test function that exercises the desired behavior. Run it and confirm it fails (red). The failing output demonstrates that the test is actually checking something meaningful.

2. **Write minimal production code** — implement just enough to make the failing test pass. Do not add untested behavior.

3. **Refactor** — improve code structure while keeping all tests green. Run the full suite after each change.

This discipline applies even to trivial features. Skipping the red step ("I'll just write the code and test together") defeats the purpose because it removes the design-pressure that TDD provides.

## Setup

### pytest Configuration

All Django test suites use pytest-django as the test runner. Do not use Django's built-in unittest-based `TestCase` classes or `manage.py test`. The pytest ecosystem provides better fixture composition, parametrization, and output formatting.

```ini
# pytest.ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings.test
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --reuse-db
    --nomigrations
    --cov=apps
    --cov-report=html
    --cov-report=term-missing
    --strict-markers
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
```

### Test Settings

The test settings module must include Celery eager mode to ensure asynchronous tasks execute synchronously during tests. Without this, tests that trigger Celery tasks will silently skip the task logic, leading to false passes.

```python
# config/settings/test.py
# WARNING: This settings file is for testing ONLY.
# NEVER use it in production (DJANGO_SETTINGS_MODULE must NOT point here in prod).
from .base import *  # noqa: F403 — intentional wildcard import for settings overlay

DEBUG = False  # Keep False even in tests; True can mask template errors and hide issues

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Disable migrations for speed
class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

# Faster password hashing — MD5 is intentionally used here for speed.
# SECURITY: MD5 is cryptographically broken; this MUST NEVER be used in production.
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Email backend
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Celery must run tasks synchronously in tests to guarantee deterministic assertions.
# Omitting these settings is a common source of intermittent test failures.
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
```

### conftest.py and Fixtures

Shared test state lives in `conftest.py` using `@pytest.fixture` decorators. Do not use `setUp` / `tearDown` methods or `TestCase` class hierarchies — they create implicit coupling between tests and make fixture composition impossible.

Fixtures should be scoped appropriately: session-scoped for expensive one-time setup (like loading large datasets), function-scoped (the default) for most test data to ensure isolation.

```python
# tests/conftest.py
import pytest
from rest_framework.test import APIClient

@pytest.fixture
def api_client():
    """Provide a DRF APIClient instance."""
    return APIClient()

@pytest.fixture
def authenticated_api_client(api_client, user):
    """Provide an authenticated APIClient."""
    api_client.force_authenticate(user=user)
    return api_client
```

Note that the `user` fixture above is defined via a factory (see next section), not via `User.objects.create_user(...)` inline.

## Factory Boy for Test Data

### Why Factories, Not Manual Object Creation

All test data creation must go through factory_boy factories. Direct calls to `Model.objects.create()`, `Model.objects.create_user()`, or manual model instantiation in tests are not acceptable because:

- They scatter default values across hundreds of test files, making schema changes painful
- They obscure which fields are relevant to each test (noise vs. signal)
- They cannot express relationships between objects declaratively

When you need a model instance in a test, always call the appropriate factory. When you need to override specific fields for a particular test scenario, pass them as keyword arguments to the factory call.

### Factory Patterns

```python
# tests/factories.py
import factory
from factory import fuzzy
from django.contrib.auth import get_user_model

User = get_user_model()

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    username = factory.Sequence(lambda n: f"user{n}")
    password = factory.PostGenerationMethodCall('set_password', 'testpass123')
    is_active = True

class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'products.Category'

    name = factory.Faker('word')
    slug = factory.LazyAttribute(lambda obj: obj.name.lower())

class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'products.Product'

    name = factory.Faker('sentence', nb_words=3)
    slug = factory.LazyAttribute(lambda obj: obj.name.lower().replace(' ', '-'))
    price = fuzzy.FuzzyDecimal(10.00, 1000.00, 2)
    stock = fuzzy.FuzzyInteger(0, 100)
    is_active = True
    category = factory.SubFactory(CategoryFactory)
    created_by = factory.SubFactory(UserFactory)
```

### Registering Factories as Fixtures

The recommended pattern is to expose factories as pytest fixtures in `conftest.py` so they participate in dependency injection:

```python
# tests/conftest.py
from tests.factories import UserFactory, ProductFactory

@pytest.fixture
def user(db):
    """Create a user via factory."""
    return UserFactory()

@pytest.fixture
def product(db, user):
    """Create a product via factory."""
    return ProductFactory(created_by=user)
```

## Model Testing

Model tests verify custom methods, validators, managers, and signals. They should not re-test Django ORM behavior (e.g., that `save()` persists data).

```python
# tests/test_models.py
import pytest
from tests.factories import ProductFactory

class TestProductModel:

    def test_reduce_stock_success(self, db):
        product = ProductFactory(stock=10)
        product.reduce_stock(3)
        product.refresh_from_db()
        assert product.stock == 7

    def test_reduce_stock_insufficient_raises(self, db):
        product = ProductFactory(stock=2)
        with pytest.raises(ValueError, match="Insufficient stock"):
            product.reduce_stock(5)

    def test_active_manager_excludes_inactive(self, db):
        ProductFactory.create_batch(3, is_active=True)
        ProductFactory.create_batch(2, is_active=False)
        assert Product.objects.active().count() == 3
```

## DRF API Testing

### Endpoint Tests

```python
# tests/test_api.py
import pytest
from rest_framework import status
from django.urls import reverse
from tests.factories import ProductFactory

class TestProductAPI:

    def test_list_products(self, api_client, db):
        ProductFactory.create_batch(5)
        response = api_client.get(reverse('api:product-list'))
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 5

    def test_create_unauthorized(self, api_client, db):
        response = api_client.post(reverse('api:product-list'), {'name': 'X'})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_authorized(self, authenticated_api_client, db):
        data = {'name': 'Widget', 'price': '29.99', 'stock': 10}
        response = authenticated_api_client.post(reverse('api:product-list'), data)
        assert response.status_code == status.HTTP_201_CREATED
```

## Mocking External Services

Mock only at the boundary — external APIs, payment gateways, email providers. Prefer `unittest.mock.patch` as a decorator or context manager targeting the import path where the dependency is used, not where it is defined.

```python
from unittest.mock import patch

class TestPaymentFlow:

    @patch('apps.payments.services.stripe.Charge.create')
    def test_charge_success(self, mock_charge, authenticated_client, product):
        mock_charge.return_value = {'id': 'ch_123', 'status': 'succeeded'}
        response = authenticated_client.post(reverse('payments:process'), {
            'product_id': product.id,
            'token': 'tok_visa',
        })
        assert response.status_code == 302
        mock_charge.assert_called_once()
```

## Celery Task Testing

Because test settings include `CELERY_TASK_ALWAYS_EAGER = True`, Celery tasks execute synchronously in-process during tests. This means you can call a task and immediately assert on its side effects without needing to mock the task or use a real broker.

```python
# tests/test_tasks.py
from apps.orders.tasks import send_order_confirmation

def test_order_confirmation_sends_email(db, order, mailoutbox):
    send_order_confirmation.delay(order.id)
    assert len(mailoutbox) == 1
    assert order.user.email in mailoutbox[0].to
```

If a task must be tested with real async behavior (rare), use `@pytest.mark.slow` and a dedicated Celery worker fixture, but the default test path should always rely on eager execution.

## Testing Best Practices

- **Factories over fixtures over manual creation** — never call `Model.objects.create()` in a test
- **One logical assertion per test** — a test should verify one behavior
- **Descriptive names** — `test_anonymous_user_cannot_delete_product`
- **Arrange-Act-Assert** — clear three-phase structure
- **Test permissions** — always verify both authorized and unauthorized paths
- **Keep tests fast** — use `--reuse-db`, `--nomigrations`, in-memory SQLite

## Quick Reference

| Pattern | Usage |
|---------|-------|
| `@pytest.fixture` | Define reusable test state in conftest.py |
| `factory.SubFactory` | Express model relationships in factories |
| `ProductFactory(field=val)` | Create test data with specific overrides |
| `create_batch(n)` | Generate multiple instances |
| `@patch('path.to.dep')` | Mock external boundaries |
| `@pytest.mark.django_db` | Enable database access (alternative to `db` fixture) |
| `api_client.force_authenticate(user=user)` | Skip auth in API tests |
| `CELERY_TASK_ALWAYS_EAGER` | Run tasks synchronously in tests |

Remember: tests are living documentation. A well-written test suite should make it obvious how each feature is supposed to behave without reading the implementation.
