# Architecture

How the system is put together and why. Decisions in detail: [adr/](adr/).

## Context

```mermaid
flowchart LR
  user([User]) --> app[Our system]
  app --> payments[(Payment provider)]
  app --> email[(Email service)]
```

## Containers

```mermaid
flowchart LR
  web[Web app<br/>Next.js] -->|HTTPS / JSON| api[API<br/>FastAPI]
  api --> db[(PostgreSQL)]
  api --> queue[[Queue]]
  worker[Worker] --> queue
  worker --> db
```

## Components
| Component | Responsibility | Technology | Code |
| --- | --- | --- | --- |
| Web app | | | `apps/web/` |
| API | | | `apps/api/` |

## Key flows
Only flows that are hard to follow in the code. One sequence diagram each.

```mermaid
sequenceDiagram
  participant U as User
  participant W as Web
  participant A as API
  U->>W: Submit order
  W->>A: POST /orders
  A-->>W: 201 Created
```

## Decisions
- [ADR-0001](adr/0001-record-architecture-decisions.md): …
