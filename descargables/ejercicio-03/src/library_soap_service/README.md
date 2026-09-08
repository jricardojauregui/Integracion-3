# library_soap_service — Módulo SOAP de clasificación (Ejercicio 03)

Módulo **independiente** en Flask + psycopg2 que se integra con el monolito
de librería (Ejercicio 2) **sin modificarlo**: publica un contrato WSDL,
construye el sobre SOAP a mano con `xml.etree`, valida y persiste en
PostgreSQL con transacciones atómicas, responde errores como `soap:Fault`
interpretable, protege una operación con WS-Security, y se consume desde el
cliente de escritorio Electron (`apps/client01`) y desde un cliente
generado con `zeep` (`tarea4_interoperabilidad/`).

## Operaciones (contrato: `wsdl/library-classifier.wsdl`)

| Operación | Descripción |
|---|---|
| `ObtenerConceptosPendientes` | Conceptos del catálogo sin clasificación Cloud |
| `RegistrarClasificacion` | Registra IaaS/PaaS/SaaS/FaaS (valida contra el catálogo) |
| `ObtenerProgresoUsuario` | Totales clasificados / pendientes de un clasificador |
| `RegistrarClasificador` | Alta de identidad mínima (nombre + apellido, correo opcional) |
| `ObtenerEstadisticasPorModelo` | Conteo por modelo Cloud — **protegida con WS-Security** (Tarea 1) |

## Puesta en marcha

```bash
cd apps/services/library_soap_service
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # editar con credenciales reales

# SQL (las copias canónicas también viven en db/ del repo)
psql -U library_user -d library -f sql/soap_module.sql
psql -U library_user -d library -f sql/soap_module_procedures.sql
psql -U postgres     -d library -f sql/soap_module_privileges.sql
psql -U library_user -d library -f sql/soap_module_migracion_correo_estadisticas.sql

python app.py                   # sirve /wsdl y /soap (puerto de .env, default 5050)
```

## Pruebas

```bash
cd apps/services/library_soap_service
pytest tests/ -q                # test_app.py + test_operaciones_e2e.py (10 casos, BD en memoria)
```

## Documentación

- `docs/DOCUMENTACION_TECNICA.md` — índice técnico completo
- `docs/ENGINEERING_DECISIONS_SOAP.md` — 9 decisiones de ingeniería
- `docs/CONTRACT_AUDIT.md` / `docs/AUDITORIA_OPERACIONES.md` — auditoría del contrato
- `docs/ERROR_HANDLING.md` / `docs/SOAP_FAULT_UX.md` — SOAP Fault y UX
- `docs/WS_SECURITY.md` — WS-Security (Tarea 1)
- `docs/INTEROPERABILIDAD.md` — cliente `zeep` (Tarea 4)
- `docs/TEST_PLAN.md` / `docs/VERIFICATION_GUIDE.md` — pruebas y verificación en la VM
- `docs/METRICS.md` — métricas y preguntas de reflexión (Tarea 5)
- `evidencia/` — request/response XML reales + `evidencia_real.json`
- `evidencia/capturas/` — checklist y script de las 23 capturas de la galería
