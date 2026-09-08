# Paso 1-2: Revisión del sistema existente y definición del scope

Ver el desarrollo completo de esta parte (mapeo de tablas books/concepts/
book_concepts/categories -> libros/conceptos/libro_concepto/generos,
qué es de solo lectura, qué genera el módulo, y el scope acordado con
las 6 capacidades mínimas + lo fuera de alcance) en la conversación con
Claude y resumido en:
`codigo_fuente_completo/library_soap_service/DOCUMENTACION_TECNICA.md`
(secciones 1 y 5) y en el archivo de memoria del proyecto.

Resumen ejecutivo:
- usuarios del monolito: fuera de alcance total del módulo SOAP.
- libros/autores/generos/formatos/libro_autor/libro_genero/libro_imagen: solo lectura.
- conceptos/libro_concepto: base de lectura para "pendientes"; el módulo
  agrega su propia capa de escritura en tablas nuevas (Parte 4).
- Scope: consultar pendientes, registrar clasificaciones Cloud, consultar
  progreso, registrar clasificadores/clientes y contar peticiones,
  detectar duplicados vía Fault, monolito sin cambios. Fuera de alcance:
  migrar el monolito, API REST, reemplazar PostgreSQL, modificar el
  esquema funcional existente, usar Spyne/Zeep en el servidor.
