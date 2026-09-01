# Registro de Decisiones de Ingeniería — Librería en Línea

Universidad de Monterrey · Integración de Aplicaciones Computacionales
Esquema de registro: **Necesidad/problema → alternativas consideradas → decisión tomada →
justificación técnica → riesgo o limitación → evidencia de validación**

---

## Decisión 1 — Arquitectura monolítica server-side

**Necesidad/problema**
Construir un sistema de gestión de librería con CRUD completo, autenticación y control de roles,
en un plazo de curso corto, con un solo desarrollador y sin infraestructura de orquestación
disponible.

**Alternativas consideradas**
1. Monolito server-side (Node.js + Express + EJS).
2. Frontend SPA (React/Vue) + API REST separada.
3. Arquitectura de microservicios (un servicio por dominio: usuarios, catálogo, imágenes).

**Decisión tomada**
Monolito server-side, tal como lo exige el enunciado del ejercicio: una sola unidad
desplegable donde presentación, lógica de negocio y acceso a datos conviven en el mismo
proceso Node.js.

**Justificación técnica**
- Una sola base de código y un solo despliegue reduce la complejidad operativa: no hay que
  coordinar versiones entre frontend y backend, ni gestionar red interna entre servicios.
- El renderizado server-side (EJS) evita duplicar lógica de validación en cliente y servidor,
  y elimina la necesidad de una capa de serialización JSON.
- Para el tamaño del equipo (una persona) y el alcance del ejercicio, el costo de coordinación
  de microservicios (descubrimiento de servicios, comunicación entre ellos, despliegues
  independientes) no se justifica frente al beneficio.

**Riesgo o limitación**
- Escalabilidad horizontal limitada: todo el sistema escala como una sola unidad; no se puede
  escalar solo el módulo de imágenes o solo el catálogo por separado.
- Un error en un módulo (p. ej. la carga de imágenes) puede afectar la disponibilidad de todo
  el proceso si no se maneja el error de forma aislada.
- El acoplamiento entre módulos aumenta con el tiempo si no se mantiene disciplina de
  organización por carpetas (routes/services/models).

**Condición futura que justificaría cambiar**
Si el número de usuarios concurrentes creciera significativamente, o si distintos equipos
necesitaran desplegar y escalar el catálogo y la gestión de usuarios de forma independiente,
tendría sentido migrar hacia una API REST desacoplada de un frontend SPA, y eventualmente
separar el módulo de imágenes (más intensivo en I/O) como servicio independiente.

**Evidencia de validación**
La aplicación corre como un único proceso Node.js (`node src/server.js`), sirviendo rutas,
vistas EJS y consultas a PostgreSQL desde el mismo código base — confirmado en ejecución
local (`http://localhost:3000`).

---

## Decisión 2 — Acceso directo a PostgreSQL con `pg.Pool` (sin ORM)

**Necesidad/problema**
El backend necesita ejecutar consultas SQL de forma segura y eficiente contra PostgreSQL,
manejando múltiples peticiones HTTP concurrentes sin agotar conexiones ni exponer el sistema
a inyección SQL.

**Alternativas consideradas**
1. `pg.Client`: una sola conexión persistente compartida.
2. `pg.Pool`: conjunto de conexiones reutilizables gestionadas automáticamente.
3. Un ORM (Sequelize, Prisma) sobre `pg`.

**Decisión tomada**
Acceso directo a PostgreSQL mediante el driver `pg`, usando `pg.Pool` para la gestión de
conexiones, con SQL parametrizado (`$1, $2, ...`) en cada consulta — sin ORM, tal como
restringe el ejercicio.

**Justificación técnica**
- `pg.Pool` reutiliza conexiones entre peticiones concurrentes en vez de abrir/cerrar una
  conexión por request (costoso) o compartir una sola conexión entre requests simultáneos
  (`pg.Client`, que no es seguro bajo concurrencia).
- El SQL parametrizado con `pg` neutraliza inyección SQL sin necesitar un ORM, cumpliendo el
  requisito RNF-02 con el mínimo de dependencias.
- Control total y explícito sobre cada consulta (relevante porque el modelo tiene relaciones
  N:M y una relación asociativa con atributo propio — `libro_concepto` — que un ORM genérico
  modelaría de forma menos directa).

**Riesgo o limitación**
- Más código repetitivo por consulta comparado con un ORM (no hay generación automática de
  queries CRUD).
- Responsabilidad manual de mantener consistentes las consultas si el esquema cambia (sin
  migraciones automáticas de un ORM).

**Condición futura que justificaría cambiar**
Si el número de entidades y relaciones creciera sustancialmente, o si un equipo más grande
necesitara consistencia automática entre modelo de datos y código, un ORM con migraciones
formales podría justificar su curva de aprendizaje adicional.

**Evidencia de validación**
`src/config/db.js` implementa `new Pool({...})` con las credenciales desde variables de
entorno (`.env`, no versionado); confirmado en ejecución (`npm start` conecta sin error).

---

## Decisión 3 — Renderizado server-side con EJS (sin API JSON)

**Necesidad/problema**
Presentar la interfaz de usuario (catálogo, formularios CRUD, detalle de libro) cumpliendo la
restricción del ejercicio de no usar JSON/XML como mecanismo de intercambio frontend-backend.

**Alternativas consideradas**
1. Vistas renderizadas en servidor con EJS, formularios HTML tradicionales (POST directo).
2. SPA con fetch/AJAX consumiendo una API JSON interna.

**Decisión tomada**
EJS como motor de plantillas, con formularios HTML que envían datos directamente a las rutas
Express del monolito (sin capa de API intermedia).

**Justificación técnica**
- Cumple directamente la restricción arquitectónica del ejercicio (no JSON/XML entre
  frontend/backend).
- Simplifica el flujo de datos: una petición HTTP = una respuesta HTML ya renderizada, sin
  necesidad de hidratar el DOM en el cliente ni mantener estado de aplicación en JavaScript.
- Reduce superficie de ataque en el cliente: no hay lógica de negocio expuesta en JavaScript
  del navegador.

**Riesgo o limitación**
- Experiencia de usuario menos fluida que una SPA (recarga completa de página en cada acción).
- Las vistas EJS pueden volverse difíciles de mantener si se les agrega lógica de negocio
  (mitigado manteniendo esa lógica en controllers/services, no en las plantillas).

**Condición futura que justificaría cambiar**
Si el proyecto evolucionara hacia una aplicación con interacciones ricas en tiempo real
(actualizaciones parciales sin recarga, notificaciones en vivo), convendría exponer una API
JSON y migrar la presentación a un framework de frontend.

**Evidencia de validación**
Las vistas en `views/*.ejs` (libros, autores, generos, formatos, conceptos, usuarios) reciben
datos ya consultados por los controladores y los renderizan en servidor; los formularios
(`formulario.ejs`, `nuevo.ejs`, `editar.ejs`) usan `method="POST"` estándar.

---

## Decisión 4 — Limpieza de historial de git tras exposición de credenciales

**Necesidad/problema**
Se detectó que `apps/web-monolith/.env` (con la contraseña real de PostgreSQL) fue
commiteado en los primeros commits del repositorio (`Primera vesión`, `Remove .env.example
from repository`) antes de que `.gitignore` lo excluyera. Aunque el archivo ya no aparece en
el working directory, seguía presente en el historial de git, accesible con
`git show <commit>:apps/web-monolith/.env`.

**Alternativas consideradas**
1. Dejarlo como está, confiando en que el repositorio es privado.
2. Solo eliminar el archivo del commit actual (`git rm --cached`) sin tocar el historial.
3. Reescribir el historial completo con `git filter-repo` para eliminar el archivo de todos
   los commits.

**Decisión tomada**
Reescritura del historial con `git filter-repo --path apps/web-monolith/.env --invert-paths`,
seguida de `git push --force` para sincronizar el remoto.

**Justificación técnica**
Un repositorio privado no es garantía suficiente: puede volverse público por error, puede ser
clonado por un colaborador, o puede ser indexado si cambia su visibilidad en el futuro.
Eliminar solo el archivo del commit actual (opción 2) no elimina el riesgo, ya que el
historial completo sigue siendo accesible vía `git log` o `git show`. `git filter-repo` es la
herramienta recomendada actualmente (sobre `filter-branch`, deprecado) para reescribir
historial de forma segura y eficiente.

**Riesgo o limitación**
- Reescribir el historial cambia los hashes de todos los commits afectados, lo cual habría
  roto cualquier clon existente de otros colaboradores (no aplica aquí, repo personal de un
  solo desarrollador).
- La contraseña específica usada en desarrollo (fija por requisito del entorno de práctica) ya
  estuvo expuesta en el remoto durante un tiempo; se documenta como **riesgo residual
  aceptado** dado que PostgreSQL solo escucha en `localhost` y no se expone directamente a
  Internet (el acceso público pasa por Node.js en `127.0.0.1:3000` detrás del reverse proxy).

**Condición futura que justificaría cambiar**
En un entorno real (no de práctica), esta contraseña debería rotarse inmediatamente al
detectar la exposición, independientemente de que el acceso a PostgreSQL esté restringido a
localhost.

**Evidencia de validación**
```
$ git log --all --oneline -- apps/web-monolith/.env
(sin salida — el archivo ya no existe en ningún commit del historial)
```
Confirmado tras `git push origin main --force`; el repositorio remoto en GitHub refleja el
historial reescrito.

---
*Documento generado como parte de la evidencia de la Parte 2 del ejercicio. Referencia
cruzada: ver `REQUIREMENTS.md` para los requisitos que motivan estas decisiones, y
`SECURITY_REVIEW.md` (pendiente, Parte 6) para el detalle completo de controles de
seguridad.*
