# Verificación de persistencia e integración (Paso 16)

No hay un PostgreSQL real disponible en el entorno donde armé este
módulo, así que esto es una **guía lista para ejecutar** contra tu base
real — no evidencia ya corrida (a diferencia de `TEST_PLAN.md`, que sí
corrió contra un servidor real con una BD en memoria equivalente).

## 1. Clasificar conceptos reales

Con el módulo corriendo (`python app.py` dentro de
`apps/services/library_soap_service/`), usa el cliente Electron (Paso 14)
o `curl` con los XML de `evidencia/xml/*_request.xml` como plantilla,
contra libros/conceptos reales de tu base (`SELECT isbn, id_concepto FROM
libro_concepto LIMIT 5;` para elegir combinaciones válidas).

Clasifica **varios libros y categorías distintas** — no solo repitas el
mismo isbn/concepto — para que la verificación de abajo tenga datos
variados que revisar.

## 2. Verificar en PostgreSQL que llegó a `clasificaciones_cloud`

```sql
-- Debe haber una fila por cada clasificación que registraste
SELECT cc.id_clasificacion, cc.isbn, l.titulo, c.nombre AS concepto,
       cc.modelo_cloud, cc.id_clasificador, cc.fecha_clasificacion
FROM clasificaciones_cloud cc
JOIN libros l ON l.isbn = cc.isbn
JOIN conceptos c ON c.id_concepto = cc.id_concepto
ORDER BY cc.created_at DESC
LIMIT 20;

-- Confirma que el UNIQUE hace su trabajo: no debe haber ninguna fila
-- duplicada de (id_clasificador, isbn, id_concepto)
SELECT id_clasificador, isbn, id_concepto, count(*)
FROM clasificaciones_cloud
GROUP BY id_clasificador, isbn, id_concepto
HAVING count(*) > 1;
-- Esperado: 0 filas (la restricción UNIQUE lo garantiza a nivel de motor)
```

## 3. Verificar `clientes_servidos`

Esta tabla la pobla el modo cliente SOAP de la app de escritorio (Paso 14)
cada vez que sirve una petición — si tu implementación final del cliente
todavía no escribe ahí directamente (el diseño actual la deja para que
el módulo la use como bitácora, ver Paso 7), regístrala manualmente para
verificar el conteo:

```sql
SELECT tipo_cliente, identificador_cliente, peticiones_atendidas,
       primera_peticion, ultima_peticion
FROM clientes_servidos
ORDER BY ultima_peticion DESC;
```

## 4. Confirmar que el monolito sigue intacto

```sql
-- No debe haber diferencias de estructura: compara contra
-- data/schema.sql / db/01_schema.sql del Ejercicio02
\d libros
\d usuarios
\d conceptos
\d libro_concepto

-- El rol del módulo NO debe poder tocar usuarios (Paso 8) -- correr
-- esto CONECTADO COMO soap_module_user, debe fallar con "permission denied":
SELECT * FROM usuarios LIMIT 1;
INSERT INTO libros (isbn, titulo, anio_publicacion, precio, stock, id_formato)
VALUES ('000-TEST', 'no deberia poder', 2024, 1, 1, 1);
```

## 5. Qué conservar como evidencia

- Captura de pantalla de la consulta del punto 2 con filas reales.
- Captura de la consulta del punto 4 mostrando el `permission denied`
  (es la prueba más fuerte de mínimo privilegio — negativa, no solo
  la lista de GRANTs del Paso 8).
- El WSDL servido (`curl http://localhost:5050/wsdl`), una captura de la
  GUI del cliente Electron en modo SOAP, y los XML de
  `evidencia/xml/` (ya generados con un servidor real, aunque con datos
  de la BD en memoria) como referencia del formato esperado.
