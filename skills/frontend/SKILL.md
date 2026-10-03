---
name: frontend
description: Frontend engineering with React and Next.js - component design, Server vs Client Components, data fetching, forms and validation, state management, styling, accessibility (WCAG), responsive design, loading/error/empty states, and component tests with Testing Library. Use whenever building or changing UI, pages, layouts, components, hooks, forms, client state or styling in a React/Next.js project, or when the user mentions frontend, interfaz, pantalla, componente, página or formulario.
---

# Frontend (React / Next.js)

Good UI code is easy to change: small components with clear props, data fetched in one obvious place, every async state handled, and an interface that works with a keyboard and a screen reader. Follow the project's existing stack (router, styling, state and form libraries) before introducing anything new.

For Next.js specifics (App Router, Server Components, Server Actions, caching, routing), read `references/nextjs.md`.

## Before writing code
- Check `package.json` for the React and Next.js versions and the libraries already in use (styling, forms, data fetching, UI kit). APIs and defaults change between major versions; when unsure, check the current docs (e.g. the context7 MCP if it's available) instead of relying on memory.
- Look for an existing design system or component folder (`components/ui`, shadcn/ui…) and reuse it.

## Components
- One component, one job. Split when a component mixes data fetching, business logic and presentation, or grows beyond what fits on a screen.
- Keep business rules out of components: put them in plain functions or modules (`lib/`, `domain/`) that can be unit-tested without React.
- Props are typed (TypeScript), minimal, and named for intent. Prefer composition (`children`, slots) over boolean-prop explosions.
- Derive values instead of storing duplicated state. Use `useEffect` only to synchronise with external systems, never to compute values from props or state.
- Stable, meaningful `key`s for lists (never the index if items can be reordered).
- Files in kebab-case (`user-profile.tsx`) with named exports; see `dev-workflow` → `references/conventions.md` for naming and style.
- Co-locate files by feature (`features/orders/components`, `hooks`, `api`, `tests`) rather than by type, unless the project already does otherwise.

## State
Pick the smallest scope that works:
1. Local `useState`/`useReducer`.
2. URL state (search params) for filters, pagination and tabs, so they're shareable and survive reloads.
3. Server state with the framework's data fetching (Next.js Server Components) or TanStack Query/SWR on the client. Don't copy server data into a global store.
4. Global client state (Context, Zustand, Redux Toolkit) only for truly app-wide UI state such as theme or session.

## Forms
Validate with a schema (zod or similar) shared between client and server where possible, always re-validate on the server, show field-level errors, disable double submits, and keep the user's input on errors. React Hook Form or Server Actions + `useActionState` are both fine; follow the project.

## Every async view has four states
Loading (skeletons over spinners when the layout is known), error (a message plus a retry action), empty (explain and offer the next action), and success. Handle optimistic updates and their rollback explicitly.

## Accessibility (non-negotiable)
- Semantic HTML first: `button` for actions, `a` for navigation, real `label`s for inputs, one `h1`, ordered headings, landmarks (`main`, `nav`).
- Everything usable by keyboard with a visible focus. Manage focus in modals and after route changes.
- Images have `alt` (empty for decorative ones); icon-only buttons have `aria-label`.
- Colour contrast ≥ 4.5:1 for text; never convey information by colour alone.
- Respect `prefers-reduced-motion` and `prefers-color-scheme` when relevant.
- Use ARIA only when no semantic element fits.

## Styling and responsiveness
Follow the project's approach (Tailwind, CSS Modules…). Mobile-first, fluid layouts with flex/grid, design tokens or theme variables instead of magic values, and no fixed widths that break at 360px.

## Performance
Ship less JavaScript (Server Components, dynamic `import()` for heavy client-only parts), use `next/image` and `next/font` in Next.js, avoid unnecessary re-renders (but measure before you `memo`), virtualise long lists, and keep an eye on bundle size when adding dependencies.

## Testing
- Unit-test logic functions and hooks with Vitest/Jest.
- Component tests with Testing Library: query by role and label the way a user would (`getByRole('button', { name: /save/i })`), assert visible behaviour, and use `user-event` for interactions. Mock the network at the boundary (MSW), not internal modules.
- Critical user flows get end-to-end tests (see the `e2e-testing` skill).
- After a UI change, look at it in a real browser when a browser tool is available, at mobile and desktop widths.
