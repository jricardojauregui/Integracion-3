# Tarea 3 — Auditoría del contrato WSDL (extensión de CONTRACT_AUDIT.md)

El Paso 10 ya audita campo por campo. Esta tarea pide la vista
complementaria: **operación por operación**, más riesgos concretos.

## Tabla operación → exposición

| Operación | Columnas del monolito que expone | Columnas que transforma | Columnas que oculta deliberadamente |
|---|---|---|---|
| `ObtenerConceptosPendientes` | `libros.isbn`, `libros.titulo`, `conceptos.nombre` | `generos.nombre` (N:M) se colapsa en un solo string `categoria` vía `string_agg` | `libros.precio`, `stock`, `id_formato`, `created_at/updated_at`, `libro_concepto.definicion` |
| `RegistrarClasificacion` | Ninguna del monolito se **devuelve**; `isbn`/`idConcepto` se **reciben** como entrada, se validan contra el catálogo pero no se reflejan de vuelta | El resultado (`idClasificacion`) es un ID de una tabla propia, no del monolito | Todo lo demás del libro/concepto — la operación no necesita mostrarlo, solo confirmar |
| `ObtenerProgresoUsuario` | Ninguna directa del monolito | `totalPendientes` es un **agregado calculado** (`count(*)` sobre la vista), no una columna real | Cualquier detalle de cuáles conceptos exactos están pendientes (para eso está la otra operación) |
| `RegistrarClasificador` | Ninguna del monolito | — | Se comunica explícitamente que NO usa `usuarios` (Paso 1) |
| `ObtenerEstadisticasPorModelo` (Tarea 1) | Ninguna del monolito | Conteos agregados por `modelo_cloud` | Quién clasificó cada cosa (no expone `id_clasificador` individual, solo el total) |

## Riesgos identificados y mitigación

1. **Riesgo — enumeración de conceptos por fuerza bruta de `idConcepto`.**
   `RegistrarClasificacion` acepta cualquier entero como `idConcepto` y
   distingue "no encontrado" de "duplicado" con Faults distintos — un
   atacante podría iterar IDs para mapear qué conceptos existen.
   **Mitigación:** el catálogo de conceptos no es secreto (es contenido
   de un catálogo público de librería, no datos personales), así que el
   riesgo real es bajo; si se necesitara mitigar, se podría devolver el
   mismo Fault genérico para "no encontrado" en vez de dos códigos
   distintos — trade-off contra la utilidad del mensaje para el cliente
   legítimo (documentado en Paso 13).

2. **Riesgo — acoplamiento por compartir la base de datos con el
   monolito.** Si el monolito cambiara el tipo o el nombre de
   `libros.isbn`, las FKs de `clasificaciones_cloud` y las vistas
   (`vw_conceptos_pendientes`) se romperían sin que el WSDL lo avise.
   **Mitigación:** las FKs con `ON DELETE RESTRICT` (Paso 7) hacen que
   cualquier incompatibilidad falle de forma ruidosa (un error de FK)
   en vez de silenciosa; a mediano plazo, la mitigación real es dejar de
   compartir la base (ver pregunta de reflexión en `METRICS.md`).

3. **Riesgo — credenciales WS-Security de un solo usuario compartido
   (Tarea 1).** `ObtenerEstadisticasPorModelo` usa un único par
   usuario/contraseña para todo el mundo que necesite estadísticas — no
   hay manera de saber *quién* las consultó, ni de revocar acceso a una
   persona sin cambiarle la contraseña a todos.
   **Mitigación real necesaria más allá de esta etapa:** una tabla de
   credenciales por operador (varias filas, cada una con su propio hash)
   en vez de una sola constante en `.env` — documentado como limitación
   conocida en `ENGINEERING_DECISIONS_SOAP.md`, decisión #7.

4. **Riesgo — el correo del clasificador (Paso 14) no se valida como
   identidad.** `RegistrarClasificador` acepta cualquier string como
   `correo`, sin verificar que le pertenezca a quien lo escribió.
   **Mitigación:** por diseño no se usa para nada sensible (ni
   autenticación, ni autorización — ver `soap/service.py`), así que un
   correo falso no compromete ninguna operación protegida; si se
   necesitara confiar en él (p. ej. para notificaciones), habría que
   agregar verificación por link de confirmación, fuera del alcance de
   este ejercicio.

## Conclusión sobre contrato estricto y mantenibilidad

Un contrato que expone solo lo que cada operación necesita (en vez de
"todo lo que hay en la tabla, por si acaso") cuesta más pensar al
diseñarlo — cada campo nuevo exige volver a esta tabla y justificarlo —
pero paga esa inversión en dos formas concretas: (1) un cambio interno
del monolito (agregar una columna, renombrar otra) no obliga a tocar el
contrato mientras no afecte a los campos ya expuestos, y (2) cualquier
cliente que lea el WSDL sabe exactamente qué puede pedir y qué va a
recibir, sin tener que adivinar qué columnas "sobran" en la respuesta.
El costo de mantenimiento se paga una vez, al diseñar; el beneficio de
seguridad y de contrato claro se cobra en cada cliente nuevo que se
conecta sin tener que leer el código del servidor.
