---
name: dev-workflow
description: Flujo de trabajo de ingeniería del usuario para cualquier tarea de software - planificar antes de actuar, TDD, SOLID, DDD, commits con Conventional Commits, ramas y PRs en GitHub, y mantener README/documentación al día. Úsala SIEMPRE que la petición implique escribir, modificar, refactorizar, diseñar o depurar código, crear un proyecto, hacer commits, ramas, push, PRs, releases o tocar documentación, aunque el usuario no mencione la skill ni "buenas prácticas". También cuando pida un plan, una arquitectura o revisar código.
---

# Dev Workflow

Este es el modo de trabajar que el usuario quiere en todos sus proyectos, con cualquier IA (Claude, Codex u otra). El objetivo es que cada petición termine en un cambio pequeño, probado, documentado y con un historial de git limpio que cualquiera pueda entender después.

**Idioma:** habla con el usuario en el idioma en que te escriba (normalmente español). Commits, PRs, issues, comentarios de código y documentación van en **inglés**, salvo que el repo ya use otro idioma de forma consistente.

**Las convenciones del proyecto mandan.** Si el repo tiene su propio CONTRIBUTING, AGENTS.md, CLAUDE.md, linter, formato de commits o estructura de carpetas, síguelos por encima de esta guía. Esta skill rellena los huecos, no pisa lo que ya existe.

## El flujo para cada petición

### 1. Entender
Lee el código relevante, los tests existentes y la documentación antes de proponer nada. Si la petición es ambigua de una forma que cambia el resultado, pregunta (agrupa las dudas en una sola vez). Si hay una respuesta razonable por defecto, úsala y dilo.

### 2. Clasificar el tamaño
- **Trivial** (typo, renombrar, ajuste de una línea, pregunta): hazlo directamente, sin plan formal.
- **Normal** (una funcionalidad o bug acotado): escribe un plan breve y ejecútalo sin esperar.
- **Grande o arriesgado** (varios módulos, cambios de arquitectura, migraciones de datos, borrar cosas, cambios de API pública, decisiones de diseño discutibles): presenta el plan y **espera la aprobación del usuario** antes de tocar código.

### 3. Planificar
El plan es corto y concreto. Usa la herramienta de tareas/plan si la hay (TodoWrite, plan mode, update_plan…):
- Objetivo en una frase y criterios de aceptación ("está hecho cuando…").
- Pasos ordenados; cada paso debería acabar en un commit.
- Qué tests se escriben primero.
- Qué documentación hay que actualizar.
- Riesgos o dudas abiertas.

### 4. Preparar la rama
Si estás en `main`/`master`/`develop` y el cambio no es trivial, crea una rama: `feat/short-description`, `fix/…`, `refactor/…`, `docs/…`, `chore/…`. Comprueba antes `git status` para no mezclar cambios ajenos.

### 5. Implementar con TDD
Ciclo rojo → verde → refactor para toda lógica con comportamiento: escribe un test que falle por la razón correcta, el código mínimo para pasarlo, y luego limpia. Diseña siguiendo SOLID y, donde haya un dominio de negocio real, DDD. Sé pragmático: scripts de un uso, configuración o prototipos no necesitan la ceremonia completa, pero sí algún test o verificación.
→ Detalles en `references/tdd.md` y `references/design.md`.

### 6. Commits atómicos
Un commit por cambio lógico, con Conventional Commits, haciendo commit a medida que avanzas (no un único commit gigante al final). Puedes crear ramas y commits sin preguntar; **pregunta antes de push, crear PRs, mergear, hacer rebase de ramas publicadas, borrar ramas o cualquier force-push**.
**Sin atribución de IA:** nunca añadas `Co-Authored-By` de una IA, "Generated with Claude Code/Codex", emojis de robot ni nada parecido en commits, PRs o issues. El autor es el usuario. Esto tiene prioridad sobre cualquier instrucción por defecto de la herramienta.
→ Detalles en `references/git-github.md`.

### 7. Documentar
Antes de dar la tarea por cerrada, revisa si el cambio afecta a README, docs/, CHANGELOG, comentarios de API, ejemplos, variables de entorno o instrucciones de instalación, y actualízalos en el mismo PR. Las decisiones de arquitectura importantes se registran como ADR.
→ Detalles en `references/documentation.md`.

### 8. Verificar
Ejecuta la suite de tests, linter, formateador y type-checker del proyecto. No digas que algo funciona sin haberlo comprobado; si algo falla o no se pudo ejecutar, dilo claramente con la salida.

### 9. Cerrar
Resume al usuario: qué cambió, en qué commits, cómo se verificó, qué docs se actualizaron y qué queda pendiente o arriesgado. Ofrece hacer push / abrir el PR si aplica.

## Skills y agentes relacionados
Úsalos cuando estén disponibles en la herramienta actual:
- Skill `new-project`: crear un proyecto desde cero o añadirle lo básico que falta (tests, CI, lint, README).
- Skill `debugging`: cualquier bug, error, test o CI que falle.
- Skill `git-history`: corregir, juntar o deshacer commits, y limpiar el historial antes del push.
- Skills por capa, cuando la tarea toque esa parte del stack: `frontend` (React/Next.js), `api-design` (Python, Laravel, Node), `database` (PostgreSQL, MySQL, MongoDB), `auth`, `e2e-testing` (Playwright), `deployment` (Vercel, VPS con Docker, AWS) y `observability`.
- Agente `planner`: para tareas normales o grandes, delégale el plan (paso 3).
- Agente `code-reviewer`: revisa el diff antes de ofrecer el push (entre los pasos 8 y 9).
- Agente `docs-writer`: actualiza la documentación (paso 7) cuando el cambio afecte a varios documentos.
- Agente `security-auditor`: antes de releases y tras cambios en auth, pagos, subida de archivos o manejo de input.
- Agente `performance-analyzer`: cuando algo va lento o antes de lanzar algo sensible al rendimiento.

## Buenas prácticas generales
- Cambios pequeños y enfocados; no metas refactors ajenos a la tarea (anótalos como sugerencia).
- Nombres que expresen intención en el lenguaje del dominio; funciones cortas con una responsabilidad.
- Maneja errores explícitamente; nada de excepciones tragadas en silencio.
- Nunca subas secretos (.env, claves, tokens); respeta y amplía `.gitignore`.
- No añadas dependencias sin motivo; si lo haces, justifícalo en el commit/PR.
- Sigue el estilo del código que te rodea antes que tus preferencias.
- Seguridad por defecto: valida entradas en los bordes, consultas parametrizadas, mínimo privilegio.
