# Git y GitHub

## Conventional Commits

Formato:
```
<type>(<scope opcional>): <subject>

<body opcional: el porqué, no el qué>

<footer opcional: BREAKING CHANGE: …, Closes #123>
```

Tipos:
| Tipo | Uso |
| --- | --- |
| `feat` | Nueva funcionalidad para el usuario |
| `fix` | Corrección de un bug |
| `refactor` | Cambio de código sin cambiar comportamiento |
| `test` | Añadir o corregir tests |
| `docs` | Solo documentación |
| `style` | Formato, espacios; sin cambio de lógica |
| `perf` | Mejora de rendimiento |
| `build` | Sistema de build, dependencias |
| `ci` | Configuración de CI |
| `chore` | Mantenimiento que no encaja en lo anterior |
| `revert` | Revierte un commit anterior |

Reglas del subject: imperativo ("add", no "added"), minúscula inicial, sin punto final, ≤ 72 caracteres. Cambio incompatible: `feat(api)!: …` y footer `BREAKING CHANGE: …`.

Ejemplos:
- `feat(auth): add JWT refresh token rotation`
- `fix(cart): prevent negative quantities on update`
- `refactor(orders): extract pricing policy into domain service`
- `test(orders): cover discount edge cases`
- `docs(readme): document required environment variables`

En TDD, el test y el código que lo hace pasar suelen ir en el mismo commit (`feat`/`fix`); el refactor posterior, en un commit `refactor` aparte.

## Sin atribución de IA

Los hooks globales de git lo hacen cumplir: `commit-msg` borra estas líneas y exige Conventional Commits, y `pre-push` impide reescribir `main`. Si un hook rechaza algo, corrige la causa; nunca uses `--no-verify`.


No añadas trailers `Co-Authored-By` de ninguna IA, ni "🤖 Generated with …", ni menciones a Claude/Codex/ChatGPT en commits, PRs, issues, tags o changelogs. Usa la identidad de git configurada por el usuario (`git config user.name/user.email`) y no la cambies.

## Ramas

- `main` (o `master`) siempre desplegable; nunca commits directos para cambios no triviales.
- Nombres: `<type>/<kebab-case-description>`, p. ej. `feat/order-discounts`, `fix/login-redirect-loop`. Si hay issue: `feat/123-order-discounts`.
- Ramas cortas; actualiza con `git rebase` de main mientras la rama sea solo local.

## Qué hacer sin preguntar y qué no

Sin preguntar: `status`, `diff`, `log`, crear ramas, `add`, `commit`, `stash`, rebase de commits locales no publicados.

Pregunta antes: `push`, crear/editar PRs o issues, `merge`, rebase o amend de commits ya publicados, borrar ramas, crear tags/releases. **Nunca** force-push a `main`/`master`; en otras ramas, solo `--force-with-lease` y con permiso.

Antes de commitear: revisa `git diff --staged`, que no entren secretos, archivos generados ni cambios ajenos a la tarea. No uses `git add -A` a ciegas.

## Pull Requests

Los PRs se integran con **squash merge**: el título del PR se convierte en el commit de `main`, así que debe ser un Conventional Commit válido (ver `conventions.md`). Título en formato Conventional Commit. Cuerpo:
```markdown
## Summary
What changes and why (1-3 sentences).

## Changes
- …

## How to test
Steps or commands to verify.

## Notes
Risks, follow-ups, screenshots if UI.

Closes #123
```
Para trabajar a partir de issues, redactarlos o dividir un plan en issues, sigue la skill `github-issues`.

PRs pequeños y revisables; si crece mucho, divídelo. Usa `gh` para crear PRs (`gh pr create --title … --body …`), siempre con permiso del usuario.

## Versionado y releases

SemVer: `fix` → patch, `feat` → minor, breaking → major. Si el proyecto tiene CHANGELOG, actualízalo siguiendo Keep a Changelog. Para hacer una release (versión, tag, GitHub Release, automatización), sigue la skill `release`.
