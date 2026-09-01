'use strict';

const bcrypt = require('bcryptjs');
const pool = require('../../config/db');

async function findByEmail(email) {
  const result = await pool.query(
    'SELECT * FROM usuarios WHERE email = $1',
    [email]
  );
  return result.rows[0] || null;
}

async function findAll() {
  const result = await pool.query(
    'SELECT id_usuario, nombre, email, es_administrador, activo, created_at, updated_at FROM usuarios ORDER BY nombre'
  );
  return result.rows;
}

async function findById(id) {
  const result = await pool.query(
    'SELECT id_usuario, nombre, email, es_administrador, activo, created_at, updated_at FROM usuarios WHERE id_usuario = $1',
    [id]
  );
  return result.rows[0] || null;
}

async function create({ nombre, email, password, es_administrador = false }) {
  const salt = await bcrypt.genSalt(10);
  const password_hash = await bcrypt.hash(password, salt);
  const result = await pool.query(
    `INSERT INTO usuarios (nombre, email, password_hash, es_administrador, activo)
     VALUES ($1, $2, $3, $4, true)
     RETURNING id_usuario, nombre, email, es_administrador, activo`,
    [nombre, email, password_hash, es_administrador]
  );
  return result.rows[0];
}

async function update(id, { nombre, email, es_administrador, activo }) {
  const result = await pool.query(
    `UPDATE usuarios
     SET nombre = $1, email = $2, es_administrador = $3, activo = $4, updated_at = NOW()
     WHERE id_usuario = $5
     RETURNING id_usuario, nombre, email, es_administrador, activo`,
    [nombre, email, es_administrador, activo, id]
  );
  return result.rows[0];
}

async function updatePassword(id, newPassword) {
  const salt = await bcrypt.genSalt(10);
  const password_hash = await bcrypt.hash(newPassword, salt);
  await pool.query(
    'UPDATE usuarios SET password_hash = $1, updated_at = NOW() WHERE id_usuario = $2',
    [password_hash, id]
  );
}

async function remove(id) {
  await pool.query('DELETE FROM usuarios WHERE id_usuario = $1', [id]);
}

async function verifyPassword(plainPassword, hash) {
  return bcrypt.compare(plainPassword, hash);
}

async function countAdmins() {
  const result = await pool.query(
    'SELECT COUNT(*) AS total FROM usuarios WHERE es_administrador = true'
  );
  return parseInt(result.rows[0].total, 10);
}

module.exports = {
  findByEmail,
  findAll,
  findById,
  create,
  update,
  updatePassword,
  remove,
  verifyPassword,
  countAdmins
};
