// ─────────────────────────────────────────────────────────────────────────
// Clasificador de texto libre en uno de los 4 modelos de servicio Cloud:
// IaaS, PaaS, FaaS, SaaS.
//
// Estrategia: cada modelo tiene una función INDEPENDIENTE que cuenta cuántas
// palabras/frases clave asociadas a ese modelo aparecen en el texto del
// usuario. Al final se comparan los 4 puntajes y gana el modelo con más
// coincidencias. Esto mantiene el análisis simple, explicable y fácil de
// ajustar (basta con editar la lista de palabras clave de cada función).
// ─────────────────────────────────────────────────────────────────────────

// Palabras/frases clave por modelo (español e inglés, en minúsculas).
const PALABRAS_IAAS = [
  "infraestructura", "infrastructure", "iaas", "máquina virtual", "maquina virtual",
  "virtual machine", "servidor virtual", "servidores", "cómputo", "computo", "compute",
  "almacenamiento en bloque", "block storage", "red virtual", "virtual network",
  "balanceador de carga", "load balancer", "firewall", "hipervisor", "hypervisor",
  "bare metal", "disco duro virtual", "vpc", "subred", "subnet", "ec2", "compute engine",
  "aprovisionar servidores", "centro de datos", "data center", "rack", "networking",
];

const PALABRAS_PAAS = [
  "plataforma", "platform", "paas", "entorno de desarrollo", "development environment",
  "runtime", "middleware", "framework", "despliegue de aplicaciones", "app deployment",
  "base de datos administrada", "managed database", "app engine", "elastic beanstalk",
  "heroku", "cloud foundry", "openshift", "integración continua", "ci/cd",
  "contenedor administrado", "managed kubernetes", "entorno gestionado", "sdk",
];

const PALABRAS_FAAS = [
  "función", "funcion", "function", "faas", "serverless", "sin servidor",
  "por evento", "event-driven", "eventos", "trigger", "disparador", "lambda",
  "cloud functions", "azure functions", "pago por ejecución", "pago por ejecucion",
  "pay per execution", "cómputo efímero", "computo efimero", "stateless", "microservicio",
  "escalado automático a cero", "scale to zero",
];

const PALABRAS_SAAS = [
  "software", "saas", "aplicación web", "aplicacion web", "web application",
  "suscripción", "suscripcion", "subscription", "listo para usar", "ready to use",
  "gmail", "office 365", "salesforce", "dropbox", "zoom", "correo electrónico",
  "correo electronico", "usuario final", "end user", "multiusuario", "multi-tenant",
  "navegador", "browser", "sin instalación", "sin instalacion", "no installation",
];

function _contarCoincidencias(texto, palabrasClave) {
  const textoNormalizado = texto.toLowerCase();
  return palabrasClave.filter((palabra) => textoNormalizado.includes(palabra)).length;
}

/** Analiza el texto en busca de indicios de Infraestructura como Servicio. */
function analizarIaaS(texto) {
  return _contarCoincidencias(texto, PALABRAS_IAAS);
}

/** Analiza el texto en busca de indicios de Plataforma como Servicio. */
function analizarPaaS(texto) {
  return _contarCoincidencias(texto, PALABRAS_PAAS);
}

/** Analiza el texto en busca de indicios de Función como Servicio. */
function analizarFaaS(texto) {
  return _contarCoincidencias(texto, PALABRAS_FAAS);
}

/** Analiza el texto en busca de indicios de Software como Servicio. */
function analizarSaaS(texto) {
  return _contarCoincidencias(texto, PALABRAS_SAAS);
}

/**
 * Ejecuta las 4 funciones de análisis y determina el modelo predominante.
 * Devuelve el detalle de puntajes y la categoría ganadora (o "Indeterminado"
 * si el texto no arrojó ninguna coincidencia con ningún modelo).
 */
function clasificarTexto(texto) {
  const puntajes = {
    IaaS: analizarIaaS(texto),
    PaaS: analizarPaaS(texto),
    FaaS: analizarFaaS(texto),
    SaaS: analizarSaaS(texto),
  };

  const maxPuntaje = Math.max(...Object.values(puntajes));
  const ganadores = Object.keys(puntajes).filter((k) => puntajes[k] === maxPuntaje);

  const categoria = maxPuntaje === 0 ? "Indeterminado" : ganadores[0];
  const empate = maxPuntaje > 0 && ganadores.length > 1;

  return { categoria, empate, puntajes };
}

module.exports = { analizarIaaS, analizarPaaS, analizarFaaS, analizarSaaS, clasificarTexto };
