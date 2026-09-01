'use strict';

const pool = require('../../config/db');

async function findAll(search = '') {
  let query = `
    SELECT
      l.isbn,
      l.titulo,
      l.anio_publicacion,
      l.precio,
      l.stock,
      f.nombre AS formato,
      STRING_AGG(DISTINCT a.nombre, ', ' ORDER BY a.nombre) AS autores,
      MAX(CASE WHEN li.es_portada THEN li.url END) AS portada_url,
      MAX(CASE WHEN li.es_portada THEN li.alt_text END) AS portada_alt
    FROM libros l
    LEFT JOIN formatos f ON l.id_formato = f.id_formato
    LEFT JOIN libro_autor la ON l.isbn = la.isbn
    LEFT JOIN autores a ON la.id_autor = a.id_autor
    LEFT JOIN libro_imagen li ON l.isbn = li.isbn
    WHERE 1=1
  `;
  const params = [];

  if (search) {
    params.push(`%${search}%`);
    query += ` AND (l.titulo ILIKE $${params.length} OR l.isbn ILIKE $${params.length})`;
  }

  query += `
    GROUP BY l.isbn, l.titulo, l.anio_publicacion, l.precio, l.stock, f.nombre
    ORDER BY l.titulo
  `;

  const result = await pool.query(query, params);
  return result.rows;
}

async function findByIsbn(isbn) {
  const result = await pool.query(
    `SELECT l.*, f.nombre AS formato
     FROM libros l
     LEFT JOIN formatos f ON l.id_formato = f.id_formato
     WHERE l.isbn = $1`,
    [isbn]
  );
  return result.rows[0] || null;
}

async function findFullByIsbn(isbn) {
  const libroResult = await pool.query(
    `SELECT l.*, f.nombre AS formato
     FROM libros l
     LEFT JOIN formatos f ON l.id_formato = f.id_formato
     WHERE l.isbn = $1`,
    [isbn]
  );

  const libro = libroResult.rows[0];
  if (!libro) return null;

  const [autoresResult, generosResult, imagenesResult, conceptosResult] = await Promise.all([
    pool.query(
      `SELECT a.id_autor, a.nombre FROM autores a
       JOIN libro_autor la ON a.id_autor = la.id_autor
       WHERE la.isbn = $1 ORDER BY a.nombre`,
      [isbn]
    ),
    pool.query(
      `SELECT g.id_genero, g.nombre FROM generos g
       JOIN libro_genero lg ON g.id_genero = lg.id_genero
       WHERE lg.isbn = $1 ORDER BY g.nombre`,
      [isbn]
    ),
    pool.query(
      `SELECT id_imagen, url, alt_text, orden, es_portada
       FROM libro_imagen WHERE isbn = $1 ORDER BY es_portada DESC, orden ASC`,
      [isbn]
    ),
    pool.query(
      `SELECT lc.id_concepto, c.nombre, lc.definicion
       FROM libro_concepto lc
       JOIN conceptos c ON lc.id_concepto = c.id_concepto
       WHERE lc.isbn = $1 ORDER BY c.nombre`,
      [isbn]
    )
  ]);

  return {
    ...libro,
    autores: autoresResult.rows,
    generos: generosResult.rows,
    imagenes: imagenesResult.rows,
    conceptos: conceptosResult.rows
  };
}

async function create(client, { isbn, titulo, anio_publicacion, precio, stock, id_formato }) {
  const result = await client.query(
    `INSERT INTO libros (isbn, titulo, anio_publicacion, precio, stock, id_formato)
     VALUES ($1, $2, $3, $4, $5, $6)
     RETURNING *`,
    [isbn, titulo, anio_publicacion, precio, stock || 0, id_formato]
  );
  return result.rows[0];
}

async function update(client, isbn, { titulo, anio_publicacion, precio, stock, id_formato }) {
  const result = await client.query(
    `UPDATE libros
     SET titulo = $1, anio_publicacion = $2, precio = $3, stock = $4, id_formato = $5, updated_at = NOW()
     WHERE isbn = $6
     RETURNING *`,
    [titulo, anio_publicacion, precio, stock, id_formato, isbn]
  );
  return result.rows[0];
}

async function remove(isbn) {
  await pool.query('DELETE FROM libros WHERE isbn = $1', [isbn]);
}

async function setAutores(client, isbn, autoresIds = []) {
  await client.query('DELETE FROM libro_autor WHERE isbn = $1', [isbn]);
  for (const id_autor of autoresIds) {
    await client.query(
      'INSERT INTO libro_autor (isbn, id_autor) VALUES ($1, $2)',
      [isbn, id_autor]
    );
  }
}

async function setGeneros(client, isbn, generosIds = []) {
  await client.query('DELETE FROM libro_genero WHERE isbn = $1', [isbn]);
  for (const id_genero of generosIds) {
    await client.query(
      'INSERT INTO libro_genero (isbn, id_genero) VALUES ($1, $2)',
      [isbn, id_genero]
    );
  }
}

async function addImagen(isbn, { url, alt_text, orden, es_portada }) {
  if (es_portada) {
    await pool.query(
      'UPDATE libro_imagen SET es_portada = false WHERE isbn = $1 AND es_portada = true',
      [isbn]
    );
  }
  const result = await pool.query(
    `INSERT INTO libro_imagen (isbn, url, alt_text, orden, es_portada)
     VALUES ($1, $2, $3, $4, $5)
     RETURNING *`,
    [isbn, url, alt_text || '', orden || 0, es_portada || false]
  );
  return result.rows[0];
}

async function removeImagen(id_imagen) {
  await pool.query('DELETE FROM libro_imagen WHERE id_imagen = $1', [id_imagen]);
}

async function addConcepto(isbn, id_concepto, definicion) {
  const result = await pool.query(
    `INSERT INTO libro_concepto (isbn, id_concepto, definicion)
     VALUES ($1, $2, $3)
     ON CONFLICT (isbn, id_concepto) DO UPDATE SET definicion = EXCLUDED.definicion
     RETURNING *`,
    [isbn, id_concepto, definicion]
  );
  return result.rows[0];
}

async function removeConcepto(isbn, id_concepto) {
  await pool.query(
    'DELETE FROM libro_concepto WHERE isbn = $1 AND id_concepto = $2',
    [isbn, id_concepto]
  );
}

module.exports = {
  findAll,
  findByIsbn,
  findFullByIsbn,
  create,
  update,
  remove,
  setAutores,
  setGeneros,
  addImagen,
  removeImagen,
  addConcepto,
  removeConcepto
};
