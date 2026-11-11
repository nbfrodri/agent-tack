# Go libraries

Go's standard library is the default: `net/http` (with method and wildcard routing since 1.22), `log/slog`, `encoding/json`, `database/sql`, `testing`, `flag`. Add a module when the need outgrows it. Names are module paths.

| Need | Default | Alternatives | Notes |
| --- | --- | --- | --- |
| HTTP routing and middleware | `net/http` | `github.com/go-chi/chi/v5`, `github.com/gin-gonic/gin`, `github.com/labstack/echo/v4` | chi keeps the `net/http` handler types; Gin and Echo bring their own context |
| PostgreSQL driver | `github.com/jackc/pgx/v5` | | |
| SQL to typed code | `github.com/sqlc-dev/sqlc` | `gorm.io/gorm` | sqlc generates code from SQL; GORM is an ORM |
| Migrations | `github.com/pressly/goose/v3` | | |
| CLI | `github.com/spf13/cobra` | `flag` | |
| Configuration | `github.com/knadh/koanf/v2` | `github.com/spf13/viper` | Viper pulls many dependencies |
| Terminal applications | `github.com/charmbracelet/bubbletea` with `lipgloss` | | |
| Test assertions | `testing` with `github.com/google/go-cmp` | `github.com/stretchr/testify` | |
| Logging | `log/slog` | `go.uber.org/zap`, `github.com/rs/zerolog` | For hot paths that need zero allocation |
| Struct validation | `github.com/go-playground/validator/v10` | | |
| Concurrency helpers | `golang.org/x/sync` (`errgroup`) | | |
| RPC | `connectrpc.com/connect` | `google.golang.org/grpc` | Connect serves gRPC, gRPC-Web and plain HTTP from one handler |
| Lint | `golangci-lint` | `go vet`, `staticcheck` | |
