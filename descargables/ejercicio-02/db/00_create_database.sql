-- =====================================================================
-- 00_create_database.sql
-- Creación del rol de aplicación y la base de datos "library"
-- Ejecutar como superusuario de PostgreSQL:
--   sudo -iu postgres psql -f db/00_create_database.sql
-- =====================================================================
--
-- IMPORTANTE (seguridad):
-- Reemplaza 'CAMBIA_ESTA_CONTRASENA' por el valor real de DB_PASS antes
-- de ejecutar este script en tu servidor. NO commitees este archivo con
-- la contraseña real ya escrita — mantenla como placeholder en git y
-- sustitúyela solo en el momento de ejecutarlo (o pásala por variable
-- de entorno con psql -v).
-- =====================================================================

-- Elimina el rol/base si ya existieran, para poder re-ejecutar el script
-- de forma idempotente en un entorno de práctica (NO usar en producción).
DROP DATABASE IF EXISTS library;
DROP ROLE IF EXISTS library_user;

-- Rol de aplicación con login, sin privilegios de superusuario
CREATE ROLE library_user WITH LOGIN PASSWORD 'CAMBIA_ESTA_CONTRASENA';

-- Base de datos propiedad del rol de aplicación
CREATE DATABASE library OWNER library_user;

-- Principio de mínimo privilegio: el rol de aplicación no debe poder
-- crear otras bases de datos ni otros roles.
ALTER ROLE library_user NOCREATEDB NOCREATEROLE;

\c library

-- Otorga privilegios sobre el esquema public (donde vivirán las tablas
-- creadas en 01_schema.sql) al usuario de aplicación.
GRANT ALL PRIVILEGES ON SCHEMA public TO library_user;
