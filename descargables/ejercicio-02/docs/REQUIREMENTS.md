# Requisitos del Sistema — Librería en Línea

Universidad de Monterrey · Integración de Aplicaciones Computacionales
Ejercicio 02 — Aplicación Web Monolítica para Gestión de una Librería

## 1. Descripción del problema

Se requiere una aplicación web monolítica (Node.js + Express + EJS + PostgreSQL) que permita
administrar el catálogo de una librería en línea: libros, autores, géneros, formatos y los
conceptos/definiciones asociados al contenido de cada libro. El sistema debe operar con acceso
restringido a usuarios registrados y con un único usuario Administrador.

## 2. Requisitos funcionales

| ID | Requisito |
|----|-----------|
| RF-01 | El sistema debe permitir el registro de nuevos usuarios (nombre, email único, contraseña). |
| RF-02 | El sistema debe permitir el inicio de sesión mediante email y contraseña. |
| RF-03 | El sistema debe permitir el cierre de sesión, invalidando la sesión activa. |
| RF-04 | Un usuario autenticado debe poder consultar el catálogo completo de libros. |
| RF-05 | El sistema debe permitir buscar libros por ISBN y por título. |
| RF-06 | El sistema debe permitir consultar el detalle de un libro: datos propios, autores, géneros, formato, imágenes y conceptos/definiciones asociados. |
| RF-07 | El Administrador debe poder crear, consultar, actualizar y eliminar registros de `libros`. |
| RF-08 | El Administrador debe poder crear, consultar, actualizar y eliminar registros de `autores`. |
| RF-09 | El Administrador debe poder crear, consultar, actualizar y eliminar registros de `generos`. |
| RF-10 | El Administrador debe poder crear, consultar, actualizar y eliminar registros de `formatos`. |
| RF-11 | El Administrador debe poder crear, consultar, actualizar y eliminar registros de `conceptos`. |
| RF-12 | El sistema debe permitir asociar uno o varios autores a un mismo libro (`libro_autor`). |
| RF-13 | El sistema debe permitir asociar uno o varios géneros a un mismo libro (`libro_genero`). |
| RF-14 | El sistema debe permitir registrar, por libro, uno o varios conceptos junto con su definición específica para ese libro (`libro_concepto`), ya que la misma definición no aplica necesariamente a otro libro que use el mismo concepto. |
| RF-15 | El sistema debe permitir cargar una o varias imágenes por libro (`libro_imagen`), en formato JPG, PNG o WebP. |
| RF-16 | El sistema debe permitir marcar como máximo una imagen por libro como portada. |
| RF-17 | El sistema debe permitir editar el texto alternativo (`alt_text`) y el orden de una imagen, y eliminarla. |
| RF-18 | El sistema debe permitir gestionar el stock y el precio de cada libro, rechazando valores negativos o inválidos. |
| RF-19 | El sistema debe restringir la administración (CRUD, gestión de usuarios) exclusivamente al usuario marcado como Administrador. |
| RF-20 | El sistema debe impedir la existencia de más de un usuario Administrador, tanto en la interfaz como a nivel de base de datos. |
| RF-21 | El sistema debe rechazar de forma controlada (sin exponer detalles internos) cualquier intento de un usuario no autorizado de acceder a funciones administrativas. |

## 3. Requisitos no funcionales

| ID | Requisito |
|----|-----------|
| RNF-01 | **Seguridad**: las contraseñas se almacenan con hash seguro (bcrypt); nunca en texto plano. |
| RNF-02 | **Seguridad**: todas las consultas a PostgreSQL se ejecutan de forma parametrizada mediante el driver `pg`; no se concatena SQL con datos de entrada del usuario. |
| RNF-03 | **Mantenibilidad**: el código se organiza en módulos con responsabilidad única (rutas, controladores, modelos, vistas, middleware), evitando lógica de negocio en `app.js` o en las vistas EJS. |
| RNF-04 | **Integridad de datos**: las reglas de negocio (ISBN único, un solo administrador, una sola portada por libro, stock/precio no negativos) se refuerzan en la base de datos mediante PK/UNIQUE/CHECK/índices, no solo en el frontend. |
| RNF-05 | **Rendimiento básico**: las búsquedas por título deben responder de forma aceptable sobre el catálogo de prueba (soportado por índice `gin`/`tsvector` en `libros.titulo`). |
| RNF-06 | **Usabilidad**: los formularios deben mostrar mensajes de error y confirmación claros ante operaciones CRUD. |
| RNF-07 | **Disponibilidad**: la aplicación Node.js corre en `127.0.0.1:3000` y se expone a la red mediante un reverse proxy (Apache/NGINX). |
| RNF-08 | **Trazabilidad de errores**: los errores se manejan de forma centralizada, registrando detalles técnicos en el servidor pero mostrando mensajes genéricos al usuario final. |
| RNF-09 | **Facilidad de despliegue**: la configuración sensible (credenciales, cadena de conexión) se maneja mediante variables de entorno (`.env`), nunca hardcodeada ni publicada. |

## 4. Supuestos

- El proyecto no requiere una tabla `categorias` independiente: el catálogo `generos` cubre esa
  función de clasificación temática del libro (decisión de diseño, documentada también en
  `ENGINEERING_DECISIONS.md`).
- Solo existe un rol "Usuario Registrado" además del Administrador; no hay roles intermedios
  (p. ej. editor, bibliotecario).
- Las imágenes se almacenan en el sistema de archivos del servidor (`uploads/`) y la base de
  datos guarda únicamente metadatos y la ruta/URL relativa.
- El catálogo de conceptos (`conceptos`) es reutilizable entre libros, pero la definición
  (`libro_concepto.definicion`) es siempre específica de la combinación libro-concepto.

## 5. Restricciones

- Arquitectura monolítica server-side (Node.js + Express + EJS); sin APIs REST/GraphQL/SOAP.
- Sin intercambio JSON/XML entre frontend y backend; los formularios HTML envían datos
  directamente al monolito.
- Acceso a PostgreSQL únicamente vía el driver `pg` con SQL parametrizado.
- Un único usuario Administrador, garantizado también a nivel de base de datos
  (`ux_usuarios_un_solo_admin`).

## 6. Criterios de aceptación (ejemplos representativos)

- **RF-02 / RF-19**: un usuario no administrador que intenta acceder a `/admin/*` recibe un
  código de acceso denegado (403) y no puede ejecutar la operación.
- **RF-20**: un intento de marcar a un segundo usuario como administrador (vía interfaz o vía
  SQL directo) es rechazado por la base de datos con un error de violación de índice único.
- **RF-15 / RF-16**: al subir una segunda imagen marcada como portada para el mismo libro, la
  primera deja de ser portada o la operación es rechazada según la regla implementada; nunca
  quedan dos portadas simultáneas para un mismo ISBN.
- **RF-18**: un intento de guardar un libro con `stock < 0` o `precio < 0` es rechazado tanto en
  la validación server-side como por el `CHECK` de la base de datos.
- **RF-14**: el mismo concepto (p. ej. "Serverless") puede registrarse en dos libros distintos
  con definiciones distintas, sin conflicto.

## 7. Actores, operaciones y riesgos

### 7.1 Actores y operaciones

| Actor | Puede hacer | No puede hacer |
|-------|-------------|-----------------|
| **Visitante** (no autenticado) | Acceder a `/login` y `/registro`; ver páginas públicas expresamente autorizadas. | Consultar catálogo, ver detalle de libros, acceder a cualquier ruta administrativa. |
| **Usuario Registrado** | Iniciar/cerrar sesión; consultar catálogo; buscar por ISBN/título; ver detalle de libro (autores, géneros, formato, imágenes, conceptos). | Crear/editar/eliminar libros, autores, géneros, formatos, conceptos, usuarios; acceder a rutas de administración. |
| **Administrador** (máximo uno) | Todo lo del Usuario Registrado, más: CRUD completo de libros, autores, géneros, formatos, conceptos; gestión de asociaciones libro-autor / libro-género / libro-concepto; carga/edición/eliminación de imágenes. | Crear un segundo Administrador (bloqueado por regla de negocio en BD). |

### 7.2 Riesgos identificados

| Riesgo | Descripción | Mitigación prevista |
|--------|-------------|----------------------|
| Acceso no autorizado | Un usuario regular intenta ejecutar operaciones administrativas directamente por URL. | Middleware de autorización por rol en cada ruta administrativa (RF-21). |
| SQL Injection | Entrada maliciosa en formularios (título, búsqueda, definición de concepto, etc.). | Consultas 100% parametrizadas con `pg` (RNF-02); nunca concatenación de strings. |
| Subida de archivos peligrosos | Un usuario intenta subir un archivo ejecutable disfrazado de imagen. | Validación de extensión/MIME/tamaño y renombrado del archivo por el sistema (RF-15). |
| Exposición de credenciales | Publicación accidental de `.env`, contraseñas o cadenas de conexión en el repositorio o en `ubiquitous.udem.edu`. | Variables de entorno, `.gitignore`, `.env.example` sin valores reales (RNF-09). |
| Eliminación accidental de información | Borrado de un autor/género/concepto referenciado por libros existentes. | `ON DELETE RESTRICT` en `libro_autor`, `libro_genero`, `libro_concepto`; `ON DELETE CASCADE` solo donde tiene sentido (imágenes de un libro eliminado). |
| Publicación de datos sensibles | Exposición de rutas internas del servidor, stack traces o hashes de contraseña al usuario final. | Manejo centralizado de errores con mensajes genéricos (RNF-08). |

---
*Documento generado como parte de la evidencia de la Parte 1 del ejercicio. Referencia cruzada: ver `ENGINEERING_DECISIONS.md` para la justificación de las decisiones arquitectónicas asociadas.*
