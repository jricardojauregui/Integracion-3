'use strict';

const { Pool } = require('pg');

const requiredEnvVars = ['DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASS'];
for (const key of requiredEnvVars) {
  if (!process.env[key]) {
    throw new Error(`Falta la variable de entorno ${key}. Revisa tu archivo .env`);
  }
}

const pool = new Pool({
  host: process.env.DB_HOST,
  port: parseInt(process.env.DB_PORT, 10),
  database: process.env.DB_NAME,
  user: process.env.DB_USER,
  password: process.env.DB_PASS
});

pool.on('error', (err) => {
  console.error('Error inesperado en el pool de PostgreSQL:', err);
});

module.exports = pool;
