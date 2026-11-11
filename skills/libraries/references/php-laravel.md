# PHP and Laravel packages

Laravel ships queues, cache, mail, validation, events, scheduling and storage: check the framework before adding a package, and prefer a first-party one. Names are Composer packages.

| Need | Default | Alternatives | Notes |
| --- | --- | --- | --- |
| Reactive interfaces in Blade | `livewire/livewire` | | |
| React or Vue pages without an API | `inertiajs/inertia-laravel` | | |
| Admin panels | `filament/filament` | | |
| API tokens and SPA authentication | `laravel/sanctum` | | Follow the `auth` skill |
| Login, registration, two-factor backend | `laravel/fortify` | | |
| Social login | `laravel/socialite` | | |
| Subscriptions with Stripe | `laravel/cashier` | | |
| Queue dashboard on Redis | `laravel/horizon` | | |
| Full-text search | `laravel/scout` | | |
| WebSockets | `laravel/reverb` | | |
| Feature flags | `laravel/pennant` | | |
| Long-lived application server | `laravel/octane` | | Watch for state leaking between requests |
| Production metrics | `laravel/pulse` | | |
| Local debugging | `laravel/telescope` | `barryvdh/laravel-debugbar` | Keep both out of production |
| Roles and permissions | `spatie/laravel-permission` | | |
| File attachments and conversions | `spatie/laravel-medialibrary` | | |
| Typed data objects | `spatie/laravel-data` | | |
| Audit log | `spatie/laravel-activitylog` | | |
| Backups | `spatie/laravel-backup` | | |
| Filtering and sorting from the query string | `spatie/laravel-query-builder` | | Allow-list every filter and sort |
| Excel import and export | `maatwebsite/excel` | | |
| Tests | `pestphp/pest` | PHPUnit | See the `testing` skill |
| Static analysis | `larastan/larastan` | | |
| Code style | `laravel/pint` | | |
| Automated upgrades | `rector/rector` | | |
