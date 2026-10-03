# Database MCP servers (read-only, per project)

An MCP server lets the AI inspect the real schema, run `EXPLAIN` and read sample data from a **development** database, instead of guessing from the models. Configure it per project, read-only, and never against production data.

| Engine | Server | Read-only switch |
| --- | --- | --- |
| PostgreSQL | `postgres-mcp` (Postgres MCP Pro, run with `uvx`) | `--access-mode=restricted` |
| MySQL | `@benborla29/mcp-server-mysql` | Writes are disabled unless `ALLOW_*_OPERATION=true` is set; don't set them |
| MongoDB | `mongodb-mcp-server` (official) | `--readOnly` |

Don't use `@modelcontextprotocol/server-postgres`: it is deprecated.

## Claude Code: `.mcp.json` in the project root
Credentials come from environment variables (expanded by Claude Code), so the file can be committed without secrets. Keep only the engine the project uses:
```json
{
  "mcpServers": {
    "postgres": {
      "command": "uvx",
      "args": ["postgres-mcp", "--access-mode=restricted"],
      "env": { "DATABASE_URI": "${DEV_DATABASE_URL}" }
    },
    "mysql": {
      "command": "npx",
      "args": ["-y", "@benborla29/mcp-server-mysql"],
      "env": {
        "MYSQL_HOST": "${DEV_DB_HOST:-127.0.0.1}",
        "MYSQL_PORT": "${DEV_DB_PORT:-3306}",
        "MYSQL_USER": "${DEV_DB_USER}",
        "MYSQL_PASS": "${DEV_DB_PASSWORD}",
        "MYSQL_DB": "${DEV_DB_NAME}"
      }
    },
    "mongodb": {
      "command": "npx",
      "args": ["-y", "mongodb-mcp-server", "--readOnly"],
      "env": { "MDB_MCP_CONNECTION_STRING": "${DEV_MONGODB_URI}" }
    }
  }
}
```
Document the `DEV_*` variables in `.env.example` and the README. Claude Code asks for approval the first time it sees a project's `.mcp.json`.

## Codex
Codex keeps MCP servers in its user config, so add one per project's dev database and remove it when you're done:
```bash
codex mcp add myapp-db --env DATABASE_URI="postgresql://user:pass@localhost:5432/myapp" -- uvx postgres-mcp --access-mode=restricted
codex mcp remove myapp-db
```

## Rules
- Use a dev or local database only, through a database user with read-only grants where possible (defence in depth on top of the read-only switch).
- Never use production credentials, and never commit real connection strings.
- Schema changes still go through migrations (see `SKILL.md`), never through the MCP server.
