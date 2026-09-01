# Historial de Prompts de IA

Universidad de Monterrey · Integración de Aplicaciones Computacionales · Trabajo en casa 2e

## Entrada 1 — Auditoría de `middleware/upload.js`

**Fecha:** sesión de auditoría de código, Parte 5 del ejercicio.

**Prompt (resumen del contexto y la solicitud exacta):** ver `PROMPT_MAESTRO_IA.md`. En
resumen: se pidió a la IA revisar el middleware de carga de imágenes para confirmar que
validaba correctamente tipo y tamaño de archivo, después de haber compartido el contenido
completo del archivo original:

```javascript
const fileFilter = (req, file, cb) => {
  const allowedMimes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
  if (allowedMimes.includes(file.mimetype)) {
    cb(null, true);
  } else {
    cb(new Error('Tipo de archivo no permitido...'), false);
  }
};
```
con la generación del nombre de archivo:
```javascript
filename: (req, file, cb) => {
  const ext = path.extname(file.originalname).toLowerCase();
  cb(null, `img_${Date.now()}${ext}`);
}
```

**Respuesta relevante de la IA (resumida):** la IA identificó que `fileFilter` valida
únicamente `file.mimetype`, un dato controlado por el cliente y falsificable en la petición
HTTP; y que `filename` deriva la extensión final directamente de `file.originalname`, también
controlado por el cliente. La combinación permite que un archivo `shell.php` enviado con
`Content-Type: image/jpeg` falsificado quede guardado en el servidor con extensión `.php`
dentro de una carpeta servida públicamente (`public/uploads`, montada vía `express.static`).

**Riesgo identificado por la IA:** ejecución de código en el servidor si la configuración de
despliegue llegara a interpretar archivos `.php` en esa ruta (no aplica al stack actual, 100%
Node.js, pero es el tipo de hallazgo que una revisión de seguridad debe señalar
independientemente de la probabilidad de explotación en el entorno actual).

**Cambio propuesto por la IA:** reescribir `upload.js` para que la extensión del archivo
**siempre** salga de un mapa fijo `mimetype → extensión` decidido por el servidor
(`image/jpeg → .jpg`, `image/png → .png`, `image/webp → .webp`), eliminando por completo el uso
de `file.originalname` para ese propósito, y agregar un componente aleatorio
(`crypto.randomBytes`) al nombre final del archivo.

---
*Ver `AI_CHANGELOG.md` para el archivo modificado, las pruebas ejecutadas y el resultado.*
