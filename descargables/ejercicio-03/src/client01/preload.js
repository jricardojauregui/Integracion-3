// Puente seguro entre el renderer (sin acceso a Node) y el proceso
// principal. Expone únicamente las funciones necesarias, nada más --
// en particular, nunca expone psycopg2/Postgres ni detalles de red.
const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("clienteLibreria", {
  analizarTexto: (datos) => ipcRenderer.invoke("analizar-texto", datos),
});

contextBridge.exposeInMainWorld("clienteSoap", {
  registrarClasificador: (datos) => ipcRenderer.invoke("soap-registrar-clasificador", datos),
  obtenerConceptosPendientes: (isbn) => ipcRenderer.invoke("soap-obtener-conceptos-pendientes", isbn),
  registrarClasificacion: (datos) => ipcRenderer.invoke("soap-registrar-clasificacion", datos),
  obtenerProgresoUsuario: (idClasificador) => ipcRenderer.invoke("soap-obtener-progreso-usuario", idClasificador),
  obtenerEstadisticasPorModelo: (credenciales) => ipcRenderer.invoke("soap-obtener-estadisticas-por-modelo", credenciales),
});
