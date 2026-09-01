# Tarea 2d — Tabla Resumida de Revisión de Seguridad

Universidad de Monterrey · Integración de Aplicaciones Computacionales · Trabajo en casa 2d

Tabla condensada para publicación en la página web. Detalle completo (amenaza + control +
evidencia de prueba) en [`docs/SECURITY_REVIEW.md`](./SECURITY_REVIEW.md).

| # | Amenaza | Mitigación | Riesgo residual |
|---|---|---|---|
| 1 | Contraseñas en texto plano si se compromete la BD | Hash bcrypt (10 rondas) en todas las contraseñas | Ninguno |
| 2 | Credenciales expuestas en el código fuente o en git | Variables de entorno vía `.env` (no versionado); historial de git limpiado con `git filter-repo` tras detectar exposición previa | Contraseña de PostgreSQL fija por requisito del entorno de práctica (mitigado: solo accesible en `localhost`) |
| 3 | Inyección SQL vía formularios | 100% de las consultas parametrizadas (`$1, $2...`) en los 6 módulos, sin concatenación de strings | Ninguno detectado en la auditoría |
| 4 | Datos inválidos enviados directo al servidor (bypass de validación de JS) | Doble capa: validación server-side en controladores + `CHECK` constraints en PostgreSQL (precio, stock, año, ISBN) | Ninguno |
| 5 | Usuario no-admin accede a funciones administrativas por URL directa | Middlewares `isAuthenticated`/`isAdmin` en cada ruta de escritura de los 6 módulos | Ninguno |
| 6 | Secuestro de sesión (session hijacking) | Sesiones con expiración de 8h, invalidación explícita en logout (`session.destroy`) | Fallback de `SESSION_SECRET` hardcodeado en el código como respaldo si `.env` fallara (riesgo bajo, `.env` sí está bien configurado) |
| 7 | **Subida de archivo ejecutable disfrazado de imagen** (hallazgo crítico real) | Extensión final del archivo decidida por el servidor desde un mapa fijo mimetype→extensión, nunca por el nombre/tipo que envía el cliente; nombre aleatorio | Mimetype sigue siendo dato del cliente; peor caso posible es un `.jpg` no válido, no un ejecutable — probado en vivo con archivo `.php` disfrazado, resultado: guardado como `.jpg` |
| 8 | Mensajes de error exponen estructura interna de la BD (tablas, constraints) | Helper `dbErrors.js` traduce códigos de error de PostgreSQL a mensajes de negocio; manejador de errores centralizado en `app.js` | Ninguno |
| 9 | Un usuario logra crear un segundo Administrador | Índice único parcial en PostgreSQL + trigger con mensaje de negocio claro (`ERRCODE 'P0001'`) | Ninguno — probado en vivo, rechazado correctamente |
| 10 | La app se conecta a la BD con privilegios excesivos | `library_user` confirmado sin atributos especiales (no superusuario, no createdb, no createrole) vía `\du` | Ninguno |
| 11 | Aplicación Node.js accesible directamente desde Internet sin pasar por el reverse proxy | `app.listen(PORT, '127.0.0.1', ...)` + regla de firewall del puerto 3000 eliminada; único acceso público es NGINX en el puerto 80 | Resuelto en la Parte 8 |
| 12 | Publicación accidental de secretos en la página pública del ejercicio | Revisión manual de `docs/` antes de publicar; scripts SQL usan placeholders en vez de contraseñas reales | Pendiente repetir la revisión justo antes de publicar en `ubiquitous.udem.edu` |

---
*12 amenazas documentadas (supera el mínimo de 8 exigido). Documento generado para la Tarea 2d
de trabajo en casa.*
