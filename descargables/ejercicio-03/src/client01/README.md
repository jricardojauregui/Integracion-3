# Cliente 01 — Clasificador Cloud (Electron)

Aplicación de escritorio (Electron) que consume **exclusivamente XML** del
microservicio de libros (`apps/services/soap/libros_service.py`) y clasifica
una descripción de texto libre en uno de los cuatro modelos de servicio
Cloud: **IaaS, PaaS, FaaS o SaaS**.

## Cómo funciona

1. El usuario captura su nombre, apellido y un texto sobre Cloud Computing.
2. `src/classifier.js` analiza el texto con una función independiente por
   modelo (`analizarIaaS`, `analizarPaaS`, `analizarFaaS`, `analizarSaaS`),
   cada una contando coincidencias con su propio listado de palabras clave.
   El modelo con más coincidencias es el resultado (`clasificarTexto`).
3. `src/xmlApiClient.js` consulta `GET /libros/buscar?genero=Cloud
   Computing&format=xml` en el microservicio remoto para mostrar libros
   relacionados del catálogo. La petición siempre pide XML (`format=xml` +
   `Accept: application/xml`); la respuesta se parsea con `fast-xml-parser`.
4. `main.js` (proceso principal de Electron) orquesta ambos pasos y expone
   el resultado al renderer vía IPC (`preload.js` + `window.clienteLibreria`).

## Modo cliente SOAP (Ejercicio 03)

Además del modo REST/XML anterior, el cliente puede consumir el módulo
**`apps/services/library_soap_service`** (Flask + SOAP) para clasificar
conceptos reales del catálogo:

- `src/soapClient.js` arma el sobre SOAP **a mano** (sin librerías SOAP),
  lo envía por HTTP POST y parsea la respuesta / el `soap:Fault` con
  `fast-xml-parser`.
- `main.js` expone cada operación por IPC (`soap-registrar-clasificador`,
  `soap-obtener-conceptos-pendientes`, `soap-registrar-clasificacion`,
  `soap-obtener-progreso-usuario`, `soap-obtener-estadisticas-por-modelo`)
  y siempre devuelve `{ ok, data }` o `{ ok:false, fault }` — el renderer
  nunca ve un stack trace ni toca la red.
- `renderer/renderer.js` traduce el `soap:Fault` a un mensaje amigable
  (`MENSAJES_FAULT`, Tarea 2).
- Endpoint configurable en `.env`: `SOAP_ENDPOINT_URL=http://localhost:5050/soap`.

## Sobre CORS

Las peticiones HTTP se hacen desde el **proceso principal** de Electron
(Node.js), no desde el renderer/navegador, así que no están sujetas a la
política de mismo origen ni a CORS. El microservicio remoto además habilita
CORS de forma abierta (`flask-cors`), por si en el futuro se quisiera migrar
esta lógica al renderer.

## Configuración

```bash
cp .env.example .env
# Edita .env y coloca la URL pública de tu instancia en la nube:
# API_BASE_URL=https://tu-instancia-cloud.example.com
```

## Ejecutar

```bash
npm install
npm start
```
