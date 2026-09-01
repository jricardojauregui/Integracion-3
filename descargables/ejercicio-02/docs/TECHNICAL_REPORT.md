# Reporte Técnico — Aplicación Web Monolítica para Gestión de una Librería

Universidad de Monterrey · Integración de Aplicaciones Computacionales · Ejercicio 02

---

## 1. Descripción del problema y alcance

Se construyó una aplicación web monolítica para administrar el catálogo de una librería en
línea: libros, autores, géneros, formatos, imágenes y conceptos/definiciones asociados al
contenido de cada libro. El sistema opera con acceso restringido a usuarios registrados y un
único Administrador, renderiza HTML del lado del servidor y accede a PostgreSQL directamente
mediante el driver `pg` con SQL parametrizado — sin APIs REST/GraphQL/SOAP ni intercambio
JSON/XML entre frontend y backend, conforme a las restricciones arquitectónicas del ejercicio.

## 2. Requisitos funcionales y no funcionales

Documentados en detalle en [`docs/REQUIREMENTS.md`](./REQUIREMENTS.md): 21 requisitos
funcionales (RF-01 a RF-21) cubriendo autenticación, CRUD de las 6 entidades, relaciones N:M
libro-autor/libro-género, conceptos por libro, gestión de imágenes con portada única, control
de stock/precio y la regla de administrador único; y 9 requisitos no funcionales (RNF-01 a
RNF-09) de seguridad, mantenibilidad, integridad, rendimiento, usabilidad, disponibilidad,
trazabilidad de errores y facilidad de despliegue. El mismo documento define los tres actores
del sistema (Visitante, Usuario Registrado, Administrador) y sus riesgos iniciales.

## 3. Macro-arquitectura y patrón de presentación

**Arquitectura:** monolito server-side (Node.js + Express + EJS), una sola unidad desplegable
que integra presentación, lógica de negocio y acceso a datos. El diagrama completo está en
[`docs/ARCHITECTURE_MONOLITHIC.png`](./ARCHITECTURE_MONOLITHIC.png).

**Patrón de presentación:** variante server-side de MVC, con separación de responsabilidades
por carpeta: `app.js` (inicialización y montaje de rutas), `config/` (conexión a PostgreSQL vía
`pg.Pool`), `routes/` (una por entidad, aplicando middlewares de autorización), `modules/*/controller.js`
y `modules/*/model.js` (lógica de negocio y acceso a datos separados), `middleware/` (auth y
upload), `views/` (plantillas EJS sin lógica de negocio ni SQL), `public/` (estáticos) y
`uploads/` (archivos cargados). Las tres decisiones arquitectónicas centrales (monolito, acceso
directo a PostgreSQL con `pg.Pool`, renderizado server-side con EJS) están justificadas con el
esquema *necesidad → alternativas → decisión → justificación → riesgo → evidencia* en
[`docs/ENGINEERING_DECISIONS.md`](./ENGINEERING_DECISIONS.md).

## 4. Organización del código y responsabilidades de los módulos

Seis módulos (`usuarios`, `libros`, `autores`, `generos`, `formatos`, `conceptos`), cada uno con
`controller.js` (orquesta la petición HTTP), `model.js` (única capa que toca PostgreSQL, 100%
consultas parametrizadas) y `routes.js` (define endpoints y aplica `isAuthenticated`/`isAdmin`
según corresponda). El módulo `libros` es el más complejo: usa un `client` de `pg.Pool` dedicado
con `BEGIN/COMMIT/ROLLBACK` explícitos para las operaciones que tocan varias tablas a la vez
(crear/editar libro junto con sus autores y géneros), garantizando atomicidad.

## 5. Modelo de datos y normalización hasta 4FN

El modelo completo, con el análisis de dependencias funcionales y multivaluadas, está en
[`docs/NORMALIZATION_4FN.xlsx`](./NORMALIZATION_4FN.xlsx) (progresión 0FN → 1FN → 2FN →
3FN/BCNF → 4FN) y el diagrama ER final en
[`docs/DB_DESIGN_ER_4FN.png`](./DB_DESIGN_ER_4FN.png). Resumen: `libros` (PK `isbn`) referencia
los catálogos independientes `formatos`, `generos`, `autores` y `conceptos`; las dependencias
multivaluadas independientes (`isbn ->> autor`, `isbn ->> genero`, `isbn ->> imagen`) se
resolvieron en tablas puente propias (`libro_autor`, `libro_genero`, `libro_imagen`) para evitar
productos cartesianos espurios; `libro_concepto` es una relación asociativa con atributo propio
(`definicion` depende de la clave compuesta `isbn + id_concepto`, no de cada parte por
separado), por lo que no se descompone más — ya está en 4FN tal como está. No existe una tabla
`categorias` separada: el catálogo `generos` cubre esa función (decisión documentada en
`REQUIREMENTS.md`, sección de supuestos).

## 6. Decisiones sobre integridad y restricciones en PostgreSQL

- **Máximo un Administrador:** índice único parcial `ux_usuarios_un_solo_admin`, reforzado con
  el trigger `trg_prevenir_segundo_admin` que da un mensaje de negocio claro en vez del error
  genérico de PostgreSQL.
- **Máximo una portada por libro:** índice único parcial `ux_libro_imagen_una_portada`,
  complementado por el trigger `trg_libro_imagen_una_portada` que desmarca automáticamente la
  portada anterior.
- **Validaciones de dominio:** `CHECK (stock >= 0)`, `CHECK (precio >= 0)`,
  `CHECK (anio_publicacion BETWEEN 1450 AND 2100)`, `CHECK (isbn ~ '^[0-9Xx-]{10,20}$')`.
- **Acciones referenciales:** `ON DELETE CASCADE` en las tablas puente y en `libro_imagen`
  (dependen completamente del libro); `ON DELETE RESTRICT` en las referencias a catálogos
  (`autores`, `generos`, `conceptos`) para impedir borrar un catálogo en uso.
- **Procedimientos almacenados, triggers y vistas:** ver `db/04_stored_procedures.sql`,
  `db/05_triggers.sql` y `db/06_views.sql` — encapsulan operaciones de negocio (crear libro con
  relaciones, ajustar stock de forma segura, marcar portada) y consultas reutilizables
  (catálogo completo, conceptos por libro, stock bajo).

## 7. Funcionalidades implementadas y flujo de datos

Flujo estándar: **Navegador → NGINX (reverse proxy) → Express (rutas → middleware de
autorización → controller) → model (SQL parametrizado vía `pg.Pool`) → PostgreSQL → vista EJS
renderizada → respuesta HTML.** Implementado y auditado: registro/login/logout con hash bcrypt,
autorización por rol en las 6 entidades, CRUD completo de libros/autores/géneros/formatos/
conceptos, asociación N:M de autores y géneros por libro, conceptos con definición específica
por combinación libro-concepto, carga de imágenes con extensión validada por el servidor y
gestión de portada única, y búsqueda por ISBN/título.

## 8. Seguridad

Detalle completo en [`docs/SECURITY_REVIEW.md`](./SECURITY_REVIEW.md) — 12 hallazgos con
amenaza, control aplicado y evidencia de prueba real. Puntos clave: contraseñas con bcrypt,
SQL 100% parametrizado (cero concatenación en los 6 modelos), autorización por rol en cada ruta
administrativa, sesiones con expiración de 8 horas e invalidación explícita en logout,
validación server-side de campos reforzada por `CHECK` en base de datos, mensajes de error
traducidos a lenguaje de negocio (`src/utils/dbErrors.js`) sin exponer detalles internos de
PostgreSQL, y una vulnerabilidad real de subida de archivos (extensión decidida por el cliente,
permitiendo disfrazar un `.php` de imagen) detectada y cerrada con evidencia reproducible
durante el desarrollo.

## 9. Estrategia de pruebas y resultados

Matriz completa de 23 casos en [`docs/TEST_PLAN.md`](./TEST_PLAN.md), cubriendo pruebas
funcionales, de autorización, negativas de integridad de base de datos, de seguridad, de
despliegue y de usabilidad — superando el mínimo de 15 exigido. Tres casos ya ejecutados con
evidencia real durante el desarrollo (login exitoso, rechazo de archivo malicioso disfrazado de
imagen, rechazo de creación de un segundo Administrador con mensaje de negocio correcto).

## 10. Despliegue mediante NGINX

Node.js corre exclusivamente en `127.0.0.1:3000` (nunca expuesto directamente); NGINX escucha
en el puerto 80 y publica la aplicación bajo `/library` mediante `proxy_pass`, con un bloque
adicional que reenvía también las rutas absolutas que la propia aplicación genera (redirecciones,
archivos estáticos, imágenes subidas) al mismo backend, evitando tener que reescribir la
aplicación para que conozca su prefijo de publicación. Configuración completa en
[`deploy/nginx-library.conf`](../deploy/nginx-library.conf). El firewall de GCP se ajustó para
exponer únicamente el puerto 80; la regla que exponía el puerto 3000 directamente a Internet fue
eliminada.

## 11. Limitaciones actuales, riesgos técnicos y posibles mejoras

- La contraseña de PostgreSQL se mantiene fija por requisito del entorno de práctica (riesgo
  residual aceptado, mitigado porque PostgreSQL solo escucha en `localhost`).
- El `mimetype` de los archivos subidos sigue siendo un dato reportado por el cliente; una
  mejora futura sería validar la firma binaria real del archivo (`file-type` o similar).
- El fallback de `SESSION_SECRET` hardcodeado en `app.js` debería eliminarse en un entorno de
  producción real, exigiendo la variable de entorno sin valor por defecto.
- No hay pruebas automatizadas (unitarias/integración); toda la validación actual es manual,
  documentada en `TEST_PLAN.md`. Una mejora natural sería introducir un framework de pruebas
  (Jest/Mocha) para las funciones de `model.js` y los procedimientos almacenados.
- El almacenamiento de imágenes es local al servidor (`uploads/`); no escala horizontalmente
  sin un almacenamiento compartido (ej. bucket de objetos) si el sistema creciera.

## 12. Qué cambiaría si el sistema evolucionara hacia componentes desacoplados

Si el catálogo, la autenticación o la gestión de imágenes necesitaran escalar o desplegarse de
forma independiente, los cambios principales serían: (1) reemplazar las vistas EJS por una API
REST/GraphQL que devuelva JSON, separando presentación de lógica de negocio; (2) introducir un
frontend independiente (SPA) que consuma esa API; (3) mover el estado de sesión de memoria/cookie
de servidor a un mecanismo compartido entre instancias (tokens JWT o un almacén de sesiones
centralizado como Redis), ya que el monolito actual asume un solo proceso; (4) separar el
almacenamiento de imágenes a un servicio de objetos accesible desde cualquier instancia; y
(5) evaluar si las relaciones N:M y la relación asociativa `libro_concepto` seguirían siendo
consultas SQL directas o si convendría encapsularlas detrás de un servicio de catálogo propio.
El costo de este cambio es la complejidad operativa adicional (orquestación, comunicación entre
servicios, consistencia eventual) que hoy no existe gracias a que todo vive en un solo proceso y
una sola base de datos.

---
*Documento generado como parte de la evidencia de la Parte 9 del ejercicio. Consolida y
referencia el resto de la documentación entregada en `docs/`.*
