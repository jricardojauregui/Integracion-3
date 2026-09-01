# Changelog de Cambios Asistidos por IA

Universidad de Monterrey · Integración de Aplicaciones Computacionales · Trabajo en casa 2e

## Cambio 1 — Corrección de vulnerabilidad en carga de archivos

**Archivo modificado:** `apps/web-monolith/src/middleware/upload.js`

**Riesgo introducido por el hallazgo original (antes del cambio):** un atacante podía subir un
archivo con extensión ejecutable (ej. `.php`) disfrazándolo con un `Content-Type` de imagen
falso, y el servidor lo guardaba con esa extensión intacta en una carpeta pública.

**Riesgo introducido por el cambio (evaluado antes de aplicarlo):** ninguno nuevo. El cambio
solo restringe comportamiento (una lista blanca cerrada de 3 mimetypes en vez de 4, y una fuente
de verdad para la extensión controlada por el servidor en vez del cliente). Se evaluó que no
rompe ningún caso de uso legítimo, ya que el ejercicio (`REQUIREMENTS.md`, RF-15) solo exige
soportar JPG, PNG y WebP — se eliminó GIF, que estaba fuera del alcance original.

**Diff conceptual:**
- Antes: `const ext = path.extname(file.originalname).toLowerCase();` (extensión del cliente)
- Después: `const ext = MIME_A_EXTENSION[file.mimetype];` (extensión decidida por el servidor,
  mapa fijo)
- Se agregó `crypto.randomBytes(16)` al nombre del archivo final.

**Pruebas ejecutadas para verificar el fix:**
1. Se creó un archivo de prueba `fake.php` con contenido `<?php echo 'test'; ?>`.
2. Se subió con `curl`, falsificando el `Content-Type` como `image/jpeg`:
   ```bash
   curl -b cookies.txt -X POST http://localhost:3000/libros/978-0-307-47472-8/imagenes \
     -F "imagen=@fake.php;type=image/jpeg" -F "alt_text=prueba de seguridad"
   ```
3. Se verificó el archivo resultante en el servidor:
   ```bash
   ls apps/web-monolith/public/uploads/ | tail -5
   ```

**Resultado observado:** el archivo quedó guardado como
`img_1788151789469_973ed0739e100ad31b82bf5c8b56adb4.jpg` (22 bytes, contenido PHP intacto pero
con extensión forzada a `.jpg` por el servidor) — nunca con extensión `.php`. La vulnerabilidad
quedó cerrada con evidencia reproducible. Este caso de prueba se agregó formalmente como TC-12
en `docs/TEST_PLAN.md`, y el hallazgo completo (amenaza, control, evidencia) está documentado
como control #7 en `docs/SECURITY_REVIEW.md`.

**Responsabilidad de verificación:** el estudiante revisó el código propuesto por la IA antes de
aplicarlo, entendió por qué la extensión del cliente no es una fuente confiable, ejecutó
personalmente la prueba de explotación (no solo aceptó la explicación de la IA), y confirmó el
resultado en el sistema de archivos real del servidor antes de dar el cambio por válido.

---
*Documento generado para la Tarea 2e de trabajo en casa. Ver `PROMPT_MAESTRO_IA.md` para la
solicitud original y `AI_PROMPT_HISTORY.md` para la respuesta completa de la IA.*
