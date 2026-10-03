# PHP / Laravel testing (Pest, PHPUnit)

Use whichever the project uses: Pest is the default in new Laravel projects and runs on top of PHPUnit, so both can coexist, but write new tests in the existing style.

## Setup
- `tests/Unit` (no framework boot, fast) and `tests/Feature` (HTTP, DB, the full app). Run with `php artisan test` (or `./vendor/bin/pest`), adding `--parallel` for speed.
- `phpunit.xml` sets the testing env: a dedicated test DB (a MySQL/Postgres container when queries are engine-specific; SQLite in-memory only if the app has no engine-specific SQL), `QUEUE_CONNECTION=sync` or a fake, `MAIL_MAILER=array`, `CACHE_STORE=array`.
- Coverage: `php artisan test --coverage --min=80` (needs Xdebug or PCOV). Mutation testing: Infection, or Pest's `--mutate`.

## Pest idioms
```php
it('rejects an order when stock is insufficient', function () {
    $product = Product::factory()->create(['stock' => 1]);
    $user = User::factory()->create();

    $response = $this->actingAs($user)->postJson('/api/v1/orders', [
        'product_id' => $product->id,
        'quantity' => 2,
    ]);

    $response->assertUnprocessable()
        ->assertJsonValidationErrors(['quantity']);
    expect($product->fresh()->stock)->toBe(1);
});

it('calculates totals', function (int $quantity, string $expected) {
    expect(Order::totalFor('10.00', $quantity))->toBe($expected);
})->with([
    'single' => [1, '10.00'],
    'bulk discount' => [10, '90.00'],
]);
```
- `uses(RefreshDatabase::class)->in('Feature')` in `tests/Pest.php` (or `LazilyRefreshDatabase`); `beforeEach` for shared setup; datasets for table tests; architecture tests (`arch()->expect('App\Domain')->not->toUse('Illuminate\Http')`) to enforce layering.

## Laravel testing helpers
- Auth: `actingAs($user)`, `Sanctum::actingAs($user, ['abilities'])`.
- HTTP assertions: `assertOk`, `assertCreated`, `assertForbidden`, `assertNotFound`, `assertJsonPath`, `assertJsonStructure`, `assertJsonValidationErrors`.
- DB: `assertDatabaseHas`, `assertDatabaseMissing`, `assertSoftDeleted`, `assertModelExists`; `DB::enableQueryLog()` or `expectsDatabaseQueryCount()` to catch N+1 queries.
- Fakes for side effects: `Queue::fake()`, `Bus::fake()`, `Event::fake()`, `Mail::fake()`, `Notification::fake()`, `Storage::fake('s3')` and `Http::fake([...])` + `Http::preventStrayRequests()`, then assert with `assertPushed`, `assertDispatched`, `assertSent`…
- Time: `$this->travelTo(now()->addDays(3))` or `Carbon::setTestNow()`.
- Factories with states (`User::factory()->admin()->create()`), relationships (`has()`, `for()`), and sequences. Keep the defaults valid and minimal.
- Policies: test them directly (`$user->can('update', $order)`) as well as through endpoints (403).
- Jobs and Actions: unit-test their `handle()`/`execute()` directly with fakes for their dependencies.
