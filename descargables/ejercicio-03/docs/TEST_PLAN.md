# Plan de pruebas — Módulo SOAP (Paso 15)

Todas las pruebas se ejecutaron contra el servidor real (`app.py` corriendo
de verdad en un hilo, WSDL servido en `/wsdl`, endpoint `/soap` real por
HTTP) — no son simulaciones de Flask test client. La única pieza
reemplazada es la capa de PostgreSQL (`db/queries.py`), porque este
entorno no tiene un Postgres disponible: se sustituyó por una base en
memoria con el **mismo comportamiento de negocio** (duplicados,
no-encontrado, etc.), documentado en `evidencia/generar_evidencia.py`.
El evento completo (petición y respuesta XML de cada caso) queda en
`evidencia/evidencia_real.json`.

**Al correr esto contra el Postgres real (Paso 16), reemplaza la columna
"Resultado obtenido" por lo que de verdad devuelva tu servidor — el
comportamiento no debería cambiar, pero es la evidencia que pide el
ejercicio.**

## Pruebas positivas

| ID | Prueba | Entrada | Resultado esperado | Resultado obtenido (real, BD en memoria) | Estado |
|---|---|---|---|---|---|
| P01 | Obtener conceptos pendientes | `ObtenerConceptosPendientesRequest` sin isbn | Lista válida | HTTP 200, 1 concepto pendiente ("1984" / Distopía) — el otro ya se había clasificado en la prueba anterior | ✅ |
| P02 | Registrar IaaS | isbn=978-0-307-47472-8, idConcepto=7, modeloCloud=IaaS | Registro exitoso | HTTP 200, `idClasificacion=1`, "Clasificación registrada correctamente." (397 bytes de request, 371 de response) | ✅ |
| P03 | Obtener progreso de usuario | idClasificador=1 | Totales correctos | HTTP 200, `totalClasificados=1`, `totalPendientes=1` | ✅ |
| P04 (Tarea 1) | Estadísticas con credenciales correctas | usuario/password válidos en `wsse:UsernameToken` | Conteo por modelo | HTTP 200, `totalIaaS=1`, resto en 0 | ✅ |

## Pruebas negativas

| ID | Prueba | Entrada | Resultado esperado | Resultado obtenido (real) | Estado |
|---|---|---|---|---|---|
| N01 | Repetir clasificación | Mismo isbn+idConcepto+idClasificador que P02 | SOAP Fault 409 | HTTP **409**, `faultcode=soap:Client`, `codigo=CLASIFICACION_DUPLICADA` | ✅ |
| N02 | Concepto inexistente | idConcepto=9999 (no existe) | SOAP Fault | HTTP 400, `codigo=CONCEPTO_NO_ENCONTRADO` | ✅ |
| N03 | Modelo inválido | modeloCloud="Xaas" | SOAP Fault | HTTP 400, `codigo=DATOS_INVALIDOS`, mensaje "'Xaas' no es un modelo Cloud válido..." | ✅ |
| N04 | XML inválido | `<soap:Envelope><soap:Body>` (sin cerrar) | SOAP Fault de cliente, sin ejecutar SQL | HTTP 400, `codigo=ENVELOPE_INVALIDO`, mensaje "XML mal formado: unbound prefix..." | ✅ |
| N05 (Tarea 1) | Estadísticas sin credenciales | Sin `soap:Header` | SOAP Fault | HTTP 401, `codigo=CREDENCIALES_INVALIDAS` | ✅ |
| N06 (Tarea 1) | Estadísticas con password incorrecta | usuario correcto, password mala | SOAP Fault | HTTP 401, `codigo=CREDENCIALES_INVALIDAS`, "Usuario o contraseña inválidos." | ✅ |

## Conclusión

10/10 casos (4 positivos + 6 negativos) se comportaron exactamente como
predice `ERROR_HANDLING.md` (Paso 13) — cada Fault trae `faultcode`,
`codigo` y `descripcion` interpretables, y ningún caso negativo llegó a
ejecutar una escritura en la base (N01-N06 fallan todos ANTES o EN la
capa de datos, nunca dejan un registro corrupto a medio camino, gracias
a la validación en `soap/service.py` y a la transacción atómica de
`sp_registrar_clasificacion`).
