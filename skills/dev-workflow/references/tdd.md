# Test-Driven Development

## El ciclo
1. **Rojo:** escribe un test pequeño que describa el siguiente comportamiento. Ejecútalo y confirma que falla *por la razón esperada* (no por un import roto).
2. **Verde:** escribe el código mínimo para que pase. Nada de funcionalidad especulativa.
3. **Refactor:** con los tests en verde, elimina duplicación y mejora nombres y estructura. Los tests siguen en verde tras cada paso.

Repite en pasos pequeños: un comportamiento por ciclo, no toda la batería de tests de golpe. Empieza por el caso más simple y ve añadiendo casos límite. Los ciclos cortos hacen que cada fallo apunte a un único cambio.

En un módulo nuevo, el primer rojo suele ser un `ImportError`, que no prueba nada del comportamiento. Crea primero la interfaz mínima (firmas que lanzan `NotImplementedError` o devuelven un valor vacío) para que el test falle en la aserción.

## Bugs
Antes de arreglar un bug, escribe un test que lo reproduzca y falle. Así el arreglo queda demostrado y protegido contra regresiones.

## Buenos tests
- Nombre que describe el comportamiento: `rejects_order_when_stock_is_insufficient`.
- Estructura Arrange / Act / Assert (o Given / When / Then).
- Prueban comportamiento observable, no detalles de implementación.
- Rápidos, deterministas e independientes entre sí; nada de depender del orden, la hora real o la red.
- Una razón para fallar por test.

## Pirámide
- **Unitarios** (la mayoría): dominio y lógica pura, sin I/O.
- **Integración:** repositorios, adaptadores, base de datos real o de test.
- **End-to-end** (pocos): los flujos críticos.

Usa dobles de test (fakes, stubs, mocks) solo en los bordes (red, BD, reloj, servicios externos), no para aislar cada clase del dominio.

## Pragmatismo
- Lógica de negocio, cálculos, validaciones, parsing: TDD estricto.
- UI, glue code, configuración, scripts de un solo uso, spikes exploratorios: basta con verificación razonable (un test de humo o ejecución manual documentada). Si el spike se queda, añade tests antes de darlo por terminado.
- Si el proyecto no tiene tests, prepara el framework de test estándar del ecosistema (pytest, vitest/jest, go test, cargo test…) como primer paso, en su propio commit.
