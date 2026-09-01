# Revisión de Seguridad — Librería en Línea

Universidad de Monterrey · Integración de Aplicaciones Computacionales

Para cada control: **amenaza → control aplicado → evidencia de prueba**. Incluye los 10 controles
mínimos exigidos por el ejercicio, más 2 hallazgos adicionales detectados durante el desarrollo
(12 en total, cubriendo también la Tarea 2d de trabajo en casa, que exige documentar al menos
ocho amenazas).

---

## 1. Hash de contraseñas y política básica de contraseñas

**Amenaza:** si las contraseñas se almacenan en texto plano y la base de datos se ve
comprometida, todas las cuentas quedan expuestas de inmediato.

**Control aplicado:** las contraseñas se hashean con `bcryptjs` (salt de 10 rondas) antes de
guardarse (`usuarios/model.js`, función `create`). Nunca se guarda ni se registra en logs la
contraseña en texto plano. Política mínima: 6 caracteres, validada en `postRegistro`.

**Evidencia de prueba:** se generó un hash real (`node -e "bcrypt.hash(...)"`), se verificó en
la columna `password_hash` de PostgreSQL, y se confirmó login exitoso solo con la contraseña
correcta (`bcrypt.compare` en `verifyPassword`). Una contraseña incorrecta devuelve
"Credenciales incorrectas" sin distinguir si el email existe o no.

---

## 2. Variables de entorno para secretos; `.env` no se publica

**Amenaza:** credenciales de base de datos u otros secretos expuestos en el código fuente o en
el repositorio público.

**Control aplicado:** todas las credenciales (`DB_HOST`, `DB_USER`, `DB_PASS`, `SESSION_SECRET`)
se leen de `.env` vía `dotenv`, nunca hardcodeadas en el código. `.gitignore` excluye `.env`,
`.env.local` y `.env.*.local`.

**Hallazgo real detectado y corregido durante el desarrollo:** `.env` había sido commiteado en
los primeros commits del repositorio antes de que `.gitignore` lo excluyera, quedando accesible
en el historial de git (`git show <commit>:apps/web-monolith/.env`) aunque ya no estuviera en el
working directory.

**Evidencia de prueba:** se limpió el historial completo con `git filter-repo --path
apps/web-monolith/.env --invert-paths` y se forzó el push. Verificación:
```
$ git log --all --oneline -- apps/web-monolith/.env
(sin salida)
```

**Riesgo residual aceptado:** la contraseña de PostgreSQL se mantiene fija en un valor simple
por requisito del entorno de práctica. Se acepta como riesgo residual bajo porque PostgreSQL
solo escucha en `localhost` (no expuesto a la red), por lo que un atacante necesitaría acceso
previo al servidor para explotarlo.

---

## 3. Consultas SQL parametrizadas (prevención de SQL Injection)

**Amenaza:** un atacante inserta código SQL a través de un campo de formulario (título de
libro, email, búsqueda) para leer o modificar datos fuera de control de la aplicación.

**Control aplicado:** el 100% de las consultas en todos los modelos (`usuarios`, `libros`,
`autores`, `generos`, `formatos`, `conceptos`) usa `pool.query(texto, [parámetros])` con
placeholders `$1, $2, ...`. Cero concatenación de strings con datos de entrada en cualquier
módulo revisado.

**Evidencia de prueba:** revisión de código línea por línea de los 6 modelos + `config/db.js`.
Prueba funcional pendiente para `TEST_PLAN`: búsqueda de título con caracteres especiales
(`'; DROP TABLE libros; --`) debe devolver una búsqueda vacía o sin resultados, nunca un error
de sintaxis SQL ni efecto destructivo.

---

## 4. Validación server-side de todos los campos

**Amenaza:** un atacante deshabilita o evita la validación de JavaScript del navegador y envía
datos inválidos directamente al servidor (precio negativo, año fuera de rango, ISBN mal
formado, email inválido).

**Control aplicado:** dos capas independientes:
- **Aplicación:** `postRegistro`/`putEditar` validan campos requeridos, formato de email
  (regex) y longitud de contraseña; controladores de catálogo validan que el nombre no esté
  vacío.
- **Base de datos (última línea de defensa, no depende de que la aplicación no tenga bugs):**
  `CHECK (precio >= 0)`, `CHECK (stock >= 0)`, `CHECK (anio_publicacion BETWEEN 1450 AND 2100)`,
  `CHECK (isbn ~ '^[0-9Xx-]{10,20}$')` en la tabla `libros`.

**Evidencia de prueba:** intento de registro con email `"no-es-un-email"` rechazado con mensaje
claro. Pendiente de capturar para `TEST_PLAN`: intento de `INSERT`/`UPDATE` directo con
`precio = -50` debe ser rechazado por PostgreSQL con el código `23514` (violación de CHECK), y
la aplicación debe traducirlo a un mensaje de negocio vía `mensajeAmigable()`.

---

## 5. Autorización por rol en cada ruta administrativa

**Amenaza:** un usuario autenticado pero no administrador accede directamente por URL a rutas
de creación/edición/eliminación (ej. `POST /libros`, `DELETE /autores/:id`).

**Control aplicado:** middlewares `isAuthenticated` e `isAdmin` (`middleware/auth.js`),
aplicados en `routes.js` de los 6 módulos. Todas las rutas de escritura (`POST`, `PUT`,
`DELETE`) exigen `isAdmin`; las rutas de solo lectura del catálogo exigen únicamente
`isAuthenticated`.

**Evidencia de prueba:** revisión de los 6 archivos `routes.js` confirmando el middleware en
cada ruta de escritura. Pendiente para `TEST_PLAN`: iniciar sesión como usuario no-admin e
intentar `POST /libros` directamente → debe redirigir con mensaje "No tienes permisos de
administrador" y no debe crear el registro.

---

## 6. Manejo seguro de sesiones y cierre de sesión

**Amenaza:** sesiones que nunca expiran, o que no se invalidan correctamente al cerrar sesión,
permitiendo secuestro de sesión (session hijacking) con una cookie robada o reutilizada.

**Control aplicado:** `express-session` con `cookie.maxAge` de 8 horas; `getLogout` llama
`req.session.destroy()` explícitamente, no solo borra la cookie del lado del cliente.
`SESSION_SECRET` se lee de variable de entorno, no hardcodeado en producción (aunque el
fallback en `app.js` sí tiene un valor literal — ver nota abajo).

**Nota de mejora identificada (no bloqueante):** `app.js` tiene
`secret: process.env.SESSION_SECRET || 'libreria_secret_2024'`. Igual que con `DB_PASS`, un
fallback hardcodeado en el código fuente es un mal hábito aunque `.env` sí esté configurado
correctamente en este entorno — si `.env` fallara en cargar, la app seguiría funcionando pero
con un secreto de sesión predecible y público (está en este mismo documento). Se documenta como
mejora recomendada para producción real, no se considera crítico en este entorno de práctica.

**Evidencia de prueba:** después de `logout`, un intento de acceder a `/libros` sin volver a
iniciar sesión redirige a `/usuarios/login`.

---

## 7. Validación de archivos subidos (extensión, MIME, tamaño y nombre)

**Amenaza (la más crítica encontrada en todo el proyecto):** un atacante sube un archivo
ejecutable (ej. `.php`) disfrazado de imagen, falsificando el `Content-Type` de la petición.
Si el archivo queda en una carpeta servida públicamente con la extensión maliciosa intacta,
podría ejecutarse como código en el servidor bajo ciertas configuraciones.

**Hallazgo real detectado:** el `upload.js` original derivaba la extensión del archivo final
directamente de `file.originalname` (dato controlado por el cliente), confiando únicamente en
el `mimetype` (también controlado por el cliente) para el filtro. Esto permitía que un archivo
`shell.php` enviado con `Content-Type: image/jpeg` quedara guardado como `img_....php` dentro
de `public/uploads/`, una ruta servida por `express.static`.

**Control aplicado:** se reescribió `upload.js` para que la extensión del archivo **siempre**
salga de un mapa fijo `mimetype → extensión` decidido por el servidor (`.jpg`, `.png`,
`.webp`), nunca del nombre que envía el cliente. Se agregó también un componente aleatorio
(`crypto.randomBytes`) al nombre final para eliminar colisiones y evitar nombres predecibles.
Límite de tamaño de 5MB (`multer` `limits.fileSize`).

**Evidencia de prueba (realizada en vivo):**
```bash
curl -b cookies.txt -X POST http://localhost:3000/libros/978-0-307-47472-8/imagenes \
  -F "imagen=@fake.php;type=image/jpeg" -F "alt_text=prueba de seguridad"
```
Resultado: el archivo quedó guardado como
`img_1788151789469_973ed0739e100ad31b82bf5c8b56adb4.jpg` (22 bytes, contenido PHP intacto pero
con extensión forzada a `.jpg`) — nunca con extensión `.php`. Vulnerabilidad confirmada y
cerrada con evidencia reproducible.

**Riesgo residual aceptado:** el `mimetype` sigue siendo un dato del cliente y no se valida por
"magic bytes" (firma real del archivo). El peor caso posible ahora es un `.jpg` corrupto/no
válido como imagen, no un archivo ejecutable — riesgo aceptado dado el alcance del ejercicio;
mejora futura sugerida: librería de detección de tipo real de archivo (`file-type`).

---

## 8. Mensajes de error controlados (no exponer stack traces ni SQL)

**Amenaza:** un mensaje de error que expone el nombre de tablas, columnas, constraints o
consultas SQL internas ayuda a un atacante a mapear la estructura de la base de datos
(reconocimiento para un ataque posterior), además de ser una mala experiencia de usuario.

**Hallazgos reales detectados y corregidos:**
1. `libros/controller.js` (`postNuevo`, `putEditar`) devolvía `err.message` de PostgreSQL
   directamente al usuario vía `req.flash`, exponiendo nombres de tabla y constraint.
2. El trigger `fn_prevenir_segundo_admin` usaba `ERRCODE = 'unique_violation'` (23505), el
   mismo código que la violación de email duplicado — causando que el sistema mostrara "ya
   existe un usuario con ese email" al intentar crear un segundo administrador (mensaje
   incorrecto y confuso).

**Control aplicado:** se creó `src/utils/dbErrors.js` (`mensajeAmigable(err)`) que traduce
códigos de error de PostgreSQL (`23505`, `23503`, `23514`, `P0001`) a mensajes de negocio en
español, aplicado en `libros/controller.js` y `usuarios/controller.js`. Se corrigió el trigger
para usar `ERRCODE = 'P0001'` (código genérico de excepción de aplicación, sin colisión con
códigos reales de PostgreSQL). Se agregó un manejador de errores centralizado en `app.js` (con
4 parámetros `(err, req, res, next)`) para capturar errores no manejados explícitamente (p. ej.
los que lanza `multer` al rechazar un archivo).

**Evidencia de prueba:**
```
$ psql ... INSERT INTO usuarios (..., es_administrador) VALUES (..., TRUE);
ERROR:  Ya existe un usuario Administrador; el sistema permite como máximo uno.
```
Mensaje correcto y específico, ya no confundido con el error de email duplicado.

---

## 9. Principio de mínimo privilegio para el usuario de PostgreSQL

**Amenaza:** si la aplicación se conecta con un superusuario de PostgreSQL, cualquier
vulnerabilidad de inyección SQL (aunque esté mitigada por el control #3) tendría el peor caso
posible: control total sobre el servidor de base de datos, no solo sobre los datos de la
aplicación.

**Control aplicado:** la aplicación se conecta exclusivamente con `library_user`, un rol sin
privilegios especiales.

**Evidencia de prueba:**
```
$ psql -U library_user -d library -c "\du library_user"
       List of roles
  Role name   | Attributes
--------------+------------
 library_user |
```
Columna de atributos vacía: no es superusuario, no puede crear bases de datos ni otros roles —
solo tiene los privilegios otorgados sobre el esquema `public` de la base `library`.

---

## 10. No publicar credenciales en `ubiquitous.udem.edu`

**Amenaza:** publicar accidentalmente contraseñas, tokens, llaves SSH o cadenas de conexión en
la página web de evidencias del ejercicio, accesible públicamente.

**Control aplicado:** `docs/GCP_COMMANDS.md` fue redactado explícitamente sin incluir
contraseñas, tokens ni llaves privadas (ver nota al inicio de ese documento). El script
`db/00_create_database.sql` usa un placeholder (`CAMBIA_ESTA_CONTRASENA`) en vez de la
contraseña real, para que el archivo pueda versionarse y publicarse sin exponer el secreto real.

**Evidencia de prueba:** revisión manual de todos los documentos en `docs/` antes de la
publicación final (pendiente de repetir justo antes de publicar en la Parte 10).

---

## 11. Hallazgo adicional — Node.js expuesto directamente a Internet (pendiente, Parte 8)

**Amenaza:** la aplicación Node.js es accesible directamente desde Internet sin pasar por un
reverse proxy, saltándose cualquier control que se planee agregar a nivel de Apache/NGINX
(rate limiting, cabeceras de seguridad, terminación TLS futura, etc.), y exponiendo
directamente el stack tecnológico interno.

**Estado actual:** la regla de firewall de GCP `iac608995` permite `tcp:3000` desde
`0.0.0.0/0`, y `src/server.js` llama `app.listen(PORT)` sin especificar host, lo que hace que
Node escuche en todas las interfaces (`0.0.0.0`) por defecto.

**Decisión:** se deja así intencionalmente durante el desarrollo porque el entorno fue
configurado explícitamente por el profesor para esta etapa. **Antes de la entrega final**, se
debe: (1) cambiar a `app.listen(PORT, '127.0.0.1', callback)`, y (2) cerrar o restringir la
regla de firewall del puerto 3000, dejando como único punto de entrada público el puerto 80 del
reverse proxy (ver Parte 8 / `docs/GCP_COMMANDS.md`).

---

## 12. Hallazgo adicional — Fallback de secreto de sesión hardcodeado

Ver control #6, nota de mejora. Riesgo bajo en este entorno (el `.env` real sí está bien
configurado), documentado por completitud y buena práctica.

---
*Documento generado como parte de la evidencia de la Parte 6 del ejercicio. Cubre los 10
controles mínimos exigidos más 2 hallazgos adicionales, satisfaciendo también el mínimo de 8
amenazas documentadas de la Tarea 2d de trabajo en casa.*
