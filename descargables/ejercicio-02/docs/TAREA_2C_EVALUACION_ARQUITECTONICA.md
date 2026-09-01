# Tarea 2c — Evaluación Arquitectónica: Monolito Server-Side vs. Componentes Desacoplados vs. Microservicios

Universidad de Monterrey · Integración de Aplicaciones Computacionales · Trabajo en casa 2c

---

La arquitectura monolítica server-side elegida para este ejercicio —Node.js, Express y EJS
renderizando HTML del lado del servidor, con acceso directo a PostgreSQL desde el mismo
proceso— es adecuada para el escenario actual, pero esa adecuación depende directamente de las
condiciones específicas del proyecto: un solo desarrollador, un alcance funcional acotado (CRUD
sobre seis entidades relacionadas, autenticación simple, carga de imágenes) y un entorno de
práctica académica sin requisitos reales de escala. Evaluar si esta decisión sigue siendo
correcta requiere comparar, trade-off por trade-off, contra dos alternativas: una solución
desacoplada por componentes (API REST + frontend SPA) y una arquitectura de microservicios.

**Complejidad operativa.** El monolito actual tiene la complejidad operativa mínima posible: un
solo proceso que iniciar, un solo conjunto de dependencias (`npm install`), una sola base de
datos a la que apuntar. Una solución desacoplada introduce al menos dos procesos coordinados
(API y frontend), dos ciclos de build distintos, y la necesidad de definir un contrato de datos
(JSON) entre ambos. Microservicios multiplica esto: cada dominio (usuarios, catálogo, imágenes)
se convierte en su propio servicio con su propio ciclo de vida, requiriendo descubrimiento de
servicios, comunicación entre ellos (HTTP interno o mensajería) y manejo de fallos parciales
—qué pasa si el servicio de imágenes está caído pero el de catálogo no—. Para un equipo de una
persona, esta complejidad adicional no tiene contrapartida de beneficio real en este momento.

**Despliegue.** Publicar el monolito es un solo `git pull` + `npm install` + reinicio del
proceso Node detrás de un reverse proxy, como se hizo en la Parte 8 de este ejercicio. Una
solución desacoplada ya exige coordinar el despliegue de dos artefactos (API y build estático
del frontend), potencialmente en dominios o subrutas distintas. Microservicios exige
orquestación real —Docker Compose como mínimo, Kubernetes en un entorno productivo serio—,
además de versionado independiente de cada servicio y compatibilidad entre versiones cuando no
se despliegan simultáneamente.

**Escalabilidad.** Aquí es donde el monolito muestra su límite más real: solo puede escalarse
como unidad completa. Si en el futuro la carga de imágenes se volviera el cuello de botella
(por volumen de subida o de lectura), no hay forma de darle más recursos solo a esa
funcionalidad sin escalar también el resto de la aplicación. Una arquitectura de microservicios
resolvería esto exactamente: el servicio de imágenes podría escalar horizontalmente de forma
independiente. Sin embargo, para el volumen de datos y usuarios de este ejercicio (30 libros,
30 usuarios sintéticos), esta ventaja es completamente teórica — no hay carga real que
justifique el costo de construirla.

**Mantenibilidad.** El monolito, si se organiza con disciplina (como se hizo aquí: separación
clara en `routes/services/models`, sin lógica de negocio en las vistas), es perfectamente
mantenible a esta escala. El riesgo real de un monolito es que, sin esa disciplina, el
acoplamiento crece con el tiempo hasta volverse difícil de modificar sin romper otras partes.
Una arquitectura de microservicios fuerza el desacoplamiento por diseño —cada servicio tiene su
propia base de código—, pero a cambio introduce el problema inverso: lógica de negocio que
debería estar junta (por ejemplo, la relación libro-concepto con su definición propia)
terminaría dividida entre servicios, complicando el razonamiento sobre el sistema como un todo.

**Seguridad.** El monolito actual concentra la superficie de ataque en un solo proceso, lo cual
simplifica la auditoría (como se hizo en la Parte 5 y 6 de este ejercicio: fue posible revisar
los seis módulos y confirmar consistentemente que todo el SQL está parametrizado). Una
arquitectura desacoplada multiplica los puntos de entrada: cada servicio expuesto es una
superficie de ataque adicional, y la comunicación entre servicios necesita su propia capa de
autenticación (tokens internos, mTLS), trabajo que el monolito simplemente no necesita porque
todo vive en el mismo proceso de confianza.

**Tamaño del equipo.** Este es, en la práctica, el factor decisivo. Microservicios y sistemas
desacoplados existen para permitir que equipos grandes trabajen en paralelo sin bloquearse entre
sí, desplegando cada parte de forma independiente. Con un solo desarrollador, esa ventaja de
paralelismo organizacional no aplica — no hay nadie más con quien coordinar despliegues
simultáneos, así que el costo de la separación no tiene beneficio compensatorio.

**Conclusión.** El monolito server-side sigue siendo la decisión correcta para el alcance y
equipo actuales de este proyecto. La condición que justificaría migrar no es un umbral técnico
abstracto, sino un cambio concreto en el contexto: crecimiento real del equipo a varias personas
trabajando en paralelo, o una necesidad de escalar un componente específico (probablemente
imágenes) de forma independiente del resto. Hasta que eso ocurra, introducir la complejidad de
componentes desacoplados o microservicios sería sobre-ingeniería — resolver un problema de
escala que el proyecto todavía no tiene.

---
*Palabras aproximadas: 640. Documento generado para la Tarea 2c de trabajo en casa. Expande el
análisis de la sección 12 de `docs/TECHNICAL_REPORT.md`.*
