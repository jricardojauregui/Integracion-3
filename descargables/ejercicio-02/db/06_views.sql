-- =====================================================================
-- 06_views.sql
-- Vistas construidas a partir de las consultas de
-- 03_all_quieries_before_stored_procedures.sql
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. vw_catalogo_libros
--    Catálogo completo listo para mostrar en la interfaz: libro +
--    formato + autores concatenados + géneros concatenados + portada.
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_catalogo_libros AS
SELECT
    l.isbn,
    l.titulo,
    l.anio_publicacion,
    l.precio,
    l.stock,
    f.nombre AS formato,
    string_agg(DISTINCT a.nombre, ', ' ORDER BY a.nombre) AS autores,
    string_agg(DISTINCT g.nombre, ', ' ORDER BY g.nombre) AS generos,
    (SELECT url FROM libro_imagen li
        WHERE li.isbn = l.isbn AND li.es_portada = TRUE LIMIT 1) AS portada_url
FROM libros l
JOIN formatos f           ON f.id_formato = l.id_formato
LEFT JOIN libro_autor la  ON la.isbn = l.isbn
LEFT JOIN autores a       ON a.id_autor = la.id_autor
LEFT JOIN libro_genero lg ON lg.isbn = l.isbn
LEFT JOIN generos g       ON g.id_genero = lg.id_genero
GROUP BY l.isbn, l.titulo, l.anio_publicacion, l.precio, l.stock, f.nombre;

-- ---------------------------------------------------------------------
-- 2. vw_conceptos_por_libro
--    Todos los conceptos y definiciones registrados, con el libro y
--    autor(es) a los que pertenecen, listos para la sección de
--    "conceptos" de la interfaz.
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_conceptos_por_libro AS
SELECT
    l.isbn,
    l.titulo,
    c.id_concepto,
    c.nombre AS concepto,
    lc.definicion
FROM libro_concepto lc
JOIN libros l    ON l.isbn = lc.isbn
JOIN conceptos c ON c.id_concepto = lc.id_concepto
ORDER BY l.titulo, c.nombre;

-- ---------------------------------------------------------------------
-- 3. vw_stock_bajo
--    Libros con stock por debajo del umbral de reabastecimiento (15
--    unidades), para la pantalla de alertas del Administrador.
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_stock_bajo AS
SELECT isbn, titulo, stock
FROM libros
WHERE stock < 15
ORDER BY stock ASC;

-- ---------------------------------------------------------------------
-- 4. vw_resumen_autores
--    Cantidad de libros por autor, útil para reportes administrativos.
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_resumen_autores AS
SELECT
    a.id_autor,
    a.nombre,
    count(la.isbn) AS total_libros
FROM autores a
LEFT JOIN libro_autor la ON la.id_autor = a.id_autor
GROUP BY a.id_autor, a.nombre
ORDER BY total_libros DESC, a.nombre;
