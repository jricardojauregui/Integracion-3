-- =====================================================================
-- 03_all_quieries_before_stored_procedures.sql
-- Consultas manuales exploratorias, ejecutadas para validar la lógica
-- ANTES de encapsularla en procedimientos almacenados (04), triggers (05)
-- y vistas (06). Sirven como evidencia del razonamiento paso a paso.
-- =====================================================================

-- ---------------------------------------------------------------------
-- A. Consultas de catálogo (bases para la futura vista vw_catalogo_libros)
-- ---------------------------------------------------------------------

-- A.1 Catálogo completo con formato, autores y géneros concatenados
SELECT
    l.isbn,
    l.titulo,
    l.anio_publicacion,
    l.precio,
    l.stock,
    f.nombre AS formato,
    string_agg(DISTINCT a.nombre, ', ') AS autores,
    string_agg(DISTINCT g.nombre, ', ') AS generos
FROM libros l
JOIN formatos f       ON f.id_formato = l.id_formato
LEFT JOIN libro_autor la  ON la.isbn = l.isbn
LEFT JOIN autores a       ON a.id_autor = la.id_autor
LEFT JOIN libro_genero lg ON lg.isbn = l.isbn
LEFT JOIN generos g       ON g.id_genero = lg.id_genero
GROUP BY l.isbn, l.titulo, l.anio_publicacion, l.precio, l.stock, f.nombre
ORDER BY l.titulo;

-- A.2 Búsqueda por ISBN exacto
SELECT * FROM libros WHERE isbn = '978-0-307-47472-8';

-- A.3 Búsqueda por título (usa el índice GIN de texto completo en español)
SELECT isbn, titulo, anio_publicacion
FROM libros
WHERE to_tsvector('spanish', titulo) @@ plainto_tsquery('spanish', 'soledad');

-- A.4 Detalle completo de un libro: autores, géneros, portada, conceptos
SELECT
    l.isbn, l.titulo,
    (SELECT string_agg(a.nombre, ', ') FROM libro_autor la
        JOIN autores a ON a.id_autor = la.id_autor WHERE la.isbn = l.isbn) AS autores,
    (SELECT string_agg(g.nombre, ', ') FROM libro_genero lg
        JOIN generos g ON g.id_genero = lg.id_genero WHERE lg.isbn = l.isbn) AS generos,
    (SELECT url FROM libro_imagen WHERE isbn = l.isbn AND es_portada = TRUE) AS portada_url,
    (SELECT count(*) FROM libro_concepto WHERE isbn = l.isbn) AS num_conceptos
FROM libros l
WHERE l.isbn = '978-0-307-47472-8';

-- ---------------------------------------------------------------------
-- B. Consultas de conceptos por libro (base para vw_conceptos_por_libro)
-- ---------------------------------------------------------------------
SELECT l.titulo, c.nombre AS concepto, lc.definicion
FROM libro_concepto lc
JOIN libros l    ON l.isbn = lc.isbn
JOIN conceptos c ON c.id_concepto = lc.id_concepto
ORDER BY l.titulo, c.nombre;

-- ---------------------------------------------------------------------
-- C. Secuencia manual para "insertar un libro completo" — el flujo que
--    después se encapsula en sp_crear_libro_con_relaciones (04)
-- ---------------------------------------------------------------------
BEGIN;
INSERT INTO libros (isbn, titulo, anio_publicacion, precio, stock, id_formato)
VALUES ('978-0-00-000000-1', 'Libro de prueba manual', 2020, 199.00, 10, 2);

INSERT INTO libro_autor (isbn, id_autor) VALUES ('978-0-00-000000-1', 1);
INSERT INTO libro_genero (isbn, id_genero) VALUES ('978-0-00-000000-1', 1);
COMMIT;

-- Limpieza de la prueba manual anterior (para no dejar basura en el seed)
BEGIN;
DELETE FROM libro_genero WHERE isbn = '978-0-00-000000-1';
DELETE FROM libro_autor  WHERE isbn = '978-0-00-000000-1';
DELETE FROM libros       WHERE isbn = '978-0-00-000000-1';
COMMIT;

-- ---------------------------------------------------------------------
-- D. Secuencia manual para "marcar una imagen como portada" — el flujo
--    que después se encapsula en el trigger trg_libro_imagen_una_portada (05)
-- ---------------------------------------------------------------------
-- Antes de tener el trigger, había que hacerlo en dos pasos manuales:
BEGIN;
UPDATE libro_imagen SET es_portada = FALSE WHERE isbn = '978-0-307-47472-8';
UPDATE libro_imagen SET es_portada = TRUE
    WHERE isbn = '978-0-307-47472-8'
    AND id_imagen = (SELECT MIN(id_imagen) FROM libro_imagen WHERE isbn = '978-0-307-47472-8');
COMMIT;

-- ---------------------------------------------------------------------
-- E. Consulta base para "libros con stock bajo" (base para vw_stock_bajo)
-- ---------------------------------------------------------------------
SELECT isbn, titulo, stock
FROM libros
WHERE stock < 15
ORDER BY stock ASC;

-- ---------------------------------------------------------------------
-- F. Prueba manual de la regla "un solo administrador" antes de agregar
--    el trigger de mensaje amigable (05) — se espera el error genérico
--    de índice único hasta que el trigger dé un mensaje más claro.
-- ---------------------------------------------------------------------
-- INSERT INTO usuarios (nombre, email, password_hash, es_administrador)
-- VALUES ('Segundo Admin', 'segundo.admin@correo.com', 'hash_de_prueba', TRUE);
-- Resultado esperado (sin trigger): ERROR: duplicate key value violates
-- unique constraint "ux_usuarios_un_solo_admin"
