# UI libraries for React

A proven library gives the interface a base that is accessible and plain by default, so the result reads as designed rather than generated. Reuse what `package.json` and `components/ui` already hold; add a library from this table only when the need appears and nothing in the project covers it, and mention the new dependency to the user.

| Need | Library | Notes |
| --- | --- | --- |
| Components (buttons, dialogs, menus, forms, tables) | [shadcn/ui](https://ui.shadcn.com) | Code copied into `components/ui` and owned by the project; add pieces with its CLI as needed and adapt the tokens to the product's look |
| Accessible primitives under shadcn/ui or custom components | [Base UI](https://base-ui.com) or [Radix](https://www.radix-ui.com) | One primitive layer per project: keep the one already in use; for a new project, either works with shadcn/ui |
| Toasts | [Sonner](https://sonner.emilkowal.ski) | shadcn/ui's toast component already wraps it |
| Command palette, searchable lists | [cmdk](https://cmdk.paco.me) | shadcn/ui's `command` component already wraps it |
| Animated counters, prices and stats | [NumberFlow](https://number-flow.barvian.me) | |
| Mobile bottom sheet / drawer | [Vaul](https://vaul.emilkowal.ski) | Its README marks it unmaintained: prefer the project's dialog or sheet unless the drag-to-close drawer is needed |
| Chat and agent interfaces (streaming text, tool calls, approvals) | [Beautiful UI](https://beautifului.dev) | Copy-paste components; read the code before adopting it |

Showcase libraries (Aceternity UI, Magic UI, RareUI, 21st.dev) bring decorative effects that read as generic; they live in the `showcase-ui` set and are used only when the user asks for them.
