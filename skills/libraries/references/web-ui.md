# Web UI libraries (React, Vue)

Base components, primitives, toasts, command palette and drawers are in `frontend` → `references/ui-libraries.md`. Names are npm packages.

| Need | Default | Alternatives | Notes |
| --- | --- | --- | --- |
| Forms | `react-hook-form` | `@tanstack/react-form` | Server Actions with `useActionState` need no library |
| Schema validation | `zod` | `valibot` | Valibot when bundle size matters |
| Data tables | `@tanstack/react-table` | `ag-grid-community` | AG Grid: pivoting, grouping and Excel export are in the paid Enterprise edition |
| Long lists | `@tanstack/react-virtual` | `react-virtuoso` | Virtuoso handles variable heights and chat lists with less code |
| Server state | `@tanstack/react-query` | `swr` | Not needed where Server Components fetch the data |
| Client state | `zustand` | `jotai` | Jotai for many small independent atoms |
| Routing outside a framework | `@tanstack/react-router` | `react-router` | |
| Charts | `recharts` | `echarts`, `@visx/visx`, `chart.js`, `d3` | ECharts for large datasets on canvas; visx or D3 for custom charts |
| Dates | `date-fns` | `dayjs`, `temporal-polyfill` | `Intl` covers formatting alone |
| Drag and drop | `@dnd-kit/core` | `@atlaskit/pragmatic-drag-and-drop` | dnd kit's core had no release since 2024-12; Pragmatic is smaller and framework-neutral |
| Rich text editor | `@tiptap/core` | `lexical` | Tiptap: collaboration and some extensions are paid |
| Code editor | `codemirror` | `monaco-editor` | Monaco is several megabytes; use it for an IDE-like editor |
| Maps | `maplibre-gl` | `leaflet` | Leaflet's last stable release is from 2023; fine for simple raster maps |
| Carousel | `embla-carousel` | | shadcn/ui's carousel wraps it |
| Icons | `lucide-react` | `@phosphor-icons/react` | One icon set per project |
| Translations | `i18next` | `next-intl`, `@inlang/paraglide-js` | next-intl for the Next.js App Router; Paraglide compiles messages and tree-shakes |
| File upload | `react-dropzone` | `@uppy/core` | Uppy for resumable uploads and remote sources |
| PDF | `react-pdf` (viewing) | `pdf-lib` (creating, editing) | pdf-lib had no release since 2021 |
| Markdown | `react-markdown` | `@mdx-js/mdx` | Sanitise untrusted Markdown |
| Class names | `clsx` with `tailwind-merge` | `class-variance-authority` | cva for component variants |
| Dark mode | `next-themes` | | |
| Syntax highlighting | `shiki` | | Run it on the server where possible |
| One-time code input | `input-otp` | | |

## Vue
| Need | Default | Alternatives | Notes |
| --- | --- | --- | --- |
| State | `pinia` | | |
| Composables | `@vueuse/core` | | |
| Components | `shadcn-vue` on `reka-ui` | `@nuxt/ui` | Nuxt UI in Nuxt projects |
| Forms | `vee-validate` | `@tanstack/vue-form` | |
| Server state, tables, virtual lists | TanStack's Vue packages | | Same APIs as the React rows above |
