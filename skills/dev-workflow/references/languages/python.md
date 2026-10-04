# Python (FastAPI, Django, scripts)
| Topic | Convention |
| --- | --- |
| Tooling | **uv** (dependencies, virtualenv, running); **Ruff** for lint and format (PEP 8); **mypy** or **pyright** (strict in new projects). |
| Layout | `src/<package>/` with `tests/` alongside (Django: the standard project/app layout). |
| Identifiers | `snake_case` modules, functions and variables; `PascalCase` classes; `UPPER_SNAKE_CASE` constants; leading `_` for private. |
| Types | Type hints on every public function and method; `X \| None` rather than `Optional[X]`; Pydantic models or dataclasses rather than bare dicts for structured data. |
| Docstrings | Google style, on public modules, classes and functions whose purpose isn't obvious from the name and types. |
| Idioms | `pathlib` over `os.path`; f-strings; context managers for resources; `logging`, not `print`, in application code. |
