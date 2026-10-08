# Design: SOLID, DDD and other practices

## SOLID
- **S – Single Responsibility:** keep a cohesive responsibility together; split a module when unrelated changes repeatedly affect it, not just to make files shorter.
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

## Minimal, modular change
- **Smallest diff that solves the problem:** fewer files and lines mean less risk and easier review. Don't reformat, rename or reorganise code you aren't changing.
- **Change in one place:** a new variant (a mode, a provider, a rule) should be a new entry in data or a new implementation of an existing interface, not edits scattered across call sites. If it can't be, the missing extension point is the design problem to raise.
- **Signals that the architecture needs attention:** shotgun surgery (one feature touches many files), god files or functions, dependency cycles or domain logic depending on infrastructure, copy-pasted logic, configuration hard-coded in code, and load or data growth the current design can't absorb. Report them with evidence and options; refactor only with the user's agreement.

## Contracts, failures and recovery

Apply these checks when the change touches the relevant boundary; they are not extra artifacts for every task.

- **Observable behavior:** state the intended outcome and reproduce a real failure for a bug fix. Test boundaries and invariants rather than mirroring implementation details. Keep fast focused checks first and broader integration checks where the impact warrants them.
- **Compatibility:** identify callers, supported platforms and persisted formats before changing an interface or schema. Validate malformed and unsupported versions explicitly; preserve compatible defaults or provide a migration with tests.
- **Reversible changes:** for installation, migrations or configuration writes, identify what user state must survive and how partial failures recover. Verify restoration where relevant; never infer reversibility just because a backup file exists.
- **Bounded execution:** external commands and network operations need appropriate timeouts and visible failures. Distinguish unavailable or skipped checks from passing checks; invalidate results when their inputs change.
- **One source of truth:** reuse project commands, schemas and conventions across CLI, CI and adapters. Share project data while keeping credentials and execution permissions local. Do not add a second framework for a check the project already has.
- **Maintainable delivery:** keep code, relevant tests and affected documentation in a coherent change. Review complexity and compatibility as well as correctness; record unresolved risks. Measure a claimed performance or quality improvement under comparable conditions.

## Other practices
- **DRY** with judgement: duplicate rather than couple things that only look alike by accident.
- **Composition over inheritance.**
- **Fail fast:** validate at the boundaries and in value-object constructors.
- **Immutability** by default where the language makes it easy.
- **Law of Demeter:** don't chain `a.b().c().d()` through other objects.
- **Clean code:** no dead code; comments as in `conventions.md`.
