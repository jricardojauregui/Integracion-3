// ─────────────────────────────────────────────────────────────────────────
// Proceso principal de Electron.
// - Crea la ventana con contextIsolation activado y nodeIntegration
//   desactivado en el renderer (buena práctica de seguridad: el renderer
//   nunca toca Node ni la red directamente).
// - Toda la lógica de clasificación local, las llamadas al microservicio
//   REST/XML (Ejercicio03) y ahora también las llamadas al módulo SOAP
//   (Ejercicio04, Paso 14) viven aquí; el renderer solo pide resultados
//   por IPC y nunca se conecta a PostgreSQL para ejecutar nada.
// ─────────────────────────────────────────────────────────────────────────
const { app, BrowserWindow, ipcMain } = require("electron");
const path = require("path");

const { clasificarTexto } = require("./src/classifier");
const { buscarLibrosPorGenero } = require("./src/xmlApiClient");
const soap = require("./src/soapClient");

function crearVentana() {
  const win = new BrowserWindow({
    width: 780,
    height: 900,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });
  win.loadFile(path.join(__dirname, "renderer", "index.html"));
}

// ── Modo microservicio REST/XML (Ejercicio03), sin cambios ─────────────
ipcMain.handle("analizar-texto", async (_event, { nombre, apellido, texto }) => {
  const resultadoClasificacion = clasificarTexto(texto || "");
  let librosRelacionados = [];
  let errorCatalogo = null;
  try {
    librosRelacionados = await buscarLibrosPorGenero("Cloud Computing");
  } catch (err) {
    errorCatalogo = err.message;
  }
  return {
    nombreCompleto: `${nombre || ""} ${apellido || ""}`.trim(),
    ...resultadoClasificacion,
    librosRelacionados,
    errorCatalogo,
  };
});

// ── Modo cliente SOAP (Ejercicio04, Paso 14) ────────────────────────────
// Cada handler devuelve siempre { ok, data } o { ok:false, fault:{...} }
// o { ok:false, error:"..." } -- el renderer NUNCA ve un stack trace ni
// tiene que distinguir tipos de excepción de Node, solo lee esta forma.
function envolver(promesa) {
  return promesa
    .then((data) => ({ ok: true, data }))
    .catch((err) => {
      if (err instanceof soap.SoapFaultError) {
        return { ok: false, fault: { codigo: err.codigo, descripcion: err.message, faultcode: err.faultcode } };
      }
      return { ok: false, error: err.message };
    });
}

ipcMain.handle("soap-registrar-clasificador", (_event, datos) =>
  envolver(soap.registrarClasificadorSoap(datos))
);
ipcMain.handle("soap-obtener-conceptos-pendientes", (_event, isbn) =>
  envolver(soap.obtenerConceptosPendientesSoap(isbn))
);
ipcMain.handle("soap-registrar-clasificacion", (_event, datos) =>
  envolver(soap.registrarClasificacionSoap(datos))
);
ipcMain.handle("soap-obtener-progreso-usuario", (_event, idClasificador) =>
  envolver(soap.obtenerProgresoUsuarioSoap(idClasificador))
);
ipcMain.handle("soap-obtener-estadisticas-por-modelo", (_event, credenciales) =>
  envolver(soap.obtenerEstadisticasPorModeloSoap(credenciales))
);

app.whenReady().then(() => {
  crearVentana();
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) crearVentana();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});
