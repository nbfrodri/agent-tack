# Laravel

Check `composer.json` for the Laravel and PHP versions and follow the conventions already used (folder layout, Pest vs PHPUnit).

## Tooling
Laravel Pint (format), Larastan/PHPStan (static analysis, as high a level as the project allows), Pest or PHPUnit (tests), and Laravel Sail or docker-compose for local services.

## Structure
- Routes in `routes/api.php`, grouped and versioned (`Route::prefix('v1')`), with `apiResource` for CRUD.
- **Controllers are thin**: they receive a Form Request, call an Action/Service and return an API Resource.
- **Form Requests** (`php artisan make:request`) handle validation (`rules()`) and authorisation (`authorize()`, usually delegating to a Policy).
- **Actions/Services** (`app/Actions/CreateOrder.php`, single-method classes) hold the use cases. For DDD, use `app/Domain/<Context>/` with models, value objects, actions and events.
- **API Resources** (`JsonResource`, `ResourceCollection`) shape every response, so models never get serialised directly and fields don't leak.
- **Policies** for authorisation (`$this->authorize()` or `Gate`), registered per model.
- Services are bound to interfaces in a ServiceProvider for dependency inversion.

## Eloquent
- Prevent N+1 queries: eager-load with `with()`/`load()`, and enable `Model::preventLazyLoading(! app()->isProduction())` in `AppServiceProvider`.
- Guard mass assignment with `$fillable` (or explicit `$guarded`). Never `$request->all()` into `create()`; use `$request->validated()`.
- Casts for dates, enums (backed PHP enums), JSON and value objects; query scopes for reusable filters.
- Wrap multi-step writes in `DB::transaction()`.
- Migrations for every schema change, with a working `down()`; factories and seeders for test and dev data.

## Errors, queues and the rest
- Map domain exceptions to HTTP responses in the exception handler (`bootstrap/app.php` → `withExceptions` in recent versions, `app/Exceptions/Handler.php` in older ones), in one consistent JSON format.
- Queued Jobs (`ShouldQueue`) for slow work, with `tries`, `backoff` and idempotent handlers; Horizon when using Redis.
- Events and listeners for side effects; Notifications for email, SMS or Slack.
- Rate limiting with `RateLimiter::for()` plus the `throttle` middleware.
- Auth: Sanctum for SPAs and first-party tokens; Passport only if you need a full OAuth2 server (see the `auth` skill).
- API docs: Scribe or Scramble.

## Testing
Feature tests per endpoint using `RefreshDatabase` (or `LazilyRefreshDatabase`) against a real MySQL/Postgres test DB when the queries are DB-specific, `actingAs()` / `Sanctum::actingAs()` for auth, `assertJsonPath`/`assertJsonValidationErrors`, and `Queue::fake()`, `Event::fake()`, `Mail::fake()` and `Http::fake()` for side effects. Unit tests for Actions and domain classes.
