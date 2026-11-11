---
name: showcase-ui
description: "Add showcase effects from Aceternity UI, Magic UI, RareUI or 21st.dev to React landing pages. Use only when the user asks for these libraries or for eye-catching effects."
---

# Showcase UI

Showcase libraries ship striking effects (beams, spotlights, particles, marquees, animated gradients, 3D cards) as copy-paste React, Tailwind and motion code. One effect, chosen on purpose, can make a hero section; several at once produce the look people recognise as generated. Build the page on the base libraries the `frontend` skill recommends (shadcn/ui on Base UI or Radix) and treat each effect as an accent.

| Library | What it offers | How it arrives |
| --- | --- | --- |
| [Aceternity UI](https://ui.aceternity.com) | Hero backgrounds, spotlights, beams, 3D and parallax cards | Copied code or shadcn registry; some components and templates are paid (Pro) |
| [Magic UI](https://magicui.design) | Animated text, marquees, number tickers, bento grids, shimmer buttons | shadcn registry (`npx shadcn add` with its URL) |
| [RareUI](https://rareui.in) | Animated components with themes, variants and spring settings | Its CLI copies source into the project and configures Tailwind and motion |
| [21st.dev](https://21st.dev) | Community marketplace of components, uneven quality | shadcn registry per component; its Magic MCP server needs an API key |

## Steps
1. Confirm the page and the section that get the effect, and keep the rest of the page on the base components. Done when each effect has one named place.
2. Prefer an effect whose registry or CLI fits the project's stack (Tailwind version, motion library); read the copied code before keeping it, since it becomes the project's code.
3. Make every effect respect `prefers-reduced-motion` (static fallback), keep text contrast at 4.5:1 over animated backgrounds, and keep the content readable without the effect.
4. Check the cost: new dependencies in `package.json`, client-only code (lazy-load heavy canvas or particle effects) and a look at the page at mobile width. Done when the user has seen the added dependencies and the page renders well on mobile and desktop.
