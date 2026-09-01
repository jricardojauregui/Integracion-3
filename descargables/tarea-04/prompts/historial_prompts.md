# Historial de prompts — Tarea 4

Registro literal de los prompts usados, para reproducibilidad.

---

## Prompt inicial

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

**Resultado:** arquitectura v1 (`diagramas/arquitectura_v1.svg`) y `backend_v1/main.py`.

---

## Prompt 1 — Vulnerabilidades

```
Actúa ahora como pentester y auditor de seguridad especializado en banca. Revisa
el prototipo de backend y la arquitectura línea por línea. Enumera cada
vulnerabilidad concreta indicando: el vector de ataque, el impacto en un contexto
financiero regulado y la corrección específica. No des recomendaciones genéricas:
señala la línea de código o el componente exacto. Considera OWASP Top 10, OWASP
API Security Top 10 y los requisitos de PCI-DSS.
```

**Produjo:** catálogo F-1 a F-15. Cambios: WAF, gestor de secretos, MFA,
tokenización de PAN, redacción de logs.

---

## Prompt 2 — Puntos únicos de falla

```
Identifica todos los puntos únicos de falla de esta arquitectura. Para cada uno
indica qué ocurre exactamente cuando falla, qué porcentaje de usuarios se ve
afectado y cómo eliminarlo. Presta atención especial al enlace híbrido con el core
on-premises: ¿qué pasa con la aplicación móvil si el datacenter queda incomunicado
30 minutos? Analiza también fallos parciales y en cascada, no solo caídas totales.
```

**Produjo:** hallazgo F-8 (el más grave de arquitectura). Cambios: multi-AZ,
circuit breaker, degradación elegante, saga, bus de eventos.

---

## Prompt 3 — Escalabilidad y justificación

```
Dimensiona la arquitectura para 2 millones de usuarios activos, con picos de 15.000
peticiones por segundo en quincena y día de pago. Identifica qué componente satura
primero y por qué. Para cada servicio propuesto, justifica por qué ese y no una
alternativa: compara contenedores contra serverless para cada carga de trabajo, y
SQL contra NoSQL para cada tipo de dato. Sé explícito sobre los contras de cada
elección.
```

**Produjo:** el core on-prem como cuello de botella real. Cambios: colas
amortiguadoras, caché distribuida, bulkhead, tabla de justificación de servicios.

---

## Prompt 4 — Observabilidad

```
Incorpora observabilidad de nivel producción. No basta con "usar CloudWatch":
define qué métricas específicas, qué SLIs y SLOs, qué alertas y sobre qué umbrales.
¿Cómo se rastrea una transferencia individual que atraviesa la app móvil, el API
Gateway, el backend en la nube y el core on-premises? ¿Qué se registra y qué NO
debe registrarse nunca por cumplimiento?
```

**Produjo:** F-12 y F-13. Cambios: OpenTelemetry, correlation-ID, logs JSON con
redacción, SLOs orientados al usuario.

---

## Prompt 5 — Costos y DR

```
Analiza el modelo de costos e identifica las tres partidas que más crecerán con el
volumen. ¿Qué decisión arquitectónica actual generará una factura inesperada?
Después diseña la estrategia de recuperación ante desastres: define RTO y RPO
justificados para banca, qué se replica, con qué frecuencia, cómo se prueba el
failover y cómo se recupera un core on-premises destruido.
```

**Produjo:** costo de egreso como partida subestimada. Cambios: enlace dedicado,
retención por niveles, DR warm standby con RTO ≤ 30 min y RPO ≤ 5 min.

---

## Prompt 6 — Revisión de código y pruebas

```
Revisa el prototipo de backend buscando errores de correctitud, no de estilo:
condiciones de carrera, problemas de concurrencia, manejo de dinero, atomicidad de
transacciones e idempotencia. Para cada problema, escribe una prueba automatizada
que lo demuestre fallando antes de la corrección. Genera después la versión
corregida y la suite completa de pruebas.
```

**Produjo:** F-5, F-6, F-7. Cambios: Decimal sobre centavos, idempotencia
obligatoria, bloqueo ordenado, máquina de estados. Resultado: 43 pruebas.
