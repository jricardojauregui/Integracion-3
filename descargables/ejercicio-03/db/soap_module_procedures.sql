-- =====================================================================
-- VISTA Y STORED PROCEDURE DEL MÓDULO SOAP (Ejercicio04 — Paso 12)
-- =====================================================================
-- Correr DESPUÉS de sql/soap_module.sql (necesita sus 3 tablas) y con
-- el mismo usuario dueño del esquema (library_user o superusuario) —
-- el rol de mínimo privilegio soap_module_user NO tiene permiso de DDL
-- (ver sql/soap_module_privileges.sql), así que este archivo no lo
-- ejecuta él, solo lo consulta/ejecuta después.
-- =====================================================================

BEGIN;

-- ---------------------------------------------------------------------
-- vw_conceptos_pendientes
-- Integra book_concepts(libro_concepto) + concepts(conceptos) +
-- books(libros) + categories(generos), tal como pide el Paso 12,
-- respetando el esquema del monolito sin modificarlo.
--
-- "Pendiente" = nadie lo ha clasificado todavía (NOT EXISTS contra
-- clasificaciones_cloud, sin filtrar por clasificador). Es una cola
-- compartida: en cuanto CUALQUIER clasificador registra una
-- clasificación para ese (isbn, id_concepto), desaparece de esta
-- vista para todos — aunque la restricción UNIQUE de
-- clasificaciones_cloud sigue siendo por clasificador (Paso 7), así
-- que técnicamente alguien podría clasificar algo que ya no aparece
-- aquí si lo hace por otra vía. Si la intención real era "pendiente
-- para MÍ" (por clasificador), avisar — cambia el WHERE por un
-- parámetro en vez de un NOT EXISTS global.
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_conceptos_pendientes AS
SELECT
    lc.isbn,
    l.titulo                                          AS titulo_libro,
    string_agg(DISTINCT g.nombre, ', ' ORDER BY g.nombre) AS categoria,
    c.id_concepto,
    c.nombre                                           AS nombre_concepto
FROM libro_concepto lc
JOIN libros l           ON l.isbn = lc.isbn
JOIN conceptos c        ON c.id_concepto = lc.id_concepto
LEFT JOIN libro_genero lg ON lg.isbn = l.isbn
LEFT JOIN generos g       ON g.id_genero = lg.id_genero
WHERE NOT EXISTS (
    SELECT 1 FROM clasificaciones_cloud cc
    WHERE cc.isbn = lc.isbn AND cc.id_concepto = lc.id_concepto
)
GROUP BY lc.isbn, l.titulo, c.id_concepto, c.nombre;

COMMENT ON VIEW vw_conceptos_pendientes IS
    'Conceptos (libro_concepto+conceptos+libros+generos) sin ninguna clasificación Cloud registrada todavía.';

-- ---------------------------------------------------------------------
-- sp_registrar_clasificacion
-- Válida existencia (isbn, concepto-en-ese-libro, clasificador) y
-- registra la clasificación en una sola transacción atómica: si
-- cualquier RAISE EXCEPTION dispara, PostgreSQL revierte el
-- procedimiento completo — nada queda a medio insertar (Paso 12:
-- "transacciones... y rollback ante errores").
--
-- Usa SQLSTATE personalizados (P0001-P0003, mismo patrón que
-- trg_prevenir_segundo_admin del monolito) para que db/queries.py
-- pueda distinguir cada causa sin parsear el mensaje de texto.
-- ---------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE sp_registrar_clasificacion(
    p_id_clasificador   BIGINT,
    p_isbn              VARCHAR(20),
    p_id_concepto       BIGINT,
    p_modelo_cloud      VARCHAR(4),
    OUT p_id_clasificacion BIGINT
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM libros WHERE isbn = p_isbn) THEN
        RAISE EXCEPTION 'ISBN % no existe en el catálogo', p_isbn
            USING ERRCODE = 'P0001';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM libro_concepto
        WHERE isbn = p_isbn AND id_concepto = p_id_concepto
    ) THEN
        RAISE EXCEPTION 'El concepto % no está definido para el libro %', p_id_concepto, p_isbn
            USING ERRCODE = 'P0002';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM clasificadores WHERE id_clasificador = p_id_clasificador) THEN
        RAISE EXCEPTION 'El clasificador % no existe', p_id_clasificador
            USING ERRCODE = 'P0003';
    END IF;

    -- Si esto viola UNIQUE(id_clasificador, isbn, id_concepto), PostgreSQL
    -- lanza 23505 de forma natural — no hace falta un RAISE EXCEPTION
    -- propio; db/queries.py atrapa psycopg2.errors.UniqueViolation.
    INSERT INTO clasificaciones_cloud (isbn, id_concepto, id_clasificador, modelo_cloud)
    VALUES (p_isbn, p_id_concepto, p_id_clasificador, p_modelo_cloud)
    RETURNING id_clasificacion INTO p_id_clasificacion;
END;
$$;

COMMENT ON PROCEDURE sp_registrar_clasificacion(BIGINT, VARCHAR, BIGINT, VARCHAR)
    IS 'Valida isbn/concepto/clasificador e inserta en clasificaciones_cloud dentro de una sola transacción atómica.';

COMMIT;
