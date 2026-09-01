'use strict';

const express = require('express');
const path = require('path');
const session = require('express-session');
const flash = require('connect-flash');
const methodOverride = require('method-override');

const app = express();

// View engine
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, '../views'));

// Body parser
app.use(express.urlencoded({ extended: true }));

// Static files
app.use(express.static(path.join(__dirname, '../public')));

// Method override (for PUT/DELETE via forms)
app.use(methodOverride('_method'));

// Session
app.use(session({
  secret: process.env.SESSION_SECRET || 'libreria_secret_2024',
  resave: false,
  saveUninitialized: false,
  cookie: { maxAge: 8 * 60 * 60 * 1000 } // 8 horas
}));

// Flash messages
app.use(flash());

// Global locals middleware
app.use((req, res, next) => {
  res.locals.success = req.flash('success');
  res.locals.error = req.flash('error');
  res.locals.usuario = req.session.usuario || null;
  next();
});

// Routes
app.get('/', (req, res) => res.redirect('/libros'));

const usuariosRoutes = require('./modules/usuarios/routes');
const librosRoutes = require('./modules/libros/routes');
const autoresRoutes = require('./modules/autores/routes');
const generosRoutes = require('./modules/generos/routes');
const formatosRoutes = require('./modules/formatos/routes');
const conceptosRoutes = require('./modules/conceptos/routes');

app.use('/usuarios', usuariosRoutes);
app.use('/libros', librosRoutes);
app.use('/autores', autoresRoutes);
app.use('/generos', generosRoutes);
app.use('/formatos', formatosRoutes);
app.use('/conceptos', conceptosRoutes);

// 404 handler
app.use((req, res) => {
  res.status(404).render('404', { titulo: 'Página no encontrada' });
});

// Manejador de errores centralizado (debe ir al final, después de las rutas)
app.use((err, req, res, next) => {
  console.error('Error no controlado:', err);

  if (err.code === 'LIMIT_FILE_SIZE') {
    req.flash('error', 'El archivo excede el tamaño máximo permitido (5MB).');
  } else if (err.message && err.message.includes('Tipo de archivo no permitido')) {
    req.flash('error', err.message);
  } else {
    req.flash('error', 'Ocurrió un error inesperado. Intenta de nuevo.');
  }

  res.redirect('back');
});

module.exports = app;
