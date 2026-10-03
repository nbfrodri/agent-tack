# Documentación

La documentación se actualiza en el mismo cambio que el código que la afecta; documentación desfasada es peor que ninguna.

## Checklist al cerrar una tarea
- ¿Cambió cómo se instala, configura o ejecuta? → README.
- ¿Nuevas variables de entorno o configuración? → README y `.env.example` (sin valores reales).
- ¿Cambió una API pública, CLI o endpoint? → docs de referencia y ejemplos.
- ¿Cambio visible para usuarios? → CHANGELOG (si existe).
- ¿Decisión de arquitectura relevante o difícil de revertir? → ADR.
- ¿Nuevo concepto de dominio? → glosario / lenguaje ubicuo si el proyecto lo tiene.

## README (estructura recomendada para proyectos nuevos)
```markdown
# Project name
One-line description.

## Features
## Requirements
## Installation
## Configuration      (env vars table)
## Usage              (real commands/examples that work)
## Development        (run tests, lint, project structure)
## Architecture       (short overview or link to docs/)
## Contributing       (branch + commit conventions)
## License
```
Comprueba que los comandos del README realmente funcionan.

## ADR (Architecture Decision Records)
Archivo `docs/adr/NNNN-short-title.md`:
```markdown
# NNNN. Title
Date: YYYY-MM-DD
Status: Proposed | Accepted | Superseded by NNNN

## Context
## Decision
## Consequences
```

## CHANGELOG
Formato Keep a Changelog: sección `## [Unreleased]` con `Added / Changed / Fixed / Removed / Security`.

## Comentarios y docstrings
Documenta las APIs públicas (docstrings/JSDoc/rustdoc según el lenguaje). En el código interno, comenta el porqué, no el qué.
