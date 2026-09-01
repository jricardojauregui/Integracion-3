-- =====================================================================
-- ESQUEMA DE BASE DE DATOS - LIBRERÍA EN LÍNEA
-- Motor: PostgreSQL 14+
-- =====================================================================
--
-- ---------------------------------------------------------------------
-- ANÁLISIS DE DEPENDENCIAS FUNCIONALES (DF)
-- ---------------------------------------------------------------------
-- Atributo determinante -> Atributos dependientes
--
--  isbn -> titulo, anio_publicacion, precio, stock, id_formato
--      (el ISBN identifica de forma única los atributos propios del
--       libro; título/año/precio/stock/formato son mono-valuados por
--       libro, por lo que dependen funcionalmente y por completo del
--       ISBN, no de una combinación con autor o género).
--
--  id_autor         -> nombre_autor
--  id_genero        -> nombre_genero
--  id_formato        -> nombre_formato
--  id_concepto       -> nombre_concepto   (el TÉRMINO es único e independiente
--                                           del libro que lo use)
--  id_usuario        -> nombre, email, password_hash, es_administrador
--  id_imagen         -> isbn, url, orden, alt_text
--
--  DF NO TRIVIAL CLAVE DEL DISEÑO (dependencia sobre clave compuesta):
--  (isbn, id_concepto) -> definicion
--      Un mismo concepto (p. ej. "Bildungsroman") puede aparecer en
--      varios libros, pero su DEFINICIÓN es propia de la combinación
--      libro-concepto, no del concepto en sí ni del libro en sí. Por
--      lo tanto "definicion" NO depende funcionalmente de id_concepto
--      solo, ni de isbn solo: depende de la clave compuesta completa.
--      Esto evita anomalías de actualización si el mismo concepto se
--      define distinto en dos libros.
--
-- ---------------------------------------------------------------------
-- ANÁLISIS DE DEPENDENCIAS MULTIVALUADAS (DMV) Y NORMALIZACIÓN 4FN
-- ---------------------------------------------------------------------
-- Si autores, géneros e imágenes se modelaran como columnas repetidas
-- o listas dentro de la tabla "libros", tendríamos DMV independientes:
--
--   isbn ->> id_autor   (múltiples autores por libro)
--   isbn ->> id_genero  (múltiples géneros por libro)
--   isbn ->> id_imagen  (múltiples imágenes por libro)
--
-- Estas tres son DMV independientes entre sí (el conjunto de autores
-- de un libro no depende de cuántos géneros o imágenes tenga). Mezclar
-- estos tres conjuntos multivaluados en una sola tabla generaría
-- productos cartesianos espurios (anomalía clásica de 4FN). La
-- solución es descomponer cada DMV en su propia tabla puente:
--
--   libro_autor(isbn, id_autor)
--   libro_genero(isbn, id_genero)
--   libro_imagen(id_imagen, isbn, url, ...)
--
-- De esta forma cada tabla captura una sola DMV respecto a "libros" y
-- el diseño queda en 4FN.
--
-- El caso libro_concepto es distinto: no es una DMV pura porque el
-- atributo "definicion" cuelga de la combinación (isbn, id_concepto),
-- es decir, es una relación ternaria/asociativa con atributo propio,
-- no una simple tabla puente N:M.
-- =====================================================================

BEGIN;

-- ---------------------------------------------------------------------
-- Función genérica para mantener updated_at
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- 1. USUARIOS  (registro de usuarios; a lo sumo un administrador)
-- =====================================================================
CREATE TABLE usuarios (
    id_usuario       BIGSERIAL PRIMARY KEY,
    nombre           VARCHAR(120)  NOT NULL,
    email            VARCHAR(255)  NOT NULL UNIQUE,
    password_hash    VARCHAR(255)  NOT NULL,
    es_administrador BOOLEAN       NOT NULL DEFAULT FALSE,
    activo           BOOLEAN       NOT NULL DEFAULT TRUE,
    created_at       TIMESTAMPTZ   NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ   NOT NULL DEFAULT now()
);

-- Regla de negocio: "debe existir como máximo un administrador".
-- Un índice único parcial garantiza a nivel de motor que jamás haya
-- más de una fila con es_administrador = TRUE, sin necesidad de
-- lógica en la aplicación ni de un trigger adicional.
CREATE UNIQUE INDEX ux_usuarios_un_solo_admin
    ON usuarios (es_administrador)
    WHERE es_administrador = TRUE;

CREATE TRIGGER trg_usuarios_updated_at
    BEFORE UPDATE ON usuarios
    FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

-- =====================================================================
-- 2. CATÁLOGOS INDEPENDIENTES: formato y género (categoría)
-- =====================================================================
CREATE TABLE formatos (
    id_formato   SMALLSERIAL PRIMARY KEY,
    nombre       VARCHAR(60) NOT NULL UNIQUE   -- p. ej. 'Tapa dura', 'eBook', 'Audiolibro'
);

CREATE TABLE generos (
    id_genero    SMALLSERIAL PRIMARY KEY,
    nombre       VARCHAR(80) NOT NULL UNIQUE   -- p. ej. 'Novela', 'Ciencia ficción'
);

-- =====================================================================
-- 3. AUTORES (catálogo, relación N:M con libros)
-- =====================================================================
CREATE TABLE autores (
    id_autor     BIGSERIAL PRIMARY KEY,
    nombre       VARCHAR(150) NOT NULL,
    UNIQUE (nombre)
);

-- =====================================================================
-- 4. CONCEPTOS (el término en sí, independiente del libro)
-- =====================================================================
CREATE TABLE conceptos (
    id_concepto  BIGSERIAL PRIMARY KEY,
    nombre       VARCHAR(150) NOT NULL UNIQUE  -- término, p. ej. 'Bildungsroman'
);

-- =====================================================================
-- 5. LIBROS (entidad principal; formato es catálogo 1:N)
-- =====================================================================
CREATE TABLE libros (
    isbn              VARCHAR(20)   PRIMARY KEY
                        CONSTRAINT ck_libros_isbn_formato
                        CHECK (isbn ~ '^[0-9Xx-]{10,20}$'),
    titulo            VARCHAR(300)  NOT NULL,
    anio_publicacion  SMALLINT      NOT NULL
                        CHECK (anio_publicacion BETWEEN 1450 AND 2100),
    precio            NUMERIC(10,2) NOT NULL CHECK (precio >= 0),
    stock             INTEGER       NOT NULL DEFAULT 0 CHECK (stock >= 0),
    id_formato        SMALLINT      NOT NULL REFERENCES formatos(id_formato),
    created_at        TIMESTAMPTZ   NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ   NOT NULL DEFAULT now()
);

CREATE INDEX ix_libros_titulo   ON libros USING gin (to_tsvector('spanish', titulo));
CREATE INDEX ix_libros_formato  ON libros (id_formato);

CREATE TRIGGER trg_libros_updated_at
    BEFORE UPDATE ON libros
    FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

-- =====================================================================
-- 6. LIBRO_AUTOR  (resuelve la DMV isbn ->> id_autor, N:M)
-- =====================================================================
CREATE TABLE libro_autor (
    isbn        VARCHAR(20) NOT NULL REFERENCES libros(isbn)  ON DELETE CASCADE,
    id_autor    BIGINT      NOT NULL REFERENCES autores(id_autor) ON DELETE RESTRICT,
    PRIMARY KEY (isbn, id_autor)
);

CREATE INDEX ix_libro_autor_autor ON libro_autor (id_autor);

-- =====================================================================
-- 7. LIBRO_GENERO (resuelve la DMV isbn ->> id_genero, N:M)
-- =====================================================================
CREATE TABLE libro_genero (
    isbn        VARCHAR(20) NOT NULL REFERENCES libros(isbn)   ON DELETE CASCADE,
    id_genero   SMALLINT    NOT NULL REFERENCES generos(id_genero) ON DELETE RESTRICT,
    PRIMARY KEY (isbn, id_genero)
);

CREATE INDEX ix_libro_genero_genero ON libro_genero (id_genero);

-- =====================================================================
-- 8. LIBRO_IMAGEN (resuelve la DMV isbn ->> id_imagen; 1 libro : N imágenes)
-- =====================================================================
CREATE TABLE libro_imagen (
    id_imagen    BIGSERIAL   PRIMARY KEY,
    isbn         VARCHAR(20) NOT NULL REFERENCES libros(isbn) ON DELETE CASCADE,
    url          TEXT        NOT NULL,
    alt_text     VARCHAR(200),
    orden        SMALLINT    NOT NULL DEFAULT 0,
    es_portada   BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_libro_imagen_isbn ON libro_imagen (isbn);

-- A lo sumo una imagen marcada como portada por libro
CREATE UNIQUE INDEX ux_libro_imagen_una_portada
    ON libro_imagen (isbn)
    WHERE es_portada = TRUE;

-- =====================================================================
-- 9. LIBRO_CONCEPTO (relación asociativa con atributo propio: la
--    definición depende de la combinación isbn + id_concepto, no
--    del concepto por sí solo)
-- =====================================================================
CREATE TABLE libro_concepto (
    isbn         VARCHAR(20) NOT NULL REFERENCES libros(isbn)      ON DELETE CASCADE,
    id_concepto  BIGINT      NOT NULL REFERENCES conceptos(id_concepto) ON DELETE RESTRICT,
    definicion   TEXT        NOT NULL,
    PRIMARY KEY (isbn, id_concepto)
);

CREATE INDEX ix_libro_concepto_concepto ON libro_concepto (id_concepto);

COMMIT;

-- =====================================================================
-- COMENTARIOS DE DOCUMENTACIÓN (metadatos visibles vía \d+ / pg_catalog)
-- =====================================================================
COMMENT ON TABLE  usuarios        IS 'Usuarios registrados de la aplicación; a lo sumo uno con es_administrador = TRUE (ver ux_usuarios_un_solo_admin).';
COMMENT ON TABLE  formatos        IS 'Catálogo independiente de formatos de libro (tapa dura, eBook, audiolibro, etc.).';
COMMENT ON TABLE  generos         IS 'Catálogo independiente de géneros/categorías.';
COMMENT ON TABLE  autores         IS 'Catálogo de autores; relación N:M con libros vía libro_autor.';
COMMENT ON TABLE  conceptos       IS 'Términos/conceptos reutilizables; su definición concreta se guarda por libro en libro_concepto.';
COMMENT ON TABLE  libros          IS 'Entidad principal del catálogo; atributos mono-valuados dependen funcionalmente de isbn.';
COMMENT ON TABLE  libro_autor     IS 'Tabla puente N:M que resuelve la dependencia multivaluada isbn ->> id_autor.';
COMMENT ON TABLE  libro_genero    IS 'Tabla puente N:M que resuelve la dependencia multivaluada isbn ->> id_genero.';
COMMENT ON TABLE  libro_imagen    IS 'Imágenes de un libro (1:N); resuelve la dependencia multivaluada isbn ->> id_imagen.';
COMMENT ON TABLE  libro_concepto  IS 'Relación asociativa isbn+id_concepto -> definicion (DF sobre clave compuesta, no DMV pura).';
