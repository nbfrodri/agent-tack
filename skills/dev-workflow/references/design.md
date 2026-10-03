# Diseño: SOLID, DDD y otras prácticas

## SOLID
- **S – Single Responsibility:** cada módulo/clase tiene una sola razón para cambiar. Si describirla necesita "y", probablemente son dos.
- **O – Open/Closed:** extiende el comportamiento añadiendo código (nuevas implementaciones, estrategias) en vez de modificar lo que ya funciona, cuando se espera variación real.
- **L – Liskov Substitution:** una implementación debe poder sustituir a su abstracción sin sorpresas (sin lanzar "not supported", sin endurecer precondiciones).
- **I – Interface Segregation:** interfaces pequeñas y específicas del cliente, mejor que una grande.
- **D – Dependency Inversion:** el dominio depende de abstracciones (puertos); la infraestructura las implementa. Inyecta dependencias por constructor.

No crees abstracciones especulativas: aplica O y D cuando haya al menos dos implementaciones o un borde de I/O claro. YAGNI y KISS también son buenas prácticas.

## DDD
Úsalo cuando haya un dominio de negocio con reglas reales (pedidos, pagos, reservas, inventario…). Para CRUDs simples, utilidades o scripts, basta con una buena separación de capas.

**Estratégico**
- **Lenguaje ubicuo:** usa en el código los mismos términos que el negocio. Si un concepto no tiene nombre claro, pregúntalo.
- **Bounded contexts:** separa modelos que significan cosas distintas en contextos distintos (p. ej. `Customer` en facturación vs. en soporte). Comunícalos por interfaces o eventos, no compartiendo entidades.

**Táctico**
- **Entidades:** identidad propia y ciclo de vida.
- **Value Objects:** inmutables, definidos por sus valores, con validación en el constructor (`Email`, `Money`, `Quantity`). Prefiérelos a primitivos.
- **Agregados:** grupo de objetos con una raíz que protege las invariantes. Se modifica solo a través de la raíz; una transacción = un agregado. Mantenlos pequeños.
- **Repositorios:** interfaz en el dominio, implementación en infraestructura; uno por agregado.
- **Servicios de dominio:** lógica que no pertenece a una sola entidad.
- **Eventos de dominio:** hechos pasados (`OrderPlaced`) para desacoplar efectos secundarios.
- **Servicios de aplicación / casos de uso:** orquestan; no contienen reglas de negocio.

Evita el modelo anémico: las reglas viven en las entidades y value objects, no en servicios que manipulan getters/setters.

## Arquitectura por capas (hexagonal / clean)
```
src/
  domain/          # entidades, VOs, agregados, eventos, puertos (interfaces). Sin dependencias de frameworks.
  application/     # casos de uso; orquestan dominio y puertos.
  infrastructure/  # BD, HTTP clients, colas: implementan los puertos.
  interfaces/      # controladores, CLI, UI: adaptan la entrada a casos de uso.
```
Las dependencias apuntan hacia dentro: `interfaces → application → domain`, e `infrastructure → domain`. El dominio nunca importa infraestructura. Adapta los nombres de carpetas a las convenciones del lenguaje/framework y del proyecto.

## Otras prácticas
- **DRY** con criterio: duplica antes que acoplar cosas que solo se parecen por casualidad.
- **Composición antes que herencia.**
- **Fail fast:** valida en los bordes y en los constructores de VOs.
- **Inmutabilidad** por defecto cuando el lenguaje lo facilite.
- **Ley de Demeter:** no encadenes `a.b().c().d()` a través de objetos ajenos.
- **Código limpio:** sin código muerto, sin comentarios que repiten el código; los comentarios explican el *porqué*.
