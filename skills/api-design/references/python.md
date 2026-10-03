# Python backends (FastAPI, Django)

## Tooling (defaults for new projects; follow the existing repo otherwise)
- `uv` for dependencies and virtualenvs (`pyproject.toml`), `ruff` for lint and format, `mypy` or `pyright` for type checking, `pytest` (+ `pytest-asyncio` for async code).
- Settings from environment variables with `pydantic-settings` (FastAPI) or `django-environ`, validated at startup.

## FastAPI
Structure by feature, with layers inside:
```
app/
  main.py                # app factory, routers, exception handlers, middleware
  core/                  # config, security, logging, db session
  <feature>/
    router.py            # endpoints: thin, use Depends()
    schemas.py           # Pydantic request/response models (separate Create/Update/Read)
    service.py           # use cases
    models.py            # SQLAlchemy models
    repository.py
  domain/                # pure domain objects when using DDD
tests/
```
- Declare a `response_model` on every endpoint so internal fields never leak.
- Use dependency injection (`Depends`) for the DB session, the current user and services. Tests override them with `app.dependency_overrides`.
- SQLAlchemy 2.x style (`select()`, typed `Mapped[]`), migrations with Alembic.
- If you use `async def` endpoints, use async drivers throughout (asyncpg, motor). A blocking call inside async code freezes the event loop; use a plain `def` endpoint for blocking work instead.
- Register global exception handlers that map domain errors to Problem Details.
- Tests: `httpx.AsyncClient` with `ASGITransport` (or `TestClient`), against a real Postgres/MySQL test database (testcontainers or a docker-compose service), with a transaction rolled back per test.
- Background work: `BackgroundTasks` only for trivial jobs; use a real queue (Celery, RQ, arq, Dramatiq) for anything that must not be lost.

## Django / Django REST Framework
- One app per bounded context. Business logic goes in `services.py` / domain modules, not in views, serializers or model `save()` overrides scattered everywhere.
- DRF: `ModelViewSet` only for plain CRUD; explicit `APIView`/`GenericAPIView` when there's logic. Serializers validate input; permission classes handle authorisation.
- Avoid N+1 queries with `select_related` (FK/one-to-one) and `prefetch_related` (M2M/reverse), and check with `django-debug-toolbar` or `assertNumQueries` in tests.
- `python manage.py makemigrations` for every model change; review the generated migration and commit it with the change.
- Docs with `drf-spectacular`. Tests with `pytest-django` and `APIClient`, using factories (`factory_boy`) instead of fixtures dumps.
