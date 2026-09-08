// ─────────────────────────────────────────────────────────────────────────
// Cliente HTTP para el microservicio de libros (Flask), consumiendo
// EXCLUSIVAMENTE el formato XML (nunca JSON).
//
// Nota sobre CORS: esta app hace las peticiones desde el proceso PRINCIPAL
// de Electron (Node.js), no desde el renderer/navegador. El proceso
// principal no está sujeto a la política de mismo origen del navegador,
// por lo que no dispara comprobaciones CORS. Aun así, el microservicio
// remoto habilita CORS (flask-cors) para admitir también clientes basados
// en navegador que corran fuera de su dominio, tal como indica el
// enunciado. El renderer nunca llama a la red directamente: siempre pasa
// por IPC hacia este módulo (ver preload.js / main.js).
// ─────────────────────────────────────────────────────────────────────────
const http = require("http");
const https = require("https");
const { URL } = require("url");
const { XMLParser } = require("fast-xml-parser");
const { API_BASE_URL } = require("./config");

const parser = new XMLParser({
  ignoreAttributes: false,
  attributeNamePrefix: "@_",
  isArray: (tagName, jPath) => {
    // Las colecciones que devuelve el microservicio pueden venir como un solo
    // elemento; forzamos siempre arreglo para que el resto del código no
    // tenga que distinguir "un libro" de "varios libros".
    return ["libro", "item"].includes(tagName);
  },
});

/**
 * Ejecuta un GET contra el microservicio pidiendo explícitamente XML
 * (?format=xml y Accept: application/xml) y devuelve el objeto ya parseado.
 */
function getXml(pathAndQuery) {
  return new Promise((resolve, reject) => {
    const url = new URL(`${API_BASE_URL}${pathAndQuery}`);
    url.searchParams.set("format", "xml"); // fuerza XML sin importar lo que pida el llamador

    const client = url.protocol === "https:" ? https : http;
    const req = client.request(
      url,
      {
        method: "GET",
        headers: { Accept: "application/xml" },
      },
      (res) => {
        let body = "";
        res.setEncoding("utf8");
        res.on("data", (chunk) => (body += chunk));
        res.on("end", () => {
          if (res.statusCode >= 400) {
            reject(new Error(`El microservicio respondió ${res.statusCode}: ${body}`));
            return;
          }
          try {
            resolve(parser.parse(body));
          } catch (err) {
            reject(new Error(`No se pudo interpretar la respuesta XML: ${err.message}`));
          }
        });
      }
    );
    req.on("error", (err) => reject(new Error(`Fallo de red al contactar el microservicio: ${err.message}`)));
    req.setTimeout(10000, () => req.destroy(new Error("Tiempo de espera agotado al contactar el microservicio")));
    req.end();
  });
}

/**
 * Busca libros por género en el catálogo remoto (p. ej. "Cloud Computing"),
 * usando el endpoint /libros/buscar?genero=...
 * Devuelve siempre un arreglo (vacío si no hay coincidencias).
 */
async function buscarLibrosPorGenero(genero) {
  const query = `/libros/buscar?genero=${encodeURIComponent(genero)}`;
  const data = await getXml(query);
  const libros = data?.libros?.libro;
  if (!libros) return [];
  return Array.isArray(libros) ? libros : [libros];
}

/**
 * Verifica disponibilidad del microservicio (usa /health, también en XML).
 */
async function verificarSalud() {
  const data = await getXml("/health");
  return data?.salud || data;
}

module.exports = { buscarLibrosPorGenero, verificarSalud };
