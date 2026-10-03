# Design: SOLID, DDD and other practices

## SOLID
- **S – Single Responsibility:** each module or class has one reason to change. If describing it needs "and", it's probably two.
- **O – Open/Closed:** extend behaviour by adding code (new implementations, strategies) rather than modifying what works, when real variation is expected.
- **L – Liskov Substitution:** an implementation must replace its abstraction without surprises (no "not supported" errors, no stricter preconditions).
- **I – Interface Segregation:** small, client-specific interfaces rather than one big one.
- **D – Dependency Inversion:** the domain depends on abstractions (ports); infrastructure implements them. Inject dependencies through constructors.

Don't create speculative abstractions: apply O and D when there are at least two implementations or a clear I/O boundary. YAGNI and KISS are good practices too.

## DDD
Use it when there's a business domain with real rules (orders, payments, bookings, inventory…). For simple CRUD, utilities or scripts, good layer separation is enough.

**Strategic**
- **Ubiquitous language:** use the business's own terms in the code. If a concept has no clear name, ask.
- **Bounded contexts:** keep models that mean different things in different contexts (e.g. `Customer` in billing vs. in support). Connect them through interfaces or events, not shared entities.

**Tactical**
- **Entities:** have their own identity and lifecycle.
- **Value objects:** immutable, defined by their values, validated in the constructor (`Email`, `Money`, `Quantity`). Prefer them to primitives.
- **Aggregates:** a cluster of objects with a root that protects the invariants. Change it only through the root; one transaction = one aggregate. Keep them small.
- **Repositories:** interface in the domain, implementation in infrastructure; one per aggregate.
- **Domain services:** logic that doesn't belong to a single entity.
- **Domain events:** past facts (`OrderPlaced`) to decouple side effects.
- **Application services / use cases:** orchestrate; they hold no business rules.

Avoid the anaemic model: rules live in entities and value objects, not in services that shuffle getters and setters.

## Layered architecture (hexagonal / clean)
```
src/
  domain/          # entities, VOs, aggregates, events, ports (interfaces). No framework dependencies.
  application/     # use cases; orchestrate the domain and ports.
  infrastructure/  # DB, HTTP clients, queues: implement the ports.
  interfaces/      # controllers, CLI, UI: adapt input to use cases.
```
Dependencies point inwards: `interfaces → application → domain`, and `infrastructure → domain`. The domain never imports infrastructure. Adapt folder names to the language's, framework's and project's conventions.

## Other practices
- **DRY** with judgement: duplicate rather than couple things that only look alike by accident.
- **Composition over inheritance.**
- **Fail fast:** validate at the boundaries and in value-object constructors.
- **Immutability** by default where the language makes it easy.
- **Law of Demeter:** don't chain `a.b().c().d()` through other objects.
- **Clean code:** no dead code; comments as in `conventions.md`.
