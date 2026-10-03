# PostgreSQL

## Types
- `bigint generated always as identity` (or `uuid`) for primary keys; `text` instead of `varchar(n)` unless the limit is a real business rule (enforce it with `CHECK`).
- `timestamptz` for timestamps (stored as UTC), `numeric(19,4)` for money, `jsonb` (not `json`) for semi-structured data, and native enums or a lookup table for statuses (enums are hard to remove values from).
- `citext` or a `lower(email)` unique index for case-insensitive uniqueness.

## Indexes
- B-tree by default; GIN for `jsonb`, arrays and full-text search (`tsvector`); `pg_trgm` + GIN for `ILIKE '%foo%'`; BRIN for huge, naturally ordered tables (logs by time).
- Partial indexes (`WHERE deleted_at IS NULL`, `WHERE status = 'pending'`) and expression indexes (`lower(email)`).
- `CREATE INDEX CONCURRENTLY` in production (it can't run inside a transaction, so disable the migration transaction for that migration).
- Find missing or unused indexes with `pg_stat_user_indexes`, and slow queries with `pg_stat_statements`.

## Safe migrations
- Set `lock_timeout` (e.g. `SET lock_timeout = '5s'`) in migrations so they fail fast instead of queuing behind long transactions and blocking traffic.
- Adding a nullable column, or a column with a constant default, is cheap in modern Postgres; changing a column type usually rewrites the table.
- Adding a `NOT NULL` or foreign key on a big table: add the constraint `NOT VALID`, then `VALIDATE CONSTRAINT` separately.

## Queries
- `EXPLAIN (ANALYZE, BUFFERS)` to optimise. Look for sequential scans on big tables, bad row estimates (run `ANALYZE`) and nested loops over many rows.
- `INSERT … ON CONFLICT DO UPDATE` for upserts; `RETURNING` to avoid an extra select.
- CTEs and window functions for reports; keyset pagination (`WHERE (created_at, id) < ($1, $2) ORDER BY created_at DESC, id DESC LIMIT n`) for large lists.
- Row-Level Security for multi-tenant isolation when appropriate (it's required to be on with Supabase).

## Operations
- Connection pooling (PgBouncer in transaction mode, or the platform's pooler) when there are many app instances or serverless functions.
- Autovacuum is on by default; watch for table bloat on high-churn tables.
- Backups: managed PITR (RDS, Neon, Supabase…), or `pg_dump` plus WAL archiving on a VPS. Test restores.
