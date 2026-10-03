# Documentación

La documentación se actualiza en el mismo cambio que el código que la afecta; documentación desfasada es peor que ninguna. Estructura, plantillas, documentación para IA y para humanos, planes, auditorías y handoffs: skill `project-docs`.

## Checklist al cerrar una tarea
- ¿Cambió cómo se instala, configura o ejecuta? → `README.md`, `docs/development.md` y `AGENTS.md` (comandos).
- ¿Nuevas variables de entorno o configuración? → `.env.example` (sin valores reales) y `docs/development.md`.
- ¿Cambió una API pública, CLI o endpoint? → `docs/api.md` o la referencia generada, y ejemplos.
- ¿Cambio visible para usuarios? → `CHANGELOG.md` (si existe).
- ¿Cambió la arquitectura (componentes, flujos, dependencias externas)? → `docs/architecture.md` y `docs/overview.md`.
- ¿Decisión de arquitectura relevante o difícil de revertir? → ADR en `docs/adr/`.
- ¿Nuevo concepto de dominio? → `docs/glossary.md`.
- ¿Había un plan? → actualiza su estado en `docs/plans/`.
- ¿Tarea significativa hecha con IA? → una fila en `docs/ai/log.md`.
- ¿Se queda a medias? → handoff en `docs/handoffs/`.

## CHANGELOG
Formato Keep a Changelog: sección `## [Unreleased]` con `Added / Changed / Fixed / Removed / Security` (ver skill `release`).

## Comentarios y docstrings en el código
Ver `conventions.md`: por defecto sin comentarios; solo el porqué no obvio y docstrings en la API pública.
