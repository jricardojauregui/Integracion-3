-- =====================================================================
-- TABLAS PROPIAS DEL MÓDULO SOAP (Ejercicio04 — Parte 4, Paso 7)
-- =====================================================================
-- Comparten la base de datos con el monolito (library) pero NO forman
-- parte de su esquema funcional. No se ALTERA ninguna tabla existente
-- del monolito; solo se referencian libros.isbn y conceptos.id_concepto
-- como FKs de SOLO LECTURA hacia el catálogo (ver Paso 1).
-- =====================================================================

BEGIN;

-- ---------------------------------------------------------------------
-- 1. clasificadores
-- Identidad de quien usa el clasificador. Datos mínimos necesarios
-- (nombre + apellido) — explícitamente NO es la tabla `usuarios` del
-- monolito (esa tiene password_hash/es_administrador, autenticación
-- del monolito, fuera de alcance de este módulo — ver Paso 1).
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS clasificadores (
    id_clasificador  BIGSERIAL    PRIMARY KEY,
    nombre           VARCHAR(120) NOT NULL CHECK (length(trim(nombre))   > 0),
    apellido         VARCHAR(120) NOT NULL CHECK (length(trim(apellido)) > 0),
    correo           VARCHAR(255),  -- opcional, dato de contacto de la GUI (Paso 14); no autentica ni autoriza
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------
-- 2. clientes_servidos
-- Tipo de cliente de escritorio, identificador y conteo de peticiones
-- atendidas. Independiente de `clasificadores`: registra la aplicación
-- que sirvió la petición (p. ej. client01/Electron), no a la persona.
-- UNIQUE(tipo_cliente, identificador_cliente) evita filas duplicadas
-- para la misma instalación/instancia de cliente.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS clientes_servidos (
    id_cliente_servido    BIGSERIAL    PRIMARY KEY,
    tipo_cliente          VARCHAR(60)  NOT NULL CHECK (length(trim(tipo_cliente)) > 0),
    identificador_cliente VARCHAR(120) NOT NULL,
    peticiones_atendidas  INTEGER      NOT NULL DEFAULT 0 CHECK (peticiones_atendidas >= 0),
    primera_peticion      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    ultima_peticion       TIMESTAMPTZ  NOT NULL DEFAULT now(),
    UNIQUE (tipo_cliente, identificador_cliente)
);

-- ---------------------------------------------------------------------
-- 3. clasificaciones_cloud
-- Concepto, libro, clasificador, modelo Cloud, fecha y auditoría.
-- id_cliente_servido es NULLABLE y ON DELETE SET NULL: es un dato de
-- auditoría (qué cliente sirvió la petición), no debe bloquear ni
-- perder la clasificación si esa fila de clientes_servidos se borra.
--
-- FKs hacia libros/conceptos del monolito: ON DELETE RESTRICT, mismo
-- criterio que usa el propio monolito en libro_concepto.id_concepto —
-- el módulo nunca queda con una clasificación huérfana, y tampoco le
-- exige al monolito ningún cambio de comportamiento al borrar.
--
-- Restricción pedida explícitamente: un mismo clasificador no puede
-- registrar dos veces el mismo concepto. Se interpreta "concepto" a
-- nivel de la unidad que realmente se clasifica — el par (isbn,
-- id_concepto), que es como existe en libro_concepto del monolito (un
-- mismo término puede tener definición distinta por libro) — de ahí
-- UNIQUE(id_clasificador, isbn, id_concepto). Si la intención real era
-- "el mismo id_concepto sin importar el libro", avisar para ajustarlo.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS clasificaciones_cloud (
    id_clasificacion    BIGSERIAL    PRIMARY KEY,
    isbn                VARCHAR(20)  NOT NULL REFERENCES libros(isbn)          ON DELETE RESTRICT,
    id_concepto         BIGINT       NOT NULL REFERENCES conceptos(id_concepto) ON DELETE RESTRICT,
    id_clasificador     BIGINT       NOT NULL REFERENCES clasificadores(id_clasificador) ON DELETE RESTRICT,
    modelo_cloud        VARCHAR(4)   NOT NULL CHECK (modelo_cloud IN ('IaaS', 'PaaS', 'SaaS', 'FaaS')),
    fecha_clasificacion TIMESTAMPTZ  NOT NULL DEFAULT now(),
    id_cliente_servido  BIGINT       REFERENCES clientes_servidos(id_cliente_servido) ON DELETE SET NULL,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT now(),
    UNIQUE (id_clasificador, isbn, id_concepto)
);

CREATE INDEX IF NOT EXISTS ix_clasificaciones_cloud_clasificador
    ON clasificaciones_cloud (id_clasificador);
CREATE INDEX IF NOT EXISTS ix_clasificaciones_cloud_isbn
    ON clasificaciones_cloud (isbn);
CREATE INDEX IF NOT EXISTS ix_clasificaciones_cloud_cliente_servido
    ON clasificaciones_cloud (id_cliente_servido);

COMMENT ON TABLE clasificadores       IS 'Identidad mínima de quien usa el clasificador. Independiente de usuarios del monolito.';
COMMENT ON TABLE clientes_servidos    IS 'Instancias de cliente de escritorio (tipo + identificador) y conteo de peticiones atendidas.';
COMMENT ON TABLE clasificaciones_cloud IS 'Clasificación Cloud (IaaS/PaaS/SaaS/FaaS) de un concepto de un libro; UNIQUE(id_clasificador,isbn,id_concepto) evita que el mismo clasificador repita un concepto.';

COMMIT;
