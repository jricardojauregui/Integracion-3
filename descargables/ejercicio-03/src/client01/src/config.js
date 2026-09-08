// Carga la configuración del cliente desde variables de entorno (.env).
// Las URLs de los servicios remotos viven en la nube; aquí solo se
// referencian por config, nunca se hardcodean en el resto del código.
require("dotenv").config();

const API_BASE_URL = (process.env.API_BASE_URL || "http://localhost:5000").replace(/\/+$/, "");
const SOAP_ENDPOINT_URL = process.env.SOAP_ENDPOINT_URL || "http://localhost:5050/soap";

module.exports = { API_BASE_URL, SOAP_ENDPOINT_URL };
