# Tarea 4 — Diseño de arquitectura Cloud asistido por IA
## Aplicación de banca móvil sobre nube híbrida

**Alumno:** José Ricardo Jáuregui
**Matrícula:** 608995
**Universidad de Monterrey (UDEM)**

---

## 1. Descripción del problema

Una institución financiera requiere una nueva aplicación de banca móvil. El sistema debe permitir a los clientes consultar saldos, realizar transferencias, recibir notificaciones y depositar cheques desde el teléfono, con la restricción de que **el core bancario (el libro mayor, la fuente de verdad de los saldos) no puede migrarse a la nube**: es un sistema legado, crítico y sujeto a requisitos regulatorios de custodia.

Esto obliga a una **arquitectura de nube híbrida**: el frente de cara al cliente vive en la nube pública (donde se necesita elasticidad, despliegue rápido y alcance global), mientras que el núcleo transaccional y los elementos regulados permanecen on-premises. El reto central no es construir cada pieza por separado, sino diseñar la frontera entre ambos mundos de forma que un problema en el datacenter no derribe la aplicación móvil, y que el dinero nunca se pierda ni se duplique en el tránsito entre ambos.

El sistema debe cubrir: aplicación móvil, backend y APIs, autenticación, base de datos y almacenamiento, notificaciones, funciones serverless, alta disponibilidad y escalabilidad, seguridad y monitoreo, integración con la infraestructura existente y la estrategia híbrida en conjunto.

---

## 2. Herramienta de IA utilizada

| Aspecto | Detalle |
|---|---|
| **Entorno** | Visual Studio Code |
| **Asistente de IA** | Claude (Anthropic), usado como agente de programación y diseño |
| **Modo de trabajo** | Conversacional iterativo: prompt inicial + 6 prompts de refinamiento |
| **Verificación** | Ejecución real del código generado, suite de 43 pruebas automatizadas y scripts de demostración de vulnerabilidades |
| **Lenguaje del prototipo** | Python 3.12 con FastAPI |

**Nota metodológica importante:** el criterio que seguí fue no aceptar ninguna afirmación de la IA sin poder ejecutarla. Cada vulnerabilidad que la IA identificó la reproduje en código, y cada corrección la verifiqué con una prueba automatizada. Las secciones 7 y 8 documentan resultados de ejecución real, no descripciones teóricas.

---

## 3. Prompt inicial

```
Actúa como arquitecto de soluciones Cloud. Diseña una arquitectura para una
aplicación de banca móvil utilizando una estrategia de nube híbrida. La solución
deberá incluir aplicación móvil, API Gateway, servicios backend, autenticación,
bases de datos, almacenamiento, funciones serverless/FaaS, monitoreo y mecanismos
de seguridad. Identifica qué componentes deberían permanecer on-premises y cuáles
deberían ejecutarse en la nube, justificando cada decisión. Propón una arquitectura
escalable, tolerante a fallos y altamente disponible. Genera un diagrama de
arquitectura y desarrolla un prototipo básico del backend. Explica cada componente
y las decisiones arquitectónicas realizadas.
```

### 3.1 Primera arquitectura obtenida (v1)

Ver `diagramas/arquitectura_v1.svg`. La respuesta inicial propuso:

```
App móvil → API Gateway → Backend monolítico → Base de datos
                ↓              ↓                    ↓
            Auth (JWT)    Lambda (notif.)         S3
                                                    ↓
                                          Core bancario (VPN)
```

**Componentes propuestos:** app móvil nativa, API Gateway, backend en contenedores, autenticación con JWT, base de datos relacional gestionada, S3 para documentos, Lambda para notificaciones, CloudWatch para monitoreo, VPN hacia el core on-premises.

**Prototipo de backend generado:** `backend_v1/main.py` (conservado sin corregir como evidencia).

**Evaluación inicial:** la propuesta era *plausible* y cubría nominalmente todos los puntos solicitados. Ese es precisamente su peligro: identifica las cajas correctas, pero no las relaciones críticas entre ellas. Un revisor sin experiencia la aprobaría. Lo que faltaba era todo lo que separa un diagrama de una arquitectura operable:

| Categoría | Omisión |
|---|---|
| Disponibilidad | Sin multi-AZ; base de datos y backend son puntos únicos de falla |
| Continuidad | Sin plan de DR, sin RTO/RPO definidos |
| Frontera híbrida | Llamada síncrona sin timeout al core: acoplamiento total |
| Consistencia | Sin idempotencia ni manejo de transacciones distribuidas |
| Seguridad | Sin WAF, sin MFA, sin rate limiting, sin tokenización de PAN |
| Observabilidad | Sin trazas distribuidas ni correlación entre entornos |
| Costos | Sin análisis; sin considerar el costo de egreso de datos |
| Cumplimiento | Sin mención de PCI-DSS ni de regulación bancaria local |

---

## 4. Prompts de mejora e iteraciones

Se ejecutaron **seis iteraciones**. Cada una se documenta con el prompt exacto, los hallazgos y el cambio concreto que produjo en la arquitectura.

---

### Iteración 1 — Análisis de vulnerabilidades

> **Prompt:** *Actúa ahora como pentester y auditor de seguridad especializado en banca. Revisa el prototipo de backend y la arquitectura línea por línea. Enumera cada vulnerabilidad concreta indicando: el vector de ataque, el impacto en un contexto financiero regulado y la corrección específica. No des recomendaciones genéricas: señala la línea de código o el componente exacto. Considera OWASP Top 10, OWASP API Security Top 10 y los requisitos de PCI-DSS.*

**Hallazgos (15 fallas, catalogadas F-1 a F-15):**

| ID | Vulnerabilidad | Impacto en banca |
|---|---|---|
| F-1 | Secreto JWT embebido en el código | Cualquiera con acceso al repositorio falsifica tokens de cualquier cliente |
| F-2 | Tokens sin expiración ni revocación | Un token robado da acceso permanente; imposible cerrar sesión de verdad |
| F-3 | Contraseñas comparadas en texto plano | Una fuga de la base de datos expone credenciales reutilizables |
| F-4 | Montos en `float` | Descuadre contable acumulativo; hallazgo grave en auditoría |
| F-9 | Sin validación de monto | Un monto negativo invierte la transferencia: **robo directo** |
| F-10 | Sin autorización por recurso (IDOR) | Cualquier usuario autenticado lee y mueve cuentas ajenas |
| F-11 | Sin rate limiting | Fuerza bruta ilimitada sobre credenciales |
| F-12 | PAN y tokens en los logs | Incidente de cumplimiento PCI-DSS por sí solo |
| F-14 | CORS abierto con credenciales | Cualquier sitio hace peticiones autenticadas en nombre del usuario |

**Cambio en la arquitectura:** se incorporaron WAF con reglas OWASP, gestor de secretos con rotación automática, MFA obligatorio, tokenización de PAN (bóveda de tokens), y política de redacción de datos sensibles en logs.

---

### Iteración 2 — Puntos únicos de falla y tolerancia a fallos

> **Prompt:** *Identifica todos los puntos únicos de falla de esta arquitectura. Para cada uno indica qué ocurre exactamente cuando falla, qué porcentaje de usuarios se ve afectado y cómo eliminarlo. Presta atención especial al enlace híbrido con el core on-premises: ¿qué pasa con la aplicación móvil si el datacenter queda incomunicado 30 minutos? Analiza también fallos parciales y en cascada, no solo caídas totales.*

**Hallazgo principal (F-8), el más grave de arquitectura:** el backend llamaba al core on-premises de forma síncrona, sin timeout. En una nube híbrida el enlace al datacenter es el componente más lento y menos elástico del sistema. Si el core se degrada, cada petición se queda esperando, el pool de workers se agota y **toda la API cae, incluidas operaciones que ni siquiera necesitan el core**, como consultar el saldo en caché. Un problema localizado en un sistema se convierte en una caída total.

**Segundo hallazgo:** la operación de transferencia movía el saldo en la nube y *después* avisaba al core. Si el core fallaba, el dinero quedaba movido de un lado y no del otro, sin registro ni forma de detectarlo.

**Cambios en la arquitectura:**

| Antes | Después |
|---|---|
| Backend en una AZ | Multi-AZ activo-activo con autoescalado horizontal |
| BD instancia única | Multi-AZ con failover automático + réplicas de lectura |
| Llamada directa al core | Timeout 2 s + 3 reintentos con backoff exponencial y *jitter* + **circuit breaker** |
| Acoplamiento síncrono | Bus de eventos (Kafka/EventBridge) + colas con DLQ |
| Falla total si cae el core | **Degradación elegante**: modo solo lectura con saldos de caché |
| Sin registro de operaciones a medias | Patrón *saga*: movimiento persistido como PENDIENTE + job de reconciliación |

El *jitter* merece una nota: sin aleatoriedad en el reintento, todas las instancias reintentan al mismo tiempo y vuelven a tumbar el core justo cuando se estaba recuperando (*thundering herd*).

---

### Iteración 3 — Escalabilidad y justificación de servicios

> **Prompt:** *Dimensiona la arquitectura para 2 millones de usuarios activos, con picos de 15.000 peticiones por segundo en quincena y día de pago. Identifica qué componente satura primero y por qué. Para cada servicio propuesto, justifica por qué ese y no una alternativa: compara contenedores contra serverless para cada carga de trabajo, y SQL contra NoSQL para cada tipo de dato. Sé explícito sobre los contras de cada elección.*

**Hallazgo:** el cuello de botella no es el backend en la nube (que escala horizontalmente) sino **el core on-premises**, cuya capacidad es fija y no elástica. Escalar la nube sin proteger al core solo hace que le llegue la avalancha más rápido.

**Cambios:** amortiguamiento mediante colas para operaciones que toleran asincronía, caché distribuida (Redis) para consultas de saldo, patrón *bulkhead* (aislamiento de pools de conexión para que un servicio saturado no consuma las conexiones de los demás), y limitación de concurrencia hacia el core.

**Justificación de elecciones clave:**

| Carga de trabajo | Elección | Por qué no la alternativa |
|---|---|---|
| API transaccional | Contenedores (EKS/AKS) | Serverless: el *cold start* es inaceptable en el camino crítico y el control de conexiones a BD es peor |
| Notificaciones, OCR, reportes | Serverless (FaaS) | Contenedores: son cargas esporádicas; pagar por instancias ociosas no se justifica |
| Saldos y movimientos | PostgreSQL | NoSQL: se necesitan transacciones ACID y restricciones de integridad referencial |
| Sesiones, feature flags | NoSQL / Redis | SQL: acceso por clave a altísimo volumen, sin necesidad de *joins* |
| Bitácora de auditoría | Almacén *append-only* | BD relacional: se requiere inmutabilidad demostrable |

---

### Iteración 4 — Observabilidad

> **Prompt:** *Incorpora observabilidad de nivel producción. No basta con "usar CloudWatch": define qué métricas específicas, qué SLIs y SLOs, qué alertas y sobre qué umbrales. ¿Cómo se rastrea una transferencia individual que atraviesa la app móvil, el API Gateway, el backend en la nube y el core on-premises? ¿Qué se registra y qué NO debe registrarse nunca por cumplimiento?*

**Hallazgo (F-13):** era imposible seguir una transacción de punta a punta. Ante el reclamo de un cliente por un cargo, habría que correlacionar a mano los registros de cuatro sistemas con relojes distintos. Además (F-12), los logs contenían PAN y tokens completos.

**Cambios:** OpenTelemetry con propagación de contexto entre entornos, **correlation-ID obligatorio** en toda la cadena, logs estructurados en JSON con redacción centralizada de campos sensibles, métricas de las cuatro señales doradas (latencia, tráfico, errores, saturación), y alertas definidas sobre **SLOs orientados al usuario**, no sobre umbrales de CPU.

La distinción importa: al cliente no le importa la CPU del servidor, le importa si su transferencia se completa. Se definieron SLOs como "99,5 % de las transferencias se confirman en menos de 3 segundos" y se alerta sobre el consumo del presupuesto de error, no sobre métricas de infraestructura que pueden estar mal sin que nadie lo note y bien mientras el usuario sufre.

---

### Iteración 5 — Costos y recuperación ante desastres

> **Prompt:** *Analiza el modelo de costos e identifica las tres partidas que más crecerán con el volumen. ¿Qué decisión arquitectónica actual generará una factura inesperada? Después diseña la estrategia de recuperación ante desastres: define RTO y RPO justificados para banca, qué se replica, con qué frecuencia, cómo se prueba el failover y cómo se recupera un core on-premises destruido.*

**Hallazgo de costos:** la transferencia de datos de salida (*egress*) desde la nube hacia el datacenter es una partida que suele subestimarse y que en una arquitectura híbrida con tráfico constante puede superar el costo de cómputo. También se detectó que replicar todo el histórico a la nube tendría un costo desproporcionado frente a su frecuencia de consulta.

**Cambios:** enlace dedicado (Direct Connect/ExpressRoute) que reduce el costo por GB frente a salida por internet, política de retención por niveles con archivado automático, etiquetado por centro de costo con alertas de desviación presupuestal, y la decisión de mantener el *data warehouse* histórico on-premises.

**Estrategia de DR definida:**

| Parámetro | Valor | Justificación |
|---|---|---|
| **RTO** | ≤ 30 min | Tolerancia máxima antes de daño reputacional y reportable al regulador |
| **RPO** | ≤ 5 min | Ninguna transacción confirmada puede perderse; 5 min es el límite de reproceso desde bitácora |
| Estrategia | *Warm standby* en segunda región | *Pilot light* no cumple el RTO; activo-activo multiplica el costo sin necesidad |
| Pruebas | *Game days* trimestrales con failover real | Un DR no probado es una hipótesis, no un plan |

---

### Iteración 6 — Revisión de código y generación de pruebas

> **Prompt:** *Revisa el prototipo de backend buscando errores de correctitud, no de estilo: condiciones de carrera, problemas de concurrencia, manejo de dinero, atomicidad de transacciones e idempotencia. Para cada problema, escribe una prueba automatizada que lo demuestre fallando antes de la corrección. Genera después la versión corregida y la suite completa de pruebas.*

Esta fue la iteración más productiva, porque produjo **evidencia ejecutable** en lugar de afirmaciones.

**Hallazgos de correctitud:**

- **F-5 (atomicidad):** la resta y la suma de saldos no eran atómicas. Si el proceso moría entre ambas líneas, el dinero se destruía.
- **F-6 (idempotencia):** sin clave de idempotencia, un reintento del cliente duplicaba la transferencia. Con red móvil, un reintento tras un *timeout* no es un caso raro: es lo normal.
- **F-7 (concurrencia):** clásico *lost update*. Varias peticiones simultáneas leían el mismo saldo antes de que ninguna lo escribiera, todas veían fondos suficientes y la cuenta terminaba en negativo.

**Cambios:** montos en `Decimal` y almacenamiento en centavos enteros, bloqueo por cuenta con **orden alfabético de adquisición** (para evitar interbloqueo en transferencias cruzadas A→B y B→A simultáneas), clave de idempotencia obligatoria por cabecera HTTP, y máquina de estados del movimiento (PENDIENTE → APLICADO / REVERSADO / FALLIDO).

---

## 5. Arquitectura final

Ver `diagramas/arquitectura_final.svg`.

### 5.1 Flujo principal

```
Usuario → App móvil → CDN/WAF → API Gateway → Microservicios → Datos
                                      ↓              ↓
                                  Identidad     Serverless / Colas
                                                     ↓
                                        [ENLACE PRIVADO CIFRADO]
                                                     ↓
                                        Core bancario on-premises
```

### 5.2 Qué va en la nube y qué permanece on-premises

| Componente | Ubicación | Justificación |
|---|---|---|
| App móvil, CDN, WAF | **Nube** | Necesita alcance global, elasticidad y despliegue rápido |
| API Gateway, microservicios | **Nube** | Carga muy variable (picos de quincena); autoescalado es esencial |
| Identidad (IdP) | **Nube**, federado con AD | Escala con los clientes; se federa para no duplicar identidades de empleados |
| BD transaccional operativa | **Nube** | Alto volumen de lectura; servicios gestionados dan multi-AZ y PITR |
| Almacén de objetos | **Nube** | Costo por GB muy inferior; durabilidad de 11 nueves |
| Funciones serverless | **Nube** | Cargas esporádicas; escala a cero elimina costo ocioso |
| **Core bancario** | **On-premises** | Sistema legado; el riesgo y costo de migrarlo supera el beneficio |
| **HSM / llaves criptográficas** | **On-premises** | Exigencia regulatoria de custodia física (FIPS 140-2 Nivel 3) |
| **Conexión SPEI / cámara** | **On-premises** | Conectividad dedicada obligatoria por normativa |
| Directorio corporativo (AD) | **On-premises** | Identidad de empleados ya establecida; se federa, no se migra |
| *Data warehouse* histórico | **On-premises** | Retención legal prolongada; costo de egreso desproporcionado |

### 5.3 Comparativa v1 → final

| Dimensión | v1 | Final |
|---|---|---|
| Disponibilidad | Una AZ, sin redundancia | Multi-AZ activo-activo + DR en segunda región |
| Enlace híbrido | VPN, llamada síncrona sin timeout | Enlace dedicado + VPN de respaldo, con circuit breaker |
| Si el core cae | Caída total de la aplicación | Degradación elegante a modo solo lectura |
| Consistencia | Ninguna garantía | Saga con estados + idempotencia + reconciliación |
| Manejo de dinero | `float` | `Decimal` sobre centavos enteros |
| Autenticación | JWT eterno, secreto en código | OAuth2/OIDC + MFA, tokens cortos revocables, secretos en KMS |
| Datos de tarjeta | PAN en claro y en logs | Tokenización; la nube nunca almacena el PAN real |
| Observabilidad | Logs básicos | OpenTelemetry, correlation-ID, SLOs, SIEM |
| DR | No contemplado | RTO ≤ 30 min, RPO ≤ 5 min, pruebas trimestrales |

---

## 6. Código: prototipo generado y mejorado

### 6.1 Qué hace y cómo funciona

El prototipo (`backend_v2/`) implementa el núcleo transaccional: autenticación, consulta de cuentas y transferencias con integración simulada al core on-premises.

```
backend_v1/main.py          Primera versión SIN corregir (evidencia)
backend_v2/
├── app/
│   ├── config.py           Configuración; falla rápido si falta un secreto
│   ├── domain.py           Dinero con Decimal, entidades, errores de negocio
│   ├── security.py         Hashing, JWT con exp/jti, rate limiting
│   ├── core_client.py      Adaptador al core: timeout, reintentos, circuit breaker
│   ├── ledger.py           Atomicidad, concurrencia, idempotencia, saga
│   ├── observability.py    Logs JSON, correlation-ID, métricas, redacción de PII
│   └── main.py             API FastAPI: endpoints, middleware, health checks
├── tests/test_backend.py   43 pruebas ligadas a cada falla [F-n]
└── demo_vulnerabilidades.py  Demostración ejecutable v1 vs v2
```

**El flujo de una transferencia**, que concentra las decisiones importantes:

1. Se exige la cabecera `Idempotency-Key`. Si esa clave ya se usó, se devuelve **el mismo resultado** sin volver a cobrar.
2. Se valida la propiedad de la cuenta origen en la **capa de datos**, no solo en el *endpoint*: aunque un desarrollador agregue después un *endpoint* nuevo y olvide revisarlo, la comprobación sigue ahí.
3. Se adquieren los bloqueos de ambas cuentas **en orden alfabético**. Ordenar los recursos es la forma estándar de evitar interbloqueo entre transferencias cruzadas.
4. Dentro del bloqueo se re-verifica el saldo (*check-then-act*), se registra el movimiento como PENDIENTE y se mueven ambos saldos.
5. **Fuera del bloqueo** se confirma contra el core. Se sale del bloqueo a propósito: mantener la cuenta bloqueada durante una llamada de red serializaría las operaciones y destruiría el rendimiento.
6. Si el core no responde, el movimiento **queda PENDIENTE y persistido**, no se pierde. Un proceso de reconciliación lo confirma después.

### 6.2 Por qué fue diseñado así

**Inyección de dependencias en el adaptador del core.** El cliente del core se recibe como parámetro, no se instancia dentro. Esto permite inyectar un doble de prueba que simula latencia, fallos intermitentes y caídas totales — que es exactamente lo que hay que reproducir para verificar que el circuit breaker funciona. Sin esa decisión, probar la resiliencia requeriría un core real fallando a demanda.

**Fallar rápido en la configuración.** La aplicación se niega a arrancar si falta un secreto en producción. Es preferible que el despliegue falle de inmediato y visiblemente a que arranque con un valor por defecto inseguro que nadie note durante meses.

**Errores de negocio como tipos propios.** Permiten traducir a HTTP sin filtrar detalles internos, y devolver códigos estables que la app móvil interpreta sin analizar textos.

### 6.3 Qué modificaría para producción

| Aspecto | Prototipo | Producción |
|---|---|---|
| Persistencia | Diccionarios en memoria | PostgreSQL con `SELECT ... FOR UPDATE` y `UNIQUE` sobre idempotencia |
| Rate limiting | Contador en memoria | Redis (límite global entre instancias) + refuerzo en el WAF |
| Revocación de tokens | `set` en memoria | Redis con TTL igual a la expiración del token |
| Hashing | PBKDF2 (biblioteca estándar) | Argon2id con parámetros calibrados |
| Cliente del core | Simulado | Cliente real con mTLS y *pool* de conexiones acotado |
| Secretos | Variables de entorno | Inyección desde Vault/Secrets Manager vía CSI driver |
| Reconciliación | Endpoint manual | Función serverless por calendario, con rol de ejecución propio |
| Autorización | Verificación de propiedad | Motor de políticas (OPA) con reglas auditables |

---

## 7. Errores detectados

### 7.1 Verificación ejecutable

No me limité a aceptar que las vulnerabilidades existían: las reproduje. Salida real de `demo_vulnerabilidades.py`:

**Condición de carrera** — 30 transferencias simultáneas de $100 desde una cuenta con $1.000 (solo caben 10):

```
v1  exitosas=30  rechazadas= 0
    saldo final MX001 = $-2,000.00   <-- NEGATIVO
v2  exitosas=10  rechazadas=20
    saldo final MX001 = $0.00        <-- CORRECTO
```

La versión inicial permitió un sobregiro de **$2.000 en una cuenta que tenía $1.000**. Este es el tipo de fallo que no aparece en pruebas manuales (donde las peticiones llegan de una en una) y sí aparece el primer día de quincena con carga real.

**Precisión monetaria** — 1.000 sumas de $0,10:

```
v1 (float)   = 99.9999999999986
v2 (Decimal) = 100.00
```

**Idempotencia** — el usuario reintenta tras perder señal:

```
Intento 1: movimiento=c999594d  saldo=$500.00
Intento 2: movimiento=c999594d  saldo=$500.00
Intento 3: movimiento=c999594d  saldo=$500.00
-> 3 envíos, 1 solo cargo. En v1 habrían sido 3 cargos.
```

### 7.2 Catálogo completo

| ID | Falla | Categoría | Corrección |
|---|---|---|---|
| F-1 | Secreto en el código | Seguridad | Variables de entorno + KMS; arranque falla si falta |
| F-2 | Token sin expiración ni revocación | Seguridad | `exp` de 10 min, `jti`, `aud`/`iss`, lista de revocación |
| F-3 | Contraseñas en texto plano | Seguridad | PBKDF2 con sal + comparación en tiempo constante |
| F-4 | Dinero en `float` | Correctitud | `Decimal` y centavos enteros |
| F-5 | Transferencia no atómica | Correctitud | Ambos saldos bajo el mismo bloqueo + estado persistido |
| F-6 | Sin idempotencia | Correctitud | Cabecera `Idempotency-Key` obligatoria |
| F-7 | Condición de carrera | Correctitud | Bloqueo por cuenta en orden alfabético |
| F-8 | Llamada al core sin timeout | Arquitectura | Timeout + reintentos con jitter + circuit breaker |
| F-9 | Monto sin validar | Seguridad | Rechazo de negativos, cero, NaN, exceso de decimales |
| F-10 | IDOR | Seguridad | Autorización verificada en la capa de datos |
| F-11 | Sin rate limiting | Seguridad | Ventana deslizante por IP y por usuario + 429 |
| F-12 | PII en logs | Cumplimiento | Redacción centralizada por lista de denegación |
| F-13 | Sin trazabilidad | Operación | Correlation-ID propagado extremo a extremo |
| F-14 | CORS abierto | Seguridad | Lista explícita de orígenes, métodos y cabeceras |
| F-15 | Estado en memoria | Escalabilidad | Externalización a Redis/BD (documentado) |

### 7.3 Un error detectado por las propias pruebas

Al ejecutar la suite por primera vez, una prueba falló con `429 Too Many Requests`. La causa no estaba en el código de producción: las pruebas de *rate limiting* agotaban el contador por IP y, como el cliente de pruebas usa siempre la misma IP, contaminaban las pruebas posteriores.

Lo incluyo porque ilustra algo que la IA no advirtió por sí sola: **el estado global acopla pruebas que deberían ser independientes**. Se corrigió con un *fixture* que aísla el estado entre pruebas. Es el mismo principio que en producción justifica mover ese contador a Redis.

---

## 8. Mejoras realizadas

| # | Mejora | Iteración |
|---|---|---|
| 1 | Multi-AZ activo-activo con autoescalado | 2 |
| 2 | Circuit breaker + timeout + reintentos con jitter hacia el core | 2 |
| 3 | Degradación elegante a modo solo lectura | 2 |
| 4 | Patrón saga con estados y reconciliación | 2, 6 |
| 5 | Bus de eventos y colas para desacoplar del core | 2 |
| 6 | Caché distribuida y patrón bulkhead | 3 |
| 7 | Justificación explícita de cada servicio frente a su alternativa | 3 |
| 8 | OpenTelemetry con correlation-ID entre entornos | 4 |
| 9 | SLIs/SLOs y alertas por síntoma, no por umbral de infraestructura | 4 |
| 10 | Redacción automática de datos sensibles en logs | 4 |
| 11 | Enlace dedicado y política de retención por niveles | 5 |
| 12 | Estrategia de DR con RTO/RPO y game days trimestrales | 5 |
| 13 | `Decimal` sobre centavos enteros | 6 |
| 14 | Idempotencia obligatoria | 6 |
| 15 | Bloqueo ordenado anti-interbloqueo | 6 |
| 16 | Autorización en la capa de datos (anti-IDOR) | 1, 6 |
| 17 | MFA, WAF, tokenización de PAN | 1 |
| 18 | Suite de 43 pruebas ligadas a cada falla | 6 |

**Resultado de la suite:**

```
$ python -m pytest tests/ -q
43 passed in 4.21s
```

---

## 9. Screenshots

*(Insertar capturas)*

1. **Prompt inicial y primera respuesta** — la arquitectura v1 propuesta.
2. **Diagrama de arquitectura final** — `diagramas/arquitectura_final.svg`.
3. **Suite de pruebas** — `python -m pytest tests/ -v` con los 43 casos.
4. **Demostración de vulnerabilidades** — salida de `demo_vulnerabilidades.py` mostrando el saldo negativo en v1.
5. **API en ejecución** — documentación interactiva en `http://localhost:8000/docs`.
6. **Circuit breaker en acción** — respuesta de `/health/ready` reportando el circuito abierto.

---

## 10. Reflexión individual

**Prompt engineering.** El cambio más notable no fue la cantidad de información obtenida, sino su naturaleza. El prompt inicial produjo un inventario de componentes: una lista de cajas correctas. Los prompts de refinamiento produjeron *relaciones y modos de falla*, que es donde vive la arquitectura real. La diferencia estuvo en el rol que asigné: pedir "diseña una arquitectura seguraˮ genera recomendaciones genéricas; pedir "actúa como pentester y señala la línea exacta, el vector de ataque y el impacto en un contexto reguladoˮ genera hallazgos accionables. Igualmente decisivo fue exigir escenarios concretos: preguntar "¿qué pasa si el datacenter queda incomunicado 30 minutos?ˮ reveló el acoplamiento síncrono con el core, que ninguna pregunta abierta sobre disponibilidad había sacado a la luz.

**La primera propuesta.** No era adecuada, pero —y esto es lo preocupante— era *plausible*. Cubría nominalmente los diez puntos solicitados y un revisor sin experiencia la habría aprobado. Le faltaba justamente lo que distingue un diagrama de un sistema operable: redundancia, plan de continuidad, protección de la frontera híbrida y garantías de consistencia. La IA identificó correctamente **qué** componentes se necesitan; no anticipó **cómo fallan juntos**.

**Errores y decisiones cuestionables.** Detecté quince fallas. Las de seguridad clásica (secreto embebido, CORS abierto) son las que la IA corrige de inmediato al preguntarle. Las verdaderamente peligrosas fueron las de correctitud: la condición de carrera permitía un sobregiro de $2.000 sobre una cuenta de $1.000, y no se manifiesta en pruebas manuales, solo bajo concurrencia real. Reproducirla ejecutando el código fue lo que convirtió una advertencia teórica en evidencia.

**Contexto financiero.** La IA no lo incorporó por defecto. Aplicó buenas prácticas generales de desarrollo web, pero omitió lo específico del dominio: tokenización de PAN, alcance de PCI-DSS, requisitos de custodia de llaves, inmutabilidad de la bitácora de auditoría y el uso de `float` para dinero —que en cualquier otro dominio sería tolerable y aquí produce descuadres contables auditables. El contexto regulado hubo que introducirlo explícitamente en los prompts.

**Comprensión del código.** Sí, y lo verifiqué del único modo que considero válido: ejecutándolo. Escribí pruebas que fallan sin la corrección y pasan con ella. El punto que más me exigió razonar fue el orden de adquisición de bloqueos: entender por qué dos transferencias cruzadas simultáneas pueden quedar en interbloqueo si cada una toma los bloqueos en orden distinto, y por qué ordenarlos alfabéticamente lo resuelve, no es algo que se pueda aceptar por confianza en el generador.

**Validación.** Por tres vías: contrastar las recomendaciones con documentación oficial de los proveedores, ejecutar el código y medir su comportamiento bajo concurrencia, y razonar sobre los modos de falla planteando escenarios ("si el core cae ahora, ¿dónde queda el dineroˮ). La tercera es la que más omisiones destapó.

**Rol del ITC.** Para validar una arquitectura generada por IA hace falta poder responder preguntas que la IA no formula: dónde está el punto único de falla, qué ocurre entre dos líneas de código si el proceso muere, cuánto cuesta el egreso de datos, qué exige el regulador. Eso requiere bases sólidas en sistemas distribuidos, concurrencia, redes, seguridad y modelado de datos. La IA acelera enormemente la generación; no sustituye el criterio para evaluarla.

**IA frente a ingeniero.** Es razonable delegar la generación de código repetitivo, la enumeración de vulnerabilidades conocidas, la redacción de pruebas y la exploración de alternativas. Deben permanecer bajo responsabilidad humana las decisiones con consecuencias irreversibles: qué datos salen del perímetro regulado, qué RTO/RPO se compromete ante el regulador, qué compensaciones de consistencia se aceptan y la validación final de que el sistema hace lo que dice hacer.

**Conclusión.** No, una persona sin bases sólidas no podría evaluar correctamente esta solución. El motivo no es que la IA se equivoque mucho, sino que **se equivoca de forma verosímil**. La primera arquitectura parecía completa; el código parecía correcto y estaba bien comentado. Solo con conocimiento previo se puede formular la pregunta adecuada —"¿qué pasa si dos transferencias llegan al mismo tiempo?ˮ— y solo con esa pregunta aparece el fallo. La IA responde extraordinariamente bien; decidir qué preguntarle, y verificar la respuesta, sigue siendo trabajo de ingeniería.

*(≈510 palabras)*

---

## 11. Conclusiones

1. **El valor está en la iteración, no en el primer resultado.** Las seis rondas de refinamiento transformaron un inventario de componentes en una arquitectura con modos de falla analizados. La primera respuesta fue un punto de partida útil y un producto final inaceptable.

2. **La IA optimiza el camino feliz.** Todas las omisiones graves estaban en el comportamiento bajo fallo: core caído, peticiones concurrentes, reintentos del cliente. Es coherente con cómo se entrenan estos modelos —la mayoría del código publicado ilustra el caso exitoso— y define exactamente dónde debe concentrarse la revisión humana.

3. **El contexto regulado debe introducirse explícitamente.** Sin mencionar PCI-DSS ni el dominio bancario, la IA aplica buenas prácticas web genéricas. La tokenización de PAN, la custodia de llaves y la inmutabilidad de la bitácora aparecieron solo cuando se nombraron.

4. **La frontera híbrida es el punto de diseño crítico.** No es un detalle de conectividad: determina qué ocurre con la aplicación cuando el datacenter falla. La diferencia entre una caída total y una degradación elegante estuvo en tres patrones concretos —timeout, circuit breaker y persistencia del estado intermedio.

5. **La verificación ejecutable es innegociable.** Afirmar en un reporte que "se corrigió la concurrenciaˮ no es evidencia. Mostrar que la versión inicial produce un saldo de −$2.000 y la corregida no, sí lo es. Las 43 pruebas cumplen esa función y sobrevivirán a cambios futuros.

6. **La IA amplifica el criterio existente; no lo reemplaza.** Con bases sólidas es un acelerador notable. Sin ellas, produce con enorme fluidez sistemas que parecen correctos y no lo son —que en banca es precisamente el peor resultado posible.

---

## Anexo — Cómo ejecutar

```bash
# Dependencias
pip install fastapi "uvicorn[standard]" pyjwt httpx pytest pytest-asyncio

# Pruebas (43 casos)
cd backend_v2 && python -m pytest tests/ -v

# Demostración de vulnerabilidades v1 vs v2
python demo_vulnerabilidades.py

# API en ejecución
uvicorn app.main:app --reload
# Documentación interactiva: http://localhost:8000/docs
```
