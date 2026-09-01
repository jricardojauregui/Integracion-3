/* =============================================================================
   Visor de imágenes a pantalla completa: zoom, arrastre, teclado y gestos.
   Se conecta a cualquier contenedor con el atributo data-galeria.
   ============================================================================= */
(function () {
  "use strict";

  var ICONOS = {
    cerrar: '<path d="M4 4l10 10M14 4L4 14" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>',
    previo: '<path d="M11.5 3.5L5.5 9l6 5.5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>',
    siguiente: '<path d="M6.5 3.5L12.5 9l-6 5.5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>',
    mas: '<path d="M9 4v10M4 9h10" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>',
    menos: '<path d="M4 9h10" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>',
    restablecer: '<path d="M3 9a6 6 0 106-6" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><path d="M9 0.5V5.5L13 3" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>',
    descargar: '<path d="M9 3v8m0 0l-3.2-3.2M9 11l3.2-3.2M3.5 13.5h11" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>'
  };

  var ZOOM_MIN = 1, ZOOM_MAX = 6;

  var estado = {
    imagenes: [], indice: 0, escala: 1, x: 0, y: 0,
    arrastrando: false, origen: null, distanciaPinza: 0, disparador: null
  };
  var nodos = {};

  function svg(camino) {
    return '<svg viewBox="0 0 18 18" aria-hidden="true">' + camino + "</svg>";
  }

  function construir() {
    var visor = document.createElement("div");
    visor.className = "visor";
    visor.setAttribute("role", "dialog");
    visor.setAttribute("aria-modal", "true");
    visor.setAttribute("aria-label", "Visor de imágenes");
    visor.innerHTML =
      '<div class="visor__barra">' +
        '<span class="visor__contador" data-contador></span>' +
        '<p class="visor__titulo" data-titulo></p>' +
        '<div class="visor__herramientas">' +
          '<button type="button" class="visor__boton" data-alejar aria-label="Alejar">' + svg(ICONOS.menos) + "</button>" +
          '<span class="visor__zoom" data-nivel>100%</span>' +
          '<button type="button" class="visor__boton" data-acercar aria-label="Acercar">' + svg(ICONOS.mas) + "</button>" +
          '<button type="button" class="visor__boton" data-restablecer aria-label="Restablecer zoom">' + svg(ICONOS.restablecer) + "</button>" +
          '<a class="visor__boton" data-descargar download aria-label="Descargar imagen">' + svg(ICONOS.descargar) + "</a>" +
          '<button type="button" class="visor__boton" data-cerrar aria-label="Cerrar visor">' + svg(ICONOS.cerrar) + "</button>" +
        "</div>" +
      "</div>" +
      '<div class="visor__escenario" data-escenario>' +
        '<button type="button" class="visor__boton visor__nav visor__nav--previo" data-previo aria-label="Imagen anterior">' + svg(ICONOS.previo) + "</button>" +
        '<img class="visor__imagen" data-imagen alt="">' +
        '<button type="button" class="visor__boton visor__nav visor__nav--siguiente" data-siguiente aria-label="Imagen siguiente">' + svg(ICONOS.siguiente) + "</button>" +
      "</div>" +
      '<div class="visor__tira" data-tira></div>' +
      '<p class="visor__pie"><kbd>←</kbd> <kbd>→</kbd> cambiar · <kbd>+</kbd> <kbd>−</kbd> zoom · doble clic para acercar · <kbd>Esc</kbd> cerrar</p>';
    document.body.appendChild(visor);

    nodos.visor = visor;
    nodos.imagen = visor.querySelector("[data-imagen]");
    nodos.titulo = visor.querySelector("[data-titulo]");
    nodos.contador = visor.querySelector("[data-contador]");
    nodos.nivel = visor.querySelector("[data-nivel]");
    nodos.tira = visor.querySelector("[data-tira]");
    nodos.escenario = visor.querySelector("[data-escenario]");
    nodos.previo = visor.querySelector("[data-previo]");
    nodos.siguiente = visor.querySelector("[data-siguiente]");
    nodos.descargar = visor.querySelector("[data-descargar]");

    visor.querySelector("[data-cerrar]").addEventListener("click", cerrar);
    visor.querySelector("[data-acercar]").addEventListener("click", function () { zoomPor(1.5); });
    visor.querySelector("[data-alejar]").addEventListener("click", function () { zoomPor(1 / 1.5); });
    visor.querySelector("[data-restablecer]").addEventListener("click", restablecer);
    nodos.previo.addEventListener("click", function () { mover(-1); });
    nodos.siguiente.addEventListener("click", function () { mover(1); });
    visor.addEventListener("click", function (ev) {
      if (ev.target === visor || ev.target === nodos.escenario) cerrar();
    });

    conectarGestos();
  }

  function aplicar(animar) {
    nodos.imagen.style.transition = animar === false ? "none" : "";
    nodos.imagen.style.transform =
      "translate(" + estado.x + "px, " + estado.y + "px) scale(" + estado.escala + ")";
    nodos.imagen.style.cursor = estado.escala > 1 ? "grab" : "zoom-in";
    nodos.nivel.textContent = Math.round(estado.escala * 100) + "%";
  }

  function ajustar() {
    if (estado.escala <= 1) { estado.x = 0; estado.y = 0; return; }
    var caja = nodos.imagen.getBoundingClientRect();
    var marco = nodos.escenario.getBoundingClientRect();
    var mx = Math.max(0, (caja.width - marco.width) / 2);
    var my = Math.max(0, (caja.height - marco.height) / 2);
    estado.x = Math.min(mx, Math.max(-mx, estado.x));
    estado.y = Math.min(my, Math.max(-my, estado.y));
  }

  function zoomPor(factor, px, py) {
    var previa = estado.escala;
    var nueva = Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, previa * factor));
    if (nueva === previa) return;
    if (px !== undefined) {
      var marco = nodos.escenario.getBoundingClientRect();
      var cx = px - marco.left - marco.width / 2;
      var cy = py - marco.top - marco.height / 2;
      var razon = nueva / previa;
      estado.x = cx - (cx - estado.x) * razon;
      estado.y = cy - (cy - estado.y) * razon;
    }
    estado.escala = nueva;
    ajustar();
    aplicar();
  }

  function restablecer() { estado.escala = 1; estado.x = 0; estado.y = 0; aplicar(); }

  function separacion(toques) {
    return Math.hypot(toques[0].clientX - toques[1].clientX,
                      toques[0].clientY - toques[1].clientY);
  }

  function conectarGestos() {
    var img = nodos.imagen;

    img.addEventListener("dblclick", function (ev) {
      ev.preventDefault();
      if (estado.escala > 1) restablecer(); else zoomPor(2.5, ev.clientX, ev.clientY);
    });

    nodos.escenario.addEventListener("wheel", function (ev) {
      ev.preventDefault();
      zoomPor(ev.deltaY < 0 ? 1.12 : 1 / 1.12, ev.clientX, ev.clientY);
    }, { passive: false });

    img.addEventListener("pointerdown", function (ev) {
      if (estado.escala <= 1) return;
      ev.preventDefault();
      estado.arrastrando = true;
      estado.origen = { x: ev.clientX - estado.x, y: ev.clientY - estado.y };
      img.classList.add("arrastrando");
      img.setPointerCapture(ev.pointerId);
    });

    img.addEventListener("pointermove", function (ev) {
      if (!estado.arrastrando) return;
      estado.x = ev.clientX - estado.origen.x;
      estado.y = ev.clientY - estado.origen.y;
      ajustar();
      aplicar(false);
    });

    ["pointerup", "pointercancel", "pointerleave"].forEach(function (tipo) {
      img.addEventListener(tipo, function () {
        estado.arrastrando = false;
        img.classList.remove("arrastrando");
      });
    });

    nodos.escenario.addEventListener("touchstart", function (ev) {
      if (ev.touches.length === 2) estado.distanciaPinza = separacion(ev.touches);
    }, { passive: true });

    nodos.escenario.addEventListener("touchmove", function (ev) {
      if (ev.touches.length !== 2) return;
      ev.preventDefault();
      var actual = separacion(ev.touches);
      if (estado.distanciaPinza) {
        zoomPor(actual / estado.distanciaPinza,
                (ev.touches[0].clientX + ev.touches[1].clientX) / 2,
                (ev.touches[0].clientY + ev.touches[1].clientY) / 2);
      }
      estado.distanciaPinza = actual;
    }, { passive: false });

    nodos.escenario.addEventListener("touchend", function (ev) {
      if (ev.touches.length < 2) estado.distanciaPinza = 0;
    }, { passive: true });

    document.addEventListener("keydown", function (ev) {
      if (!nodos.visor || !nodos.visor.classList.contains("abierto")) return;
      switch (ev.key) {
        case "Escape": cerrar(); break;
        case "ArrowLeft": mover(-1); break;
        case "ArrowRight": mover(1); break;
        case "+": case "=": zoomPor(1.5); break;
        case "-": case "_": zoomPor(1 / 1.5); break;
        case "0": restablecer(); break;
      }
    });
  }

  function mostrar(indice) {
    if (indice < 0 || indice >= estado.imagenes.length) return;
    estado.indice = indice;
    var item = estado.imagenes[indice];

    restablecer();
    nodos.imagen.src = item.src;
    nodos.imagen.alt = item.alt || "";
    nodos.titulo.textContent = item.alt || "";
    nodos.contador.textContent = (indice + 1) + " / " + estado.imagenes.length;
    nodos.descargar.href = item.src;

    var unica = estado.imagenes.length < 2;
    nodos.previo.hidden = unica;
    nodos.siguiente.hidden = unica;

    Array.prototype.forEach.call(nodos.tira.children, function (ficha, i) {
      ficha.setAttribute("aria-current", i === indice ? "true" : "false");
      if (i === indice && ficha.scrollIntoView) {
        ficha.scrollIntoView({ block: "nearest", inline: "center", behavior: "smooth" });
      }
    });
  }

  function mover(delta) {
    var destino = estado.indice + delta;
    if (destino < 0) destino = estado.imagenes.length - 1;
    if (destino >= estado.imagenes.length) destino = 0;
    mostrar(destino);
  }

  function pintarTira() {
    nodos.tira.innerHTML = "";
    nodos.tira.hidden = estado.imagenes.length < 2;
    if (estado.imagenes.length < 2) return;
    nodos.tira.classList.toggle("visor__tira--centrada", estado.imagenes.length < 9);
    estado.imagenes.forEach(function (item, i) {
      var boton = document.createElement("button");
      boton.type = "button";
      boton.className = "visor__ficha";
      boton.setAttribute("aria-label", "Ver imagen " + (i + 1));
      boton.innerHTML = '<img src="' + (item.min || item.src) + '" alt="" loading="lazy">';
      boton.addEventListener("click", function () { mostrar(i); });
      nodos.tira.appendChild(boton);
    });
  }

  function abrir(imagenes, indice, disparador) {
    if (!imagenes || !imagenes.length) return;
    if (!nodos.visor) construir();
    estado.imagenes = imagenes;
    estado.disparador = disparador || null;
    pintarTira();
    nodos.visor.classList.add("abierto");
    document.body.classList.add("visor-abierto");
    mostrar(indice || 0);
    nodos.visor.querySelector("[data-cerrar]").focus();
  }

  function cerrar() {
    nodos.visor.classList.remove("abierto");
    document.body.classList.remove("visor-abierto");
    if (estado.disparador && estado.disparador.focus) estado.disparador.focus();
  }

  /* Lee las galerías de la página: cada botón declara su imagen completa. */
  function conectar(contenedor) {
    var raiz = contenedor || document;
    Array.prototype.forEach.call(raiz.querySelectorAll("[data-galeria]"), function (galeria) {
      var botones = Array.prototype.slice.call(galeria.querySelectorAll("[data-completa]"));
      var lista = botones.map(function (b) {
        return {
          src: b.getAttribute("data-completa"),
          min: b.getAttribute("data-min") || "",
          alt: b.getAttribute("data-titulo") || ""
        };
      });
      botones.forEach(function (boton, i) {
        boton.addEventListener("click", function () { abrir(lista, i, boton); });
      });
    });
  }

  window.Visor = { abrir: abrir, conectar: conectar };
})();