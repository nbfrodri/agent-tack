---
name: database
description: Database design and data access for PostgreSQL, MySQL and MongoDB - schema and data modelling, migrations (Alembic, Django, Laravel, Prisma, Drizzle, Knex), indexes, query optimisation, N+1 prevention, transactions, constraints, seeds, backups and safe production changes. Use whenever creating or changing tables, collections, models, migrations, queries, indexes or ORM code, when something is slow at the database level, or when the user mentions base de datos, tabla, consulta, SQL, migración, Postgres, MySQL or Mongo.
---

# Database

Data outlives code. A bad migration or a missing constraint can corrupt data in ways no deploy can roll back, so changes to the schema are deliberate, versioned and reversible, and the database itself enforces the rules it can.

Engine-specific guidance (read the one the project uses):
- PostgreSQL: `references/postgresql.md`
- MySQL: `references/mysql.md`
- MongoDB: `references/mongodb.md`
- Letting the AI inspect a dev database through a read-only MCP server: `references/mcp.md`

## Choosing (for new projects)
Default to **PostgreSQL** for most applications: relational integrity, transactions, JSONB for flexible bits, full-text search. Use **MySQL** when the project, host or team already uses it (e.g. many Laravel setups). Choose **MongoDB** when the data really is document-shaped (data read and written as a whole, variable schemas, little cross-document joining), not just to avoid designing a schema.

## Migrations: the only way to change a schema
| Stack | Tool |
| --- | --- |
| FastAPI / SQLAlchemy | Alembic (`alembic revision --autogenerate`, then review it) |
| Django | `makemigrations` / `migrate` |
| Laravel | `php artisan make:migration` / `migrate` |
| Node | Prisma Migrate, Drizzle Kit, Knex or TypeORM migrations |
| MongoDB | `migrate-mongo` or app-level versioned scripts, plus JSON Schema validators |

Rules:
- Every schema change is a migration committed together with the code that needs it. Never edit a migration that has already run in a shared environment; write a new one.
- Review auto-generated migrations: they miss renames (and do drop + add instead, losing data), data backfills and index options.
- Provide a working `down`/rollback when the tool supports it, or document why it's irreversible.
- **Production-safe changes (expand → migrate → contract):** add new columns as nullable or with a default, deploy code that writes both shapes, backfill in batches, switch reads, then drop the old column in a later release. Avoid long table locks: create indexes concurrently/online, and don't add a `NOT NULL` column without a default on big tables in one step.
- Data migrations (backfills) run in batches, are idempotent, and are kept separate from schema migrations where possible.

## Modelling (relational)
- Normalise first (3NF); denormalise deliberately, for measured read performance.
- Primary keys: `bigint` identity or UUID (UUIDv7 or ULID if you need sortable, non-guessable IDs). Don't expose sequential IDs publicly if enumeration matters.
- Let the database enforce invariants: `NOT NULL`, `UNIQUE`, `CHECK`, foreign keys with explicit `ON DELETE` behaviour, and enums or lookup tables.
- Money as `DECIMAL(19,4)` or integer minor units, never float. Timestamps in UTC (`timestamptz` in Postgres). `created_at`/`updated_at` on every table.
- Soft deletes (`deleted_at`) only when there's a real need (audits, undo), because they complicate every query and unique constraint.
- Name things consistently: `snake_case`, plural table names, `<table>_id` foreign keys, `idx_<table>_<cols>` indexes.

## Queries and performance
- **N+1 queries** are the most common performance bug: eager-load relations (`select_related`/`prefetch_related`, `with()`, `include`, `selectinload`). Assert the query count in tests for important endpoints.
- Select only the columns you need for large tables, and paginate everything.
- Index the columns used in `WHERE`, `JOIN` and `ORDER BY` of frequent queries. In composite indexes, put equality columns first, then range or sort columns. Every index slows writes, so don't add them speculatively.
- Use `EXPLAIN` (`EXPLAIN ANALYZE` in Postgres) before and after optimising, and show the user the plan difference.
- Always use parameterised queries or the ORM's binding. Never build SQL with string concatenation of user input.
- Use transactions for multi-step writes. Keep them short, never wrap network calls in them, and use optimistic locking (a version column) or `SELECT … FOR UPDATE` for concurrent updates to the same rows.
- Use connection pooling, and size pools for serverless (PgBouncer, RDS Proxy, Prisma Accelerate or Neon pooling on Vercel).

## Testing
- Test against the same engine as production (testcontainers or a docker-compose service), not SQLite, when queries use engine-specific features.
- Isolate tests: transaction rollback or truncate per test, plus factories for data.
- Test migrations: `up` on an empty DB, plus `down` → `up` where supported, in CI.

## Seeds and environments
Seeders for local and dev data (fake but realistic, with factories), never production data copied to dev without anonymising it. Each environment has its own credentials, and app users have least-privilege DB users (no superuser for the app).

## Backups
In production, check that automated backups and point-in-time recovery are on, and that a restore has actually been tested. Before risky manual operations, take a snapshot. Ask the user before running anything destructive (`DROP`, `TRUNCATE`, mass `DELETE`/`UPDATE`) against a non-local database.
