# MongoDB

## Modelling: design for your queries
- Model around access patterns, not entities: list the queries first, then shape documents to answer them in a single read.
- **Embed** data that's read together, owned by the parent and bounded in size (order lines inside an order, addresses inside a user).
- **Reference** data that's shared, updated independently or grows without bound (comments on a popular post, events, logs). Unbounded arrays inside a document are an anti-pattern: documents have a 16 MB limit and large arrays make updates slow.
- Duplicating some fields (e.g. the author's name in a post) is fine if you plan how to keep them updated.
- Still enforce a schema: JSON Schema validators on the collection (`$jsonSchema`) and/or Mongoose schemas or Pydantic models in the app.

## Indexes
- Every frequent query needs an index; check with `explain("executionStats")` (look for `COLLSCAN` and `totalDocsExamined` ≫ `nReturned`).
- Follow the **ESR rule** for compound indexes: Equality fields first, then Sort fields, then Range fields.
- Unique indexes for natural keys (email), TTL indexes for expiring data (sessions, tokens), partial indexes for subsets, and text or Atlas Search indexes for search.
- Create indexes in migrations or startup scripts that are versioned in the repo, not by hand in production.

## Writes and consistency
- Updates use atomic operators (`$set`, `$inc`, `$push`), not read-modify-write of the whole document.
- Use multi-document transactions (they need a replica set, which Atlas always has) only when you really must update several documents atomically; good modelling usually avoids them.
- Write concern `majority` for important data. Use idempotent upserts with a unique key for retries.

## Queries
- Projections to return only the fields you need; range-based pagination on an indexed field (`_id` or `createdAt`) instead of a large `skip()`.
- Aggregation pipelines for reports: `$match` and `$sort` early so they use indexes, and `$lookup` sparingly.
- Never pass raw user objects into queries (operator injection, e.g. `{ "$ne": null }`); validate and cast inputs first (Mongoose `sanitizeFilter`, or schema validation).

## Stack notes
- Node: Mongoose (schemas, middleware, `lean()` for read-only queries) or the official driver with zod. Python: the PyMongo async API (Motor is deprecated in favour of it) or Beanie/ODMantic. Laravel: the official `mongodb/laravel-mongodb` package.
- Tests: `mongodb-memory-server` (Node) or a testcontainers or docker-compose replica set.
- Operations: MongoDB Atlas (backups, PITR, monitoring) or a self-hosted replica set with authentication enabled; never expose port 27017 publicly.
