-- =====================================================================
-- MÍNIMO PRIVILEGIO PARA EL MÓDULO SOAP (Ejercicio04 — Parte 4, Paso 8)
-- =====================================================================
-- library_user (el rol del monolito) tiene CRUD sobre TODO el esquema
-- funcional, porque el monolito lo necesita para su propia operación.
-- Darle ese mismo rol al módulo SOAP violaría mínimo privilegio: el
-- módulo no necesita, y no debe poder, escribir en `libros`, `usuarios`
-- ni ninguna tabla del monolito. Por eso se crea un rol NUEVO,
-- exclusivo del módulo, sin superusuario y sin relación con `postgres`.
-- =====================================================================

-- Ejecutar como el superusuario/owner de la base (no desde la app).
-- Cambiar la contraseña antes de usar en un entorno real.

-- IF NOT EXISTS evita que re-correr este archivo completo (p. ej. tras
-- agregar los GRANT de vw_conceptos_pendientes/sp_registrar_clasificacion
-- en el Paso 12) falle con "el rol ya existe" — mismo espíritu que el
-- CREATE TABLE IF NOT EXISTS de sql/soap_module.sql.
DO
$$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'soap_module_user') THEN
        CREATE ROLE soap_module_user LOGIN PASSWORD 'CAMBIA_ESTA_CONTRASENA';
    END IF;
END
$$;

GRANT CONNECT ON DATABASE library TO soap_module_user;
GRANT USAGE ON SCHEMA public TO soap_module_user;

-- ---------------------------------------------------------------------
-- SOLO LECTURA: catálogo del monolito que el módulo consulta
-- (ConsultarConceptosPendientes necesita leer libros/conceptos/
--  libro_concepto; el resto se deja por si se amplía la consulta).
-- Nunca se otorga ningún privilegio sobre `usuarios` (Paso 1).
-- ---------------------------------------------------------------------
GRANT SELECT ON
    libros,
    autores,
    generos,
    formatos,
    libro_autor,
    libro_genero,
    libro_imagen,
    conceptos,
    libro_concepto
TO soap_module_user;

-- ---------------------------------------------------------------------
-- LECTURA + ESCRITURA: únicamente las 3 tablas propias del módulo.
-- Sin DELETE — no está en el alcance del ejercicio (Paso 2) y no hay
-- necesidad justificada de borrar clasificaciones o clasificadores.
-- ---------------------------------------------------------------------
GRANT SELECT, INSERT, UPDATE ON
    clasificadores,
    clientes_servidos,
    clasificaciones_cloud
TO soap_module_user;

-- Secuencias de las 3 tablas propias (BIGSERIAL las crea implícitas).
-- Sin esto, INSERT falla: el rol no puede leer/avanzar el nextval().
GRANT USAGE, SELECT ON
    clasificadores_id_clasificador_seq,
    clientes_servidos_id_cliente_servido_seq,
    clasificaciones_cloud_id_clasificacion_seq
TO soap_module_user;

-- ---------------------------------------------------------------------
-- Vista y stored procedure del Paso 12 (sql/soap_module_procedures.sql).
-- El GRANT EXECUTE solo lista los parámetros IN — los OUT no forman
-- parte de la firma que identifica al procedure.
-- ---------------------------------------------------------------------
GRANT SELECT ON vw_conceptos_pendientes TO soap_module_user;
GRANT SELECT ON vw_estadisticas_por_modelo TO soap_module_user;
GRANT EXECUTE ON PROCEDURE sp_registrar_clasificacion(BIGINT, VARCHAR, BIGINT, VARCHAR)
    TO soap_module_user;

-- Defensivo y explícito, aunque PostgreSQL ya no otorga nada por
-- defecto sin GRANT: deja documentado que usuarios es intocable.
REVOKE ALL ON usuarios FROM soap_module_user;

-- =====================================================================
-- Resumen para documentación (Paso 8, "documenta qué tablas puede
-- consultar y en cuáles puede insertar/actualizar"):
--
--  SOLO SELECT:
--    libros, autores, generos, formatos, libro_autor, libro_genero,
--    libro_imagen, conceptos, libro_concepto
--
--  SELECT + INSERT + UPDATE:
--    clasificadores, clientes_servidos, clasificaciones_cloud
--
--  SIN NINGÚN ACCESO:
--    usuarios (y cualquier tabla futura del monolito no listada arriba)
--
--  Sin DELETE en ninguna tabla. Sin privilegios de DDL (no puede crear
--  ni alterar tablas). No es superusuario, no es owner de la base.
-- =====================================================================
