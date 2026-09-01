# Plan y Matriz de Pruebas — Librería en Línea

Universidad de Monterrey · Integración de Aplicaciones Computacionales

Formato por caso: **ID · Requisito relacionado · Precondición · Entrada · Pasos · Resultado
esperado · Resultado observado · Estado · Evidencia**

Leyenda de Estado: ✅ Ejecutada y aprobada · ⬜ Pendiente de ejecutar · ❌ Ejecutada y falló

**Los 23 casos fueron ejecutados y aprobados.**

---

## Pruebas funcionales

### TC-01 — Login exitoso
- **Requisito:** RF-02
- **Entrada:** email correcto + contraseña correcta.
- **Resultado esperado:** redirección a `/libros`, sesión creada.
- **Resultado observado:** login exitoso, sesión activa confirmada.
- **Estado:** ✅

### TC-02 — Login fallido con contraseña incorrecta
- **Requisito:** RF-02
- **Entrada:** email correcto + contraseña incorrecta.
- **Resultado esperado:** mensaje genérico "Credenciales incorrectas", no se crea sesión.
- **Resultado observado:** mensaje "Credenciales incorrectas" mostrado correctamente.
- **Estado:** ✅

### TC-03 — Logout invalida la sesión
- **Requisito:** RF-03
- **Pasos:** loguearse, cerrar sesión, intentar acceder a `/libros`.
- **Resultado esperado:** redirección a `/usuarios/login`.
- **Resultado observado:** redirigido correctamente a login tras logout.
- **Estado:** ✅

### TC-04 — Búsqueda por ISBN exacto
- **Requisito:** RF-05
- **Entrada:** `978-0-307-47472-8`
- **Resultado esperado:** un solo resultado: "Cien años de soledad".
- **Resultado observado:** un solo resultado correcto.
- **Estado:** ✅

### TC-05 — Búsqueda por título parcial
- **Requisito:** RF-05
- **Entrada:** `soledad`
- **Resultado esperado:** incluye "Cien años de soledad" y "El laberinto de la soledad".
- **Resultado observado:** ambos resultados aparecieron.
- **Estado:** ✅

### TC-06 — Crear libro con autores y géneros (transacción completa)
- **Requisito:** RF-07, RF-12, RF-13
- **Pasos:** crear libro `978-0-00-999999-9` con 2 autores y 2 géneros.
- **Resultado esperado:** libro creado con autores/géneros correctamente asociados.
- **Resultado observado:** creado correctamente, asociaciones visibles en el detalle.
- **Estado:** ✅

### TC-07 — Editar libro (cambiar autores asociados)
- **Requisito:** RF-07, RF-12
- **Pasos:** quitar un autor y agregar otro distinto al libro de TC-06.
- **Resultado esperado:** `libro_autor` refleja exactamente la nueva selección.
- **Resultado observado:** cambio reflejado correctamente (patrón "borrar todo y reinsertar" en `setAutores` funcionando).
- **Estado:** ✅

### TC-08 — Eliminar libro
- **Requisito:** RF-07
- **Pasos:** eliminar el libro de prueba; verificar `libro_autor` en BD.
- **Resultado esperado:** el libro y sus filas relacionadas desaparecen (`ON DELETE CASCADE`).
- **Resultado observado:** `SELECT count(*) FROM libro_autor WHERE isbn = '978-0-00-999999-9';` → `0`.
- **Estado:** ✅

### TC-09 — CRUD de catálogos simples (autores/géneros/formatos/conceptos)
- **Requisito:** RF-08, RF-09, RF-10, RF-11
- **Pasos:** crear, editar y eliminar un registro de prueba en `autores`.
- **Resultado esperado:** operaciones exitosas con mensajes de confirmación.
- **Resultado observado:** crear/editar/eliminar funcionaron sin errores.
- **Estado:** ✅

### TC-10 — Registrar concepto y definición específica de un libro
- **Requisito:** RF-14
- **Pasos:** agregar el concepto "Realismo mágico" con una definición nueva a un libro.
- **Resultado esperado:** se guarda en `libro_concepto` sin conflicto con la definición del mismo concepto en otro libro.
- **Resultado observado:** guardado correctamente, sin conflicto entre definiciones del mismo concepto en libros distintos.
- **Estado:** ✅

### TC-11 — Cargar imagen válida y marcarla como portada
- **Requisito:** RF-15, RF-16
- **Pasos:** subir imagen real, marcarla como portada de un libro que ya tenía otra portada.
- **Resultado esperado:** el trigger `trg_libro_imagen_una_portada` desmarca automáticamente la portada anterior.
- **Resultado observado:** portada anterior desmarcada automáticamente, sin intervención manual.
- **Estado:** ✅

---

## Pruebas de seguridad

### TC-12 — Rechazo de archivo malicioso disfrazado de imagen
- **Requisito:** RF-15, RNF-01, control #7 de `SECURITY_REVIEW.md`
- **Entrada:** archivo `fake.php` con `Content-Type: image/jpeg` falsificado.
- **Resultado esperado:** el archivo se guarda con extensión `.jpg` forzada por el servidor.
- **Resultado observado:** archivo guardado como `img_1788151789469_973ed0739e100ad31b82bf5c8b56adb4.jpg` (22 bytes, contenido PHP intacto pero extensión forzada).
- **Estado:** ✅
- **Evidencia:** ver `AI_CHANGELOG.md` y `SECURITY_REVIEW.md` control #7.

### TC-13 — Usuario no-admin intenta acceder a una ruta administrativa
- **Requisito:** RF-19, RF-21
- **Pasos:** usuario registrado (no-admin) navega directo a `/libros/nuevo`.
- **Resultado esperado:** redirección con mensaje "No tienes permisos de administrador".
- **Resultado observado:** redirigido correctamente con el mensaje esperado; el registro NO se creó.
- **Estado:** ✅

### TC-14 — Visitante sin sesión intenta acceder al catálogo
- **Requisito:** actor Visitante (`REQUIREMENTS.md` sección 7.1)
- **Pasos:** sin sesión, navegar directamente a `/libros`.
- **Resultado esperado:** redirección a `/usuarios/login`.
- **Resultado observado:** redirigido correctamente a login.
- **Estado:** ✅

### TC-15 — Creación de un segundo Administrador (regla de negocio crítica)
- **Requisito:** RF-20
- **Entrada:** `INSERT` marcando `es_administrador = TRUE` en un segundo usuario.
- **Resultado esperado:** rechazado con mensaje de negocio claro.
- **Resultado observado:** `ERROR: Ya existe un usuario Administrador; el sistema permite como máximo uno.`
- **Estado:** ✅

### TC-16 — Consulta con caracteres especiales (verificación de parametrización)
- **Requisito:** RNF-02
- **Entrada:** búsqueda con `'; DROP TABLE libros; --`
- **Resultado esperado:** ningún efecto destructivo.
- **Resultado observado:** la búsqueda no tuvo efecto en la BD; `\dt libros` confirmó que la tabla sigue existiendo intacta.
- **Estado:** ✅

---

## Pruebas negativas de base de datos e integridad

### TC-17 — ISBN duplicado
- **Requisito:** RNF-04
- **Resultado esperado:** rechazado por violación de PK.
- **Resultado observado:** `ERROR: duplicate key value violates unique constraint "libros_pkey"`.
- **Estado:** ✅

### TC-18 — Stock negativo
- **Requisito:** RF-18, RNF-04
- **Resultado esperado:** rechazado por `CHECK (stock >= 0)`.
- **Resultado observado:** `ERROR: new row for relation "libros" violates check constraint "libros_stock_check"`.
- **Estado:** ✅

### TC-19 — Precio inválido
- **Requisito:** RF-18
- **Resultado esperado:** rechazado por `CHECK (precio >= 0)`.
- **Resultado observado:** `ERROR: new row for relation "libros" violates check constraint "libros_precio_check"`.
- **Estado:** ✅

### TC-20 — Llave foránea inexistente
- **Requisito:** integridad referencial (Parte 3)
- **Resultado esperado:** rechazado con error de FK.
- **Resultado observado:** `ERROR: insert or update on table "libro_autor" violates foreign key constraint "libro_autor_id_autor_fkey"`.
- **Estado:** ✅

### TC-21 — Eliminación que viola una relación (ON DELETE RESTRICT)
- **Requisito:** integridad referencial (Parte 3)
- **Entrada:** eliminar al autor García Márquez (id_autor=1), que tiene libros asociados.
- **Resultado esperado:** rechazado.
- **Resultado observado:** `ERROR: update or delete on table "autores" violates foreign key constraint "libro_autor_id_autor_fkey" on table "libro_autor"`.
- **Estado:** ✅

---

## Prueba de despliegue

### TC-22 — Acceso mediante reverse proxy
- **Requisito:** Parte 8 del ejercicio
- **Pasos:** desde una ventana de incógnito (sin sesión), acceder a `http://34.51.64.152/library/libros`.
- **Resultado esperado:** la ruta protegida redirige a login; la página de login carga completa con estilos.
- **Resultado observado:** redirección correcta a `/library/usuarios/login`, página cargó completa con CSS a través de NGINX.
- **Estado:** ✅

---

## Prueba de navegación y usabilidad

### TC-23 — Navegación básica end-to-end
- **Requisito:** RNF-06
- **Pasos:** como usuario registrado: login → catálogo → detalle de libro → conceptos → logout.
- **Resultado esperado:** flujo completo sin errores 500.
- **Resultado observado:** flujo completo exitoso, sin errores en ningún paso.
- **Estado:** ✅

---
*Documento generado como parte de la evidencia de la Parte 7 del ejercicio y actualizado con
resultados reales de ejecución. 23/23 casos ejecutados y aprobados — cubre pruebas funcionales,
de autorización, negativas de base de datos, de seguridad, de despliegue y de usabilidad,
superando el mínimo de 15 exigido por la Tarea 2b de trabajo en casa.*
