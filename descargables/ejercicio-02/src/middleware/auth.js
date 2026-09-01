'use strict';

function isAuthenticated(req, res, next) {
  if (req.session && req.session.usuario) {
    return next();
  }
  req.flash('error', 'Debes iniciar sesión para acceder a esta página.');
  res.redirect('/usuarios/login');
}

function isAdmin(req, res, next) {
  if (req.session && req.session.usuario && req.session.usuario.es_administrador) {
    return next();
  }
  req.flash('error', 'No tienes permisos de administrador para realizar esta acción.');
  res.redirect('/libros');
}

module.exports = { isAuthenticated, isAdmin };
