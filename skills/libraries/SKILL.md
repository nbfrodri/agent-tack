---
name: libraries
description: "Choose a library for a need from a catalog by domain (web UI, motion and 3D, JS backend, Python, data and ML, Go, Rust, PHP, .NET, mobile, shell). Use before adding a dependency or hand-writing what a library covers."
---

# Libraries

A maintained library usually beats hand-written code for a solved problem, and what the project already depends on beats a new dependency. The catalog gives a default and its alternatives per need; the user chooses what gets installed.

## Steps
1. **Name the need and look in the project.** Read the manifest, the lockfile and the code for something that already covers it, including the framework and the standard library. Done when you can say the project has nothing for this need; otherwise use what is there.
2. **Read the one catalog file for the domain.**

   | Work | File |
   | --- | --- |
   | React and Vue interfaces: forms, tables, charts, state, editors, maps | `references/web-ui.md` |
   | Animation, scroll, 3D, canvas, physics, audio | `references/web-motion-3d.md` |
   | Node, Bun and edge servers in TypeScript; JS tooling | `references/js-backend.md` |
   | Python applications, APIs and tools | `references/python.md` |
   | Dataframes, plots, machine learning, pipelines | `references/data-ml.md` |
   | Go | `references/go.md` |
   | Rust | `references/rust.md` |
   | PHP and Laravel | `references/php-laravel.md` |
   | .NET | `references/dotnet.md` |
   | React Native and Expo | `references/mobile.md` |
   | Shell scripts and command-line tools | `references/shell-cli.md` |

3. **Propose and stop.** Present the default and one or two alternatives from the row: when each fits, its licence, and its cost (bundle size, runtime limits, paid tier). Ask through the tool's question prompt when it has one. Done when the user has chosen. A need without a row follows the search order in `dev-workflow`, and the result is proposed the same way.
4. **Check the registry before installing.** The catalog was checked on 2026-11-11 and ages: confirm the latest version, its release date and its licence in the package registry, and read the notes column for traps. Done when the installed version is current and the user has seen the new dependency.
