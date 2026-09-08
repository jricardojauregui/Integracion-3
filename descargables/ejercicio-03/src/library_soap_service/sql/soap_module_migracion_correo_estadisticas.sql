-- =====================================================================
-- MIGRACIÓN ADITIVA — Paso 14 (correo en la GUI) + Tarea 1 (estadísticas)
-- =====================================================================
-- Aditiva y sin romper nada: agrega una columna NULLABLE nueva a una
-- tabla PROPIA del módulo (no del monolito) y una vista nueva. No borra
-- ni renombra nada existente — las 4 operaciones ya implementadas del
-- Paso 9 siguen funcionando exactamente igual que antes.
-- =====================================================================

BEGIN;

-- Paso 14: la GUI ahora captura correo además de nombre/apellido. Es
-- solo un dato de contacto opcional -- el módulo no lo usa para
-- identificar ni autorizar a nadie (ver Tarea 5, pregunta de reflexión
-- sobre confiar en el correo del cliente).
ALTER TABLE clasificadores
    ADD COLUMN IF NOT EXISTS correo VARCHAR(255);

-- Tarea 1: estadísticas por modelo Cloud, protegidas con WS-Security
-- en la operación ObtenerEstadisticasPorModelo (soap/security.py).
CREATE OR REPLACE VIEW vw_estadisticas_por_modelo AS
SELECT modelo_cloud, count(*) AS total
FROM clasificaciones_cloud
GROUP BY modelo_cloud;

COMMENT ON COLUMN clasificadores.correo IS 'Dato de contacto opcional capturado por la GUI (Paso 14); no se usa para autenticar ni autorizar.';
COMMENT ON VIEW vw_estadisticas_por_modelo IS 'Conteo de clasificaciones por modelo Cloud (Tarea 1).';

COMMIT;
