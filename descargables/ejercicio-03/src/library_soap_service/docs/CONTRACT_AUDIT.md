# Auditoría del contrato — Módulo SOAP (Ejercicio04, Paso 10)

Regla de ingeniería aplicada: **el contrato expone capacidades y datos
necesarios, no la estructura completa de la base de datos.** Revisión
campo por campo de cada tabla que el módulo toca (catálogo de solo
lectura del monolito + tablas propias), contra las 4 operaciones
definidas en `wsdl/library-classifier.wsdl` (Paso 9).

## Catálogo del monolito (solo lectura — ver Paso 1)

| Dato | ¿Se expone? | Justificación |
|---|---|---|
| `libros.isbn` | Sí | El cliente necesita identificar exactamente qué libro está clasificando. |
| `libros.titulo` | Sí | Igual — es lo que el humano ve en el clasificador de escritorio, no un ID interno. |
| `generos.nombre` (categoría) | Sí | Pedido explícitamente por `ObtenerConceptosPendientes` ("información necesaria del libro y categoría"). |
| `libros.anio_publicacion` | No | Ninguna de las 4 operaciones lo necesita; no aporta a la tarea de clasificación. |
| `libros.precio` | No | Dato comercial interno del catálogo — irrelevante para clasificar un concepto y expone información de negocio innecesaria. |
| `libros.stock` | No | Mismo criterio que precio: dato operativo interno del monolito. |
| `libros.id_formato` / `formatos.nombre` | No | No lo pide ninguna operación del contrato mínimo. |
| `libros.created_at` / `updated_at` | No | Metadata interna del monolito — el cliente SOAP no necesita saber cuándo se editó el libro. |
| `conceptos.id_concepto` | Sí | Identificador opaco que el cliente debe reenviar en `RegistrarClasificacion` — no es una columna "interna", es la clave de negocio del concepto. |
| `conceptos.nombre` | Sí | El texto del concepto — es literalmente lo que se está clasificando. |
| `libro_concepto.definicion` | No | Útil para un humano, pero ninguna de las 3 operaciones mínimas del Paso 9 la pide; se puede agregar como campo opcional en una versión futura del contrato si se justifica. |
| Cualquier columna de `usuarios` (email, password_hash, es_administrador) | **No, nunca** | Fuera de alcance por completo desde el Paso 1 — es autenticación del monolito, ni siquiera el rol `soap_module_user` tiene privilegios sobre esta tabla (Paso 8). |
| Credenciales de conexión a PostgreSQL | No | Información sensible interna — vive en `.env`, nunca en el contrato ni en ninguna respuesta. |

## Tablas propias del módulo

| Dato | ¿Se expone? | Justificación |
|---|---|---|
| `clasificadores.id_clasificador` | Sí | Necesario en `RegistrarClasificacion` y `ObtenerProgresoUsuario` para saber de quién es la clasificación/el progreso. |
| `clasificadores.nombre` / `apellido` | Sí, solo como **entrada** en `RegistrarClasificador` | El propio cliente los provee; el contrato nunca los *devuelve* en una consulta de otro clasificador — no hay operación que exponga el nombre de alguien más. |
| `clasificaciones_cloud.id_clasificacion` | Sí (solo como confirmación) | `RegistrarClasificacionResponse` lo devuelve como comprobante de que la escritura ocurrió — es la forma mínima de confirmar éxito sin reexponer todo el registro. |
| `clasificaciones_cloud.modelo_cloud` | Sí | Es el resultado mismo de la clasificación — el dato central de todo el ejercicio. |
| `clasificaciones_cloud.totalClasificados` / `totalPendientes` (agregados, no columnas reales) | Sí | Estos son cálculos derivados para `ObtenerProgresoUsuario`, no una columna expuesta directamente — cumple el mismo principio: se expone la capacidad ("cuánto llevo"), no la tabla cruda. |
| `clasificaciones_cloud.fecha_clasificacion` | Solo si aplica | No la pide ninguna de las 3 operaciones mínimas del Paso 9; si más adelante se agrega un historial/auditoría visible al cliente, ahí se justificaría exponerla. Por ahora, no. |
| `clasificaciones_cloud.id_cliente_servido` | No | Es dato de auditoría interna del módulo (qué instancia de cliente sirvió la petición) — no tiene utilidad para quien consume el contrato. |
| `clasificaciones_cloud.created_at` | No | Metadata interna, redundante con `fecha_clasificacion` para efectos del cliente. |
| Cualquier columna de `clientes_servidos` (tipo_cliente, identificador_cliente, peticiones_atendidas, etc.) | No | Ninguna de las 4 operaciones del contrato la lee ni la devuelve — el conteo de peticiones es contabilidad interna del módulo, no una capacidad que el cliente consulte. |

## Conclusión

Los tipos XSD del WSDL (`ConceptoPendienteType`, los `*Request`/`*Response`
de cada operación) contienen exactamente las columnas marcadas "Sí" de
esta tabla — ninguna más. Es la misma disciplina que ya se aplicó en
`docs/SECURITY_REVIEW.md` del Ejercicio02: minimizar superficie expuesta,
documentando el porqué de cada exclusión en vez de solo omitirla en
silencio.
