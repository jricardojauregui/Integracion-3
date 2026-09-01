'use strict';

const pool = require('../../config/db');
const model = require('./model');
const autoresModel = require('../autores/model');
const generosModel = require('../generos/model');
const formatosModel = require('../formatos/model');
const conceptosModel = require('../conceptos/model');
const upload = require('../../middleware/upload');
const { mensajeAmigable } = require('../../utils/dbErrors');

// GET /libros
async function getLista(req, res) {
  try {
    const search = req.query.q || '';
    const libros = await model.findAll(search);
    res.render('libros/lista', { titulo: 'Catálogo de Libros', libros, search });
  } catch (err) {
    console.error('Error en getLista:', err);
    req.flash('error', 'Error al cargar el catálogo de libros.');
    res.redirect('/');
  }
}

// GET /libros/:isbn
async function getDetalle(req, res) {
  try {
    const libro = await model.findFullByIsbn(req.params.isbn);
    if (!libro) {
      return res.status(404).render('404', { titulo: 'Libro no encontrado' });
    }
    const todosConceptos = await conceptosModel.findAll();
    res.render('libros/detalle', { titulo: libro.titulo, libro, todosConceptos });
  } catch (err) {
    console.error('Error en getDetalle:', err);
    req.flash('error', 'Error al cargar el libro.');
    res.redirect('/libros');
  }
}

// GET /libros/nuevo
async function getNuevo(req, res) {
  try {
    const [autores, generos, formatos] = await Promise.all([
      autoresModel.findAll(),
      generosModel.findAll(),
      formatosModel.findAll()
    ]);
    res.render('libros/nuevo', { titulo: 'Nuevo Libro', autores, generos, formatos });
  } catch (err) {
    console.error('Error en getNuevo:', err);
    req.flash('error', 'Error al cargar el formulario.');
    res.redirect('/libros');
  }
}

// POST /libros
async function postNuevo(req, res) {
  const client = await pool.connect();
  try {
    const { isbn, titulo, anio_publicacion, precio, stock, id_formato } = req.body;
    let autoresIds = req.body.autores || [];
    let generosIds = req.body.generos || [];
    if (!Array.isArray(autoresIds)) autoresIds = [autoresIds];
    if (!Array.isArray(generosIds)) generosIds = [generosIds];

    await client.query('BEGIN');
    await model.create(client, { isbn, titulo, anio_publicacion, precio, stock, id_formato });
    await model.setAutores(client, isbn, autoresIds);
    await model.setGeneros(client, isbn, generosIds);
    await client.query('COMMIT');

    req.flash('success', 'Libro creado exitosamente.');
    res.redirect(`/libros/${encodeURIComponent(isbn)}`);
  } catch (err) {
    await client.query('ROLLBACK');
    console.error('Error en postNuevo:', err);
    req.flash('error', mensajeAmigable(err));
    res.redirect('/libros/nuevo');
  } finally {
    client.release();
  }
}

// GET /libros/:isbn/editar
async function getEditar(req, res) {
  try {
    const [libro, autores, generos, formatos] = await Promise.all([
      model.findFullByIsbn(req.params.isbn),
      autoresModel.findAll(),
      generosModel.findAll(),
      formatosModel.findAll()
    ]);

    if (!libro) {
      req.flash('error', 'Libro no encontrado.');
      return res.redirect('/libros');
    }

    res.render('libros/editar', { titulo: 'Editar Libro', libro, autores, generos, formatos });
  } catch (err) {
    console.error('Error en getEditar:', err);
    req.flash('error', 'Error al cargar el formulario de edición.');
    res.redirect('/libros');
  }
}

// PUT /libros/:isbn
async function putEditar(req, res) {
  const client = await pool.connect();
  const isbn = req.params.isbn;
  try {
    const { titulo, anio_publicacion, precio, stock, id_formato } = req.body;
    let autoresIds = req.body.autores || [];
    let generosIds = req.body.generos || [];
    if (!Array.isArray(autoresIds)) autoresIds = [autoresIds];
    if (!Array.isArray(generosIds)) generosIds = [generosIds];

    await client.query('BEGIN');
    await model.update(client, isbn, { titulo, anio_publicacion, precio, stock, id_formato });
    await model.setAutores(client, isbn, autoresIds);
    await model.setGeneros(client, isbn, generosIds);
    await client.query('COMMIT');

    req.flash('success', 'Libro actualizado exitosamente.');
    res.redirect(`/libros/${encodeURIComponent(isbn)}`);
  } catch (err) {
    await client.query('ROLLBACK');
    console.error('Error en putEditar:', err);
    req.flash('error', mensajeAmigable(err));
    res.redirect(`/libros/${encodeURIComponent(isbn)}/editar`);
  } finally {
    client.release();
  }
}

// DELETE /libros/:isbn
async function deleteLibro(req, res) {
  try {
    await model.remove(req.params.isbn);
    req.flash('success', 'Libro eliminado correctamente.');
    res.redirect('/libros');
  } catch (err) {
    console.error('Error en deleteLibro:', err);
    req.flash('error', mensajeAmigable(err));
    res.redirect('/libros');
  }
}

// POST /libros/:isbn/imagenes
async function postAddImagen(req, res) {
  const isbn = req.params.isbn;
  try {
    if (!req.file) {
      req.flash('error', 'No se recibió ningún archivo de imagen.');
      return res.redirect(`/libros/${encodeURIComponent(isbn)}`);
    }

    const { alt_text, orden, es_portada } = req.body;
    const url = `/uploads/${req.file.filename}`;

    await model.addImagen(isbn, {
      url,
      alt_text: alt_text || '',
      orden: orden ? parseInt(orden, 10) : 0,
      es_portada: es_portada === 'on' || es_portada === 'true'
    });

    req.flash('success', 'Imagen agregada correctamente.');
  } catch (err) {
    console.error('Error en postAddImagen:', err);
    req.flash('error', mensajeAmigable(err));
  }
  res.redirect(`/libros/${encodeURIComponent(isbn)}`);
}

// DELETE /libros/:isbn/imagenes/:id
async function deleteImagen(req, res) {
  const isbn = req.params.isbn;
  try {
    await model.removeImagen(req.params.id);
    req.flash('success', 'Imagen eliminada correctamente.');
  } catch (err) {
    console.error('Error en deleteImagen:', err);
    req.flash('error', mensajeAmigable(err));
  }
  res.redirect(`/libros/${encodeURIComponent(isbn)}`);
}

// POST /libros/:isbn/conceptos
async function postAddConcepto(req, res) {
  const isbn = req.params.isbn;
  try {
    const { id_concepto, definicion } = req.body;
    if (!id_concepto || !definicion) {
      req.flash('error', 'Concepto y definición son requeridos.');
      return res.redirect(`/libros/${encodeURIComponent(isbn)}`);
    }
    await model.addConcepto(isbn, id_concepto, definicion);
    req.flash('success', 'Concepto agregado correctamente.');
  } catch (err) {
    console.error('Error en postAddConcepto:', err);
    req.flash('error', mensajeAmigable(err));
  }
  res.redirect(`/libros/${encodeURIComponent(isbn)}`);
}

// DELETE /libros/:isbn/conceptos/:id_concepto
async function deleteConcepto(req, res) {
  const isbn = req.params.isbn;
  try {
    await model.removeConcepto(isbn, req.params.id_concepto);
    req.flash('success', 'Concepto eliminado correctamente.');
  } catch (err) {
    console.error('Error en deleteConcepto:', err);
    req.flash('error', mensajeAmigable(err));
  }
  res.redirect(`/libros/${encodeURIComponent(isbn)}`);
}

module.exports = {
  getLista,
  getDetalle,
  getNuevo,
  postNuevo,
  getEditar,
  putEditar,
  deleteLibro,
  postAddImagen,
  deleteImagen,
  postAddConcepto,
  deleteConcepto
};
