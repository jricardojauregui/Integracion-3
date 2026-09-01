# Prompt Maestro de IA — Solicitud de Mejora Verificable

Universidad de Monterrey · Integración de Aplicaciones Computacionales · Trabajo en casa 2e

Este documento registra la solicitud puntual usada para pedirle a la IA (Claude, Anthropic) que
analizara `apps/web-monolith/src/middleware/upload.js` en busca de una mejora pequeña y
verificable, como parte de la auditoría de código de la Parte 5 del ejercicio.

## Prompt exacto

> "Falta ver el middleware de carga de imágenes para confirmar que valida tipo/tamaño de archivo
> (RF-15/RNF de seguridad). Mándame: `cat apps/web-monolith/src/middleware/upload.js`"

Seguido de pegar el contenido real del archivo para que la IA lo auditara línea por línea.

## Alcance solicitado

Revisión de seguridad de un único archivo (~30 líneas), buscando específicamente si la
validación de tipo de archivo era suficiente para impedir la subida de archivos peligrosos,
conforme al control "Validación de archivos subidos: extensión, MIME, tamaño y nombre" exigido
por la Parte 6 del ejercicio.

---
*Ver `AI_PROMPT_HISTORY.md` para la respuesta completa y `AI_CHANGELOG.md` para el resultado
verificado.*
