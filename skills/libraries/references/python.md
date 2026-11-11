# Python libraries

The standard library covers more than expected (`pathlib`, `dataclasses`, `argparse`, `sqlite3`, `tomllib`, `asyncio`, `logging`): a script with one need stays on it. Names are PyPI packages. Dataframes and machine learning are in `data-ml.md`.

| Need | Default | Alternatives | Notes |
| --- | --- | --- | --- |
| Web API | `fastapi` | `litestar`, `flask` | |
| Full web application with admin, ORM and auth | `django` | | |
| Validation and settings | `pydantic`, `pydantic-settings` | `msgspec` | msgspec is faster and smaller, with fewer features |
| SQL | `sqlalchemy` with `alembic` | `sqlmodel` | SQLModel joins SQLAlchemy and Pydantic models for FastAPI |
| HTTP client | `httpx` | | Last release 2024-12; still the usual choice for sync and async |
| CLI | `typer` | `click`, `argparse` | |
| Terminal output | `rich` | | |
| Terminal applications | `textual` | | |
| Tests | `pytest` | | See the `testing` skill |
| Property-based tests | `hypothesis` | | MPL-2.0 |
| Mocking HTTP | `respx` | | For httpx |
| Background jobs | `celery` | `dramatiq`, `arq` | Dramatiq is LGPL; arq is asyncio on Redis |
| Logging | `structlog` | `loguru`, `logging` | |
| Retries | `tenacity` | | |
| Browser automation | `playwright` | | |
| HTML parsing | `beautifulsoup4` | | |
| Crawling | `scrapy` | | |
| Templates | `jinja2` | | |
| Fast JSON | `orjson` | `msgspec` | |
| Images | `pillow` | | |
| Packaging and environments | `uv` | | See `uv-package-manager` when active |
| Lint and format | `ruff` | | |
| Type checking | `mypy` | `ty`, pyright | ty is new and fast: check it supports the project's plugins |
