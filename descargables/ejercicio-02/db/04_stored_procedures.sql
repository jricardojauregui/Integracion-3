-- =====================================================================
-- 04_stored_procedures.sql
-- Procedimientos almacenados que encapsulan operaciones de negocio
-- representativas, construidos a partir de las consultas exploratorias
-- de 03_all_quieries_before_stored_procedures.sql
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. sp_crear_libro_con_relaciones
--    Crea un libro y asocia autores y géneros en una sola transacción
--    atómica (o todo se aplica, o nada, evitando libros "huérfanos" sin
--    autor/género si algo falla a medio camino).
-- ---------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE sp_crear_libro_con_relaciones(
    p_isbn             VARCHAR(20),
    p_titulo           VARCHAR(300),
    p_anio_publicacion SMALLINT,
    p_precio           NUMERIC(10,2),
    p_stock            INTEGER,
    p_id_formato       SMALLINT,
    p_autores          BIGINT[],   -- arreglo de id_autor
    p_generos          SMALLINT[]  -- arreglo de id_genero
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_id_autor  BIGINT;
    v_id_genero SMALLINT;
BEGIN
    INSERT INTO libros (isbn, titulo, anio_publicacion, precio, stock, id_formato)
    VALUES (p_isbn, p_titulo, p_anio_publicacion, p_precio, p_stock, p_id_formato);

    FOREACH v_id_autor IN ARRAY p_autores LOOP
        INSERT INTO libro_autor (isbn, id_autor) VALUES (p_isbn, v_id_autor);
    END LOOP;

    FOREACH v_id_genero IN ARRAY p_generos LOOP
        INSERT INTO libro_genero (isbn, id_genero) VALUES (p_isbn, v_id_genero);
    END LOOP;
END;
$$;

-- Ejemplo de uso:
-- CALL sp_crear_libro_con_relaciones('978-0-00-111111-1', 'Libro de ejemplo', 2022, 199.00, 20, 2, ARRAY[1,6]::BIGINT[], ARRAY[1,4]::SMALLINT[]);

-- ---------------------------------------------------------------------
-- 2. sp_registrar_concepto_libro
--    Registra (o actualiza) la definición de un concepto para un libro
--    específico. Si el concepto no existe en el catálogo, lo crea.
-- ---------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE sp_registrar_concepto_libro(
    p_isbn        VARCHAR(20),
    p_nombre_concepto VARCHAR(150),
    p_definicion  TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_id_concepto BIGINT;
BEGIN
    SELECT id_concepto INTO v_id_concepto
    FROM conceptos WHERE nombre = p_nombre_concepto;

    IF v_id_concepto IS NULL THEN
        INSERT INTO conceptos (nombre) VALUES (p_nombre_concepto)
        RETURNING id_concepto INTO v_id_concepto;
    END IF;

    INSERT INTO libro_concepto (isbn, id_concepto, definicion)
    VALUES (p_isbn, v_id_concepto, p_definicion)
    ON CONFLICT (isbn, id_concepto)
    DO UPDATE SET definicion = EXCLUDED.definicion;
END;
$$;

-- Ejemplo de uso:
-- CALL sp_registrar_concepto_libro('978-0-307-47472-8', 'Realismo mágico', 'Definición actualizada...');

-- ---------------------------------------------------------------------
-- 3. sp_marcar_portada
--    Marca una imagen específica como portada de un libro, garantizando
--    que sea la única (delega el "descuido" de las demás al trigger
--    trg_libro_imagen_una_portada de 05_triggers.sql, pero también
--    puede usarse de forma independiente sin depender del trigger).
-- ---------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE sp_marcar_portada(
    p_isbn      VARCHAR(20),
    p_id_imagen BIGINT
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM libro_imagen WHERE id_imagen = p_id_imagen AND isbn = p_isbn) THEN
        RAISE EXCEPTION 'La imagen % no pertenece al libro %', p_id_imagen, p_isbn;
    END IF;

    UPDATE libro_imagen SET es_portada = FALSE WHERE isbn = p_isbn;
    UPDATE libro_imagen SET es_portada = TRUE  WHERE id_imagen = p_id_imagen;
END;
$$;

-- Ejemplo de uso:
-- CALL sp_marcar_portada('978-0-307-47472-8', 3);

-- ---------------------------------------------------------------------
-- 4. sp_ajustar_stock
--    Incrementa o decrementa el stock de un libro de forma segura,
--    rechazando explícitamente cualquier operación que lo deje negativo
--    (defensa adicional a nivel de procedimiento, más allá del CHECK).
-- ---------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE sp_ajustar_stock(
    p_isbn     VARCHAR(20),
    p_cantidad INTEGER  -- positivo para entradas, negativo para salidas/ventas
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_stock_actual INTEGER;
BEGIN
    SELECT stock INTO v_stock_actual FROM libros WHERE isbn = p_isbn FOR UPDATE;

    IF v_stock_actual IS NULL THEN
        RAISE EXCEPTION 'No existe un libro con ISBN %', p_isbn;
    END IF;

    IF v_stock_actual + p_cantidad < 0 THEN
        RAISE EXCEPTION 'Operación rechazada: dejaría el stock en % (negativo) para el libro %',
            v_stock_actual + p_cantidad, p_isbn;
    END IF;

    UPDATE libros SET stock = stock + p_cantidad WHERE isbn = p_isbn;
END;
$$;

-- Ejemplo de uso:
-- CALL sp_ajustar_stock('978-0-307-47472-8', -5);  -- venta de 5 unidades
-- CALL sp_ajustar_stock('978-0-307-47472-8', 20);  -- reabastecimiento
