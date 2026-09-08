# Documentación técnica — Módulo SOAP de clasificación (Ejercicio04)

Este documento compila las decisiones y el estado del módulo
`library_soap_service`. Cada sección referencia el archivo fuente donde
vive el detalle completo, para no duplicar contenido.

## 1. Arquitectura seleccionada y justificación

Flask + psycopg2 puro, SOAP construido a mano con `xml.etree`, contrato
WSDL+XSD definido antes de programar. Ver `ENGINEERING_DECISIONS_SOAP.md`
(9 decisiones en formato Necesidad→Decisión→Justificación→Ventajas→Limitaciones).

## 2. Macro-arquitectura, patrón de diseño y organización del código

App de escritorio (Electron, cliente SOAP) → HTTP POST/XML → Módulo SOAP
(Flask) → psycopg2 → PostgreSQL, con el monolito Node.js accediendo a la
misma base de forma completamente independiente. Diagrama y fronteras
documentados en el Paso 3 de la conversación (diagrama de arquitectura).

Patrón de organización: separación estricta contrato / acceso a datos /
lógica de negocio / seguridad / pruebas — ver árbol completo abajo
(sección 3).

## 3. Organización de módulos y componentes

```
library_soap_service/
├── app.py                  # único endpoint POST /soap y GET /wsdl
├── config/settings.py      # carga de .env
├── db/
│   ├── connection.py       # cursor_lectura() / transaccion()
│   └── queries.py          # capa de acceso a datos parametrizada
├── soap/
│   ├── envelope.py         # parseo/construcción manual del sobre
│   ├── faults.py           # catálogo de errores + faultcode/HTTP status
│   ├── security.py         # WS-Security simplificado (Tarea 1)
│   └── service.py          # lógica de negocio + validación
├── wsdl/library-classifier.wsdl
├── sql/
│   ├── soap_module.sql                          # DDL (Paso 7)
│   ├── soap_module_privileges.sql                # mínimo privilegio (Paso 8)
│   ├── soap_module_procedures.sql                # vista + stored procedure (Paso 12)
│   └── soap_module_migracion_correo_estadisticas.sql  # aditiva (Paso 14/Tarea 1)
│                           # (copia canónica también en db/ del repo)
├── tests/
│   ├── test_app.py                 # /wsdl se publica
│   └── test_operaciones_e2e.py     # 10 casos de TEST_PLAN.md (BD en memoria)
├── docs/                   # TEST_PLAN, VERIFICATION_GUIDE, ERROR_HANDLING,
│                           # CONTRACT_AUDIT, WS_SECURITY, SOAP_FAULT_UX,
│                           # AUDITORIA_OPERACIONES, INTEROPERABILIDAD, METRICS,
│                           # ENGINEERING_DECISIONS_SOAP, DOCUMENTACION_TECNICA...
├── evidencia/               # XML real + JSON de una corrida real del servidor
├── evidencia/capturas/      # checklist + script de las 23 capturas de la VM
├── tarea4_interoperabilidad/interop_client_zeep.py
├── .env.example, requirements.txt, README.md
```

## 4. Contrato WSDL, tipos XSD y operaciones

5 operaciones: `ObtenerConceptosPendientes`, `RegistrarClasificacion`,
`ObtenerProgresoUsuario`, `RegistrarClasificador`,
`ObtenerEstadisticasPorModelo` (Tarea 1, protegida). Diseño completo,
mensajes, binding document/literal y auditoría campo-por-campo en
`CONTRACT_AUDIT.md` + `docs/AUDITORIA_OPERACIONES.md`.

## 5. Funcionalidades implementadas

Las 5 operaciones completas con lógica real (no stubs), validación de
entrada, transacciones con rollback, y las 3 tablas propias del módulo
(`clasificadores`, `clasificaciones_cloud`, `clientes_servidos`) más la
columna `correo` (Paso 14) y las vistas `vw_conceptos_pendientes` /
`vw_estadisticas_por_modelo`.

## 6. Flujo de información

Usuario → GUI Electron (captura nombre/apellido/correo + datos a
clasificar) → `soapClient.js` arma el Envelope → HTTP POST → `app.py`
→ `envelope.py` (parseo) → `soap/service.py` (validación + lógica) →
`db/queries.py` (SQL parametrizado) → PostgreSQL. La respuesta recorre
el camino inverso; un Fault interrumpe el flujo en el primer punto donde
se detecta el problema (nunca después de escribir en la base a medias).

## 7. Autenticación, autorización y seguridad

- Sin autenticación de sesión para las 4 operaciones originales (decisión
  de ingeniería #7) — el módulo es anónimo por diseño.
- WS-Security simplificado (usuario/contraseña por hash) solo para
  `ObtenerEstadisticasPorModelo` — ver `docs/WS_SECURITY.md`.
- Mínimo privilegio a nivel de PostgreSQL: rol `soap_module_user` sin
  acceso a `usuarios`, sin DELETE, sin DDL — ver `sql/soap_module_privileges.sql`.

## 8. Validación de datos y manejo de SOAP Fault

Validación de campos obligatorios/formato antes de tocar la base
(`soap/service.py`). Cada Fault trae `faultcode` (Client/Server) y HTTP
status (400/401/409/500) según el catálogo de `soap/faults.py` — tabla
completa y evidencia real en `ERROR_HANDLING.md` y `TEST_PLAN.md`.

## 9. Persistencia, transacciones y permisos de PostgreSQL

`db/connection.py` con `transaccion()` (COMMIT/ROLLBACK automático de
psycopg2) para toda escritura; `sp_registrar_clasificacion` valida y
escribe de forma atómica dentro de una única transacción de base de
datos. Permisos documentados en `sql/soap_module_privileges.sql` y
verificables con `VERIFICATION_GUIDE.md` (Paso 16).

## 10. Despliegue y configuración del servicio

```bash
cd apps/services/library_soap_service
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # editar con credenciales reales

psql -U library_user -d library -f sql/soap_module.sql
psql -U library_user -d library -f sql/soap_module_procedures.sql
psql -U postgres     -d library -f sql/soap_module_privileges.sql
psql -U library_user -d library -f sql/soap_module_migracion_correo_estadisticas.sql

python app.py   # sirve /wsdl y /soap en el puerto de .env (default 5050)
```

## 11. Rendimiento, mantenimiento, interoperabilidad y escalabilidad

- **Rendimiento:** overhead de XML medido en ~90% del tamaño del mensaje
  para operaciones pequeñas (ver `docs/METRICS.md`)
  — aceptable para el volumen de este ejercicio, no para tráfico masivo.
- **Mantenimiento:** contrato-primero + tipos específicos reduce el
  riesgo de romper clientes al cambiar el servidor, a costa de más
  disciplina para extenderlo (ver conclusión de `docs/AUDITORIA_OPERACIONES.md`).
- **Interoperabilidad:** demostrada con un cliente generado en `zeep`
  contra el WSDL real, sin tocar la implementación del servidor —
  `docs/INTEROPERABILIDAD.md`.
- **Escalabilidad:** el módulo es stateless (cada request abre y cierra
  su propia conexión); el cuello de botella natural sería PostgreSQL
  compartido con el monolito, no el módulo Flask en sí.
