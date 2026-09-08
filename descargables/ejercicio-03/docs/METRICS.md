# Tarea 5 — Medición técnica y reflexión SOAP

## Métricas

**Tiempo de desarrollo:** _[completa esto tú — yo no tengo forma de medir
cuánto tiempo le dedicaste realmente a cada sesión; es el único dato de
esta tarea que no puedo generar]._

**Líneas de código relevantes (conteo real con `wc -l`):**

| Componente | Archivos | Líneas |
|---|---|---|
| Servidor (Python) | `app.py`, `config/settings.py`, `db/connection.py`, `db/queries.py`, `soap/envelope.py`, `soap/faults.py`, `soap/security.py`, `soap/service.py` | **730** |
| Cliente SOAP (JS, `soapClient.js`, nuevo en el Paso 14) | 1 archivo | **174** |
| Contrato (WSDL, tipos inline) | `wsdl/library-classifier.wsdl` | **332** |
| SQL (tablas + vistas + stored procedure + privilegios + migración) | `sql/*.sql` | **318** |

**Tamaño real de una solicitud/respuesta de `RegistrarClasificacion`**
(medido byte a byte sobre la evidencia real del Paso 15/`TEST_PLAN.md`,
caso P02):

| | Bytes totales | Bytes de datos de negocio | Overhead de estructura XML |
|---|---|---|---|
| Request | 397 | ~23 | **94.2%** |
| Response | 371 | ~41 | **88.9%** |

"Datos de negocio" = solo el contenido de texto dentro de las etiquetas
(`1`, `978-0-307-47472-8`, `7`, `IaaS`, etc.) — todo lo demás (namespaces,
nombres de elementos repetidos en apertura/cierre, la envoltura
`Envelope`/`Body`) es estructura. Para un mensaje tan pequeño como este,
el overhead de XML domina casi por completo el tamaño del mensaje.

## Preguntas de reflexión

**¿Qué pasaría si agregas un campo obligatorio a `RegistrarClasificacion`
sin actualizar a los clientes?**
El cliente viejo seguiría mandando el mismo XML de siempre, sin el campo
nuevo. Con la validación actual (`soap/service.py`, `_campo_requerido`),
el servidor respondería con `DATOS_INVALIDOS` — un Fault claro, no un
crash. Pero para el usuario del cliente viejo eso se ve como "de repente
todo falla", sin ningún aviso previo. Es exactamente el tipo de ruptura
que un contrato versionado debería evitar (agregar el campo como
`minOccurs="0"` con un valor por defecto, no como obligatorio).

**¿Qué información del WSDL podría ser útil para un atacante y qué no
debería exponerse?** Útil para un atacante: los nombres exactos de
operaciones y campos (facilita construir peticiones válidas sin tantear),
y los patrones de validación del XSD (p. ej. el regex del ISBN, que dice
exactamente qué formato aceptar). Lo que nunca debería estar ahí —y no
está— son direcciones internas reales, credenciales, o nombres de tablas
de la base de datos; el WSDL de este proyecto usa `localhost:5050` como
placeholder justamente para no filtrar la URL real de despliegue por
accidente si el archivo se comparte.

**¿Por qué el tipado XSD aporta certeza al contrato?**
Porque mueve la validación de "algo que cada cliente debe adivinar y
reimplementar" a "algo que está escrito una sola vez y es verificable
mecánicamente" — un `xs:enumeration` con los 4 modelos Cloud, por
ejemplo, es una fuente de verdad única en vez de 4 strings copiados a
mano en cada cliente que alguien escriba.

**¿Qué partes del Envelope fueron boilerplate y cuáles dependieron de la
operación?** Boilerplate: `soap:Envelope`, `soap:Body`, los namespaces
declarados, y (cuando aplica) `soap:Header`/`wsse:Security` — son
idénticos para las 5 operaciones. Lo que depende de la operación es
solo el elemento `*Request`/`*Response` de adentro y sus campos — en
`envelope.py`, por eso `_envelope_con_body()` y `_dict_a_elemento()`
existen como funciones genéricas reutilizadas por las 5, mientras que
el contenido interno lo arma cada handler de `soap/service.py`.

**¿Cuándo justificarías el overhead de XML frente a un formato más
ligero?** Cuando el valor está en el contrato tipado y verificable (XSD)
más que en el tamaño del mensaje — sistemas empresariales con
validación estricta, generación automática de clientes en múltiples
lenguajes, o integración con infraestructura legada que ya habla SOAP.
Para mensajes pequeños y frecuentes entre servicios propios (microservicios
internos, APIs para apps móviles), el 90%+ de overhead medido arriba deja
de tener sentido frente a JSON.

**¿Por qué un SOAP Fault es parte del contrato y no solo un error HTTP?**
Porque el `detail` (`LibreriaFaultDetail` con `codigo`/`descripcion`) está
definido en el mismo XSD que las respuestas exitosas — un cliente que lee
el WSDL sabe de antemano qué formas de error puede recibir, sin tener que
inventar una convención aparte para "cómo se ve un error" (a diferencia
de HTTP, donde un código 400 no dice nada sobre la forma del cuerpo).

**¿Cómo debe reaccionar una GUI ante un Fault de cliente frente a un
Fault de servidor?** Ante `soap:Client` (datos inválidos, duplicado, no
encontrado): mostrar el mensaje específico y dejar que el usuario corrija
algo (es exactamente lo que hace `MENSAJES_FAULT` en `renderer.js`).
Ante `soap:Server`: nunca sugerir "corrige tu entrada" porque no fue el
usuario quien se equivocó — mostrar un mensaje genérico de "inténtalo más
tarde" y, del lado de desarrollo, revisar el log del servidor.

**¿Qué riesgo existe porque el módulo SOAP y el monolito compartan la
misma base de datos?** El principal es acoplamiento oculto: un cambio en
el esquema del monolito puede romper el módulo SOAP sin que quien lo
cambia sepa que existe ese segundo consumidor. Mitigado parcialmente por
FKs `ON DELETE RESTRICT` (Paso 7) que fallan ruidosamente en vez de
corromper datos en silencio — pero no elimina el acoplamiento, solo lo
hace visible cuando ocurre.

**¿Qué ocurriría si el monolito renombra `books.isbn`? ¿Cómo reducirías
ese acoplamiento?** Las vistas y el stored procedure (`sql/soap_module_procedures.sql`)
fallarían de inmediato (columna inexistente) — el módulo entero dejaría
de funcionar hasta actualizar el SQL a mano. Para reducir el
acoplamiento: el módulo debería consumir el catálogo del monolito a
través de una API/vista publicada explícitamente por el monolito (un
contrato propio, versionado), en vez de leer sus tablas internas
directamente — es la misma lección que motivó todo este ejercicio
aplicada de vuelta hacia el monolito.

**¿Dónde debe aplicarse autenticación y qué problema resuelve
WS-Security?** Se aplicó donde hay una operación sensible de verdad
(estadísticas agregadas del negocio, Tarea 1) y no en operaciones donde
cualquiera legítimamente puede participar sin credenciales (clasificar
un concepto es la actividad pública que el ejercicio quiere fomentar).
WS-Security resuelve pasar credenciales de forma estandarizada *dentro*
del contrato SOAP (`soap:Header`), en vez de inventar un mecanismo propio
por fuera del sobre.

**¿Es suficiente confiar en el correo enviado por el cliente para
identificar al usuario?** No — y por eso el módulo no lo usa para nada
operativo (`soap/service.py`, `registrar_clasificador`): cualquiera puede
escribir cualquier correo sin que el sistema lo verifique. Confiar en un
dato no verificado como identidad sería un hueco de seguridad —
identificar de verdad requeriría un flujo de verificación (link de
confirmación, login real), fuera del alcance de este ejercicio.

**¿En qué escenarios empresariales seguirías eligiendo SOAP en 2026?**
Integración con sistemas legados que ya hablan SOAP y no se van a
reescribir (banca, gobierno, ERPs como SAP), o contextos donde el
contrato tipado y verificable formalmente importa más que la ligereza
del mensaje — por ejemplo, transacciones financieras donde un error de
tipo silencioso es inaceptable. Para todo lo demás (APIs públicas,
apps móviles, microservicios nuevos) REST/JSON o gRPC ganan por
simplicidad y tamaño de mensaje, como muestran las métricas de arriba.
