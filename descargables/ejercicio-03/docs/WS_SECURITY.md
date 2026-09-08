# Tarea 1 — Estadísticas por modelo + WS-Security

## Qué se agregó

- Operación nueva `ObtenerEstadisticasPorModelo` en `wsdl/library-classifier.wsdl`
  (mensajes, portType, binding — no se tocó ninguna operación existente,
  ver diff conceptual en `ENGINEERING_DECISIONS_SOAP.md`).
- `soap/security.py`: WS-Security simplificado (`wsse:UsernameToken` en
  `soap:Header`), contraseña **nunca en texto plano** — se compara por
  hash (`werkzeug.security.check_password_hash`) contra
  `WS_SECURITY_PASSWORD_HASH` en `.env` (nunca en el código ni en las
  evidencias).
- `soap/faults.py`: código nuevo `CREDENCIALES_INVALIDAS` → `soap:Client`,
  HTTP 401.

## WSDL actualizado

`wsdl/library-classifier.wsdl` — la operación se agregó al final del
`portType` y del `binding` sin modificar ninguno de los mensajes/tipos
existentes de las 4 operaciones anteriores (compatibilidad hacia atrás:
un cliente viejo que solo conocía las primeras 4 sigue funcionando
exactamente igual).

## Evidencia real (generada corriendo el servidor de verdad — ver `TEST_PLAN.md`)

**Solicitud autenticada y respuesta** (`evidencia/xml/T1b_estadisticas_credenciales_correctas_*.xml`):
HTTP 200, `totalIaaS=1`, resto en 0 (reflejando la única clasificación
registrada en esa corrida de prueba).

**Prueba con credenciales incorrectas** (`evidencia/xml/T1c_estadisticas_credenciales_incorrectas_*.xml`):
HTTP 401, Fault `CREDENCIALES_INVALIDAS`, mensaje "Usuario o contraseña
inválidos." — sin revelar si el usuario existía o no (mismo mensaje para
usuario incorrecto y para password incorrecta, para no dar pistas a un
atacante).

**Sin credenciales en absoluto** (`evidencia/xml/T1a_estadisticas_sin_credenciales_*.xml`):
HTTP 401 también, con mensaje distinto ("Esta operación requiere
credenciales...") — distingue "no mandaste nada" de "mandaste algo
incorrecto" para facilitar depuración a un cliente legítimo que se
equivocó de implementación, sin comprometer seguridad.

## Explicación de la decisión de seguridad

Se protegió únicamente esta operación (no todo el módulo) porque es la
única que expone un agregado de negocio (cuántas clasificaciones de cada
tipo existen) que no tiene sentido dejar abierto a cualquiera, a
diferencia de las operaciones de clasificar/consultar pendientes, que
son la actividad pública que el ejercicio fomenta (ver decisión de
ingeniería #7 en `ENGINEERING_DECISIONS_SOAP.md`, ahora con esta
excepción puntual documentada). Es un WS-Security simplificado a
propósito para el alcance académico: usuario/contraseña en el Header,
sin `PasswordDigest`/`Nonce`/firma XML del estándar completo — suficiente
para demostrar el mecanismo sin la complejidad de una implementación
WS-Security completa.
