-- =====================================================================
-- 05_triggers.sql
-- Triggers de la base de datos. Incluye los dos triggers de auditoría
-- ya definidos en 01_schema.sql (redeclarados aquí de forma idempotente
-- como referencia centralizada) y dos triggers de negocio nuevos.
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. Triggers de auditoría (ya creados en 01_schema.sql; se redeclaran
--    aquí de forma idempotente para tener todos los triggers
--    documentados en un solo archivo, tal como pide el ejercicio)
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_usuarios_updated_at ON usuarios;
CREATE TRIGGER trg_usuarios_updated_at
    BEFORE UPDATE ON usuarios
    FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

DROP TRIGGER IF EXISTS trg_libros_updated_at ON libros;
CREATE TRIGGER trg_libros_updated_at
    BEFORE UPDATE ON libros
    FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

-- ---------------------------------------------------------------------
-- 2. trg_libro_imagen_una_portada
--    Complementa el índice único parcial ux_libro_imagen_una_portada:
--    en vez de que la aplicación reciba un error de violación de índice
--    al marcar una nueva portada, este trigger desmarca automáticamente
--    la portada anterior del mismo libro antes de insertar/actualizar
--    la nueva, haciendo la operación transparente para el usuario.
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_libro_imagen_una_portada()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.es_portada = TRUE THEN
        UPDATE libro_imagen
        SET es_portada = FALSE
        WHERE isbn = NEW.isbn
          AND id_imagen <> COALESCE(NEW.id_imagen, -1)
          AND es_portada = TRUE;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_libro_imagen_una_portada ON libro_imagen;
CREATE TRIGGER trg_libro_imagen_una_portada
    BEFORE INSERT OR UPDATE ON libro_imagen
    FOR EACH ROW EXECUTE FUNCTION fn_libro_imagen_una_portada();

-- ---------------------------------------------------------------------
-- 3. trg_prevenir_segundo_admin
--    Defensa adicional sobre la regla "máximo un Administrador". El
--    índice único parcial ux_usuarios_un_solo_admin YA impide un segundo
--    admin a nivel de motor (es la garantía real e inviolable), pero
--    lanza un error genérico de PostgreSQL poco amigable
--    ("duplicate key value violates unique constraint ..."). Este
--    trigger intercepta el intento ANTES de llegar al índice y da un
--    mensaje de negocio claro, mejorando la experiencia de la capa de
--    aplicación al mostrar el error al usuario final.
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_prevenir_segundo_admin()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.es_administrador = TRUE THEN
        IF EXISTS (
            SELECT 1 FROM usuarios
            WHERE es_administrador = TRUE
              AND id_usuario <> COALESCE(NEW.id_usuario, -1)
        ) THEN
            RAISE EXCEPTION 'Ya existe un usuario Administrador; el sistema permite como máximo uno.'
                USING ERRCODE = 'unique_violation';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_prevenir_segundo_admin ON usuarios;
CREATE TRIGGER trg_prevenir_segundo_admin
    BEFORE INSERT OR UPDATE ON usuarios
    FOR EACH ROW EXECUTE FUNCTION fn_prevenir_segundo_admin();
