// ─────────────────────────────────────────────────────────────────────────
// Cliente SOAP manual (Paso 14) contra apps/services/library_soap_service.
// Mismo espíritu que el servidor: sin librerías de SOAP (nada de un cliente
// generado desde el WSDL aquí -- eso es la Tarea 4, un cliente APARTE).
// Construye el Envelope a mano (con escape explícito de valores) y parsea
// la respuesta con fast-xml-parser, que ya es dependencia del proyecto.
//
// Igual que xmlApiClient.js: todo corre en el proceso PRINCIPAL de
// Electron, nunca en el renderer -- por eso no hay problema de CORS y por
// eso el renderer nunca toca la red ni Postgres directamente (Paso 14:
// "la aplicación de escritorio deberá comunicarse con el módulo SOAP; no
// deberá conectarse a PostgreSQL para ejecutar la clasificación").
// ─────────────────────────────────────────────────────────────────────────
const http = require("http");
const https = require("https");
const { URL } = require("url");
const { XMLParser } = require("fast-xml-parser");
const { SOAP_ENDPOINT_URL } = require("./config");

const SOAP_NS = "http://schemas.xmlsoap.org/soap/envelope/";
const TNS = "urn:udem:iac:libreria:soap";
const WSSE_NS = "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd";

const parser = new XMLParser({ ignoreAttributes: false, removeNSPrefix: true, htmlEntities: true });

/** Escapa un valor para insertarlo como texto dentro de un elemento XML. */
function escaparXml(valor) {
  return String(valor ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

/** Un elemento <tag>valor</tag>, o "" si valor es null/undefined (omitido). */
function campo(tag, valor) {
  if (valor === null || valor === undefined || valor === "") return "";
  return `<${tag}>${escaparXml(valor)}</${tag}>`;
}

/** Construye el soap:Header con wsse:UsernameToken, o vacío si no hay credenciales. */
function construirHeader(credenciales) {
  if (!credenciales || !credenciales.usuario) return "<soap:Header/>";
  return `<soap:Header>
    <wsse:Security xmlns:wsse="${WSSE_NS}">
      <wsse:UsernameToken>
        <wsse:Username>${escaparXml(credenciales.usuario)}</wsse:Username>
        <wsse:Password>${escaparXml(credenciales.password)}</wsse:Password>
      </wsse:UsernameToken>
    </wsse:Security>
  </soap:Header>`;
}

function construirEnvelope(nombreOperacion, camposInternos, credenciales) {
  return `<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="${SOAP_NS}" xmlns:tns="${TNS}">
  ${construirHeader(credenciales)}
  <soap:Body>
    <tns:${nombreOperacion}Request>${camposInternos}</tns:${nombreOperacion}Request>
  </soap:Body>
</soap:Envelope>`;
}

/** Error específico para un soap:Fault -- distinto de un error de red/parseo. */
class SoapFaultError extends Error {
  constructor(codigo, descripcion, faultcode) {
    super(descripcion);
    this.name = "SoapFaultError";
    this.codigo = codigo;
    this.faultcode = faultcode;
  }
}

function enviarEnvelope(xmlEnvelope) {
  return new Promise((resolve, reject) => {
    const url = new URL(SOAP_ENDPOINT_URL);
    const cliente = url.protocol === "https:" ? https : http;
    const cuerpo = Buffer.from(xmlEnvelope, "utf8");

    const req = cliente.request(
      url,
      {
        method: "POST",
        headers: {
          "Content-Type": "text/xml; charset=utf-8",
          "Content-Length": cuerpo.length,
        },
      },
      (res) => {
        let body = "";
        res.setEncoding("utf8");
        res.on("data", (chunk) => (body += chunk));
        res.on("end", () => {
          let parsed;
          try {
            parsed = parser.parse(body);
          } catch (err) {
            reject(new Error(`Respuesta SOAP no es XML válido: ${err.message}`));
            return;
          }
          const envelope = parsed.Envelope;
          const fault = envelope?.Body?.Fault;
          if (fault) {
            const detalle = fault.detail?.LibreriaFaultDetail || {};
            reject(
              new SoapFaultError(
                detalle.codigo || "DESCONOCIDO",
                detalle.descripcion || fault.faultstring || "Error no especificado.",
                fault.faultcode || ""
              )
            );
            return;
          }
          resolve(envelope?.Body);
        });
      }
    );
    req.on("error", (err) => reject(new Error(`Fallo de red al contactar el módulo SOAP: ${err.message}`)));
    req.setTimeout(10000, () => req.destroy(new Error("Tiempo de espera agotado contactando el módulo SOAP")));
    req.write(cuerpo);
    req.end();
  });
}

// ── Operaciones expuestas (nombres iguales al WSDL) ────────────────────

async function obtenerConceptosPendientesSoap(isbn) {
  const xml = construirEnvelope("ObtenerConceptosPendientes", campo("isbn", isbn));
  const body = await enviarEnvelope(xml);
  const respuesta = body?.ObtenerConceptosPendientesResponse;
  const conceptos = respuesta?.concepto || [];
  return Array.isArray(conceptos) ? conceptos : [conceptos];
}

async function registrarClasificacionSoap({ idClasificador, isbn, idConcepto, modeloCloud }) {
  const campos =
    campo("idClasificador", idClasificador) +
    campo("isbn", isbn) +
    campo("idConcepto", idConcepto) +
    campo("modeloCloud", modeloCloud);
  const xml = construirEnvelope("RegistrarClasificacion", campos);
  const body = await enviarEnvelope(xml);
  return body?.RegistrarClasificacionResponse;
}

async function obtenerProgresoUsuarioSoap(idClasificador) {
  const xml = construirEnvelope("ObtenerProgresoUsuario", campo("idClasificador", idClasificador));
  const body = await enviarEnvelope(xml);
  return body?.ObtenerProgresoUsuarioResponse;
}

async function registrarClasificadorSoap({ nombre, apellido, correo }) {
  const campos = campo("nombre", nombre) + campo("apellido", apellido) + campo("correo", correo);
  const xml = construirEnvelope("RegistrarClasificador", campos);
  const body = await enviarEnvelope(xml);
  return body?.RegistrarClasificadorResponse;
}

/** Tarea 1: protegida con WS-Security -- requiere credenciales {usuario, password}. */
async function obtenerEstadisticasPorModeloSoap(credenciales) {
  const xml = construirEnvelope("ObtenerEstadisticasPorModelo", "", credenciales);
  const body = await enviarEnvelope(xml);
  return body?.ObtenerEstadisticasPorModeloResponse;
}

module.exports = {
  SoapFaultError,
  obtenerConceptosPendientesSoap,
  registrarClasificacionSoap,
  obtenerProgresoUsuarioSoap,
  registrarClasificadorSoap,
  obtenerEstadisticasPorModeloSoap,
};
