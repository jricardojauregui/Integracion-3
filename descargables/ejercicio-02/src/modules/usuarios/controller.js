'use strict';

const model = require('./model');
const { mensajeAmigable } = require('../../utils/dbErrors');

// GET /usuarios/login
async function getLogin(req, res) {
  if (req.session.usuario) return res.redirect('/libros');
  res.render('usuarios/login', { titulo: 'Iniciar Sesión' });
}

// POST /usuarios/login
async function postLogin(req, res) {
  try {
    const { email, password } = req.body;
    if (!email || !password) {
      req.flash('error', 'Email y contraseña son requeridos.');
      return res.redirect('/usuarios/login');
    }

    const usuario = await model.findByEmail(email);
    if (!usuario) {
      req.flash('error', 'Credenciales incorrectas.');
      return res.redirect('/usuarios/login');
    }

    if (!usuario.activo) {
      req.flash('error', 'Tu cuenta está desactivada. Contacta al administrador.');
      return res.redirect('/usuarios/login');
    }

    const passwordOk = await model.verifyPassword(password, usuario.password_hash);
    if (!passwordOk) {
      req.flash('error', 'Credenciales incorrectas.');
      return res.redirect('/usuarios/login');
    }

    req.session.usuario = {
      id_usuario: usuario.id_usuario,
      nombre: usuario.nombre,
      email: usuario.email,
      es_administrador: usuario.es_administrador
    };

    req.flash('success', `¡Bienvenido, ${usuario.nombre}!`);
    res.redirect('/libros');
  } catch (err) {
    console.error('Error en postLogin:', err);
    req.flash('error', 'Error al iniciar sesión.');
    res.redirect('/usuarios/login');
  }
}

// GET /usuarios/logout
function getLogout(req, res) {
  req.session.destroy((err) => {
    if (err) console.error('Error destruyendo sesión:', err);
    res.redirect('/usuarios/login');
  });
}

// GET /usuarios/registro
async function getRegistro(req, res) {
  if (req.session.usuario) return res.redirect('/libros');
  res.render('usuarios/registro', { titulo: 'Crear Cuenta' });
}

// Validación simple de formato de email (server-side, RNF de REQUIREMENTS.md)
function esEmailValido(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

// POST /usuarios/registro
async function postRegistro(req, res) {
  try {
    const { nombre, email, password, password2 } = req.body;

    if (!nombre || !email || !password || !password2) {
      req.flash('error', 'Todos los campos son requeridos.');
      return res.redirect('/usuarios/registro');
    }

    if (!esEmailValido(email)) {
      req.flash('error', 'El formato del email no es válido.');
      return res.redirect('/usuarios/registro');
    }

    if (password !== password2) {
      req.flash('error', 'Las contraseñas no coinciden.');
      return res.redirect('/usuarios/registro');
    }

    if (password.length < 6) {
      req.flash('error', 'La contraseña debe tener al menos 6 caracteres.');
      return res.redirect('/usuarios/registro');
    }

    const existe = await model.findByEmail(email);
    if (existe) {
      req.flash('error', 'Ya existe una cuenta con ese email.');
      return res.redirect('/usuarios/registro');
    }

    await model.create({ nombre, email, password, es_administrador: false });
    req.flash('success', 'Cuenta creada exitosamente. Ahora puedes iniciar sesión.');
    res.redirect('/usuarios/login');
  } catch (err) {
    console.error('Error en postRegistro:', err);
    req.flash('error', mensajeAmigable(err));
    res.redirect('/usuarios/registro');
  }
}

// GET /usuarios (admin only)
async function getLista(req, res) {
  try {
    const usuarios = await model.findAll();
    res.render('usuarios/lista', { titulo: 'Gestión de Usuarios', usuarios });
  } catch (err) {
    console.error('Error en getLista:', err);
    req.flash('error', 'Error al cargar la lista de usuarios.');
    res.redirect('/libros');
  }
}

// GET /usuarios/:id/editar (admin only)
async function getEditar(req, res) {
  try {
    const usuario = await model.findById(req.params.id);
    if (!usuario) {
      req.flash('error', 'Usuario no encontrado.');
      return res.redirect('/usuarios');
    }
    const adminCount = await model.countAdmins();
    res.render('usuarios/editar', { titulo: 'Editar Usuario', usuario, adminCount });
  } catch (err) {
    console.error('Error en getEditar:', err);
    req.flash('error', 'Error al cargar el usuario.');
    res.redirect('/usuarios');
  }
}

// PUT /usuarios/:id (admin only)
async function putEditar(req, res) {
  try {
    const id = req.params.id;
    const { nombre, email, es_administrador, activo } = req.body;

    if (!nombre || !email) {
      req.flash('error', 'Nombre y email son requeridos.');
      return res.redirect(`/usuarios/${id}/editar`);
    }

    if (!esEmailValido(email)) {
      req.flash('error', 'El formato del email no es válido.');
      return res.redirect(`/usuarios/${id}/editar`);
    }

    await model.update(id, {
      nombre,
      email,
      es_administrador: es_administrador === 'on' || es_administrador === 'true',
      activo: activo === 'on' || activo === 'true'
    });

    // If updating the logged-in user, refresh session
    if (req.session.usuario && req.session.usuario.id_usuario == id) {
      const updated = await model.findById(id);
      req.session.usuario = {
        id_usuario: updated.id_usuario,
        nombre: updated.nombre,
        email: updated.email,
        es_administrador: updated.es_administrador
      };
    }

    req.flash('success', 'Usuario actualizado correctamente.');
    res.redirect('/usuarios');
  } catch (err) {
    console.error('Error en putEditar:', err);
    req.flash('error', mensajeAmigable(err));
    res.redirect(`/usuarios/${req.params.id}/editar`);
  }
}

// DELETE /usuarios/:id (admin only)
async function deleteUsuario(req, res) {
  try {
    const id = req.params.id;

    if (req.session.usuario && req.session.usuario.id_usuario == id) {
      req.flash('error', 'No puedes eliminar tu propia cuenta.');
      return res.redirect('/usuarios');
    }

    await model.remove(id);
    req.flash('success', 'Usuario eliminado correctamente.');
    res.redirect('/usuarios');
  } catch (err) {
    console.error('Error en deleteUsuario:', err);
    req.flash('error', mensajeAmigable(err));
    res.redirect('/usuarios');
  }
}

module.exports = {
  getLogin,
  postLogin,
  getLogout,
  getRegistro,
  postRegistro,
  getLista,
  getEditar,
  putEditar,
  deleteUsuario
};
