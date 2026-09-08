# Diseño de errores — SOAP Fault (Ejercicio04, Paso 13)

Tabla exacta del enunciado, con el estado real verificado contra la
implementación (`soap/faults.py`, `soap/envelope.py`, `app.py`) y por las
pruebas automatizadas (`pytest tests/` → 11 passed; los 10 casos del plan
de pruebas cubren todos estos Faults).

| Caso | Comportamiento esperado | Código | faultcode | HTTP | Verificado |
|---|---|---|---|---|---|
| Concepto inexistente | SOAP Fault de cliente con mensaje claro | `CONCEPTO_NO_ENCONTRADO` | `soap:Client` | 400 | ✅ |
| ISBN inexistente (mismo criterio) | SOAP Fault de cliente con mensaje claro | `ISBN_NO_ENCONTRADO` | `soap:Client` | 400 | ✅ |
| Clasificador inexistente (mismo criterio) | SOAP Fault de cliente con mensaje claro | `CLASIFICADOR_NO_ENCONTRADO` | `soap:Client` | 400 | ✅ |
| Modelo distinto de IaaS/PaaS/SaaS/FaaS | SOAP Fault de validación | `DATOS_INVALIDOS` | `soap:Client` | 400 | ✅ (nunca llega a tocar la BD) |
| Campo obligatorio faltante (mismo criterio) | SOAP Fault de validación | `DATOS_INVALIDOS` | `soap:Client` | 400 | ✅ |
| Clasificación duplicada | SOAP Fault asociado a conflicto | `CLASIFICACION_DUPLICADA` | `soap:Client` | **409** | ✅ |
| XML inválido | SOAP Fault de cliente; no ejecutar SQL | `ENVELOPE_INVALIDO` | `soap:Client` | 400 | ✅ (se verificó que la capa de BD nunca se invoca) |
| Falla de PostgreSQL no anticipada | SOAP Fault de servidor; detalle técnico solo en log | `ERROR_INTERNO` | `soap:Server` | 500 | ✅ (traceback completo va a `app.logger.exception`, nunca al body de la respuesta) |

## Qué cambió respecto al Paso 11/12

Hasta este paso, `construir_fault()` mandaba **siempre** `faultcode=soap:Server`
y `app.py` devolvía **siempre** HTTP 500, sin importar la causa — no
distinguía nada. Se corrigió:

- `soap/faults.py` ahora tiene dos tablas de metadatos por código
  (`_SOAP_FAULTCODE`, `_HTTP_STATUS`) y dos funciones (`soap_faultcode()`,
  `http_status()`) que las consultan.
- `soap/envelope.py` (`construir_fault`) usa `faults.soap_faultcode(fault.codigo)`
  en vez del string fijo `"soap:Server"`.
- `app.py` usa `faults.http_status(fault.codigo)` para el `status=` de
  la `Response`, tanto en el `except LibreriaFault` como en el
  `except Exception` genérico.

## Por qué "duplicado" es `soap:Client` y no `soap:Server`

SOAP 1.1 solo tiene dos faultcodes generales (`Client`/`Server`, más
`VersionMismatch`/`MustUnderstand`, que no aplican aquí). Un conflicto
409 sigue siendo, por definición, un problema con lo que pidió el
cliente (repitió una clasificación que ya existía) — no un fallo del
servidor. El **409** en el HTTP y el **código `CLASIFICACION_DUPLICADA`**
en el `detail` son los que le dan al cliente la granularidad real; el
`faultcode` solo distingue la categoría amplia que exige el estándar SOAP.

## Verificación de "nada sensible se filtra"

Se probó explícitamente inyectando un mensaje de error con una ruta de
sistema falsa (`/var/run/postgresql`) y una palabra clave inventada
("DETALLE-SECRETO-DE-POSTGRES") en una excepción no anticipada — ninguna
de las dos apareció en el cuerpo de la respuesta HTTP; solo en el log
del servidor (`app.logger.exception`). Ningún mensaje de Fault en todo
el código construye texto con rutas de archivo, cadenas de conexión,
contraseñas o SQL crudo — todos son strings fijos o reflejan como mucho
el propio dato que el cliente envió (p. ej. "'Xaas' no es un modelo
Cloud válido"), nunca información interna del servidor.
