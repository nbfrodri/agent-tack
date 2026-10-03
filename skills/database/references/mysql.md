# MySQL

## Configuration and types
- InnoDB only; charset `utf8mb4` with a `utf8mb4_0900_ai_ci` (MySQL 8) or `utf8mb4_unicode_ci` collation. `utf8` (utf8mb3) can't store emojis and some characters.
- Run with a strict SQL mode (`STRICT_TRANS_TABLES`, the default in MySQL 8) so invalid data errors instead of being silently truncated.
- `BIGINT UNSIGNED AUTO_INCREMENT` or `BINARY(16)` UUIDs (with `UUID_TO_BIN(uuid, 1)` for ordering) as primary keys. The PK is the clustered index, so random UUIDs as PK fragment inserts.
- `DATETIME` for application timestamps stored in UTC (`TIMESTAMP` is limited to 2038 and converts time zones); `DECIMAL(19,4)` for money; `JSON` columns with generated columns + indexes for fields you query often.
- MySQL 8.0.16+ enforces `CHECK` constraints; older versions parse them but ignore them.

## Indexes
- Composite indexes follow the leftmost-prefix rule: `(a, b, c)` serves `a`, `a,b` and `a,b,c`, not `b` alone.
- Covering indexes (all selected columns in the index) avoid table lookups.
- Index prefixes for long `VARCHAR`/`TEXT` columns; `FULLTEXT` indexes for text search.
- Every foreign key column needs an index (InnoDB creates one automatically if missing, but name and plan it).

## Safe migrations
- Most `ALTER TABLE` operations in MySQL 8 support `ALGORITHM=INPLACE` or `INSTANT` (adding columns is instant from 8.0.12+). Specify `ALGORITHM` and `LOCK=NONE` explicitly so the migration fails instead of locking if it can't be done online.
- For big tables on older versions or heavy changes, use `gh-ost` or `pt-online-schema-change`.
- DDL is not transactional in MySQL: a migration that fails halfway leaves partial changes, so keep each migration to one logical DDL change.

## Queries
- `EXPLAIN` / `EXPLAIN ANALYZE` (8.0.18+): watch for `type: ALL` (a full scan), `Using filesort` and `Using temporary` on large tables.
- `INSERT … ON DUPLICATE KEY UPDATE` for upserts.
- Avoid functions on indexed columns in `WHERE` (`WHERE DATE(created_at) = …` can't use the index; use ranges instead).
- Default isolation is `REPEATABLE READ`; know about gap locks when debugging deadlocks (`SHOW ENGINE INNODB STATUS`).

## Operations
Enable the slow query log in non-trivial environments. Backups: managed snapshots and PITR (RDS, PlanetScale), or `mysqldump --single-transaction` / Percona XtraBackup on a VPS. Test restores.
