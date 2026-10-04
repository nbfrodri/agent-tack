# TypeScript / JavaScript (React, Next.js, Node)
| Topic | Convention |
| --- | --- |
| Package manager | **pnpm** for new projects (`pnpm-lock.yaml`, `packageManager` field in `package.json` via Corepack). In existing projects, the one its lockfile says. |
| Language | TypeScript with `"strict": true`; no `any` (use `unknown` and narrow it); `import type` for type-only imports. |
| Formatting and linting | The project's tool. New projects: Biome, or ESLint + Prettier when a framework preset needs ESLint (e.g. `eslint-config-next`). |
| File names | **kebab-case** for every file: `user-profile.tsx`, `use-cart.ts`, `order-service.ts`. Next.js special files keep their names (`page.tsx`, `layout.tsx`, `route.ts`). |
| Identifiers | `PascalCase` components, classes, types and interfaces (no `I` prefix); `camelCase` variables and functions; `useSomething` hooks; `UPPER_SNAKE_CASE` true constants. |
| Exports | Named exports. Default exports only where the framework requires them (Next.js `page`, `layout`, `route`, config files). |
| Imports | Path alias `@/` for project files instead of long `../../..` chains. |
| Components | Function components; props type named `<Component>Props`; one exported component per file (small private helpers may live alongside). |
