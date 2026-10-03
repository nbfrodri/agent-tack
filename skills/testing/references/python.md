# Python testing (pytest)

## Setup
- `pytest` with config in `pyproject.toml` (`[tool.pytest.ini_options]`): `testpaths = ["tests"]`, `addopts = "-ra --strict-markers"`, and `asyncio_mode = "auto"` if you use `pytest-asyncio`.
- Useful plugins: `pytest-cov` (coverage), `pytest-xdist` (`-n auto`, parallel), `pytest-randomly` (random order), `pytest-asyncio` or `anyio`, `pytest-django`, `factory_boy` or `polyfactory`, `freezegun` or `time-machine` (time), `respx` (httpx mocking) or `responses` (requests), and `testcontainers` (a real Postgres/MySQL/Mongo).
- Layout: `tests/unit/`, `tests/integration/`, `tests/api/`, with shared fixtures in `conftest.py` at the narrowest level that needs them.

## Idioms
```python
import pytest

@pytest.mark.parametrize(
    ("quantity", "expected"),
    [(1, Money("10.00")), (10, Money("90.00")), (0, None)],
    ids=["single", "bulk-discount", "zero"],
)
def test_order_total_applies_bulk_discount(quantity, expected):
    order = OrderFactory.build(unit_price=Money("10.00"), quantity=quantity)
    assert order.total() == expected

def test_rejects_negative_quantity():
    with pytest.raises(InvalidQuantity, match="must be positive"):
        Quantity(-1)
```
- Fixtures over setup methods; use `yield` fixtures for teardown, and scope them (`session` for containers, `function` for data).
- `tmp_path` for files, `monkeypatch` for env vars and attributes, `caplog` for logs.
- Prefer dependency injection to patching. If you must patch, use `mocker` (`pytest-mock`), patch where the name is *looked up*, and use `autospec=True`.

## FastAPI
- `httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test")`, or `TestClient` for sync tests.
- Override dependencies (`app.dependency_overrides[get_db] = ...`, `get_current_user`) in fixtures, and clear them after.
- DB: a session fixture bound to a connection with an outer transaction that's rolled back after each test, with the migrations (Alembic) applied once per session against a testcontainer.

## Django
- `pytest-django`: the `@pytest.mark.django_db` marker; `client`/`admin_client` fixtures or DRF's `APIClient`; `django_assert_num_queries` to catch N+1 queries; `settings` fixture to override settings.
- `factory_boy` `DjangoModelFactory` for models; `--reuse-db` locally for speed.

## Coverage
`pytest --cov=src --cov-branch --cov-report=term-missing`, with `fail_under` in `[tool.coverage.report]` once the baseline is known. Mutation testing: `mutmut` on domain modules.
