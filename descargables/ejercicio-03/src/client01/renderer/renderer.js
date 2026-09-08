// Lógica del renderer: solo maneja formularios y pinta resultados. Toda
// la red (REST/XML del Ejercicio03 y SOAP del Ejercicio04) ocurre del
// otro lado (main.js), a la que se accede exclusivamente mediante
// `window.clienteLibreria` / `window.clienteSoap` (expuestas de forma
// segura por preload.js). El renderer nunca sabe nada de PostgreSQL.

// ── Modo microservicio REST/XML (sin cambios) ───────────────────────────
const formulario = document.getElementById("formulario");
const seccionResultado = document.getElementById("resultado");

formulario.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const nombre = document.getElementById("nombre").value;
  const apellido = document.getElementById("apellido").value;
  const texto = document.getElementById("texto").value;

  const boton = formulario.querySelector("button");
  boton.disabled = true;
  boton.textContent = "Analizando...";
  try {
    const resultado = await window.clienteLibreria.analizarTexto({ nombre, apellido, texto });
    pintarResultado(resultado);
  } catch (err) {
    alert(`Ocurrió un error al analizar el texto: ${err.message}`);
  } finally {
    boton.disabled = false;
    boton.textContent = "Analizar (microservicio REST/XML)";
  }
});

function pintarResultado(resultado) {
  document.getElementById("saludo").textContent = `Hola, ${resultado.nombreCompleto}`;
  document.getElementById("categoriaDetectada").textContent = resultado.categoria;
  document.getElementById("avisoEmpate").hidden = !resultado.empate;

  const listaPuntajes = document.getElementById("listaPuntajes");
  listaPuntajes.innerHTML = "";
  for (const [modelo, puntaje] of Object.entries(resultado.puntajes)) {
    const li = document.createElement("li");
    li.textContent = `${modelo}: ${puntaje} coincidencia(s)`;
    listaPuntajes.appendChild(li);
  }

  const avisoCatalogo = document.getElementById("avisoCatalogo");
  const listaLibros = document.getElementById("listaLibros");
  listaLibros.innerHTML = "";
  if (resultado.errorCatalogo) {
    avisoCatalogo.hidden = false;
    avisoCatalogo.textContent = `No se pudo consultar el catálogo remoto: ${resultado.errorCatalogo}`;
  } else if (resultado.librosRelacionados.length === 0) {
    avisoCatalogo.hidden = false;
    avisoCatalogo.textContent = "No hay libros de Cloud Computing registrados en el catálogo por ahora.";
  } else {
    avisoCatalogo.hidden = true;
    for (const libro of resultado.librosRelacionados) {
      const li = document.createElement("li");
      li.textContent = `${libro.titulo} (${libro.anio_publicacion || "s/f"}) — ISBN ${libro.isbn || ""}`;
      listaLibros.appendChild(li);
    }
  }
  seccionResultado.hidden = false;
}

// ── Modo cliente SOAP (Ejercicio04, Paso 14) ────────────────────────────
let idClasificadorActual = null;

// Traduce cada código de soap:Fault a un mensaje útil en español, SIN
// tecnicismos ni XML/SQL/stack traces (Tarea 2: "SOAP Fault y experiencia
// de usuario"). Lo técnico (fault.faultcode, fault.codigo crudo) se deja
// solo en la consola del renderer -- nunca en lo que ve el usuario.
const MENSAJES_FAULT = {
  ISBN_NO_ENCONTRADO: "Ese ISBN no existe en el catálogo.",
  CONCEPTO_NO_ENCONTRADO: "Ese concepto no está definido para ese libro.",
  CLASIFICADOR_NO_ENCONTRADO: "No encontramos ese clasificador. Regístrate de nuevo.",
  CLASIFICACION_DUPLICADA: "Ya habías clasificado ese concepto de ese libro antes.",
  DATOS_INVALIDOS: "Revisa los datos del formulario: algo no tiene el formato correcto.",
  ENVELOPE_INVALIDO: "Ocurrió un problema de comunicación con el servicio. Intenta de nuevo.",
  CREDENCIALES_INVALIDAS: "Usuario o contraseña incorrectos.",
  ERROR_INTERNO: "El servicio tuvo un problema interno. Intenta más tarde.",
};

function mensajeAmigable(resultado) {
  if (resultado.fault) {
    // El detalle técnico completo queda en consola (equivalente al "log"
    // del lado cliente); el usuario solo ve el mensaje traducido.
    console.error("SOAP Fault:", resultado.fault);
    return MENSAJES_FAULT[resultado.fault.codigo] || resultado.fault.descripcion;
  }
  console.error("Error de red/cliente:", resultado.error);
  return "No se pudo contactar al servicio SOAP. Verifica tu conexión e intenta de nuevo.";
}

function mostrarMensajeSoap(texto, esError) {
  const el = document.getElementById("soapMensaje");
  el.hidden = false;
  el.textContent = texto;
  el.className = esError ? "aviso aviso-error" : "aviso aviso-ok";
}

document.getElementById("formSoapClasificador").addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const nombre = document.getElementById("soapNombre").value;
  const apellido = document.getElementById("soapApellido").value;
  const correo = document.getElementById("soapCorreo").value;

  const resultado = await window.clienteSoap.registrarClasificador({ nombre, apellido, correo });
  if (!resultado.ok) {
    mostrarMensajeSoap(mensajeAmigable(resultado), true);
    return;
  }
  idClasificadorActual = resultado.data.idClasificador;
  document.getElementById("soapIdClasificadorTexto").textContent = idClasificadorActual;
  document.getElementById("soapAcciones").hidden = false;
  mostrarMensajeSoap(`Registrado correctamente. Tu id de clasificador es ${idClasificadorActual}.`, false);
});

document.getElementById("btnPendientes").addEventListener("click", async () => {
  const resultado = await window.clienteSoap.obtenerConceptosPendientes();
  const lista = document.getElementById("soapListaPendientes");
  lista.innerHTML = "";
  if (!resultado.ok) {
    mostrarMensajeSoap(mensajeAmigable(resultado), true);
    return;
  }
  if (resultado.data.length === 0) {
    lista.innerHTML = "<li>No hay conceptos pendientes por clasificar ahora mismo.</li>";
    return;
  }
  for (const c of resultado.data) {
    const li = document.createElement("li");
    li.textContent = `${c.tituloLibro} (${c.categoria}) — concepto "${c.nombreConcepto}" [isbn=${c.isbn}, idConcepto=${c.idConcepto}]`;
    lista.appendChild(li);
  }
});

document.getElementById("formSoapClasificar").addEventListener("submit", async (evento) => {
  evento.preventDefault();
  if (!idClasificadorActual) {
    mostrarMensajeSoap("Regístrate como clasificador primero.", true);
    return;
  }
  const isbn = document.getElementById("soapIsbn").value;
  const idConcepto = document.getElementById("soapIdConcepto").value;
  const modeloCloud = document.getElementById("soapModelo").value;

  const resultado = await window.clienteSoap.registrarClasificacion({
    idClasificador: idClasificadorActual,
    isbn,
    idConcepto,
    modeloCloud,
  });
  if (!resultado.ok) {
    mostrarMensajeSoap(mensajeAmigable(resultado), true);
    return;
  }
  mostrarMensajeSoap(resultado.data.mensaje || "Clasificación registrada.", false);
});

document.getElementById("btnProgreso").addEventListener("click", async () => {
  if (!idClasificadorActual) {
    mostrarMensajeSoap("Regístrate como clasificador primero.", true);
    return;
  }
  const resultado = await window.clienteSoap.obtenerProgresoUsuario(idClasificadorActual);
  if (!resultado.ok) {
    mostrarMensajeSoap(mensajeAmigable(resultado), true);
    return;
  }
  document.getElementById("soapProgresoTexto").textContent =
    `Clasificados: ${resultado.data.totalClasificados} — Pendientes: ${resultado.data.totalPendientes}`;
});

// ── Tarea 1: estadísticas protegidas con WS-Security ────────────────────
document.getElementById("formEstadisticas").addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const usuario = document.getElementById("wsUsuario").value;
  const password = document.getElementById("wsPassword").value;

  const resultado = await window.clienteSoap.obtenerEstadisticasPorModelo({ usuario, password });
  const lista = document.getElementById("listaEstadisticas");
  lista.innerHTML = "";
  if (!resultado.ok) {
    mostrarMensajeSoap(mensajeAmigable(resultado), true);
    return;
  }
  // Nunca se guarda ni se muestra la contraseña de vuelta -- se usa una
  // sola vez para esta petición y se descarta.
  document.getElementById("wsPassword").value = "";
  const { totalIaaS, totalPaaS, totalSaaS, totalFaaS } = resultado.data;
  for (const [modelo, total] of [["IaaS", totalIaaS], ["PaaS", totalPaaS], ["SaaS", totalSaaS], ["FaaS", totalFaaS]]) {
    const li = document.createElement("li");
    li.textContent = `${modelo}: ${total}`;
    lista.appendChild(li);
  }
});
