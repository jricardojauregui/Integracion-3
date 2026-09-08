# Decisiones de ingeniería — Módulo SOAP (Ejercicio04)

Universidad de Monterrey · Integración de Aplicaciones Computacionales

Formato por decisión: **Necesidad → Decisión → Justificación → Ventajas → Limitaciones**

---

## 1. Framework del servicio: Flask (Python)

- **Necesidad:** exponer un servicio HTTP nuevo, independiente del monolito, que reciba y responda XML.
- **Decisión:** Flask puro, sin blueprints, un solo archivo de entrada (mismo patrón ya usado en el microservicio REST del Ejercicio03).
- **Justificación:** el enunciado lo pide explícitamente; Flask no impone una capa de serialización JSON automática como otros frameworks, lo que deja el cuerpo de la petición/respuesta completamente bajo control manual — necesario porque el XML se arma a mano.
- **Ventajas:** curva de aprendizaje mínima, control total sobre el ciclo request/response, fácil de correr como proceso independiente en la misma VM o en otra.
- **Limitaciones:** sin blueprints, todas las rutas viven en un solo archivo — aceptable al tamaño de este ejercicio (3–5 operaciones), no escalaría a un servicio grande sin reestructurar.

## 2. Protocolo: SOAP (no REST)

- **Necesidad:** el ejercicio exige explícitamente un contrato SOAP, no una API REST.
- **Decisión:** un único endpoint `POST /soap` que recibe siempre un `Envelope` SOAP; la operación a ejecutar se determina leyendo el elemento hijo de `Body` (o el header `SOAPAction`), no por la URL.
- **Justificación:** así es como funciona SOAP real — un solo punto de entrada, contrato-driven, en vez de una URL por recurso como en REST.
- **Ventajas:** el contrato (WSDL) es la única fuente de verdad sobre qué operaciones existen; cualquier cliente SOAP genérico puede descubrirlas sin leer el código Python.
- **Limitaciones:** depurar es menos cómodo que REST (no se puede "probar en el navegador"); todo el enrutamiento interno de operaciones es responsabilidad nuestra, no del framework.

## 3. Contrato: WSDL + XSD antes de programar

- **Necesidad:** el ejercicio pide explícitamente definir el contrato antes de escribir código, y que sea reproducible por otros clientes.
- **Decisión:** `library.wsdl` (portType, binding document/literal, service) + `library-types.xsd` (tipos) como archivos versionados en el repo, escritos y congelados antes de tocar `libros_soap_service.py`.
- **Justificación:** es la práctica estándar de integración SOAP — el contrato es lo que hace interoperable al servicio; programar primero y documentar después invierte el orden que pide el ejercicio y arriesga que el código y el contrato se desincronicen.
- **Ventajas:** el `.xsd` documenta los tipos de forma validable (un XML se puede validar contra él); separar tipos (`.xsd`) de operaciones (`.wsdl`) permite reusar los tipos si se agregan más operaciones después.
- **Limitaciones:** el WSDL se escribió a mano (no generado desde código), así que un cambio en el modelo de datos obliga a actualizar WSDL, XSD y el servidor por separado — no hay una sola fuente generando los tres.

## 4. Acceso a PostgreSQL: psycopg2 directo (sin ORM)

- **Necesidad:** consultar y escribir en la misma base de datos que usa el monolito, sin arriesgar su integridad.
- **Decisión:** `psycopg2` puro con SQL parametrizado, igual que el patrón ya usado en `apps/web-monolith` (driver `pg`) y en el microservicio REST del Ejercicio03 — nada de ORM, nada de migraciones automáticas.
- **Justificación:** el ejercicio lo exige explícitamente ("Utiliza exclusivamente psycopg2"); además evita que una herramienta de ORM intente "administrar" el esquema y toque tablas del monolito por accidente.
- **Ventajas:** control fino sobre cada query, coherencia con el resto del proyecto, sin dependencias pesadas.
- **Limitaciones:** SQL escrito a mano en cada operación; sin capa de abstracción que valide tipos antes de llegar a PostgreSQL (la validación es responsabilidad del código Python contra el XSD).

## 5. Tablas propias del módulo (sin tocar el esquema del monolito)

- **Necesidad:** registrar clasificaciones Cloud y clasificadores atendidos sin modificar el esquema funcional existente ni reutilizar `usuarios`.
- **Decisión:** dos tablas nuevas, propias del módulo: `soap_clasificadores` (identifica a quien usa el clasificador) y `soap_clasificaciones` (una fila por clasificación Cloud registrada, con `UNIQUE(isbn, id_concepto)` para bloquear duplicados a nivel de motor).
- **Justificación:** el monolito y el módulo comparten base de datos pero deben mantenerse desacoplados en su modelo de datos — "compartir la conexión" no es lo mismo que "compartir las tablas de dominio"; y `usuarios` es autenticación del monolito, no aplica a un clasificador anónimo.
- **Ventajas:** el monolito sigue funcionando exactamente igual aunque estas tablas cambien; la restricción `UNIQUE` delega la detección de duplicados a PostgreSQL en vez de a una condición de carrera en Python.
- **Limitaciones:** dos "islas" de datos (catálogo del monolito vs. tablas del módulo) que solo se relacionan por `isbn`/`id_concepto` como claves foráneas de solo lectura hacia el monolito — si el monolito borra un libro o concepto, hay que decidir el comportamiento (ver limitación abajo, ON DELETE a definir en el DDL real).

## 6. Construcción manual del Envelope XML (sin Spyne/Zeep)

- **Necesidad:** producir y consumir sobres SOAP válidos sin ocultar su estructura detrás de una librería.
- **Decisión:** `xml.etree.ElementTree` para parsear el `Envelope` entrante y construir el de salida a mano, replicando namespaces (`soap:Envelope`, `soap:Body`, `soap:Fault`) explícitamente en el código.
- **Justificación:** el ejercicio lo prohíbe expresamente en esta etapa inicial — el objetivo pedagógico es entender qué hay dentro de un sobre SOAP, no delegarlo a una librería que lo genere automáticamente.
- **Ventajas:** control total y visibilidad completa del formato del mensaje; mismo patrón de construcción de XML ya usado (y probado) en el microservicio REST del Ejercicio03 para las respuestas `?format=xml`.
- **Limitaciones:** más código repetitivo por operación (namespaces, tags calificados) que con una librería SOAP; mayor superficie para errores de bien-formado si no se centraliza la construcción del envelope en una sola función helper.

## 7. Autenticación

- **Necesidad:** decidir si el módulo requiere identificar/autorizar a quien lo llama.
- **Decisión:** sin autenticación de sesión ni de usuario — el módulo es anónimo por diseño (un clasificador se identifica con nombre/apellido, no con credenciales), consistente con "no reutilizar la tabla usuarios del monolito".
- **Justificación:** el alcance de este ejercicio es la mecánica de integración SOAP, no un sistema de autorización; introducir login duplicaría lógica del monolito que el ejercicio pide evitar.
- **Ventajas:** simplicidad; ningún riesgo de mezclar sesiones del monolito con el módulo nuevo.
- **Limitaciones:** cualquiera con la URL del servicio puede invocarlo — aceptable para un ejercicio académico con base de datos de práctica, inaceptable para producción sin una capa adicional (API key, mTLS, etc.), que queda documentada como trabajo futuro y no se implementa en esta etapa.

## 8. Manejo de errores: SOAP Fault (no HTTP status crudo)

- **Necesidad:** comunicar errores de negocio (ISBN inexistente, clasificación duplicada, datos inválidos) de forma que un cliente SOAP los pueda interpretar sin adivinar.
- **Decisión:** todo error de negocio se responde como `soap:Fault` con `faultcode`, `faultstring` y un `detail` propio (`LibreriaFaultDetail`: código + descripción), nunca como un mensaje de error crudo de PostgreSQL ni como un simple código HTTP 4xx/5xx sin cuerpo interpretable.
- **Justificación:** es la forma estándar de reportar errores en SOAP; además sigue el mismo principio ya aplicado en el monolito (`utils/dbErrors.js` — nunca exponer `err.message` crudo de PostgreSQL al cliente).
- **Ventajas:** el cliente Electron puede distinguir programáticamente entre "no encontrado", "duplicado" e "inválido" por el código del Fault, sin parsear texto libre.
- **Limitaciones:** hay que mantener un catálogo propio de códigos de Fault (`ISBN_NO_ENCONTRADO`, `CLASIFICACION_DUPLICADA`, `DATOS_INVALIDOS`, etc.) sincronizado entre servidor y cliente a mano, ya que no hay generación automática desde el WSDL.

## 9. Interoperabilidad

- **Necesidad:** que el módulo pueda ser consumido por cualquier cliente SOAP, no solo por la app Electron construida en este proyecto.
- **Decisión:** contrato en inglés y estándar (namespaces XML calificados, tipos XSD explícitos, binding document/literal), sin atajos específicos del cliente Electron dentro del contrato o del servidor.
- **Justificación:** acoplar el contrato a las particularidades de un cliente específico rompería el propósito mismo de tener un WSDL — cualquier herramienta (SoapUI, Postman, `curl` con XML crudo, otro lenguaje) debería poder invocar el servicio leyendo solo el contrato.
- **Ventajas:** verificable de forma independiente al cliente (se puede probar con `curl -d @sobre.xml` antes de tocar Electron); reutilizable si más adelante se agrega otro cliente de escritorio o web.
- **Limitaciones:** exige más disciplina al programar (no se puede "atajar" devolviendo un campo extra solo porque el cliente actual lo necesita); cualquier cambio de contrato debe versionarse con cuidado para no romper clientes existentes.

---

*Documento vivo — se actualiza conforme avanza la implementación del Ejercicio04. Referencia: `library.wsdl`, `library-types.xsd`.*
