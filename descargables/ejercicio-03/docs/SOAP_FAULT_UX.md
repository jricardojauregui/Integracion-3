# Tarea 2 — SOAP Fault y experiencia de usuario

## Evidencia (reutilizada de `TEST_PLAN.md` / `evidencia/xml/`)

La clasificación duplicada, el concepto inexistente, el modelo Cloud
inválido y el XML inválido ya se probaron con evidencia real en el
Paso 15 (`TEST_PLAN.md`, casos N01-N04) — no se repiten aquí para no
duplicar contenido. Los Envelope de error completos están en
`evidencia/xml/N01_repetir_clasificacion_response.xml` (409),
`N02_concepto_inexistente_response.xml`,
`N03_modelo_invalido_response.xml` y `N04_xml_invalido_response.xml`.

## Cómo la GUI interpreta el Fault (Paso 14, `client01/renderer/renderer.js`)

```js
const MENSAJES_FAULT = {
  ISBN_NO_ENCONTRADO: "Ese ISBN no existe en el catálogo.",
  CONCEPTO_NO_ENCONTRADO: "Ese concepto no está definido para ese libro.",
  CLASIFICADOR_NO_ENCONTRADO: "No encontramos ese clasificador. Regístrate de nuevo.",
  CLASIFICACION_DUPLICADA: "Ya habías clasificado ese concepto de ese libro antes.",
  DATOS_INVALIDOS: "Revisa los datos del formulario: algo no tiene el formato correcto.",
  ENVELOPE_INVALIDO: "Ocurrió un problema de comunicación con el servicio. Intenta de nuevo.",
  CREDENCIALES_INVALIDAS: "Usuario o contraseña incorrectos.",
  ERROR_INTERNO: "El servicio tuvo un problema interno. Intenta más tarde.",
};
```

## Qué ve el usuario vs. qué queda solo en logs

| | El usuario ve | Solo en logs/consola |
|---|---|---|
| Fault de cliente (validación, duplicado, no encontrado) | El mensaje traducido de `MENSAJES_FAULT`, en español, sin tecnicismos | El `codigo` crudo y el `faultcode` (`console.error("SOAP Fault:", resultado.fault)` en `renderer.js`) |
| Fault de servidor (`ERROR_INTERNO`) | "El servicio tuvo un problema interno. Intenta más tarde." — nunca el detalle real | El traceback completo, del lado del **servidor** (`app.logger.exception`, Paso 13) — el cliente nunca lo recibe siquiera, así que ni la consola del renderer lo ve |
| Error de red (servidor caído, timeout) | "No se pudo contactar al servicio SOAP..." | El mensaje de error de Node (`err.message`) en consola |

La regla aplicada en los tres casos es la misma que ya se documentó en
`ERROR_HANDLING.md` (Paso 13) del lado del servidor: información técnica
nunca llega al usuario final, ni siquiera reformulada — se sustituye por
un mensaje de acción ("revisa esto", "intenta más tarde"), y lo técnico
queda donde alguien que esté depurando sí lo necesita (logs de servidor,
consola de desarrollador del cliente).
